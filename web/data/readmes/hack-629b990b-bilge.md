# AI Sana — Business Challenge Quality Rating & Open Team Selection

Interactive multiplayer 3D campus for discovering AI Sana business challenges.

![3D Campus](3d-world-overview.png)
Team **Bilge**, HackAlem · "Gamification of Practical Tasks" case study.

Watch our demo video here: https://drive.google.com/drive/folders/1PKSJU6z9LSoA1dz7B01vrEgPE5YPXJvW

A business describes a problem in its own words. AI helps complete the description, and the server transparently calculates the card's readiness from 0 to 100. The task is published in a shared catalog, which is also shown as a live 3D campus. Student teams choose tasks themselves and submit proposals; the business manually selects one, several or no teams. A team earns points only for a milestone confirmed by the business.

**The main gamification is for the business:** the more complete and useful the description, the higher the rating and the position in the catalog. The rating shows how ready a task is for work with students, not how well known the company is.

---

## 1. Launch (one command)

Only **Node.js 22.12+** is required (https://nodejs.org). From the repository root:

```sh
npm start        # dependencies → build → server: http://127.0.0.1:3001
npm run check    # check: backend/frontend types and tests, build, smoke run (PASS/FAIL summary)
```

- `npm start` creates `backend/.env` from `backend/.env.example`. **Everything works without an OpenAI key**; AI questions run in a clearly labelled fallback mode. For live AI, set `OPENAI_API_KEY` in `backend/.env` and restart.
- After launch, the console prints **login codes and ready-made links** (2 businesses, 5 teams). The codes are stored in the local `backend/demo-accounts.local.json`; this file is not committed to git. You can also log in as a guest.
- Each browser tab is a separate role. For example, the business in one tab and a team in another.
- `npm run start:bots` runs the same thing plus demo players in the 3D world (marked "demo").
- `npm run check` starts the server on a temporary database with AI in `stub` mode and Git in `mock` mode: no external calls, no spend and no changes to your data.
- If the port is busy: `PORT=3005 npm start`. In PowerShell: `$env:PORT=3005; npm start`.
- Development with hot reload: `cd frontend && npm run dev:all` → http://localhost:5173. API documentation: http://127.0.0.1:3001/api/docs

## How to use

### For a business: add and publish a task
1. **Log in.** On the login screen enter a business code (printed by `npm start`, also in `backend/demo-accounts.local.json`). You land on **My tasks**.
2. **Describe a new task.** In the "Describe a new task" block, write in your own words what happens now and what you want to change (e.g. "The cafe has a lot of unsold food left over"). Title and industry can be added later. Click **Save description** — the task builder opens.
3. **Improve the card** in the builder:
   - **Analyze description** — AI suggests values for empty fields as exact quotes from your text; tick the ones you want and click **Add selected**.
   - **Clarify with AI** — answer 3–5 questions one at a time; answers go into the card verbatim.
   - Edit any field by hand and click **Save draft**. On the right you see the **forecast** score and what the next improvement is worth.
4. **Confirm details** — the official score is recalculated; the breakdown shows exactly which fields earned points.
5. **Publish** — the task appears in the shared catalog and as a building in the 3D world. Low readiness does not block publishing or proposals.
6. **Choose teams.** When proposals arrive, open **Compare proposals** from your dashboard, then **Select team** or **Reject** each one (several teams or none is fine).
7. **Review results.** A selected team creates a milestone and submits a Git/PR link. Open the milestone, check the materials, then **Confirm result** (+10 points to the team, GRAND TRIUMPH in the 3D world) or **Return for rework** with a comment.

### For a team
Log in with the team code (optionally enter your name for the 3D world) → walk around the campus (WASD, `M` map, `E` open a task) or use **All tasks** → submit a proposal → after the business selects you, create a milestone and submit your result from the task card or **Team dashboard**. Teammates share one code and see each other in the world.

### As a guest
Click **Guest — view only** on the login screen: browse the catalog and the 3D world without proposals.

## 2. Architecture

```
frontend/  React 19 + TypeScript + Vite 8 + React Three Fiber (three.js)
   │  2D screens: login, dashboard, builder, catalog, card, proposals, milestone, rating
   │  3D campus: task buildings, team bases, online players, GRAND TRIUMPH
   │  typed client backend/client/index.ts (HTTP) + socket.io-client
   ▼
backend/   BFF: Node.js + TypeScript + Express 5 + Zod + SQLite (better-sqlite3) + Socket.IO
   ├─ src/app.ts            HTTP API /api/v1 (OpenAPI 3.1 → /api/docs), CORS/Origin, rate limit
   ├─ src/services/         use cases and invariants: tasks, proposals, selection, milestones, point awards
   ├─ src/domain/score.ts   readiness formula (section 3)
   ├─ src/views.ts          ready-made screen models, available actions, next step
   ├─ src/integrations/     OpenAI (Responses API, Luna) and Git/PR checks — replaceable, with a fallback mode
   ├─ src/realtime.ts       invalidate/sync.required events after writes to SQLite
   └─ src/world.ts          player presence in 3D, emotes, world.triumph, GET /api/v1/world
```

- **The server is the source of truth.** The client never sends scores, team names or decisions. Permissions are checked on every command: role, task owner, selected team.
- **Versions and retries.** Changes are protected by `expectedVersion`: on a conflict the server returns 409 and does not overwrite someone else's edits. Creating a task, a proposal and a milestone is idempotent (`Idempotency-Key`).
- **Real time.** After every change, clients receive an event and re-read the screen. The same task is shown identically in the 2D catalog and in the 3D world.
- **Storage.** SQLite (`backend/data/ai-sana.db`) survives restarts. Secrets are stored only on the server and are not committed to git.
- **3D world.**
  - A highly rated task stands as the main pavilion by the monument in the centre of the square. Other tasks are buildings in districts by industry.
  - A building's location is stable; it is chosen by `seed = hash(task.id)`.
  - The readiness level changes the building's styling, beacon and label.
  - Players are synchronized via Socket.IO at 12 Hz with movement smoothing. Walking and emotes do not give points.
  - GRAND TRIUMPH is triggered only after the business confirms a milestone.
  - Without WebGL, the 2D catalog opens instead.

## 3. Task rating formula

Points are awarded only for fields **confirmed** by the business (`backend/src/domain/score.ts`, scale from the brief, section 4):

| Category | Points | Condition |
|---|---:|---|
| Context and need | 10 + 10 | describes what happens now / what needs to change |
| Data and materials | 10 + 10 | data availability is known (available or not) / if available, a real source is named |
| Expected result | 15 | a concrete result of the team's work is described |
| Success criterion | 15 | a metric with a target value **or** an acceptance condition |
| Constraints | 10 | deadlines, technologies, access **or** explicitly confirmed "no constraints" |
| Users | 10 | it is clear who the solution is for |
| Communication with the business | 5 + 5 | contact channel / format of consultations and feedback |
| **Total** | **100** | |

- Empty and boilerplate answers (typical placeholders such as "don't know", "TBD") give no points. Separate quality hints flag generic phrases, the same text in several fields and contradictions, but they do not change the score. "No data" gives 10 points but does not pretend a dataset exists.
- The score is an explainable completeness heuristic, not a verification that the information is true: the business vouches for accuracy.
- The card shows a breakdown by category, a list of what is missing and the nearest improvement, for example "+15: add an acceptance condition".
- A draft gives a **forecast**, while the official score is recalculated on every "Confirm details" and can both rise and fall.

**Readiness levels:**
- 0–39 "Draft" — the task is visible, marked as needing clarification;
- 40–69 "Working";
- 70–89 "Ready" — higher in the catalog;
- 90–100 "Priority" — highlighted.

A low rating does not hide a task or prevent proposals.

**Team points** are a separate metric: **10 points per milestone**, only after confirmation by the business and exactly once (the award record is written in a single SQLite transaction). Proposals, commit links, AI comments, walking and time online give no points.

## 4. Catalog rules

- The catalog shows **all published tasks** to all teams and guests. Drafts are visible only to their owner.
- Only a confirmed snapshot of the card is published. Draft edits are not publicly visible until confirmed.
- **Sorting:** official score descending → newer publication first → id (stable order).
- **Filters:** industry (topic), readiness level, search by title and description.
- The number of proposals is unlimited; a team may propose several approaches.
- **Selection is manual only:** on the proposal comparison screen the business selects or rejects each proposal. Several teams or none may be selected. There is no automatic assignment.
- The selected team creates a milestone with an acceptance criterion. Submitting a Git/PR link moves the milestone to "in review"; this gives no points. The business confirms the milestone (+10 points) or returns it with an explanation.

## 5. AI usage

By default the OpenAI Responses API is used, model `gpt-6-luna` (`OPENAI_MODEL`), with structured output (Zod schema). The code is in `backend/src/integrations/ai.ts`, `analysis.ts`, `ai-runtime.ts`.

| Function | Input | Output | Rule |
|---|---|---|---|
| Description analysis | `{ rawDescription, fields }` | `{ suggestions: [{ field, quote }] }` | the server accepts only **verbatim** contiguous quotes from the original description and only for empty fields; the human chooses what to apply |
| Clarifying questions | `{ rawDescription, fields, missingFields }` | `{ missingFields, questions: [{ field, text }] }`, 3–5 questions | the AI chooses the missing fields, the question text comes from a neutral server-side catalog; answers are copied into the card verbatim |
| Milestone pre-check | acceptance criterion, description, fetched Git/PR materials | quotes from the materials for each criterion | a quote does not prove completion; the business decides |

- **An invalid model response** (off-schema, refusal, 30 s timeout, no key) triggers an explicit fallback mode `mode=stub`:
  - questions come from a template;
  - analysis returns an empty list;
  - the milestone check switches to manual mode with a warning.

  Manual filling, confirmation and publication do not depend on AI. There are no automatic paid retries.
- The AI **does not add facts** the user did not provide, does not choose a team on behalf of the business and does not use personal data.
- Every call is recorded in the task history: operation, model, duration, validation, fallback reason. Prompts and keys are not written to the log.
- Live regression report: [docs/evals/live-harness-report.json](docs/evals/live-harness-report.json).

## 6. Data

On first launch the server creates synthetic demo data (`backend/src/seed.ts`):
- 2 businesses and 5 teams with interests, skills and technologies;
- 5 drafts of varying completeness;
- 5 published cards covering all four levels;
- 5 proposals with an idea, plan, timeline and link.

Restarting does not overwrite your changes. All companies and people are fictional.

## 7. Test scenarios

### Automated (`npm run check`)
- **backend, 172 tests (vitest):**
  - formula and level boundaries;
  - role permissions, draft isolation, version conflicts, idempotency;
  - end-to-end business and team scenarios;
  - AI and Git providers, including fallback mode;
  - realtime, session logout;
  - OpenAPI and client contract;
  - 3D world: team players are visible separately, speed is limited by the server, emotes from an allowlist, `world.triumph` exactly once and only after business confirmation.
- **frontend, 6 tests:** deterministic world layout, stable locations when new tasks appear, no overlap between buildings and roads, collisions, movement interpolation.
- **Smoke run of the built application:** health, UI serving, catalog, `/world`, code login, two players see each other.

### Manual: required demo (≤ 5 minutes)
1. **Business** (tab 1): "Describe a new task" — enters a weak description, for example "The cafe has a lot of unsold food left over". Clicks "Analyze description" and selects quotes.
2. "Clarify with AI": answers 3–5 questions one at a time. On the right, the score **forecast** grows.
3. Edits the card and clicks "Confirm details": **the official score has risen**, and the breakdown shows exactly what for. Then "Publish".
4. **Team** (tab 2, team code): the task immediately appears in the catalog and as a building in the 3D world. The player walks up to the building, presses `E` and submits a proposal.
5. **Business**: "Compare proposals" → "Select team" or "Reject".
6. *(P1)* The team creates a milestone and submits a link. The business confirms: +10 points in the team rating, and GRAND TRIUMPH plays across the whole 3D world.

### Edge-case checks
- **Input errors:** an empty description or an invalid link — the server returns field errors, which are highlighted in the form.
- **Edits without confirmation:** fields were changed but "Confirm" was not clicked — the public score does not change.
- **Version conflict:** editing the same card in two tabs — 409 and an offer to load the latest version; the input is preserved.
- **Permission bypass attempts:** a team tries to confirm its own milestone — 403. A repeated confirmation — "No repeated award".
- **No AI key:** template questions with a label; the whole scenario completes.

## 8. Repository structure

```
backend/     BFF (README: backend/README.md; frontend notes: docs/backend-integration.md)
frontend/    web interface and 3D world (README: frontend/README.md)
scripts/     start.mjs (npm start), check.mjs (npm run check)
docs/        backend and harness design, eval reports
```

3D model licenses: CC0 — Kenney (City Kit Commercial, Car Kit, Mini) and KayKit City Builder Bits; full list in `frontend/public/models/LICENSES.txt`.
