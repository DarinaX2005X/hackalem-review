# Electrical kit: automatic calculation of orders to suppliers

The service generates recommended orders to suppliers based on sales history. For each item, it provides the quantity, urgency, and justification, and groups the entire list by supplier. The calculation takes into account seasonality, steady growth, current stock levels, goods in transit, categories, planned growth, and lost demand during periods when the product is unavailable. One‑off large orders, including large sales to a single customer, are excluded from regular requirements.

The procurement department manager initiates the calculation by warehouse or category, receives a list of suppliers, adjusts the quantity if necessary, and approves the order. **Nothing is automatically sent to the supplier**: the approval only saves the files for the responsible employee.

## Launch

Python 3.12 is required for the fixed set of dependencies. Run the commands from the repository folder.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade 'pip>=26.2,<27'
python -m pip install -r requirements.txt

# quick start: without arguments, it runs on demo data from data/demo (creates them if necessary)
python main.py

# synthetic data + reference tables (data/demo/*.csv)
python -m src.generate_synthetic_data

# full calculation
python main.py --input data/demo/synthetic_sales.csv \
  --suppliers data/demo/suppliers.csv --catalog data/demo/catalog.csv \
  --stockouts data/demo/stockouts.csv --growth data/demo/category_growth.csv \
  --chart-sku SKU001

# only one warehouse / one category
python main.py --input data/demo/synthetic_sales.csv --warehouse WH1
python main.py --input data/demo/synthetic_sales.csv --category "Category 1"

# dashboard: by default, a secure demo mode on synthetic data
python -m streamlit run app.py

# tests
python -m unittest discover -s tests -v
```

On Windows, create an environment using `py -3.12 -m venv .venv` and activate it using the command `.venv\Scripts\Activate.ps1` in PowerShell. If Python of the required version is not installed, first install Python 3.12; activation does not create the environment.

**Choose the dashboard mode:** `APP_MODE=demo` provides synthetic examples only; `APP_MODE=local` enables file uploads and order approval without login on the operator's own computer; `APP_MODE=production` requires corporate login. For production, configure OIDC according to [SECURITY.md](SECURITY.md), fill in `.streamlit/secrets.toml` according to the example, and set `APP_MODE=production`. An unconfigured production mode blocks access. The CLI `python main.py --input ...` is also available for local calculations.

After updating the dependencies and modules, stop the old server (`Ctrl+C`) and launch it again: a single tab refresh may not be enough. If `localhost` is not responding, check `http://127.0.0.1:8501` and make sure the old process has released the port.

Inventory policy parameters: `--review-days` (review period, default is 7), `--service-z` (service level z, 1.65 ≈ 95%), `--default-lead-time` (lead time if not specified, 14). `--forecast-days` sets the forecast report horizon. The forecast horizon for an order is selected automatically and covers the longest lead time plus the review period.

### Local dashboard: upload files without login

After installing the dependencies above, stop any previous server with `Ctrl+C` and run from the repository folder. Virtual environment activation is optional when using the explicit Python paths below.

**Windows / VS Code PowerShell:**

```powershell
$env:APP_MODE = "local"
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

**macOS / Linux:**

```bash
APP_MODE=local ./.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

Open [http://127.0.0.1:8502](http://127.0.0.1:8502) and select **«Загрузить свои файлы»** in the left sidebar. CSV and XLSX uploads, calculations, approval, and exports are available. Local approvals are attributed to `local-operator`.

Local mode requires a loopback listener (`127.0.0.1` or `::1`) and is intended for the operator's own computer, not public deployment through a proxy or tunnel. To return to demo mode in the same PowerShell terminal, stop the server, set `$env:APP_MODE = "demo"`, and run the launch command again. On macOS/Linux, replace `APP_MODE=local` with `APP_MODE=demo`.

## Dashboard

`python -m streamlit run app.py` opens the interface in a browser (http://localhost:8501). When `APP_MODE` is unset, only demo data is available. File uploads are available in local mode as described above, or to authorized analysts and managers in production:

1. **Data.** Upload sales history (CSV/XLSX, for example, an export from 1C) and, if available, reference data: suppliers, items, stock levels, periods of product unavailability, growth forecast. In the “File Templates” section, you can download examples in the required format. The “Show on demo data” button runs the calculation on synthetic data without its own files.
2. **Parameters.**Warehouse or category, revision period, service level. Then click the “Run calculation” button.
3. **Orders by supplier.** Summary indicators, positions of the selected supplier with urgency and justification. The “Approved quantity” column can be edited.
4. **Statement.**The manager clicks “Approve”: buttons to download the order in XLSX and CSV for 1C appear. In production, the responsible person is determined by the account; in local mode it is `local-operator`. In the demo, the approval is marked as training. The order is not automatically sent to the supplier.
5. **Article card.** A 120‑day chart: actual sales, demand for calculation (excluding one‑off orders, with missed demand), and forecast for the coverage period. One‑off orders are marked with dots, and days when the item is out of stock are highlighted with a fill. Next, a step‑by‑step calculation of the quantity from forecast to order and a list of events.
6. **Trends by category.** Weekly adjusted demand.

**Appearance:** open the **⋮** menu at the top right to switch between light and dark themes. The menu is enabled with `client.toolbarMode = "viewer"` in `.streamlit/config.toml`.

The service verifies the owner and session when reading the result. Temporary folders are deleted after an hour, and copied source files are deleted after the calculation. One calculation is allowed at a time, and up to three per user within five minutes; in the public demo, this limit is shared. Browser/Streamlit memory storage limitations and download links are described in [SECURITY.md](SECURITY.md).

## Demo and production deployment

For public demonstration, use `APP_MODE=demo`, Python 3.12, and only synthetic files from `data/demo/`. The platform must install `requirements.txt` along with `requirements.lock`. Set the listening address to match the network model of the chosen hosting; by default, the repository listens only to loopback.

For production deployment with real data, HTTPS, OIDC, an authentication gateway before all Streamlit routes, and resource limits are required. The [deploy/nginx.conf.example](deploy/nginx.conf.example) template requires configuration of the domain, certificate, and gateway; it is not an already completed deployment. Configuration order and remaining restrictions: [SECURITY.md](SECURITY.md). Audit results: [SECURITY_REPORT.md](SECURITY_REPORT.md).

## Input data

Files are accepted in CSV (comma, semicolon, tab, or `|`; UTF-8/Windows-1251) or XLSX with a single sheet of values, without formulas, macros, or external links. Limits: 20 MB per file, 60 MB per web upload set, 100,000 rows, 40 columns, and 2 million cells per table. Column names are recognized in Russian and English; case is not important. If two columns fit into the same field, the file is rejected.

Value formats are the same as in 1C exports:
- **Dates:** `YYYY-MM-DD` (ISO, including date cells from Excel) or `DD.MM.YYYY` (the day is always first: `01.02.2025` — 1 February).
- **Numbers:**You can use a space or an non‑breaking space between the digits and a comma in the fractional part (`1 234,5`).**
- **CSV for 1C as output:** delimiter `;`, decimal comma, whole quantities without `,0`, UTF‑8 with BOM.
- **“Out of stock” flag:** `yes/no`, `true/false`, `1/0`.

Rows with an incorrect date, an empty article number. 
