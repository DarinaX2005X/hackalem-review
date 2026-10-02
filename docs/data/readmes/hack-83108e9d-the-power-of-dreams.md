# join city — подбор подрядчиков для мероприятий

## Описание проекта

join city помогает организаторам мероприятий в Казахстане находить подходящих подрядчиков без долгого изучения каталога. Пользователь указывает город, дату, формат мероприятия и бюджет, а сервис предлагает до трёх подходящих вариантов с понятным объяснением каждого результата.

Система учитывает занятость по календарю, стоимость, специализацию и дополнительные пожелания. Искусственный интеллект помогает дополнять объяснения фактами из описаний подрядчиков, а проверка по исходным данным защищает от выдуманных характеристик. Это помогает сравнить варианты и принять обоснованное решение.

## Технологические теги

Next.js, React, TypeScript, Node.js, Tailwind CSS, OpenAI API, Docker

## Тематические теги

Искусственный интеллект, Подбор подрядчиков, Организация мероприятий, Объяснимые рекомендации

## Application overview

A local web application for hackathon task **#79-lite**.

The Russian-language form asks for **city, event date, event format, contractor
category and budget in KZT**, with optional language and duration under
**Дополнительные условия**. Results show each contractor's name, category,
city, starting price, explanation and data-provenance labels. The catalogue
contains anonymized and synthetic profiles; this is a demonstration of selection,
not a booking service or a source of confirmed contractor availability.

## Quick start with Docker (recommended for judges)

