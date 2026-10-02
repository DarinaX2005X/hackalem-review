# Career Quest — DomaDoma

FastAPI + SQLite backend для Career Quest. Python 3.12; UI и recommendation engine
разрабатываются отдельно. Полный контракт и граница интеграции: [docs/backend.md](docs/backend.md).

**Текущее состояние:** backend подключён к AI engine/service из `3f45c46`.
Работают профиль, рекомендации, Complete с пересчётом навыков/readiness и HR.
Без OPENAI_API_KEY рекомендации работают в явно обозначенном fallback-режиме.
Frontend добавлен: вход, профиль, рекомендации, Complete, история, HR и импорт.
Сборка интерфейса: `cd frontend`, `npm ci`, `npm run build`; затем backend
раздаёт `frontend/dist` на своём адресе. Локально сейчас http://127.0.0.1:8765.
Основной интерфейс команды: [frontend/README.md](frontend/README.md).
Наш альтернативный вариант сохранён в `frontend-preview/`: [docs/frontend.md](docs/frontend.md).
Старый черновик в `work/` в сборку не входит.

## Итоговый запуск после интеграции

Требуются Docker Engine/Desktop, Compose и файлы всех трёх участников:
`frontend/package.json` + lockfile с `npm run build` → `dist`,
`backend/recommendation/{engine.py,service.py,requirements-ai.txt}`,
`data/{skills.json,events.json,employees.json,activity_history.csv}`.

1. Скопировать `.env.example` в `.env`.
2. Задать случайный `JWT_SECRET` минимум 32 байта и `DEMO_PASSWORD` минимум 8 символов.
   Например, секрет можно сгенерировать локально через `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
3. Владелец ключа отдельно задаёт `OPENAI_API_KEY` и `OPENAI_MODEL` для AI-демо.
4. Запустить `docker compose up --build`.

Адрес: http://localhost:8000. Swagger: http://localhost:8000/docs.
Один контейнер раздаёт API и SPA; SQLite сохраняется в named volume.
Полная Docker-сборка пока не проверена. Production-сборка frontend проверена отдельно.

## Разработка backend отдельно

Из корня репозитория, Python 3.12:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
# Общий исходный набор из main:
$env:DATA_DIR = "data"
$env:JWT_SECRET = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
$env:DEMO_PASSWORD = "choose-a-private-demo-password"
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

На Windows PowerShell 5.1 вместо `GetBytes(48)` можно задать секрет,
сгенерированный приведённой выше Python-командой. Секрет не коммитить.
Для запуска без платных вызовов оставьте OPENAI_API_KEY незаданным или пустым.
Uvicorn в этом режиме использует переменные окружения; `.env` автоматически
читает только Compose. Для frontend dev использовать Vite proxy `/api` → `http://localhost:8000`.

Для проверки OpenAI перед запуском Uvicorn задайте `OPENAI_API_KEY` в окружении
своего терминала и `$env:OPENAI_MODEL = "gpt-4.1"`. У каждого участника свой
локальный ключ: `.env` в Git не передаётся. Если порт 8000 занят, добавьте
к команде Uvicorn `--port 8765`; Swagger будет на http://127.0.0.1:8765/docs.

## Demo-аккаунты и API

Логины: `employee`, `hr`, `admin`. На первом запуске всем задаётся `DEMO_PASSWORD`,
сохраняется только Argon2-хеш. Employee связан с `E0002` (настраивается
`DEMO_EMPLOYEE_ID` при первоначальном создании аккаунта). Смена env после seed
не перезаписывает существующие пароли. JWT действует 30 минут по реальному времени.

`POST /api/auth/login` с `{"username":"admin","password":"<ваш пароль>"}`
возвращает токен. Дальше передавать `Authorization: Bearer <token>`.

| Endpoint | Доступ |
|---|---|
| `GET /api/health` | публичный |
| `GET /api/auth/me` | любой вошедший |
| `GET /api/employees` | HR/admin |
| `GET /api/employees/{id}` | employee self, HR/admin |
| `GET /api/employees/{id}/recommendations?lang=kk` | employee self, HR/admin |
| `POST /api/employees/{id}/activities/{event_id}/complete` | employee self/admin |
| `GET /api/hr/overview` | HR/admin |
| `POST /api/admin/upload` | admin |

Upload — один multipart-запрос с `employees_file` и `history_file`.
Пример нового профиля: [employees.json](backend/examples/employees.json),
пустая история с правильным заголовком: [history.csv](backend/examples/history.csv).
Можно отправить через Swagger после добавления Bearer-заголовка клиентом или curl:

```sh
curl http://localhost:8000/api/admin/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F employees_file=@backend/examples/employees.json \
  -F history_file=@backend/examples/history.csv
```

Лимит каждого файла 5 MiB; UTF-8 и BOM поддерживаются. Оба файла валидируются
до записи. Повтор history пропускается, конфликт record_id → 409 без частичного
импорта. Профиль с прежним ID обновляет версию. При demo-завершениях замена
отличающегося baseline пока запрещена 409 до согласования reconciliation с AI.

Complete: JSON `{"occurrence_key":null}`, заголовок `Idempotency-Key` с уникальным
ключом операции. Для `EV_036` occurrence_key — дата рекомендованной сессии.
Повтор не повышает навыки снова. Ответ содержит профиль; рекомендации запрашиваются
отдельно. При `stale_revision` повторить GET рекомендаций. Grade не повышается автоматически.

SQLite загружает исходный набор только один раз. Модельная дата берётся из набора:
`2026-10-01`; JWT и системные timestamps используют реальные часы. Не удаляйте
volume/SQLite для обычного рестарта. Complete использует локальный движок и не ждёт LLM.

## Проверки и ограничения

```powershell
.\backend\.venv\Scripts\python.exe -m pytest tests/backend tests/ai -q
```

Тесты используют синтетический исходный набор из `data/` или текущего `work/karim312k1/`.
Часть HTTP-тестов использует тестовый DomainDouble; интеграционные тесты
`test_ai_integration.py` используют настоящий engine/service и SQLite.
Результат: **40 passed**. Ключ и платные запросы не нужны. Проверенные версии прямых
Python-зависимостей зафиксированы в requirements; AI-зависимости принадлежат напарнику.
Локальные проверки сейчас выполняются Python 3.13.5; Python 3.12 и полный Docker
остаются интеграционными проверками.

Проверены реальные gain/readiness, HR, fallback, повтор Complete и состояние
после рестарта. HTTP smoke: E0002 + EV_005 → System Design 1 → 2,
readiness 62 → 66, revision 1 → 2. Отдельно выполнен реальный HTTP-запрос через
backend к OpenAI (`gpt-4.1`): `source=llm`, `fallback_reason=null`,
2 рекомендации для E0002. Health, login и профиль вернули 200;
доступ employee к чужому профилю — 403. Подробнее: [docs/backend.md](docs/backend.md).
Подтверждённые вопросы к качеству AI-объяснений и локализации перечислены
в [docs/backend.md](docs/backend.md). Backend ограничивает запрос 8 секундами.
Это demo auth, без регистрации/refresh/SSO и без заявления о production-защите.

Источники: синтетический набор Career Quest v1.0 и его README.ru.md; пользовательский
контракт Backend/Integration v1. Исходный engine получен из main вместе с общими
документами. AI service подключён из коммита напарника 3f45c46 без изменения
его исходников и общего контракта.
