# QalaAI — «Аким на 5 часов»

AI-симулятор управления условными районами Астаны для HackAlem AI.
Пользователь выбирает ровно пять мероприятий в пределах 100 бюджетных единиц
и сравнивает состояние города до и после двух условных лет.

Данные синтетические: это учебная модель по заданию хакатона, не реальные
городские измерения и не прогноз. Персональные данные не используются.
Набор районов, 14 мероприятий и формула сверены с предоставленным заданием.

## Архитектура и роль AI

HTML/CSS/vanilla JavaScript → FastAPI → расчётный движок → результат → OpenAI.

- `backend/data.py`: исходные показатели, мероприятия, веса и ограничения.
- `backend/simulation.py`: валидация, расчёт Score, дельт и вкладов мероприятий.
- `backend/main.py`: HTTP API для интерфейса.
- `backend/ai_service.py`: объяснение готового результата через OpenAI (`gpt-4o-mini`).
- `frontend/`: выбор решений, бюджет, результаты по районам и AI-анализ.
- `tests/`: тесты движка и API на стандартном `unittest`.

Нет базы данных, регистрации или сохранения планов между перезагрузками.
Все пользователи начинают с одного состояния. Сервер не изменяет исходный датасет.

AI объясняет сильные стороны, риски, компромиссы и возможные последствия,
но не считает баллы. Все числа готовит Python. Реальный AI требует ключа
и доступного API-баланса. Без ключа симуляция работает, а интерфейс сообщает
о недоступности анализа. Автотесты заменяют OpenAI подставными ответами:
они не доказывают качество настоящего ответа модели.

## Правила

- Бюджет 100; остаток не даёт бонуса.
- Ровно 5 разных мероприятий, максимум 2 из одного направления.
- Для районной меры нужен один из пяти районов. У городской район отсутствует
  (в JSON допускается `null`, означающий отсутствие района).
- M1 и M3 несовместимы во всём городе.
- M4/M7 и M5/M13 несовместимы при выборе одного района.
- Нарушение правил возвращает причины и `final_score: null`.
- Порядок выбора не влияет на расчёт.

## Формула Astana Quality of Life Score

Горизонт H = 8 кварталов. Для каждого района и показателя:

```text
новый показатель = clip(исходный + сумма(полный эффект × (8 − лаг) / 8)
                        + синергии, 0, 100)
D_района = сумма(вес показателя × новый показатель)
D_avg = сумма(доля населения × D_района)
Score = 0.7 × D_avg + 0.3 × минимальный D_района − N_crit
```

`N_crit` — число пар «район × показатель» строго ниже 40.
Значение ровно 40 не штрафуется. Расчёты не округляются, интерфейс показывает
два знака после запятой. Базовый Score = **52.55768** (на экране **52.56**).

| Показатель | T1 | T2 | E1 | E2 | S1 | S2 | B1 | B2 | C1 | C2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Вес | 0.10 | 0.10 | 0.09 | 0.11 | 0.11 | 0.11 | 0.09 | 0.09 | 0.10 | 0.10 |

Синергии не масштабируются лагом: M1/M2 дают +2 T1 в районе M1,
M10/M12 дают +2 B1 в районе M10, M5/M6 дают +2 E2 в районе M5.

## Что передаётся AI

Ответ симуляции содержит исходные и конечные значения, бюджет, Score,
критические показатели, выбранные меры и синергии. Дополнительно:

- `district_score_deltas`: готовая разница оценок каждого района.
- `indicator_deltas`: готовые изменения всех показателей после ограничения 0–100.
- `measure_contributions`: стоимость, лаг, реализованная доля и эффекты каждой
  меры по районам в `indicator_effects_before_clip` — **до ограничения 0–100**.
- `clipping_adjustments`: поправки, внесённые ограничением 0–100.

Эффекты мер и синергии вместе с поправками объясняют итоговые изменения.
Эффект меры не является её отдельным вкладом в итоговый Score: минимум района,
штрафы и границы делают такое разложение неоднозначным. AI запрещено самому
складывать или придумывать числа. Для невалидного плана дельты и поправки
равны `null`, список вкладов пуст. Старые поля ответа сохранены.

