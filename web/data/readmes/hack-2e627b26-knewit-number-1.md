# EKT AI Assistant

Интерактивный прототип AI-консультанта для интернет-магазина электротехники EKT.kz. Он помогает найти товар, показать проверяемые характеристики, цену и наличие, подобрать допустимый аналог и сформировать защищённое предложение для корзины. Изменение корзины выполняется только после явного подтверждения пользователя.

Проект сделан как hackathon MVP, но в нём уже выделены границы, необходимые для дальнейшей продуктовой интеграции: frontend не имеет доступа к учётным данным EKT или OpenAI, а все внешние вызовы и бизнес-правила находятся на backend.

## Что умеет проект

- Главная страница EKT.kz с интерактивным 3D hero-блоком: планету можно вращать, анимацию — поставить на паузу. Для окружений без WebGL есть CSS-fallback.
- Каталог и карточки товаров, построенные поверх backend API.
- Чат-консультант на русском и казахском языках.
- Поиск по локальному индексу, семантический поиск и подбор аналогов по утверждённым правилам совместимости.
- Карточка товара в чате: цена, остаток, характеристики, статус свежести данных и ссылка на официальный источник.
- Безопасный flow корзины: сначала создаётся неизменяемое предложение, затем пользователь подтверждает именно его. Для устаревшей цены или остатка формируется новое предложение.
- Защита от повторных добавлений, ограничений количества и конкурентных изменений корзины в fixture-режиме.
- Локальная база знаний для условий доставки, оплаты и других справочных вопросов.
- Опциональная серверная интеграция с OpenAI Responses API: модель работает только как планировщик над ограниченными backend-инструментами.
- Прокси к EKT API с таймаутами, ограничением размера ответа, контролем редиректов и безопасной обработкой ошибок.
- Health/readiness/metrics, request ID и структурированное журналирование без секретов и содержимого сообщений.

> В текущей ветке UI выбора вложений готов к использованию, но серверный endpoint `/api/dialog/uploads` ещё не реализован. Не используйте загрузку файлов как завершённую функцию до добавления backend-обработчика и антивирусной/контентной проверки.

## Архитектура

```text
Браузер (React / Vite)
  │  относительные /api/* и /demo/* запросы
  ▼
Django BFF
  ├─ каталог: fixture или защищённый адаптер EKT API
  ├─ локальный индекс, поиск и правила аналогов
  ├─ dialog / knowledge base / локализация
  ├─ корзина и подтверждаемые cart actions
  └─ опциональный OpenAI Responses API через ограниченные инструменты
        │
        ├─ EKT API (только backend, Basic Auth)
        └─ OpenAI API (только backend, ключ в секрет-хранилище)
```

## Стек

| Слой | Технологии | Назначение |
| --- | --- | --- |
| Клиент | React 18, Vite 6, JavaScript | Главная, каталог, чат, локализация и UX корзины |
| 3D hero | Three.js, `@react-three/fiber` | Интерактивная визуальная сцена на главной |
| Тесты frontend | Vitest, Testing Library, JSDOM | Проверка пользовательских сценариев чата и корзины |
| Сервер | Django 5.2, SQLite для MVP | BFF, сессии, API, каталог, корзина, knowledge base |
| Внешние системы | EKT API, OpenAI Responses API | Каталог и опциональная LLM-оркестрация |

## Структура репозитория

```text
.
├── frontend/                     # React/Vite клиент
│   ├── src/App.jsx               # страницы, каталог, чат, корзина
│   ├── src/OrbitDeliveryHero.jsx # интерактивный Three.js hero
│   ├── src/cartApi.js            # клиент к backend API
│   ├── src/i18n.js               # RU/KK тексты интерфейса
│   └── src/*.test.*              # frontend-тесты
├── backend/                      # Django BFF
│   ├── catalog/                  # провайдеры, индекс, поиск, аналоги
│   ├── cart/                     # предложения и подтверждение корзины
│   ├── dialog/                   # состояние диалога, SSE, safety checks
│   ├── assistant/                # LLM-оркестрация и локализация
│   ├── knowledge_base/           # утверждённые справочные знания
│   ├── gateway/                  # лимиты, сессия и middleware
│   ├── config/                   # настройки, URL, наблюдаемость
│   └── docs/                     # контракты и acceptance-материалы
├── HackAlem_AI_ekt_kz.md         # исходное ТЗ/контекст кейса
└── ekt-case-notes.md             # проверенные заметки по EKT API
```

## Быстрый запуск

### 1. Backend в fixture-режиме

