# Wind Farm Forecast

A minimal full-stack application that produces 24- or 48-hour normalized power
forecasts for two wind turbines. The user selects a turbine, a forecast issue time
in UTC, and a horizon. The backend retrieves an issue-time-safe ECMWF weather run,
builds the model features, runs the local scikit-learn model, and returns an hourly
table to the React UI.

The application has no database, needs no API key, and runs as one Docker container.

## Quick start with Docker

Requirements: Docker Desktop or Docker Engine. The trained production models are
already stored in `storage/models/production/` and are copied into the image.

```bash
docker build -t wind-app .
docker run --rm -p 127.0.0.1:8080:8000 wind-app
```

Open <http://127.0.0.1:8080>.

Port `8080` is the host port; the application always listens on port `8000` inside
the container. You can use `8000:8000` instead when local port 8000 is free.

Check the running service:

```bash
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/ready
```

Optional environment settings are documented in `.env.example`. To persist the
weather cache in a mounted `storage` directory, that directory must also contain
the two production model folders:

```bash
cp .env.example .env
docker run --rm \
  -p 127.0.0.1:8080:8000 \
  --env-file .env \
  -v "$PWD/storage:/app/storage" \
  wind-app
```

## Development mode

Requirements: Python 3.11–3.14, `uv`, Node.js 24, and npm.

Install the locked dependencies:

```bash
uv sync --locked --group dev
npm ci --prefix frontend
```

Start the backend in the first terminal:

```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

Start the frontend in the second terminal:

```bash
npm run dev --prefix frontend
```

Open the Vite URL printed in the second terminal. Vite proxies `/api` requests to
the backend on `127.0.0.1:8000`. Swagger UI is available at
<http://127.0.0.1:8000/docs>.

## How a forecast is produced

1. The UI sends `turbine_id`, a timezone-aware UTC `issue_time`, and a horizon of
   24 or 48 hours to `POST /api/forecasts`.
2. The backend chooses the newest ECMWF run that should have been available at the
   issue time using a conservative six-hour publication-delay assumption.
3. Open-Meteo returns hourly 10 m wind speed and 2 m air temperature in m/s and °C.
4. The backend derives `month` and meteorological `season` from each valid time.
5. The trusted local model for each turbine predicts `power_normalized`.
6. The API returns the weather, prediction, model version, run provenance, cache
   status, and warnings for every forecast hour.

Example request:

```bash
curl -X POST http://127.0.0.1:8080/api/forecasts \
  -H 'Content-Type: application/json' \
  -d '{
    "turbine_id": "turbine_1",
    "issue_time": "2026-01-31T00:00:00Z",
    "horizon_hours": 24
  }'
```

Valid turbine selections are `turbine_1`, `turbine_2`, and `both`. The `both`
selection returns two independent series plus their mean normalized output. It is
not total farm power in MW because turbine ratings and the normalization formula
were not supplied.

## Weather API

The application uses the free
[Open-Meteo Single Runs API](https://open-meteo.com/en/docs/single-runs-api):

- weather reference point for both turbines: `43.5381, 79.4658` (nearest station);
- endpoint: `https://single-runs-api.open-meteo.com/v1/forecast`;
- model: ECMWF IFS HRES, requested as `ecmwf_ifs`;
- variables: `wind_speed_10m` and `temperature_2m`;
- units: metres per second and degrees Celsius;
- timezone: GMT/UTC;
- no API key is required.

Requests are cached by the complete URL parameters for 15 minutes. Transient 429
and server errors use bounded retries. If the preferred run is unavailable, the
backend can use a valid cached response or one ECMWF run six hours older. A stale
cache or older run is explicitly marked as fallback data in the response.

Open-Meteo states that a global run normally needs about 4–6 hours after
initialisation to become available. The project therefore uses six hours as a
conservative assumption and exposes both `run_time` and assumed `available_at`.

## How the models were trained

There is one independent model per turbine. Training data covers measurements from
11 March 2023 through 31 January 2026.

### Data preparation

- The source CSV files contain ten-minute observations.
- The source `ID` column is removed.
- Only complete hours with six observations are aggregated.
- The target is normalized active power, `power_normalized`.
- Input features are `wind_speed_ms`, `temperature_c`, `month`, and `season`.
- The original timestamp is not passed to the estimator; it is only used to derive
  month, season, and chronological splits.