## Быстрый запуск на macOS (zsh)

В терминале откройте корень проекта:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Во втором терминале из той же папки:

```sh
.venv/bin/python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Откройте http://127.0.0.1:5500. Документация API: http://127.0.0.1:8000/docs.
Остановка каждого сервера — Ctrl+C в его терминале.

Когда будет ключ, остановите backend и в его терминале выполните:

```zsh
read -rs 'OPENAI_API_KEY?Вставьте ключ OpenAI (ввод скрыт): '
export OPENAI_API_KEY
printf '\n'
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Ключ вводится в скрытое приглашение, не в команду и не в код.
В Linux/bash вместо строки `read` используйте
`read -rsp 'OpenAI API key: ' OPENAI_API_KEY`.
`.env` автоматически не загружается. После работы можно убрать переменную
командой `unset OPENAI_API_KEY`.

Проверка без ключа и платных запросов:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

## Демонстрация и ограничения

Официальный пример ниже: M7/M8/M10 в Nura, M12 по городу, M5 в Saryarka.
Стоимость **95**, Score **56.54307**, прирост **3.98539**.
Дешёвый пример M9/M11/M10/M4 в Nura и M12 по городу стоит **61**,
Score **55.667385**. Районы уточнены для воспроизводимости второго результата.

Покажите исходные показатели → выберите пять мер → нажмите SIMULATE 2 YEARS →
сравните районы и критические показатели → прочитайте AI-анализ, если ключ настроен.

Сравнение команд, случайные события и автоматическая генерация презентаций
пока не реализованы и являются опциональными. Практическая цель — обсуждение
компромиссов в распределении бюджета. Применение к реальному городу потребует
проверенных данных и отдельной валидации модели.


## Возможности

- **Расчет базового состояния (`calculate_baseline`)**: Оценивает исходные показатели по всем районам города, рассчитывает средневзвешенный балл (`D_avg`), минимальный балл (`min_D`), количество критических индикаторов и итоговый скор.
- **Валидация сценария (`validate_scenario`)**: Проверяет список выбранных мер на соответствие бюджету, лимитам по категориям, ограничениям по количеству решений, а также на наличие глобальных и локальных несовместимостей.
- **Симуляция сценария (`simulate_scenario`)**: Применяет валидные меры с учетом временного горизона (`SIMULATION_HORIZON`), лагов внедрения, синергетических эффектов и ограничений индикаторов (от 0 до 100), возвращая детальное сравнение «до/после».

---

## Требования

Для работы модуля необходим Python 3.13 и файл `.data` со следующими структурами:
- `BUDGET` (int/float)
- `DISTRICTS` (dict с данными районов, долями населения и начальными индикаторами)
- `MEASURES` (dict доступных мер с указанием стоимости, категории, типа и эффектов)
- `INCOMPATIBILITIES` (список правил несовместимости мер)
- `SYNERGIES` (список возможных синергетических бонусов)
- `INDICATOR_WEIGHTS` (веса индикаторов для расчета баллов)
- `REQUIRED_DECISIONS` (обязательное количество мер в сценарии)
- `SIMULATION_HORIZON` (горизонт симуляции в условных единицах)

---

## Использование

### 1. Расчет базовой ситуации
```python
from backend.simulation import calculate_baseline

baseline = calculate_baseline()
print("Базовый скор города:", baseline["score"])
```


## Local installation and API verification

Use **Python 3.13**. Run these commands from the repository root.
The deterministic simulation works without an OpenAI key or AI availability.

