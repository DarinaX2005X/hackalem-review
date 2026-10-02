# QazMeeting AI

Прототип системы автопротоколирования совещаний для HackAlem AI
(владелец кейса — Самрук-Қазына).

> **Статус для жюри.** В этой ветке объединены локальный аудио/STT-модуль,
> общий контракт данных, агент протокола и материалы кейса. Локальное
> распознавание MP3/WAV с таймкодами проверено на настоящем
> `Совещание №1.mp3`. Полный сценарий с UI и экспортом DOCX ещё не проходил
> сквозную проверку; диаризация и качество поручений требуют ручной проверки.

## Какую проблему решает проект

Протоколы совещаний часто составляют вручную. В длинной или смешанной
русско-казахской речи можно пропустить поручение, перепутать исполнителя или
срок и потерять доказательство того, где решение прозвучало. Для секретаря,
руководителя и куратора поручений нужен проверяемый черновик протокола, а не
непрозрачный ответ модели.

## Целевой сценарий MVP

1. Пользователь загружает MP3 или WAV.
2. Локальный multilingual STT строит транскрипт на русском, казахском или в
   смешанной речи и сохраняет таймкоды.
3. Диаризация пытается разделить реплики по говорящим.
4. Локальный Meeting Protocol Agent извлекает поручения, ответственных и
   сроки, привязывая каждое поручение к исходной реплике.
5. Пользователь проверяет сомнительные места и получает краткое саммари.
6. UI команды экспортирует подтверждённый результат в DOCX/PDF.

Обязательные требования кейса: русский, казахский и смешанный язык,
распознавание речи, диаризация, поручение с ответственным и сроком,
управленческое саммари и экспортный протокол.

## Что проверено сейчас

| Компонент | Фактический статус |
| --- | --- |
| MP3/WAV → текст с таймкодами | Apple Silicon: MLX Whisper. Windows/Linux: faster-whisper. На Windows «Совещание №2.mp3» распознано моделью small на CPU/int8: 44 сегмента за 44,54 с (без времени загрузки модели). |
| Speaker diarization | Есть локальный адаптер и безопасный fallback. В проверенном прогоне модель была недоступна, поэтому все сегменты получили `speaker_id="UNKNOWN"`; имена говорящих не угадываются. |
| Meeting Protocol Agent | Локальная реализация Ollama, evidence-проверка, нормализация сроков, отмены и дедупликация добавлены вместе с материалами кейса. Качество зависит от модели и требует ручной проверки. |
| Материалы кейса | В `case_materials/` добавлены описание кейса, эталонные протоколы, манифест и ожидаемые поручения. MP3 и полные транскрипты не коммитятся. |
| UI и DOCX | Объединены в `main`: Streamlit, ручное редактирование и экспорт DOCX. Полный путь MP3 → DOCX с настоящими моделями пока не подтверждён. |

Отдельная строгая проверка агента на материалах совещания №2 с
`qwen3:1.7b` дала 0/5 обязательных ожиданий: единственный кандидат был
отброшен, потому что не подтвердился выбранным evidence. Это ограничение
зафиксировано намеренно: неподтверждённое поручение не выдаётся за факт.

## Приватность и API-ключи

Финальный путь обработки проектируется для закрытого контура: аудио и текст
совещания обрабатываются локально и не отправляются во внешние AI API. Ключи
OpenAI и NVIDIA не нужны для локального MVP и не должны попадать в Git.

Ссылка NVIDIA Brev предоставляет биллинг/GPU-кредиты, а не ключ inference.
Для NVIDIA API Catalog нужен отдельный `NVIDIA_API_KEY`; в этой ветке нет
непроверенного NVIDIA-STT backend.

В репозитории есть отдельный opt-in smoke test OpenAI. Он отправляет выбранный
файл наружу только при явном флаге `--allow-cloud-upload` и предназначен для
отдельной проверки, а не для закрытого контура. Ранее тестовый запрос получил
HTTP 429, поэтому успешный облачный результат не заявляется.

Никогда не коммитьте:

- `OPENAI_API_KEY`, `NVIDIA_API_KEY`, `HF_TOKEN` и любые другие токены;
- реальные чувствительные аудиозаписи;
- скачанные модели и полные транскрипты.

