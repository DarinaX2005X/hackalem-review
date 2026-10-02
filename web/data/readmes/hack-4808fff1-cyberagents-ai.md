# Saqta Voice Router — HackAlem AI

Гибридный голосовой AI-ассистент для страхового контакт-центра Saqta Insurance.

Система принимает голосовые и текстовые обращения на русском, казахском и в mixed RU/KK речи, преобразует голос в текст, использует LLM для выбора бизнес-сценария и возвращает голосовой ответ.

Главная идея решения: вместо классического intent-классификатора используется **LLM routing layer**, который учитывает смысл реплики, границы сценариев, multi-intent и состояние диалога.

## Возможности

- 40 бизнес-сценариев Saqta Insurance
- RU / KK / mixed-language routing
- Voice input через STT
- Voice output через TTS
- LLM-based semantic routing
- Multi-intent detection
- Structured Output
- Dialog state
- Slot extraction
- Out-of-scope / unclear / goodbye system intents
- Scenario boundary handling через `not_this_if`
- Deterministic scenario executor для ключевых quote/read-only flows
- Simulated operator handoff с сохранением контекста
- Confirmation guard для необратимых действий
- Supervisor Trace для объяснимости решения
- Confidence score и alternatives
- Измерение router latency
- Cross-browser microphone MIME negotiation
- Web UI с микрофоном и текстовым fallback
- Evaluation pipeline на 104 dev utterances
- Docker / Docker Compose
- `.env`-based secret management

## Последний измеренный routing benchmark

Полный прогон `data/dev_utterances.json` — 104 тестовых высказывания. Ниже — последний сохранённый benchmark маршрутизации до финального hardening. Live UI отдельно измеряет STT, router/response, TTS-to-first-audio и полный voice turn:

| Metric | Result |
|---|---:|
| Primary accuracy | **96.154%** |
| Full match | **94.231%** |
| Multi-intent recall | **92.308%** |
| Router median latency | **1481 ms** |

Маршрутизатор тестируется на русских, казахских и mixed-language запросах, включая multi-intent и системные сценарии.

## Архитектура

```text
                    ┌──────────────────────┐
                    │      Browser UI      │
                    │  Voice + Text input  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │         STT          │
                    │   OpenAI Audio API   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     LLM Router       │
                    │                      │
                    │ RU / KK / mixed      │
                    │ Multi-intent         │
                    │ Structured Output    │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
      scenarios.json     Dialog State     Boundary Rules
                         + Slots          + not_this_if
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │   Decision Policy    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Scenario Executor    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │         TTS          │
                    │   OpenAI Audio API   │
                    └──────────────────────┘

                               └────► Supervisor Trace
```

## LLM Router

Router не работает как простой keyword classifier.

При выборе сценария учитываются:

- semantic meaning текущей реплики;
- `description` сценария;
- `not_this_if` / boundary rules;
- история диалога;
- активный сценарий;
- уже известные slots;
- RU / KK / mixed speech;
- multi-intent обращения.

LLM возвращает structured decision, включающий:

```json
{
  "language": "ru",
  "scenarios": [
    {
      "scenario_id": "SC06",
      "confidence": 0.9,
      "reason": "Travel insurance purchase"
    }
  ],
  "alternatives": [],
  "slots": {}
}
```

## Supervisor Trace

Web UI показывает технический trace каждого решения:

- transcript;
- detected language;
- scenario ID;
- confidence;
- alternatives;
- routing reason;
- extracted slots;
- STT latency;
- router latency;
- response latency;
- TTS-to-first-audio latency;
- end-of-user-turn → first-audio latency для voice turns.

Это позволяет оператору или жюри видеть, почему AI выбрал конкретный сценарий.

## Соответствие must-have HackAlem

