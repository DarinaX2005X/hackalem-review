# Aqylman — автопротокол совещаний

Готовый hackathon MVP: загрузка записи, транскрипт со спикерами, резюме, решения,
поручения, ручное редактирование и экспорт протокола в DOCX/PDF.

## Запуск

Из корня проекта:

```powershell
python -m pip install -r BACKEND/requirements.txt
python main.py
```

Откроется интерфейс: http://127.0.0.1:8000/

Дополнительные адреса:

- Swagger: http://127.0.0.1:8000/docs
- Health и текущий AI-режим: http://127.0.0.1:8000/health

Node.js, npm, Docker, отдельный uvicorn и второй терминал не нужны. Остановка — `Ctrl+C`.
Чтобы не открывать браузер автоматически, задайте `ALEM_NO_BROWSER=1`.

## Режимы AI

### REAL AI

Создайте `BACKEND/.env`:

```dotenv
OPENAI_API_KEY=ваш_ключ
AI_PROVIDER=auto
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-transcribe-diarize
OPENAI_TEXT_MODEL=gpt-4o-mini
```

После перезапуска верхний индикатор покажет `REAL AI`.

Pipeline использует официальный Python SDK OpenAI:

1. `gpt-4o-transcribe-diarize` получает оригинальный транскрипт и реальные метки спикеров;
2. `diarized_json` возвращает `speaker`, `start`, `end`, `text`;
3. text model возвращает типизированный Structured Output через Pydantic;
4. результат сохраняется в существующую SQLite-базу.

Поддерживаются FLAC, MP3, MP4, MPEG, MPGA, M4A, OGG, WAV и WEBM размером до 25 МБ.
Ключ не хранится в исходном коде и `BACKEND/.env` игнорируется Git.

### DEMO MODE

Если `OPENAI_API_KEY` отсутствует, приложение не падает. Оно показывает жёлтый индикатор
`DEMO MODE` и позволяет пройти полный сценарий на детерминированных демонстрационных данных:
загрузка → обработка → участники → поручения → редактирование → DOCX/PDF.

Mock provider используется только в этом явно обозначенном fallback-режиме и в тестах.

### Опциональный LOCAL AI

Существующий локальный pipeline сохранён. Для него задайте `AI_PROVIDER=local`, установите
`BACKEND/requirements-ai.txt`, FFmpeg и локальные модели в `BACKEND/models/`.
Основной MVP от локальных моделей не зависит.

## Возможности интерфейса

- drag-and-drop аудио/видео;
- название и дата совещания;
- реальный polling прогресса через `/status`;
- обзор, решения, проблемы и ключевые моменты;
- редактирование имён/ролей участников;
- редактирование поручения, ответственного, автора и дедлайна;
- полный транскрипт с таймкодами;
- официальный протокол и скачивание DOCX/PDF;
- архив ранее обработанных совещаний;
- понятные сообщения об ошибках вместо белого экрана.

Переименование участника обновляет его имя в транскрипте, связанных поручениях и последующих
экспортах.

## API

Сохранён существующий контракт:

- `GET/POST /api/v1/meetings`
- `POST /api/v1/meetings/{id}/upload`
- `POST /api/v1/meetings/{id}/process`
- `GET /api/v1/meetings/{id}/status`
- `GET /api/v1/meetings/{id}`
- `PATCH /api/v1/meetings/{id}/participants/{participant_id}`
- `PATCH /api/v1/meetings/{id}/tasks/{task_id}`
- `GET /api/v1/meetings/{id}/export/docx`
- `GET /api/v1/meetings/{id}/export/pdf`

## Тесты

```powershell
cd BACKEND
python -m pytest -q
```

Тесты не обращаются к OpenAI и явно включают DEMO mode. Отдельный fake-client тест проверяет
контракт diarization и Structured Outputs без сетевого запроса.

## Структура MVP

```text
main.py                         единая точка запуска
BACKEND/app/main.py             FastAPI + встроенный web UI
BACKEND/app/web/                HTML / CSS / Vanilla JavaScript
BACKEND/app/ai/providers/       OpenAI, demo и local providers
BACKEND/app/services/           processing и экспорт
BACKEND/app/models/             существующая SQLite-модель
FRONT/                          прежний Vite/Tauri UI, не нужен для запуска MVP
```
