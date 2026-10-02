# Akim AI

**Akimator.AI — «Аким на 5 часов»** is a hackathon MVP: a web simulator where a player becomes the mayor of Astana for five hours, spends a fixed virtual budget, and sees how five city decisions change quality of life.

## Problem

City decisions are usually presented as slogans. Residents and officials rarely see a simple, comparable picture: what happens to transport, parks, schools, safety, and public services if the budget is spent one way instead of another.

## Solution

The player must approve **exactly five measures** — one per direction — within **100 billion ₸**. A deterministic simulation engine recalculates city indicators and an **AQOL** score. Optional AI text then *explains* the result; it never calculates the score.

## Features

- Five decision cards: transport, green zones, social infrastructure, safety, city services
- Live budget: total / used / remaining
- Simulation blocked when the budget is exceeded
- Deterministic AQOL score (0–100)
- Progress bars for five city indicators
- Strengths, risks, and consequences
- Reset scenario
- Mock AI analysis if no API key is set

## Architecture

```text
Frontend (HTML / CSS / JS)
        ↓
     FastAPI
        ↓
 Simulation Engine
        ↓
    AQOL Score
        ↓
   AI Analysis (or mock fallback)
```

1. The browser collects five selected measures.
2. `POST /api/simulate` validates the payload.
3. `simulation.py` applies costs and effects from `data/city_data.json`.
4. Indicators are clamped to 0–100 and AQOL is rounded to an integer.
5. Analysis text is generated from the numeric result. If `OPENAI_API_KEY` is present, the app may call an LLM; otherwise it uses a built-in mock.

## Simulation Engine

Starting indicators (synthetic Astana baseline):

| Indicator | Key | Baseline |
|-----------|-----|----------|
| Transport | `transport` | 48 |
| Green zones | `green` | 42 |
| Social infrastructure | `social` | 50 |
| Safety | `safety` | 45 |
| City services | `services` | 52 |

Each measure has a cost and a set of effects (including possible side effects on other indicators). Effects are added to the baseline, then clamped to `0–100`.

Budget rule: the sum of five measure costs cannot exceed `100_000_000_000` ₸.

## AQOL Score

**Astana Quality of Life Score** is computed only by the engine:

```text
AQOL = round(
  transport * 0.25 +
  green     * 0.15 +
  social    * 0.20 +
  safety    * 0.20 +
  services  * 0.20
)
```

AI does not invent this number.

Color bands in the UI:

- high: AQOL ≥ 70
- mid: 55–69
- low: below 55

## Dataset

`data/city_data.json` is a synthetic dataset: city name, total budget, baseline indicators, weights, and three measures per category. No external database is used.

## Installation

From the project folder:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Running locally

```bash
uvicorn app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

The app works without an AI key. To optionally enable live analysis later, create a `.env` file (not committed) with `OPENAI_API_KEY=...` and load it in your environment.

API:

- `GET /` — dashboard
- `GET /api/city` — measures and budget
- `POST /api/simulate` — `{ "decisions": { "transport": "...", "green": "...", "social": "...", "safety": "...", "services": "..." } }`

## Example Scenario

A balanced package that stays under 100 billion ₸:

- Transport: dedicated bus lanes (20)
- Green zones: new district park (20)
- Social: school repairs (15)
- Safety: smart lighting (10)
- Services: better utilities (20)

Total: **85 billion ₸**. The engine updates indicators, computes AQOL, then returns strengths, risks, and consequences.

An all-premium package (30+30+30+30+30) costs 150 billion ₸ and is rejected.

## Future Development

- Real city open data instead of synthetic JSON
- More than three measures per category and multi-year budget
- Map of districts and spatial effects
- Comparison of two scenarios side by side
- Official briefing PDF for hackathon jury
- Live LLM analysis with a safer, structured prompt
