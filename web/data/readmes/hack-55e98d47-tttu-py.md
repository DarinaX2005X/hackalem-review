# Event Match

**До трёх подходящих подрядчиков из существующего каталога — с объяснением на основе фактов.**

Введите город, дату, формат мероприятия, категорию и бюджет; при необходимости —
длительность и язык общения. Event Match исключит неподходящих подрядчиков,
сравнит оставшихся и покажет цену «от», причины выбора и признаки synthetic/imputed.
AI помогает выбрать содержательный фрагмент описания; допуск и порядок определяет Python.
Приложение полностью работает без AI-ключа.

**Начать:** установите Python 3.13, клонируйте репозиторий и выполните команды
[Quick Start](#quick-start). Откройте `http://127.0.0.1:5000`, заполните форму или
запустите `python -X utf8 scripts/demo.py` из подготовленного окружения.

[CONTRACT.md](CONTRACT.md) фиксирует поведение и DTO.
[Финальная проверка](docs/FINAL_SUBMISSION_VERIFICATION.md) содержит выполненные проверки и ограничения.

## Problem & Value

В каталоге сложно одновременно сравнить занятость, цену, формат, языки и содержание
описаний. Event Match сокращает список до проверяемого shortlist: пользователь видит
не только имена, но и факты, объясняющие каждый выбор. При отсутствии совпадений
система показывает причины отказа, чтобы можно было осмысленно изменить запрос.
Каталог не расширяется автоматически; бронирование и окончательная цена согласуются с подрядчиком.

## How It Works

```text
User Query → Validation → City + Category → Hard Filters
           → Deterministic Ranking → Top ≤ 3 → Evidence
           → AI / Fallback Explanation → Web / API
```

**AI does NOT decide eligibility.** Python проверяет город, категорию, занятость,
бюджет, формат, опциональные длительность и язык. Модель получает только evidence
уже выбранных кандидатов и не может добавить карточку или изменить её место.

```text
FILTER WITH CODE.
RANK DETERMINISTICALLY.
EXPLAIN WITH EVIDENCE.
USE AI WHERE AI ADDS VALUE.
NEVER LET AI OVERRIDE FACTS.
```

## Implemented

- Единый подбор для HTML и JSON API, максимум три карточки, три явных исхода.
- Диагностика причин отказа; deterministic ranking и объяснения без внешней модели.
- Интерфейс и framing объяснений RU / ҚАЗ / EN; язык подрядчика — отдельный фильтр.
- Смена языка сохраняет черновик и предыдущий результат без повторного AI-вызова.
- Сравнение 2–3 карточек по фактическим публичным полям без выдуманного «победителя».
- JSON/CSV-экспорт сохранённого результата; CSV защищён от формул электронных таблиц.
- Светлый адаптивный интерфейс, synthetic/imputed-маркеры и предупреждение о цене «от».
- Администратор может проверить CSV, увидеть preview и явно подтвердить полную замену каталога.
- Отдельные CLI-команды validate/stage для доверенного локального оператора.

## Architecture

Модульный монолит: один процесс, Flask routes, общие сервисы и локальная SQLite.

```text
Browser → Web / Jinja2 ─┐
                       ├→ RecommendationService → Filters → Ranking → Evidence
JSON API ──────────────┘                                             ↓
                             CatalogManager ← SQLite       AI reason IDs / Fallback
                                   ↑                                  ↓
                      validated source / active CSV            factual explanation
```

`create_app()` создаёт приложение. `CatalogManager` сериализует чтение/активацию;
каждая операция SQLite использует собственное соединение. Один и тот же
`RecommendationService` обслуживает Web, API и экспорт нового запроса.
Экспорт snapshot не запускает подбор повторно.

## Technology & Project Structure

Python **3.13**, Flask **3.1.3**, Jinja2, Bootstrap **5.3.3**, SQLite из стандартной
библиотеки, httpx **0.28.1**, Waitress **3.0.2**. Проверки: pytest **8.4.2**,
Ruff **0.16.8**, Black **26.5.1**. Прямые зависимости закреплены в requirements;
транзитивные зависимости разрешает pip. Bootstrap CSS загружается с CDN.

```text
app/
  __init__.py, config.py    factory и runtime configuration
  models/, repositories/   DTO, CSV validation, SQLite
  services/                filtering, ranking, evidence, exports, catalog management
  ai/                      bounded chat-completions transport
  api/, web/               JSON / HTML / authenticated administration
  templates/, static/      Jinja2, CSS, JavaScript
 data/hackathon_dataset.csv исходный каталог: 66 профилей, 13 synthetic
 scripts/                  demo.py, product_qa.py, configure_admin.py
 tests/                    unit, integration, frontend, fixtures
 docs/                     текущий отчёт финальной проверки
 run.py                    development entry point
 requirements*.txt         runtime / development dependencies
 CONTRACT.md               behavioral and technical contract
```

## Quick Start

Требуются Git и установленный **Python 3.13**. Команды выполняются из корня проекта.
Для независимой проверки используйте новую папку clone: локально применённый каталог
в `instance/` меняет демонстрационные результаты.

Windows / PowerShell:

```powershell
git clone --branch feature/jonas https://github.com/BAITC-Hacks/hack-55e98d47-tttu-py.git
cd hack-55e98d47-tttu-py
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
$env:LLM_API_KEY = ""
.venv/Scripts/python.exe run.py
```

macOS / Linux:

```bash
git clone --branch feature/jonas https://github.com/BAITC-Hacks/hack-55e98d47-tttu-py.git
cd hack-55e98d47-tttu-py
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
export LLM_API_KEY=""
.venv/bin/python run.py
```

Откройте `http://127.0.0.1:5000`; `http://127.0.0.1:5000/api/v1/health`
возвращает `{"status":"ok"}`. Остановить сервер: Ctrl+C.

**`.env` служит локальным шаблоном и автоматически не загружается.** Передавайте
значения через `$env:NAME = "value"` (PowerShell), `export NAME="value"` (POSIX)
или secret manager. Для запуска без AI конфигурация сверх команд выше не нужна.
При старте валидируется CSV и создаётся SQLite snapshot; миграции вручную не нужны.
Отсутствующий или невалидный каталог останавливает запуск.

## Environment Variables

| Variable | Required | Purpose | Safe example / default |
| --- | --- | --- | --- |
| `DATASET_PATH` | Нет | Исходный CSV и словарь допустимых значений | `data/hackathon_dataset.csv` |
| `DATABASE_PATH` | Нет | SQLite snapshot, каталог должен быть writable | `instance/catalog.sqlite3` |
| `CATALOG_ACTIVE_PATH` | Нет | Применённый через Web CSV; имеет приоритет при старте | `instance/catalog-active.csv` |
| `CATALOG_STAGING_PATH` | Нет | Изолированный CLI staging snapshot | `instance/catalog-staged.sqlite3` |
| `LLM_API_KEY` | Только для AI | Секрет провайдера из secret manager | Пустая строка отключает AI |
| `LLM_BASE_URL` | Только для AI | HTTPS base URL с version prefix, без `/chat/completions` | `https://provider.example/v1` — placeholder |
| `LLM_MODEL` | Только для AI | Поддерживаемая провайдером модель | `your-model` — placeholder |
| `CATALOG_WEB_ADMIN_ENABLED` | Для Web admin | `1` включает администратора при корректных hash и secret | `0`; local setup включает автоматически |
| `CATALOG_ADMIN_PASSWORD_HASH` | Для Web admin | Werkzeug scrypt/pbkdf2 hash | Создаётся local setup; реального значения в Git нет |
| `FLASK_SECRET_KEY` | Для Web admin | Случайный ключ сессии, минимум 32 символа | Генерируется local setup / secret manager |
| `SESSION_COOKIE_SECURE` | Для HTTPS admin | Secure cookie при `1` | `0` локально, `1` для HTTPS |
| `CATALOG_ADMIN_ENABLED` | Для CLI admin | Явное разрешение validate/stage | `0`; установить `1` оператору |
| `HOST` | Нет | Адрес только development runner | `127.0.0.1` |
| `PORT` | Нет | Порт только development runner | `5000` |

Пути по умолчанию вычисляются от корня проекта. Явные относительные пути из environment
разрешаются от рабочего каталога процесса; для службы удобно использовать абсолютные пути.
CSV, активный CSV, SQLite и staging должны быть отдельными файлами. CLI staging
отклоняет совпадение с исходным/активным CSV, БД или входным файлом.
Environment admin credentials имеют приоритет над локальной конфигурацией.

## Without AI / With AI

Без `LLM_API_KEY` приложение фильтрует, ранжирует и строит конкретные объяснения
из evidence. Отсутствие любого из трёх `LLM_*` значений также включает fallback.

Для AI передайте все три значения через защищённую конфигурацию процесса.
Провайдер должен поддерживать chat-completions JSON endpoint,
`response_format=json_object` и `temperature=0`.
Один batch-вызов содержит evidence не более трёх кандидатов; общий deadline —
**3 секунды**, ответ — до **64 KiB**, без повторов и переходов по redirect.
AI возвращает только пары `candidate_id` / `reason_id`. Python проверяет их
принадлежность и формирует текст из фактов и исходной цитаты.
Timeout, недоступность, неподдерживаемые параметры, malformed JSON или чужие IDs
дают deterministic fallback. AI не участвует в score.

Тесты выполняют AI success, invalid output, network errors и timeout через test doubles;
реальный внешний провайдер и его качество/latency при финальной проверке не проверялись.

## Usage

1. Выберите город, дату, формат, категорию и бюджет; необязательно — часы и язык подрядчика.
2. Нажмите кнопку подбора. Проверьте цену «от», цитату описания и synthetic/imputed-флаги.
3. Для 2–3 карточек откройте сравнение; скачайте CSV или JSON текущего результата.
4. Измените дату или бюджет и отправьте новый запрос, чтобы пересчитать подбор.
5. RU / ҚАЗ / EN меняет интерфейс; прежнее объяснение сохраняет язык генерации.

Исходные описания и значения каталога не переводятся автоматически. При выключенном
JavaScript смена locale сохраняет только последние отправленные серверу поля.

## API

| Method / path | Назначение |
| --- | --- |
| `GET /api/v1/health` | Liveness: `200 {"status":"ok"}`; не проверяет провайдера и доступность диска |
| `POST /api/v1/recommendations` | Подбор; `200` для всех трёх продуктовых исходов |
| `POST /api/v1/recommendations/export` | JSON/CSV нового запроса или ранее сохранённого snapshot |
| `GET /`, `POST /` | Форма, подбор и переключение locale |
| `POST /recommendations/export/json`, `/csv` | Web download с `export_id` в body |
| `GET /admin/catalog` | Вход/управление; без конфигурации — страница `503` |

Ошибки запроса: `422` с `error.code=VALIDATION_ERROR` и `details`.
Неожиданная ошибка: generic `500 INTERNAL_ERROR`, без исключений и секретов.
Полный контракт, включая административные POST-операции и snapshot schema: [§13 и §23](CONTRACT.md).

Пример запроса (UTF-8 JSON):

```json
{
  "city": "Астана",
  "event_date": "2026-10-15",
  "event_format": "свадьба",
  "category": "Ведущий",
  "budget_kzt": 1000000,
  "duration_hours": 10,
  "language": "казахский"
}
```

Фактически полученный ответ исходного каталога без AI:

```json
{
  "status": "matched",
  "count": 1,
  "message": "Найдено подходящих подрядчиков: 1. На выбранную дату заняты 2 подрядчика этой категории; они исключены из подбора. Показаны все подрядчики города и категории, прошедшие условия заказа; их меньше трёх.",
  "recommendations": [{
    "id": "HK-97041",
    "anon_name": "Тэнъя Иида",
    "category": "Ведущий",
    "city": "Астана",
    "price_from_kzt": 1000000,
    "synthetic": false,
    "city_imputed": false,
    "price_imputed": false,
    "explanation": "Цена от 1 000 000 ₸ при бюджете 1 000 000 ₸; категория «Ведущий», город — Астана, формат — «свадьба», дата 2026-10-15 свободна; поддерживаемый язык — казахский; длительность 10 ч не превышает лимит 10 ч. В описании: «Тэнъя ведёт 12 лет на каз/рус языках , современно, интеллигентно , с юмором»."
  }]
}
```

`locale` принимает `ru` (default), `kk`, `en`. `communication_language` — alias
`language`; если переданы оба, их нормализованные значения должны совпадать.
Бюджет — целое число от 0 до 10^15, дата — существующая `YYYY-MM-DD`, длительность —
положительное конечное число до 10^6. Optional поля можно опустить или передать `null`.

Для экспорта нового запроса: `{"format":"json","request":{...}}` либо `csv`.
Для точного snapshot добавьте `X-Enable-Export: true` к обычному подбору; ответный
`X-Recommendation-Export-Token` передайте в body `{"format":"csv","export_token":"..."}`.
Отсутствующий/истёкший token даёт `404 EXPORT_NOT_FOUND`. Token — bearer capability,
его нельзя помещать в URL или журналы. Необязательный сбой snapshot не отменяет подбор.

Snapshots живут 15 минут в памяти процесса, до 128 записей по 256 KiB в каждом
Web/API store; возможны вытеснение и потеря при перезапуске. JSON/CSV сохраняют
исходные запрос, результат, locale и UTC timestamp. CSV использует UTF-8 BOM,
фиксированные колонки и защиту формул. Экспорты формируются в памяти.

## Recommendation Logic

1. Точное совпадение города и вхождение категории в multi-category профиль.
2. Дата отсутствует в `busy_dates`; цена «от» не превышает бюджет; формат поддерживается.
3. Если заданы часы, они не превышают `max_hours`; `null` означает, что услуга не
   привязана к присутствию на площадке. Если задан язык — он входит в `languages`.
4. Для допустимых профилей: `score = 35B + 45S + 10L + 10D`, затем `score DESC, id ASC`.

`B` — доля использования бюджета (price/budget, при нулевом бюджете и цене — 1).
`S` — среднее долей совпавших основ слов формата и категории в описании, [0, 1].
`L` — 1 при явно запрошенном совпадающем языке, иначе 0.
`D` — requested_hours/max_hours; при `max_hours=null` — 1; без запроса часов — 0.
`Fraction` исключает дрейф floating-point ties. Более высокая цена среди допустимых
может повышать budget signal: это использование бюджета, а не рейтинг качества.

Это bounded lexical proxy, а не embedding search. Сначала применяются фильтры,
потом score; хороший текст никогда не компенсирует занятость или превышение бюджета.
Для top ≤3 Python собирает evidence, затем AI выбирает допустимую цитату либо
fallback выбирает первый содержательный фрагмент. При отсутствии такого фрагмента
объяснение содержит только структурированные факты.

## Outcomes

| Product outcome | API status | Что видит пользователь |
| --- | --- | --- |
| `MATCHED` | `matched` | 1–3 карточки; объяснение малого числа результатов и занятости |
| `CATEGORY_NOT_FOUND` | `category_not_found` | В этом городе нет указанной категории |
| `NO_ELIGIBLE_CANDIDATES` | `no_eligible_candidates` | Категория есть; причины отказа по ограничениям |

Диагностика учитывает все нарушения каждого профиля: суммы причин могут превышать
число профилей. Коды `busy`, `over_budget`, `wrong_format`, `duration_too_long`,
`language_mismatch` не переводятся; пользовательские подписи локализованы.

## Demo Scenarios

Все сценарии используют исходные 66 профилей, без optional полей, бюджет **6 000 000 ₸**,
город **Алматы**, формат **свадьба**, дату **2026-10-15**, если не указано изменение.
Даты фиксированы для воспроизводимости; система не запрещает исторические даты.

| Сценарий | Категория / изменение | Ожидаемый результат |
| --- | --- | --- |
| A: dense | Ведущий | 3 карточки: HK-35215, HK-27222, HK-77838 |
| Rare | Флорист | 2 карточки, включая synthetic-профиль |
| B: date sensitivity | Ведущий; дата 2026-10-16 | Другой shortlist; занятые исключены |
| C: empty | Ведущий; бюджет 0 | `no_eligible_candidates`, причины отказа |
| Category absent | Флорист; город Зарубежье | `category_not_found` |
| D: AI failure | Команда теста ниже | Сбой/timeout AI сохраняет eligibility и порядок, включает fallback |
| E: product | RU/ҚАЗ/EN, сравнение, JSON/CSV | Те же IDs и сохранённый результат |

В другом терминале при запущенном приложении:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/demo.py
.venv/Scripts/python.exe -X utf8 scripts/product_qa.py
```

Первый скрипт печатает пять реальных HTTP-ответов с карточками, объяснениями,
диагностикой и временем. Второй проверяет API/Web/export, одинаковый порядок
для трёх locale, alias языка, сравнение и возвращает краткий JSON.
Оба принимают `--base-url http://127.0.0.1:8080` для production.
Демонстрация контролируемого отказа без ключей и внешних запросов:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/test_ai_client.py tests/integration/test_ai_pipeline.py --basetemp=.pytest-ai-temp
```

## Catalog Administration

Опционально, для локальной настройки пароля:

```powershell
.venv/Scripts/python.exe scripts/configure_admin.py
```

Команда запрашивает пароль дважды и сохраняет только Werkzeug hash и случайный
session secret в игнорируемом `instance/catalog-admin-auth.json`. Перезапустите
приложение, откройте `/admin/catalog`, войдите, скачайте шаблон и загрузите CSV.
Preview показывает SHA-256, число профилей/городов/категорий и пять фактических строк.
Отдельная кнопка подтверждает **полную замену** каталога; отмена удаляет preview.

CSV: UTF-8/BOM, до 1 MiB и 1000 профилей, списки через `|`, колонки исходного dataset.
Категории/форматы/языки должны принадлежать исходному словарю. Экспорт рекомендаций
имеет другую схему и не предназначен для импорта. Исходный CSV остаётся неизменным;
активный CSV сохраняется после перезапуска, прежние recommendation snapshots не меняются.
Сессия — 30 минут, preview — 15; CSRF, ограничение входа, HttpOnly/SameSite cookies.

CLI-подготовка изолированного snapshot, без активации:

```powershell
$env:CATALOG_ADMIN_ENABLED = "1"
.venv/Scripts/python.exe -m flask --app app.admin:create_admin_app catalog-admin validate data/hackathon_dataset.csv
.venv/Scripts/python.exe -m flask --app app.admin:create_admin_app catalog-admin stage data/hackathon_dataset.csv
```

На POSIX используйте `export CATALOG_ADMIN_ENABLED=1` и `.venv/bin/python`.
CLI требует доверенного доступа к ОС; dedicated factory не инициализирует активную БД.

## Testing

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-release-temp
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m black --check app tests scripts run.py
.venv/Scripts/python.exe -m pip check
```

На POSIX замените `.venv/Scripts/python.exe` на `.venv/bin/python`.
`--basetemp` обходит ограничения системной temp-папки; pytest очищает эту специально
выделенную папку, поэтому не указывайте вместо неё каталог с пользовательскими данными.
Тесты покрывают каждый hard filter, deterministic ranking, evidence/AI, три исхода,
CSV/SQLite, API/Web, locale/draft/snapshot/export, CSRF и активацию каталога.
Запускайте проверки в свежем clone с незаданными операторскими environment overrides.

Финальная проверка на Python 3.13.15: **291 passed**; Ruff, Black и `pip check` успешны.
Подробности окружения и границы проверки — в [отчёте](docs/FINAL_SUBMISSION_VERIFICATION.md).

## Deployment

### Development

`python run.py` в виртуальном окружении запускает Flask на `127.0.0.1:5000`, debug выключен.
Для другого адреса/порта задайте `HOST` и `PORT`. **Flask development server не является
production-сервером.** Не используйте `flask run --debug` для размещения.

### Production

Поддерживаемый способ — **один процесс Waitress**, 4 потока, factory `app:create_app`.
[Документация Flask](https://flask.palletsprojects.com/en/stable/deploying/waitress/)
описывает эту схему для Windows и POSIX.

```powershell
.venv/Scripts/python.exe -m waitress --host=127.0.0.1 --port=8080 --threads=4 --max-request-body-size=1114112 --call app:create_app
```

На POSIX замените путь Python. Адрес и порт задаются `--host` / `--port`,
health: `http://127.0.0.1:8080/api/v1/health`. Factory по умолчанию создаёт приложение
с debug=False; команда не включает debugger/reloader. Лимит тела Waitress 1 MiB + 64 KiB
допускает multipart overhead, Flask дополнительно ограничивает upload до 1 MiB,
обычный API body — до 16 KiB.

Для внешнего HTTPS разместите TLS reverse proxy перед loopback Waitress и задайте
`SESSION_COOKIE_SECURE=1`. Не запускайте приложение от root/Administrator.
Настройте supervisor/service на рабочий каталог проекта и тот же Python/environment.
Конкретный cloud/TLS/service deployment в финальной проверке не выполнялся.

Нужны readable source CSV, writable SQLite directory, writable active/staging directories
при администрировании и системная временная папка для буферизации WSGI. Сохраните
активный CSV на постоянном диске; SQLite восстанавливается из CSV при старте.
Не редактируйте SQLite вручную. Резервируйте свой active CSV перед заменой.
Несколько процессов, реплик или одновременный запуск dev и production на одних
runtime-файлах не поддерживаются; используйте разные пути либо остановите первый процесс.
AI-конфигурация та же, что при локальном запуске, и остаётся опциональной.

## Production Readiness & Limitations

Проверяемые основы: environment secrets, валидация, общий deterministic core,
ограниченный AI/fallback, защищённое управление каталогом, generic ошибки,
health endpoint и автоматические тесты. Текущее состояние проверок — в
[финальном отчёте](docs/FINAL_SUBMISSION_VERIFICATION.md).

Ограничения: SQLite и in-memory snapshots/лимиты/preview рассчитаны на один процесс;
нет load/SLA проверки, distributed activation, истории каталогов/rollback UI,
многопользовательских аккаунтов или бронирования. Health — только liveness.
Исходный каталог демонстрационный: synthetic/imputed-флаги не скрываются.
Цены «от» и занятость не заменяют подтверждение подрядчика. Bootstrap CDN требует сети;
полностью офлайн-визуальная проверка не заявляется. Внешний AI не проверялся live.

Rotate previously exposed credentials before public publication.

## Future Development

- Версионирование каталогов, аудит изменений и откат.
- Сохранённые поиски и пользовательские аккаунты.
- Улучшение переводов evidence и multilingual semantic ranking с оценкой качества.
- Общие snapshots/администрирование для нескольких процессов после измерения нагрузки.
- Метрики, трассировка отказов и rate limiting публичного API на уровне размещения.
- Интеграции с актуальными календарями и каталогами при сохранении прозрачных constraints.

Это roadmap. Locale, CSV/JSON-экспорт, сравнение и одиночный администратор уже реализованы.

## Reproducibility Checklist

Чеклист для самостоятельного запуска проверяющим; выполненные release-проверки записаны в отчёте.

- [ ] Install dependencies
- [ ] Configure environment
- [ ] Start application
- [ ] Open UI
- [ ] Run recommendation
- [ ] Check API health
- [ ] Run demo scenarios
- [ ] Run tests
