# CareerUp

**Demo website:** [http://92.38.48.67](http://92.38.48.67)

CareerUp is an employee development prototype built with Next.js, React and SQLite. Employees own their goals and plans, explore learning activities, and submit evidence for human review. Managers and HR can approve or return reviews; AI helps explain options but never sets ratings or promotes employees.

The supplied synthetic dataset contains **200 employees, 40 activities, 60 skills and 2,743 participation records**. Its business date is **2026-10-01**, independent of the server clock.

> Demo identity only: anyone can select any employee or HR account on the public entry page. Server-side role checks do not establish a person's identity. Use synthetic data only.

## Quick start

Requires **Node.js 22.13+** and npm. Run from the repository root:

```sh
npm ci
npm run dev
```

Open [localhost:3000](http://localhost:3000), select an employee or HR, and enter the workspace. No external database or AI key is required for the core workflows.

For a production-mode synthetic demo, one command installs, builds and starts:

```sh
npm run demo
```

Or build and start separately:

```sh
npm run build
npm start
```

On first repository access, the app loads fixtures from `case_source/case_1/career_quest_dataset/` into `.data/career-quest.sqlite`. Existing databases are reused; changing fixture files does not reseed them automatically.

Optional configuration:

```sh
# Only for a new local setup; preserve an existing .env.local.
cp -n .env.example .env.local
```

Set `OPENAI_API_KEY` for live assistance. The key stays on the server; never use a `NEXT_PUBLIC_*` variable. Set `COOKIE_SECURE=true` when serving over HTTPS. See [setup and operations](docs/getting-started.md) for every setting, isolated demo data, troubleshooting and validation.

## Workspaces

| Route | What works |
| --- | --- |
| `/` | Public employee/HR account picker and language selector |
| `/employee/dashboard` | Overview, goals/milestones, advisor, skill evidence and learning history through `?view=` |
| `/employee/learning` | Search/filter catalog, activity detail, add to plan and demo completion |
| `/employee/reviews` | Self-assessment drafts/submission; direct-report reviews for managers |
| `/hr/dashboard` | Profile search, target-gap prevalence and participation aggregates |
| `/hr/employees/[id]` | Read-only employee plans, AI discussion briefs, review approval/return |
| `/hr/data` | Preview/apply employee JSON and history CSV imports; fixture reset |

English, Russian and Kazakh are available through **ENG / РУС / ҚАЗ**. Switching language reloads the current URL; save edits first. Supplied catalog text is translated, while unknown imported free text stays verbatim.

## What progress means

- **Plan:** employee intentions, milestones and claimed evidence. Changing a milestone does not increase skills.
- **Effective skills:** assessed baseline plus eligible completed-activity gains, respecting caps and per-skill assessment cutoffs.
- **Formal modules:** target requirements met by human-approved skill baselines, or imported assessments when no approval exists. Learning alone cannot close a module.
- **Grade:** recorded employment data. No workflow automatically promotes an employee.

A missing goal remains unset. An optional next-grade preview becomes a target only after the employee saves a role-linked focus. Free-form goals work for planning; catalog-based recommendations and quarterly reviews need a supported role/grade target.

## Docker

```sh
docker build -t career-quest:local .
docker volume create career-quest-data
docker run -d --name career-quest \
  --restart unless-stopped \
  -p 3000:3000 \
  --mount type=volume,source=career-quest-data,target=/app/.data \
  career-quest:local
```

The image includes fixtures and runs Next.js standalone as UID/GID 1000. Persist the **entire writable `/app/.data` directory**, including SQLite WAL files. Use one application replica with its own volume. PostgreSQL and MinIO are not integrated. For Kubernetes use `Recreate`; an image rollback does not roll back database contents.

```sh
# Builds the application and executes the checked-in validation suites.
docker build --target test -t career-quest:test .
```

For an AMD64 server when building on Apple Silicon, use `docker buildx build --platform linux/amd64 --load -t career-quest:local .`. Deployment manifests, CI behavior and recovery commands are in [the deployment runbook](deploy/README.md); its recorded live state is not a fresh deployment verification.

## Validate

```sh
npm run typecheck
npm run lint
npm test
npm run build
npm run test:http
npm run test:ai
npm run test:reviews
npm run test:identity
```

Build before the HTTP suites: they run `next start` against temporary SQLite databases. The AI suite explicitly disables the provider and does not establish live model quality. Ports and overrides are in [the validation guide](docs/getting-started.md#validation).

## Documentation

| Guide | Contents |
| --- | --- |
| [Documentation index](docs/README.md) | Current guides versus historical plans/reviews |
| [Setup and operations](docs/getting-started.md) | Configuration, validation, persistence, imports and troubleshooting |
| [Architecture](docs/architecture.md) | Components, storage, authorization, API surface and consistency rules |
| [UX](docs/ux.md) | Navigation, progress semantics, empty/error states and localization |
| [User flows](docs/user-flows.md) | Employee, manager and HR walkthroughs with expected outcomes |
| [AI assistance](docs/ai-assistance.md) | Evidence, consultation, streaming, adoption and provider boundaries |
| [Implementation status](docs/implementation-status.md) | Current capability summary and historical delivery evidence |

Still pending: production SSO, AI review calibration, arbitrary natural-language constraint filtering, a unified action timeline, HR-authored tasks/resources and full dataset replacement. Demo completions, review approval/return, structured duration/format preferences and Docker packaging are implemented.

Versions and scripts are maintained in [package.json](package.json). The Next.js PostCSS override is deliberate; review it when upgrading the framework rather than removing it incidentally.
