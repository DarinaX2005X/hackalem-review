# Qoryt / SuperPuperNovaID

Прототип системы автопротоколирования совещаний: загрузка записи, распознавание речи,
разделение говорящих, подготовка стенограммы, выделение решений и поручений,
экспорт протокола в DOCX/PDF и сохранение его версий.

Бэкенд — **модульный монолит FastAPI**, интерфейс — **React + TypeScript + Vite + Bootstrap 5**.
Длительная обработка выполняется в **Celery**, очередь — **Redis**, данные — **PostgreSQL**.
API и worker используют один Python-код и один образ. ИИ-анализ построен на **OpenAI Agents SDK**.
Текущий облачный сценарий использует **NVIDIA для речи** и **OpenAI для текста**.

> Без настройки ключей приложение запускается, но полный анализ совещания недоступен.
> `AI_MODE=mock` относится только к отдельному демонстрационному `/jobs` API.
> Он не подменяет распознавание и анализ совещания тестовыми результатами.

## Содержание

- [Как работает проект](#как-работает-проект)
- [Модули и структура](#модули-и-структура)
- [Быстрый запуск через Docker](#быстрый-запуск-через-docker)
- [Настройка .env](#настройка-env)
- [Работа с совещанием через API](#работа-с-совещанием-через-api)
- [Ежедневная разработка](#ежедневная-разработка)
- [Запуск Python и React вне Docker](#запуск-python-и-react-вне-docker)
- [Хранение, версии и напоминания](#хранение-версии-и-напоминания)
- [Ограничения и диагностика](#ограничения-и-диагностика)
- [Дополнительная документация](#дополнительная-документация)

## Как работает проект

```text
React → FastAPI → PostgreSQL (совещание и состояние обработки)
           │
           ├─ загрузка записи → общее файловое хранилище
           │
           └─ запуск обработки → Redis → Celery worker
                                           │
                                  FFmpeg: нормализация аудио
                                           ↓
                                  ASR + diarization
                                  текст + метки говорящих
                                           ↓
                                  Canonicalization
                                  нормализованная стенограмма
                                           ↓
                                  Speaker resolution
                                  сопоставление говорящих участникам
                                           ↓
                                  Extraction → Resolver → Summary → Review
                                  поручения, решения, краткое содержание
                                           ↓
                                  MeetingProtocol → DOCX / PDF
                                           ↓
                                  сохранённая версия протокола
```

Порядком этапов управляет обычный Python-сервис `MeetingProcessingService`.
В очередь передаются идентификаторы, а не содержимое аудио или стенограммы.
Результаты этапов сохраняются и могут повторно использоваться при следующем запуске.
Экспорт строится из сохранённых данных и сам не вызывает ИИ.

У запуска обработки состояния `queued → running → completed / failed`.
Поле `stage` показывает текущий этап: `preprocessing`, `transcribing`, `diarizing`,
`canonicalizing`, `resolving_speakers`, `analyzing`, `exporting`.
У самой встречи успешное финальное состояние называется `ready`.

## Модули и структура

Все пути модулей ниже находятся в `backend/src/app/`.

| Модуль | Ответственность |
| --- | --- |
| `meetings/` | Совещания, участники, стенограмма и представление прогресса для UI |
| `media/` | Загрузка, проверка формата через ffprobe, оригинальные файлы и их метаданные |
| `audio/` | Нормализация через FFmpeg: по умолчанию WAV, PCM16, 16 кГц, mono |
| `speech/` | ASR, diarization и `AttributedTranscript` с таймкодами и speaker ID |
| `canonicalization/` | `CanonicalTranscript`: исходный текст сохраняется рядом с обработанным |
| `intelligence/` | Сопоставление участников, извлечение поручений, согласование результатов, summary и review |
| `processing/` | Общий pipeline, очередь, сохранённое состояние текущей попытки и обработка ошибок |
| `tasks/` | Поручения, ответственные, сроки и статусы выполнения |
| `protocols/` | Сборка `MeetingProtocol`, DOCX/PDF, неизменяемые снимки версий |
| `notifications/` | Внутренние напоминания о приближении срока и просрочке, без отправки почты |
| `domain/`, `application/` | Сущности, сценарии и порты первоначального demo jobs API |
| `infrastructure/` | Подключения к БД, Celery, demo-агентам; подготовленные адаптеры SMTP/S3 |
| `entrypoints/` | Сборка HTTP API и регистрация Celery-задач |
| `config.py`, `bootstrap.py` | Настройки и связывание зависимостей |

```text
backend/
  src/app/             # модули выше
  migrations/          # Alembic, включая 0010: версии протоколов и напоминания
  tests/               # модульные, контрактные и опциональные интеграционные проверки
  pyproject.toml       # зависимости Python
  uv.lock              # зафиксированные версии зависимостей
frontend/
  src/
    components/layout/ # оболочка приложения
    components/ui/     # общие компоненты
    features/meetings/ # создание и рабочая область совещания
    features/tasks/    # доска поручений
    features/jobs/     # первоначальный demo-экран агентов
    lib/               # HTTP-клиент
  package-lock.json
compose.infra.yaml     # PostgreSQL, Redis; опционально MinIO и Mailpit
compose.yaml           # API, worker, миграции, frontend; включает инфраструктуру
compose.dev.yaml       # исходники с хоста, Uvicorn reload и Vite HMR
.env.example           # шаблон настроек без секретов
Makefile               # сокращения для команд Docker и проверок
docs/                  # подробные контракты и ограничения модулей
```

Бизнес-правила располагаются в сервисах модулей; HTTP-роуты и Celery-задачи вызывают
эти сервисы. Внешние провайдеры подключаются через адаптеры. API и worker — разные
процессы одного монолита, а не независимые микросервисы.

## Быстрый запуск через Docker

Нужны Git и работающий Docker Desktop / Docker Engine с **Compose 2.24.4+**.
Установка Python, Node.js и моделей на хост для облачного Docker-сценария не требуется.
Все команды выполняются из корня репозитория.

### 1. Получить проект и создать настройки

```sh
git clone https://github.com/BAITC-Hacks/hack-64cc2b8c-superpupernovaid.git
cd hack-64cc2b8c-superpupernovaid
```

Скопируйте `.env.example` в `.env`, **только если `.env` ещё не существует**.

macOS / Linux / Git Bash:

```sh
test -f .env || cp .env.example .env
```

Windows PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Для полного pipeline заполните ключи и включите этапы по примеру в следующем разделе.
Без этого можно проверить запуск API/UI и загрузку файлов, но не полный ИИ-анализ.

### 2. Собрать и запустить режим разработки

```sh
docker compose -f compose.yaml -f compose.dev.yaml build backend frontend
docker compose -f compose.yaml -f compose.dev.yaml up -d --no-build --wait backend worker frontend
```

Эквивалент при установленном `make`: `make setup-dev`.
При старте сервис `migrate` применяет миграции; затем запускаются API и worker.
Первая сборка загружает зависимости. При последующих стартах достаточно `make dev`
или второй команды выше: повторная сборка не нужна.

| Что открыть | Адрес |
| --- | --- |
| React в режиме разработки | http://localhost:5173 |
| Swagger: интерактивная документация всех API | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Проверка API | http://localhost:8000/api/v1/health |
| Готовность PostgreSQL и Redis | http://localhost:8000/api/v1/ready |

### 3. Упакованный режим для демонстрации

Здесь исходники входят в образы, а frontend раздаётся через nginx:

```sh
docker compose build backend frontend
docker compose up -d --no-build --wait backend worker frontend
```

Эквивалент: `make build`, затем `make up`. Интерфейс: **http://localhost:8080**.
Dev и упакованный режим используют один Compose project и одни volumes: это
альтернативные режимы, не два одновременно работающих окружения.

## Настройка .env

`.env` содержит локальные настройки и секреты, исключён из Git и не приходит через
`git pull`. Каждый разработчик создаёт его самостоятельно. Шаблон — `.env.example`,
источник значений по умолчанию — `backend/src/app/config.py`.
Ключи должны находиться только на бэкенде: не помещайте их в `VITE_*`.

### Минимальные изменения для облачного pipeline

Добавьте или замените эти строки в копии `.env.example`, без дублирования имён:

```dotenv
# Первоначальный demo jobs API; основной pipeline имеет отдельные флаги ниже.
AI_MODE=openai
OPENAI_API_KEY=replace-with-your-openai-key
OPENAI_MODEL=gpt-4.1-mini

# Распознавание речи и разделение говорящих в NVIDIA cloud.
SPEECH_ENABLED=true
ASR_PROVIDER=nvidia
DIARIZATION_PROVIDER=nvidia
NVIDIA_API_KEY=replace-with-your-nvidia-key
NVIDIA_LANGUAGE_CODE=ru-RU

# Обработка стенограммы через OpenAI.
TRANSCRIPT_CANONICALIZATION_ENABLED=true
TRANSCRIPT_CANONICALIZATION_MODEL=gpt-4.1-mini
TRANSCRIPT_CANONICAL_LANGUAGE=ru

# Все пять моделей необходимо задать явно.
MEETING_INTELLIGENCE_ENABLED=true
MEETING_SPEAKER_RESOLUTION_MODEL=gpt-4.1-mini
MEETING_EXTRACTION_MODEL=gpt-4.1-mini
MEETING_RESOLVER_MODEL=gpt-4.1-mini
MEETING_SUMMARY_MODEL=gpt-4.1-mini
MEETING_REVIEW_MODEL=gpt-4.1-mini
MEETING_TRACING_ENABLED=false
```

Имена моделей в примере соответствуют стартовой конфигурации проекта; доступ к ним
должен быть у вашего OpenAI-проекта. `OPENAI_MODEL` не заменяет настройки моделей
канонизации и анализа. Переменная `API_KEY` не распознаётся: нужна **`OPENAI_API_KEY`**.
`NVIDIA_API_KEY` — отдельный ключ другого провайдера.

После изменения `.env` пересоздайте процессы, чтобы они получили новые значения:

```sh
docker compose -f compose.yaml -f compose.dev.yaml up -d --no-build --no-deps --force-recreate backend worker
```

Для упакованного режима уберите `-f compose.yaml -f compose.dev.yaml`.
Если включён планировщик `reminders`, пересоздайте и его. Обычный `restart` новые
переменные контейнера не загружает; пересборка образа для изменения `.env` не нужна.

### Подключения и базовые настройки

В таблицах указаны значения шаблона/настроек по умолчанию; «пусто» означает, что
значение нужно задать при включении соответствующей функции.

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `AI_MODE` | `mock` | `mock` или `openai` только для demo jobs API |
| `OPENAI_API_KEY` | пусто | Ключ OpenAI для канонизации, анализа и demo в режиме openai |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Модель demo-агента |
| `AGENT_TIMEOUT_SECONDS` | `120` | Таймаут demo-задания, секунды |
| `DATABASE_URL` | `postgresql+psycopg://app:app@localhost:5432/app` | URL SQLAlchemy; для БД из Compose при запуске Python на хосте замените порт на **5332** |
| `REDIS_URL` | `redis://localhost:6379/0` | Брокер Celery |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:8080"]` | Разрешённые origin, JSON-массив |
| `API_PROXY_TARGET` | `http://localhost:8000` | Настройка Vite, не FastAPI; dev Compose передаёт `http://backend:8000` |

Compose передаёт корневой `.env` в Python-контейнеры и **переопределяет** `DATABASE_URL`,
`REDIS_URL`, `MEDIA_UPLOAD_DIR`, `S3_ENDPOINT_URL`, `SMTP_HOST` внутренними адресами.
Поэтому `localhost:5332` нужен только Python-процессу на хосте; внутри Docker БД —
`postgres:5432`. Изменение этих пяти строк только в `.env` не меняет значения внутри
контейнеров: для внешней БД/SMTP/S3 потребуется также изменить Compose override.

### Загрузка и подготовка аудио

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `MEDIA_MAX_FILE_SIZE_BYTES` | `5368709120` | Максимум оригинального файла, 5 ГиБ |
| `MEDIA_ALLOWED_FORMATS` | `["wav","mp3","flac","ogg","mov","matroska"]` | Семейства demuxer ffprobe, не расширения файлов |
| `MEDIA_UPLOAD_DIR` | `./data/media` в шаблоне | Каталог файлов; в Docker `/data/media`, относительный путь настроек считается от `backend/` |
| `MEDIA_FFPROBE_TIMEOUT_SECONDS` | `15` | Таймаут проверки файла |
| `MEDIA_FFPROBE_EXECUTABLE` | `ffprobe` | Путь или имя бинарника |
| `MEDIA_MAX_CONCURRENT_UPLOADS` | `2` | Одновременные загрузки на процесс API |
| `AUDIO_MAX_CONCURRENT_PROCESSES` | `1` | Одновременные конвертации на процесс |
| `AUDIO_TARGET_SAMPLE_RATE` | `16000` | Частота дискретизации, Гц |
| `AUDIO_TARGET_CHANNELS` | `1` | Число каналов |
| `AUDIO_TARGET_CODEC` | `pcm_s16le` | Кодек нормализованного аудио |
| `AUDIO_TARGET_FORMAT` | `wav` | Контейнер; поддержана также согласованная пара FLAC/flac |
| `AUDIO_FFMPEG_TIMEOUT_SECONDS` | `900` | Таймаут FFmpeg |
| `AUDIO_FFMPEG_EXECUTABLE` | `ffmpeg` | Путь или имя бинарника |

Лимит загрузки не равен лимиту провайдера распознавания. Например, допустимый для
загрузки MP3 может после преобразования превысить предел NVIDIA в 16 МиБ WAV.
При превышении локальной параллельности API возвращает `429` с `Retry-After`.

### Распознавание и diarization

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `SPEECH_ENABLED` | `false` | Включить обработку речи |
| `ASR_PROVIDER` | `nemo` | `nemo`, `whisper` или `nvidia` |
| `DIARIZATION_PROVIDER` | `nemo` | `nemo`, `pyannote` или `nvidia`; облачный сценарий использует пару nvidia/nvidia |
| `NVIDIA_API_KEY` | пусто | Ключ NVIDIA cloud |
| `NVIDIA_ASR_FUNCTION_ID` | `71203149-d3b7-4460-8231-1be2543a1fca` | ID облачной функции речи |
| `NVIDIA_LANGUAGE_CODE` | `ru-RU` | Язык текущего облачного сценария |
| `NVIDIA_MAX_AUDIO_BYTES` | `16777216` | Максимум нормализованного аудио, не более 16 МиБ |
| `NVIDIA_REQUEST_TIMEOUT_SECONDS` | `180` | Таймаут облачного запроса |
| `NEMO_ASR_MODEL` | пусто | Локальная модель ASR NeMo |
| `NEMO_DIARIZATION_MODEL` | пусто | Локальный checkpoint Sortformer `.nemo` |
| `NEMO_DEVICE` | `cuda` | `cpu` или `cuda` |
| `WHISPER_MODEL` | `large-v3` | При включении замените абсолютным путём к локальной CTranslate2-модели |
| `WHISPER_DEVICE` | `cuda` | `cpu` или `cuda` |
| `WHISPER_COMPUTE_TYPE` | `default` | `default`, `float16`, `float32`, `int8` |
| `PYANNOTE_MODEL` | пусто | Абсолютный путь к локальной community-1 |
| `PYANNOTE_DEVICE` | `cuda` | `cpu` или `cuda` |
| `SPEECH_MAX_DURATION_SECONDS` | `14400` | Общий предел длительности, 4 часа; предел провайдера может быть ниже |
| `SPEECH_DIARIZATION_MAX_DECODED_BYTES` | `536870912` | Лимит декодированного аудио для локальной diarization |
| `SPEECH_MODEL_REVISION` | `1` | Версия кэша; увеличивайте при замене весов/runtime |

Локальные ML-провайдеры требуют отдельной установки зависимостей, весов и ресурсов.
Базовый Docker-образ с лимитом API 1 ГиБ не является готовым GPU-окружением.
Подробнее: [Speech](docs/speech-processing.md), [NVIDIA cloud](docs/nvidia-cloud-speech.md).

### Канонизация стенограммы

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `TRANSCRIPT_CANONICALIZATION_ENABLED` | `false` | Включить этап |
| `TRANSCRIPT_CANONICALIZATION_MODEL` | пусто | Отдельно заданная модель OpenAI |
| `TRANSCRIPT_CANONICAL_LANGUAGE` | `ru` | Язык обработанного текста |
| `CANONICALIZATION_BATCH_MAX_SEGMENTS` | `50` | Сегментов в пакете |
| `CANONICALIZATION_BATCH_MAX_BYTES` | `12000` | Бюджет UTF-8 JSON входа, включая контекст и ID; не токены |
| `CANONICALIZATION_CONTEXT_SEGMENTS` | `2` | Сегментов соседнего контекста |
| `CANONICALIZATION_MAX_CONCURRENCY` | `3` | Параллельные запросы |
| `CANONICALIZATION_REQUEST_TIMEOUT_SECONDS` | `60` | Таймаут запроса |
| `CANONICALIZATION_MAX_ATTEMPTS` | `3` | Максимум попыток |
| `CANONICALIZATION_RETRY_BASE_SECONDS` | `0.5` | База задержки повторов |
| `CANONICALIZATION_MAX_OUTPUT_TOKENS` | `4096` | Лимит ответа модели |

### Анализ совещания

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `MEETING_INTELLIGENCE_ENABLED` | `false` | Включить анализ |
| `MEETING_SPEAKER_RESOLUTION_MODEL` | пусто | Сопоставление speaker ID участникам |
| `MEETING_EXTRACTION_MODEL` | пусто | Извлечение поручений и решений |
| `MEETING_RESOLVER_MODEL` | пусто | Согласование результатов извлечения |
| `MEETING_SUMMARY_MODEL` | пусто | Краткое содержание |
| `MEETING_REVIEW_MODEL` | пусто | Проверка результата |
| `SPEAKER_RESOLUTION_MAX_CONTEXT_SEGMENTS` | `60` | Контекст определения участников |
| `MEETING_CHUNK_MAX_SEGMENTS` | `50` | Сегментов в части стенограммы |
| `MEETING_CHUNK_MAX_BYTES` | `24000` | Бюджет части в байтах |
| `MEETING_CHUNK_OVERLAP_SEGMENTS` | `3` | Перекрытие частей |
| `MEETING_AGENT_MAX_INPUT_BYTES` | `120000` | Максимум входа агента |
| `MEETING_MAX_OUTPUT_TOKENS` | `8192` | Лимит ответа модели |
| `AGENT_MAX_CONCURRENCY` | `3` | Параллельные агентные вызовы |
| `AGENT_MAX_REVIEW_ITERATIONS` | `1` | Поддерживается одна итерация review |
| `MEETING_AGENT_MAX_ATTEMPTS` | `3` | Максимум попыток вызова |
| `MEETING_AGENT_RETRY_BASE_SECONDS` | `0.5` | База задержки повторов |
| `MEETING_TRACING_ENABLED` | `true` | SDK tracing; в облачном примере выше явно выключен |

### Экспорт

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `PROTOCOL_TRANSCRIPT_TEXT_MODE` | `canonical` | `canonical` или `original` в экспортируемой стенограмме |
| `PROTOCOL_PDF_FONT_PATH` | `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` | Основной Unicode-шрифт PDF |
| `PROTOCOL_PDF_BOLD_FONT_PATH` | `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` | Полужирный шрифт PDF |
| `PROTOCOL_EXPORT_MAX_CHARACTERS` | `2000000` | Лимит текста протокола |
| `PROTOCOL_EXPORT_MAX_BYTES` | `52428800` | Максимум файла экспорта, 50 МиБ |

Шрифты установлены в Docker-образе. Для локального запуска задайте существующие
пути к обоим TTF-файлам на своей машине.

### Подготовленные настройки S3 и SMTP

Эти адаптеры не подключены к основному хранению записей и доставке напоминаний.
Для стандартного запуска менять их не требуется.

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `S3_ENDPOINT_URL` | `http://localhost:9000` | Endpoint S3; Compose заменяет на `http://minio:9000` |
| `S3_ACCESS_KEY` | `minioadmin` | Ключ локального MinIO |
| `S3_SECRET_KEY` | `minioadmin` | Секрет локального MinIO |
| `S3_BUCKET` | `prototype` | Bucket, создаётся отдельно |
| `SMTP_HOST` | `localhost` | SMTP-сервер; Compose заменяет на `mailpit` |
| `SMTP_PORT` | `1025` | SMTP-порт |
| `SMTP_FROM` | `noreply@example.test` | Отправитель |
| `SMTP_USER` | пусто | Логин, если требуется |
| `SMTP_PASSWORD` | пусто | Пароль, если требуется |
| `SMTP_STARTTLS` | `false` | Включение STARTTLS |

`AGENT_TIMEOUT_SECONDS`, SMTP-аутентификация и `API_PROXY_TARGET` не перечислены
в текущем `.env.example`, но поддерживаются кодом. Vite получает `API_PROXY_TARGET`
из окружения своего процесса; корневой `.env` автоматически ему не передаётся.

## Работа с совещанием через API

Swagger — независимый от готовности frontend способ пройти весь сценарий.
Используйте `language_hint=ru` для текущего NVIDIA pipeline.

1. Создайте встречу: `POST /api/v1/meetings`.
2. Загрузите аудио/видео: `POST /api/v1/meetings/{id}/media`, multipart-поле `file`.
3. Запустите общий pipeline: `POST /api/v1/meetings/{id}/process`.
4. Опрашивайте `GET /api/v1/meetings/{id}/processing-run` до `completed` или `failed`.
5. Получите результат и скачайте DOCX/PDF.

Пример тела создания встречи:

```json
{
  "title": "Рабочее совещание",
  "language_hint": "ru",
  "expected_participant_count": 3,
  "recording_consent_confirmed": true
}
```

`recording_consent_confirmed` устанавливается при подтверждённом согласии на запись.
Используйте возвращённый `id`: произвольный UUID не создаёт встречу автоматически.
В запрос обработки подставьте `id` загруженного MediaAsset:

```json
{
  "media_id": "UUID_ИЗ_ОТВЕТА_ЗАГРУЗКИ",
  "export_formats": ["docx", "pdf"]
}
```

| Метод и путь | Результат |
| --- | --- |
| `GET /api/v1/meetings` | Сохранённые совещания |
| `GET /api/v1/meetings/{id}/processing-run` | Текущая попытка, этапы и ошибка |
| `GET /api/v1/meetings/{id}/result` | Сохранённый результат анализа |
| `GET /api/v1/meetings/{id}/transcript` | Сегменты стенограммы |
| `GET /api/v1/meetings/{id}/exports/docx` | Текущий протокол DOCX |
| `GET /api/v1/meetings/{id}/exports/pdf` | Текущий протокол PDF |
| `GET /api/v1/meetings/{id}/protocol-versions` | История версий |
| `GET /api/v1/meetings/{id}/protocol-versions/{version_id}/exports/pdf` | PDF конкретной версии; также доступен `docx` |

Повторный POST обработки может вернуть существующий запуск. После ошибки следующий
POST создаёт новую попытку, используя сохранённые артефакты. `"refresh": true` создаёт
новую попытку завершённого запуска, но не означает принудительный сброс всех кэшей.
Не запускайте отдельные endpoints стадий параллельно с общим pipeline одной встречи.

Frontend содержит экраны встреч и поручений; подключение всех новых backend endpoints
ведётся отдельно. Наличие API истории/напоминаний не означает наличие соответствующего
экрана в текущей версии UI. Контракты: [backend/UI](docs/backend-ui-contract.md),
[общая обработка](docs/meeting-processing.md).

## Ежедневная разработка

| Задача | Команда |
| --- | --- |
| Первый запуск dev | `make setup-dev` |
| Следующий запуск без сборки | `make dev` |
| Только PostgreSQL и Redis | `make infra` |
| Логи API, worker и frontend | `make logs` |
| Перезапуск worker после изменения Python-кода | `make restart-worker` |
| Применить миграции к работающей БД | `make migrate` |
| Пересобрать после изменения зависимостей / Dockerfile | `make rebuild-dev` |
| Остановить API, worker и frontend, оставить инфраструктуру | `make stop-app` |
| Остановить весь стек | `make down` |

Uvicorn и Vite автоматически подхватывают изменения исходников. Celery worker требует
перезапуска. Если включён `reminders`, `make stop-app` его не останавливает — остановите
его отдельно. Команды Makefile — сокращения для Compose; Windows может использовать
прямые команды из раздела запуска без установки `make`.

После обновления кода через `git pull` проверьте новые строки `.env.example`.
В dev при неизменных зависимостях достаточно применить миграции и перезапустить worker:

```sh
docker compose -f compose.yaml -f compose.dev.yaml run --rm --no-deps migrate
docker compose -f compose.yaml -f compose.dev.yaml restart worker
```

Здесь PostgreSQL уже должен работать. При изменении зависимостей используйте
`make rebuild-dev`; в упакованном режиме любые изменения исходников требуют сборки.

Команды для разработчика, когда нужны проверки:

```sh
cd backend
uv sync --frozen
uv run ruff check .
uv run pytest
```

Из `frontend/`: `npm ci`, затем `npm run build`. Обычные проверки используют подменённые
внешние адаптеры; live/GPU/benchmark проверки требуют отдельной настройки.
Список маркеров находится в `backend/pyproject.toml`.

## Запуск Python и React вне Docker

Потребуются **Python 3.12–3.14**, **uv**, **Node.js 22.12+**, npm, FFmpeg/ffprobe
и Unicode-шрифты для PDF. БД и Redis можно оставить в Docker:

```sh
docker compose -f compose.infra.yaml up -d postgres redis
```

В корневом `.env` для этого режима задайте:

```dotenv
DATABASE_URL=postgresql+psycopg://app:app@localhost:5332/app
REDIS_URL=redis://localhost:6379/0
```

Также настройте пути `PROTOCOL_PDF_FONT_PATH` и `PROTOCOL_PDF_BOLD_FONT_PATH`.
Настройки Python по умолчанию ищут файл `backend/.env`; чтобы использовать единый
корневой файл, явно передавайте его через `uv run --env-file ../.env`.

Терминал API, из корня проекта:

```sh
cd backend
uv sync --frozen
uv run --env-file ../.env alembic upgrade head
uv run --env-file ../.env uvicorn app.entrypoints.api:app --reload
```

Терминал worker, из `backend/`:

```sh
uv run --env-file ../.env celery -A app.infrastructure.queue:celery_app worker --loglevel=info --pool=solo
```

`solo` удобен для локального запуска, в том числе на macOS. Основной проверяемый
способ запуска worker — Linux-контейнер с prefork и `--concurrency=1`.

Терминал frontend, из `frontend/`:

```sh
npm ci
npm run dev
```

Vite проксирует `/api` на `localhost:8000`; браузер открывайте на `localhost:5173`.

## Хранение, версии и напоминания

PostgreSQL хранит встречи, участников, метаданные записей, стенограммы, результаты
анализа, поручения, состояние текущего запуска, версии протоколов и напоминания.
Оригиналы, нормализованное аудио и экспорты хранятся в общем volume `media-data`.
API и worker должны видеть одно и то же файловое хранилище.

`docker compose down` сохраняет named volumes. **`docker compose down -v` удаляет
данные volumes**, поэтому не используйте его как обычную команду перезапуска.
Для резервной копии нужны и PostgreSQL, и файловое хранилище.

При экспорте сохраняется снимок `MeetingProtocol`. Одинаковое содержимое использует
одну версию; изменения создают новую. Старый снимок не перезаписывается.
Исходное выражение срока («до пятницы») сохраняется рядом с уточнённой датой.
Файлы, созданные до миграции `0010`, не получают исторический снимок задним числом.

Напоминания создаются для актуальных незавершённых поручений с точным `due_at`:
за 24 часа до срока и после просрочки. Это записи внутренней ленты, **не email**.
Проверка вручную: `POST /api/v1/notifications/scan`; просмотр:
`GET /api/v1/notifications`; прочтение: `POST /api/v1/notifications/{id}/read`.

Для автоматической проверки раз в 5 минут включите один Celery Beat при уже работающем
основном dev-стеке:

```sh
docker compose -f compose.yaml -f compose.dev.yaml --profile reminders up -d --no-build --no-deps reminders
```

Остановка планировщика:

```sh
docker compose -f compose.yaml -f compose.dev.yaml --profile reminders stop reminders
```

Для упакованного режима уберите два `-f`. SMTP настраивать не нужно.
Подробности: [версии и напоминания](docs/protocol-history-reminders.md).

MinIO и Mailpit доступны опционально:

```sh
docker compose --profile storage --profile mail up -d minio mailpit
```

MinIO: API `localhost:9000`, консоль `localhost:9001`, локальные учётные данные
`minioadmin` / `minioadmin`; bucket `prototype` создаётся отдельно.
Mailpit: SMTP `localhost:1025`, просмотр писем `localhost:8025`.
Запуск этих сервисов сам по себе не переключает media storage на S3 и не включает
отправку напоминаний. Для ссылок S3 браузеру нужен доступный извне endpoint,
а не внутреннее имя контейнера `minio`.

## Ограничения и диагностика

Текущий облачный pipeline ориентирован на русский язык: `language_hint=ru`.
Казахский и mixed не покрыты этим режимом. NVIDIA-путь ограничен 16 МиБ
нормализованного WAV (примерно 8 мин 44 с при 16 кГц, mono, PCM16) и четырьмя говорящими.
Канонизация текста не компенсирует отсутствие поддерживаемого распознавания языка.

Облачная конфигурация передаёт аудио NVIDIA, текст — OpenAI. Она не выполняет
требование исходного ТЗ о закрытом контуре. Подготовленные локальные адаптеры требуют
отдельного развёртывания и проверки качества. Интеграции с Zoom/Teams/Meet и live-захват
не реализованы; текущий вход — загруженный файл.

Нет авторизации и разграничения доступа по пользователям. Автоматическая отправка
уведомлений и восстановление зависшего запуска после полной потери worker-хоста
не реализованы. Хранится текущая попытка обработки, а не история всех попыток;
transactional outbox отсутствует. Качество ИИ требует отдельного benchmark и ручной
проверки ответственных/сроков, оно не гарантируется прохождением unit-тестов.

| Симптом | Что проверить |
| --- | --- |
| Речь работает, анализ недоступен / `503` при запуске | `OPENAI_API_KEY`, оба флага canonicalization/intelligence и все шесть моделей: одна канонизации + пять анализа |
| Ключ указан, но бэкенд его не видит | Имя `OPENAI_API_KEY`, не `API_KEY`; после изменения `.env` пересоздайте backend и worker |
| `422` при NVIDIA pipeline | `language_hint=ru`, корректный media ID и ограничения входа |
| `429` при загрузке/конвертации | Дождитесь свободного слота; лимиты действуют на процесс |
| Запуск остаётся `queued` | Проверьте Redis и логи worker; `/ready` не проверяет worker или ключи провайдеров |
| `409` при экспорте | Для текущей стенограммы ещё нет сохранённого анализа |
| Ошибка PDF при запуске на хосте | Проверьте существование обоих файлов шрифтов |
| Локальный Python не подключается к PostgreSQL | Порт хоста `5332`, внутри Compose `5432`; передан ли `--env-file` |
| Новая таблица отсутствует | Примените `alembic upgrade head` через сервис `migrate` |

Для диагностики dev:

```sh
docker compose -f compose.yaml -f compose.dev.yaml ps
docker compose -f compose.yaml -f compose.dev.yaml logs --tail=100 backend worker migrate
```

## Дополнительная документация

- [Приём файлов](docs/media-ingestion.md) и [подготовка аудио, лимиты памяти](docs/audio-preprocessing.md).
- [Speech providers](docs/speech-processing.md) и [NVIDIA cloud](docs/nvidia-cloud-speech.md).
- [Канонизация](docs/transcript-canonicalization.md) и [агентный анализ](docs/meeting-analysis-integration.md).
- [Общий pipeline и повторные попытки](docs/meeting-processing.md).
- [Экспорт DOCX/PDF](docs/protocol-export.md), [история и напоминания](docs/protocol-history-reminders.md).
- [Контракт backend/UI](docs/backend-ui-contract.md) и [frontend](docs/frontend-ui.md).
- [Режимы разработки](docs/development.md).
- [Benchmark](docs/meeting-benchmark.md) и [разбор качества](docs/meeting-quality-review.md).
- [Контекст проекта и исходные требования](docs/project-context.md).

Подробные документы фиксируют также отдельные этапы разработки; для текущих параметров
запуска сверяйтесь с этим README, `.env.example`, Compose и Swagger запущенной версии.
