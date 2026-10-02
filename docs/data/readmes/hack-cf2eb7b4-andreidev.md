# Агент тарифных кампаний

`agent.py`: портфель экспертов (история + LLM) предлагает гипотезы → адаптивные пилоты → жадный план под лимиты. pandas/numpy + stdlib. Без LLM-ключа (`OPENROUTER_API_KEY` / `OPENAI_API_KEY`) детерминирован.

**Назначение.** Агент для телеком-оператора: сам проводит пилоты на аудитории и отдаёт план до 10 кампаний (кому, какой тариф, какой канал), чтобы чистый прирост ARPU был максимальным при лимитах бюджета, охвата и числа пилотов. Пользователь — аналитик маркетинга. Для него есть веб-интерфейс Campaign Cockpit: видно, почему агент принял каждое решение. Для менеджера — упрощённый экран «сформировать план → CSV».

## Быстрый старт (проверка с чистого клона)
Требования: Python 3.13 (на нём проверено), для UI — Node 22 или Docker.

1. **Положить пакет среды и данных в корень репо.** В git он не коммитится (`.gitignore`). Нужны файлы: `local_eval.py`, `make_submission.py`, `environment.py`, `mock_environment.py`, `scoring_core.py`, `customer_profile.csv`, `feature_dictionary.csv`, `tariff_dictionary.csv` и папка `data/` (`change_tariff.csv`, `traffic.csv`, `arpu_monthly.csv`, `dict_tariff.csv`). Копия пакета лежит в релизе `participant-pkg` этого репо:
   ```bash
   gh release download participant-pkg -p participant-pkg.tar.gz && tar xzf participant-pkg.tar.gz && rm participant-pkg.tar.gz
   ```
2. **Установить зависимости агента:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Проверить основной сценарий:**
   ```bash
   python local_eval.py              # ожидается «Статус: PASS», net ≈ 4.4M, «Пилотов проведено: 20 из 20», нет строк «отброшена»
   python local_eval.py --runs 10    # устойчивость: все 10 прогонов в плюс
   python make_submission.py         # пересобирает submission.csv; должен совпасть с закоммиченным (git diff пуст)
   ```
4. **UI (по желанию):** см. «Сборка и запуск UI» ниже. Есть и офлайн-приложение для macOS и Windows — «Десктоп-приложение».

LLM-ключ не обязателен: без него LLM-эксперт выключается, и агент работает на истории и пилотах. Ключи и прочие настройки кладутся в `.env` в корне репо (см. [docs/configuration.md](docs/configuration.md)):
```bash
OPENROUTER_API_KEY=...        # или OPENAI_API_KEY=...
LLM_MODEL=openai/gpt-4o-mini
```

## Сборка и запуск UI (Campaign Cockpit)
Пакет среды должен лежать в корне репо (шаг 1 быстрого старта): в образ он попадает из рабочей копии.

**Docker — одной командой** (Postgres + API + собранный фронт на одном порту):
```bash
docker compose up --build     # сборка образа и запуск → http://localhost:8000
docker compose down           # остановить; данные остаются в томах pgdata и uploads
```

**Локально для разработки** (hot reload фронта):
```bash
pip install -r requirements.txt fastapi uvicorn "fastapi-users[sqlalchemy]" "psycopg[binary]"
docker compose up -d db                           # только Postgres на 127.0.0.1:5432
AUTH_DEMO=1 uvicorn server:app --port 8000        # API из корня репо
cd web && npm ci && npm run dev                   # http://localhost:5173, /api проксируется на :8000
```

**Локально со сборкой фронта** (собранный фронт отдаёт сам API; Postgres и pip-зависимости — как в блоке выше):
```bash
cd web && npm ci && npm run build && cd ..        # tsc + vite build → web/dist
AUTH_DEMO=1 uvicorn server:app --port 8000        # http://localhost:8000
```

Swagger: http://localhost:8000/api/docs. Self-check'и и тесты — [docs/testing.md](docs/testing.md).

## Десктоп-приложение (macOS и Windows)
Кокпит собирается в офлайн-приложение на Tauri: без Docker, Postgres и Python у пользователя. Внутри лежат сервер (PyInstaller), фронт, агент и данные, хранилище — SQLite. Можно собрать версии и для **macOS** (`.dmg`, Apple Silicon), и для **Windows** (`.exe`-установщик и `.msi`).

```bash
bash desktop/build.sh     # на маке → desktop/src-tauri/target/release/bundle/dmg/*.dmg; на Windows (Git Bash) → bundle/nsis/*.exe, bundle/msi/*.msi
```
Нужны Python 3.13, Node 22, Rust и пакет среды в корне. Обе версии разом собирает GitHub Actions: Actions → **desktop** → Run workflow (или тег `v*`), установщики лежат в артефактах прогона. Вход — те же демо-пользователи. Каталог данных, `.env` для LLM-ключа и ограничения описаны в [docs/desktop.md](docs/desktop.md): promote лаборатории и CatBoost в десктопе недоступны, сборка не подписана.

## Вход
При пустой таблице пользователей и `AUTH_DEMO=1` (по умолчанию в `docker compose`) заводятся демо-пользователи, пароль равен роли:

