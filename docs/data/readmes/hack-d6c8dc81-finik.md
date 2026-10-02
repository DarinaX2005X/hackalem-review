# Career Quest

Career Quest is an AI-powered employee development navigator that turns scattered HR activities into an explainable career trajectory. It analyzes an employee profile, current skills, target role/grade requirements, development history, and available activities to recommend 0–3 relevant next development steps with clear explanations.

## Problem

Employees are often offered disconnected trainings and events without understanding how they support career progression. HR also needs a clear view of recurring competency gaps and of employees who currently have no useful next step.

## Solution

```text
Employee profile → career target → skill gaps → eligibility filtering
→ multi-factor ranking → explanation → activity completion
→ updated skills, trajectory, and recommendations
```

The employee workspace presents this flow end to end. An HR workspace adds organization-level gap and participation analytics, plus a judge-data import flow whose employees use the same profile and recommendation engine immediately.

## Key Features

- Searchable employee selector with current role, grade, tenure, target role/grade, activity history, and career readiness.
- Target-skill view with current levels, gaps, and critical requirements.
- Up to three deterministic, ranked development recommendations with computed factors and explanations.
- Optional OpenAI wording for employee-friendly explanations, with deterministic fallback wording.
- Activity completion that applies valid skill gains, returns an updated profile, and refreshes recommendations without a page reload.
- HR overview of employee count, completed activities, common target-skill gaps, event participation, and employees without a recommended step.
- Multipart import of judge files (`employees.json`, `events.json`, `skills.json`, and `activity_history.csv`) with atomic validation.
- All starter and imported data is synthetic and processed locally by the backend.

## Recommendation Engine

Recommendation **selection is deterministic**; it never depends on an LLM.

1. Reconstruct current skills from the last assessment plus completed activities after `last_review_date`.
2. Resolve the employee's explicit career goal when valid, otherwise the next grade in the current-role ladder.
3. Calculate gaps against that target profile.
4. Exclude mandatory activities, wrong-audience activities, unmet prerequisites, unavailable scheduled activities, completed activities, and activities that cannot reduce a target gap.
5. Calculate useful target-gap reduction for every remaining activity.
6. Give extra weight to useful gains on critical target requirements.
7. Compare participation in similar activities.
8. Sort deterministically, then return the top 0–3 activities.
9. Produce deterministic explanations; optionally replace only their wording through the OpenAI explanation layer.

For a candidate activity, the implemented score is:

```text
10 × effective useful target-gap levels
+ 5 × effective useful levels on critical target skills
+ 2.5 × max(0, useful target skills addressed − 1)
+ 1 × min(completed similar activities, 3)
− 2.5 × min(missed / declined / dropped similar activities, 3)
```

`effective useful target-gap levels` is the portion of an activity's gain that reduces an unmet target requirement, bounded by both the remaining gap and the activity's maximum level. “Similar” means the historical and candidate activities develop at least one shared skill. This makes history meaningful while keeping direct, critical skill-gap reduction dominant, rather than simply recommending an activity for the lowest current skill.

## AI / OpenAI Usage

```text
Employee data
    ↓
Deterministic career analysis
    ↓
Eligibility and multi-factor scoring
    ↓
Top recommendations + computed facts
    ↓
OpenAI explanation layer (optional)
    ↓
Employee-friendly explanation
```

The backend uses the OpenAI Responses API only after deterministic selection. By default it uses `gpt-5-mini`, sends `store: false`, applies a 4.5-second timeout, and makes no retry attempts. It supplies only the calculated explanation context: current/target role and grade, selected activity identifiers/titles/types, relevant skill impacts, and similar-activity counts.

- OpenAI does **not** choose activities, calculate skills, alter eligibility, or change scores/ranking.
- The response is constrained to event-ID/explanation pairs and validated before use.
- If `OPENAI_API_KEY` is absent, the provider fails, or its output is invalid, the backend returns its deterministic explanations.
- HR analytics do not call OpenAI.

## Technologies

| Area | Implementation |
| --- | --- |
| Frontend | JavaScript, React 19, React DOM, Vite 8, and ESLint. |
| Backend | TypeScript, Node.js, Express 5, CORS, Multer, and `csv-parse`. |
| Validation and tests | TypeScript compiler, Vitest, Supertest, and Node's built-in test runner. |
| AI integration | OpenAI Node SDK and the OpenAI Responses API; `gpt-5-mini` by default when an API key is provided. |
| Data | Local JSON and CSV starter files; no database or external HR system is required. |

## Architecture

```text
React + Vite frontend
          │ REST / JSON + multipart import
          ▼
Express + TypeScript backend
          ├── Dataset and profile logic
          ├── Deterministic recommendation engine
          ├── Activity completion logic
          ├── Import validation
          ├── HR analytics
          └── Optional OpenAI explanation provider
                       │
                       ▼
                   OpenAI API
```

The backend holds an active dataset in memory. Imports and completions first calculate and validate prospective state, then replace the active state atomically. Restarting the backend reloads the starter dataset from `DATA_DIR` (the repository root by default).

## Data

The current synthetic starter dataset contains 200 employees, 40 development activities, 60 skills, 32 role profiles, and 2,743 activity-history records. Its snapshot date is `2026-10-01`.

- `employees.json` — employee profiles and assessed skills
- `events.json` — development activity catalog
- `skills.json` — skill catalog, proficiency scale, and role/grade requirements
- `activity_history.csv` — participation history

