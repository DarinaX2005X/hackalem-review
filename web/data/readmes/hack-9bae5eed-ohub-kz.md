# Alem Protocol — Система автопротоколирования совещаний с фиксацией поручений

**Трек 08 — Инновации Самрук-Казына**

[[Watch demo](https://img.shields.io/badge/DEMO-YouTube-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/watch?v=lr-3VZfQ3u4)

> 🎥 **Видео использования (2 мин):** https://www.youtube.com/watch?v=lr-3VZfQ3u4
> Показан полный сценарий: загрузка mp3 → транскрибация → диаризация → 9 поручений → экспорт HTML + дашборд

## 1. Название проекта

Alem Protocol

## 2. Краткое описание

**Проблема:** Протоколы пишутся вручную 2-3 часа, теряются поручения. Для секретаря (протокол за 2 мин), руководителя (дашборд просрочено/в работе), СЭД Самрук-Казына (JSON поручений). Экономия 15+ ч/неделю.

## 3. Что реализовано

- [x] STT ru/kk/shala — faster-whisper локально (small/large-v3)
- [x] Диаризация — pyannote 3.1 локально, SPEAKER_01 = Ерлан (на Windows эвристика 3 спикера, на Linux Docker полная)
- [x] Поручения кто/что/к сроку — KazLLM через llm.alem.ai (self-hosted, понимает шала-казахский)
- [x] Саммари 3-5 предложений
- [x] Экспорт HTML (Notion стиль), PDF (DejaVu), DOCX
- [x] Дашборд статусов просрочено/в работе/выполнено, фильтры, приоритет high/medium/low

## 4. Как работает

1. Вход mp3/wav из Zoom/Teams → uploads/
2. STT faster-whisper → 43 сегмента
3. Диаризация pyannote → SPEAKER_00,01,02
4. KazLLM → JSON {tasks:[{assignee, task, deadline:YYYY-MM-DD, source_quote, speaker}], summary}
5. Нормализация дат: "до пятницы"=2026-05-16
6. Выход: POST /transcribe → JSON, POST /export?format=both → HTML/PDF, GET /dashboard → дашборд
   Видео сценария: https://www.youtube.com/watch?v=lr-3VZfQ3u4

## 5. Технологии

Python 3.11, FastAPI, uvicorn, faster-whisper (CTranslate2), pyannote.audio 3.1, torch CPU, KazLLM llm.alem.ai, fpdf2 DejaVuSans, React Tailwind Recharts

## 6. Архитектура

```
[mp3] -> stt.py (faster-whisper local) + diarize.py (pyannote local) -> merge -> extractor.py (KazLLM) -> export.py -> main.py (/transcribe, /export, /dashboard)
```

Все AI локальные кроме KazLLM в контуре Alem — соответствует ограничению "без внешних облачных API".

## 7. Установка и запуск

```powershell
git clone https://github.com/BAITC-Hacks/hack-9bae5eed-ohub-kz
cd hack-9bae5eed-ohub-kz
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# .env: HF_TOKEN, KAZLLM_API_KEY
# Принять gated: hf.co/pyannote/speaker-diarization-3.1 -> Agree
hf auth login
$env:HF_TOKEN="hf_xxx"; $env:HUGGINGFACE_HUB_TOKEN="hf_xxx"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# http://127.0.0.1:8000/docs — видео как проверять: https://www.youtube.com/watch?v=lr-3VZfQ3u4
```

## 8. Как проверить — сценарий для жюри

Смотри видео: https://www.youtube.com/watch?v=lr-3VZfQ3u4

1. /docs → POST /export → format=html, file=data/meeting1.mp3 → Execute → protocol\_\*.html с резюме, 9 поручениями, транскриптом с бейджами [SPEAKER_00]
2. Шала-тест: "отчет керек, deadline ертеңге дейін, ответственный Ерлан"
3. /dashboard → 9 задач, 2 просрочено

## 9. Данные и интеграции

Вход mp3/wav/m4a, live Zoom/Teams, API llm.alem.ai (KazLLM self-hosted), выход HTML/PDF/DOCX + JSON для СЭД, внешних сервисов нет

## 10. Ограничения

Диаризация на Windows эвристика (из-за torchcodec), на Linux Docker полная, large-v3 медленнее, СЭД mock, макс 30 мин аудио, PDF без жирного шрифта

## 11. Deployed-версия

- Видео демо: https://www.youtube.com/watch?v=lr-3VZfQ3u4
- Demo (ngrok для жюри): https://xxxx.ngrok-free.app/docs — живой бэкенд (запусти ngrok http 8000)
- On-premise: docker-compose up --build → :8000
- Код: https://github.com/BAITC-Hacks/hack-9bae5eed-ohub-kz

## Деплой — куда и как

**On-premise (рекомендуется):** docker build -t alem-protocol . && docker run -p 8000:8000 --env-file .env -v ./models:/app/models alem-protocol
**Render free (облегченный):** используй requirements.render.txt без torch/pyannote
**Ngrok для жюри:** ngrok http 8000 → вставь URL в пункт 11
Требования: 4 CPU, 8GB RAM, 10GB диск

Команда Alem Protocol — Трек 08, HackAlem 2026
