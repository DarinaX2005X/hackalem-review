# AML Agent

AML Agent превращает обезличенный граф банковских переводов в объяснимую очередь проверок для AML-аналитика. Система проверяет входные данные, рассчитывает детерминированные графовые признаки, назначает роли, ранжирует цели, создаёт локальный review case и независимо проверяет полученные артефакты.

> Текущий статус: работают детерминированная аналитика, CLI agent, FastAPI и React UI на встроенном датасете (фазы 0–5). Docker Compose собирает и запускает полный demo workflow без API-ключа; состояние остальных задач фазы 6 отражено в [TODO.md](TODO.md).

## Запуск через Docker Compose

Для воспроизводимого demo не нужен `.env` или API-ключ:

```bash
docker compose up --build
```

После успешных healthchecks откройте <http://127.0.0.1:5173>. Backend health доступен по <http://127.0.0.1:8000/health> и через frontend proxy по <http://127.0.0.1:5173/health>. По умолчанию используется `DEMO_MODE=true`; аналитика, tools, SQLite, review case, экспорт и verification выполняются по-настоящему.

Остановка контейнеров:

```bash
docker compose down
```

Именованные volumes сохраняют SQLite и артефакты между обычными перезапусками. Команду `docker compose down --volumes` используйте только когда нужно намеренно удалить локальное demo-состояние.

## Запуск HTTP API и демоверсии

Из корня репозитория, с Python 3.12+ (macOS/Linux):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.lock
python -m pip install --no-deps --no-build-isolation -e backend
python -m pip install -r backend/requirements-api.txt
python -m uvicorn backend.app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1
```

Windows PowerShell, без активации окружения:

Если установлен Python новее 3.12, замените `-3.12` ниже на его версию.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e backend
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-api.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1
```

