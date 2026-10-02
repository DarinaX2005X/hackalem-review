# Akim AI — «Аким на 5 часов»

> **AI-симулятор городских управленческих решений для HackAlem AI 2026 · Astana Innovations**

**100 единиц бюджета · 5 игровых районов · 14 инициатив · только 5 решений**

Akim AI помогает увидеть последствия управленческого сценария **до его реализации**: пользователь распределяет ограниченный бюджет, принимает пять решений, запускает детерминированную симуляцию и получает изменение районных показателей, Astana Quality of Life Score и объяснение основных компромиссов от AI Advisor.

> **Simulation Engine считает. AI объясняет. Человек принимает решение.**

## Ссылки

- **Рабочий продукт:** https://helpmake-id.live/
- **API / Swagger:** https://api.helpmake-id.live/docs
- **Frontend:** [frontend/README.md](frontend/README.md)
- **AI Advisor:** [docs/AI_ADVISOR.md](docs/AI_ADVISOR.md)
- **Архитектурные решения:** [docs/DECISIONS.md](docs/DECISIONS.md)
- **Исходное ТЗ:** [docs/task-brief.md](docs/task-brief.md)
- **Описание датасета:** [docs/district-dataset.md](docs/district-dataset.md)

---

## Проблема

При развитии города приходится одновременно учитывать транспорт, озеленение и экологию, социальную инфраструктуру, безопасность и качество городских сервисов. При ограниченном бюджете отдельное решение может улучшить один район или показатель, но оставить другую проблему нерешённой.

Главная продуктовая задача Akim AI — дать пользователю возможность **сравнивать управленческие сценарии и видеть их последствия и компромиссы на одной воспроизводимой модели**.

## Пользователь и ценность

Основные пользователи в рамках задания:

- городской управленец;
- аналитик;
- пользователь симулятора.

Akim AI не заменяет управленца и не выдаёт AI-мнение за математический прогноз. Он разделяет ответственность:

1. **человек выбирает стратегию;**
2. **Simulation Engine рассчитывает последствия;**
3. **AI Advisor объясняет рассчитанный результат и помогает исследовать альтернативы.**

---

## Как работает продукт

```text
Состояние города
      ↓
100 единиц бюджета
      ↓
5 управленческих решений
      ↓
Validator
      ↓
Deterministic Simulation Engine
      ↓
Before / After + Q0–Q8 + Quality of Life Score
      ↓
AI Advisor
      ↓
Объяснение / риски / компромиссы / альтернативы
      ↓
Новый сценарий или сравнение сценариев
```

### Основной demo-flow

1. Открыть **Situation Center**.
2. Посмотреть исходное состояние пяти игровых районов.
3. Выбрать ровно пять инициатив из M1–M14.
4. Следить за бюджетом и пройти backend validation.
5. Нажать **Simulate**.
6. Получить Score и изменения районов **Before / After**.
7. Посмотреть динамику **Q0–Q8** с учётом lag.
8. Получить AI-объяснение рассчитанного результата.
9. Изменить стратегию или сохранить сценарии для сравнения.

---

## Соответствие заданию HackAlem

### Must Have

| Требование | Реализация |
| --- | --- |
| Единый виртуальный бюджет | **100** единиц для всех сценариев |
| Решения по пяти направлениям | Транспорт, экология/озеленение, социальная инфраструктура, безопасность, городской сервис |
| Пять управленческих решений | Validator требует ровно 5 инициатив |
| Автоматический контроль бюджета | Backend отклоняет невалидный сценарий |
| AI-анализ решений | `/advisor/explain` |
| Astana Quality of Life Score | Детерминированный scoring engine |
| Сильные стороны, риски и последствия | Grounded AI Advisor |
| Решения меняют показатели | Effects, lag, synergies и Q0–Q8 |
| Другой набор решений → другой результат | Каждый валидный сценарий пересчитывается Simulation Engine |

### Дополнительно реализовано

- визуализация изменений районов;
- поквартальная симуляция Q0–Q8;
- AI-рекомендации по проверенным альтернативам;
- вопросы к сценарию через AI Advisor;
- сохранение сценариев;
- сравнение двух сценариев;
- PostgreSQL persistence;
- воспроизводимый backend demo-flow.

Не реализованные optional-функции — неожиданные городские события и автоматическая генерация презентации — не требуются для основного сценария MVP.

---

## Ключевые возможности

### 🏙️ Situation Center
Показывает пять игровых районов, их исходные показатели, бюджет и доступные инициативы.

### 💰 Управление ограниченным бюджетом
Пользователь получает 100 условных единиц и должен принять ровно пять решений.

### 🧮 Детерминированная симуляция
Все числовые результаты рассчитываются backend-кодом. LLM не рассчитывает официальный Score.

