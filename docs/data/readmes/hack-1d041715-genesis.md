# Автопротокол совещаний HackAlem AI

Рабочий MVP для кейса Самрук-Казына: система принимает запись совещания,
формирует транскрипт по говорящим, находит поручения с ответственными и сроками,
создаёт управленческое саммари и выдаёт готовый протокол в DOCX.

## Проблема

Ручное протоколирование занимает время, а поручения, сроки и ответственные могут
теряться. Проект собирает эти данные в одном проверяемом результате и сохраняет
исходный контекст разговора.

## Что реализовано

- загрузка аудио в форматах `flac`, `m4a`, `mp3`, `mp4`, `mpeg`, `mpga`, `ogg`,
  `wav`, `webm`;
- транскрипция через OpenAI Transcriptions API;
- speaker diarization с безопасным fallback на `SPEAKER_00`;
- контекстное сопоставление speaker с именем без биометрии;
- извлечение поручений со строгой JSON-схемой и исходной цитатой;
- сохранение неизвестных ответственного и срока как `null`/«Не указано»;
- краткое управленческое саммари;
- единый объект протокола;
- презентабельный DOCX;
- минимальный web UI;
- полностью автономный demo-mode без ключа и сети.

## End-to-end сценарий

```text
audio / demo fixture
  → transcription and diarization
  → contextual speaker names
  → action items and summary
  → meeting protocol
  → DOCX
  → web UI
```

Каждый этап расположен в отдельном модуле. Если optional diarization недоступна,
API-режим пытается сохранить результат через обычную транскрипцию с одним
говорящим.

## Архитектура и технологии

- Python 3.10+;
- Flask — локальный web UI;
- OpenAI Python SDK — облачный API-режим;
- `gpt-4o-transcribe-diarize` — speaker diarization;
- `whisper-1` — совместимый резервный STT существующего модуля;
- Responses API Structured Outputs — структурированные поручения;
- `python-docx` — DOCX-экспорт;
- `unittest` — тесты без платных API-вызовов.

Модели задаются environment variables, поэтому provider можно заменить без
изменения структуры протокола.

## Структура проекта

```text
app entrypoint                 src/meeting_minutes/web.py
transcription                  src/meeting_minutes/transcription.py
diarization and fallback       src/meeting_minutes/diarization.py
speaker name inference         src/meeting_minutes/speaker_names.py
task extraction                src/meeting_minutes/task_extraction.py
summary                        src/meeting_minutes/summary.py
protocol and pipeline          src/meeting_minutes/protocol.py, pipeline.py
DOCX export                    src/meeting_minutes/export_docx.py
offline fixture                src/meeting_minutes/fixtures/demo_meeting.json
tests                          tests/
```

## Установка

