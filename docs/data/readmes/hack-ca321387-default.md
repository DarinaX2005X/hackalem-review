# EventLens

EventLens подбирает подрядчиков для мероприятий в Казахстане: проверяет обязательные
условия, показывает до трёх вариантов, объясняет оценки и предлагает другие даты.
Во frontend также доступны компактные готовые сценарии, поиск по описанию,
подробный разбор ранжирования и AI-чат. Правила подбора и API описаны в
[архитектуре](docs/ARCHITECTURE.md).

В поиске по описанию можно написать, например: «Нужен ведущий на корпоратив
в Алматы 15 ноября 2026, бюджет до 800 000 ₸, на 6 часов». AI извлекает поля,
а backend проверяет каждое значение по точной цитате из запроса и справочникам.
Незаполненные условия **не** берутся из примера или текущей формы: если не хватает
обязательных полей, пользователь дополняет их вручную. Поиск запускается
автоматически только при полном и проверенном запросе. При наличии ключа
используется OpenAI, иначе — локальная модель из профиля `local-llm`.

## Что понадобится

- Для варианта с Docker: Docker Desktop с запущенным Docker Engine и `docker compose`.
- Для варианта без Docker: Python 3.12+ и Node.js 22+ с npm.
- Свободные порты: `8000` (backend), `8100` (сервис сходства), `8200` (локальная
  модель); frontend использует `3000` в Docker или `5173` без Docker.
- Интернет при первой сборке образов и первой загрузке весов локальной модели.

Все команды ниже выполняются **из корня репозитория** — папки, где находятся
`docker-compose.yml`, `backend/` и `frontend/`. На Windows откройте PowerShell в
этой папке. `npm start` в корне не работает: `package.json` лежит в `frontend/`.

## Вариант 1. Запуск с Docker (рекомендуется)

1. При первом запуске создайте `.env` в корне проекта:

   ```powershell
   Copy-Item .env.example .env
   ```

   Если `.env` уже существует, не перезаписывайте его. Файл игнорируется Git.
   Впишите `OPENAI_API_KEY=...`, если хотите использовать OpenAI. Ключ нужен
   только backend; не добавляйте его во frontend или переменные `VITE_*`.

2. Запустите **весь стек**, включая локальную модель для резервного AI-чата:

   ```powershell
   docker compose --profile local-llm up -d --build
   ```

   При первом запуске локальный контейнер скачает Qwen2.5-0.5B-Instruct и
   установит CPU-зависимости — это может занять несколько минут. Весы хранятся
   в Docker volume `huggingface-cache` и не лежат в Git-репозитории. Дождитесь
   состояния `healthy` у `backend`, `ai-service` и `local-explainer`:

   ```powershell
   docker compose --profile local-llm ps
   ```

3. Откройте **http://localhost:3000**. Документация API —
   **http://localhost:8000/docs**. Быстрая проверка:

   ```powershell
   Invoke-RestMethod http://localhost:8000/api/health
   Invoke-RestMethod http://localhost:8100/health
   Invoke-RestMethod http://localhost:8200/health
   ```

   Чат сначала пробует OpenAI при наличии ключа, затем локальную модель. Без
   ключа будет использоваться локальная модель. Подбор подрядчиков не зависит
   от AI-чата. Для текстов «Почему этот подрядчик подходит» режим `auto`
   использует OpenAI при наличии ключа, иначе проверенный шаблон. Чтобы
   использовать локальную модель также для этих текстов, поставьте в `.env`
   `EXPLANATION_MODE=local` и перезапустите стек.

Остановить контейнеры без удаления сохранённых весов:

```powershell
docker compose --profile local-llm down
```

Если нужна только версия с OpenAI **без локальной модели**, достаточно
`docker compose up -d --build` и ключа в `.env`. В этом режиме при отказе OpenAI
AI-чат будет недоступен; основной поиск продолжит работать. Не используйте
`down -v`, если хотите сохранить скачанные веса.

## Вариант 2. Запуск без Docker

Ниже команды для PowerShell. Для полного набора функций запускаются четыре
процесса в отдельных терминалах. Нужны Python, Node.js и интернет для первой
установки зависимостей и загрузки локальной модели.

