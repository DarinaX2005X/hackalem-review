# WindAgent — прогноз выработки ВЭС «Нурлы» · Localhosters, HackAlem AI

Агент каждый день в 18:00 UTC выпускает почасовой прогноз мощности двух турбин на 48 часов в виде P10 / P50 / P90. Когда выходит новый ран погоды, агент пересчитывает прогноз и объясняет, что изменилось. Каждый шаг выпуска пишется в трейс, поэтому любой выпуск можно разобрать постфактум.

В репозитории — replay февраля 2026: 29 выпусков и 29 пересчётов. Каждый использует только те прогнозы погоды, которые были опубликованы к моменту выпуска.

| Что нужно | Команда |
|---|---|
| "поставить зависимости" | `make setup` |
| "проверить, что всё работает" | `make verify` |
| "собрать сабмит февраля 2026" | `make backtest` |
| "посчитать метрики на январе 2026" | `make backtest-dev` |
| "посчитать метрики на феврале 2025" | `make backtest-feb2025` |
| "запустить один выпуск агентом" | `uv run --frozen python -m windagent issue --at 2026-02-10T18:00Z --model-adapter windagent.model.v1:predict_power` |
| "прогнать февраль с решениями LLM" | `make llm-replay` |
| "открыть дашборд локально" | `make dashboard` |
| "проверить в Docker" | `make docker-verify` |
| "запустить юнит-тесты" | `make test` |
| "переобучить LightGBM v1" | `make train` |

**Основной сабмит:** [`submission/forecast_test_hourly_v1.csv`](submission/forecast_test_hourly_v1.csv) — 672 часа × 2 турбины = 1 344 строки.
**Дашборд:** https://windagent-localhosters.pages.dev — логин `localhosters`, пароль `wind-c02371-be3da7`.

---

## Описание решения и назначение

Задача кейса: почасовой прогноз выработки двух турбин на 24–48 часов. Весь цикл выполняет агент: погода → подготовка данных → модель → прогноз → анализ → пересчёт при обновлении входных данных. [Условие кейса](task%20context/HackAlemAIAgenticAI.html).

| Вопрос | Ответ |
|---|---|
| Что прогнозируем | нормализованную мощность 0–1 (доля от 2.5 МВт) каждой турбины и МВт по станции, по часам |
| Когда выпуск | 18:00 UTC накануне = 00:00 дня D по часам SCADA (UTC+6); горизонт 48 ч |
| Когда пересчёт | когда появляется новый ран погоды: в 20:00 UTC становится доступен ECMWF 12Z |
| Откуда погода | Open-Meteo Single Runs, ECMWF IFS 9 км — архив прогнозов в том виде, в каком они вышли |
| Что получает диспетчер | P10 / P50 / P90 на 48 ч, решение publish / reissue с причиной, `report.md` на русском |
| Как проверить отсутствие утечки | у каждой строки есть `nwp_run_init_utc`; ран, опубликованный позже момента выпуска, отклоняется |

Кому полезно: диспетчеру ВЭС для заявки на сутки вперёд и для решения, нужно ли обновлять заявку, когда пришла свежая погода.

---

## Архитектура

```text
┌─ офлайн: make train ─────────────────────────┐
│ SCADA 2 турбин: 10 мин → 1 ч, UTC+6          │
│ + архив прогнозов ECMWF IFS и Previous Runs  │
│ v0: MOS ветра + логистическая кривая         │
│ v1: LightGBM, p50 = 0.4·LightGBM + 0.6·v0    │
└───────────────────────┬──────────────────────┘
                        │ models/
                        ▼
┌─ каждый выпуск: run_issue(at) ───────────────┐
│ Clock: какой ран уже опубликован к at        │ ◄── Open-Meteo Single Runs
│ Проверка: 48 ч погоды без пропусков          │     ECMWF IFS 9 км, as-issued
│ Модель: P10 / P50 / P90, 48 ч × 2 турбины    │     data/nwp_cache/single_runs/
│ Сравнение с прошлым выпуском                 │
│ Планировщик: правила или OpenAI              │
│   → publish / reissue + объяснение           │
└───────────────────────┬──────────────────────┘
                        │ trace.jsonl · decision.json · report.md
                        ▼
       submission/forecast_test_*_v1.csv  ──►  дашборд
```

Модель считает мощность, LLM её не считает. Агент выбирает ран погоды по правилу as-of, проверяет входные данные, вызывает модель, сравнивает результат с прошлым выпуском и решает, публиковать ли выпуск и нужен ли пересчёт.