### ⏱️ Временная динамика
Simulation Engine возвращает Q0–Q8 и учитывает implementation lag каждой инициативы.

### 🤖 Grounded AI Advisor
AI работает только с подготовленными backend-фактами и проверенными альтернативами. При недоступности AI числовая симуляция продолжает работать.

### 🔄 Сохранение и сравнение сценариев
Сценарии сохраняются в PostgreSQL и могут сравниваться по Score, бюджету, районам, показателям и критическим парам.

---

## Архитектура

```text
┌────────────────────────────────────┐
│ Frontend — React + TypeScript      │
│ Situation Center / Decisions / UI  │
└─────────────────┬──────────────────┘
                  │ REST API
                  ▼
┌────────────────────────────────────┐
│ Backend — FastAPI                  │
│ Validator / API / Scenario layer   │
└───────────┬───────────────┬────────┘
            │               │
            ▼               ▼
┌──────────────────┐  ┌──────────────────┐
│ Simulation Engine│  │ AI Advisor       │
│ deterministic    │  │ grounded AI      │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
          Structured Result
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     Frontend UI          PostgreSQL
```

### Почему AI отделён от математики

AI не является источником числовой истины. Перед вызовом AI backend проверяет актуальность результата и формирует ограниченный набор фактов. Рекомендации строятся только из кандидатов, которые предварительно прошли Validator и Simulation Engine.

Это делает систему:

- воспроизводимой;
- тестируемой;
- устойчивой к числовым галлюцинациям;
- работоспособной даже при недоступности AI provider.

Подробнее: [AI Advisor V1](docs/AI_ADVISOR.md).

---

## Датасет и модель

Проект использует предоставленный для хакатона **синтетический датасет**, не содержащий персональных или ограниченных данных.

- 5 игровых районов;
- 10 индикаторов;
- 14 инициатив;
- бюджет 100;
- горизонт H = 8 кварталов;
- эффекты, lag, synergies и incompatibilities.

Версия датасета: **1.1.0**. Backend также публикует `dataset_hash` для контроля воспроизводимости.

### Astana Quality of Life Score

Для меры с лагом `L` реализованная доля эффекта в квартале `q` определяется моделью симуляции. Итоговый Score:

```text
Score = 0.7 × D_avg
      + 0.3 × min(D_d)
      - N_crit
```

где:

- `D_avg` — средневзвешенный районный Score;
- `min(D_d)` — Score слабейшего района;
- `N_crit` — число пар «район × показатель» со значением строго ниже 40.

Проверенный baseline: **52.56**.

Подробное описание: [docs/district-dataset.md](docs/district-dataset.md).

---

## Технологический стек

### Frontend
- React 19
- TypeScript
- Vite

### Backend
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy Core
- asyncpg

### Database
- PostgreSQL 17
- Alembic migrations

### AI
- OpenAI-compatible Chat Completions API
- Grounded Advisor contract

### QA / Infrastructure
- pytest / pytest-cov
- Ruff
- Docker / Docker Compose
- Nginx

---

## Структура репозитория

```text
/
├── frontend/              # React + TypeScript Situation Center
├── backend/               # FastAPI, Simulation Engine, AI, tests
├── docs/                  # ТЗ, dataset, AI contract, architecture
├── design/                # UI/UX design materials
├── deploy/                # Deployment scripts/config examples
├── openapi.json           # API schema
└── README.md
```

---

## Локальный запуск всего проекта

Подробные шаги и проверка запуска: [гайд по локальному запуску](docs/local-setup.md). В приватном репозитории уже есть `backend/.env` с настройками для команды; копировать `.env.example` не нужно.

### Требования

- Docker + Docker Compose
- Python 3.12+ для локальной backend-разработки
- Node.js 20.19+ для frontend

### 1. Backend

```bash
cd backend
docker compose up --build -d
```

Backend: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

Для запуска вне Docker необходимо запустить PostgreSQL, задать `DATABASE_URL`, выполнить `make migrate` и `make dev`.

### 2. Frontend

Во втором терминале:

```bash
cd frontend
npm ci
npm run dev
```

Vite проксирует `/api` на локальный backend. Для другого backend можно задать `AKIM_API_URL`; для production build используется `VITE_API_BASE_URL`.

---

## API v1

| Метод и путь | Назначение |
| --- | --- |
| `GET /api/v1/health` | Проверка процесса |
| `GET /api/v1/ready` | Проверка датасета и PostgreSQL |
| `GET /api/v1/data` | Районы, индикаторы, меры, правила, map anchors |
| `POST /api/v1/simulate` | Валидация и расчёт Q0–Q8 |
| `POST /api/v1/advisor/explain` | Объяснение результата |
| `POST /api/v1/advisor/recommend` | Проверенные альтернативы |
| `POST /api/v1/advisor/ask` | Ответ на вопрос по фактам сценария |
| `POST /api/v1/scenarios` | Сохранить пересчитанный сценарий |
| `GET /api/v1/scenarios` | Получить список сценариев |
| `GET /api/v1/scenarios/{id}` | Получить сценарий |
| `DELETE /api/v1/scenarios/{id}` | Удалить сценарий |
| `POST /api/v1/scenarios/compare` | Сравнить два сценария |