### Install (Windows PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux, create the environment with `python3.13 -m venv .venv`
and use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe` below.

### Optional AI configuration

The backend reads `OPENAI_API_KEY` from its process environment only.
`.env.example` is a placeholder template. Creating a `.env` file does **not**
automatically load it; no dotenv loader is used. Keep real keys out of source,
frontend code, and version control. `.env` is ignored by Git.

To set the key for the current PowerShell session without entering it into
command history, enter it as the password in the credential prompt:

```powershell
$credential = Get-Credential -UserName "OpenAI" -Message "Enter the API key as the password"
$env:OPENAI_API_KEY = $credential.GetNetworkCredential().Password
Remove-Variable credential
```

Start the backend in this same session. Restart an existing backend after
changing its environment. Without a key, AI returns a controlled error and
simulation remains available. AI explains supplied results; it does not run
or replace the deterministic numerical simulation.

### Run the backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Run the frontend in a second terminal

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Open http://localhost:5500 (or http://127.0.0.1:5500).
The frontend calls http://127.0.0.1:8000; it is served separately from FastAPI.
Interactive API documentation is at http://127.0.0.1:8000/docs.

### API contracts

| Endpoint | Request | Response |
| --- | --- | --- |
| `GET /api/health` | No body | `{"status":"ok"}` |
| `GET /api/initial-state` | No body | Budget, required decisions, baseline score, districts, measures, indicator metadata |
| `POST /api/simulate` | `{"selections": [...]}` | Structured deterministic result; invalid scenarios return `valid=false`, validation errors, and `final_score=null` |
| `POST /api/analyze` | `{"simulation_result": {...}}` with the complete valid simulation response | `summary`, `strengths`, `risks`, `tradeoffs`, `consequences`, `recommendations`, or `{"error":{"code":"...","message":"..."}}` |

Domain validation and controlled AI errors use HTTP 200 with the above JSON
fields, preserving the frontend contract. Malformed request bodies use HTTP
422 with a `detail` list. AI errors never invalidate a simulation result.
AI error codes include `missing_api_key`, `invalid_simulation`,
`openai_request_failed`, `openai_timeout`, `invalid_ai_response`, and
`analysis_unavailable`. OpenAI requests have a 30-second SDK timeout and no
SDK retries. The analysis endpoint verifies every submitted numerical field against a fresh
engine calculation from the selected measures, rejecting altered results.

### Official reference scenario

Submit this JSON to `POST /api/simulate` through `/docs` or an HTTP client:

```json
{
  "selections": [
    {"measure_id": "M7", "district": "Nura"},
    {"measure_id": "M8", "district": "Nura"},
    {"measure_id": "M10", "district": "Nura"},
    {"measure_id": "M12", "district": null},
    {"measure_id": "M5", "district": "Saryarka"}
  ]
}
```

Expected: `valid=true`, `baseline_score` approximately **52.55768**,
`final_score` approximately **56.54307**, `total_cost=95`,
`remaining_budget=5`, and the M10 + M12 synergy in Nura.

### Run the complete automated test suite

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

No running server or API key is needed. API tests use FastAPI TestClient
(`httpx`) and the standard-library `unittest` runner. All external OpenAI calls
are mocked, including success, request failure, and timeout cases.


### Verified AI explanations and comparison

AI uses `gpt-4o-mini` to select and prioritize relevant evidence for strengths,
risks, trade-offs, consequences and recommendations. The engine supplies the
full result, district/indicator deltas and measure contributions. Python builds
a catalog of verified statements from that result; the model returns evidence
IDs and the server renders their text. Unknown IDs, wrong sections, duplicate
IDs and incomplete responses are rejected. This deliberately constrains prose:
AI chooses relevance but cannot invent numerical claims or critical indicators.
Numbers displayed in these sentences are formatted to five decimal places;
underlying engine results retain full precision. Missing keys or AI failures
show unavailable status, never a template silently presented as an AI response.

To compare strategies, simulate a valid plan, click **Save this result as Plan A**,
change the decisions, and simulate again. The comparison shows cost, Score and
all district scores for A and B. The saved plan exists only in the current tab
and disappears on reload; no database or authentication is involved.
`POST /api/compare` accepts `selections_a` and `selections_b` lists and recalculates
both using identical official data. Invalid plans return `valid=false`, reasons
under `errors.a`/`errors.b`, and `comparison=null`. A valid comparison includes
`score_difference` (B minus A), costs and per-district differences. Comparison
is deterministic; AI analysis describes the current plan separately.

### Reproducible installation

Python 3.13 is the tested runtime. `requirements.txt` pins the five direct
dependencies; `requirements.lock` constrains their tested transitive versions.
Keep both files together. No new runtime dependency was added for explanations
or comparison. Install from the repository root:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

On macOS/zsh, enter the key in the same terminal before starting the backend:

```sh
read -s 'OPENAI_API_KEY?Paste API key (hidden): '; echo
export OPENAI_API_KEY
```

Do not put a literal key in a shell command, source code or Git. `.env.example`
is a template only; this application reads the process environment and does
not automatically load `.env`. Run the frontend in a second terminal:

```sh
.venv/bin/python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Open http://127.0.0.1:5500. Both servers must remain running. This address works
on the local computer; this repository does not provide public hosting.

