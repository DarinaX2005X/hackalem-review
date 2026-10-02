# QOR — Supplier Replenishment

Single-process Streamlit purchasing workspace: audited imports, causal demand
review, deterministic dated inventory planning, scenarios, versioned manager
approval, and verified CSV/XLSX export. No API server or supplier dispatch.

**Verified source:** the local `Downloads/IEK.zip` archive. Real Systeme Electric
files, the named original case file `Вставленная ​​уценка.md`, and participant model access were not found
in the searched locations. The built-in SE walkthrough is visibly **synthetic**.
Live AI is **blocked**, not mocked. See [current QA](docs/QA_REPORT.md).

The app opens at `/` with a Russian product overview and a clearly labeled
static synthetic calculation example. The working Источники, Спрос, Заказы
and Сценарии views are at `/workspace`. The overview links directly into that workspace. For the current
product audit and diagrams, see [PRODUCT_AUDIT.md](docs/PRODUCT_AUDIT.md),
[PRODUCT_AND_ARCHITECTURE.md](docs/PRODUCT_AND_ARCHITECTURE.md),
[FEATURE_MATRIX.md](docs/FEATURE_MATRIX.md), and
[DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). Theme and accessibility tokens are in
[DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md).

## Demo release and online deployment

The demo release is tagged **v0.1.0-demo**. GitHub Actions workflows are
configured to test pushes and pull requests. A tag matching **v*** creates a
GitHub Release from the checked-in release notes when organization-hosted
Actions runners are available.

Streamlit Community Cloud deployment coordinates:

| Setting | Value |
|---|---|
| Repository | **BAITC-Hacks/hack-b734fee1-zhasik1** |
| Branch | **main** |
| Main file path | **frontend/app.py** |
| Python | **3.12** |

No application secrets are required. See [DEPLOYMENT.md](docs/DEPLOYMENT.md)
for the one-time account setup, operating limits, and verification checklist.

## Install and run

Target Python 3.12 with the tested pins in `pyproject.toml`. The previous
Python 3.14 `.venv` remains intact; the clean 3.12 verification environment is
under ignored `runtime/venv312`. `requirements.txt` delegates to
`pyproject.toml` and is not a separate dependency list.

Windows PowerShell, from this project directory:

```powershell
py -3.12 -m venv runtime\venv312
.\runtime\venv312\Scripts\python.exe -m pip install -e '.[test]'
.\runtime\venv312\Scripts\python.exe -m streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8511
.\runtime\venv312\Scripts\python.exe -m pytest -q
```

Linux/macOS (commands provided; not executed on Linux in this audit):

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m streamlit run frontend/app.py --server.address 127.0.0.1
.venv/bin/python -m pytest -q
```

If port 8511 is occupied by the already running app, open it or choose another
port. Use **frontend/app.py**; root `app.py` and `qor/` are preserved legacy code,
not the implemented MVP entry point. The frontend explicitly selects `backend/`
to avoid that legacy package shadowing the editable installation. For standalone
scripts, add `backend/` to the front of `sys.path` as the verification scripts do;
from inside `frontend/`, ordinary `import qor` resolves to the installed backend.

```text
backend/qor/
  __init__.py
  contracts.py          # validated policy, stock, review and AI-tool inputs
  data/                 # read-only ZIP/XLSX/CSV adapters + synthetic demo
  demand/               # candidate review, stockout correction, forecasts/evaluation
  planning/             # daily inventory and MOQ/pack calculation
  ai/                   # bounded deterministic router; live provider blocked
  storage/              # SQLite versions, audit, approval and export verification
  service.py            # shared orchestration for UI and future AI tools
frontend/
  app.py
  app_pages/            # Overview and purchasing-workspace routes
  components/views.py   # Источники, Спрос, Заказы, Сценарии