| Шаг `run_issue` | Что делает | Где видно |
|---|---|---|
| `read_memory` | берёт прошлый выпуск для сравнения, только из прошлого | `trace.jsonl` |
| `get_clock` | фиксирует момент выпуска и задержки публикации ранов | `trace.jsonl` |
| `fetch_nwp_forecast` | берёт самый свежий ран, доступный к моменту выпуска | `inputs.json` |
| `fetch_scada_history` | фиксирует границу as-of для SCADA | `trace.jsonl` |
| `check_data_quality` | проверяет 48 ч погоды без пропусков | `dq_report.json` |
| `prepare_features` | вырезает окно горизонта из рана | `inputs.json` |
| `predict_power` | вызывает модель через общий контракт адаптера → P10 / P50 / P90 | `forecast.csv` |
| `compare_with_previous` + планировщик | новый ран? сдвиг ветра? → publish / reissue / reject + объяснение | `comparison.json`, `decision.json` |
| `save_forecast` | сохраняет прогноз, если решено публиковать | `forecast.csv` |
| `write_report` | пишет отчёт для диспетчера | `report.md` |
| `write_memory` | сохраняет заметку для следующего выпуска | `memory.json` |

**Правило as-of.** Ран ECMWF IFS доступен через 8 / 7 / 8 / 7 ч после старта циклов 00Z / 06Z / 12Z / 18Z (`windagent/clock.py`). В 18:00 UTC последний доступный ран — 06Z; 12Z становится доступен в 20:00 UTC, и агент делает пересчёт. Historical Forecast и ERA5 используются только для обучения: это не прогнозы в том виде, в каком они вышли.

**Два режима планировщика.** Режим `scripted` — детерминированные правила без сети и ключа, на нём построен сабмит. Режим `openai` — Pydantic AI + `gpt-5.4-mini` принимает то же решение и пишет объяснение. Код проверяет ответ LLM: ссылка на другой ран, коррекция, которой не было, или противоречие проверке качества → выпуск принимается по правилам, причина пишется в `fallback_reason`. На всём феврале LLM совпал с правилами в 58 решениях из 58, 0 откатов, $0.098 за месяц — [отчёт](reports/llm_replay_test.md).

**Модели.** v0 — линейный MOS ветра на 100 м и эмпирическая логистическая кривая мощности. v1 — LightGBM на признаках Single Runs и Previous Runs, P50 = 0.4 · LightGBM + 0.6 · v0. P10 / P90 — эмпирические квантили остатков v0 по корзинам мощности. На окнах с фактами (январь 2026, февраль 2025) работает holdout-модель `models/lightgbm_v1_holdout.txt`, которая этих месяцев не видела; для февраля 2026 — финальная `models/lightgbm_v1.txt`.

Подробнее: [архитектура и ADR](docs/architecture.md), [правило as-of](docs/research/as-of-convention.md), [допущения](docs/assumptions.md), [LightGBM v1](docs/research/lightgbm-v1.md).

---

## Используемые технологии

| Слой | Технология | Зачем |
|---|---|---|
| Окружение | Python 3.12, uv, `uv.lock` | одна команда ставит зафиксированные версии |
| Данные | pandas, pyarrow (Parquet) | SCADA 10 мин → 1 ч, архив прогнозов |
| Погода | Open-Meteo Single Runs и Previous Runs (ECMWF IFS), requests + requests-cache | прогнозы с `run_init_utc`, офлайн-кеш в репозитории |
| Модель | LightGBM 4.7, линейный MOS + логистическая кривая (v0) | P10 / P50 / P90 на 48 ч |
| Агент | собственный runtime `run_issue`, контракты на Pydantic | 11 шагов, трейс, память, решения |
| LLM | Pydantic AI + OpenAI `gpt-5.4-mini` | решение publish / reissue и объяснение для диспетчера |
| Дашборд | Vite 7, React 19, Cloudflare Pages + Basic Auth | прогноз, пересчёт и трейс каждого выпуска |
| Упаковка и проверки | Make, Docker, pytest | воспроизводимый запуск и проверка |

---

## Необходимые зависимости

