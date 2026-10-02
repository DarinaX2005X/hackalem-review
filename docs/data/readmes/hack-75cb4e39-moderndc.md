# Money Graph / Граф денег — HackAlem

Локальное решение кейса «Граф денег» для аналитика AML-проверки и жюри HackAlem.
Оно помогает перейти от набора переводов к объяснимой структуре денежных связей:
найти приоритетные для проверки узлы, изучить их роли, соседей и сообщества,
не теряя ограничений наблюдаемой выборки.

**Priority score — приоритет дальнейшей проверки, а не вероятность или
доказательство нарушения.** Роли и гипотезы сообществ описывают наблюдаемую структуру.

## Что реализовано

- Детерминированный расчёт направленных графовых и дневных временных признаков,
  шести ролевых scores, ролей, кластеров и приоритета проверки.
- Три проверяемые CSV-выгрузки, сохраняющие все узлы, включая узлы без рёбер.
- Локальный Streamlit UI: Dashboard, Node Inspector, Cluster Inspector и Agentic Analyst.
- Направленный локальный граф и доступ к полным таблицам через раскрываемые блоки.
- Пять детерминированных действий с численным объяснением и журналом выполненных операций.
- Аналитические, agent- и UI smoke tests на предоставленных данных.

## Как работает решение

1. `starter.py` читает три parquet-файла и проверяет согласованность входов.
2. Все `gid` из `nodes.parquet` добавляются в направленный граф, затем добавляются рёбра.
3. Базовые признаки и `analytics.py` дают роли, кластеры, priority и evidence;
   результат проверяется, записывается в CSV и повторно проверяется после чтения.
4. `app.py` через `agent.py` загружает готовые CSV и `edges.parquet`.
   UI не пересчитывает PageRank, betweenness, Louvain, роли или scores.
5. Пользователь проходит путь: Dashboard → priority shortlist → точный gid →
   explanation/evidence → входящие и исходящие связи → cluster → ограничения наблюдения.

## Архитектура

| Компонент | Ответственность и взаимодействие |
|---|---|
| `starter.py` | CLI: загрузка, `sanity_check`, направленный граф, базовые признаки, вызов расчёта и validation |
| `analytics.py` | Temporal features, scoring, Louvain, hypothesis, формирование и проверка CSV |
| `out/*.csv` | Сохранённый аналитический результат; источник истины для inspection |
| `agent.py` | Проверка минимальной схемы UI-данных, чтение записей, пять actions и dispatcher |
| `app.py` | Streamlit-экраны, Plotly-граф, presentation-only previews и разбор сохранённой hypothesis |
| `test_analytics.py` | Корректность аналитики, сериализации и детерминизма |
| `test_agent.py` | Соответствие actions исходным файлам и штатные Streamlit UI smoke tests |

Обмен между расчётом и интерфейсом идёт через локальные файлы.
Отдельных backend/API, БД, внешних AI-сервисов и LLM-интеграции нет.

## Технологии

Проверенное окружение: **Python 3.14.7**. Прямые зависимости закреплены
в `requirements.txt`; версия Python указана здесь, но не устанавливается этим файлом.

| Библиотека | Версия | Назначение |
|---|---|---|
| pandas | 3.0.6 | Таблицы, агрегации, CSV |
| pyarrow | 25.0.1 | Чтение parquet |
| NumPy | 2.3.5 | Численные операции |
| NetworkX | 3.7 | DiGraph, PageRank, betweenness, Louvain |
| SciPy | 1.18.1 | Численная зависимость NetworkX PageRank |
| Streamlit | 1.64.0 | Локальный UI и AppTest |
| Plotly | 7.1.0 | Графики ролей и локальные направленные связи |

## Установка

Откройте терминал в корне репозитория с указанным Python.
Убедитесь, что три предоставленных parquet-файла находятся в `data/`.

```powershell
python -m pip install -r requirements.txt
```

Используйте обычный Python без `-O`: существующие аналитические проверки используют
`assert`. Для воспроизведения используйте проверенные версии выше.

## Запуск

### Шаг 1 — analytics

```powershell
python starter.py --data data --out out
```

