# Career Quest

**Rumba · HackAlem AI · Halyk Bank challenge**

## Executive Summary

Career Quest is a working career development tool built on the supplied synthetic challenge dataset. It connects an employee's grade requirements, assessed skills, activity history and eligible events. The result is 1–3 actionable recommendations with a projected effect. Employees can preview an event and complete it; the application then updates skills, gaps, readiness and the next recommendation. HR sees aggregate gaps and participation.

## Problem

An employee can see activities but cannot easily tell which one helps reach the next grade. A low skill is not necessarily a critical promotion gap. Previous missed or declined activities also matter when choosing a practical next step.

## Target Users

- **Employees:** view their own trajectory and plan a next activity.
- **HR:** see aggregate development gaps and activity uptake.

The included profiles are synthetic. This local demo does not implement production authentication.

## Core Workflow

`Profile → next-grade requirements → effective skills → gaps → eligible candidates → verified recommendation → what-if → completion → recalculation`

The web app opens `E0005` as its default demo profile. Enter any other dataset employee ID, or upload a JSON object containing a new `employee` and optional `history` rows in the supplied schema.

## Why This Is Not a Chatbot Wrapper

The domain engine calculates every skill level, gap, grade requirement, event effect and readiness value in deterministic Python code. The model can rerank a bounded set of prefiltered recommendation candidates or propose workflow event IDs and evidence factors. Verifiers check those proposals against domain facts, and recommendation explanations are assembled from checked evidence. The product still works without an API key.

## Multi-Factor Recommendation

Candidates must match role and grade, meet prerequisites, have an available session (or be self paced), and produce a useful next-grade skill gain after `max_level`. Mandatory, completed (except recurring `EV_036`), in-progress and ineffective events are excluded. Ranking considers critical and ordinary gap closure, number of requirements helped, gain, effort, and similar completed, missed or declined activities. It never selects an event solely because the employee's lowest skill is low.

## Explainability

Each recommendation carries `effects`, `requirements_helped`, `critical_gap_units_closed`, `gap_units_closed`, `history`, projected readiness, factor keys and a fact-based explanation. Similar history is shown as counts. The model does not get names, free-text employee biography or raw activity records: only structured candidate evidence.

## Architecture

Modular monolith, Python standard library server and a responsive vanilla HTML/CSS/JS client:

| Module | Responsibility |
| --- | --- |
| `career_quest/engine.py` | Load dataset, replay post-review completions, calculate trajectory, candidates, simulation and completion |
| `career_quest/recommend.py` | Multi-factor ranking, optional bounded OpenAI reranking, strict proposal verification and fallback |
| `career_quest/api.py` | JSON endpoints, aggregate HR view, atomic persistence of local changes |
| `career_quest/workflow.py` | Bounded AI/deterministic proposals, projected-state compiler and simulator-backed expected effects |
| `career_quest/workflow_runtime.py` | Canonical execution state, observations, factual trace, revalidation and replan |
| `web/index.html` | Employee and HR views, what-if modal, completion and profile upload |

## Career Workflow Execution Runtime

The employee screen can create a persisted next-grade workflow of up to three activities: `Goal → compiled verified workflow → user-confirmed action → observation → check → replan → DONE`. A proposal contains only event IDs and evidence factor keys; the compiler independently verifies eligibility, requirements, dataset gains and caps, critical-first priority and marginal value on each projected state. The deterministic planner uses the same compiler when no key is configured or an AI proposal fails or times out. Activities are followed by `CHECK` and `REASSESS`; later steps remain tentative. Confirming the current activity commits it through the domain engine, reads fresh skills, appends an observation and revalidates the tail. Completing another eligible activity through the existing endpoint also triggers observation and replan. The trace and completed prefix remain intact. Readiness is a forecast until observed after completion; achieving all requirements marks `DONE` without changing grade. Workflows, observations and trace are restored after server restart. API details are in [docs/API.md](docs/API.md).

In the verified workflow demo, initial readiness is **94%** and the compiled forecast is **94 → 96 → 98 → 100%**, starting with planned activity `EV_007`. Completing alternative activity `EV_006` produces **96% actual readiness**, marks the old tail `DIRTY`, and replans the remaining activities as `EV_036 → EV_036`. The workflow reaches `DONE` at **100%**. These values describe the reproducible demo state, not rules hardcoded into the planner.

API contracts are in [docs/API.md](docs/API.md). Dataset details are in [docs/DATASET.md](docs/DATASET.md).

## Model Proposes, Runtime Verifies

