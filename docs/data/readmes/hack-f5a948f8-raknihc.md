# Career Quest — навигатор развития сотрудника

Проект команды **Raknihc** для HackAlem AI, кейс АО «Народный Банк Казахстана».
Ветка приложения — `feat/app-ui`. FastAPI + SQLite, React + TypeScript + Vite.

## Demo accounts

These are **synthetic/local hackathon demo credentials**, provided for judges to
sign in to the prepared local application. They are not production credentials.
These accounts belong to the prepared demo database; a fresh installation creates
its own accounts and does not automatically receive these passwords.

| Account | Username | Password |
| --- | --- | --- |
| Employee E0001 | `employee1` | `6jrzBbFOxf91YqFj8jmfRvtC` |
| Employee E0002 | `employee2` | `oX2QTK93SSWnuiZqb4RKqjdU` |
| HR | `hr` | `vumXwTTkzgVqBaZaU1IIeiAg` |

Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Что работает

- Вход, отзывные сессии и серверные права сотрудник/HR. Сотрудник видит только свои данные.
- Кабинет: роль, грейд, актуальные навыки, история, требования цели и критические дефициты.
- До трёх рекомендаций: объяснение, формат, часы, дата, ожидаемый рост навыков.
- Симуляция без записи; загрузка, ошибки с повтором, fallback и отсутствие подходящих шагов.
- Выполнение активности: подтверждение в интерфейсе, транзакционная запись, защита от повторов,
  обновление навыков, истории и рекомендаций. Отдельные сессии клуба `EV_036`.
- HR-экран: частые дефициты, сотрудники без следующего шага, участие и завершения по мероприятиям.
  Просмотр профилей и симуляций; сотрудники упорядочены по ID, публичного рейтинга нет.
- Добавочный импорт JSON профилей и CSV истории: проверка перед сохранением, ошибки по строкам,
  атомарность, точные повторы пропускаются. Новые профили сразу доступны HR и движку.
- Запуск собранного приложения и API одной командой на одном порту.

## AI Engine and integration status

The deterministic AI Engine is implemented and frozen in `backend/app/engine/`.
**FastAPI now defaults to RealAIEngineAdapter. The frozen AI Engine supplies
recommendations, current skills, trajectory and Digital Twin calculations.**

- Reconstructs current skills from the snapshot at `last_review_date`, applying
  completed post-review activity gains with `max_level` caps without reducing higher skills.
- Analyzes next-grade requirements, mapped career targets, skill gaps and criticality.
- Filters by role, grade, prerequisites, availability and completed non-repeatable events.
- Uses deterministic multifactor ranking with exact `score_breakdown`; participation
  history modifies ranking rather than automatically vetoing a useful activity.
- Career Digital Twin simulates skill changes and readiness before/after each candidate.
- WHY THIS / WHY NOT compares verified alternatives; Recommendation Critic checks
  independent evidence categories.
- Optional OpenAI explanations receive verified facts only. Missing SDK/key, API
  failures, timeouts or invalid output retain deterministic explanations and selection.
- Public Python entry point: `from backend.app.engine import recommend`.
- AI, jury/adversarial, review-date and JSON-serialization tests live in `tests/`.

MockEngine reconstructs skills and simulates catalog gains, but returns activities
in catalog order, without AI ranking. Its scores and readiness percentages are null.
The UI shows WHY THIS / WHY NOT, expected readiness before/after and skill gains.
The HTTP response also preserves explanation_source, explanation, expected impact
and caution. Internal Critic and full score breakdown remain in the Python contract.
Readiness measures target skill coverage, not a guarantee of promotion.

## Project structure

