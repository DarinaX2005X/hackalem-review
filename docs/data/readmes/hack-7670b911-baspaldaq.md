# BASPALDAQ

<p align="center">
  <strong>От сырой бизнес-идеи — к понятной и готовой к работе задаче.</strong>
</p>

<p align="center">
  HackAlem AI Hackathon · AI-платформа для уточнения и оценки практических бизнес-задач
</p>

## Скриншоты приложения

| Создание задачи | Каталог |
| --- | --- |
| ![Создание задачи](docs/screenshots/home.png) | ![Каталог задач](docs/screenshots/catalog.png) |
| Карточка задачи | Предложения команд |
| ![Карточка задачи](docs/screenshots/task-card.png) | ![Предложения команд](docs/screenshots/proposals.png) |

### Полёт и 3D-сцена

| Запуск ракеты | Поворот к системе |
| --- | --- |
| ![Ракета после отправки описания](docs/screenshots/rocket-launch.png) | ![Поворот ракеты во время полёта](docs/screenshots/rocket-turn.png) |
| Система планет | AI-диалог |
| ![Планеты и ракета в Three.js](docs/screenshots/planet-system.png) | ![Уточнение задачи на фоне планет](docs/screenshots/ai-workspace.png) |

Реальные десктопные кадры приложения. На отдельном снимке системы планет интерфейс временно скрыт для обзора 3D-сцены.


---

## О проекте

**BASPALDAQ** — AI-платформа, которая помогает бизнесу превращать размытые идеи и реальные проблемы в понятные, структурированные практические задания для студенческих команд.

Название происходит от казахского слова **«баспалдақ» — «ступень»**.  
Это отражает основную механику продукта: задача не становится качественной мгновенно — она проходит несколько ступеней уточнения и постепенно становится готовой к работе.

Бизнес может начать даже с очень общего запроса:

> «Нам нужен сервис, который поможет магазинам лучше управлять остатками товаров».

BASPALDAQ анализирует описание, определяет, что уже известно, находит пробелы, задаёт уточняющие вопросы и шаг за шагом формирует полноценную карточку задачи.

---

## Какую проблему решает BASPALDAQ

Бизнес часто хорошо понимает саму проблему, но не всегда может сразу сформулировать её как качественное техническое или практическое задание.

В исходном описании могут отсутствовать:

- целевые пользователи;
- данные и материалы;
- ожидаемый результат;
- критерии успеха;
- ограничения;
- формат взаимодействия с бизнесом.

Для студенческой команды это означает неопределённость ещё до начала работы.

**BASPALDAQ помогает убрать эту неопределённость до того, как задача попадёт к студентам.**

---

## Что реализовано

В текущем MVP предусмотрены:

- ввод бизнес-задачи в свободной форме;
- AI-анализ исходного описания;
- извлечение только тех фактов, которые действительно предоставил пользователь;
- определение недостающей информации;
- генерация релевантных уточняющих вопросов;
- последовательное уточнение задачи через ответы пользователя;
- структурирование полученной информации;
- readiness score от **0 до 100**;
- прозрачный breakdown оценки по критериям;
- автоматический пересчёт готовности после новых подтверждённых данных;
- хранение состояния в **SQLite**;
- backend API на Express;
- валидация входных данных;
- обработка ошибок AI/API;
- health-check endpoint;
- frontend на React;
- адаптивный интерфейс и анимации.

Ключевой принцип архитектуры:

> **AI помогает понять и структурировать задачу, но не определяет итоговый числовой рейтинг.**

---

## Основной пользовательский сценарий

```text
Бизнес описывает проблему
        ↓
AI анализирует описание
        ↓
Определяются известные факты и пробелы
        ↓
AI задаёт уточняющие вопросы
        ↓
Бизнес отвечает
        ↓
Поля задачи становятся полнее
        ↓
Readiness score пересчитывается
        ↓
Формируется структурированная карточка
        ↓
Бизнес проверяет и подтверждает её
        ↓
Задача публикуется
        ↓
Студенческая команда отправляет предложение
        ↓
Бизнес вручную принимает или отклоняет предложение
```

Главное правило:

> **AI не должен придумывать факты, которых пользователь не сообщал.**

Если бизнес не указал дедлайн, данные, пользователей, критерии успеха или другие детали, BASPALDAQ оставляет их неизвестными и предлагает уточнить.

---

## Readiness Score

Готовность задачи оценивается по семи критериям:

| Критерий | Максимум |
|---|---:|
| Контекст и потребность | 20 |
| Данные и материалы | 20 |
| Ожидаемый результат | 15 |
| Критерии успеха | 15 |
| Ограничения | 10 |
| Пользователи | 10 |
| Взаимодействие с бизнесом | 10 |
| **Итого** | **100** |

Уровни готовности:

| Баллы | Уровень |
|---:|---|
| 0–39 | Draft |
| 40–69 | Workable |
| 70–89 | Ready |
| 90–100 | Priority |

LLM **не выставляет итоговый балл самостоятельно**.

```text
AI → понимает и структурирует текст
Backend → рассчитывает readiness
SQLite → хранит состояние
Frontend → показывает прогресс и результат
```

Формула итоговой оценки детерминирована при одинаковой классификации критериев. Сама AI-классификация текста может отличаться между запросами.

---

## Технологии

### Frontend

- React
- Three.js, React Three Fiber и Drei
- Vite
- JavaScript
- Tailwind CSS
- Motion for React
- GSAP
- Lenis
- Radix UI
- Hugeicons
- dotLottie
- Howler.js
- TanStack Query
- Zustand
- React Router
- React Hook Form
- Zod

### Backend

- Node.js
- Express
- JavaScript
- Prisma ORM
- SQLite
- Zod

### AI

- Vercel AI SDK
- OpenAI API
- structured AI responses
- серверная обработка AI-запросов

API-ключ AI-провайдера хранится только на backend через environment variables и не передаётся в браузер.

---

## Архитектура

```text
┌─────────────────────────────┐
│        React Frontend       │
│                             │
│ UI · State · Motion · Forms │
└──────────────┬──────────────┘
               │ HTTP / JSON
               ▼
┌─────────────────────────────┐
│       Express Backend       │
│                             │
│ Routes · Validation         │
│ AI Services                 │
│ Readiness Engine            │
└───────────┬─────────┬───────┘
            │         │
            │         └──────────────► LLM API
            │
            ▼
┌─────────────────────────────┐
│      Prisma + SQLite        │
│                             │
│ Tasks · Questions · Answers │
│ Readiness State             │
└─────────────────────────────┘
```

Секретный API-ключ никогда не должен попадать во frontend:

```text
Browser → BASPALDAQ API → LLM Provider
```

---

## Структура проекта

```text
baspaldaq/
├── client/
│   ├── src/
│   └── package.json
├── server/
│   ├── prisma/
│   ├── src/
│   └── package.json
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

Проект сознательно остаётся компактным: без лишних микросервисов и тяжёлой инфраструктуры, которая не помогает основному сценарию хакатона.

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/BAITC-Hacks/hack-7670b911-baspaldaq.git
cd hack-7670b911-baspaldaq
```

### 2. Установить зависимости

```bash
npm ci
```

### 3. Настроить переменные окружения

Создайте локальный `.env` на основе `.env.example` и заполните необходимые значения.

Пример:

```env
PORT=3000
CLIENT_ORIGIN=http://localhost:5173
DATABASE_URL="file:./dev.db"
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
AI_TIMEOUT_MS=30000
VITE_API_URL=http://localhost:3000
```

Настоящий API-ключ нельзя добавлять в GitHub.

### 4. Подготовить Prisma / SQLite

```bash
npm run prisma:generate
npm run prisma:deploy
```

---

## Запуск

Из корня проекта:

```bash
npm run dev
```

Одна команда запускает **frontend и backend одновременно**.

Не нужно открывать два терминала и запускать серверы отдельно.

После старта Vite и Express выведут актуальные локальные адреса в консоль.

Проверка backend:

```http
GET /api/health
```

---

## Как жюри может проверить решение

### 1. Ввести слабое описание

```text
Хотим сервис, который поможет магазинам лучше управлять остатками товаров.
```

### 2. Запустить AI-анализ

