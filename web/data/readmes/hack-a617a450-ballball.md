# hack-a617a450-ballball

## Live Demo

https://ekt-ai-assistant.vercel.app

HackAlem prototype: a **Next.js sales-assistant web application for ekt.kz**,
with a grounded OpenAI assistant, persistent catalog search, fresh EKT details,
comparison candidates, and a confirmation-only demo cart. No production checkout
or real EKT cart-write API is connected.

## Stack and setup

The initial repository contained this README only. The integration uses Node.js
24+, TypeScript, native `fetch` for EKT, the official `openai` SDK for the
Responses API, Next.js App Router with React, and Node's built-in test runner.

```sh
npm ci
cp .env.example .env.local  # Only if .env.local does not already exist
```

Set the following in `.env.local` locally, without committing or sharing values:

```dotenv
EKT_API_USERNAME=...
EKT_API_PASSWORD=...
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

`.env.local`, other environment files (except `.env.example`), and local API
response snapshots are Git-ignored. For production, inject these variables into
the server environment. Never use browser-public environment variable prefixes.

## Start the web demo

After setting the four variables above:

```sh
npm run catalog:refresh  # One-time preparation if .ekt-cache/catalog.json is absent
npm run dev
```

Open **http://localhost:3000**. Keep using the same hostname throughout the demo
so the browser session cookie is retained. The existing local cache can be reused;
there is no need to refresh it before every start. A full initial refresh can take
several minutes. Ordinary searches use the completed persistent index immediately.

```sh
npm test
npm run typecheck
npm run build
npm start               # Run the production build instead of the dev server
```

The Russian-first responsive UI includes chat, quick prompts, product cards,
images, real EKT links, characteristic/conflict warnings, and warehouse quantities
when freshly checked. Search snapshot prices are labeled as such; the API supplies
no currency, so the UI does not invent one. Current quantities are never inferred
from empty offers. The CLI (`npm run assistant:dev -- --trace`) remains available.

### Web architecture and demo limits

`Browser → /api/chat → per-session assistant → existing product tools → EKT API`.
`src/server/web` adds session orchestration, comparison candidates, configurable
policy placeholders, and the demo cart. The browser receives only product display
fields and conversation messages, never credentials, authorization headers, or
raw tool JSON. Cookies are HTTP-only and SameSite Strict. Mutation requests check
Origin against the request Host. Keep this demo local/trusted; public deployment
still needs authentication, rate limits, and shared session storage.

- Sessions and demo carts live in one Node process, expire after two hours, and
  reset on a server restart. They are separate for each browser cookie. The
  catalog cache persists independently across restarts.
- Alternatives first resolve up to four actual EKT recommendation IDs. These can
  be unrelated accessories, so references without at least two matching known
  technical fields are not presented as substitutes. If needed, a literal series
  token/name/brand search examines up to six actual detail records. Results show
  shared and differing values and require engineering compatibility verification.
  This is a bounded comparison feature, not an exhaustive compatibility engine.
- `src/server/web/policy.ts` is explicitly demo/configurable knowledge. Payment,
  delivery, and minimum order remain unconfirmed; no EKT policy is fabricated.
- `/cart` is **only a prototype cart**: it does not write to EKT, reserve inventory,
  place an order, collect card details, or process payment. Proposing an addition
  does not change it. Explicit “Да, добавь” or the confirmation button consumes a
  five-minute single-use proposal, fetches fresh EKT detail, and checks existing
  cart quantity plus requested quantity against the actual aggregate stock.
  Removal is explicit. Totals use prices checked at addition and have no invented
  currency. No checkout is offered.

### Judge demo sequence

1. Ask `Найди товар с артикулом 200300283`. The real stored article is
   `200300283_`; the assistant labels the underscore difference.
2. Ask `Проверь наличие и остатки по складам` and expand warehouse availability.
3. Ask `Покажи характеристики`.
4. Ask `Подбери аналог` and review shared/differing parameters and uncertainty.
5. Ask `Добавь 2 штуки товара с артикулом 200300283`. The cart must stay unchanged.
6. Say `Да, добавь`; open the supplied `/cart` link and inspect two units.
   Fresh stock may change: if fewer than two units remain, addition is rejected.
7. Ask `Есть сертификат на товар с артикулом 200300283?` — no certificate is invented.
8. Optional: `Покажи характеристики товара с артикулом 200300285_` demonstrates
   the real 160 A / 250 A source conflict. Ask about delivery to show policy limits.

## Usage (server only)

```ts
import { getProducts, getProductById } from "./src/server/ekt/client.ts";