```text
backend/app/
  main.py, config.py, schemas.py       # FastAPI and HTTP/Pydantic models
  auth.py, manage_users.py             # employee/HR access and accounts
  storage.py, import_dataset.py        # SQLite and initial dataset import
  hr.py, jury_import.py                # HR analytics and additive JSON/CSV import
  engine_port.py, mock_engine.py       # protocol and explicit emergency fallback
  real_ai_engine_adapter.py            # default application-to-AI boundary
  engine/                             # frozen AI, Digital Twin, Critic, optional LLM
backend/tests/                        # application tests
frontend/src/                         # React employee and HR screens
frontend/tests/                       # Playwright browser tests
tests/                                # AI Engine tests
docs/                                 # HTTP/Python contracts, examples, scoring
scripts/start.py, start.sh             # install, build, initialize and serve
data/private/                         # local dataset, SQLite, access files; ignored
requirements.txt, pyproject.toml       # backend dependencies and test configuration
frontend/package.json                 # frontend dependencies and scripts
```

The one-command launcher currently uses Bash and `.venv/bin/python` (Unix).
On native Windows use manual startup with `.venv/Scripts/python.exe`; launcher
portability has not been implemented.

## Запуск одной командой

Нужны **Python 3.11+ с venv/pip**, **Node.js 22.12+ (LTS 22) либо 24+** и npm.
Проверено на Python 3.14 / Node.js 24. При первой установке нужен интернет для зависимостей.
На Debian/Ubuntu при ошибке `ensurepip` установите пакет `python3-venv`.

Из корня репозитория:

```bash
./start.sh --dataset /absolute/path/to/career_quest_dataset
```

Команда создаёт `.venv`, устанавливает зависимости из `requirements.txt` и
`frontend/package-lock.json`, собирает интерфейс, импортирует исходный датасет
без перезаписи существующих данных и запускает **http://127.0.0.1:8000**.
Swagger — **http://127.0.0.1:8000/docs**. Остановка — **Ctrl+C**.
При повторном запуске зависимости не переустанавливаются, если их контрольные файлы
не изменились. Данные SQLite и учётные записи сохраняются.

Если аккаунтов ещё нет, создаются `hr` и `employee1` (при наличии профилей) со
случайными паролями. Путь к файлу `data/private/access-<случайный ID>.json` выводится
в терминал; сам пароль не печатается. Файл доступен только владельцу (права 0600),
не входит в Git и не раздаётся веб-сервером. Существующие аккаунты не меняются.

Для уже заполненной БД достаточно `./start.sh`. Без датасета доступен вход HR,
но сначала нужно загрузить исходный каталог через CLI/`--dataset`: импорт жюри
добавляет профили и историю к существующему каталогу.

Дополнительные варианты:

```bash
./start.sh --port 8010                       # если 8000 занят
./start.sh --skip-install                   # зависимости уже установлены, сборка выполняется
./start.sh --prepare-only --dataset /path/to/career_quest_dataset
```

`--prepare-only` устанавливает, собирает и инициализирует данные без запуска сервера.
Для повторной принудительной установки можно явно выполнить `pip install -r requirements.txt`
через `.venv/bin/python -m pip` и `npm ci --prefix frontend`.

## Настройки и секреты

Скопируйте `.env.example` в `.env` при необходимости. `start.sh` читает строки
`CQ_NAME=value` буквально, без исполнения команд и подстановок shell. Переменные,
уже экспортированные в окружение, имеют приоритет. Прямой запуск Uvicorn/CLI
самостоятельно `.env` не читает.

| Переменная | Значение по умолчанию / назначение |
| --- | --- |
| `CQ_DB_PATH` | `data/private/career-quest.sqlite3` |
| `CQ_AS_OF_DATE` | `2026-10-01`, расчётная дата датасета |
| `CQ_DATASET_DIR` | Не задана; путь к исходным четырём файлам |
| `CQ_HOST`, `CQ_PORT` | `127.0.0.1`, `8000` |
| `CQ_SESSION_TTL_SECONDS` | `28800`, срок сессии по реальному UTC-времени |
| `CQ_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` |
| `CQ_SERVE_FRONTEND` | `0`; launcher устанавливает `1` после сборки |

