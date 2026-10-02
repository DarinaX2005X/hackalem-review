# ÖRLE

**AI Career Intelligence**

*Your growth. Your path. Your next move.*

ÖRLE is our solution for the Career Quest case in the Halyk Bank track of HackAlem AI.

## Full local MVP

The full ÖRLE MVP is run locally using the **[Quick Start](#quick-start)** instructions.

Judges and reviewers who want to evaluate the complete solution should run ÖRLE locally with the official Career Quest dataset. The local version includes:

- the official dataset;
- Career Readiness Engine;
- Recommendation Engine;
- trained ML Engagement Model;
- What-if simulation;
- Complete Activity with live reranking;
- HR Analytics; and
- development bottleneck detection.

Follow the **[Quick Start](#quick-start)** instructions to run the full version.

ÖRLE is an explainable career-development navigator built for the official Career Quest case and dataset. It combines four deliberately separate layers:

```text
Official role requirements + employee skills
                    ↓
             Career Gap Engine
                    ↓
       deterministic eligibility + ranker
                    ↓
       bounded ML engagement adjustment
                    ↓
    grounded recommendation evidence + what-if
```

Rules determine **what the employee needs**. The ML model estimates **which already-relevant activity the employee is likely to complete**. An LLM, if added later, may only verbalize the evidence; it must never select or rank an activity.

## Implemented product

- Official JSON/CSV loading with schema and relationship validation.
- Support for additional official-format employees and history rows.
- Current-to-target career resolution using the dataset's grade order: `Junior → Middle → Senior → Lead`.
- Readiness against exact role/grade requirements, including the official missing-skill rule (`level = 0`).
- Deterministic eligibility, prerequisite checks, completion suppression, and recurring `EV_036` support.
- Explainable deterministic ranking with stored score components.
- A language-free trained engagement model used only as a bounded multiplier.
- Failure-safe deterministic ranking when ML is missing, invalid, or unavailable.
- In-memory what-if and completion flows using official `gain` and `max_level` rules.
- Live React employee and HR dashboards backed by FastAPI.
- Official-data HR analytics and development-bottleneck detection.

The source dataset is read-only. Session completions live only in backend memory and reset when the server restarts.

## Career Gap Engine

For target requirement `i`:

```text
achievement_i = min(current_level_i / required_level_i, 1)
weight_i      = 2 when the dataset marks the skill critical, otherwise 1

readiness = 100 × Σ(weight_i × achievement_i) / Σ(weight_i)
```

The response also includes every current/required level, numeric gap, satisfied requirement count, total requirement count, and critical gaps. A missing skill is level `0`, exactly as specified by the official dataset README.

When no explicit career goal exists, the target is the next grade for the employee's current role. A Lead without a goal is measured against the current Lead profile.

Skill state starts with the last assessment and applies official completed activities dated after `last_review_date`, because those gains are not yet reflected in the assessment snapshot. Runtime completions are then layered on top.

## Eligibility

An activity is a recommendation candidate only when all of these are true:

- it is voluntary (`mandatory = false`);
- its target roles include the career target role;
- its target grades include the career target grade;
- every prerequisite is satisfied using current effective skills;
- it has a future session or is self-paced;
- it improves at least one current target-grade gap after `max_level` is applied; and
- it has not already been completed, except for the officially recurring `EV_036`.

## Deterministic recommendation score

Every eligible candidate receives a 0–100-oriented additive career score:

```text
career_score =
    35 × weighted_gap_closed / weighted_total_gap
  + 20 × critical_gap_closed / total_critical_gap
  + 15 × usable_gain / configured_relevant_gain
  + 25 × min(readiness_delta / 10, 1)
  +  5 × relevant_activity_type_completion_rate
```

Critical gap units use the same weight of `2`; standard gap units use `1`. `usable_gain` is capped by both the employee's remaining gap and the event's official `max_level`. With no finalized same-type voluntary history, the history rate is neutral `0.5`.

The deterministic score remains the primary signal and is returned alongside all five components. The top recommendation also includes a component-level comparison with the runner-up.

## ML Engagement Model

The trained classifier estimates:

```text
P(employee completes a voluntary activity)
```

The final language-free artifact is `ml/artifacts/engagement_model_language_free.joblib`. `preferred_language` was removed from model features and is never exposed as recommendation evidence.

For a valid probability `p`:

```text
engagement_multiplier = 0.90 + 0.20 × p
final_score           = career_score × engagement_multiplier
```

Therefore ML influence is strictly bounded to `[0.90, 1.10]`. Eligibility and career relevance are already established before prediction. A missing artifact, unknown value, exception, NaN, infinity, or out-of-range probability produces multiplier `1.0`; deterministic recommendations continue normally.

Read-only dataset/model resources and repeated predictions are cached. The model is never retrained at API runtime.

## What-if and completion

Simulation copies the employee's effective skill state in memory and applies each event effect:

```text
projected_level = min(current_level + gain, max_level)
```

It returns skill-by-skill before/after values, readiness before/after/delta, and critical gaps before/after. It never mutates an official file.

Completing an eligible activity applies that simulation to session state, records a session completion, recalculates readiness, suppresses a completed non-repeatable activity, and reranks the next 1–3 activities.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Service health |
| GET | `/employees` | Real employee selector summaries |
| GET | `/employees/{employee_id}` | Effective employee profile |
| GET | `/employees/{employee_id}/career` | Target, readiness, requirements, and gaps |
| GET | `/employees/{employee_id}/recommendations` | Top 1–3 ranked activities and evidence |
| GET | `/employees/{employee_id}/history` | Enriched official + runtime history |
| POST | `/employees/{employee_id}/simulate/{event_id}` | Official in-memory what-if |
| POST | `/employees/{employee_id}/complete/{event_id}` | Session completion and recalculation |
| GET | `/hr/analytics` | Workforce readiness, gaps, outcomes, and bottlenecks |

FastAPI generates interactive docs at `http://localhost:8000/docs`.

## Frontend

The original visual design is preserved. The normal application path now uses real API values for:

- the 200-person employee selector;
- official target role/grade and capability requirements;
- weighted readiness, requirement counts, and critical gaps;
- recommendation cards, score evidence, ML probability, and runner-up comparison;
- what-if previews and complete-activity recalculation;
- enriched participation history; and
- HR metrics, charts, guidance table, and development bottlenecks.

No mock data is used by the active employee or HR routes.

## Quick Start

Python 3.11+ and Node.js 20+ are recommended.

```powershell
python -m venv backend/.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Verification

```powershell
backend\.venv\Scripts\python -m pytest backend\tests ml\tests -q
cd frontend
npm run build
```

The tests cover additional official-format profiles, cold-start recommendations, ML failure, missing skills, mandatory suppression, prerequisites, gain/max-level simulation, completion effects, reranking, and critical-skill prioritization.

## Key modules

- `backend/app/services/data_loader.py` — official schema loading and career-target resolution
- `backend/app/progress/service.py` — Career Gap Engine
- `backend/app/recommendation/engine.py` — eligibility, deterministic score, simulation, explainability
- `backend/app/services/engagement.py` — safe ML adapter
- `backend/app/services/career_service.py` — runtime state and application orchestration
- `backend/app/analytics/service.py` — HR aggregates and bottlenecks
- `ml/` — language-free engagement model, training/evaluation, prediction interface
- `frontend/src/services/api.ts` — frontend API boundary

---

Built for the HackAlem AI Hackathon, Halyk Bank track. The dataset is synthetic and contains no real people or companies.
