# HackAlem AI — консультант каталога EKT

## Кратко для жюри

- **Задача:** помочь покупателю найти электротовары по артикулу или описанию, сравнить аналоги и разобрать спецификацию. Цены и остатки показаны из проверяемого снимка каталога EKT, а неподтверждённые условия продажи не выдумываются.
- **Технологии:** Python 3.12, FastAPI и Uvicorn; HTML, CSS и JavaScript без фронтенд-фреймворка; OpenAI API для диалога и эмбеддингов; NumPy для поиска, SQLite для кеша эмбеддингов. Источник товаров — API EKT.
- **Запуск:** установите зависимости, скачайте подготовленные данные с Kaggle и скопируйте папку `data` в корень проекта, объединив её с существующей папкой. Укажите `OPENAI_API_KEY` в `.env` и запустите сервер. Инструкция — в разделе [Run with prepared Kaggle data](#run-with-prepared-kaggle-data). Для этого пути не нужны доступ к API EKT и повторное построение эмбеддингов.
- **Проверка:** без ключей выполните команды из [Reviewer quick start](#reviewer-quick-start); при наличии Node.js дополнительно запустите `node --test tests/frontend_workflows.cjs`. Для проверки уже подготовленного приложения откройте `http://localhost:8000`, найдите артикул `151100015_` и проверьте `/api/ready`.

В текущем снимке EKT нет подтверждённых минимальной партии и шага покупки. Товары с ценой и положительным остатком можно добавить в предварительную корзину; условия продажи нужно уточнить у поставщика.

A Russian-language shopping assistant for the [ekt.kz](https://ekt.kz) catalog. It searches a downloaded catalog by article or description and shows product details and stock from that snapshot. Products with a known price and positive warehouse stock can be prepared for a local cart, and adding them always requires explicit confirmation. This is a hackathon prototype; it does not place an order or reserve stock.

The app uses a snapshot because semantic search needs a prebuilt embedding index for the catalog. It calls the EKT API when downloading or refreshing data, not for each chat request. This makes searches independent of EKT API availability during a demo, but prices and stock can become stale.

## Reviewer quick start

The automated tests need **no API keys or catalog download**. Run this first; the prepared Kaggle data lets you run the UI without downloading or embedding the catalog yourself:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -c constraints.txt
python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"
python -m pytest -q
```

Use Python 3.12. On Windows, run these commands in WSL/Ubuntu: the catalog downloader uses Unix file locking. CI runs the same test command on every push and pull request.

To try the live UI with the prepared Kaggle data, you need an OpenAI API key for chat and semantic queries. EKT catalog API credentials are needed only to download a fresh snapshot. Tests use fixtures. Credentials and downloaded data are not committed.

## Run with prepared Kaggle data

The prepared Kaggle data contains exactly two files: the catalog CSV and one bundle with saved embeddings and matching product records for 15,037 products. Download it from the [Kaggle dataset](https://kaggle.com/datasets/0b00e052ecd76da9facf9b97c354efebadfe611689523fbf5f0b6ac5229067f8).

1. Sign in to Kaggle, download the dataset, and unzip it. No password is required.
2. Copy the extracted `data` folder into the repository root, beside `README.md`. Merge it with the existing `data` folder; do not delete that folder or create `data/data`.
3. Check that these two files exist:

```text
data/ekt/products.csv
data/index/catalog-index.zip
```

After installing dependencies as in [Reviewer quick start](#reviewer-quick-start), run:

```bash
cp .env.example .env
# Set OPENAI_API_KEY in .env; keep EMBED_MODEL=text-embedding-3-small.
python main.py
```

Open [http://localhost:8000](http://localhost:8000) and check `GET /api/ready` for HTTP 200 and 15,037 products. Search for article `151100015_` to check the catalog. The package already includes vectors, so do not run `download_ekt.py` or `python -m app.index_build` for this review path. The CSV is provided for inspection; the running app reads `catalog-index.zip` directly, so do not extract that inner file. Chat and natural-language searches still call the configured OpenAI API. If the embedding model or text template changes, download a fresh catalog snapshot and rebuild the index.

## Run with a downloaded catalog

```bash
cp .env.example .env
# Fill OPENAI_API_KEY, EKT_API_USER, and EKT_API_PASSWORD in .env.
python download_ekt.py
python -m app.index_build
python main.py
```

Run these commands after installing dependencies as above. Open [http://localhost:8000](http://localhost:8000). The cart is at `/cart`. `GET /api/ready` returns HTTP 200 with the catalog version and product count when the index is usable, or HTTP 503 when it is missing. The index command embeds all downloaded products. Indexing calls the embedding API and may incur cost. Re-running the build reuses cached embeddings.

The downloader resumes interrupted raw-response downloads. Existing CSV rows do not count as complete: run the downloader once to backfill the full API data. Use `python download_ekt.py --new` for a fresh snapshot. Change `EMBED_MODEL` only if you also rebuild the index. Set `CHAT_MODEL` to a model available to your API account.

## Five-minute review flow

1. Run the key-free test command above. It checks the cart and confirmation flow with products that have confirmed purchase rules.
2. With a prepared catalog and API key, search for article `151100015_` or ask for “Автоматический выключатель 16 А”. Open a product card to inspect its source, price, stock and technical details.
3. Try **Показать аналоги** or ask about delivery terms. The assistant should distinguish known facts from information that needs supplier confirmation.

The current 15,037-product EKT snapshot has no confirmed minimum quantity or purchase increment for any product. Products with a known price and positive warehouse stock can still be added to a provisional cart. The app shows which supplier terms remain unconfirmed; confirmed terms are enforced when available.

Exact article matches avoid an embedding call. Natural-language searches use the local embedding index. The model can prepare a proposal for an in-stock product, but only the server's confirmation handler changes the cart. A proposal expires after 10 minutes; prices and quantities are checked again on confirmation.

The product card's quantity control uses server-calculated minimum, multiple, and remaining stock. Missing requested technical specifications are marked for clarification. Monetary API values are decimal strings; the displayed price and totals come from server-formatted labels.

Adding a product requires a known price and positive warehouse stock. Missing purchase terms do not block the provisional cart; any confirmed minimum quantity or purchase increment is enforced. Unknown selling units are shown as catalog units, without claiming a supplier-confirmed unit. A metre-based selling unit does not prove that the supplier offers any particular cut length. `KRATNOST_MIN`, `KRATNOST_MAKS`, package lengths and numbers in names are not substitutes for documented purchase rules. Confirmed terms must come from catalog ingestion, not chat assertions or browser parameters.

### Everyday chat controls

- **Новый чат** clears the conversation, pending proposal, selection and attachment review while keeping confirmed cart items. It also invalidates an in-flight response. It starts a fresh conversation; it does not archive previous conversations.
- Each answer retains its own product cards and source links. Visible history lasts for the anonymous session; only the last 20 text messages are sent as model history. Sessions still expire after inactivity and are cleared on server restart.
- **Остановить** discards a pending response and restores the submitted draft. You can type the next message while waiting. A provider call already in progress may finish, but its late results cannot change the chat, proposal or cart.
- **Показать аналоги** works on available and unavailable products and provides matching attributes, differences and unknowns. The same read-only capability is available to the assistant.
- Cart quantities are editable. Decreases are validated and saved; increases show the additional quantity and cost and require confirmation.
- Specification checkboxes, candidate choices and edited quantities survive rerenders. Review drafts also survive refresh in the same tab via session storage; original file bytes are never saved there.

## Scope and checks

`app/` contains the FastAPI API, catalog search, model tools, and cart rules. `static/` contains the browser UI. `download_ekt.py` saves catalog records under `data/ekt/`; `python -m app.index_build` publishes a validated index under `data/index/`. These generated directories and `.env` are ignored by Git.

After a raw archive is published, the index builder reads only that archive and verifies every response checksum. Older CSV/detail files cannot overwrite its values or fill in obsolete stock. Legacy file precedence is retained only for old installations and test fixtures without an archive pointer. Fetch timestamps identify when responses were observed; the provider's own stock update time remains unknown.

```bash
python -m pytest -q
```

The tests cover search, index publication, model tool restrictions, cart proposals and confirmation, stock checks, document reconciliation, row completion, unit mismatches, request recovery, session ownership, concurrent or duplicate confirmation, and API behavior. They mock external services. Frontend workflow regressions run with `node --test tests/frontend_workflows.cjs`.

There is no login. An anonymous cookie connects chat and cart, and a server restart clears those sessions. Localhost ports use separate session cookies so simultaneous demos do not interfere. Catalog prices and stock are snapshot values. Missing price or stock prevents additions. See [acceptance results](ACCEPTANCE.md) for real-provider/browser checks, measured latency and source-data limitations.

## Consultation and specification workflow

- Payment and delivery answers use `app/policies.json`, verified against [EKT's published information](https://ekt.kz/about/information/) on 2026-09-23. Overlapping Алматы delivery thresholds are reported for supplier confirmation. The demo does not accept payment.
- Alternatives compare technical families and electrical/mechanical attributes. Conflicting known attributes exclude candidates; missing compatibility information stays visible. These comparisons do not certify suitability for an installation.
- Upload JPEG, PDF, DOC/DOCX, XLS/XLSX or CSV: at most five files, 10 MB per file and 20 MB total. Spreadsheets/CSV support up to 1,000 rows per sheet and 20,000 reviewed rows per session. Supported tables are automatically processed in bounded chunks. PDF is limited to 100 pages. Encrypted, corrupt and inconsistent file types are rejected before model submission. Office embedded images require PDF export or separate images.
- Table review reconciles every nonempty data row. Source references and requested units remain visible; duplicate products aggregate distinct row contributions. Correct articles or units, search alternatives, or exclude rows with a reason inline. Select all ready rows and confirm successive batches of at most 50. Confirmed rows are excluded from later batches unless explicitly reopened. PDF, Word and image extraction remains model-assisted and requires a manual completeness check.
- XLS/XLSX/CSV are parsed locally; other uploaded bytes are forwarded to the configured model provider with `store=False`; the application does not save those bytes or log file contents. Session memory retains conversation text and extracted review information. This does not override the provider's retention policy. Failed processing keeps the browser draft for retry. Do not upload payment details or confidential documents.

The compact selection tray preserves browsing position. A product can go directly from quantity entry to a server-owned confirmation. Expired proposals can be renewed in one click. Catalog search offers stock and price controls, real pagination and comparison of two or three products.

Composer text, quantities and document review edits survive refresh within the same browser tab. Refresh reconnects to active work; existing products remain reviewable while a response runs. A second upload adds to the current review, and starting a new chat asks before discarding unfinished work. Server sessions remain in memory; this does not provide durable saved procurement work.

## Data provenance and refresh

Each download run lives in `data/ekt/raw/<run-id>/`. `pages/` and `details/` contain unchanged response bodies; `manifest.json` holds request parameters, fetch times, HTTP statuses and SHA-256 checksums separately. All JSON fields are retained, including unknown fields, nested arrays, offers, warehouse IDs, nulls and embedded specifications. Linked files are preserved as URLs; their binary contents are not downloaded.

The downloader uses 500 records per page and stops at a short or empty page. Repeated IDs/pages fail the run, since the upstream API can wrap back to its first page. Detail URLs must use the configured EKT API endpoint; redirects are disabled. Downloads resume from verified raw responses, never CSV IDs. `--concurrency` controls simultaneous requests (default 16).

`data/ekt/download.json` points to the resumable run. `data/ekt/current.json` changes only after every listed product has a valid detail response. `report.json` records completeness, field coverage and IDs no longer listed. Derived `products.json` and `products.csv` live inside the run; CSV nested cells use JSON instead of delimiter flattening. The existing application index remains active until a new index build succeeds:

```bash
python download_ekt.py --new
# If interrupted, resume without --new:
python download_ekt.py
python -m app.index_build
```

Normalized products retain `source_fields` and `source_response` for provenance, complete properties and offers, and warehouse IDs. Explicit cord/roll lengths are exposed in `lengths` with original values, source fields and parsed metres. `embedded_specifications` decodes recognized embedded JSON without changing the original string. A positive `METRAZHNYY_TOVAR` flag supplies the selling unit `м` when an explicit unit is unavailable. Supplier quantity and lead time are exposed separately in `supplier_availability`; they never increase catalog stock or promise delivery to the customer. Expanded product cards show the full description. Package information, stock, length and purchase increments remain distinct; numbers in product names and `KRATNOST_MAKS` are not guessed to be lengths.

Index publication is atomic. Metadata records the source run, field coverage, model, checksum and build version. Certificate IDs such as `FILES_CERTIFICATES` are not links. `KRATNOST_MIN` alone remains supplier-unconfirmed; known purchase rules are enforced when proposing and confirming. The legacy targeted refresh helper refuses to modify published raw archives: use a fresh complete run instead. Synthetic fixtures stay in tests and are never mixed into the real catalog.

Configure `EKT_API_USER` and `EKT_API_PASSWORD` through the environment or ignored `.env`, not source code. `docs/` is ignored because local client documents can contain credentials. Runtime timing logs record request ID, method, route template, status and elapsed seconds.

## Embedding text and retrieval checks

The active vectors are `data/index/<version>/embeddings.npy`, with product records and checksummed metadata alongside them. `current.json` selects the version; `embedding-cache.sqlite3` reuses vectors for identical model/token inputs. The Kaggle package combines the active vectors, product records and metadata in `data/index/catalog-index.zip`, which the app reads directly when no `current.json` is present. Query vectors use a bounded in-process cache.

`app/embedding_text.py` owns an explicit allowlist of readable identity and technical fields, independently of UI labels. It omits stock, supplier lead times, price-display flags, media IDs, barcodes, promotional category paths and unknown properties. Original fields remain in product metadata. Stable fields are sorted, HTML is removed, and descriptions come last. Each product uses at most 8,192 tokens; requests contain at most 64 inputs and 300,000 tokens. Overlong search queries are rejected instead of silently losing customer requirements.

Increment `EMBEDDING_TEMPLATE_VERSION` when changing field selection, labels, cleanup, ordering or truncation, then rebuild before starting the updated app. An index with an absent or different template version is rejected. Index builds reuse cached vectors and only replace the active pointer after successful validation. CI caches the tokenizer vocabulary during setup, so first-use tokenization needs no download there.

Run the labeled Russian retrieval regression independently of the chat model:

```bash
python -m scripts.retrieval_eval
# Diagnose thresholds; calibration and validation groups are reported separately:
python -m scripts.retrieval_eval --thresholds 0.30 0.45 0.50 0.55
```

These commands call the embedding API. Reports go to ignored `data/acceptance/retrieval.json` and record the snapshot, label hash, hit@5, MRR@5 and no-match accuracy. The default run exits nonzero on any failed case. Labels in `scripts/retrieval_cases.json` are manually selected real product IDs; missing products fail explicitly and require label review. Positive targets are not exhaustive relevance judgments, so the report does not claim precision or recall over the entire catalog. This small regression set is not a production quality guarantee. Full chat acceptance also requires these queries to retrieve the labeled products or return no products for negative cases.

The current cutoff is 0.55 for `text-embedding-3-small` with template 1. Lower cutoffs returned unrelated products for out-of-catalog requests, including automotive tire queries matching electrical busbars. The regression set includes paraphrases and broad valid searches to check this precision/recall tradeoff. Recheck the cutoff when changing the model, text template or catalog. Validation cases used to diagnose a failure become regression cases after the fix; broader independent evaluation is still needed before claiming general search quality.

Bare model codes already present in product names (for example `HB-20-24`) are looked up directly and marked `model_match`. They are not mislabeled as article matches; real article matches take priority, explicit article requests still only use article fields, and multiple products with the same model code require clarification. Structured luminaire types also prevent abbreviated product names from being rejected by category filtering.

## Reproduce live acceptance

These commands call the configured OpenAI models and require a built catalog. They generate clearly synthetic requests under ignored `data/acceptance/`; selected product records remain real. Development dependencies are only needed for fixture generation.

```bash
python -m pip install -r requirements-dev.txt -c constraints.txt
python -m scripts.acceptance --text-only
python -m scripts.acceptance --files-only
python -m scripts.acceptance_specification
# Measure complete HTTP request/response latency with the application running:
python -m scripts.acceptance --text-only --http-url http://localhost:8000
python -m scripts.acceptance --files-only --http-url http://localhost:8000
python -m scripts.acceptance_regressions --http-url http://localhost:8000
```

The legacy DOC fixture derives from Apache POI's Apache-2.0 test document and substitutes a synthetic article/quantity request; its source is documented in the script. Results include model, snapshot, behavior checks and end-to-end `run_turn` timings. HTTP timing middleware separately measures complete API requests. See [implementation record and future same-origin integration](IMPLEMENTATION_PLAN.md) for architecture, contracts and delivery boundaries.