| Роль | Email | Пароль | Что видит |
|---|---|---|---|
| manager | `manager@cockpit.demo` | `manager` | «Сформировать план» → таблица кампаний → CSV |
| analyst | `analyst@cockpit.demo` | `analyst` | весь кокпит без лаборатории |
| admin | `admin@cockpit.demo` | `admin` | кокпит + лаборатория версий и загрузка базовых выгрузок |

Свой пользователь или смена пароля и роли:
```bash
python3 auth.py add boss@corp.ru 'пароль' manager
```
**На стенде демо-пароли не используйте:** задайте в `.env` `AUTH_DEMO=0`, `AUTH_USERS="email:пароль:роль,..."` и `AUTH_SECRET`. Без `AUTH_USERS` и `AUTH_DEMO=1` сервер на пустой таблице не стартует. Подробнее — [SECURITY.md](SECURITY.md).

## Архитектура
```
пакет среды (env, data/) ──▶ agent.py ──▶ план кампаний ──▶ make_submission.py ──▶ submission.csv
                                       │  ▲
                        агрегаты ячеек ▼  │ до 2 target на ячейку
                                 LLM (OpenRouter / OpenAI, опционально)

web/ (React) ──/api──▶ server.py (FastAPI) ──▶ agent.py в мок- или стресс-мире
                            │                  lab.py: версии настроек, матрица тестов, gate
                            ▼
                        Postgres (db.py, auth.py): пользователи, сессии, версии, аудит LLM
```
- `agent.py` — агент (`Agent.act(env)`). От БД и UI не зависит.
- `stress_eval.py` — локальный стенд: искажённые и жёсткие миры для проверки устойчивости.
- `lab.py` — лаборатория версий настроек агента (цикл самоулучшения с gate).
- `server.py`, `auth.py`, `db.py`, `web/` — Campaign Cockpit: API, роли, хранилище, фронтенд.

Все модули и поток данных — [docs/architecture.md](docs/architecture.md).

## Технологии
- **Агент:** Python, pandas, numpy, stdlib (`urllib` для LLM); CatBoost — только в опциональном режиме `PRIOR_MODEL=catboost_*`. Байесовские апостериоры, expected improvement для выбора пилотов, LCB-отбор и жадный план.
- **LLM:** OpenAI-совместимый API — OpenRouter (по умолчанию `openai/gpt-4o-mini`) или OpenAI (`gpt-4o-mini`).
- **Бэкенд UI:** FastAPI, Uvicorn, fastapi-users (SQLAlchemy), psycopg, PostgreSQL 17.
- **Фронтенд:** React 19, HeroUI v3, Vite 8, TypeScript.
- **Запуск:** Docker, Docker Compose; десктоп — Tauri v2 (Rust) + PyInstaller, SQLite вместо Postgres.

## Документация
| Документ | О чём |
|---|---|
| [Архитектура](docs/architecture.md) | модули, поток данных, файлы пакета среды, структура фронтенда |
| [Как работает агент](docs/agent.md) | ключевое наблюдение, prior, эксперты, EI-пилоты, план, fallback, честная игра |
| [Настройки](docs/configuration.md) | переменные окружения и константы `agent.py` |
| [CatBoost-prior](docs/catboost.md) | опциональный ML-prior: зачем, как устроен, как включить, почему выключен |
| [Данные и эксперименты](docs/experiments.md) | что показали данные, стресс-миры, ablation, отброшенные идеи |
| [Проверка](docs/testing.md) | `local_eval`, `stress_eval`, self-check'и кокпита |
| [Campaign Cockpit](docs/cockpit.md) | экраны, роли и доступ к API, Swagger, хранилище |
| [Новые данные](docs/data.md) | база знаний, CSV итогов кампаний, базовые выгрузки |
| [Лаборатория версий](docs/lab.md) | матрица тестов, детекторы, ремедиация, gate, promote, privacy gateway |
| [Десктоп-приложение](docs/desktop.md) | сборка под macOS и Windows, GitHub Actions, каталог данных, ограничения |
| [Безопасность](SECURITY.md) | защита API и UI, чек-лист выкладки |

## Сторонние компоненты
Использованы:
- **внешний пакет среды и данных** (в git не входит, это не наш код): среда `environment.py` / `mock_environment.py`, `scoring_core.py`, `local_eval.py`, `make_submission.py`, синтетические данные;
- **open-source библиотеки** по их лицензиям: pandas, numpy (BSD), CatBoost (Apache 2.0), FastAPI, fastapi-users, Uvicorn (MIT / BSD), SQLAlchemy, psycopg (MIT / LGPL), React, Vite, HeroUI (MIT), PostgreSQL (PostgreSQL License); для десктопа — Tauri v2 (MIT / Apache 2.0), PyInstaller (GPL с исключением для сборок), aiosqlite (MIT), SQLite (public domain). Полный список фронтенда — в `web/package.json`, Rust-зависимостей — в `desktop/src-tauri/Cargo.toml`;
- **внешняя модель:** `gpt-4o-mini` через OpenAI или OpenRouter — только как эксперт-источник гипотез; в неё уходят агрегаты по ячейкам, без строк абонентов;
- **AI-ассистенты** при разработке.
