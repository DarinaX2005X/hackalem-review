# SOLAI Inventory Intelligence

A HackAlem procurement decision workspace built on the existing monthly SKU forecasting and replenishment engine. Managers can inspect anomaly, stockout, seasonal and growth adjustments, review urgency, edit quantities and approve decisions. **Approval is a local demo decision: no supplier order is sent.**

## Business problem and solution

Procurement teams must distinguish regular demand from one-off purchases, censored sales during stockouts, seasonality and sustained growth. Sales totals alone cannot answer how much stock to order, which products need attention first, or which missing inputs make a decision unreliable.

SOLAI combines partner-provided sales and inventory evidence with explainable forecasts, safety stock, supplier constraints and an explicit manager review workflow. The light interface uses an ivory background, restrained olive accents and readable status treatments. It does not replace the calculations with a visual mockup or an AI prediction service.

## Workspace

- **Overview:** KPIs for the full filtered selection, a transparent priority queue, data-quality counts, urgency distribution and lead-time coverage.
- **Forecast:** observed demand, detected spikes, reconstructed demand, baseline/forecast levels and retained monthly/document audits.
- **Replenishment:** a compact decision table, order quantities, selected-SKU details, structured explanations and source-versus-derived provenance.
- **Warehouse:** calculated inventory/target comparison. No 3D component was present at implementation; no layout or storage coordinates are fabricated. `dashboard_views.warehouse(..., renderer=...)` accepts a teammate renderer with `recommendations` and `selected_sku`; `warehouse_selected_sku` also exposes the shared selection in session state.
- **AI Copilot:** on-demand, evidence-grounded decision briefs and SKU analyses. Its exact behavior is documented below.
- **Approvals:** read-only calculated quantities, separate manager edits, explicit approval, session decision history, supplier proposals and CSV export.

Supplier, literal SKU/product search, urgency and status filters apply **before** 25-SKU pagination. KPIs, brief, supplier totals and complete export cover all filtered results. Only the visible page feeds detailed comparison tables/charts. The selected SKU is shared across tabs. Empty filters show an explicit empty state. Missing table values display as **—**; text uses **Not available** (EN) or **Нет данных** (RU). Values remain null in the underlying data and exports; known zero remains zero.

EN/RU language switching is available in the header (KZ is also retained). Core forecast explanations accept the selected language; some technical audit text remains English. The engine refreshes legacy one-argument forecast explainers in running Streamlit sessions.

### Warehouse / 3D status

The current working tree contains a real-data inventory comparison and a renderer integration boundary, **not an installed 3D SKU visualization**. No 3D implementation was found during the current fix. An existing teammate component can use the renderer contract described above; this repository must not be presented as already rendering a 3D warehouse.

## Installation, run and tests

Requires Python 3.10 or newer. Run these commands from the repository root:

```bash
python -m venv .venv
```

Activate in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Exact application command:

```bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

Exact command for the complete test suite:

```bash
python -m unittest discover -s tests -v
```

Tests use Python unittest and Streamlit AppTest; pytest is not required. They cover forecasting, stockouts, growth, anomalies, replenishment, urgency, supplier totals, schema recovery and manager editing/approval across reruns.

## Architecture

| File | Responsibility |
| --- | --- |
| `app.py` | Existing application entry point, filters, shared selection, six-tab workspace and manager state orchestration |
| `src/dashboard_data.py` | Cached calls to the existing partner/sample forecast and replenishment engines |
| `src/dashboard_views.py` | Overview, forecast, decision detail, warehouse integration boundary, Copilot and approval views |
| `src/presentation.py`, `.streamlit/config.toml` | Light design system, localized display helpers and missing-value formatting |
| `src/decision_intelligence.py` | Pure, read-only portfolio facts, data quality, signals, priority ordering and SKU analysis |
| `src/copilot.py` | Localized evidence briefs and optional constrained provider adapter |
| `src/data_loader.py` | Synthetic CSV loading and basic validation |
| `src/partner_loader.py` | Validated Excel adapters, 1C joins, document anomaly audit and inventory evidence |
| `src/partner_pipeline.py` | Observed complete-month histories and explicit manager planning assumptions |
| `src/anomaly_detection.py` | Per-SKU spike flags, thresholds and audit reasons |
| `src/demand_adjustments.py` | Stockout metadata, lost-demand estimation and sustainable growth |
| `src/forecasting.py` | Recent baseline, SKU/category seasonality, final forecast and forecast explanations |
| `src/replenishment.py` | Safety stock, calculated quantities, urgency and supplier grouping |
| `src/manager_review.py` | Separate manager quantities, approval timestamps and in-memory decision history |
| `src/explanations.py` | Human-readable replenishment and urgency explanations |
| `src/engine.py` | Refresh legacy imported modules after result-schema changes |
| `data/sample_data.csv` | Synthetic monthly history and inventory inputs |
| `tests/` | Automated calculation and UI regression tests |

## Input data

The primary source is **12 partner-provided Excel workbooks in `data/raw/`**, covering IEK (3,184 valid distinct 1C codes) and Systeme Electric (724). All 14 sheets were inspected. One empty IEK transit placeholder with code `0` is excluded from the product catalog; earlier inspection counts included it. See [the workbook inspection and mapping report](docs/partner_data_inspection.md) for workbook structure and joins. Keep supplied workbooks private; do not publish raw partner records or credentials.

The loader preserves 1C codes as strings, including leading zeroes and trailing underscores. Monthly sales/inventory `Номенклатура.Код`, document `Код`, and transit/MOQ `Код 1с` (or `Номенклатура.Код`) join on the same real SKU. Articles/names are metadata, not fuzzy join keys. Brands supply the supplier grouping; they are not confirmed legal supplier entities. No customer identifiers are supplied.

### Missing-data policy

Blank source cells remain unknown, never zero. Missing/placeholder identifiers do not become SKU `0`; integral numeric Excel codes normalize to strings while text codes retain leading zeroes. A supplied name in another report can fill a blank catalog name for the same exact code. Missing product names remain unavailable. No name or stock quantity is invented. Category blanks remain null rather than the literal string `None`.

Forecast charts use the selected string SKU and sorted valid dated observations. Products with no usable history display an EN/RU insufficient-history message rather than an empty chart. Missing supplier lead times, purchase prices, stock or transit still require review; a planning lead time is an explicit manager assumption. The synthetic CSV remains a fallback/demo source.

Monthly reports cover January 2024 through September 2026. September is partial at the dated 22 September 2026 snapshot: it is retained for audit and excluded from fitting. Forecast origin is September 2026, not the computer's current date. Blank monthly cells remain unknown. Complete observed signed outbound document totals can fill a blank sales month; a month with missing document quantities remains incomplete; missing documents never imply zero sales. Negative net return months remain auditable but are excluded from demand fitting. Monthly and document sales are reconciled, never added together.

Current stock is the latest monthly inventory cell; for 497 Systeme Electric products, the dated `Свободный остаток` snapshot overrides it. Known shipment quantities are summed for transit. An all-blank transit entry stays unknown. No historical inventory blank is converted into zero. Warehouse-level documents and available stock components remain in normalized audit data, but inventory scope cannot consistently be allocated to the document warehouse, so recommendations filter by brand rather than claiming warehouse-specific coverage.

**Lead times and confirmed supplier purchase prices are absent.** Enter an explicit **Planning lead time (days)** in the sidebar to calculate provisional recommendations where stock/transit/history are known. Leaving it blank leaves order quantities unknown and marked REVIEW. Prices remain unavailable; `СС реал` is preserved as reported cost and is not used as a supplier quote. IEK category is absent; Systeme Electric category codes are preserved where supplied.

Choose **Synthetic demo** in the sidebar to use `data/sample_data.csv`. It remains a fallback when no partner workbooks exist and a test fixture; malformed/incomplete partner files surface a load error instead of silently switching data. The synthetic dataset has 144 observations, 8 SKUs, 4 categories and 18 months (January 2025 through June 2026). Columns are:

`date`, `sku`, `product_name`, `category`, `supplier`, `sales`, `current_stock`, `in_transit`, `lead_time_days`, `unit_price`, and optional `stockout_days`.

There must be one finite, nonnegative sales observation per SKU/calendar month. Inventory, lead time, supplier and price use the latest SKU snapshot. `stockout_days` records unavailable days during that historical month. Absent stockout metadata is unknown; low sales and current inventory do not independently establish a historical stockout. The synthetic dataset has no customer identities or transaction identifiers.

The sample includes three annotated outages and six growing months for cold brew coffee. Its history is too short for learned seasonality, so seasonal factors are 1.0. At default settings, inventory covers calculated targets and all calculated orders are zero. Tests include positive shortages and multi-year seasonality. Managers may enter a positive demo quantity without changing the sample or calculation.

## Forecasting methodology

Each SKU is sorted chronologically and processed independently. The raw estimate is the mean of recent sales. The baseline is the median of non-anomalous, stockout-adjusted demand in the latest six calendar months. If none is usable, up to six older usable observations supply the fallback. Missing months are not assumed to have zero demand.

```text
final_forecast = stockout_adjusted_baseline * seasonal_factor * growth_factor
```

The UI exposes the raw-sales baseline, robust/spike adjustment, stockout adjustment, seasonal adjustment, growth adjustment and final forecast. The robust/spike adjustment includes the switch from mean to median, not only removal of flagged spikes.

### Anomaly/outlier detection and exclusion

From non-stockout observations, calculate median sales and MAD (median absolute deviation). Robust standard deviation is `1.4826 * MAD`, falling back to `IQR / 1.349` when MAD is zero.

```text
spike_threshold = median + max(4 * robust_std, 0.5 * median, 1 unit)
```

At least four available observations are required. A suspected global spike must also exceed the equivalent local threshold within four months when at least four nearby observations exist. This helps distinguish a sustained new level from a one-off bulk order. Sales strictly above the threshold are flagged `is_anomaly=True`, with reason `high_sales_spike`.

Rows are retained for audit, but flagged sales are excluded from regular demand, growth evidence, lost-demand comparators and safety-stock variability. Customer-specific bulk purchases cannot be identified without customer IDs.

For partner data, signed outbound lines first aggregate per SKU/document/warehouse. With at least eight positive documents, a candidate must exceed all of: `median + 6 * robust_std`, `5 * median`, and 10 units. A comparable repeated purchase (at least 80% of the candidate quantity) prevents automatic one-off exclusion. Only isolated candidates whose monthly signed shipment total reconciles exactly with the monthly report (tolerance 0.000001), and whose quantity does not exceed that net total, are subtracted. Unreconciled candidates are retained as review flags. Original quantities, document identifiers, reasons, thresholds, raw monthly values and excluded quantities remain auditable. This is a conservative statistical classification, not confirmation of a customer's intent. The optional future anonymized `customer_id` can be retained by the detector; there is no current customer-level attribution or anonymization service.

### Seasonality

Partner forecasts first use the supplied 12-month **brand-level** `СЕЗОННОСТЬ` coefficient profile (source `partner_brand`). These coefficients are normalized relative to the baseline months using the formula below; they are not treated as SKU-specific measurements. If a usable mapped profile is unavailable, derive history-based seasonality:

Require two complete calendar years of non-spike, estimable demand. Normalize each year's months by its annual median, then take the median index for each calendar month. Eligible same-category peers provide a normalized profile when the SKU lacks one. Without sufficient evidence, use factor 1.0.

```text
seasonal_factor = next_month_index / median_index_of_baseline_months
```

This adjusts relative to the recent season rather than counting seasonality twice.

### Sustainable growth

Use the latest six clean, non-stockout observations within nine months, with the newest no more than two months before the forecast month. Remove known seasonality first. Require at least four of five positive transitions and at least a 10% increase between the first-three and last-three medians. Positive changes must exceed 0.1% of the first-three median or a numerical tolerance.

Estimate a Theil-Sen slope (median of pairwise demand changes per elapsed month), fit a median residual intercept, and project next-month demand. Restore the next month's seasonal index.

```text
growth_factor = min(1.5, max(1, projected_demand / seasonal_forecast))
```

Without persistent evidence, the factor is 1.0. One isolated bulk order cannot establish a trend. The 50% uplift cap limits extrapolation.

### Stockout/lost-demand compensation

Prefer two or more same-calendar-month comparators; otherwise use up to six nearest non-stockout, non-anomalous months within 12 months of the outage.

```text
comparable_daily_rate = median(comparator_sales / comparator_calendar_days)
estimated_lost_demand = comparable_daily_rate * stockout_days
adjusted_demand = observed_sales + estimated_lost_demand
```

Imputed demand never supplies comparator rates or growth evidence. One or two nearby comparators are flagged as limited evidence. With none, at least seven available days permit an own-sales/available-days fallback; otherwise demand is unknown. If no usable history remains, forecast and calculated order are blank and require REVIEW. Raw sales remain unchanged in the audit. Historical lost units are not blindly added to next month's order.

For partner data, absent outage-day metadata does not establish availability or an outage. Only an **explicit zero historical inventory snapshot** supports a possible-stockout flag. With comparable clean months, estimate `lost = max(0, comparable_daily_rate * calendar_days - observed_sales)`, leaving the outage duration unknown. Such estimates require review and are excluded from growth/variability evidence. Without comparators they are unresolved, not zero. The supplied historical inventory sheets contain **no explicit zeros**, so this import infers no historical stockouts; current zero free stock alone does not establish a historical period outage.

## Replenishment formula and safety stock

```text
daily_demand = final_forecast / 30
lead_time_demand = daily_demand * lead_time_days
safety_stock = service_factor * monthly_std * sqrt(lead_time_days / 30)
target_stock = lead_time_demand + safety_stock
inventory_position = current_stock + in_transit
raw_order_qty = target_stock - inventory_position
raw_required_qty = max(0, ceil(raw_order_qty))
# If raw_required_qty == 0, final quantity remains 0.
quantity = max(raw_required_qty, supplied_minimum_or_zero)
recommended_order_qty = ceil(quantity / order_multiple) * order_multiple
# Without a positive order multiple, use ceil(quantity).
```

The configurable service factor defaults to 1.65. `monthly_std` is sample standard deviation (`ddof=1`) from up to 12 recent months, excluding anomalies and stockouts. At least three clean observations are needed; otherwise use the greater of forecast demand and clean historical mean as a conservative 100% variability proxy and require REVIEW. The whole-unit raw requirement and final constrained quantity are both retained. IEK `Мин. разр. к отгр.` is a **minimum shipment**, not an assumed multiple. Systeme Electric `Кратность` is an **order multiple**, with the dedicated MOQ workbook taking precedence over embedded sales-sheet values. Example: requirement 137 with multiple 20 becomes 140; requirement 21 with minimum 20 stays 21. Zero/absent constraints leave the ordinary requirement unchanged and are labelled unavailable. Never round downward or create an order solely because a minimum exists.

ORDER means positive calculated quantity; COVERED means inventory meets the target. REVIEW overrides either for anomalies, stockout estimates, insufficient/missing history or invalid data. Invalid quantity inputs produce a blank quantity, not zero coverage. Missing prices leave supplier values unknown.

## Urgency calculation

For positive demand:

```text
current_coverage_days = current_stock / daily_demand
position_coverage_days = (current_stock + in_transit) / daily_demand
```

Apply these rules in order using unrounded values:

| Level | Rule |
| --- | --- |
| CRITICAL | Current stock is zero, or total coverage is shorter than lead time |
| HIGH | Current-stock coverage is shorter than lead time, although transit makes total coverage sufficient |
| MEDIUM | Current stock covers lead time, but total coverage is less than lead time plus seven days |
| LOW | Current stock covers lead time, and total coverage includes at least seven extra days |

Zero forecast demand is LOW with coverage marked not applicable. Invalid demand, inventory or lead time is HIGH for investigation, explicitly not a confirmed shortage. Urgency is separate from ORDER/COVERED/REVIEW. Explanations state the coverage, lead time and reason; supplier summaries show their most urgent positive proposal.

## Manager review and approval

1. Review **Replenishment Recommendations**, including urgency.
2. Select a SKU using the shared **SKU** selector and inspect **Why this recommendation?**, the provenance panel and warnings.
3. Enter a nonnegative integer **Manager order quantity**. The algorithm's `recommended_order_qty` stays read-only; edits are stored as `manager_order_qty`.
4. Click **Approve reviewed quantity** to approve that SKU's demo decision and record its quantity and UTC timestamp. Zero-quantity decisions are valid.

The review table shows original and edited quantities, whether they differ, Pending/Approved state and approval time. A per-SKU session log retains edits, approvals and calculation changes. Editing an approved quantity resets it to Pending. Changed calculation inputs also invalidate approval: manual overrides survive, while untouched quantities follow the updated recommendation.

Streamlit session state preserves decisions across ordinary reruns and SKU switches. A new browser session, lost session or server restart may discard them. There is no authentication or durable approval database. **Approval never sends an order or contacts a supplier.**

## Supplier grouping and export

Filters and 25-SKU pagination prevent thousands of rows being rendered at once. Source loading is cached by workbook filename/size/modification time and source-code version; full supplier forecasts and recommendations are cached separately. Changing language, page, search, urgency, status or opening a Copilot brief does not rerun engine calculations. Changing a planning lead time or service factor recalculates replenishment, reusing forecasts. A cold partner load and full supplier calculation can take substantially longer than a warm interaction; spinners report those operations. Cache entries are bounded in memory. Restart the server after engine implementation changes.

Supplier totals and the full reviewed export cover **all filtered SKUs**, including products on other pages. Supplier detail previews show up to 50 lines, with a complete per-supplier CSV export. Product and review tables remain paginated; their native table exports contain only the displayed rows.

Supplier proposals group positive manager-reviewed quantities, including Pending ones, and show original quantities, urgency, data-review status and approval state. Totals use reviewed quantity times latest unit price. Zero-quantity decisions remain visible in the review table. Summary metrics and charts above this section continue to show calculated quantities, not overrides.

Use the download icon in a table's toolbar to export displayed columns as CSV. The review table exports original/edited quantities and decision states; supplier tables export proposal lines/totals. The explicit **Export reviewed recommendations (all filtered SKUs)** button includes full calculated adjustments, explanations, order constraints, original and reviewed quantities and approval state. A separate button exports the complete selected-SKU document audit. Manager quantities violating supplied constraints show a warning; the original compliant recommendation is preserved. There is no separate Excel generator or supplier dispatch integration.

## Assumptions and limitations

- Replenishment uses 30-day months; lost-demand reconstruction uses actual calendar days.
- The horizon is supplier lead time, without an additional periodic-review interval.
- Transit is assumed usable within that horizon; supplied expected arrival dates are retained in the inbound audit but are not time-phased by the replenishment formula. HIGH urgency flags reliance on timely transit.
- Synthetic calculations use the latest historical month; partner calculations use the supplied September 2026 snapshot origin, not today's date. Past evaluations must supply only history available at that forecast origin.
- Monthly aggregates cannot recover daily patterns, customer concentration or promotions without additional data. Historical outage durations must be supplied explicitly; zero inventory snapshots support only flagged comparable-period estimates.
- Without enough seasonal history, a seasonal ramp cannot always be distinguished from permanent growth.
- Safety stock assumes independent daily demand and is not a guaranteed service level. Constant observed sales yield zero estimated safety stock; fallbacks are heuristics, not guaranteed upper bounds.
- One common currency is assumed. Supplied shipment minimums/order multiples are modeled; taxes, shipping, capacity limits and cancellation of inbound orders are not.
- Customer-level anomaly analysis and anonymization of future customer imports are not implemented. Neither the synthetic schema nor the supplied partner document exports contains customer identifiers. Do not add raw customer PII to this dashboard.
- Approvals exist only in the current session and are not legal purchase-order authorization.

Further details: [forecasting methods](docs/demand_forecasting.md) and [replenishment assumptions](docs/replenishment.md).

## Automatic product-name translation

New product names are translated on demand with Google Cloud Translation Basic (v2). Russian and Kazakh (`kk`) are supported. The translation API key is read from the `TRANSLATION_API_KEY` environment variable; if it is missing or a request fails, the dashboard displays the original name. No extra Python package is needed.

1. In a billing-enabled Google Cloud project, enable the Cloud Translation API and create an API key restricted to that API.
2. Set the key in the shell where Streamlit will run. PowerShell example:

   ```powershell
   $env:TRANSLATION_API_KEY = "YOUR_GOOGLE_CLOUD_TRANSLATION_API_KEY"
   .venv\Scripts\python.exe -m streamlit run app.py
   ```

Translation results are cached in the operating system's user cache directory (`%LOCALAPPDATA%\Solai\product_translations.sqlite3` on Windows, or `$XDG_CACHE_HOME/solai/product_translations.sqlite3` / `~/.cache/solai/product_translations.sqlite3` on Linux/macOS). The cache key is the original product name plus target language. [Google Cloud language support](https://cloud.google.com/translate/docs/languages) · [Translation Basic v2 API](https://cloud.google.com/translate/docs/reference/rest/v2/translate).


## AI Procurement Copilot

**Mode A is always available and requires no API key.** It is deterministic decision intelligence, not an external LLM or a new demand model. **Generate decision brief** produces portfolio counts, known recommended units, unknown quantity counts, up to five priority SKUs, supplier impact, explicit data risks and next actions from the current filtered calculation outputs. Unknown quantities are excluded from known totals; an entirely unknown total is unavailable, not zero.

**Analyze SKU** exposes the actual forecast adjustments, inventory position, coverage, lead time, safety stock, target and order requirement, with RECOMMENDATION, RISK, DATA QUALITY and NEXT ACTION sections. Existing forecast/replenishment explanations remain accessible. Briefs and analyses have context fingerprints; changing the selection, calculation or language hides stale text until regenerated. Ordinary reruns preserve matching results.

Quality is qualitative, not a probability:

- **Review required:** any missing critical forecast/stock/transit/lead/order input, engine REVIEW status or review reasons.
- **Limited data:** no above review flags, but fewer than six baseline observations, fewer than twelve variability observations, unavailable seasonality or unknown stockout metadata.
- **Strong data:** none of those limitations. This is an evidence-completeness label, not a service or forecast-accuracy guarantee.

The priority queue uses these visible rules in order: engine urgency; REVIEW first within urgency; shortest known on-hand coverage; positive calculated order requirement; SKU as deterministic tie-breaker. Unknown coverage follows known coverage within each urgency/review group. There is no opaque AI score.

Key signals use existing growth, anomaly, stockout, coverage and MOQ outputs. Inventory above twice the calculated target is labelled precisely, not asserted to be obsolete. A declining-sales signal requires six consecutive clean recent months, at least four decreases and a last-three median at least 10% below the first-three median. It is explicitly observed sales, not seasonally adjusted, and does not change the forecast. Signals never infer an outage from missing data.

### Optional real-model mode

No LLM provider was configured during implementation. The app runs fully without one. To opt in, supply all three variables externally:

- `SOLAI_LLM_ENDPOINT`: your HTTPS chat-completions-compatible endpoint.
- `SOLAI_LLM_MODEL`: model identifier accepted by that provider.
- `SOLAI_LLM_API_KEY`: provider credential. Never put secrets in source files or Git.

The separate `TRANSLATION_API_KEY` is never reused for Copilot. Optional mode requires an explicit checkbox and button action. It sends only the generated evidence sentences, not raw workbooks or customer records. Supplier/SKU identifiers may appear in those sentences; enable it only for a provider you authorize to receive that business information.

The provider must accept JSON `model`, `messages`, `temperature` and `max_tokens`, and return chat-completions-style `choices[0].message.content` containing a JSON object with `fact_ids`. For example, `{"fact_ids": ["F1", "F0"]}` selects sentences provided in the request. The real model chooses the emphasis and ordering of the explanation; the application renders only those exact verified sentences. Free-form model claims, unknown IDs, extra fields and duplicate IDs are rejected. This intentionally constrains LLM narration instead of pretending arbitrary generated prose is verified. A 10-second timeout and 64 KiB response limit protect responsiveness. Missing configuration, service errors and unverified responses retain the full deterministic brief. No model response can modify calculations, quantities or approval state.

## Explainability and safety

Source sales, stock, transit, product metadata, constraints and source timestamps remain distinct from derived baseline, adjustments, forecast, safety stock, target, quantity and urgency. Manager-entered lead time is explicitly an assumption. Raw documents and monthly reconciliation evidence remain available for audit. Unknown values are never silently changed to zero for presentation or intelligence.

No supplier order is automatically sent. Approval is a local session decision, with no supplier dispatch integration. Existing business calculations and translation modules are reused; the new intelligence layer is read-only. This remains a decision-support MVP: approvals have no durable database or authentication, missing partner inputs still require confirmation, and optional LLM summaries are constrained evidence selections, not autonomous agents. Some technical audit/reason text remains in English even when localized navigation and core explanations use Russian or Kazakh.

## Screenshots

Add current validated captures here for submission:

- Overview with active data source and filtered portfolio KPIs.
- Replenishment detail showing source/derived provenance and urgency.
- Copilot brief with calculated evidence and data-quality limitations.
- Approval showing separate calculated/manager quantities and decision history.
