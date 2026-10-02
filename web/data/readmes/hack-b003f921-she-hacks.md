# Wind power forecasting — She Hacks

User 1 provides turbine-specific CatBoost models and the prediction interface. User 2 provides archived-weather checks, the data contract and the offline integration adapter.

## Setup and full forecast cycle

Use Python 3.11 with `prediction/requirements.txt`. This workspace uses `.venv/ml/python.exe`; the system Python is 3.14. Recreate the isolated environment with Conda, or use another Python 3.11 virtual environment:

```powershell
conda create --prefix .venv/ml --override-channels --channel conda-forge python=3.11 pip --yes
.\.venv\ml\python.exe -m pip install -r prediction/requirements.txt
.\.venv\ml\python.exe -B scripts/run_weather_integration.py --issue-time 2026-02-14T12:00:00Z --wind-height-m 100 --model-dir models --drop-threshold 0.20
```

Run from the repository root. The cycle selects the latest 00/06/12/18 UTC ECMWF initialization at least 12 hours before issue time, reads an exact validated cache or downloads that individual run, validates weather, prepares model features, invokes the real batch CLI, checks predictions, analyzes power drops and atomically saves results. No training occurs. The existing February example seeds the cache from saved API responses, without another download. Wind height accepts 10, 100 or 200 m; 100 m is a technical assumption, not an established hub/sensor height.

Each successful version lives at `results/forecast_runs/<issue>/<weather-run>/<input-version>/`, containing `weather.csv`, `weather_model_input.csv`, `predictions.csv`, `alerts.csv` and `metadata.json`. Identical reruns validate and reuse cached weather and outputs, without model inference. New weather runs, changed input/model hashes, heights or thresholds create separate versions. Old versions are retained. The earlier [integration artifacts](examples/integration_20260214_100m/) remain unchanged.

`--issue-time` accepts any supported date at an exact UTC hour (required by the integer 1..48-hour contract). Use `--weather-run-time 2026-02-14T00:00:00Z` to select an older eligible cycle explicitly. A model directory must implement User 1's two-turbine metadata/artifact schema and pass the training-cutoff guard. Weather outside actual archive coverage fails; it is not synthesized. Useful options:

```powershell
# Repeat entirely offline: valid cache or exact saved evidence required.
.\.venv\ml\python.exe -B scripts/run_weather_integration.py --issue-time 2026-02-14T12:00:00Z --wind-height-m 100 --model-dir models --drop-threshold 0.20 --offline

# Demonstrate a cache-miss error without network access, even with an old successful forecast present.
.\.venv\ml\python.exe -B scripts/run_weather_integration.py --issue-time 2026-02-14T12:00:00Z --wind-height-m 100 --offline --cache-dir .venv/empty-weather-cache --seed-dir .venv/no-weather-seeds
```

The latter intentionally exits 1 and writes a failure report, not a forecast. Missing/corrupt weather or outputs never fall back to an older run or report a new success. `--cache-dir`, `--seed-dir` and `--output-root` control storage. The ignored runtime weather cache is separate from tracked original evidence. To deliberately refresh an archived response, use a new cache directory; existing evidence is never overwritten.

## Three-hour power-drop alerts

For each turbine independently, compare forecast `P(t)` with `P(t+3h)` within the same issue/run. Emit an alert when `P(t) - P(t+3h) >= --drop-threshold`. **0.20 means 20 percentage points of normalized power, not a relative 20% decrease.** This is a demonstration threshold, not calibrated on history. “Current” means the forecast value at each target time, not observed power or power at issue time. The last three targets have no +3h endpoint and are not extrapolated; 45 pairs per turbine are checked. No alerts is valid and produces a header-only CSV. Overlapping alert windows are retained, not counted as independent physical events.

The checked February cycle produced **96 predictions and 7 alert windows** (4 for turbine 1, 3 for turbine 2). See [cycle verification](docs/forecast_cycle.md) for results, cache behavior and error handling.

The actual User 1 batch syntax is:

```powershell
.\.venv\ml\python.exe -m prediction --model-dir models batch --input examples/integration_20260214_100m/weather_model_input.csv --output examples/integration_20260214_100m/batch_reproduction.csv
```

Choose a new output path for direct batch reproduction: that CLI can overwrite its output. It rejects duplicate turbine/target pairs, so overlapping issues must be processed separately and preserved as distinct forecast versions.

## User 1 metrics with measured weather

Earlier comparison fits were trained through July 2025 and validated August 2025–January 2026 using **measured weather at the target hour**. These are power-estimation metrics, not 24–48-hour forecast-weather scores. Comparison outputs were not clipped; the validation set was used for model selection.

| Turbine | CatBoost MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| turbine_1 | 0.020992 | 0.041434 | 0.986010 |
| turbine_2 | 0.020304 | 0.053243 | 0.976771 |