tests/                  # source, forecast, planning, workflow and UI tests
docs/                   # evidence, model-access audit and demo
sample_data/            # synthetic/shareable fixtures only, no private originals
scripts/                # source verification and local smoke checks
runtime/                # ignored local SQLite/evidence, created at runtime
pyproject.toml
README.md
.gitignore
.streamlit/config.toml # dark product theme
```

## Input format and privacy

Upload supplier files on **Data**, choosing the supplier explicitly. Multiple
uploads for a supplier replace its prior upload batch; uploads for the other
supplier can coexist. ZIP is read in memory, never extracted or modified. XLSX
uses cached cell values (`data_only`); formulas are never executed. CSV is UTF-8,
comma-delimited. Unsupported headers are reported, not guessed.

Canonical columns (text SKU is mandatory, supplier comes from the upload selector):

| Table | Columns |
|---|---|
| Transactions | `sku`, `unit`, `date`, `quantity`, `document`, `warehouse` |
| Available stock | `sku`, `unit`, `free_stock`, `as_of`; optional `reserved` |
| Pending inbound | `sku`, `unit`, `inbound_qty`, `eta`, `document` (shipment ID) |
| Purchase rules | `sku`, `unit`, `moq`, `pack_multiple`, `category`, `article` |
| Monthly sales | `sku`, `unit` if known, month columns such as `2024-01` |

Dates: `YYYY-MM-DD` or `DD.MM.YYYY` (optional `HH:MM:SS`). Common Russian IEK
headers and Russian monthly columns are recognized. Text `0007_` remains text;
numeric Excel SKU cells generate a warning because lost leading zeroes cannot
be recovered. Quantities may use decimal commas. No conversion between pieces,
packs, coils and meters is inferred. Blank units can be mapped only if a unique
known unit exists; purchase-side use requires explicit manager confirmation of
factor 1. Conflicting units or duplicate lookups block that SKU.

Real IEK adapters cover transactions, monthly sales, monthly opening stock, MOQ,
and dated shipment columns. Monthly opening stock is **not** current stock.
The supplied seasonality reference is not applied blindly because its basis
is unverified. Real SE header compatibility awaits that archive; canonical SE
fixtures exercise the same engine. Only explicit anonymized customer IDs are
accepted; customer names, contact details and addresses are not imported.

Private spreadsheets/archives, CSVs, DOCX/PDF uploads, secrets, SQLite and exports
are ignored by Git. This does not untrack files already committed: inspect
`git status` before publishing. No private data or credentials are sent to AI.

## Calculation methodology

Snapshot defaults to **2026-09-22**, not the machine's current date. September is
incomplete and excluded from forecast fitting. This historical snapshot must
be replaced with current data for actual purchasing.

1. Preserve returns, blanks and zero separately. Returns do not become negative
   demand. Reconcile overlapping monthly totals with net transactions; never
   add them. Use monthly 2024 and transactional 2025+ history. Absent months
   remain missing rather than being invented as zero sales.
2. Candidate large purchases are flagged at document/day level using only the
   preceding 60 documents (at least 20): log-median plus six log-MADs, with a
   minimum ten-times-median threshold. When an anonymized client ID exists,
   a concentrated one-client document can also be flagged against prior
   60-day sales. Original and reviewed sales remain visible; an unreviewed
   candidate is capped only in forecast input. A dated, reasoned manager
   `keep` or `exclude` decision overrides the cap. Real customer IDs were
   not supplied, so the client branch is demonstrated with synthetic IDs.
3. Seasonal forecast uses complete prior years (latest two weighted 25%/75%),
   normalized monthly factors, and a weighted six-month deseasonalized level.
   Baseline is a three-month mean. `auto` uses a source-fingerprint and horizon
   matched offline comparison where available, by supplier/unit/intermittency;
   otherwise it labels a seasonal fallback. The manager can select either
   baseline explicitly. A local CPU HistGradientBoostingRegressor challenger
   was trained and evaluated on a real IEK 100-SKU sample, but did not win the
   held-out gate and is not deployed. See
   [measured results](docs/FORECAST_EVALUATION.md); no accuracy is promised.
   Future data and later review decisions are excluded from earlier origins.
4. Optional confirmed file growth uses the same month one year earlier times
   `(1 + growth)` **once**, never an already grown recent level. Confirmation is
   a manual assumption with provenance in the saved policy, not an auto-read
   trusted growth file. Confirmed stockouts use preceding observed demand/calendar
   days for a bounded daily compensation; overlapping intervals are counted once.
   Hypothetical 7/14-day unknown-stockout sensitivity is labeled as a scenario.
5. Defaults: lead `L=14`, review `R=7`, buffer `S=7` days, editable by manager.
   For day t: `P(t) = free_stock + sum(inbound ETA <= t) - sum(demand <= t)`.
   Only future pending receipts after the dated snapshot are added, at the
   start of their expected delivery day. Unknown ETAs and past/today pending
   shipments require reconciliation and are excluded by default. Backlog stays
   negative; late receipts never erase the earlier shortage warning.
6. `buffer(t) = demand(t+1 .. t+S)` and
   `raw_need = max(0, max(buffer(t) - P(t), t=L..L+R))`.
   Taking the maximum across that interval protects against a late receipt
   making only the final balance appear adequate. If need is positive,
   `qty = ceil(max(raw_need, MOQ) / pack_multiple) * pack_multiple` when a pack
   multiple is supplied. MOQ is a minimum, not inherently a multiple. No need
   means zero order even when MOQ exists. Missing pack rules permit fractional
   quantities and explicitly require review. IEK's ambiguous dispatch field
   interpretation is selected by the manager.

The first negative projected balance is a **forecast shortage date**, not an
observed stockout. Shortage before lead time is `expedite`; a normal new order
cannot fix it. Free/available stock is used once; reservations are not subtracted
again. Missing/undated/stale stock blocks approval. Sources, policy, forecast
history, binding date, daily inventory, assumptions and reasons are inspectable.

## Manager workflow

Enter the responsible manager, load data, review demand, supply evidenced dated
stock where needed, and calculate one SKU or all SKUs of one supplier. Save
quantity adjustments with a reason. SQLite stores immutable versions through
`draft → review → approved → exported`; an edit resets approval. Export is
generated from the latest approved revision and reopened/compared before
download. CSV and XLSX escape spreadsheet formula text and preserve SKU codes.
Nothing is dispatched. Default DB: `runtime/qor.sqlite3`; override `QOR_DB_PATH`.

This is a local single-user MVP, not authenticated enterprise approval. Manager
names are audit labels, not verified identities. Keep the server on localhost;
multi-user authorization, encrypted storage, budgets, currencies, transport
capacity, and production deployment are outside this implementation.

## AI gate

No participant endpoint/provider, authorized model identifier, credential,
checkpoint, or documented protocol was found. No model ID was guessed and no
SDK/runtime can honestly be selected for an unidentified resource. `PendingProvider`
raises an explicit blocked result. The local router exposes only `inspect_data`,
`calculate_plan`, `simulate_policy`, `explain_sku`; it cannot approve or dispatch.
It is **not** a verified live function-calling integration.

`scripts/model_probe.py` currently exits before networking because required
entitlement variables are absent. Its legacy generic HTTP branch is only a
preliminary Responses-shaped probe, not a provider-neutral verified adapter.
Do not enable it without checking organizer protocol documentation. Once exact
access is provided, install that documented SDK/runtime, keep credentials outside
source control, and verify a live text + tool round trip before enabling AI.
For a documented OpenAI API use Responses function calling, with Python remaining
authoritative for quantities. `.env.example` contains blank names only; dotenv
is not automatically loaded.

## Verification and demo

```powershell
.\runtime\venv312\Scripts\python.exe -m pytest -q
.\runtime\venv312\Scripts\python.exe scripts/train_forecast.py --iek 'C:\Users\Kuralai\Downloads\IEK.zip' --max-skus 100
.\runtime\venv312\Scripts\python.exe scripts/evaluate_forecast.py
.\runtime\venv312\Scripts\python.exe scripts/smoke_real_ui.py
```

Real source evidence and derived traces stay in ignored `runtime/`; do not
publish them. Import caching is bounded; UI displays filtered previews of at
most 300 rows and only computes the selected view. Initial real ZIP import is
about 20 seconds on the tested machine, not instantaneous. The 249k benchmark
is generated CSV import/audit only, not a claim about full supplier forecasting.

Demo: load **Open labeled synthetic walkthrough** → choose Systeme Electric →
Demand review/evaluation → Orders calculate → adjust with reason → review →
approve → generate/reopen export. Then load real IEK and show the missing-current-
stock gate and the 7/14/30 scenarios. See [demo and requirement evidence](docs/IMPLEMENTATION_VERIFICATION.md).
