# MoneyGraph AI — Граф денег

Локальный инструмент для анализа транзакционного графа и объяснимой приоритизации проверки клиентов по кейсу Freedom на HackAlem AI.

## Что делает продукт

Продукт предназначен для AML-аналитика: по переводам на четыре колена от исходных клиентов он должен определять предполагаемые роли участников и выделять группы связанных узлов. Результат — очередь проверки с числовыми объяснениями и три CSV в формате стартера. Все выводы являются аналитическими гипотезами, которые требуют проверки человеком.

**Текущий статус:** фронтенд из макета MoneyGraph подключён к FastAPI и PostgreSQL: регистрация/вход, импорт исходного ZIP, расчёт ролей и кластеров, очередь проверки, поиск, граф реальных связей и три CSV. Интерфейс доступен на `/`, документация API — на `/docs`. Защищённый CRUD, миграции, аудит данных и пересборка очереди через `POST /ranking/rebuild` сохранены.

## Запуск дашборда

После настройки `DATABASE_URL` и `JWT_SECRET_KEY` в `.env`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Откройте [MoneyGraph](http://127.0.0.1:8000/), создайте аккаунт и загрузите исходный
ZIP кнопкой «Загрузить ZIP с данными». Если база уже заполнена, данные появятся
сразу после входа. Фронтенд и API работают с одного адреса; отдельный frontend-сервер
и сборка не нужны. HTML следует открывать через сервер, а не двойным кликом по файлу.

Альтернатива для первоначальной загрузки в **пустую** базу:

```powershell
.\.venv\Scripts\python.exe -m backend.import_dataset "..\data (1).zip"
```

Импорт принимает `data/nodes.parquet`, `data/edges.parquet`, `data/transactions.parquet`
или эти файлы в корне ZIP. Проверяются уникальность GID и пар, ссылки, суммы и число
переводов. Идентичные транзакции сохраняются отдельными строками. Импорт и анализ
атомарны; повторная загрузка в непустую базу возвращает `409`. Лимиты: ZIP 30 МБ,
распакованные файлы 100 МБ, 20 000 узлов / 100 000 рёбер / 500 000 транзакций.

«Пересчитать анализ» заменяет только производные оценки, кластеры и очередь, сохраняя
исходные узлы и транзакции. После ручных изменений исходных данных через CRUD выполните
пересчёт. Карта показывает до 250 узлов с высоким приоритетом или окружение выбранного
GID; над картой указано ограничение. Поиск и пагинация очереди работают по всему набору.
GID всегда передаются строками, включая идентификаторы длиннее безопасного целого JavaScript.

### Метод анализа

Роли назначаются детерминированными графовыми правилами по числу контрагентов, суммам,
отношению исходящего объёма к входящему и достижимости от seed. Четвёртое колено без
исходящих получает `peripheral` с явным предупреждением о границе данных. Кластеры:
Louvain с `seed=42`, сумма встречных переводов используется как вес ненаправленной связи;
изолированные узлы сохраняются. Взвешенный PageRank рассчитывается на направленном графе.

Приоритет = 30% нормированного логарифма оборота + 20% степени + 20% seed-достижимости
+ 15% PageRank + 15% веса роли. На границе глубины применяется коэффициент 0,6;
изолированным узлам присваивается 0. Счёт роли — сила эвристики, а не обученная вероятность.
Это объяснимый базовый алгоритм без LLM и обученной модели; выводы требуют проверки человеком.

### API интерфейса

Все маршруты ниже требуют Bearer-токен:

| Маршрут | Назначение |
|---|---|
| `GET /dataset` | Счётчики, период, оборот, распределение ролей, дата расчёта |
| `POST /dataset/import` | Multipart-поле `file`: ZIP, импорт и автоматический анализ |
| `POST /analysis` | Пересчёт на текущих узлах и рёбрах |
| `GET /ranking/search` | `{items,total,skip,limit}`, фильтры `q`, `role`, `cluster_id`, сортировка `sort`, `direction` |
| `GET /graph` | Узлы и реальные рёбра; `gid`, `hops=1..4`, `cluster_id`, `limit=1..500` |
| `GET /graph/nodes/{gid}` | Узел и его метрики по точному строковому GID |
| `GET /exports/{filename}` | `nodes_roles.csv`, `clusters.csv`, `top_nodes.csv` в UTF-8 с BOM |

### Проверки интеграции

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
npm install
$env:DATASET_ZIP = "C:\путь\к\data.zip"
npm run test:e2e
```

Для браузерных тестов нужен установленный Chrome; для Edge задайте
`$env:BROWSER_CHANNEL = "msedge"`. Тесты создают отдельную SQLite-базу, применяют миграции,
запускают временный сервер и проверяют регистрацию, импорт, поиск, граф, сортировку,
CSV, пересчёт, мобильную ширину, экранирование текста и обработку ошибок. Рабочая
PostgreSQL не изменяется. Снимки экрана, CSV и отчёт сохраняются в `output/e2e-*/`.

## Стек технологий

- **Python 3.12** — версия в Docker и CI; backend и самостоятельный аудит данных.
- **FastAPI, Uvicorn, Pydantic 2, pydantic-settings** — HTTP-сервер, валидация и настройки из окружения и `.env`.
- **PostgreSQL, SQLAlchemy 2, psycopg 3, Alembic** — хранение сущностей и миграции схемы.
- **passlib, bcrypt, PyJWT, email-validator** — хеширование паролей, JWT access-токены и проверка email.
- **SlowAPI** — ограничения частоты регистрации и входа по IP.
- **HTML, CSS, JavaScript** — фронтенд на основе предоставленного макета, без сборки.
- **pandas, NumPy** — самостоятельный аудит данных.
- **PyArrow** — чтение Parquet.
- **NetworkX** — направленный взвешенный граф и графовые алгоритмы.
- **pytest, unittest, HTTPX/TestClient** — тесты HTTP API, сервисов, репозиториев и миграций.
- **Docker Compose, PostgreSQL 16, GitHub Actions** — воспроизводимый запуск и CI.

Backend-зависимости перечислены в `backend/requirements.txt`, тестовые — в
`backend/requirements-dev.txt`. Корневой `requirements.txt` устанавливает зависимости
backend и самостоятельного аудита `analysis/profile_data.py`, включая pandas и NumPy.
Защита API использует JWT Bearer, API-ключи не реализованы.

База данных нужна для хранения сущностей; самостоятельный аудит Parquet и health-check работают без подключения к ней. Node.js нужен только для браузерных тестов. Внешние API и LLM не требуются.

## Структура проекта

```text
moneygraph-ai/
├── README.md                    # Описание проекта и команды запуска
├── .gitignore                   # Исключения для Git
├── .env.example                 # Шаблон настроек backend, DATABASE_URL и JWT
├── alembic.ini                  # Конфигурация миграций без паролей
├── alembic/
│   ├── env.py                  # DATABASE_URL и metadata всех моделей
│   └── versions/               # Две миграции: шесть таблиц данных и users
├── analysis/                    # Существующий самостоятельный аудит данных
├── frontend/                    # index.html, styles.css и клиент API app.js
├── tests/e2e/                   # Браузерные тесты на отдельной базе
└── backend/
    ├── __init__.py              # Python-пакет backend
    ├── main.py                  # FastAPI, GET /health, CORS и подключение API
    ├── requirements.txt         # Зависимости HTTP-сервера, ORM и миграций
    ├── requirements-dev.txt     # Зависимости сервера и HTTP-тестов
    ├── api/                    # CRUD и аналитический API дашборда
    │   ├── __init__.py          # Общий роутер, собирающий модули
    │   ├── dependencies.py     # get_current_user и сервисы с сессией из get_db
    │   ├── auth.py             # Регистрация, вход по email и текущий пользователь
    │   ├── nodes.py            # CRUD узлов: /nodes/
    │   ├── edges.py            # CRUD рёбер: /edges/
    │   ├── transactions.py     # CRUD транзакций: /transactions/
    │   ├── clusters.py         # CRUD кластеров: /clusters/
    │   ├── node_assessments.py # CRUD оценок: /node-assessments/
    │   ├── ranked_nodes.py     # CRUD записей рейтинга: /ranked-nodes/
    │   ├── dataset.py          # Сводка датасета и импорт ZIP
    │   ├── analysis.py         # Пересчёт ролей, кластеров и очереди
    │   ├── ranking.py          # Чтение очереди и пересборка: /ranking, /ranking/rebuild
    │   ├── graph.py            # Карта связей и окружение узла: /graph
    │   └── exports.py          # Три CSV в контракте стартера: /exports
    ├── core/
    │   ├── __init__.py
    │   ├── config.py           # Settings: окружение → .env → defaults
    │   ├── database.py         # Engine, фабрика Session и get_db с commit/rollback
    │   ├── logging.py          # Консольные логи и middleware HTTP-запросов
    │   └── security.py         # bcrypt, create_access_token и verify_token
    ├── services/               # CRUD, бизнес-проверки и кастомные исключения
    ├── models/                 # Base, enum ролей, шесть моделей данных и User
    ├── schemas/                # Схемы шести сущностей и аутентификации
    ├── repositories/           # CRUD через SQLAlchemy Session
    └── tests/                  # Проверки миграции, репозиториев, сервисов и HTTP API
```

### HTTP API

Полная интерактивная спецификация доступна в [Swagger UI `/docs`](http://localhost:8000/docs),
альтернативное представление — `/redoc`, JSON-спецификация — `/openapi.json`.
`GET /health` возвращает `{"status":"ok"}` и проверяет HTTP-сервер; подключение к БД
этот маршрут не проверяет.

Все маршруты данных требуют заголовок `Authorization: Bearer <access_token>`,
включая чтение списков и отдельных объектов. Защищены все операции в `/nodes/`,
`/edges/`, `/transactions/`, `/clusters/`, `/node-assessments/`, `/ranked-nodes/`.
Общий роутер данных подключает `Depends(get_current_user)` также к модулям
`/dataset`, `/analysis`, `/ranking`, `/graph`, `/exports`: их обработчики
наследуют эту проверку.

### Аутентификация

| Метод и путь | Доступ | Результат |
|---|---|---|
| `POST /auth/register` | Публичный | JSON `{ "email": "analyst@example.com", "password": "…" }`; пользователь, `access_token`, `token_type: "bearer"` и `201 Created` |
| `POST /auth/login` | Публичный | Такой же JSON; `{ "access_token": "…", "token_type": "bearer" }` и `200 OK` |
| `GET /auth/me` | Bearer-токен | Текущий пользователь и `200 OK` |

Поля пользователя: `id`, `email`, `created_at`, `updated_at`. Регистрация также
возвращает `access_token` и `token_type`, поэтому защищённые запросы можно выполнять
сразу. `GET /auth/me` возвращает только поля пользователя.
Email проверяется, очищается от пробелов по краям и приводится к нижнему регистру.
Повторная регистрация email возвращает `409`, неверный email или пароль при входе —
`401`, некорректные поля запроса — `422`. В БД хранится уникальный email и
`hashed_password`; пароль и хеш не попадают в ответы API.

Пароль должен содержать минимум 8 символов, занимать не более 72 байт в UTF-8
и не содержать нулевой символ. Для кириллицы и emoji число байт может быть больше
числа символов. Ограничение проверяется до хеширования, чтобы bcrypt не обрезал
пароль: [описание bcrypt в passlib](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html).

`backend/core/security.py` создаёт и проверяет access-токены с фиксированным
алгоритмом HS256. `get_current_user` — FastAPI dependency: проверяет Bearer-токен
и его срок действия, затем загружает пользователя из БД. Отсутствующий, неверный
или просроченный токен, а также токен удалённого пользователя дают `401` с
`WWW-Authenticate: Bearer`. Проверка подписи и срока действия выполняется через
[PyJWT](https://pyjwt.readthedocs.io/en/stable/usage.html).

Публичны `/auth/register`, `/auth/login`, `/health`, `/docs`, `/redoc`, `/openapi.json`.
Для выдачи и проверки JWT нужен настроенный `JWT_SECRET_KEY`: без него регистрация,
вход с верными данными и попытка проверить Bearer-токен возвращают `503`.
Если токен после регистрации не удалось выдать, создание пользователя откатывается.
Отсутствующий Bearer-заголовок или неверная схема авторизации дают `401`;
неверные данные входа также дают `401`. Health-check, документация и миграции
доступны без JWT-секрета. Клиент передаёт access-токен в `Authorization: Bearer …`;
сам серверный `JWT_SECRET_KEY` не принимается вместо токена.
Данные общие для всех зарегистрированных пользователей; разделение по владельцу
и роли в текущую реализацию не входит. Refresh-токены не выдаются: после истечения
access-токена нужно войти заново.

### Ограничение частоты запросов

SlowAPI ограничивает публичные `POST /auth/login` и `POST /auth/register` отдельно
для каждого IP: по умолчанию 10 и 5 запросов в минуту соответственно. Порог задаётся
через `LOGIN_RATE_LIMIT` и `REGISTER_RATE_LIMIT`; при превышении сервер возвращает
`429 Too Many Requests` и `Retry-After`. Запросы к `/health`, `/docs`, `/redoc` и
`/openapi.json` свободны от этих ограничений; все операции с данными требуют JWT.

Счётчики хранятся в памяти одного процесса и сбрасываются при перезапуске. Для
локального демо используется один процесс Uvicorn. При будущем запуске нескольких
процессов или реплик потребуется общее хранилище лимитов или ограничение на reverse proxy.
За прокси доверяйте forwarded-заголовкам только от его адресов, чтобы IP клиента
нельзя было подменить произвольным `X-Forwarded-For`.

### Операции с данными

Для `Node`, `Edge`, `Transaction`, `Cluster`, `NodeAssessment`, `RankedNode`
доступны соответственно `/nodes/`, `/edges/`, `/transactions/`, `/clusters/`,
`/node-assessments/`, `/ranked-nodes/`:

| Префикс | Назначение |
|---|---|
| `/nodes/` | Участники графа переводов |
| `/edges/` | Агрегированные направленные связи между участниками |
| `/transactions/` | Отдельные переводы |
| `/clusters/` | Группы связанных узлов и их характеристики |
| `/node-assessments/` | Оценки ролей и приоритета проверки узлов |
| `/ranked-nodes/` | Сохранённые записи очереди проверки |

Каждый роутер поддерживает одинаковые операции:

| Метод | Путь относительно префикса | Результат |
|---|---|---|
| `POST` | `/` | Создание по схеме `Create`, объект и `201 Created` |
| `GET` | `/?skip=0&limit=100` | Список объектов, `200 OK` |
| `GET` | `/{id}` | Один объект, `200 OK` |
| `PATCH` | `/{id}` | Частичное обновление по схеме `Update`, объект и `200 OK` |
| `DELETE` | `/{id}` | Удаление, `204 No Content` без тела ответа |

Например, `GET /nodes/?skip=20&limit=10` возвращает страницу узлов.
На всех шести списочных маршрутах `skip` — целое число от 0, `limit` — целое
число от 0 до 100 включительно. По умолчанию `skip=0`, `limit=100`;
`limit=0` возвращает пустой список, `limit=101` или отрицательное значение — `422`.
Порядок стабилен по `id`, кроме `/ranked-nodes/`, где используется `rank`;
следующая страница получается увеличением `skip`.
Для получения одного объекта, текущего пользователя или health-check пагинация не нужна.
Параметр `{id}` — технический идентификатор записи из ответа API; бизнес-ключи
`gid`, `row_id` и `cluster_id` передаются в полях объекта. `PATCH` меняет только
переданные поля. Отсутствующая запись при чтении, обновлении или удалении даёт `404`.

Роуты вызывают только сервисы. Глобальные обработчики в `backend/main.py`
преобразуют `NotFoundError`, `ConflictError`, `ValidationError` в HTTP `404`, `409`,
`422` соответственно, с телом `{"detail": "описание ошибки"}`. Некорректные
параметры запроса и поля схем возвращают стандартный ответ валидации FastAPI `422`.
Непойманные исключения возвращают `500` с `{"detail": "Internal server error"}`;
полный traceback записывается в серверный лог и не передаётся клиенту.

Стандартный `logging` выводит читаемые консольные сообщения (не JSON).
Middleware записывает каждый HTTP-запрос, включая CORS preflight: метод, путь,
статус и длительность в миллисекундах. Эти значения также доступны как поля
`LogRecord`: `method`, `path`, `status_code`, `duration_ms`. Успешные запросы
и перенаправления имеют уровень `INFO`, ответы `4xx` — `WARNING`, `5xx` — `ERROR`.
В журнал запросов не включаются query string, заголовки и тело запроса.

```text
2026-09-23 12:00:00 | INFO    | backend.access | HTTP request completed | method=GET path='/health' status_code=200 duration_ms=1.234
```

Dependency `get_db` открывает сессию, выполняет `commit` при успехе, `rollback`
при исключении и всегда закрывает сессию. Сервисы создаются в
`backend/api/dependencies.py`; `Depends(get_db, scope="function")` завершает
транзакцию до отправки HTTP-ответа. Фабрика сессий создаётся при первом обращении
к БД, поэтому запуск приложения и `GET /health` не требуют подключения к ней.

`GET /ranking?skip=0&limit=100` возвращает сохранённую очередь по месту в рейтинге.
`POST /ranking/rebuild` строит её из всех текущих `NodeAssessment` и возвращает
`{"ranked_nodes": количество}`. Оба маршрута требуют Bearer-токен.

### Репозитории и сервисы

Пользователи следуют тем же слоям: `models/user.py`, `schemas/user.py`,
`repositories/user_repository.py`, `services/user_service.py`. `UserCreate`
принимает email и пароль, `UserService.create` проверяет уникальность email,
хеширует пароль и передаёт репозиторию только email и хеш. `UserRepository`
наследует общий `BaseRepository`. `AuthService` использует `UserService` для
регистрации и поиска аккаунта при входе. Транзакцией, как и для остальных
сущностей, управляет `get_db`; `created_at` задаётся в БД.

Для `Node`, `Edge`, `Transaction`, `Cluster`, `NodeAssessment`, `RankedNode`
доступны классы `<Entity>Repository` и `<Entity>Service` в файлах
`backend/repositories/<entity>_repository.py` и `backend/services/<entity>_service.py`.
Общие методы наследуются из `BaseRepository` и `BaseService`:

- `get_by_id(entity_id)` — поиск по техническому `id`.
- `get_all(skip=0, limit=100)` — страница с устойчивым порядком по `id`;
  `skip` и `limit` — целые неотрицательные числа, `limit=0` возвращает пустой список.
- `create(data)`, `update(entity_id, data)`, `delete(entity_id)` — запись и удаление.

Репозитории принимают словари полей и возвращают ORM-объекты; при отсутствии
записи `get_by_id` и `update` возвращают `None`, `delete` — `False` (при успехе `True`).
Сервисы принимают существующие Pydantic-схемы `Create`/`Update`, возвращают
ORM-объекты, а успешный `delete` возвращает `None`. Для преобразования результата
в схему ответа доступен `NodeResponse.model_validate(node)` и аналоги.

Сервисы проверяют уникальность бизнес-ключей, наличие связанных записей и
условие `n_seed <= n_nodes`. Транзакции требуют существующего направленного
ребра; одинаковые переводы с разными `row_id` сохраняются. Частичные обновления
меняют только переданные поля и проверяют итоговую запись. Явный `None` разрешён
только для nullable-поля `pass_through`.

Ошибки экспортируются из `backend.services`: `NotFoundError`, `ConflictError`,
`ValidationError` (общий предок — `ServiceError`). Эти классы не зависят от HTTP.
Удаление или изменение бизнес-ключа используемой записи блокируется ограничениями
БД и превращается в `ConflictError`; каскадного удаления и пересчёта анализа нет.

Оба слоя используют переданную синхронную `Session`. Записи вызывают `flush`,
а `commit`/`rollback` принадлежат вызывающему коду. После ошибки ограничения БД
нужен rollback; контекст `session.begin()` выполнит его автоматически, если
исключение выйдет из блока:

```python
from sqlalchemy.orm import Session

from backend.core.database import create_db_engine
from backend.repositories import NodeRepository
from backend.schemas import NodeCreate
from backend.services import NodeService

engine = create_db_engine()
with Session(engine) as session, session.begin():
    service = NodeService(NodeRepository(session))
    node = service.create(NodeCreate(gid="example-node", depth=0, is_seed=True))
    node_id = node.id
```

Проверка API, репозиториев, сервисов и миграций на временной SQLite
(HTTP-тесты используют `pytest` и `TestClient`; зависимости включают `httpx` и `httpx2`
для совместимости с поддерживаемыми версиями Starlette):

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

В активированном виртуальном окружении достаточно `pytest -v`. Настройка `testpaths`
в корневом `pytest.ini` ограничивает поиск по умолчанию каталогом `backend/tests`,
чтобы копии проекта в `output/` не вызывали конфликтов при сборе тестов.
Команда запускает как существующие unittest-тесты, так и отдельные HTTP-тесты шести сущностей из
`backend/tests/test_api_*.py`. Фикстуры в `backend/tests/conftest.py` создают для
каждого нового HTTP-теста отдельную SQLite в памяти с проверкой внешних ключей,
тестового пользователя с JWT и необходимые связанные объекты.

## Docker Compose и CI

Docker-образ использует Python 3.12, устанавливает `backend/requirements.txt`
отдельным кэшируемым слоем и запускает API от непривилегированного пользователя.

Для первой установки клонируйте репозиторий и создайте файл настроек:

```powershell
git clone https://github.com/BAITC-Hacks/hack-7d81d142-the-hateful-three.git moneygraph-ai
cd moneygraph-ai
Copy-Item .env.example .env
```

В Linux/macOS вместо `Copy-Item` используйте `cp .env.example .env`.
Если `.env` уже есть, отредактируйте его без перезаписи. Затем выберите одну из двух
конфигураций ниже; для чистой машины подходит «Отдельная PostgreSQL в контейнере».

На Windows установите Docker Desktop с WSL 2, запустите его и дождитесь
готовности движка. После установки перезапустите PowerShell или PyCharm.
Команда `docker version` должна выводить обе секции: `Client` и `Server`.
Ошибка подключения к `//./pipe/docker_engine` означает, что выбранный движок
недоступен; проверьте Docker Desktop и текущий контекст через `docker context ls`.
Команды ниже вводятся целиком в одну строку, без завершающего `\`.

### Существующая PostgreSQL из .env

Для работы с уже настроенной базой используйте отдельную конфигурацию:

```bash
docker compose -f docker-compose.existing-db.yml up --build
```

Она запускает API и применяет миграции к существующей PostgreSQL. Укажите
в `.env` переменную `DOCKER_DATABASE_URL` с теми же реквизитами, что в
`DATABASE_URL`. Если PostgreSQL работает на вашем компьютере, замените
только хост `localhost` на `host.docker.internal`: `localhost` внутри
контейнера относится к самому контейнеру. Локальный Python продолжает
использовать исходный `DATABASE_URL`. PostgreSQL должна быть запущена
и принимать подключения со стороны Docker.

Также заполните `JWT_SECRET_KEY` в `.env`: без него регистрация и выдача токенов
возвращают `503`. Сгенерируйте секрет командой
`docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(32))"`
и сохраните результат в `JWT_SECRET_KEY` перед запуском Compose.

