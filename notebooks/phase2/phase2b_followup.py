#!/usr/bin/env python3
"""
Saans - Phase 2b follow-up tests. Answers the open questions from the first smoke run (17 Nov 2026):

  T2b  Which Open-Meteo weather MODEL keeps boundary_layer_height (and other mixing proxies) in its
       archived forecasts? (first run: 0% non-null for the default model in Nov 2022 and Nov 2024)
  T4a2 OpenAQ Delhi: lag of ACTIVE stations only, and duplicate stations (same place, two providers)
  T4b2 FIRMS: why did VIIRS_SNPP_SP return 0 fires for 2024-11-05? Compare all sensors and years.
  T5   CAMS archive from ADS (re-run after accepting the licence)

Keys come from env vars OPENAQ_API_KEY, FIRMS_MAP_KEY and ~/.cdsapirc (same as before).
Run:  python phase2b_followup.py   ->  saves phase2b_results.json
"""
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone

import pandas as pd
import requests

DELHI = (28.6139, 77.2090)
TIMEOUT = 60
R = {"run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tests": {}}


def rec(name, **kv):
    R["tests"].setdefault(name, {}).update(kv)


def run(name, fn):
    print(f"\n=== {name} ===")
    t0 = time.time()
    try:
        fn()
        rec(name, status=R["tests"].get(name, {}).get("status", "PASS"))
    except Exception as e:
        rec(name, status="FAIL", error=f"{type(e).__name__}: {e}"[:600])
    rec(name, seconds=round(time.time() - t0, 1))
    print(json.dumps(R["tests"][name], indent=1, default=str)[:4000])


# ---------------------------------------------------------------- T2b weather archives by model
VARS = ["boundary_layer_height", "temperature_2m", "temperature_850hPa", "wind_speed_10m",
        "relative_humidity_2m", "shortwave_radiation", "cloud_cover_low"]
MODELS = ["best_match", "ecmwf_ifs025", "ecmwf_ifs", "gfs_seamless", "gfs_global", "icon_seamless",
          "jma_seamless", "gem_seamless", "cma_grapes_global"]


def nn_share(js, var):
    vals = (js.get("hourly") or {}).get(var) or []
    return round(sum(v is not None for v in vals) / len(vals), 2) if vals else None


def t2b_weather_models():
    lat, lon = DELHI
    out = {}
    for api, host, start, end, suffix in (
        ("hist_forecast_2022", "historical-forecast-api", "2022-11-01", "2022-11-07", ""),
        ("hist_forecast_2024", "historical-forecast-api", "2024-11-01", "2024-11-07", ""),
        ("previous_runs_2024_day1", "previous-runs-api", "2024-11-01", "2024-11-07", "_previous_day1"),
    ):
        for m in MODELS:
            hourly = ",".join(v + suffix for v in VARS)
            r = requests.get(f"https://{host}.open-meteo.com/v1/forecast", timeout=TIMEOUT, params=dict(
                latitude=lat, longitude=lon, hourly=hourly, models=m, start_date=start, end_date=end,
                timezone="Asia/Kolkata"))
            if r.status_code != 200:
                out[f"{api}|{m}"] = f"HTTP {r.status_code}: {r.text[:120]}"
                continue
            js = r.json()
            out[f"{api}|{m}"] = {v: nn_share(js, v + suffix) for v in VARS}
            time.sleep(0.3)
    rec("T2b_weather_models", results=out)


# ---------------------------------------------------------------- T4a2 OpenAQ active lag + duplicates
def t4a2_openaq():
    key = os.getenv("OPENAQ_API_KEY")
    if not key:
        rec("T4a2_openaq", status="SKIPPED", reason="no OPENAQ_API_KEY"); return
    r = requests.get("https://api.openaq.org/v3/locations", headers={"X-API-Key": key}, timeout=TIMEOUT,
                     params={"coordinates": f"{DELHI[0]},{DELHI[1]}", "radius": 25000, "limit": 1000})
    r.raise_for_status(); res = r.json()["results"]
    now = datetime.now(timezone.utc)
    rows = []
    for loc in res:
        if not any((s.get("parameter") or {}).get("name") == "pm25" for s in loc.get("sensors", [])):
            continue
        last = (loc.get("datetimeLast") or {}).get("utc")
        lag = (now - datetime.fromisoformat(last.replace("Z", "+00:00"))).total_seconds() / 60 if last else None
        c = loc.get("coordinates") or {}
        rows.append({"id": loc["id"], "name": loc.get("name"), "provider": (loc.get("provider") or {}).get("name"),
                     "is_monitor": loc.get("isMonitor"), "lat": c.get("latitude"), "lon": c.get("longitude"),
                     "lag_min": lag})
    df = pd.DataFrame(rows)
    active = df[df.lag_min <= 24 * 60]
    df["cell"] = df.lat.round(3).astype(str) + "," + df.lon.round(3).astype(str)
    dup = df.groupby("cell").filter(lambda g: len(g) > 1)
    rec("T4a2_openaq",
        pm25_locations=len(df), reference_monitors=int(df.is_monitor.fillna(False).sum()),
        active_last_24h=len(active),
        active_lag_minutes=active.lag_min.describe(percentiles=[.1, .5, .9]).round(1).to_dict(),
        active_by_provider=active.groupby("provider").lag_min.median().round(1).to_dict(),
        inactive_over_30d=int((df.lag_min > 30 * 24 * 60).sum()),
        duplicate_place_groups=int(dup.cell.nunique()),
        duplicate_examples=dup.sort_values("cell")[["cell", "name", "provider", "lag_min"]].head(12)
            .round(1).to_dict(orient="records"))
    df.to_csv("openaq_delhi_pm25_locations.csv", index=False)


