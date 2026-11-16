# DATASETS.md — Saans data sources, facts and traps

Every source Saans may use, with what was **verified** (and how), what is still **pending**, and the traps found. A source enters the build only after its smoke test passes (results in OUTPUTS.md §2).

Status: **VERIFIED** (checked against docs or data) · **PARTLY VERIFIED** (works, with a measured gap) · **PENDING TEST** (waiting for a test) · **REJECTED** (with reason)

Last updated: 17 Nov 2026 03:05, after all Phase 2 tests (OUTPUTS §2.1–2.3).

## 0. Status
| Source | Status | One-line result |
|---|---|---|
| S1 CPCB repository | **REACHABLE FROM INDIA ONLY; ENDPOINT MOVED** | Singapore cloud = timeout; Indian home IP = instant HTTP 404 on the old endpoint → rediscover in B1 |
| S2 / S3 mirrors | VERIFIED | Hourly AQI 2017–2023 measured; 15-minute files 2024–25 listed |
| S4 OpenAQ | **VERIFIED** | Works from cloud; 56 active agency stations ≤ 25 km; CPCB data about 2 h 50 min old on arrival |
| S7 Open-Meteo live | VERIFIED | Mixing height 100% |
| S8 Open-Meteo archives | **PARTLY VERIFIED** | Historical Forecast (stitched): GFS proxies 2022+, mixing height from Sep 2024. Previous Runs (lead-exact): T2m 2022+, wind/RH/shortwave from Nov 2024; low cloud, mixing height, T850 never |
| S9 ERA5 | VERIFIED | Mixing height 100% (analysis only) |
| S10 CAMS via Open-Meteo | **PARTLY VERIFIED** | Live + history from Aug 2022 OK; **no as-issued values** |
| S11 CAMS ADS | **VERIFIED** | 1 day, leads 0–72 h, 41 s incl. queue; kg m⁻³ |
| S13 FIRMS | **VERIFIED** | NOAA-20/21 + MODIS reliable; **S-NPP excluded** (NRT ended; archive gap on 2024-11-05) |

---

## 1. Ground truth: what the stations measured

### S1 — CPCB Data Repository (official, 15-minute raw data) · PRIMARY FOR HISTORY · INDIA-ONLY, ENDPOINT TO REDISCOVER
- **T1 from Mayank's laptop (17 Nov 2026, Airtel, Haryana, IN):** `POST /dataRepository/all_india_stationlist` → **HTTP 404 in 0.1 s**. So the server answers Indian IPs (vs a timeout from Singapore), but the old undocumented path has moved → T-17.
- **B1 step 1:** capture the real request with Chrome DevTools → Network while downloading one station-year by hand; record it here. Fallbacks: OpenCity (S3, Public Domain) → Vonter releases (S2, ODbL, private use) → manual downloads (D-011 amendment).
- **What:** CPCB's CCR portal, Data Repository section. One file per station per year, 15-minute averages of PM2.5, PM10, NO, NO₂, NOx, NH₃, SO₂, CO, O₃, benzene/toluene/xylene, plus on-site weather (AT, RH, WS, WD, RF, SR, BP). Hourly AQI is in the separate AQI Repository.
- **Access:** no key. The portal's backend endpoints (`/dataRepository/all_india_stationlist`, `/file_Path`, `/download_file`) take base64-encoded JSON. They are undocumented; the method is copied from the open-source `Vonter/india-cpcb-aqi/fetch.py` (read 17 Nov 2026).
- **T1 (17 Nov 2026, Google LLC, Singapore):** `ConnectTimeout` after 60 s at TCP connect, consistent with foreign IPs being dropped or the site being down. **Laptop run decides** (D-011).
- **Coverage (measured on the S2 mirror, 2017–2023):**
  - **39 Delhi stations.** Earliest from Jan 2017; most DPCC stations from Feb 2018; IITM Lodhi Road / Chandni Chowk from Nov 2020.
  - **NCR ring (by station name):** Noida 6, Gurugram 4, Faridabad 4, Ghaziabad 3, Sonipat 1.
- **Network growth:** 45 of Delhi's **59** stations had missing hourly readings at Diwali 2026 (Outlook, 11 Nov 2026). The newer stations (e.g. IIT Delhi, JNU, Talkatora Garden, Commonwealth Sports Complex, IGNOU, Cantonment, seen live in OpenAQ) have short histories → global model (D-021).
- **Licence:** government open data. Attribute CPCB.

