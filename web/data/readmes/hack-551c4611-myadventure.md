# JINALYS AI

## 1. Описание решения и назначение
Локальный AI-секретарь совещаний: аудио → транскрипт со спикерами → поручения/сроки/ответственные → ключевые цитаты → DOCX. Предназначен для подготовки и ручной проверки протокола секретарём.

Интеграционный код связывает модули участников №1/№2 с существующим интерфейсом №3. На проверочной машине Whisper распознал публичную RU-запись, а Ollama/qwen3:4b прошла проверку протокола на синтетическом RU/KZ/mixed-тексте. Веса pyannote ещё не подготовлены; реальный сквозной RU/KK/mixed/30-минутный сценарий не подтверждён. Кнопка «Демоны ашу» остаётся явно обозначенным примером, не результатом распознавания. [Статус интеграции и последние изменения](docs/PROJECT_STATUS.md).

## 2. Архитектура
Включены защитные проверки Protocol AI из коммита `88a51dc`: очистка технических идентификаторов вместо имён, проверка имён по цитируемым репликам и фильтрация неподтверждённых сроков/пустых поручений. Неопределённые значения остаются `null`, задачи с сомнениями требуют ручной проверки. [Описание и ограничения](docs/PROTOCOL_QUALITY_UPDATE.md).

```text
Browser File + metadata
 → Next.js POST /api/meetings (streaming proxy)
 → Python POST /jobs → 202 jobId
 → очередь: prepareAudio → transcribeAudio → diarizeAudio → alignTranscript
 → protocol: chunks → extractor → verifier → summary
 → MeetingProtocol (+ date из metadata)
Browser GET /api/meetings?jobId=... → status/stage/result → UI → DOCX
```
Один Python worker, до двух активных/ожидающих заданий. Статусы отражают реальные вызовы. chunk:N/M не является точным процентом. done выдаётся после сохранения всего результата.

Основные файлы: app/page.tsx, app/api/meetings/route.ts, integration/server.py, speech/, protocol/, lib/contracts.ts, lib/export.ts. [Полный HTTP-контракт и жизненный цикл](docs/LOCAL_RUN.md).

## 3. Используемые технологии
Next.js App Router, React, TypeScript, CSS, Zod, lucide-react, docx. Python standard-library HTTP server и очередь. Speech: faster-whisper 1.2.1, PyAV 18.1.0, local pyannote.audio 4.0.7. Protocol: jsonschema 4.26.0, Ollama/qwen3:4b. Npm версии закреплены package-lock.json.

## 4. Инструкции по установке
PowerShell из корня репозитория:
```powershell
npm.cmd ci
python -m venv .venv
.venv/Scripts/python -m pip install -r integration/requirements.txt
python -m venv speech/.venv-diarization
speech/.venv-diarization/Scripts/python -m pip install -r speech/requirements-diarization.txt
```
Скачивание моделей и необходимые условия доступа описаны пошагово в [docs/LOCAL_RUN.md](docs/LOCAL_RUN.md), раздел «Этап 2». Whisper требует локальных весов/tokenizer, pyannote — полного разрешённого community-1 bundle, Ollama — qwen3:4b. Веса не коммитятся. Без них реальная обработка возвращает ошибку, не demo fallback.

## 5. Инструкции по запуску
Запуск в трёх отдельных терминалах из корня:
1. `powershell -File protocol/start-local.ps1` — Ollama на 127.0.0.1:11435.
2. Установить переменные из раздела 7, затем `.venv/Scripts/python -m integration.server` — Python на 127.0.0.1:8765.
3. `npm.cmd run dev` — UI на http://127.0.0.1:3000.

Если 3000 занят, `npm.cmd run dev -- --port 3001`. Для production frontend: `npm.cmd run build`, затем `npm.cmd start`; Python и Ollama остаются отдельными процессами. Полные copy-paste команды и порядок настройки: [LOCAL_RUN.md](docs/LOCAL_RUN.md).

## 6. Необходимые зависимости
Git, Node.js 22.18+, npm, Python 3.11+ (для ML-пакетов рекомендуются 3.11/3.12), Ollama, локальные Whisper/pyannote/Qwen. Windows-команды выше; Linux/macOS: npm вместо npm.cmd, .venv/bin/python вместо Scripts/python.

