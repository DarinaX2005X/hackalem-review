# Voice Router — Hybrid Voice AI Robot with LLM Scenario Routing

## 1. О проекте

**Voice Router**
От голосового меню — к интеллектуальной маршрутизации.

Клиенту больше не нужно искать нужный пункт меню или ждать свободного оператора. Voice Router понимает, что именно хочет клиент, и сам выбирает нужный бизнес-сценарий.LLM выступает не только как conversational layer, а как интеллектуальный роутер между голосом клиента и бизнес-логикой Saqta Insurance.

Система поддерживает:

- русский язык;
- казахский язык;
- смешанную RU/KZ речь;
- single-intent и multi-intent запросы;
- продолжение сценария между несколькими репликами;
- смену темы и возврат к предыдущему сценарию;
- clarification вместо угадывания при низкой уверенности;
- перевод на оператора;
- непрерывный голосовой диалог;
- supervisor trace с выбранным сценарием, confidence, альтернативами и latency.

В проекте используется датасет HackAlem AI / Halyk Bank с **40 бизнес-сценариями и системными intents**. Выбор сценария выполняется LLM; encoder-based intent classifier не используется.

Все бизнес-данные в `data/starter_kit/` синтетические.

---

## ⚡ Quick Start

Для полной технической проверки нужны:

- Python **3.11+**;
- Node.js **22.12+** и npm;
- Chrome или Edge;
- микрофон;
- интернет;
- `OPENAI_API_KEY`.

Используемая модель LLM Router:

```dotenv
OPENAI_ROUTER_MODEL=gpt_4.1-mini
```

### Минимальный путь запуска

```text
1. Клонировать репозиторий
2. Установить backend dependencies
3. Выполнить npm ci во frontend
4. Создать .env и frontend/.env
5. Запустить backend
6. Запустить frontend
7. Открыть URL, который выведет Vite
8. Разрешить доступ к микрофону
9. Нажать «Начать разговор»
```

Подробные инструкции:

