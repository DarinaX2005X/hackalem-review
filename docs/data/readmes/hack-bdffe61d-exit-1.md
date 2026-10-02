# AlemProtocol

> Локальная AI-система, которая превращает запись совещания в готовый протокол с транскриптом,
> кратким содержанием, поручениями, исполнителями и сроками.

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-required-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/AI-Docker%20ready-2496ED?logo=docker&logoColor=white)

AlemProtocol автоматизирует протоколирование русскоязычных, казахскоязычных и смешанных
совещаний. Пользователь загружает аудиозапись, backend ставит её в очередь, AI-сервис локально
распознаёт речь и формирует результат, после чего протокол можно проверить, отредактировать,
подтвердить и скачать в DOCX.

## Возможности

- загрузка WAV, MP3 и M4A с названием, датой и списком участников;
- асинхронная обработка записи отдельным worker-процессом;
- распознавание речи через `faster-whisper`;
- разделение реплик по спикерам через `pyannote.audio`;
- саммари и извлечение поручений локальной моделью Qwen через Ollama;
- определение исполнителей и преобразование сроков из естественного языка в даты;
- переход от поручения к исходному фрагменту записи;
- сопоставление спикеров с участниками и ручная правка поручений;
- подтверждение протокола и экспорт в DOCX;
- mock-режимы для разработки без GPU и ML-моделей;
- полностью локальная AI-обработка без передачи аудио во внешние API.

## Состав проекта

| Компонент | Каталог | Назначение | Порт по умолчанию |
| --- | --- | --- | --- |
| Frontend | [`frontend/`](frontend/) | React, TypeScript, Vite | `5173` |
| Backend API | [`backend/`](backend/) | FastAPI, загрузка файлов, REST API | `8080` |
| Backend worker | [`backend/`](backend/) | Очередь и отправка записей в AI | отдельный процесс |
| AI-сервис | [`ai-service/`](ai-service/) | ASR, диаризация, LLM, PDF/DOCX | `8000` |
| База данных | PostgreSQL | встречи, участники, задания и транскрипты | `5432` |

## Архитектура

```text
Браузер
   │
   ▼
Frontend (React/Vite или static hosting)
   │  /api/*
   ▼
Reverse proxy ───────────────► Backend API :8080
                                  │          │
                                  │          ├──► PostgreSQL
                                  │          └──► persistent audio storage
                                  ▼
                           очередь в PostgreSQL
                                  │
                                  ▼
                         Backend worker
                                  │  HTTP + audio
                                  ▼
                         AI service :8000
                                  │
                faster-whisper → pyannote → Qwen/Ollama
```

API быстро сохраняет файл и создаёт задачу. Worker независимо забирает задачи из PostgreSQL,
отправляет записи в AI-сервис и сохраняет результат. Поэтому для полной обработки должны работать
оба backend-процесса: API и worker.

## Быстрый локальный запуск

Для запуска всей системы без ML-моделей используйте встроенный mock backend. Понадобятся:

- Node.js `20.19+` или `22.12+` и npm;
- Python `3.11` или `3.12`;
- PostgreSQL;
- Git.

### 1. Клонирование

```bash
git clone https://github.com/BAITC-Hacks/hack-bdffe61d-exit-1.git
cd hack-bdffe61d-exit-1
```

### 2. PostgreSQL и backend

Создайте базу и пользователя PostgreSQL, затем подготовьте окружение:

```bash
cd backend
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
cp .env.example .env  # Windows: Copy-Item .env.example .env
```

Для локальной проверки без отдельного AI-сервиса укажите в `backend/.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://hackalem:password@127.0.0.1:5432/hackalem
STORAGE_DIR=C:/hackalem-data
MAX_UPLOAD_MB=200
AI_BASE_URL=http://127.0.0.1:8000
AI_MODE=mock
AI_INTERNAL_TOKEN=
AI_TIMEOUT_SECONDS=3600
FRONTEND_ORIGIN=http://localhost:5173
```

Создайте каталог из `STORAGE_DIR`, примените миграции и запустите API:

```bash
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Во втором терминале, с тем же виртуальным окружением и из каталога `backend`, запустите worker:

```bash
python -m app.worker
```

Проверка backend:

- Swagger UI: [http://localhost:8080/docs](http://localhost:8080/docs);
- API healthcheck: [http://localhost:8080/health](http://localhost:8080/health);
- готовность PostgreSQL: [http://localhost:8080/ready](http://localhost:8080/ready).

### 3. Frontend

В третьем терминале:

```bash
cd frontend
npm ci
cp .env.example .env  # Windows: Copy-Item .env.example .env
npm run dev
```

Откройте [http://localhost:5173](http://localhost:5173). Frontend обращается к `/api`, а Vite
перенаправляет запросы на `BACKEND_URL=http://127.0.0.1:8080` и удаляет префикс `/api`.