- Missing targets are not interpolated.

### Model selection

The training pipeline evaluates 15 scikit-learn candidates:

`DecisionTree`, `RandomForest`, `ExtraTrees`, `HistGradientBoosting`,
`GradientBoosting`, `AdaBoost`, `Bagging`, `LinearRegression`, `Ridge`, `Lasso`,
`ElasticNet`, `Huber`, `KNN`, `SVR (RBF)`, and `MLP`.

Selection is performed separately for each turbine:

1. A coarse `GridSearchCV` evaluates every candidate.
2. Five expanding chronological folds are used; data is never shuffled.
3. Candidates are ranked by mean cross-validation MAE.
4. The five best candidates enter the larger fine grid search.
5. January 2026 is evaluated independently and does not select hyperparameters.
6. After selection, the production pipeline is refitted on all available data
   through 31 January 2026 and saved with its manifest.

The selected production estimator for both turbines is `ExtraTreesRegressor`:

| Turbine | Training hours | CV MAE | January MAE | January RMSE | January R² | Trees |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Turbine 1 | 23,667 | 0.02567 | 0.02213 | 0.04774 | 0.97997 | 900 |
| Turbine 2 | 24,785 | 0.02251 | 0.02530 | 0.06348 | 0.96464 | 300 |

Both selected models use `max_depth=12`, `min_samples_leaf=2`, and
`max_features=1.0`. The random seed is 42. Model files are trusted local joblib
pipelines stored under `storage/models/production/<turbine_id>/` together with JSON
manifests containing the grids, metrics, versions, and provenance.

These metrics are **power-curve evaluation on measured weather**. They are not
evidence of end-to-end 24/48-hour weather forecast accuracy. That claim would
require evaluation against issue-time-safe archived weather forecasts and observed
future turbine power.

### Train the models again

Short smoke training:

```bash
uv run python -m ml.cli train --config config/training.json --smoke --n-jobs 1
```

Full CPU training using all available workers:

```bash
uv run python -m ml.cli train --config config/training.json --n-jobs -1
```

The current scikit-learn estimators are CPU-based; renting an NVIDIA GPU does not
accelerate this pipeline. Full models are written to `storage/models/production/`.
Smoke artifacts are isolated under `storage/models/production/smoke/`.

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript 7 strict mode, Vite 8 |
| Backend | Python, FastAPI, Pydantic, Uvicorn, HTTPX |
| Machine learning | scikit-learn, pandas, NumPy, joblib |
| Weather | Open-Meteo Single Runs API, ECMWF IFS HRES |
| Storage | JSON/joblib and a file-based weather cache; no database |
| Testing | pytest, pytest-cov, Vitest, React Testing Library, Ruff |
| Deployment | Multi-stage Docker build, one non-root container, one public port |

All Python and npm dependencies are pinned by `uv.lock` and
`frontend/package-lock.json`. Docker base images are versioned in the `Dockerfile`.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Process liveness |
| `GET` | `/api/ready` | Models, coordinates, and storage readiness |
| `GET` | `/api/turbines` | Turbine names and coordinates |
| `POST` | `/api/forecasts` | Synchronous 24/48-hour forecast |
| `GET` | `/docs` | Interactive Swagger documentation |

## Tests

Run all offline checks:

```bash
bash scripts/verify.sh
```

The script runs Ruff, backend and ML tests, coverage thresholds, frontend component
tests, TypeScript checking, and a production frontend build. Weather requests are
mocked in normal tests. Current enforced Python coverage thresholds are at least 85%
lines and 80% branches.

Run the production container smoke test separately:

```bash
bash scripts/docker-smoke.sh
```

The smoke test builds the image on a free local port and checks `/api/ready` and the
served SPA without spending a weather API request.

## Project layout

```text
backend/app/                 FastAPI, weather client, schemas, forecast service
frontend/src/                React UI and component tests
ml/                          data preparation, features, training, inference
config/training.json         model grids and training configuration
config/turbines.json         turbine coordinates
storage/models/production/   trusted trained pipelines and manifests
tests/                       backend and ML tests
Dockerfile                   single-container production build
```

More detail is available in [docs/setup.md](docs/setup.md),
[docs/testing.md](docs/testing.md), [ml/ML.md](ml/ML.md), and [GUIDE.md](GUIDE.md).
