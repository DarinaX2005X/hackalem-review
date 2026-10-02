# AKIM OS

## What It Is

AKIM OS is a hackathon-ready city management simulator: "Аким на 5 часов". A player receives a fixed budget of 100, chooses exactly five policy measures for Astana districts, and gets a deterministic quality-of-life score with transparent breakdowns and AI-style interpretation.

## Architecture

```text
Next.js
  -> REST
Django / DRF
  -> Scenario Validator
  -> Deterministic Simulation Engine
  -> Score + breakdown
  -> AI Agents
  -> Explanation / Recommendations
```

The LLM never calculates Score. Backend domain code calculates every number first; AI only interprets the resulting JSON. Without `LLM_API_KEY`, the app uses deterministic fallback analysis.

## Dataset And Methodology

Dataset version: `ASTANA_SYNTH_V1`. The canonical source is [city_config.json](backend/apps/simulator/data/city_config.json).

Final formula:

```text
Score = 0.7 * D_avg + 0.3 * D_min - N_crit
```

Effects are scaled by implementation lag: `full_effect * (8 - lag) / 8`. Synergies are applied after normal effects and are not lag-scaled. Indicators are clipped to `0..100`. A critical indicator is strictly below `40`; exactly `40` is not critical.

## API

- `GET /api/v1/health/`
- `GET /api/v1/config/`
- `GET /api/v1/districts/`
- `GET /api/v1/measures/`
- `POST /api/v1/scenarios/validate/`
- `POST /api/v1/scenarios/simulate/`
- `POST /api/v1/scenarios/{id}/analysis/`
- `GET /api/v1/leaderboard/`

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_city_data
python manage.py runserver 8000
```

SQLite is used by default. PostgreSQL can be enabled later with `DATABASE_URL`.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000/simulator`.

## District Map

Original SVGs live in `frontend/public/map_icons/` and are served directly by the frontend.
`frontend/lib/district-paths.json` contains the district paths extracted from those SVGs for click and keyboard targets.
The map sets the default district for new projects; per-project overrides and saved decisions keep their assigned districts.

With both dev servers running, run `npx playwright test` from `frontend/` to check mouse/touch/keyboard selection, district assignments, results and mobile layout. Tests use installed Microsoft Edge and mock scenario saving so the leaderboard stays unchanged.

## Running Tests

```bash
cd backend
pytest
python manage.py check

cd ../frontend
npm run lint
npm run build
```

## Example Scenario

Reference decisions:

1. `M7 -> Нура`
2. `M8 -> Нура`
3. `M10 -> Нура`
4. `M12 -> city`
5. `M5 -> Сарыарка`

Expected result:

- Baseline Score: `52.55768`
- Reference Score: `56.54307`
- Display delta: `+3.99`

## Project Structure

```text
backend/
  apps/simulator/domain/       pure validation and simulation logic
  apps/simulator/data/         canonical dataset
  apps/simulator/services/     AI interpretation facade
  apps/simulator/tests/        regression and API tests
frontend/
  app/                         Next.js App Router pages
  components/                  reusable simulator UI
  lib/                         API client, types, formatting
```

## Environment Variables

Optional backend variables: `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DATABASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`.

Frontend variable: `NEXT_PUBLIC_API_URL`, default `http://localhost:8000/api/v1`.

## Future Development

- Add richer scenario comparison.
- Add authenticated team rooms.
- Connect a production LLM provider through the existing AI facade.
- Export presentation mode to PDF/PPTX.