### Acceptance checklist and demo

- Identical budget/data, exactly five decisions, maximum two per category,
  no repetitions, district scope and all incompatibilities: engine tests.
- Lag-adjusted effects, all three synergies, 0–100 clipping, strict below-40
  penalty, population weights and official formula: numerical regression tests.
- Invalid input never receives a final Score. Simulation works without AI.
- Official demo: M7/M8/M10 in Nura, M12 city-wide, M5 in Saryarka. Cost 95,
  Score 56.54307; Nura S1 becomes 48 and S2 becomes 43.75. Both critical
  indicators are resolved. M10 + M12 adds its fixed B1 synergy.
- Comparison demo: M9/M11/M10/M4 in Nura plus M12 city-wide. Cost 61,
  Score 55.667385; S2 in Nura remains 37.625. Compared with the official demo,
  it spends less but scores 0.875685 lower. Unspent budget gives no bonus.
- AI errors, refusals, timeouts, invented evidence and forged input: mocked
  regression tests. Real API access additionally requires a funded key and
  model access; mocked tests do not prove live connectivity.

The project is a synthetic policy sandbox, not a decision system validated for
actual municipal spending. Its useful distinction is deterministic scoring
with a weakest-district term and transparent, constrained AI explanations.
Potential extensions include calibrated public datasets, alternative horizons
and sensitivity analysis. Unexpected events and presentation generation are
optional task features and are not implemented. Judge-awarded scores cannot
be inferred from a passing test suite.

### Русский интерфейс и показ проекта

Интерфейс и проверенные объяснения AI доступны на русском. Внутренние ID
районов и мероприятий в API не изменились. `GET /api/initial-state` дополнительно
возвращает `ui_labels` и `rules` для подписей и предварительных подсказок.
Окончательное решение о допустимости плана всегда принимает сервер.

1. Нажмите **«Загрузить пример из задания · 95»** и **«Рассчитать»**.
2. Посмотрите графики всех десяти показателей выбранного района: «было» и
   «стало» на одной шкале 0–100. Пунктир обозначает порог 40.
3. Сохраните результат как **план А**.
4. Загрузите **экономный план · 61** и снова рассчитайте. Кнопка примера
   заменяет текущий набор решений, но сохраняет план А до перезагрузки вкладки.
5. Сравните стоимость, общий балл, районные баллы и оставшиеся критические
   показатели. В раскрывающемся блоке видны мероприятия обоих планов.

`POST /api/compare` дополнительно возвращает `cost_difference` (Б − А),
`critical_a` и `critical_b`. Вывод о компромиссе строится по этим расчётам;
он не обещает улучшений за пределами модели и не выдаётся за ответ AI.

Готовый текст защиты и последовательность нажатий: [docs/DEMO_RU.md](docs/DEMO_RU.md).

## Инструкция для жюри: самостоятельная проверка без защиты

Проект можно проверить по этому репозиторию без участия команды.
Это локальное веб-приложение: публичный сервер не предоставляется.
Адрес `http://127.0.0.1:5500/` открывается на компьютере проверяющего после
запуска двух серверов по инструкции ниже.

### 1. Скачать проект и установить зависимости

Нужны Git и Python 3.13. Для клонирования приватного репозитория требуется
GitHub-аккаунт с доступом к репозиторию команды.

```sh
git clone https://github.com/BAITC-Hacks/hack-9983edb9-www-ai.git
cd hack-9983edb9-www-ai
```

**macOS / Linux:**

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

**Windows, PowerShell:**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Команды выполняются из корня репозитория. Активация виртуального окружения
не требуется: команды используют Python из `.venv` напрямую.

### 2. Запустить сервер расчётов

Для проверки расчётов API-ключ не нужен. Выполните в первом терминале:

