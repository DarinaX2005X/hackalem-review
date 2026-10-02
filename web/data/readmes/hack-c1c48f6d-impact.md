# Explainable Supplier Replenishment

A deterministic warehouse-replenishment decision-support application for **SystemElectric** and **IEK**. It is designed for purchasing managers who need to turn sales, stock, inbound supply, seasonality, growth, and supplier order constraints into explainable supplier-order recommendations.

The application reads the partner-provided Excel workbooks, normalizes them into a common data model, removes abnormal one-off demand from the regular-demand signal, applies a conservative stockout adjustment, forecasts demand, accounts for available stock and eligible inbound supply, rounds the result to the supplier shipment multiple, and presents the result in a Streamlit dashboard.

> **Important:** The application does not use an LLM, external AI model, or external API to calculate order quantities. The recommendation logic is deterministic and auditable.

---

## 1. Project name

**Explainable Supplier Replenishment**

HackAlem AI case: **Automatic calculation of supplier orders for warehouse replenishment**.

---

## 2. Short description

Purchasing managers currently have to combine sales and inventory information manually when deciding what to reorder. This process is slow and can produce both overstock and shortages, especially when regular demand is distorted by one-off large orders, stockouts, seasonality, or changing demand.

This project provides a single dashboard that:

- reads the supplied SystemElectric and IEK Excel workbooks;
- normalizes product, sales, stock, MOQ, seasonality, and inbound-shipment data;
- separates regular demand from quantity anomalies;
- estimates a conservative stockout adjustment;
- calculates growth and seasonality factors;
- forecasts demand for a configurable replenishment horizon;
- subtracts usable stock and inbound supply expected before the required date;
- rounds the result to the supplier shipment multiple;
- assigns an urgency level;
- explains every recommendation;
- exports recommendations to CSV or Excel.

The primary user is a **purchasing / procurement manager** reviewing warehouse replenishment needs before approving an order.

---

## 3. What has been implemented

### Multi-source Excel ingestion

The repository contains source-specific loaders for all supplied SystemElectric and IEK workbooks.

The loaders:

- detect workbook header rows using required field names;
- preserve 1C SKU codes as strings;
- preserve meaningful leading zeroes and trailing underscores;
- parse Russian month/year columns dynamically;
- parse IEK expected-arrival dates from shipment-column headers;
- preserve raw transaction quantities for auditability;
- normalize source-specific tables into common structures.

### Sales normalization

The transaction exports contain positive and negative movements. The project implements an audited sign rule instead of applying `abs(quantity)`:

- valid positive `Расходная накладная` movements from 2025 onward are treated as outbound demand;
- valid negative pre-2025 expense-invoice movements are treated as legacy outbound demand and sign-reversed;
- opposite-sign corrections/returns are not counted as regular demand;
- non-sales documents and invalid/footer rows contribute zero regular demand.

The original value remains available as `raw_quantity`.

### One-off quantity anomaly detection

Sales are aggregated by supplier, SKU, and day.

For each SKU independently, unusually large daily demand is detected using:

- median absolute deviation (MAD) and a robust z-score;
- an IQR/ratio fallback when MAD is zero.

Flagged demand remains in the raw source history but is excluded from the cleaned regular-demand series.

### Monthly demand reconciliation

The application uses transaction-level demand when transaction detail is available for a month and uses the monthly sales workbook as a fallback.

The two sources are **not added together**, preventing double counting.

### Stockout adjustment

Monthly stock values at or below zero are treated as potential stockout observations.

Because monthly snapshots cannot prove that an SKU was out of stock for an entire month, the application applies a configurable conservative stockout fraction instead of claiming exact lost sales.

The default fraction is `0.35`.

### Growth calculation

Sustained growth is calculated from multi-month demand windows rather than from a single month-to-month change.

The calculated growth factor is capped to a configurable range (default `0.70` to `1.50`) to reduce unstable forecasts from noisy histories.

### Seasonality

The forecast uses a hierarchy:

1. SKU-level seasonality when sufficient history exists;
2. supplier-level aggregate seasonality from the supplied workbooks;
3. neutral factor `1.0` as the final fallback.

SystemElectric's supplied growth and seasonality coefficients are preserved separately for audit/comparison rather than silently replacing the application's calculated factors.

### Inventory handling

For **SystemElectric** the application keeps:

- total/current stock;
- reserved stock;
- free stock.

Reserved units are not added to usable/free stock.

For **IEK**, where there is no separate current-inventory file in the supplied data, the latest non-null monthly stock snapshot is used as the latest available stock estimate.

### Goods in transit

