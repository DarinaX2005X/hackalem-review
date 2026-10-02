🇬🇧 English · 🇷🇺 [Русский](README.ru.md)

# Career Quest by Sudack

An AI career navigator for employees and HR, built by team Sudack for the HackAlem AI hackathon (Halyk Bank track, case "Career Quest"). An employee opens their profile and sees where they stand against the next grade, gets one to three recommended development activities with an explanation grounded in several factors, marks an activity as done and sees progress move. HR sees which skills sag across the company, who has no useful next step, who is dropping out of development, and what a new event would change before it is created.

The core of the solution is the quality and explainability of the recommendation, not the interface. Every recommendation is produced by a deterministic, inspectable scorer; an LLM only selects among the top candidates and writes the explanation, and everything it writes is validated against the facts before it is shown. When no LLM is available or its text is not grounded, the same facts are rendered by a template and labeled as such.

## Architecture

```
 Browser ──> Frontend (Next.js, :3000) ──> Go API (Echo + SQLite, :8080) ──> AI service (FastAPI, :8001) ──> OpenAI / NVIDIA (optional)
                                                │                                  │
                                       stores kit + imports,             stateless: scores, explains,
                                       auth (employee / HR),             simulates, estimates impact
                                       progress transactions
```

| Service | Directory | Responsibility | Docs |
| --- | --- | --- | --- |
| Frontend | `frontend/` | Login by role, employee screen (profile, trajectory, recommendations with "how it was calculated", "why not X", grade roadmap, complete button), HR screen (weak skills, no-step list, participation, dropout risk, draft-event constructor, import) | `frontend/README.md`, `frontend/FRONTEND.md` |
| Go API | `backend/` | Kit import on first start and HR upload of extra profiles, role tokens with a demo login, employee/HR access control, eligible-event checks, idempotent progress transactions, HR aggregates. Calls the AI service with the full context of one employee | `backend/BACKEND.md`, `backend/README.md` |
| AI service | `sudack-ai/` | Deterministic scoring, LLM selection and explanation with validation, template fallback, grade roadmap simulator, dropout risk, draft-event impact | `sudack-ai/README.md`, `sudack-ai/docs/api.md`, `sudack-ai/docs/AI_SERVICE.md` |

The AI service holds no data and no rights logic: Go sends the employee, the target grade profile, the event catalog and that employee's history in every request. Names are never sent to the model.

## Run everything with one command

Requires Docker with Compose v2.

```bash
cp .env.example .env          # optional: add OPENAI_API_KEY for LLM-written explanations
docker compose up --build
```

| URL | What |
| --- | --- |
| http://localhost:3000 | Frontend |
| http://localhost:8080/healthz | Go API health |
| http://localhost:8080/api/v1/auth/demo-token | Demo login (POST role + employee_id) |
| http://localhost:8001/docs | AI service OpenAPI |

Without an API key the system still works end to end: explanations come from the multilingual template and are labeled `template`. With a key, `LLM_MODEL` defaults to `gpt-4o`, which passed our live audits in Russian, Kazakh and English.

**Interchangeable LLM providers.** The AI service talks to every provider through the OpenAI chat-completions protocol, so a provider is a base URL, a key and a model name. `LLM_PROVIDERS` (default `openai,nvidia`) sets the failover order; `GET /providers` on the AI service shows the active chain; every recommendation names the engine that answered in `llm_provider` and `llm_model`. The chain runs against one deadline (`LLM_TIMEOUT`): a provider that fails fast hands the remaining time to the next one, and no provider except the last may use more than 75% of what is left. Verified live: with `LLM_PROVIDERS=nvidia,openai` the NVIDIA call fails, OpenAI answers, and the response reports `llm_provider: openai`. The hackathon NVIDIA key currently lists models but returns 401 on inference, so NVIDIA acts as a configured standby until the key is activated; details in `sudack-ai/docs/VERDICT_AUDIT.md`.

`FRONTEND_USE_MOCKS` in `.env` controls whether the frontend talks to the Go API (`false`, the default) or runs on the bundled synthetic dataset (`true`, a demo fallback). In the bundled-data mode the browser calls the AI service directly at `FRONTEND_AI_URL` for live LLM explanations, the "why not X" block, the grade roadmap, dropout risk and the draft-event constructor, so the AI layer is demonstrable without the Go API; if the AI service is down the screens fall back to the local calculation and say so. Employee names never leave the browser in that mode. **This direct browser-to-AI path is a demo fallback only:** the production path is frontend → Go API → AI service, with Go owning data, access control and the AI call, and that is what `docker compose up` runs by default. Keep `FRONTEND_USE_MOCKS=false` for the real flow; the fallback exists so the AI layer can still be shown if the Go API is unavailable.

### Running services separately

```bash
# AI service
cd sudack-ai && uv sync && uv run uvicorn main:app --port 8001      # tests: uv run pytest
# Go API
cd backend && go run ./cmd/migrate -data ../sudack-ai/docs/data && go run ./cmd   # PORT 8080; tests: go test ./...
# Frontend
cd frontend && npm install && npm run dev                           # NEXT_PUBLIC_API_URL, NEXT_PUBLIC_USE_MOCKS
```

## Demo scenario

