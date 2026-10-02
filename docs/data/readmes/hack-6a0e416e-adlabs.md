# Career Quest

Career Quest - hackathon MVP для персонального развития сотрудников. Проект помогает сотруднику увидеть разрыв навыков до целевой роли, получить объяснимый план развития и проверить, как конкретная обучающая активность меняет готовность к карьерной цели.

Для HR реализован агрегированный обзор прогресса по сотрудникам и отделам. В демо нет авторизации: выбор Employee/HR режима меняет пользовательский сценарий в интерфейсе.

## Кратко о проблеме

В компаниях часто уже есть данные о ролях, навыках, обучающих мероприятиях и истории участия, но сотруднику сложно понять:

- какие навыки мешают перейти на следующий грейд;
- какая активность даст максимальный эффект;
- почему система рекомендует именно этот шаг;
- что изменится после завершения обучения.

Career Quest собирает эти данные в один сценарий: профиль сотрудника -> gap analysis -> рекомендации -> roadmap -> объяснение AI Navigator -> симуляция завершения активности.

## Что реализовано

- Выбор сотрудника из синтетического датасета.
- Employee mode с профилем, карьерной целью, readiness и gap analysis.
- Расчет skill gaps до целевой роли/грейда.
- Рекомендации 0-3 активностей, отсортированные по score.
- Score breakdown: покрытие критичных навыков, общий gap coverage, соответствие цели, вероятность завершения и time efficiency.
- Roadmap до 3 последовательных шагов с пересчетом после каждого виртуального шага.
- Детальная карточка активности: описание, формат, длительность, prerequisites, developed skills, forecast, eligibility.
- Демо-действия `enroll`, `start`, `complete`.
- После `complete` backend обновляет in-memory состояние: effective skills, readiness, recommendations, roadmap и activity history.
- AI Navigator с ответами по evidence packet: факты, причина, ожидаемый эффект, ограничения, следующий шаг и source IDs.
- Offline/template режим AI Navigator без API-ключей.
- Опциональные интеграции с OpenAI Responses API и NVIDIA API при наличии ключей.
- HR overview: количество сотрудников, цели, готовность, средний прогресс, распределение по грейдам и отделам.
- API contract, demo script, финальные notes для защиты.

## Как работает решение

1. Backend загружает датасет из `datasets/career_quest`.
2. Frontend получает список сотрудников и показывает Employee/HR сценарии.
3. Для сотрудника Career Engine определяет цель: явная `career_goal` из датасета или следующий грейд, если цель не задана.
4. Engine сравнивает текущие/effective skills с требованиями target role profile.
5. На основе gaps и каталога events система считает рекомендации, прогноз влияния и roadmap.
6. AI Navigator получает только ограниченный evidence packet и объясняет уже рассчитанный результат.
7. При завершении активности изменения применяются в памяти процесса backend. Исходные JSON/CSV файлы не меняются.
8. После перезапуска backend демо-состояние сбрасывается к данным из датасета.

## Технологии

### Backend

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- httpx
- python-dotenv
- pytest

### Frontend

- React 18
- TypeScript
- Vite
- lucide-react

### AI, API и внешние сервисы

- `TemplateAIProvider` - режим по умолчанию, работает без интернета и ключей.
- OpenAI Responses API - опционально через `OPENAI_API_KEY`.
- NVIDIA API - опционально через `NVIDIA_API_KEY`.
- Внешняя модель не выбирает и не ранжирует активности. Ranking, forecast и roadmap считает локальный deterministic engine.
- Ответ внешнего провайдера валидируется Pydantic-схемой и проверяется на неизвестные ID и неподдержанные числа.

## Архитектура проекта

```text
datasets/career_quest
        |
        v
backend/app/data.py
  загрузка и валидация JSON/CSV
        |
        v
ml/engine.py
  target resolution
  skill gaps
  recommendations
  roadmap
        |
        v
backend/app/main.py
  FastAPI JSON API
        |
        v
frontend/src
  React/Vite интерфейс
```

Основные директории:

| Путь | Назначение |
| --- | --- |
| `backend/app/` | FastAPI backend, API endpoints, Pydantic models, AI providers |
| `backend/app/services/` | Navigator service и AI provider chain |
| `ml/engine.py` | Детерминированная логика рекомендаций, gaps, roadmap и skill gains |
| `frontend/` | React + TypeScript frontend |
| `datasets/career_quest/` | Датасет сотрудников, навыков, ролей, events и истории |
| `contracts/` | API contract и shared types |
| `docs/` | MVP spec, demo script, jury Q&A, final checklist, AI integration notes |
| `scripts/` | Smoke/eval/check scripts для демо и AI providers |

## Данные

Датасет находится в `datasets/career_quest`.

| Файл | Содержимое |
| --- | --- |
| `skills.json` | Каталог навыков, шкала 0-5, требования role profiles |
| `employees.json` | 200 синтетических профилей сотрудников |
| `events.json` | 40 обучающих мероприятий |
| `activity_history.csv` | 2 743 записи истории участия |

Дата среза данных: `2026-10-01`.

Все люди и компании в датасете вымышлены. Подробное описание структуры есть в `datasets/career_quest/README.ru.md`.

## Установка и запуск

### Требования

- Python 3.11 или новее
- Node.js 20.19 или новее
- npm

Проект в `main` запускается локально без Docker.

### Windows PowerShell