Если ключ уже публиковался в чате или логе, его следует немедленно отозвать и
создать новый.

## Архитектура

```text
Audio MP3/WAV
      |
      v
Local Audio / STT (faster-whisper on Windows/Linux, MLX on Apple Silicon)
  - preprocessing
  - multilingual transcription
  - timestamps
      |
      v
Local diarization (pyannote, optional)
  - speaker segments
  - merge with transcript
      |
      v
MeetingProtocolAgent (Ollama, local)
  - speaker resolution
  - task extraction
  - deadline normalization
  - evidence validation
  - summary
      |
      v
MeetingResult (Pydantic)
      |
      +--> Streamlit UI
      +--> DOCX export
```

Если диаризация недоступна, транскрипция сохраняется, выдаётся предупреждение
и используется `speaker_id="UNKNOWN"`. `UNKNOWN` не означает установленную
личность.

## Структура репозитория

```text
app/
├── agents/meeting_agent.py
├── models/schemas.py
├── services/audio.py
├── services/audio_cloud.py
└── config.py
case_materials/
├── expected/              # ожидаемые поручения без аудио
├── source/                # описание кейса и reference DOCX
└── manifest.json
scripts/
├── smoke_audio.py
├── smoke_audio_cloud.py
└── evaluate_agent.py
tests/
requirements.txt
requirements-audio.txt
requirements-agent.txt
README.md
```

## Единый контракт данных

Все ветки используют модели из `app/models/schemas.py`; дубликаты схем не
создаются и публичные поля не меняются.

```python
# feature/audio
from app.services.audio import process_audio
segments = process_audio("/path/to/meeting.mp3")
# process_audio(audio_path: str) -> list[TranscriptSegment]

# feature/agent
from app.agents import MeetingProtocolAgent
result = MeetingProtocolAgent().run(transcript, meeting_date, title)

# feature/ui
build_docx(result: MeetingResult) -> bytes
```

Точная точка импорта аудио для UI и агента: `app.services.audio.process_audio`.
Результат использует именно `TranscriptSegment` из
`app/models/schemas.py` и содержит `id`, `start`, `end`, `speaker_id` и `text`.
`speaker_name` и `language` заполняются только при достоверном источнике.

## Установка

Нужен Python 3.11 (допускается 3.12).

```bash
git clone https://github.com/BAITC-Hacks/hack-4649b58f-flame.git
cd hack-4649b58f-flame
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-audio.txt
```

Первый запуск загрузит multilingual Whisper в локальный кэш: `small` для
Windows/Linux, MLX small для Apple Silicon. Модель можно
заменить через `AUDIO_STT_MODEL`. Без заранее известного языка не задавайте
`AUDIO_LANGUAGE`: Whisper сам определит режим multilingual-распознавания.

Для локальной диаризации установите `pip install -r requirements-diarization.txt`.
Нужна модель
`pyannote/speaker-diarization-community-1`. Её условия принимаются в Hugging
Face один раз; токен задаётся только через окружение `HF_TOKEN` или локальный
путь `AUDIO_DIARIZATION_MODEL`. Если модель недоступна, срабатывает fallback
`UNKNOWN`, а текст не теряется.

## Streamlit UI и DOCX

Для запуска интерфейса под Windows:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-ui.txt -r requirements-audio.txt
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Для анализа транскрипта установите Ollama с официального сайта и в отдельном
терминале запустите:

```powershell
ollama pull qwen2.5:3b-instruct-q4_K_M
ollama serve
```

Если Ollama уже запущена приложением, второй `serve` не нужен. Рекомендуемые
параметры для 16 GB RAM / RTX 3050 6 GB (задайте в терминале запуска UI):