The standalone AI explainer expects `OPENAI_API_KEY` in the server process environment.
The launcher accepts `CQ_*` and `OPENAI_API_KEY` assignments in its local `.env`.
OPENAI_* values are excluded from the frontend build environment. Direct Uvicorn/CLI and the engine
do not load `.env`. Never put secrets in `VITE_*`, source code, logs or Git.
Default: `CQ_USE_LLM=0`. Set `CQ_USE_LLM=1` for optional explanations; no key is required
for operation, and failures keep real deterministic recommendations. HR bulk calculations
always disable LLM. The SDK is included in requirements.txt; standalone installation:
`python -m pip install -r backend/app/engine/requirements-llm.txt`.
Launcher исключает `CQ_` и `VITE_` переменные окружения из процесса сборки.
`.env`, SQLite, локальные пароли и загруженные данные исключены из Git.
Веб-сервер раздаёт только `frontend/dist`, а не корень проекта.

Приложение предназначено для локального запуска; при публикации авторизованного
API используйте HTTPS. Доска планирования — отдельный сервис.

## Кабинет и выполнение

1. Войдите под учётной записью сотрудника и откройте **«Рекомендации»**.
2. Нажмите **«Посмотреть результат»**: симуляция покажет навыки до/после, не изменяя БД.
3. Для пройденного обучения поставьте подтверждение и нажмите **«Сохранить выполнение»**.
4. После ответа сервера кабинет заново получает навыки, историю и рекомендации.
   При ошибке повтор использует прежний ключ; потеря ответа не создаёт второе выполнение.

Самостоятельный курс можно завершить в дату среза. Сессию по расписанию — только
в её расчётную дату. Будущие сессии доступны для симуляции, кнопка выполнения для
них отсутствует. Дата среза берётся из `CQ_AS_OF_DATE`, а не системных часов.

Исходные `profile.skills` остаются оценкой на `last_review_date`. Актуальные навыки
возвращаются в `trajectory.current_skills` и `recommendations.current_skills`.
Адаптер последовательно применяет завершения **строго после оценки и не позже среза**;
уровень не превышает потолок мероприятия и не снижается, если уже выше него.
Для старых записей без `completed_at` используется `date` как допущение. У исходного
self-paced это дата зачисления, поэтому такой расчёт приблизительный. Новые выполнения
сохраняют точную `completed_at`. Повторы обычной активности не начисляются повторно;
клуб учитывается отдельно по дате сессии, обязательное обучение — по датам записей.

При недоступности основного движка preview возвращает помеченный резервный расчёт.
Выполнение не использует fallback: при ошибке движка транзакция откатывается.

## HR и импорт жюри

Учётная запись HR открывает **HR-обзор**. Доступны частые дефициты относительно
заданных целей, список сотрудников с фильтром «без подходящего шага», история и
симуляция отдельных профилей, статистика мероприятий. Ошибка расчёта не считается
отсутствием следующего шага. Участники — уникальные сотрудники; записи и завершения
включают отдельные сессии и повторное обязательное обучение.

В разделе **«Импорт JSON/CSV»** выберите JSON профилей и/или CSV истории, нажмите
**«Проверить файлы»**, затем **«Сохранить импорт»**. Есть скачиваемые шаблоны.
Лимиты: 500 профилей, 10 000 строк истории; каждый файл до 2 МБ.
Ошибки показывают файл, строку/номер объекта и поле. При любой ошибке нет частичных
записей. Существующие ID с изменёнными данными отклоняются, точные повторы пропускаются.
Каталог мероприятий и навыков через этот экран не изменяется.

API: `POST /api/v1/hr/imports` принимает `{employees_json?, history_csv?, dry_run}` —
**содержимое файлов как строки JSON**, не multipart. По умолчанию `dry_run: true`.
[Форматы, примеры и правила импорта](docs/jury-import.md).

Импорт не создаёт пароли и роли. Чтобы новый сотрудник мог войти, администратор
создаёт учётную запись, пароль запрашивается скрытым вводом:

```bash
.venv/bin/python -m backend.app.manage_users create jury1 --role employee --employee-id JURY_001
.venv/bin/python -m backend.app.manage_users set-password jury1
```