SystemElectric's supplied inbound quantity is represented as an inbound shipment with its known arrival date.

IEK shipment columns are normalized into individual inbound records containing:

- SKU;
- quantity;
- expected arrival date;
- shipment reference;
- supplier article.

The calculation subtracts only inbound supply expected to arrive before the required replenishment date.

### Replenishment calculation

The application calculates:

```text
demand during horizon
    = forecast monthly demand × horizon days / 30

safety stock
    = service factor
      × recent demand standard deviation
      × sqrt(lead time days / 30)

raw requirement
    = max(
        0,
        demand during horizon
        + safety stock
        - available/free stock
        - eligible inbound
      )

recommended order
    = raw requirement rounded up to the supplier order multiple
```

Default planning assumptions in the repository are:

- replenishment horizon: **45 days**;
- lead-time assumption: **30 days**;
- safety-stock service factor: **1.28**;
- estimated stockout-month fraction: **0.35**;
- one-off robust z threshold: **5.0**.

These values are editable in the dashboard.

### MOQ / shipment-multiple handling

The final recommendation respects:

- SystemElectric `Кратность`;
- IEK `Мин. разр. к отгр.`.

If a usable shipment multiple is missing, the current implementation falls back to `1` and marks the SKU as having missing MOQ data.

### Urgency

Recommendations receive one of four deterministic urgency levels:

- `CRITICAL`
- `HIGH`
- `MEDIUM`
- `LOW`

Urgency is based on available stock, forecast demand, calculated days of supply, lead-time assumption, horizon, and whether additional stock is required.

### Explainability

Every recommendation includes a text rationale with the important calculation inputs, including:

- forecast demand;
- safety stock;
- available/free stock;
- reserved stock;
- eligible inbound;
- raw requirement;
- MOQ/order multiple;
- final rounded recommendation;
- relevant growth, seasonality, stockout, anomaly, MOQ, or stock-data context.

The SKU detail view also exposes calculation diagnostics.

### Streamlit dashboard

The dashboard includes:

- configurable planning assumptions;
- supplier filter;
- SKU/product search;
- category filter when category metadata exists;
- urgency filter;
- KPI cards;
- recommendation table;
- SKU-level demand history;
- cleaned and stockout-adjusted demand;
- monthly stock history;
- inbound-shipment detail;
- business-calculation explanation;
- calculation diagnostics;
- data-quality report;
- deterministic demo examples selected from calculated results;
- CSV export;
- Excel export grouped into supplier worksheets.

### Data-quality reporting

The application reports issues instead of silently hiding them, including:

- sales SKUs without MOQ records;
- MOQ SKUs without sales;
- missing current inventory;
- missing transit records;
- missing or invalid MOQ;
- duplicate product SKUs;
- invalid transaction dates;
- invalid transaction quantities.

### Automated tests

The repository includes tests for:

- SKU normalization and leading-zero preservation;
- Russian month parsing;
- IEK shipment-date parsing;
- sales-sign normalization;
- exclusion of non-sales documents;
- per-SKU one-off anomaly detection;
- extreme one-off demand not dominating the cleaned forecast;
- transaction/monthly reconciliation without double counting;
- stockout adjustment;
- seasonality;
- sustained growth;
- stock and inbound monotonicity;
- reserved-stock treatment;
- MOQ rounding and fallback;
- business-friendly zero-demand display;
- late inbound not covering an earlier shortage;
- rationale generation;
- supplier grouping.

---

## 4. How the solution works

The end-to-end flow is:

```text
Partner Excel workbooks
        │
        ▼
Source-specific loaders
        │
        ▼
Normalized product / sales / stock / inbound data
        │
        ▼
Transaction sign normalization
        │
        ▼
Per-SKU one-off quantity anomaly detection
        │
        ▼
Monthly demand reconciliation
(transaction detail preferred; monthly workbook fallback)
        │
        ▼
Conservative stockout adjustment
        │
        ▼
Baseline demand + sustained growth + seasonality
        │
        ▼
Demand forecast for the planning horizon
        │
        ▼
Safety stock
        │
        ▼
Subtract available stock and eligible inbound supply
        │
        ▼
Round requirement up to supplier MOQ / shipment multiple
        │
        ▼
Urgency + human-readable rationale
        │
        ▼
Purchasing-manager review
        │
        ├── Streamlit dashboard
        ├── CSV export
        └── Excel export
```

The system stops at decision support and export. It does **not** automatically send an order to a supplier.

---

## 5. Technologies

### Language

- Python

### Application / UI

- Streamlit

### Data processing

- pandas
- NumPy

### Excel support

