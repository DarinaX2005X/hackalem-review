# ⚡ EKT Store

> Қалаға бейімделген электр жабдықтары интернет-дүкені: көптілді каталог, қойма есебі, транзакциялық тапсырыстар және қауіпсіз AI-ассистент.

[Қазақша](#-қазақша) · [Русский](#-русский) · [English](#-english)

![Node.js](https://img.shields.io/badge/Node.js-20%2B-339933?logo=nodedotjs&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111)
![Express](https://img.shields.io/badge/Express-5-000000?logo=express&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Prisma_6-4169E1?logo=postgresql&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)

---

## 🇰🇿 Қазақша

### Жоба туралы

**EKT Store** — электр жабдықтарын қалаға қарай іздеуге, салыстыруға және тапсырыс беруге арналған хакатондық интернет-дүкен.

Жүйе әр қаладағы баға мен қойма қалдығын бөлек есептейді, қонақ және тіркелген пайдаланушы себетін қолдайды, тапсырыс кезінде тауарды транзакциялық түрде резервтейді және қазақша/орысша AI-ассистент ұсынады.

Каталогтағы атаулар, бағалар, мекенжайлар, жаңалықтар және жеткізу шарттары — синтетикалық демо деректер. Оларды нақты коммерциялық ұсыныс немесе өндіруші растаған техникалық ақпарат ретінде қолдануға болмайды.

> 💡 Инвестициялық өтініш: **өтінемін, 100 000доллар керек** — жобаны production деңгейіне жеткізуге, нақты каталог, төлем жүйесі және логистика интеграциясын қосуға жұмсаймыз.

### Негізгі мүмкіндіктер

- 64 өнімнен тұратын қазақша және орысша демо каталог;
- 39 иерархиялық санат және динамикалық техникалық сипаттамалар;
- 9 қала бойынша аймақтық бағалар;
- 12 қоймадағы тауар қалдығын бақылау;
- іздеу, сүзу, сұрыптау және pagination;
- таңдаулылар және 4 тауарға дейін салыстыру;
- қонақ және тіркелген пайдаланушы себеті;
- checkout және жеткізу құнын есептеу;
- қоймадағы тауарды транзакциялық резервтеу;
- тапсырысты тоқтату және аяқтау сценарийлері;
- JWT авторизациясы;
- `CUSTOMER`, `MANAGER` және `ADMIN` рөлдері;
- әкімшілік CRUD операциялары;
- акциялар, жаңалықтар, FAQ және контент беттері;
- XLSX прайс-парағын қалыптастыру;
- JPG, PNG, WEBP және PDF файлдарын жүктеу;
- Swagger/OpenAPI құжаттамасы;
- қауіпсіз қазақша/орысша AI-ассистент;
- каталог, себет, checkout және аккаунтқа арналған React интерфейсі.

### Архитектура

```text
React 18 + Vite
http://localhost:5173
          │
          │ REST / JSON
          ▼
Express 5 API
http://localhost:3000
          │
          ├── Авторизация
          ├── Каталог
          ├── Себет
          ├── Тапсырыстар
          ├── Контент
          ├── Admin API
          └── AI Assistant
                    │
                    ▼
             Prisma 6
                    │
                    ▼
              PostgreSQL
```

### Жоба құрылымы

```text
.
├── frontend/                  # React 18, TypeScript және Vite
├── backend/                   # Express, Prisma және PostgreSQL
│   ├── prisma/
│   │   ├── migrations/       # Дерекқор migration файлдары
│   │   ├── seed-data/        # Демо каталог және контент
│   │   ├── schema.prisma
│   │   └── seed.js
│   ├── src/
│   │   ├── config/           # Орта және Prisma конфигурациясы
│   │   ├── docs/             # Swagger/OpenAPI
│   │   ├── middleware/       # Auth, validation, rate limit
│   │   └── modules/          # Бизнес модульдер
│   └── tests/                # Jest және Supertest
├── ai/                       # Архивтік migration reference
├── ASSISTANT_MIGRATION.md
├── INTEGRATION_REPORT.md
└── INTEGRATION_API_CONTRACT.md
```

> **Маңызды:** `ai/` бумасы жұмыс істейтін екінші сервер емес. Ол бұрынғы архитектураның архивтік нұсқасы ретінде сақталған. Қолдау көрсетілетін жалғыз сервер — `backend/src/server.js`. AI-ассистент сол backend ішінде жұмыс істейді.

### Қолданылған технологиялар

| Бөлік | Технологиялар |
|---|---|
| Frontend | React 18, TypeScript 5, Vite 6, React Router, Axios |
| Backend | Node.js 20+, Express 5, CommonJS |
| Database | PostgreSQL, Prisma 6 |
| Қауіпсіздік | JWT, bcrypt, Helmet, CORS, rate limiting |
| Тесттер | Jest, Supertest, jsdom |
| API құжаттамасы | OpenAPI 3, Swagger UI |
| AI | Детерминдік intent routing, optional OpenAI classification |

### Жүйелік талаптар

- Node.js 20 немесе одан жаңа нұсқа;
- npm;
- PostgreSQL;
- Git;
- бос `3000` және `5173` порттары.

### Дерекқорды дайындау

PostgreSQL ішінде пайдаланушы мен база жасаңыз:

```sql
CREATE ROLE ekt_app
WITH LOGIN PASSWORD 'CHANGE_ME';

CREATE DATABASE ekt_store
OWNER ekt_app;
```

### Backend орнату

```powershell
cd backend
npm ci
Copy-Item .env.example .env
```

`.env` файлын баптаңыз:

```dotenv
PORT=3000
NODE_ENV=development

DATABASE_URL="postgresql://ekt_app:CHANGE_ME@localhost:5432/ekt_store?schema=public"

JWT_SECRET="REPLACE_WITH_A_LONG_RANDOM_SECRET"
JWT_EXPIRES_IN="7d"

CLIENT_URL="http://localhost:5173"
BCRYPT_ROUNDS=10

OPENAI_API_KEY=""
OPENAI_MODEL="gpt-4.1-mini"
ASSISTANT_LLM_ENABLED=false
ASSISTANT_PROPOSAL_TTL_SECONDS=900

SEED_ADMIN_EMAIL=""
SEED_ADMIN_PASSWORD=""
```

Migration мен демо деректерді қолданыңыз:

```powershell
npm run prisma:generate
npx prisma migrate deploy
npm run prisma:seed
```

Backend серверін іске қосыңыз:

```powershell
npm run dev
```

### Frontend орнату

Жаңа терминал ашыңыз:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Frontend ортасы:

```dotenv
VITE_API_URL=http://localhost:3000/api
VITE_USE_MOCKS=false
```

Құпия кілттерді frontend ортасына жазбаңыз. `VITE_*` айнымалылары браузерге қолжетімді болады.

### Қызмет мекенжайлары

| Қызмет | Мекенжай |
|---|---|
| Web қолданба | http://localhost:5173 |
| REST API | http://localhost:3000/api |
| Health check | http://localhost:3000/api/health |
| Swagger UI | http://localhost:3000/api-docs |

### AI-ассистент

Ассистенттің негізгі endpoint-і:

```http
POST /api/assistant/chat
```

Ассистент:

- нақты каталогтан өнім іздейді;
- актуалды баға мен қойма қалдығын оқиды;
- балама тауарларды ұсынады;
- қазақша және орысша жұмыс істейді;
- пайдаланушы жіберген баға немесе stock мәніне сенбейді;
- себетті пайдаланушының нақты растауынсыз өзгертпейді.

Себетке қосу екі кезеңнен тұрады:

1. Ассистент ұсыныс дайындап, растау сұрайды.
2. Пайдаланушы `Иә, қос` немесе `Да, добавь` деп нақты растағаннан кейін ғана себет өзгереді.

Мысал:

```powershell
$session = [guid]::NewGuid().ToString()

$headers = @{
  "X-Session-Id" = $session
  "Accept-Language" = "kk"
}

$body = @{
  message = "Маған 16А автомат керек"
  sessionId = $session
  city = "almaty"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:3000/api/assistant/chat" `
  -Headers $headers `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

Детерминдік ассистент API кілтінсіз жұмыс істейді. Қосымша LLM классификациясын қосу үшін backend `.env` ішінде:

```dotenv
OPENAI_API_KEY="YOUR_KEY"
ASSISTANT_LLM_ENABLED=true
```

Frontend чат интерфейсі негізгі backend-ке қосылған. Сайттың төменгі оң жағындағы **«ИИ консультант»** батырмасын ашып, «Маған 16А автомат керек» деп жазыңыз. Нәтижеден «Таңдау» арқылы тауарды таңдаңыз; «3 данасын себетке қос» ұсыныс дайындайды, ал бөлек **«Иә, қос»** растауынан кейін ғана себет өзгереді. Қала, JWT және қонақ сессиясы сайтпен ортақ. `ai/.env` және `PORT=3001` қолданылмайды.

Frontend бумасындағы `npm run check:assistant` чаттың UI сценарийлерін тексереді; `npm run check:assistant:integration` іске қосылған backend-пен нақты HTTP байланысын тексереді. Екінші команда тек өзінің уақытша тест деректерін құрып/тазартады.

### API бағыттары

| Модуль | Base path |
|---|---|
| Health | `/api/health` |
| Авторизация | `/api/auth` |
| Пайдаланушылар | `/api/users` |
| Қалалар | `/api/cities` |
| Филиалдар | `/api/branches` |
| Санаттар | `/api/categories` |
| Брендтер | `/api/brands` |
| Өнімдер | `/api/products` |
| Каталог | `/api/catalog` |
| Таңдаулылар | `/api/favorites` |
| Салыстыру | `/api/comparison` |
| Себет | `/api/cart` |
| Тапсырыстар | `/api/orders` |
| Бір басумен тапсырыс | `/api/one-click-orders` |
| Акциялар | `/api/promotions` |
| Жаңалықтар | `/api/news` |
| FAQ | `/api/faqs` |
| Контент беттері | `/api/pages` |
| Клиент өтінімдері | `/api/requests` |
| AI-ассистент | `/api/assistant/chat` |
| Admin | `/api/admin` |

### Тексеру

Backend:

```powershell
cd backend
npm run check
npm test
npm run check:demo
```

Backend іске қосылып тұрғанда:

```powershell
npm run check:assistant
```

Frontend:

```powershell
cd frontend
npm run build
npm run check:contexts
npm run check:pages
```

Backend `3000` портында іске қосылып тұрғанда:

```powershell
npm run check:integration
```

Backend тесттері mock database емес, нақты PostgreSQL қолданады. Тест ортасын оқшаулау үшін `TEST_DATABASE_URL` айнымалысын орнатуға болады.

### Белгілі шектеулер

- төлем провайдері қосылмаған;
- қонақ себеті аккаунт себетімен автоматты біріктірілмейді;
- чаттың көрінетін тарихы бетті жаңартқанда тазарады; сервердегі контекст сақталады, файл жүктеу әлі қосылмаған;
- кейбір сұрыптау және stock сүзгілері жадта орындалады;
- ассистент тарихына production retention cleanup қажет;
- нақты каталог пен контент қосылмаған;
- production алдында қауіпсіздік аудиті және browser smoke test қажет.

---

## 🇷🇺 Русский

### О проекте

**EKT Store** — демонстрационный интернет-магазин электрооборудования с региональными ценами, складскими остатками, корзиной, оформлением заказов и безопасным AI-ассистентом.

Платформа поддерживает казахский и русский языки, гостевые и авторизованные сессии, транзакционное резервирование товаров и управление заказами.

Каталог, цены, адреса, новости и условия доставки являются синтетическими демо-данными. Они не являются реальным коммерческим предложением или подтверждёнными производителем характеристиками.

> 💡 Небольшая инвестиционная просьба: **пожалуйста, нам нужно 100 000 долларов** — на production-запуск, подключение настоящего каталога, платежей и логистики.

### Возможности

- двуязычный каталог из 64 товаров;
- 39 иерархических категорий;
- цены для 9 городов;
- остатки на 12 складах;
- поиск, фильтры, сортировка и пагинация;
- избранное и сравнение до 4 товаров;
- гостевая и пользовательская корзина;
- checkout и расчёт доставки;
- транзакционное резервирование остатков;
- JWT-авторизация;
- роли `CUSTOMER`, `MANAGER` и `ADMIN`;
- административный CRUD;
- акции, новости, FAQ и контентные страницы;
- формирование XLSX-прайса;
- Swagger/OpenAPI;
- AI-ассистент на казахском и русском языках.

### Технологии

| Слой | Технологии |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router, Axios |
| Backend | Node.js 20+, Express 5 |
| Database | PostgreSQL, Prisma 6 |
| Security | JWT, bcrypt, Helmet, CORS, rate limiting |
| Tests | Jest, Supertest, jsdom |
| Documentation | OpenAPI 3, Swagger UI |

### Быстрый запуск

Backend:

```powershell
cd backend
npm ci
Copy-Item .env.example .env
npm run prisma:generate
npx prisma migrate deploy
npm run prisma:seed
npm run dev
```

Перед запуском укажите в `.env` корректные значения `DATABASE_URL` и `JWT_SECRET`.

Frontend запускается в отдельном терминале:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

После запуска:

- приложение — http://localhost:5173;
- API — http://localhost:3000/api;
- health check — http://localhost:3000/api/health;
- Swagger — http://localhost:3000/api-docs.

### AI-ассистент

Endpoint ассистента:

```http
POST /api/assistant/chat
```

Ассистент использует настоящий каталог и актуальные серверные цены. Добавление товара в корзину выполняется только после отдельного явного подтверждения пользователя.

Детерминированный режим работает без API-ключа. Опциональная LLM-классификация включается через backend-переменные:

```dotenv
OPENAI_API_KEY="YOUR_KEY"
ASSISTANT_LLM_ENABLED=true
```

Каталог `ai/` является архивной версией старого сервиса и не должен запускаться. Поддерживаемая реализация ассистента находится внутри `backend/`.

### Проверка проекта

```powershell
# backend/
npm run check
npm test
npm run check:demo
npm run check:assistant

# frontend/
npm run build
npm run check:contexts
npm run check:pages
npm run check:integration
```

### Ограничения

- платёжный провайдер не интегрирован;
- гостевая корзина не объединяется с корзиной аккаунта автоматически;
- чат подключён к основному backend, но история на экране очищается при перезагрузке страницы; загрузка файлов в чат ещё не подключена;
- перед production необходимы аудит безопасности, monitoring и browser smoke test.

---

## 🇬🇧 English

### About

**EKT Store** is a hackathon e-commerce platform for electrical equipment. It combines a multilingual storefront with city-specific pricing, multi-warehouse inventory, transactional checkout, content management, and a safety-focused AI shopping assistant.

All catalog entries, prices, addresses, news, and delivery terms are synthetic demo data. They are not an actual commercial offer and must not be treated as manufacturer-verified specifications.

> 💡 A small funding request: **please, we need 100,000 dollars** to turn the demo into a production product and integrate a real catalog, payments, and logistics.

### Highlights

- bilingual catalog with 64 demo products;
- 39 hierarchical categories;
- city-specific pricing for 9 cities;
- inventory across 12 warehouses;
- search, dynamic filters, sorting, and pagination;
- favorites and comparison of up to 4 products;
- guest and authenticated carts;
- checkout and delivery calculation;
- atomic stock reservations;
- JWT authentication;
- `CUSTOMER`, `MANAGER`, and `ADMIN` roles;
- administrative CRUD operations;
- promotions, news, FAQs, and content pages;
- XLSX price-list generation;
- controlled file uploads;
- OpenAPI and Swagger documentation;
- deterministic Kazakh/Russian AI assistant.

### Technology stack

| Area | Stack |
|---|---|
| Frontend | React 18, TypeScript 5, Vite 6, React Router, Axios |
| Backend | Node.js 20+, Express 5 |
| Database | PostgreSQL, Prisma 6 |
| Security | JWT, bcrypt, Helmet, CORS, rate limiting |
| Testing | Jest, Supertest, jsdom |
| API documentation | OpenAPI 3, Swagger UI |

### Quick start

Prerequisites:

- Node.js 20 or newer;
- npm;
- PostgreSQL;
- Git.

Start the backend:

```powershell
cd backend
npm ci
Copy-Item .env.example .env

# Configure DATABASE_URL and JWT_SECRET

npm run prisma:generate
npx prisma migrate deploy
npm run prisma:seed
npm run dev
```

Start the frontend in another terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Available services:

| Service | URL |
|---|---|
| Web application | http://localhost:5173 |
| REST API | http://localhost:3000/api |
| Health check | http://localhost:3000/api/health |
| Swagger UI | http://localhost:3000/api-docs |

### Assistant safety model

The assistant is available at:

```http
POST /api/assistant/chat
```

It reads server-side product, price, and stock data. Commercial values supplied by the client are not trusted.

Cart additions use a prepare-and-confirm flow:

1. The assistant creates an expiring proposal.
2. It asks the customer for confirmation.
3. The cart is modified only after a separate validated confirmation.

The deterministic assistant works without an API key. Optional provider-assisted intent classification is backend-only and cannot authorize cart mutations.

The top-level `ai/` directory is a disabled migration reference. The supported assistant implementation runs inside the main Express backend.

### Verification

```powershell
# backend/
npm run check
npm test
npm run check:demo
npm run check:assistant

# frontend/
npm run build
npm run check:contexts
npm run check:pages
npm run check:integration
```

Backend tests use PostgreSQL rather than a mock database. Configure `TEST_DATABASE_URL` to isolate test data; otherwise the tests use `DATABASE_URL`.

### Current limitations

- no payment-provider integration;
- guest carts are not automatically merged after sign-in;
- the frontend chat is connected to the main backend; reloading clears visible history (server context persists), and chat file uploads are not yet enabled;
- some sorting and stock filtering operations happen in memory;
- production conversation retention cleanup is required;
- a production rollout requires a security review, monitoring, real content, and browser-level smoke testing.

---

## Additional documentation

- [`backend/README.md`](backend/README.md) — PostgreSQL configuration, seed data, API rules and troubleshooting;
- [`ASSISTANT_MIGRATION.md`](ASSISTANT_MIGRATION.md) — assistant architecture and security model;
- [`INTEGRATION_REPORT.md`](INTEGRATION_REPORT.md) — frontend/backend integration report;
- [`INTEGRATION_API_CONTRACT.md`](INTEGRATION_API_CONTRACT.md) — integration API contract;
- `http://localhost:3000/api-docs` — live Swagger documentation.

## License

The project is currently marked **UNLICENSED**. No permission to copy, modify, or redistribute the project is granted unless the repository owner adds an explicit license.