1. Один раз установите зависимости из корня репозитория:

   ```powershell
   python -m venv backend/.venv
   backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
   python -m venv services/ai/.venv
   services/ai/.venv/Scripts/python.exe -m pip install "torch>=2.4,<3" --index-url https://download.pytorch.org/whl/cpu
   services/ai/.venv/Scripts/python.exe -m pip install -r services/ai/requirements-local.txt
   npm --prefix frontend ci
   Copy-Item .env.example .env
   ```

   Последнюю команду выполняйте только если `.env` ещё нет. При желании
   добавьте в `.env` `OPENAI_API_KEY=...`. Если `python` не найден, установите
   Python с включённым PATH или используйте Windows launcher `py -3.12` для
   создания окружений.

2. Откройте четыре терминала PowerShell в корне репозитория и запустите по
   одной команде в каждом:

   ```powershell
   # Терминал 1 — backend, загружает .env
   backend/.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port 8000 --env-file .env
   ```

   ```powershell
   # Терминал 2 — детерминированное текстовое сходство
   services/ai/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir services/ai --port 8100
   ```

   ```powershell
   # Терминал 3 — локальная модель для AI-чата
   services/ai/.venv/Scripts/python.exe -m uvicorn app.local_explainer:app --app-dir services/ai --port 8200 --env-file .env
   ```

   ```powershell
   # Терминал 4 — Vite frontend
   npm --prefix frontend run dev
   ```

3. Откройте **http://localhost:5173**. Vite перенаправляет `/api` на backend
   `localhost:8000`; менять `VITE_API_URL` для обычного локального запуска не
   требуется. Проверки API и локальной модели — те же URL, что в варианте с
   Docker. Для остановки нажмите `Ctrl+C` в каждом терминале.

На macOS/Linux используйте `python3 -m venv ...` и замените
`.../Scripts/python.exe` на `.../bin/python`, а `Copy-Item .env.example .env`
на `cp .env.example .env`; остальные команды аналогичны.
Если локальная модель не нужна, третий терминал и установку CPU PyTorch можно
пропустить, но AI-чат тогда требует действующий ключ OpenAI.

## Настройки и диагностика

Корневой `.env.example` описывает настройки сервера. `OPENAI_MODEL` по умолчанию
равен `gpt-4.1-mini`. Для API нужен отдельный ключ OpenAI Platform — подписка
ChatGPT сама по себе его не предоставляет. `EXPLANATION_MODE=auto|local|openai|template`
управляет только текстом объяснений карточек, **не** порядком подбора и **не**
приоритетом провайдеров AI-чата. `SEMANTIC_MODE=tfidf` использует локальный
сервис сходства на порту 8100; при его недоступности backend сообщает о fallback.
Чат получает параметры поиска и историю беседы, но пока не получает сам список
выданных подрядчиков — он не должен утверждать, что видел результаты.

Если порт занят, остановите другой процесс/контейнер на нём или измените
проброс порта и соответствующий URL. Если Docker не отвечает, сначала запустите
Docker Desktop. Если frontend показывает ошибку API, проверьте
`/api/health` и `docker compose --profile local-llm logs backend` (Docker)
или вывод первого терминала (без Docker). Если AI-чат недоступен, проверьте
`OPENAI_API_KEY`, состояние `local-explainer` и его `/health`.

## Проверки проекта

Из корня репозитория на Windows:

```powershell
backend/.venv/Scripts/python.exe -m unittest discover -s backend/tests -v
backend/.venv/Scripts/python.exe -m mypy --strict backend/app
Push-Location services/ai
./.venv/Scripts/python.exe -m unittest discover -s tests -v
Pop-Location
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

После намеренного изменения backend-контракта или данных обновляйте контракт
и фикстуры командами из `backend/scripts/`.

## Синхронизация веток

После push в `main` workflow `.github/workflows/sync-main.yml` пытается
влить изменения в `arys` и `damir` без force-push. При конфликте или запрете
записи GitHub Actions соответствующее задание завершится ошибкой; ветку нужно
разрешить вручную. Workflow не заменяет коммиты в ветках.
