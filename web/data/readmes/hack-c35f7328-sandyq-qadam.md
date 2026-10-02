# hack-c35f7328-sandyq-qadam
Hackathon team repository for Sandyq Qadam
# hack-c35f7328-sandyq-qadam
Hackathon team repository for Sandyq Qadam
**
For judges / reviewers: if the main branch currently shows only a basic README.md, please check the other branches — the working implementation may still be located in dev, feature/data-forecasting, feature/inventory, and feature/frontend. The team developed the solution in parallel branches and merged components incrementally.**

# Sandyq Qadam — AI Procurement Assistant

AI-powered demand forecasting and supplier order recommendation system.

Developed for the HackAlem AI case:

**Supplier Order Generation Automation**

---

## Problem

Procurement managers need to simultaneously consider:

- historical sales;
- demand seasonality;
- current stock;
- incoming goods;
- supplier lead times;
- one-off large customer orders;
- stockout periods;
- safety stock.

Manual planning can lead to two major problems:

- **stock shortages** → lost sales;
- **excess inventory** → higher storage costs and frozen capital.

---

## Solution

Sandyq Qadam provides an end-to-end procurement recommendation pipeline:

```text
Sales History
    ↓
Data Preprocessing
    ↓
One-off Order Detection
    ↓
Stockout Correction
    ↓
Demand Forecasting
    ↓
Inventory Calculation
    ↓
Recommended Order
    ↓
Risk Assessment
    ↓
Supplier Grouping
    ↓
Frontend Dashboard
```

The system produces a recommendation for the procurement manager rather than automatically sending a purchase order.

---

## Data

### Sales History

The project uses the open **UCI Online Retail II** dataset.

Dataset period:

```text
2009-12-01 → 2011-12-09
```

Raw dataset size:

```text
1,067,371 transactions
```

Main source fields:

```text
Invoice
StockCode
Description
Quantity
InvoiceDate
Price
Customer ID
Country
```

For the MVP, 50 SKUs with sufficient sales history were selected.

> UCI Online Retail II is used as an open proxy dataset to demonstrate the algorithm. It is not real data from TОО Elektokomplekt.

### Warehouse Data

The public dataset does not contain:

- current stock;
- incoming stock;
- supplier;
- lead time;
- stock history.

Therefore, warehouse-related fields are synthetic in the current MVP.

```text
Sales history  → real open data
Warehouse data → synthetic MVP data
```

---

## Data Preprocessing

Before forecasting, the pipeline:

- separates cancelled orders;
- separates returns;
- removes invalid records;
- converts transactions into daily sales;
- creates a continuous daily calendar;
- fills missing dates;
- selects SKUs with sufficient history.

Processed modeling dataset:

```text
Selected SKUs:        50
Daily observations:   36,648
```

---

## One-off Order Detection

Large one-off customer purchases can significantly distort regular demand.

Example:

```text
Typical customer order: 12 units
One-off customer order: 4300 units
```

The detector uses:

- SKU-level IQR;
- median order size;
- historical behavior of the customer for the SKU.

Results for the selected SKUs:

```text
Customer-day orders:        94,957
Strong one-off orders:         771
Anomaly rate:                 0.81%
```

Actual sales are not removed.

Instead, the forecasting pipeline creates a separate adjusted demand value so that extreme one-off purchases do not inflate regular demand forecasts.

---

## Stockout Correction

Zero sales do not always mean zero demand.

For example:

```text
sales = 0
stock = 0
```

In this situation, the product may simply have been unavailable.

For stockout days, the system estimates lost demand using historical demand from comparable previous days.

MVP stockout simulation results:

```text
Stockout days:             273
Recovered lost demand:   7,942 units
```

The final demand series is therefore:

```text
Raw Sales
    ↓
One-off Order Adjustment
    ↓
Stockout Correction
    ↓
Final Demand
```

---

## Demand Forecasting

The forecasting horizon is defined as:

```text
forecast_horizon =
lead_time_days + review_period_days
```

Example:

```text
lead_time_days = 14
review_period_days = 7

forecast_horizon = 21 days
```

The returned `forecast` is the **total expected demand over the entire forecast horizon**.

The inventory module must not multiply the forecast by lead time again.

### Public Forecasting API