# ---------------------------------------------------------------- T4b2 FIRMS sensors x years
def t4b2_firms():
    key = os.getenv("FIRMS_MAP_KEY")
    if not key:
        rec("T4b2_firms", status="SKIPPED", reason="no FIRMS_MAP_KEY"); return
    base = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    bbox = "73.8,27.6,77.6,32.6"   # Punjab + Haryana (west,south,east,north)
    out = {}
    for src in ("MODIS_SP", "VIIRS_SNPP_SP", "VIIRS_NOAA20_SP", "VIIRS_NOAA21_SP"):
        for date in ("2023-11-05", "2024-11-05", "2025-11-05"):
            try:
                df = pd.read_csv(f"{base}/{key}/{src}/{bbox}/1/{date}")
                cell = {"fires": len(df)}
                if len(df) and "acq_time" in df.columns:
                    cell["acq_time_utc_min_max"] = [int(df.acq_time.min()), int(df.acq_time.max())]
                    if "frp" in df.columns:
                        cell["frp_sum"] = round(float(df.frp.sum()), 1)
                out[f"{src}|{date}"] = cell
            except Exception as e:
                out[f"{src}|{date}"] = f"{type(e).__name__}: {str(e)[:120]}"
    for src in ("VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT", "MODIS_NRT"):
        try:
            df = pd.read_csv(f"{base}/{key}/{src}/{bbox}/2")
            out[f"{src}|last_2_days"] = {"fires": len(df)}
        except Exception as e:
            out[f"{src}|last_2_days"] = f"{type(e).__name__}: {str(e)[:120]}"
    rec("T4b2_firms", results=out)


# ---------------------------------------------------------------- T5 CAMS ADS archive
def t5_cams():
    import cdsapi
    c = cdsapi.Client()
    t0 = time.time()
    c.retrieve("cams-global-atmospheric-composition-forecasts", {
        "date": ["2024-11-10/2024-11-10"], "type": ["forecast"], "time": ["00:00"],
        "leadtime_hour": [str(h) for h in range(0, 73, 3)],
        "variable": ["particulate_matter_2.5um", "particulate_matter_10um"],
        "area": [29.2, 76.8, 28.2, 77.8], "data_format": "netcdf_zip"}, "cams_delhi_test.zip")
    rec("T5_cams_ads", downloaded_bytes=os.path.getsize("cams_delhi_test.zip"),
        wall_seconds_incl_queue=round(time.time() - t0, 1))
    try:  # optional: peek inside if xarray is available
        import zipfile, xarray as xr
        with zipfile.ZipFile("cams_delhi_test.zip") as z:
            z.extractall("cams_test"); names = z.namelist()
        ds = xr.open_dataset(os.path.join("cams_test", names[0]))
        rec("T5_cams_ads", files=names, dims={k: int(v) for k, v in ds.sizes.items()},
            variables=list(ds.data_vars), pm25_units=str(ds[list(ds.data_vars)[0]].attrs.get("units")))
    except Exception as e:
        rec("T5_cams_ads", inspect_note=f"could not open netcdf: {type(e).__name__}")


if __name__ == "__main__":
    for n, f in (("T2b_weather_models", t2b_weather_models), ("T4a2_openaq", t4a2_openaq),
                 ("T4b2_firms", t4b2_firms), ("T5_cams_ads", t5_cams)):
        run(n, f)
    json.dump(R, open("phase2b_results.json", "w"), indent=1, default=str)
    print("\nSaved phase2b_results.json (+ openaq_delhi_pm25_locations.csv). Send both to Claude.")
