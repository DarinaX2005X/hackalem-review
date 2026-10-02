# AML Graph — восстановление финансовой структуры сети

Локальный explainable-пайплайн по ТЗ HackAlem AI. Из `nodes/edges/transactions` строит направленный граф, рассчитывает структурные, денежные и временные признаки, Louvain-кластеры, 6 ролей и priority score.

## Роли
`consolidator`, `transit`, `distributor`, `terminal`, `coordinator`, `peripheral`.

Важно: `depth=4 && out_degree=0` не считается достаточным основанием для `terminal`, поскольку это граница 4-hop выгрузки. Все формулировки — гипотезы для AML-проверки, не утверждения о виновности.

## Быстрый запуск
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python pipeline.py
streamlit run app.py
```

Pipeline автоматически предпочитает Parquet, если он есть; иначе читает CSV.

## Выход
- `outputs/nodes_roles.csv`: gid, role, role_score, cluster_id, priority_score, evidence
- `outputs/clusters.csv`: cluster_id, n_nodes, n_seed, sum_kzt_internal, top_gids, hypothesis
- `outputs/top_nodes.csv`: rank, gid, role, priority_score, why
- `outputs/node_features.csv`: диагностические признаки для UI/аудита

## Priority score
`0.24 seed_coverage + 0.23 betweenness + 0.17 degree + 0.12 volume + 0.09 PageRank + 0.08 cluster_bridge + 0.07 role_score`, после percentile-нормализации. Известным seed применяется множитель 0.55: задача TOP-листа — искать следующие узлы для проверки, а не повторять исходные 81.

## Explainability
Роль выбирается из шести интерпретируемых role-score. В `evidence` сохраняются наблюдаемые признаки (fan-in/fan-out, поток, seed coverage, betweenness, межкластерные связи). Весовые коэффициенты priority вынесены в `config.json`.

## Ограничения
Граф содержит только исходящие переводы от seed на 4 колена, поэтому observed IN/OUT не является полным балансом клиента. Seed имеют неполный входящий поток; depth=4 обрезан; операции ниже порога исходной выгрузки невидимы.

## Масштабирование до ~1 млн узлов
NetworkX заменить на igraph/Graph-tool/Spark GraphFrames или специализированный graph engine; centrality считать приближённо; seed coverage — батчевым multi-source traversal; признаки хранить в Parquet/аналитической БД. UI должен получать ego-subgraph через API, а не загружать весь граф в браузер.
