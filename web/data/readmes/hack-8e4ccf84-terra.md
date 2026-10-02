# TERRA — Agentic AI для прогнозирования выработки ВЭС

TERRA — прототип платформы, которая формирует почасовой прогноз нормализованной активной мощности ветроэлектростанции на горизонте 24 или 48 часов. Система объединяет исторические измерения, архивные прогнозы погоды, ML-модель и устойчивый агентный процесс с журналом решений, повторным запуском и защитой от утечки будущих данных.

Проект создан для кейса HackAlem AI. Краткое ТЗ находится в [docs/hackalem-ai-agentic-wind-forecasting.md](docs/hackalem-ai-agentic-wind-forecasting.md), оригинальный PDF и два набора данных — в [resources/](resources/).

> **Статус на 23 сентября 2026:** по статическому анализу кода реализованы основные компоненты, но полный исторический сценарий ТЗ не подтверждён. В исходных CSV нет фактической выработки за февраль 2026 года, а у загружаемых погодных прогонов нет доказанного исторического времени публикации. Официальный февральский результат и превосходство модели над baseline не установлены. При этом ревью тесты, сборка и приложение не запускались; наличие кода не означает проверенную работоспособность.

## Содержание

- [Задача и подход](#задача-и-подход)
- [Что реализовано](#что-реализовано)
- [Соответствие требованиям кейса](#соответствие-требованиям-кейса)
- [Как работает система](#как-работает-система)
- [Архитектура](#архитектура)
- [Быстрый запуск в Docker](#быстрый-запуск-в-docker)
- [Deploy на сервер и обновление](#deploy-на-сервер-и-обновление)
- [Локальный запуск](#локальный-запуск)
- [Интерфейс](#интерфейс)
- [Основной сценарий через API](#основной-сценарий-через-api)
- [Входные данные](#входные-данные)
- [Agentic AI, replay и модель](#agentic-ai-replay-и-модель)
- [Проверки](#проверки)
- [Структура репозитория](#структура-репозитория)
- [Переменные окружения](#переменные-окружения)
- [Ограничения](#ограничения)
- [Дополнительная документация](#дополнительная-документация)

## Задача и подход

По условиям кейса требуется:

1. обучить модель на истории работы ВЭС с марта 2023 года по 31 января 2026 года;
2. получать для координат ВЭС прогноз погоды, который был доступен в момент выпуска;
3. формировать прогноз мощности на следующие 24–48 часов с почасовой детализацией;
4. повторять цикл при появлении нового погодного прогона;
5. последовательно воспроизвести выпуски с 31 января по 28 февраля 2026 года без использования будущей информации;
6. сохранить происхождение данных, параметры, версии модели и журнал решений агента.

Ключевой принцип TERRA: **числовой прогноз вычисляется детерминированным кодом, LLM используется только для анализа и пояснения**. Отключение LLM не меняет прогнозные значения и не останавливает основной процесс.

## Что реализовано

| Возможность | Состояние | Что можно проверить |
|---|---|---|
| Защищённый dashboard | Реализовано | Вход администратора, «Обзор», «Прогноз», «Источники», «Журнал агента» |
| Демонстрационный UI | Реализовано | Сценарии: готово, частично, устарело, загрузка, пусто, ошибка |
| PostgreSQL и миграции | Реализовано | `npm run db:migrate`, автоматическая миграция в Docker |
| Импорт CSV | Реализовано | Предпросмотр, подтверждение mapping/времени/единиц, дедупликация, отчёт ошибок, SHA-256 raw-файла |
| Канонические наблюдения | Реализовано | Training-строки попадают в `observations`, evaluation-only данные изолированы |
| Снимок входов и прогноз | Реализовано | Проверка доступности данных, 24/48 точек, версии и CSV export |
| Baseline | Реализовано | Production persistence-модель использует последнее допустимое наблюдение |
| ML training и inference | Реализованы в коде, историческая модель не подтверждена | Ridge, power curve, временная валидация, сравнение с persistence; approved artifact подключён к синхронному и агентному пути |
| Agent jobs | Реализовано | PostgreSQL queue, checkpoint, journal, lease/fencing, retry, cancel и restart recovery |
| Replay | Runtime и пакетный CLI | Preflight, resume, manifests, 29 дней × 2 объекта × 2 горизонта = 116 выпусков при полном наборе входов |
| Open-Meteo Single Runs | Коннектор и запись в PostgreSQL | Raw/hash, `weather_runs/weather_values`; исторические `published_at/available_at` остаются NULL и блокируют официальный расчёт |
| Пересчёт при новых входах | Частично | Durable input events и закреплённые snapshots; trigger сохраняет только ветер, чего недостаточно для trained inference с температурой |
| Оценка опубликованных прогнозов | Worker и PostgreSQL реализованы | Изолированные revisions факта, версии MAE/RMSE/N/coverage; HTTP endpoint пока читает legacy backtest registry |
| Deployment workers | Описаны в Compose | Базовый dispatcher; input-trigger и evaluation включаются дополнительным Compose-файлом |
| Oracle / Siemens WinCC | Реализованы gateway-контракты | Test/discover/enable; промышленные секреты не попадают в браузер |
| Официальный февральский backtest | Заблокирован данными | Нет факта за февраль и доказанного `published_at` архивной погоды |

Предыдущий аудит: [docs/backend-spec-audit.md](docs/backend-spec-audit.md). Более поздние изменения описаны в [handoff P1–P6](docs/handoffs/); актуальная статическая оценка приведена ниже.

## Соответствие требованиям кейса

Оценка относится к исходникам локального `main` на базе `18b8a28` с учётом интеграции P7 (`e2071cc`), а не к запущенной системе. Отчёты прежних проверок в handoff-документах не считаются повторно выполненными проверками этого ревью.

| Требование ТЗ | Что сделано и где | Что ещё не подтверждено или не завершено |
|---|---|---|
| Обучение на истории до февраля 2026 | [CSV import](src/server/data/import/service.ts), [training](src/server/ml/training/approved.ts), [CLI](scripts/train-approved.ts): cutoff, временная валидация, сравнение с persistence | Не предоставлены канонические архивные training snapshots и реальный approved artifact; synthetic evidence не даёт approval |
| Самостоятельное получение доступного на момент выпуска прогноза погоды | [Open-Meteo](src/server/connectors/weather/open-meteo.ts), [ingestion](src/server/connectors/weather/ingestion.ts), [CLI](scripts/weather-ingest.ts): координаты, raw/hash, транзакционная запись | Наличие архивного run не доказывает время его публикации. Текущий ingestion сохраняет NULL для исторической доступности; официальный режим блокируется |
| Почасовой прогноз на 24–48 часов | [Forecast service](src/server/forecast/service.ts), [approved inference](src/server/forecast/approved-inference.ts): persistence либо approved model, версии и экспорт | Прогноз обученной модели на реальных входах не продемонстрирован; ошибка artifact не заменяется baseline |
| Агентный цикл: подготовка → модель → анализ → повторный расчёт | [Workflow](src/server/agent/workflow.ts), [adapters](src/server/agent/adapters.ts), [triggers](src/server/triggers/discovery.ts): durable jobs, checkpoint, журнал, опциональный LLM | Weather ingestion — отдельный CLI; единый цикл его автономного запуска агентом не подтверждён. Trigger snapshot не включает температуру, необходимую trained inference |
| Последовательное воспроизведение 31 января — 28 февраля | [Batch replay](src/server/replay/batch/index.ts), [CLI](scripts/replay-february.ts): явный календарь, preflight, resume, manifests | Реальные 116 выпусков и общий E2E не подтверждены; допустимые weather runs и модель обязательны до запуска |
| Использование архивных прогнозов, а не позднего факта | [As-of selection](src/server/data/weather/selection.ts), [features](src/server/ml/inference/features.ts), [evaluation](src/server/evaluation/worker.ts): границы времени и изоляция evaluation-only | Защитные проверки есть в коде, но не создают отсутствующих доказательств происхождения данных |

**Вывод по требованиям:** реализована значительная часть инфраструктуры и вычислительного пути; полное соответствие основному сценарию пока частичное. Отсутствие февральского факта блокирует оценку качества, но само по себе не мешает выпуску прогнозов. Выпуск сейчас ограничивают прежде всего доступность архивной погоды, approved model и неполный trigger snapshot.

По критериям жюри: соответствие и работоспособность (25) требуют демонстрации полного цикла; техническая реализация (25) представлена кодом, но имеет указанные разрывы; README и воспроизводимость (25) обеспечены инструкциями и контрактами, однако реальный результат не воспроизведён; применимость (15) ограничена неподтверждённой семантикой и отсутствием оценки точности; потенциал развития (10) поддерживают replay, происхождение данных и версионирование. Числовой итог из 100 без запуска и результатов не присваивается.

## Как работает система

1. Администратор регистрирует станцию, турбину или линию.
2. Загружает CSV и подтверждает столбцы, часовой пояс, смысл метки времени, задержку доступности и единицы.
3. Импорт сохраняет raw-файл и хеш, проверяет строки и создаёт канонические наблюдения.
4. Отдельный weather CLI сохраняет архивный прогноз и происхождение. Для допуска в runtime нужны доказанные `published_at/available_at`; исследовательское допущение их не заменяет.
5. Агент фиксирует неизменяемый снимок входов и проверяет `available_at <= issued_at`.
6. Детерминированная модель формирует ровно 24 или 48 часовых точек либо возвращает явный неполный результат.
7. Прогноз сохраняется как новая версия, решения и ошибки — в журнале агента.
8. При включённом input-trigger worker новый допустимый набор входов ставит задачу повторного расчёта. Идемпотентность защищает от повторной публикации; ограничение trained snapshot указано выше.
9. Replay последовательно воспроизводит исторические события с виртуальным временем.

Режимы работы:

| Режим | Назначение |
|---|---|
| `live` | Текущий оперативный прогноз |
| `backtest` | Историческая оценка последовательности прошлых выпусков |
| `replay` | Управляемая симуляция потока событий |

Интерфейс также разделяет два источника данных:

- **«Демонстрационные»** — синтетические fixtures для полного показа UX, но не доказательство качества модели;
- **«Настоящий API»** — `/api/v1` с защищённой сессией. Ошибка API не заменяется fixture-данными.

## Архитектура

```mermaid
flowchart LR
    CSV[CSV / Oracle / WinCC] --> INGEST[Импорт и качество]
    INGEST --> DB[(PostgreSQL)]
    WEATHER[Архивные прогнозы погоды] --> DB
    API[Next.js API] --> JOBS[Очередь задач]
    DISPATCHER[Job dispatcher] --> JOBS
    JOBS --> AGENT[Agent workflow]
    DB --> SNAPSHOT[Снимок available_at <= issued_at]
    SNAPSHOT --> AGENT
    AGENT --> MODEL[Persistence / approved artifact]
    MODEL --> FORECAST[(Версии прогнозов)]
    AGENT --> JOURNAL[(Checkpoint и журнал)]
    FORECAST --> UI[Dashboard / CSV]
    JOURNAL --> UI
    LLM[OpenAI, опционально] -. пояснение .-> AGENT
```

Стек:

- Next.js 16, React 19, TypeScript;
- PostgreSQL 16;
- Drizzle ORM и SQL-репозитории;
- Zod для входных контрактов;
- `@openai/agents` для опционального reasoning-слоя;
- Docker Compose;
- Node test runner, `tsx`, ESLint и TypeScript.

Агент управляет процессом: выбирает допустимый weather run, проверяет входы, запускает расчёт, сохраняет checkpoint и объяснение. Временные границы, вычисления, авторизация, идемпотентность и публикация остаются в детерминированном коде.

## Быстрый запуск в Docker

### Требования

- Docker с Compose v2;
- свободный порт `3000` либо другой `APP_PORT`;
- ресурсы, достаточные для локальной сборки Next.js и PostgreSQL.

### 1. Настройте `.env`

Скопируйте `.env.example` в `.env` и замените все `replace-with-*`. Не коммитьте `.env`.

```dotenv
POSTGRES_PASSWORD=local-terra-db-password
ADMIN_PASSWORD=local-terra-admin-password
ADMIN_API_TOKEN=local-terra-api-token
SESSION_SECRET=local-session-secret-at-least-32-characters
JOB_TICK_SECRET=local-job-tick-secret
APP_PORT=3000
AGENT_LLM_ENABLED=false
```

`ADMIN_PASSWORD` в production должен содержать не менее 12 символов, `SESSION_SECRET` — не менее 32. Для production-подобной среды используйте случайные значения.

### 2. Соберите и запустите

```bash
docker compose up --build
```

Отдельный сервис `migrate` применяет миграции; приложение ждёт его успешного завершения. Проверьте здоровье:

```bash
curl http://localhost:3000/api/health
```

Ожидается:

```json
{"status":"ok","database":"ready"}
```

Откройте <http://localhost:3000> и войдите как `admin` с `ADMIN_PASSWORD`. Имя можно изменить через `ADMIN_USERNAME`.

### 3. Фоновые процессы

`compose.yaml` уже включает dispatcher для `/api/v1/agent-runs`; он ждёт готовности приложения. Дополнительные input-trigger и evaluation workers описаны в `compose.workers.yaml`:

```bash
docker compose -f compose.yaml -f compose.workers.yaml up --build -d
```

Перед этим задайте `INPUT_TRIGGER_CONFIG` и `EVALUATION_CONFIG` — пути к существующим JSON-конфигурациям с явными объектами, моделью, календарём и параметрами оценки. Они монтируются только для чтения. Форматы: [P3](docs/handoffs/parallel-P3.md), [P5](docs/handoffs/parallel-P5.md), [P6](docs/handoffs/parallel-P6.md). Эти workers не запускают загрузку погоды автоматически. Команды приведены для самостоятельного воспроизведения и в рамках этого ревью не выполнялись.

Остановка без удаления данных:

```bash
docker compose down
```

Команда `docker compose down --volumes` дополнительно и необратимо удалит локальные тома PostgreSQL и артефактов.

## Deploy на сервер и обновление

Поддерживаемый репозиторием способ — Docker Compose на сервере с постоянным диском. Нужны Git-доступ к репозиторию и Docker Compose v2. Сначала разворачивается приложение с PostgreSQL и dispatcher; исторические данные, модель и дополнительные workers настраиваются отдельно. Deploy сам по себе не создаёт февральские прогнозы.

### Первый deploy

В чистом checkout ветки `main`:

```bash
git clone https://github.com/BAITC-Hacks/hack-8e4ccf84-terra.git terra
cd terra
git switch main
git pull --ff-only origin main
cp .env.example .env
```

На Windows вместо `cp` можно использовать `Copy-Item .env.example .env`. Замените placeholders в `.env`: `POSTGRES_PASSWORD`, `ADMIN_PASSWORD`, `ADMIN_API_TOKEN`, `SESSION_SECRET`, `JOB_TICK_SECRET`. Используйте разные случайные значения; пароль БД — буквенно-цифровой, поскольку Compose подставляет его непосредственно в URL. `ADMIN_PASSWORD` должен иметь минимум 12 символов, `SESSION_SECRET` — 32. Для первого запуска оставьте `AGENT_LLM_ENABLED=false`. `.env` не входит в Git и Docker build context.

Установите постоянный `COMPOSE_PROJECT_NAME=terra` в `.env`: от него зависят имена образа и томов. Для публичного сервера поставьте HTTPS reverse proxy перед приложением. В текущем Compose порт публикуется как `${APP_PORT:-3000}:3000`; если proxy работает на том же хосте, `APP_PORT=127.0.0.1:3000` ограничивает доступ localhost. TLS/proxy конфигурация в репозитории отсутствует. Proxy должен сохранять внешний Host и передавать схему HTTPS; после настройки проверьте вход через домен и атрибут Secure у cookie. Не считайте готовность health endpoint проверкой входа.

```bash
docker compose config --quiet
docker compose build app
docker compose up -d db
docker compose run --rm migrate
docker compose up -d app dispatcher
docker compose ps -a
docker compose logs --tail=100 migrate app dispatcher
curl --fail http://127.0.0.1:3000/api/health
```

Сначала собирается общий образ, затем применяются миграции, затем поднимается приложение. `up` может повторно запустить сервис `migrate` как зависимость; migration runner пропускает имена из `schema_migrations`. При ошибке миграции остановитесь и исправьте её причину до запуска приложения. Ожидаемый health: `{"status":"ok","database":"ready"}`; `migrate` завершается с кодом 0, `app` и `db` становятся healthy, dispatcher остаётся запущенным. Войдите как `admin`, выберите «Настоящий API», создайте объект и импортируйте историю. Пустая БД не содержит готовой ML-модели и архивной погоды.

Compose передаёт контейнерам только переменные из соответствующих `environment` секций. Например, `ADMIN_USERNAME`, дополнительные LLM limits и industrial gateway variables из `.env` автоматически внутрь `app` не попадут: для них нужен явный локальный Compose override. Значение `ARTIFACT_ROOT` в контейнере уже задано как `/app/artifacts`.

### Данные, модель и дополнительные workers

CSV из `resources/` исключены из Docker image: загружайте их через «Источники» или API импорта. Weather/training/replay CLI и их ограничения описаны в разделе [Agentic AI, replay и модель](#agentic-ai-replay-и-модель). Файлы конфигураций CLI должны быть доступны внутри контейнера через явно добавленный bind mount либо скопированы туда; пути хоста не становятся путями контейнера автоматически.

Approved artifact храните в томе `artifacts` внутри `/app/artifacts`; соответствующий `raw_artifacts.path` должен указывать на контейнерный абсолютный путь. Зарегистрируйте согласованные SHA-256, approval, версию и cutoff в реестре модели по [P6](docs/handoffs/parallel-P6.md). Нельзя просто назвать произвольный JSON approved-моделью.

Для input-trigger и evaluation создайте JSON по [P3](docs/handoffs/parallel-P3.md) и [P5](docs/handoffs/parallel-P5.md), затем добавьте в `.env` абсолютные пути **на сервере deploy**:

```dotenv
INPUT_TRIGGER_CONFIG=/srv/terra-config/input-trigger.json
EVALUATION_CONFIG=/srv/terra-config/evaluation.json
EVALUATION_POLL_MS=30000
```

```bash
docker compose -f compose.yaml -f compose.workers.yaml config --quiet
docker compose -f compose.yaml -f compose.workers.yaml up -d
docker compose -f compose.yaml -f compose.workers.yaml logs --tail=100 input-trigger evaluation
```

Оба файла обязательны для этого overlay. Workers не получают погоду сами и не устраняют пробел температуры в trigger snapshot или отсутствие февральского факта. Evaluation требует конкретные опубликованные `forecastRunIds` и подтверждённый semantic manifest. Не включайте его с выдуманными UUID или неподтверждённой семантикой.

### Обновление существующего deploy

Сохраните предыдущий commit SHA, резервную копию PostgreSQL и тома `artifacts`. Остановите writers на время согласованной копии и миграции (если overlay включён, используйте оба `-f` во всех соответствующих командах):

```bash
git rev-parse HEAD
docker compose stop dispatcher app
git pull --ff-only origin main
docker compose build app
docker compose run --rm migrate
docker compose up -d app dispatcher
docker compose ps -a
docker compose logs --tail=100 app dispatcher
curl --fail http://127.0.0.1:3000/api/health
```

При включённом overlay также остановите `input-trigger evaluation` перед копированием/миграцией и поднимите их после успешной миграции с обоими Compose-файлами. При любой ошибке команды обновления не переходите к следующему шагу. Данные сохраняются в `postgres_data` и `artifacts`; не используйте `down --volumes` при обновлении. Изменение `POSTGRES_PASSWORD` в `.env` не меняет пароль уже созданного пользователя в существующей БД.

Автоматического rollback миграций нет. Откат приложения к предыдущему commit допустим только при совместимости схемы; иначе нужен согласованный план восстановления БД и artifacts из резервной копии. Проверяйте deploy отдельно от качества прогноза: health и работа dispatcher не подтверждают успешный исторический replay.

Приведённые команды — инструкция оператору. При подготовке этого README deploy, сборка, тесты и запуск сервисов не выполнялись.

## Локальный запуск

Рекомендуются Node.js 22 (та же версия используется в Docker), npm 10+ и PostgreSQL 16.

```bash
npm ci
```

Создайте пустую БД и задайте окружение. Пример PowerShell:

```powershell
$env:DATABASE_URL = "postgres://terra:password@localhost:5432/terra"
$env:ARTIFACT_ROOT = ".data/artifacts"
$env:ADMIN_PASSWORD = "local-terra-admin-password"
$env:ADMIN_API_TOKEN = "local-terra-api-token"
$env:SESSION_SECRET = "local-session-secret-at-least-32-characters"
$env:JOB_TICK_SECRET = "local-job-tick-secret"
$env:AGENT_LLM_ENABLED = "false"
npm run db:migrate
npm run dev
```

В отдельном терминале с теми же `DATABASE_URL` и `JOB_TICK_SECRET`:

```powershell
node scripts/job-dispatcher.mjs
```

Production-сборка:

```bash
npm run build
npm run start
```

## Интерфейс

После входа доступны:

- **Исторический прогон** (`/history`, стартовый экран) — выбор турбины, периода выпусков с 31 января по 28 февраля 2026 и горизонта 24/48 часов; переходы по дням, график и почасовая таблица. В деморежиме показаны синтетические выпуски двух турбин. В режиме API читаются сохранённые backtest/replay-прогнозы; новый расчёт при выборе дня не запускается. Автоматический запуск всего периода пока не подключён.
- **Обзор** — состояние объекта, текущий прогноз и качество данных;
- **Прогноз** — почасовой график, версии, горизонт, actuals в backtest и экспорт;
- **Источники** — CSV, weather и industrial connections, импорт и отчёты;
- **Журнал агента** — шаги workflow, аргументация, длительность и ошибки.

В верхней панели выбираются источник данных, `live`/`backtest`/`replay`, часовой пояс, язык и тема. В fixture-режиме можно отдельно проверить loading/empty/error-состояния. Все синтетические данные явно помечены.

## Основной сценарий через API

Все `/api/v1/*` защищены cookie-сессией. Сначала выполните вход и сохраните cookie:

```bash
curl -c terra.cookies \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"local-terra-admin-password"}' \
  http://localhost:3000/api/auth/session
```

Далее передавайте `-b terra.cookies`.

### 1. Создать объект

```bash
curl -b terra.cookies \
  -H "Content-Type: application/json" \
  -d '{
    "kind":"turbine",
    "name":"Турбина 1",
    "latitude":43.645150,
    "longitude":78.535604,
    "time_zone":"Asia/Almaty",
    "power_unit":"normalized"
  }' \
  http://localhost:3000/api/v1/assets
```

Координаты взяты из ссылок ТЗ, однако их mapping и часовой пояс должен подтвердить владелец данных.

### 2. Импортировать CSV

`POST /api/v1/imports` принимает multipart-поля `file`, `config` (JSON) и необязательный `connectionId`. Сначала используйте `confirmed: false`, проверьте preview, затем повторите с `confirmed: true`.

```json
{
  "assetId": "<UUID объекта>",
  "dialect": {"encoding":"utf-8","delimiter":",","decimalSeparator":"."},
  "mapping": {
    "timestamp": "Статистическое время",
    "windSpeed": "Средняя скорость ветра(m/s)",
    "normalizedPower": "Нормализованная активная мощность",
    "ambientTemperature": "Средняя температура окружающей среды(°C)"
  },
  "time": {
    "format": "yyyy-MM-dd HH:mm:ss",
    "timeZone": "Asia/Almaty",
    "timestampMeaning": "interval_start",
    "sourceIntervalMinutes": 10,
    "availabilityLagMinutes": 10,
    "availabilityAssumption": "available after the source interval"
  },
  "units": {
    "windSpeed": "m/s",
    "normalizedPower": "normalized",
    "ambientTemperature": "degC"
  },
  "hourlyCoverageThreshold": 1,
  "confirmed": false
}
```

Отчёт: `GET /api/v1/imports/{id}`; CSV ошибок: `GET /api/v1/imports/{id}/errors`. Повторный импорт не должен удваивать наблюдения.

### 3. Запустить прогноз

```bash
curl -b terra.cookies \
  -H "Content-Type: application/json" \
  -d '{
    "asset_ids":["<UUID объекта>"],
    "issued_at":"2026-01-31T12:00:00Z",
    "horizon_hours":24,
    "mode":"backtest",
    "model_version":"baseline",
    "data_policy":"history_only"
  }' \
  http://localhost:3000/api/v1/forecast-jobs
```

`issued_at` должен быть ровно на границе часа. Production-путь публикует только `normalized`. При неполных входах API возвращает явный неполный результат, а не подмену.

Для durable workflow отправьте контракт в `POST /api/v1/agent-runs` с уникальным `Idempotency-Key`. Ответ `202` содержит `job_id`; статус доступен по `GET /api/v1/jobs/{id}`, журнал — `GET /api/v1/agent-runs/{id}`, отмена — `POST /api/v1/agent-runs/{id}/cancel`.

### Карта API

| Метод и путь | Назначение |
|---|---|
| `GET /api/health` | Готовность приложения и БД |
| `POST, DELETE /api/auth/session` | Вход и выход |
| `GET, POST /api/v1/assets` | Список и регистрация объектов |
| `GET, POST /api/v1/connections` | CSV connections и подтверждённые mappings |
| `POST /api/v1/connections/{id}/test` | Проверка sample-файла |
| `POST /api/v1/imports` | Preview или подтверждённый CSV import |
| `GET /api/v1/imports/{id}` | Статус и отчёт импорта |
| `POST /api/v1/training-jobs` | Создание training-задачи |
| `POST /api/v1/forecast-jobs` | Синхронный 24/48-часовой прогноз |
| `GET /api/v1/forecasts` | Поиск сохранённых прогнозов |
| `GET /api/v1/forecasts/{id}/export` | Воспроизводимый CSV export |
| `POST /api/v1/backtest-jobs` | Последовательный backtest |
| `GET /api/v1/evaluations/{id}` | Legacy backtest report; persisted evaluation worker reports пока не подключены |
| `POST /api/v1/agent-runs` | Durable agent job |
| `GET /api/v1/jobs/{id}` | Статус и текущий шаг |
| `POST /api/v1/replay-sessions` | Создание replay session |
| `POST /api/v1/replay-sessions/{id}/advance` | Продвижение virtual time |
| `POST /api/v1/industrial-connectors/{oracle\|wincc}` | Test/discover/enable gateway |

## Входные данные

В `resources/` находятся два CSV. Несмотря на их имена, фактический диапазон обоих файлов:

- начало: `2023-03-11 00:00:00`;
- конец: `2026-01-31 23:50:00`;
- шаг: 10 минут;
- строк за февраль 2026: **0**.

| Исходный столбец | Смысл |
|---|---|
| `ID` | ID строки внутри файла |
| `Статистическое время` | Локальная метка без указанной зоны |
| `Средняя скорость ветра(m/s)` | Скорость ветра, м/с |
| `Нормализованная активная мощность` | Цель в исходной нормализованной шкале |
| `Средняя температура окружающей среды(°C)` | Температура, °C |

Владелец данных должен подтвердить часовой пояс, начало/конец 10-минутного интервала, задержку доступности, смысл двух рядов, формулу нормализации, номинал, mapping координат и высоту ветра.

TERRA не называет нормализованные значения МВт/МВт·ч и не объединяет два ряда без подтверждения. Подробнее: [docs/data-contract.md](docs/data-contract.md) и [docs/data-audit.md](docs/data-audit.md).

## Agentic AI, replay и модель

Agent job выполняется возобновляемыми шагами. Runtime:

- атомарно сохраняет checkpoint и событие журнала;
- использует lease и fencing token против устаревшей публикации;
- ограничивает turns, tool calls и время;
- поддерживает retry, cancel и heartbeat;
- маскирует секреты и не сохраняет `OPENAI_API_KEY` в payload;
- использует `Idempotency-Key` против повторной публикации.

Replay хранит виртуальное время и события погоды. `advance` разрешает только движение вперёд и транзакционно обновляет cursor вместе с постановкой jobs.

По умолчанию `AGENT_LLM_ENABLED=false`. Для пояснений:

```dotenv
AGENT_LLM_ENABLED=true
OPENAI_API_KEY=<ключ>
OPENAI_MODEL=<проверенная модель>
OPENAI_REASONING_EFFORT=medium
```

При выключенном LLM или временной ошибке детерминированные gates продолжают работать, журнал фиксирует fallback.

Репозиторий содержит persistence baseline, признаки, ridge, power curve, временную валидацию, artifacts и backtest с MAE/RMSE. Обязательные gates:

- только `available_at <= issued_at`;
- `target_time = issued_at + lead_hour`;
- февральские targets — только `evaluation_only`;
- мартовский хвост не входит в февральскую метрику;
- при `N = 0` метрика отсутствует, а не равна нулю;
- фактическая погода не заменяет архивный forecast;
- выбор модели по февральской метрике запрещён.

Production inference поддерживает явно выбранный persistence и approved trained artifact. Загрузчик сверяет approval в реестре, версию, cutoff, SHA-256 файла и checksum artifact; файл должен находиться внутри `ARTIFACT_ROOT`. Ошибка trained inference не приводит к скрытому переходу на baseline. Создание artifact через CLI само по себе не регистрирует его в production: нужны запись `model_versions`, связанный `raw_artifacts` и доступный runtime файл.

### Исторический сценарий через CLI

Ниже указаны существующие entry points, а не свидетельство выполненного прогона. Нужны мигрированная БД, зарегистрированные UUID объектов, подтверждённая семантика и конфигурации. Сначала загружаются история и погода, затем обучается и регистрируется допустимая модель; для replay должны работать приложение и dispatcher.

```bash
node --import tsx scripts/weather-ingest.ts weather-config.json
node --import tsx scripts/train-approved.ts --input training-manifest.json --out .data/ml/approved
node --import tsx scripts/replay-february.ts --assets <uuid1>,<uuid2> --model <approved-model-uuid> --timezone Asia/Almaty --issue-hour 0 --mode replay --from 2026-01-31 --to 2026-02-28 --output .data/replay
node --import tsx scripts/evaluate-forecasts.ts evaluation-request.json actuals.json
```

`Asia/Almaty` здесь пример явного календаря, а не подтверждение timezone исходных CSV. Форматы входов и порядок регистрации описаны в [P1](docs/handoffs/parallel-P1.md), [P2](docs/handoffs/parallel-P2.md), [P4](docs/handoffs/parallel-P4.md), [P5](docs/handoffs/parallel-P5.md), [P6](docs/handoffs/parallel-P6.md).

- Weather CLI сохраняет архивные данные, но возвращает код 2 при недоказанной исторической доступности; их нельзя автоматически считать пригодными для следующего шага.
- Training без исторических snapshots не даёт подтверждённую модель. Синтетические входы остаются `candidate`.
- Batch replay сохраняет manifests и почасовой JSON с происхождением; повтор той же команды возобновляет пакет. Его `officialResult` всегда `false`: успешное исполнение ещё не подтверждает официальный результат.
- Evaluation использует отдельные revisions факта и сохраняет версии отчёта в PostgreSQL. Требуется подтверждённый semantic manifest; шаблон [semantic-manifest.json](src/server/evaluation/semantic-manifest.json) содержит `UNKNOWN`. Нет пар — нет числовой метрики.

## Проверки

Во время обновления README выполнено только чтение исходников и ревью diff. Тесты, lint, typecheck, сборка, Docker и проект **не запускались по просьбе пользователя**. Следующие команды — инструкция для будущей проверки, не список PASS.

Основной набор:

```bash
npm test
npm run test:foundation
npm run test:agent
npm run test:agent:replay
node --test tests/weather/weather.test.mjs
node --test tests/acceptance/harness.test.mjs
npm run lint
npm run typecheck
npm run build
docker compose config --quiet
docker compose build app
```

PostgreSQL integration требует отдельную одноразовую БД. Agent test намеренно отказывается от URL, имя БД которого не содержит `test`.

```powershell
$env:TEST_DATABASE_URL = "postgres://terra:password@localhost:5432/terra_test"
npm run test:postgres
npm run test:agent:integration
```

OpenAI smoke по умолчанию пропускается:

```powershell
$env:RUN_OPENAI_SMOKE = "1"
$env:OPENAI_API_KEY = "..."
$env:OPENAI_MODEL = "..."
npm run test:agent:openai
```

Acceptance harness:

```bash
node --test tests/acceptance/harness.test.mjs
node tests/acceptance/run.mjs verify
```

Harness подключён к `demo:import/train/backtest/export/verify`. Команды выполняют synthetic component integration suites на disposable PostgreSQL, сохраняют журналы и отдельный historical BLOCKED отчёт. Это ещё не единая сквозная цепочка; `demo:verify` не возвращает общий PASS. Настройка и повторный запуск: [docs/demo.md](docs/demo.md).

## Структура репозитория

```text
app/                         Next.js App Router и HTTP routes
src/components/dashboard/    Dashboard, API client и fixtures
src/server/agent/             Production agent workflow и adapters
src/server/connectors/        CSV, Open-Meteo и industrial contracts
src/server/data/              Импорт, качество и snapshots
src/server/db/migrations/     SQL migrations
src/server/forecast/          Расчёт, публикация и хранилище прогнозов
src/server/jobs/              Durable jobs, lease, checkpoint и runner
src/server/ml/                Baseline, features, ridge и training
src/server/replay/            Виртуальные часы и replay sessions
src/server/backtest/          Backtest и leakage gates
src/server/triggers/          Обнаружение новых входов и durable input events
src/server/evaluation/        Изолированный факт и persisted evaluation reports
tests/                        Unit, integration, UI и acceptance tests
scripts/                      Миграции, dispatcher, weather/training/replay/evaluation CLI
resources/                    ТЗ и исходные CSV
docs/                         Контракты, аудиты и demo-инструкции
samples/                      Synthetic CC0 smoke fixture
```

В проекте временно есть `app/` и `src/app/`: корневой `app/` — фактический App Router, часть handlers делегирует реализацию модулям из `src/app/`.

## Переменные окружения

| Переменная | Обязательность | Назначение |
|---|---|---|
| `DATABASE_URL` | Да вне Compose | PostgreSQL URL |
| `POSTGRES_PASSWORD` | Для Compose | Пароль PostgreSQL |
| `ADMIN_USERNAME` | Нет | Login, по умолчанию `admin` |
| `ADMIN_PASSWORD` | Да | Пароль веб-сессии |
| `ADMIN_API_TOKEN` | Да | Внутренний token backtest/evaluation/export |
| `SESSION_SECRET` | Да | HMAC cookie secret, минимум 32 символа |
| `JOB_TICK_SECRET` | Для agent jobs | Защита internal tick |
| `ARTIFACT_ROOT` | Нет | Raw/artifacts, по умолчанию `.data/artifacts` |
| `IMPORT_BATCH_SIZE` | Нет | Batch импорта, по умолчанию 500 |
| `FORECAST_CONFIG_VERSION` | Нет | Forecast config, по умолчанию `baseline-v1` |
| `AGENT_LLM_ENABLED` | Нет | Включение LLM, по умолчанию `false` |
| `OPENAI_API_KEY` | При LLM | Ключ OpenAI, не сохраняется в jobs |
| `OPENAI_MODEL` | При LLM | Явно проверенная модель |
| `AGENT_MAX_TURNS` | Нет | Лимит turns, по умолчанию 8 |
| `AGENT_MAX_TOOL_EXECUTIONS` | Нет | Лимит tools, по умолчанию 16 |
| `AGENT_LLM_TIMEOUT_MS` | Нет | LLM timeout, по умолчанию 30000 |
| `AGENT_TOOL_TIMEOUT_MS` | Нет | Tool timeout, по умолчанию 45000 |
| `AGENT_TICK_BUDGET_MS` | Нет | Tick budget, по умолчанию 60000 |
| `AGENT_LEASE_MS` | Нет | Lease, по умолчанию 90000 |
| `AGENT_HEARTBEAT_MS` | Нет | Heartbeat, по умолчанию 15000 |
| `JOB_DISPATCHER_BASE_URL` | Нет | App URL, по умолчанию `http://localhost:3000` |
| `JOB_DISPATCHER_INTERVAL_MS` | Нет | Пауза ticks, по умолчанию 1000 |
| `INPUT_TRIGGER_CONFIG` | Для worker Compose | Путь к JSON с объектами, моделью и календарём input-trigger |
| `EVALUATION_CONFIG` | Для worker Compose | Путь к JSON с forecastRunIds, calendarTimezone и manifest |
| `EVALUATION_POLL_MS` | Нет | Пауза evaluation worker, по умолчанию 30000 |
| `ORACLE_CONNECTOR_GATEWAY_URL/TOKEN` | Для Oracle | URL и token server gateway |
| `WINCC_CONNECTOR_GATEWAY_URL/TOKEN` | Для WinCC | URL и token server gateway |

Базовый безопасный шаблон: [.env.example](.env.example).

## Ограничения

1. В CSV нет февральского факта, поэтому официальный MAE/RMSE за 1–28 февраля не вычисляется.
2. Open-Meteo evidence не доказывает исторический момент публикации weather run.
3. Weather ingestion пишет в canonical tables, но оставляет исторические `published_at/available_at` NULL; production runtime такие runs не допускает.
4. Trained inference подключён, но реальный approved artifact и его качество не подтверждены. Input-trigger snapshot содержит только ветер, без требуемой температуры.
5. Legacy training/backtest stores остаются локальными/in-memory. Новый evaluation worker сохраняет отчёты в PostgreSQL, но `/api/v1/evaluations/{id}` всё ещё читает legacy registry.
6. Dashboard adapters согласованы с canonical envelopes в коде; HTTP/browser E2E в этом ревью не проверялся. Синтетический UI не доказывает работу на реальных данных.
7. Dispatcher включён в Compose; автоматический input-trigger и evaluation требуют отдельного worker-конфига, а weather ingestion остаётся отдельным шагом.
8. Без подтверждения семантики нельзя переводить мощность в MW/MWh или суммировать два ряда.

Проект не маскирует эти ограничения синтетическими результатами и не подменяет архивный прогноз фактической погодой.

## Дополнительная документация

- [ТЗ кейса](docs/hackalem-ai-agentic-wind-forecasting.md)
- [Контракт данных](docs/data-contract.md)
- [Аудит CSV](docs/data-audit.md)
- [Аудит backend](docs/backend-spec-audit.md)
- [Weather verification](docs/weather-verification.md)
- [Agent runtime verification](docs/agent-runtime-verification.md)
- [Industrial connectors](docs/industrial-connectors.md)
- [Acceptance](docs/acceptance.md)
- [Demo](docs/demo.md)
- [Synthetic sample](samples/README.md)

## Дальнейшее развитие

Следующие шаги для соответствия ТЗ: сохранять полный набор trained features в input-trigger snapshot; подключить persisted evaluations к API; связать получение погоды с автономным циклом; подтвердить семантику источника и историческую доступность weather runs; обучить и зарегистрировать реальный artifact; воспроизвести последовательность февральских выпусков и отдельно оценить их по закрытому факту. Изменения этих компонентов в рамках обновления README не выполнялись.