```python
from src.forecasting.model import get_demand_forecast

result = get_demand_forecast(
    sku="20685",
    lead_time_days=14,
    review_period_days=7,
)
```

Example result:

```python
{
    "sku": "20685",
    "forecast": 205.12,
    "horizon_days": 21,
    "lead_time_days": 14,
    "review_period_days": 7,
    "anomalies_found": 1,
    "stockout_days": 2,
    "recovered_lost_demand": 20.0
}
```

---

## Seasonality

The current forecasting model includes weekly seasonality.

For example:

```text
Future Monday    → recent Mondays
Future Tuesday   → recent Tuesdays
Future Wednesday → recent Wednesdays
...
```

This allows the forecast to model weekly demand patterns instead of using a single average value for every day.

---

## Forecast Evaluation

The forecasting approach was evaluated using time-based backtesting.

Two baselines were compared:

1. simple recent mean;
2. seasonal weekday forecast.

Results:

```text
Simple Mean MAE:       35.91
Seasonal Weekday MAE:  32.21

Improvement:           10.29%

Seasonal model better:
39 / 50 SKUs
```

The weekly seasonal model reduced MAE by approximately **10%** compared with the simple mean baseline.

---

## Inventory Recommendation

After receiving the demand forecast, the inventory module considers:

- forecast demand;
- current stock;
- incoming goods;
- safety stock;
- supplier;
- lead time.

### Safety Stock

Current MVP logic:

```text
safety_stock =
forecast × safety_factor
```

Default:

```text
safety_factor = 20%
```

### Recommended Order

```text
raw_order =
forecast
+ safety_stock
- stock
- incoming
```

Final order quantity:

```text
recommended_order =
max(
    0,
    ceil(raw_order)
)
```

`ceil()` is used to avoid rounding required inventory downward.

---

## End-to-End Backend Example

Example product:

```text
SKU: 20685
Product: DOORMAT RED RETROSPOT
```

Input:

```text
Forecast horizon: 21 days
Forecast:         205.12

Current stock:     80
Incoming stock:    40

Safety factor:     20%
Safety stock:      41.024
```

Calculation:

```text
205.12
+ 41.024
- 80
- 40
= 126.144
```

Final recommendation:

```text
Recommended order: 127 units
Risk: HIGH
```

---

## Backend API for Frontend

The backend exposes a single public entry point for the frontend:

```python
from src.inventory import get_order_recommendation
```

The frontend should not calculate:

- forecast;
- safety stock;
- recommended order;
- risk.

It should receive the final recommendation from the backend.

Example result structure:

```python
{
    "sku": "20685",
    "supplier": "Supplier_A",

    "forecast": 205.12,
    "horizon_days": 21,

    "stock": 80,
    "incoming": 40,

    "lead_time_days": 14,
    "review_period_days": 7,

    "safety_stock": 41.024,
    "recommended_order": 127,

    "risk": "HIGH",

    "anomalies_found": 1,
    "stockout_days": 2,
    "recovered_lost_demand": 20.0,

    "explanation": "..."
}
```

---

## Risk Assessment

The backend returns one of three deterministic risk levels:

```text
LOW
MEDIUM
HIGH
```

The current MVP risk represents inventory coverage over the planning horizon.

It is **not** a statistical stockout probability.

---

## Supplier Grouping

Order recommendations can be grouped by supplier.

Example:

```text
Supplier_A
├── SKU_001 → 70 units
├── SKU_014 → 127 units
└── SKU_025 → 35 units

Supplier_B
├── SKU_003 → 20 units
└── SKU_041 → 45 units
```

This allows the procurement manager to review proposed orders separately for each supplier.

---

## Explainability

Each recommendation includes a human-readable explanation.

Example:

```text
Forecast for 21 days: 205.12 units.
Current stock: 80 units.
Incoming stock: 40 units.
Safety stock: 41.024 units.
Recommended order: 127 units.
```

The backend also preserves forecasting metadata:

```text
anomalies_found
stockout_days
recovered_lost_demand
```

---

## Tests

Run all tests:

```bash
python -m pytest -v
```

Current backend validation:

```text
57 tests passed
```

Tests cover:

