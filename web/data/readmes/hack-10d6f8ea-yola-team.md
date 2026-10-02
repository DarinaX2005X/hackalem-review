# Sana Hub — AI Sana Challenge Hub

Рабочий MVP для трека HackAlem / AI Sana «от бизнес-задачи к решению».

Sana Hub превращает короткое описание потребности бизнеса в редактируемую карточку задачи: AI находит пробелы и задаёт уточняющие вопросы, приложение прозрачно рассчитывает готовность, а бизнес вручную подтверждает и публикует задачу. Студенты находят её в общем каталоге, отправляют предложения, после чего бизнес самостоятельно принимает или отклоняет каждое из них.

## Что работает

- серверная регистрация и вход для ролей Business и Student;
- серверные профили и opaque-сессии в SQLite;
- HttpOnly cookie без JWT или session token в `localStorage`;
- реальный server-side OpenAI flow с настраиваемой моделью;
- динамические AI-вопросы и валидируемый fallback;
- редактируемая карточка и обязательное подтверждение человеком;
- детерминированный score 0–100 с breakdown и рекомендациями;
- общий каталог, поиск, фильтры и сортировка;
- student proposals и ручные решения бизнеса без auto-assignment;
- сохранение demo-задач, откликов и незавершённой карточки после refresh.

> Важная граница MVP: аккаунты, сессии и профили уже хранятся на сервере. Задачи, каталог и отклики пока остаются demo-данными в `localStorage` и не являются серверно-авторизованными. Их миграция в БД — отдельный следующий этап.

## Архитектура и стек

```text
Browser SPA (HTML/CSS/vanilla JS, hash routes)
        │
        ├── /api/auth/* + HttpOnly cookie
        │           ▼
        │     Node.js native http
        │           ▼
        │     SQLite / better-sqlite3
        │     users + profiles + sessions
        │
        └── POST /api/ai/analyze
                    ▼
              OpenAI Responses API
              validated local fallback

Demo tasks / catalog / proposals → validated localStorage store
Readiness score                 → deterministic application module
```

- Frontend: HTML5, CSS, vanilla JavaScript, ES modules.
- Backend: native `node:http`, без Express.
- Database: SQLite через `better-sqlite3`.
- Passwords: встроенный `crypto.scrypt` с уникальной солью.
- Sessions: случайный 256-bit opaque token; в БД хранится только SHA-256 hash.
- AI: OpenAI Responses API и Structured Outputs JSON Schema.
- Tests: встроенный `node:test` и временные SQLite-БД.

## Быстрый запуск для жюри

Требуется Node.js 18+; рекомендуется Node.js 20 LTS.

```bash
git clone https://github.com/BAITC-Hacks/hack-10d6f8ea-yola-team.git
cd hack-10d6f8ea-yola-team
npm install
npm start
```

