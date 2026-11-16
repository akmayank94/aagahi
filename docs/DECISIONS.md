# DECISIONS.md — Aagahi (working name until 17 Nov: Saans): explainable air-quality forecasting for Delhi-NCR

**Owner:** Mayank · **Started:** 17 Nov 2026 (night session) · **Product name: Aagahi** (D-010; "Saans" in older entries = the same project)
**Project type:** personal side project, no supervisor, no deadline. Built for real users and for the DS/DA resume.
**Purpose of this file:** a factual record of every design decision: what was decided, why, what evidence supports it, which alternatives were rejected, and how to defend it if a recruiter asks "why not X?". Nothing goes in §0 unless it was measured, run, or checked against a cited source. Same rules as DeepGuard and NIDS.
**Companion files:** DATASETS.md (data sources, traps, smoke tests) · TERMS.md (glossary) · OUTPUTS.md (measured results only) · ARCHITECTURE.md (system diagram + Miro guide) · ROADMAP.md (build phases + versions).
**Language rule (Mayank, 17 Nov 2026):** clear, simple English everywhere, in docs, UI and agent answers, from start to end. Hindi (v2) follows the same rule.

Status labels: **DONE** (implemented and verified) · **DECIDED** (agreed, not yet implemented) · **SUPERSEDED** (replaced, with the reason) · **PROPOSED** (suggested, waiting for Mayank) · **PENDING** (waiting on evidence)

---

## 0. Verified facts

### 0.1 The problem landscape (checked 17 Nov 2026)
- **Official forecast system:** Delhi's Air Quality Early Warning System (AQEWS) is run by IITM Pune with IMD and NCMRWF. It combines real-time observations, satellite aerosol data and predictions from two chemistry-transport models, and issues warnings and bulletins for the Delhi region. (ews.tropmet.res.in/about.php)
- **How well it forecasts (CEEW study "How Well Can Delhi Predict Air Quality?", reported 3 Oct 2025):**
  - "Very poor or worse" days (AQI > 300): caught 83 of 92 in 2023–24 and 54 of 58 in 2024–25.
  - Severe episodes (AQI > 400): caught only **1 of 15** in 2023–24 and **5 of 14** in 2024–25.
  - Mean absolute percentage error in 2024–25: **35% for PM2.5, 38% for PM10**.
  - The system **keeps under-predicting** pollution, which limits early action.
- **Source attribution today:**
  - IITM's Decision Support System (DSS) was added in 2021 to estimate how much each sector and region contributes to Delhi's PM2.5.
  - It uses outdated emission inventories (2016 for NCR districts, 2018 for Delhi) and runs only in winter.
  - **CAQM stopped using the DSS for decisions in December 2024** because of the outdated data.
- **GRAP (Graded Response Action Plan), the policy that acts on forecasts:**
  - Four stages: I = AQI 201–300, II = 301–400, III = 401–450, IV = above 450 (as reported in Nov 2025).
  - CAQM's sub-committee invokes or withdraws stages from AQI trends **and weather/AQI forecasts**, and can apply higher-stage actions in advance when pollution is projected to worsen.
  - The schedule was revised on 21 Nov 2025 to move several measures to earlier stages.
- **Monitoring network:**
  - 39 Delhi stations in the 2017–2023 CPCB data (measured, DATASETS.md S2).
  - **59 Delhi stations** by Nov 2026: CPCB said 45 of Delhi's 59 had missing hourly readings at Diwali 2026 (Outlook, 11 Nov 2026).

**What this means for Saans:** the gap is not "showing the AQI", which many apps do. The gaps are:
- (1) forecasts that miss severe episodes;
- (2) no up-to-date, year-round explanation of **why** the air is bad;
- (3) no station-level forecast with an honest measure of uncertainty.

### 0.2 Free LLM facts (checked 17 Nov 2026)
- **Groq free tier, gpt-oss-120b:** 30 requests/min, 1,000 requests/day, 8,000 tokens/min, 200,000 tokens/day. Limits are set per model.
- **Gemini free tier:** covers the Flash class and the embedding models. Pro models became paid-only in 2026.
- Free-tier limits change without notice. The design must assume any one provider can drop or throttle us, so an LLM fallback chain and caching are mandatory (D-024).

### 0.3 Data facts (Phase 2, 17 Nov 2026; evidence in DATASETS.md, measurements in OUTPUTS.md §2)
- **Ground truth:**
  - The official CPCB Data Repository serves per-station, per-year **15-minute** files of all pollutants plus on-site weather, through undocumented endpoints.
  - **From a Google cloud server in Singapore it timed out at TCP connect (T1).**
  - **From an Indian home IP it answered in 0.1 s, but with HTTP 404**: the server accepts Indian IPs and drops foreign cloud IPs, and the old undocumented endpoint path no longer exists (OUTPUTS §2.3).
  - The ODbL mirror of the hourly AQI covers 2017-01-01 → 2023-12-31 for 39 Delhi stations (measured).
- **Live observations, OpenAQ v3 (T4a/T4a2):**
  - Works from foreign cloud servers.
  - Within 25 km of central Delhi: 95 PM2.5 locations, **63 active in the last 24 h**, of which **56 are agency stations** (DPCC 27, IMD 9, UPPCB 9, CPCB 6, IITM 3, HSPCB 2).
  - **All 21 "caaqm" locations are dead** (last data 4–8.5 years ago), and 9 old "CPCB" location IDs are also dead. These are retired IDs, not live duplicates.
  - **The latest CPCB-origin value is 168.9 min old for 47 of 48 active CPCB-provider stations**, i.e. observations arrive about **2 h 50 min late**, in one batch.
  - OpenAQ's `isMonitor` flag is wrong for 8 active agency stations (they show False).
  - Pusa IMD and Pusa DPCC report identical coordinates.
- **Weather (T2/T2b):**
  - Open-Meteo: free for non-commercial use, < 10,000 calls/day, 5,000/hour, 600/minute, CC BY 4.0.
  - Historical Forecast archive, Delhi, 1–7 Nov:
    - **2022:** mixing height (`boundary_layer_height`) 0% for all 9 models tested. GFS (`gfs_seamless`, `gfs_global`) and `best_match` have 100% of T2m, T850, 10 m wind, RH, shortwave and low cloud. ECMWF IFS lacks T850; ICON/GEM/CMA/ECMWF-0.25 have no 2022 archive.
    - **2024:** mixing height 100% for `best_match`, `ecmwf_ifs`, `gfs_seamless`, `gfs_global`; 0% for the others.
  - **T2c:** GFS mixing height in the archive **starts in the first week of September 2024** (0% every month Nov 2022–Aug 2024; 76% Sep 2024; 100% Oct–Nov 2024).
  - **Previous Runs API (weather as issued 1 or 3 days earlier, T2c):**
    - GFS T2m 100% from 2022;
    - 10 m wind, RH and shortwave 100% **only from Nov 2024** (0% in 2022 and 2023);
    - low cloud and mixing height 0% in every year;
    - pressure-level variables (T850) not supported (HTTP 400).
    - ECMWF-0.25: nothing before 2024.
- **Physics baseline:**
  - CAMS global via Open-Meteo: 0.4° (~45 km), 3-hourly, history from August 2022; **no as-issued values** (0%).
  - **Copernicus ADS archive works (T5):**
    - one day, leads 0–72 h every 3 h, PM2.5 + PM10, over a 1° box around Delhi = 38.7 KB, a 3 × 3 grid, 41 s including the queue;
    - **units kg m⁻³** (× 10⁹ → µg/m³).
- **Fires (T4b/T4b2):**
  - NASA FIRMS: 5,000 transactions per 10 min.
  - **VIIRS S-NPP is unreliable:** its near-real-time stream ended 2026-11-02, and its archive has **0 fires on 2024-11-05**, while NOAA-20 (344), NOAA-21 (483) and MODIS (239) all saw fires that day.
  - Fires on 5 November, Punjab + Haryana box:
    - NOAA-20: 2,209 (2023) → 344 (2024) → 233 (2025);
    - NOAA-21: 2,823 → 483 → 198;
    - MODIS: 677 → 239 → 14.

    These are single days, so anecdotal, but consistent with both real decline and the detection-timing shift.
  - Counts are biased and drifting: peak burning moved from 13:30 to 17:00 IST, 2020→2024 (ISRO); > 90% of large Punjab fires after 15:00 in 2025 (iFOREST).