- openpyxl
- XlsxWriter

### Testing

- pytest

### AI models

No AI/LLM model is used at runtime for forecasting or order-quantity calculation.

### APIs and external services

The current repository does not require an external API or external web service to perform the replenishment calculation.

---

## 6. Project architecture

```text
.
├── app.py
├── requirements.txt
├── README.md
├── docs/
│   └── DATA_AUDIT.md
├── src/
│   ├── config.py
│   ├── diagnostics.py
│   ├── explanations.py
│   ├── export.py
│   ├── forecast.py
│   ├── inventory.py
│   ├── loaders.py
│   ├── normalize.py
│   ├── outliers.py
│   ├── pipeline.py
│   ├── presentation.py
│   ├── quality.py
│   ├── replenishment.py
│   ├── seasonality.py
│   ├── stockouts.py
│   └── transactions.py
├── tests/
│   ├── test_forecast.py
│   ├── test_loaders.py
│   ├── test_outliers.py
│   └── test_replenishment.py
├── Systeme electric/
│   └── Systeme electric/
│       └── partner Excel workbooks
└── IEK/
    └── IEK/
        └── partner Excel workbooks
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| `app.py` | Streamlit interface, filters, charts, downloads, SKU details |
| `src/config.py` | Workbook locations and default planning assumptions |
| `src/loaders.py` | Source-specific Excel ingestion and header/date parsing |
| `src/normalize.py` | SKU and Russian month normalization |
| `src/transactions.py` | Audited sales-sign normalization |
| `src/outliers.py` | Per-SKU one-off quantity anomaly detection |
| `src/stockouts.py` | Conservative lost-demand adjustment |
| `src/forecast.py` | Baseline demand and sustained-growth forecast |
| `src/seasonality.py` | SKU/supplier seasonal-factor selection |
| `src/inventory.py` | Latest IEK stock and date-aware inbound aggregation |
| `src/replenishment.py` | Safety stock, net requirement, MOQ rounding, urgency |
| `src/explanations.py` | Deterministic recommendation rationale |
| `src/diagnostics.py` | SKU-level calculation trace |
| `src/quality.py` | Data-quality checks |
| `src/export.py` | CSV and supplier-grouped Excel export |
| `src/pipeline.py` | End-to-end orchestration |

A detailed audit of the supplied workbooks is available in `docs/DATA_AUDIT.md`.

---

## 7. Installation and launch

### Prerequisites

- Python 3
- The partner Excel files in the repository paths expected by `src/config.py`

### 1. Clone the repository

```bash
git clone <repository-url>
cd hack-c1c48f6d-impact
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate it

#### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```cmd
.venv\Scripts\activate.bat
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Launch the dashboard

```bash
streamlit run app.py
```

Streamlit will print the local address in the terminal, normally:

```text
http://localhost:8501
```

---

## 8. How to test the solution

### Automated tests

Run:

```bash
pytest -q
```

Optional syntax check:

```bash
python -m compileall -q app.py src tests
```

### Reproducible judge scenario

1. Start the application with:

   ```bash
   streamlit run app.py
   ```

2. Keep the default planning assumptions:

   - horizon: 45 days;
   - lead-time assumption: 30 days;
   - safety-stock service factor: 1.28;
   - stockout-month fraction: 0.35;
   - outlier threshold: 5.0.

3. Enable **Demo mode** in the sidebar.

4. Choose one of the representative examples generated from the current calculated results, for example:

   - `Anomaly-adjusted SKU`;
   - `Stockout-adjusted SKU`;
   - `Inbound-covered SKU`;
   - `SKU requiring reorder`.

5. In **SKU detail**, review:

   - the recommendation rationale;
   - growth factor;
   - seasonality factor;
   - safety stock;
   - days of supply;
   - raw vs cleaned vs stockout-adjusted demand;
   - stock history;
   - inbound shipments;
   - business calculation;
   - calculation diagnostics.

6. Return to the recommendation table and confirm that each row contains supplier, SKU, forecast, stock/inbound information, MOQ, recommended order quantity, urgency, and warnings.

7. Use **Download CSV** and **Download Excel** to verify export.

### Business-rule checks implemented in tests

The included test suite also verifies important expected behavior:

- increasing stock cannot increase the calculated order;
- increasing eligible inbound cannot increase the calculated order;
- reserved stock is not treated as free stock;
- late inbound cannot cover an earlier shortage;
- a very large one-off quantity anomaly is retained in raw history but removed from cleaned regular demand;
- stockout adjustment increases adjusted demand in the tested stockout scenario;
- shipment multiples round the final recommendation upward;
- transaction-level and monthly sales sources are not double counted.

