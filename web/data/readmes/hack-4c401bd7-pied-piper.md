<p align="center">
  <img src="docs/assets/money-graph-banner.svg" alt="Money Graph — HackAlem AI · трек Freedom · команда Pied Piper" width="100%">
</p>

<h1 align="center">Money Graph · Граф денег</h1>

<p align="center">
  <strong>HackAlem AI · Трек Freedom · Команда Pied Piper</strong><br>
  Объяснимая аналитика денежных потоков — от переводов до очереди ручной проверки.
</p>

<p align="center">
  <a href="https://www.hackalem.ai/"><img alt="HackAlem AI 2026" src="https://img.shields.io/badge/HackAlem_AI-2026-49c9bd?style=flat-square"></a>
  <img alt="Трек Freedom" src="https://img.shields.io/badge/Track-Freedom-92c83e?style=flat-square">
  <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white">
  <img alt="Docker Compose" src="https://img.shields.io/badge/Docker-Compose-2496ed?style=flat-square&amp;logo=docker&amp;logoColor=white">
  <img alt="Объяснимые правила" src="https://img.shields.io/badge/Explainable-Rule_based-49c9bd?style=flat-square">
</p>

<p align="center">
  <a href="#локальный-запуск"><strong>Запустить</strong></a> ·
  <a href="docs/methodology.md">Методология</a> ·
  <a href="docs/demo.md">Демо для жюри</a> ·
  <a href="docs/backend.md">Backend / API</a> ·
  <a href="docs/README.md">Вся документация</a>
</p>

| Данные | Аналитика | Результат |
| :--- | :--- | :--- |
| **2 248** клиентов · **3 119** связей | **6** объяснимых ролей · **105** сообществ | **Top-20** для проверки · **3 CSV** |

> **Кейс трека Freedom:** восстановление финансовой структуры по графу переводов. Разработано на [HackAlem AI](https://www.hackalem.ai/), Астана, 23 сентября 2026.

<details>
<summary>Организаторы и партнёры HackAlem AI</summary>

Среди организаторов и партнёров мероприятия на [официальном сайте HackAlem AI](https://www.hackalem.ai/) указаны Astana Hub, Silkroad Innovation Hub, OpenAI и BAITC.

<p>
  <a href="https://www.hackalem.ai/"><img alt="Astana Hub — партнёр мероприятия" src="https://img.shields.io/badge/Astana_Hub-18181b?style=flat-square"></a>
  <a href="https://www.hackalem.ai/"><img alt="Silkroad Innovation Hub — партнёр мероприятия" src="https://img.shields.io/badge/Silkroad_Innovation_Hub-6454c0?style=flat-square"></a>
  <a href="https://www.hackalem.ai/"><img alt="OpenAI — партнёр мероприятия" src="https://img.shields.io/badge/OpenAI-141414?style=flat-square"></a>
  <a href="https://www.hackalem.ai/"><img alt="BAITC — партнёр мероприятия" src="https://img.shields.io/badge/BAITC-2563eb?style=flat-square"></a>
</p>

</details>


---

Локальный инструмент объяснимой AML-аналитики графа переводов команды Pied Piper.
Роли и приоритеты — сигналы для ручной проверки, а не доказательства нарушения.

## Эксперимент устойчивости сети

В **«Сеть и сообщества» → «Устойчивость сети: исключение ключевых узлов»** можно
исключить top-1/3/5/10 клиентов по приоритету и сравнить результат с отбором по обороту.
Показаны размер крупнейшей группы, новые изоляты, доля разобщённых пар оставшихся
клиентов, затронутые суммы и списки gid. Расчёт использует полную сеть независимо от
фильтров, не меняет роли и CSV. Это симуляция наблюдаемого графа, не рекомендация
блокировки и не оценка предотвращённого ущерба. [Метод и ограничения](docs/methodology.md#устойчивость-сети-what-if).

## Структура

```text
backend/             API, worker, pipeline и независимый validator
  core/              загрузка, контракты, графовая аналитика, экспорт и чтение результатов
frontend/            Streamlit, визуализация графа и HTML-шаблон
docs/                архитектура, методология, контракты и отчёты аудита
tests/               аналитические, API, UI и интеграционные проверки
scripts/             служебные команды запуска и проверки
data/                исходные Parquet для сдачи (включены в Git)
outputs/             проверенный результат и current.json (включены в Git)
.streamlit/          настройки Streamlit для запуска из корня проекта
Dockerfile           общий runtime-образ и отдельная стадия tests
compose.yaml         UI, подготовка результатов, API, worker и CLI
requirements.lock    закреплённые зависимости общего Python-окружения
```

Все команды выполняются из корня репозитория. Используется Python 3.12.
UI читает опубликованные файлы напрямую; API и worker работают отдельным сервисом.

## Локальный запуск

Windows PowerShell (нужен `uv`):

```powershell
.\make.cmd setup
.\make.cmd demo
```

Синтетический демонабор создаётся локально и не требует исходных данных.
Предоставленные `nodes.parquet`, `edges.parquet` и `transactions.parquet` уже
включены в `data/`. Для повторного расчёта:

```powershell
.\make.cmd run
```

Linux/macOS: `make setup`, затем `make demo` или `make run`.
Интерфейс: http://localhost:3000. Для существующих результатов — `make ui` / `.\make.cmd ui`.
API и worker: `make backend` / `.\make.cmd backend` (порт 8000).

Прямые команды после активации окружения:

```bash
python -m backend.pipeline --data data --out outputs
python -m backend.validate --data data --out outputs
python -m streamlit run frontend/app.py --server.port 3000 -- --outputs outputs
python -m backend
python -m pytest -q
```

## Docker

Три входных Parquet для UI уже включены в `data/`:

```bash
docker compose build ui
docker compose up -d --no-build --pull never
```

`prepare` рассчитывает результаты в именованном volume `results` либо проверяет
существующую публикацию. `ui` запускается после успешной проверки на http://localhost:3000.

```bash
docker compose run --rm validate
docker compose run --rm --no-deps pipeline
docker compose --profile backend up -d api worker
docker compose build tests
docker compose run --rm tests
docker compose down
```

API доступен на http://localhost:8000. API/worker используют отдельный volume
`backend-state`, UI — `results`. Локальный `outputs/` не является Docker volume.
Остановка через `down` сохраняет volumes. Данные и результаты не включаются в образ.

## Аудит и документация

- [Навигация по документации](docs/README.md)
- [Подробное руководство](docs/product-guide.md)
- [Методология](docs/methodology.md) и [архитектура](docs/architecture.md)
- [Backend API и ограничения](docs/backend.md)
- [Воспроизводимые проверки](docs/qa.md)
- [Схема исходных данных](data/README.md)

Исходные данные, результаты, окружения, runtime и кэши исключены из Git.
На чистом клоне исходные данные предоставляются отдельно; тесты реальных данных
требуют локального набора. Исторические отчёты описывают проверки указанных в них
версий и не заменяют новый прогон. Ранее закоммиченные данные остаются в истории Git.
