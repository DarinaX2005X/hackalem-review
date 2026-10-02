# False Positive — Beeline Tariff Marketing Campaigns

Агент решает, каким абонентам предложить смену тарифа, какой тариф и канал
выбрать. В кейсе 23 441 абонент, бюджет 100 000 у.е., максимум 15 000 контактов
и 20 пилотов. Пилоты и финальные кампании расходуют общие ресурсы. Итог —
1–10 кампаний; критерий — прирост ARPU за вычетом затрат на коммуникации.

Текущий агент — детерминированный baseline: строит сегменты по текущему
тарифу и потреблению, выбирает следующий по публичной цене тариф и самый
дешёвый канал, проводит до трёх пилотов и выбирает допустимый финальный план
по наблюдениям. При неудачных пилотах возвращает fallback. Это не чат-бот:
LLM, API-ключи и `.env` для принятия решений не нужны.

Работают два контура:

- Judge: `agent.py:Agent.act(env) -> list[dict]`, независимое ядро `false_positive/`.
- Demo: FastAPI `backend.app.main:app`, четыре endpoint `/api/v1`, отдельная
  mock-среда на запуск и официальный evaluator для KPI. Frontend ещё не создан.

## Быстрый запуск backend

Команды из корня, PowerShell. В текущей рабочей копии `.venv` подготовлена.
В новом клоне сначала создайте её установленным Python: `py -3 -m venv .venv`
(или `python -m venv .venv`, если Python доступен в PATH).

```powershell
py -3.14 -m venv .venv
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

API: `http://127.0.0.1:8000`, интерактивная документация: `/docs`.
Во втором терминале:

```powershell
.\.venv\Scripts\python.exe -m backend.smoke
```

Сценарий: POST `/api/v1/runs` с `{"seed":42,"mode":"mock"}` → 202 и `run_id`
→ GET `/api/v1/runs/{run_id}` до `completed` или `failed`.
Детали и PowerShell-пример: [backend/README.md](backend/README.md).

## Как тестировать агента

Из корня проекта в PowerShell. Команды организаторов:

```powershell
$env:PYTHONUTF8 = '1'
$env:FP_LLM_PROVIDER = 'off'
.\.venv\Scripts\python.exe local_eval.py
.\.venv\Scripts\python.exe local_eval.py --runs 10
.\.venv\Scripts\python.exe make_submission.py
```

Один прогон показывает пилоты, затраты и net; десять seed — устойчивость.
`make_submission.py` создаёт `submission.csv`. Mock использует судейский
скоринг, но эффекты искусственные: результат не прогнозирует балл финала.

Полная автоматическая проверка (нужны `backend/requirements-dev.txt`):

```powershell
.\.venv\Scripts\python.exe scripts/verify_core.py
git diff --check
```

Один прогон показывает пилоты, затраты и net; десять seed — устойчивость.
`make_submission.py` создаёт `submission.csv`. Mock воспроизводит механику
судейства, но не скрытые эффекты финала. Seed 42: 3 пилота, 1 финальная
кампания, 1 285 контактов, net≈4 042; из seed 0–9 прибыльны 6.

Последняя проверка: 82 tests PASS, включая реальный HTTP smoke. Полный
verifier — FAIL из-за существующих CRLF в 14 organizer-файлах рабочей копии;
Git HEAD и manifest совпадают. Подробности — [PROJECT_STATE](docs/PROJECT_STATE.md).

## Документация и работа команды

[Архитектура](docs/ARCHITECTURE.md), [API v1](contracts/README.md),
[состояние](docs/PROJECT_STATE.md), [правила](AGENTS.md),
[backend handoff](docs/handoffs/03-backend-to-integration.md).
Данные синтетические; источники — [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).
Codex оставляет рабочее дерево для review; commit/push выполняет человек.