### S2 — `Vonter/india-cpcb-aqi` on GitHub (mirror of S1) · BACKUP · VERIFIED
- 15-minute raw data as Parquet/CSV in GitHub Releases; hourly AQI in `data/cpcb-aqi.parquet`.
- **Licence:** ODbL 1.0 (attribution + share-alike). **Not used for the published data lake** (D-019).
- **Measured:** hourly AQI file = 15.6 MB, 562,878 station-days, **2017-01-01 → 2023-12-31**.
- **Trap:** the `Station ID` column is wrong (all 39 Delhi stations share `site_115`) → T-9.

### S3 — OpenCity "Delhi Hourly Air Quality Reports" · BACKUP · VERIFIED (listing only)
- data.opencity.in mirrors CPCB data: hourly data for 39 Delhi stations 2017–2023, plus per-station 15-minute files for 2024–25. Listed as **Public Domain**. Resources created Jan 2026.

### S4 — OpenAQ API v3 · LIVE SOURCE FOR CLOUD JOBS · VERIFIED (T4a, T4a2)
- **Access:** free API key; limit **60 requests/minute** (header-confirmed), 2,000/hour (docs).
- **Measured (17 Nov 2026, from Singapore), within 25 km of central Delhi:**
  - 95 PM2.5 locations; **63 active in the last 24 h**; **56 active agency stations** (DPCC 27, IMD 9, UPPCB 9, CPCB 6, IITM 3, HSPCB 2) + AirGradient 6 + AirNow 1.
  - **All 21 "caaqm" IDs are dead** (last data 1,478–3,111 days ago); 9 old "CPCB" IDs are dead too → T-16.
  - **CPCB-origin data arrives in one batch, about 168.9 min (≈ 2 h 50 min) after the measured hour** (47 of 48 active CPCB-provider stations) → T-13.
  - `isMonitor` is False for 8 active agency stations → T-16.
  - Pusa IMD and Pusa DPCC share identical coordinates.
  - IGI Airport (id 15) and Civil Lines (id 16) have no `datetimeLast`.
- **Licence:** set per source; CPCB-origin data carries no licence field → attribute CPCB.

### S5 — data.gov.in "Real time Air Quality Index from various locations" · REJECTED
- On 17 Nov 2026 the resource page said "The API for this resource does not exist" (last updated 24/04/2025).

### S6 — CPCB live dashboard / Sameer app · CONTEXT ONLY
- Known outages: 10 Nov 2025 (no updated AQI for Delhi); Diwali 2026 blank hours (T-1).

---

## 2. Weather (inputs)

### S7 — Open-Meteo Forecast API (live) · PRIMARY · VERIFIED (T2)
- No key. `boundary_layer_height` 100% over 120 h (measured).
- **Free-use terms:** non-commercial only; < **10,000 calls/day, 5,000/hour, 600/minute**; **CC BY 4.0**.
- **Pinned model: `gfs_seamless`** (D-027).

### S8 — Open-Meteo Historical Forecast + Previous Runs (training) · PARTLY VERIFIED (T2, T2b)
- **Historical Forecast, Delhi, 1–7 Nov (T2b):**
  - **GFS (`gfs_seamless`/`gfs_global`) and `best_match`:** T2m, T850, 10 m wind, RH, shortwave, low cloud **100% in 2022 and 2024**; mixing height **0% in 2022, 100% in 2024**.
  - ECMWF IFS (9 km): mixing height 100% in 2024 but **no T850** in either year.
  - ECMWF IFS 0.25°, ICON, GEM, CMA: no 2022 archive at all.
  - JMA: no shortwave.
- **Mixing height start (T2c-A, GFS):** 0% every month Nov 2022–Aug 2024 → **Sep 2024 76%** → Oct/Nov 2024 100%.
- **Previous Runs API** (forecast as issued 1/3 days earlier; T2c-B, 1–7 Nov each year):
  - GFS T2m 100% from 2022;
  - GFS wind 10 m, RH and shortwave **0% in 2022–2023, 100% from 2024**;
  - low cloud and mixing height 0% in all years;
  - pressure levels (T850) → HTTP 400 (not supported with `_previous_dayN`);
  - ECMWF-0.25: nothing before 2024, then the same pattern as GFS.
- **Consequence:** lead-exact weather for honest testing exists from Nov 2024 (D-012 amendment, D-029).
- Single Runs API: exact runs by start time; ECMWF IFS from March 2024, other models from April 2026 (docs).

### S9 — Open-Meteo Historical Weather API (ERA5 / IFS reanalysis) · LIMITED USE · VERIFIED (T2)
- Mixing height 100% for 1–7 Nov 2017. **Analysis only** (T-3).

---

## 3. Physics-model air-quality forecast (baseline + input)