Система должна определить:

- что уже понятно;
- какой информации не хватает;
- какие уточняющие вопросы стоит задать;
- текущий уровень готовности задачи.

### 3. Ответить на уточняющий вопрос

Например:

```text
Сервисом будут пользоваться менеджеры наших магазинов.
```

После этого BASPALDAQ должен:

- использовать только информацию из ответа;
- обновить соответствующий критерий;
- пересчитать readiness;
- предложить следующий релевантный вопрос.

### 4. Продолжить уточнение

По мере заполнения задачи её уровень готовности должен расти:

```text
Draft → Workable → Ready → Priority
```

### 5. Проверить итоговую карточку

Результат должен быть понятен без необходимости перечитывать весь AI-диалог.

Финальный end-to-end сценарий проекта:

```text
слабая идея
→ AI-уточнение
→ рост readiness
→ карточка задачи
→ подтверждение
→ публикация
→ предложение студенческой команды
→ ручное решение бизнеса
```

---

## Данные и интеграции

BASPALDAQ использует:

- исходные описания задач от бизнеса;
- ответы на уточняющие вопросы;
- SQLite для локального хранения данных;
- Prisma ORM для работы с базой;
- внешний LLM API для анализа текста и генерации уточняющих вопросов.

Секретные ключи не хранятся в репозитории.

---

## Защита от галлюцинаций

Один из ключевых принципов BASPALDAQ:

> **AI не добавляет в задачу сведения, которых бизнес не предоставлял.**

Если данных недостаточно, система должна:

- оставить поле неизвестным;
- определить пробел;
- задать уточняющий вопрос.

AI может структурировать ответ пользователя, но не должен подменять пользователя и придумывать недостающие факты. Backend проверяет наличие источника и точное вхождение цитаты в пользовательский текст. Это снижает риск выдуманных сведений, но не гарантирует семантическую правильность каждого вывода: итоговую карточку обязательно проверяет человек.

---

## Безопасность и надёжность

- API-ключи находятся только на backend;
- `.env` исключён из Git;
- пользовательский ввод проходит валидацию;
- AI-ответы обрабатываются в структурированном формате;
- readiness рассчитывается детерминированно;
- frontend не увеличивает баллы вручную;
- AI не выбирает студенческую команду вместо бизнеса.

---

## Ограничения MVP

BASPALDAQ создаётся в рамках 5-часового HackAlem AI Hackathon, поэтому проект сфокусирован на основном end-to-end сценарии.

В текущий scope не входят:

- полноценная регистрация и восстановление пароля;
- сложная система ролей;
- realtime chat;
- уведомления;
- календарь;
- файловое хранилище;
- обучение собственной ML-модели;
- vector database;
- полноценный project tracker;
- микросервисная инфраструктура.

Цель проекта — не построить самый большой продукт.

Цель — показать, как AI может сделать бизнес-задачу действительно готовой к работе.

---

## Репозиторий

**GitHub:**  
https://github.com/BAITC-Hacks/hack-7670b911-baspaldaq

---

## Deployed-версия

Публичный деплой пока не выполнен. Код опубликован в GitHub, приложение запускается локально по инструкции ниже. Для внешнего доступа необходимы отдельно размещённые frontend и API, постоянное хранилище SQLite и настройка переменных окружения.

---


## Роли и полный цикл работы

| Роль | Возможности |
| --- | --- |
| Бизнес | Создание и уточнение задачи, редактирование карточки, подтверждение, публикация, просмотр предложений, ручной выбор команд и подтверждение этапов |
| Студенческая команда | Профиль команды, просмотр каталога, отправка идеи решения, плана, сроков и ссылки на прототип |

Переключение роли является навигацией, а не авторизацией. В MVP нет изолированных личных кабинетов: нельзя использовать его для конфиденциальных заявок в открытом интернете без дополнительной защиты.

### Поля карточки

| Поле API | Содержание |
| --- | --- |
| `title` | Название задачи |
| `context` | Текущая ситуация бизнеса |
| `need` | Проблема или потребность |
| `users` | Пользователи решения |
| `dataMaterials` | Доступные данные и материалы |
| `constraints` | Ограничения |
| `expectedResult` | Ожидаемый результат |
| `successCriteria` | Проверяемые критерии успеха |
| `contact` | Контакт со стороны бизнеса |
| `interactionFormat` | Формат совместной работы |