Fixture-режим не требует доступа к EKT API и подходит для демо и разработки.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

В `backend/.env` установите:

```dotenv
CATALOG_PROVIDER=fixture
DJANGO_ENV=development
DJANGO_DEBUG=true
```

Затем примените миграции и запустите сервер:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Для macOS/Linux активируйте окружение командой `source .venv/bin/activate`.

### 2. Frontend

В новом терминале:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Откройте адрес, который напечатает Vite (обычно `http://localhost:5173`). По умолчанию frontend проксирует `/api/*` и `/demo/*` на `http://localhost:8000`, поэтому cookies и CSRF работают в same-origin сценарии.

Требования: Node.js 20+ и Python с поддержкой Django 5.2.

## Режимы каталога

| Режим | Настройка | Когда использовать |
| --- | --- | --- |
| Fixture | `CATALOG_PROVIDER=fixture` | Разработка, тесты и стабильная демонстрация без внешних зависимостей |
| EKT API | `CATALOG_PROVIDER=ekt` + `EKT_API_USERNAME` / `EKT_API_PASSWORD` | Интеграция с реальным каталогом; credentials остаются только на сервере |

Live-адаптер предоставляет read-only данные каталога. Реальное изменение корзины EKT не включается, пока не согласован официальный conditional cart API. В fixture-режиме доступна демонстрационная сессионная корзина.

## Основные пользовательские сценарии

1. Пользователь открывает чат и пишет запрос на русском или казахском.
2. Backend определяет язык, подбирает данные каталога/базы знаний и возвращает ответ со статусом источника.
3. При найденном товаре отображаются цена, наличие, характеристики и количество.
4. Нажатие «Добавить» не меняет корзину: создаётся предложение с `action_id`, ценой и сроком действия.
5. Пользователь подтверждает конкретное предложение кнопкой или строгой фразой подтверждения.
6. Сервер повторно проверяет данные. Если цена, наличие или версия корзины изменились, старое предложение истекает и возвращается replacement action.
7. Только успешное подтверждение изменяет сессионную fixture-корзину.

## API: ключевые маршруты

| Маршрут | Назначение |
| --- | --- |
| `GET /api/products` | Список товаров из настроенного провайдера |
| `GET /api/products/detail?id=…` | Карточка товара с нормализованными полями |
| `GET /api/search?q=…` | Поиск по локальному индексу |
| `GET /api/search/semantic?q=…` | Поиск по свойствам и описанию индексированных товаров |
| `GET /api/analogs?id=…` | Объяснимый подбор аналогов для поддерживаемых категорий |
| `GET /api/knowledge-base?q=…&lang=ru` | Поиск утверждённых справочных знаний |
| `GET /api/dialog` | Текущее состояние диалога и приветствие |
| `POST /api/dialog/messages` | Обычное сообщение диалога |
| `POST /api/dialog/messages/stream` | Потоковый ответ по SSE |
| `POST /api/dialog/cancel` | Отмена текущей операции |
| `DELETE /api/dialog/history` | Очистка истории текущей сессии |
| `GET /api/cart` | Текущее состояние demo-корзины |
| `POST /api/cart/actions` | Создание предложения корзины |
| `POST /api/cart/actions/{action_id}/confirm` | Подтверждение конкретного предложения |
| `POST /api/cart/actions/confirm-text` | Строгое текстовое подтверждение единственного активного предложения |
| `POST /api/chat/language` | Явная смена RU/KK в сессии |
| `GET /health`, `GET /ready`, `GET /metrics` | Liveness, readiness и метрики |

Полный контракт, граничные случаи и формат данных описаны в [backend/README.md](backend/README.md), а контракты провайдера — в [backend/docs](backend/docs).

## Конфигурация

Не коммитьте `backend/.env` и не передавайте секреты в браузер.

| Переменная | Назначение |
| --- | --- |
| `CATALOG_PROVIDER` | `fixture` или `ekt` |
| `EKT_API_BASE_URL`, `EKT_API_USERNAME`, `EKT_API_PASSWORD` | Параметры серверного адаптера EKT API |
| `SELLABLE_STORE_IDS` | Согласованный allowlist складов, доступных для продажи в live-режиме |
| `DJANGO_SECRET_KEY`, `DJANGO_ENV`, `DJANGO_ALLOWED_HOSTS` | Настройки Django и production-окружения |
| `API_RATE_LIMIT_PER_MINUTE`, `API_MAX_BODY_BYTES` | Защита публичного API BFF |
| `OPENAI_ENABLED`, `OPENAI_API_KEY`, `OPENAI_MODEL` | Опциональный OpenAI Responses API; ключ только на backend |
| `CATALOG_INDEX_*` | Путь, лимиты и правила синхронизации локального индекса |
| `VITE_API_BASE_URL` | Адрес backend для Vite proxy во frontend |