Первичная установка из корня репозитория:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm --prefix frontend install
```

Запуск API в первом окне PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Запуск frontend во втором окне PowerShell:

```powershell
npm --prefix frontend run dev
```

Откройте:

- Frontend: <http://localhost:5173>
- API health: <http://localhost:8000/api/health>
- Swagger/OpenAPI docs: <http://localhost:8000/docs>

### macOS/Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
npm --prefix frontend install
```

API:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
npm --prefix frontend run dev
```

Откройте <http://localhost:5173>.

## Конфигурация AI Navigator

По умолчанию проект работает без `.env` и без внешних API:

```text
AI_PROVIDER=template
AI_FALLBACK_PROVIDER=template
```

Чтобы попробовать реальные провайдеры, скопируйте `.env.example` в `.env` и заполните ключи:

```text
OPENAI_API_KEY=
NVIDIA_API_KEY=
```

Поддерживаемые переменные:

| Переменная | Назначение |
| --- | --- |
| `AI_PROVIDER` | `template`, `openai` или `nvidia` |
| `AI_FALLBACK_PROVIDER` | fallback provider |
| `OPENAI_API_KEY` | ключ OpenAI |
| `NVIDIA_API_KEY` | ключ NVIDIA |
| `OPENAI_MODEL` | модель OpenAI, default `gpt-4o-mini` |
| `NVIDIA_MODEL` | модель NVIDIA, default `openai/gpt-oss-20b` |
| `NVIDIA_BASE_URL` | base URL NVIDIA API |

Если ключи не заданы, Navigator остается в offline/template режиме.

## Как проверить решение жюри

Быстрый сценарий:

1. Запустите API и frontend по инструкции выше.
2. Откройте <http://localhost:5173>.
3. В Employee mode используйте предвыбранного сотрудника `E0100` или выберите другого.
4. Проверьте overview: целевая роль, readiness, ключевой gap и первая активность.
5. Откройте **Activities** и нажмите **Подробнее и начать** на рекомендации.
6. Посмотрите описание, prerequisites, skill gains, forecast и source IDs.
7. Выполните последовательность **Записаться -> Начать -> Отметить выполненным**.
8. Убедитесь, что readiness, recommendations, roadmap и activity history обновились.
9. Откройте **Roadmap** и проверьте последовательность шагов.
10. Откройте **AI Navigator** и задайте вопрос, например: `Почему эта активность лучше второй?`.
11. Перейдите в HR overview и проверьте агрегированные показатели.

Повторяемый golden path описан в `docs/DEMO_SCRIPT.md`. Smoke script проверяет тот же сценарий в API:

```bash
.venv/bin/python scripts/demo_smoke_test.py
```

Для Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\demo_smoke_test.py
```

## API

Base URL:

```text
http://localhost:8000/api
```

Основные endpoints:

| Method | Path | Назначение |
| --- | --- | --- |
| `GET` | `/health` | Проверка состояния API и датасета |
| `GET` | `/ai/status` | Статус AI provider chain без секретов |
| `GET` | `/employees` | Список сотрудников |
| `GET` | `/employees/{employee_id}` | Профиль сотрудника |
| `GET` | `/employees/{employee_id}/skill-gap` | Gap analysis |
| `GET` | `/employees/{employee_id}/recommendations` | Рекомендации |
| `GET` | `/employees/{employee_id}/roadmap` | Roadmap |
| `GET` | `/employees/{employee_id}/activities/{event_id}` | Детали активности |
| `GET` | `/employees/{employee_id}/activity-history` | История активности |
| `POST` | `/employees/{employee_id}/activities/{event_id}/actions/enroll` | Записаться |
| `POST` | `/employees/{employee_id}/activities/{event_id}/actions/start` | Начать |
| `POST` | `/employees/{employee_id}/activities/{event_id}/complete` | Завершить |
| `POST` | `/employees/{employee_id}/navigator/ask` | Вопрос AI Navigator |
| `GET` | `/hr/overview` | HR overview |

Полный контракт: `contracts/api.md`.

## Проверки

Backend tests:

```bash
.venv/bin/python -m pytest backend/tests tests -q --basetemp .pytest_local
```

Frontend typecheck/build:

```bash
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Проверка AI provider credentials:

```bash
.venv/bin/python scripts/check_ai_providers.py
```

Eval на пяти cases:

```bash
.venv/bin/python scripts/eval_ai_providers.py
```

Если ключи отсутствуют, AI scripts сообщат `BLOCKED_BY_MISSING_KEY`. Это ожидаемо для offline/template режима.

## Ограничения текущей версии

- Это hackathon MVP, не production HR/LMS платформа.
- Данные синтетические; реальные персональные данные не используются.
- Демо-действия хранятся в памяти backend и сбрасываются после перезапуска.
- Нет авторизации, ролей доступа и SSO.
- Полноценная интеграция с LMS/HRIS не реализована; dataset содержит только ссылки, если они явно есть в данных.
- Внешние OpenAI/NVIDIA ответы считаются опциональными и требуют ключей.
- В репозитории не подтверждена deployed-версия.

## Deployed-версия

Подтвержденной deployed-ссылки в репозитории нет. Проект рассчитан на локальный запуск.

## Полезные документы

- `docs/MVP_SPEC.md` - описание MVP behavior
- `docs/DEMO_SCRIPT.md` - сценарий демонстрации
- `docs/FINAL_GAP_ANALYSIS.md` - финальные gaps и ограничения
- `docs/AI_INTEGRATION.md` - статус AI-интеграции
- `docs/JURY_QA.md` - вопросы и ответы для защиты
- `docs/FINAL_CHECKLIST.md` - checklist перед демонстрацией
- `contracts/api.md` - API contract
- `datasets/career_quest/README.ru.md` - описание датасета