1. **Log in.** The login screen issues a role token from the Go API: pick "I am an employee" and an employee, or "I am HR". The starter kit is imported into SQLite on first start. As HR, use **Import** to upload additional `employees.json` and `activity_history.csv` in the same format, which is how the jury's check profiles are loaded; ready-made trap profiles with expected answers are in `docs/jury-profiles/`, and uploaded employees appear in the login search immediately.
2. **Open an employee** (for example `E0028`). The profile shows role, grade, tenure, skills against the next-grade requirements, readiness, completed activities and missed ones.
3. **Read the recommendations.** One to three activities, each with a reason in the employee's language and an expandable "how it was calculated" block: the next-grade requirement, the skill gap with exact levels, participation history on these skills, the real gain the activity gives, and the score formula. A "why not X" block explains why the skill with the largest gap is not first when history or criticality says otherwise.
4. **Mark an activity as done.** Skill levels rise by the event's `gain` up to its `max_level`, readiness and the recommendation list update, and the completion is recorded once (idempotent).
5. **Open the roadmap.** The simulator lays out the activities to the next grade with dates from upcoming sessions and total hours, and lists the skills the current catalog cannot raise and why.
6. **Switch to HR.** Skills that sag most often, employees without a useful next step, participation per activity, dropout risk with reasons, and the draft-event constructor that predicts how many people a new event would move and at what cost per skill level.

## How a recommendation is made

For each eligible event (right role and grade, prerequisites met, not mandatory, not completed unless recurring, not in progress, has a future session) the AI service computes:

- **Effective gain** per skill from the dataset rule: `min(current + gain, max_level) - current`.
- **Weighted gap closed**: gain capped by the gap to the next grade, weighted 2.5 for the grade's critical skills, 1.5 for other required skills, 0.3 for growth outside the requirements.
- **Engagement**: a Laplace-smoothed completion rate of the employee's history on the same skills, with same-type events on other skills at 0.3 and entries older than a year at 0.6. No history gives 0.5.
- **Score** `= gap_closed × engagement^0.7`, then a light penalty so two consecutive picks do not target the same skill.

The top gap-closing candidates go to the LLM as plain facts (skill names and levels, critical and gap flags, event description, history counts) with no weights. Each returned reason must be in the requested language, mention history, and contain the exact current, required and resulting levels; otherwise the template explanation is used for that event and the item is labeled accordingly. Completions recorded after the employee's `last_review_date` are applied to their skills before scoring, so progress is visible before the next formal assessment.

Full formulas, worked examples and the live audit log are in `sudack-ai/README.md`, `sudack-ai/docs/api.md` and `sudack-ai/docs/VERDICT_AUDIT.md`.

## Beyond the must-haves

- **Why not X.** Counterfactual explanation for the skill a naive rule would pick.
- **Grade roadmap.** Dated plan to the next grade, hours, readiness path, and catalog gaps classified as no event, wrong audience, level ceiling, prerequisites, already completed, or no session. On the starter kit no employee can fully reach the next grade with the 40-event catalog, and the roadmap says exactly which events are missing.
- **Dropout risk.** Per-employee score from miss rate, recent misses, inactivity and stale in-progress items, with a suggested event format when the employee finishes one format and skips another.
- **Draft-event impact.** For an event HR is about to create: who can attend, who closes a gap, predicted completions, hours per closed skill level, rank against the existing catalog.

## Constraints from the brief

- Recommendations never rest on one field: every explanation carries the grade requirement, the gap, the history and the gain, and the calculation is shown.
- No public performance ratings, no points for mandatory processes (mandatory events are excluded from recommendations), no real personal data (the dataset is synthetic).
- Engagement data is visible to the employee and to HR only; access is split by role in the Go API.
- Tone is voluntary: missed activities are stated without blame, and no step is ever presented as an assignment.

## Repository layout

```
README.md                 this file
README.ru.md              Russian version
docker-compose.yml        full stack
.env.example              keys, auth secret and frontend mode
.gitattributes            LF line endings for scripts and Go sources (Docker and gofmt need them)
docs/jury-profiles/       three trap profiles in kit format with expected answers
frontend/                 Next.js app
backend/                  Go API (Echo, SQLite, sqlc)
sudack-ai/                FastAPI AI service, tests, dataset copy, API docs
```

## Verifying

```bash
cd sudack-ai && uv run pytest         # 70 tests: trap profiles, contract, dataset run over 200 employees, LLM validation
cd backend && go test ./...           # 5 integration tests on the starter kit with a fake AI
cd frontend && npm run lint && npm run build
```

Without a local Go toolchain the backend tests run in a container from the repository root:

```bash
docker run --rm -v "$PWD:/work" -w /work/backend golang:1.26.1-bookworm go test ./...
```

End-to-end through the Go API (demo login, profile, recommendations, roadmap, HR overview, jury import, idempotent completion, role checks) was verified against `docker compose up` on 2026-09-23; with `OPENAI_API_KEY` in `.env` recommendations return `source: llm` in 3–5 s.

Good employees to click through: `E0028` (Middle Backend, explanations in Kazakh), `E0002` (Middle Backend, Russian, five-step roadmap), `E0008` (Senior Frontend, English), `E0025` (Junior Data Analyst, Kazakh), and the trap profiles `E0901`–`E0903` after import. The interface itself is in Russian; the explanation language follows the employee's `preferred_language`.

A live one-call audit of the LLM layer for any kit employee: `cd sudack-ai && uv run python scripts/audit_verdict.py --live E0002`.

## Status

- AI service: complete and tested, including live LLM audits.
- Frontend: complete; talks to the Go API by default (`FRONTEND_USE_MOCKS=false`), with a bundled-data demo mode as a fallback.
- Go API: import of the kit on first start, HR upload of extra profiles and history, profile, recommendations, roadmap, preview, idempotent completion, HR overview with dropout risk, draft-event impact, role tokens with a demo login. Integration tests run against the starter kit with a fake AI.
