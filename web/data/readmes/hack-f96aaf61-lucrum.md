# Lucrum

Lucrum is a procurement and inventory replenishment application for reviewing supplier order recommendations. The FastAPI backend analyzes sales, stock, goods in transit, and supplier terms. The React dashboard lets a manager inspect recommendations and approve selected positions. Orders remain pending until an employee explicitly approves them; the system does not submit orders to suppliers.

## Repository layout

```text
backend/       FastAPI application, calculation engine, XLSX loader, SQLite access
frontend/      React + TypeScript + Vite dashboard and its Node package files
data/raw/      Local partner XLSX inputs (ignored by Git)
data/sample/   Synthetic CSV examples and their documentation
docs/          API contract and calculation methodology
scripts/       Sample-data utility scripts
tests/         Backend pytest suite
requirements.txt
```

Frontend dependencies belong in `frontend/package.json` and `frontend/package-lock.json`. Install and run npm commands from `frontend/`. Python dependencies are managed separately in the root `requirements.txt`.

## Requirements

- Python 3.10 or newer
- Node.js 20.19+ (or 22.12+) and npm
- Git

## Install

Clone the repository and change into its root directory:

```sh
git clone <repository-url>
cd Lucrum
```

### Backend dependencies

Create and activate a virtual environment, then install the Python requirements.

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**macOS or Linux:**

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Frontend dependencies

```sh
cd frontend
npm ci
```

Copy the frontend API configuration template to `.env.local`:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env.local
```

**macOS or Linux:**

```sh
cp .env.example .env.local
```

The template sets `VITE_API_BASE_URL=http://127.0.0.1:8000`. In Vite development mode, the frontend sends same-origin `/api` requests through its dev proxy to FastAPI. The backend currently has no CORS middleware, so use the Vite proxy for local development.

## Run both services

Start the services in **two terminals**. Keep both running while using the dashboard.

### Terminal 1: FastAPI backend

From the repository root, activate `.venv` if it is not already active, then run:

```sh
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`; Swagger UI is at `http://127.0.0.1:8000/docs`.

### Terminal 2: Vite frontend

From the repository root:

```sh
cd frontend
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

The frontend checks the backend health endpoint and then loads the latest run and stock records. To create current recommendations, use the dashboard's calculation workflow. The backend calculation endpoint is `POST /api/calculate`.

## Verify the integration

With both services running, check the backend directly:

```sh
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"ok","api_version":"v1"}
```

The dashboard's configured API adapter sends requests through Vite to:

- `GET /api/health`
- `GET /api/orders`
- `GET /api/stock`
- `POST /api/calculate` (optional `warehouse` and `category` query filters)
- `POST /api/orders/approve`
- `GET /api/orders/export-1c`
- `POST /api/upload`

To build the frontend for production, run this in `frontend/`:

```sh
npm run build
npm run preview
```

Production hosting must route `/api` to FastAPI on the same origin or configure appropriate CORS middleware in the backend. CORS is not enabled by the current FastAPI application.

## Backend tests and utilities

Run backend tests from the repository root with the virtual environment active:

```sh
pytest
```

Generate deterministic synthetic CSV examples with:

```sh
python scripts/generate_sample.py
```

The sample generator writes under `data/sample/`; these CSV files are documentation/demo data and are not loaded by the XLSX adapter.

## Data and configuration

At startup, the backend scans `data/raw/` for recognized XLSX source workbooks. If inputs are missing or malformed, it logs a warning and uses its deterministic in-memory synthetic dataset. Keep confidential partner workbooks local; the directory is ignored by Git.

| Variable | Default | Purpose |
| --- | --- | --- |
| `LUCRUM_RAW_DIR` | `<repository>/data/raw/` | Directory containing partner XLSX workbooks |
| `LUCRUM_DB_PATH` | `<repository>/data/lucrum.sqlite3` | SQLite persistence path |
| `VITE_API_BASE_URL` | Set in `frontend/.env.local` to `http://127.0.0.1:8000` | Backend origin used as Vite proxy target in development; its presence also enables live API mode in the frontend |
| `VITE_API_PROXY` | `true` in development | Keep `/api` requests on Vite's proxy; set to `false` only when intentionally making direct browser requests to the backend |

The supplied IEK and SystemElectric books do not include a separate legal supplier directory or explicit lead times. The loader uses provisional `IEK` and `SYSTEMELECTRIC` range keys and defaults missing lead times to 30 days. These supplier keys are not verified 1C directory codes; provide an authoritative supplier crosswalk before using the CSV export as a production 1C import.

Successful XLSX uploads reload the complete raw-data directory and invalidate existing recommendations. Run a fresh calculation after an upload before approving or exporting positions.

## API and calculation documentation

- [API contract](docs/API.md)
- [Calculation methodology](docs/METHODOLOGY.md)
- [Frontend integration notes](frontend/README.md)
- [Synthetic sample data](data/sample/README.md)