Source: [model comparison](reports/model_comparison.md). Deployable models were subsequently refitted through January 31; these metrics do not independently evaluate the final refits.

## Integration success

The February 14 example connects ECMWF weather, the adapter and both actual `.cbm` models: **96 rows, 48 per turbine**, targets February 14 13:00 through February 16 12:00 UTC. Checks cover horizons, missing values, duplicate keys, unchanged input fields/time strings and finite `predicted_normalized_power` in [0,1]. The interface clips finite raw predictions to this range; range compliance is not accuracy. The output is normalized power, not MW or energy.

See [integration evidence](docs/ml_weather_integration.md) and output metadata for actual results, hashes and package versions.

## User 2: completed February forecast schedule and demonstration

The February schedule is complete: **29/29 daily issues, January 31–February 28 at 12:00 UTC**, 48 future hours for both turbines. In the explicitly assumed UTC+05 source clock, **all 672 February hours are covered for each turbine**, with no missing issue or forecast value. This is forecast generation and coverage, not a February accuracy score. The earlier January evaluation was not rerun.

Weather comes from **Open-Meteo Single Runs API, ECMWF IFS** (`https://single-runs-api.open-meteo.com/v1/forecast`), selecting each day's 00:00 UTC initialization with an assumed 12-hour availability delay. The two requested turbine locations use the same weather grid cell. Wind at 100 m is an explicit technical choice, not a confirmed hub/sensor height. Archive origin remains `unverified`; availability, UTC+05, interval-start labels and zero extra observation delay remain `assumed`.

`scripts/run_february_forecasts.py` calls the existing weather-to-power cycle only for missing compatible results. It uses the January models on January 31 and production models on February 1–28, checking completed training intervals under the same timezone assumption. It validates model/response/output hashes, reuses exact weather caches, keeps every issue and overlapping forecast, records failures while continuing, and saves versioned tables, alerts, coverage and an offline HTML report. The already completed February 14 predictions were checked and reused without another model invocation; their original files remain unchanged.

Results: [`results/february_forecasts/ba114e109ecee099/`](results/february_forecasts/ba114e109ecee099/).

- [`forecasts.csv`](results/february_forecasts/ba114e109ecee099/forecasts.csv): all **2,784** forecast cases, retaining issue/run/target times and original weather fields.
- [`february_forecasts.csv`](results/february_forecasts/ba114e109ecee099/february_forecasts.csv): **2,652** cases whose targets fall within February in UTC+05; overlapping issues are retained.
- [`alerts.csv`](results/february_forecasts/ba114e109ecee099/alerts.csv): **350** three-hour warning windows (179 / 171 by turbine), preserving issue/run identity. The 0.20 absolute drop is a demonstration threshold; overlapping windows are not independent observed events.
- [`report.html`](results/february_forecasts/ba114e109ecee099/report.html): offline report with a real February 14 plot and searchable warning table; [`forecast.png`](results/february_forecasts/ba114e109ecee099/forecast.png) is the standalone plot.
- `coverage.json`, `issues.csv`, `missing_hours.csv`, `weather_evidence.json`, `metadata.json`: actual coverage, all issue outcomes, source evidence, checks and assumptions.

```powershell
# Show the completed demonstration; no downloads, inference or local SCADA needed.
Start-Process .\results\february_forecasts\ba114e109ecee099\report.html

# Continue only missing issues; reuse matching existing results and exact weather cache.
.\.venv\ml\python.exe -B scripts/run_february_forecasts.py --source-timezone Etc/GMT-5 --observation-delay-hours 0 --wind-height-m 100

# Validate/reuse the entire completed schedule offline in this workspace.
.\.venv\ml\python.exe -B scripts/run_february_forecasts.py --source-timezone Etc/GMT-5 --observation-delay-hours 0 --wind-height-m 100 --offline
```

Use the Python 3.11 setup above. Full per-issue artifacts are local in ignored `data/processed/february_runs/`; the reused February 14 run is in the previously tracked `results/forecast_runs/`. Cache bodies stay in ignored `data/weather_cache/`. A clean clone can show the tracked report immediately; an offline schedule rerun additionally needs the local full-run/cache files, while an online rerun can rebuild missing results. The wrapper never trains models or uses SCADA for forecasting. Failed or corrupt data cannot be presented as a new successful issue.

Validation: seven focused February tests passed; a real completed 96-row example was verified unchanged, and the full schedule was repeated with network and model calls forbidden. All 29 results were reused. See [February completion report](docs/february_forecast_completion.md). No branches were merged and no pull request was created for this completion.

February actual power is absent, so accuracy and alert effectiveness remain unmeasured. Historical publication/SCADA timing, archive provenance, and wind-height comparability remain unresolved. These limitations do not become confirmed merely because coverage is complete. Saule's measured-weather metrics and the preliminary January scores remain separate experiments.

## Forecast quality with archived weather — preliminary January evaluation