Полная схема: [openapi.json](openapi.json) или Swagger работающего API.

### Контрольный пример

```json
{
  "decisions": [
    {"measure_id": "M7", "district_code": "nura"},
    {"measure_id": "M8", "district_code": "nura"},
    {"measure_id": "M10", "district_code": "nura"},
    {"measure_id": "M12"},
    {"measure_id": "M5", "district_code": "saryarka"}
  ]
}
```

Ожидаемые ключевые поля:

```text
valid = true
spent = 95
remaining_budget = 5
baseline_score = 52.56
score = 56.54
Q0 = 52.56
Q8 = 56.54
```

---

## Проверка и воспроизводимость

### Backend

```bash
cd backend
make check
make test
```

Coverage gate: **90%**.

### Frontend

```bash
cd frontend
npm ci
npm run build
```

### Автоматический backend demo-flow

При запущенном backend:

```bash
cd backend
.venv/bin/python scripts/demo_flow.py
```

Скрипт проверяет `/data`, `/simulate`, маршруты Advisor, сохранение двух сценариев, чтение, сравнение и cleanup. Числовой flow работает даже без AI API.

---

## AI и сторонние инструменты

В соответствии с требованиями хакатона команда раскрывает использование AI, сторонних библиотек и предоставленных материалов.

| Инструмент / материал | Использование |
| --- | --- |
| ChatGPT | Product analysis, архитектура, документация, prompt design, QA |
| Codex | Помощь в разработке и анализе кода |
| OpenAI-compatible API | Runtime AI Advisor |
| React / ReactDOM | Frontend |
| Vite / TypeScript | Frontend build и типизация |
| FastAPI / Pydantic | Backend API и схемы |
| SQLAlchemy Core / asyncpg | Доступ к PostgreSQL |
| PostgreSQL / Alembic | Хранение сценариев и миграции |
| pytest / Ruff | Тестирование и качество кода |
| Docker / Nginx | Сборка и deployment |
| HackAlem synthetic dataset | Источник данных и правил симуляции |
| Smart City materials | Предметный контекст и продуктовый reference |
| Figma | UI/UX design |

AI-assisted разработка не меняет принцип источника истины: числовые результаты продукта определяет только Simulation Engine.

---

## Команда и вклад

| Участник | Роль | Основной вклад |
| --- | --- | --- |
| **Ануар** | Product / AI Logic / Documentation | Product concept, scope, AI Advisor contract, README, product/AI QA, demo и pitch |
| **Дамир** | Backend / AI / Infrastructure | Dataset, Validator, Simulation Engine, Score, API, AI integration, PostgreSQL, tests и deployment |
| **Дарья** | Frontend / UX | Situation Center, React frontend, визуализация, API integration, UI/UX |

Git history репозитория отражает вклад участников отдельными содержательными коммитами.

---

## Потенциал развития

Текущий MVP уже разделяет математическую модель и AI-интерпретацию, поэтому архитектуру можно расширять без передачи LLM ответственности за расчёты.

Следующие возможные уровни:

1. более развитое сравнение нескольких стратегий;
2. goal-based AI recommendations;
3. городские события с детерминированными эффектами;
4. более богатая временная визуализация;
5. подключение реальных открытых городских данных при наличии валидированного источника;
6. GIS/digital-twin integration как отдельный будущий слой.

Эти направления являются roadmap, а не заявлением о текущей функциональности.

---

## Ограничения MVP

- Все городские показатели, стоимость и эффекты в текущем MVP синтетические.
- Результат не является прогнозом реальной городской политики.
- Карта использует условные illustrative anchors, а не официальные GIS-границы.
- Учётных записей и приватных пользовательских сценариев в MVP нет.
- AI может быть недоступен; математическая симуляция при этом продолжает работать.
- Неожиданные городские события и автоматическая генерация презентации пока не реализованы.

---

## Документация

- [Исходное ТЗ](docs/task-brief.md)
- [Датасет и правила](docs/district-dataset.md)
- [AI Advisor V1](docs/AI_ADVISOR.md)
- [Архитектурные решения](docs/DECISIONS.md)
- [Deployment](docs/deployment.md)
- [Локальный запуск](docs/local-setup.md)
- [Frontend](frontend/README.md)

---

## Disclaimer

Akim AI — хакатонный прототип на синтетических данных. Он демонстрирует подход к scenario-based decision support и не должен интерпретироваться как официальный прогноз, рекомендация или производственная система городского управления.