### S10 — Open-Meteo Air Quality API, CAMS global domain · LIVE · PARTLY VERIFIED (T3)
- **Docs:** 0.4° (~45 km), 3-hourly, from August 2022, updated every 12 h, 5-day forecast.
- **Measured:** live 288 h, PM2.5 93.8% non-null; history from the week of 1 Aug 2022 (54% filled), Nov 2022 and Nov 2023 100%.
- **No as-issued values** (`pm2_5_previous_day1` 0%) → used **live only** (+ our own archive), with a parity test against ADS (D-013).

### S11 — Copernicus ADS, `cams-global-atmospheric-composition-forecasts` · BASELINE + TRAINING ARCHIVE · VERIFIED (T5)
- Free account + licence acceptance (T5 first failed with 403 until the licence was accepted).
- **Measured:** 2024-11-10, 00 UTC run, leads 0–72 h every 3 h, PM2.5 + PM10, 1° box → **38,745 bytes, 41.2 s including queue**; NetCDF `data_sfc.nc`; dims forecast_period 25 × reference_time 1 × lat 3 × lon 3; variables `pm2p5`, `pm10`; **units kg m⁻³** → T-14.
- ADS shows a "Data Stores Service protection measures" notice (2026-10-06); the backfill logs queue times (D-013).

### S12 — AQEWS official forecast (IITM) · COMPARISON ONLY · PENDING
- No public download or API found. Comparisons use CEEW's published scores at city level.

---

## 4. Fire activity (driver)

### S13 — NASA FIRMS (MODIS + VIIRS active fires) · INPUT WITH KNOWN BIAS · VERIFIED (T4b, T4b2)
- Free MAP_KEY; **5,000 transactions per 10 minutes** (confirmed); each day in a request counts as one transaction.
- **Availability (17 Nov 2026):**

| Product | From | To |
|---|---|---|
| MODIS_SP | 2000-11-01 | 2026-08-31 |
| MODIS_NRT | 2026-09-01 | 2026-11-16 |
| VIIRS_SNPP_SP | 2012-01-20 | 2026-07-31 |
| VIIRS_SNPP_NRT | 2026-08-01 | **2026-11-02 (stream ended)** |
| VIIRS_NOAA20_SP | 2018-04-01 | 2026-07-31 |
| VIIRS_NOAA20_NRT | 2026-08-01 | 2026-11-16 |
| VIIRS_NOAA21_SP | 2023-03-01 | 2026-07-31 |
| VIIRS_NOAA21_NRT | 2024-01-17 | 2026-11-16 |
| GOES_NRT | 2022-08-09 | 2026-11-16 (does not cover India) |

- **Fires on 5 November, Punjab + Haryana box (count):**

| Sensor | 2023 | 2024 | 2025 |
|---|---|---|---|
| MODIS | 677 | 239 | 14 |
| VIIRS S-NPP | 3,592 | **0 (gap)** | 357 |
| VIIRS NOAA-20 | 2,209 | 344 | 233 |
| VIIRS NOAA-21 | 2,823 | 483 | 198 |

  FRP sums are in OUTPUTS §2.2.
- MODIS 2019-11-05: all 306 detections at 11:11–14:25 IST.
- **Key bias (T-4):** the polar orbits pass at about 10:30–13:30 and 22:30–01:30 IST, and farmers shifted burning to late afternoon:
  - ISRO: 13:30 → 17:00 IST, 2020–2024;
  - iFOREST: > 90% of large Punjab fires after 15:00 in 2025;
  - NASA (GEO-KOMPSAT-2A): mostly 4–6 pm.
- **Geostationary fire data** → v2 research.

---

## 5. Calendar and context
- **Festivals/holidays:** a dated Diwali table (2017 onward) checked against official holiday lists; public holidays; school vacations.
- **GRAP stage history:** CAQM orders (start/withdrawal dates per stage) for context and a possible "policy in force" feature.

---

## 6. Traps found (each must have a rule before modelling)

