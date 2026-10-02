# OrgLens · OpenAI Edition

A standalone, server-backed reorganization analysis prototype. Python Flask backend; OpenAI Responses API; Russian dark interface. Import before/after TXT, MD, DOCX, PDF (with extractable text), XLSX or paste text. Get structured evidence-grounded findings, PDF via browser print, JSON export and analyst chat.

## MacBook / Windows startup

1. Install Python 3.11+.
2. Open Terminal in this folder. On Mac, use `python3 -m venv .venv && source .venv/bin/activate`; on Windows use `py -m venv .venv && .venv\\Scripts\\activate`.
3. `python -m pip install -r requirements.txt`
4. Copy `.env.example` to `.env`; replace the placeholder with a NEW OpenAI key. Never reuse a key shared in chat. On Mac: `cp .env.example .env`.
5. `python app.py` then open `http://127.0.0.1:5000`.
6. Run `python -m pytest -q` for offline checks.

## Hosting

A static-only `chatgpt.site` deployment cannot run Python or protect a key itself. Deploy Flask to a backend that supports Python and environment secrets. Configure `OPENAI_API_KEY` and `ORGLENS_ACCESS_TOKEN` on the host and proxy both frontend and `/api/*` to Flask, or connect the static frontend to an HTTPS Flask endpoint (requires updating fetch paths and CORS). Never publish `.env`. Do not expose upload endpoints publicly without authentication, throttling, privacy review and cost caps; optional token gate in this prototype is a basic demo gate, not production authentication. Flask's built-in server is for local testing, not production.

## Privacy and limitations

Original documents are parsed in memory; extracted text is sent to OpenAI with `store=False` after consent. No persistent file storage is added. The original local-only privacy claim is no longer true. No scanned PDF OCR. Long files are capped at 110 segments / 40k chars per side, with a visible warning; PDFs limited to 75 pages; XLSX to 12 sheets x 1500 rows. Automated analysis is a review aid, not definitive legal or organizational advice. Quotes and locators are from parser-extracted source segments and model-made findings without valid evidence IDs are dropped. Authentication, rate limiting, production file scanning and further access controls are required for external deployment.

**Double-click launcher:** `start_mac.command` (Mac), `start_windows.bat` (Windows). macOS may require granting permission to a downloaded script in Privacy & Security. The initial Mac launch creates `.env` for editing; launch again after adding your new key.
