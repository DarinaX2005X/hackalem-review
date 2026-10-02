# TaskUp · Kuskon AI

**Live demo:** https://taskup-kuskon-ai.streamlit.app/

TaskUp is an AI Sana hackathon MVP that helps a business turn a raw need into a structured task card, improve its readiness score, publish it to an open catalogue, receive student-team proposals, and manually choose one, several, or no teams.

## Open the site

For judges and demo users, no installation is required.

1. Open **https://taskup-kuskon-ai.streamlit.app/**
2. Choose the interface language: **Қазақша / English / Русский**.
3. Choose a demo role:
   - **Business representative** — create and improve tasks, publish them, review proposals, and manually choose teams.
   - **Student / team** — browse the catalogue, open tasks, and submit proposals.
4. Use **Change role** at any time to return to the role-selection screen.

If Streamlit has put the app to sleep after inactivity, the first opening can take a little longer while the app wakes up.

## Core flow

1. Business enters a raw description.
2. The system detects missing information and asks 3–5 clarifying questions.
3. A task card is built and remains editable.
4. The business confirms the fields.
5. A transparent readiness score from 0 to 100 is calculated.
6. The task is published to the shared catalogue.
7. A student team independently submits an idea, plan, timeline, and prototype/repository link.
8. The business manually selects or rejects proposals.
9. A selected team may submit one result milestone; the business can confirm it and award demo progress points.

The AI never assigns a team automatically.

## Readiness score

The MVP uses the hackathon rubric:

- Context and need — 20
- Data and materials — 20
- Expected outcome — 15
- Success criteria — 15
- Constraints — 10
- Users — 10
- Business communication — 10

Total: **100**

Readiness levels:

- 0–39 — Draft
- 40–69 — Working
- 70–89 — Ready
- 90–100 — Priority

A low score does not hide a published task and does not block proposals.

## Languages

The UI supports:

- Қазақша
- English
- Русский

The user chooses a language on the landing screen and may switch it later from the sidebar. New AI/fallback clarification questions follow the selected interface language.

### Content translation

When an OpenAI API key is configured, TaskUp automatically translates task-card content into the selected interface language (Kazakh, Russian or English). The translated fields are `title`, `context`, `need`, `data`, `access`, `result`, `success`, `constraints`, `users`, `interaction`, and `feedback`.

The original task remains the source of truth:

- the SQLite data is never replaced by translated text;
- readiness scoring uses the original confirmed task card;
- contacts stay original;
- company names, team names, URLs, numbers, code and known technologies are protected;
- the UI can show the original text;
- if translation is unavailable, the original text is displayed.

Translations are cached separately under `.cache/translations/` so identical content does not need a new API request on every rerun.

## Roles

The first screen requires a demo role choice:

- **Business representative** — create/edit tasks, review proposals, manually select/reject teams.
- **Student / team** — browse the open catalogue, submit proposals, and submit a milestone after selection.

A **Change role** button always returns to the role-selection screen.

This is a hackathon demo identity switch, not production authentication.

## Stack

- Python
- Streamlit
- SQLite
- OpenAI Responses API (optional; local fallback is available)
- python-dotenv
- custom CSS / Streamlit UI helpers

## Run locally

### 1. Clone the repository

```powershell
git clone https://github.com/BAITC-Hacks/hack-acae0008-kuskon-ai.git
cd hack-acae0008-kuskon-ai
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

If `python` is not available from PATH, select an installed Python interpreter in VS Code and create a Venv from **Python: Create Environment**.

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure the optional OpenAI API key

Copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

Then put the local secret in that file:

```toml
OPENAI_API_KEY = "YOUR_REAL_KEY"
# Optional:
OPENAI_MODEL = "YOUR_SUPPORTED_MODEL"
```

Never commit `.streamlit/secrets.toml`. It is excluded by `.gitignore`.

The app can also read `OPENAI_API_KEY` / `OPENAI_MODEL` from a local `.env` file or environment variables.

### 5. Start Streamlit

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Deploy to Streamlit Community Cloud

The current public deployment is:

**https://taskup-kuskon-ai.streamlit.app/**

To deploy another copy:

1. Push the latest code to a GitHub repository where the deploying account has sufficient access.
2. Open Streamlit Community Cloud.
3. Create a new app.
4. Select the repository and branch.
5. Set the main file to:
   ```text
   app.py
   ```
6. Open **Advanced settings → Secrets** and add:
   ```toml
   OPENAI_API_KEY = "YOUR_REAL_KEY"
   OPENAI_MODEL = "YOUR_SUPPORTED_MODEL"
   ```
7. Choose an available `*.streamlit.app` subdomain.
8. Deploy.

### If the hackathon organization repository is not visible

The official repository belongs to the `BAITC-Hacks` organization. If Streamlit Community Cloud cannot access that private organization repository, keep the official repository as `origin` and use a personal deployment mirror:

```powershell
git remote add streamlit https://github.com/YOUR_GITHUB_USERNAME/YOUR_DEPLOY_REPO.git
git push streamlit main
```

For later updates:

```powershell
git switch main
git pull origin main
git push streamlit main
```

The deployment mirror is only for hosting; the hackathon repository remains the primary source repository.

## AI safety / grounding

The AI is instructed to extract only information that already exists in the user's original description. Unknown fields remain empty. The returned structured card is validated before use, and the user must review and confirm the card before publication.

If the AI API fails, times out, returns malformed output, or violates the extraction constraints, TaskUp keeps the original text and falls back to the local clarification flow.

Translation requests are display-only and use additional guards for contacts, URLs, quantities, technologies and protected names.

## Data

SQLite persists task cards, versions, scores, proposals, decisions, and result milestones while the application instance is running.

On first run the app seeds synthetic hackathon data:

- at least 5 draft examples
- at least 5 published task cards
- 5 team profiles
- 5 proposals

Database files under `data/` are excluded from Git.

**Streamlit Community Cloud note:** local filesystem data is not intended as durable production storage. For this hackathon MVP the seeded demo data is enough. A production version should move persistence to an external managed database.

## Repository structure

```text
app.py                    Streamlit application and navigation
ai_service.py             AI interview, schema validation, fallback
translation_service.py    Display-only translation and translation cache
database.py               SQLite persistence and state transitions
scoring.py                Deterministic 0–100 readiness score
seed_data.py              Synthetic demo data
i18n.py                   RU / KZ / EN interface text
ui.py                     Escaped presentation helpers
assets/taskup.css         TaskUp visual theme and responsive layout
tests/                    Core, UI and translation tests
.streamlit/config.toml     Streamlit theme
```

## 5-minute demo script

1. Open **https://taskup-kuskon-ai.streamlit.app/**
2. Select **Business representative**.
3. Create a weak task description.
4. Run AI analysis and show at least 3 clarifying questions.
5. Fill missing fields and confirm the card.
6. Show the readiness score increasing and explain the score breakdown.
7. Publish the task.
8. Use **Change role** and select **Student / team**.
9. Find the published task in the catalogue and submit a proposal.
10. Switch back to the business role and manually select or reject the team.

Optional multilingual moment for the demo: switch the interface between **Қазақша / English / Русский**, show automatic task translation, and then use **Show original**.

## Important hackathon principle

TaskUp gamifies the quality of the business task, not the popularity of the company. A clearer, more complete and confirmed task receives a higher readiness score and a stronger position in the catalogue.

Students choose tasks themselves. The AI may assist with clarification and translation, but it does **not** automatically assign teams or choose a winner for the business.