| Требование | Реализация |
|---|---|
| Голосовое взаимодействие в вебе | Browser MediaRecorder → STT → LLM Router → TTS |
| LLM-слой выбора сценария | Structured LLM routing по каталогу 40 сценариев, без encoder intent classifier |
| Корректность выбора | `scripts/evaluate_dev.py`, raw и accepted predictions |
| Панель трассировки | transcript, proposed/accepted scenarios, reason, alternatives, slots, handoff, latency |
| Русский / казахский / mixed | Router принимает `ru`, `kk`, `mixed`; reply language передаётся в TTS |
| Безопасность | необратимые действия не выполняются без явного подтверждения |
| Передача оператору | simulated handoff с queue + reason в Supervisor Trace |
| Запуск | `run.bat`, `bash run.sh`, Docker Compose |

## Быстрый запуск

### Windows

Создать виртуальное окружение:

```powershell
python -m venv .venv
```

Активировать:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Установить зависимости:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Создать `.env`:

```powershell
Copy-Item .env.example .env
```

Добавить API key:

```env
OPENAI_API_KEY=your_key_here
```

Запустить:

```powershell
.\run.bat
```

Открыть в браузере:

`http://localhost:8000`

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
bash run.sh
```

### Docker Compose

```bash
docker compose up --build
```

## Evaluation

Быстрая проверка первых 10 примеров:

```bash
python scripts/evaluate_dev.py --limit 10
```

Полный benchmark:

```bash
python scripts/evaluate_dev.py
```

Evaluation сохраняет raw + accepted predictions и рассчитывает:

- Primary accuracy
- Full match
- Multi-intent recall
- Median router latency

## Offline smoke-check

Без внешних API можно проверить детерминированный executor:

```bash
python scripts/smoke_check.py
```

Проверяются OGPO quote, travel quote, claim status и office lookup на синтетических данных.

## Demo scenarios

### 1. Автострахование

```text
Сколько стоит обязательная страховка на машину?
```

Expected route:

```text
SC01
```

### 2. Travel insurance

```text
Мне нужна страховка для поездки за границу.
```

Expected route:

```text
SC06
```

### 3. Kazakh

```text
Шетелде аяғымды сындырып алдым, сақтандыруым бар.
```

Expected route:

```text
SC15
```

### 4. Out of scope

```text
Можно у вас взять кредит на машину?
```

Expected route:

```text
SYS_OUT_OF_SCOPE
```

### 5. Multi-intent

Router поддерживает несколько независимо actionable intents в одной реплике и возвращает массив сценариев.

## Структура проекта

```text
voice-router-saqta/
├── app/
│   ├── main.py
│   ├── router.py
│   ├── assistant.py
│   ├── executor.py
│   ├── audio.py
│   ├── session.py
│   ├── schemas.py
│   ├── data_store.py
│   ├── config.py
│   └── static/
│       └── index.html
├── data/
│   ├── scenarios.json
│   ├── slots.json
│   ├── actions.json
│   ├── knowledge_base.json
│   ├── mock_backend.json
│   └── dev_utterances.json
├── scripts/
│   ├── evaluate_dev.py
│   └── smoke_check.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.bat
├── run.sh
└── .env.example
```

## Security

Секреты не хранятся в репозитории.

`.env` исключён через `.gitignore`.

Для запуска используется `.env.example`, в который не включаются реальные API keys.

## Tech stack

- Python
- FastAPI
- Uvicorn
- OpenAI API
- Structured Outputs
- OpenAI Speech-to-Text
- OpenAI Text-to-Speech
- HTML / CSS / JavaScript
- Docker

## HackAlem AI

Проект разработан для кейса **Voice Router — гибридный голосовой AI-робот с LLM-слоем выбора сценария**.

Основной фокус решения — высокая точность semantic routing при живой RU / KK / mixed речи и минимальной задержке.

## Safety and current scope

- Все данные в `data/` синтетические.
- Необратимые действия не выполняются молча: требуется явное подтверждение клиента.
- Handoff в веб-демо моделируется очередью оператора и отображается в Supervisor Trace.
- Реализованы детерминированные расчёты/поиски для ключевых quote/read-only сценариев; остальные сценарии продолжают безопасный grounded flow.
- `.env` исключён из Git и Docker build context через `.dockerignore`.