Команда проверяет входы, генерирует аналитические outputs и выполняет validation
до записи и после повторного чтения CSV. Она записывает три файла в `out/`.

### Шаг 2 — UI

```powershell
python -m streamlit run app.py --server.address 127.0.0.1
```

Откройте Local URL, который напечатает Streamlit (адрес может быть подписан
`URL`; обычно это `http://127.0.0.1:8501`). Это локальный адрес.

UI определяет пути относительно `app.py` и кэширует чтение через `st.cache_data`.
Изменение размера или mtime файла обновляет кэш. При отсутствии outputs он
показывает команду analytics; при некорректных данных — понятную ошибку.
Тяжёлый расчёт автоматически при загрузке UI не запускается.

## Данные и интеграции

Источники — только предоставленные локальные parquet-файлы и рассчитанные из них
CSV. Внешние API и сервисы не используются для получения или классификации данных.

### Фактические входные данные

| Файл | Строк | Схема parquet |
|---|---:|---|
| `data/nodes.parquet` | 2248 | gid int64, depth int64, is_seed bool |
| `data/edges.parquet` | 3119 | src/dst int64, sum_kzt float64, n_tx int64, depth int8 |
| `data/transactions.parquet` | 4840 | src/dst int64, date string/object, sum_kzt float64 |

Размеры parquet: nodes 11905 байт, edges 34187 байт, transactions 40745 байт.

Пропусков, дубликатов gid, повторных пар рёбер, неизвестных концов рёбер и петель
в предоставленных данных нет. Gid лежат между 100000000011452100 и
100000008782800100: в parquet и аналитике это int64, в CSV — точная целая
запись, а в UI — строка без преобразования в float. Канонический порядок —
числовой порядок gid.

81 seed, включая 19 узлов без рёбер. Распределение depth 0..4: 81, 472, 462,
789, 444. Все 444 узла depth=4 не имеют наблюдаемого выхода.
Рёберные суммы: 5000..4400000 KZT; n_tx: 1..67. Суммы отдельных переводов:
5000..3000000 KZT. Общая сумма: 365890012.01 KZT.
`sanity_check` проверяет пары прежним outer merge и дополнительно сравнивает
суммы (rtol=1e-12, atol=1e-6 KZT) и точные количества переводов.

Период: 2026-07-01..2026-07-31, 31 уникальная дата, времени суток нет.
`active_days` — число различных дней с любым входом или выходом;
`activity_span_days` — включительный интервал между первым и последним днём.
У isolates оба значения равны 0. Диапазон active_days на этих данных: 0..29.
`out_after_prior_day_in_tx` считает исходящие операции, для которых существует
хотя бы один вход **строго на предыдущий календарный день**;
`prior_day_in_fraction` делит это число на out_tx (при отсутствии выхода — 0).
Таких исходящих операций 1002. Совпадения в тот же день не учитываются;
будущие входы не используются. Это временное соседство, не установление источника денег.

## Выгрузки и фактический результат

| Файл | Строк | Обязательные колонки |
|---|---:|---|
| `out/nodes_roles.csv` | 2248 | `gid, role, role_score, cluster_id, priority_score, evidence` |
| `out/clusters.csv` | 88 | `cluster_id, n_nodes, n_seed, sum_kzt_internal, top_gids, hypothesis` |
| `out/top_nodes.csv` | 30 | `rank, gid, role, priority_score, why` |

В `nodes_roles.csv` также сохранены базовые и временные признаки, маска
`pass_through_defined`, все шесть `score_<role>` и компоненты priority.
Каждый исходный gid встречается ровно один раз; сохранены все 19 isolates.
`role_score`, шесть scores и `priority_score` конечны и лежат в [0,1].
Evidence непустой, содержит числа и ограничен 200 символами; фактический максимум — 134.

| Роль | Узлов |
|---|---:|
| consolidator | 248 |
| transit | 13 |
| distributor | 111 |
| terminal | 247 |
| coordinator | 198 |
| peripheral | 1431 |

Эти количества — результат текущих входов, не цель настройки.
Все 444 truncated узла не классифицированы как terminal; интерпретация приведена
в разделе «Ограничения».