### Поведение AI-диалога

Вопросы показываются последовательно. Полезный ответ запускает повторный анализ и пересчёт полноты. Неясный ответ приводит к уточнению с подсказкой; повторная неудачная попытка позволяет перейти дальше, не задерживая пользователя на одном вопросе. Вопрос можно пропустить явно.

Если пользователь вместо ответа задаёт собственный вопрос, AI может кратко ответить отдельным сообщением, не засчитывая его как заполнение критерия. Пропуск и неподтверждённые догадки не должны искусственно повышать готовность.

Наличие текста само по себе не означает полноту. Ручные изменения проходят AI-проверку содержания: заполнение всех полей словами «Не знаю» не даёт 100 баллов. Новый принятый ответ или редактирование снимает финальное подтверждение; перед публикацией карточку нужно подтвердить заново.

### Интерфейс и 3D

Тёмный интерфейс включает полупрозрачные поверхности, анимированный ввод, сцену с ракетой и планетами на Three.js и звуковое сопровождение. Ракета запускается после отправки описания. AI-диалог работает в полноэкранном интерфейсе с последовательными вопросами; текст отправляется Enter, Shift+Enter добавляет строку.

### Что сохраняется в базе

Prisma-модели хранят задачи, поля с происхождением и доказательствами, оценки критериев, вопросы, ответы, сообщения диалога, команды, предложения и этапы. SQLite сохраняет эти записи между перезапусками приложения. Файл базы и секреты не отправляются в GitHub; схема, миграции и сценарий наполнения входят в репозиторий.

### Навигация

| Адрес | Экран |
| --- | --- |
| `/business/new` | Новая задача и AI-уточнение |
| `/business` | Задачи бизнеса |
| `/business/tasks/:taskId` | Работа с задачей |
| `/business/tasks/:taskId/review` | Проверка карточки |
| `/business/tasks/:taskId/proposals` | Предложения и решения бизнеса |
| `/catalog` | Каталог опубликованных задач |
| `/tasks/:taskId` | Карточка для команды |
| `/tasks/:taskId/proposal` | Отправка предложения |
| `/team` | Профиль команды |

## Техническое руководство

Ниже сохранены точные команды, API, параметры оценки, тестирование и границы развёртывания. Для установки JavaScript-зависимостей используются `package.json` и `package-lock.json`, отдельный `requirements.txt` не нужен.

## Run Locally

Requires Node.js 20.19+ and npm 10+. `package-lock.json` locks the JavaScript dependencies; this project does not need Python's `requirements.txt`. On Windows, the fastest setup is:

```powershell
.\scripts\setup.ps1 -Seed
```

Omit `-Seed` to start with an empty database. The script creates `.env` only if it is missing, installs exact dependencies with `npm ci`, generates Prisma Client, and applies migrations. It never overwrites an existing `.env`.

The equivalent manual commands are:

```powershell
npm ci
Copy-Item .env.example .env
npm run prisma:generate
npm run prisma:deploy
npm run dev
```

Set `OPENAI_API_KEY` only in the ignored local `.env`. Set `PORT`, `CLIENT_ORIGIN`, `DATABASE_URL` and `VITE_API_URL` there as needed. Vite prints the frontend URL. The API listens on `PORT`; `GET /api/health` checks the database connection. The default SQLite file is `server/prisma/dev.db`.

The role switch is in the navigation: business creates and manages tasks; student teams use the catalog and team profile. Open `/business` for tasks, `/catalog` for published tasks, and `/team` to create or update a team profile. Browser storage remembers only the selected team ID; all tasks, teams, proposals, decisions and milestone points live in SQLite.

## Demo Data

```powershell
npm run db:seed
```

This idempotent command adds five synthetic drafts, five published task cards, five synthetic teams and five proposals. Their IDs begin with `demo-`, and their prototype links are illustrative, not live team projects. It does not overwrite existing records. Production seeding requires `ALLOW_DEMO_SEED=true` explicitly.

