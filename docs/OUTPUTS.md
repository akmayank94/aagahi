# OUTPUTS.md — Saans measured results

Only measured or run results go here. Each entry records: date, phase, what was run (notebook/script + git commit), data window, and the numbers. Claims on the resume or in the report may only quote numbers from this file.

**Test-run counter** (final-exam season, 2025–26 winter hold-out): 0 runs.

---

## Phase 0–1 (17 Nov 2026)
No measurements. Phases 0–1 are decisions and research only (DECISIONS.md §0).

---

## Phase 2 — Data access

### 2.0 CPCB hourly-AQI mirror, measured by Claude (17 Nov 2026, ~01:30 IST)
- **File:** `Vonter/india-cpcb-aqi/data/cpcb-aqi.parquet` (raw.githubusercontent.com), 15.6 MB.
- **Script:** `saans_audit/inspect_aqi.py`.
- **Contents:** 562,878 station-days × 29 columns; date range **2017-01-01 → 2023-12-31**.
- **Delhi:** 81,148 station-days, **39 stations** by name.
  - Earliest from 2017-01-01: Mandir Marg, Punjabi Bagh, ITO, Sirifort, IHBAS, Shadipur, DTU, R K Puram, NSIT Dwarka.
  - IMD stations from Aug 2017; most DPCC stations from 2018-02-01.
  - Mundka, Pusa DPCC, Sri Aurobindo Marg, Bawana from Jul 2018; Alipur from Nov 2018; IITM Lodhi Road and Chandni Chowk from 2020-11-08.
- **NCR stations by name:** Noida 6, Gurugram 4, Faridabad 4, Ghaziabad 3, Meerut 3, Baghpat 2, Sonipat 1, Hapur 1, Bulandshahr 1.
- **Defect:** the `Station ID` column is wrong. All 39 Delhi stations share one ID (`site_115`) → DATASETS T-9.

### 2.1 Smoke tests T1–T5, run by Mayank on Colab (17 Nov 2026, 01:59 IST)
- **Notebook:** `saans_phase2_smoke_tests.ipynb`; results in `phase2_smoke_results.json`.
- **Runner:** Google LLC, Singapore (country SG), i.e. a foreign cloud IP.

| Test | Result | Measured |
|---|---|---|
| T1 CPCB repository | **FAIL** | `ConnectTimeout` on `airquality.cpcb.gov.in:443` after 60 s. The TCP connection itself never opened. Not yet known whether CPCB blocks foreign IPs or was down → laptop run (Indian IP) pending |
| T2 Open-Meteo weather | PASS with a **gap** | Live forecast: `boundary_layer_height` 100% non-null (120 h). **Historical Forecast, Nov 2022: 0% (168 h). Previous Runs, `_previous_day1`, Nov 2024: 0% (168 h).** ERA5 archive, Nov 2017: 100% |
| T3 CAMS via Open-Meteo | PASS with a **gap** | Live: 288 h, PM2.5 93.8% non-null, last value 2026-11-21 05:00 IST. History: week of 2022-08-01 54.2%; Nov 2022 100%; Nov 2023 100%. **`pm2_5_previous_day1`: 0% (192 h)** → no as-issued CAMS through Open-Meteo |
| T4a OpenAQ | PASS | 97 locations within 25 km, 95 with PM2.5. Providers: CPCB 57, caaqm 23, AirGradient 7, N/A 8, AirNow 1, StateAir NewDelhi 1. Licences listed on 8 (CC BY 4.0 ×7, US Public Domain ×1). PM2.5 lag median 150.8 min over all 95; 62 of 95 updated within 3 h. Rate limit 60/min confirmed |
| T4b FIRMS | PASS with an **anomaly** | Limit 5,000 per 10 min confirmed. Archive: MODIS from 2000-11-01, VIIRS S-NPP from 2012-01-20, NOAA-20 from 2018-04-01, NOAA-21 from 2023-03-01; all SP to 2026-07-31. NRT: NOAA-20/21 and MODIS to 2026-11-16, **S-NPP NRT ends 2026-11-02**. Punjab+Haryana box: MODIS SP 2019-11-05 = **306** (11:11–14:25 IST); **S-NPP SP 2024-11-05 = 0** |
| T5 CAMS ADS | **FAIL** (licence) | HTTP 403 "required licences not accepted" |

### 2.2 Follow-up tests T2b / T4a2 / T4b2 / T5, run by Mayank on Colab (17 Nov 2026, 02:18 IST)
- **Notebook:** `saans_phase2b_followup.ipynb`.
- **Files:** `phase2b_results.json`, `openaq_delhi_pm25_locations.csv` (analysed by Claude with pandas).