Speech использует CPU int8; автор Protocol AI проверял qwen3:4b на RTX 4060 Laptop 8 ГБ и примерно 16 ГБ RAM. Это проверенная им конфигурация, не установленный минимум. UI GPU не нужен. Whisper около 1.6 ГБ, Qwen около 2.5 ГБ на диске; pyannote/PyTorch требуют дополнительного места. Для pyannote decoder могут понадобиться совместимые TorchCodec/FFmpeg shared libraries. Подробности: [speech/README.md](speech/README.md), [speech/DIARIZATION.md](speech/DIARIZATION.md), [Protocol AI](docs/handoff/protocol-ai.md).

## 7. Параметры окружения
Python читает переменные процесса, а не .env автоматически. Задать в терминале Python сервера:
```powershell
$env:LOCAL_LLM_BASE_URL='http://127.0.0.1:11435'
$env:LOCAL_LLM_MODEL='qwen3:4b'
$env:LOCAL_LLM_TIMEOUT='600'
$env:JINALYS_STT_MODEL_DIR=(Resolve-Path speech/models/large-v3-turbo).Path
$env:JINALYS_DIARIZATION_MODEL_DIR=(Resolve-Path speech/models/community-1).Path
$env:JINALYS_DIARIZATION_PYTHON=(Resolve-Path speech/.venv-diarization/Scripts/python.exe).Path
$env:HF_HUB_OFFLINE='1'
$env:HF_HUB_DISABLE_TELEMETRY='1'
```
LOCAL_LLM_MODEL обязателен; URL adapter по умолчанию 127.0.0.1:11434, наш сервер Ollama работает на 11435; timeout 600 секунд относится к ОДНОМУ запросу модели. STT/DIARIZATION_MODEL_DIR — папки с настоящими весами. DIARIZATION_PYTHON — отдельный interpreter. Скрипт Ollama устанавливает OLLAMA_HOST=127.0.0.1:11435 и OLLAMA_NO_CLOUD=1. Образцы: .env.example, speech/.env.example, protocol/.env.example.

Next UI не требует env, обращается к собственному /api/meetings; прокси фиксирован на loopback:8765. Не отправлять аудио/тексты внешним cloud AI. Не публиковать job server в сеть: это локальный прототип без auth.

## 8. Порядок проверки основного сценария
1. Установить зависимости/модели и запустить три процесса.
2. Ввести название, дату совещания и IANA timezone. Неизвестную дату оставить пустой.
3. Загрузить MP3/PCM WAV до 400 МиБ и 30 минут.
4. Дождаться обработки, проверить реальные этапы, весь транскрипт, источники поручений, ответственных и сроки.
5. Для assignee=null UI показывает неизвестного ответственного; deadlineText сохраняется при неизвестной дате; needsReview требует человека. Confidence — оценка, не обещание точности.
6. Проверить многострочное саммари (ключевые исходные цитаты, не свободный пересказ), экспорт полного DOCX.
7. Повторить с RU/KK/mixed и 30-минутной записью с поручением в конце; проверить ошибку модели, повреждённый файл и превышение лимитов.

Тестовые записи: speech/tests/fixtures/{ru,kk,mixed,multi-speaker}.wav, атрибуция/ограничения в speech/tests/fixtures/README.md. Для проверки поручений нужен отдельно смоделированный сценарий с заранее известным содержанием. Демо интерфейса работает без моделей, но не подтверждает качество распознавания.

```powershell
.venv/Scripts/python -m unittest discover -s integration/tests -v
.venv/Scripts/python -m unittest discover -s protocol/tests -v
npm.cmd test
npm.cmd run build
```
Проверено без весов: 4 интеграционных теста, 25 Protocol AI тестов, 5 frontend/DOCX тестов, build, HTTP 202 → GET failed/MODEL_MISSING через Next.js. Success pipeline тесты используют doubles. Реальные модели и полная установка ML зависимостей пока не проверены на этой машине.

## Ограничения и дальнейшая проверка
Сервер повторно проверяет размер, формат, полную декодируемость и 1800 секунд через speech validator. AI: до 120000 символов/5000 реплик, части с перекрытием до двух реплик. Поздние отмены/далёкие уточнения глобально не сверяются; разные формулировки одной задачи могут остаться.

«Күтуді тоқтату» останавливает только браузерное ожидание. Server-side отмены нет. Результаты хранятся в памяти до 6 часов, исчезают при перезапуске; аудио удаляется после обработки, но после аварии возможны остатки в системном temp. Общего watchdog и постоянной очереди нет. Эти ограничения, восстановление ожидания и подробная ручная приёмка: [docs/LOCAL_RUN.md](docs/LOCAL_RUN.md).