### Отдельная PostgreSQL в контейнере

Для запуска через Docker Compose создайте корневой `.env` по `.env.example`
(если он уже есть, дополните его). Задайте `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD` и `JWT_SECRET_KEY`. В `DATABASE_URL` используйте те же
имя базы, пользователя и пароль, хост **`db`** и порт **`5432`**:

```dotenv
POSTGRES_DB=moneygraph
POSTGRES_USER=moneygraph
POSTGRES_PASSWORD=<ваш пароль>
DATABASE_URL=postgresql+psycopg://moneygraph:<пароль в URL-кодировке>@db:5432/moneygraph
JWT_SECRET_KEY=<случайный секрет минимум 32 байта>
```

Замените значения в угловых скобках. В `POSTGRES_PASSWORD` пароль задаётся
без URL-кодирования, а в `DATABASE_URL` спецсимволы кодируются. JWT-секрет
можно сгенерировать командой `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Если Python не установлен на хосте, используйте
`docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(32))"`
и скопируйте результат в `JWT_SECRET_KEY` в `.env`.
Для запуска Python вне Docker используйте адрес вашей локальной PostgreSQL
вместо `db`; Compose не публикует порт базы на хост.

Из корня проекта:

```bash
docker compose up --build
```

Compose ждёт успешного healthcheck базы, выполняет `alembic upgrade head`
и только после успешных миграций запускает Uvicorn. API доступен на
[http://localhost:8000/docs](http://localhost:8000/docs), проверка сервера —
[http://localhost:8000/health](http://localhost:8000/health).
`.env` передаётся контейнеру при запуске и исключён из контекста сборки.

`docker compose down` останавливает контейнеры и сохраняет данные в volume
`postgres_data`. `POSTGRES_*` используются для инициализации пустого volume:
изменение этих значений в `.env` не меняет реквизиты уже созданной базы.

Workflow `.github/workflows/ci.yml` запускается при push в `main` и pull request
в `main`: поднимает PostgreSQL 16, устанавливает зависимости из
`backend/requirements-dev.txt`, применяет миграции и выполняет `pytest`.
`TEST_DATABASE_URL` включает проверки миграций на PostgreSQL во временных
схемах; существующие HTTP-тесты используют изолированные базы SQLite.
CI использует отдельные тестовые реквизиты и не требует `.env` или GitHub Secrets.
Деплой в workflow не настроен.

## Как запустить локально

Ниже команды для PowerShell. Используйте Python 3.12, как в Docker и CI,
и запущенную PostgreSQL с существующей базой и пользователем.

### 1. Клонировать репозиторий

```powershell
git clone https://github.com/BAITC-Hacks/hack-7d81d142-the-hateful-three.git moneygraph-ai
cd moneygraph-ai
```

Если проект уже скачан, откройте терминал в его корне.

### 2. Установить зависимости

Из корня проекта создайте виртуальное окружение Python 3.12
и установите зависимости сервера:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

В Linux/macOS используйте `python3.12 -m venv .venv`, затем `.venv/bin/python`
вместо `.\.venv\Scripts\python.exe` во всех последующих командах.

Зависимости анализа включены в зависимости API. Для тестов установите
`backend/requirements-dev.txt` вместо `backend/requirements.txt`.

### 3. Подготовить .env и данные

```powershell
Copy-Item .env.example .env
```

Не перезаписывайте `.env`, если он уже настроен. Backend читает корневой `.env`
независимо от рабочей папки; сам `.env.example` служит шаблоном. Настройки:

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `APP_NAME` | `MoneyGraph AI` | Название приложения в документации API |
| `CORS_ORIGINS` | localhost и 127.0.0.1 на портах 5173 и 8501 | Разрешённые origins, JSON-массив строк; полный список в `.env.example` |
| `DATABASE_URL` | `postgresql+psycopg://postgres@localhost:5432/moneygraph` | Подключение к PostgreSQL; настройте в `.env` перед миграцией |
| `JWT_SECRET_KEY` | Нет | Случайный секрет минимум 32 байта в UTF-8 для подписи HS256; обязателен для аутентификации |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Срок действия access-токена, положительное целое число минут |
| `LOGIN_RATE_LIMIT` | `10/minute` | Максимальная частота входа для одного IP |
| `REGISTER_RATE_LIMIT` | `5/minute` | Максимальная частота регистрации для одного IP |
| `DOCKER_DATABASE_URL` | Нет | Только для `docker-compose.existing-db.yml`: адрес существующей PostgreSQL из контейнера |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Нет | Обязательны для основной Compose-конфигурации; инициализируют базу в контейнере |
| `TEST_DATABASE_URL` | Нет | Адрес тестовой PostgreSQL для миграционных тестов; задаётся в окружении процесса, не в `.env`; без него используется SQLite |

Пустые значения используют defaults там, где они есть; переменные окружения имеют приоритет над `.env`.
Сервер запускается и без `.env`. CORS допускает методы `GET`, `POST`, `PATCH`, `DELETE` и заголовки
`Content-Type` и `Authorization` для указанных origins; передача credentials выключена.
Для фронтенда на Vite разрешён `http://localhost:5173` (также `http://127.0.0.1:5173`).
Сейчас демо запускается локально. При будущем деплое задайте точный origin фронтенда
со схемой и портом, если он нестандартный, без пути и завершающего `/`, затем перезапустите API:

```dotenv
CORS_ORIGINS=["https://your-frontend.example"]
```

`https://your-frontend.example` — пример для будущего размещения.
Настройка заменяет весь список: добавляйте dev-origins в тот же JSON-массив, если они нужны.

Для миграции укажите в `.env` существующую базу и пользователя с правом создания таблиц:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB_NAME
```

Замените заглушки настоящими значениями. Спецсимволы в логине и пароле
кодируются для URL, например `@` → `%40`, `%` → `%25`. Адрес с префиксом
`postgresql://` также поддерживается и использует установленный драйвер psycopg 3.
Alembic создаёт таблицы внутри существующей базы, а не саму базу PostgreSQL.

Перед запуском сервера задайте случайный JWT-секрет. Следующая команда генерирует
его через `secrets.token_urlsafe(32)` и сохраняет в окружении текущего PowerShell:

```powershell
$env:JWT_SECRET_KEY = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "30"
```

Запускайте Uvicorn в том же окне. Для постоянной настройки сохраните сгенерированный
секрет в `JWT_SECRET_KEY` корневого `.env` и используйте одинаковый ключ во всех
процессах сервера. Не добавляйте `.env` в Git. Замена ключа делает ранее выданные
токены недействительными; готового общего секрета в проекте нет.

### 4. Применить миграции

Из корня проекта:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

При активированной `.venv` эквивалентная команда — `alembic upgrade head`.
Текущая ревизия: `a61f27b90c3d` (таблица `users`), после `28fe255db73e`
(шесть таблиц данных). Повторный запуск `upgrade head` безопасен.
Для запуска из другой папки передайте `-c <абсолютный путь к alembic.ini>`.
Подключение берётся из окружения или корневого `.env`, пароль в `alembic.ini` не хранится.

Создаются таблицы `nodes`, `edges`, `transactions`, `clusters`, `node_assessments`,
`ranked_nodes`, `users` и служебная `alembic_version`. Начальные данные не загружаются.

У каждой сущности есть технический `id`, `created_at`, `updated_at`.
Бизнес-ключи `gid`, `row_id`, `cluster_id` сохраняются отдельно. Временные поля
в PostgreSQL имеют тип `TIMESTAMP WITH TIME ZONE`; `updated_at` обновляется
SQLAlchemy при изменении строки через ORM/Core. Прямой SQL должен обновлять это поле явно.

Денежные суммы — `NUMERIC(20, 2)`, `top_gids` — массив строк PostgreSQL.
Ограничения БД проверяют диапазоны глубины и баллов, роли, длину `evidence`,
уникальность оценки узла, пары рёбер, номера строки транзакции и позиции рейтинга.
`pass_through` допускает `NULL` и значения больше 1 по смыслу исходного плана.

Транзакция ссылается на узлы и на агрегированное ребро по составному ключу
`src/dst`. Сначала сохраняются узлы и рёбра, затем транзакции. Связи
`Transaction.edge` и `Edge.transactions` доступны для чтения; отправитель и
получатель задаются через `src/dst` или `sender/recipient`. Одинаковые переводы
с разными `row_id` разрешены. Удаление используемых узлов, рёбер и кластеров блокируется FK.

`RankedNode` хранит выбранных участников очереди. Для добавления необходима
`NodeAssessment` того же узла; переданные `role` и `priority_score` должны совпадать
с оценкой, иначе API возвращает `422`. Отсутствующая оценка даёт `404`.
`rank` назначается сервером: по убыванию `priority_score`, при равенстве — по `gid`.
Старое поле `rank` в POST/PATCH принимается для совместимости, но не задаёт место.
В POST его можно опустить. После добавления, обновления или удаления места
перенумеровываются от 1 без пропусков.

Изменение оценки обновляет роль, приоритет и место уже включённого в очередь узла.
Объяснение `why` обновляется вместе с `evidence`, если до изменения оно совпадало
с ним; вручную изменённый `why` сохраняется. Удаление оценки или перенос её на
другой `gid` удаляет старую запись очереди. Удаление самой записи очереди сохраняет
оценку. Новые оценки включаются явно через CRUD либо через `POST /ranking/rebuild`.
Пересборка включает все оценки, обновляет объяснения из `evidence` и сохраняет
технические ID существующих записей. Для приведения старых снимков к этим правилам
выполните пересборку. Все изменения происходят в транзакции запроса; PostgreSQL
сериализует операции рейтинга транзакционной advisory-блокировкой.

При создании и изменении оценки `evidence` должно быть непустым, содержать хотя бы
одну десятичную цифру и занимать не более 200 символов. Это проверка формата,
а не доказательство достоверности объяснения. `pagerank` — конечное число в `[0, 1]`,
`pass_through` — `null` либо конечное неотрицательное число; значения больше 1 допустимы.
CRUD узлов требует `is_seed=true` ровно при `depth=0`.
`truncated_by_depth` должен совпадать с условием «глубина 4 и нет наблюдаемых
исходящих рёбер». При изменении глубины или исходящих рёбер этот флаг существующей
оценки обновляется автоматически. Полный пересчёт кратчайших расстояний от seed
при частичной загрузке графа не выполняется. Эти семантические проверки действуют
на уровне схем запросов и сервисов; прямые SQL/ORM-записи должны соблюдать их сами.

Проверки миграции на временной SQLite (PostgreSQL-массив заменяется JSON только в SQLite):

```powershell
.\.venv\Scripts\python.exe -W error -m unittest backend.tests.test_migrations -v
```

Для тех же проверок на PostgreSQL задайте `TEST_DATABASE_URL` в окружении.
Тесты создают отдельную временную схему и удаляют только её; пользователю нужны
права на создание схем. Проверяются upgrade/downgrade, соответствие metadata,
связи, ограничения, временные поля и сохранение повторных переводов.

### 5. Запустить backend

Из корня проекта:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --no-access-log
```

`--no-access-log` отключает второй журнал HTTP-запросов Uvicorn: запросы уже
логирует middleware приложения. Служебные сообщения Uvicorn остаются доступны.

- Проверка: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) → `{"status":"ok"}`.
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- Остановка сервера: `Ctrl+C`.

Датасет для запуска backend не требуется. Для CRUD API нужна доступная база
с применёнными миграциями и access-токен; `GET /health` и Swagger UI работают без подключения к БД.

В другом окне PowerShell зарегистрируйтесь, войдите и выполните защищённый запрос:

```powershell
$apiUrl = "http://127.0.0.1:8000"
$email = Read-Host "Email"
$password = [System.Net.NetworkCredential]::new("", (Read-Host "Пароль" -AsSecureString)).Password
$credentials = @{ email = $email; password = $password } | ConvertTo-Json

$registration = Invoke-RestMethod -Method Post -Uri "$apiUrl/auth/register" -ContentType "application/json; charset=utf-8" -Body $credentials
# Токен регистрации уже подходит для защищённых запросов.
$headers = @{ Authorization = "Bearer $($registration.access_token)" }
Invoke-RestMethod -Uri "$apiUrl/auth/me" -Headers $headers
# При последующих входах получите новый токен через /auth/login.
$auth = Invoke-RestMethod -Method Post -Uri "$apiUrl/auth/login" -ContentType "application/json; charset=utf-8" -Body $credentials
$headers = @{ Authorization = "Bearer $($auth.access_token)" }
Invoke-RestMethod -Uri "$apiUrl/auth/me" -Headers $headers
Invoke-RestMethod -Uri "$apiUrl/nodes/?skip=0&limit=10" -Headers $headers
Remove-Variable password, credentials
```

Если пользователь уже существует, пропустите запрос регистрации. В Swagger UI
вызовите `/auth/register` или `/auth/login` с JSON, скопируйте `access_token`, нажмите **Authorize**
и вставьте только токен: префикс `Bearer` Swagger добавляет сам.

Проверка доступа к данным:

```bash
curl -i http://127.0.0.1:8000/nodes/
# HTTP 401 без токена
curl -i http://127.0.0.1:8000/nodes/ -H "Authorization: Bearer <access_token>"
# HTTP 200 с действующим токеном из ответа регистрации или входа
```

### 6. Запустить существующий аудит данных (отдельно от backend)

Для аудита дополнительно установите библиотеки:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Скрипт анализа не загружает `.env`.

Поместите предоставленный `data (1).zip` в родительскую папку проекта. Это фиксированный путь, используемый текущим скриптом; переименовывать или распаковывать архив не нужно.

```text
<родительская папка>/
├── data (1).zip
└── moneygraph-ai/
    └── analysis/profile_data.py
```

Внутри архива должны находиться `data/nodes.parquet`, `data/edges.parquet` и `data/transactions.parquet`. Для транзакций используются поля `src`, `dst`, `date`, `sum_kzt`; ID операции и времени суток в данных нет.

```powershell
.\.venv\Scripts\python.exe analysis/profile_data.py
```

Скрипт выводит сводку и перезаписывает `analysis/profile.json` и `analysis/node_features.csv`. Исходный архив остаётся неизменным. Для предоставленных данных ожидаются 2 248 строк признаков, `amount_mismatch = 0`, `count_mismatch = 0` и `unknown_endpoints = 0`.

Это отдельный аудит исходного архива. Для рабочего приложения используйте инструкции
«Запуск дашборда» в начале README. При `FileNotFoundError` проверьте расположение
архива; при ошибке импорта — установку зависимостей в `.venv`.

## Проверка перед демо

- В новой папке клонируйте репозиторий и пройдите один сценарий запуска выше.
  Для Docker достаточно Docker Compose и заполненного `.env`; для локального запуска
  нужны Python, PostgreSQL и миграции. Проверьте регистрацию, `/auth/me` и чтение `/nodes/`.
- Убедитесь, что `git ls-files -- .env` ничего не выводит, а
  `git ls-files -- .env.example` выводит `.env.example`. `.env` исключён через `.gitignore`
  и `.dockerignore`; шаблон хранится без реальных паролей и JWT-секрета.
- Запустите `python -m pytest backend/tests` в окружении с dev-зависимостями.
- Откройте [локальный `/health`](http://localhost:8000/health),
  [Swagger `/docs`](http://localhost:8000/docs) и
  [спецификацию `/openapi.json`](http://localhost:8000/openapi.json).
  `/health` должен отвечать `200` и `{"status":"ok"}`, Swagger должен загружать схемы.
  Проверьте и защищённый запрос с JWT: одного health-check недостаточно для проверки БД.
- Если подключён фронтенд, проверьте запрос из его браузера, включая `Authorization`,
  с origin, перечисленным в `CORS_ORIGINS`.

Текущее демо локальное, публичного URL нет. При будущем размещении повторите проверки
`/health`, `/docs` и защищённого CRUD по фактическому адресу API и укажите домен фронтенда
в `CORS_ORIGINS`. CI выполняет проверки, но не деплой.

## Требования хакатона и границы MVP

Источник требований — предоставленные README датасета, README и код стартера. Отдельного полного ТЗ и валидатора в доступных материалах нет.

Обязательные результаты:

| Файл | Требование |
|---|---|
| `nodes_roles.csv` | Ровно 2 248 строк, включая 19 изолятов; заполненные поля, одна роль на узел, числовое `evidence` до 200 символов |
| `clusters.csv` | Строка на кластер с характеристиками и гипотезой о назначении |
| `top_nodes.csv` | Не менее 20 узлов, отсортированных по убыванию приоритета, с объяснением |

Сохраняются колонки стартера; дополнительные разрешены:

```text
nodes_roles.csv:
gid,role,role_score,cluster_id,priority_score,evidence,in_deg,out_deg,in_kzt,out_kzt,pagerank,pass_through,depth,is_seed,truncated_by_depth

clusters.csv:
cluster_id,n_nodes,n_seed,sum_kzt_internal,top_gids,hypothesis

top_nodes.csv:
rank,gid,role,priority_score,why
```

Допустимые роли: `consolidator`, `transit`, `distributor`, `terminal`, `coordinator`, `peripheral`. `role_score` и `priority_score` находятся в `[0, 1]` и отражают разные показатели: поддержку роли и приоритет проверки.

При реализации обязательно учитывать:

- У 444 узлов четвёртого колена нет наблюдаемых выходов: это граница выгрузки, а не доказательство конечного получения средств. Сохраняется флаг `truncated_by_depth`.
- Входящие потоки неполны, особенно у seed. `pass_through` — отношение наблюдаемых сумм, а не доказанная доля переданных дальше денег.
- Суммы и количество операций — разные признаки. Направление и веса графа сохраняются; неориентированную проекцию для кластеризации нужно явно описать.
- Период ограничен июлем 2026 года, порог перевода — 5 000 KZT. Даты не позволяют устанавливать порядок операций внутри дня.
- 97 повторных строк транзакций нельзя автоматически удалять без ID операции. В браузере идентификаторы нужно передавать строками, чтобы избежать потери точности.
- При нулевом входе `pass_through` неопределён. Стартер оставляет `NaN`, хотя его README требует заполненные колонки; допустимое представление нужно сверить с валидатором организаторов, не выдавая техническую замену за измеренное значение.

При бюджете три часа приоритет — объяснимые правила ролей, кластеры, отдельный рейтинг, три CSV и проверка их схем, чисел и повторяемости. Затем — простой экран и демонстрация одного узла с объяснением за минуту. Временные признаки дают дополнительную ценность по README стартера и добавляются после обязательных результатов. AI-чат, генератор синтетики, обучение без разметки и масштабирование на миллионы узлов в этот план не входят.

## Команда

- **Название команды:** [заполнить]
- **Участники и роли:** [имя — роль; заполнить]
- **Контакт:** [заполнить]