const firstPage = await getProducts(1);
const secondPage = await getProducts(2);
const product = await getProductById(515291);

// firstPage.items: EktProductSummary[]
// product: EktProductDetail (bare object, no envelope)
```

The default first-page call uses `/api/products`; subsequent pages use
`/api/products?page=N`. Detail requests use `/api/products/detail?id=N`.
IDs and page numbers must be positive safe integers.

The client reads credentials from the server environment at request time and
sends HTTP Basic Authentication only to the fixed `https://ekt.kz` origin.
Redirects are refused, caching is disabled, and requests have a 15-second
timeout. Node built-ins and a browser runtime guard prevent ordinary browser use;
keep this module behind a server route/action when adding a framework. No
credentials or upstream error bodies are included in errors. There is no automatic
retry and no cart-writing method.

The inspection command loads `.env.local` using Node's environment-file support.
Other server entry points must load it themselves or receive environment variables
from the deployment environment; importing the client does not load files.

## Verification and API inspection

```sh
npm test
npm run typecheck
npm run ekt:inspect
```

The inspection command performs three real requests: catalog page 1, page 2,
and product `515291`. Successful responses are saved in `.ekt-inspection/`
with private file permissions. It prints only success/error summaries, never
credentials. A nonzero exit code means at least one probe failed.

## Verified API schema

Source of truth: the three authenticated responses saved locally by the user,
inspected on 2026-09-23. The API works from the user's local machine; earlier
request timeouts were a sandbox/network limitation, not evidence of an API outage
or bad credentials. Schema verification and tests here use these saved responses,
not new live requests. Reviewed copies are in `test/fixtures/`; production code
never imports them.

Types live in `src/server/ekt/types.ts`, and runtime validators in
`src/server/ekt/validation.ts`. Both client functions return validated, typed wire
responses without renaming fields, converting property values, or combining data.

### Catalog: `EktProductsResponse`

| Field | Observed type / meaning |
| --- | --- |
| `page` | Number; 1 and 2 in the supplied samples |
| `per_page` | Number; 20 in both samples |
| `count` | Number; 20 in both, matching `items.length` |
| `items` | Array of `EktProductSummary` |

All 40 products have these fields:

| Field | Type / meaning |
| --- | --- |
| `id` | Numeric product ID |
| `name` | Product name string |
| `article` | Article string; preserve leading zeros and trailing underscores |
| `price` | Numeric price; no currency metadata |
| `image` | Absolute image URL or `null` (one null image on page 1) |
| `url` | Absolute product-page URL |
| `url_api_detail` | Absolute API detail URL |
| `offers` | Array; empty for every sampled product; element schema unknown |

Pages contain 40 distinct IDs. Product `515291` is the first item of page 2.
There are no `total`, `total_pages`, `next`, or `has_more` fields. The observed
`count` is treated as the returned item count, not the catalog total. The validator
checks it against `items.length` and `per_page`. An empty page ends the catalog scan. The live API also wraps back to first-page
items after a short final page; that verified boundary pattern ends the scan too.
Short pages alone are followed by another request. Maximum page size and search/filter
parameters have not been established. Do not hardcode 20 as a universal
page size or assume these 40 products are the entire catalog.

### Detail: `EktProductDetail`

The response is a **bare product object**, not `{item: ...}` or `{data: ...}`.
It includes `id`, `name`, `article`, `price`, `image`, `url`, and `offers` from the
summary shape, plus:

| Field | Type / meaning |
| --- | --- |
| `description` | String, with CRLF line breaks and tabs in the sample |
| `quantity` | Numeric aggregate stock quantity |
| `stores` | Array of `{id: number, name: string, quantity: number}` |
| `properties` | Property-code map; values are strings or string arrays |

`url_api_detail` is absent from detail. Detail image is a URL in this sample;
the shared type also permits the null image observed in catalog data. Prices and
quantities remain finite nonnegative numbers (no coercion or rounding); IDs and
pagination metadata are safe integers. Numeric strings are rejected in those
fields, but intentionally preserved in `properties`.

All 19 observed property codes are listed below. They are optional per product,
not universal requirements. Additional property codes are accepted with the
observed string/string-array value formats.

