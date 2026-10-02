# hack-4d3d6773-al-manas
Hackathon team repository for al-manas
bgbggb
## Новый веб-сайт «Граф денег»

Исходники сайта: `web/`; Python API и аналитика: `src/`; тесты: `tests/`.
Полная инструкция: [README-web.md](README-web.md).

Запуск из корня репозитория:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m src.server
```

Открыть http://127.0.0.1:8000. Если порт занят, добавьте `--port 8001`.
Старые `app.py`, `__main__.py` и HTML-файлы сохранены; для нового сайта используйте команду выше.