## Локальный индекс каталога

Для быстрого поиска и подбора аналогов синхронизируйте каталог в локальный индекс:

```powershell
cd backend
python manage.py sync_catalog --include-details
```

Данные записываются в `backend/var/` и игнорируются Git. В production запускайте синхронизацию по расписанию; рекомендуемый интервал — один раз в 24 часа. Readiness-проверка вернёт 503, если выбранный провайдер или локальный индекс недоступен.

## Безопасность и границы ответственности

- EKT credentials и OpenAI API key не попадают во frontend, ответы API или логи.
- Backend принимает внешние каталоговые, файловые и web-данные как недоверенные: опасная разметка и неразрешённые URL отбрасываются.
- Данные банковских карт, CVV/CVC, IBAN и реквизиты отклоняются до сохранения сессии и до обращения к LLM.
- Цена и остаток для предложения корзины проверяются на сервере; клиент не является источником истины.
- Cart actions привязаны к сессии, имеют TTL и работают идемпотентно.
- Ограничитель запросов в MVP процессный. Для нескольких экземпляров backend вынесите rate limiting в Redis или другой общий storage.

## Проверки

```powershell
# frontend
cd frontend
npm run test:run
npm run build

# backend
cd backend
python manage.py test
```

## Документация

- [Backend API и эксплуатация](backend/README.md)
- [Контракт провайдеров каталога](backend/docs/catalog-provider-contract.md)
- [Оркестрация LLM](backend/docs/llm-orchestrator.md)
- [Матрица приёмки](backend/docs/acceptance-matrix.md)
- [Исходный контекст кейса](HackAlem_AI_ekt_kz.md)

## Что нужно для production

Перед реальным запуском необходимо: подключить production-БД с блокировками строк для корзины, вынести rate limit и сессии в общую инфраструктуру, настроить секрет-хранилище, добавить мониторинг/алерты, согласовать продаваемые склады, завершить endpoint безопасной загрузки файлов и получить официальный контракт на mutation API корзины EKT.

## Local installation and `.env` configuration

### Requirements

- Python 3.12+;
- Node.js 20+ and npm;
- access to `https://ekt.kz/api` for the live catalog.

### Backend (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py check
python manage.py runserver 127.0.0.1:8000
```

If PowerShell blocks `Activate.ps1`, use `.\.venv\Scripts\python.exe` directly. If port `8000` is busy, use `8001` and set the same port in `frontend/.env`.

### `backend/.env`

Create it by copying `backend/.env.example`. Use one `NAME=VALUE` pair per line, with no spaces around `=`.

Demo mode:

```dotenv
CATALOG_PROVIDER=fixture
DJANGO_ENV=development
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=local-development-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
OPENAI_ENABLED=false
```

Live EKT mode:

```dotenv
CATALOG_PROVIDER=ekt
EKT_API_BASE_URL=https://ekt.kz/api
EKT_API_USERNAME=<EKT API username>
EKT_API_PASSWORD=<EKT API password>
SELLABLE_STORE_IDS=
EKT_CONNECT_TIMEOUT_SECONDS=1
EKT_READ_TIMEOUT_SECONDS=3
EKT_DEADLINE_SECONDS=5
EKT_MAX_RETRIES=2
EKT_ASSET_ALLOWED_HOSTS=ekt.kz
```

`SELLABLE_STORE_IDS` may stay empty until EKT confirms sellable warehouses. It does not disable catalog loading; it only prevents stock from being treated as confirmed sellable.

Optional OpenAI:

```dotenv
OPENAI_ENABLED=true
OPENAI_API_KEY=<new OpenAI key>
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=<available model>
```

Keep credentials only in backend `.env`; never commit them or put them in frontend. Revoke any key exposed in chat or git. `.env` files are ignored by `.gitignore`.

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Set `frontend/.env` to the backend URL:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Use `http://127.0.0.1:8001` when backend runs on port 8001. Restart Vite after changing `.env`; the UI is usually at `http://localhost:5173`.

### Verification

```powershell
Invoke-WebRequest http://127.0.0.1:8000/ready
Invoke-WebRequest "http://127.0.0.1:8000/api/products?page=1&per_page=2"
cd frontend
npm.cmd run test:run
npm.cmd run build
```