When `OPENAI_API_KEY` is set, the recommendation API sends up to 12 compact candidate feature objects to [`gpt-4.1-mini`](https://developers.openai.com/api/docs/models/gpt-4.1-mini) by default (`OPENAI_MODEL` can override). It requests [strict JSON](https://developers.openai.com/api/docs/guides/structured-outputs) containing 1–3 event IDs and factor keys, with an 8-second network timeout. The recommendation verifier rejects unknown, duplicate, ineligible or ineffective events; unsupported skills, requirements, gain or `max_level`; and fewer than three distinct evidence factors. Explanations are built from verified fields. If the model call or verification fails, a deterministic top-three fallback responds. The OpenAI workflow proposal path is also supported when `OPENAI_API_KEY` is configured; the same workflow compiler and verifier validate AI proposals. Deterministic workflow fallback is fully operational and was used in the verified release gate. Live OpenAI workflow planning was not part of the final release-gate run.

## What-If Simulation

The what-if endpoint applies the selected event to a copy of effective skills and returns before/after readiness, gaps and skill levels. It does not append history or mutate the employee. The UI presents the comparison before offering completion.

## HR View

The HR endpoint and screen show common next-grade skill gaps, grade counts, average assessed skill levels, activity participation/completion counts, and the count of employees without a candidate recommendation. There is no public employee leaderboard.

## Data

The real starter kit is committed in `data/`: `employees.json` (200 profiles), `events.json` (40 events), `skills.json` (60 skills and 8 roles × 4 grades), `activity_history.csv` (2,743 rows), and the original English, Russian and Kazakh READMEs. The snapshot date is 2026-10-01; the starter kit says to treat it as today. Employee skill assessments are dated; completed events after `last_review_date` are replayed to calculate current skill levels. Apple metadata files were not used.

## Challenge Requirements Mapping

| Challenge requirement | Implementation | Evidence |
| --- | --- | --- |
| Employee profile and trajectory | Effective skills, next grade, requirements, critical gaps and readiness | `engine.py`; `GET /api/employees/{id}/trajectory` |
| 1–3 multi-factor AI recommendations | Prefiltered candidate features, optional OpenAI reranking, deterministic fallback | `recommend.py`; `GET /api/employees/{id}/recommendations` |
| Explain at least three factors | Verifier requires three distinct supported factor keys | `verify_proposals`; tests |
| Completion updates progress | Apply `gain` bounded by `max_level`; append history; recalculate | `POST /api/activity/complete`; browser flow |
| What-if | Clone skills and return before/after without mutation | `POST /api/activity/simulate`; test |
| HR view | Aggregate gaps, grades and participation, no leaderboard | `GET /api/hr/overview`; HR screen |
| Additional judge profile/history | Upload through API or web input without ID-specific logic | `POST /api/profiles`; test |

## Performance

Dataset-derived catalogs and indexes load once at startup; candidate filtering runs before the model call. On the local test environment, a direct HR overview calculation took about **0.03 s** for 200 employees and a deterministic recommendation for `E0001` took under **0.01 s**. These are local measurements, not a hosted UI guarantee. The OpenAI request has an 8-second timeout and falls back locally to stay within the challenge's 10-second recommendation target when the provider is slow or unavailable.

## Tests

Run `python -m unittest discover -s tests -v`. The current verified result is **26/26 tests passing**. The suite covers recommendation ranking and verification, fallback, uploaded profiles, completion, what-if immutability, workflow compilation and execution, alternative activity replan, `DONE`, and persistence across restart. Browser and HTTP smoke checks were also run locally.

## Privacy

Challenge people are synthetic. The HR endpoint returns aggregates and no leaderboard. The local server is a demo and has no login or role authorization; protect employee and HR endpoints with organization identity and access control before connecting real personnel data. Local mutations live in ignored `state/changes.json`.

## Run Locally

Requires Python 3.10+; no pip dependencies.

```powershell
python -m career_quest.api
```

Open <http://127.0.0.1:8000>. Optionally set `OPENAI_API_KEY` and `OPENAI_MODEL` before launch to enable AI recommendation reranking and workflow proposals. Without a key, deterministic recommendations and workflows work end to end. `PORT` and `HOST` can override the default `127.0.0.1:8000` bind address.

## Demo

The default UI profile is `E0005`. For a separate reproducible core-flow example:

1. Open employee `E0001`: view Junior → Middle requirements and the critical API Design gap.
2. Open **What if?** on **System Design Fundamentals**: readiness is projected from 54.5% to 60.6% on the untouched starter state.
3. Complete it: the API writes history, updates two skills, removes that completed event from candidates and recalculates the next step.
4. Open **HR обзор** to see aggregate gaps and completion counts.
5. Upload a new JSON profile/history to exercise judge input without changing source code.

## Limitations

- No production authentication, employee-level authorization or hosted deployment is included.
- The next-grade trajectory follows the employee's current role; cross-role `career_goal` planning is not yet calculated.
- Readiness is a transparent skill-requirement percentage, not an HR promotion decision.
- The starter snapshot fixes event availability at 2026-10-01; the demo does not update calendars in real time.
- OpenAI recommendation reranking and workflow proposals are optional and have deterministic fallbacks. Live provider behavior needs an API key to verify.
