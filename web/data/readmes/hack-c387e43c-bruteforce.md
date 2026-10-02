# Sidequest

Turn a business challenge into a confirmed project brief, publish it in an open catalog, and let student teams propose an approach. The business chooses one, several, or no teams.

This is the Phase 1 implementation: the complete local workflow with SQLite persistence, deterministic readiness scoring, and explicitly labeled **Demo AI mode**. It requires no account registration, API keys, or paid services.

## Run locally

Use **Node.js 24.11.1** (recorded in `.nvmrc`) and npm. Run commands from this directory:

```sh
nvm use
npm ci
npm run seed
npm run dev
```

Open [localhost:3000](http://localhost:3000). For the production build:

```sh
npm run build
npm run start
```

On an already seeded checkout, skip `npm run seed`. It deliberately refuses to overwrite existing records. Ordinary startup and restarts preserve the database. To explicitly replace **all local demo records** with the five original fixtures:

```sh
npm run seed:reset
```

The default database is `data/sidequest.sqlite`, excluded from Git. An optional `SIDEQUEST_DB_PATH` overrides it. When overriding the path, supply the same value to seed and server commands, for example:

```sh
SIDEQUEST_DB_PATH=data/alternate.sqlite npm run seed
SIDEQUEST_DB_PATH=data/alternate.sqlite npm run dev
```

Stop the app before deliberately resetting its database. SQLite uses a writable local directory; this release targets local execution.

## Demonstrate Phase 1

Use the **Demo identity** selector in the header. It is a local role switch, not production authentication. Choose **Business · Sunrise Café** to start.

1. Inspect the five published tasks. Their confirmed scores are **90, 80, 65, 45, 25**. Apply topic/readiness filters, open a task, and return to the filtered catalog.
2. Click **Create task → Load café example → Find the missing details**. Three relevant questions appear. Click **Load café user & deadline answers**, leave the materials question unanswered, then **Create editable card**. Unknown information remains empty.
3. Click **Confirm details**. The official score becomes **35**. Click **Publish task**, then **View published task**: its position is **5 of 6**. A low score never blocks a proposal.
4. Switch to **Student · Pixel Pioneers**, open **Reduce food waste at Sunrise Café**, load a sample proposal, and submit. Repeat as **Student · Data Sprouts**; its sample proposal is different. Entering an invalid prototype URL demonstrates validation without losing the rest of the form.
5. Switch back to **Business · Sunrise Café**, open **My tasks**, select the café task, and choose **Edit task**. Click **Add café materials & success details**, then **Save draft**. Public content and its score remain at 35. Click **Confirm details**: the official score becomes **85**, the task moves to **2 of 6**, and both proposals remain attached.
6. In **Review proposals**, select both teams. Reject one and select it again. Decisions are independent and reversible; the task stays open to further proposals. For a selected team, open **Confirm a completed milestone**, enter a label/evidence note, and confirm. It earns **10 team progress points once**, separate from readiness.
7. Refresh, restart the server, and check **My proposals** as each team. Saved tasks, proposals, decisions, and points remain. Removing a qualifying card detail and confirming again can lower the task's score and catalog position.

These exact ranks assume five unchanged seed tasks and one new café task. Additional tasks or score changes naturally change the order. Sample controls only fill editable inputs; confirmation, publication, proposals, and decisions perform real server operations. All demo businesses, facts, and teams are fictional, and `example.com` prototype links are illustrative.

## What is implemented

- Three-step builder: Describe → Clarify → Review; editable structured fields, persistent drafts, explicit confirmation, publication, and a save-or-stay warning before navigating away with unsaved builder changes.
- Private working content and a separate last-confirmed snapshot. A published card remains unchanged until another confirmation. Publication requires a confirmed title, topic, and meaningful context or need, with no minimum score.
- Public catalog with score ordering, topic/readiness filters in the URL, proposal counts, neutral low-score labels, and global positions on task details.
- Five student profiles, unlimited intentional proposals, business selection/rejection/reset, and student decision visibility.
- A small milestone form with one-time progress points, retained even after a selection changes.
- Server validation, role/ownership checks, stale-revision rejection, safe HTTP(S) prototype links, and retry protection for proposals and milestones.
- Local topic-aware question generation and literal answer mapping, with shared Zod response schemas. See [AI contracts and examples](docs/AI_DEMO.md).

## Scoring and ordering

Official points come from **confirmed fields only**. The client cannot supply a score. `lib/scoring.ts` is the single calculation used by the catalog, task details, and editor breakdown.

| Category | Points | Qualifying details |
| --- | ---: | --- |
| Context and need | 20 | Current situation (10) and desired change (10). |
| Data and materials | 20 | Named material plus its contents (10); access instructions, only with identified materials (10). |
| Expected result | 15 | An artifact type and deliverable description. |
| Success criteria | 15 | Metric/comparison/numeric target/unit, or an observable check/expected outcome (10); verification method, only with a target (5). |
| Constraints | 10 | Delivery boundary (5) and technology/access boundary (5). |
| Users | 10 | An identified user group. |
| Business connection | 10 | Valid email (4), consultation format (3), feedback process (3). |

Whitespace and obvious placeholders such as `TBD`, `I don't know yet`, and `Not provided` earn no points. Text copied from the task title into another field does not qualify. Incomplete optional information earns zero but does not block publication. The form explicitly separates structured subfields; it does not claim to prove the truth or semantic quality of arbitrary text.

Readiness tiers: **0–39 Needs clarification**, **40–69 Workable**, **70–89 Ready**, **90–100 Priority**. Publication status is separate from readiness. Catalog order is descending score, then most recent publication, then stable task ID. Position always refers to all published tasks, before filtering.

## Architecture

Next.js App Router + React + strict TypeScript, Tailwind/CSS, `better-sqlite3`, and Zod. Server-rendered pages load current data; client components call Node.js route handlers for mutations. System fonts keep startup and builds independent of a font service.

| Location | Responsibility |
| --- | --- |
| `app/` | Catalog, task/editor pages, business/student workspaces, API handlers. |
| `components/` | Builder, readiness breakdown, proposal forms/cards, identity selector, navigation guard. |
| `lib/schemas.ts` | Shared task/card/question/answer/proposal contracts. |
| `lib/db.ts` | SQLite schema, transactions, ownership, revision checks, public ordering, and proposal/milestone operations. |
| `lib/scoring.ts` | Pure deterministic eligibility, points, and tier mapping. |
| `lib/ai.ts` | Local fallback, prompt, operation schemas, and source-evidence validation. |
| `lib/fixtures.ts`, `lib/seed.ts` | Reproducible owner answers, proposals, and seed data with asserted scores. |
| `tests/` | Focused rules/state tests and production-server browser walkthroughs. |

SQLite has relational business, team, task, proposal, and milestone records. Tasks contain JSON working/confirmed cards, original description, append-only answer history, source references, and revisions. Mutation transactions reject stale saves. Public responses to students exclude working drafts. Proposal request IDs deduplicate retries but allow separate intentional submissions. Milestones deduplicate by ID and by normalized label within the same proposal.

## Verification

```sh
npm test
npm run typecheck
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser tests start the production server on port **3100** and explicitly reset **`data/e2e.sqlite`**, never the normal demo database. Build first. Focused tests use a disposable database in the operating system's temporary directory. Browser screenshots/traces go to ignored `test-results/`.

See [Phase 1 verification record](docs/PHASE_1_VERIFICATION.md) for the actual completed checks and checkpoint.

## Scope and limitations

Phase 1 intentionally uses the allowed deterministic fallback, not a live model. It does not perform broad natural-language extraction or automatic factual verification. It asks three topic-aware questions, copies explicit owner statements into matching fields, and leaves the remaining editing to the owner. No credentials are needed; live AI and adaptive follow-ups belong to Phase 2.

The header selector makes demo profiles publicly switchable. Ownership checks prevent mistakes between selected roles; they are not a substitute for production authentication. This is an English-only local demonstration, not a hosted multi-user service.

Phase 2's unconfirmed score preview, improvement shortcuts, score-change receipts, and live coaching are deferred. Source expansion, dedicated proposal comparison, animation, and the final submission/rehearsal pass remain later-phase work. Basic breakdowns, normal proposal cards, and required functionality are already included.