| Property | Sample / interpretation |
| --- | --- |
| `BRAND_PRIORITY` | `"1"`; raw priority value |
| `CML2_ARTICLE` | `"200300285_"`; matches article |
| `NOVINKA` | `"Да"`; raw new-item flag |
| `SPETSPREDLOZHENIE` | `"Нет"`; raw special-offer flag |
| `RECOMMEND` | `["48783", "23466", "28727"]`; recommendation references, semantics unverified |
| `CML2_BAR_CODE` | `"3414970344526"`; barcode string |
| `CML2_TRAITS` | String array; includes text, flags, `"0,00212"`, `"1,467"`, and zeros; positional meanings unverified |
| `CML2_TAXES` | `"16"`; tax-related raw value, not proof of price tax inclusion |
| `KRATNOST_MIN` | `"1"`; apparent order-multiple/minimum metadata, exact rule unverified |
| `IMYAKARTINKI` | `"Legrand.jpg"`; filename, not a full image URL |
| `ARTIKULPOSTAVSHCHIKA` | `"027228"`; supplier article |
| `OBYEM` | `"Автоматический выключатель"`; product-type text despite the property code |
| `KOLICHESTVO_POLYUSOV` | `"3"`; poles |
| `NOMINALNAYA_OTKLYUCHAYUSHCHAYA_SPOSOBNOST` | `"18кА"`; breaking capacity |
| `NOMINALNOE_NAPRYAZHENIE` | `"400В"`; nominal voltage |
| `NOMINALNYY_TOK` | `"250 А"`; nominal current, conflicting with name/description |
| `TIP_USTANOVKI` | `"Винтовое"`; installation type |
| `TORGOVAYA_MARKA` | `"Legrand"`; brand |

### Example and limitations for the future assistant

Historical sample product **515291** is
`027228 АВ DRX250 MT 3ф 160А 18ka Legrand (1)`, article `200300285_`,
supplier article `027228`, price **64920** (currency not supplied), quantity **23**.
Its 24 warehouse quantities sum to 23. Nonzero stock appears at:
Шымкент (ул.Байдукова) 2, Алматы 5, Тараз 2, Атырау 3, Караганда 2,
Нур-Султан 8, and Шымкент (Тассай) 1. These are snapshot values, not current stock.

- **Specifications conflict:** name and description say 160 A, while
  `NOMINALNYY_TOK` says `250 А`. Preserve provenance and surface the discrepancy;
  do not silently choose a value or recommend an electrical substitute based on it.
- **Catalog is insufficient for availability:** all catalog `offers` arrays are
  empty, including product 515291 with positive detail stock. Empty offers do not
  mean out of stock. Fetch detail for quantities and technical properties.
- **Offers remain `unknown[]`:** no offer fields can be verified from empty arrays.
  Nonempty arrays are preserved but must not be used for stock/pricing decisions
  until their schema is inspected.
- **Stock is not a reservation:** warehouse names include internal locations such
  as defect, marketing, and samples locations. No sellability, reservation,
  delivery eligibility, stock timestamp, or quantity unit fields are supplied.
  Do not assume every warehouse is eligible for sale, or overwrite aggregate stock
  with a computed sum. Recheck authorized available inventory before any future
  confirmed cart operation.
- **No certificate fields, files, or links appear in these samples.** This does
  not establish that certificates never exist for other products.
- **No explicit category IDs/names/hierarchy appear.** Product URLs contain category
  path segments, but these are not authoritative category metadata. `OBYEM` is
  product-type text, not a verified category field.
- **No currency, price-unit, discount breakdown, or tax-inclusion field is present.**
  Do not infer currency from the domain or reinterpret `CML2_TAXES` as a full policy.
- **Catalog/detail images differ for 515291.** Preserve the returned URLs; no
  gallery or authoritative-image precedence is specified.
- **Recommendations are not verified alternatives.** `RECOMMEND` contains string
  references only; no compatibility explanation or substitution guarantee exists.
- Purchasing conditions, shipping/payment/returns policies, and cart endpoints or
  cart links are not supplied by these responses. Separate authoritative sources
  and an authorized cart API will be needed later.
- The original schema fixtures cover two catalog pages and one detail. The later
  live catalog scan validates additional summary pages against that schema. Other
  detail property shapes, nullability, missing-product payloads, and rate limits
  still require more real samples. Unsupported shapes fail closed
  instead of producing guessed product facts.

## Error handling

`EktApiError` has a typed `code`, a safe `message`, and an optional HTTP `status`:

| Code | Meaning |
| --- | --- |
| `CONFIGURATION` | Missing credentials or a colon in the Basic Auth username |
| `INVALID_ARGUMENT` | Invalid page number or product ID |
| `AUTHENTICATION` | HTTP 401 or 403 |
| `NOT_FOUND` | HTTP 404 |
| `NETWORK` | Connection, timeout, redirect, or body-read failure |
| `MALFORMED_RESPONSE` | Invalid JSON, wrong field/nested types, inconsistent pagination, or wrong requested page/product ID |
| `API_ERROR` | A successful-HTTP object with an unrecognized `error` field; upstream text is not exposed |
| `HTTP` | Other unsuccessful status, including 429 and 5xx |

