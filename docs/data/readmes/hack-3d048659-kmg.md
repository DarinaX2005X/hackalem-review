# Ветропрогноз — агентный почасовой прогноз выработки ВЭС на 48 часов

Windmill management, hourly power forecasting, and an interactive 3D map.
React/TypeScript frontend, Python API, MongoDB storage, and Celery workers with
Redis transport. Power is normalized to `[0, 1]`; all displayed times are UTC.

## Run the complete application

From the repository root, with Docker Desktop / Docker Compose running:

```bash
docker compose up --build -d --wait
```

Open [http://127.0.0.1:8091](http://127.0.0.1:8091). MongoDB and Redis stay on the
private container network. The first startup imports the bundled two-windmill
archive into MongoDB; subsequent starts preserve uploaded data and models.

## Windmills and measurements

Open **Ветряки и данные** to add a windmill with its name and coordinates. It
immediately becomes selectable and appears on the 3D map, even without data.
Upload hourly CSV measurements or correct an individual hour:

```csv
time,power
2026-03-01T00:00:00Z,0.42
2026-03-01T01:00:00Z,0.38
```

Imports update matching hours and preserve other measurements. Every changed
import automatically queues retraining and a new 48-hour forecast. The page
shows queued/running/completed/failed jobs, input revisions, and validation
metrics. Previous model versions and forecasts remain available.

The new per-windmill model uses power history and calendar features, without
inventing weather for new sites. Start with at least five consecutive days of
hourly measurements. Insufficient data is reported explicitly and remains saved
for the next upload. Forecasts begin relative to the latest measured hour;
training on old data does not produce a forecast for today's date.

## Bundled archive

The initial archive contains 29 forecast origins (January 30–February 27, 2026),
48 predictions per turbine per origin, and January measurements for two turbines.
These original weather-based forecasts are retained. The original offline
research/model scripts are documented in [backend/README.md](backend/README.md).

## Frontend development

Run the backend, database, workers, and scheduler in containers while Vite runs
on the host:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d backend worker scheduler
cd frontend
npm ci
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The development override
publishes the API on loopback port 8000 for Vite's existing proxy. Use Node 22.12+
(Node 24 recommended). Stop any older API using port 8000 before this setup.

## Documentation and checks

- [Data architecture, collections, training and API](DATA_ARCHITECTURE.md)
- [Deployment, persistence and integration checks](DEPLOYMENT.md)
- [Frontend source boundaries and commands](frontend/README.md)

```bash
cd frontend
npm test
npm run build
npm run docker:check
```

Backend unit tests run with `python -m pytest -p no:cacheprovider` from `backend/`
after installing `requirements.txt`. Real MongoDB integration tests are enabled
with `MONGODB_TEST_URI`; they create and remove isolated `windfarm_test_*`
databases. See deployment instructions for running them inside the stack.
