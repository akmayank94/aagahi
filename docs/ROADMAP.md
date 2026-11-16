# ROADMAP.md — Saans build plan (v0.1 → v1 → v2 → v3)

**Status:** PROPOSED 17 Nov 2026, 03:15 (Phase 5). Every phase ends only when its **acceptance test** passes. Results go to OUTPUTS.md, decisions to DECISIONS.md.
**Capacity assumed:** about 20 hours/week (Mayank's stated availability). Week numbers are targets, not promises; a failed acceptance test is fixed or reported, never skipped.

---

## 0. The one timing fact that shapes everything
It is **mid-November: the smog season is happening now** (it lasts roughly Oct–Feb). That gives three reasons to ship *something* live early, before the ML model is ready:
1. **Usefulness:** people need forecasts this winter, not next.
2. **Data:** from the day the hourly job starts, **our own forecast archive** saves every weather/CAMS input exactly as issued. That is the lead-exact data the old archives lack (DATASETS T-18). Every week of delay is a week of that data lost forever.
3. **The most honest test possible:** forecasts published *before* the outcome is known (a prospective test on the 2026–27 winter), on top of the retrospective test on 2025–26.

So the order is: **live pipeline first (B2), history second (B1)**, and a public **v0.1 Season Preview** that honestly shows the physics baseline until our model passes its tests (D-030).

---

## 1. Version overview
| Version | Target | What users get | Why it matters |
|---|---|---|---|
| **v0.1 Season Preview** | Week 4 (≈ mid-Dec 2026) | Live station map, 72-h **CAMS-baseline** forecast clearly labelled "baseline", data-age labels, an About page explaining the plan | Live this winter; starts our as-issued archive; first real users |
| **v1.0** | Week 11 (≈ early Feb 2027, still in smog season) | Our ML forecast with ranges and category chances, "why" drivers, advice by profile, public scoreboard, grounded AI chat (English) | The full product described in D-003 |
| **v2** | Before winter 2027–28 | Hindi, alerts, more cities, public API + MCP server, mixing height and multi-model weather from our own archive | Reach and scale |
| **v3** | 2028 | Neighbourhood-level map, source attribution, exposure planner, research write-up | Depth and long-term value |

---

## 2. v1 build phases (B0 → B8)

### B0 — Setup (week 1, ~6 h)
**Work:**
- Public GitHub monorepo (`pipeline/`, `web/`, `configs/`, `docs/`, `.github/workflows/`); `uv` project; ruff + pytest + pre-commit.
- Empty CLI (`saans --help`).
- HF repos: `-data`, `-live`, `-models`.
- Accounts: cron-job.org, Upstash (later), LLM keys (later).
- Secrets in GitHub Actions; docs copied into `docs/`.

**Acceptance:**
- CI green on an empty test.
- `saans --help` runs in CI.
- The three HF repos exist.
- Secrets present (names checked by a CI step, never printed).

### B2 — Live pipeline + own archive, no ML (weeks 1–2, ~15 h) · *runs before B1 on purpose*
**Work:**
- `hourly.yml`: OpenAQ ingest (active-station + crosswalk rules, D-011) → pandera validation → GFS (pinned) + Open-Meteo CAMS live fetch → **baseline forecasts** (persistence, CAMS raw at stations).
- Publish `latest/*.json` + `status.json`.
- **forecast_archive** written every run.
- cron-job.org trigger.

**Measurements started:**
- OpenAQ arrival-time distribution (to fix the cron minute, D-020);
- the 14-day ADS ↔ Open-Meteo CAMS **parity test** (D-013).

**Acceptance (7 consecutive days):**
- ≥ 95% of hourly runs succeed.
- Publish ≤ 30 min after new data arrives (M7).
- Archive files complete for ≥ 95% of hours.
- Arrival-time histogram + parity numbers in OUTPUTS.

### B1 — History foundation + audit + baselines (weeks 2–3, ~25 h)
**Work:**
1. **CPCB endpoint rediscovery** (DevTools capture by Mayank → downloader by Claude), then 15-min history 2017–2025 for Delhi + NCR, with SHA-256 per file. Fallback: OpenCity / Vonter / manual (D-011 amendment).
2. ADS CAMS backfill Aug 2022 → now (monthly requests, queue times logged).
3. GFS Historical Forecast 2022 → now, plus Previous Runs from Nov 2024.
4. FIRMS SP (NOAA-20/21, MODIS).
5. Calendar table (Diwali, holidays, GRAP stage dates).
6. **Lead-exact check of the extra GFS variables** (wind direction, precipitation, pressure, dew point, 80/120 m temperature; D-029).
7. **Data audit** (DeepGuard-style, pre-registered):
   - completeness by station/year;
   - ≥ 999 µg/m³ counts and gaps on high- vs low-pollution days (missing-not-at-random test, D-014);
   - bad values (T-7);
   - Pusa IMD vs DPCC series identity;
   - unit checks (T-14);
   - network growth timeline (T-5).
8. **Baseline scores on 2024–25** with lead-exact inputs: persistence, seasonal-naive, raw CAMS (ADS), linear bias-correction.
9. → **Freeze the D-006 numbers.**

**Acceptance:**
- Every audit item reported in OUTPUTS, with a written rule for every flag.
- Data contracts pass on the full history.
- **D-006 targets frozen with the date**, before any ML training.

### B3 — Modelling v1 (weeks 4–6, ~45 h)
**Work:**
- Feature builder: as-issued only, real delays simulated (D-012, D-028, D-029).
- Global LightGBM quantile model (PM2.5, PM10; leads 1–72 h).
- Conformal calibration (CQR) → category probabilities via the CPCB AQI formula.
- SHAP driver families.
- **Lead-mismatch penalty** measured (D-012 rule 3).
- **Chronos-2 challenger** under the pre-registered rule (D-021).
- Rolling-origin validation on 2024–25; **one** test run on 2025–26 (test-run counter in OUTPUTS).

**Acceptance:**
- M1–M3 checked on 2025–26 with lead-exact inputs and reported **whether they pass or fail**.
- Champion chosen by the pre-registered rule.
- Model card drafted.

### B4 — MLOps loop (week 7, ~15 h)
**Work:**
- `nightly.yml`: evaluate → scoreboard → drift report.
- `weekly.yml`: retrain → promotion gate → register CHAMPION (D-022).
- Switch the live forecast from the baseline to the champion; the scoreboard keeps showing the baselines.

**Acceptance:**
- One full weekly cycle runs unattended, with the gate decision logged.
- The scoreboard shows ≥ 7 days of prospective (live) scores.
- **Prospective-test counter** starts.

### B5 — Web app v1 (weeks 5–9, ~40 h; starts after Phase 6 design; parallel with B3–B4)
**Work:**
- Next.js pages: Map (MapLibre + deck.gl: stations, fires, wind), Station (72-h chart with range, category chances, drivers, advice by profile, cleanest hours), Scoreboard (vs baselines, calibration curve), About/Method (honest limitations: delay, fire undercount, sensor quality).
- ISR + revalidate; Vercel Analytics.
- Accessibility: colour-blind-safe AQI colours plus text labels.

**Acceptance:**
- **Lighthouse mobile: LCP ≤ 2.5 s (M8)**, accessibility ≥ 90.
- Every number on screen traces to `latest/*.json`.
- Works with the live feed down (shows the data-age banner).

### B6 — AI agent (weeks 8–9, ~25 h)
**Work:**
- Vercel AI SDK route; 7 read-only tools; number validator; Groq → Gemini → OpenRouter fallback; Upstash rate limit + cache.
- An **evaluation set of ≥ 100 questions** (in-scope, out-of-scope, tricky numbers, persona questions).

**Acceptance:**
- **M5: 100% grounded numbers.**
- **M6: ≥ 95% correct refusals.**
- First token ≤ 3 s at median.
- Provider-down drill passes.

### B7 — Hardening + v1.0 launch (week 10, ~15 h)
**Work:**
- **Failure drills**: kill OpenAQ, kill one LLM provider, publish stale data, corrupt one input file. Each must produce the designed behaviour (fallback, banner, no crash).
- README, dataset card, model card, disclaimer and privacy note.
- Final name live (D-010).

**Acceptance:** all drills pass; public URL; launch checklist complete.

### B8 — Report + portfolio (week 11, ~12 h)
**Work:**
- Project report (Phase 8 skeleton).
- Resume bullets **only from OUTPUTS numbers**.
- 2-minute demo video.
- LinkedIn launch post.
- Architecture diagram exported from Mayank's Miro board.

**Acceptance:** every claim in the report and on the resume links to an OUTPUTS entry.

**Total ≈ 200–230 hours ≈ 11 weeks at 20 h/week.** Phase 6 (UI design) and Phase 7 (repo skeleton) from tonight's plan feed B5 and B0.

---

## 3. Critical path and parallel work
```
Week:  1      2      3      4      5      6      7      8      9      10     11
B0 ████
B2 ███████████ (then runs forever, archive growing)
B1        ████████████
          v0.1 Season Preview ▲ (week 4)
B3                      █████████████████
B4                                        ██████
B5                            ███████████████████████  (after Phase 6 design)
B6                                               ████████████
B7                                                            ██████
B8                                                                   ██████ ▲ v1.0
```
- **Critical path:** B0 → B2 → B1 (D-006 freeze) → B3 → B4 → B7.
- B5 and B6 run alongside.

---

## 4. v2 (before winter 2027–28) — reach and scale
| Feature | Why now | Depends on |
|---|---|---|
| **Hindi** UI + agent (same clarity rule) | Reach most of the Delhi-NCR audience | v1 strings in one i18n file from day 1 |
| **Alerts:** Telegram bot + web push ("Severe likely tomorrow at your station") | Turns a site into a daily habit | Calibrated probabilities (M3) |
| **More cities** (config files): e.g. Lucknow, Patna, Kolkata, Mumbai | Indo-Gangetic Plain shares the winter problem | Global model + city config (D-025) |
| **Public API + MCP server** (same tools as the agent) | Other apps and AI assistants can use the forecasts | D-024 tools |
| **Mixing height + ECMWF as second weather model** | By then our own archive holds a full winter of lead-exact values | Own archive (B2) |
| **GRAP stage probability** ("chance of Stage III within 48 h") | What schools, offices and RWAs actually plan around | v1 category probabilities |
| **Low-cost sensor fusion** (AirGradient etc., calibrated against reference stations) | Denser coverage between stations | Calibration study |

**v2 success KPIs:** monthly active users; alert opt-ins; prospective severe-day hit rate across a whole season; ≥ 3 cities live.

## 5. v3 (2028) — depth
- **Neighbourhood-level map:** spatial model over the station network, e.g. a graph neural network on the station graph (builds directly on Mayank's GNN work in the NIDS project) or Gaussian-process interpolation, validated by leave-station-out.
- **Source attribution, kept up to date:** what DSS stopped doing. Combine CAMS species, fire indices, wind trajectories and receptor modelling, with honest uncertainty.
- **Personal exposure planner:** "best 2-hour window this week for a run near me".
- **Geostationary fire data** (evening fires; D-015f).
- **Research write-up** of the leakage-safe evaluation and the prospective scoreboard.

## 6. How this lines up with industry direction (for interviews)
- **Agentic AI with grounding and evaluation** (v1 agent, M5/M6) → MCP exposure (v2).
- **Time-series foundation models tested honestly** against tuned trees (Chronos-2 challenger).
- **Data quality and contracts as first-class work** (pandera, audits, traps T-1…T-18).
- **MLOps on ₹0:** scheduled retraining, promotion gates, model registry, drift monitoring.
- **Prospective evaluation:** a public scoreboard of forecasts made before the outcome was known.

## 7. Risk register
| Risk | Signal | Response (already designed) |
|---|---|---|
| CPCB history endpoint can't be rediscovered | B1 step 1 fails | OpenCity (Public Domain) → Vonter (private) → manual (D-011) |
| OpenAQ outage or longer delay | status.json data age > 6 h | Forecast from weather + CAMS + last obs; banner (M7) |
| Free tier changes (Open-Meteo, Groq, HF, Vercel) | API errors / terms change | Fallback chains; `fsspec` storage swap; provider-agnostic SDK |
| Model misses D-006 targets | B3 test | Report honestly; ship the best model that beats the baselines; iterate in v1.x |
| Scope creep before v1 | New ideas mid-build | Goes into v2 list; v1 scope locked (D-007) |
| Burnout / time | Weeks slip | v0.1 is already useful; phases are independent, so slipping a week doesn't break anything |