The previously observed `{"error":"Unauthorized"}` envelope is also recognized
if delivered with HTTP 200. HTTP status errors take precedence over body parsing.
No actual missing-product response has been supplied: HTTP 404 maps to `NOT_FOUND`,
but an empty object, null, or an unrecognized error payload is not guessed to mean
“product missing.” Errors never include raw response bodies or property values.
Known fields are validated; additional fields are preserved without interpreting
them. Property-code validation does not resolve contradictory business data.

## Stage 2: product retrieval and search

The server-side flow is:

```text
Future tools → products/index.ts → EKT client → HTTPS API
                    ↓                 ↓
              normalize + rank   wire-schema validation
```

`src/server/products/types.ts` defines the domain contracts; `normalize.ts`
preserves source facts and identifies the observed current conflict; `rank.ts`
implements deterministic text matching; `catalog.ts` handles shared incremental catalog loading and in-memory product/article
indexes; `index.ts` handles retrieval and optional detail enrichment. The existing EKT client is
the only component making authenticated network requests. No fixtures are imported
by production code.

```ts
import {
  searchProducts,
  findProductByArticle,
  getNormalizedProductById,
  createProductRetrieval,
} from "./src/server/products/index.ts";

const search = await searchProducts("DRX250 160А");
// {query, matches: [{product, score, matchedBy}], coverage}
const exact = await findProductByArticle("200300285_");
// Same result envelope. Stops at an exact article match and returns all matches
// loaded so far. May return labeled trailing-underscore candidates after a complete
// scan with no exact match. Inspect matchedBy and coverage.
const product = await getNormalizedProductById(515291);
// Product; always fetches fresh detail and does not scan the catalog.

const catalogOnly = createProductRetrieval({
  maxPages: 5,
  maxDetailRequests: 0,
  cacheTtlMs: 60_000,
});
```

### Normalized Product

| Fields | Source / missing-value handling |
| --- | --- |
| `id`, `article`, `name`, `price`, `image`, `productUrl` | Direct wire values; no currency invented |
| `description` | Detail text, otherwise `null` |
| `totalQuantity`, `warehouses` | Only detail `quantity` and `stores`; otherwise `null` |
| `stockStatus` | `positive`/`zero` from aggregate quantity, or `unknown`; not sellability |
| `brand`, `supplierArticle`, `barcode` | `TORGOVAYA_MARKA`, `ARTIKULPOSTAVSHCHIKA`, `CML2_BAR_CODE`; otherwise `null` |
| `technicalCharacteristics` | `{code, value, source, conflictDetected}` for the five observed engineering property codes |
| `recommendationReferences` | Copy of `RECOMMEND`, otherwise `[]`; not validated alternatives |
| `properties` | All original property values, including flags, tax-related metadata, traits, product-type text, and order-multiple metadata |
| `conflicts` | Source-tagged conflict evidence; currently a conservative nominal-current detector |
| `detailLoaded` | Distinguishes catalog-only records from inspected detail |
| `raw.catalog`, `raw.detail` | Separate unmodified source snapshots when available, otherwise `null` |

Engineering codes retained in `technicalCharacteristics` are
`KOLICHESTVO_POLYUSOV`, `NOMINALNAYA_OTKLYUCHAYUSHCHAYA_SPOSOBNOST`,
`NOMINALNOE_NAPRYAZHENIE`, `NOMINALNYY_TOK`, and `TIP_USTANOVKI`.
Their values remain strings with original units. This code-based representation
can support future comparison rules without pretending that free text has already
been converted into verified engineering quantities.

Detail values populate common fields when detail is loaded; any catalog snapshot
is also retained separately (including the different image for 515291). No stock
is inferred from offers, warehouse names, or sums. Empty warehouse lists and zero
quantities stay distinct from unknown (`null`). Missing properties are not filled
from names or descriptions. Empty characteristic/reference collections indicate
no supplied values, not proof that such values never exist.

### Conflicting characteristics

For 515291, `conflicts` contains `field: "NOMINALNYY_TOK"` with evidence:

- `properties.NOMINALNYY_TOK`: raw `250 А`, comparison value `250 A`.
- `name`: original full name containing `160А`, comparison value `160 A`.
- `description`: original nominal-current line containing `160А`, comparison value `160 A`.