**T2b — weather variables in the Historical Forecast archive, Delhi, 1–7 Nov (share of 168 h non-null)**

| Model | 2022: mixing height | 2022: T2m / T850 / wind / RH / SW / low cloud | 2024: mixing height | 2024: others |
|---|---|---|---|---|
| best_match | 0 | 1 / 1 / 1 / 1 / 1 / 1 | **1** | all 1 |
| gfs_seamless | 0 | 1 / 1 / 1 / 1 / 1 / 1 | **1** | all 1 |
| gfs_global | 0 | 1 / 1 / 1 / 1 / 1 / 1 | **1** | all 1 |
| ecmwf_ifs | 0 | 1 / **0** / 1 / 1 / 1 / 1 | **1** | T850 = 0, others 1 |
| ecmwf_ifs025 | 0 | all 0 | 0 | others 1 |
| icon_seamless | 0 | all 0 | 0 | others 1 |
| jma_seamless | 0 | 1 / 1 / 1 / 1 / **0** / 1 | 0 | SW = 0, others 1 |
| gem_seamless | 0 | all 0 | 0 | others 1 |
| cma_grapes_global | 0 | all 0 | 0 | others 1 |

- Previous Runs API: HTTP 400 for every model. **Cause: a bug in Claude's request** (`temperature_850hPa_previous_day1`; a pressure-level variable with a previous-day suffix fails the whole request) → re-test T2c.

**T4a2 — OpenAQ, 95 PM2.5 locations within 25 km of central Delhi** (run 02:18 IST)
- `isMonitor = True`: 79. **Active in the last 24 h: 63.**
- Active by provider: CPCB 48, N/A 8, AirGradient 6, AirNow 1. **caaqm 0 of 21** (all dead, last data 1,478–3,111 days ago); CPCB 9 inactive (old IDs, e.g. DTU id 13, ITO "Income Tax Office" id 103, Mandir Marg id 236).
- **Active agency stations** (by name suffix): 56 (DPCC 27, IMD 9, UPPCB 9, CPCB 6, IITM 3, HSPCB 2).
- 8 active agency stations have `isMonitor = False` (IIT Delhi IITM, Talkatora Garden, JNU, Commonwealth Sports Complex, IGNOU Maidan Garhi, Cantonment Area, Khora, Ved Vihar-Loni).
- **Age of the latest value:** 168.9 min for 47 of 48 active CPCB-provider stations (one at 183.9). AirGradient 48.9 min; AirNow 738.9 min. Mean 168.7, min 48.9, max 738.9.
- Two locations without `datetimeLast`: IGI Airport (id 15), Civil Lines (id 16).
- **Co-located active pair:** Pusa IMD (id 5404) and Pusa DPCC (id 6356) report identical coordinates (28.6396, 77.1463) → series check in the build phase.

**T4b2 — FIRMS fires in the Punjab + Haryana box on 5 November (count / FRP sum, MW)**

| Sensor | 2023 | 2024 | 2025 |
|---|---|---|---|
| MODIS_SP | 677 / 12,348 | 239 / 3,066 | 14 / 533 |
| VIIRS_SNPP_SP | 3,592 / 24,633 | **0** | 357 / 1,567 |
| VIIRS_NOAA20_SP | 2,209 / 15,880 | 344 / 1,909 | 233 / 1,232 |
| VIIRS_NOAA21_SP | 2,823 / 20,212 | 483 / 3,221 | 198 / 1,263 |

- NRT last 2 days (16–17 Nov 2026): NOAA-20 691, NOAA-21 487, MODIS 671.
- VIIRS detection times span about 07:24–21:47 UTC (12:54–03:17 IST, i.e. day + night passes).

**T5 — CAMS ADS archive: PASS**
- Request: 2024-11-10, 00 UTC run, leads 0–72 h every 3 h, PM2.5 + PM10, area N29.2 W76.8 S28.2 E77.8.
- Result: 38,745 bytes; **41.2 s including queue** (accepted → running → successful); file `data_sfc.nc`; dims forecast_period 25 × reference_time 1 × lat 3 × lon 3; variables `pm2p5`, `pm10`; **units kg m⁻³**.

**Conclusions from 2.2:**
1. GFS pinned (D-027).
2. Mixing-height ablation (D-012).
3. ADS is the as-issued CAMS source (D-013).
4. CPCB data reaches OpenAQ about 2 h 50 min late → M7 redefined, delay simulated in training (D-028).
5. OpenAQ station rules (D-011).
6. S-NPP excluded (D-015).

