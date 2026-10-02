# Problemly

Problemly помогает бизнесу превратить краткое описание потребности в понятную, проверяемую задачу для студенческих команд. Бизнес отвечает на уточняющие вопросы, вручную подтверждает поля и публикует карточку; команда выбирает задачу из каталога и отправляет отклик. Решение о выборе команды всегда остаётся за бизнесом.

## Что реализовано

- AI-анализ черновика через OpenRouter с fallback без внешнего ключа;
- редактируемая карточка с явным подтверждением полей и детерминированным рейтингом 0–100;
- каталог опубликованных задач, фильтры и прямые ссылки на карточки;
- пять тематических demo-задач с рейтингами 30, 50, 80, 90 и 100, а также пять профилей команд;
- отклики команд и ручные статусы `pending`, `selected`, `rejected`, включая выбор нескольких команд;
- Swagger-документация API: `/api/docs`.

## Технологии

- React, Vite и Nginx — frontend;
- Node.js 22, SQLite и Docker Compose — backend и развёртывание;
- OpenRouter, OpenAI-совместимый Chat Completions API и модель `qwen/qwen3-coder-next` — AI-анализ. Если провайдер или ключ недоступны, приложение использует безопасные fallback-вопросы.

## Архитектура

- `frontend/` — React/Vite, в production раздаётся Nginx;
- `backend/` — Node.js API и SQLite;
- `docker-compose.yaml` — единый production-подобный запуск. Frontend доступен на хост-порту `5380`, backend — на `3388`.

## Проверка сценария

Полный acceptance-сценарий backend покрывает: AI-анализ, сборку и ручное подтверждение карточки, публикацию без минимального порога рейтинга, два отклика, ручной выбор команды и сохранение SQLite после перезапуска. Также проверяются валидация, миграции и Docker health/smoke.

Подробная матрица соответствия требованиям и точные команды проверок находятся в [backend/docs/requirements.md](backend/docs/requirements.md).

## Запуск на сервере

Требуются Docker Engine и Docker Compose v2. Клонируйте или обновите репозиторий, затем создайте локальные env-файлы — они не попадают в Git:

```bash
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

В `frontend/.env` задайте production API. Корневой Compose передаст этот файл в Vite только на время сборки и не включит его в Docker-образ:

```env
VITE_API_BASE_URL=https://haa-api.defaul7.net
```

В `backend/.env` минимум проверьте следующие значения:

```env
PORT=3388
DATABASE_URL=file:/app/data/problemly.db
FRONTEND_ORIGIN=https://haa.defaul7.net
API_BASE_URL=https://haa-api.defaul7.net/api
```

Для AI-анализатора укажите `LLM_API_KEY` OpenRouter только при необходимости внешнего провайдера. Используемая модель — `qwen/qwen3-coder-next`. Без ключа backend использует fallback-вопросы.

Из корня проекта соберите и запустите оба сервиса:

```bash
docker compose up -d --build
```

Проверка статуса и логов:

```bash
docker compose ps
docker compose logs -f backend
```

Остановка:

```bash
docker compose down
```

Данные SQLite сохраняются в Docker volume `backend-data`. Чтобы удалить их вместе с контейнерами, используйте `docker compose down -v`.

## Домены и reverse proxy

Направьте TLS reverse proxy на тот же сервер:

- `https://haa.defaul7.net` → `http://127.0.0.1:5380`;
- `https://haa-api.defaul7.net` → `http://127.0.0.1:3388`.

После проксирования frontend должен открываться по `https://haa.defaul7.net`, а health check API — по `https://haa-api.defaul7.net/api/health`.

## Развёрнутая версия

Problemly развёрнут на сервере в Германии. Production-домены: [haa.defaul7.net](https://haa.defaul7.net) для интерфейса и [haa-api.defaul7.net/api/health](https://haa-api.defaul7.net/api/health) для проверки API.

## Локальная разработка

Смотрите [frontend README](frontend/README.md) и [backend README](backend/README.md). Для совместного запуска используйте те же команды Compose выше.

## Ограничения MVP

- нет регистрации, чата, уведомлений и автоматического назначения команд;
- AI-поля не считаются подтверждёнными без действия пользователя;
- ключ OpenRouter хранится только в локальном `backend/.env`;
- внешний AI-провайдер может быть недоступен, поэтому fallback-вопросы остаются частью MVP.
