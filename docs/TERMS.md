# TERMS.md — Aagahi glossary

Each project term in plain English, where it is used in Aagahi, and a link to learn more. Kept up to date as new terms appear. ("Saans" in older docs = the working name of the same project until 17 Nov 2026, D-010.)

## A. Air quality and policy
| Term | Plain-English meaning | Where it matters in Aagahi | Learn more |
|---|---|---|---|
| AQI (Indian National AQI) | One number (0–500) summarising air quality. Each pollutant gets its own sub-index from fixed breakpoints, and the AQI is the highest of them. | We compute it from forecast pollutant levels; we never predict it directly (D-005). | en.wikipedia.org/wiki/Air_quality_index |
| AQI categories | Good (0–50), Satisfactory (51–100), Moderate (101–200), Poor (201–300), Very Poor (301–400), Severe (401–500). | Category probabilities (Q2) and colours on the map. | — |
| Sub-index | The AQI-scale score of a single pollutant. | Shows which pollutant drives the AQI. | — |
| US EPA AQI vs Indian NAQI | Two different AQI scales. The US one uses different averaging and has no fixed 500 ceiling, so foreign apps can show "1,747" while CPCB shows 373. | We show Indian NAQI only, clearly labelled (DATASETS T-8). | — |
| PM2.5 / PM10 | Tiny airborne particles smaller than 2.5 / 10 micrometres. PM2.5 reaches deep into the lungs. | The main forecast targets in v1. | en.wikipedia.org/wiki/Particulates |
| µg/m³ | Micrograms of a pollutant per cubic metre of air. | Unit of the forecasts. | — |
| CPCB | Central Pollution Control Board, India's national pollution regulator. Publishes station data and the AQI. | Main source of ground truth. | — |
| CAAQMS | Continuous Ambient Air Quality Monitoring Station: an official station that measures pollutants every few minutes. | Our forecast locations. | — |
| DPCC / IMD / IITM stations | Delhi's stations are run by different agencies (Delhi Pollution Control Committee, India Meteorological Department, IITM, CPCB); the agency is in the station name. | Station metadata; quality can differ by operator. | — |
| CPCB Data Repository | The section of CPCB's CCR portal that offers yearly files of 15-minute station data. | Primary history source (DATASETS S1). | airquality.cpcb.gov.in/ccr |
| 15-minute raw data | Measurements averaged every 15 minutes, before CPCB's hourly/AQI processing. | We build our own hourly values from it (D-011). | — |
| Analyser range / 999 cap | The highest value an instrument can record. CPCB's AQI method drops hourly PM readings above 999 µg/m³. | Missing data on the worst hours (T-1, D-014). | — |
| Missing not at random (MNAR) | Data is missing *because of* its value (e.g. the highest readings vanish). Dropping it biases the model. | D-014. | en.wikipedia.org/wiki/Missing_data |
| GRAP | Graded Response Action Plan: Delhi-NCR's emergency plan. Stages I–IV switch on restrictions as the AQI rises or is forecast to rise. | Users care about the "chance of GRAP stage X". | — |
| CAQM | Commission for Air Quality Management: the body that invokes GRAP stages. | Policy context. | — |
| AQEWS | Air Quality Early Warning System for Delhi (IITM Pune): the official forecast. | Benchmark we compare against (M2). | ews.tropmet.res.in |
| DSS | IITM's Decision Support System that estimates pollution sources. Winter only; uses outdated inventories. | The gap our driver explanations fill. | — |
| SAFAR | An older IITM air-quality forecasting and information system for big cities. | Context only. | safar.tropmet.res.in |
| Stubble burning | Farmers burning crop residue after the rice harvest (Punjab/Haryana, Oct–Nov). A major seasonal pollution source. | A key driver feature. | — |
| Mixing height / boundary layer | The height of the air layer near the ground where pollution mixes. Low on winter nights, so pollution gets trapped. | Key weather driver; not archived as-issued for the default model (T-11). | en.wikipedia.org/wiki/Planetary_boundary_layer |
| Temperature inversion | Warm air sitting above cold air, acting like a lid that traps pollution. | Inversion strength (T850 − T2m) is our mixing proxy (D-012). | en.wikipedia.org/wiki/Inversion_(meteorology) |
| Ventilation | How well wind clears pollution away; low wind + low mixing = poor ventilation. | Driver family "wind and ventilation". | — |

