#!/usr/bin/env python3
"""
Saans - Phase 2c: weather archive details (no keys needed, ~1 min).

  A. From which month does GFS keep boundary_layer_height in the Historical Forecast archive?
     (T2b: 0% in Nov 2022, 100% in Nov 2024)
  B. Previous Runs API (forecast as issued 1/2/3 days earlier) - which variables and from when?
     T2b failed with HTTP 400 because it asked for a pressure-level variable (temperature_850hPa)
     with a _previous_dayN suffix. That was a bug in Claude's test; here each variable is asked
     separately so one unsupported variable cannot fail the whole request.
Output: phase2c_results.json
"""
import json
import time
from datetime import date

import requests

LAT, LON = 28.6139, 77.2090
OUT = {"A_gfs_blh_by_month": {}, "B_previous_runs": {}}


def share(js, var):
    vals = (js.get("hourly") or {}).get(var) or []
    return round(sum(v is not None for v in vals) / len(vals), 2) if vals else None


def get(host, **p):
    r = requests.get(f"https://{host}.open-meteo.com/v1/forecast", timeout=60,
                     params=dict(latitude=LAT, longitude=LON, timezone="Asia/Kolkata", **p))
    return r.status_code, (r.json() if r.status_code == 200 else r.text[:160])


# A: first week of every month, Nov 2022 -> Nov 2024
y, m = 2022, 11
while (y, m) <= (2024, 11):
    start = date(y, m, 1).isoformat(); end = date(y, m, 7).isoformat()
    code, js = get("historical-forecast-api", hourly="boundary_layer_height", models="gfs_seamless",
                   start_date=start, end_date=end)
    OUT["A_gfs_blh_by_month"][start[:7]] = share(js, "boundary_layer_height") if code == 200 else f"HTTP {code}"
    m += 1
    if m == 13:
        y, m = y + 1, 1
    time.sleep(0.25)

# B: previous runs, one variable per request
VARS = ["temperature_2m", "wind_speed_10m", "relative_humidity_2m", "boundary_layer_height",
        "shortwave_radiation", "cloud_cover_low", "temperature_850hPa"]
for model in ("gfs_seamless", "ecmwf_ifs025", "best_match"):
    for start in ("2022-11-01", "2023-11-01", "2024-11-01", "2025-11-01"):
        end = start[:8] + "07"
        for v in VARS:
            for d in (1, 3):
                code, js = get("previous-runs-api", hourly=f"{v}_previous_day{d}", models=model,
                               start_date=start, end_date=end)
                OUT["B_previous_runs"][f"{model}|{start[:7]}|{v}|day{d}"] = (
                    share(js, f"{v}_previous_day{d}") if code == 200 else f"HTTP {code}: {str(js)[:80]}")
                time.sleep(0.2)

json.dump(OUT, open("phase2c_results.json", "w"), indent=1)
print(json.dumps(OUT["A_gfs_blh_by_month"], indent=1))
ok = {k: v for k, v in OUT["B_previous_runs"].items() if v == 1.0}
print(f"\nPrevious runs: {len(ok)} of {len(OUT['B_previous_runs'])} combos fully available")
print("Saved phase2c_results.json - send it to Claude.")
