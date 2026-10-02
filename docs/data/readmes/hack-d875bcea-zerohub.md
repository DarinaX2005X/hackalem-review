# Akim for 5 Hours

**An AI-assisted city-management simulator for the Astana Innovations hackathon.**

## 1. What the product does

Akim for 5 Hours helps users explore how a limited city budget can affect quality of life across hypothetical districts.

Every user starts with the **same 100 virtual budget units** and the **same synthetic dataset**. The user chooses a district and one initiative in each of five areas:

1. Transport
2. Greening
3. Social infrastructure
4. Safety
5. City services

The application checks the budget, calculates changes in district indicators, and produces an **Astana Quality of Life Score**. With live AI enabled, it explains the strengths, risks, trade-offs and possible consequences of the plan. Users can refine decisions and compare saved scenarios.

**Who it is for:** city managers, analysts, students and anyone learning about urban budget decisions.

**Important:** the districts, costs and effects are synthetic educational assumptions. The score is not an official Astana index or a forecast of real city outcomes. The dataset contains no personal data.

### Main features

- A shared starting budget and dataset.
- Exactly five decisions: one per development area.
- Budget-overrun prevention in the interface and backend.
- Immediate previews of modeled effects.
- Before-and-after district indicators and city scores.
- Saved scenarios that can be reopened and compared.
- AI explanations and explanations of tested, affordable alternatives.
- An explicitly labeled rule-based mode for running without an API key.

## 2. Technologies used

| Part | Technologies | Purpose |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | Simulator interface and results pages |
| API validation | Zod, Pydantic | Validate data exchanged between frontend and backend |
| Backend | Python 3.12, FastAPI, Uvicorn | Budget rules, simulation, API and analysis coordination |
| Database | SQLite | Store scenarios and cached analysis |
| AI | OpenAI Responses API, HTTPX, structured JSON output | Generate explanations from calculated results |
| Deployment | Docker Compose, Nginx | Run both services and forward API requests |
| Testing | Pytest, Vitest, Playwright | Backend, frontend and browser integration checks |
| Automation | GitHub Actions | Run verification and build a source release |

The configured AI model is `gpt-4.1-mini-2025-04-14`. Provider access must be checked with the team's API key.

### How the parts work together

The browser sends the five decisions to FastAPI. The backend validates them, calculates the cost and score, and saves the scenario in SQLite. The AI adapter receives the calculated facts and tested alternatives, then returns explanatory text. The frontend displays the results.

**The language model does not calculate or change the official simulation score.**

## 3. Project structure

Use the complete **Person 4 package**. It already includes the code from Persons 1–3; no additional merging is needed.

| Path | Contents |
| --- | --- |
| `frontend/` | React application |
| `backend/` | API, simulation, database, AI adapter and backend tests |
| `data/v1/` | Shared synthetic districts, initiatives and scoring configuration |
| `data/person3/` | Assumption ledger and repeatable evaluation cases |
| `scripts/` | Development launcher, verification and release tools |
| `docs/` | Deployment guide, demo script and verification record |
| `.github/workflows/ci.yml` | Continuous integration workflow |
| `compose.yaml` | Configuration for starting the complete application |
| `.env.example` | Example Docker deployment settings |

## 4. Run the whole project in VS Code

**Use this method first. It starts both the frontend and backend.**

### Before starting

You need:

- The extracted complete project folder, named `akim-team` in the supplied ZIP.
- VS Code.
- Docker Desktop installed and running, with Docker Compose available.
- Internet access for the first build to download dependencies and images.

You do **not** need to install Python or Node.js on your computer for this Docker method.

### Step 1 — Open the correct folder

In VS Code, select **File → Open Folder → akim-team**.

You are in the correct folder if the VS Code file panel shows `compose.yaml`, `frontend` and `backend` together.

### Step 2 — Open the terminal

Select **Terminal → New Terminal**.

Run all commands in this section from the project root—the folder containing `compose.yaml`.

### Step 3 — Check Docker

Run these commands one at a time:

```bash
docker --version
```

```bash
docker compose version
```

Both commands should print a version. If Docker is not recognized, install Docker Desktop and reopen VS Code. If Docker cannot connect to its engine, open Docker Desktop and wait until it is running.

### Step 4 — Create the settings file

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux:**

```bash
cp .env.example .env
```

Do this only during the first setup. If `.env` already exists, keep it and edit its values as needed.

The initial settings use rule-based explanations. This lets you check the simulator before adding an AI key.