- **Extreme-hour gaps:** CPCB's AQI method drops hourly PM above 999 µg/m³, so severe hours go missing.
- **Rejected:** the data.gov.in real-time AQI API (the resource page says no API exists).

### 0.4 Platform facts for the stack (checked 17 Nov 2026)
- **GitHub Actions:**
  - Free for standard runners in **public** repositories; public-repo Linux runners are **4 vCPU / 16 GB RAM / 14 GB SSD** (private: 2 vCPU / 8 GB).
  - **Scheduled workflows are disabled after 60 days without repository activity**, and the `schedule` trigger can be delayed under load.
  - The documented community fix: an external cron calling `workflow_dispatch` / `repository_dispatch`. cron-job.org is free, with a 1-minute minimum interval.
- **Vercel Hobby:**
  - Free, **personal non-commercial use only**.
  - Monthly: about 100 GB transfer, 1M edge requests, 1M function invocations, 4 active-CPU hours; function max duration 300 s.
  - Blob storage: 1 GB with only 10,000 reads per month, so it is **not suitable for serving data to visitors**.
  - Vercel Cron on Hobby runs once a day only.
- **Cloudflare R2:** 10 GB-month, 1M writes, 10M reads/month free, zero egress. **Needs a payment method on file before the first bucket.**
- **Hugging Face Hub:**
  - Free dataset/model repos; DeepGuard facts: 100 GB private storage on free accounts.
  - Commits are rate-limited: about 128/hour on the free plan (third-party report, Sep 2026; HF docs confirm commit limits exist).
  - API rate limits use 5-minute windows (free user: 1,000 API / 5,000 resolver requests per window, Sep 2025 figures).
- **Upstash Redis free:** 256 MB, 500,000 commands/month, 1 database.
- **OpenFreeMap:** free MapLibre vector tiles and styles, no API key; provided "as-is", may change.
- **Chronos-2** (Amazon, Oct 2025): pretrained time-series model with zero-shot univariate, multivariate and **covariate-informed** forecasting; **Apache-2.0** (pip `chronos-forecasting`). By Oct 2026 several foundation models accept covariates (TimesFM-3, TiRex-2, Toto 2.0, Timestral), so licence and context length are the deciding factors.

---

## 1. Decision log

### D-001 — Project idea: Saans · DECIDED 2026-11-17
Explainable, probabilistic air-quality forecasting for Delhi-NCR with a grounded AI agent and a public accuracy scoreboard.

**Candidates compared (17 Nov 2026):**
- **A. Saans (chosen).**
- **B. Bharat Data Copilot:** an AI analyst over Indian government open data.
- **C. Paisa Lens:** in-browser bank/UPI statement analytics.

**Why A:**
- **Depth on both sides.** It has real data-science depth (forecasting, measured against a public physics-model baseline) and real AI depth (an agent grounded in tool outputs).
- **Alive and timely.** The data is live, so the deployed link changes every day, and the problem is in the news every November.
- **Fills the portfolio gap.** Mayank's other projects are computer vision (DeepGuard), graph ML for security (NIDS) and business analytics (Coupon ROI, Complaint Intelligence).
- **Room to grow:** more cities, alerts, neighbourhood-level estimates, policy what-ifs, a public API.

**Why not B:** government data is messy, the idea sits close to the crowded "chat with your data" space, and it is harder to make visually striking.

**Why not C:** expense trackers are common, bank statement formats are fragmented, and it overlaps with the coupon project's fintech angle.

### D-002 — Geography for v1: Delhi-NCR only · DECIDED 2026-11-17
- **Reason:** depth beats breadth. Delhi-NCR has the most severe problem, dense monitoring, and an official forecast (AQEWS) whose published accuracy we can compare against.
- Other cities come in v2 through the same pipeline (a city is a config file, not new code; D-025).

### D-003 — Problem statement · DECIDED 2026-11-17 (approved by Mayank)
> People in Delhi-NCR make daily decisions around air quality: outdoor exercise, children's play, school activities, commuting, caring for elderly or asthmatic family members. Existing tools show the current AQI, or give a city-level forecast that under-predicts severe days (official system: 5 of 14 severe episodes caught in 2024–25) and does not say *why*. **Saans gives a 72-hour, station-level forecast of PM2.5, PM10 and AQI, with the probability of crossing each AQI category, an explanation of what is driving it (crop fires, wind, low mixing height, festivals, traffic), and personal advice. It publishes its own accuracy every day against the official and global models.**

**The five questions Saans must answer** (every feature has to serve one of them):

| # | User question | Saans answer |
|---|---|---|
| Q1 | What will the air be at my place in the next 72 hours? | Station-level hourly forecast, PM2.5 / PM10 → AQI |
| Q2 | How sure are you? | Forecast range (quantiles) + probability of crossing each category (e.g. "62% chance of Severe tomorrow") |
| Q3 | Why? | Driver breakdown from model explanations: fires, wind, mixing height, humidity, time and festival effects |
| Q4 | What should I do? | Advice by profile (child, elderly, asthma, runner, outdoor worker) + the cleanest hours of the day |
| Q5 | Why should I trust you? | Public scoreboard: our error vs persistence, the global model (CAMS) and the official forecast where comparable |

### D-004 — Users (personas) · DECIDED 2026-11-17 (order confirmed by Mayank)
| Priority | Persona | Main need | Main questions |
|---|---|---|---|
| P1 | **Parent / everyday resident** | "Can my kids play outside tomorrow? Should I go for my morning walk?" | Q1, Q4 |
| P1 | **Sensitive groups and caregivers** (asthma, COPD, heart conditions, elderly, pregnancy) | Early warning, before symptoms start | Q1, Q2, Q4 |
| P2 | **Runners, cyclists, outdoor workers** | The cleanest time window today or tomorrow | Q1, Q4 |
| P2 | **Schools, RWAs, offices** | Plan outdoor events and work-from-home; likelihood of a GRAP stage | Q2, Q3 |
| P3 | **Journalists, students, researchers** | Why it's bad, trends, data access | Q3, Q5 (+ API/export) |

### D-005 — Predict pollutant concentrations, then compute AQI with the official formula · DECIDED 2026-11-17
**Decision:** models forecast hourly **PM2.5 and PM10** concentrations (µg/m³) per station. The AQI is computed from those forecasts with CPCB's official National AQI breakpoints and averaging rules. Other pollutants (NO₂, O₃, SO₂, CO) come in v2 if the data supports them. Note: in Delhi winters the AQI is mostly driven by PM.

**Why:** the AQI is a derived, non-linear index (the maximum of pollutant sub-indices, each on rolling averages). Predicting it directly:
- learns a broken, clipped target;
- hides which pollutant is responsible;
- cannot be re-used when the breakpoints change.

Predicting concentrations keeps the physics clean and the explanations honest.

**Recruiter defence:** "Why not predict AQI directly?" → "AQI is a piecewise-linear transform of rolling averages. Forecasting the underlying concentrations and applying the official formula is more accurate, more explainable and future-proof. That's how official systems report it too."

### D-006 — Success metrics and targets · DECIDED as a framework 2026-11-17; numbers frozen in build phase B1 (after the full history download and baseline measurement), before any model training
Mayank: "work for all needed first, then decide further"; the draft targets were not judged too ambitious.

**Forecast quality (the data-science core)**
- **M1 Point accuracy:** MAE of station PM2.5 at 24 h, 48 h and 72 h ahead. It must beat (a) persistence, (b) a seasonal-naive forecast, and (c) the raw CAMS forecast **as issued at the same lead time** (D-013).
  - Draft target: ≥ 15% lower MAE than raw CAMS at 24 h.
  - The improvement's bootstrap 95% interval must exclude 0.
