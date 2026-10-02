# hack-f5ec9a3e-codex-make-no-mistakes
Hackathon team repository for Codex, make no mistakes

HackAlem AI case: supplier order recommendations for Elektrokomplekt LLP (ekt.kz).

## Forecasting: what we use and what the research found

**Operational choice: uncapped weekly EWMA, selected through `forecast_method: "auto"`.**
There is no universally best model in the experiments. EWMA is our explainable
baseline for purchasing; full-feature Tweedie LightGBM is the strongest ML challenger,
not a validated replacement across all suppliers and forecast periods.

The calculation API and imported-source preparation support automatic forecasting:

- With at least 56 declared history days, use the last eight weeks with weights
  `0.72 ** floor(age_in_days / 7)`, without automatically capping large sales.
- With shorter history, or explicit stockout compensation, use the existing
  historical-mean policy. An explicitly entered daily-demand assumption takes precedence.
- Forecast the user's inclusive start/end dates, then apply scenario factors,
  buffer, eligible stock/transit, unit conversion, minimum order and order multiples.
  Supplier lead time controls arrival timing; it is not added to a custom date range.
- Return `forecast_method` with each result. Existing API callers that omit the
  selector retain `history_mean`; new source-prepared scenarios opt into `auto`.
  Bulk exclusion and stockout compensation remain off unless explicitly requested.

Seven registered experiments share 65,754 forecast keys. The table compares
2026 retrospective WAPE (%; lower is better) with the development-selected benchmark,
which is **not the same as the uncapped application EWMA**.

| Supplier / unit / horizon | Selected benchmark | Full Tweedie | Finding |
| --- | ---: | ---: | --- |
| IEK / meters / 28 days | 64.977 | 58.803 | Strong ML lead; Tweedie lost in 2025 development |
| IEK / packs / 28 days | 42.567 | 46.293 | Capped baseline has lower error, with more underforecasting |
| IEK / pieces / 28 days | 40.245 | 40.152 | Small difference; no convincing general replacement |
| Systeme / pieces / 28 days | 42.760 | 42.430 | Small difference; monitor bias as well as error |

The narrower **IEK packs, 7-day, Tweedie without weekly-lag features** candidate
scored 66.990 vs 81.969 retrospectively and 51.634 vs 51.879 in development.
Automatic cleaning worsened every 28-day baseline group. Combined raw/clean/bulk
features, SBA and TSB did not establish a universal improvement. Keep raw demand
and validate challengers at the actual purchasing horizon before promotion.

These are forecasts of recorded positive sales, not unconstrained demand or proven
inventory savings. WAPE is not an accuracy percentage. July–December 2025 was used
for selection; January–August 2026 has already informed multiple experiments and
is retrospective, not a fresh test. Arbitrary custom horizons are extrapolations;
LightGBM and calibrated safety buffers are not connected as automatic defaults.

Evidence: [registered comparison](experiments/INDEX.md),
[baseline findings](docs/DEMAND_RESULTS.md), [ablation findings](docs/LIGHTGBM_ABLATION.md),
[cleaning findings](docs/DEMAND_CLEANING_RESULTS.md),
[combined features](docs/COMBINED_FORECAST_RESULTS.md).
Implementation: [calculation policy](backend/src/replenishment/planning/calculator.py),
[custom-period contract](docs/CUSTOM_FORECAST_PERIOD.md).

Промышленный базовый выбор — недельный EWMA без ограничения пиков; при короткой
истории используется среднее. Tweedie — перспективный кандидат для отдельных
групп и горизонтов, а не доказанный общий победитель. Собственные даты передаются
в расчёт, а использованный метод возвращается для каждой позиции.
Built within 3 hours: an end-to-end supplier order recommendation prototype with Excel ingestion, demand forecasting, order drafts, CSV export and a React interface.

## Deployment

Requires GNU Make, uv, Node.js 22+ and PostgreSQL 17. On the server, from the
repository root, set a connection URL for an empty application database:

```sh
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/replenishment'
make install migrate import-data calculate build
cd backend
uv run --frozen uvicorn replenishment.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Keep the API running with a service manager (e.g. systemd). Configure an HTTPS
web server to serve `frontend/dist` and proxy `/api/*` to `127.0.0.1:8000`,
preserving the path. Use deployment credentials; the bundled Compose starts
only a development database. For a local demo, use `make dev-setup`, then
`make dev-api` and `make dev-ui` in separate terminals.

## Development tasks

Run `make help` from the repository root. Requires GNU Make, uv, Node.js 22+;
Docker is needed for database tasks. On Windows use a POSIX shell with Make,
or the native PowerShell commands in [backend setup](backend/README.md).

```sh
make dev-setup       # Install dependencies, start DB, migrate, import workbooks
make dev-api         # API with reload; keep running
make dev-ui          # Frontend; run in a second terminal
make check           # Lint, DB-free tests, frontend build, registry guards
make test-eval       # Evaluation contracts and tests only; no DB
make evaluate        # Evaluate monthly three-period forecasts on original documents
make calculate       # Persist pinned forecast/order drafts in PostgreSQL
```

`make install` installs dependencies without starting Docker. `make test` runs
backend and frontend tests; `make test-postgres` requires an explicitly set
`TEST_DATABASE_URL` pointing to a dedicated empty `*_test` database (creation
instructions in the backend setup). `DATABASE_URL` defaults to local Compose;
override it through the environment when needed. `make db-stop` preserves data.

The main application implements the **v2 forecast-first contract**. Development origins are
June–September 2025; the January–May 2026 comparison is retrospective.
`make test-eval-strict` and `make evaluate-strict` exercise the implemented calculation contract. Reports use new immutable
directories under `artifacts/inventory-evaluation/`. See the
[evaluation protocol](docs/INVENTORY_EVALUATION.md). Forecast research retains its
separate [Python 3.10 environment](experiments/README.md).

Start with the [project documentation](docs/README.md), then read the
[project context](docs/PROJECT_CONTEXT.md) and [data guide](docs/DATA_GUIDE.md).
The original brief and all 12 extracted supplier workbooks are included in `docs/`.

Current state: source documentation, audit checks, Excel ingestion, read API and React source tables,
plus backend purchasing calculations, saved scenario revisions, approval and CSV export are implemented.
The new Elektrokomplekt purchasing workspace connects imported products, calculation, saved revisions, approval and CSV export to the backend. Explicitly labelled synthetic examples remain available.
Calculable v0 recommendations are explicitly labelled scenarios. See the
[current verification and demo walkthrough](docs/DELIVERY_VERIFICATION.md).
Start with [purchasing backend RU/EN](backend/PLANNING.md) and the [parallel execution plan](docs/PARALLEL_DELIVERY_PLAN.md).
See [backend setup RU/EN](backend/README.md), [architecture](backend/ARCHITECTURE.md)
and [Excel-to-database mapping](docs/DATA_MODEL.md).

Текущее состояние: импорт Excel, API чтения и React-таблицы, backend расчёта закупок, сохранение версий,
утверждение и CSV. Новое рабочее место Электрокомплект подключено к backend: импортированные товары, расчёт, версии сценариев, утверждение и CSV. Учебные примеры явно обозначены.
Актуальная проверка и сценарий показа: [RU/EN](docs/DELIVERY_VERIFICATION.md).
Current state: source documentation, locked audit checks, modular SQLAlchemy models, PostgreSQL migration,
Excel ingestion, read API and React tables are implemented. The forecast-first calculation, supplier draft persistence and CSV export are the main backend path.
See [backend setup RU/EN](backend/README.md), [architecture](backend/ARCHITECTURE.md)
and [Excel-to-database mapping](docs/DATA_MODEL.md).

Текущее состояние: документация, проверки аудита, модульные модели SQLAlchemy, миграция PostgreSQL,
импорт Excel, API чтения и React-таблицы. Основной forecast-first расчёт, сохранение черновиков и CSV-экспорт доступны через CLI.

Запуск / Run: [backend + import](backend/README.md), [frontend](frontend/README.md).
API: [contract RU/EN](backend/API.md). UI scope: [requirements RU/EN](docs/FRONTEND_REQUIREMENTS.md).

Проверка импорта / Import validation: [independent data-quality report](docs/reports/data-quality.md)
and [reproduction command](backend/IMPORTING.md#независимая-сверка--independent-reconciliation).

Согласованные требования к стеку, запуску через F5 и Docker, сценариям и демонстрации:
[план сдачи RU/EN](docs/DELIVERY_PLAN.md). Инструкции запуска: [Docker и F5](docs/STARTUP.md).

Approved stack, F5/Docker startup, scenarios and demonstration requirements:
[delivery plan RU/EN](docs/DELIVERY_PLAN.md). See [Docker and F5 startup](docs/STARTUP.md); Docker was verified, F5 configuration has not been launched in VS Code.
