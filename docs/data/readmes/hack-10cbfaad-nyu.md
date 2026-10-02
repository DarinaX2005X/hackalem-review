# EKT AI — консультант по электротоварам

Хакатонный MVP чат-ассистента для каталога ekt.kz. Пользователь может искать электротовары, смотреть карточки и сведения о наличии, прикладывать спецификации и подтверждать предложение добавить товар в корзину. Проект разделён на веб-приложение, AI Service и Product Service. AI Service обращается к подключённому API модели; ниже приведена настройка Gemini.

## Состав проекта

| Каталог | Назначение |
| --- | --- |
| `web/` | Интерфейс чата, загрузка файлов, карточки товаров, подтверждение корзины и серверные API-маршруты Next.js. |
| `ai-service/` | Обработка сообщений и вложений, вызов LLM и инструментов поиска товаров. |
| `services/product-service/` | Получение и нормализация каталога ekt.kz, поиск, аналоги, проверка деталей и остатков. |
| `services/product-service/fixtures/` | Пример товара для проверки каталога без доступа к API ekt.kz. |

Поток запросов: браузер → `web` → AI Service → Product Service → PostgreSQL / API ekt.kz. Предложение добавить товар в корзину возвращается в `web` и выполняется только после подтверждения пользователя.

## Запуск с подключённым Gemini API

Нужны Docker Desktop с `docker compose`, Python 3.12, Node.js 20, npm, ключ Gemini API и учётные данные API ekt.kz для загрузки реального каталога. Команды рассчитаны на PowerShell и выполняются из корня репозитория. Порты `3000`, `6379`, `8001` и `8002` должны быть свободны. [Ключ Gemini можно создать в Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key).

### 1. Product Service и PostgreSQL

Скопируйте файл настроек, заполните `EKT_API_USERNAME` и `EKT_API_PASSWORD` в `services/product-service/.env`, затем запустите сервис:

```powershell
cd .\services\product-service
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

После сохранения `.env`:

```powershell
docker compose -f compose.yml up -d --build product-service
Invoke-RestMethod http://localhost:8001/health
```

Затем загрузите каталог:

```powershell
docker compose -f compose.yml exec product-service python -m app.sync_catalog
```

Compose запускает PostgreSQL и Product Service. Ожидаемый ответ `/health` — `status: healthy`. Каталог сам при старте не загружается. Для короткой проверки синхронизации можно добавить `--max-pages 1`.

Для проверки поиска напрямую:

```powershell
$headers = @{ Authorization = 'Bearer change-me' }
$body = @{ query = '027228'; limit = 5; filters = @{} } | ConvertTo-Json -Depth 3
Invoke-RestMethod -Method Post -Uri http://localhost:8001/internal/v1/products/search -Headers $headers -ContentType 'application/json' -Body $body
```

### 2. Redis

Для хранения истории диалогов запустите Redis в отдельном контейнере:

```powershell
docker run --rm -d --name ekt-ai-redis -p 6379:6379 redis:7-alpine
```

Если Redis уже работает на `localhost:6379`, этот шаг пропустите.

### 3. AI Service и файл `.env`

В новом окне PowerShell:

```powershell
cd .\ai-service
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Перед запуском Uvicorn** откройте `ai-service/.env` и вставьте настоящий ключ в `LLM_API_KEY`. Содержимое файла для локального запуска:

```dotenv
APP_ENV=development
AI_SERVICE_PORT=8002
INTERNAL_SERVICE_TOKEN=change-me
PRODUCT_SERVICE_URL=http://127.0.0.1:8001
REDIS_URL=redis://127.0.0.1:6379/0
LLM_PROVIDER=gemini
LLM_API_KEY=
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-3.5-flash-lite
LLM_TIMEOUT_SECONDS=60
MAX_ATTACHMENT_MB=15
CONVERSATION_TTL_SECONDS=86400
KNOWLEDGE_DIR=knowledge
```

Пустое `LLM_API_KEY` нужно заменить своим ключом: без него AI Service не запустится. Не добавляйте `ai-service/.env` в Git. Затем запустите сервис:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

