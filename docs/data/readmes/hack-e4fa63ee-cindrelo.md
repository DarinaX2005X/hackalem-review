# Cindrelo — wind power forecasting

Hourly normalized-power forecasts for two wind turbines, driven by archived weather. A bounded OpenAI tool controller fetches weather, prepares data, validates temporal eligibility, runs a numerical model, compares revisions and publishes dashboard files. The same guarded tools also run deterministically without an API key.

**Implemented:** data preparation, weather caching, December model selection, January holdout evaluation, February replay, agent execution/recovery, real dashboard examples, an offline demonstration, and a Streamlit dashboard with a one-click forecast cycle, forecasts, revisions, actuals, metrics and tool traces.

**Limitations:** source timezone and interval convention are assumed; weather publication delay is assumed; the archive's historical as-issued provenance is unverified. Forecasts carry `degraded` status and visible warnings. February has no supplied observations, so no February accuracy is claimed.

![Dashboard](assets/image.png)

[!NOTE]
Review CINDRELO_ARCHITECTURE.pdf for details

## Quick start

Tested with Python 3.14.7 on macOS ARM64. Run from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-backend.txt
python -m src demo
```

`demo` **recomputes** two real January forecasts from the bundled empirical curve and four cached weather responses. It needs no network, API key or prior training. Outputs go to `outputs/offline-demo/`. Running it again skips numerical prediction for unchanged inputs. The included source turbine CSVs supply actuals.

The UI can immediately consume `examples/dashboard/`: 192 genuine forecast rows, matching actuals, measured January metrics, and traces from two successful live OpenAI runs:

```sh
python -m pip install -r requirements-ui.txt
CINDRELO_OUTPUT_DIR=examples/dashboard streamlit run app.py
# Or use freshly recomputed forecasts:
CINDRELO_OUTPUT_DIR=outputs/offline-demo streamlit run app.py
```

Start Streamlit from the repository root so it loads [`.streamlit/config.toml`](.streamlit/config.toml). Horizon uses an explicit light theme for native controls and text, including on machines with a dark system preference. After updating this file, stop Streamlit with `Ctrl+C`, restart it, and reload the browser. The [Streamlit theme configuration](https://docs.streamlit.io/develop/concepts/configuration/theming) keeps widget colors consistent with the dashboard's light backgrounds.

`docs/fixtures/dashboard/` remains synthetic UI test data. `examples/dashboard/` contains model results. Both follow [the same contract](docs/TEAMMATE_SPEC.md).

### Run the full cycle from the dashboard

Install both backend and UI requirements as above, set `OPENAI_API_KEY` in an ignored root `.env` file, and press **Run forecast cycle**. The default action:

1. Retrieves external archived weather for the 9 January 2026, 19:00 UTC issuance.
2. Prepares hourly observations, validates inputs and runs the trained numerical model.
3. Analyzes revisions and publishes 48 hourly predictions for each turbine.
4. Advances the replay clock 12 hours, fetches the newer eligible weather run and repeats the cycle automatically.
5. Displays the latest forecast, previous issuance, actuals and the recorded tool trace.

Progress comes from actual tool calls. This is a historical replay; it does not claim to forecast today's weather. The bundled December-selected **AIFS/GEM wind model** supplies hours 25–48; the empirical curve supplies hours 1–24. No training is needed. The 12-hour update is an operational replay; its accuracy has not been evaluated separately. **Run options** lets you change the issuance, disable the automatic revision, or select **Offline deterministic rehearsal** with cached weather and no OpenAI call. **Refresh** only reloads files.

Live mode rechecks external weather on every run. Each weather request has one attempt with a 12-second timeout before falling back to a verified cache when available; cache fallback is visibly logged. Input identity ignores provider timing metadata, so repeated unchanged inputs reuse forecasts. Changed selected weather values from any provider or a newly eligible IFS run produce a new version. Runtime weather caches are isolated under `outputs/`; responses must pass validation before replacing cached data. Actual observations refresh even when predictions are reused.

To run the same selected-model service from the terminal:

```sh
python -m src cycle --offline
# Live OpenAI controller and external weather refresh:
python -m src cycle --agent --output outputs/candidate-live
```

The command prints the completed snapshot directory to use as `CINDRELO_OUTPUT_DIR`. Bundled candidate caches cover the default issuance and its 12-hour revision; other dates require online retrieval or an existing cache. Candidate model fitting uses no January labels. The extra AIFS/GEM/GFS/ICON/JMA inputs use eligible 48/72-hour Previous Runs offsets with an assumed eight-hour publication delay. Original publication times are unverified.

Completed dashboard runs are immutable snapshots under `outputs/dashboard-runs/<session>/snapshot-<id>/`. The UI selects a snapshot only after the entire requested cycle succeeds; a failed revision keeps the previous view. Committed examples are preserved. The cycle runs on demand, with a simulated update; there is no background scheduler.

<a id="windows-powershell-enable-utf-8"></a>

### Windows PowerShell

Backend files are explicitly read as UTF-8 (with optional BOM) and written as UTF-8. `-X utf8` is no longer required for backend file handling. This fixes the spurious weather-cache checksum mismatch caused by Windows legacy encodings; checksum validation remains enabled and the bundled hashes are unchanged. The regression suite exercises a clean demo under a simulated Windows `cp1252` file default, including Cyrillic source metadata, degree-symbol weather units, Unicode event messages and repeat-run deduplication. The integrated backend also runs on Windows/Python 3.12 without the earlier `python -X utf8` workaround. On an older checkout, `python -X utf8 -m src demo` enables UTF-8 explicitly; upgrading and regenerating old output is the durable fix.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt -r requirements-ui.txt
.\.venv\Scripts\python.exe -m src demo
$env:CINDRELO_OUTPUT_DIR = "outputs/offline-demo"
.\.venv\Scripts\python.exe -m streamlit run app.py --browser.gatherUsageStats false
```

