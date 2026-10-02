# Voice Router

## Run

Run these commands from the repository root. The backend now lives in `apps/web/backend`.

1. Create and activate a Python 3.12+ virtual environment: `python -m venv .venv`, then `.\.venv\Scripts\Activate.ps1` in PowerShell.
2. Install backend and test dependencies: `python -m pip install -e "./apps/web/backend[dev]"`.
3. Copy `apps/web/backend/.env.example` to `apps/web/backend/.env` **only if the `.env` file does not already exist**. Set `VOICE_ROUTER_API_KEY` (or `OPENAI_API_KEY`). OpenAI's base URL and `gpt-4.1-mini` are the defaults. Dataset paths resolve from the repository root, so starting from a different directory does not break them.
4. Run `python -m uvicorn app.main:app --app-dir apps/web/backend --reload`.
5. In a separate terminal, run `npm install --prefix apps/web` then `npm run dev --prefix apps/web`.

The web app is a responsive routing studio built with Tailwind CSS and shadcn/ui. Its development server proxies `/api` to `http://127.0.0.1:8000`. Restart Vite after changing its configuration. For production, serve `/api` through your backend reverse proxy, or set `VITE_API_URL` when building and set `VOICE_ROUTER_CORS_ORIGINS` to the frontend origin (comma-separated when needed). Localhost ports 5173 and 5174 are allowed by default.

Use **Load an example** to explore the UI without calling a provider. Live conversations show routing decisions, extracted details, execution status, and JSON traces. Session history lasts for the current browser tab; use **Export session** to save a conversation before reloading. Voice input is not configured; the studio supports text input.

Checks: `python -m pytest apps/web/backend/tests -q`, `npm run build --prefix apps/web`, and `npm test --prefix apps/web`. Backend tests block live provider requests and use synthetic data.

Consequential actions are mock operations. They require a conversation-bound preview and explicit confirmation; cancellation and retries cannot execute the same preview twice. A preview created on turn 10 can still be confirmed or cancelled. Other new messages are limited to 10 turns.

Run `$env:PYTHONIOENCODING='utf-8'; python apps/web/backend/run_evaluation.py` in PowerShell to create predictions and invoke the checked-in evaluator. This makes paid provider requests for the development dataset. Results are written to the repository's `artifacts` directory. The checked-in dataset is authoritative.
Hackathon team repository for Cathays
