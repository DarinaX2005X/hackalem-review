# Граф денег

Локальное приложение для исследования транзакционной сети: роли, кластеры, приоритеты, граф и объяснения. Роли и score — аналитические гипотезы, не вероятности виновности; ограничения исходной выборки сохраняются в карточках.

Полный расчёт обрабатывает предоставленные **2248 узлов, 3119 направленных связей и 4840 переводов**. Реализованы правила с численными основаниями, кластеры Louvain, признаки активности по датам, API, React-интерфейс и три CSV задания. AI необязателен: пользователь подтвердил работу с API-ключами; автоматические проверки провайдера используют имитацию. [Методология](docs/methodology.md), [проверки реального расчёта](docs/real-data-verification.md).

## Основной запуск: реальные данные в Docker

Нужен Docker Desktop с Linux-контейнерами на Windows/macOS либо Docker Engine с Compose v2+ на Linux. Отдельная установка Python и Node.js не нужна. Все команды выполнять из корня этого репозитория, где находятся `compose.yaml` и `Dockerfile`.

Разместить три предоставленных файла в `data/raw/`:

```text
data/raw/nodes.parquet
data/raw/edges.parquet
data/raw/transactions.parquet
```

Запустить:

```sh
docker compose -f compose.yaml -f compose.real.yaml up --build --wait --wait-timeout 90
```