---

## 9. Data and integrations

The application works directly with the partner-provided Excel workbooks.

### SystemElectric

- `MOQ SystemElectric.xlsx`
- `Динамика продаж_Syseme Electric_2025-2026.xlsx`
- `Ежемесячные остатки SystemElectric 2024-2026.xlsx`
- `Ежемесячные продажи в кол-м выражении SystemElectric 2024-2026.xlsx`
- `Сезонность SystemElectric 2024-2026.xlsx`
- `Товар в пути_SystemElectric на 22.09.2026.xlsx`

### IEK

- `MOQ  ИЭК.xlsx`
- `Динамика продаж_2025-2026.xlsx`
- `Ежемесячные остатки продукции за последние 2 года  ИЭК.xlsx`
- `Ежемесячные продажи в количественном выражении за последние 2 года.xlsx`
- `Путь ИЭК 22.09.2026.xlsx`
- `Сезонность ИЭК.xlsx`

### Normalized information used

Depending on the source, the pipeline uses:

- 1C SKU code;
- supplier article;
- product name;
- category metadata where available;
- transaction date;
- document type;
- warehouse;
- transaction quantity;
- monthly sales;
- monthly stock;
- current stock;
- reserved stock;
- free stock;
- order multiple / minimum shipment multiple;
- aggregate seasonality;
- supplied SystemElectric growth/seasonality coefficients for audit;
- inbound quantity;
- expected inbound arrival date.

### External integrations

There is currently no runtime integration with:

- supplier ordering systems;
- email;
- 1C API;
- OpenAI API;
- NVIDIA API;
- other external services.

The source files are exported business data and are read locally by the application.

---

## 10. Limitations

The current implementation has the following documented limitations.

### Customer-specific bulk-order detection cannot be evaluated

The case mentions large purchases made by a single customer, but the supplied transaction workbooks do not contain a customer identifier.

The current implementation detects **quantity-based per-SKU one-off anomalies**, but it cannot verify whether several transactions belong to one customer.

No customer IDs are fabricated.

### Stockouts are estimated from monthly snapshots

The provided inventory histories are monthly snapshots, not daily stockout intervals.

A zero/non-positive monthly stock observation therefore indicates a **potential stockout**, not proof that the SKU was unavailable for the whole month.

The application uses a configurable conservative adjustment rather than claiming exact lost demand.

### Explicit supplier lead times are not present

The supplied workbooks do not contain a complete supplier lead-time directory.

Lead time is therefore a clearly labeled configurable planning assumption in the dashboard. The default is 30 days.

Expected arrival dates from known inbound shipments are still used when determining eligible in-transit stock.

### IEK current stock is approximated from the latest monthly snapshot

SystemElectric has dedicated current/free/reserved stock fields.

For IEK, the latest available monthly stock value is used because a separate current-stock field is not present in the supplied IEK inputs.

### Missing MOQ values use a fallback

Missing or non-positive supplier order multiples use a fallback value of `1`.

The condition is carried as `moq_missing`, reported by the data-quality layer, and mentioned in the rationale for affected recommendations.

### Product metadata is incomplete for some SKUs

Some SKU keys do not have complete article, product, or category metadata across the supplied sources.

The application uses a deterministic metadata-priority order and displays warnings where information remains unavailable.

### Category is metadata/filtering, not a forecasting feature

Category information is preserved where available and can be used to filter the dashboard.

The current forecast calculation does not use category-level demand as an input or fallback.

### Forecasting is intentionally transparent

The project uses a deterministic baseline/trend/seasonality method rather than a complex black-box forecasting model.

This improves auditability for a hackathon MVP but does not attempt to model every possible demand pattern.

### Sparse histories can have lower forecast confidence

Some SKUs have limited regular-demand history. The current repository marks sparse history in its warning layer, but the underlying recommendation should still be reviewed by a purchasing manager.

### Safety-stock variability depends on available history

Safety stock uses recent observed demand standard deviation. When history is limited, statistical variability can be weak or unavailable.

### No automatic supplier submission

The project deliberately does not automatically place or send orders to suppliers.

Recommendations are intended for human review and export.

### No deployed public URL is currently defined in the repository

The application is run locally with Streamlit unless a separate deployment is added.

---

## 11. Deployed version

No deployed public URL is currently specified in the repository.

Run the application locally with:

```bash
streamlit run app.py
```

---

## Repository notes

- The application does not modify the original Excel workbooks.
- The detailed source-data audit is in `docs/DATA_AUDIT.md`.
- Recommendations are decision support and remain subject to purchasing-manager review.
