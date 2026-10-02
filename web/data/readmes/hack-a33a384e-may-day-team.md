[Русский](README.md) | [Қазақша](README.kz.md) | [English](README.en.md)

# Career Quest

Career Quest помогает сотруднику дойти до следующего грейда текущей роли: движок считает навыки, требования и допустимые активности, а OpenAI выбирает из этого списка 1–3 шага и объясняет выбор. Если модель недоступна, тот же сценарий продолжается через явный серверный fallback.

## Что решает

Employee:

профиль → next grade → gaps → recommendation → WHY THIS, NOT THAT → Complete → recalculation.

HR:

gaps → employees without next step → participation → hidden/test profile import.

Основная цель — следующий грейд текущей роли: `Junior → Middle → Senior → Lead`. Межролевой `career_goal` показывается отдельно и не подменяет эту цель. Для Lead следующий грейд не выдумывается. Выполнение требований не повышает сотрудника автоматически. Публичного рейтинга сотрудников нет.

Отметка выполнения сохраняется на сервере и пересчитывает навыки. Это модель завершения в прототипе, а не подтверждение обучения во внешней LMS.

## Что уже работает

На ветке `final/submission`:

- Employee/HR demo login;
- profile;
- trajectory / next-grade requirements;
- deterministic candidate engine;
- OpenAI recommendation 1–3;
- explanation;
- fallback;
- completion;
- progress recalculation;
- refreshed recommendations;
- HR overview;
- multipart import;
- responsive frontend;
- one-command launcher.

`POST /api/auth/demo-login` — вход для hackathon demo. Обычный `POST /api/auth/login` с username и password тоже есть. Экран входа demo использует кнопки Employee и HR.

## Почему это не ChatGPT-wrapper

DETERMINISTIC CODE:

- replay skills;
- current levels;
- next grade;
- requirements;
- gaps;
- prerequisites;
- eligibility;
- event effects;
- participation facts.

AI:

- получает только разрешённых candidates;
- сравнивает;
- выбирает 1–3;
- объясняет;
- structured JSON;
- server-side validation.

В payload модели не входят полное имя, отдел, руководитель и сырая история. Передаются роль, грейд, цель и факты допустимых активностей. Модель не создаёт мероприятия, уровни, требования или историю.

Fallback срабатывает при:

- missing key;
- timeout;
- provider error;
- invalid output.

Сервер возвращает `selection_status=fallback_ranked` и `fallback_reason`: `missing_api_key`, `timeout`, `provider_error` или `invalid_ai_output`. Это не числовой AI-score.

Frontend при `fallback_ranked` пишет «Рекомендуемый шаг» и не называет ответ AI. Подпись «AI · Рекомендуемый шаг» остаётся только при `used_ai=true`. Пустой список показывает «Рекомендация временно недоступна».

## Архитектура

```text
Dataset
  ↓
Validated Loader
  ↓
Deterministic Career Engine
  ↓
FastAPI
  ├ Auth / Sessions / CSRF
  ├ Employee API
  ├ Completion
  ├ HR / Import
  └ OpenAI Recommendation Layer
  ↓
PostgreSQL

React/Vite → FastAPI
```

Расчётный engine не зависит от FastAPI, PostgreSQL и OpenAI. `GET /api/health` проверяет процесс backend. `GET /api/ready` проверяет соединение с PostgreSQL.

## Stack

Backend:

- Python 3.10+
- FastAPI 0.116.1
- SQLAlchemy 2.0.43
- Alembic 1.16.5
- PostgreSQL
- psycopg 3.2.9

AI:

- OpenAI Responses API
- OpenAI SDK 2.8.1
- strict JSON Schema
- `OPENAI_MODEL` configurable
- live smoke: `gpt-5.6-terra`

Frontend:

- React 19
- Vite 8
- Inter
- CSS
- local SVG icons

Auth:

- server-side sessions
- HttpOnly cookie
- CSRF
- Employee/HR authorization

## Dataset

Dataset синтетический.

Подтверждённые размеры:

- 60 skills
- 32 role profiles
- 200 employees
- 40 events
- 2743 history rows

Raw official dataset в git не хранится. `DATASET_PATH` указывает на папку. В ней обязательно:

```text
career_quest_dataset/
├── skills.json
├── employees.json
├── events.json
└── activity_history.csv
```

Содержимое official dataset в документацию не входит.

## Запуск одной командой

После установки зависимостей, PostgreSQL, dataset и `.env`:

```powershell
python scripts/start.py
```

Launcher запускает backend и Vite. Зависимости не устанавливает. Ctrl+C или Ctrl+Break останавливает оба процесса.

Адреса: backend `http://127.0.0.1:8000`, frontend `http://127.0.0.1:5173`.

Final smoke на Windows: backend started, frontend started, `/api/health` → 200, `/api/ready` → 200, ports closed after stop. Launcher реализован cross-platform; фактический final smoke выполнен на Windows.

Полная установка с чистого ПК: [docs/SETUP.md](docs/SETUP.md).

## ENV

Скопируйте `.env.example` в `.env`. Реальные секреты в репозиторий не кладутся. Полное объяснение — в [docs/SETUP.md](docs/SETUP.md).