Проверить прокси можно по адресу
[http://localhost:5173/api/ready](http://localhost:5173/api/ready).

## Подключение реального AI

Сначала запустите AI-сервис в `mock`-режиме, чтобы проверить транспорт между компонентами, затем
подготовьте модели и переключите его в `real`.

```bash
cd ai-service
cp .env.example .env  # Windows: Copy-Item .env.example .env
docker compose up --build -d
```

Проверка: [http://localhost:8000/health](http://localhost:8000/health).

В `backend/.env` задайте:

```dotenv
AI_MODE=http
AI_BASE_URL=http://127.0.0.1:8000
AI_INTERNAL_TOKEN=replace-with-a-long-random-token
```

В `ai-service/.env` должен быть тот же токен:

```dotenv
AI_MODE=real
INTERNAL_TOKEN=replace-with-a-long-random-token
```

После изменения `.env` перезапустите AI-сервис, backend API и worker. Подготовка Whisper,
pyannote и Ollama, offline-режим и GPU-запуск описаны в
[`ai-service/README.md`](ai-service/README.md).

Для запуска компонентов на разных компьютерах используйте
[`CONNECT_TWO_LAPTOPS.md`](CONNECT_TWO_LAPTOPS.md).

### Режимы AI

| Backend `AI_MODE` | AI-сервис `AI_MODE` | Что происходит |
| --- | --- | --- |
| `mock` | любой | Backend возвращает встроенный тестовый результат, HTTP-запроса нет |
| `http` | `mock` | Полный HTTP-путь с тестовым ответом AI-сервиса |
| `http` | `real` | Настоящее распознавание и анализ локальными моделями |

## Переменные окружения

### Frontend

| Переменная | Пример | Назначение |
| --- | --- | --- |
| `VITE_USE_MOCK` | `false` | Использовать реальный backend или UI-заглушку |
| `VITE_API_BASE_URL` | `/api` | Публичный путь к backend API |
| `VITE_MAX_UPLOAD_MB` | `200` | Ограничение файла в интерфейсе |
| `BACKEND_URL` | `http://127.0.0.1:8080` | Цель Vite proxy в dev/preview |

`VITE_*` встраиваются во frontend во время сборки. `BACKEND_URL` нужен только Vite dev/preview и
не используется статическими файлами после production build.

### Backend

| Переменная | Пример | Назначение |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://...` | Подключение к PostgreSQL |
| `STORAGE_DIR` | `/var/lib/alemprotocol/audio` | Постоянное хранилище аудио |
| `MAX_UPLOAD_MB` | `200` | Максимальный размер записи |
| `AI_BASE_URL` | `http://ai-host:8000` | Базовый URL AI-сервиса |
| `AI_MODE` | `http` | `mock`, `http` или совместимый alias `real` |
| `AI_INTERNAL_TOKEN` | секрет | Токен для AI-сервиса |
| `AI_TIMEOUT_SECONDS` | `3600` | Таймаут долгой AI-обработки |
| `FRONTEND_ORIGIN` | `https://alem.example` | Разрешённый browser origin для CORS |

Полные шаблоны находятся в [`frontend/.env.example`](frontend/.env.example),
[`backend/.env.example`](backend/.env.example) и
[`ai-service/.env.example`](ai-service/.env.example).

## Production deployment

### Рекомендуемая схема

- **Frontend:** статическая сборка на Nginx, CDN, S3-compatible hosting, Netlify или Vercel;
- **Backend API + worker:** Linux VM или PaaS с постоянными процессами;
- **PostgreSQL:** managed database или отдельный сервер с резервным копированием;
- **Audio storage:** persistent volume, доступный одновременно API и worker;
- **AI-сервис:** отдельная GPU/CPU VM с Docker, локальными моделями и постоянными volumes;
- **Сеть:** backend и AI соединяются по private network или VPN, а не через публичный порт.

Serverless-функции без фоновых процессов и постоянного диска для backend не подходят: worker
должен непрерывно опрашивать очередь, а API и worker должны видеть одни и те же аудиофайлы.

### 1. Сборка frontend

Создайте `frontend/.env.production`:

```dotenv
VITE_USE_MOCK=false
VITE_API_BASE_URL=/api
VITE_MAX_UPLOAD_MB=200
```

Соберите приложение:

```bash
cd frontend
npm ci
npm run build
```

Публиковать нужно содержимое `frontend/dist`. Веб-сервер должен:

1. отдавать `index.html` для неизвестных frontend-маршрутов, включая `/meetings/:id`;
2. проксировать `/api/*` в backend с удалением префикса `/api`;
3. разрешать запросы размером не меньше `MAX_UPLOAD_MB`;
4. работать по HTTPS.

Пример Nginx:

```nginx
server {
    listen 80;
    server_name alem.example;

    root /var/www/alemprotocol;
    index index.html;
    client_max_body_size 200m;

    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

TLS можно завершать на Nginx, load balancer или CDN. Если frontend и API размещены на разных
доменах, задайте полный `VITE_API_BASE_URL=https://api.example.com` до сборки и укажите точный URL
frontend в `FRONTEND_ORIGIN` backend.

### 2. Развёртывание backend

На сервере создайте виртуальное окружение, установите зависимости и сохраните production `.env`
в `backend/.env`:

```bash
cd /opt/alemprotocol/backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
```

Запускайте два независимых долгоживущих процесса через systemd, Supervisor или возможности PaaS:

```bash
# Web process
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8080

# Worker process
.venv/bin/python -m app.worker
```

Миграции выполняются один раз перед запуском новой версии. `STORAGE_DIR` должен находиться на
постоянном диске; при разнесении API и worker по разным узлам потребуется shared storage.

### 3. Развёртывание AI-сервиса

AI лучше размещать на отдельном узле. Подготовьте модели по инструкции AI-сервиса, задайте
`AI_MODE=real`, включите offline-флаги и запустите Compose:

```bash
cd /opt/alemprotocol/ai-service
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
curl http://127.0.0.1:8000/health
```

Для CPU уберите `docker-compose.gpu.yml`. Каталоги моделей и volume Ollama должны сохраняться
между релизами. Порт `8000` разрешайте только backend-хосту. Порт Ollama `11434` не должен быть
доступен из интернета.

### 4. Порядок релиза и healthchecks

1. проверить доступность PostgreSQL и persistent storage;
2. применить Alembic-миграции;
3. запустить AI-сервис и проверить `GET /health`;
4. запустить backend API и worker;
5. проверить backend `GET /health` и `GET /ready`;
6. опубликовать frontend и проверить `GET /api/ready` через reverse proxy;
7. выполнить сквозной тест с тестовой записью.

## Проверка проекта

### Frontend

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run smoke
```

`npm run test:connected` проверяет реальный путь frontend → backend → worker → AI mock, включая
аудио после перезагрузки, редактирование, подтверждение и DOCX. Для него все сервисы должны быть
запущены, backend должен использовать `AI_MODE=http`, а AI-сервис — `AI_MODE=mock`.

### Backend

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
python scripts/smoke_e2e.py --audio "/path/to/meeting.wav"
```

### AI-сервис

```bash
cd ai-service
python -m pip install -r requirements-dev.txt
pytest
ruff check app tests scripts
```

## Структура репозитория

```text
.
├── frontend/                  # React UI и browser-тесты
├── backend/
│   ├── app/api/               # REST endpoints
│   ├── app/models/            # SQLAlchemy models
│   ├── app/services/          # AI-клиент и DOCX export
│   ├── migrations/            # Alembic migrations
│   ├── scripts/               # backend E2E smoke-test
│   └── tests/                 # integration tests
├── ai-service/
│   ├── app/pipeline/          # ASR, diarization, LLM и сроки
│   ├── scripts/               # модели и test audio
│   └── tests/                 # unit и API-тесты
└── CONNECT_TWO_LAPTOPS.md     # запуск компонентов на разных устройствах
```

## Безопасность и данные

- не добавляйте `.env`, реальные записи, модели, базы и generated documents в Git;
- используйте разные длинные случайные значения `INTERNAL_TOKEN`/`AI_INTERNAL_TOKEN` для каждого
  окружения;
- не публикуйте AI-сервис и Ollama напрямую в интернете;
- ограничьте доступ к PostgreSQL и storage на уровне сети и прав файловой системы;
- включите HTTPS на публичной точке входа и регулярно создавайте backup PostgreSQL и audio storage;
- для закрытого контура заранее скачайте модели и оставьте Hugging Face в offline-режиме.

---

Проект разработан командой **Exit 1** для BAITC Hacks.
