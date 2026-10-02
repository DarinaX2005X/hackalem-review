# AEVIX - AI Career Quest Platform

AEVIX - платформа персонального развития сотрудников. Система анализирует профиль сотрудника, историю активностей и skill gaps, рекомендует карьерные квесты, объясняет логику рекомендаций через AI и помогает проходить активности по шагам.

## Архитектура

```text
+-----------------+       HTTP        +-----------------+       HTTPS       +--------------+
|    Frontend     | <---------------> |     Backend     | <--------------> |    OpenAI    |
|  React + Vite   |      :3000        |     FastAPI     |  Responses API   |     LLM      |
+-----------------+                   +-----------------+                  +--------------+
                                              |
                                              v
                                      +-----------------+
                                      |     SQLite      |
                                      | career_quest.db |
                                      +-----------------+
                                              |
                                              v
                                      +-----------------+
                                      | Career Dataset  |
                                      | employees/events|
                                      +-----------------+
```

## Возможности

- **Персональные рекомендации**: deterministic engine считает score по skill gaps, целевому грейду, impact, prerequisites и истории активностей.
- **AI-объяснения**: OpenAI Responses API формулирует понятное объяснение, почему выбран конкретный квест.
- **AI-шаги квеста**: модель генерирует практический план из 3-5 шагов для выбранной активности.
- **Прогресс-бары ожидания**: frontend показывает индикатор, пока модель думает.
- **Парное обучение**: сотрудник может найти коллегу и пройти квест вместе.
- **Growth Coins**: кошелек, транзакции и награды за завершение активностей.
- **ESG goals**: вклад Growth Coins в инициативы компании.
- **HR analytics**: агрегированная аналитика по skill gaps, активности сотрудников и ESG engagement.
- **Импорт данных**: загрузка employees, events, skills и activity history через API.

## Презентация

- **Google Drive**: https://drive.google.com/drive/folders/1A299QTBNUuf_FNof-x1WaDoIz2rqlgfu?usp=share_link

## Быстрый запуск через Docker Compose

### Требования

- Docker
- Docker Compose
- Git
- OpenAI API key, если нужны AI-объяснения и AI-шаги

### 1. Настрой `.env`

Файл `.env` лежит в папке backend:

```bash
cd hack-fe3472cb-aevix
```

Пример:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-6-sol

# Optional dataset override
# DATASET_DIR=C:\path\to\career_quest_dataset\case_1\career_quest_dataset
```

Если `OPENAI_API_KEY` не задан, приложение продолжит работать через локальные template-ответы.

### 2. Настрой логины и пароли

Скрипты генерации паролей запускаются из backend-папки. Если зависимости еще не установлены локально, подготовь окружение:

```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

HR-аккаунт создается локально. По умолчанию логин HR: `hr`, пароль генерируется автоматически:

```bash
python -m app.setup_hr
```

Скрипт добавит `HR_USERNAME` и `HR_PASSWORD_HASH` в `.env`, а реальный пароль сохранит только локально:

```text
.local/hr-access.txt
```

Пароли сотрудников тоже генерируются локально. Логин сотрудника совпадает с `employee_id`, например `E0002`. Запускай команду после первого старта backend или после импорта dataset, чтобы в базе уже были сотрудники:

```bash
python -m app.setup_employees
```

Список employee-логинов и паролей будет сохранен в приватный файл:

```text
.local/employee-access.csv
```

Чтобы пересоздать пароли и сбросить активные сессии:

```bash
python -m app.setup_hr --rotate
python -m app.setup_employees --rotate
```

Файлы `.env` и `.local/` уже находятся в `.gitignore`, поэтому пароли и хэши не должны попадать в Git.

### 3. Запусти сервисы

```bash
docker compose up --build -d
```

### 4. Открой приложение

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs
- **Demo employee ID**: `E0002`
- **HR login**: `hr`
- **HR password**: `QQE5Ln5QncFCEOXmUgMpXWnlGyojp0Qi`
- **Employee login**: `E0002`
- **Employee password**: `MWS7-LMSEy2H80FHiFoT6XfQ4q6AT1p-`

### 5. Остановить сервисы

```bash
docker compose down
```

Чтобы удалить volume с SQLite-базой:

```bash
docker compose down -v
```

## Ручной запуск без Docker

### Backend

```bash
cd hack-fe3472cb-aevix
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Проверка:

```bash
curl http://127.0.0.1:8000/health
```

### Frontend

Frontend находится рядом с backend-папкой:

```bash
cd ../career-quest-frontend
npm install
npm run dev
```

По умолчанию Vite откроется на:

```text
http://127.0.0.1:5173
```

## Сервисы

| Сервис | Порт | Описание |
| ------ | ---- | -------- |
| Frontend | 3000 | React/Vite SPA, собранный в Nginx container |
| Backend | 8000 | FastAPI API для рекомендаций, квестов, HR и ESG |
| SQLite | volume | Локальная база `career_quest.db` внутри Docker volume |
| OpenAI | external | AI-объяснения и генерация шагов квеста |

## Docker-файлы

```bash
aevix/
├── hack-fe3472cb-aevix/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
└── career-quest-frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── .dockerignore
```

## Переменные окружения

### Backend

| Переменная | Обязательная | Значение по умолчанию | Описание |
| ---------- | ------------ | --------------------- | -------- |
| `OPENAI_API_KEY` | Нет | `None` | API key для OpenAI |
| `OPENAI_MODEL` | Нет | `gpt-6-astra` | Модель для AI-объяснений и шагов |
| `DATABASE_URL` | Нет | `sqlite:///./career_quest.db` | SQLAlchemy URL базы данных |
| `DATASET_DIR` | Нет | bundled dataset | Путь к dataset |
| `ALLOWED_ORIGINS` | Нет | localhost origins | CORS origins для frontend |
| `HR_USERNAME` | Нет | `hr` | Логин HR-аккаунта |
| `HR_PASSWORD_HASH` | Да для HR-login | `None` | Хэш HR-пароля, генерируется через `python -m app.setup_hr` |
| `HR_SESSION_HOURS` | Нет | `8` | Время жизни auth-сессии в часах |
| `HR_COOKIE_SECURE` | Нет | `false` | `true` для HTTPS-cookie в production |

