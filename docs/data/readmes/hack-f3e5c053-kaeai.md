# AI Sana Challenge Hub

A marketplace where businesses publish AI-assisted challenges and student teams apply to solve them.

## Structure

- `apps/frontend` — Next.js UI: registration, challenge builder, marketplace and dashboard.
- `backend` — FastAPI API: accounts, challenges, applications and PostgreSQL storage.
- `ai-logic` — FastAPI AI service: analysis, generation, question regeneration, improvement, translation and review.

The browser calls the backend on port 8000. The backend calls the AI service on port 8001. OpenAI keys stay in `ai-logic/.env` and are never sent to the browser.

## Start with Docker

1. If missing, copy `.env.example` to `.env` and `ai-logic/.env.example` to `ai-logic/.env`.
2. Set `OPENAI_API_KEY` in `ai-logic/.env`. Set a unique `JWT_SECRET` in the root `.env`.
3. Run `docker compose up --build` from the repository root.
4. Open `http://localhost:3000`. The backend docs are at `http://localhost:8000/docs`.

PostgreSQL data lives in the `postgres_data` Docker volume. If the OpenAI key is missing or the provider is unavailable, basic analysis and generation use a local fallback; the optional improvement, translation and review tools require OpenAI.

## Demo flow

Register a `business` account → create a challenge → answer AI questions → generate → optionally improve, translate or review → publish. Register a `student` account → browse challenges → apply. The business dashboard shows its own challenges and can select a team.

## Local development without Docker

Run the AI service on port 8001 and the backend on port 8000. For a local database, set `DATABASE_URL=sqlite+pysqlite:///./local.db` in the backend environment; production Docker Compose uses PostgreSQL. Set `AI_SERVICE_URL=http://127.0.0.1:8001`. Then run `npm ci` and `npm run dev` inside `apps/frontend`.

Keep `.env` files out of Git. Never paste an API key into frontend code or a GitHub issue.