| ID | Trap | Evidence | Consequence if ignored | Rule |
|---|---|---|---|---|
| T-1 | **Extreme hours go missing:** CPCB's AQI method drops hourly PM above 999 µg/m³; 45 of 59 Delhi stations had gaps at Diwali 2026. | Outlook, 11 Nov 2026 | The model under-predicts severe days. | D-014 |
| T-2 | **Live feed outages** (Sameer silent 10 Nov 2025; portal slow; timed out from a cloud IP). | PTI 2025; CEEW 2021; T1 | Nothing shown on the days that matter. | D-011, M7 |
| T-3 | **Look-ahead leak through weather** (training on observed/reanalysis weather). | Open-Meteo docs | Offline scores look great, live accuracy collapses. | D-012 |
| T-4 | **Fire counts undercount, and the undercount grows each year.** | ISRO, iFOREST 2025, NASA; T4b/T4b2 | Drift; wrong explanations. | D-015 |
| T-5 | **Network changes:** 39 → 59 Delhi stations. | S2; Outlook 2026; OpenAQ list | Per-station models fail for new stations. | D-021 |
| T-6 | **Sensor and siting quality:** humidity inflates PM; drift; 25 stations non-compliant with siting rules. | Newslaundry 2025; CAG via IE | Some "pollution" is instrument behaviour. | Audit flags + humidity feature; stated limitation |
| T-7 | **Bad values:** 0, negative, 999-style fillers, flat repeats. | DataMeet (urbanemissions) | Garbage enters training. | Cleaning rules; counts in OUTPUTS |
| T-8 | **US EPA vs Indian NAQI scales.** | National Herald | Users compare the wrong scale. | Indian NAQI only, labelled |
| T-9 | **Mirror ID bug** in S2. | Measured | Stations silently merged. | Key by S1 IDs |
| T-10 | **Duplicate/retired station IDs in OpenAQ:** the same station under "CPCB" and "caaqm", or under an old and a new CPCB ID. | T4a2: all 21 caaqm + 9 old CPCB IDs dead | Double-counting, or training on dead IDs. | Active-in-24 h filter + hand-checked crosswalk (D-011) |
| T-11 | **Feature exists live but not archived** (mixing height: archived for GFS in 2024, not 2022). | T2, T2b | Train/serve skew. | Feature-availability rule + ablation (D-012) |
| T-12 | **A satellite stream can drop silently** (S-NPP NRT ended 2026-11-02; S-NPP archive had 0 fires on 2024-11-05 while other sensors saw 239–483). | T4b, T4b2 | The model reads "no fires" on a peak burning day. | S-NPP excluded; sensor-independent features (D-015) |
| T-13 | **Observation delay:** CPCB data reaches OpenAQ about 2 h 50 min after the measured hour. | T4a2 | A model trained as if the last hour is known performs worse live (hidden leak); "real-time" claims are false. | Delay simulated in training (D-028); two timestamps in the UI (M7) |
| T-14 | **Unit mismatch:** CAMS ADS gives kg m⁻³; stations and Open-Meteo give µg/m³. | T5 | Values off by 10⁹. A silent bug if a model "learns" around it. | One tested conversion function + range checks in data contracts |
| T-15 | **`best_match` changes model silently** (Open-Meteo picks per place and time). | Open-Meteo behaviour; T2b differences between models | The feature source differs between training and live. | Pin GFS (D-027) |
| T-16 | **OpenAQ metadata is unreliable:** `isMonitor` is False for 8 active agency stations; 2 locations lack `datetimeLast`. | T4a2 | Real stations dropped or wrong ones kept. | Classify by agency suffix + crosswalk (D-011) |
| T-17 | **Undocumented endpoints move:** the CPCB repository path used by an open-source downloader now returns 404. | T1 (laptop) | The history download silently breaks. | Rediscover from DevTools evidence; fallback mirrors; SHA-256 per file (D-011 amendment) |
| T-18 | **"Historical forecast" ≠ "forecast as issued at lead N":** the stitched archive is short-lead (more accurate than a real 48-h forecast); lead-exact data exists only from Nov 2024 for most variables. | T2c | Test scores look better than the live product will be. | Test-honesty rule: training may use stitched data, every reported score uses lead-exact inputs (D-012 amendment) |

---

## 7. Smoke tests (Phase 2 acceptance)
| Test | Source | Result |
|---|---|---|
| T1 | S1 CPCB | Cloud: timeout. **Laptop (India): HTTP 404 instantly** → India-only + endpoint moved |
| T2 / T2b | S7–S9 weather | Live + ERA5 pass; archives: GFS has every proxy in 2022 + 2024, mixing height only in 2024 |
| T2c | S8 detail | Done: mixing height from Sep 2024; lead-exact wind/RH/shortwave from Nov 2024, T2m from 2022 |
| T3 | S10 CAMS | Live OK; history from Aug 2022; no as-issued values |
| T4a / T4a2 | S4 OpenAQ | PASS; 56 active agency stations; about 2 h 50 min delay; retired IDs |
| T4b / T4b2 | S13 FIRMS | PASS; S-NPP gap → excluded |
| T5 | S11 ADS | **PASS** (after licence acceptance) |