## B. Data sources and data handling
| Term | Plain-English meaning | Where it matters in Aagahi | Learn more |
|---|---|---|---|
| CAMS | Copernicus Atmosphere Monitoring Service: Europe's free global air-quality forecast, made by a physics/chemistry model. | Baseline to beat, and an input feature. | atmosphere.copernicus.eu |
| ADS (Atmosphere Data Store) | Copernicus's free download service for CAMS data, used from Python with `cdsapi`. | Archive of CAMS forecasts by lead time (D-013). | ads.atmosphere.copernicus.eu |
| GFAS | CAMS's Global Fire Assimilation System: fire emissions estimated from satellites, fed into the CAMS forecast. | Indirect fire signal inside CAMS (D-015). | — |
| Chemistry-transport model | A physics simulation of how emissions move and react in the air. | What AQEWS and CAMS are. We correct them with ML. | — |
| Emission inventory | A table estimating how much pollution each source emits. | Why the DSS is outdated. | — |
| Grid cell / resolution (0.4°, ~45 km) | A physics model predicts one value per square of the map. CAMS global squares are about 45 km wide. | Why station-level ML correction adds value. | — |
| OpenAQ | A non-profit platform that collects air-quality data from governments and sensors worldwide and offers it through one API. | Live source for cloud jobs (D-011). | docs.openaq.org |
| Provider (OpenAQ) | Who delivered a station's data to OpenAQ. The same station can appear under two providers. | Duplicate trap T-10. | — |
| Low-cost sensor | A cheap PM sensor (e.g. AirGradient). Useful for coverage, but less accurate than official stations. | Excluded from ground truth in v1 (D-011). | — |
| Fire count (FIRMS) | Number of fires detected by NASA satellites in an area and time window. | Driver feature, with a known undercount (D-015). | firms.modaps.eosdis.nasa.gov |
| NRT / SP (FIRMS) | Near-real-time data (fast, preliminary) vs standard processing (archive, final). | Live features use NRT; training uses SP. | — |
| Fire radiative power (FRP) | How much heat a detected fire gives off; a rough measure of its size. | Weighting fires in the upwind fire index. | — |
| Polar-orbiting vs geostationary satellite | Polar satellites (MODIS, VIIRS) pass over a place about twice a day; geostationary ones watch the same area every few minutes. | Why evening fires are missed (T-4). | — |
| Upwind fire index | Fires counted with more weight when the wind blows from them towards Delhi. | Planned fire feature (D-015). | — |
| Issue time | The moment a forecast is made. Only information available at that moment may be used. | Leakage rule (D-012, D-013). | — |
| As-issued / archived forecast | A past forecast exactly as it was published then, not corrected later. | Training inputs and fair baselines. | open-meteo.com/en/docs/historical-forecast-api |
| Reanalysis (ERA5) | A best-estimate reconstruction of past weather, made later using all observations. It's hindsight. | Analysis only (D-012). | en.wikipedia.org/wiki/ECMWF_re-analysis |
| Look-ahead bias / leakage | Using information during training that would not have existed at forecast time. | D-012 prevents it (T-3). | — |
| Train/serve skew | The model sees features computed differently (or from different sources) in training vs live. Accuracy silently drops. | Feature-availability rule (D-012), parity tests (D-013, D-026). | — |
| Parity test | A test proving two pipelines give the same numbers for the same input. | CAMS ADS vs Open-Meteo (D-013); training vs live features (D-026). | — |
| Smoke test | A quick test that only checks a thing works at all (reachable, returns data) before deeper testing. | Phase 2 acceptance. | — |
| Licences: CC BY 4.0 / ODbL / Public Domain | CC BY 4.0: free use with attribution. ODbL: free use of a database with attribution, and shared improvements stay open. Public Domain: no conditions. | Open-Meteo (CC BY), CPCB mirror (ODbL), OpenCity (Public Domain). | creativecommons.org/licenses/by/4.0 · opendatacommons.org/licenses/odbl |
| Non-commercial use | Use that is not mainly for money. Open-Meteo's free API and Vercel Hobby require it. | Aagahi stays free and non-commercial in v1. | — |