Judge imports can append or replace records according to [API_CONTRACT.md](API_CONTRACT.md). The backend validates the complete prospective dataset before changing active state; all data remains local and synthetic.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/employees` | List selectable employee profiles. |
| `GET` | `/api/employees/:employeeId` | Return an employee profile, target trajectory, skills, history, and readiness. |
| `GET` | `/api/employees/:employeeId/recommendations` | Return 0–3 ranked next development steps. |
| `POST` | `/api/employees/:employeeId/complete` | Complete an eligible activity and return updated profile/recommendations. |
| `GET` | `/api/hr/overview` | Return active-dataset HR aggregates. |
| `POST` | `/api/import` | Import one or more supported judge dataset files through the `files` multipart field. |

See [API_CONTRACT.md](API_CONTRACT.md) for complete request and response schemas, status codes, and import semantics.

## Local Setup

Prerequisites:

- Node.js **22.12+** and npm. The OpenAI SDK requires Node 22+, and the installed Vite version requires Node `^20.19.0` or `>=22.12.0`.
- An OpenAI API key is optional; the application is fully usable without one.

There is no root `package.json`; install and run each application from its own directory.

Terminal 1 — Backend:

```sh
cd backend
npm ci
npm run dev
```

Terminal 2 — Frontend:

```sh
cd frontend
npm ci
npm run dev -- --host localhost --port 5173 --strictPort
```

Open the frontend at [http://localhost:5173](http://localhost:5173). The backend listens at [http://localhost:8000/api](http://localhost:8000/api) by default.

For a production-style local backend start, build it first and then run `npm start` from `backend/`.

## Deployment

No deployed URL or deployment configuration is present in this repository. The documented target is local execution for the hackathon demo.

## Environment Variables

The backend reads environment variables directly from the process; it does not load a `.env` file itself. If your shell, IDE, or process manager loads `.env` files, this is a safe placeholder example (never commit real credentials):

```dotenv
# backend/.env — reference only; load it through your chosen environment runner
PORT=8000
CORS_ORIGIN=http://localhost:5173
DATA_DIR=/absolute/path/to/hack-d6c8dc81-finik
OPENAI_API_KEY=your_optional_key_here
OPENAI_MODEL=gpt-5-mini
```

| Variable | Used by | Default / behavior |
| --- | --- | --- |
| `PORT` | Backend | `8000`; must be an integer from 1 to 65535. |
| `CORS_ORIGIN` | Backend | `http://localhost:5173`. |
| `DATA_DIR` | Backend | Repository root, where the four starter data files reside. |
| `OPENAI_API_KEY` | Backend | Optional. Without it, no OpenAI provider is created and deterministic explanations are used. |
| `OPENAI_MODEL` | Backend | `gpt-5-mini` when unset or blank. |
| `VITE_API_BASE_URL` | Frontend | `http://localhost:8000/api` when unset. |

For example, set an optional key in PowerShell before starting the backend:

```powershell
$env:OPENAI_API_KEY = "your_optional_key_here"
npm run dev
```

## Tests

Backend commands (from `backend/`):

```sh
npm test
npm run typecheck
npm run build
```

The backend suite currently contains 49 tests. Frontend commands (from `frontend/`):

```sh
npm test
npm run lint
npm run build
```

## Demo Scenario

1. Open the frontend and enter the demo employee workspace.
2. Select `E0001` (Marat Yessenov), the starter profile exercised by the end-to-end backend test.
3. Show the current Junior Backend Engineer profile, target Middle Backend Engineer grade, readiness, and target-skill gaps.
4. Open the recommended next steps and point out the skill impacts, criticality, and participation-history factors.
5. Complete an eligible recommended activity.
6. Show the returned skill change, refreshed trajectory/history, and adapted recommendations.
7. Open **HR overview** to show real active-dataset gap counts, participation, and the no-step list.
8. Import a synthetic judge employee using the supported file names.
9. Return to the employee workspace and select the imported profile; it is served by the same normal profile and recommendation pipeline.

Avoid completing an activity before the recommendation discussion: in-memory state is intentionally updated for the rest of that backend session.

## Explainability / Design Decisions

- Recommendation selection, eligibility, and ranking remain deterministic and traceable.
- The LLM is a wording layer only, with a deterministic fallback.
- Every recommendation includes the calculated skill impacts, current/target grades, and relevant history counts.
- Activity completion and dataset import are atomic: invalid operations do not partially mutate active state.
- The frontend renders backend results and does not duplicate career or recommendation calculations.
- The MVP has no public employee leaderboard and uses synthetic data only.

## Project Structure

```text
.
├── frontend/                 # React/Vite employee and HR UI
│   ├── src/
│   ├── test/
│   └── package.json
├── backend/                  # Express/TypeScript API and business logic
│   ├── src/services/
│   ├── src/routes/
│   ├── test/
│   └── package.json
├── employees.json
├── events.json
├── skills.json
├── activity_history.csv
├── API_CONTRACT.md
└── README.md
```

## Limitations / Production Considerations

This hackathon MVP uses in-memory active state, so imports and completions reset when the backend restarts. Authentication and role-based authorization are outside the MVP, and the available event schema has no general recurrence field; completed activities are therefore not recommended again.

A production version could add persistent storage, SSO/RBAC, auditability, operational monitoring, and explicit recurrence metadata while retaining the same deterministic decision layer.
