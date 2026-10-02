# Delphi

Помощник для проверки реорганизации: сравнивает документы «До / После», показывает изменения обязанностей и связывает выводы с исходными пунктами.

**Статус:** backend FastAPI/PostgreSQL подключён к frontend Next.js через сгенерированный HeyAPI-клиент и защищённый proxy. Реализованы вход/регистрация, история, загрузка комплектов, просмотр источников, экран результатов, ручная проверка, экспорт и уведомления; UI поддерживает RU/KK/EN. Миграции, заполнение БД, HTTP-сценарии, lint, typecheck и production build проверены. Прошли 10 Playwright-тестов и 10 тестов генератора отчёта; результаты AI пока проверены только через синтетические UI fixtures. [Браузерный отчёт: 18 состояний страниц со скриншотами](frontend/docs/report/latest.md).

- [Backend: структура, настройка и команды запуска](backend/README.md)
- [Типизированный OpenAPI-контракт](backend/openapi.json)
- [Контрольные синтетические примеры](backend/fixtures/synthetic/README.md)
- [Начать с документации](docs/README.md)
- [План реализации и приёмка](docs/implementation-plan.md)
- [Продукт и интерфейс](docs/product.md)
- [Архитектура](docs/architecture.md)
- [Проверенные изменения исходных документов](docs/source-analysis.md)
- [Frontend: настройка и команды](frontend/README.md)

Для локальной проверки из `backend/`, после установки зависимостей через `uv sync --frozen`:

```sh
uv run ruff check app scripts migrations tests
uv run pytest -q
uv run --no-sync python scripts/export_openapi.py
```

Эти offline-проверки не доказывают качество семантического сравнения. Демонстрационная пара — исходные DOCX редакций 8/9; в локальную БД загружены оба файла и 966 исходных блоков. Вход обеспечивает Better Auth в отдельной БД, рабочая область backend общая. Сканы без OCR и отсутствующие приложения остаются ограничениями.

Локальный UI: `http://localhost:3000`. Демо-вход: `analyst@delphi.local` / `password123`; остальные учётные записи и воспроизводимый запуск — в [frontend/README.md](frontend/README.md). Для анализа и перевода нужны `OPENAI_API_KEY` и `OPENAI_MODEL` в backend; без них доступны история и подготовка документов, а UI показывает ограничение.

Правила для coding-агентов — в [AGENTS.md](AGENTS.md).