## C. Forecasting and evaluation
| Term | Plain-English meaning | Where it matters in Aagahi | Learn more |
|---|---|---|---|
| Persistence baseline | The simplest forecast: "tomorrow = today". Every model must beat it. | M1 baseline. | — |
| Seasonal-naive baseline | "Same hour, same day last week (or the usual value for this date)". | M1 baseline. | — |
| MOS (model output statistics) | The classic method of correcting a physics forecast with a simple statistical (often linear) model. | Baseline in D-021. | en.wikipedia.org/wiki/Model_output_statistics |
| Bias correction / post-processing | Using ML to fix a physics forecast's systematic errors at a specific place. | The core Aagahi modelling idea. | — |
| Global model | One model trained on all stations together, with station identity as an input. | Handles new stations (D-021, T-5). | — |
| Direct multi-horizon forecasting | Predicting each future hour directly (lead time as an input), instead of feeding predictions back in step by step. | D-021. | — |
| Forecast horizon / lead time | How far ahead we predict (e.g. 24 h, 48 h, 72 h). | Metrics are reported per horizon. | — |
| Nowcast | A forecast for the next few hours, built mainly from the latest observations. | Hours 1–6 of the forecast. | — |
| LightGBM | A fast gradient-boosted decision-tree library, strong on table-shaped data. | Champion candidate (D-021). | lightgbm.readthedocs.io |
| Time-series foundation model | A large model pretrained on many time series that can forecast new ones with little or no training (zero-shot). | Chronos-2 challenger (D-021). | — |
| Chronos-2 | Amazon's pretrained forecasting model (Oct 2025) that accepts covariates (extra inputs like weather); Apache-2.0 licence. | Challenger (D-021). | arxiv.org/abs/2510.15821 |
| Covariates | Extra inputs that help predict the target (weather, fires, calendar). | All models get the same covariates. | — |
| Zero-shot | Using a pretrained model on new data without training it on that data. | Chronos-2 first test. | — |
| Quantile forecast / quantile loss | Predicting a range, e.g. p10/p50/p90, by training with a loss that targets each quantile. | Uncertainty band (Q2). | — |
| Conformal prediction / CQR | A method that adjusts prediction ranges using recent errors so an "80% range" really contains the truth about 80% of the time. CQR = conformalized quantile regression. | Calibrated uncertainty (D-021, M3). | en.wikipedia.org/wiki/Conformal_prediction |
| Exceedance probability | The chance that a value crosses a threshold, e.g. "62% chance AQI > 400". | Category probabilities (Q2), GRAP chance. | — |
| MAE | Mean absolute error: the average size of the forecast's mistakes, in µg/m³. | Main accuracy metric (M1). | en.wikipedia.org/wiki/Mean_absolute_error |
| MAPE | Mean absolute percentage error. | How the official system's error was reported. | en.wikipedia.org/wiki/Mean_absolute_percentage_error |
| Hit rate / false-alarm ratio | Of the real severe days, the share we predicted / of our severe warnings, the share that were wrong. | Severe-day detection (M2). | — |
| Brier score | The error of probability forecasts (0 = perfect). | Calibration metric (M3). | en.wikipedia.org/wiki/Brier_score |
| Calibration / reliability curve | Checks that "70% chance" really happens about 70% of the time. | M3; published on the scoreboard. | — |
| Climatology | The usual historical frequency for this time of year. A probability baseline. | M3 baseline. | — |
| Bootstrap interval | A range for a metric, found by re-sampling the test data many times. Shows whether an improvement is real or luck. | M1 acceptance; challenger rule. | — |
| Time-based split / rolling-origin validation | Train on the past, test on the future; repeat while moving the cut-off forward. | M4, D-021. | — |
| Pre-registration | Writing the test and the pass rule down *before* running it, so the result can't be bent afterwards. | Challenger rule (D-021), targets (D-006). | — |
| Data leakage | Future or test information sneaking into training, which inflates scores. | M4, D-012, D-013. | — |
| SHAP | A method that splits a model's prediction into contributions from each input feature ("fires added +80 µg/m³"). | Powers "why" explanations (Q3). | github.com/shap/shap |
| Driver family | A group of related features shown to users as one cause (e.g. "wind and ventilation"). | Explanations UI (D-021). | — |
| Concept drift | The relationship between inputs and outcome changes over time. | Drift report and alarm (D-022). | en.wikipedia.org/wiki/Concept_drift |

