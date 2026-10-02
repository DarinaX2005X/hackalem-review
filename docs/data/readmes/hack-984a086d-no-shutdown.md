# No Shutdown: wind power forecasting agent

Python backend for the HackAlem AI wind power forecasting case. It trains a separate model for each turbine, retrieves archived weather forecast runs, produces hourly forecasts of normalized power for 24–48 hours, and records agent decisions for audit and recalculation.

**Current interface:** the backend and its interactive API at `http://127.0.0.1:8000/docs`. The existing `index.html`, `styles.css`, and `app.js` remain a **synthetic-data prototype** and are not connected to the backend's ML forecasts. See [frontend instructions](docs/FRONTEND_README.md).

**Scope of the data:** the supplied CSVs contain 291,859 ten-minute observations ending on January 31, 2026. Despite their filenames, they contain no February 2026 ground truth. The project can generate February forecasts, but cannot calculate February accuracy without actual February observations. Validation with observed historical weather measures conditional weather-to-power error, not operational day-ahead forecast error.

## Quick start

From the repository root on Windows, run in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

The startup script creates a local environment and installs pinned dependencies. Then open [the interactive API](http://127.0.0.1:8000/docs). The server binds to localhost by default. Source CSVs are expected in `data/raw/`; see the repository's data instructions before training if they are absent.

Manual setup with Python 3.12+:

```bash
python -m venv .venv
# Activate the environment: .venv\Scripts\activate on Windows,
# or source .venv/bin/activate on Linux/macOS.
python -m pip install -r requirements.lock.txt
python -m windagent train
python -m windagent serve
```

Data, model artifacts, and state default to the project directory. Set `WINDAGENT_HOME` or pass `--home PATH` to select another directory.

## Reproduce forecasts and tests

Run these commands from the repository root after placing the supplied CSVs in `data/raw/`:

```bash
python -m windagent train --cutoff 2026-02-01T00:00:00+05:00
python -m windagent forecast --origin 2026-02-01T00:00:00+05:00 --horizon 48 --output reports/first_forecast.json --csv reports/first_forecast.csv
python -m windagent replay --start 2026-02-01T00:00:00+05:00 --days 28
python -m windagent backtest --start 2026-01-01T00:00:00+05:00 --days 7
python -m pytest -q
```

The model cutoff excludes observations at and after midnight on February 1, local time. The February replay issues a new 48-hour forecast for each of 28 daily origins; forecast windows overlap. The February 28 origin reaches into March 1, so any February-only evaluation must filter target timestamps and report lead times separately.

The brief also asks for an origin on January 31. That origin requires a **separate model** trained with a cutoff no later than `2026-01-31T00:00:00+05:00` and a separate artifact directory. A model trained through the end of January 31 would leak future observations into that forecast. The 28-day February replay above does not include the January 31 origin.

To check for revised input at one origin or poll automatically:

```bash
python -m windagent forecast --origin 2026-02-01T00:00:00+05:00 --refresh
python -m windagent watch --interval 300
python -m windagent watch --origin 2026-02-01T00:00:00+05:00 --interval 300
```

`--refresh` rechecks the input; unchanged content can reuse a previous prediction. `watch` polls for updates. Weather changes can trigger recalculation; retraining the model remains an explicit operation.

## Forecast pipeline

1. Load the two turbine CSVs and convert local `Asia/Almaty` timestamps to UTC. Check missing and duplicate observations. Aggregate ten-minute telemetry to hours only when at least four valid, distinct samples exist.
2. Select an archived weather **forecast run** available at the requested origin, rather than later observed weather. Cache the raw provider response and its provenance.
3. Prepare hourly features and run the turbine-specific model. A learned wind-speed curve and gradient-boosted trees compete on chronological validation data; a later, untouched period is used to measure the selected model.
4. Validate forecast values and write hourly predictions, source metadata, and audit events. The agent decides whether to reuse, recalculate, or report failure when inputs change.

This is a policy-driven agent: it orchestrates data retrieval, prediction, validation, and refresh without an LLM API key. The project does **not** claim that a language model predicts turbine output.

### Time and weather availability

The input CSV does not specify its timezone or interval convention. The implementation **assumes** `Asia/Almaty` and treats a timestamp as the start of its ten-minute interval, available only at the interval's end. Missing hours are not filled with later observations.

Weather is obtained from [Open-Meteo Single Runs](https://open-meteo.com/en/docs/single-runs-api) using a specified ECMWF initialization time. The implementation assumes a conservative 12-hour publication delay: a run is eligible only if its initialization time plus that delay is no later than the forecast origin. This is an availability rule used by the project, **not verified evidence of the provider's exact publication time** for each historical run. See [weather details](docs/WEATHER.md).

Prediction intervals are based on historical conditional residuals. They do not fully represent uncertainty in future weather. Model metadata records input hashes, feature schema, split dates, and artifact hashes.

## Reported results

The repository reports a completed February replay for **28/28 origins** and **2,688 turbine-hour forecast rows** (28 origins × 48 hours × 2 turbines). This counts predictions; it is **not a February accuracy score**.

A separate model, frozen before the January diagnostic, was tested on seven January origins with archived forecast weather. All 672 forecast rows were matched to actuals. The reported mean absolute errors (MAE) are in normalized power units:

| Turbine | Lead time | Model MAE | Persistence MAE |
| --- | ---: | ---: | ---: |
| 1 | 0–23 hours | 0.1398 | 0.2850 |
| 1 | 24–47 hours | 0.1355 | 0.2292 |
| 2 | 0–23 hours | 0.1389 | 0.2994 |
| 2 | 24–47 hours | 0.1333 | 0.2144 |

This is a small diagnostic with overlapping origins, not a February or seasonal score. No tuning was performed on this diagnostic. See `reports/january_backtest.json` for run provenance and coverage, and `reports/january_backtest_predictions.csv` for individual predictions and the persistence baseline. A mismatch between grid-forecast wind and site wind remains an accuracy limitation.

## API and output files

Useful endpoints are `GET /health`, `GET /model`, `POST /forecasts`, `GET /forecasts`, `GET /forecasts/{id}`, `GET /forecasts/{id}/csv`, and `POST /replay`. The [interactive API](http://127.0.0.1:8000/docs) documents their request and response schemas.

Example forecast request body:

```json
{"origin": "2026-02-01T00:00:00+05:00", "horizon": 48, "refresh": false}
```

The forecast detail includes an audit trail. The dashboard contract is `GET /api/forecast?turbine_id=T1&as_of_date=2026-02-01&horizon_hours=48`; it returns `forecast` points containing `predicted_power`, `wind_speed`, and `temperature`, plus warnings and provenance. `as_of_date` denotes local midnight in `Asia/Almaty`; returned point timestamps are UTC. Connecting the current UI requires replacing its mock data generator **and** its unit labels.

| Path | Contents |
| --- | --- |
| `data/raw/` | Supplied CSVs under stable names |
| `data/weather/` | Cached archived weather responses and provenance |
| `artifacts/` | Turbine models and training metadata |
| `reports/` | Data profile, validation, replay, and hourly forecast exports |
| `state/` | Local SQLite run and audit history; excluded from Git |
| `docs/` | Requirements, weather method, frontend notes, and limitations |

## Physical interpretation and power curves

The target is **normalized active power**, not MW or MWh. The output is bounded to `[0, 1]` according to the project's data interpretation; confirm the observed training range per turbine before treating these bounds as verified properties of the source CSVs. The farm-level equal-weight mean is a proxy because turbine rated capacities are unavailable. The prototype UI's 2.5/3.2 MW capacities are synthetic and must not be applied to model predictions. With verified rated capacities, an hourly mean normalized power can be converted to energy by multiplying by rated MW and one hour.

`power_curves_turbines.png` visualizes observed wind speed against normalized power for the two turbines. A curve used for training, a physics feature, or model validation must be fitted **only on observations available before the forecast cutoff**. February targets must never influence such a curve or its thresholds.

The physics module `src/physics.py` is described as providing `apply_physics_sanity_check()` and `calculate_physics_power_baseline()`. The first checks or constrains implausible predictions; the second provides a physics-inspired baseline that an ML model may use as a feature. Verify the actual function signatures and whether the training pipeline calls them before claiming the hybrid model is integrated.

The proposed `vin = 2.5 m/s` and `vrated = 10.5 m/s` should be documented as **empirical estimates** only if they were derived from pre-February data for the relevant turbine. `vout = 25 m/s` should be labeled a **design assumption** unless supported by turbine documentation or data. A wind forecast at the grid's reference height can differ from hub-height wind; hard-zero rules at these thresholds can therefore remove plausible production. Keep the estimated bounds and warnings distinct from verified equipment specifications.

## Limitations and next steps

1. **No February actuals:** February MAE/RMSE cannot be reported until observations for that period are supplied.
2. **Weather-to-site mismatch:** the grid wind height and turbine hub height require confirmation; calibrate grid forecasts to site observations using only pretest data.
3. **Historical run availability:** the 12-hour publication delay is an assumption; verify it against the provider and the required issuance schedule.
4. **Unknown operating conditions:** curtailment, outages, turbine model, and rated capacities are not supplied, so causes of low power cannot be identified from wind alone.
5. **Integration:** validate the physics module against an actual ML forecast and connect the dashboard to the backend before describing those paths as end-to-end features.

Load only trusted local model artifacts. The API is intended for local hackathon use; external deployment would need authentication, TLS, and request limits. A `Dockerfile` is included for packaging; live deployment is not required for local reproduction.

## References

- [Case requirements](docs/REQUIREMENTS.md) and [implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Open-Meteo Single Runs API](https://open-meteo.com/en/docs/single-runs-api)
- [scikit-learn histogram gradient boosting](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html)
- [FastAPI deployment guidance](https://fastapi.tiangolo.com/deployment/manually/)
- [Presentation](https://canva.link/istoddntna5ut7e)