To view the committed live-agent examples instead, set `$env:CINDRELO_OUTPUT_DIR = "examples/dashboard"`. Offline regeneration uses the deterministic controller; its events do not represent a live OpenAI run.

**Recovery for artifacts created before the fix:** if a previous run wrote metadata or events using a Windows legacy encoding, regenerate preparation metadata and use a fresh output directory. Changing the file-handling code cannot repair already misencoded files. Do not disable weather-cache validation or change bundled hashes.

```powershell
.\.venv\Scripts\python.exe -m src prepare
.\.venv\Scripts\python.exe -m src demo --output outputs/offline-demo-utf8
$env:CINDRELO_OUTPUT_DIR = "outputs/offline-demo-utf8"
.\.venv\Scripts\python.exe -m streamlit run app.py --browser.gatherUsageStats false
```

See [the demo guide](docs/DEMO.md) for the walkthrough and original integration rehearsal, and [the backend follow-up](docs/BACKEND_VERIFICATION.md) for the fixes and repeated checks after PR #6.

## Train and replay the full period

```sh
python -m src prepare
python -m src train
python -m src replay
```

Training downloads daily single-run forecasts for September 2025–January 2026 at both coordinates, caches them under `data/weather/`, and fits three temporally separated model bundles. Requests have bounded retries. Re-running uses the cache. `python -m src train --offline` reproduces training after that cache exists.

Replay covers local daily origins January 31–February 28. It writes 2,784 forecast rows (29 origins × 48 hours × 2 turbines) to `outputs/dashboard/forecasts.csv`. `february_day_ahead.csv` contains exactly 1,344 rows: February's 672 hours per turbine. It always selects horizons 25–48 from the preceding local midnight, rather than choosing a forecast based on future accuracy. March spillover remains in the full export only.

A ready-to-review [February day-ahead CSV](examples/submission/february_day_ahead.csv) is committed with [verification and provenance](examples/submission/README.md), so the export is available without the full local weather/model cache. This 24-hour-per-origin table is a submission export, not a complete dashboard directory.

The January 31 origin uses the December-trained bundle because a model fitted through January 31 would leak future observations at that origin. February origins use the final bundle fitted through January 31. All cutoffs use interval end times, not just target start timestamps.