- **M2 Severe-day detection:** hit rate and false-alarm ratio for "next-day city-average AQI > 400".
  - The official system's published reference is 5/14 ≈ 36% (2024–25).
  - Draft target: hit rate ≥ 60% with false-alarm ratio ≤ 40%, on the same seasons as far as data allows.
- **M3 Calibration:** for "probability of crossing a category", the Brier score must beat climatology. Reliability curve published. For forecast ranges: an 80% interval must actually contain the truth 75–85% of the time.
- **M4 Honest testing:** time-based splits only (train on the past, test on later seasons). Hold out the whole 2025–26 winter as the final exam. Every test run is logged in OUTPUTS.md.

**AI agent quality**
- **M5 Groundedness:** 100% of numbers in agent answers must trace back to a tool output, checked automatically on a test set of ≥ 100 questions.
- **M6 Refusal / uncertainty:** the agent says "I don't know" for questions outside its data (e.g. a city not covered) in ≥ 95% of test cases.

**Product**
- **M7 Freshness (clarified 17 Nov 2026 after T4a2):** a new forecast is published within **30 minutes** of new observations arriving at our source. The UI always shows two ages: "observations as of HH:MM" and "forecast issued HH:MM". When the feed is down, the app says so and shows the last valid forecast with its age.
  - *Why changed:* the source itself delivers CPCB data about 2 h 50 min late (OpenAQ, measured). Promising freshness relative to the measurement time would be impossible to keep; promising it relative to data arrival is honest and measurable.
- **M8 Speed:** first page load (LCP) ≤ 2.5 s on mid-range mobile over 4G; agent answer first token ≤ 3 s.
- **M9 Cost:** ₹0 per month at the expected traffic, using free tiers only.

### D-007 — v1 scope and non-goals · DECIDED 2026-11-17 (Hindi moved to v2 by Mayank; retraining cadence set by D-022)
**In v1:**
- Delhi-NCR CPCB stations.
- Hourly PM2.5 / PM10 → AQI, 72-hour horizon.
- Live map.
- A page per station.
- Driver explanations.
- Grounded agent chat in **clear, simple English**.
- Advice by profile.
- Public accuracy scoreboard.
- Automatic hourly data refresh and forecasting.
- Scheduled retraining with promotion gates (D-022).

**Not in v1 (planned for v2+):**
- **Hindi** UI and agent (same clarity rule).
- Other cities.
- WhatsApp / Telegram / push alerts.
- Low-cost sensor fusion and neighbourhood-level estimates.
- Geostationary fire data (D-015).
- Policy what-if simulator (beyond simple driver what-ifs).
- Public API and MCP server.
- Native mobile app.

**Never:**
- Medical diagnosis or treatment advice. Advice stays at the level of CPCB / WHO public health guidance, with a disclaimer.
- Presenting Saans as an official GRAP authority.

### D-008 — The AI rule: the LLM explains, it never invents numbers · DECIDED 2026-11-17
- Every number, category and driver the agent mentions comes from a tool call to Saans's own forecasts, explanations, observations or scoreboard.
- A validator checks every number in the answer against the tool outputs before it is shown. Failing answers are regenerated or replaced by a template answer.
- Same principle as DeepGuard D-009: "an LLM may rephrase but never decides".

**Recruiter defence:** "Isn't this just an LLM wrapper?" → "No. The forecasts come from trained, evaluated models. The LLM is the interface, and an automatic check proves it can't make up a number (M5)."

### D-009 — Architecture practice: Mayank builds the Miro board by hand · DECIDED 2026-11-17
- Claude draws the architecture as an image and guides Mayank step by step.
- Mayank rebuilds it on Miro himself and shares screenshots for review. No Miro connector.
- **Reason:** practising professional system-design diagramming is part of the learning goal.

### D-010 — Final product name: **Aagahi** · DECIDED 2026-11-17 03:21 (chosen by Mayank from the shortlist)
- Mayank (17 Nov 2026): "Saans" is self-explanatory, but many campaigns already use it, so the product gets a **different, more distinctive name**.
- Criteria for Phase 6:
  - short and easy to say in English and Hindi;
  - not already used by a government campaign or an existing air-quality app;
  - a free `.vercel.app` / GitHub / Hugging Face name is available;
  - hints at air, breath or foresight.
- "Saans" stays the internal working name in the docs until then.
- **Name research (17 Nov 2026, web search):**
  - **Rejected** for collisions:
    - "Hawa…": HawaHaal is a live Delhi-NCR AQI/GRAP app (released Jan 2026); True AQI's mascot is named Hawa.
    - "Vayu…": Clean Air Asia's VAYU app (2018); Rajasthan's RajVayu.
    - "Pran Vayu": Haryana's "Pran Vayu Devta" tree-pension scheme.
    - "Air-Pravah": MeitY air-quality app (2024).
    - "Smog…": many apps (Smog Report, Smog Alert…).
    - Also taken: Breezo, Airveda, AQI.in, SAFAR-Air, Sameer.
  - **Shortlist** (no air-quality product found under these names):
    - **Aagahi** (आगाही: "awareness; advance warning", Hindi/Urdu, from Persian; dictionary: Rekhta, Oxford Hindi-English via Wiktionary);
    - **AirAhead** (English);
    - **Agrim** (अग्रिम: "in advance"; also a common personal/company name, so weaker as a brand).
  - **Before final adoption (B0):** check that the GitHub repo, Hugging Face names and `<name>.vercel.app` are free.
- **UI directions:** 3 options on the Design canvas "Air-quality forecast app — 3 visual directions" (A Night Smog · B Almanac · C Breath); Mayank picks one.

### D-011 — Observation sources and ingestion fallback chain · DECIDED 2026-11-17 (updated with T1/T4a/T4a2)
**Decisions:**
- **History (training):**
  - The CPCB Data Repository 15-minute raw files (S1) are the single source of truth.
  - If CPCB is reachable only from Indian IPs (T1 from the laptop decides), the full history is downloaded **once from Mayank's laptop** and uploaded to the data lake (D-019).
  - The S2/S3 mirrors are used only to fill access failures, and every filled row is tagged with its source.
- **Live (hourly, in the cloud):**
  1. CPCB, if reachable from the runner;
  2. **OpenAQ v3**, proven from cloud IPs;
  3. no new observation → keep forecasting from weather + CAMS + the last valid observation, and show the data age in the UI (M7).
- **OpenAQ station rules (from T4a2):**
  - Keep only locations that were active in the last 24 h. This drops all 21 "caaqm" IDs and 9 retired "CPCB" IDs.
  - Identify agency stations by the agency suffix in the name (DPCC/CPCB/IMD/IITM/UPPCB/HSPCB), **not** by `isMonitor`, which is wrong for 8 active stations.
  - Map each OpenAQ location to its CPCB station ID through a hand-checked crosswalk table (name + coordinates), stored in `configs/`.
  - Co-located pairs (Pusa IMD / Pusa DPCC) are kept as separate stations only if their time series differ. Identical series → one station.
  - Low-cost sensors (AirGradient) are excluded from ground truth in v1 (v2 fusion source).
- 15-minute data is aggregated to hourly by our own documented rule (minimum valid quarters per hour), not taken from CPCB's pre-averaged hourly values, whose QA/QC rules are unclear.
- **Amendment from T1 (laptop), 17 Nov 2026, DECIDED (approved 03:05):**
  - CPCB answers Indian IPs only (T1: Singapore = timeout, India = instant reply), so **live ingestion in the cloud uses OpenAQ only**. CPCB is used only for history, from the laptop.
  - The old endpoint returned 404, so **build phase B1, step 1**: Mayank opens the CPCB Data Repository page in Chrome with DevTools → Network, downloads one station-year file by hand, and records the real request (URL, method, payload, headers) in DATASETS.md. Claude then rewrites the downloader from that evidence (a good reverse-engineering exercise).
  - **If no programmatic method works:**
    1. per-station 15-min files from the **OpenCity mirror (Public Domain, 2017–2025)**;
    2. the Vonter release files (ODbL, used only privately for training, never republished);
    3. manual downloads from the CPCB page for the remaining gaps.
  - Every file is tagged with its source and SHA-256 either way.

