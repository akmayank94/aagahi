#!/usr/bin/env python3
"""
Saans - Phase 2 data-access smoke tests (run on your own laptop, ~5-10 min).

Each test checks one data source: can we reach it, how fresh is it, how far back
does it go, and does it contain the fields we need. Results are printed and saved
to phase2_smoke_results.json - paste that file back to Claude.

Setup (once):
    pip install requests pandas
    # optional, only for test T5 (CAMS archive):  pip install cdsapi

Keys (all free; tests that need a missing key are skipped, not failed):
    OPENAQ_API_KEY   -> https://explore.openaq.org/register
    FIRMS_MAP_KEY    -> https://firms.modaps.eosdis.nasa.gov/api/map_key/
    T5 needs ~/.cdsapirc from https://ads.atmosphere.copernicus.eu (free account,
    accept the CAMS licence on the dataset page first). Run with --cams to enable.

Windows PowerShell:  $env:OPENAQ_API_KEY="..."; $env:FIRMS_MAP_KEY="..."
Linux / macOS:       export OPENAQ_API_KEY=... FIRMS_MAP_KEY=...

Run:
    python phase2_smoke_tests.py            # T1-T4
    python phase2_smoke_tests.py --cams     # T1-T5
"""
import base64
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import pandas as pd
import requests

DELHI = (28.6139, 77.2090)          # city centre, used for weather / CAMS / OpenAQ radius
TIMEOUT = 60
RESULTS = {"run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tests": {}}


def record(name, **kv):
    RESULTS["tests"].setdefault(name, {}).update(kv)


def run(name, fn):
    print(f"\n=== {name} ===")
    t0 = time.time()
    try:
        fn()
        record(name, status=RESULTS["tests"].get(name, {}).get("status", "PASS"))
    except Exception as e:  # keep going; one broken source must not stop the audit
        record(name, status="FAIL", error=f"{type(e).__name__}: {e}"[:500])
    record(name, seconds=round(time.time() - t0, 1))
    print(json.dumps(RESULTS["tests"][name], indent=2, default=str)[:3000])


# ---------------------------------------------------------------------------
# T1 - CPCB official data repository (15-minute raw station data)
# ---------------------------------------------------------------------------
CPCB = "https://airquality.cpcb.gov.in/dataRepository"
UA = {"User-Agent": "Mozilla/5.0 (saans-phase2-audit; student project)",
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
NCR_CITIES = ["Delhi", "Gurugram", "Noida", "Ghaziabad", "Faridabad", "Greater Noida", "Sonipat",
              "Bahadurgarh", "Meerut", "Baghpat"]


def t1_cpcb():
    s = requests.Session(); s.headers.update(UA)
    r = s.post(f"{CPCB}/all_india_stationlist", data="e30=", timeout=TIMEOUT); r.raise_for_status()
    data = json.loads(base64.b64decode(r.text).decode())
    stations_by_city = data["dropdown"]["stations"]
    counts = {c: len(stations_by_city.get(c, [])) for c in NCR_CITIES if c in stations_by_city}
    record("T1_cpcb_repository", stations_per_ncr_city=counts,
           total_india_stations=sum(len(v) for v in stations_by_city.values()))

    # one high-pollution Delhi station; fall back to the first Delhi station
    delhi = stations_by_city["Delhi"]
    st = next((x for x in delhi if "Anand Vihar" in x["label"]), delhi[0])
    payload = {"station_id": st["value"], "station_name": st["label"], "state": "Delhi", "city": "Delhi",
               "frequency": "15min", "dataType": "raw"}
    enc = base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    r = s.post(f"{CPCB}/file_Path", data=enc, timeout=TIMEOUT); r.raise_for_status()
    files = json.loads(base64.b64decode(r.text).decode()).get("data", [])
    years = sorted(str(f.get("year")) for f in files)
    record("T1_cpcb_repository", test_station=st["label"], station_id=st["value"], years_available=years)

    # download the most recent COMPLETE year if present, else the latest
    this_year = datetime.now().year
    pick = next((f for f in files if str(f.get("year")) == str(this_year - 1)), files[-1])
    url = f"{CPCB}/download_file?file_name={quote(pick['filepath'])}"
    raw = s.get(url, timeout=180).content
    df = pd.read_csv(io.BytesIO(raw))
    ts_col = next((c for c in df.columns if c.strip().lower() in ("timestamp", "date", "from date")), df.columns[0])
    record("T1_cpcb_repository", timestamp_column_used=ts_col)
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    pm25 = next((c for c in df.columns if c.upper().startswith("PM2.5")), None)
    pm10 = next((c for c in df.columns if c.upper().startswith("PM10")), None)
    out = {"downloaded_year": pick.get("year"), "file_mb": round(len(raw) / 1e6, 2), "rows": len(df),
           "columns": list(df.columns)[:40], "first_ts": str(df[ts_col].min()), "last_ts": str(df[ts_col].max())}
    for name, col in (("pm25", pm25), ("pm10", pm10)):
        if col:
            v = pd.to_numeric(df[col], errors="coerce")
            out[f"{name}_non_null_share"] = round(v.notna().mean(), 3)
            out[f"{name}_max"] = float(v.max())
            out[f"{name}_count_ge_999"] = int((v >= 999).sum())     # the "999 cap" trap
            out[f"{name}_count_le_0"] = int((v <= 0).sum())
            out[f"{name}_p99"] = float(v.quantile(0.99))
    record("T1_cpcb_repository", **out)
    df.head(2000).to_csv("cpcb_sample_rows.csv", index=False)


# ---------------------------------------------------------------------------
# T2 - Open-Meteo weather: live forecast, archived forecasts, previous runs, ERA5
# ---------------------------------------------------------------------------
WX_VARS = "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,boundary_layer_height,precipitation"


def _om(url, **params):
    r = requests.get(url, params=params, timeout=TIMEOUT)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300])