The corresponding technical characteristic is flagged `conflictDetected: true`.
There is no resolved or authoritative amperage field. Comparison values are used
only to detect differences; raw strings remain available. The detector compares
plain A/А values in the property, title, and explicit Russian nominal-current
description lines. It excludes kA/mA and is deliberately limited: absence of a
flag does not certify consistency, and other unit systems/languages or conflicting
characteristics need additional rules. Future alternative selection must inspect
conflict evidence and obtain authoritative clarification before claiming electrical
compatibility.

### Search ranking and coverage

Search uses Unicode NFKC normalization, case folding, and collapsed whitespace.
Article punctuation, underscores, and leading zeros are preserved. There is no
LLM, fuzzy matching, transliteration, stemming, or cross-script unit normalization.
Scores are fixed priorities, not confidence values:

| Score | Strongest matching rule |
| --- | --- |
| 700 | Exact article, supplier article, or `CML2_ARTICLE` |
| 600 | Partial substring in one of those article fields |
| 500 | Exact product name |
| 400 | Name contains the query phrase |
| 300 | Name contains every whitespace-delimited query token, in any order |
| 200 | Brand contains query |
| 100 | All query tokens occur across name, description, or textual property values |

Results sort by descending score then ascending numeric product ID. Ranking is
deterministic for the same query and available product data. `matchedBy` explains
the strongest rule. Duplicate articles already loaded return multiple results, never an arbitrary
single product. Early article lookup does not guarantee that all duplicates on
later pages have been discovered. Blank queries, queries over 500 characters, and invalid IDs fail
before network access. No matches returns an empty list **with coverage**.

Explicit catalog refresh loads **all available pages**. Normal production discovery
uses the persisted completed snapshot instead of scanning pages in the request path.
The lower-level in-memory loader (used by injected test sources or `cachePath: false`)
can still load all pages on demand. There is no
hardcoded page count. The actual EKT pagination envelope contains `page`,
`per_page`, `count`, and `items`, with no total/last-page/next pointer. The loader
requests successive pages and validates their metadata. It stops on an empty page
(`count: 0`, `items: []`) or the **observed EKT boundary pattern**: a short page,
then an exact repeat of the first page's ordered product IDs. It does not treat an
arbitrary short/repeated page as complete. `catalogPages` includes the terminal
probe. Unexpected repeated nonempty pages fail closed instead of looping.

Live inspection on 2026-09-23 traversed **15,037 unique products on 752 populated
pages**. Page 752 had 17 items (`per_page: 20`); page 753 echoed `page: 753` but
returned the first page's 20 products. The termination reason is therefore
`short-page-wrap`, not `empty-page`. The two real boundary response fixtures are
saved in `test/fixtures/end-page-752.json` and `end-page-753.json`; their page
numbers/counts are evidence, never hardcoded loader limits. The catalog can grow.
Final live verification of `findProductByArticle("200300283")` returned product
`515289`, stored article `200300283_`, with `matchedBy: "article-variant"`,
`catalogComplete: true`, and 753 requested pages. A second lookup reported
`catalogSource: "cached"` and made **zero additional catalog requests**. This was
a discovery-only verification (`maxDetailRequests: 0`), not a stock check.
If a future catalog ends on a full page and wraps without a preceding short page,
the loader currently fails safely as incomplete rather than treating an
indistinguishable broken/repeated page as proof of completion.

The architecture is `EKT pages → shared catalog loader → atomic persistent snapshot
→ normalized in-memory product/article indexes → retrieval functions → AI tools`.
The lower-level loader behavior is:

- `findProductByArticle` checks the article index, then loads additional pages
  until an exact match or the end. Exact lookups ignore the optional general-search
  `maxPages` cap. An early match leaves a resumable partial index.
- `searchProducts` continues that same index to the end by default, then runs the
  existing deterministic ranking. `maxPages` is now an explicit opt-in cap for
  special callers only; reaching it is always reported as incomplete.
- One in-flight next-page request is shared by all callers. Concurrent full scans
  and article lookups neither fetch duplicate pages nor start separate full loads.
- Successful pages are committed together. On a later failure, `CatalogLoadError`
  carries safe error/coverage metadata; successful pages remain cached and the next
  call retries the failed page. Failure is never an empty, complete search result.
- Production discovery loads a persistent snapshot and marks it stale after 24
  hours; stale data remains searchable during background refresh. It does not
  discard the index on expiry. See the persistent-cache policy below.
