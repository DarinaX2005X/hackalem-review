# Career Quest

AI-навигатор карьерного развития сотрудников для HackAlem AI / Halyk Bank.

Сотруднику сложно увидеть связь между обучением, текущими навыками и следующим карьерным шагом. Career Quest показывает профиль и карьерную траекторию, выявляет разрывы в навыках и предлагает 1–3 объяснимые развивающие активности. HR получает агрегированный обзор skill gaps и участия в активностях.

## Что реализовано

- выбор сотрудника и просмотр его профиля;
- текущий и целевой грейд, навыки и требования карьерной траектории;
- история активностей;
- rule-based подбор 1–3 подходящих активностей с объяснениями;
- пересчёт in-memory прогресса после завершения активности;
- HR-панель: skill gaps, сотрудники без рекомендации и участие в мероприятиях;
- импорт дополнительных `employees.json` и `activity_history.csv` через API;
- детерминированный fallback без внешнего LLM.

## Основной сценарий

1. Frontend загружает список сотрудников из FastAPI.
2. Для выбранного сотрудника backend рассчитывает effective skills: учитывает завершённые после review активности и ограничение `max_level`.
3. Система определяет требования цели/следующего грейда, skill gaps и critical skills.
4. Недопустимые мероприятия исключаются по роли, грейду, prerequisites, истории completed и доступности.
5. Rule-based scoring ранжирует кандидатов по gap reduction, critical skills, career goal, history fit и feasibility.
6. Пользователь видит до трёх рекомендаций с подтверждёнными факторами и может завершить активность.
7. HR-панель показывает агрегированные данные без персональных рейтингов.

## AI и рекомендации

Основой является explainable hybrid recommendation engine: eligibility, score, evidence и тексты факторов рассчитываются локально в backend. Это позволяет приложению работать без внешних AI-сервисов.

Опционально настроенный OpenAI Responses API выполняет только reranking deterministic top-8 до трёх событий. Ему передаются event ID, название, deterministic score и подтверждённые evidence IDs/facts — без полного профиля, истории сотрудника или ключа. Ответ строго валидируется; при отсутствии `OPENAI_API_KEY`, timeout, API-ошибке или невалидном ответе backend возвращает deterministic top-3.

Модель задаётся переменной `OPENAI_MODEL`; шаблон указывает `gpt-4o-mini`.

## Стек

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui, Recharts.
- Backend: Python 3.12+, FastAPI, Pydantic, httpx, OpenAI SDK.
- Данные: JSON и CSV.
- Контейнеризация backend: Docker.

## Архитектура

```text
Next.js frontend
        |
        v
FastAPI API (/api)
        |
        +--> data loader --> employees.json / events.json / skills.json / activity_history.csv
        |
        +--> deterministic recommendation engine
        |         |
        |         +--> optional OpenAI Responses reranker
        |
        +--> HR analytics
```

Frontend обращается только к FastAPI. Backend загружает и валидирует датасет при старте; изменения после Complete и импортированные данные хранятся в памяти процесса.

## Структура

```text
Career Quest/
├── frontend/                         # Next.js интерфейс
├── backend/
│   ├── app/                          # FastAPI, services и schemas
│   ├── data/raw/career_quest_dataset/# исходный датасет
│   ├── scripts/check_openai.py       # ручная проверка OpenAI
│   ├── tests/                        # backend tests
│   └── Dockerfile
├── docs/                             # задача, архитектура и API-заметки
└── README.md
```

## Данные

Используется синтетический датасет из `backend/data/raw/career_quest_dataset/`:

- `employees.json` — профили сотрудников;
- `events.json` — каталог развивающих мероприятий;
- `skills.json` — навыки и требования ролей/грейдов;
- `activity_history.csv` — история участия в активностях.

Датасет загружается только backend. Frontend не читает JSON или CSV напрямую.

## Требования

- Python 3.12 или новее;
- Node.js и Corepack/pnpm (проект фиксирует `pnpm@12.3.4`);
- Docker — опционально, для контейнерного backend.

## Переменные окружения

### Frontend

Создайте `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```

### Backend

`backend/.env` необязателен. Без него работает локальный deterministic ranking. Для OpenAI reranking создайте его по `backend/.env.example`:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` хранится только в окружении или `backend/.env` и не должен попадать в Git. Значения переменных операционной системы имеют приоритет над `.env`.

## Быстрый запуск

### 1. Клонирование

```powershell
git clone <repository-url>
cd <repository-directory>
```

### 2. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend доступен по `http://127.0.0.1:8000`; интерактивная OpenAPI-документация FastAPI — `http://127.0.0.1:8000/docs`.

### 3. Frontend

В отдельном терминале из корня репозитория:

```powershell
cd frontend
corepack enable
pnpm install
pnpm dev
```

Откройте `http://localhost:3000`.

## Проверка для жюри

1. Запустите backend и frontend.
2. Откройте приложение и выберите сотрудника в верхнем списке.
3. На странице «Профиль сотрудника» проверьте грейд, навыки и историю активностей.
4. Перейдите в «Рекомендации»: отображаются от одной до трёх активностей и причины выбора.
5. Завершите рекомендованную активность и убедитесь, что интерфейс обновляет прогресс.
6. Откройте «HR-панель» для агрегированных skill gaps и статистики участия.

## Основные API endpoints

| Метод | Путь | Назначение |
| --- | --- | --- |
| GET | `/health` | Проверка доступности backend. |
| GET | `/api/employees` | Список сотрудников. |
| GET | `/api/employees/{employee_id}` | Профиль сотрудника. |
| GET | `/api/employees/{employee_id}/trajectory` | Карьерная траектория и gaps. |
| GET | `/api/employees/{employee_id}/activities` | История активностей. |
| GET | `/api/employees/{employee_id}/recommendations` | Рекомендации. |
| POST | `/api/employees/{employee_id}/complete/{event_id}` | Завершить активность в памяти. |
| GET | `/api/hr/dashboard` | HR-агрегации. |
| POST | `/api/import` | Импорт проверочных profiles/history. |

Также доступны совместимые маршруты `/api/hr-dashboard` и `/api/recommendations/{recommendation_id}/complete`.

## Тесты и production build

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

```powershell
cd frontend
pnpm build
```

## Deployment

Backend можно собрать с имеющимся Dockerfile:

```powershell
cd backend
docker build -t career-quest-backend .
docker run --rm -p 8000:8000 career-quest-backend
```

Для frontend нужен production API URL в `NEXT_PUBLIC_API_URL`; backend CORS разрешает `http://localhost:3000` и `http://127.0.0.1:3000`. Конфигурация конкретного хостинга для frontend или backend в репозитории отсутствует.

### Checklist перед деплоем

- [ ] Backend production dependencies установлены.
- [ ] `NEXT_PUBLIC_API_URL` указывает на доступный backend API.
- [ ] CORS дополнен production origin при необходимости.
- [ ] При использовании OpenAI секрет задан только через environment variables.
- [ ] Проверены `pytest` и `pnpm build`.
- [ ] Пройден основной пользовательский сценарий.

## Демо

Deployed-версия: [Добавить ссылку после деплоя]

## Ограничения MVP

- Данные синтетические.
- Полноценная авторизация не реализована.
- Complete, импортированные данные и cache хранятся только в памяти процесса и сбрасываются после перезапуска backend.
- OpenAI reranking необязателен; без ключа используется deterministic ranking.
