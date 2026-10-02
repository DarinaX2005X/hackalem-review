# Halyk Voice · test release

Independent voice assistance platform with Russian, Kazakh and English interface, OpenAI speech recognition and a female synthesized voice. It provides conversation history and spoken step-by-step guides. It is not an official Halyk Bank service and has no access to banking accounts.

The default release uses `gpt-4.1-mini` for brief contextual replies, `gpt-4o-transcribe` for recognition and `gpt-4o-mini-tts` with the Marin voice. Known navigation/greeting responses avoid a model round trip. Audio streams as 24 kHz PCM into WebAudio with a short buffer; replay uses a private session cache. Starting a new spoken question stops playback and cancels an unfinished older answer. Empty recognition and connection failures return the interface to a usable state.

These are latency reductions, not a zero-latency guarantee. OpenAI availability, microphone quality and network conditions still matter. The voice is AI-generated. Voice guidance follows the [OpenAI speech documentation](https://developers.openai.com/api/docs/guides/text-to-speech).

## Run locally on Windows

Requires Python 3.11+ and Node.js 22+. Quick setup: run `./setup.ps1`, verify the local `.env`, then run `./start.ps1`. Setup preserves an existing `.env`. By the owner's explicit request, this private test repository includes a configured `.env`. Anyone with repository access can use its API key and incur charges. Keep access restricted and configure a separate server-side key for each deployment.

1. Create a Python virtual environment: `python -m venv .venv`.
2. Install dependencies: `.venv/Scripts/python.exe -m pip install -r requirements.txt`.
3. Use the supplied `.env`, or copy `.env.example` to `.env` and fill in your own `OPENAI_API_KEY` locally.
4. In `frontend`, run `npm ci` and `npm run build`.
5. Run `./start.ps1`, then open http://localhost:8010 and create an account.

`APP_MODE=assistant` is the normal test mode: conversation and navigation, without fake balances, synthetic client identifiers, or mock transactions. Its short contextual prompt does not send the legacy scenario catalog to OpenAI. `APP_MODE=demo` is a legacy router test mode and must not be used as an actual bank integration. The internal scenario taxonomy does not authorize bank actions.

## Accounts and data

Email/password accounts are stored in SQLite. Passwords are salted scrypt hashes. Conversation text is encrypted with a server-local Fernet key. Users can delete history, change their password and revoke all login sessions. Email address ownership is not verified; Gmail OAuth and password-reset email delivery are not configured.

Back up both `runtime/accounts.sqlite3` and `runtime/history.key` securely. Restrict access to `.env`; never publish runtime files or backups. A production operator must restrict filesystem permissions and protect backups. See [SECURITY.md](SECURITY.md) for implemented controls and their limits.

## HTTPS deployment

`Dockerfile`, `compose.yaml` and `Caddyfile` provide a single-worker deployment with a non-root application, persistent data and a reverse proxy. Set `PUBLIC_DOMAIN` to a domain you control in the deployment `.env`, configure DNS and make ports 80/443 reachable, then run `docker compose up --build -d`. No application port is published directly. Only the proxy's fixed private address is trusted for forwarded headers. If the subnet conflicts with your server network, change both the subnet/addresses and FORWARDED_ALLOW_IPS together.

These deployment files have not been exercised against a public domain in this workspace. Supply a real bank-approved API and authorization contract before adding banking operations. Infrastructure DDoS protection, email verification, MFA and an independent security assessment remain production rollout tasks.

## Checks

Install `requirements-dev.txt`. Run `.venv/Scripts/python.exe -m unittest tests.test_release.ReleaseTests tests.test_release.VoiceRelayTests -v`. Build the frontend, then run `.venv/Scripts/python.exe scripts/check_ui.py` for isolated browser checks using Edge. Set `HV_BROWSER_CHANNEL=chrome` to use Chrome, or `chromium` after installing Playwright Chromium. The UI test creates a temporary database, runs a test server on port 8011 and uses synthetic microphone/PCM/WebSocket fixtures, without OpenAI calls. It checks playback, interruption, recovery, accounts, guides and desktop/mobile layout. Screenshots are saved in ignored `reports/`.

Optional live speech check: `.venv/Scripts/python.exe scripts/check_speech.py --save-sample`. This makes billable OpenAI requests using only a fixed synthetic greeting; it never reads customer history or sends the routing catalog. It checks Marin PCM generation, model availability and recognition of the generated Russian sample. It is not a real microphone accuracy benchmark.

Official banking information: https://halykbank.kz/knowledge_base and https://halykbank.kz/knowledge_base/3286.