Источники истины UI: `nodes_roles.csv` — все узлы и Node Inspector;
`clusters.csv` — cluster summary/hypothesis; `top_nodes.csv` — готовый shortlist;
`edges.parquet` — непосредственные направленные связи.
`transactions.parquet` UI не читает: его счётчик Transactions равен сумме `edges.n_tx`.

## Интерфейс и Agentic Analyst

- **Dashboard:** фактические counts, распределение ролей, готовый shortlist и
  гипотезы кластеров. Transactions = сумма n_tx из edges.parquet; отдельные
  transactions.parquet UI не загружает. Gid из shortlist можно скопировать в Inspector.
  По умолчанию показаны первые 10 priority nodes в сохранённом порядке и 10
  кластеров по n_nodes DESC, cluster_id ASC (только UI-сортировка). Полные таблицы
  доступны в закрытых expanders «Show all priority nodes» и «Show all clusters».
- **Node Inspector:** выбор из всех nodes_roles.csv или точный gid, сохранённые
  scores/evidence, доступные диагностические колонки, ограничения и cluster hypothesis.
  Основное объяснение — строка explanation из explain_node(gid); evidence входит
  в неё без изменения и отдельно повторно не выводится. Warnings показаны отдельно.
  Gid передаётся браузеру строкой; float и scientific notation не принимаются.
  Неопределённый pass_through показан как undefined, а не как реальный нулевой ratio.
- **Neighbors / local graph:** только выбранный gid и непосредственные соседи
  из edges.parquet. Каждая линия — фактическое incident directed edge со стрелкой
  и tooltip суммы/числа переводов; встречные направления разделены кривыми.
  Navy marker выделяет выбранный узел, green — incoming, amber — outgoing.
  Геометрическое размещение не имеет аналитического смысла. Полный граф по
  умолчанию не строится, скрытые downstream edges не добавляются. Isolates имеют empty state.
  Перед графом показаны counts входящих, исходящих и всех возвращённых наблюдаемых
  связей. GRAPH_EDGE_LIMIT=30: при превышении граф показывает первые 30 рёбер
  по sum_kzt DESC, n_tx DESC, numeric src ASC, numeric dst ASC, с явным указанием
  показанного и полного количества. Таблица показывает первые 15 связей в порядке
  get_neighbors; все связи доступны в закрытом «Show all N observed relationships».
- **Cluster Inspector:** сохранённые counts, internal KZT, top_gids и hypothesis;
  members берутся только по cluster_id, сортируются по priority descending / gid ascending.
  Компактная сводка извлекает только однозначные сохранённые поля category,
  dominant_role, dominant_share, internal KZT, truncated из hypothesis; отсутствующие
  или неоднозначные значения не угадываются. Точная исходная строка всегда доступна
  в закрытом «Full stored structural hypothesis». По умолчанию показаны первые
  15 members в существующем порядке; остальные доступны в «Show all M members».
- **Agentic Analyst:** явный выбор inspect_node(gid), inspect_cluster(cluster_id),
  get_top_priority(n), get_neighbors(gid), explain_node(gid). Каждое действие
  проверяет параметр и наличие записи/допустимый диапазон, возвращает сохранённые
  данные. Dispatcher возвращает structured result и audit trace фактических операций.
  explain_node(gid) детерминированно формирует краткое presentation explanation
  из сохранённых gid, role, role_score, evidence и priority_score, с форматированием
  обоих scores до 4 знаков и пояснением смысла review priority. Seed/truncation
  limitations возвращаются отдельно, в порядке seed, затем truncation.
  Это не chatbot/LLM; natural-language intent recognition отсутствует.
  Для n разрешён только диапазон готового shortlist: новые места рейтинга не создаются.
  Сначала показывается читаемый результат выбранного действия (объяснение, компактные
  поля или таблица); warnings остаются отдельно. Полный неизменённый structured result
  доступен в закрытом «Raw structured result», audit trace остаётся видимым после результата.

Все ограничения числа строк/рёбер относятся только к presentation: аналитика,
исходные данные и результаты действий не меняются; полные данные не удаляются.