### Step 5 — Start everything

```bash
docker compose up --build
```

The first build may take several minutes. Leave this terminal open while using the application. You do not need to start either service separately.

### Step 6 — Open the application

Open this address in your browser:

**http://127.0.0.1:8080**

Choose your initiatives and districts, then select **“See my city’s future.”**

### Stop and start again

To stop the application, press **Ctrl+C** in the running terminal.

To start it again:

```bash
docker compose up
```

Saved scenarios remain in the named database volume. Do not run `docker compose down -v` unless you intentionally want to delete that stored data.

## 5. Enable real AI analysis

**The default rule-based mode does not demonstrate the hackathon's live AI requirement. Complete this section before presenting the AI feature.**

1. Open the **root `.env` file**, next to `compose.yaml`.
2. Set these values, replacing the API-key placeholder with your own key:

```dotenv
AKIM_ADVISOR_FACTORY=app.services.team_advisor:TeamAdvisor
AKIM_ANALYSIS_VERSION=person4-ai-v1
OPENAI_API_KEY=your_actual_api_key
OPENAI_MODEL=gpt-4.1-mini-2025-04-14
```

3. Save the file. Open a second VS Code terminal in the project root and run:

```bash
docker compose up -d --force-recreate backend frontend
```

4. Open the application and submit a scenario. A successful live assessment displays **“Your AI city advisor.”**

AI requests require working provider credentials and model access and may incur charges. Keep the key server-side; never put it in frontend code or commit `.env`.

If AI fails, the calculated score and saved scenario remain available. The backend does not silently replace a failed live AI response with a rule-based one.

After changing the model or prompt, change `AKIM_ANALYSIS_VERSION` so cached explanations from the earlier configuration are not reused.

## 6. How the score is calculated

Each district has five quality indicators on a 0–100 scale, with higher values meaning better quality. Initiatives change the targeted district's indicators according to the shared dataset. Resulting indicators are constrained to the 0–100 range.

The five indicators have equal weight in each district's score.

```text
City Quality of Life Score =
    0.80 × population-weighted average district score
  + 0.20 × lowest district score
```

The lowest-district component makes the distribution of benefits matter, alongside the citywide average. These weights are explicit model design choices.

The starting city score is **47.1375**, shown as **47.1** when rounded to one decimal. All users use the same starting configuration.

AI output is checked against a structured schema and a catalog of calculated facts. Numeric placeholders are filled with backend values. These checks constrain numeric errors, but they cannot prove every free-form statement is correct; explanations still need human review.

## 7. Verify the solution manually

Start the application, then perform the checks below.

| Check | What to do | Expected result |
| --- | --- | --- |
| Same starting conditions | Start a new plan in two separate browser sessions | Both receive 100 budget units and the same district data |
| All five areas | Inspect the decision tabs and build a complete plan | Transport, greening, social infrastructure, safety and city services are available |
| Five-decision rule | Try submitting before completing every area | An incomplete plan cannot be submitted successfully |
| Budget control | Build a 100-unit plan, then try a more expensive replacement | An over-budget selection/submission is prevented; backend tests also check HTTP 422 rejection |
| Indicator changes | Submit the repeatable plan below | The district indicators and final city score change |
| Saved results | Reload the results page | The saved scenario remains available |
| Different choices | Refine the plan with a cheaper transport measure and submit again | The resulting score changes |
| Comparison | Open “Compare plans” after saving two plans | Both plans can be compared |
| Live AI | Enable AI, submit a plan and inspect its report | A successful AI report includes a summary, strengths, risks and trade-offs grounded in the scenario |

### Repeatable test plan

Select these exact initiatives and districts:

| Area | Initiative | District | Cost |
| --- | --- | --- | ---: |
| Transport | Bus-priority lanes | District A | 20 |
| Greening | Neighborhood pocket park | District B | 20 |
| Social infrastructure | Local clinic upgrade | District C | 20 |
| Safety | Safer pedestrian crossings | District D | 20 |
| City services | District maintenance crew | District E | 20 |

Expected results for the unchanged v1 dataset:

- Total cost: **100**.
- Remaining budget: **0**.
- Final score: **49.819**, displayed as **49.8**.

This plan is stored as `distributed_medium_cost` in `data/person3/evaluation_cases.json`.

## 8. Automated verification

### A. Check a running Docker deployment

In a second terminal at the project root:

```bash
docker compose ps
```