### Frontend

| Переменная | Обязательная | Значение по умолчанию | Описание |
| ---------- | ------------ | --------------------- | -------- |
| `VITE_API_URL` | Нет | `http://127.0.0.1:8000` | URL backend API |
| `VITE_EMPLOYEE_ID` | Нет | `E0002` | ID сотрудника для demo UI |

В Docker Compose frontend собирается с:

```env
VITE_API_URL=http://localhost:8000
VITE_EMPLOYEE_ID=E0002
```

## Структура проекта

```bash
aevix/
├── hack-fe3472cb-aevix/              # Backend FastAPI
│   ├── app/
│   │   ├── core/                     # Конфигурация
│   │   ├── db/                       # SQLAlchemy модели и база
│   │   ├── routers/                  # API роуты
│   │   ├── schemas/                  # Pydantic схемы
│   │   ├── services/                 # Бизнес-логика
│   │   ├── tests/                    # Pytest тесты
│   │   └── main.py                   # FastAPI приложение
│   ├── career_quest_dataset/         # Demo dataset
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env
└── career-quest-frontend/            # Frontend React/Vite
    ├── src/
    │   ├── api.js                    # API client
    │   ├── SiteApp.jsx               # Основной UI
    │   ├── AdminPages.jsx            # HR и import страницы
    │   └── site.css                  # Стили
    ├── Dockerfile
    ├── nginx.conf
    └── package.json
```

## API endpoints

### Health

- `GET /health` - проверка backend

### Auth

- `POST /api/auth/login` - вход сотрудника или HR
- `POST /api/auth/hr/login` - вход только для HR
- `GET /api/auth/session` - текущая auth-сессия
- `POST /api/auth/logout` - выход

### Employees

- `GET /api/employees` - список сотрудников
- `POST /api/employees/register` - регистрация сотрудника
- `GET /api/employees/{employee_id}` - данные сотрудника
- `GET /api/employees/{employee_id}/profile` - профиль сотрудника
- `GET /api/employees/{employee_id}/trajectory` - траектория развития
- `GET /api/employees/{employee_id}/recommendations` - рекомендации с AI-объяснениями

### Quests

- `POST /api/employees/{employee_id}/quests/{event_id}/select` - выбрать квест
- `GET /api/employees/{employee_id}/quests/{event_id}/steps` - получить шаги квеста
- `POST /api/employees/{employee_id}/quests/{event_id}/steps/{step_number}/complete` - завершить шаг
- `POST /api/employees/{employee_id}/quests/{event_id}/complete` - завершить квест

### Game / Wallet / ESG

- `GET /api/game/{employee_id}/map` - карта развития
- `GET /api/game/{employee_id}/progress` - игровой прогресс
- `GET /api/game/{employee_id}/quests` - игровые квесты
- `GET /api/wallet/{employee_id}` - Growth Coins wallet
- `GET /api/esg-goals` - ESG goals
- `POST /api/esg-goals/{goal_id}/contribute` - отправить coins на ESG goal

### Pair learning / Teams

- `GET /api/pairs/invitations?employee_id={employee_id}` - список приглашений
- `POST /api/pairs/invitations` - опубликовать приглашение
- `GET /api/pairs/invitations/{invitation_id}/preview?employee_id={employee_id}` - проверить совместимость
- `POST /api/pairs/invitations/{invitation_id}/respond` - принять или отклонить приглашение
- `POST /api/teams` - создать команду
- `GET /api/teams/{team_id}` - получить команду
- `POST /api/teams/{team_id}/join` - вступить в команду

### HR / Import

- `GET /api/hr/dashboard` - HR dashboard
- `GET /api/hr/esg-engagement` - ESG engagement analytics
- `POST /api/import/dataset` - импорт dataset
- `POST /api/import/check-profiles` - импорт employees JSON
- `POST /api/import/check-history` - импорт activity history CSV
- `POST /api/import/events` - импорт events JSON
- `POST /api/import/skills` - импорт skills JSON

## Тестирование

Backend:

```bash
cd hack-fe3472cb-aevix
pytest
```

Frontend:

```bash
cd ../career-quest-frontend
npm run build
```

Docker Compose config:

```bash
cd hack-fe3472cb-aevix
docker compose config
```

## Troubleshooting

### Backend не запускается

- Проверь `.env`
- Проверь, что порт `8000` свободен
- Посмотри логи:

```bash
docker compose logs backend
```

### Frontend не видит backend

- Проверь, что backend отвечает: http://localhost:8000/health
- В Docker Compose frontend собирается с `VITE_API_URL=http://localhost:8000`
- Пересобери frontend после изменения env:

```bash
docker compose build frontend
docker compose up -d frontend
```

### AI отвечает медленно

- Используй более быструю модель:

```env
OPENAI_MODEL=gpt-6-sol
```

- Пока модель думает, frontend показывает progress bar.
- Без `OPENAI_API_KEY` backend использует template fallback.

### Рекомендации пустые

- Проверь, что demo dataset импортировался при старте backend
- Проверь employee ID, например `E0002`
- Перезапусти backend или выполни import endpoint

---

**AEVIX v1.0** - AI Career Quest Platform