- Production discovery makes zero detail requests by default. Details are fetched
  explicitly for current facts. Optional `maxDetailRequests` enrichment remains
  available; injected nonpersistent test sources retain their previous defaults.
  Detail-only brand, supplier article, barcode, and property searches therefore
  have separate, explicitly incomplete coverage.
- Search metadata, prices, and detail snapshots are cached for discovery only.
  `getNormalizedProductById` always calls EKT for fresh detail, and the assistant
  still requires fresh current-turn detail evidence before displaying stock.

Coverage includes `catalogPages`, `catalogProducts`, `catalogTermination`,
`catalogComplete`, `catalogSource` (`network`, `cached`, or `mixed`), `pagesFetched`,
`nextPage`, `catalogFetchedAt`, `detailedProducts`, and
`allScannedProductsDetailed`. `pagesFetched` counts page advancement observed during
the request, including shared work. `catalogComplete` means the catalog summaries
were scanned to a supported API boundary, not that every detail field was inspected or
that the upstream catalog was an atomic snapshot. Cached no-results retain this
provenance. The AI receives coverage on success and partial pagination failures.

The live lookup issue also exposed an article-format distinction: the API stores
`200300283_`, not `200300283`. Literal article matching retains punctuation. If a
**complete scan** finds no exact match for a numeric query, lookup may return
products whose actual article is that number followed by one underscore. These
are explicitly labeled `matchedBy: "article-variant"` (score 650), not exact
matches. The original article is preserved and the assistant displays a candidate
warning. No arbitrary punctuation removal, leading-zero stripping, or inferred
article replacement occurs. An exact match on a later page wins over an earlier
underscore candidate.

**Limitations:** building a full index takes many API requests, but ordinary
searches no longer await that work. A completely new install needs an initial
refresh; until it finishes, discovery reports that the catalog is warming.
The persistent path must be private and isolated per deployment/account context.
Do not share one cache path between unrelated EKT accounts. In-memory-only
adapters retain resumable scan behavior for lower-level callers.
Product detail-only searches are incomplete unless `allScannedProductsDetailed`
is true. Catalog modifications during a sequential scan can create gaps; the API
provides no snapshot/version token. Fresh stock is neither a reservation nor
confirmation of sellability. No public routes or new customer features are added.

Tests use the three original response fixtures plus the two live pagination-boundary
fixtures, with explicitly synthetic variations
for missing fields, duplicate articles, pagination termination, and ranking cases.
Run `npm test` and `npm run typecheck`. Tests never require credentials or network.

### Persistent cache and measured latency

A live three-page diagnostic measured **230 ms, 176 ms, and 158 ms** per page
(**570 ms total**). The old exact lookup continued past a matching underscore
candidate on page 1 because variant fallback required scanning to completion.
A 753-request sequential scan therefore explained substantial retrieval latency;
OpenAI latency is separate and is now traced rather than folded into that wait.

`src/server/products/persistent.ts` stores `.ekt-cache/catalog.json`, ignored by
Git. It persists only a versioned, completed discovery snapshot with its timestamp,
page count, terminal condition, and allowlisted product IDs, articles, names,
image/product/detail URLs, and historical catalog prices. Credentials, headers,
stock quantities, warehouses, arbitrary extra API fields, and offer contents are
never serialized. On restore, discarded offers are represented by an empty opaque
array; this is not evidence that a product has no offers or stock. Detail data and
technical enrichment remain memory-only.

Writes use private directory/file permissions, a unique temporary file, file sync,
and atomic rename. A failed refresh cannot replace the last good snapshot.
Same-process callers share the refresh promise; a PID lock prevents other live
processes from launching duplicate builds. Locks belonging to exited processes
can be reclaimed. The cache file is validated on startup; corrupt, incompatible,
or invalid snapshots are treated as missing, not trusted product data.

Freshness policy:

- Startup loads and validates the local snapshot immediately, rebuilding the
  in-memory product/article indexes without contacting EKT. `initializeCatalog()`
  lets the terminal finish this before its first prompt.
- Discovery freshness defaults to **24 hours** (`cacheTtlMs` is configurable).
  After that, the last good snapshot remains usable while a new snapshot is built
  separately and swapped in only on success. This is stale-while-refresh behavior,
  not permission to treat old prices/stock as current.
- No snapshot: search returns `CATALOG_NOT_READY` promptly and starts a shared
  background build; the assistant explains that the catalog is warming. Operators
  can prebuild the cache before starting chat with `npm run catalog:refresh`.
- Explicit refresh always requests a new full catalog without blocking existing
  readers. Refresh errors retain the old cache, are reported in coverage, and
  automatic retries back off for 60 seconds. Other-process cache replacements are
  detected on stale/missing-cache checks (at most once every five seconds).