| Что | Версия | Зачем | Установка (macOS) |
|---|---|---|---|
| git, make | любые | клонирование и команды | `xcode-select --install` |
| uv | ≥ 0.6 | ставит Python 3.12 и пакеты из `uv.lock` | `brew install uv` |
| libomp | любая | OpenMP для LightGBM | `brew install libomp` |
| Node.js | 20.19+ или 22.12+ | только дашборд | `brew install node` |
| Docker | любой | только проверка в контейнере | Docker Desktop |
| `OPENAI_API_KEY` | — | только режим LLM | [platform.openai.com](https://platform.openai.com/api-keys) |

**CRITICAL (macOS): без `brew install libomp` `make verify` проходит первую половину и падает на второй с `Library not loaded: @rpath/libomp.dylib`.** v0 работает без libomp, а LightGBM v1 — нет. На Debian/Ubuntu нужна библиотека `libgomp1` (`sudo apt-get install libgomp1`); в Docker-образе она уже стоит.

Python-пакеты и их версии зафиксированы в [`pyproject.toml`](pyproject.toml) и [`uv.lock`](uv.lock): requests, requests-cache, pandas, pyarrow, pydantic, pydantic-ai-slim[openai], python-dotenv, PyYAML, lightgbm; для тестов — pytest, responses, ruff. Версия Python задана в `.python-version`: uv сам скачает 3.12, даже если в системе стоит другая.

Сеть нужна только для установки пакетов. Прогнозы погоды, SCADA и обученные модели лежат в репозитории (`data/` — 24 МБ, `models/`), поэтому бэктест и проверки идут офлайн.

---

## Установка

```bash
git clone https://github.com/BAITC-Hacks/hack-75766fed-localhosters.git
cd hack-75766fed-localhosters
brew install uv libomp          # macOS; на Linux: uv + libgomp1
make setup                      # uv sync --frozen: Python 3.12 + пакеты из uv.lock
cp .env.example .env            # по желанию: ключ OpenAI для режима LLM
```

Через Docker (Python, uv и libgomp внутри образа):

```bash
docker build -t windagent .     # образ с кодом, архивом погоды и моделями
docker run --rm windagent       # запускает ту же проверку, что make verify
```

---

## Параметры окружения

Шаблон — [`.env.example`](.env.example). Все переменные необязательны: без `.env` работают значения по умолчанию. `.env` читают `python -m windagent` и `make llm-replay`; `make verify` от него не зависит.

| Переменная | По умолчанию | Что задаёт |
|---|---|---|
| `OPENAI_API_KEY` | пусто | ключ для `--llm openai` и `make llm-replay`; режиму `scripted` не нужен |
| `OPENAI_MODEL` | `gpt-5.4-mini` | модель планировщика в режиме `openai` |
| `LLM_MODE` | `scripted` | планировщик по умолчанию для `windagent issue` |
| `WINDAGENT_MODEL` | `v1` | модель сабмита для `make backtest` и `make verify` (`v0` — эталон) |
| `OPEN_METEO_CACHE_ONLY` | `1` | `1` — только закоммиченный кеш погоды, без запросов в сеть |
| `ISSUE_HOUR_UTC` | `18` | час выпуска, UTC |
| `HORIZON_HOURS` | `48` | горизонт прогноза, ч |
| `SCADA_TZ_OFFSET_HOURS` | `6` | часовой пояс SCADA (фиксированный UTC+6) |
| `REISSUE_ON_NEW_RUN` | `1` | `1` — пересчёт на каждом новом ране; `0` — только при сдвиге ветра больше порога |
| `DIVERGENCE_THRESHOLD_MS` | `1.5` | порог среднего сдвига ветра на 100 м между ранами, м/с |
| `POINT_ESTIMATE` | `median` | точечный прогноз = P50 |
| `AVAIL_LAG_HOURS` | `7` | задержка публикации для будущих не-ECMWF источников; для ECMWF задержки по циклам заданы в `windagent/clock.py` |
| `RESIDUAL_Z_THRESHOLD`, `RESIDUAL_WINDOW_HOURS`, `DRIFT_WINDOW_DAYS` | `2.5`, `6`, `14` | пороги триггеров по фактам; пока не исполняются (см. «Ограничения») |

---

## Запуск

Сабмит февраля 2026 — 29 выпусков и 29 пересчётов через агента, ~5 секунд:

```bash
make backtest                   # = make backtest-v1: сабмит на LightGBM v1
make backtest-v0                # эталон v0 → submission/*_v0.csv, runs/backtest/v0/test/
```

| Файл | Строк | Что внутри |
|---|---:|---|
| [`submission/forecast_test_hourly_v1.csv`](submission/forecast_test_hourly_v1.csv) | 1 344 | основной сабмит: час × турбина, `p50/p10/p90`, `power_mw`; `p50` из выпуска накануне, `p50_h25_48` — из выпуска за двое суток |
| [`submission/forecast_test_dayahead_v1.csv`](submission/forecast_test_dayahead_v1.csv) | 2 784 | 29 выпусков × 48 ч × 2 турбины, с `nwp_run_init_utc` и `lead_h` |
| [`submission/forecast_test_intraday_v1.csv`](submission/forecast_test_intraday_v1.csv) | 2 784 | пересчёты в 20:00 UTC на ране 12Z, та же схема |
| [`submission/forecast_test_hourly_plant_v1.csv`](submission/forecast_test_hourly_plant_v1.csv) | 672 | станция целиком, МВт и МВт·ч по часам |
| [`runs/backtest/v1/test/`](runs/backtest/v1/test) | 58 папок | по папке на выпуск: `trace.jsonl`, `decision.json`, `comparison.json`, `report.md`, `forecast.csv` |

Один выпуск агентом и пересчёт после выхода рана 12Z:

```bash
uv run --frozen python -m windagent issue --at 2026-02-10T18:00Z --model-adapter windagent.model.v1:predict_power               # day-ahead на ране 06Z
uv run --frozen python -m windagent issue --at 2026-02-10T20:00Z --model-adapter windagent.model.v1:predict_power               # пересчёт на ране 12Z
uv run --frozen python -m windagent issue --at 2026-02-10T18:00Z --model-adapter windagent.model.v1:predict_power --llm openai  # решение принимает LLM
```

Каждый запуск создаёт папку `runs/<время>-<id>/` с `forecast.csv`, `inputs.json`, `dq_report.json`, `comparison.json`, `decision.json`, `trace.jsonl`, `report.md`, `memory.json`, `status.json`.

**Частые ошибки (команда падает или считает не то):**

| WRONG | RIGHT |
|---|---|
| `python -m windagent issue --at 2026-02-10T18:00Z` → `MODEL_NOT_FOUND` | добавить `--model-adapter windagent.model.v1:predict_power` |
| `uv run pytest` при `OPEN_METEO_CACHE_ONLY=1` в окружении → 5 тестов погоды падают | `make test` (снимает флаг сам) |
| `python -m windagent ...` системным Python | `uv run --frozen python -m windagent ...` |

Метрики на окнах с фактами, LLM и дашборд:

```bash
make backtest-dev               # январь 2026 → reports/backtest_{v1,v0}_dev*.csv
make backtest-feb2025           # февраль 2025, тот же сезон → reports/backtest_{v1,v0}_feb2025*.csv
make llm-replay                 # февраль 2026 с решениями OpenAI: ~2.5 мин, ~$0.1, нужен OPENAI_API_KEY
make dashboard                  # экспорт данных + http://127.0.0.1:5173 (нужен Node.js)
make train                      # переобучить LightGBM v1 → models/lightgbm_v1*.txt
```

Развёрнутый дашборд: https://windagent-localhosters.pages.dev — логин `localhosters`, пароль `wind-c02371-be3da7`. Сайт закрыт паролем, потому что в нём SCADA организаторов. На дашборде все 60 выпусков (январь с фактами и февраль), P10–P90, пересчёт 18:00 → 20:00 UTC, трейс агента по шагам и решения LLM рядом с правилами. [Сценарий демо](docs/demo-storyboard.md).

---

## Проверка основного сценария

```bash
make verify                     # ~6 секунд, без сети и ключей
```

Ожидаемый вывод заканчивается двумя строками `PASS`:

```text
PASS: 11 steps, 96 rows, 06Z→12Z revision, no future memory, rejected late/missing/demo inputs, TestModel
PASS: v1 — 29 issues via agent + 29 reissues (11-step traces); v0 and v1 agent == direct model; 2784 rows, 1344 hourly rows, all as-of, 19Z rejects 12Z, real 06Z→12Z revision
```

| Что проверяется | Как |
|---|---|
| Агент проходит все 11 шагов | трейс каждого из 58 выпусков содержит 11 строк |
| Пересчёт работает | 29 папок `*-reissue` на ране 12Z с `reissue_recommended=true` |
| Сабмит собран агентом, а не в обход | прогноз через `run_issue` совпадает с прямым расчётом модели, v0 и v1 |
| Нет утечки будущего | каждая из 2 784 строк проходит `assert_as_of`; в 19:00 UTC ран 12Z отклоняется |
| Плохие входы отклоняются | поздний ран, пропущенный час, демо-данные в боевом режиме → ошибка |
| Контракт LLM | ответ проверяется схемой `IssueDecision` (Pydantic AI `TestModel`, без сети) |
| Объём сабмита | 2 784 строки по выпускам, 1 344 почасовых |

Проверка перезаписывает `submission/` и `runs/backtest/` теми же байтами: после неё `git status` чистый. Если он не чистый — результат не воспроизвёлся.

Дополнительно:

```bash
make test                       # 69 юнит-тестов, ~9 секунд, включая tests/test_clock_no_leakage.py
make docker-verify              # docker build + та же проверка в контейнере
```

Проверка вручную на одном дне:

1. Откройте `runs/backtest/v1/test/2026-02-10T1800Z-dayahead/decision.json` → `"reason": "initial_issue"`, ран `2026-02-10T06:00:00Z`.
2. Откройте `runs/backtest/v1/test/2026-02-10T2000Z-reissue/decision.json` → `"reason": "new_nwp_run"`, ран `2026-02-10T12:00:00Z`, `"reissue_recommended": true`.
3. В `trace.jsonl` той же папки 11 строк, по одной на шаг; в `comparison.json` — насколько сдвинулся прогноз.

---

## Результаты

Фактов февраля 2026 в данных нет, поэтому качество измеряем тем же путём через агента на двух окнах с фактами, holdout-моделью:

| Окно | Модель | MAE T1 | MAE T2 | Медиана 7 сут. (T1 / T2) | Покрытие P10–P90 |
|---|---|---:|---:|---:|---:|
| январь 2026 | **v1** | **0.171** | **0.175** | 0.294 / 0.288 | 0.80 |
| январь 2026 | v0 | 0.174 | 0.177 | | 0.80 |
| февраль 2025 (тот же сезон) | **v1** | **0.165** | **0.188** | 0.339 / 0.304 | 0.80 |
| февраль 2025 (тот же сезон) | v0 | 0.172 | 0.192 | | 0.79 |

MAE — по нормализованной мощности на всём горизонте 48 ч. Бейзлайн Previous Runs → кривая мощности даёт 0.20–0.22; цель ≤ 0.19 выполнена на обоих окнах. Блоки h1–24 / h25–48, режим без часов простоя и ограничений, skill: [отчёт v1](docs/research/backtest-v1.md), [отчёт v0](docs/research/backtest-v0.md), [бейзлайны](docs/research/baselines.md). Статус доказательств по критериям жюри — [rubric-map](docs/research/rubric-map.md).

---

## Ограничения

- Качество на феврале 2026 неизвестно: фактов нет. Оценка — январь 2026 и февраль 2025.
- В момент выпуска модель не получает SCADA: шаг `fetch_scada_history` фиксирует только границу as-of. Прогноз строится по погоде; SCADA используется для обучения и оценки.
- P10 / P90 — эмпирические квантили остатков v0, а не квантильная модель.
- Пересчёты есть только в тестовом окне: в архиве января 2026 и февраля 2025 лежат только раны 06Z.
- Триггеры по остаткам и дрейфу (`RESIDUAL_*`, `DRIFT_*`) описаны, но не исполняются: им нужны факты в реальном времени.
- Задержки публикации ранов ECMWF (8 / 7 / 8 / 7 ч) — наша консервативная оценка, не официальная цифра Open-Meteo.
- В выпуске один источник погоды — ECMWF IFS; другие модели Previous Runs входят только в признаки v1.
- Дашборд — статический экспорт готовых выпусков, не live-сервис.

---

## Структура репозитория

```text
windagent/            агент: clock.py (as-of), agent/{runtime,planner,scripted,trace}.py,
                      model/{v0,v1,serve,schema}.py, backtest.py
scripts/              verify, verify_backtest, llm_replay, export_dashboard, flatten_submission
data/                 архив прогнозов ECMWF, Previous Runs, почасовая SCADA (24 МБ)
models/               v0_params.json, lightgbm_v1.txt, lightgbm_v1_holdout.txt
submission/           CSV сабмита (v1 — основной, v0 — эталон)
runs/backtest/        по папке на выпуск: trace, decision, report
runs/llm/test/        те же выпуски с решениями LLM
reports/              метрики и отчёт LLM
dashboard/            Vite/React, Cloudflare Pages
docs/                 архитектура, допущения, исследования
task context/         условие кейса и SCADA организаторов
```

---

## Данные и атрибуция

Погода: [Open-Meteo Single Runs](https://open-meteo.com/en/docs/single-runs-api) и Previous Runs, модель ECMWF IFS. Запросы, сетка, время выгрузки и хеши — в `data/nwp_cache/manifest.json`, описание архива — в [docs/03_WEATHER_ARCHIVE.md](docs/03_WEATHER_ARCHIVE.md). Условие кейса и SCADA предоставлены организаторами HackAlem AI. Часовой пояс SCADA (UTC+6) проверен кросс-корреляцией с погодой: [tz_xcorr.png](docs/figures/tz_xcorr.png), [scripts/tz_check.py](scripts/tz_check.py).
