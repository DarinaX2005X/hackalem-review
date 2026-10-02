# Career Quest · AIVIOM

AI-powered career development navigator for **HackAlem AI · Case 1 — Halyk Bank**.

> **Deployed demo:** **https://career.aiviom.ai**

Career Quest helps an employee understand the gap between their current profile and a target role/grade, build a feasible development path, receive explainable AI-assisted recommendations, submit evidence of completed work, and see verified progress. Managers, advisors, supervisors, and HR receive role-specific workflows for approvals, assignments, analytics, imports, and audit.

The repository contains the complete application, source dataset, demo seed, API/server code, frontend, tests, Docker configuration, and technical documentation required to run and inspect the solution independently.

---

## 1. What the solution does

The main product flow is:

```text
Employee profile
    ↓
Target role / grade
    ↓
Skill gaps and eligibility rules
    ↓
Roadmap + explainable recommendation
    ↓
Preview / plan / completion evidence
    ↓
Advisor or manager verification where required
    ↓
Skill recalculation + XP/reward ledger
    ↓
HR analytics + audit trail
```

The application supports the following demo roles:

- **Employee** — profile, goal, roadmap, recommendations, plan, completion requests, side quests, help requests, rewards.
- **Advisor** — completion verification and side-quest review.
- **Manager** — team-scoped actions, assignments, resource approvals, help resolution, analytics.
- **Supervisor** — policy approvals, audit access, analytics.
- **HR** — organization-wide analytics, import preview/commit, assignments, audit.

The application intentionally separates **recommendation** from **state-changing actions**. A preview or AI recommendation does not grant skills. Skills/XP change only after a permitted completion or accepted side quest.

---

## 2. Architecture

Career Quest is implemented as a **TypeScript modular monolith**.

```text
Browser
  │
  │ React 19 + Vite 6
  ▼
Express 4 application server
  │
  ├── Session / demo workspace isolation
  ├── Server-side RBAC and scope checks
  ├── Domain calculations
  │     ├── effective skills
  │     ├── gaps
  │     ├── eligibility
  │     ├── preview
  │     ├── roadmap
  │     └── analytics
  ├── Workflows
  │     ├── completions
  │     ├── assignments
  │     ├── side quests
  │     ├── approvals
  │     ├── rewards
  │     └── audit
  ├── Import validation
  └── AI recommendation layer
        ├── direct OpenAI API when OPENAI_API_KEY is configured
        ├── team judge gateway when configured
        └── explicit rules fallback when live AI is unavailable
  │
  ▼
SQLite / better-sqlite3
```

### Main source directories

| Path | Responsibility |
|---|---|
| `src/client/` | React UI, screens, API client, localization |
| `src/server/` | Express API, sessions, RBAC, SQLite persistence, workflows, audit, AI budget/gateway |
| `src/domain/` | Pure domain calculations, roadmap, analytics, import validation |
| `src/ai/` | Recommendation orchestration and external opportunity search |
| `src/shared/` | Shared types and RU/KK/EN localization contracts |
| `data/source/` | Source case dataset |
| `data/demo/` | Demo/import fixture |
| `tests/` | Domain, server, integration, AI and localization tests |
| `docs/` | Detailed technical/reviewer documentation |