```powershell
$env:AUDIO_STT_BACKEND = "auto"
$env:AUDIO_STT_DEVICE = "cpu"
$env:AUDIO_STT_COMPUTE_TYPE = "int8"
$env:OLLAMA_NUM_CTX = "8192"
$env:OLLAMA_TIMEOUT_SECONDS = "180"
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

После установки зависимостей можно запускать всё одной командой:

```powershell
.\scripts\start_windows.ps1
# Для portable Ollama:
.\scripts\start_windows.ps1 -OllamaPath "C:\path\to\ollama.exe"
```

Скрипт проверяет локальную Ollama, при необходимости запускает её в фоне,
скачивает выбранную модель и открывает Streamlit. Служебная папка `.ollama`
создаётся Ollama в профиле пользователя; если доступ запрещён, запуск нужно
выполнить из обычного пользовательского терминала. Никакие секреты скрипт не
записывает в репозиторий.

Demo-режим использует явно помеченные синтетические данные. В локальном режиме
UI вызывает `app.services.audio.process_audio`, затем `MeetingProtocolAgent.run`.
Перед экспортом DOCX можно исправить имена говорящих, исполнителей и сроки.

На Windows выбран CPU/int8, чтобы не требовать ручной установки CUDA/cuDNN;
NVIDIA остаётся доступна Ollama. При установленных CUDA-библиотеках можно явно
выбрать `AUDIO_STT_DEVICE=cuda` и `AUDIO_STT_COMPUTE_TYPE=float16`.
Запуск demo не является проверкой настоящих моделей. При недоступной диаризации
сохраняется текст с `UNKNOWN`; при недоступной Ollama — транскрипт и предупреждение.
`.env.example` — образец: параметры задаются через окружение, `.env` автоматически
не загружается. Исходное аудио не отправляется во внешние AI API.

## Smoke test аудио

Аудио должно находиться вне Git (например, в `~/Downloads`).

```bash
python scripts/smoke_audio.py "/path/to/Совещание №1.mp3" \
  --limit 8 --output output/meeting_1_transcript.json
```

Скрипт печатает время обработки, количество сегментов, speaker id и несколько
реплик с таймкодами. Каталог `output/` игнорируется Git.

## Локальный агент и материалы кейса

Агент обращается только к `127.0.0.1`/`localhost` через Ollama и проверяет
каждое поручение по существующему `segment_id`. Evidence и таймкоды берутся из
исходных сегментов, а не придумываются моделью. Невалидные ответы, несуществующие
сегменты и неподтверждённые задачи отбрасываются.

```bash
pip install -r requirements-agent.txt
ollama pull qwen2.5:3b-instruct-q4_K_M
ollama serve
export OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M

python scripts/evaluate_agent.py \
  /path/to/meeting_2_transcript.json \
  case_materials/expected/meeting_2.json \
  --meeting-date 2026-09-23 \
  --title "Совещание №2" \
  --timeout 300
```

В `case_materials/source/` находятся предоставленные описание кейса и
эталонные DOCX. MP3 остаются во внешнем хранилище; JSON-транскрипты для
локальной оценки создаются отдельно и не добавляются в Git.

## Отдельный облачный smoke test (не часть MVP)

Команда ниже допустима только для аудио, передачу которого явно разрешили:

```bash
export OPENAI_API_KEY="<ключ из окружения, не из Git>"
python scripts/smoke_audio_cloud.py "/path/to/meeting.mp3" \
  --allow-cloud-upload --limit 8 --output output/cloud_transcript.json
```

Без `--allow-cloud-upload` аудио не отправляется. Публичный
`process_audio(...)` и обычный локальный smoke test облачных вызовов не делают.

## Проверка

```bash
python -m pytest -q
```

Тесты проверяют общий Pydantic-контракт, конфигурацию, аудио-обработку,
облачный opt-in транспорт, evidence-валидацию агента, fallback и совместимость
ответов Ollama/MLX. Unit-тесты не заменяют оценку качества STT, диаризации,
агента или экспорта.

## Ветки команды и ограничения

- `feature/audio` — локальный STT, таймкоды и fallback диаризации;
- `feature/agent` — локальный агент, извлечение и проверка поручений;
- `feature/ui` — Streamlit и DOCX-интеграция;
- `main` — общий контракт и интеграционная база.

Пока не реализованы production-интеграции с Teams/Zoom/Google Meet и СЭД,
голосовая биометрическая идентификация и развёрнутая версия сервиса. До
демонстрации полного MVP нужно отдельно прогнать русский, казахский и
смешанный аудиоматериал по пути **MP3 → транскрипт → говорящие → поручения →
саммари → DOCX** и провести ручную проверку результата.