### 2.3 T1 from Mayank's laptop + T2c (17 Nov 2026, 02:52 IST)
**T1 — CPCB from an Indian IP** (runner: Bharti Airtel, Haryana, country IN)
- `POST /dataRepository/all_india_stationlist` → **HTTP 404 in 0.1 s**. The server answered immediately.
- Compare with Singapore (Google cloud): TCP connect timeout after 60 s.
- **Conclusions:**
  - (1) CPCB **answers Indian IPs and drops foreign cloud IPs**, so cloud runners cannot use CPCB (D-011 live = OpenAQ).
  - (2) The undocumented endpoint used by `Vonter/india-cpcb-aqi/fetch.py` **no longer exists at that path**, so the history download method must be rediscovered (build phase B1) → DATASETS T-17.
- T2/T3 re-ran from India with the same results as from Singapore.

**T2c-A — GFS (`gfs_seamless`) mixing height in the Historical Forecast archive** (share of 1–7 of each month non-null)
- Nov 2022 → Aug 2024: **0.0** every month.
- **Sep 2024: 0.76**; Oct 2024: 1.0; Nov 2024: 1.0.
- So the archived mixing height **starts in the first week of September 2024**.

**T2c-B — Previous Runs API (forecast as issued 1 and 3 days earlier), Delhi, 1–7 Nov of each year** (share non-null; identical for day 1 and day 3)

| Variable | GFS 2022 | GFS 2023 | GFS 2024 | GFS 2025 | ECMWF-0.25 2022/23 | ECMWF-0.25 2024/25 |
|---|---|---|---|---|---|---|
| temperature_2m | **1** | **1** | 1 | 1 | 0 | 1 |
| wind_speed_10m | 0 | 0 | 1 | 1 | 0 | 1 |
| relative_humidity_2m | 0 | 0 | 1 | 1 | 0 | 1 |
| shortwave_radiation | 0 | 0 | 1 | 1 | 0 | 1 |
| cloud_cover_low | 0 | 0 | 0 | 0 | 0 | 0 |
| boundary_layer_height | 0 | 0 | 0 | 0 | 0 | 0 |
| temperature_850hPa | HTTP 400 (pressure levels not supported with `_previous_dayN`) | ← | ← | ← | ← | ← |

- `best_match` = same pattern as GFS.
- **Conclusions:**
  - Weather **as issued at a known lead time** exists for the core surface variables (T2m, 10 m wind, RH, shortwave) **only from Nov 2024**; T2m back to 2022.
  - Low cloud, mixing height and T850 are **not** available lead-exact at all.
  - The stitched Historical Forecast (short lead) has all of them from 2022, except mixing height (from Sep 2024).
  - → D-012 amendment (test-honesty rule) and v1 feature list (D-029).

### 2.4 B0 repo skeleton (17 Nov 2026, 03:55 IST)
- **What was built:** monorepo `aagahi` (one commit, `cff6da2`).
  - `pipeline/`: uv package with a Typer CLI (`version`, `check-config`, `aqi`; `ingest`/`forecast`/`publish` say which build phase adds them).
  - `aagahi.aqi`: PM-based Indian NAQI. Severe-band upper breakpoint is marked provisional until checked against the CPCB document in B1.
  - `aagahi.units`: kg/m³ → µg/m³ conversion, with a check for values that were never converted (T-14).
  - `aagahi.config`: loads `configs/delhi-ncr.yaml` and rejects `best_match` (D-027), VIIRS S-NPP (D-015b), duplicate station IDs and bad coordinates.
  - `configs/delhi-ncr.yaml`: 56 agency stations active on OpenAQ (DPCC 27, IMD 9, UPPCB 9, CPCB 6, IITM 3, HSPCB 2); `cpcb_id` left empty for the B1 crosswalk.
  - Plus `docs/` (all six md files + diagram), `notebooks/phase2/`, README, MIT LICENSE, .gitignore (data, models and secrets never committed), `.env.example`, GitHub Actions CI.
- **Results (fresh clone, Python 3.12.3):** ruff lint clean; format check clean; **24/24 tests pass** (0.28 s); `aagahi check-config` OK.
  - Example check: `aagahi aqi --pm25 180 --pm10 300` → AQI 346 · Very Poor (99/129 × (180−121) + 301 = 346.3 ✓).
- **Not yet done:** the push to GitHub. Mayank creates an empty public repo `aagahi`, then Claude attaches and pushes it, or Mayank uploads the zip.