For a deeper implementation-oriented description, see [`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md).

---

## 3. Technologies

### Runtime and application

- **Node.js 20.19+**; Node 22 LTS is recommended.
- **TypeScript 5.8**
- **React 19**
- **Vite 6**
- **Express 4**
- **SQLite** through `better-sqlite3`
- **Zod 3** for request/data validation
- **OpenAI Node SDK 6** for optional live AI
- **csv-parse** for source/import parsing
- **Lucide React** for UI icons

### Development and delivery

- npm + lockfile (`package-lock.json`)
- Node built-in test runner executed through `tsx`
- Docker / Docker Compose
- Local SQLite persistence

Exact dependency versions are pinned by `package-lock.json`.

---

## 4. Requirements

For a normal local run:

- Git
- Node.js **>= 20.19**
- npm
- Internet access while installing npm dependencies

No separate database server is required.

On systems where `better-sqlite3` cannot use a prebuilt binary, compilation may additionally require:

- Python 3
- `make`
- a C/C++ compiler

The provided Docker image installs the native build toolchain automatically.

---

## 5. Installation

### Option A — local Node.js

```bash
git clone https://github.com/BAITC-Hacks/hack-6ee0248f-aiviom.git
cd hack-6ee0248f-aiviom
npm ci
```

Optional environment configuration:

```bash
cp .env.example .env
```

A `.env` file is **not required** for the basic demo flow.

### Option B — Docker

```bash
cp .env.example .env
docker compose build
docker compose up -d
```

The supplied Compose configuration publishes the application on:

```text
http://127.0.0.1:3500
```

The container itself listens on port `3000`.

---

## 6. Running the application

### Development mode

```bash
npm run dev
```

### Production-style local run

```bash
npm run build
npm start
```

By default open:

```text
http://127.0.0.1:3000
```

Health check:

```bash
curl http://127.0.0.1:3000/health
```

Expected shape:

```json
{
  "ok": true,
  "service": "career-quest",
  "version": "development"
}
```

---

## 7. Environment variables

All supported variables are listed in `.env.example`.

| Variable | Default / example | Purpose |
|---|---|---|
| `PORT` | `3000` | HTTP port used by the Node server |
| `HOST` | `127.0.0.1` locally | Interface to bind to |
| `DATABASE_PATH` | `.runtime/career-quest.sqlite` | SQLite database file |
| `OPENAI_API_KEY` | empty | Optional server-side live OpenAI access |
| `OPENAI_MODEL` | `gpt-5.4-mini` | Model requested by the AI layer |
| `AI_BUDGET_USD` | `30` | Conservative application-side AI reservation budget |
| `DEMO_ENABLED` | `true` | Enables demo workspace/session APIs |
| `JUDGE_GATEWAY_URL` | `https://career.aiviom.ai` | Team recommendation gateway; use `off` to disable |
| `AI_MODE` | unset | Set to `offline` to disable remote AI calls |
| `TRUST_PROXY` | usually unset locally | Set by deployment when running behind a trusted proxy |
| `RELEASE_SHA` | `development`/`local` | Version returned by `/health` |

### AI behavior

The recommendation endpoint has explicit modes:

- `live_ai` — validated response from a live model.
- `cached_live_ai` — validated cached live result.
- `rules_fallback` — deterministic domain fallback; not presented as an LLM response.
- `unavailable` — no meaningful recommendation can be produced, e.g. no goal or no gaps/candidates.

A personal OpenAI key is therefore not required to inspect the main product and domain flows.

Never commit `.env`, API keys, SQLite runtime files, logs, or tokens. The repository `.gitignore` excludes these files.

---

## 8. Main API surface

The browser UI uses the same server API that can be inspected manually.

Key endpoints include:

- `GET /health`
- `GET /api/session`
- `POST /api/session/switch`
- `POST /api/demo/reset`
- `POST /api/demo/date`
- `GET /api/catalog`
- `GET /api/employees`
- `GET /api/employees/:id/profile`
- `PUT /api/employees/:id/goal`
- `GET /api/employees/:id/roadmap`
- `POST /api/employees/:id/preview`
- `POST /api/employees/:id/recommendations`
- `POST /api/plan`
- `POST /api/completion-requests`
- `POST /api/completion-requests/:id/accept`
- `GET/POST /api/side-quests`
- `POST /api/side-quests/:id/review`
- `POST /api/side-quests/:id/resource`
- `POST /api/side-quests/:id/policy`
- `POST /api/side-quests/:id/evidence`
- `POST /api/side-quests/:id/accept`
- `GET/POST /api/help`
- `POST /api/assignments`
- `GET /api/hr/analytics`
- `POST /api/import/preview`
- `POST /api/import/commit`
- `GET /api/rewards`
- `POST /api/rewards/:id/redeem`
- `GET /api/audit`

Detailed request examples are in [`docs/DEMO_API.md`](docs/DEMO_API.md).

---

## 9. How to verify the main scenario

The following sequence is the recommended reviewer path.

### Step 1 — open the deployed or local application

Deployed version:

**https://career.aiviom.ai**

Local version after `npm start`:

```text
http://127.0.0.1:3000
```

### Step 2 — Employee: inspect profile and target

1. Keep or select the **Employee** demo identity.
2. Open the employee profile.
3. Inspect current role/grade, target role/grade, skills and gaps.
4. Open the roadmap.
5. Request recommendations.
6. Inspect the recommendation explanation and alternative.

Expected result: recommendations refer to real catalog activities and are constrained by server-computed eligibility and current profile facts.

### Step 3 — verify preview is non-mutating

1. Select an eligible activity.
2. Open its preview.
3. Observe projected skill/gap changes.
4. Refresh or reopen the real profile.

Expected result: preview does **not** permanently change skills or history.

### Step 4 — submit a completion for verification

1. As **Employee**, submit evidence for an eligible/completable activity.
2. Switch to the **Advisor** identity.
3. Open the pending completion request and accept it with a reason.
4. Switch back to **Employee**.
5. Reopen the profile/rewards.

Expected result: accepted completion can update effective skills and XP once. Repeating the same accepted operation must not grant a duplicate credit.

### Step 5 — verify the side-quest workflow

1. As **Employee**, create a side quest with deliverables and skill IDs.
2. As **Advisor**, review it and define criteria plus allowed gain/cap.
3. If the quest requires resources, switch to **Manager** and approve/reject the resource request.
4. If it requires policy approval, switch to **Supervisor** and process that decision.
5. As **Employee**, submit evidence.
6. As **Advisor**, accept the evidence.

Expected result: approval of a proposal alone does not grant skills. Credit is created only after accepted evidence.

### Step 6 — verify HR functions

1. Switch to **HR**.
2. Open HR analytics.
3. Inspect gaps, participation, mandatory assignments and no-next-step cases.
4. Use **import preview** with `data/demo/import-example.json`.
5. Commit only after a valid preview.
6. Verify that the imported employee appears and can be opened.
7. Inspect the audit view.

Expected result: invalid imports do not partially mutate state; valid imports are committed through the server workflow.

### Step 7 — verify persistence and reset

1. Perform a state-changing demo action.
2. Restart the application without deleting the SQLite file/volume.
3. Confirm the state is still present.
4. Use the UI **demo reset** only when you intentionally want to reset the current workspace.

For the extended reviewer sequence, see [`docs/13_REVIEWER_GUIDE.md`](docs/13_REVIEWER_GUIDE.md).

---

## 10. Tests and technical checks

Run:

```bash
npm test
npm run typecheck
npm run build
npm run verify:source
```

Optional dependency security inspection:

```bash
npm audit
```

The test suite includes coverage for:

- domain skill/gap calculations;
- roadmap and prerequisite sequencing;
- import validation and atomicity;
- workspace isolation;
- role/scope enforcement;
- completion idempotency;
- reward idempotency and overspend protection;
- side-quest approval/evidence flows;
- recommendation validation/fallback/cache behavior;
- RU/KK/EN server/client localization.

The repository also includes reviewer/live smoke scripts under `scripts/`.

---

## 11. Data and persistence

The case dataset is stored under `data/source/` and contains employees, events, skills, role profiles and activity history.

Runtime state is persisted in SQLite. Default local path:

```text
.runtime/career-quest.sqlite
```

Docker uses a named volume mounted at:

```text
/app/.runtime
```

The application creates isolated demo workspaces backed by an HTTP-only `cq_session` cookie. Switching demo identities changes the active identity inside the same demo workspace; it does not represent production SSO.

---

## 12. Security and integrity controls implemented in the demo

The code includes:

- server-side role and employee/team scope checks;
- isolated demo workspaces;
- HTTP-only session cookie;
- same-site request protections and same-origin write validation;
- JSON body limit;
- request validation with Zod;
- idempotency guards for credits/rewards;
- audit events for state-changing workflows;
- AI output validation against server-side candidates/facts;
- restricted judge gateway payload and model flow;
- API keys kept on the server side.

This remains a competition/demo application. It does **not** claim production enterprise authentication or production SSO.

---

## 13. Known limitations

- Demo identity switching is intentionally provided for judging and is not production authentication.
- SQLite is appropriate for this self-contained demo deployment; a large production deployment would normally use a managed transactional database and a production identity provider.
- External/live AI availability depends on configured credentials/gateway/network. The application exposes fallback modes instead of presenting fallback output as live AI.
- Rewards and some demo policies are product demonstration policies, not Halyk Bank commitments.
- Recommendations support career development decisions; they do not automatically promote, grade, or rank employees.

See [`docs/15_RELEASE_AND_LIMITATIONS.md`](docs/15_RELEASE_AND_LIMITATIONS.md) for additional project-specific caveats.

---

## 14. Documentation map

Start here:

- [`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md) — implementation-oriented technical documentation.
- [`docs/13_REVIEWER_GUIDE.md`](docs/13_REVIEWER_GUIDE.md) — independent reviewer scenario.
- [`docs/11_DEPLOYMENT.md`](docs/11_DEPLOYMENT.md) — deployment details.
- [`docs/DEMO_API.md`](docs/DEMO_API.md) — API verification examples.
- [`docs/02_ARCHITECTURE.md`](docs/02_ARCHITECTURE.md) — architecture and component boundaries.
- [`docs/04_DOMAIN_CALCULATIONS.md`](docs/04_DOMAIN_CALCULATIONS.md) — domain calculations.
- [`docs/05_RECOMMENDATIONS_AND_AI.md`](docs/05_RECOMMENDATIONS_AND_AI.md) — AI recommendation design.
- [`docs/07_ROLES_AND_SECURITY.md`](docs/07_ROLES_AND_SECURITY.md) — roles and security model.
- [`docs/08_API_AND_STORAGE.md`](docs/08_API_AND_STORAGE.md) — API/storage detail.
- [`docs/12_TESTING.md`](docs/12_TESTING.md) — testing strategy.

---

## 15. Deployment

The public demo is available at:

**https://career.aiviom.ai**

Docker deployment is included in the repository:

```bash
cp .env.example .env
docker compose build
docker compose up -d
```

Check health:

```bash
curl http://127.0.0.1:3500/health
```

Stop without deleting persistent data:

```bash
docker compose down
```

Do **not** add `-v` unless you intentionally want to delete the Docker volume and its SQLite state.

---

## 16. Quick reviewer checklist

- [ ] Open **https://career.aiviom.ai**.
- [ ] Verify employee profile, target and gaps.
- [ ] Generate recommendation and inspect its mode/evidence.
- [ ] Run a preview and confirm it does not mutate state.
- [ ] Submit + approve a completion and confirm exactly one credit.
- [ ] Exercise a side-quest approval/evidence path.
- [ ] Open manager/supervisor/HR role views.
- [ ] Preview and commit an HR import.
- [ ] Inspect analytics and audit.
- [ ] For local reproduction, run `npm ci`, `npm run build`, `npm start`.
- [ ] Run `npm test` and `npm run typecheck`.

---

**Team AIVIOM · HackAlem AI 2026**