**Why:** the CPCB portal is often slow, has gone silent during the worst episodes (DATASETS T-2), and timed out from a foreign cloud IP (T1). A single source would fail on exactly the days that matter.

**Recruiter defence:** "Why not just scrape one API?" → "The official feed fails during severe episodes and isn't reachable from cloud runners. A fallback chain with source tags keeps the product alive and the training data auditable."

### D-012 — Train only on information available at forecast time · DECIDED 2026-11-17 (updated with T2/T2b)
**Decision:** model inputs use only information that would have existed at forecast time:
- weather from Open-Meteo's archived forecasts at the matching lead time (Previous Runs where available, else Historical Forecast; T2c decides);
- CAMS as issued (D-013);
- observations up to the issue time **minus the real data delay** (D-028).

Reanalysis (ERA5) is used only for analysis and for explaining past days.

**Feature-availability rule:** a feature is allowed **only if it exists both in the as-issued archive and in the live feed, from the same pinned model (D-027), for the whole training window.**

**Mixing height (T2b):** archived for GFS in Nov 2024 but **not** in Nov 2022, so it fails the rule for the 3-winter window. **Pre-registered ablation (build phase):**
- **(A)** 3 winters (2022–23 → 2024–25) with mixing proxies only: inversion strength T850 − T2m, 10 m wind, low cloud, shortwave, RH. All 100% in GFS for 2022 and 2024.
- **(B)** the winters where mixing height exists (start month from T2c), with mixing height + proxies.
- Both are judged on the same validation window. B is kept only if it beats A by ≥ 3% MAE at 24 h with a bootstrap interval excluding 0. More, older data vs one better feature is a real trade-off, decided by measurement.

The live mixing height may still be **shown** in the UI as context.

**Amendment from T2c (17 Nov 2026), DECIDED (approved 03:05): the test-honesty rule.**
- **Facts:**
  - weather *as issued at a known lead time* (Previous Runs API) exists for the core surface variables only from Nov 2024 (T2m from 2022);
  - the stitched Historical Forecast (short lead, better than a real 48-h forecast) has everything from 2022 except mixing height;
  - archived mixing height starts in Sep 2024.
- **Rule (1) Training** may use the stitched Historical Forecast for 2022–2024 (more winters), and Previous Runs from Nov 2024. Each training row records which archive and lead it came from.
- **Rule (2) Every reported test, validation and scoreboard number uses only lead-exact inputs:**
  - Previous Runs weather at the right lead;
  - ADS CAMS at the right lead;
  - the real data delay (D-028).

  So any optimism from short-lead training weather shows up as a *lower honest test score*, never as an inflated one.
- **Rule (3) Measured, not guessed:** on the 2024–25 validation winter, score the same model with stitched vs lead-exact weather and publish the gap (the "lead-mismatch penalty") in OUTPUTS. If the penalty is large, a model trained only on lead-exact data (Nov 2024 onward) is compared under the same pre-registered rule.
- **Mixing-height ablation (B above): dropped for v1.** Archived values start in Sep 2024, which leaves at most one training winter before the 2025–26 test. Mixing height re-enters in v2, when our own forecast archive (saved from day 1, D-013) holds two winters of it.

**Recruiter defence:** "Your weather archive isn't lead-exact before 2024. Isn't that leakage?" → "Training may use it; testing never does. Every number I report uses only what was knowable at issue time, and I measured how much the training mismatch costs."

**Why:** training on observed weather and predicting with forecast weather is a look-ahead leak (DATASETS T-3). Offline scores look excellent and live accuracy collapses.

**Recruiter defence:** "Why not use ERA5 or the mixing height like many papers do?" → "ERA5 is hindsight, and the mixing height isn't archived as-issued for the early winters. I ran a pre-registered ablation (more winters with proxies vs fewer winters with mixing height) instead of guessing."

### D-013 — The CAMS baseline (and CAMS input) must be lead-time exact · DECIDED 2026-11-17 (updated with T3/T5)
**Decision:**
- For each issue time and horizon (24/48/72 h), compare against the CAMS forecast issued at that same time for that lead.
- Open-Meteo has **no** as-issued CAMS (T3), so the **Copernicus ADS archive is the training and baseline source.**
- **T5 PASS:** one day = 38.7 KB, 41 s including the queue, a 3 × 3 grid over Delhi-NCR, PM2.5 + PM10 in **kg m⁻³** (converted × 10⁹ to µg/m³ in one tested function; DATASETS T-14).
- **Backfill plan:** request one month per call (00 and 12 UTC runs, leads 0–72 h); about 4 winters ≈ 25–50 calls; log the queue time per call.
- **Live serving:** Open-Meteo's latest CAMS run (as-issued by definition at that moment) plus our own **forecast archive**: every live run is saved from day 1.
- **Parity test:** for ≥ 14 overlapping days, compare the ADS and Open-Meteo CAMS values at each station for the same run and lead.
  - If the median absolute difference is ≤ 5%, Open-Meteo is used live.
  - If not, live also pulls from ADS (about 1 minute per request is acceptable for an hourly job).

**Why:** Open-Meteo's continuous history is stitched from the newest runs (short lead). Comparing our 24-h forecast with CAMS's 0–12-h forecast would be unfair, and feeding it as an input would leak future information.

### D-014 — Missing extreme hours are treated as information, not noise · DECIDED 2026-11-17
**Decisions:**
- **(a) Never fill gaps by interpolation across more than 2 hours, and never fill with averages.** LightGBM handles missing values natively (D-021).
- **(b) Use the raw 15-minute files.** If they contain values ≥ 999 µg/m³ that the AQI method dropped (T1 checks this), keep them, flagged `above_analyser_range`.
- **(c) Report how often gaps happen on high-pollution days compared with normal days.** If gaps are missing-not-at-random, evaluate severe-day metrics both on official AQI and on our raw-based AQI, and say which one the scoreboard uses.
- **(d) Training weights must not under-represent severe hours.** Checked by comparing the distribution of target values before and after cleaning.

**Why:** at Diwali 2026, CPCB's 999 µg/m³ rule blanked hours at 45 of 59 Delhi stations (DATASETS T-1). Dropping those hours teaches the model that bad days are milder: the same under-prediction the official system suffers from.

### D-015 — Fire features: use them, but never trust raw satellite counts as truth · DECIDED 2026-11-17 (updated with T4b/T4b2)
**Decisions:**
- **(a) Build upwind fire indices** from FIRMS: counts and fire radiative power, weighted by the forecast wind direction and distance to Delhi.
- **(b) Sensor-independent:**
  - combine VIIRS **NOAA-20 + NOAA-21** (and MODIS for long history);
  - normalise per sensor;
  - **exclude VIIRS S-NPP entirely**: its NRT stream ended 2026-11-02, and its archive returned 0 fires on 2024-11-05 while the other three sensors saw 239–483;
  - a missing sensor reduces coverage instead of breaking the feature, and its gap is flagged.
- **(c) Add CAMS's own aerosol forecast,** which includes satellite-based fire emissions (GFAS), plus the observed PM2.5/PM10 ratio as a smoke signal.
- **(d) Validate per season:** check that fire-feature importance and model error are stable year by year. 5-Nov counts fell about 6–14× from 2023 to 2025 across sensors (T4b2), so a drop that follows the burning-time shift is a known bias, not a discovery.
- **(e) Explanations say "satellite-detected fires"** and carry a short note that evening fires are undercounted.
- **(f) Geostationary fire data** (GEO-KOMPSAT-2A / Meteosat IODC / INSAT-3DS) → v2 research. FIRMS' GOES feed doesn't cover India.

**Why:** farmers moved burning after the polar satellites' overpass. FIRMS now sees a shrinking share of fires (DATASETS T-4). Raw counts would make the model and its explanations wrong in a way that gets worse every year.

**Recruiter defence:** "Why not just use fire counts?" → "Because ISRO, NASA and iFOREST all show the counts now miss most evening fires, and I measured a satellite dropping out of the archive on a peak burning day. Knowing the bias in your own data is what separates data science from model fitting."

