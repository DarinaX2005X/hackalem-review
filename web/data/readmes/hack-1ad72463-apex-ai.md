# Apex Match — Event Vendor Matching

**English** | [Русский](README.ru.md)

Deployment: [English](DEPLOY.MD) · [Русский](DEPLOY.ru.MD)

**Apex Match** is a web application built by **Apex-AI** for HackAlem AI. It helps event organizers find up to three suitable vendors based on city, category, date, event format, budget, language, and working duration. Each result includes a starting price and an explanation of why the profile matches.

**Live website:** [testrr.shop](https://testrr.shop/) · **API reference data:** [catalog](https://testrr.shop/api/catalog/meta) · **API status:** [health](https://testrr.shop/api/health)

This overview reflects the project as of **September 23, 2026**. The public frontend and Go backend are deployed and connected through the live API. The baseline catalog contains **66 profiles across 17 categories**, with calendar data covering **September 23–December 31, 2026**.

## Contents

- [Purpose and features](#purpose-and-features)
- [How matching works](#how-matching-works)
- [Data and explanations](#data-and-explanations)
- [Technology and architecture](#technology-and-architecture)
- [Repository structure](#repository-structure)
- [Local quick start](#local-quick-start)
- [Admin panel](#admin-panel)
- [Configuration](#configuration)
- [HTTP API](#http-api)
- [Demo scenarios](#demo-scenarios)
- [Testing](#testing)
- [Deployment and operations](#deployment-and-operations)
- [Limitations and future work](#limitations-and-future-work)
- [Documentation](#documentation)
- [Authors](#authors)

## Purpose and features

Event organizers need to compare their requirements against information spread across vendor profiles. Apex Match makes that selection reproducible and explains the outcome.

After completing the form and running a search, users receive:

- Up to three catalog cards with starting prices, working-hour limits, and explanations.
- The total number of eligible profiles before the three-card limit is applied.
- Reasons for excluding other candidates: event format, budget, language, duration, or availability.
- Distinct messages when a city has no vendors in the selected category and when existing vendors do not meet the requirements.
- Labels identifying synthetic profiles and values filled in during dataset preparation.
- Field-level validation messages, plus separate loading, technical-error, and retry states.

The interface includes five quick scenarios. They populate the form; the user then starts the search with **«Найти подрядчиков» (Find vendors)**. Each request covers **one category and one vendor**; the budget is not distributed across all services for an event.

## How matching works

1. The backend validates JSON, required fields, types, and the supported date window.
2. It selects profiles whose normalized city and category match exactly. Normalization handles Unicode, case, and extra whitespace.
3. It checks constraints in this order: **event format → budget → language → duration → availability**.
4. It sorts eligible profiles by `price_from_kzt ASC`, then `id ASC`, and returns the first three.
5. It builds explanations from the request conditions, structured data, and verified excerpts from profile descriptions.

When a profile fails several checks, the public diagnostics count it at the first failed step. Conditions are never relaxed automatically, and ineligible profiles are not added to fill three cards. The same catalog version and normalized request produce the same results in the same order.

A price equal to the budget and a duration equal to the working-hour limit are allowed. If language or duration is omitted, the corresponding check is skipped. `max_hours: null` means the working-hour limit does not apply.

## Data and explanations

The source dataset is stored in [backend/data/catalog.csv](backend/data/catalog.csv). It contains 66 anonymized profiles, including 13 synthetic profiles already present in the supplied data.

| Attribute | Value |
|---|---|
| Geography | Almaty, Astana, and «Зарубежье» (Abroad), a source-dataset grouping |
| Categories | 17, including hosts, photographers, videographers, venues, florists, and others |
| Event formats | Wedding, toi, corporate event, conference, anniversary, birthday |
| Languages | Russian, Kazakh, English |
| Currency | Kazakhstani tenge, `KZT` |
| Calendar window | `2026-09-23` through `2026-12-31`, inclusive |
| Explanation facts | 66 profile features and 2 conditions requiring confirmation |

[backend/data/catalog.meta.json](backend/data/catalog.meta.json) defines the calendar window. [backend/data/facts.json](backend/data/facts.json) links statements to a profile ID, a quotation, and a hash of the source description. If a description changes, outdated facts fail import validation.

**The current implementation does not make online LLM calls.** Explanations are assembled from templates and prepared facts. Model API keys, training, embeddings, and a vector database are not required. Verifying that a fact matches a description is not an independent verification of a vendor's advertising claim.

The starting price applies to the event, is not multiplied by hours, and is not a final quote. A date missing from the busy-date list means only that it is not marked busy in the dataset; it does not confirm real availability or a booking.

## Technology and architecture

| Component | Technologies |
|---|---|
| Frontend | React 19, TypeScript, Vite, CSS |
| API response validation | Zod |
| Frontend tests | Vitest, Testing Library, jsdom |
| Backend | Go 1.25+, `net/http`, `pgx/v5` |
| Admin panel | Separate Go module, embedded HTML/CSS/JavaScript, bcrypt, PostgreSQL sessions |
| Storage | PostgreSQL 16+; local Compose uses PostgreSQL 16 |
| Backend tests | Go testing, race detector, PostgreSQL integration |
| Local infrastructure | Docker Compose |
| Production | Ubuntu, Nginx, HTTPS, systemd, PostgreSQL |

```text
Browser → Nginx / HTTPS → React frontend
                     ├─ /api/* → Go matching API → PostgreSQL
                     └─ /admin/* → Go admin service → same PostgreSQL

CSV + metadata + facts → catalog CLI → validation → migrations / import → PostgreSQL
```

The frontend sends requests and displays backend responses; it does not independently filter or reorder vendors. The API reads a consistent catalog snapshot from PostgreSQL and verifies its integrity. Import validates the entire dataset before replacing the catalog in a single transaction. A failed import preserves the previous snapshot.

The catalog is small, so there is no separate Redis instance, queue, or persistent cache. The public interface uses built-in form options. The metadata endpoint is available, but the frontend does not yet load those options dynamically.

## Repository structure

```text
.
├── README.md                        # project overview in English
├── README.ru.md                     # project overview in Russian
├── TECH_SPEC.md                      # original requirements and acceptance criteria
├── ARCHITECTURE.md                   # architecture and solution contract
├── admin_panel/                    # authenticated catalog management, CSV preview, audit log
├── backend/
│   ├── cmd/server/                  # HTTP server
│   ├── cmd/catalog/                 # catalog validation, migrations, and import
│   ├── internal/                    # models, matching, HTTP, PostgreSQL, configuration
│   ├── data/                        # CSV, calendar metadata, facts
│   ├── examples/                    # request and response examples
│   ├── scripts/smoke.sh             # HTTP smoke checks
│   ├── compose.yaml                 # local database, initialization, and API
│   ├── Dockerfile
│   ├── Makefile
│   ├── ENDPOINT.MD                  # full HTTP contract
│   ├── TESTING.md                   # backend testing
│   └── README.md
└── frontend/
    ├── src/api/                     # HTTP/mock adapters, contracts, and schemas
    ├── src/app/                     # application configuration
    ├── src/features/recommendations/ # form, cards, states, and tests
    ├── src/shared/                  # shared components and formatting
    ├── src/styles/                  # styles
    ├── .env.example
    ├── .env.production              # live API on the same origin
    ├── package.json
    └── README.md
```

The repository also includes a separate [admin panel](admin_panel/README.md) at [testrr.shop/admin/](https://testrr.shop/admin/). It supports authenticated catalog search, manual creation and editing, deletion, CSV preview and import, export, and an audit log. It shares PostgreSQL with the public API, so saved changes are reflected in subsequent searches. Setup and API details are documented in the admin panel directory.

## Local quick start

You need Git, Docker with Compose v2, and Node.js 24+ with npm. Go 1.25+ is required to run or test the backend outside Docker. Access to the private GitHub repository is required.

### 1. Get the project

```sh
git clone https://github.com/BAITC-Hacks/hack-1ad72463-apex-ai.git
cd hack-1ad72463-apex-ai
```

### 2. Start the backend and PostgreSQL

From the repository root:

```sh
cd backend
docker compose up --build -d
curl --fail http://localhost:8080/readyz
sh scripts/smoke.sh
```

Compose starts the database, applies migrations and imports the catalog through a one-off `init` service, then starts the API. The API is available at `http://localhost:8080`, and PostgreSQL at `127.0.0.1:54329`. Database files are persisted in `backend/.tmp/postgres-compose`.

### 3. Start the frontend

In another terminal, from the repository root:

```sh
cd frontend
npm ci
cat > .env.local <<'ENV'
VITE_API_MODE=http
VITE_API_BASE_URL=http://localhost:8080
ENV
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open [localhost:5173](http://localhost:5173). The backend configuration allows the `http://localhost:5173` origin, so use that exact browser address. In this mode, the interface calls the local API.

### Standalone demo without a backend

Set `VITE_API_MODE=mock` in `frontend/.env.local` and restart Vite. The interface displays a **DEMO / MOCK API** label. Mock mode uses prepared scenarios, does not perform a real catalog search, and does not replace integration testing with PostgreSQL.

### Run the backend with Go

From `backend`, with Go installed and Docker available:

```sh
docker compose up -d db
cp .env.example .env
set -a
. ./.env
set +a
make deps
make bootstrap
make run
```

This replaces running the API through Compose. If the Compose API already occupies port 8080, run `docker compose stop api` first. The application does not load `.env` automatically, so export the variables as shown above.

To stop Compose, run `docker compose down` from `backend`. Database files are retained.

## Admin panel

Open [testrr.shop/admin/](https://testrr.shop/admin/) to manage the shared catalog. Access requires an administrator account. The panel supports manual creation, full-record editing, deletion, CSV preview and import, CSV export, a blank template, and the latest 50 audit events. Vendor IDs are immutable; deleting the last profile is blocked.

### Local setup and first login

First initialize the backend catalog using the quick-start instructions above. In another terminal, from the repository root:

```sh
cd admin_panel
cp .env.example .env
set -a
. ./.env
set +a
make build
bin/admin init
bin/admin serve
```

The supplied configuration uses the same local database as the backend. Open [127.0.0.1:18081/admin/](http://127.0.0.1:18081/admin/); the exact origin must match `ADMIN_ORIGIN`. The admin service is not included in the backend Compose file. Keep the `backend` and `admin_panel` directories next to each other because the Go module uses `replace ../backend`.

`init` creates admin tables and the `admin` account without replacing the catalog. It prints a random temporary password once. There is no shared default password. Repeating `init` preserves an existing account. On first login, change the temporary password, then sign in again. Password changes revoke all sessions; sessions otherwise expire after eight hours. Account creation and role management are not exposed in the UI.

### Catalog changes and CSV

Download the template or export from the panel to obtain the 13-column CSV format. Use UTF-8, comma-separated columns, and `|` inside list fields, such as `русский|английский`. The upload limit is 5 MiB per multipart request and 5,000 records per file. Manual and CSV input use the same catalog validation rules.

Preview the file before applying it. By default, only new IDs may be imported; any existing ID rejects the entire import. Selecting **update existing records** allows those profiles to be replaced in full. Profiles absent from the file are retained. Preview is a validation step, not a reservation: a concurrent catalog change requires a new preview.

Changes use a catalog revision (`ETag` / `If-Match`) to prevent overwriting another administrator's work. A successful transaction saves the catalog and audit event together. New matching requests see committed changes without restarting the public API. Editing a description removes its outdated explanation facts; new facts are not generated automatically. Changes live in PostgreSQL and do not rewrite repository CSV files.

The public frontend still uses built-in city/category options. Adding a new city or category in the panel updates API metadata but does not automatically add an option to that form. The three-result limit and price/ID sorting remain unchanged.

See the [admin guide](admin_panel/README.md), [admin API](admin_panel/ENDPOINT.MD), [test guide](admin_panel/TESTING.md), and [deployment guide](admin_panel/deploy/README.md).

## Configuration

### Backend

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL DSN; required for the server, migrations, and import |
| `HTTP_ADDR` | HTTP server address; defaults to `:8080` |
| `CORS_ORIGINS` | Comma-separated allowed origins; locally `http://localhost:3000,http://localhost:5173` |
| `CATALOG_CSV` | Catalog file for the CLI; defaults to `data/catalog.csv` |
| `CATALOG_META` | Calendar metadata; defaults to `data/catalog.meta.json` |
| `CATALOG_FACTS` | Facts file; `-` disables additional facts during import |
| `TEST_DATABASE_URL` | Separate connection for integration tests |

Example: [backend/.env.example](backend/.env.example). The password in the local Compose configuration is for development only.

### Admin service

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Same database as the matching API |
| `ADMIN_ADDR` | Listen address, default `127.0.0.1:18081` |
| `ADMIN_ORIGIN` | Exact browser origin without a path; default `https://testrr.shop` |
| `ADMIN_INSECURE_HTTP` | `true` only for local loopback HTTP; production uses secure cookies |
| `ADMIN_TRUST_PROXY` | Trust Nginx `X-Real-IP` only when the service and peer use loopback |
| `ADMIN_INITIAL_PASSWORD` | Optional initial password for `init`; omit to generate one |

### Frontend

| Variable | Purpose |
|---|---|
| `VITE_API_MODE` | `http` for the live API; `mock` for standalone fixtures |
| `VITE_API_BASE_URL` | Backend root URL or a URL ending in `/api` |

Production configuration: `VITE_API_MODE=http`, `VITE_API_BASE_URL=/api`. Requests go to `POST /api/recommendations` on the same domain.

Vite variables are embedded at build time. Rebuild the frontend after changing the API address. Before a production build, remove local overrides from `.env.local` or explicitly set the production values in the environment. `VITE_*` variables are visible in the browser and must not contain secrets.

## HTTP API

| Method | Backend path | Purpose |
|---|---|---|
| `POST` | `/api/recommendations` | Find up to three suitable vendors |
| `GET` | `/api/catalog/meta` | Reference data, versions, and calendar window |
| `GET` | `/healthz` | HTTP process liveness |
| `GET` | `/readyz` | Database availability and catalog integrity |
| `GET` | `/metrics` | HTTP counters and latency metrics in Prometheus format |

In production, Nginx also exposes `GET /api` as an alias for `/api/catalog/meta` and `GET /api/health` as a readiness check mapped to `/readyz`. The internal `/healthz`, `/readyz`, and `/metrics` paths are not directly proxied to the public Internet.

Example request to the deployed service. Keep the Russian catalog values shown below: translating the documentation does not change the API's accepted values.

```sh
curl --fail-with-body https://testrr.shop/api/recommendations \
  -H 'Content-Type: application/json' \
  -d '{
    "city": "Алматы",
    "date": "2026-11-14",
    "event_format": "корпоратив",
    "category": "Ведущий",
    "budget_kzt": 1000000,
    "duration_hours": 6,
    "language": "русский"
  }'
```

Required fields: `city`, `date`, `event_format`, `category`, and `budget_kzt`. Language and duration may be omitted or set to `null`. The response contains `status`, `message`, `results`, `diagnostics`, and `metadata`.

| Outcome | HTTP | Meaning |
|---|---|---|
| `MATCHES_FOUND` | 200 | Eligible profiles were found |
| `NO_CATALOG` | 200 | No profiles exist in the selected city and category |
| `NO_MATCH` | 200 | Profiles exist, but all were excluded by the conditions |
| `VALIDATION_ERROR` | 422 | Request field validation failed |
| `CATALOG_UNAVAILABLE` | 503 | The database or catalog is not ready |

Business outcomes and errors use different response structures. See [backend/ENDPOINT.MD](backend/ENDPOINT.MD) for the full contract, additional error codes, and examples.

## Demo scenarios

Baseline request: Almaty, host, corporate event, `2026-11-14`, budget `1,000,000 ₸`, Russian, 6 hours.

| Scenario | Change from the baseline | Expected result with the original catalog |
|---|---|---|
| Popular request | None | 4 eligible profiles; returns `HK-44923`, `HK-29829`, `HK-27222` |
| Busy date | Date `2026-12-19` | 1 card: `HK-35215` |
| Rare category | Florist, wedding, budget `300,000 ₸` | 1 card: `HK-90001`, a synthetic profile |
| No matches | Budget `100,000 ₸` | `NO_MATCH` |
| No category | Astana, decorator | `NO_CATALOG` |

These expectations apply to the original dataset version. Results may change when the catalog is updated.

## Testing

Frontend, from `frontend`:

```sh
npm ci
npm run test:run
npm run build
```

Tests cover the form, result cards, distinct empty states, synthetic-profile labels, starting prices, correct handling of `max_hours: null`, and 422/503 errors. The build also checks TypeScript.

Backend, from `backend`:

```sh
make test
make check
make build
make benchmark
```

Integration tests require a real PostgreSQL instance and `TEST_DATABASE_URL`:

```sh
export TEST_DATABASE_URL='postgres://hackalem:hackalem_local@127.0.0.1:54329/hackalem?sslmode=disable'
make test-integration
```

Integration tests create a unique schema, verify migrations, import, rollback, concurrent reads, catalog corruption, and database failures, then remove that test schema. PostgreSQL checks in the general test run are skipped when `TEST_DATABASE_URL` is not set.

During deployment on September 23, 2026, all 8 frontend tests, the production build, HTTP checks for five business scenarios, and browser checks against the live API passed. These are results from a specific run, not a continuous CI status. See [TESTING.md](backend/TESTING.md) for backend details.

Admin tests run separately from the backend module. From `admin_panel`, with `TEST_DATABASE_URL` pointing to a test database, run `make test check`. Without it, database integration tests are skipped. See [admin_panel/TESTING.md](admin_panel/TESTING.md) for coverage and a manual verification procedure.

## Deployment and operations

The live website is [testrr.shop](https://testrr.shop/). Nginx serves the static frontend build and proxies `/api/*` to the Go service at `127.0.0.1:18080`. PostgreSQL and the application port are not exposed to the Internet. HTTPS uses a Let's Encrypt certificate with automatic renewal; HTTP and `www` redirect to the canonical HTTPS address.

| Component | Current location |
|---|---|
| Frontend | `/opt/hackalem/frontend/current`, a symlink to a release directory |
| Backend | `/opt/hackalem/backend/current` |
| Backend service | `hackalem-backend.service` |
| Backend environment | `/etc/hackalem/backend.env` |
| Admin release / service | `/opt/hackalem/admin_panel/current` / `hackalem-admin.service` |
| Admin environment / port | `/etc/hackalem/admin.env` / `127.0.0.1:18081` |
| Website configuration | `/etc/nginx/sites-available/testrr.shop` |
| Production PostgreSQL | 18.6; database `hackalem` |

Build the production frontend from `frontend`:

```sh
npm ci
VITE_API_MODE=http VITE_API_BASE_URL=/api npm run build
```

To update the frontend, upload the contents of `frontend/dist` into a new release directory and switch the `current` symlink atomically. Preserve the Nginx `/admin/` proxy, API routes, SPA fallback to `index.html`, HTTPS settings, and ACME configuration. `index.html` uses `no-cache`; hashed files under `/assets/` use long-lived caching. Retain previous releases and configuration backups for rollback.

Update the catalog through local Compose, from `backend`:

```sh
docker compose build
docker compose run --rm init
docker compose up -d api
```

The `catalog check|migrate|import|bootstrap` CLI validates and loads files. CLI import **replaces the entire catalog** rather than adding a single record. The admin panel offers a separate incremental CSV workflow with a preview: existing IDs are updated only when explicitly selected, and records absent from the uploaded file are retained. Back up the database before a production update. Direct table edits can break integrity checks; use the supported import workflow.

Check the production API:

```sh
curl --fail https://testrr.shop/api/health
curl --fail https://testrr.shop/api/catalog/meta
```

On the server, use `systemctl status hackalem-backend hackalem-admin nginx` and `journalctl -u hackalem-backend`. The backend writes JSON logs with request IDs, status codes, duration, catalog versions, and matching outcomes. Process metrics reset on restart.

## Limitations and future work

The current MVP does not handle bookings, payments, messages to vendors, or verification of their actual availability. The public matching API does not require authentication. Catalog CRUD and CSV uploads are handled by the separate authenticated admin panel, not by the public matching API.

Only dates within the source calendar window are supported. There is no free-text search, semantic ranking, reviews, quality scoring, automatic budget expansion, service-bundle selection, or calendar synchronization. Price sorting is a transparent MVP rule, not a measure of professional quality.

Future work includes extending the admin panel, loading form options dynamically, updating the calendar, adding typed constraints, and evaluating relevance against labeled scenarios. Semantic ranking can be introduced separately among profiles that already satisfy all mandatory constraints.

## Documentation

The detailed documents linked below are currently in Russian.

- [Technical specification](TECH_SPEC.md) — matching and administration requirements, scope, and acceptance criteria.
- [Architecture](ARCHITECTURE.md) — components, data model, matching flow, and design decisions.
- [Backend README](backend/README.md) — setup, storage, import, and operational details.
- [HTTP API](backend/ENDPOINT.MD) — all endpoints, fields, statuses, and errors.
- [Backend testing](backend/TESTING.md) — covered scenarios and results.
- [Frontend README](frontend/README.md) — interface, HTTP/mock modes, and integration.
- [Admin panel](admin_panel/README.md) — authentication, catalog management, CSV import, and setup.
- [Admin API](admin_panel/ENDPOINT.MD) — protected routes and data formats.
- [Example request](backend/examples/recommendation-request.json) and [full response](backend/examples/recommendation-response.json).

## Authors

- **Sanzhar Serikbayev (Серикбаев Санжар)** — Fullstack developer
- **Alina Kumarova (Құмарова Алина)** — Analyst / QA tester
- **Viktor Babanov (Бабанов Виктор)** — Frontend developer