Откройте [интерактивную документацию API](http://127.0.0.1:8000/docs) или [health](http://127.0.0.1:8000/health).
`/health` показывает доступность backend. В `/docs` создайте run через `POST /api/runs` с `{"dataset_id":"bundled","mode":"demo"}`, затем передайте полученный `run_id` в `POST /api/runs/{run_id}/execute`. Дождитесь `status=completed` и `verification_status=passed` в `GET /api/runs/{run_id}`; только после этого доступны оценки узлов, case и проверенные файлы. API принимает только встроенный `dataset_id=bundled`, без загрузки произвольных parquet. В demo-режиме API-ключ не нужен. Используйте один Uvicorn worker: координация выполняющихся запусков находится в памяти процесса.

### Запуск интерфейса React

Оставьте API работающим и в другом терминале выполните:

```bash
cd frontend
npm ci
npm run dev
```

Откройте <http://127.0.0.1:5173> и нажмите **Start bundled demo**. Интерфейс покажет безопасный execution trace, затем проверенные top-20, кластеры, направленный 1–2-hop ego graph, локальный review case и скачиваемые файлы. **Reset demo** доступен после завершения run. Подробности: [frontend/README.md](frontend/README.md).

```bash
python -m pip install -r backend/requirements-api-dev.txt
python -m pytest backend/tests/api -q
python -m ruff check backend/app/api backend/app/config.py backend/app/main.py backend/tests/api
```

Тесты `backend/tests/api/` проверяют HTTP-контракт и полный golden path на настоящем backend. Зависимости HTTP зафиксированы отдельно от `backend/requirements.lock`. Для полного набора установите также `backend/requirements-api-dev.txt`, затем запустите `python -m pytest backend/tests -q` в активированном окружении (Windows без активации: `.\.venv\Scripts\python.exe -m pytest backend\tests -q`).

## Проблема

AML-аналитик начинает с 81 известного seed-клиента, но должен вручную исследовать четырёхуровневую сеть из 2 248 счетов. Полезный результат — не общее резюме, а ответ на три конкретных вопроса: **какие счета проверять первыми, почему и какие данные подтверждают этот приоритет**.

AML Agent — инструмент поддержки решений. Роли и приоритеты являются гипотезами для проверки аналитиком, а не доказательствами вины и не указаниями блокировать счёт.

## Целевой рабочий процесс

```text
Пакет parquet
  -> проверка данных и ограничений
  -> построение направленного взвешенного графа
  -> расчёт структурных и временных признаков
  -> кластеризация и назначение объяснимых ролей
  -> ранжирование целей для проверки
  -> создание локального AML review case
  -> экспорт и проверка обязательных артефактов
```

В live-режиме модель OpenAI выбирает контролируемые tools и возвращает конечное решение по строгой схеме. Детерминированный backend рассчитывает роли и метрики, создаёт case и проверяет результаты.

## Реализованный основной сценарий через CLI

Текущий offline workflow выполняет девять изменяющих состояние или проверочных шагов. Десятый контролируемый tool, `get_node_evidence`, вызывается по запросу:

```text
inspect_dataset -> build_graph -> compute_graph_features -> cluster_network
-> assign_roles -> rank_targets -> create_review_case -> export_results
-> verify_run -> completed
```

На встроенном датасете система создаёт 2 248 оценок узлов, 91 сводку по кластерам, top-20, один локальный review case, три обязательных CSV-файла, форматированный `aml_review_report.xlsx`, `audit.json` и независимый отчёт проверки. Demo-режиму API-ключ не нужен.

### Быстрый запуск в Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e backend
.\.venv\Scripts\aml-agent-tools.exe --data data --database var\aml-agent.sqlite3 --artifacts artifacts --top 20
.\.venv\Scripts\aml-agent-run.exe --mode demo --data data --database var\agent.sqlite3 --artifacts artifacts
```

### Быстрый запуск в macOS/Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e backend
.venv/bin/aml-agent-tools --data data --database var/aml-agent.sqlite3 --artifacts artifacts --top 20
.venv/bin/aml-agent-run --mode demo --data data --database var/agent.sqlite3 --artifacts artifacts
```

Успешный `aml-agent-run` печатает конечное решение со `status: completed` и `case_id`. Сохранённый run имеет `verification_status: passed`; команда `aml-agent-tools` дополнительно печатает результаты девяти обязательных tools с `ok: true`. Каждый запуск создаёт новую запись run.

## Датасет

В репозитории находится обезличенный датасет хакатона:

- `data/nodes.parquet`: 2 248 клиентов;
- `data/edges.parquet`: 3 119 агрегированных направленных рёбер;
- `data/transactions.parquet`: 4 840 отдельных транзакций;
- период: с 2026-07-01 по 2026-07-31;
- наблюдаемый оборот: 365 890 012,01 KZT.

Поля и ограничения сбора описаны в [data/README.md](data/README.md). Главное ограничение — граница обхода в четыре перехода: у 444 узлов с `depth=4` нет видимых исходящих переводов, поэтому их нельзя автоматически считать конечными получателями.

## Критерии ролей

Версия правил `v1` назначает каждому узлу одну роль в указанном порядке. `in_degree` и `out_degree` считают уникальных наблюдаемых контрагентов; `pass-through` равен наблюдаемому `out_kzt / in_kzt` и не применяется к seed-клиентам.

| Роль | Условие |
|---|---|
| `coordinator` | Не seed, `depth < 4`, есть входящие и исходящие рёбра; достижимость от seed не ниже 90-го percentile, составной индекс координации не ниже 99-го percentile. |
| `consolidator` | Не seed, `in_degree >= 5`, `pass-through < 0.5`. |
| `distributor` | `out_degree >= 10` и `out_degree >= 2 × max(in_degree, 1)`. |
| `transit` | Не seed, `depth < 4`, `in_degree >= 2`, `out_degree >= 1`, `0.8 <= pass-through <= 1.2`. |
| `terminal` | Не seed, `depth < 4`, `out_degree = 0`, `in_degree >= 2`. |
| `peripheral` | Остальные узлы, включая изолированные seed и узлы с недостаточным evidence на границе обхода. |

`role_score` измеряет силу совпадения с правилом; `priority_score` задаёт порядок проверки аналитиком. Ни один из них не является вероятностью преступления. Кластеры строятся Louvain по ненаправленной проекции, но признаки ролей используют направленные переводы. Формулы scores, порядок разрешения равенств и шаблоны evidence приведены в [аналитическом ruleset](docs/ANALYTICS.md).

## Ограничения данных

- У 444 узлов на `depth=4` дальнейший outflow не наблюдался из-за границы обхода; они получают флаг неопределённости, а не автоматическую роль `terminal`.
- Входящий поток seed-клиентов неполон, поэтому их pass-through нельзя надёжно оценить. Все 19 seed без рёбер всё равно включены в `nodes_roles.csv`.
- Данные охватывают наблюдаемые переводы за июль 2026 года с порогом суммы от 5 000 KZT. Даты не содержат время, поэтому порядок переводов внутри дня неизвестен.
- В наборе нет ФИО, ИИН, возраста, дохода или размеченной истины. Результаты служат гипотезами для проверки аналитиком.
- GID хранится как `int64` в parquet/CSV, но передаётся как десятичная строка в API, JSON и аргументах tools: значения превышают безопасный диапазон JavaScript.

## Архитектура

React UI получает результаты через FastAPI, который передаёт работу одному orchestrator с контролируемыми tools. Детерминированная аналитика рассчитывает роли и приоритеты; SQLite хранит run, events и case; локальные артефакты проверяются независимо перед выдачей. Диаграмма компонентов и сценарий показа находятся в [docs/JUDGING_DEMO.md](docs/JUDGING_DEMO.md).

Подробная документация:

- [Архитектура](docs/ARCHITECTURE.md)
- [Baseline фазы 0](docs/BASELINE.md)
- [Результаты проверки фаз 0–2](docs/PHASES_0_2_RESULTS.md)
- [Модель данных](docs/DATA_MODEL.md)
- [Аналитические правила](docs/ANALYTICS.md)
- [Контракты tools](docs/TOOLS.md)
- [Цикл агента](docs/AGENT_LOOP.md)
- [HTTP API](docs/API.md)
- [План реализации](TODO.md)

## Настройка OpenAI

Live orchestrator использует OpenAI Responses API с function calling и Structured Outputs. Модель задаётся через `OPENAI_MODEL`; analytics, роли и verification остаются детерминированными. Для live-режима после основной установки добавьте extra `backend[live]` (он включает официальный SDK), затем задайте ключ в окружении или игнорируемом корневом `.env`:

```bash
.venv/bin/python -m pip install -e 'backend[live]'
```

В Windows PowerShell используйте `.\.venv\Scripts\python.exe -m pip install -e 'backend[live]'`.

```dotenv
DEMO_MODE=false
OPENAI_API_KEY=<ваш существующий ключ>
OPENAI_MODEL=gpt-5-mini
```

Ключ вводится только локально: не отправляйте его в чат и не добавляйте в `.env.example`. Корневой `.env` исключён из Git.

После настройки можно использовать любой из двух способов:

- Docker: `docker compose up --build`, затем выберите **OpenAI live** в интерфейсе. Образ уже содержит зафиксированную версию OpenAI SDK.
- CLI: `aml-agent-run --mode live --data data --database var/live.sqlite3 --artifacts artifacts`. На Windows используйте `.\.venv\Scripts\aml-agent-run.exe`; на macOS/Linux — `.venv/bin/aml-agent-run`.

Через HTTP API создайте run с `{"dataset_id":"bundled","mode":"live"}`, затем вызовите `/execute`. Ключ нельзя добавлять в исходный код, логи или коммиты.

CLI по умолчанию запускается с `--mode demo`. Настройка API `DEMO_MODE=true` также выбирает demo для новых runs без явного `mode` и разрешает локальный demo reset; `DEMO_MODE=false` меняет режим по умолчанию на live и отключает reset. Demo заменяет только model provider — аналитика, tools, case, экспорт и проверка остаются настоящими.

Автоматические тесты live-provider используют имитацию транспорта Responses. Настоящий внешний запрос к OpenAI API ими не проверяется.

## Запуск стартового решения

Starter проверяет parquet-файлы, строит граф, рассчитывает базовые признаки и записывает пустые шаблоны результатов. Это baseline, а не готовый продукт.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r starter/requirements.txt
.venv/bin/python starter/starter.py --data data --out out
```

В Windows замените `.venv/bin/python` на `.\.venv\Scripts\python.exe`.

Ожидаемые файлы:

- `out/nodes_roles.csv`
- `out/clusters.csv`
- `out/top_nodes.csv`

Starter намеренно не реализует назначение ролей, кластеризацию, ранжирование и визуализацию.

## Компонент оркестрации фазы 3

`backend/aml_agent/agent/` содержит ограниченный цикл запуска, demo-provider, адаптер OpenAI Responses, строгую проверку вызовов tools и адаптеры к рабочим SQLite-аудиту и runtime tools. Demo-режим выполняет настоящую аналитику и создание case. Интеграционный тест сравнивает результаты demo- и live-provider на встроенных parquet-файлах; транспорт Responses в тесте имитируется.

Запуск тестов после установки `backend/requirements-api-dev.txt`:

```bash
python -m pytest backend/tests -q
```

Для live-режима требуются дополнительные зависимости `backend[live]` и `OPENAI_API_KEY` в окружении или игнорируемом `.env`.

## Создаваемые артефакты

- `nodes_roles.csv`: одна строка для каждого из 2 248 узлов;
- `clusters.csv`: статистика кластеров и осторожная гипотеза;
- `top_nodes.csv`: минимум 20 ранжированных целей для проверки;
- `aml_review_report.xlsx`: те же проверенные данные в удобной для аналитика книге с фильтрами, закреплёнными заголовками, переносом текста и настроенной шириной колонок;
- `audit.json`: хеш датасета, версия ruleset, события tools, предупреждения и результат проверки;
- браузерный UI с направлением графа, ролями, кластерами, поиском GID, execution trace и состоянием до/после;
- локальный review case в SQLite со snapshot top-20.

Артефакты каждого run сохраняются в `artifacts/<run_id>/` и исключены из Git. Для получения проверенных файлов на своей машине запустите `aml-agent-tools` или demo в React UI; скачивание доступно только после `verification_status=passed`. Проверенные counts, SHA-256 и команда воспроизведения описаны в [docs/VERIFIED_EXPORTS.md](docs/VERIFIED_EXPORTS.md).

## Безопасность и объяснимость

- В JSON значения GID передаются строками, потому что они превышают безопасный целочисленный диапазон JavaScript. В CSV/parquet сохраняется `int64`.
- Входящие переводы seed-клиентов неполны, поэтому их коэффициент pass-through нельзя использовать без оговорок.
- Узел с `depth=4` без видимого исходящего ребра получает флаг `truncated_by_depth`, а не автоматически роль `terminal`.
- `role_score` означает силу совпадения с правилом, а не вероятность преступной деятельности.
- Каждая строка evidence должна ссылаться на рассчитанные значения и занимать не более 200 символов.
- Внешние и разрушительные действия не входят в MVP. Единственное действие для аналитика — создание локального review case и проверенного пакета экспорта; служебные run, events и audit также сохраняются локально.

## Масштабирование и режим работы

Проверенный масштаб встроенного датасета — 2 248 узлов, 3 119 рёбер и 4 840 транзакций. Pipeline использует pandas/NetworkX в памяти, SQLite и локальные файлы; HTTP API запускается с одним Uvicorn worker. API ограничивает размер страниц и ego graph, но чтение узлов после завершения run заново загружает проверенные CSV и исходный parquet и пересчитывает признаки. Это локальный однопользовательский MVP, без подтверждённой работы на графе в миллион узлов. Для большего масштаба потребуются другие реализации графового расчёта, хранения и bounded queries при сохранении контрактов API и tools.

## Устранение неполадок

| Симптом | Что проверить |
|---|---|
| `/health` возвращает 503 | Наличие трёх файлов `data/*.parquet`, доступность локальной SQLite и запуск из корня репозитория. |
| `409 OPENAI_KEY_REQUIRED` | Для demo выберите `mode=demo`. Для live установите `backend[live]` и настройте `OPENAI_API_KEY` локально. |
| `409 INVALID_STATE` при запросе узлов или файлов | Дождитесь `status=completed` и `verification_status=passed` у run. |
| `422` при запросе GID | Передайте канонический десятичный GID как строку, без JSON number или ведущих нулей. |
| `409 RUN_BUSY` при demo reset | Дождитесь завершения активного run и закройте SSE-подключения. |
| `503 EXECUTION_CAPACITY` или `STREAM_CAPACITY` | Повторите запрос после освобождения слота; для MVP оставьте один API worker. |
| Run завершился `failed` или `verification_failed` | Посмотрите безопасные events и сохранённые предупреждения, исправьте причину и создайте новый run. |
| UI на `:5173` не получает данные | Убедитесь, что FastAPI запущен на `127.0.0.1:8000`; Vite проксирует `/api` и `/health` на этот порт. |
| `docker compose up --build` не проходит healthchecks | Проверьте, что Docker Engine запущен, а порты 8000 и 5173 свободны; `docker compose ps` покажет состояние сервисов. |

Полный HTTP-контракт и коды ошибок описаны в [docs/API.md](docs/API.md). Вывод `/health` подтверждает доступность локального backend, но не действительность ключа или доступность внешнего API.

## Структура проекта

```text
.
|-- AGENTS.md
|-- TODO.md
|-- data/
|   |-- README.md
|   |-- edges.parquet
|   |-- nodes.parquet
|   `-- transactions.parquet
|-- docs/
|   |-- AGENT_LOOP.md
|   |-- ANALYTICS.md
|   |-- ARCHITECTURE.md
|   |-- API.md
|   |-- DATA_MODEL.md
|   |-- JUDGING_DEMO.md
|   |-- VERIFIED_EXPORTS.md
|   `-- TOOLS.md
|-- backend/
|   |-- app/api/          # Phase 4 HTTP routes, DTOs, SSE, adapters
|   |-- app/config.py
|   |-- app/main.py
|   |-- aml_agent/
|   |   |-- agent/
|   |   |-- analytics/
|   |   |-- storage/
|   |   |-- tools/
|   |   `-- tool_runtime.py
|   |-- tests/            # Phase 1–3 tests and Phase 4 tests/api/
|   |-- pyproject.toml
|   |-- requirements.lock
|   |-- requirements-api.txt
|   |-- requirements-live.txt
|   `-- requirements-api-dev.txt
|-- frontend/          # React/Vite/TypeScript UI и Cytoscape-граф
|-- docker-compose.yml # backend/frontend и healthchecks
|-- starter/
|   |-- README.md
|   |-- requirements.txt
|   `-- starter.py
|-- .env.example
`-- README.md
```

## Границы MVP

В hackathon MVP не входят автоматическая блокировка счетов, отправка данных регулятору, внешнее обогащение, выполнение произвольного кода, generic chat, multi-agent orchestration и production-обработка графа из миллиона узлов.

Для будущего развёртывания на миллионе узлов слой NetworkX следует заменить графовым движком или распределённой аналитической базой данных, сохранив контракты tools и API.