---

### 1.1 Stack at a glance (Phase 3, DECIDED 17 Nov 2026; details D-016 to D-026)

| Layer | Choice | Free limit that matters | Main alternative rejected |
|---|---|---|---|
| Serving style | **Batch forecasts every hour + static-first web** (D-016) | — | Always-on model server |
| Data/ML language | **Python 3.12**, `uv`, ruff, pytest, pandera, Typer CLI (D-017/018) | — | — |
| Data processing | **Polars + DuckDB on Parquet** (D-018) | fits an 8 GB laptop and 16 GB runners | pandas-only; Spark |
| Data lake + model registry | **Hugging Face Hub** dataset + model repos (D-019) | ~128 commits/hour, we use ≤ 2 | Cloudflare R2 (needs a card), Vercel Blob (10k reads/month), Postgres |
| Scheduler + compute | **GitHub Actions** (public repo, 4 vCPU/16 GB) **triggered by cron-job.org** (D-020) | free, unlimited minutes for public repos | Airflow server, GitHub `schedule` alone, Vercel Cron |
| Weather model | **GFS (`gfs_seamless`), pinned** (D-027) | Open-Meteo 10k calls/day | `best_match` (silently switches models) |
| Forecast model | **Global LightGBM quantile model** (champion candidate) vs **Chronos-2** (challenger) + baselines (D-021) | runs on CPU | per-station ARIMA/Prophet, deep nets from scratch |
| Uncertainty | **Conformalized quantile regression** per horizon (D-021) | — | raw quantiles |
| Explanations | **SHAP TreeExplainer**, grouped into driver families (D-021) | — | permutation importance |
| MLOps | Weekly retrain + daily evaluation, promotion gate, champion on HF (D-022) | — | daily blind retrain |
| Web app | **Next.js (TypeScript) on Vercel Hobby**, Tailwind + shadcn/ui, **MapLibre + OpenFreeMap + deck.gl**, ISR caching (D-023) | non-commercial; 1M invocations | Streamlit/Gradio, Mapbox, Leaflet |
| AI agent | **Vercel AI SDK** tool-calling + number validator; Groq → Gemini → OpenRouter; **Upstash Redis** cache and rate limit (D-024) | Groq 1,000 req/day; Upstash 500K commands/month | LangChain/LangGraph, a Python agent on a sleeping host |
| Repo | Public monorepo `pipeline/` + `web/` + `docs/` (D-025) | — | separate repos |
| Quality | CI tests, data contracts, parity tests, agent eval, freshness status (D-026) | — | — |

**Monthly cost: ₹0.** No credit card needed anywhere in the v1 stack.

### D-016 — Serving style: hourly batch forecasting + static-first web · DECIDED 2026-11-17 (approved by Mayank)
**Decision:**
- Forecasts are computed **once per hour, for all stations, in a batch job**, not when a user asks.
- The job publishes small JSON artifacts: latest forecast per station, drivers, scoreboard, status.
- The website reads those artifacts through Vercel's edge cache. Only the agent chat runs code per request.

**Why:**
- Inputs (observations, weather runs) only change hourly, so computing per request adds cost and cold starts for nothing.
- Batch + CDN means ₹0, sub-second page loads (M8) and no server to keep alive.

**Rejected:** an always-on FastAPI model server. On free hosts it sleeps (cold starts of tens of seconds) or costs money.

**Recruiter defence:** "Why no model API?" → "The prediction inputs refresh hourly, so batch inference + CDN is the correct pattern: cheaper, faster and simpler. That's how most weather apps serve forecasts. A live endpoint would only add latency."

### D-017 — Languages: Python for data/ML, TypeScript for the product · DECIDED 2026-11-17
- **Python 3.12** for ingestion, features, training, evaluation and artifact publishing.
- **TypeScript** for the web app and the agent.
- **Why:** each language where its ecosystem is strongest; the industry norm for a data product with a modern web front.

### D-018 — Python tooling and data processing · DECIDED 2026-11-17
**Tooling:**
- **`uv`** for environments and a lockfile (fast, reproducible).
- **ruff** for lint and format; **pytest** for tests.
- **pandera** for data contracts (schema, ranges, uniqueness per station-hour).
- **Typer** for CLI steps (`saans ingest`, `saans features`, `saans forecast`, `saans publish`, `saans train`, `saans evaluate`).

**Processing:** **Polars** for transforms and **DuckDB** for SQL analytics, on **Parquet** files partitioned by source/year/month.

**Why:**
- The data is a few million station-hours, so it fits one machine.
- Polars and DuckDB are columnar and multi-threaded, and run comfortably on the 8 GB laptop and the 16 GB runners.
- Parquet is the standard open format for analytics.

**Rejected:**
- pandas-only: memory-heavy and slower at this size.
- Spark: a cluster tool, wrong for single-machine data.
- A database as the primary store: analytics on time series is columnar work.

**Recruiter defence:** "Why not Spark?" → "Spark solves data that doesn't fit one machine. Ours does. Polars and DuckDB give the same SQL/dataframe power without a cluster."

### D-019 — Storage: Hugging Face Hub as data lake, model registry and artifact store · DECIDED 2026-11-17
**Repos:**

| Repo | Contents | Write pattern |
|---|---|---|
| `<name>-data` (dataset, public) | `raw/` (CPCB 15-min, OpenAQ, FIRMS, CAMS-ADS, weather archives), `clean/`, `features/`, `forecast_archive/` (every live forecast we issue) | Daily batch commit |
| `<name>-models` (model, public) | Versioned models, `metrics.json`, model card, `CHAMPION` pointer file | Weekly (D-022) |
| `<name>-live` (dataset, public) | `latest/*.json` (forecast, drivers, scoreboard, status) | 1 commit per hour; history squashed weekly with `super_squash_history` |

**Why:**
- Free, versioned (every change is a git revision), and no card needed.
- Parquet-native dataset viewer; public datasets are themselves a portfolio asset with a dataset card.
- About 2 commits/hour is far below the reported ~128/hour cap.
- Mayank already uses HF (DeepGuard).

**Rejected:**
- **Cloudflare R2:** the technically ideal store (S3 API, zero egress), but it needs a payment method → **kept as the upgrade path**. Our storage layer goes through one interface (`fsspec`), so switching is a config change.
- **Vercel Blob:** 10,000 reads/month on Hobby is far too few for serving.
- **Supabase/Neon Postgres:** an OLTP database is the wrong tool for append-only analytical time series, and free tiers have size limits.
- **Committing data to GitHub:** bloats the repo.

**Licence note:** published data keeps its sources' terms: CPCB attribution, Open-Meteo/CAMS CC BY 4.0. We use S1 (official), not the ODbL mirror, for the published lake, to avoid share-alike obligations. Exact wording goes into the dataset card in Phase 7.

### D-020 — Scheduling and compute: GitHub Actions triggered by an external cron · DECIDED 2026-11-17
**Decisions:**
- **Public GitHub repo** → free standard runners at 4 vCPU / 16 GB.
- **cron-job.org** calls the GitHub `workflow_dispatch` API every hour. The minute is tuned from data: CPCB values reach OpenAQ in one batch about 2 h 50 min after the measured hour (T4a2), so the arrival minute is measured over a week before it is fixed.
- GitHub's own `schedule` trigger is kept only as a backup.
- **Workflows:**
  - `hourly.yml`: ingest → validate → features → forecast → publish → revalidate the website.
  - `nightly.yml`: evaluate yesterday's forecasts → update the scoreboard → drift report.
  - `weekly.yml`: retrain → gate → promote.
  - `ci.yml`: tests on every push.
- **Secrets** (OpenAQ, FIRMS, ADS, HF token, revalidation secret) live in GitHub Actions secrets.

**Why:**
- Free, close to the code, logs for every run.
- The external trigger avoids two documented problems: `schedule` delays, and schedules being disabled after 60 days without repo activity.
- Every step is a plain CLI command, so the pipeline is **orchestrator-agnostic**. Moving to Prefect/Airflow/Dagster later only means writing a new DAG file.