AI Service загружает `.env` при старте и доступен на `http://localhost:8002/docs`. Базовый URL и идентификатор модели соответствуют [OpenAI-совместимому API Gemini](https://ai.google.dev/gemini-api/docs/openai) и [странице Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite). Для других провайдеров можно указать `LLM_PROVIDER=openai` или `deepseek` и их URL, модель и ключ.

Адреса `product-service` и `redis` из вашего примера подходят при запуске всех сервисов в **одной Docker-сети**. В описанном здесь локальном запуске AI Service работает на компьютере, поэтому в `.env` нужны адреса `127.0.0.1`.

### 4. Веб-приложение

```powershell
cd .\web
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm ci
npm run dev
```

Проверьте в `web/.env.local`: `AI_SERVICE_URL=http://127.0.0.1:8002`, `PRODUCT_SERVICE_URL=http://127.0.0.1:8001`, тот же `INTERNAL_SERVICE_TOKEN`, что у Product Service, и `CART_ADAPTER_MODE=live`. Затем откройте `http://localhost:3000`. Веб-приложение отправляет сообщения в AI Service, который вызывает Gemini API и Product Service. При подтверждении предложения корзины `web` запрашивает актуальное наличие в Product Service. После изменения `.env.local` перезапустите `npm run dev`.

Остановка: `Ctrl+C` в окнах AI Service и Next.js, затем в каталоге `services/product-service` выполните `docker compose -f compose.yml down` и остановите Redis командой `docker stop ekt-ai-redis`. Данные PostgreSQL останутся в Docker volume.

## Проверка подключения

После запуска отправьте сообщение напрямую в AI Service:

```powershell
$body = @{ message = 'Привет'; attachment_ids = @(); locale = 'ru-RU' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8002/internal/v1/chat/messages -ContentType 'application/json' -Body $body
```

Ответ с `text`, `conversation_id` и пустым массивом `errors` подтверждает успешный вызов модели. Запрос к Gemini требует действующего ключа и сетевого доступа. `INTERNAL_SERVICE_TOKEN` должен совпадать у Product Service, AI Service и `web`; при замене `change-me` обновите три файла настроек. Если меняете `.env`, перезапустите соответствующий сервис.

## Основные настройки

| Переменная | Где используется | Назначение |
| --- | --- | --- |
| `AI_SERVICE_URL` | `web` | Адрес AI Service для запросов чата и передачи вложений. |
| `PRODUCT_SERVICE_URL` | `ai-service`, `web` | Адрес Product Service. |
| `INTERNAL_SERVICE_TOKEN` | все модули | Токен внутренних запросов к Product Service. |
| `PRODUCT_DATABASE_URL` | Product Service | Подключение к PostgreSQL; в Compose уже задано. |
| `EKT_API_USERNAME`, `EKT_API_PASSWORD` | Product Service | Basic Auth для запросов к API ekt.kz. |
| `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | AI Service | Провайдер, ключ, адрес и модель подключённого AI API. |
| `REDIS_URL` | AI Service | Подключение к Redis для истории диалогов. |
| `CART_ADAPTER_MODE` | `web` | Значение `live` включает проверку наличия через Product Service. |
| `CART_PROPOSAL_TTL_SECONDS` | `web` | Срок действия предложения корзины; по умолчанию 900 секунд. |
| `EKT_CART_URL` | `web` | Ссылка на страницу корзины, возвращаемая текущим адаптером. |

Примеры всех переменных находятся в `web/.env.example`, `ai-service/.env.example` и `services/product-service/.env.example`.

## Проверки

В каталоге `web`:

```powershell
npm run lint
npm run build
```

В каталоге `services/product-service` тесты запускаются в отдельном профиле Compose:

```powershell
docker compose -f compose.yml --profile test build tests
docker compose -f compose.yml --profile test run --rm tests
```

В каталоге `ai-service` после создания виртуального окружения:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

## Технологический стек: что и для чего используется

Версии веб-пакетов зафиксированы в `web/package.json`. Версии Python-зависимостей указаны диапазонами в `requirements.txt`; Dockerfile обоих Python-сервисов использует Python 3.12.

| Технология | Где | Для чего |
| --- | --- | --- |
| Node.js 20 и npm | `web` | Запуск Next.js, установка пакетов и сборка интерфейса. |
| Next.js 14.2.15 (App Router) | `web/app` | Страницы чата и корзины, а также серверные API-маршруты для чата, файлов и подтверждения предложений. |
| React 18.3.1 | `web/components` | Компоненты чата, карточек товаров, загрузки файлов и подтверждения действий. |
| TypeScript 5.7.2 | `web` | Типы запросов, ответов и данных между интерфейсом и API. |
| Tailwind CSS 3.4.17 | `web` | Стили и адаптивная верстка интерфейса. |
| PostCSS 8.4.49 и Autoprefixer 10.4.20 | `web` | Обработка CSS и добавление браузерных префиксов при сборке. |
| ESLint 8.57.1 и `eslint-config-next` 14.2.15 | `web` | Проверка кода командой `npm run lint`. |
| Python 3.12 | `ai-service`, `services/product-service` | Среда выполнения двух серверных сервисов. |
| FastAPI и Uvicorn | оба Python-сервиса | HTTP API для чата, вложений, каталога, остатков и синхронизации; Uvicorn запускает приложения. |
| Pydantic | оба Python-сервиса | Проверка входных данных и формирование структурированных ответов API. |
| `pydantic-settings` | Product Service | Чтение и проверка настроек сервиса из окружения и `.env`. |
| `python-dotenv` | AI Service | Загрузка `ai-service/.env` с адресом модели и API-ключом при старте сервиса. |
| `httpx` | оба Python-сервиса | Запросы к API ekt.kz, Product Service и OpenAI-совместимому API модели. |
| PostgreSQL 16 | Product Service | Постоянное хранение нормализованного каталога и поиск товаров, включая полнотекстовый поиск. |
| SQLAlchemy 2 и `psycopg` 3 | Product Service | Модель данных, SQL-запросы и подключение Python-сервиса к PostgreSQL. |
| Redis и Python-пакет `redis` | AI Service | Хранение истории диалога с ограниченным сроком жизни. |
| OpenAI-совместимый Chat Completions API | AI Service | Вызов Gemini, OpenAI или DeepSeek через `httpx`; отдельный SDK не используется. |
| `python-multipart` | AI Service | Прием файлов через `multipart/form-data`. |
| `openpyxl`, `python-docx`, `pypdf` | AI Service | Извлечение данных соответственно из XLSX, DOCX и PDF. JPEG принимается, но OCR пока нет. |
| HTTP/REST, JSON и `multipart/form-data` | Все модули | Обмен запросами и ответами между сервисами; отдельный формат для передачи файлов. |
| Basic Auth, Bearer token и cookie | API ekt.kz, внутренние запросы, `web` | Авторизация к каталогу ekt.kz, проверка внутренних запросов Product Service и привязка предложений корзины к сессии браузера. |
| Docker и Docker Compose | Dockerfile всех модулей; `services/product-service/compose.yml` | Контейнерные сборки; Compose сейчас запускает Product Service и PostgreSQL, а также тестовый профиль. |
| pytest | Тесты Python-сервисов | Проверка контрактов AI Service, API каталога, нормализации и клиента ekt.kz. |

В браузере ответы приходят целиком, без SSE. Интеграция с Cart API ekt.kz остаётся отдельной задачей.
