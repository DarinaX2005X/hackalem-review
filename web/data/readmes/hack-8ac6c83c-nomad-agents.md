# TaskForge — AI Challenge Coach

Hackathon project by team Nomad Agents. Full target design lives in [`MVP_SPEC.md`](MVP_SPEC.md) (source of truth); this README covers what's implemented today.

<img width="1919" height="878" alt="TaskForge screenshot" src="https://github.com/user-attachments/assets/708a63d3-ff99-4ddc-b5bb-7626addd85c7" />

https://taskforge-web.netlify.app/

## 1. Project name

**TaskForge** — "AI Challenge Coach: Business Task Readiness & Open Team Selection".

## 2. Brief description

Businesses posting challenges for student teams often write vague briefs ("we want an app to fix churn"). TaskForge helps a **business** turn that into a clear, complete task card, and lets **student teams** browse a shared catalog and tell which tasks are actually ready to work on. An AI coach flags missing information, asks clarifying questions, and a scoring rubric rates each task card 0–100.

## 3. Implementation details

- **Backend** (`api/`, .NET 9 Minimal API): `GET /api/health`, public `GET /api/actors` (demo businesses/teams). Actor headers (`X-Actor-Role`/`X-Actor-Id`) are validated per request with role/ownership guards. Full domain + repository layer over an in-memory store (actors, tasks, ratings, proposals, milestones, AI logs) with revision-safe updates. Swagger/OpenAPI in dev.
- **Frontend** (`web/`, Vite + React + TypeScript): all planned pages are built — role switcher, task-creation wizard (Draft → Clarify → Card → Rating → Published), catalog, task detail, proposal submission/review, leaderboard, and AI call logs.
- **Sample workspace fallback**: when the API is unavailable or lacks feature endpoints, the frontend transparently falls back to an in-browser demo dataset (`web/src/lib/demo.ts`) with a placeholder scoring heuristic, so the whole flow is clickable end-to-end without a backend. A banner always marks this mode clearly.

## 4. How the solution works

1. Pick a role via the role switcher (business or student team) — no login.
2. **As a business:** *My Tasks* → *New task* → write a draft → step through the wizard (AI clarifies → card → rating → publish).
3. The published task appears in the shared **Catalog**.
4. **As a team:** browse the catalog, open a task, submit a **proposal**.
5. **As the business:** review proposals, select/reject, confirm milestones → points go to the **Leaderboard**.
6. **AI Logs** shows every AI call made during clarification.

## 5. Technologies

- **Backend:** .NET 9 (Minimal APIs), C#, OpenAPI/Swagger, in-memory storage, Docker.
- **Frontend:** React 18, TypeScript, Vite 5, Tailwind CSS + shadcn/ui.
- **Planned:** OpenAI Responses API for the `analyze` clarification call, TanStack Query, orval-generated API client.

## 6. Project architecture

```
React SPA (Vite, :5173) ──HTTPS/JSON──► .NET 9 Minimal API (:8080)
        │            X-Actor-* headers        │
        └───── falls back to sample data ◄────┘
               (web/src/lib/demo.ts) when a route is unavailable
```

- `api/Features/<Feature>/` — one folder per backend feature (`Health`, `Actors` today).
- `api/Infrastructure/InMemory/` — process-local state, cleared on restart.
- `web/src/pages/`, `web/src/components/` — routed pages and UI, hand-rolled router in `App.tsx`.
- `web/src/lib/http.ts` — fetch wrapper adding actor headers + API→sample fallback.
- `web/src/lib/demo.ts` — in-memory stand-in for backend logic used only in fallback mode.

## 7. Installation and setup

Requires **.NET 9 SDK** + **Node.js**, or **Docker + Docker Compose**.

**Docker Compose (recommended):**
```sh
cp .env.example .env   # optional
docker compose up --build
```
API on `localhost:8080`, web on `localhost:5173`.

**Run directly:**
```sh
dotnet run --project api/TaskForge.Api.csproj   # API on :8080

cd web && npm ci && npm run dev                 # web on :5173
```

No credentials or API keys are required to run what exists today.

## 8. How to test the solution

1. `docker compose up --build`, open `http://localhost:5173`.
2. Pick **Tamaq Café Chain** (business) → *My Tasks* → *New task* → paste a short draft (e.g. "We are a café chain. Customers stop coming back and we don't know why.").
3. Run through the wizard: Analyze → answer clarifying questions → edit card → confirm twice.
4. Publish and open **Catalog** — compare against the two seeded sample tasks.
5. Switch to **Byte Nomads** (team), open a task, submit a proposal.
6. Switch back to the business, Select/Reject the proposal, confirm a milestone → check the **Leaderboard**.
7. Open **AI Logs** to see the recorded call from step 3.
8. Verify the backend directly: `curl http://localhost:8080/api/health` and `http://localhost:8080/swagger/`.

## 9. Data and integrations

- **Current:** singleton in-memory store on the API; all data is lost on restart. Sample data (businesses, teams, tasks, proposals) lives in browser memory and resets on reload.
- **Planned:** OpenAI Responses API (`POST https://api.openai.com/v1/responses`) for the `analyze` call with validation, retry, and deterministic fallback; `demo`/`full` seed profiles.

## Limitations

- No durable persistence, no real OpenAI integration yet, no deterministic rating engine (sample mode uses a placeholder heuristic), no auth, no automated tests, not yet deployed.