**Rejected:**
- Airflow: needs an always-on server.
- Vercel Cron: once a day on Hobby.
- Kaggle/Colab: not schedulable services.

**Risk:** if CPCB blocks foreign IPs, cloud runs use OpenAQ (D-011), already proven from cloud IPs.

### D-021 — Modelling approach · DECIDED 2026-11-17 (final model chosen by pre-registered experiment in the build phase)
**Baselines (must all be beaten, M1):**
- persistence;
- seasonal-naive;
- raw CAMS as issued;
- linear CAMS bias-correction (the classic "model output statistics" approach).

**Champion candidate:**
- **One global LightGBM model** across all stations: station ID and coordinates as features, so new stations work from day one (DATASETS T-5).
- Lead time as a feature; direct multi-horizon, 1–72 h.
- Targets: log1p(PM2.5) and log1p(PM10).
- **Quantile objectives** (p10/p50/p90).
- Missing values handled natively (D-014).

**Challenger:** **Chronos-2** (Apache-2.0), zero-shot with the same covariates, then fine-tuned if it is close.

**Selection rule (pre-registered):**
- Rolling-origin validation on the 2024–25 winter; test on 2025–26 **once**.
- Because explanations are a hard requirement (Q3), the challenger must beat the champion by **≥ 5% MAE at 24 h, with a bootstrap interval excluding 0**, to justify losing native per-feature explanations.

**Uncertainty:**
- Split-conformal calibration of the quantiles on a recent window, per horizon (conformalized quantile regression).
- Category probabilities come from the calibrated predictive distribution and are checked by Brier score and reliability curves (M3).

**Explanations:** SHAP TreeExplainer values, grouped into driver families shown to users:
- persistence / recent levels;
- CAMS physics;
- fires;
- wind and ventilation;
- inversion/mixing;
- humidity;
- calendar and festivals.

**Why LightGBM:**
- Gradient-boosted trees are the strongest standard choice for tabular forecasting with many external features.
- Fast on CPU, native quantile loss and missing-value handling, and exact, fast SHAP values.

**Rejected:**
- Per-station ARIMA/Prophet: weak with covariates; can't handle 59+ stations with short histories.
- LSTM/TFT from scratch: data-hungry for about three winters, needs a GPU, harder to explain.

**Recruiter defence:**
- "Why not deep learning?" → "I tested the strongest pretrained forecaster, Chronos-2, as a challenger under a pre-registered rule. The tree model had to be beaten by a margin worth losing explainability."
- "Why one model for all stations?" → "A global model shares patterns across stations and works for new stations, which matters because Delhi's network grew from 39 to 59."

### D-022 — MLOps: retraining, gates and registry · DECIDED 2026-11-17
**Cadence:**
- **Hourly** inference.
- **Nightly** evaluation of all issued forecasts against the observations that arrived, which feeds the public scoreboard, plus a drift report: feature distributions and error by station/horizon.
- **Weekly** retrain, or earlier if the drift alarm fires (rolling 7-day MAE > 1.3 × its 30-day median).

**Promotion gate:** a new model becomes champion only if all of these hold:
- (a) it beats the champion on the last 30 days of as-issued backtests at 24 h;
- (b) calibration coverage of the 80% interval stays within 75–85%;
- (c) data-contract checks pass;
- (d) no station's MAE gets worse by more than 15%.

Otherwise the champion stays and the reason is logged.

**Registry:** HF model repo revisions + a `CHAMPION` file + `metrics.json`. Every run records its git commit, data snapshot revision and seed (DeepGuard D-018.7 rule).

**Why not daily retraining:** one extra day adds little information, costs compute, and makes forecasts jumpy. A weekly cadence with drift-triggered retraining is the standard balance.

### D-023 — Web app stack · DECIDED 2026-11-17 (visual design in Phase 6)
**Stack:**
- **Next.js** (App Router, TypeScript) on **Vercel Hobby** (non-commercial, which matches the project).
- **Tailwind CSS + shadcn/ui** for components.
- **MapLibre GL JS** with **OpenFreeMap** vector tiles (no key).
- **deck.gl** layers for stations, fire hotspots and animated wind.
- Chart library chosen in Phase 6.

**Caching:**
- Pages read the `latest/` artifacts with **ISR** (incremental static regeneration).
- The hourly pipeline calls a secret `/api/revalidate` route after publishing, so pages refresh within seconds of new data and stay cached between runs.

**Analytics:** Vercel Web Analytics (privacy-friendly).

**Why:** full design control for a "cool, clean, eye-catchy" product, fast edge delivery (M8), and the same pattern as Mayank's existing flowgraph-nids.vercel.app.

**Rejected:**
- Streamlit/Gradio: quick, but limited design control and slow cold starts on free hosts.
- Mapbox: needs a key and billing.
- Leaflet: raster-first, no GPU layers for wind and fire animation.

### D-024 — AI agent stack · DECIDED 2026-11-17
**Runtime:** **Vercel AI SDK** in a Next.js route handler: streaming, tool calling, provider-agnostic.

**Tools (read-only over the published artifacts):**
- `get_forecast(station|place, hours)`
- `get_drivers(station, time)`
- `get_recent_observations(station, days)`
- `get_scoreboard(horizon)`
- `get_health_advice(aqi_category, profile)`, from a fixed CPCB/WHO advice table
- `find_station(place_name)`
- `compare_stations(a, b)`

**Providers:** fallback chain **Groq (gpt-oss-120b) → Gemini Flash → OpenRouter free model**, switching on error or rate limit (§0.2).

**Safety and cost:**
- **Upstash Redis** (free: 500K commands/month): per-IP rate limit, plus an answer cache keyed by (question, data revision).
- **Number validator** (D-008): every number in the answer must match a tool output after unit/rounding normalisation; otherwise one regeneration, then a template answer.

**Evaluation:** a fixed set of ≥ 100 questions with expected tool calls and facts, run in CI against a frozen artifact snapshot (M5/M6).

**v2:** the same tools exposed as an **MCP server**, so any AI assistant can query the forecasts.

**Rejected:**
- LangChain/LangGraph: built for multi-step, stateful agent graphs. Ours is one tool-calling loop plus a deterministic validator, and extra abstraction adds weight without capability.
- A Python agent on HF Spaces / Render free: these sleep, so cold starts break the ≤ 3 s first-token target (M8).

**Recruiter defence:** "Why not LangGraph?" → "The agent is one tool loop with a hard validator. I picked the smallest tool that gives streaming, tool calling and provider fallback. LangGraph becomes worth it when the agent needs multi-step plans, which is a v2 question."

### D-025 — Repository and configuration · DECIDED 2026-11-17
**Layout:** one **public** GitHub monorepo, name to follow D-010:
- `pipeline/`: Python package `saans`, with tests;
- `web/`: Next.js app + agent;
- `configs/`: one YAML per city (stations, OpenAQ↔CPCB crosswalk, bounding boxes, fire region, time zone, pinned weather model). Delhi-NCR is the first city, so "a city is a config file" (D-002);
- `docs/`: these files + the report;
- `.github/workflows/`.

**Why public:** free 4-vCPU runners, and the code itself is the portfolio. No secrets in the repo; secret scanning stays on.

### D-026 — Quality, monitoring and reliability · DECIDED 2026-11-17
- **CI on every push:**
  - ruff + pytest;
  - pandera data-contract tests on fixtures;
  - feature **parity test**: training and live feature code produce identical outputs on the same input;
  - web typecheck/lint/build;
  - agent eval smoke subset.
- **Runtime:**
  - every hourly run writes `status.json` (data age per source, stations reporting, model revision, run duration);
  - the UI shows the data age;
  - a failed workflow emails Mayank (GitHub default);
  - 3 consecutive failures → the site shows a "data delayed" banner automatically, because the status data is too old.
- **Reproducibility:** pinned `uv.lock`/`package-lock`; every artifact records commit, data revision and model revision.