## D. Engineering, MLOps and product
| Term | Plain-English meaning | Where it matters in Aagahi | Learn more |
|---|---|---|---|
| Batch inference | Computing predictions on a schedule for everything at once, instead of on each user request. | Hourly forecasts (D-016). | — |
| Static-first / CDN / edge cache | Serving prepared files from servers close to the user, so pages load fast and no code runs per visit. | Website delivery (D-016, D-023). | — |
| ISR (incremental static regeneration) | Next.js feature: pages are pre-built and cached, then refreshed in the background when data changes. | Web app caching (D-023). | nextjs.org/docs |
| On-demand revalidation | The pipeline tells the website "new data is ready", so it refreshes cached pages right away. | `/api/revalidate` (D-023). | — |
| Data lake | A store of raw and processed data files (here Parquet) kept in an organised folder structure. | HF dataset repo (D-019). | — |
| Parquet | A compressed, column-based file format for analytics data. | All stored tables (D-018). | parquet.apache.org |
| Polars / DuckDB | Fast, modern tools for working with tables: Polars as dataframes, DuckDB as SQL, both running on one machine. | Processing (D-018). | pola.rs · duckdb.org |
| uv | A fast Python package and environment manager with a lockfile. | Reproducible setup (D-018). | docs.astral.sh/uv |
| Data contract (pandera) | Written rules a table must satisfy (columns, types, ranges, uniqueness), checked automatically. | Pipeline validation (D-018, D-026). | pandera.readthedocs.io |
| fsspec | A Python layer that lets code read/write files the same way on local disk, Hugging Face, S3 or R2. | Makes moving to R2 a config change (D-019). | filesystem-spec.readthedocs.io |
| Model registry | A versioned place where trained models and their metrics are stored, with one marked "champion". | HF model repo (D-022). | — |
| Champion / challenger | The current production model vs a new candidate that must prove it is better before replacing it. | D-021, D-022. | — |
| Promotion gate | Automatic checks a new model must pass before it goes live. | D-022. | — |
| Orchestrator | A tool that runs pipeline steps in order on a schedule (Airflow, Prefect, Dagster, or GitHub Actions here). | D-020. | — |
| workflow_dispatch / repository_dispatch | GitHub API events that start a workflow when an outside service calls them. | External cron trigger (D-020). | docs.github.com/actions |
| External cron (cron-job.org) | A free service that calls a URL on a schedule. More reliable than GitHub's own schedule. | Hourly trigger (D-020). | cron-job.org |
| Monorepo | One repository holding several parts of a project (pipeline, web, docs). | Repo layout (D-025). | — |
| Vercel AI SDK | A TypeScript library for building AI chat features with streaming, tool calling and multiple LLM providers. | Agent runtime (D-024). | ai-sdk.dev |
| Grounded agent | An AI assistant that answers only from tool results (our data and models), not from its own memory. | The AI rule D-008. | — |
| Tool calling | An LLM asking our code to run a function (e.g. `get_forecast(station)`) and then using the result. | How the agent gets real numbers. | — |
| Hallucination | An AI stating something false with confidence. | Blocked by the number validator (D-008, M5). | — |
| Rate limiting | Capping how many requests a user can make in a time window, to protect free quotas. | Upstash Redis (D-024). | — |
| MCP (Model Context Protocol) | An open standard that lets AI assistants call external tools and data in a uniform way. | v2: Aagahi tools as an MCP server. | modelcontextprotocol.io |
| MapLibre GL JS / deck.gl / OpenFreeMap | MapLibre: open-source GPU map renderer. deck.gl: GPU data-visualisation layers on top of maps. OpenFreeMap: free map tiles without a key. | Live map (D-023). | maplibre.org · deck.gl · openfreemap.org |
| RPM / RPD / TPM | Requests per minute / requests per day / tokens per minute: free-tier API limits. | LLM and data-API budgets. | — |
| Fallback chain | If one provider fails or is rate-limited, automatically try the next one. | Ingestion (D-011) and LLMs (D-024). | — |
| LCP | Largest Contentful Paint: how long until the main content of a web page appears. | Speed target M8. | web.dev/articles/lcp |
| Persona | A short profile of a typical user and their needs. | D-004. | — |