## Аналитический метод

### Граф и нормализация

Все gid добавляются до рёбер в DiGraph. Степени, объёмы, число переводов,
PageRank и betweenness направленные. PageRank использует sum_kzt как силу связи
(стандартный damping=0.85, tol=1e-12, max_iter=1000). Если не сходится —
печатается FALLBACK, возвращается равномерный вектор, его percentile равен 0.
Betweenness — точный, направленный, **без distance-weight**, вычисляется один раз.
KZT нигде не используется как расстояние. HITS не требуется.

Для неотрицательного признака P(x): нулевые значения получают 0;
положительные — `(average_rank - 0.5) / число положительных`.
Если вся колонка постоянна, всем 0: она не даёт различающего сигнала.
NaN/inf/отрицательные значения в нормализуемых признаках отвергаются.

`pass_through = out_kzt / in_kzt` определён только при in_kzt>0.
Во время inference неопределённость сохраняется с отдельной маской
`pass_through_defined`. Только после inference в CSV записывается sentinel **-1**,
который не означает реальный ratio. Для seed этот ratio не участвует в scores.

### Фиксированные формулы ролей

Обозначения: I = среднее P(in_deg), P(in_kzt), P(in_tx);
O — аналогичное среднее исходящих признаков; B=P(betweenness), R=P(pagerank);
T=prior_day_in_fraction. Si=in_deg/max(in_deg+out_deg,1), So аналогично.
Q=min(out/in,in/out) используется только для non-seed с положительным входом
и выходом; это близость наблюдаемых объёмов, не прослеживание отдельных денег.

| Роль | Score и условие |
|---|---|
| consolidator | I·(0.5+0.5·Si), если in_deg≥2; иначе 0 |
| distributor | O·(0.5+0.5·So), если out_deg≥2; иначе 0 |
| transit, non-seed | min(I,O)·(0.65+0.25·Q+0.10·T), только при наличии входа и выхода |
| transit, seed | min(I,O)·(0.90+0.10·T), только при наличии входа и выхода |
| terminal, non-seed | I·clip(1−out/in,0,1), только при in_deg>0 и отсутствии truncation |
| terminal, seed | I, только при in_deg>0, out_deg=0 и отсутствии truncation |
| coordinator | 0.70·B+0.30·R, только при входе, выходе и betweenness>0 |
| peripheral | 1−max(scores остальных пяти ролей) |

Входящий/исходящий degree даёт структурное приближение authority/hub без
добавления отдельного нестабильного спектрального алгоритма.
При `truncated_by_depth` score_terminal=0: это ограничение наблюдаемости,
а не доказательство фактического non-terminal status (см. «Ограничения»).
Seed обрабатываются отдельной формулой из-за неполного наблюдаемого входа. Для isolated node все основные scores равны 0, peripheral=1.

Scores округляются до 10 знаков, выбирается максимум. Явный порядок равенств:
consolidator, transit, distributor, terminal, coordinator, peripheral.
Все шесть scores сохранены в диагностических колонках. Коэффициенты едины
для всех узлов и не калибровались под желаемое распределение ролей.

### Кластеры и приоритет

Только для Louvain строится отдельная неориентированная проекция: веса
противоположных направлений складываются. Seed алгоритма 42, resolution=1.
Isolates получают отдельные communities. Узлы внутри community сортируются;
communities сортируются по минимальному gid, затем получают номера 0..K−1.
Все узлы/рёбра поступают в алгоритмы в каноническом порядке.

Внутренний объём кластера считается по исходным направленным рёбрам, каждое
ровно один раз. `top_gids` — JSON-массив до 5 gid по убыванию betweenness,
затем PageRank, затем возрастанию gid (метрики округлены до 10 знаков).
`hypothesis` — структурно-функциональная гипотеза о назначении community,
основанная только на уже назначенных ролях и наблюдаемых потоках.
`dominant_role` — роль с максимальным count; равенства разрешаются строго по
ROLES order: consolidator, transit, distributor, terminal, coordinator, peripheral.
`dominant_share` = dominant count / n_nodes, формат с 10 знаками после точки.
Соответствие dominant role → category:

| Роль | Category |
|---|---|
| consolidator | collection-oriented |
| transit | transit-oriented |
| distributor | distribution-oriented |
| terminal | terminal/retention-oriented |
| coordinator | coordination/bridging-oriented |
| peripheral | peripheral/isolated |

Singleton с in_deg=out_deg=0 получает category=peripheral/isolated.
При этом правиле ориентация всегда определена; mixed и дополнительные пороги
не используются. Строка также содержит counts всех шести ролей (включая нулевые)
в ROLES order, internal KZT с 2 знаками после точки и truncated count.
Фиксированные форматирование и tie-break обеспечивают независимость от порядка
строк. Окончание `structural hypothesis only` подчёркивает, что это гипотеза,
а не вывод о преступной деятельности или доказанной незаконности community.

V=P(in_kzt+out_kzt), F=P(in_tx+out_tx).
`priority = 0.35·B + 0.15·R + 0.25·V + 0.15·F + 0.10·T·F`.
Интерпретация: посредничество и положение в потоке, наблюдаемый объём,
частота и временное соседство с поправкой на частоту.
Назначенные role/role_score не входят в формулу; для isolates priority=0.
Большие объёмы и высокая частота учитываются отдельно. Это эвристика; её значения не калиброваны как вероятности. Ограничения выборки
сохраняются: seed-вход неполон, depth=4 обрезан.

Top N=30, порядок: округлённый priority убывает, gid возрастает.
`why` содержит численные компоненты формулы. `evidence` содержит степени,
объёмы, числа переводов, сигнал выбранной роли и признаки seed/truncation.

## Проверка решения

Выполните из корня репозитория по порядку:

```powershell
python starter.py --data data --out out
python -m unittest -v test_analytics
python -m unittest -v test_agent.AgentTests
python -m unittest -v test_agent.UISmokeTests
```

| Команда | Что проверяет | Результат текущего CHECK |
|---|---|---|
| `python starter.py --data data --out out` | Согласованность входов, полный расчёт, validation до/после записи | Выполнена успешно |
| `python -m unittest -v test_analytics` | Граф, scores, ограничения наблюдения, hypothesis, сериализация, детерминизм | Analytics tests: 9/9 |
| `python -m unittest -v test_agent.AgentTests` | Фактические actions против CSV/parquet, объяснения, warnings, неверные входы | Agent tests: 12/12 |
| `python -m unittest -v test_agent.UISmokeTests` | Экраны, previews/полные данные, warnings, ошибки и directed graph | UI smoke tests: 7/7 |

### Сценарий для жюри

1. Запустите UI и откройте Dashboard: сверяйте 2248 nodes, 3119 edges,
   4840 transactions, 88 clusters, 81 seed и 444 truncated nodes.
2. Раскройте полный shortlist и скопируйте `100000003684369100` в Node Inspector.
   Сопоставьте role/priority с CSV, прочитайте explanation и warnings.
3. Для этого узла наблюдаются 86 relationships: граф показывает 30,
   таблица — первые 15, полный список доступен ниже в expander.
   Наведите курсор на стрелку и узел для численных tooltips.
4. Выберите cluster_id=2 в Cluster Inspector, прочитайте компактную сводку
   и точную исходную hypothesis, раскройте полный список members.
5. В Agentic Analyst выполните `explain_node` с этим gid.
   Сравните explanation с Inspector, раскройте Raw structured result,
   проверьте видимый Audit trace. Для shortlist выполните `get_top_priority` с n=10.

### Покрытие проверок

До записи и после чтения CSV проверяются universe gid, обязательные значения,
численная безопасность всех диагностик, шесть scores и argmax, длина и числа
в evidence, полнота кластеров, n_nodes/n_seed, независимый пересчёт внутренних
сумм, состав top_gids, последовательные ranks, сортировка и совпадение top scores.
Отдельно проверяются orphan nodes, запрет terminal при truncation и маска ratio.

