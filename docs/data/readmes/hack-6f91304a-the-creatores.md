# hack-6f91304a-the-creatores
Hackathon team repository for The Creatores
Галымбек ..

## ЗакупAI — backend участника №3

Сервер FastAPI, API загрузки/расчётов, агент OpenAI, SQLite и экспорт Excel.
Инструкции Windows PowerShell, контракт frontend и интерфейс расчётного модуля:
[docs/backend.md](docs/backend.md).

Схема API: [contracts/openapi.json](contracts/openapi.json).
Пример синтетического результата: [contracts/recommendation.example.json](contracts/recommendation.example.json).

По умолчанию деморежим выключен. Пока модуль участника №2 не подключён,
для локальной демонстрации явно задайте `DEMO_MODE=true` в `.env`.
В этой версии нет авторизации; запускайте сервер на `127.0.0.1`.