def _nn(js, var):
    vals = js.get("hourly", {}).get(var, []) if isinstance(js, dict) else []
    return round(sum(v is not None for v in vals) / max(len(vals), 1), 3), len(vals)


def t2_openmeteo_weather():
    lat, lon = DELHI
    code, js = _om("https://api.open-meteo.com/v1/forecast", latitude=lat, longitude=lon, hourly=WX_VARS,
                   past_days=2, forecast_days=3, timezone="Asia/Kolkata")
    record("T2_openmeteo_weather", forecast_http=code, forecast_blh_non_null=_nn(js, "boundary_layer_height"))
    code, js = _om("https://historical-forecast-api.open-meteo.com/v1/forecast", latitude=lat, longitude=lon,
                   hourly=WX_VARS, start_date="2022-11-01", end_date="2022-11-07", timezone="Asia/Kolkata")
    record("T2_openmeteo_weather", hist_forecast_2022_http=code,
           hist_forecast_2022_blh_non_null=_nn(js, "boundary_layer_height"),
           hist_forecast_error=None if code == 200 else js)
    code, js = _om("https://previous-runs-api.open-meteo.com/v1/forecast", latitude=lat, longitude=lon,
                   hourly="temperature_2m_previous_day1,boundary_layer_height_previous_day1,wind_speed_10m_previous_day2",
                   start_date="2024-11-01", end_date="2024-11-07", timezone="Asia/Kolkata")
    record("T2_openmeteo_weather", previous_runs_http=code,
           previous_runs_blh_day1_non_null=_nn(js, "boundary_layer_height_previous_day1"),
           previous_runs_error=None if code == 200 else js)
    code, js = _om("https://archive-api.open-meteo.com/v1/archive", latitude=lat, longitude=lon, hourly=WX_VARS,
                   start_date="2017-11-01", end_date="2017-11-07", timezone="Asia/Kolkata")
    record("T2_openmeteo_weather", era5_2017_http=code, era5_2017_blh_non_null=_nn(js, "boundary_layer_height"))


# ---------------------------------------------------------------------------
# T3 - Open-Meteo air quality (CAMS global) - our baseline to beat
# ---------------------------------------------------------------------------
def t3_openmeteo_cams():
    lat, lon = DELHI
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    code, js = _om(url, latitude=lat, longitude=lon, hourly="pm2_5,pm10", past_days=7, forecast_days=5,
                   domains="cams_global", timezone="Asia/Kolkata")
    hrs = js.get("hourly", {}) if isinstance(js, dict) else {}
    record("T3_openmeteo_cams", live_http=code, live_hours=len(hrs.get("time", [])),
           live_pm25_non_null=_nn(js, "pm2_5"),
           live_pm25_last_non_null_time=next((t for t, v in zip(reversed(hrs.get("time", [])),
                                                                reversed(hrs.get("pm2_5", []))) if v is not None), None))
    # how far back does the stitched history go?
    for start in ("2022-08-01", "2022-11-01", "2023-11-01"):
        end = (datetime.fromisoformat(start) + timedelta(days=6)).date().isoformat()
        code, js = _om(url, latitude=lat, longitude=lon, hourly="pm2_5", start_date=start, end_date=end,
                       domains="cams_global", timezone="Asia/Kolkata")
        record("T3_openmeteo_cams", **{f"history_{start}_http": code, f"history_{start}_pm25_non_null": _nn(js, "pm2_5")})
    # does an archive of the forecast AS ISSUED 1-2 days earlier exist? (needed for a fair baseline)
    code, js = _om(url, latitude=lat, longitude=lon, hourly="pm2_5_previous_day1,pm2_5_previous_day2",
                   past_days=7, forecast_days=1, domains="cams_global", timezone="Asia/Kolkata")
    record("T3_openmeteo_cams", previous_day_vars_http=code,
           previous_day1_non_null=_nn(js, "pm2_5_previous_day1"),
           previous_day_error=None if code == 200 else js)


