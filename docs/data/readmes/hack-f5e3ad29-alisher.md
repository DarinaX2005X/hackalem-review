# Граф денег

Демо: https://hackalem-ai-finances-track.onrender.com

## Аналитика (`analysis/`)

Нужен Python 3.9+. Сеть, LLM и внешние данные не нужны.

Из корня репозитория:

```bash
python3 -m venv analysis/.venv
analysis/.venv/bin/python -m pip install -r analysis/requirements.txt
analysis/.venv/bin/python analysis/run.py
```

Расчёт занимает около 5 секунд. Скрипт читает Parquet из `docs/data/` и пишет CSV в `analysis/out/`:

| Файл | Что внутри |
|---|---|
| `nodes_roles.csv` | роли и приоритет всех клиентов |
| `top_nodes.csv` | топ-30 для проверки с объяснением |
| `clusters.csv` | кластеры и гипотезы по ним |
| `resilience.csv` | сценарии блокировки топ-N счетов |
| `data_requests.csv` | каких данных не хватает по узлам |
| `edges_flow.csv` | рёбра с долей денег seed |

Тесты:

```bash
analysis/.venv/bin/python -m unittest discover -s analysis/tests -v
```

Параметры, методика и описание колонок — в [analysis/README.md](analysis/README.md).

## Веб-интерфейс (`web/`)

Нужен Node.js 20+.

Из корня репозитория:

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

Откройте [localhost:3000](http://localhost:3000).

Данные для экрана лежат в `web/public/data/`: три Parquet и три CSV из аналитики. После нового запуска `analysis/run.py` скопируйте свежие CSV:

```bash
cp analysis/out/{nodes_roles,clusters,top_nodes}.csv web/public/data/
```

Граф работает без ключа. Для AI-функций задайте `OPENAI_API_KEY` в `web/.env.local`. Модели можно поменять через `OPENAI_MODEL` и `OPENAI_BRIEF_MODEL`.

Тесты:

```bash
cd web
npm test
```