Открыть **[http://localhost:8000](http://localhost:8000)**. Если в локальном `.env` задан `APP_PORT`, использовать этот порт. При каждом старте выполняется полный расчёт из Parquet; ошибка входа останавливает запуск. Каталог входа подключён только для чтения, результаты сохраняются в Docker volume. Редактор искусственных записей в этом режиме отключён. Health возвращает `data_ready=true` и `run_id` с префиксом `real-`.

```sh
# Проверка интерфейса, API и всех выгрузок; внешние AI-вызовы не выполняются
docker compose -f compose.yaml -f compose.real.yaml exec -T app python scripts/real_smoke.py --base-url http://127.0.0.1:8000
# Логи и остановка; данные и volume сохраняются
docker compose -f compose.yaml -f compose.real.yaml logs --tail=100 app
docker compose -f compose.yaml -f compose.real.yaml down
```

Для другого каталога исходных данных задать `AML_DATA_DIR` в локальном `.env`. Настройка AI также находится только в `.env`: `OPENAI_API_KEY`, `AI_MODEL` и при необходимости `AI_PROVIDER=openai`. Создать `.env` по образцу `.env.example`, если его ещё нет; существующий файл не перезаписывать. Реальные ключи не вписывать в `.env.example`, Compose или Dockerfile. Без ключа и модели работают локальные объяснения. Подробности: [Docker](docs/docker.md), [AI](docs/ai.md).

Явные `-f` выбирают нужный режим даже при старом `COMPOSE_FILE` в окружении. Одиночный `compose.yaml` по-прежнему служит для искусственных фикстур; для реальных данных нужен `compose.real.yaml` или готовые артефакты через `compose.artifacts.yaml`.

## Запуск без Docker

Нужны Python 3.12+ и Node.js 22.12+. Исходные три Parquet находятся в `data/raw/`. На macOS/Linux:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python -m backend --data-dir data/raw
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
npm --prefix frontend ci
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m backend --data-dir data/raw
```

Открыть [http://127.0.0.1:8000](http://127.0.0.1:8000). При занятом порте добавить, например, `--port 8003` и открыть именно этот адрес. Процесс загружает один снимок расчёта; для другого набора нужно перезапустить сервер. API: [health](http://127.0.0.1:8000/api/health), [Swagger](http://127.0.0.1:8000/docs). Оформление Swagger использует CDN; само приложение и `contracts/openapi.json` доступны локально.

## Полный расчёт и CSV задания

Только расчёт, без веб-сервера (в Windows заменить `.venv/bin/python` на `.venv\Scripts\python.exe`):

```sh
.venv/bin/python -m backend.app.analytics.cli run --input-dir data/raw --output-dir artifacts --rules config/rules.json --mapping config/input_mapping.json
```

Команда сообщает `run_dir`, фактические количества и полное время. Результат — `artifacts/real-<hash>/`. Повторный расчёт выполняется заново, проверяет содержимое существующего неизменяемого результата и не переписывает его. В Docker тот же каталог находится внутри volume по пути `/app/artifacts/real-<hash>/`.

В меню «Выгрузки» доступны:

| Файл | Содержимое |
|---|---|
| `nodes_roles.csv` | Все 2248 узлов, роль и score, кластер, приоритет, численные основания и все базовые метрики starter, включая взвешенный направленный PageRank |
| `clusters.csv` | Строка на кластер: число узлов и seed, внутренняя сумма, ведущие gid и гипотеза назначения |
| `top_nodes.csv` | Первые 20 узлов по убыванию приоритета с объяснениями |

Обязательные столбцы starter сохранены. CSV использует score 0–1; интерфейс и внутренние файлы `roles.csv`/`priorities.csv` — 0–100. `NA` явно обозначает неопределённое отношение при нулевом входе или неизвестный признак и не заменяет их нулём. Все строковые gid, включая ведущие нули, сохраняются. Правила и формулы описаны в [методологии](docs/methodology.md).

Проверка готового каталога (подставить `run_dir` из вывода расчёта):

```sh
.venv/bin/python scripts/verify_task_exports.py "artifacts/real-<hash>"
```

Артефакты также содержат `temporal.json`, `diagnostics.json`, точные правила и mapping, контрольные суммы и паспорт запуска. Исходные Parquet не переписываются; `data/` и `artifacts/` исключены из Git. Расчёт выполняется локально без внешнего AI. Все 19 изолятов сохранены: полный граф имеет 35 компонент, из них 16 с рёбрами.

## Загрузка уже рассчитанного набора

Для Python-сервера:

```sh
.venv/bin/python -m backend --run-dir "artifacts/real-<hash>"
```

Для Docker задать в локальном `.env` путь `AML_ARTIFACTS_DIR=./artifacts/real-<hash>`, затем:

```sh
docker compose -f compose.yaml -f compose.artifacts.yaml up --build --wait --wait-timeout 90
```

В этом режиме готовый каталог подключён только для чтения; новый расчёт не запускается. Сервер проверяет `manifest.json` со статусом `complete`, все перечисленные файлы, модели, ссылки, количества, SHA256 правил и соответствие CSV карточкам. Ошибка загрузки даёт `data_ready=false` и HTTP 503; фикстуры не подставляются. Для другого результата указать новый каталог и повторить `up`.

Можно задать `AML_RUN_DIR` в `.env` и запустить `python -m uvicorn backend.app.main:app`. Существующее окружение имеет приоритет над `.env`. Источники `AML_FIXTURE_MODE`, `AML_DEMO_MODE` и `AML_RUN_DIR` взаимно исключаются; явный CLI-флаг источника заменяет настройки источника из окружения.

## Отдельные искусственные режимы

Для разработки без предоставленных данных:

```sh
# Четыре контрактных примера
.venv/bin/python -m backend --fixtures
# Редактируемое синтетическое демо
.venv/bin/python -m backend --demo
# Контрактные фикстуры в Docker
docker compose -f compose.yaml up --build --wait --wait-timeout 90
```

Набор `fixture-contract-v1` содержит `0007`, `7`, `0012` и `isolated`; интерфейс явно отмечает искусственные данные. Эти роли и приоритеты — примеры формата. Отдельные frontend-команды `npm run fixtures` и `npm run dev:fixtures` также запускают только искусственные данные. Обычный `npm run dev` работает с backend по адресу, заданному в `API_PROXY_TARGET`; по умолчанию это порт 8000.

## API и интеграция команды

| Маршрут | Назначение |
|---|---|
| `GET /api/health` | Готовность текущего запуска |
| `GET /api/node?gid=…` | Точная карточка строкового gid, включая `/`, Unicode и сегменты `.`/`..` |
| `GET /api/nodes/{gid}` | Совместимый маршрут карточки через путь; поддерживает `/` внутри gid |
| `GET /api/priorities?limit=20&offset=0` | Приоритеты, score убывает, затем gid возрастает |
| `GET /api/clusters` | Список кластеров |
| `GET /api/cluster?cluster_id=…` | Точная карточка кластера с непрозрачным строковым ID |
| `GET /api/clusters/{cluster_id}` | Совместимый маршрут карточки через путь; поддерживает `/` внутри ID |
| `GET /api/graph` | Ровно один `gid`, `cluster_id` или `component_id`; radius 1/2, limit 1–300 |
| `GET /api/exports/{name}` | Логическое имя обязательного файла, `manifest` или точный ключ из `manifest.files` |
| `POST /api/ai/explain` | Объяснение выбранного узла/кластера или локальная справка |
| `POST /api/ai/investigate` | Вопрос по выбранному узлу/кластеру или локальная справка |

Граф обходит связи в обе стороны, сохраняет направление рёбер и выбранный узел. Усечение сортируется по расстоянию, priority_score и gid; ответ сообщает `truncated`, `total_nodes`, `shown_nodes`. Метрики карточек берутся из полного расчёта. `null` сохраняется отдельно от нуля, денежные строки не преобразуются в float.

Для точного поиска frontend использует query-маршруты `/api/node` и `/api/cluster` с кодированием параметров через `URLSearchParams`. Это сохраняет ID с точками и разделителями без нормализации сегментов пути браузером. Пустой или отсутствующий ID даёт 422, неизвестный — 404.

Все результаты связаны `contract_version="1.0"` и `run_id`. Ошибки имеют форму `{error:{code,message},run_id}`: 404 — неизвестный id/экспорт, 422 — параметры, 503 — нет завершённого расчёта, 409 — устаревший run_id AI-запроса. Заголовки API: `X-Data-Source`, `X-Contract-Version`, `X-Run-Id`, `Cache-Control: no-store`. В `X-Run-Id` специальные и Unicode-символы percent-encoded; JSON содержит исходную строку без изменения.

- **A:** `backend.app.analytics.pipeline.run_pipeline` выполняет чтение, аудит, роли, кластеры, приоритеты и экспорт. Модели — в `backend/app/contracts.py`; `ResultStore.check_concentration` вызывает общий расчёт концентрации. Зависимости аналитики включены в `requirements.lock` и обычную установку проекта.
- **C:** [снимок OpenAPI](contracts/openapi.json), [общие примеры](tests/fixtures/contract-v1/) и [запуск frontend](frontend/README.md). Dev proxy: `/api` → `http://127.0.0.1:8000`. Разрешён CORS-origin `http://localhost:5173`; другой локальный origin задаётся `AML_FRONTEND_ORIGIN`. После сборки `frontend/dist/index.html` FastAPI автоматически раздаёт этот каталог и SPA-маршруты. Для отдельного frontend dev-сервера адрес backend задаётся через `API_PROXY_TARGET` в `frontend/.env.local`; при реальном backend на порту 8003 нужно `API_PROXY_TARGET=http://127.0.0.1:8003`. Собранный интерфейс Docker обращается к API того же приложения.
- **D:** подключены async-функции `backend.app.ai.service.explain(request, store)` и `investigate(request, store)`, возвращающие `AIResponse`. HTTP-слой проверяет существование target и текущий run_id до вызова и сохраняет коды ошибок запросов D. Доступны методы Store из контракта, типы `ExplainRequest`, `InvestigateRequest`, `AIResponse`.

Без `OPENAI_API_KEY` и `AI_MODEL` оба AI-маршрута возвращают `status="fallback"` с локальными объяснениями, основаниями и ограничениями. Для провайдера используется `AI_PROVIDER=openai`; модель задаётся конфигурацией. Общий срок — `AI_TIMEOUT_SECONDS` (не более 30), бюджет функций — `AI_MAX_TOOL_CALLS` (0–3). D проверяет ссылки на основания и числовые утверждения; сбой даёт локальную справку с уже завершёнными проверками. Неверный формат ответа или несовместимый run_id на границе HTTP дают локальную справку B. Вопрос длиннее 4000 символов получает 422. Подробности и пределы проверки достоверности — в [инструкции AI](docs/ai.md). Работу живого AI через свои API-ключи пользователь подтвердил 23.09.2026. Автоматические проверки используют имитацию провайдера; отдельный протокол с моделью и задержкой живого API не записывался.

## Проверки

Из корня проекта на macOS/Linux:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
.venv/bin/python -m backend.app.openapi --check
npm --prefix frontend test
npm --prefix frontend run build
```

В Windows использовать `.venv\Scripts\python.exe`. API/AI-тесты используют искусственные данные и имитацию провайдера, без платных запросов. Полные команды Docker и проверки реального HTTP-сервера — в [инструкции Docker](docs/docker.md). Независимый `verify_task_exports.py` проверяет CSV, числовые значения, кластеры, порядок топа и стационарное уравнение PageRank.

Фактические прогоны, время полного расчёта и границы проверки записаны в [отчёте реального запуска](docs/real-data-verification.md). Ранние отчёты на 102/206/233 теста относятся к этапам разработки API; их нельзя принимать за количество проверок текущей версии. Есть предупреждение устаревшего alias Starlette/AnyIO, не влияющее на выполненные проверки.

Рост до порядка миллиона узлов требует пакетной агрегации, компактного хранилища графа и выдачи подграфов по запросу. Сейчас Store держит этот небольшой набор и выгрузки в памяти; масштаб до миллиона узлов не измерялся.

## Контекст и планы

Комплект сдачи и его проверка описаны в [инструкции комплекта](docs/submission.md).
Для защиты подготовлен [сценарий демо на 3–5 минут](docs/demo-script.md).
Архив собирается локально из чистой закоммиченной версии:

```sh
.venv/bin/python scripts/package_submission.py --run-dir "artifacts/<run_id>" --verification data/audit/submission-csv-verification.json
```

Протокол `--verification` должен относиться к этому же расчёту и содержать
результат `verify_task_exports.py`; в текущем комплекте он дополнен итогами
Docker и воспроизводимости. Архивы находятся в игнорируемом `submission/`.

- [Архитектура](docs/superpowers/specs/2026-09-23-money-graph-design.md)
- [Контракт данных и API v1](docs/contracts/money-graph-v1.md)
- [Общий план команды](docs/superpowers/plans/2026-09-23-money-graph-parallel.md)
- [A — аналитика](docs/superpowers/plans/2026-09-23-money-graph-a-analytics.md)
- [B — backend](docs/superpowers/plans/2026-09-23-money-graph-b-backend.md)
- [C — frontend](docs/superpowers/plans/2026-09-23-money-graph-c-frontend.md)
- [D — AI](docs/superpowers/plans/2026-09-23-money-graph-d-ai.md)