# ---------------------------------------------------------------------------
# T4 - OpenAQ (live station feed, fallback ingestion) and NASA FIRMS (fires)
# ---------------------------------------------------------------------------
def t4a_openaq():
    key = os.getenv("OPENAQ_API_KEY")
    if not key:
        record("T4a_openaq", status="SKIPPED", reason="OPENAQ_API_KEY not set"); return
    h = {"X-API-Key": key}
    r = requests.get("https://api.openaq.org/v3/locations", headers=h, timeout=TIMEOUT,
                     params={"coordinates": f"{DELHI[0]},{DELHI[1]}", "radius": 25000, "limit": 1000})
    r.raise_for_status(); res = r.json()["results"]
    now = datetime.now(timezone.utc)
    lags, providers, owners, licences, pm25_locs = [], {}, {}, {}, 0
    for loc in res:
        prov = (loc.get("provider") or {}).get("name"); providers[prov] = providers.get(prov, 0) + 1
        own = (loc.get("owner") or {}).get("name"); owners[own] = owners.get(own, 0) + 1
        for lic in loc.get("licenses") or []:
            licences[lic.get("name")] = licences.get(lic.get("name"), 0) + 1
        if any((sn.get("parameter") or {}).get("name") == "pm25" for sn in loc.get("sensors", [])):
            pm25_locs += 1
            last = (loc.get("datetimeLast") or {}).get("utc")
            if last:
                lags.append((now - datetime.fromisoformat(last.replace("Z", "+00:00"))).total_seconds() / 60)
    lags.sort()
    record("T4a_openaq", locations_within_25km=len(res), pm25_locations=pm25_locs, providers=providers,
           owners=dict(list(owners.items())[:10]), licences=licences,
           pm25_lag_minutes_median=round(lags[len(lags) // 2], 1) if lags else None,
           pm25_locations_updated_last_3h=sum(l <= 180 for l in lags),
           rate_limit_headers={k: v for k, v in r.headers.items() if k.lower().startswith("x-ratelimit")})


def t4b_firms():
    key = os.getenv("FIRMS_MAP_KEY")
    if not key:
        record("T4b_firms", status="SKIPPED", reason="FIRMS_MAP_KEY not set"); return
    base = "https://firms.modaps.eosdis.nasa.gov/api"
    bbox = "73.8,27.6,77.6,32.6"   # west,south,east,north - Punjab + Haryana
    avail = pd.read_csv(f"{base}/data_availability/csv/{key}/all")
    record("T4b_firms", data_availability=avail.to_dict(orient="records"))
    out = {}
    for src, date in (("VIIRS_SNPP_NRT", None), ("VIIRS_SNPP_SP", "2024-11-05"), ("MODIS_SP", "2019-11-05")):
        url = f"{base}/area/csv/{key}/{src}/{bbox}/1" + (f"/{date}" if date else "")
        df = pd.read_csv(url)
        out[f"{src}_{date or 'latest'}_fires"] = len(df)
        if len(df) and "acq_time" in df.columns:
            out[f"{src}_{date or 'latest'}_acq_time_range_utc"] = [int(df.acq_time.min()), int(df.acq_time.max())]
    record("T4b_firms", **out)
    status = requests.get(f"https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={key}", timeout=TIMEOUT)
    record("T4b_firms", key_status=status.text[:300])


# ---------------------------------------------------------------------------
# T5 - CAMS global forecasts archive from the Atmosphere Data Store (lead-time aware)
# ---------------------------------------------------------------------------
def t5_cams_ads():
    if "--cams" not in sys.argv:
        record("T5_cams_ads", status="SKIPPED", reason="run with --cams to enable"); return
    import cdsapi
    c = cdsapi.Client()
    target = "cams_delhi_test.zip"
    c.retrieve("cams-global-atmospheric-composition-forecasts", {
        "date": ["2024-11-10/2024-11-10"], "type": ["forecast"], "time": ["00:00"],
        "leadtime_hour": [str(h) for h in range(0, 73, 3)],
        "variable": ["particulate_matter_2.5um", "particulate_matter_10um"],
        "area": [29.2, 76.8, 28.2, 77.8],            # N, W, S, E around Delhi-NCR
        "data_format": "netcdf_zip"}, target)
    record("T5_cams_ads", downloaded_bytes=os.path.getsize(target),
           note="success means archived CAMS forecasts by lead time are retrievable for a fair baseline")


def where_am_i():
    """Record the country of the machine running the tests (CPCB may block foreign IPs)."""
    try:
        info = requests.get("https://ipinfo.io/json", timeout=15).json()
        RESULTS["runner"] = {"country": info.get("country"), "region": info.get("region"), "org": info.get("org")}
    except Exception as e:
        RESULTS["runner"] = {"error": str(e)[:200]}
    print("Running from:", RESULTS["runner"])


if __name__ == "__main__":
    where_am_i()
    for name, fn in (("T1_cpcb_repository", t1_cpcb), ("T2_openmeteo_weather", t2_openmeteo_weather),
                     ("T3_openmeteo_cams", t3_openmeteo_cams), ("T4a_openaq", t4a_openaq),
                     ("T4b_firms", t4b_firms), ("T5_cams_ads", t5_cams_ads)):
        run(name, fn)
    with open("phase2_smoke_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print("\nSaved phase2_smoke_results.json  (+ cpcb_sample_rows.csv if T1 passed). Send both to Claude.")