- forecasting contract;
- unknown SKU validation;
- invalid forecast horizon;
- non-negative forecasts;
- anomaly metadata;
- stockout metadata;
- safety stock;
- order quantity;
- ceil-based replenishment;
- risk calculation;
- supplier grouping;
- backend public contract;
- Forecasting → Inventory integration.

---

## Project Structure

```text
.
├── app/
│   └── streamlit_app.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
│
├── src/
│   ├── data/
│   │   ├── load_data.py
│   │   ├── preprocess.py
│   │   ├── anomaly_detection.py
│   │   └── stockout_correction.py
│   │
│   ├── forecasting/
│   │   ├── baseline.py
│   │   └── model.py
│   │
│   ├── inventory/
│   │   ├── safety_stock.py
│   │   ├── order_calculator.py
│   │   ├── supplier_grouping.py
│   │   └── ...
│   │
│   └── pipeline.py
│
├── tests/
│
├── demo_backend.py
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Installation

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Dataset Preparation

Download **UCI Online Retail II** and place the Excel file at:

```text
data/raw/online_retail_II.xlsx
```

Raw and generated datasets are excluded from Git.

Run preprocessing:

```bash
python -m src.data.preprocess
```

Run one-off order detection:

```bash
python -m src.data.anomaly_detection
```

Run stockout correction:

```bash
python -m src.data.stockout_correction
```

Run forecasting evaluation:

```bash
python -m src.forecasting.baseline
```

---

## Backend Demo

```bash
python demo_backend.py
```

The backend demo validates the main flow:

```text
UCI Sales
→ Demand Forecast
→ Inventory Calculation
→ Recommended Order
```

---

## Frontend

After frontend integration:

```bash
streamlit run app/streamlit_app.py
```

---

## MVP Status

### Implemented

- [x] Open sales dataset
- [x] Transaction preprocessing
- [x] Returns and cancellation handling
- [x] Daily demand series
- [x] Active SKU selection
- [x] One-off large order detection
- [x] One-off demand correction
- [x] Stockout correction
- [x] Weekly seasonal forecasting
- [x] Time-based backtesting
- [x] Baseline comparison
- [x] Public forecasting API
- [x] Safety stock calculation
- [x] Recommended order calculation
- [x] Ceil-based replenishment
- [x] Risk assessment
- [x] Supplier grouping
- [x] Explanation generation
- [x] Public backend API for frontend
- [x] Automated backend tests
- [x] Forecasting → Inventory integration
- [x] End-to-end backend smoke test

### In Progress

- [ ] Final Streamlit → real backend integration
- [ ] Final end-to-end UI validation
- [ ] Frontend polishing

### Not Implemented in the MVP

- [ ] Real Elektokomplekt warehouse data
- [ ] Real supplier data or supplier APIs
- [ ] Incoming shipment ETA modeling
- [ ] Minimum order quantities
- [ ] Supplier-specific purchasing constraints
- [ ] ERP / 1C integration
- [ ] Production database
- [ ] Authentication
- [ ] Automatic purchase order submission
- [ ] Production deployment
- [ ] Probabilistic stockout risk model

---

## Known Limitations

### Synthetic Warehouse Data

Current stock, incoming quantities, suppliers, lead times and historical stockout information are synthetic.

They demonstrate the business logic but do not represent real Elektokomplekt warehouse operations.

### Historical Sales Dataset

UCI Online Retail II is a general retail dataset and is not specific to electrical equipment.

### Incoming ETA

The current MVP uses aggregate incoming stock.

Exact ETA for each incoming shipment is not modeled.

### Risk

`LOW / MEDIUM / HIGH` is a deterministic inventory coverage indicator.

It is not a probability of stockout.

### Safety Stock

The current MVP uses a configurable percentage-based safety stock.

Default:

```text
20%
```

A production system should calculate safety stock using:

- demand variability;
- lead-time variability;
- target service level.

---

## Next Steps

With real company data, the next version can include:

- real warehouse balances;
- real goods-in-transit data;
- supplier lead-time history;
- minimum order quantities;
- supplier-specific constraints;
- category-level forecasting;
- probabilistic forecasting;
- automated model retraining;
- ERP / 1C integration;
- purchase order export;
- manager approval workflow;
- production monitoring.

---

## Human-in-the-loop

The system generates a recommendation, not an automatic purchase order.

Final supplier order approval remains with the responsible procurement manager.