- Coverage adds `cacheLayer` (`memory`, `persistent`, or `network`),
  `catalogStale`, `refreshing`, and `refreshError`. Complete stale snapshots remain
  complete historical discovery snapshots, not statements about current EKT data.
- Stock/warehouses are never restored from disk. `getNormalizedProductById()`
  always retrieves fresh EKT detail. Current-price questions also require fresh
  detail; cached prices are labeled as catalog snapshots, not current quotes.

Build or refresh explicitly:

```sh
npm run catalog:refresh
npm run assistant:dev -- --trace
```

The refresh command prints total duration and final coverage and makes no OpenAI
requests. `--trace` prints catalog startup time, every OpenAI request duration,
catalog-search duration, detail-request duration, and cache provenance. It never
prints configuration, credentials, headers, or raw SDK errors. OpenAI generation
and fresh detail network time remain part of end-to-end conversational latency;
local lookup benchmarks must not be described as full chat response time.

Live verification on 2026-09-23: building the 15,037-product cache took **477.1 s**
(753 requests including the wraparound probe). In a separate process with all
network requests explicitly blocked, module startup plus persistent-index loading
took **159.55 ms**. `findProductByArticle("200300283")` took **0.56 ms** on its
first call and **0.16 ms median** over ten calls; it returned product `515289`,
actual article `200300283_`, as a labeled variant. General `Legrand` search took
**38 ms** and returned 668 matches. There were **zero network requests**. A terminal
startup/exit smoke check reported a 95 ms index load (excluding prior module setup).
These are local measured discovery timings, not full OpenAI response timings.

Tests cover restart restoration, stale reads during blocked refresh, shared
refreshes, private allowlisted persistence, failed-refresh preservation, corrupt
cache recovery, cache-based article lookup, and fresh stock requests.

## Stage 3: backend conversational assistant

The model interprets Russian, Kazakh, and English customer messages and chooses
read-only retrieval tools. It is not the product database. Server modules are in
`src/server/assistant/`:

| Module | Responsibility |
| --- | --- |
| `openai.ts` | Official SDK adapter, server environment configuration, sanitized failures |
| `protocol.ts` | Instructions, strict function schemas, constrained final answer-plan schema |
| `index.ts` | Per-conversation tool loop, evidence validation, bounded history, tool tracing |
| `render.ts` | Russian/Kazakh/English response templates populated from retrieved facts |
| `security.ts` | Configuration/authorization redaction, control-character removal, card-number screening |
| `contracts.ts` | Dependency interfaces, safe errors, future trusted purchasing-policy adapter |

### Responses API and tools

