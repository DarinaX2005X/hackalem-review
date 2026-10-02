# hack-7e2ba0bc-nx-sentinel
Hackathon team repository for NX-Sentinel

## Запуск сайта и AI API

Используется существующий `ai/agents/agent.py` с интерфейсом `Agent.act(env)`.
Frontend подключён к FastAPI через `/api/workspace`, `/api/datasets`, `/api/agent/runs`.
Дизайн frontend сохранён. API не создаёт демонстрационные кампании и не отправляет кампании абонентам.

В репозитории пока **нет официальной среды `env.run_pilot`, evaluator и данных кейса**.
Поэтому загрузка/просмотр аудитории и API работают, но реальные пилоты недоступны до подключения среды.
Тестовая среда находится только в `tests/` и не используется приложением по умолчанию.

Из fish:

```fish
cd "/home/fofka/Рабочий стол/XAKATON/HACKTON"
source .venv/bin/activate.fish
python -m pip check
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --env-file .env
```

При наличии `frontend/dist` один backend обслуживает и сайт: http://127.0.0.1:8000.
Нажмите **Connect source → Connect source** для подключения предзаполненного локального API.
**Upload audience data** отправляет CSV/JSON на локальный backend; **Import results** открывает готовый снимок только в браузере.

Для разработки frontend во втором терминале:

```fish
cd "/home/fofka/Рабочий стол/XAKATON/HACKTON/frontend"
npm run dev
```

Адрес http://127.0.0.1:5173; Vite проксирует `/api` и `/health` на `127.0.0.1:8000`.
Сборка frontend: `npm run build` в `frontend/`. После первой сборки перезапустите backend, если `dist` отсутствовал при его старте.

## Окружение и данные

Новая необходимая Python-зависимость — `pandas`: она уже использовалась Agent, но отсутствовала в requirements.
Все зависимости устанавливаются в существующую корневую `.venv` из `backend/requirements.txt`.
Для установки без записи кэша/временных файлов за пределами репозитория:

```fish
cd "/home/fofka/Рабочий стол/XAKATON/HACKTON"
source .venv/bin/activate.fish
mkdir -p .venv/.tmp .venv/.cache
env TMPDIR="$PWD/.venv/.tmp" XDG_CACHE_HOME="$PWD/.venv/.cache" PIP_NO_CACHE_DIR=1 python -m pip install -r backend/requirements.txt
```

`NX_ENV_FACTORY` — доверенный модуль внутри проекта и имя функции `module:function`.
Функция создаёт новую официальную среду для каждого запуска. Контракт адаптера и данных описан в [docs/api.md](docs/api.md).
Без этой переменной запуск возвращает `ENV_UNAVAILABLE`; импорт аудитории остаётся доступен.

LLM подключён в безопасном гибридном режиме. `LOCAL_LLM_*` настраивает локальный OpenAI-compatible сервер (например llama.cpp), а `OPENAI_*` — необязательный облачный fallback. По умолчанию `LLM_MODE=hybrid`: сначала используется локальная Qwen, а OpenAI вызывается только если локальная модель недоступна/вернула невалидный ответ и задан реальный API-ключ.

В `.env.example` уже подготовлены значения для локальной `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M` на `http://127.0.0.1:8081/v1` и облачного `gpt-5.4-mini`. Настоящий `OPENAI_API_KEY` храните только в `.env`; этот файл игнорируется Git. Локальный HTTP разрешён только на loopback (`127.0.0.1`, `localhost`, `::1`), облачный OpenAI — только через HTTPS.

LLM не вычисляет KPI, бюджет, uplift и финальный портфель: модель только выбирает порядок ID из уже проверенных сервером фактов. Финальный текст собирается из этих фактов, поэтому при ошибке обеих моделей приложение автоматически использует детерминированное объяснение.

Запуск backend с конфигурацией моделей:

```fish
cd "/home/fofka/Рабочий стол/XAKATON/HACKTON"
source .venv/bin/activate.fish
python scripts/check_llm.py
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --env-file .env
```

Если облачный fallback не нужен, оставьте `OPENAI_API_KEY=` пустым или установите `LLM_MODE=local`. Если хотите проверить только OpenAI, задайте `LLM_MODE=cloud`.

## Проверки

```fish
cd "/home/fofka/Рабочий стол/XAKATON/HACKTON"
source .venv/bin/activate.fish
python -m compileall -q ai backend
python -m pip check
python -m pytest tests/ai tests/backend -q -p no:cacheprovider
ruff check ai backend tests/ai tests/backend
cd frontend
npm test
npm run typecheck
npm run build
# При запущенном npm run dev и локально установленном Playwright Chromium:
npm run test:browser
# Интеграция с запущенным backend (изолированные тестовые данные):
npm run test:api
```

Python-тесты используют явно выделенные тестовые данные и mock HTTP-провайдер, без реальных LLM-запросов.
Они проверяют алгоритм, фактическую арифметику ресурсов, API, изоляцию сессий, ограничение времени процесса,
ошибки данных/внешнего API и отсутствие повторного вызова пилота после ошибки.
Прогон с реальными пилотами требует официальной среды и данных; успешные тесты не заменяют его.

Это локальное приложение: запускайте один процесс Uvicorn на loopback. Данные сессий хранятся в памяти,
теряются при перезапуске и удаляются после часа бездействия при следующем запросе. Лимит — 8 сессий и 2 одновременных запуска.
Аутентификация пользователей, постоянное хранение и публичное развёртывание в текущий этап не входят.