```powershell
git clone https://github.com/BAITC-Hacks/hack-1d041715-genesis.git
cd hack-1d041715-genesis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`pip install -r requirements.txt` устанавливает сам пакет, поэтому ручной
`PYTHONPATH` не нужен.

## Настройка environment variables

Безопасный шаблон находится в `.env.example`:

```dotenv
APP_MODE=demo
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_TRANSCRIPTION_MODEL=whisper-1
OPENAI_DIARIZATION_MODEL=gpt-4o-transcribe-diarize
OPENAI_TEXT_MODEL=gpt-6-astra
```

`.env` исключён из Git. Настоящий ключ нельзя добавлять в репозиторий.

## Единый запуск

После установки команда одинакова для обоих режимов:

```powershell
meeting-minutes
```

Альтернативный вариант:

```powershell
python -m meeting_minutes
```

Откройте <http://127.0.0.1:5000>.

## Demo-mode без аккаунта

Оставьте `APP_MODE=demo` и не задавайте настоящий API-ключ. В UI будет явно
показана маркировка **DEMO**. Нажмите «Запустить демонстрацию» — система покажет
полный flow и позволит скачать DOCX.

Demo-mode не распознаёт аудио. Транскрипт, поручения и саммари загружаются из
открыто обозначенного тестового RU/KZ fixture. Сборка объекта протокола, web UI и
DOCX выполняются реальным кодом.

## Реальный API-режим

В `.env` задайте:

```dotenv
APP_MODE=api
OPENAI_API_KEY=ваш_ключ
```

Перезапустите приложение, загрузите MP3/WAV и нажмите «Обработать аудио».
Приложение ограничивает загрузку 25 МБ и показывает понятную ошибку вместо
Python traceback.

## Как жюри проверить проект

1. Выполнить команды раздела «Установка».
2. Убедиться, что в `.env` установлено `APP_MODE=demo`.
3. Запустить `meeting-minutes`.
4. Открыть <http://127.0.0.1:5000>.
5. Нажать «Запустить демонстрацию».
6. Проверить саммари, таблицу пяти поручений и RU/KZ транскрипт по говорящим.
7. Скачать DOCX и открыть его локально.
8. Запустить тесты командой ниже.

## Пример результата

```json
{
  "task": "Подготовить претензию поставщику",
  "assignee": "Ерлан",
  "deadline": "до конца недели",
  "speaker": "SPEAKER_00"
}
```

В demo также есть поручение без срока и поручение без указанного ответственного,
чтобы проверить отсутствие выдуманных данных.

## Тестирование

```powershell
python -m unittest discover -s tests -v
```

Тесты не обращаются к платным API. Они проверяют ошибки аудиофайла, demo STT,
формат diarization, fallback, имена speaker, поручения с `null`, фильтрацию задач
без исходной цитаты, summary, объект протокола, DOCX и web flow.

## Данные и интеграции

- Demo fixture содержит синтетический русский, казахский и смешанный RU/KZ текст.
- В API-режиме аудио и транскрипт передаются в OpenAI.
- База данных, авторизация и постоянное серверное хранение не используются.
- Загруженный файл находится только во временном каталоге на время обработки.

## Известные ограничения

1. **Нет закрытого контура.** Облачный API-режим передаёт аудио и текст внешнему
   сервису и не подходит для чувствительных данных промышленного заказчика.
2. Реальная точность русского, казахского и смешанного аудио не подтверждена на
   предоставленном корпусе — в репозитории нет реальных аудиозаписей.
3. Demo использует fixture/mock-данные и не является доказательством качества STT
   или LLM.
4. Сопоставление имён основано на контекстных фразах и не выполняет биометрическую
   идентификацию.
5. При недоступной diarization весь fallback-транскрипт относится к
   `SPEAKER_00`.
6. `whisper-1` и текущая diarization-модель объявлены к отключению 26 февраля
   2027 года; значения вынесены в конфигурацию для миграции.
7. Результаты скачивания хранятся только в памяти процесса и исчезают после
   перезапуска приложения.

## Путь к промышленному закрытому контуру

Pipeline отделён от конкретных provider-вызовов. Для on-premise развёртывания
нужно заменить облачные реализации транскрипции, diarization и анализа на
локальные/self-hosted модели, сохранить текущие структуры `TranscriptSegment`,
`ActionItem` и `MeetingProtocol`, после чего повторно проверить качество на
корпоративном RU/KZ корпусе. Текущий MVP не заявляется как on-premise решение.

## Дальнейшее развитие

- подключить локальные STT, diarization и LLM providers;
- провести оценку качества на реальных RU/KZ и mixed записях;
- добавить ручное исправление speaker-name перед экспортом;
- нормализовать относительные сроки, сохраняя исходную формулировку;
- добавить контролируемое корпоративное хранение только после согласования
  требований безопасности.

Официальные справочные страницы:
[Speech-to-Text](https://developers.openai.com/api/docs/guides/speech-to-text),
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[Deprecations](https://developers.openai.com/api/docs/deprecations).