## Main API

| Action | Endpoint |
| --- | --- |
| Save draft | `POST /api/tasks` |
| Analyze draft | `POST /api/tasks/:id/analyze` |
| Answer or skip | `POST /api/tasks/:id/answers` |
| Read task/questions | `GET /api/tasks/:id`, `GET /api/tasks/:id/questions` |
| Edit card | `PATCH /api/tasks/:id` |
| Confirm and publish | `POST /api/tasks/:id/confirm`, `POST /api/tasks/:id/publish` |
| Catalog | `GET /api/tasks?published=true&readiness=ready&topic=...&sort=score_desc` |
| Teams | `GET/POST /api/teams`, `GET/PATCH /api/teams/:id` |
| Proposals | `GET/POST /api/tasks/:id/proposals`, `GET /api/proposals/:id`, `PATCH /api/proposals/:id/status` |
| Milestones | `GET/POST /api/tasks/:id/milestones`, `PATCH /api/milestones/:id/confirm` |

Readiness is `draft` (0-39), `workable` (40-69), `ready` (70-89), or `priority` (90-100). Every published task remains in the catalog, including low-scoring ones. Proposals have `PENDING`, `ACCEPTED`, or `REJECTED` status. The business can accept several teams or none. Confirming a milestone for an accepted team awards 10 points exactly once.

## Rating Formula

Readiness is the rounded sum of seven weighted criteria: context and need (20), data and materials (20), expected result (15), success criteria (15), constraints (10), users (10), and business contact plus interaction format (10). A missing criterion earns zero, partial completeness earns half its weight, and complete earns its full weight. Evidence must reference the user's actual input. Manual edits are semantically assessed by AI as well: nonempty text such as "I do not know" does not earn completeness points.

The immediate conversational score reflects grounded user input before final card approval. Publication requires explicit human confirmation. Editing the card or accepting another clarification answer invalidates that confirmation and requires approval again.

## Five-Minute Demo

1. Minute 0-1: open `/business/new`, describe lost orders in a shop's spreadsheets, and submit. Show the initial score and the AI's clarification questions.
2. Minute 1-2: answer with concrete users (12 shop managers and 3 delivery staff), available data (an anonymized CSV of orders), and an expected result (a web order tracker). Show the score changing and the explanation of missing information.
3. Minute 2-3: review the editable card, add measurable acceptance criteria (every order has a responsible manager and delivery status), confirm, and publish. The catalog also contains lower-readiness tasks; they remain open for proposals.
4. Minute 3-4: switch to the team role, open a seeded task, and submit an idea, plan, timeline, and prototype link from a team profile.
5. Minute 4-5: switch back to business, manually accept a proposal, create and confirm a milestone, and show the team's points. Use seeded proposals if time is short. Refresh the page to demonstrate database persistence.

## Validation

```powershell
npm run prisma:validate
npm test --workspace server
npm run build
```

The browser test needs Microsoft Edge (or `BROWSER_EXECUTABLE`) and a local running app with at least one published task. It captures desktop and mobile screenshots in `client/screenshots/`, verifies wheel scrolling, and clicks through publish, proposal, business decision, and milestone confirmation. These screenshots and the space-scene capture script are included in the repository. Temporary records are removed after the test.

```powershell
$env:TEST_BASE_URL = 'http://localhost:5173'
npm run test:ui
```

## Deployment Boundary

For a separately hosted client, set `VITE_API_URL` to the public API origin at build time and `CLIENT_ORIGIN` to the exact allowed frontend origin. Use persistent writable storage for SQLite; an ephemeral disk loses data on redeploy. Run `npm run prisma:generate` and `npm run prisma:deploy` before `npm start`.

This hackathon MVP intentionally has no login or authorization, as allowed by the brief. Role selection is a workflow convenience, **not access control**: proposal decisions and task edits are not protected from other visitors. Add real identity and authorization before exposing it as a production multi-tenant service.

---

<p align="center">
  <strong>BASPALDAQ</strong><br/>
  Одна идея. Яснее с каждой ступенью.
</p>

<p align="center">
  Made with ❤️ by <strong>AKadil ALish</strong>
</p>