## Run the agent

Set `OPENAI_API_KEY` in an ignored root `.env` file. Optional `OPENAI_MODEL` defaults to `gpt-4.1-mini`; `.env.example` shows the format. Viewing saved dashboard files and running the deterministic pipeline require no key. The dashboard's live-agent button does require one.

```sh
python -m src forecast --issue 2026-01-09T19:00:00Z --agent --output outputs/agent-demo
python -m src forecast --issue 2026-01-10T07:00:00Z --agent --output outputs/agent-demo
```

The second issuance advances the simulated clock 12 hours. A newer archived run becomes eligible and produces a new version, compared on 36 overlapping hours per turbine. Repeating an identical issuance and inputs deduplicates it. To re-demonstrate the live path after generating these versions, use a fresh output directory.

The [Responses function-calling API](https://developers.openai.com/api/docs/guides/function-calling) controls the tool sequence and recovery choices. Numerical values come from Python. Code enforces weather availability, training cutoffs, complete horizons, valid power bounds and tool order. The agent gets at most 10 API turns; weather acquisition gets at most two run choices. CLI requests allow three attempts; the dashboard uses the shorter timeout/cache policy above. `--offline` disables weather network access but an `--agent` invocation still needs OpenAI access. Omit `--agent` for the deterministic controller, which needs no LLM.

Tools: `fetch_weather`, `prepare_inputs`, `validate_inputs`, `predict_power`, `compare_forecasts`, `publish_forecast`. Errors, retries, tool results and skips are saved to `events.jsonl`. A failed run cannot publish invented forecasts. Full-month replay deliberately uses the deterministic controller to avoid hundreds of unnecessary LLM calls. This is an on-demand replay application; no background scheduler is installed.

## Measured results

The original baseline selection used December 2025 only. The empirical curve's December MAE was **0.2236**, versus **0.2395** for the fixed CatBoost candidate, so the curve was selected before January evaluation.

January 2026 holdout, both turbines and horizons pooled; 2,928 identical scored forecast/target pairs per model:

| Model                         | MAE, normalized power |
| ----------------------------- | --------------------: |
| **Empirical curve, selected** |            **0.1669** |
| CatBoost                      |                0.2087 |
| Training mean                 |                0.3023 |
| Last-known-power persistence  |                0.3340 |

Detailed per-turbine/horizon MAE, RMSE and sample counts are in [the measured metrics](examples/dashboard/metrics.csv). These results are conditional on the documented timezone and archive assumptions. They do not establish operational forecast accuracy or February performance.

Additional [forecasting research](docs/AI_WEATHER_BENCHMARK.md) tests other regression families, a week of past turbine observations and multiple weather providers. The latest December-selected AIFS/GEM challenger reduces full-January day-ahead MAE from **0.176782 to 0.160737**, with January 31 MAE **0.242786** versus **0.308140**. The preceding [site-weather model](docs/FRESH_PROVIDER_BENCHMARK.md) retains a better January 31 score of **0.215940**, while a [nearby-grid experiment](docs/SPATIAL_WEATHER_BENCHMARK.md) improves an exploratory monthly blend. These use a different, complete day-ahead target set and a two-hour reporting delay; they are not directly comparable with the pooled-horizon score above. January is now a reused research diagnostic. The 0.05 target is unmet. The dashboard now serves the selected AIFS/GEM model for hours 25–48 and the empirical curve for hours 1–24. The committed original February submission and legacy `demo`/`forecast`/`replay` commands retain their baseline model. See [the candidate decision](docs/CANDIDATE_SELECTION.md) for comparable results and scope. Research dependencies are optional: `python -m pip install -r requirements-research.txt`.

Training uses complete six-sample hourly means; missing hours remain unknown. The curve uses pre-cutoff measured turbine wind/power, then receives archived 100 m forecast wind for inference. Hub height is unconfirmed, so that wind-height mapping is an explicit approximation. The original baseline CatBoost uses only archived weather, turbine ID, calendar features and lead times; no future measured wind or invented February power lags. Its fixed configuration is 400 trees, depth 6, learning rate 0.05, seed 42. No hyperparameter search used January labels.

## Assumptions, provenance and reproducibility

See [config.json](config.json): raw and calendar timezone `Asia/Almaty`, timestamps treated as interval starts, local midnight issuance, ECMWF IFS 00/12 UTC runs, **assumed eight-hour publication delay**. IANA timezone handling preserves Kazakhstan's historical offset change; one ambiguous hour per turbine is excluded rather than guessed. Six samples are required for an hourly target. Telemetry is assumed available at the end of its hourly interval for the persistence baseline.

Only weather runs with `initialization + delay <= issuance` are eligible. Returned weather must cover all 48 target hours with finite values and expected units. Cached envelopes preserve request coordinates, returned grid coordinates, initialization, retrieval time, units, URL and content hash. Retrieval today is not evidence of historical availability. Do not describe these archives as verified as-issued forecasts until organizers confirm their acceptability. The [Open-Meteo Single Runs API](https://open-meteo.com/en/docs/single-runs-api) is used instead of a stitched historical series.

Weather attribution: **Open-Meteo, ECMWF, NOAA, DWD, JMA and Environment Canada**, [Open-Meteo](https://open-meteo.com/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Bundled weather is an attributed demonstration subset. Source turbine observations are supplied by the hackathon organizers. Normalized power is not MW or MWh; no capacity or station-energy conversion is invented.

Artifacts and downloads live in ignored `artifacts/`, `data/`, and `outputs/`. Portable AIFS/GEM models, explicit preprocessing statistics, checksums and demo caches live in `examples/candidate/`. Serving needs only backend dependencies; scikit-learn is used only for optional research. Native CatBoost bundles reproduce the 1,488 January research predictions to numerical precision. Portable baseline curve parameters and four cached weather responses live in `examples/backend/`; the example model uses only data available before January 2026. Full CatBoost bundles are local pickle files: load only files produced by this project. Configuration changes require regeneration; model/config mismatches fail explicitly. `requirements-backend.lock` records the full tested development environment; the smaller `.txt` file pins direct runtime packages.

Use one writer per CLI output directory. CLI files are replaced individually; refresh the UI after the CLI finishes. The dashboard service publishes complete immutable snapshots and serializes cycles within its Streamlit process because preparation and weather caches are shared. Do not run a separate CLI writer alongside a dashboard cycle. `events.jsonl` timestamps represent simulated issuance; `executed_at` records actual execution time.

## Verification and ownership

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m src demo --output outputs/verification
```

The integrated suite covers the backend, dashboard cycle and optional research experiments. `requirements-dev.txt` installs backend/dashboard test dependencies; `requirements-research.txt` adds the model experiments. Tests cover complete horizons, future-weather and future-training rejection, tool order, forecast revision, deduplication, refreshed observations and preservation of completed snapshots after failures. Research checks also cover delayed observations and training labels, sequence boundaries and ineligible weather values entering trajectory features.

PR #14's live dashboard cycle was verified in Chrome before this integration: four external weather responses, two completed OpenAI-controlled forecasts, 192 predictions matching the committed examples, and a saved 96-row CSV. The current combined branch passes **95 tests and 12 subtests**. Its live AIFS/GEM dashboard cycle completed two OpenAI-controlled forecasts with eight external weather responses and 192 predictions; a fresh backend-only Windows environment also passed. Evidence and the candidate decision are recorded in [the integration review](docs/PR13_PR14_INTEGRATION.md). Earlier live-agent, recovery, full-February replay and fresh-environment evidence remains under [examples/submission](examples/submission/README.md). The trace in `examples/backend/recovery-events.jsonl` contains an explicitly labelled injected failure.

Backend: `src/`, configuration, dependencies, root README and real examples. Dashboard teammate: `app.py`, `ui/`, `assets/`, `requirements-ui.txt`, `docs/DEMO.md`. Work on feature branches and integrate through PRs.

Planning context: [hackathon approach](docs/HACKATHON_APPROACH.md) · [dashboard handoff](docs/TEAMMATE_SPEC.md).