## E. Added in Phases 4–7 (17 Nov 2026)
| Term | Plain-English meaning | Where it matters in Aagahi | Learn more |
|---|---|---|---|
| Aagahi | Hindi/Urdu word for "awareness, advance knowledge". The product name. | D-010. | — |
| Lead-exact input | A past forecast value taken at exactly the same lead time it would have had live (e.g. the 48-h-ahead value, not a re-stitched one). | Every reported score must use lead-exact inputs (test-honesty rule, D-012 amendment). | — |
| Stitched archive | A history built by joining the first hours of many successive forecasts. Close to as-issued, but not lead-exact for long horizons. | Allowed for training only (T-18). | open-meteo.com/en/docs/historical-forecast-api |
| Previous Runs API | Open-Meteo service that returns what earlier model runs (1, 2, … days before) predicted for each hour. | Lead-exact weather inputs (D-012, D-029). | open-meteo.com/en/docs/previous-runs-api |
| Pinned weather model | Always asking for one named model (`gfs_seamless`) instead of "best available", which can switch models silently. | D-027, T-15; the config loader rejects `best_match`. | — |
| Data delay (latency) | How long after a measurement it becomes available to us (~170 min for OpenAQ CPCB data). | Simulated in training so live and training inputs match (D-028). | — |
| Crosswalk | A hand-checked table matching the same station across sources (OpenAQ ID ↔ CPCB ID ↔ name). | B1 task; `cpcb_id` in the city config (D-011). | — |
| City config | One YAML file per city holding stations, weather model, sensors and delays; code reads it, never hard-codes a city. | `configs/delhi-ncr.yaml` (D-025). | — |
| Season Preview (v0.1) | An early public release that shows live data and a clearly labelled CAMS-based forecast before our own ML model is ready. | D-030, ROADMAP v0.1. | — |
| Prospective test | Scoring forecasts that were published *before* the outcome happened. It cannot be tuned after the fact, so it is the most trusted test. | Live scoreboard; why D-030 starts the forecast archive early. | — |
| PM-based AQI | An AQI computed from PM2.5 and PM10 only. CPCB's official AQI needs at least three pollutants, so we label ours this way. | D-005; `aagahi.aqi`. | — |
| Provisional breakpoint | An AQI table value not yet checked against CPCB's official document; results using it are flagged. | Upper end of the Severe band, to verify in B1. | — |
| Design tokens | Named, reusable design values (colours, font, corner radius) shared by every screen. | D-031 (direction C · Breath). | — |
| AQI orb | Aagahi's main visual: a coloured circle in the AQI category colour, with the number inside and the category written beside it. | Home/Station screen (D-031). | — |
| Monorepo layout (`pipeline/`, `web/`, `configs/`, `docs/`) | Python pipeline, Next.js website, city configs and project docs live in one GitHub repo. | Repo skeleton, B0 (D-025). | — |
| CI (continuous integration) | GitHub Actions automatically runs lint and tests on every push and pull request. | `.github/workflows/ci.yml` (B0). | docs.github.com/actions |
| Lint / formatter (ruff) | A tool that finds code mistakes and style problems, and auto-formats code. | CI step (D-018). | docs.astral.sh/ruff |
