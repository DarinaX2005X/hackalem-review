## Запуск

```bash
pip install -r requirements.txt
python start.py
```

Нужны Python и Node.js с npm. Откройте **http://localhost:8000**.
`start.py` установит отсутствующие npm-зависимости, соберёт Next.js с реальным API,
пересчитает граф и запустит FastAPI. Фронтенд и API работают на одном адресе.
Ключ `OPENAI_API_KEY` читается из корневого `.env`; во фронтенд он не передаётся.
Для повторного запуска без изменения фронта: `python start.py --skip-build`.
После изменения файлов фронта запускайте без `--skip-build`.

`pipeline.py` читает `nodes.parquet`, `edges.parquet` и `transactions.parquet`, а затем создаёт `out/nodes_roles.csv`, `out/clusters.csv`, `out/top_nodes.csv` и `out/graph.json`. API: `GET /api/graph`, `GET /api/node/{gid}`, `POST /api/ask`, `POST /api/resilience`.

## Схема решения

`данные → метрики → роли → Louvain-кластеры → graph.json → API/фронт`. Граф направленный и взвешенный. Роли — объяснимые `if`-правила, поэтому результат можно защитить по числам.

| Роль | Стартовый порог |
|---|---|
| distributor | 20+ разных получателей |
| consolidator | 8+ разных отправителей |
| transit | pass-through 0.8–1.2 и не более 8 связей |
| coordinator | 3+ разных upstream courier |
| terminal | вход есть, выход не более 10%, но `is_cutoff=false` |
| peripheral | всё остальное |

`role_score` нормирован по силе превышения порога, `priority_score` объединяет роль, оборот, отправителей и upstream-курьеров. Кластеры считаются `networkx.community.louvain_communities(..., seed=42)`. Узлы глубины 4 без исходящих получают `is_cutoff=true`; курьеры не получают pass-through, потому что их вход в выгрузке занижен.

## Ограничения

В предоставленном датасете нет отдельной колонки `is_courier`: 81 seed-клиент трактуется как известный upstream-курьер из условия кейса. Поэтому для seed входящий поток считается заниженным, а `pass_through` для них не используется. `upstream_couriers` — число уникальных seed-курьеров среди всех предков узла.

Это гипотезы по структуре переводов, не доказательство нарушения. Неполная выгрузка может превращать реального получателя в cutoff. Если parquet не содержит явного `is_courier`/`courier`, upstream-couriers будут нулевыми. Транзакции используются как источник агрегаций edges; временной latency оставлен расширением для следующей итерации.

## Что изменится при миллионе узлов

`networkx` заменяется на `igraph`, Louvain — на Leiden, а весь граф и запросы — на графовую БД или потоковые агрегации. Нельзя держать все Python-объекты в памяти; нужны columnar/partitioned parquet, предварительные индексы и асинхронные тяжёлые расчёты.

## Раскрытие стартового кода

В `starter/starter.py` сохранены загрузка parquet, sanity-check, направленный `DiGraph`, базовые степени, обороты, PageRank и pass-through. Этот pipeline расширяет его ролями, cutoff/courier-ловушками, Louvain, приоритетом, CSV и контрактным `graph.json`.
