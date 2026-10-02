# Halyk Voice Router

A bilingual Russian/Kazakh hybrid voice router for HackAlem AI Hackathon demos. It combines an in-memory cosine candidate filter with an optional `gpt-4o-mini` contextual decision and streams every routing stage to a supervisor dashboard.

## Start

```bash
docker-compose up --build
```

Open `http://localhost:8001` by default (set `PORT=8000` to override). The app works without an API key using its local fast path. To enable LLM adjudication, create `.env`:

```bash
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

## Architecture

- `app/core/vector_index.py`: local hashed-vector cosine retrieval of top 3 scenarios.
- `app/services/router.py`: candidate restriction, RU/KZ/code-switch prompt, slot extraction, confidence fallback, and human handover.
- `app/main.py`: WebSocket protocol and response telemetry.
- `app/templates/index.html`: voice/text simulator and live supervisor trace.

## WebSocket Event

Send `{"type":"route","transcript":"Картамды жоғалттым"}` to `/ws/router`. The response contains selected scenario, candidates, reasoning, extracted slots, and `stt_ms`, `candidate_retrieval_ms`, `llm_routing_ms`, `tts_ms`, and `total_ms`.

## Demo Data

Replace the JSON files in `data/` with the full 40-scenario corpus. Each scenario needs `id`, `title_ru`, `title_kz`, `description`, `keywords`, and optionally `examples`.