- [Установка Backend](#9-установка-backend)
- [Установка Frontend](#10-установка-frontend)
- [Параметры окружения](#11-параметры-окружения)
- [Запуск](#12-запуск)
- [Проверка основного сценария экспертами](#13-проверка-основного-сценария-экспертами)
- [Быстрая техническая проверка](#22-быстрая-техническая-проверка)

> Все команды ниже приведены для Windows PowerShell и отдельно для Linux/macOS там, где команды отличаются. Значения host/port в README — рекомендуемые примеры; при изменении адресов важно, чтобы frontend URL, `FRONTEND_ORIGIN` и `VITE_API_BASE_URL` были согласованы.

---

## 2. Основной пользовательский сценарий

```text
Микрофон
   ↓
Streaming Voice Input
   ↓
STT + endpointing
   ↓
Final transcript
   ↓
Conversation Runtime
   ↓
POST /api/message
   ↓
Agent Core
   ↓
LLM Router + Dialogue State + Decision Policy
   ↓
Scenario / knowledge / mock backend
   ↓
response_text + routing + state + trace
   ↓
Browser TTS
   ↓
Голосовой ответ
   ↓
Listening resumes
```

Один `session_id` используется на протяжении всей беседы.

После голосового ответа система снова переходит в режим прослушивания. Разговор завершается только когда Agent Core возвращает:

- `conversation_status = ended`; или
- `conversation_status = handoff`.

Завершение отдельного бизнес-сценария само по себе не завершает беседу.

---

# 3. Архитектура

```text
┌───────────────────────────────────────────────────────────────┐
│                         FRONTEND                              │
│                                                               │
│  Microphone / File                                            │
│        │                                                      │
│        ▼                                                      │
│  VoiceControls ──────────────────────────────────────┐        │
│        │                                              │        │
│        │ final transcript                             │        │
│        ▼                                              │        │
│  ConversationRuntime                                  │        │
│        │                                              │        │
│        ├──────────── POST /api/message ───────────────┼───┐    │
│        │                                              │   │    │
│        ├── Browser TTS ◄── response_text              │   │    │
│        │                                              │   │    │
│        └── Supervisor Trace ◄── routing/state/trace   │   │    │
│                                                               │
└───────────────────────────────────────────────────────────┼───┘
                                                            │
                                                            ▼
┌───────────────────────────────────────────────────────────────┐
│                         BACKEND                               │
│                                                               │
│  WS /api/v1/voice                                             │
│      │                                                        │
│      ├── Silero VAD / endpointing                             │
│      └── OpenAI gpt-live-transcribe                           │
│                                                               │
│  POST /api/message                                            │
│      │                                                        │
│      ▼                                                        │
│  Agent Core                                                   │
│      │                                                        │
│      ├── Scenario Catalog                                     │
│      ├── LLM Router                                           │
│      ├── Confidence / Clarification Policy                    │
│      ├── DialogueState                                        │
│      ├── Scenario Stack / Pending Scenarios                   │
│      ├── Slot extraction                                      │
│      ├── Basic response generation                            │
│      └── Trace + latency                                      │
│           │                                                   │
│           ├── scenarios.json                                  │
│           ├── slots.json                                      │
│           ├── actions.json                                    │
│           ├── knowledge_base.json                             │
│           └── mock_backend.json                               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Разделение ответственности

**Voice Input / STT**
- захватывает микрофон;
- передаёт PCM16 audio по WebSocket;
- использует Silero VAD для определения конца реплики;
- получает streaming transcription от OpenAI;
- передаёт только финальную реплику в conversation runtime.

**Agent Core**
- понимает смысл пользовательской реплики;
- выбирает один или несколько сценариев;
- использует `description`, `not_this_if`, `priority` и примеры из `scenarios.json`;
- хранит состояние разговора;
- поддерживает multi-intent;
- поддерживает продолжение текущего сценария;
- при неоднозначности задаёт clarification question вместо угадывания;
- возвращает короткий ответ и supervisor trace.

**Conversation Runtime**
- хранит один `session_id` на протяжении диалога;
- связывает STT, Agent Core и TTS;
- не допускает параллельной обработки реплик;
- после окончания TTS снова включает listening;
- останавливает автоматический loop при `handoff` или `ended`.

**TTS**
- реализован через Browser Web Speech API;
- поддерживает `ru-RU`;
- пытается использовать `kk-KZ`, если такой voice доступен в браузере/ОС;
- измеряет время до начала аудио.

**Supervisor UI**
- отображает transcript;
- выбранные сценарии;
- confidence;
- alternatives;
- short routing reason;
- slots;
- active/pending scenarios;
- conversation status;
- latency.

---

# 4. Agent Core

Основной HTTP endpoint:

```http
POST /api/message
Content-Type: application/json
```

Request:

```json
{
  "session_id": "uuid",
  "text": "Хочу продлить полис и добавить сына"
}
```

Response:

```json
{
  "response_text": "Ответ ассистента",
  "conversation_status": "awaiting_user",
  "routing": {},
  "state": {},
  "trace": {}
}
```

Допустимые `conversation_status`:

```text
active
awaiting_user
awaiting_confirmation
handoff
ended
```

### Routing

Router использует один структурированный LLM-вызов и поддерживает:

- RU;
- KZ;
- mixed;
- single-intent;
- multi-intent;
- `SYS_UNCLEAR`;
- `SYS_OUT_OF_SCOPE`;
- `SYS_GOODBYE`;
- semantic decomposition;
- slot extraction;
- continuation detection;
- alternatives и confidence.

Пример:

```text
"Хочу продлить ОГПО и добавить туда сына"
```

может быть маршрутизирован как:

```text
SC27 — Policy renewal
SC04 — Add driver
```

### Dialogue State

Agent Core хранит состояние сессии между репликами, в том числе:

```text
session_id
turn_number
language
client_id
active_scenario
scenario_stack
pending_scenarios
slots
unclear_count
conversation_status
history
```

Для MVP состояние хранится in-memory.

### Clarification

При неоднозначном запросе бот не обязан угадывать сценарий.

Пример:

```text
Вы хотите узнать статус страхового случая
или не согласны с уже принятым решением?
```

Следующая реплика клиента обрабатывается в той же сессии.

---

# 5. Starter Kit

Бизнес-данные находятся в:

```text
data/starter_kit/
```

Ключевые файлы:

| Файл | Назначение |
|---|---|
| `scenarios.json` | 40 бизнес-сценариев + системные intents |
| `slots.json` | типы и правила слотов |
| `actions.json` | контракты mock backend actions |
| `knowledge_base.json` | продукты, правила, тарифы, офисы, клиники и справочная информация |
| `mock_backend.json` | тестовые клиенты, полисы, claims и payments |
| `dialogs_sample.json` | 10 размеченных многоходовых диалогов |
| `dev_utterances.json` | 104 размеченных запроса для проверки routing |
| `evaluate.py` | официальный evaluator |

Исходные starter-kit файлы не должны изменяться для улучшения метрик.

---

# 6. Технологии

| Область | Технологии |
|---|---|
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Agent Core | OpenAI Agents SDK / structured LLM output, Router model: `gpt_4.1-mini` |
| STT | OpenAI `gpt-live-transcribe` |
| Voice endpointing | Silero VAD, ONNX Runtime, faster-whisper |
| Audio processing | Web Audio API, AudioWorklet, PyAV, NumPy |
| Frontend | React, TypeScript, Vite |
| TTS | Browser Web Speech API |
| Data | JSON starter kit |
| Testing | pytest, Ruff, TypeScript, Vite build |
| Agent evaluation | `dev_utterances.json` + `evaluate.py` |

Для MVP не требуются:

- PostgreSQL;
- Supabase;
- Redis;
- Docker;
- GPU;
- vector database;
- отдельный intent classifier.

---

# 7. Системные требования

Рекомендуемая среда:

- Windows 10/11;
- PowerShell;
- Python **3.11+**;
- Node.js **22.12+**;
- npm;
- Git;
- Google Chrome или Microsoft Edge;
- микрофон;
- интернет;
- OpenAI API key с доступом к используемым моделям.

Разработка voice-модуля проверялась также на Python 3.13 и Node.js 24.13.

---

# 8. Получение проекта

```powershell
git clone https://github.com/BAITC-Hacks/hack-52fe5ec3-overfit.git
cd hack-52fe5ec3-overfit
git checkout main
git pull origin main
```

Все следующие команды выполняются из корня репозитория, если не указано иное.

---

# 9. Установка Backend

## Windows PowerShell

Проверить Python:

```powershell
python --version
```

Создать virtual environment:

```powershell
python -m venv .venv
```

Установить backend со всеми зависимостями, нужными для voice-модуля и тестов:

```powershell
./.venv/Scripts/python.exe -m pip install -c backend/requirements.lock -e './backend[dev,voice]'
```

## Linux / macOS

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -c backend/requirements.lock -e './backend[dev,voice]'
```

---

# 10. Установка Frontend

Команды одинаковы для Windows, Linux и macOS:

```bash
cd frontend
npm ci
node --version
npm --version
cd ..
```

> Для воспроизводимой установки используется `npm ci`, а не `npm install`.

---

# 11. Параметры окружения

## Backend

Создать корневой `.env`.

### Windows PowerShell

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

### Linux / macOS

```bash
cp .env.example .env
```

Минимальная конфигурация:

```dotenv
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_ROUTER_MODEL=gpt_4.1-mini
FRONTEND_ORIGIN=http://127.0.0.1:5173
```

`FRONTEND_ORIGIN` должен совпадать с origin, на котором фактически открыт frontend. Если Vite запустился на другом host/port, обновите это значение и перезапустите backend.

Опционально:

```dotenv
STARTER_KIT_PATH=data/starter_kit
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

| Переменная | Назначение |
|---|---|
| `OPENAI_API_KEY` | ключ OpenAI API; используется только backend |
| `OPENAI_ROUTER_MODEL` | модель для LLM Router |
| `FRONTEND_ORIGIN` | разрешённый frontend Origin |
| `STARTER_KIT_PATH` | путь к starter kit; по умолчанию `data/starter_kit` |
| `BACKEND_HOST` | host backend |
| `BACKEND_PORT` | port backend |

**Никогда не размещайте реальный API key в Git, README или frontend env.**

## Frontend

Создать:

```text
frontend/.env
```

Для полной интеграции:

```dotenv
VITE_USE_MOCK_AGENT=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Если backend запущен на другом адресе, укажите его фактический URL в `VITE_API_BASE_URL`.

`VITE_USE_MOCK_AGENT=true` используется только для автономной разработки frontend и не является режимом основной технической проверки.

---

# 12. Запуск

Нужны **два терминала**.

## Терминал 1 — Backend

Из корня репозитория.

### Windows PowerShell

```powershell
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --ws-max-size 8192 --ws-max-queue 16
```

### Linux / macOS

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --ws-max-size 8192 --ws-max-queue 16
```

Дождитесь:

```text
Application startup complete
```

Проверка:

```text
http://127.0.0.1:8000/health
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

## Терминал 2 — Frontend

```bash
cd frontend
npm run dev
```

Vite выведет фактический локальный URL приложения в терминале. Откройте **именно этот URL** в Chrome или Edge.

Типичный адрес:

```text
http://127.0.0.1:5173
```

или:

```text
http://localhost:5173
```

Если origin отличается от значения `FRONTEND_ORIGIN`, обновите `.env` и перезапустите backend.

Оба терминала должны оставаться запущенными.

Для остановки:

```text
Ctrl+C
```

---

# 13. Проверка основного сценария экспертами

Перед началом проверьте:

- [ ] backend запущен без ошибок;
- [ ] `/health` доступен;
- [ ] frontend открыт по URL, который вывел Vite;
- [ ] `VITE_USE_MOCK_AGENT=false`;
- [ ] `OPENAI_API_KEY` задан;
- [ ] `OPENAI_ROUTER_MODEL=gpt_4.1-mini`;
- [ ] браузеру разрешён доступ к микрофону;
- [ ] интернет-соединение доступно.

1. Запустить backend.
2. Запустить frontend.
3. Открыть URL frontend, который вывел Vite (например `http://127.0.0.1:5173` или `http://localhost:5173`).

4. Разрешить браузеру доступ к микрофону.
5. Нажать **«Начать разговор»**.
6. Сказать:

> «Я оплатил страховку, но полис не появился».

7. После завершения реплики замолчать.

Ожидаемый pipeline:

```text
microphone
→ streaming STT
→ final transcript
→ Agent Core
→ routing
→ response_text
→ Browser TTS
→ listening resumes
```

Ожидаемое поведение:

- на экране появляется финальная транскрипция;
- Agent Core выбирает соответствующий страховой сценарий;
- появляется текстовый ответ;
- ответ озвучивается;
- Supervisor Trace отображает routing/state/latency;
- после завершения озвучивания приложение снова готово слушать пользователя;
- `session_id` сохраняется.

8. Сказать вторую реплику в той же беседе, например:

> «И ещё проверьте, до какого числа действует мой полис».

9. Убедиться, что это **не новая сессия** и история предыдущей реплики сохранена.

10. Для завершения разговора сказать:

> «Спасибо, до свидания».

После `conversation_status = ended` автоматическое listening должно остановиться.

---

# 14. Дополнительные сценарии проверки

## Казахский

Сказать:

> «Маған саяхат сақтандыруы керек».

## Mixed RU/KZ

Сказать:

> «Маған полис керек, сколько это стоит?»

## Multi-intent

Через голос или text fallback:

> «Хочу продлить ОГПО и добавить туда сына».

## Clarification

Использовать неоднозначный запрос:

> «У меня проблема с полисом».

Ожидается уточняющий вопрос вместо случайного выбора сценария.

## Out of scope

Сказать:

> «Какая завтра погода в Алматы?»

Запрос не должен принудительно маршрутизироваться в SC01–SC40.

## Text fallback

Если микрофон или STT временно недоступны, основной Agent Core можно проверить через текстовое поле.

Text fallback проходит через тот же runtime pipeline:

```text
ConversationRuntime
→ Agent Core
→ Trace
→ TTS
```

Это резервный канал для диагностики и demo, а не отдельная mock-логика.

---

# 15. Supervisor Trace

После реплики интерфейс может показывать:

```text
Transcript
Language
Selected scenario
Confidence
Alternative
Reason
Active scenario
Slots
Conversation status

Latency
STT
Router
Policy
Tools
Response
TTS first audio
Total
```

Frontend не рассчитывает confidence и не выбирает scenario самостоятельно.

---

# 16. API и WebSocket контракты

## Agent API

```http
POST /api/message
```

Request:

```json
{
  "session_id": "uuid",
  "text": "текст клиента"
}
```

Response:

```json
{
  "response_text": "ответ",
  "conversation_status": "awaiting_user",
  "routing": {},
  "state": {},
  "trace": {}
}
```

## Voice

```text
WS /api/v1/voice
```

Начальное сообщение:

```json
{
  "type": "start",
  "session_id": "<UUID>",
  "sample_rate": 24000,
  "channels": 1,
  "pause_ms": 2500
}
```

После `ready` frontend отправляет PCM16 little-endian mono 24 kHz.

Основные server events:

```text
ready
activity
transcript.partial
committed
utterance.final
empty
error
```

В Agent Core передаётся только финальная реплика.

---

# 17. Тестирование перед сдачей

## Backend

```powershell
./.venv/Scripts/python.exe -m pytest backend/tests -q
./.venv/Scripts/python.exe -m ruff check backend/app backend/tests
./.venv/Scripts/python.exe -m ruff format --check backend/app backend/tests
```

## Frontend

```bash
cd frontend
npm run typecheck
npm run build
npm run test:runtime
npm run test:tts
npm run test:trace
npm run test:integration
cd ..
```

Если в `package.json` присутствует отдельный test-script для Voice Runtime Bridge, его также следует выполнить перед сдачей.

Все команды должны завершиться без ошибок перед технической сдачей.

---

# 18. Проверка Router

При наличии рабочего `OPENAI_API_KEY` и `OPENAI_ROUTER_MODEL` Router можно проверить на предоставленном dev-наборе.

```powershell
python data/starter_kit/evaluate.py predictions.json data/starter_kit/dev_utterances.json
```

Evaluator рассчитывает:

- primary accuracy;
- full match;
- multi-intent recall;
- разбивку по языку;
- разбивку по типу запроса.

`dev_utterances.json` не должен изменяться для улучшения результата.

---

# 19. Ограничения MVP

- состояние Agent Core хранится in-memory;
- после перезапуска backend активные сессии не сохраняются;
- Browser TTS зависит от voices, установленных в ОС/браузере;
- при отсутствии `kk-KZ` используется fallback voice;
- STT требует работающего OpenAI API и интернет;
- Silero VAD определяет акустическую паузу, а не смысловую завершённость мысли;
- система предназначена для синтетического hackathon dataset;
- реальные персональные данные использовать не следует;
- основной MVP запускается одним backend-процессом.

---

# 20. Безопасность

- `.env` не должен попадать в Git;
- OpenAI key используется только backend;
- секреты нельзя размещать в `VITE_*` переменных;
- реальные персональные данные не используются;
- supervisor trace показывает application-level explanation, а не hidden chain-of-thought;
- необратимые бизнес-действия должны выполняться только после явного подтверждения пользователя.

---

# 21. Troubleshooting

| Проблема | Что проверить |
|---|---|
| Backend не запускается | Python version, venv, `backend[dev,voice]`, запуск из корня |
| Frontend не запускается | Node/npm versions, `npm ci` |
| Backend unavailable | порт 8000, `/health`, `VITE_API_BASE_URL` |
| Ошибка OpenAI | `OPENAI_API_KEY`, API balance/access, интернет |
| Router не работает | `OPENAI_ROUTER_MODEL` и доступ к модели |
| Микрофон не доступен | разрешение браузера, Chrome/Edge, localhost/127.0.0.1 |
| WebSocket rejected | `FRONTEND_ORIGIN`, frontend URL и backend port |
| Казахский TTS звучит некорректно | наличие `kk-KZ` voice в ОС/браузере |
| Текст работает, voice нет | проверить `/api/v1/voice`, микрофон, VAD/STT |
| Voice работает, Agent не отвечает | проверить `POST /api/message` через `/docs` |
| Порт занят | остановить предыдущие процессы через `Ctrl+C` |

---

# 22. Быстрая техническая проверка

## Windows PowerShell

```powershell
git clone https://github.com/BAITC-Hacks/hack-52fe5ec3-overfit.git
cd hack-52fe5ec3-overfit

python -m venv .venv
./.venv/Scripts/python.exe -m pip install -c backend/requirements.lock -e './backend[dev,voice]'

cd frontend
npm ci
cd ..

Copy-Item .env.example .env
notepad .env
```

## Linux / macOS

```bash
git clone https://github.com/BAITC-Hacks/hack-52fe5ec3-overfit.git
cd hack-52fe5ec3-overfit

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -c backend/requirements.lock -e './backend[dev,voice]'

cd frontend
npm ci
cd ..

cp .env.example .env
```

Указать:

```dotenv
OPENAI_API_KEY=...
OPENAI_ROUTER_MODEL=gpt_4.1-mini
FRONTEND_ORIGIN=http://127.0.0.1:5173
```

Создать `frontend/.env`:

```dotenv
VITE_USE_MOCK_AGENT=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Запустить backend:

```powershell
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --ws-max-size 8192 --ws-max-queue 16
```

В другом терминале:

```bash
cd frontend
npm run dev
```

Открыть URL, который выведет Vite. Если origin отличается от `FRONTEND_ORIGIN`, обновить переменную и перезапустить backend.

После этого выполнить основной голосовой сценарий из раздела **«Проверка основного сценария экспертами»**.

---

## Финальный smoke-check перед сдачей

Рекомендуется выполнить проверку из **чистого clone**, а не из рабочей папки разработчика:

```text
clone
→ install backend
→ npm ci
→ configure env
→ /health
→ frontend
→ microphone
→ turn 1
→ TTS
→ turn 2 в той же session
→ goodbye / ended
→ tests
```

Если для запуска требуется действие, которого нет в README, его необходимо добавить в инструкцию до сдачи.

---

# 23. Дополнительная документация

Детальная документация отдельных модулей:

```text
README_VOICE.md
README_CONVERSATION_RUNTIME.md
docs/
```

Главным документом для установки и технической проверки итоговой системы является **этот корневой `README.md`**.