Для нестандартной БД CLI должен получить тот же экспортированный `CQ_DB_PATH`, что и сервер.
После обновления HR-обзор читает новые данные без перезапуска.

## Разработка и данные

Для разработки backend и Vite запускаются отдельно:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
npm run dev --prefix frontend
```

Кабинет — **http://127.0.0.1:5173**, Vite проксирует `/api` на `8000`.
Optional user services career-quest-api and career-quest-frontend may exist on
the teammate's machine; they are not assumed on other machines. Where configured,
inspect them with `systemctl --user status <name>`.

Токен хранится только в памяти браузера. Перезагрузка страницы требует нового входа;
401 очищает сессию, выход отзывает токен. Swagger: вызовите `/api/v1/auth/login`,
вставьте значение `access_token` в **Authorize**. [Матрица прав](docs/access-control.md).

Стартовый датасет: `employees.json`, `events.json`, `skills.json`, `activity_history.csv`:
200 сотрудников, 60 навыков, 32 профиля требований, 40 мероприятий, 2 743 записи истории.
Данные не входят в Git. CLI полного импорта:

```bash
.venv/bin/python -m backend.app.import_dataset /path/to/career_quest_dataset
```

Повтор того же датасета не перезаписывает данные. Для другого полного датасета
используйте новую БД. Для резервной копии активной SQLite используйте SQLite backup API.

## Проверки

```bash
.venv/bin/python -m pytest backend/tests -q
.venv/bin/python -B -m unittest discover -s tests -q
.venv/bin/python -m backend.app.engine --dataset data/private/career_quest_dataset --employees E0002
npm run build --prefix frontend
cd frontend
npx playwright install chromium
npm test
```

Серверные проверки используют временные БД: права, импорт/откат, идемпотентность,
одновременные записи, навыки после выполнения, отдельные сессии клуба и статистику HR.
Браузерные тесты используют Vite на 5174 и независимые ответы API: кабинет,
рекомендации, симуляция, повтор выполнения с прежним ключом, импорт, HR и мобильный экран.
Legacy mock checks and new real-adapter integration checks are separate. Final defense E2E,
defense-scenario validation and README verification/submission remain pending.

[Контракт API/движка](docs/api-contract.md) · [Mock-примеры](docs/examples/) ·
[Особенности датасета](docs/dataset-notes.md) · [План команды](docs/work-plan.md).

## Manual setup and standalone AI verification

Place the four original dataset files in `data/private/career_quest_dataset`, or pass
their actual directory to the importer. Do not modify the original dataset.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci --prefix frontend
.venv/bin/python -m backend.app.import_dataset data/private/career_quest_dataset
.venv/bin/python -m backend.app.manage_users create hr --role hr
.venv/bin/python -m backend.app.manage_users create employee1 --role employee --employee-id E0001
```

On Windows create the environment with `python -m venv .venv`, then substitute
`.venv/Scripts/python.exe` for `.venv/bin/python` in all backend commands.
Use the same CQ_DB_PATH for import, account management and server startup.

Run both Python suites explicitly: default pytest configuration selects backend tests.
Validation: 137 Python tests passed (48 AI, 89 application/integration), plus 200
dataset subtests; all 200 profiles also passed adapter consistency checks. Frontend
build and 15 browser tests passed. Browser tests use API fixtures; the separate final
defense scenario with a live browser/server remains to be verified.

[AI scoring and fallback](docs/scoring-and-explanations.md) |
[Complete Python response example](docs/integration-example.json).

## Integration date semantics

The adapter copies JSON-mode application data. For completed self-paced activities,
completed_at replaces enrollment date only in the engine input copy. Missing completion
dates retain the dataset proxy and warning. Scheduled session identity is never moved:
if a scheduled completed_at differs from its session date, AI calls return HTTP 422
with scheduled_completion_date_mismatch. Such imported records require reconciliation;
the engine has a single history-date field. Original SQLite records remain unchanged.
Completed club sessions are removed from copied availability before recommendation.
Simulation and completion can still develop skills after target readiness reaches 100;
recommendations retain the frozen gap-closing selection rules.
