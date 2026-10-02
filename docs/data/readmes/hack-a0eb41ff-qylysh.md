# MoneyGraph

**[Русский](#ru) · [English](#en)**

---

<a id="ru"></a>

## MoneyGraph — анализ сети переводов для ПОД/ФТ

MoneyGraph восстанавливает структуру группы клиентов по сети внутрибанковских переводов. Система строит направленный граф денежных потоков. Каждому клиенту она присваивает роль в этой структуре: координатор, сборщик, распределитель, транзит, конечный получатель или периферийный участник. По этим ролям формируется очередь клиентов на проверку для аналитика.

Проект сделан для хакатона **HackAlem AI** по задаче «Граф денег: восстановление финансовой структуры организованной группы по транзакционной сети».

> Роли и оценки описывают положение клиента в сети. Они помогают аналитику решить, кого смотреть первым, но **не являются обвинением и не означают вероятность преступления**.

### Как запустить проект

Проект состоит из двух частей: **бэкенд** (Python, считает аналитику и отдаёт API) и **фронтенд** (React, интерфейс в браузере). Их запускают в двух отдельных терминалах.

#### Что нужно установить заранее

| Программа | Версия | Проверить командой |
|---|---|---|
| Git | любая | `git --version` |
| Python | 3.11 или новее | `python --version` |
| Node.js | 20.19+ или 22.12+ (на Node 18 не запустится) | `node --version` |

#### Шаг 1. Скачать проект

```bash
git clone https://github.com/BAITC-Hacks/hack-a0eb41ff-qylysh.git
cd hack-a0eb41ff-qylysh
```

#### Шаг 2. Запустить бэкенд (терминал 1)

```bash
cd backend

# создать и активировать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# установить зависимости
python -m pip install -r requirements.txt

# посчитать аналитику и сохранить снимок (занимает несколько секунд)
python -m app.analytics.run_pipeline --data-dir ../docs/data --database analysis.db --out-dir out

# запустить API
uvicorn app.main:app --reload
```

Оставьте этот терминал открытым. API работает на `http://localhost:8000`.

Проверка: откройте `http://localhost:8000/health`. Должен вернуться ответ `{"status":"ok", ...}`. Документация API открывается по адресу `http://localhost:8000/docs`.

#### Шаг 3. Запустить фронтенд (терминал 2)

Откройте новый терминал в папке проекта:

```bash
cd frontend
npm install
npm run dev
```

#### Шаг 4. Открыть в браузере

Перейдите по адресу, который выведет Vite, обычно это **http://localhost:5173**. На странице «Обзор» должны появиться 2 248 клиентов и 3 119 связей.

Язык интерфейса переключается кнопками **RU / EN** в правом верхнем углу.

#### Запуск без бэкенда (демо-режим)

Если нужно просто посмотреть интерфейс, бэкенд можно не запускать. Создайте файл `frontend/.env` с такой строкой:

```
VITE_USE_MOCK_API=true
```

Затем выполните шаг 3. Интерфейс будет работать на встроенных демонстрационных данных, сверху появится пометка «ДЕМОНСТРАЦИОННЫЕ ДАННЫЕ».

#### Если что-то не работает

| Проблема | Решение |
|---|---|
| `npm run dev` падает с ошибкой про версию Node | Обновите Node.js до 20.19+ или 22.12+ |
| API отвечает ошибкой 503 | Не построен снимок. Выполните команду `run_pipeline` из шага 2 |
| Страницы пишут «Не удалось загрузить данные» | Проверьте, что бэкенд запущен и `http://localhost:8000/health` открывается |
| Ошибка CORS в консоли браузера | Фронтенд открыт не на порту 5173. Добавьте его адрес в `MONEYGRAPH_CORS_ORIGINS` в `backend/.env` |
| `.venv\Scripts\activate` не работает в PowerShell | Выполните `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` и повторите |

### Возможности

- **Обзор.** Общая статистика набора данных, распределение ролей, самые приоритетные клиенты и кластеры.
- **Сеть.** Интерактивный граф вокруг выбранного клиента (GID) или кластера. Стрелки показывают направление переводов, толщина линии показывает сумму, крупные суммы выделены цветом. По клику на узел или связь открываются подробности.
- **Приоритеты.** Рейтинг всех клиентов с поиском по GID, фильтром по роли, пагинацией и карточкой клиента с обоснованием оценки.
- **Кластеры.** Сообщества, найденные в сети, с внутренним оборотом и гипотезой для проверки.
- **Методология и ограничения данных.** Как считаются роли и оценки и какие выводы из данных делать нельзя.
- **Два языка.** Интерфейс переключается между русским и английским. Выбор запоминается в браузере.

### Как это работает

```
docs/data/*.parquet ──► pipeline (backend) ──► analysis.db + CSV ──► FastAPI ──► React-интерфейс
```

1. **Проверка данных.** Проверяются колонки, типы, пропуски, уникальность GID, ссылки рёбер на существующие узлы и совпадение агрегатов рёбер с транзакциями.
2. **Граф.** Строится направленный граф NetworkX: узел — клиент, ребро — все переводы от одного клиента другому за период.
3. **Признаки.** Для каждого клиента считаются входящие и исходящие связи, суммы, PageRank, доля «пропущенных через себя» средств (pass-through), число стартовых клиентов, от которых до него можно дойти, и перцентили этих величин.
4. **Роли.** Объяснимые правила, которые проверяются по порядку. Первое подходящее правило задаёт роль:

   | Роль | Правило |
   |---|---|
   | Координатор | Высокий PageRank и достижим от многих стартовых клиентов |
   | Сборщик | Много входящих связей и крупный входящий объём |
   | Распределитель | Много исходящих связей и крупный исходящий объём |
   | Транзит | Есть и вход, и выход, pass-through от 0,8 до 1,2. Стартовые клиенты сюда не попадают |
   | Конечный | Есть входящие переводы, нет исходящих, глубина меньше 4 |
   | Периферийный | Все остальные |

5. **Кластеры.** Сообщества находятся алгоритмом Louvain на неориентированной проекции графа, где вес ребра равен сумме переводов.
6. **Приоритет.** `priority_score` от 0 до 1 — взвешенная сумма:

   | Сигнал | Вес |
   |---|---|
   | PageRank (перцентиль) | 0,25 |
   | Сила соответствия роли (`role_score`) | 0,25 |
   | Число стартовых клиентов, от которых достижим узел (перцентиль) | 0,20 |
   | Объём переводов (перцентиль) | 0,20 |
   | Число связей (перцентиль) | 0,10 |

7. **Снимок.** Результаты записываются в SQLite (`analysis.db`) и CSV. API только читает этот снимок, поэтому отвечает быстро и одинаково при каждом запросе.

### Данные

Внутрибанковские переводы за июль 2026 года. Граф построен от 81 стартового клиента по исходящим переводам на глубину до 4 шагов. Учитываются переводы от 5 000 ₸.

| | Количество |
|---|---|
| Клиенты (узлы) | 2 248 |
| Связи (пары отправитель → получатель) | 3 119 |
| Транзакции | 4 840 |
| Стартовые клиенты | 81 |

Файлы лежат в [docs/data](docs/data), описание набора — в [docs/README (1).md](<docs/README (1).md>).

GID в данных 18-значные, это больше, чем JavaScript может точно хранить в числе. Поэтому API и фронтенд передают GID строками, а внутри Parquet и SQLite они хранятся как int64.

### Настройки

**Фронтенд** (`frontend/.env`, пример в [.env.example](frontend/.env.example)):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Адрес API |
| `VITE_USE_MOCK_API` | `false` | `true` — работать на демо-данных без бэкенда |
| `VITE_MOCK_SCENARIO` | `success` | Демо-сценарий: `success`, `empty` или `error` |

**Бэкенд** (`backend/.env`, пример в [.env.example](backend/.env.example)). Все переменные начинаются с `MONEYGRAPH_`. Самые важные:

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `MONEYGRAPH_DATABASE_PATH` | `analysis.db` | Путь к снимку SQLite |
| `MONEYGRAPH_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | С каких адресов фронтенду разрешено обращаться к API |

### API

Все маршруты, кроме `/health`, начинаются с `/api/v1`. Ответы в JSON с полями в camelCase.

| Метод | Назначение |
|---|---|
| `GET /health` | Проверка, что сервис работает |
| `GET /summary` | Сводка: счётчики, распределение ролей, топ клиентов и кластеров |
| `GET /nodes` | Список клиентов. Фильтры: `role`, `cluster`, `minPriority`, `isSeed`, `search`, `page`, `pageSize` |
| `GET /nodes/{gid}` | Карточка клиента |
| `GET /nodes/{gid}/graph` | Локальный граф вокруг клиента |
| `GET /top-nodes` | Топ клиентов по приоритету |
| `GET /clusters` | Список кластеров |
| `GET /clusters/{cluster_id}` | Карточка кластера |
| `GET /clusters/{cluster_id}/graph` | Граф кластера |

### Тесты и проверки

```bash
# бэкенд, из backend/
pytest

# отдельные проверки этапов pipeline
python -m app.analytics.check_data --data-dir ../docs/data
python -m app.analytics.check_graph --data-dir ../docs/data
python -m app.analytics.check_features --data-dir ../docs/data
python -m app.analytics.check_roles --data-dir ../docs/data

# фронтенд, из frontend/: проверка типов и production-сборка
npm run build
```

### Стек

| | |
|---|---|
| Бэкенд | Python, FastAPI, Pydantic v2, pandas, pyarrow, NetworkX, SciPy, SQLite, pytest |
| Фронтенд | React 19, TypeScript, Vite, React Router, Cytoscape.js, Sass, lucide-react |

### Структура репозитория

```
backend/
  app/analytics/     pipeline: загрузка, проверка, граф, признаки, роли, кластеры, рейтинг
  app/api/           маршруты FastAPI
  app/repositories/  чтение снимка из SQLite
  app/schemas/       модели ответов API
  tests/             тесты pytest
frontend/
  src/pages/         страницы: Обзор, Сеть, Приоритеты, Кластеры, Методология, Ограничения
  src/components/    общие компоненты и каркас страницы
  src/api/           клиент API и демо-данные
  src/i18n/          переводы RU / EN
docs/
  data/              исходные Parquet-файлы
  *.md               планы разработки, контракт API, статус интеграции
```

### Ограничения

- Данные охватывают только июль 2026 года и только переводы от 5 000 ₸.
- Граф строится по исходящим переводам от стартовых клиентов, поэтому входящие переводы к ним видны не полностью.
- Граф обрывается на глубине 4. Если у узла на границе нет исходящих связей, это не значит, что деньги там остановились.
- В данных нет подтверждённых меток нарушений, поэтому качество ролей и оценок нельзя измерить по «правильным ответам».
- Весь pipeline работает в памяти. Для сети в миллионы узлов его нужно переделать на пакетную обработку. Подробнее — в [backend/README.md](backend/README.md#scaling-beyond-the-hackathon-dataset).

### Подробная документация

- [backend/README.md](backend/README.md) — все команды бэкенда, правила ролей, проверки данных
- [frontend/README.md](frontend/README.md) — запуск и настройка интерфейса
- [docs/INTEGRATION_PLAN.md](docs/INTEGRATION_PLAN.md) — контракт API между фронтендом и бэкендом
- [docs/INTEGRATION_STATUS.md](docs/INTEGRATION_STATUS.md) — результаты проверок интеграции
- [docs/BACKEND_PLAN.md](docs/BACKEND_PLAN.md), [docs/FRONTEND_PLAN.md](docs/FRONTEND_PLAN.md) — пошаговые планы разработки

---

<a id="en"></a>

## MoneyGraph — transfer network analysis for AML

MoneyGraph reconstructs the structure of a group of clients from a network of intra-bank transfers. It builds a directed money-flow graph and assigns each client a structural role: coordinator, consolidator, distributor, transit, terminal, or peripheral. These roles feed a review queue that tells an analyst which clients to look at first.

The project was built for the **HackAlem AI** hackathon, for the task "Money graph: reconstructing the financial structure of an organised group from a transaction network".

> Roles and scores describe a client's position in the network. They help an analyst decide what to review first. They **are not accusations and are not a probability of crime**.

### How to run the project

The project has two parts: the **backend** (Python, computes the analytics and serves the API) and the **frontend** (React, the browser interface). Run them in two separate terminals.

#### Prerequisites

| Tool | Version | Check with |
|---|---|---|
| Git | any | `git --version` |
| Python | 3.11 or newer | `python --version` |
| Node.js | 20.19+ or 22.12+ (Node 18 will not work) | `node --version` |

#### Step 1. Get the code

```bash
git clone https://github.com/BAITC-Hacks/hack-a0eb41ff-qylysh.git
cd hack-a0eb41ff-qylysh
```

#### Step 2. Start the backend (terminal 1)

```bash
cd backend

# create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# install dependencies
python -m pip install -r requirements.txt

# compute the analytics and save the snapshot (takes a few seconds)
python -m app.analytics.run_pipeline --data-dir ../docs/data --database analysis.db --out-dir out

# start the API
uvicorn app.main:app --reload
```

Keep this terminal open. The API runs at `http://localhost:8000`.

To check it, open `http://localhost:8000/health`. It should return `{"status":"ok", ...}`. Interactive API docs are at `http://localhost:8000/docs`.

#### Step 3. Start the frontend (terminal 2)

Open a new terminal in the project folder:

```bash
cd frontend
npm install
npm run dev
```

#### Step 4. Open it in the browser

Go to the URL Vite prints, usually **http://localhost:5173**. The Overview page should show 2,248 clients and 3,119 relations.

Switch the interface language with the **RU / EN** buttons in the top-right corner.

#### Running without the backend (demo mode)

To just look at the interface, you can skip the backend. Create `frontend/.env` with this line:

```
VITE_USE_MOCK_API=true
```

Then run step 3. The interface uses built-in demonstration data and shows a "DEMONSTRATION DATA" label at the top.

#### Troubleshooting

| Problem | Fix |
|---|---|
| `npm run dev` fails with a Node version error | Upgrade Node.js to 20.19+ or 22.12+ |
| The API returns 503 | The snapshot is missing. Run the `run_pipeline` command from step 2 |
| Pages show "Unable to load data" | Make sure the backend is running and `http://localhost:8000/health` opens |
| CORS error in the browser console | The frontend is not on port 5173. Add its URL to `MONEYGRAPH_CORS_ORIGINS` in `backend/.env` |
| `.venv\Scripts\activate` is blocked in PowerShell | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and try again |

### Features

- **Overview.** Dataset totals, role distribution, top-priority clients and clusters.
- **Network.** An interactive graph around a selected client (GID) or cluster. Arrows show transfer direction, line width shows the amount, and large amounts are highlighted. Click a node or a relation to see details.
- **Priority.** A ranking of all clients with GID search, role filter, pagination, and a client card that explains the score.
- **Clusters.** Communities found in the network, with internal volume and a hypothesis to check.
- **Methodology and data limitations.** How roles and scores are computed, and which conclusions the data cannot support.
- **Two languages.** The interface switches between Russian and English. The choice is remembered in the browser.

### How it works

```
docs/data/*.parquet ──► pipeline (backend) ──► analysis.db + CSV ──► FastAPI ──► React UI
```

1. **Validation.** Checks columns, types, missing values, unique GIDs, that edges point to existing nodes, and that edge aggregates match the transactions.
2. **Graph.** Builds a directed NetworkX graph: a node is a client, an edge is all transfers from one client to another over the period.
3. **Features.** For each client: incoming and outgoing links and amounts, PageRank, pass-through (share of received money sent on), how many seed clients can reach it, and percentiles of these values.
4. **Roles.** Explainable rules checked in order. The first matching rule sets the role:

   | Role | Rule |
   |---|---|
   | Coordinator | High PageRank and reachable from many seed clients |
   | Consolidator | Many incoming links and high incoming volume |
   | Distributor | Many outgoing links and high outgoing volume |
   | Transit | Both incoming and outgoing flow, pass-through between 0.8 and 1.2. Seed clients are excluded |
   | Terminal | Incoming transfers, no outgoing ones, depth below 4 |
   | Peripheral | Everyone else |

5. **Clusters.** Communities are found with the Louvain algorithm on an undirected projection of the graph, weighted by transfer amount.
6. **Priority.** `priority_score` from 0 to 1 is a weighted sum:

   | Signal | Weight |
   |---|---|
   | PageRank (percentile) | 0.25 |
   | Role fit (`role_score`) | 0.25 |
   | Number of seed clients that reach the node (percentile) | 0.20 |
   | Transfer volume (percentile) | 0.20 |
   | Number of links (percentile) | 0.10 |

7. **Snapshot.** Results are written to SQLite (`analysis.db`) and CSV. The API only reads this snapshot, so responses are fast and identical on every request.

### Data

Intra-bank transfers for July 2026. The graph starts from 81 seed clients and follows outgoing transfers up to 4 hops. Only transfers of 5,000 KZT or more are included.

| | Count |
|---|---|
| Clients (nodes) | 2,248 |
| Relations (sender → recipient pairs) | 3,119 |
| Transactions | 4,840 |
| Seed clients | 81 |

The files are in [docs/data](docs/data). The dataset description (in Russian) is in [docs/README (1).md](<docs/README (1).md>).

GIDs in the data have 18 digits, which is more than JavaScript can store exactly as a number. The API and frontend therefore pass GIDs as strings. Parquet and SQLite keep them as int64.

### Configuration

**Frontend** (`frontend/.env`, see [.env.example](frontend/.env.example)):

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | API address |
| `VITE_USE_MOCK_API` | `false` | `true` runs on demo data without the backend |
| `VITE_MOCK_SCENARIO` | `success` | Demo scenario: `success`, `empty`, or `error` |

**Backend** (`backend/.env`, see [.env.example](backend/.env.example)). All variables start with `MONEYGRAPH_`. The main ones:

| Variable | Default | Purpose |
|---|---|---|
| `MONEYGRAPH_DATABASE_PATH` | `analysis.db` | Path to the SQLite snapshot |
| `MONEYGRAPH_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Origins allowed to call the API |

### API

All routes except `/health` start with `/api/v1`. Responses are JSON with camelCase fields.

| Route | Purpose |
|---|---|
| `GET /health` | Service health check |
| `GET /summary` | Totals, role distribution, top clients and clusters |
| `GET /nodes` | Client list. Filters: `role`, `cluster`, `minPriority`, `isSeed`, `search`, `page`, `pageSize` |
| `GET /nodes/{gid}` | Client card |
| `GET /nodes/{gid}/graph` | Local graph around a client |
| `GET /top-nodes` | Top clients by priority |
| `GET /clusters` | Cluster list |
| `GET /clusters/{cluster_id}` | Cluster card |
| `GET /clusters/{cluster_id}/graph` | Cluster graph |

### Tests and checks

```bash
# backend, from backend/
pytest

# individual pipeline stage checks
python -m app.analytics.check_data --data-dir ../docs/data
python -m app.analytics.check_graph --data-dir ../docs/data
python -m app.analytics.check_features --data-dir ../docs/data
python -m app.analytics.check_roles --data-dir ../docs/data

# frontend, from frontend/: type check and production build
npm run build
```

### Tech stack

| | |
|---|---|
| Backend | Python, FastAPI, Pydantic v2, pandas, pyarrow, NetworkX, SciPy, SQLite, pytest |
| Frontend | React 19, TypeScript, Vite, React Router, Cytoscape.js, Sass, lucide-react |

### Repository layout

```
backend/
  app/analytics/     pipeline: loading, validation, graph, features, roles, clusters, ranking
  app/api/           FastAPI routes
  app/repositories/  reading the SQLite snapshot
  app/schemas/       API response models
  tests/             pytest tests
frontend/
  src/pages/         pages: Overview, Network, Priority, Clusters, Methodology, Limitations
  src/components/    shared components and page layout
  src/api/           API client and demo data
  src/i18n/          RU / EN translations
docs/
  data/              source Parquet files
  *.md               development plans, API contract, integration status
```

### Limitations

- The data covers July 2026 only, and only transfers of 5,000 KZT or more.
- The graph follows outgoing transfers from seed clients, so incoming transfers to them may be incomplete.
- The graph stops at depth 4. A boundary node with no outgoing links does not mean the money stopped there.
- The data has no verified labels of wrongdoing, so the quality of roles and scores cannot be measured against ground truth.
- The whole pipeline runs in memory. A network with millions of nodes would need batch processing. See [backend/README.md](backend/README.md#scaling-beyond-the-hackathon-dataset).

### Further documentation

- [backend/README.md](backend/README.md) — all backend commands, role rules, data checks
- [frontend/README.md](frontend/README.md) — running and configuring the interface
- [docs/INTEGRATION_PLAN.md](docs/INTEGRATION_PLAN.md) — API contract between frontend and backend (in Russian)
- [docs/INTEGRATION_STATUS.md](docs/INTEGRATION_STATUS.md) — integration check results (in Russian)
- [docs/BACKEND_PLAN.md](docs/BACKEND_PLAN.md), [docs/FRONTEND_PLAN.md](docs/FRONTEND_PLAN.md) — step-by-step development plans
