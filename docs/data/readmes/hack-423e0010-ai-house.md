# Событие / Event — подбор подрядчиков для мероприятий

**Русский · [English](#event--event-vendor-recommendation-platform)**

«Событие» — веб-приложение для подбора подрядчиков на мероприятия. Пользователь задаёт город, дату, формат, категорию и бюджет, а система применяет обязательные фильтры и показывает до трёх подходящих профилей с объяснениями и ссылками на факты. Форма и чат-помощник работают с одним запросом.

Проект подготовлен командой **AI House**. Каталог содержит 66 профилей; часть профилей и часть значений помечены как синтетические или восстановленные. Приложение не бронирует подрядчиков, не отправляет заявки и не принимает оплату.

## Возможности

- Подбор по городу, дате, формату события, категории, бюджету, языку и длительности.
- Строгие фильтры доступности, цены и других условий; ранжирование подходящих профилей по пожеланиям.
- До трёх карточек с объяснениями, цитатами из описания и раскрываемыми основаниями; просмотр полного профиля и сравнение кандидатов.
- Пересчёт альтернатив даты, бюджета, языка и длительности. Альтернатива применяется только после выбора пользователем.
- Чат для изменения запроса и обсуждения текущих результатов. Без ключа внешнего API доступен ограниченный локальный помощник.
- История последних 20 подборок текущего мероприятия и сохранение запроса в браузерной сессии.
- Локальная SQLite по умолчанию; PostgreSQL при запуске через Docker Compose.
- Интерфейс на русском языке, адаптивная вёрстка и управление с клавиатуры.

## Быстрый запуск

### Docker Compose (любой поддерживаемой Docker ОС)

Установите и запустите Docker Desktop либо Docker Engine с Compose v2, затем в корне клонированного репозитория выполните:

```sh
docker compose up --build
```

Откройте [http://127.0.0.1:8000](http://127.0.0.1:8000). Остановка: `Ctrl+C`; остановить контейнеры, сохранив данные: `docker compose down`. Данные PostgreSQL и приложения хранятся в Docker volumes. Локальный демонстрационный пароль PostgreSQL задан в Compose; перед использованием вне локальной демонстрации задайте собственный `POSTGRES_PASSWORD` в `.env`.

### Локальный запуск без Docker

Требуются **Python 3.12+**, **Node.js 20.19+ или 22+** и npm. Команды ниже выполняются из корня репозитория.

#### macOS и Linux

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

#### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Set-Location frontend
npm ci
npm run build
Set-Location ..
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Если запуск PowerShell-скриптов запрещён политикой компьютера, активировать окружение не обязательно. Используйте `.\.venv\Scripts\python.exe -m pip ...` и `.\.venv\Scripts\python.exe -m uvicorn ...` вместо `python -m ...`. Также в комплекте есть `start.cmd` (Windows) и `start.ps1`.

Приложение: [http://127.0.0.1:8000](http://127.0.0.1:8000). Документация API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Остановка сервера: `Ctrl+C`.

Первый запуск устанавливает пакеты и собирает frontend, поэтому требуется подключение к интернету. При последующих запусках можно использовать готовую сборку. Для пересборки после изменений интерфейса выполните `npm run build` в папке `frontend`.

## Разработка

Для backend используйте установленный виртуальный env и запустите из корня:

```sh
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

В отдельном терминале:

```sh
cd frontend
npm run dev
```

Интерфейс разработки доступен на [http://127.0.0.1:5173](http://127.0.0.1:5173); Vite направляет запросы `/api` на backend. На Windows замените `python` на `.venv\Scripts\python.exe`, если окружение не активировано.

## Помощник и смысловой поиск

Приложение работает без API-ключа и внешних сервисов. По умолчанию действует локальный режим помощника (ограниченный разбор распространённых русских формулировок), а ранжирование пожеланий использует встроенный словарь признаков и текстовое сходство. Этот режим не является языковой моделью или нейросетевыми embeddings.

Чтобы включить чат через совместимый с OpenAI Chat Completions API сервис, скопируйте `.env.example` в `.env`, задайте ключ и при необходимости измените модель:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

Перезапустите backend. Не публикуйте `.env` и не добавляйте реальные ключи в Git. Внешняя модель выбирает ограниченные действия помощника; подбор и проверку фактов выполняет backend.

Опциональные нейросетевые embeddings настраиваются отдельно через `EMBEDDING_PROVIDER`: `openai` требует `OPENAI_API_KEY`, `sentence-transformers` — установку `backend/requirements-semantic.txt` и загрузку модели при первом запуске. Вариант по умолчанию — `local`. Ошибка внешнего провайдера возвращается как ошибка сервиса и не подменяется незаметно локальной сортировкой.

## Данные и хранение

Исходный каталог находится в `project-df/hackathon dataset anonymized .csv`. При старте он проверяется и импортируется целиком. SQLite создаётся автоматически в `data/platform.db`; папка `data/` не включается в Git. Compose вместо неё использует PostgreSQL и постоянные Docker volumes. Настройки можно переопределить в `.env` (см. `.env.example`).

Сессия определяется случайной HttpOnly-cookie; запросы и история привязаны к сессии браузера. Календарные данные каталога охватывают период **23 сентября — 31 декабря 2026 года**. Отметки синтетических профилей и восстановленных значений показываются в интерфейсе.

## Проверки и команды каталога

Из корня проекта:

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
python -m backend.cli validate
python -m backend.cli prepare
python -m backend.cli benchmark
```

Для Windows при неактивном окружении используйте `.venv\Scripts\python.exe` вместо `python`. Frontend собирается командой `npm run build` из `frontend`. Браузерные проверки: `npm run test:e2e` из `frontend` (требуют собранный frontend и установленный Google Chrome). E2E поднимают тестовый backend отдельно на порту 8765.

## Структура

```text
backend/       FastAPI API, каталог, фильтры, ранжирование, помощник и SQLite/PostgreSQL
frontend/      React, TypeScript и Vite
project-df/    исходное ТЗ, архитектура, use cases и обезличенный CSV-каталог
docs/          соответствие сценариев требованиям
compose.yaml   приложение и PostgreSQL для Docker Compose
Dockerfile     сборка frontend и backend-образа
start.cmd      установочный запуск для Windows CMD
start.ps1      установочный запуск для PowerShell
```

Исходные документы проекта находятся в `project-df`; соответствие реализованных сценариев use cases описано в [docs/use-cases.md](docs/use-cases.md).

---

## Event — event vendor recommendation platform

**[Русский](#событие--подбор-подрядчиков-для-мероприятий) · English**

Event is a web application for finding vendors for an event. A user enters a city, date, event format, category, and budget. The backend applies hard constraints and returns up to three eligible profiles with explanations and links to supporting facts. The form and chat assistant operate on the same request.

The project was built by **AI House**. Its catalog contains 66 profiles; some profiles and values are marked as synthetic or imputed. The application does not book vendors, send inquiries, or process payments.

## Features

- Search by city, date, event format, category, budget, language, and duration.
- Hard availability, price, and other constraints; preference-based ranking of eligible profiles.
- Up to three recommendation cards with explanations, description excerpts, expandable evidence, full profiles, and comparison.
- Recalculated alternatives for date, budget, language, and duration. An alternative is applied only after the user selects it.
- Chat for editing the request and discussing the current results. A limited local assistant works without an external API key.
- The latest 20 runs for the current event and request persistence within the browser session.
- SQLite by default for local use; PostgreSQL with Docker Compose.
- Russian-language interface, responsive layout, and keyboard navigation.

## Quick start

### Docker Compose (supported Docker platforms)

Install and start Docker Desktop or Docker Engine with Compose v2. From the cloned repository root, run:

```sh
docker compose up --build
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Stop with `Ctrl+C`; run `docker compose down` to stop containers while retaining data. PostgreSQL and application data are stored in Docker volumes. Compose includes a local demo PostgreSQL password; set your own `POSTGRES_PASSWORD` in `.env` before using this setup beyond a local demo.

### Run locally without Docker

Requirements: **Python 3.12+**, **Node.js 20.19+ or 22+**, and npm. Run these commands from the repository root.

#### macOS and Linux

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

#### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Set-Location frontend
npm ci
npm run build
Set-Location ..
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

If your system policy blocks PowerShell scripts, activation is optional. Use `.\.venv\Scripts\python.exe -m pip ...` and `.\.venv\Scripts\python.exe -m uvicorn ...` instead of `python -m ...`. The repository also includes `start.cmd` (Windows) and `start.ps1`.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000); API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Stop the server with `Ctrl+C`.

The first run installs packages and builds the frontend, so it needs internet access. Later runs can use the existing build. After frontend changes, rebuild by running `npm run build` in `frontend`.

## Development

With the Python virtual environment active, start the backend from the repository root:

```sh
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```sh
cd frontend
npm run dev
```

The development UI is available at [http://127.0.0.1:5173](http://127.0.0.1:5173); Vite proxies `/api` requests to the backend. On Windows, use `.venv\Scripts\python.exe` instead of `python` if the environment is not activated.

## Assistant and semantic search

The app works without API keys or external services. By default, chat uses a limited local parser for common Russian requests, and preference ranking uses a built-in concept vocabulary and text similarity. This mode is not an LLM or a neural embedding model.

To enable chat through a service compatible with the OpenAI Chat Completions API, copy `.env.example` to `.env`, set a key, and change the model if needed:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

Restart the backend. Do not commit `.env` or publish real keys. The external model selects from constrained assistant actions; the backend performs matching and verifies facts.

Optional neural embeddings are configured separately with `EMBEDDING_PROVIDER`: `openai` requires `OPENAI_API_KEY`; `sentence-transformers` requires installing `backend/requirements-semantic.txt` and downloading the model on first use. The default is `local`. An external provider failure is returned as a service error and does not silently switch to local ranking.

## Data and persistence

The source catalog is `project-df/hackathon dataset anonymized .csv`. It is validated and imported atomically at startup. SQLite is created automatically at `data/platform.db`; `data/` is excluded from Git. Compose uses PostgreSQL and persistent Docker volumes instead. Override settings in `.env` (see `.env.example`).

A random HttpOnly cookie identifies the browser session; requests and history belong to that session. Catalog calendars cover **September 23 through December 31, 2026**. Synthetic profiles and imputed values are identified in the interface.

## Checks and catalog commands

From the project root:

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
python -m backend.cli validate
python -m backend.cli prepare
python -m backend.cli benchmark
```

On Windows with an inactive environment, use `.venv\Scripts\python.exe` in place of `python`. Build the frontend with `npm run build` from `frontend`. Browser checks: `npm run test:e2e` from `frontend` (requires a built frontend and Google Chrome). E2E tests start a separate test backend on port 8765.

## Project layout

```text
backend/       FastAPI API, catalog, filtering, ranking, assistant, SQLite/PostgreSQL
frontend/      React, TypeScript, and Vite
project-df/    source brief, architecture, use cases, and anonymized CSV catalog
docs/          mapping of implemented behavior to requirements
compose.yaml   app and PostgreSQL for Docker Compose
Dockerfile     frontend build and backend image
start.cmd      setup and launch for Windows CMD
start.ps1      setup and launch for PowerShell
```

Source project documents are in `project-df`; implementation coverage of the use cases is documented in [docs/use-cases.md](docs/use-cases.md).