9 тестов проверяют также направленные агрегаты против parquet, weight=None
для betweenness, временной сигнал независимым подсчётом и примером с прошлым/
тем же/следующим днём, неизменность всех role scores при изменении ratio seed
и undefined, PageRank fallback, ошибочные суммы/числа переводов и повторяемость.
Тест hypothesis проверяет категории доминирующих ролей, singleton isolate,
все попарные равенства максимумов, долю, численные evidence и неизменность строки
при повторном вызове и перестановке узлов кластера. Validation проверяет hypothesis
каждого кластера до записи и после чтения CSV.

Agent tests проверяют valid/invalid gid и cluster, точные значения actions,
seed/truncation warnings (включая оба флага), isolates, повторяемость dispatcher,
необязательные поля и missing/malformed data.

Smoke использует штатный [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest):
Dashboard, Node/Cluster Inspector, все пять actions, видимое explanation без
дублирования evidence, audit trace и полный JSON. Проверяются previews, порядок
и доступность всех строк, безопасный разбор hypothesis, high-degree graph,
isolates, invalid inputs и состояния missing/malformed data.
Стрелки и tooltips проверяются в Plotly figure; пиксельное browser testing не заявляется.
Направление в визуализации задают [Plotly annotations](https://plotly.com/python/reference/layout/annotations/).

## Воспроизводимость

- Канонический числовой порядок int64 gid; узлы добавляются до рёбер, рёбра
  сортируются по src/dst. В браузер gid передаются строками без float conversion.
- Louvain использует fixed seed=42; cluster ids канонически перенумеровываются.
- Равенства role scores и dominant counts разрешаются фиксированным ROLES order.
  У top priority и структурных лидеров есть явный secondary key gid.
- CSV: порядок узлов по gid, кластеров по cluster_id, top — по priority DESC / gid ASC;
  `float_format="%.10f"`, разделитель строк LF. Внутри текстовой hypothesis
  share имеет 10 знаков, internal KZT — 2; UI explanation форматирует scores до 4 знаков.
- Тест выполняет повторный расчёт с перестановкой строк всех трёх входов,
  проверяет точное равенство таблиц и SHA-256 сериализованных CSV.
  При текущем CHECK повторный запуск analytics также сохранил SHA-256 файлов `out/`.
- Прямые зависимости закреплены в `requirements.txt`; проверенное окружение
  приведено в разделе «Технологии».

Детерминизм гарантируется для одинаковых входов, параметров и проверенного
окружения. Byte-identical результат между произвольными версиями NetworkX,
NumPy, SciPy или реализациями Louvain не обещается.

## Ограничения

- **Seed:** наблюдаемый входящий поток может быть неполным из-за расширения
  выборки наружу от seed. Для них pass_through не используется в role scoring.
- **Depth=4:** сбор данных заканчивается на четвёртом колене. Все 444 узла этого
  уровня имеют out_deg=0, но это не доказывает retention. Classifier не использует
  отсутствие выхода как terminal evidence и консервативно задаёт score_terminal=0.
  Их terminal/non-terminal status по этому отсутствию неидентифицируем:
  они не объявляются доказанно non-terminal, реальный downstream неизвестен.
- **Время:** timestamps имеют только дневную точность, intraday-порядок неизвестен.
  Вход на предыдущий день — temporal proximity, не доказательство источника
  финансирования исходящего перевода. Будущие входы не используются.
- **Интерпретация:** роли описывают наблюдаемую структуру; cluster hypotheses —
  структурные гипотезы. Priority — эвристический review priority, а не
  вероятность или доказательство нарушения.
- **Интерфейс:** приложение локальное, публичного deployment нет.
  Agentic Analyst не использует LLM, natural-language intent recognition отсутствует:
  пользователь выбирает действие и передаёт точный параметр.
- **Presentation limits:** по умолчанию видны subsets таблиц и до 30 рёбер графа.
  Это не удаляет исходные данные и не меняет аналитику; полные таблицы доступны
  через expanders. За обрезанную глубину синтетические связи не достраиваются.

## Deployment

Публичная deployed-версия отсутствует.
Приложение запускается локально через Streamlit.

В текущем репозитории нет публичного URL приложения или конфигурации deployment.