Откройте [http://localhost:4173](http://localhost:4173). Другой порт задаётся через `PORT`.

Без `OPENAI_API_KEY` весь сквозной сценарий работает через локальный AI fallback. Для проверки реального OpenAI скопируйте конфигурацию:

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash/zsh:

```bash
cp .env.example .env
```

Затем укажите собственный ключ в локальном `.env`:

```dotenv
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=medium
OPENAI_TIMEOUT_MS=30000
SESSION_TTL_MS=604800000
```

Файл `.env` исключён из Git, не входит в production bundle и не выдаётся static server. Настоящих API-ключей и demo-паролей в репозитории нет.

## SQLite и production deployment

Путь БД задаётся через `DATABASE_PATH`.

- Без переменной БД создаётся вне public static root, в соседней с проектом папке `.sana-hub-data/sana-hub.sqlite`.
- Для production `DATABASE_PATH` обязан указывать на постоянный writable volume сервера.
- SQLite-файл, `-wal` и `-shm` нельзя хранить в Git или в публичной static-директории.
- При `NODE_ENV=production` session cookie автоматически получает атрибут `Secure`.

Пример production-конфигурации:

```dotenv
NODE_ENV=production
DATABASE_PATH=/var/lib/sana-hub/sana-hub.sqlite
OPENAI_API_KEY=your-server-secret
OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=medium
SESSION_TTL_MS=604800000
```

GitHub Pages для проекта недостаточно: он не запускает Node.js backend и не может безопасно хранить API-ключ или SQLite. Для публичной ссылки нужен Node.js-хостинг с persistent volume и server-side environment variables.

## Регистрация, вход и профиль

1. Пользователь регистрируется через `#/register`, выбирая Business или Student.
2. Backend нормализует email, проверяет пароль и сохраняет только scrypt hash и salt.
3. Backend создаёт opaque session token, сохраняет только его SHA-256 hash и устанавливает HttpOnly cookie.
4. SPA загружает сессию через `GET /api/auth/me`; роль интерфейса приходит только с сервера.
5. Onboarding и редактирование профиля используют `PUT /api/auth/profile`.
6. Выход отзывает серверную сессию и очищает cookie.

Cookie: `HttpOnly`, `SameSite=Lax`, `Path=/`; `Secure` включается в production. Пароль, salt, password hash и session token никогда не возвращаются в JSON. Истёкшие сессии удаляются и игнорируются.

### Auth API

| Метод | Endpoint | Назначение |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Создать аккаунт и сессию |
| `POST` | `/api/auth/login` | Войти и создать новую сессию |
| `POST` | `/api/auth/logout` | Отозвать текущую сессию |
| `GET` | `/api/auth/me` | Получить безопасного user с profile или `null` |
| `PUT` | `/api/auth/profile` | Сохранить профиль согласно серверной роли |

Минимальная длина пароля — 8 символов. Повторный email возвращает `409`, неверные credentials — одинаковую безопасную ошибку `401`.

### SQLite schema

- `users`: `id`, нормализованный unique `email`, `password_hash`, `password_salt`, `role`, timestamps;
- `profiles`: `user_id`, `name`, поля business/student onboarding, timestamp;
- `sessions`: `id`, `user_id`, `token_hash`, `expires_at`, `created_at`.

## AI flow и безопасность фактов

1. Browser отправляет описание и текущее состояние карточки на `POST /api/ai/analyze`.
2. Backend передаёт описание, карточку, предыдущие вопросы, ответы и обязательную схему в OpenAI.
3. Structured Output валидируется на backend.
4. При наличии пробелов UI показывает минимум три релевантных вопроса и редактируемый результат.
5. До ручного подтверждения карточка остаётся черновиком.

AI использует только факты пользователя. Он не должен придумывать бюджет, сроки, технологии, данные, контакты, пользователей, ограничения или критерии успеха. При timeout, network/API error, пустом или malformed ответе backend возвращает fallback того же контракта, и UI продолжает работать.

## Формула готовности

| Категория | Максимум |
| --- | ---: |
| Контекст и потребность | 20 |
| Данные и материалы | 20 |
| Ожидаемый результат | 15 |
| Критерии успеха | 15 |
| Ограничения | 10 |
| Пользователи | 10 |
| Связь с бизнесом | 10 |
| Итого | 100 |

Уровни: 0–39 — Черновик; 40–69 — Рабочая; 70–89 — Готовая; 90–100 — Приоритетная. Пустые, неподтверждённые поля и «Требуется уточнение» не получают баллы.

## Каталог и предложения

- Все опубликованные demo-задачи видимы, включая low-score cards.
- По умолчанию задачи сортируются по score по убыванию.
- Есть поиск и фильтры по теме и readiness level.
- Предложение может отправить только вошедший Student с заполненным профилем.
- В demo-store создаётся производная команда `user-{id}` текущего student account.
- AI никогда не выбирает и не назначает команду.
- Business вручную принимает или отклоняет предложения.

## Demo data

В `src/data.js` находятся синтетические данные:

- 5 слабых task drafts;
- 5 подтверждённых опубликованных task cards;
- 5 профилей demo-команд;
- 5 proposals с разными статусами.

Серверные user accounts и пароли не seed-ятся. Для демонстрации зарегистрируйте новые Business и Student аккаунты через UI. `resetSanaDemo()` сбрасывает только demo-store задач/команд/откликов и не изменяет серверные аккаунты или сессии.

## Demo script — до 5 минут

1. Открыть приложение без сессии: в header видны «Регистрация» и «Вход».
2. Зарегистрировать Business, заполнить профиль и создать короткую задачу.
3. Показать AI-вопросы, карточку, рост score и публикацию.
4. Выйти через профиль.
5. Зарегистрировать Student, заполнить профиль и открыть каталог.
6. Отправить proposal от производной команды текущего пользователя.
7. Выйти, войти обратно как Business и вручную принять или отклонить proposal.
8. Обновить страницу и показать сохранение server profile/session и demo-flow.

## Маршруты

- `#/home` — landing;
- `#/register`, `#/login` — регистрация и вход;
- `#/onboarding/business`, `#/onboarding/student` — серверный профиль;
- `#/profile` — профиль и logout;
- `#/business/dashboard` — кабинет Business;
- `#/business/intake`, `#/business/card` — AI-конструктор карточки;
- `#/business/proposals` — ручное решение Business;
- `#/catalog`, `#/task/:id` — общий каталог и задача.

Unauthenticated пользователь перенаправляется с profile/onboarding/business routes на регистрацию или вход. Student не получает business UI, а Business не получает student proposal form.

## Проверки и production bundle

```bash
npm install
npm run check
npm run secret-scan
npm run build
```

Текущий набор содержит 35 тестов: auth/database/session, AI, scoring, store, catalog, proposals и HTTP server. Auth-тесты используют отдельный временный `DATABASE_PATH` и не создают demo accounts в рабочей БД.

`npm run build` создаёт папку `dist/` вместе с `package-lock.json`. Standalone bundle запускается так:

```bash
cd dist
npm install --omit=dev
node server.mjs
```

Для production перед запуском обязательно подключите persistent writable volume и задайте абсолютный `DATABASE_PATH`.

## Структура проекта

```text
.
├── index.html
├── server.mjs                    # static server + AI/auth API routes
├── src/
│   ├── app.js                    # SPA routes, auth UI and MVP flow
│   ├── store.js                  # demo task/proposal local persistence
│   ├── config/env.mjs            # server-only .env loader
│   ├── db/database.mjs           # SQLite path, schema and initialization
│   └── services/
│       ├── auth-crypto.mjs       # scrypt, opaque tokens and SHA-256
│       ├── auth-service.mjs      # users, profiles and sessions
│       ├── auth-http.mjs         # auth HTTP handlers and cookie policy
│       ├── ai-server.mjs         # server-only OpenAI integration
│       ├── ai.js                 # browser-safe fallback/validation
│       ├── scoring.js
│       ├── marketplace.js
│       └── card-change.js
├── tests/                        # isolated auth DB/API and MVP tests
├── scripts/                      # build and secret scan
├── package.json
├── package-lock.json
└── .env.example
```

## Out of scope

Нет OAuth, email verification, восстановления пароля, внешних auth providers, сложной RBAC, чата, уведомлений, календаря, файлового хранилища, vector database, собственной ML-модели или production project tracker. Перенос task/proposal данных из demo `localStorage` в серверную БД также остаётся следующим этапом.