The [preliminary January evaluation](docs/january_preliminary_evaluation.md) uses the separate `models/backtest_january/` models and 30 daily ECMWF runs, with issues January 1–30 at 12:00 UTC. All 30 issues succeeded. **2,844 paired cases, 726 of 744 local-January hours per turbine** were evaluated; the first 18 hours are uncovered by this schedule. Original full 48-hour predictions remain in ignored `data/processed/january_runs/`; compact, versioned evidence is in [results/january_preliminary/3335d4b8ac8bba15/](results/january_preliminary/3335d4b8ac8bba15/).

| Turbine | Horizon | Cases | ML MAE / RMSE | Persistence MAE / RMSE |
| --- | --- | ---: | --- | --- |
| turbine_1 | 1–24 h | 720 | 0.151585 / 0.231329 | 0.302303 / 0.431223 |
| turbine_1 | 25–48 h | 702 | 0.172892 / 0.256884 | 0.379551 / 0.490082 |
| turbine_2 | 1–24 h | 720 | 0.155823 / 0.238020 | 0.300620 / 0.432194 |
| turbine_2 | 25–48 h | 702 | 0.175617 / 0.260669 | 0.379563 / 0.491242 |

These are **preliminary scores under assumptions**, not a confirmed historical backtest. The assumed source clock is fixed UTC+05 (`Etc/GMT-5`), source timestamps label interval starts, observations become available at hour end (zero extra delay), and weather becomes available at initialization +12h. All availability/timezone assumptions are explicitly unconfirmed; weather provenance remains `unverified`. ML and persistence use exactly the same cases. Overlapping issues are preserved. Do not compare these scores directly with User 1's measured-weather metrics above.

```powershell
# Required once for the existing evaluator's dependencies.
.\.venv\ml\python.exe -m pip install -r scripts/january_requirements.txt
# Only if hourly data are absent; raw files remain unchanged and ignored by Git.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_hourly.ps1
# First check one issue; it can seed/reuse the exact weather cache.
.\.venv\ml\python.exe -B scripts/run_january_evaluation.py --source-timezone Etc/GMT-5 --observation-delay-hours 0 --last-day 1 --output-root data/processed/january_pilot_evaluation
# Full January schedule, 100 m wind; exact caches and successful runs are reused.
.\.venv\ml\python.exe -B scripts/run_january_evaluation.py --source-timezone Etc/GMT-5 --observation-delay-hours 0
# Repeat the same complete calculation without any network access.
.\.venv\ml\python.exe -B scripts/run_january_evaluation.py --source-timezone Etc/GMT-5 --observation-delay-hours 0 --offline
```

The wrapper reuses `agent.weather_pipeline.run` and `backtest.evaluate_january.evaluate`; it never asserts the confirmations required by the evaluator's strict CLI. It checks hourly source and model hashes, maps training interval ends with the same timezone as actuals, rejects ineligible models, limits transient weather downloads to three attempts (2s/4s backoff), continues to later issues after failure, and reports incomplete coverage with a nonzero exit code. A repeated complete offline run validated and reused all 30 forecasts and the evaluation. Changing inputs/code/settings creates a new version without deleting earlier results. See the report for unresolved assumptions and model-selection limitations.

No February forecast accuracy score has been calculated. Weather provenance remains **`unverified`**; the specific unresolved operational-versus-retrospective status is preserved in source metadata. Hub/sensor heights, historical publication times, SCADA timezone and interval labels remain unconfirmed. Schema compatibility does not establish that forecast wind at 100 m matches measured-wind training inputs. No February power labels were used.

Final models include data through January 31 23:00 in an unspecified source timezone. **Do not use them for an honest January backtest or a January 31 12:00 issue.** Such a forecast needs a separate model trained only on observations available before that issue, accounting for aggregation and publication delays, with cutoff/timezone documented. The adapter rejects early issues, but its conservative cutoff guard is not an as-of training pipeline. Models were physically built in September: this is a historical-input integration simulation, not actual February deployment.

## Documentation and checks

- [Kamila to Saule handoff: status, results, commands and local-only files](docs/HANDOFF_KAMILA_TO_SAULE.md).
- [Prediction interface](prediction/README.md), [model metadata](models/metadata.json).
- [Data contract and daily schedule](docs/data_contract.md).
- [Provenance evidence](docs/weather_archive_provenance.md), [organizer questions](docs/organizer_questions.md).
- Rebuild weather example offline: `python -B scripts/build_weather_example.py`.
- Tests: `.\.venv\ml\python.exe -B -m unittest prediction.test_interface scripts.test_weather_integration agent.test_weather_pipeline`.
- January checks: `.\.venv\ml\python.exe -B -m unittest scripts.test_january_pipeline backtest.test_january` (install `scripts/january_requirements.txt` first).

Local environments and production datasets remain ignored. The deployable models and small examples are retained for reproducibility.
