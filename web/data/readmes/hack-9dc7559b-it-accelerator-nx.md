# HackAlem AI

**B2B-консультант для электротехнического каталога ekt.kz** — подбор по артикулу и описанию, наличие и аналоги, условия покупки, безопасное подтверждение состава перед корзиной.

| | |
| --- | --- |
| **Команда** | TechnoHorizon · хакатон BAITC |
| **Репозиторий** | Monorepo: Spring Boot API + React SPA + Docker Compose |
| **Статус** | Активная разработка (hackathon demo), не production-release |
| **Контракт** | OpenAPI · [Swagger](http://localhost:8080/swagger-ui.html) после локального старта |

> Синтетические каталог, остатки и корзина — учебные данные. Они не являются офертой ekt.kz и не заменяют партнёрские adapters.

---

## Содержание

1. [Возможности](#возможности)
2. [Архитектура](#архитектура)
3. [Быстрый старт](#быстрый-старт)
4. [Режимы запуска](#режимы-запуска)
5. [Конфигурация](#конфигурация)
6. [Структура репозитория](#структура-репозитория)
7. [API и клиент](#api-и-клиент)
8. [Разработка](#разработка)
9. [Проверки качества](#проверки-качества)
10. [Устранение неисправностей](#устранение-неисправностей)
11. [Документация](#документация)
12. [Правила работы с репозиторием](#правила-работы-с-репозиторием)

---

## Возможности

| Область | Реализация |
| --- | --- |
| Чат и сессии | Visitor JWT, диалоги, история, идемпотентная отправка, SSE replay |
| Агент | Ограниченный tool-loop, типизированные события ответа |
| Каталог | Версионированный импорт, поиск, pgvector, синтетический seed |
| Корзина | Confirm Gate: предложение → отдельное согласие → снимок корзины |
| Вложения | Upload / review UI (XLS, DOC, PDF, JPEG) с серверным контуром |
| Embed | Script + iframe `/widget`, host-demo на отдельном origin |
| Платформа | PostgreSQL + pgvector, Redis, Flyway, Docker Compose profiles |

---

## Архитектура

```text
┌─────────────┐     ┌──────────────┐     ┌──────────────────────────┐
│  Browser    │────▶│  Frontend    │────▶│  Backend (Spring Boot)   │
│  :5173      │     │  React/Vite  │     │  :8080                   │
│  host-demo  │     │  OpenAPI SDK │     │  JWT · Chat · Catalog    │
│  :5180      │     └──────────────┘     │  Cart · Attachments      │
└─────────────┘                          └────────────┬─────────────┘
                                                      │
                                         ┌────────────┴────────────┐
                                         │  PostgreSQL :5432       │
                                         │  Redis      :6379       │
                                         └─────────────────────────┘
```

| Слой | Стек |
| --- | --- |
| Backend | Java 21, Spring Boot 3.x, Spring AI (OpenAI), Flyway, Jdbc/JPA |
| Frontend | React 19, Vite, TypeScript, TanStack Query, Tailwind |
| Data | PostgreSQL 16 + pgvector, Redis 7 |
| Ops | Docker Compose (`db`/`redis` always; `backend`/`frontend`/`host-demo` · profile `full`) |

Правило адресов:

- **Браузер** → `localhost:8080` (не DNS-имя `backend`).
- **Backend в Compose** → БД `db:5432`, Redis `redis`.
- **Backend на хосте** (`bootRun`) → БД `localhost:5432`, Redis `localhost:6379`.

---

## Быстрый старт

Рекомендуемый путь для ежедневной работы: инфраструктура в Docker, API и UI на хосте.

**Требования:** Docker Compose v2, Java 21, Node.js 20+, свободные порты `5432`, `6379`, `8080`, `5173`.

```bash
git clone https://github.com/BAITC-Hacks/hack-9dc7559b-it-accelerator-nx.git
cd hack-9dc7559b-it-accelerator-nx

cp .env.example .env
# Укажите OPENAI_API_KEY=sk-...  (не коммитьте .env)

docker compose up -d
docker compose ps                    # db и redis → healthy

# Терминал 1
cd backend && ./gradlew bootRun      # http://localhost:8080

# Терминал 2
cd frontend && npm ci && npm run gen && npm run dev
# http://localhost:5173
```

Проверка:

```bash
curl --fail http://localhost:8080/actuator/health
curl --fail -X POST http://localhost:8080/auth/visitor-session
```

Полный стек «как на проде» (нужен ключ OpenAI):

```bash
docker compose --profile full up -d --build
```

| Сервис | URL |
| --- | --- |
| Чат | http://localhost:5173 |
| Embed demo | http://localhost:5180 |
| Swagger | http://localhost:8080/swagger-ui.html |
| OpenAPI | http://localhost:8080/v3/api-docs |
| Health | http://localhost:8080/actuator/health |

---

## Режимы запуска

Выберите **один** режим. Не смешивайте порты без смены `POSTGRES_PORT` / `COMPOSE_PROJECT_NAME`.

| Режим | Назначение | OpenAI | Порты |
| --- | --- | --- | --- |
| **Dev** | Hot reload, повседневная разработка | Для live-чата | `5432` · `6379` · `8080` · `5173` |
| **Full** | Demo / compose-образцы frontend+embed | Обязателен | + host-demo `5180` |
| **Contract** | Offline API без LLM-сети | Не нужен | `55432` · `56379` · `18080` |

### Dev (детально)

1. `cp .env.example .env` → задать `OPENAI_API_KEY`.
2. Если `5432` занят: в `.env` поставить `POSTGRES_PORT=5433` и тот же порт в `SPRING_DATASOURCE_URL`.
3. `docker compose up -d` → дождаться `(healthy)`.
4. `cd backend && ./gradlew bootRun`.
5. `cd frontend && npm ci && npm run gen && npm run dev`.

Учебный UI без живого chat-backend: `cd frontend && npm run dev:mock` → http://localhost:5174.

### Full Compose

```bash
cp .env.example .env          # OPENAI_API_KEY обязателен
docker compose --profile full up -d --build
docker compose ps
```

Smoke:

```bash
curl --fail http://localhost:8080/actuator/health
curl --fail -o /dev/null -w "%{http_code}\n" http://localhost:5173/
curl --fail -o /dev/null -w "%{http_code}\n" http://localhost:5180/
curl --fail http://localhost:5173/embed/v1/widget.js | head -c 80
```

`VITE_*` запекаются при **сборке** образа. После смены `VITE_API_URL` / `VITE_EMBED_ALLOWED_ORIGINS`:

```bash
docker compose up -d --build frontend
```

### Contract (offline)

Изолированный проект — **не** использует общий volume `hackalem_pgdata`.

```bash
docker compose -p hackalem-d1 -f scripts/d1-compose.yml up -d --wait

cd backend
SPRING_PROFILES_ACTIVE=contract \
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:55432/hackalem \
REDIS_PORT=56379 \
PORT=18080 \
./gradlew bootRun

curl --fail http://localhost:18080/actuator/health
curl --fail -X POST http://localhost:18080/auth/visitor-session
```

Остановка: `docker compose -p hackalem-d1 -f scripts/d1-compose.yml down`.

### Остановка и изоляция

| Действие | Команда | Данные |
| --- | --- | --- |
| Стоп сервисов | `docker compose down` | Volume сохранён |
| Полный сброс **своей** БД | `docker compose down -v && docker compose up -d` | Volume удалён |
| Логи | `docker compose logs -f backend` | — |
| psql | `docker compose exec db psql -U hackalem -d hackalem` | — |

`down -v` на общем demo-окружении команды **не выполнять** без явного согласования.

Параллельный worktree / CI-слот:

```bash
sh scripts/isolated-compose.sh my-agent-slot1 1 up
sh scripts/isolated-compose.sh my-agent-slot1 1 ps
sh scripts/isolated-compose.sh my-agent-slot1 1 down
```

Имя проекта ≠ `hackalem`. Слот `1…9` задаёт сдвинутые порты.

---

## Конфигурация

Единый шаблон: [`.env.example`](.env.example) → локальный `.env` (в git не коммитится).

| Переменная | Назначение | Default |
| --- | --- | --- |
| `POSTGRES_*` | Учётные данные БД | `hackalem` |
| `POSTGRES_PORT` / `REDIS_PORT` | Порты на хосте | `5432` / `6379` |
| `BACKEND_PORT` / `FRONTEND_PORT` | Проброс Compose | `8080` / `5173` |
| `HOST_DEMO_PORT` | Embed host page | `5180` |
| `OPENAI_API_KEY` | Live LLM / embeddings | обязателен для `live` |
| `SPRING_PROFILES_ACTIVE` | `live` \| `contract` \| `test` | `live` |
| `VITE_API_URL` | API из браузера (**build-time**) | `http://localhost:8080` |
| `VITE_EMBED_ALLOWED_ORIGINS` | Parent origins postMessage | `5180`, `5173` |
| `EMBED_FRAME_ANCESTORS` | CSP `frame-ancestors` (runtime) | `'self'` + demo origins |
| `CORS_ALLOWED_ORIGINS` | CORS backend | UI + host-demo |
| `CART_MODE` | Корзина | `sample` |

Новая переменная → сразу в `.env.example` **и** `docker-compose.yml`.

---

## Структура репозитория

```text
backend/          Spring Boot API, Flyway, domain, security, workers
frontend/         React SPA, generated OpenAPI client, embed script
host-demo/        Статическая страница для cross-origin iframe
data/             Синтетический каталог, FAQ, fixtures, evaluation sets
docs/             ТЗ, API handoff, performance, architecture
scripts/          Compose helpers, smoke, data validators
tasks/            Функциональный backlog и DoD
tests/            Evaluation / load сценарии
docker-compose.yml
docker-compose.test.yml
.env.example
AGENTS.md         Инженерный контракт monorepo
```

---

## API и клиент

Контракт ведётся на backend (springdoc). После старта API:

```bash
cd frontend
npm run gen
npm run gen:check
```

Источник по умолчанию: `http://localhost:8080/v3/api-docs`.  
Для contract: `npm run gen -- --input http://localhost:18080/v3/api-docs`.

Каталог `frontend/src/client/**` — **только** генерация, ручные правки запрещены.

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/actuator/health` | Liveness |
| `GET` | `/v3/api-docs` | OpenAPI JSON |
| `POST` | `/auth/visitor-session` | Выдача visitor-сессии |

UI: http://localhost:8080/swagger-ui.html

---

## Разработка

### Backend

```bash
docker compose up -d
cd backend
./gradlew bootRun    # :8080
./gradlew test
./gradlew build
```

### Frontend

```bash
cd frontend
npm ci
npm run gen          # backend должен отвечать на :8080
npm run dev          # :5173
npm run build && npm run lint && npm run test
```

### API-first workflow

1. Изменить контракт / контроллеры на backend.  
2. Убедиться, что `/v3/api-docs` актуален.  
3. `cd frontend && npm run gen`.  
4. Потреблять только сгенерированные типы и SDK.

---

## Проверки качества

Перед merge / демо:

```bash
cd backend && ./gradlew build
cd ../frontend && npm run build && npm run lint && npm run test
cd ..
./scripts/validate-demo-data.sh
```

Контейнерный smoke:

```bash
docker compose --profile full up -d --build
curl --fail http://localhost:8080/actuator/health
docker compose down
```

---

## Устранение неисправностей

| Симптом | Действие |
| --- | --- |
| `port is already allocated` | Сменить `POSTGRES_PORT` / `REDIS_PORT` / `BACKEND_PORT` / `FRONTEND_PORT` в `.env` и синхронно URL-ы |
| Backend не видит БД | `docker compose up -d && docker compose ps`; в Compose хост БД — `db`, не `localhost` |
| Flyway checksum mismatch | Не править применённую миграцию; добавить `V{n}__…sql`. Сброс только своей БД: `down -v` |
| `npm run gen` падает | `curl http://localhost:8080/v3/api-docs` — backend ещё не готов |
| Frontend в Docker «старый» | `docker compose up -d --build frontend` (особенно после смены `VITE_*`) |
| Старт падает без OpenAI | Задать `OPENAI_API_KEY` или использовать [Contract](#contract-offline) |
| Embed не открывается | Проверить `/embed/v1/widget.js` на `:5173`, host-demo `:5180`, allowlist origins в env |

---

## Документация

| Документ | Содержание |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Контракт monorepo, Compose, env, DoD |
| [backend/AGENTS.md](backend/AGENTS.md) | Backend-конвенции, Flyway, security |
| [frontend/AGENTS.md](frontend/AGENTS.md) | Frontend-конвенции, генерация клиента |
| [docs/ekt-assistant-spec.md](docs/ekt-assistant-spec.md) | Единое ТЗ и архитектура |
| [docs/api/README.md](docs/api/README.md) | API v1, границы D1/D2 |
| [docs/api/d1-handoff.md](docs/api/d1-handoff.md) | Offline demo-path и evidence |
| [host-demo/README.md](host-demo/README.md) | Embed host page |
| [tasks/README.md](tasks/README.md) | Backlog и зависимости задач |
| [data/README.md](data/README.md) | Синтетические данные |

---

## Правила работы с репозиторием

1. Не ломать воспроизводимый demo-path и Compose-контракт.  
2. API: backend → OpenAPI → `npm run gen` → frontend.  
3. Секреты только в локальном `.env`; в репозитории — `.env.example`.  
4. Применённые Flyway-миграции не редактировать.  
5. Новые env — сразу в `.env.example` и `docker-compose.yml`.  
6. Перед PR: backend `build`, frontend `build` / `lint` / `test`, health smoke.  
7. Trunk-based: короткие ветки, Conventional Commits (`feat:`, `fix:`, `docs:`, …).

Инженерный источник правил: [AGENTS.md](AGENTS.md).

---

## Ограничения текущей поставки

Не считаются закрытыми без отдельной приёмки:

- боевые adapters каталога / identity / partner cart;
- полный embed/mobile acceptance (QA-01);
- live OpenAI evaluation и cost-control;
- нагрузка 1–5k суммарных API RPS;
- production secrets, observability и disaster recovery.

Валидация синтетических fixtures:

```bash
./scripts/validate-demo-data.sh
```