Only server code reads `OPENAI_API_KEY` and `OPENAI_MODEL`. Both are required;
there is no hardcoded model or fallback. Keep actual values only in `.env.local`
or the deployment's server environment. The SDK calls the fixed official API
origin, disables SDK logging and automatic retries, sets a 45-second request
timeout, uses `store: false`, and caps generated tokens at 2000 per model call.
The loop follows the official
[Responses function-calling workflow](https://developers.openai.com/api/docs/guides/function-calling).

| Model tool | Existing trusted function |
| --- | --- |
| `search_products({query})` | `searchProducts(query)` |
| `find_product_by_article({article})` | `findProductByArticle(article)` |
| `get_product_details({id})` | `getNormalizedProductById(id)` |

Function schemas are strict, and the server independently checks tool names,
argument keys, types, and limits before dispatch. The AI layer contains no new
catalog search/ranking implementation. Search outputs include at most five matches,
truncation and coverage metadata. Raw duplicate snapshots are omitted from model
tool views; normalized properties and conflict evidence are included.

Function calls and reasoning items are carried forward with matching
`function_call_output` records. Opaque encrypted reasoning is passed back unchanged
within the turn, never logged or saved to conversation history. Tool errors are
safe codes, not upstream messages or empty search results. Limits are six model
calls and eight product-tool calls per turn. Oversized tool/context payloads,
incomplete model responses, repeated call IDs, and invalid output fail closed.
An explicit/background full catalog refresh can be slow; ordinary discovery does not wait for it; there is no overall
retrieval cancellation or interactive streaming yet.

### Grounded answer generation

The final model output is a strict **answer plan**, not customer-facing prose:
language, intent, product IDs, supported field selections, notices, and an optional
purchasing-policy topic. No model-generated price, quantity, specification,
article, certificate, or URL field is accepted. Unknown fields and free prose
are rejected. Every selected product ID must be present in successful tool output
from the current turn. The server renders facts from that evidence only.

- Price, article, URL and specifications are copied from trusted retrieval data.
  Cached prices are labeled historical; current quotes require fresh detail.
  Currency is explicitly unspecified. Missing supported fields render as unknown.
- Stock and warehouse values are displayed only after a fresh detail call in the
  current turn. Cached search quantities are not displayed as current stock.
  Reported inventory is not described as a reservation or confirmed sellability.
- Conflict evidence is always displayed for selected products, even if the
  model does not ask to show specifications. The 160 A / 250 A conflict stays
  unresolved and prompts verification with EKT.
- Tool data is treated as untrusted content, not instructions. The renderer does
  not show model prose, so a fabricated factual sentence cannot pass through as
  an answer. Original catalog names/descriptions remain source text, not independently
  verified engineering advice.
- No-result answers are scoped to the searched catalog portion. Tool failures
  are shown as retrieval failures, never interpreted as zero stock or no products.
- Certificates and purchasing conditions default to unavailable. `KRATNOST_MIN`
  is not interpreted as an authoritative ordering policy.
- A server-injected `PurchasingPolicySource.lookup(topic, language)` can later
  supply trusted policy text with an HTTPS source URL. No source is configured now;
  there is no model-generated or web-search fallback.
- Cart requests get a fixed “nothing added” response. Alternative-search responses
  disclaim unverified compatibility. The core CLI has no cart/payment tool; the
  web layer separately implements the confirmation-only demo cart and bounded comparisons.

The plan still relies on model interpretation for intent, language, relevant
product selection, field selection, and ambiguity handling. This is not a proof
of semantic correctness: it prevents model-authored catalog facts, but the model
can still select irrelevant retrieved products or omit part of a question.
Runtime evidence checks and source limitations must remain in later stages.
Answer wording is deliberately templated; source product text is not translated,
and unsupported factual topics get an unavailable notice instead of general
model knowledge.

### Conversation state and security

```ts
import { createAssistant } from "./src/server/assistant/index.ts";

const chat = createAssistant(); // One instance for one customer conversation
const first = await chat.send("Найди товар с артикулом 200300285_");
const followup = await chat.send("А сколько их осталось?");
chat.reset();
```

Each instance keeps at most ten successful user/assistant exchanges in memory.
History contains redacted user text and the rendered answer, including presented
product IDs, so the model can resolve follow-ups. History is discarded on the
next send after 30 minutes of inactivity, or on reset; it is not persisted.
Prior facts are context, not current evidence: follow-ups need new tool results.
Failed turns do not enter history. Concurrent sends/reset on the same active
instance are rejected to avoid mixing conversations. Future HTTP integration must
bind instances to authenticated users and implement session lifecycle/eviction;
no public endpoints or shared global conversation registry exist now.

SDK errors are replaced with safe `AssistantError` codes. Traces contain only
validated tool arguments and sanitized product results, never SDK request objects,
configuration, headers, or raw errors. Known configuration values and authorization
tokens are redacted before tracing, rendering, or saving chat text. No transcript
files are written. Do not enable external HTTP/SDK request logging that captures
authorization headers. The assistant never requests payment-card data; likely
Luhn-valid card numbers are rejected before model calls/history. This heuristic
is not a general payment-data detector and can reject some numeric identifiers.

### Manual terminal testing

After `npm ci`, configure the four variables in `.env.local` using the empty
`.env.example` template without overwriting an existing file. Run:

```sh
npm run assistant:dev
```

For sanitized tool arguments/results during development:

```sh
npm run assistant:dev -- --trace
```

Commands: `/reset`, `/trace on`, `/trace off`, `/exit`. Do not enter credentials or
card data into the terminal. Readline history is disabled. Terminal chat uses real
OpenAI credits and real EKT calls; tracing does not switch to fixtures. On model,
network, or grounding errors it prints a safe error and allows another turn.

Automated tests inject scripted Responses outputs and fixture-backed product
tools. The SDK adapter test intercepts HTTP locally. `npm test` never loads
`.env.local`, makes a real OpenAI call, or consumes credits. All prior tests remain.
The Stage 3 implementation was verified with mocked tests, type checking, and a
terminal startup/exit smoke check; no live conversational quality evaluation was
run. Test multilingual tool planning against the real configured model manually
before relying on it in a customer-facing workflow.

## Business constraints for later work

Prices, inventory, specifications, and certificates must come from EKT responses.
Never invent these values. Cart changes require explicit customer confirmation
and must not exceed available inventory; return a cart link after an authorized
addition. Never request or store payment-card information.