Both services should be running and become healthy. In your browser, open:

**http://127.0.0.1:8080/api/health**

The JSON response should include `"status": "ok"`. Its `analysis_source` should be `rules` or `ai`, matching your configuration. Health alone does not confirm that a real provider request succeeds.

### B. Run the full automated test suite

This method requires **Python 3.12** and **Node.js 24**, in addition to the source files. Run from the project root.

Create a Python environment:

```bash
python -m venv .venv
```

If your system uses `python3`, use `python3 -m venv .venv` instead.

Activate it on **Windows PowerShell**:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or activate it on **macOS/Linux**:

```bash
source .venv/bin/activate
```

Install the locked dependencies:

```bash
python -m pip install -r backend/requirements.lock
npm --prefix frontend ci
```

Run backend tests, dataset validation, frontend tests and the production build:

```bash
python scripts/verify.py
```

For browser integration, first install Chromium:

```bash
cd frontend
npx playwright install chromium
cd ..
```

Then run:

```bash
python scripts/verify.py --browser
```

Keep ports **8001** and **5182** free for the browser checks. These checks launch their own temporary services and database. They exercise rule-based analysis and the AI adapter with mocked provider responses; they make no live AI calls.

### C. Run a deployment smoke check

With Python available and the Docker application running:

```bash
python scripts/smoke.py
```

This checks health and shared configuration without creating scenarios.

For scenario creation, persistence, overrun rejection, changed scores and analysis:

```bash
python scripts/smoke.py --write --analysis
```

This creates two scenarios and requests one assessment. In AI mode, the assessment may incur provider charges. The scenario checks use the included v1 dataset.

### Recorded verification status

| Check | Recorded result |
| --- | --- |
| Backend tests | 60 passed |
| Frontend model tests | 8 passed |
| TypeScript and production build | Passed |
| Browser integration with rule-based analysis | Passed |
| Browser integration with mocked AI provider | Passed |
| Direct API smoke check | Passed |
| Local development launcher on Linux | Passed |
| Docker/Nginx execution and GitHub Actions | Supplied but not executed in the development environment |
| Real provider call | Not executed; requires the team's API key |

These are results from the assembled project's prior verification, not a guarantee that a new machine is configured correctly. Run the checks again on the machine used for submission. See `docs/VERIFICATION.md` for details.

## 9. Optional: run without Docker

Follow the Python/Node dependency setup in Section 8B, then run from the project root with the virtual environment activated:

```bash
python scripts/dev.py
```

Open **http://127.0.0.1:5173**. The launcher starts the frontend and backend together. Press **Ctrl+C** to stop them.

For this local method, AI settings belong in **`backend/.env`**, following `backend/person3.env.example`. Docker uses the **root `.env`** instead. Do not confuse these two settings locations.

## 10. Common problems

| Problem | What to check |
| --- | --- |
| `docker` is not recognized | Install Docker Desktop, then reopen VS Code |
| Cannot connect to Docker engine | Open Docker Desktop and wait for it to start |
| No Compose configuration file found | Open the terminal in the folder containing `compose.yaml` |
| `.env.example` cannot be found | You are probably in the wrong folder; open `akim-team` |
| Port 8080 is occupied | Set `AKIM_PORT=8081` in root `.env`, rerun Compose and open port 8081 |
| Frontend opens but API fails | Check that both services are healthy and inspect their logs |
| AI report fails | Check the server-side key, model access, provider quota and backend logs |
| An old AI explanation appears | Change `AKIM_ANALYSIS_VERSION` and recreate the services |

Inspect logs with:

```bash
docker compose logs --tail=100 backend frontend
```

Do not share your API key when reporting an error.

## 11. Scope and further documentation

The simulator models immediate indicator effects; it does not model implementation timelines or recurring operating costs. Comparison is between saved plans available in the current browser, not an authenticated cross-team leaderboard. Random city events and automatic slide export are not implemented.

The Docker configuration binds to localhost by default. Public hosting requires additional access control and operational safeguards; this prototype does not implement user accounts or per-user authorization.

Further guides:

- `docs/DEMO.md` — presentation walkthrough.
- `docs/DEPLOYMENT.md` — persistence, backup and operations.
- `docs/RUBRIC.md` — mapping to hackathon criteria.
- `docs/VERIFICATION.md` — detailed test record.

To create a source release with checksums, run:

```bash
python scripts/package_release.py
```

The ZIP is written to `artifacts/akim-team-release.zip`.