### D-027 — Pin the weather model: GFS (`gfs_seamless`), never `best_match` · DECIDED 2026-11-17 (approved by Mayank 03:00; T2c confirms: GFS is the only model with lead-exact T2m back to 2022)
**Decision:**
- All weather features come from **one named model, GFS via `gfs_seamless`**, in training (archive) and live.
- `best_match` is forbidden: Open-Meteo picks the "best" model per place and time, so the source of a feature could change silently between training and serving.

**Evidence (T2b, Delhi, 1–7 Nov):**
- GFS is the only model tested with **100% of every proxy variable** (T2m, T850, 10 m wind, RH, shortwave, low cloud) in both **2022 and 2024**, and with mixing height in 2024.
- ECMWF IFS lacks T850 in the archive; ICON/GEM/CMA have no 2022 archive; JMA lacks shortwave.

**v2 option:** ECMWF IFS as a second model (multi-model features) once its archive covers the training window.

**Recruiter defence:** "Why GFS and not ECMWF, which is usually more accurate?" → "Feature consistency beats raw skill: GFS is the only model whose full feature set is archived as-issued over all my training winters. A model I can't reproduce historically can't be trained honestly. ECMWF is the v2 add-on."

### D-028 — Simulate the real data delay in training · DECIDED 2026-11-17 (approved by Mayank 03:00)
**Decision:**
- At issue time *t*, the newest observation used as a feature is the one the live system would actually have at *t*, i.e. *t* − delay.
- The delay is measured per source, not assumed:
  - OpenAQ/CPCB: currently about **2 h 50 min** (T4a2);
  - Open-Meteo GFS: run availability;
  - CAMS: 00 UTC run available by about 10:00 UTC (ECMWF);
  - FIRMS NRT: measured in build phase B1.
- Training rows are built with the same delays, and the delays are stored in the city config. "Lead time" is counted from the issue time, not from the last observation.

**Why:**
- If training assumes the observation from one hour ago is available, the model leans on it heavily.
- Live, that observation is about 3 hours old, so accuracy drops, especially for the first hours.
- This is the same leak family as D-012, and a common, invisible mistake.

**Recruiter defence:** "How did you avoid leakage?" → "Three ways: forecast-time weather (D-012), as-issued CAMS (D-013), and training with the real measured data delay of each source (D-028)."

### D-029 — v1 weather feature list (what survives the availability rules) · DECIDED 2026-11-17 (approved 03:05)
**Rule applied:** a weather feature is used in v1 only if it exists:
- (a) live in GFS,
- (b) in the training archive from 2022, and
- (c) lead-exact in Previous Runs for the test period (Nov 2025 → test; Nov 2024 → validation).

| Variable (GFS) | Live | Archive 2022+ | Lead-exact (Nov 2024+) | v1? |
|---|---|---|---|---|
| temperature_2m | ✓ | ✓ | ✓ | **yes** |
| wind_speed_10m | ✓ | ✓ | ✓ | **yes** |
| relative_humidity_2m | ✓ | ✓ | ✓ | **yes** |
| shortwave_radiation | ✓ | ✓ | ✓ | **yes** |
| wind_direction_10m, precipitation, surface_pressure, dew_point_2m | ✓ | to test | to test | **if they pass the B1 check** |
| temperature_80m / 120m (height levels, a possible inversion proxy) | ✓ | to test | to test (may fail like pressure levels) | **if they pass** |
| cloud_cover_low | ✓ | ✓ | ✗ | no |
| temperature_850hPa | ✓ | ✓ | ✗ (HTTP 400) | no |
| boundary_layer_height (mixing height) | ✓ | from Sep 2024 only | ✗ | no (v2, from our own archive) |

**Derived stability/ventilation proxies** (built only from "yes" variables):
- forecast diurnal temperature range;
- calm-night flag (10 m wind < 1.5 m/s and no sunlight);
- hours since sunset;
- RH-weighted humidity growth factor (also helps with sensor humidity bias, T-6);
- upwind direction for fires (if wind direction passes).

**Why:** losing the inversion and mixing variables hurts. But a model that uses them in training and can't get them honestly at test time is worse: its scores would be fiction. Physics knowledge partly replaces them through proxies, and the CAMS forecast already contains its own boundary-layer physics.

**Recruiter defence:** "Mixing height is the main driver of winter smog. Why isn't it in your model?" → "It is in through CAMS physics and surface proxies. The raw variable isn't archived as-issued before Sep 2024, so using it would have broken my test honesty. It returns in v2 from my own forecast archive."

### D-030 — Ship order: live pipeline + v0.1 Season Preview before the ML model · DECIDED 2026-11-17 03:21 (approved by Mayank; details in ROADMAP.md)
**Decision:**
- Build order **B0 → B2 (live pipeline + own forecast archive) → B1 (history) → B3 (model) …**
- Publish a **v0.1 Season Preview** around week 4 that shows the **CAMS physics baseline, clearly labelled as a baseline**, plus live observations and data age.
- Switch to our ML model only after it passes its B3 acceptance test.

**Why:**
- (1) The smog season is now, so people can use it this winter.
- (2) Every hour the pipeline runs adds lead-exact inputs to our own archive, which the public archives lack before 2024 (T-18). Delay loses that data forever.
- (3) A **prospective** scoreboard (forecasts published before the outcome) on winter 2026–27 is the strongest possible evidence.

**Recruiter defence:** "Why launch before the model was ready?" → "To collect the data the model needed and to prove accuracy prospectively. The preview was honestly labelled as a physics baseline, and the model replaced it only after passing pre-registered tests."

### D-031 — UI direction: **C · Breath** · DECIDED 2026-11-17 03:21 (chosen by Mayank)
**Direction:** soft, friendly, sentence-first. Built for the P1 personas (parents, sensitive groups).
- The AQI is a colour **orb** (category colour, number inside).
- Every card leads with a plain-English sentence ("Probably worse. 48% chance it turns Severe."), with numbers second.
- **Best time outside** has its own card.
- Drivers are shown as chips (↑ worsens / ↓ improves).
- Profile pills: Child · Elderly · Asthma · Runner.
- One big "Ask me anything about the air" button opens the agent.

Reference artboard: Design canvas "Air-quality forecast app — 3 visual directions", board **C · Breath**.

**Design tokens (v1, to become a Design System artifact in B5):**
- **Font:** DM Sans (400/500/700).
- **Colours:** ground `#EDF2F5`; cards `#FFFFFF`, radius 24; ink `#15202B`; secondary text `#4A5866`; action blue `#1F5FAD`.
- **AQI category colours** (Indian NAQI):

| Category | Fill | Text on fill | Chart |
|---|---|---|---|
| Good | `#2E9D5B` | white | `#2E9D5B` |
| Satisfactory | `#7CB342` | `#15202B` | `#7CB342` |
| Moderate | `#E6B800` | `#2B2200` | `#E6B800` |
| Poor | `#D9640F` | white | `#D9640F` |
| Very Poor | `#C62F37` | white | `#C62F37` |
| Severe | `#7E1F4E` | white | `#7E1F4E` |

- **Category is always written as a word next to its colour** (never colour alone, for colour-blind users).
- Driver chips: worse `#FBE3E4`/`#8E1F26`, better `#DDF2E7`/`#1E6141`.
- Touch targets ≥ 44 px; text contrast ≥ 4.5:1.

**Borrowed from the other directions:**
- From B: an optional one-line "headline" sentence at the top of a station page.
- From A: the dashed Severe-400 line on the 72-hour chart.

**v1 screens (B5):**
1. **Home / Station:** orb, tomorrow card, best-time card, drivers, profile advice, ask button; data-age line.
2. **Map:** stations as orbs on MapLibre (OpenFreeMap); deck.gl wind and satellite-fire layers; tap → station sheet.
3. **72-hour detail:** hourly forecast with p10–p90 band, category chances per day, Severe line.
4. **Scoreboard ("How accurate are we?"):** our error vs persistence and CAMS by horizon, calibration curve, prospective-test badge.
5. **Ask (agent chat):** grounded answers; every number linkable to its source card.
6. **About / Method:** plain-English method, data delays, known limits (fire undercount, sensor quality), data credits (CPCB, OpenAQ, Open-Meteo/CAMS CC BY, NASA FIRMS).
7. **Status banner component:** "Data delayed since HH:MM".

