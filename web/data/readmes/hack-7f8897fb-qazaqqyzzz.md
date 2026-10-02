# Career Quest

Career Quest is a privacy-first career development dashboard for the HackAlem AI case. It turns the supplied employee, skills, events, and activity-history data into a clear next-step plan. The deterministic rules engine proves eligibility and skill impact; OpenAI adds a concise coaching layer without being allowed to invent activities or override the rules.

## What the demo shows

- Personal employee journey with target role, grade path, readiness, critical skills, completed hours, and recent activity.
- Evidence-based activity library with search, filters, prerequisites, upcoming sessions, and skill effects.
- One-click completion with immediate persisted progress.
- Self-service account creation plus HR-created employee accounts.
- Editable profile with photo, bio, work style, email preferences, and a private career identity.
- Written career goals with target role, timeline, weekly commitment, path level, XP, and skill readiness.
- AI opportunity checker for user-entered courses, conferences, and meetups, with persistent fit analysis.
- AI plan generated only from eligible rule-based candidates, with evidence attached to every recommendation. If AI is unavailable, the verified skill-based plan remains available.
- HR workspace with readiness, skill-gap counts, participation metrics, JSON profile import, CSV history import, and export.
- Employee privacy boundaries enforced on the server: employees can access only their own profile, while HR can access the team view.

## Architecture

```text
Browser (vanilla HTML/CSS/JS)
        │ same-origin JSON + HttpOnly session cookie + CSRF token
FastAPI application
   ├── rules engine: eligibility, prerequisites, skill progression, ranking
   ├── optional OpenAI Responses API planner (server-side key, strict JSON schema)
   └── SQLite store: source snapshot, history, sessions, cache, audit log
```

The UI never receives `OPENAI_API_KEY`. The backend validates every imported profile/history row, checks permissions on every employee route, rate-limits sign-in and AI requests, caches validated plans for one hour, and falls back to deterministic recommendations on timeout, quota, provider, or validation errors.

## Run locally

Use Python 3.11+ (3.12 recommended):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# edit .env and set OPENAI_API_KEY if AI planning is desired
.venv/bin/python run.py
```

Open [http://localhost:4173](http://localhost:4173). In development, the login page offers local demo buttons. Generated demo credentials are written to `.local/credentials.txt` with mode `0600`; this file is ignored by Git.

To use normal login instead, set `ADMIN_PASSWORD` and `EMPLOYEE_PASSWORD` in `.env` before the first database initialization. Delete `.local/careerquest.sqlite3` only when you intentionally want to recreate the local demo database.

## Docker

```sh
docker compose up --build
```

The compose file persists SQLite under `./.local`. For a real deployment, provide strong passwords, a public HTTPS `PUBLIC_ORIGIN`, and the API key through the host secret manager or environment, never in the image or repository.

## Environment

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional server-side key for the AI coaching layer |
| `OPENAI_MODEL` | OpenAI model name; defaults to `gpt-4.1-mini` |
| `APP_ENV` | `development` enables local demo buttons; use `production` for deployment |
| `PUBLIC_ORIGIN` | Exact HTTPS origin required in production for mutation requests |
| `ADMIN_PASSWORD` / `EMPLOYEE_PASSWORD` | Initial HR and employee passwords |
| `DATABASE_PATH` | SQLite path; relative paths resolve from the repository root |
| `PORT` | HTTP port; defaults to `4173` |
| `SMTP_HOST`, `SMTP_PORT` | Optional email provider for reminders and connection tests |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Optional SMTP credentials; keep them in the host secret manager |
| `FROM_EMAIL`, `SMTP_TLS` | Sender address and TLS preference for email delivery |

## Gmail integration

The build stores employee email preferences, supports optional SMTP delivery, and includes a user-authorized Gmail connector using the narrow `gmail.readonly` scope. The connector reads recent message metadata and short snippets only when the employee requests a scan, never attachments. Career Quest identifies relevant interviews, courses, events, jobs, and deadlines and compares them with the employee's goal and skill gaps. OAuth refresh tokens are encrypted at rest.

For local OAuth development, register these values in Google Cloud:

```text
Authorized origin: http://localhost:4173
Redirect URI:      http://localhost:4173/api/integrations/google/callback
```

Production deployments must replace both values with the public HTTPS origin and keep OAuth tokens encrypted at rest.

Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, and a strong `OAUTH_TOKEN_ENCRYPTION_KEY` in `.env`. Rotating the encryption key intentionally disconnects existing Gmail connections.

## Verification

```sh
# syntax check
.venv/bin/python -m compileall -q app run.py

# health check after starting the server
curl http://localhost:4173/healthz
```

The app is intentionally based on the supplied synthetic dataset. A readiness percentage is a learning signal, not a promotion decision; managers still make the final career decisions outside this demo.