Install and start [Docker Desktop](https://docs.docker.com/desktop/) with
Linux containers on Windows/macOS, or Docker Engine with the
[Compose plugin](https://docs.docker.com/compose/install/linux/) on Linux.
Use Compose **2.20 or later** (Compose 5 is also supported) and a modern browser.
The first build needs internet access to download the base image, OS build tools
and npm packages; allow several minutes. Node.js and npm run inside Docker.
No database, GPU, provider account or `.env` is required for catalogue-only use.

Clone the repository, or download and extract its ZIP. From its root:

```powershell
git clone https://github.com/BAITC-Hacks/hack-83108e9d-the-power-of-dreams.git
cd hack-83108e9d-the-power-of-dreams
docker compose up --build --wait --wait-timeout 120
```

If you already have the project, run only the last command in its root. Open
[the application](http://localhost:3101) and follow the
[primary scenario](#try-the-primary-scenario) below. The command leaves the
application running in the background and waits for a successful catalogue API
healthcheck. The 120-second readiness limit starts after the build; it does not
limit initial downloads. The image includes the supplied CSV and all runtime
files, uses a non-root user, and exposes the application only on this computer.

Check status and run the supplied HTTP smoke check without installing host Node.js:

```powershell
docker compose ps
docker compose exec -T app node scripts/docker/smoke.mjs
```

Expected: service `app` is `healthy`; the smoke check reports seven passing
selection/validation cases and `Container HTTP smoke passed`. On a fresh checkout,
the modes are `catalog_fallback, not_needed`. This uses the real catalogue and
HTTP API; it does not evaluate live AI explanation quality. **If you configure
OpenAI, the smoke check can make four billable provider requests.**

### What Docker installs and starts

| Component | How it is supplied |
| --- | --- |
| Node.js 24.4.1 / npm 11.4.2 | Official Linux base image pinned by digest in `Dockerfile` |
| Application dependencies | `npm ci` installs the committed lockfile in a clean build stage; `npm prune --omit=dev` removes development packages from the runtime stage |
| Build and verification | The image build runs `npm run typecheck`, `npm test` and `npm run build`; a failing check stops the build |
| Web interface and API | One Compose service, `app`, serves both through the same port |
| Catalogue and wishes evidence | CSV is copied into the image; the validated wishes index is bundled during the application build |
| OpenAI | Optional external API, enabled only by runtime credentials; it is not a Docker service |

There is no database, Redis, queue, separate frontend container or dependency
service to start. No source bind mount or persistent volume is needed. The
runtime image includes production packages and compiled assets; browser-test
tools are build/development dependencies. Do not run `npm ci` inside the running
container: rebuild the image when dependencies change.

This Compose configuration is for local evaluation: the host port binds to
`127.0.0.1` and is not accessible from another computer. Public hosting requires
separate network/TLS/access configuration. User results live in browser memory;
reload clears them. Rebuilding is required after catalogue or source changes.

To inspect startup problems or stop and remove this project's containers/network:

```powershell
docker compose logs --tail 100 app
docker compose down
```

If port 3101 is occupied, set `APP_PORT=3111` in a root `.env` (create it if absent,
or edit that one setting without replacing existing values), run the launch
command again and open [the alternate address](http://localhost:3111).
Restart after configuration changes with
`docker compose up --wait --wait-timeout 120`; rebuild with `--build` after source
changes. `docker compose down` preserves repository files and your local `.env`.

### Optional AI explanations in Docker

Create a root `.env` by copying `.env.example` with your file manager, then fill
only `OPENAI_API_KEY`; `OPENAI_MODEL` is optional. Preserve an existing `.env`.
Run `docker compose up --wait --wait-timeout 120` to recreate the service with the
new settings. No image rebuild is needed. A funded OpenAI project, model access
and outbound internet are required; each non-empty selection can make one
billable request for a submission without wishes. Parsing wishes makes one
separate billable request; confirmed wishes use local matching. Missing/failed/rejected AI evidence retains the existing
labelled catalogue or mixed explanations.

Compose reads `.env` for substitution and forwards only `OPENAI_API_KEY` and
`OPENAI_MODEL` to the app. Existing shell variables take precedence, including
an explicitly empty value. A configured key enables live calls automatically.
To use catalogue-only mode, remove/blank the key in `.env` and unset any shell
override before recreating the service. In Compose `.env`, use single quotes
around literal values containing `$` or `#`; unlike the direct Node.js loader,
Compose expands variable references in unquoted/double-quoted values.

Credentials are supplied at runtime; `.env` files are excluded from the build
context and image. Keep them private and out of Git. Avoid sharing expanded
`docker compose config` or container environment output, which can contain keys.

| Docker symptom | Action |
| --- | --- |
| Cannot connect to the Docker daemon / missing Docker Desktop pipe | Start Docker Desktop, enable Linux containers and wait for its engine; `docker info` must succeed. |
| Unknown `--wait` option | Update Compose to 2.20 or later. |
| Build cannot download images or packages | Check internet/proxy access to Docker Hub, Debian and npm registries, then repeat the build. |
| Port is already allocated | Set a free `APP_PORT` as described above. |
| Service is unhealthy or readiness times out | Read `docker compose logs --tail 100 app`; after repairing the cause, repeat `docker compose up --build --wait --wait-timeout 120`. |

Container verification and its exact revisions/limitations are recorded in the
[Docker delivery task card](openspec/changes/docker-compose-delivery/tasks.md).
The 23 September 2026 recheck covers clean dependency installation, the current
production image, HTTP/browser scenarios, confirmed-wishes evidence and an
alternate-port restart. With explicit authorization, two live OpenAI requests
also passed: source-based explanations and wishes interpretation, followed by
local selection using the interpreted conditions. Exact evidence and limits
are recorded in the task card.

## Alternative quick start with Node.js

### 1. Install the prerequisites

- Install **Node.js 24.4.1 or a newer 24.x release** from the
  [official Node.js download page](https://nodejs.org/en/download). On Windows,
  use the installer for your architecture with npm included, then reopen your
  terminal. The recorded project environment is Node.js **24.4.1** with npm
  **11.4.2**; these are the baseline versions in [package.json](package.json).
- Install [Git](https://git-scm.com/downloads/) if you will clone the repository.
  You can also download and extract the repository ZIP and open its root folder.
- Use a modern browser. Internet access is needed to download dependencies and,
  when enabled, to call OpenAI.

Check that the tools are available:

```powershell
node --version
npm --version
```

No database, Docker, Python, WSL, GPU, NVIDIA account or separate backend service
is required for this Node.js route. OpenAI access is optional for catalogue-only
operation. Historical GPU experiments are not part of application deployment.

### 2. Get the project and install dependencies

If you already have the repository, open a terminal in its root (the directory
containing `package.json`) and skip the first two commands:

```powershell
git clone https://github.com/BAITC-Hacks/hack-83108e9d-the-power-of-dreams.git
cd hack-83108e9d-the-power-of-dreams
npm ci
```

`npm ci` installs the runtime and development dependencies pinned in
[package-lock.json](package-lock.json). Do not install Next.js, React or
`csv-parse` individually or globally. Keep development dependencies installed
for the build and checks. No separate dataset download is needed:
`raw/dataset.csv` is included in the repository.

### 3. Choose the explanation mode

**Without OpenAI:** skip configuration on a fresh checkout. The app still reads
the supplied CSV, selects contractors and explains matching format and budget.
It labels these explanations as generated from catalogue fields without AI.

**With OpenAI:** before starting the server, create the local configuration:

```powershell
node scripts/secrets/setup.mjs
```

Open the root `.env` locally and fill `OPENAI_API_KEY`. `OPENAI_MODEL` is optional;
absent or blank uses `gpt-5.6-luna`. The setup command preserves an
existing `.env`. Verify that the key is present without displaying it:

```powershell
node scripts/secrets/check.mjs OPENAI_API_KEY
```

This checks configuration presence only. Live use requires a funded OpenAI
project, access to the configured model and outbound network access. Each
submission without wishes and with selected contractors can make one billable request.
Parsing wishes makes one separate request; selecting with confirmed wishes is local. Existing
environment variables take precedence over `.env`; an already configured key
enables live calls. See [configuration details](#configuration-details) for
precedence, safe handling and optional settings.

### 4. Build and start

Run from the repository root:

```powershell
npm run build
npm start -- --port 3000
```

Keep the terminal running and open [the application](http://127.0.0.1:3000).
Stop the server with `Ctrl+C`. Both start scripts bind to `127.0.0.1` for local
access. Retain `raw/` and `back/` alongside the application: the server loads
the CSV and the existing OpenAI transport from these directories at runtime.
Copying only the build output is insufficient.

### Development mode

After installation and any optional configuration, use this instead of the
build/start pair while editing the app:

```powershell
npm run dev
```

Open [the development server](http://127.0.0.1:3000). To choose a free port,
use `npm run dev -- --port 3102`; for a production build use
`npm start -- --port 3102`. These commands follow the
[Next.js CLI options](https://github.com/vercel/next.js/blob/canary/docs/01-app/03-api-reference/06-cli/next.mdx).

## Try the primary scenario

Enter the following values and press **Подобрать**:

| Field | Value |
| --- | --- |
| City | Алматы |
| Date | 2026-10-10 |
| Event format | корпоратив |
| Category | Ведущий |
| Budget | 1500000 KZT |

Expected with the supplied catalogue: **10 candidates, 5 eligible**, with these
three cards in order: **Куррапика (HK-88430)**, **Аня Форджер (HK-29829)**,
**Сон Гоку (HK-27222)**. Selection and order are the same with or without OpenAI;
the explanations depend on whether validated source quotes are available.

Change the budget to **1** and submit again: the app should display a normal
empty result. Changing fields alone does not make an AI request. To check a
different date, change the date and press **Подобрать** again.

For a short demonstration, continue with these inputs (leave optional fields blank):

| Case | Change from the primary scenario | Expected result |
| --- | --- | --- |
| Rare category | Category Флорист, format свадьба, budget 500000 | One card: HK-39372; explanation of the incomplete three-card set |
| No category in city | Rare inputs, city Зарубежье | Explicit category-absent outcome |
| Busy-date change | Primary inputs, date 2026-10-11 | HK-44923, HK-27222, HK-44733; date comparison explains busy marks |
| Price-order date change | Primary inputs, submit October 1 then October 6 | HK-75012 is replaced by HK-29829 through starting-price order, not a new busy mark |

Reset restores the primary defaults. Without wishes, filtering and price/ID order
select the cards; optional AI supplies source quotes. Starting prices and
calendar marks never guarantee booking. Dataset and software provenance is in
[THIRD_PARTY.md](THIRD_PARTY.md).

### Try AI wishes

With a funded OpenAI key configured, restore the primary inputs and enter
**Нужен ненавязчивый ведущий, без принудительных конкурсов** in **Пожелания к подрядчику**.
Press **Разобрать пожелания**, review the displayed interpretation, remove any
incorrect condition or edit the text and parse again, then press **Подобрать**.
Interpretation alone does not submit a recommendation.

Expected: **Хаул (HK-77838)** moves into first place, followed by HK-88430 and
HK-29829. His profile explicitly states a discreet style. Compulsory contests
remain **Нужно уточнить**: avoiding compulsory contests does not mean rejecting
all contests. Cards show literal profile evidence, contradictions when present,
unknown wishes, and a question to ask the contractor. These are catalogue claims,
not independently verified promises. Budget 900000 still excludes Хаул.

Every hard-eligible profile is considered. Confirmed wishes order by fewer
conflicts, more supported matches, starting price, then ID; they never override
city/category, date, format, budget, language or duration. Up to three cards are
shown. Identical confirmed conditions, catalogue and policy give identical order
after restart. Parsing the same free text again can produce a different
interpretation, so review it before selection. Date comparisons reflect this
wishes-based order instead of attributing every replacement to price.

The current vocabulary covers 18 styles/features, with 48 verified literal
assertions across the 66-profile catalogue. Other wishes and absent claims stay
unknown; absence is not evidence of unsuitability. Text is limited to 1000 Unicode
characters and six interpreted conditions. Changing text invalidates its
interpretation. Reset cancels pending work and clears wishes. If interpretation
is unavailable, the text and previous result remain; retry explicitly or clear
the optional field to use ordinary selection. No key is required for ordinary
selection. An outdated evidence index fails wishes-based selection explicitly
rather than silently replacing it with price order.

The [implementation and measured model comparison](openspec/changes/contractor-brief-matching/tasks.md)
record Luna/Terra quality, prompt repairs, latency and conservative API cost.
The bounded experiment selected Luna; this is not a guarantee of perfect
interpretation for arbitrary customer text.

For developers, `node scripts/brief/compare.mjs --live` runs the 30 synthetic
cases twice on each of Luna and Terra. It requires a funded key and incurs
charges. `--smoke` selects two cases once per model; `--repair` selects the
11-case targeted regression set twice. A persistent local ledger under
`test-results/brief-live-budget.json` reserves a conservative cost before each
call and stops at USD 5. Preserve it across runs. This is an experiment limit,
not an account-wide or application-traffic spending control. Recorded evidence
distinguishes the original full comparison from the targeted prompt repair.

Previous results keep their original conditions while you edit or wait for a
new selection, and survive a failed request. Date-only submissions explain
changes using catalogue busy marks and price/ID order. For example, changing
October 1 to October 6 replaces HK-75012 with HK-29829 because of starting-price
order; HK-75012 still has no busy mark. **Сбросить** restores supported initial
defaults, clears results and optional conditions, and cancels pending work.
Blank optional values do not filter results; supplied duration accepts positive
fractional hours. All categories remain selectable in every city, including
combinations that correctly produce an empty catalogue outcome.

The compact conditions panel can be collapsed without losing entered values.
On mobile, **К результатам** moves to the result heading and collapses conditions;
**Условия** reopens the form. Requests finishing in the background never move
keyboard focus or scroll the page. Selected language and duration remain visible
in the closed **Дополнительные условия** summary.

Contractor explanations, reasons for fewer than three results, both empty
outcomes and date changes stay visible. **Как получился этот список** below the
cards expands the price-order rule and detailed exclusion counts. A pending
request is distinguished from further edits that have not been submitted.

## How it works

The app is one Next.js process serving both the browser interface and HTTP API.
The catalogue is loaded into memory on first use and retained for the process.

```mermaid
flowchart LR
    Form["Browser form"] --> API["Server: validate request"]
    Form --> Parse["Optional wishes: OpenAI interpretation"]
    Parse --> Review["User reviews conditions"]
    Review --> API
    CSV["CSV catalogue in memory"] --> Rules["Hard eligibility rules"]
    API --> Rules
    Rules --> Order["Confirmed wishes: local evidence order; otherwise price / ID"]
    Index["Bundled validated wishes evidence"] --> Order
    Order --> Selected["Up to three contractors"]
    Selected --> Evidence["Without wishes: optional OpenAI source quotes"]
    Selected --> Result["Local explanation assembly"]
    Evidence --> Check["Validate quotes against source descriptions"]
    Check --> Result
    Result --> Cards["Cards and explanation-mode label"]
```

1. The form loads available options from `GET /api/catalog/options` and sends
   conditions to `POST /api/recommendations` only on submission.
2. The server validates the fields and supported date range. Selection first
   narrows the catalogue by city and category, then excludes busy contractors,
   prices above the budget and unsupported event formats. The backend also
   supports the form's optional language and duration filters.
3. Without wishes, eligible profiles are sorted by starting price and catalogue
   ID. Confirmed wishes instead use the versioned source-evidence rule described
   above across all eligible profiles before choosing three. AI interpretation
   is reviewed by the user; hard eligibility and final ordering remain local.
4. Without wishes, if configured, one bounded OpenAI request receives the conditions and evidence
   fields for only the selected profiles. It selects short quotes from their
   descriptions. Local code checks the response structure, profile IDs, quote
   length and literal correspondence with the source before using a quote.
5. Local code assembles explanations from catalogue facts and accepted quotes.
   Missing configuration, provider failure or rejected quotes lead to
   catalogue-only or mixed explanations with a visible label. The underlying
   selection continues to use the supplied CSV. This is not a synthetic test
   fixture substituted for the catalogue.

`POST /api/brief` interprets text separately. The reviewed result is submitted as
optional `brief` to the recommendation operation; its cards include `briefAdvice`
and mode `brief_evidence`. This path uses bundled validated source assertions,
not another provider call. See the public types in `contracts/brief.ts` and
`contracts/contractor-selection.ts` and the
[immutable v2 handoff package](.shared/specs/contractor-selection/versions/v2/README.md).

## Stack and repository layout

All package versions are pinned in [package.json](package.json) and the lockfile.

| Dependency / tool | Role |
| --- | --- |
| Next.js 16.3.6 | Web application and server routes in one process |
| React / React DOM 19.3.0 | Browser form and result cards |
| TypeScript 6.0.3 | Typed contracts and application code |
| csv-parse 7.0.2 | Decode the supplied CSV catalogue |
| Tailwind CSS 4.3.3 / PostCSS 8.5.28 | Installed styling toolchain |
| Zod 4.6.5 | Available validation dependency; current request rules are implemented in server code |
| Node.js test runner | Runs the checks wired to `npm test` |
| Playwright 1.63.0 | Browser verification tooling |
| ESLint 9.39.5 / Vitest 5.0.1 | Installed development tooling; no lint script is currently defined, and `npm test` uses Node's runner |

OpenAI is called through the existing server HTTP adapter; no OpenAI SDK or
additional package installation is required. ESLint remains pinned to major 9
for compatibility with the current Next.js lint configuration.

| Path | Responsibility |
| --- | --- |
| `src/app/` | Page entry point, layout, styles and API routes |
| `front/` | Interactive form, loading/error/empty states and result cards |
| `contracts/` | Public request/response types and labelled examples |
| `back/catalog/`, `back/domain/` | CSV loading, calendar and deterministic selection rules |
| `back/recommend/`, `back/ai/` | Explanation assembly, quote validation and OpenAI transport |
| `back/http/`, `back/composition.ts` | Request validation, HTTP responses and module wiring |
| `back/config/` | Server-only secrets reader |
| `raw/dataset.csv` | Supplied runtime catalogue |
| `scripts/` | Verification and optional operator utilities |
| `domain/`, `architecture/`, `openspec/` | Source requirements, architecture and implementation evidence |

## Checks and troubleshooting

After `npm ci`, run these from the root:

```powershell
npm ls --depth=0
npm run typecheck
npm test
```

Expected: required dependency versions are installed, type checking succeeds,
and secrets, transport, contract, slice, catalogue, selection, evidence,
backend-configuration and frontend-comparison checks pass. These tests use controlled credentials and
transport where needed; no `.env`, provider account, billable call or Playwright
browser installation is required. They do not replace the browser scenario or
live explanation-quality review. `npx playwright install` is optional for
browser-test tooling, not an application prerequisite.

| Symptom | Action |
| --- | --- |
| `node` or `npm` is not recognized | Install Node.js with npm, reopen the terminal and check the versions. |
| Missing `csv-parse`, `UNMET DEPENDENCY`, or stale/extra packages | Stop this checkout's server and run `npm ci` in the root, then repeat the dependency check. Keep the committed lockfile. |
| Start reports a missing production build | Run `npm run build` successfully before `npm start`. |
| Port is already in use | Choose another port with `-- --port 3102` and open the corresponding URL. |
| Date is rejected | Use a date between **2026-09-23 and 2026-12-31**, inclusive. |
| Catalogue is unavailable | Ensure `raw/dataset.csv` exists and is intact, run from the root, then restart the server after repair. Failed catalogue loads are retained until restart. |
| Explanations say they were generated without AI | This is a supported result. For live quotes, check the OpenAI setting, account/model access and network. Rejected quotes also fall back to catalogue facts. Restart after configuration changes. |

Optional live domain check, after configuring OpenAI:

```powershell
node scripts/slice/live.mjs
```

This makes one billable dense-domain request and prints public output and
sanitized evidence metadata. Full live acceptance also needs manual review of
source correctness, relevance and distinctiveness. A fallback is not a live
quality pass.

## Limitations and verification status

- The supplied calendar covers **23 September–31 December 2026** only.
- Prices are starting prices. A date without a busy mark is not a confirmed
  booking; availability and final conditions must be checked with the contractor.
- Synthetic/anonymized profiles and imputed city/price values are labelled.
- There are no booking, messaging or saved-search features, no persistent user
  data, and no AI quality ranking.
- Date comparisons apply only when the date changes and all other normalized
  conditions, catalogue version and selection policy are unchanged. Only the
  latest successful result is kept in memory; reset or reload clears it.
- Catalogue/configuration changes require a server restart.

Recorded acceptance belongs to the linked revisions and scopes, not to every
future checkout. Final live rendered-text decisions, three-request timings,
clean-checkout evidence and exact publication status are in the
[P07 delivery task card](openspec/changes/archive/2026-09-23-integration-and-delivery/tasks.md).
Repository publication is separate from submission to the organizer; no
organizer submission is performed by the run instructions.

To reproduce the final live timing series after the production build, stop any
server on port 3107 and run `node scripts/delivery/live.mjs` with local OpenAI
configuration. It starts and stops its own production server and makes exactly
three application submissions (dense, rare, dense); normal provider retry policy
still applies. It requires the Playwright tooling already pinned in the lockfile
and Microsoft Edge installed locally. Results and public screenshots are written
under ignored `test-results/p07-live`. It fails on live fallback; per-card semantic
quality still needs review against the source. This optional acceptance tooling
is not required to use the application and incurs paid API usage.

| Area | Requirements and recorded evidence |
| --- | --- |
| Foundation and public contracts | [P00 task card](openspec/changes/archive/2026-09-23-foundation-and-contracts/tasks.md) |
| First working browser scenario and clean build/start | [P01 task card](openspec/changes/archive/2026-09-23-first-working-slice/tasks.md) |
| Catalogue loading | [P02 task card](openspec/changes/archive/2026-09-23-catalog-module/tasks.md) |
| Selection rules | [P03 task card](openspec/changes/archive/2026-09-23-selection-domain/tasks.md) |
| Validated AI evidence | [P04 task card](openspec/changes/archive/2026-09-23-validated-ai-evidence/tasks.md) |
| Connected backend and frontend handoff | [P05 task card](openspec/changes/archive/2026-09-23-backend-composition-and-handoff/tasks.md) |
| Complete frontend flow and date comparison | [P06 task card](openspec/changes/archive/2026-09-23-frontend-selection-flow/tasks.md) |

For product context, start with [domain documentation](domain/README.md).
See [architecture](architecture/README.md) for design and
[OpenSpec](openspec/) for requirements and current task evidence. The
[module proposal sequence](.proposals/README.md) preserves the original planning
order; it is not an instruction to reimplement completed modules.

## Configuration details

Requires Node.js 24.4.1 or compatible Node.js 24. These commands need no
additional packages. Run from the repository root:

```powershell
node scripts/secrets/setup.mjs
```

This creates one root `.env` from [.env.example](.env.example). An existing
`.env` is left unchanged. Open the file locally and fill the settings you use:

| Setting | Purpose | Required when |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API credential | A server operation uses OpenAI |
| `OPENAI_MODEL` | Optional model override; blank uses `gpt-5.6-luna` | Only to override the default OpenAI model |
| `APP_PORT` | Docker Compose host port; blank uses `3101` | Only to override the Compose port; ignored by `npm start` |

For the direct Node.js secrets reader, quote values containing `#` or
whitespace. Values are literal; references such as `${OTHER_VARIABLE}` are
not expanded. Docker Compose uses its own interpolation rules: single-quote
literal values containing `$` or `#`, as described in the Docker section.
Add future secrets to the same file and document their empty entries in the
template.

For this application, check only the OpenAI key if using live quotes:

```powershell
node scripts/secrets/check.mjs OPENAI_API_KEY
```

A successful check exits with
code 0 and says required settings are present. Missing or blank values exit
with code 1 and name the missing settings without printing their values.
Running without names shows usage and fails. This checks presence only;
it does not validate credentials, contact providers, or connect to a database.

Existing process environment variables take precedence over the file, including
blank values (which fail validation). This also supports deployments supplying
all settings through their environment without a file. The scripts locate the
root file relative to their own location, independently of the working directory.

Keep the filled `.env` out of Git, public archives, screenshots, logs, and
browser code. Git ignores `.env` and its variants but cannot prevent a forced
add. The file is plaintext: restrict local access. Organizers can use their own
credentials. If team credentials are provided, transfer the file separately
through an agreed private channel; never put them in a repository or public link.
Only the empty template belongs in the repository.

### Server integration reference for developers

The server composition calls
the reader before external operations and passes only the required values to
the corresponding adapters:

```javascript
import { loadSecrets } from './back/config/secrets.mjs';

const { OPENAI_API_KEY } = loadSecrets({ required: ['OPENAI_API_KEY'] });
// Pass the value to the server adapter; never log or return it to a client.
```

The import above is relative to a server entry point in the repository root.
The reader returns a frozen object containing only the requested names; it
does not mutate `process.env`. Errors have a stable `code`, a safe `message`,
and a `requestId`. Browser modules must not import `back/config/`; names
starting with `NEXT_PUBLIC_` are rejected. The P01 task card records application integration separately from the original secrets checks.

Run the focused checks with synthetic temporary credentials:

```powershell
node --test scripts/secrets/secrets.test.mjs
```

Current requirements and verification status:
[OpenSpec tasks](openspec/changes/unified-local-secrets/tasks.md).

## OpenAI server adapter reference for developers

Requires Node.js 24 and a funded OpenAI API project with model access. No SDK,
GPU or additional npm installation is required for this module. Run the secrets
setup above and fill `OPENAI_API_KEY` privately. `OPENAI_MODEL` is optional;
absent or blank selects `gpt-5.6-luna`. Luna and Terra use `reasoning.effort: none`
for this extraction task. Both were tested with the current strict schema.

```powershell
node scripts/openai/check.mjs
node --test scripts/openai/contract.test.mjs
```

The first command makes one billable live request with a fixed benign prompt.
Expected: JSON with `ok: true`, `mode: live`, the model, token usage and duration.
It prints neither the key nor provider response contents. The second command
uses synthetic credentials and a local test server; it incurs no provider cost.

From a server module at the repository root:

```javascript
import { createOpenAIFromEnv } from './back/ai/openai.mjs';

const openai = createOpenAIFromEnv();
const result = await openai.generate({
  input: 'Summarize the supplied text.',
  instructions: 'Use only facts from the input.',
  maxOutputTokens: 450,
  // signal: callerAbortSignal,
});
// Use result.text; do not log private inputs or secrets.
```

`generate` also accepts developer-controlled `format: { name, schema }` for
strict JSON-schema output. The caller must parse and validate domain data.
Results include `text`, `provider`, `mode`, `model`, `responseId`, `requestId`
and optional `usage` with input/output/total token counts. Errors have a safe
`message`, stable `code` and `requestId`. Codes distinguish configuration/input,
authorization, rate/quota limits, rejected requests, provider unavailability,
invalid/incomplete/refused responses, network failures, timeout and cancellation.
The live check exits nonzero and prints the code on failure.

Calls use Responses with `store: false`, a six-second deadline including body
consumption, caller cancellation, zero retries and no fallback. Local cancellation
does not guarantee cancellation of provider billing. Never import this Node-only
module into browser components. This verifies transport access; application
routes, contractor selection and UI integration are recorded separately in the P01 task card.
See [adapter requirements and evidence](openspec/changes/openai-response-adapter/tasks.md).