**Why C:** P1 users decide in seconds ("can my child play outside?"), so sentence-first beats number-first. Trust is carried by the Scoreboard and About screens (borrowing B's tone) rather than by the whole look.

---

## 2. Roadmap — foundation night (17 Nov 2026)
| Phase | Status | Output |
|---|---|---|
| 0 Lock the idea | **DONE** | D-001, D-002 |
| 1 Restate the problem | **DONE** (approved 01:22) | D-003 to D-008 DECIDED |
| 2 Check data and free resources | **DONE** (03:00). All smoke tests run. Open items moved to build phase B1: rediscover the CPCB download endpoint (D-011 amendment); lead-exact check for extra GFS variables (D-029); D-006 numbers freeze | DATASETS.md; OUTPUTS.md §2 |
| 3 Stack decisions | **DONE**: D-016 to D-028 DECIDED; D-011/D-012 amendments + D-029 PROPOSED (from T1-laptop/T2c) | §1.1 stack table |
| 4 Architecture | **design DONE** (ARCHITECTURE.md + image); Mayank rebuilds it on Miro the next day, then review | ARCHITECTURE.md §5 |
| 5 Version roadmap | **DONE (draft)**: ROADMAP.md; D-030 PROPOSED | v0.1 → v1 (B0–B8) → v2 → v3 |
| 6 UI/UX direction | **DONE** (03:21): name Aagahi (D-010), direction C · Breath + tokens + v1 screen list (D-031) | Design canvas + D-031 |
| 7 Docs + repo | — | GitHub skeleton, README, CI |
| 8 Report skeleton | — | Formatted report outline |

## 3. Sources
- AQEWS (IITM) — ews.tropmet.res.in/about.php
- CEEW study coverage (3 Oct 2025) — tribuneindia.com/news/delhi/despite-improvement-outdated-data-limits-air-pollution-forecasting-study
- GRAP stage thresholds (11 Nov 2025) — businesstoday.in/amp/india/story/grap-iii-curbs-imposed-in-delhi-as-aqi-crosses-425-bs-iv-diesel-bs-iii-petrol-cars-restricted-under-501600-2025-11-11
- GRAP invoked from forecasts — zeebiz.com/india/news-delhi-ncr-grap-iii-revoked-govt-lists-key-citizen-actions-for-pollution-control-as-aqi-improves-384117
- GRAP revision 21 Nov 2025 — tribuneindia.com/news/delhi/caqm-makes-grap-more-stringent-in-delhi-ncr-amid-worsening-air-quality
- Free LLM limits — blogs.novita.ai/free-llm-api-comparison-2026 · orcarouter.ai/blog/free-llm-api-what-it-costs
- Gartner, Top Trends in Data and Analytics 2026 — gartner.com/en/documents/7445926
- CPCB 999 µg/m³ rule, 59 Delhi stations (11 Nov 2026) — outlookindia.com/national/cpcb-explains-blank-diwali-aqi-readings-in-delhi-flags-outdated-2015-validation-system
- GitHub Actions billing and limits — docs.github.com/en/actions/reference/usage-limits-billing-and-administration · public-repo runner specs — docs.github.com/en/actions/reference/runners/github-hosted-runners · 60-day schedule disable — docs.github.com (enterprise-server usage-limits pages)
- External-cron pattern — devactivity.com/insights/github-actions-cron-woes-addressing-widespread-delays-and-missed-runs-in-software-project-development · merginit.com/blog/26062026-free-cron-job-scheduler-comparison
- Vercel Hobby — vercel.com/docs/plans/hobby · limits summary (checked 1 Nov 2026) — stork.ai/blog/vercel-pricing-2026 · Blob caps — schematichq.com/blog/vercel-pricing
- Cloudflare R2 pricing — developers.cloudflare.com/r2/pricing · card requirement — tech-insider.org/how-to-set-up-cloudflare-r2-2026
- Hugging Face rate limits — huggingface.co/docs/hub/rate-limits · commit cap report — wiki.161-35-77-84.sslip.io/lesson-hf-commit-rate-limit.html
- Upstash pricing — upstash.com/pricing/redis (via upstash.com blog, 2026)
- OpenFreeMap — openfreemap.org · MapLibre styles guide — scripts.nuxt.com/scripts/maplibre/guides/styles-and-providers
- Chronos-2 — arxiv.org/abs/2510.15821 · licence/comparison (Oct 2026) — pasqualepillitteri.it/en/news/26634/time-series-ai-compared-timesfm-chronos-timestral
- Data sources, fire-timing studies and the other traps: see DATASETS.md (each entry cites its source)

## 4. Change history
| Date | Change |
|---|---|
| 2026-11-17 00:30 | File created. Idea chosen (D-001), Delhi-NCR scope (D-002), Miro by hand (D-009). Problem landscape verified (§0.1); free LLM facts (§0.2). Phase 1 proposals D-003 to D-008 written; D-010 name pending. |
| 2026-11-17 01:22 | Mayank approved Phase 1: D-003, D-004 (order unchanged), D-005, D-006 (framework; numbers after data), D-007 (Hindi → v2; clear-English rule), D-008 → DECIDED. D-010: a new name will replace "Saans". |
| 2026-11-17 02:10 | Phase 2 research: §0.3 data facts; network now 59 stations (§0.1). DATASETS.md created (13 sources, 9 traps, 5 smoke tests). D-011 to D-015 PROPOSED. Smoke-test script given to Mayank. |
| 2026-11-17 02:40 | Smoke-test results (Colab, Singapore IP) recorded in OUTPUTS §2.1; §0.3 updated. Mayank approved D-011 to D-015 → DECIDED, each updated with test findings. Follow-up notebook issued. Phase 3: §0.4 platform facts, §1.1 stack table, D-016 to D-026 PROPOSED. D-007 retraining wording → D-022. |
| 2026-11-17 02:55 | Phase 2b results (OUTPUTS §2.2): mixing height archived for GFS from 2024 but not 2022; ADS works (kg m⁻³); OpenAQ CPCB delay ≈ 2 h 50 min, caaqm IDs all dead, isMonitor unreliable; VIIRS S-NPP archive gap. **Mayank approved D-016 to D-026 → DECIDED.** Updates: D-006 M7 freshness redefined relative to data arrival; numbers freeze moved to build phase B1; D-011 OpenAQ station rules + crosswalk; D-012 mixing-height ablation; D-013 ADS backfill plan + units; D-015 S-NPP excluded. New: D-027 pinned weather model (GFS), D-028 simulate data delay in training (PROPOSED). Claude's T2b previous-runs request was invalid (pressure-level variable + `_previous_dayN`) → re-test T2c. |
| 2026-11-17 03:05 | T1 from the laptop (Indian IP): CPCB answers instantly but returns 404 on the old endpoint → CPCB is India-only + the endpoint must be rediscovered (D-011 amendment). T2c: GFS mixing height archived from Sep 2024; lead-exact Previous Runs only from Nov 2024 for wind/RH/shortwave (T2m from 2022); low cloud, mixing height and T850 never lead-exact → D-012 amendment (test-honesty rule; mixing-height ablation dropped for v1), new D-029 v1 weather features (PROPOSED). Mayank approved D-027, D-028 → DECIDED. ARCHITECTURE.md + diagram created; Miro rebuild next day. |
| 2026-11-17 03:15 | Mayank approved the D-011 and D-012 amendments and D-029 → DECIDED. Phase 5: ROADMAP.md (v0.1 Season Preview → v1 B0–B8 with acceptance tests → v2 → v3, risk register); D-030 ship order PROPOSED. |
| 2026-11-17 03:25 | Mayank chose the name **Aagahi** (D-010 DECIDED), UI direction **C · Breath** (D-031 DECIDED: tokens, NAQI colours, v1 screens) and approved D-030. Name research recorded in D-010. |