**macOS / Linux:**

```sh
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

**Windows, PowerShell:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Дождитесь `Application startup complete`. Оставьте терминал открытым.
Проверка сервера: http://127.0.0.1:8000/api/health — ожидается `{"status":"ok"}`.

### 3. Открыть интерфейс

Во втором терминале перейдите в ту же папку репозитория и запустите:

**macOS / Linux:**

```sh
.venv/bin/python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

**Windows, PowerShell:**

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Откройте http://127.0.0.1:5500/ в браузере. Оба терминала должны оставаться
открытыми. Интерактивная документация API: http://127.0.0.1:8000/docs.

### 4. Проверить два готовых сценария

1. Нажмите **«Загрузить пример из задания · 95»**, затем **«Рассчитать»**.
   Ожидается стоимость **95**, остаток **5**, итоговый Score **56.54307**
   (в интерфейсе **56,54**) при начальном Score **52.55768**.
   В Нуре S1 становится **48**, S2 — **43.75**. Критических показателей
   после расчёта нет; срабатывает совместный бонус M10 + M12.
2. Посмотрите графики «было → стало» и переключите район.
3. Нажмите **«Сохранить результат как план А»**.
4. Нажмите **«Загрузить экономный план · 61»**, затем **«Рассчитать»**.
   Ожидается стоимость **61**, остаток **39**, Score **55.667385**
   (в интерфейсе **55,67**). Медицина Нуры остаётся критической:
   S2 = **37.625**. План дешевле на **34**, но его общий балл ниже на
   **0.875685** (в интерфейсе **0,88**).
5. Проверьте подсказки при выборе мер: бюджет не должен превышать 100,
   решений должно быть ровно пять, повторы запрещены, из одного направления
   разрешено не более двух мер. Несовместимые мероприятия блокируются.
   Сервер независимо повторяет проверку правил.

### 5. Проверить настоящий AI-анализ со своим ключом

**Ключ команды не включён в репозиторий.** Для настоящего AI-анализа
проверяющий использует свой `OPENAI_API_KEY` с доступом к используемой
модели `gpt-4o-mini` и доступной API-квотой. Запрос расходует квоту владельца
ключа. Без ключа расчёты, графики и сравнение планов продолжают работать,
а блок AI сообщает о недоступности анализа.

В первом терминале остановите сервер сочетанием **Ctrl+C**. Введите ключ
скрытым вводом в этом же терминале:

**macOS, zsh:**

```zsh
read -rs 'OPENAI_API_KEY?Вставьте свой API-ключ (ввод скрыт): '
echo
export OPENAI_API_KEY
```

**Linux, bash:**

```bash
read -rsp 'Вставьте свой API-ключ (ввод скрыт): ' OPENAI_API_KEY
echo
export OPENAI_API_KEY
```

**Windows, PowerShell:**

```powershell
$credential = Get-Credential -UserName "OpenAI" -Message "Введите свой API-ключ в поле пароля"
$env:OPENAI_API_KEY = $credential.GetNetworkCredential().Password
Remove-Variable credential
```

Снова запустите сервер командой из шага 2 **в том же терминале**.
На сайте повторите расчёт выбранного плана. В блоке AI должны появиться
русские объяснения: сильные стороны, риски, компромиссы, последствия
в модели и рекомендации.

AI выбирает существенные объяснения из проверенных фактов расчётного
движка. Он не рассчитывает Score и не генерирует произвольные числовые
прогнозы. Ошибка ключа, отсутствие квоты, недоступность модели или сети
не отменяют результат симуляции.

Приложение читает ключ из окружения процесса. Файл `.env` автоматически
не загружается. Не вставляйте ключ в исходный код, README, Git-коммиты
или форму сдачи проекта.

### 6. Запустить автоматические проверки

**macOS / Linux:**

```sh
.venv/bin/python -m unittest discover -s tests -v
```

**Windows, PowerShell:**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Ожидаемый результат финальной версии: **50 тестов, OK**. Для тестов
не нужны запущенные серверы и API-ключ: обращения к OpenAI заменены
тестовыми ответами, платных запросов нет. Поэтому для проверки живого
AI-подключения отдельно выполните шаг 5.
