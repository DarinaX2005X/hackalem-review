# Cifron AI

Cifron AI — локальный AML-инструмент, который читает три обезличенных Parquet-файла, строит транзакционный граф, считает объяснимые метрики, назначает роли, выделяет кластеры и формирует ранжированный список узлов для ручной проверки. Next.js UI показывает граф и demo-сценарий; AI-анализ выбранного узла является дополнительным, а не базовым расчётным слоем.

## Архитектура

```text
edges.parquet + nodes.parquet + transactions.parquet
  -> validation -> graph metrics -> roles and scores
  -> clusters -> nodes_roles.csv / clusters.csv / top_nodes.csv
  -> Next.js UI -> optional OpenAI node analysis
```

Базовый pipeline выполняется локально, без внешних API, GPU и облачных сервисов. OpenAI используется только для дополнительного текстового объяснения выбранного узла и не меняет базовые роли или scores.

## Быстрый запуск UI

```bash
npm install
npm run dev
```

Откройте <http://localhost:3000>. Можно загрузить UTF-8 CSV с колонками `transaction_id,timestamp,sender,receiver,amount`; demo-кнопка использует небольшой демонстрационный набор и не является полным датасетом ТЗ. Для выбранного узла доступны поиск по `gid`, граф, глубина цепочки, focus-режим и AI-анализ с локальным fallback.

## Pipeline

Установите Python-зависимости в виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r pipeline/requirements.txt
```

Положите в `data/` файлы `edges.parquet`, `nodes.parquet`, `transactions.parquet`, затем запустите одной командой:

```bash
npm run pipeline
```

Команда эквивалентна:

```bash
python -m pipeline.run --data-dir data --output-dir outputs
```

Pipeline валидирует файлы и обязательные колонки, приводит `gid` к `int64`, суммы к числам и `is_seed` к bool. Он обрабатывает все строки `nodes.parquet`, включая узлы без рёбер, и не ограничивает вход 1000 строками. При ошибке до записи проверяются все входы; outputs не заменяются частичным результатом.

Входные схемы:

- `edges.parquet`: `src`, `dst`, `sum_kzt`, `n_tx`, `depth`;
- `nodes.parquet`: `gid`, `depth`, `is_seed`;
- `transactions.parquet`: `src`, `dst`, `date`, `sum_kzt`.

## Схемы outputs

`outputs/nodes_roles.csv` содержит одну строку на каждый `gid` из `nodes.parquet` и ровно колонки:

```text
gid,role,role_score,cluster_id,priority_score,evidence
```

`role_score` и `priority_score` находятся в диапазоне `[0,1]`, `evidence` непустой и не длиннее 200 символов.

`outputs/clusters.csv` имеет ровно колонки:

```text
cluster_id,n_nodes,n_seed,sum_kzt_internal,top_gids,hypothesis
```

`top_gids` содержит до пяти узлов кластера по priority score, `hypothesis` — осторожное русскоязычное объяснение без утверждения о нарушении.

`outputs/top_nodes.csv` имеет ровно колонки:

```text
rank,gid,role,priority_score,why
```

Список сортируется по `priority_score` по убыванию, затем по `gid` по возрастанию, и содержит `min(20, n_nodes)` строк.

## Роли и scores

Используются machine-readable роли `consolidator`, `transit`, `distributor`, `terminal`, `coordinator`, `peripheral`.

Pipeline считает `in_degree`, `out_degree`, уникальных входящих и исходящих соседей, наблюдаемые входящие и исходящие объёмы, число транзакций, `depth`, `is_seed`, degree centrality как proxy центральности и `pass_through_ratio`. Последний считается только для не-seed с положительным наблюдаемым входящим объёмом.

Пороги рассчитываются по распределению текущего датасета: высокий исходящий degree — 75-й percentile, высокий входящий degree и число уникальных отправителей — 85-й percentile, высокий входящий объём для консолидации — 75-й percentile, высокая centrality — 90-й percentile, высокий priority — 90-й percentile. Порядок правил такой:

1. `coordinator`: centrality и priority не ниже 90-го percentile плюс минимум две связи с seed или минимум два seed в кластере.
2. `distributor`: исходящий degree и число уникальных получателей не ниже 75-го percentile, исходящий degree больше входящего.
3. `consolidator`: входящий degree и число уникальных отправителей не ниже 85-го percentile, входящий observed volume не ниже 75-го percentile.
4. `transit`: не-seed, есть входящие и исходящие, `pass_through_ratio` от 0.8 до 1.2.
5. `terminal`: не-seed, `out_degree == 0` и `depth < 4`.
6. `peripheral`: остальные узлы.

Узел `depth=4` без исходящих не считается terminal автоматически: в evidence указывается граница наблюдаемого графа. Для seed observed ratio не трактуется как полный баланс клиента. `priority_score` — нормализованная комбинация degree centrality, observed volume и связи с seed.

## Ограничения данных

- В выгрузке видны только исходящие переводы от стартовых seed-клиентов.
- Обход ограничен четырьмя коленами.
- Переводы ниже 5000 KZT не видны.
- `depth=4` без исходящих означает границу наблюдения, а не доказанный terminal.
- У seed неполные наблюдаемые входящие, поэтому полный баланс по ним недоступен.
- Размеченных ролей ground truth нет; результаты являются объяснимыми гипотезами для ручной проверки.
- Атрибутов клиентов, ФИО, ИИН, возраста, дохода и внешнего обогащения нет.
- На предоставленном объёме ожидается полный пересчёт менее чем за 5 минут на обычном ноутбуке.

## Масштабирование

При росте до примерно 1 млн узлов потребуется перейти на `igraph`/`graph-tool` или Spark, использовать разреженные структуры, запускать community detection по компонентам, обрабатывать данные batch/partition-способом и хранить их в Parquet или другом columnar storage. UI-агрегации следует обслуживать асинхронно через очередь. Это план масштабирования, а не утверждение, что он уже реализован в MVP.

## AI-слой

AI — опциональный ассистент аналитика. Он не рассчитывает базовые роли, кластеры и scores, получает только обезличенный профиль выбранного узла и формулирует гипотезы для ручной проверки. При отсутствии API или ошибке используется локальный fallback.

## Проверка результатов

```bash
head -n 3 outputs/nodes_roles.csv
head -n 3 outputs/clusters.csv
head -n 3 outputs/top_nodes.csv
wc -l outputs/nodes_roles.csv
```

Количество строк данных в `nodes_roles.csv` должно совпадать с количеством строк в `nodes.parquet`.

Документы: [схема решения](docs/solution-architecture.md) и [demo-сценарий](docs/demo-script.md).

## Проверки проекта

```bash
npm run lint
npx tsc --noEmit
npm run build
```

Cifron AI — вспомогательный аналитический инструмент. Результаты не подтверждают факт нарушения и требуют проверки AML-специалистом.