| Переменная | Обязательна | Назначение |
|---|---|---|
| `DATABASE_URL` | да, для рабочего запуска | PostgreSQL. Разрешены только `career_quest_dev` и `career_quest_test` |
| `DATASET_PATH` | да, для рабочего запуска | Папка четырёх файлов dataset |
| `ALLOWED_ORIGINS` | нет | Origin для cookie-запросов. Default: `http://127.0.0.1:5173,http://localhost:5173` |
| `COOKIE_SECURE` | нет | `Secure` у session cookie. Default: `false` |
| `SESSION_TTL_HOURS` | нет | Срок серверной сессии. Default: `12` |
| `DEMO_EMPLOYEE_ONE_USERNAME` | вместе с остальными `DEMO_*` | Логин первого demo employee |
| `DEMO_EMPLOYEE_ONE_PASSWORD` | вместе с остальными `DEMO_*` | Пароль первого demo employee |
| `DEMO_EMPLOYEE_ONE_ID` | вместе с остальными `DEMO_*` | `employee_id` в загруженном dataset |
| `DEMO_EMPLOYEE_TWO_USERNAME` | вместе с остальными `DEMO_*` | Логин второго demo employee |
| `DEMO_EMPLOYEE_TWO_PASSWORD` | вместе с остальными `DEMO_*` | Пароль второго demo employee |
| `DEMO_EMPLOYEE_TWO_ID` | вместе с остальными `DEMO_*` | `employee_id` в загруженном dataset |
| `DEMO_HR_USERNAME` | вместе с остальными `DEMO_*` | Логин demo HR |
| `DEMO_HR_PASSWORD` | вместе с остальными `DEMO_*` | Пароль demo HR |
| `OPENAI_API_KEY` | нет | Ключ OpenAI, только на сервере. Пустое значение включает `fallback_ranked` |
| `OPENAI_MODEL` | нет | ID модели. Default: `gpt-5.6-terra` |
| `OPENAI_TIMEOUT_SECONDS` | нет | Таймаут вызова. Default: `7` |

Пример URL без реального секрета:

```text
postgresql+psycopg://career_quest:CHANGE_ME@127.0.0.1:5432/career_quest_dev
```

Если используется demo config, все `DEMO_*` должны быть заполнены. Frontend-секреты не нужны: `VITE_OPENAI_KEY` и `VITE_DATABASE_URL` не требуются и быть не должны.

## Build и тесты

Frontend, воспроизводимая установка:

```powershell
cd frontend
npm ci
npm run build
npm run lint
```

На final assembly `npm run lint` и `npm run build` — PASS.

Backend:

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m pytest -q
```

Final assembly: `40 passed`, `5 skipped`. Пять PostgreSQL-тестов пропущены, потому что `DATABASE_URL` не был направлен на `career_quest_test`. Skipped не считаются passed.

Ранее, на PostgreSQL milestone при `DATABASE_URL` на `career_quest_test`: `42 passed`, `0 skipped`. Пять PostgreSQL integration tests проходили на PostgreSQL 14.24. Эти результаты не складываются.

## Как проверить сценарий

1. Открыть `http://127.0.0.1:5173`.
2. Employee: профиль, next grade, gaps, рекомендация, объяснение, Complete, если сервер вернул рекомендацию.
3. HR: gaps, сотрудники без следующего шага, participation, import JSON + CSV.
4. `http://127.0.0.1:8000/api/health` — процесс backend.
5. `http://127.0.0.1:8000/api/ready` — доступность PostgreSQL.

Если у сохранённого demo-профиля нет допустимого следующего шага, рекомендации пустые и `selection_status` может быть `not_applicable`. Это состояние движка, а не отключение AI.

## Безопасность

- `.env` в git ignore.
- Секреты не коммитятся.
- Ключ OpenAI только на backend.
- Пароль БД остаётся на сервере или локальной машине.
- Raw official dataset в репозиторий не входит.
- Session cookie `HttpOnly`.
- CSRF на изменяющих запросах.
- Роль проверяется на сервере.
- Employee не открывает чужого сотрудника.
- HR endpoints защищены на сервере.
- AI payload исключает полное имя, отдел, руководителя и сырую историю.

## Known limitations

- Hackathon demo login — не production auth.
- UI показывает `skill_id`, где display name навыка API не отдаёт.
- Недавняя активность показывает `event_id`.
- Карьерный путь — frontend-only на уже загруженном profile: текущие role/grade, primary target, progress, requirements и личная career goal, если она отличается. Новых backend endpoints нет.
- История — frontend-only на `profile.history`: date, event_id, status, completion_pct, origin. Fixtures не используются. Browser smoke Path/History на 1280/390 не выполнялся.
- Публичный live deploy ещё не проверен.

## Infrastructure

Подготовлены Ubuntu 22.04, Nginx, HTTPS / Let's Encrypt, PostgreSQL и домен `hack.qazentra.com`. Предпочтительная схема: Nginx → static React build → `/api` proxy → Uvicorn/FastAPI → PostgreSQL. Для backend запланирован systemd. Docker для MVP не требуется.

Career Quest final build не заявлен как публично развёрнутый, пока не выполнен live smoke. Подробности: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Ключевые файлы

```text
backend/career_quest/loader.py    — validated loader
backend/career_quest/engine.py    — deterministic career engine
backend/career_quest/ai_select.py — OpenAI layer и fallback
backend/career_quest/api.py       — HTTP API
backend/career_quest/serve.py     — миграции, seed, Uvicorn
scripts/start.py                  — backend + Vite
frontend/src/App.jsx              — сессия и экраны
frontend/src/screens.jsx          — login, detail, HR, import
frontend/src/api/client.js        — вызовы API
alembic/                          — миграции PostgreSQL
docs/SETUP.md                     — установка с нуля
docs/API.md                       — HTTP-контракт
docs/PROJECT.md                   — продуктовые и технические решения
docs/CHECKPOINT.md                — фактический статус
```
