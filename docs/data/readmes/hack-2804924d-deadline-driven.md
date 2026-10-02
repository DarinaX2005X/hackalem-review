# Beeline Campaign AI

**Team Deadline Driven | HackAlem Hackathon | Telecommunications Track**

## Project Overview

**A marketing assistant that helps Beeline decide which customers to contact,
which tariff to offer, and which communication channel to use to increase
revenue without wasting the campaign budget.**

The agent analyzes customer profiles and historical tariff changes, tests ideas
on small groups, and produces a final marketing campaign plan.

This is **not a service that finds the cheapest or "perfect" tariff for each
subscriber**. Its primary user is a marketing analyst. The objective is to
increase the operator's revenue after communication costs, within the case limits.

The complete dashboard, Python API, agent, and case data are included in this repository.
Use the instructions below to run the project locally.

## Problem and Target User

A tariff change does not always benefit the operator: a subscriber may start
paying less, while SMS, advertising, and calls also cost money. Contacting the
entire customer base without testing can therefore be unprofitable.

The agent helps marketing analysts identify promising audiences and offers,
test their assumptions, and allocate limited resources.

### Three Key Terms

| Term | Meaning |
|---|---|
| **Campaign** | A selected audience, a target tariff, and a communication channel |
| **Pilot** | A small trial campaign used to estimate the effect of an offer |
| **Campaign plan** | The final set of campaigns selected after testing |

For example, the agent can test a tariff offer on a small customer group.
If the estimated effect looks promising after accounting for cost and uncertainty,
the offer may be included in the final plan. Profit is not guaranteed.

## Implemented Features

- Analysis of customer profiles and historical tariff transitions.
- Segmentation by current tariff and ARPU, with additional data-usage and call-usage
  splits when needed. ARPU means average revenue per user.
- Pilot campaigns through the hackathon environment's public `env.run_pilot(...)` method.
- Campaign and channel selection based on estimated effects, uncertainty, budget,
  and contact limits.
- Background agent runs through the API, with progress states and error handling.
- A web dashboard with final campaigns, pilot history, net revenue gain, total
  costs, and remaining budget.
- CSV export from the stored run result without executing the agent again.
- Standalone agent evaluation and submission generation without the website.

Campaigns, pilots, and metrics displayed in the dashboard come from the backend
and belong to the same run. They are calculated in the demo environment, not
hardcoded sample results.

## How It Works

1. The analyst opens the dashboard and uses the agent launch button.
2. The backend creates a run and loads the customer profile and demo environment.
3. The agent builds customer segments and ranks tariff-transition hypotheses
   using historical data.
4. It conducts pilots, updates effect estimates, and accounts for uncertainty.
5. It selects a campaign plan within the remaining budget and contact limits.
6. The backend evaluates the pilots and final plan using `scoring_core.py`.
7. The dashboard shows the results and allows the analyst to export the plan as CSV.

The agent runs once per API run. Costs include both pilots and final campaigns.
The reporting layer computes evaluation metrics; the agent itself does not
receive private scoring inputs.

If no conservatively profitable plan is found, a fallback can select a feasible
campaign. This does not guarantee a positive result.

**The current application is a simulation. No real subscribers are contacted,
and no real campaign money is spent.**

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React 19, TypeScript 6, Vite 8, CSS, Lucide React |
| Backend | Python, FastAPI, Uvicorn |
| Agent and data processing | pandas, NumPy, heuristic selection with uncertainty estimates |
| Environment and evaluation | Hackathon SDK: `environment.py`, `mock_environment.py`, `scoring_core.py` |
| Data formats | JSON, CSV |
| Windows launcher | PowerShell |
| Checks included in the repository | Python unittest, Node.js test runner, ESLint, TypeScript |

**External AI models:** the current agent does not call OpenAI, NVIDIA, or other
LLM services. Its strategy is implemented in Python. No API keys or paid model
tokens are required. Internet access is needed for initial dependency installation.

## Architecture

```text
React dashboard
    |
    | /api via the local Vite proxy
    v
FastAPI: run creation, queue, and status
    |
    v
run_report.py
    |
    +--> Agent.act(env): data -> hypotheses -> pilots -> campaign plan
    |
    +--> scoring_core.py: demo evaluation
    |
    v
Run result stored in API memory
    |
    +--> JSON: campaigns, metrics, pilots
    +--> submission.csv
```

### Main Components

| Path | Responsibility |
|---|---|
| `frontend/src/App.tsx` | Dashboard and run states |
| `frontend/src/api.ts` | API requests and response validation |
| `frontend/vite.config.ts` | Proxy to the Python API |
| `backend/agent.py` | Strategy implemented as `Agent.act(env)` |
| `backend/api.py` | HTTP endpoints and run queue |
| `backend/run_report.py` | Combined campaign, metric, and pilot report |
| `backend/environment.py` | Public environment interface |
| `backend/mock_environment.py` | Local demo environment |
| `backend/scoring_core.py` | Strategy validation and evaluation |
| `backend/local_eval.py` | Standalone agent evaluation |
| `backend/make_submission.py` | Submission CSV generation |
| `backend/data/` | Case datasets |
| `start.ps1`, `stop.ps1` | Start and stop the local application |

### HTTP API

| Method and Path | Purpose |
|---|---|
| `GET /health` | Check service availability |
| `POST /runs` | Create a run and return its `run_id` |
| `GET /runs/{run_id}` | Read the run status |
| `GET /runs/{run_id}/result` | Retrieve completed campaigns, metrics, and pilots |
| `GET /runs/{run_id}/submission` | Download the same run's CSV |
| `POST /preview` | Perform a separate synchronous calculation |

Run states are `queued`, `running`, `completed`, and `failed`.
The frontend polls once per second and stops on failure.
Unknown runs return HTTP 404; results that are not ready return HTTP 409.

## Installation and Startup

### Requirements

- Windows and PowerShell for the combined launcher.
- Python 3.12+ with `venv` and `pip`.
- Node.js 22.12+ or 24+, with npm.
- Git and access to the team repository.

### Quick Start

Run the following in PowerShell:

```powershell
git clone https://github.com/BAITC-Hacks/hack-2804924d-deadline-driven.git HackAlem
cd HackAlem
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

If you already have the working application locally, open PowerShell in its root
directory and run only the startup command.

The script creates `.venv`, installs missing dependencies, and starts the backend
and frontend in the background.

- Default dashboard: [http://localhost:5173](http://localhost:5173).
- Default API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

If a port is occupied, the launcher selects another one.
**Use the actual URLs printed in the terminal.** Logs are stored in `.run/`.

If Python is not detected automatically, specify your interpreter path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -Python C:\Python312\python.exe
```

Add `-Install` to reinstall dependencies from the project dependency files.

To stop the servers started by the launcher:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\stop.ps1
```

### Manual Startup

In the first terminal, from the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api:app --app-dir backend --host 127.0.0.1 --port 8000
```

In a second terminal, from the project root:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Vite proxies `/api` to `http://127.0.0.1:8000` by default.
Set `API_TARGET` before starting Vite to use a different backend address.

## Verification for Judges

### Dashboard Walkthrough

1. Start the application and open the dashboard URL printed in the terminal.
2. Use the agent launch button and wait for the calculation to finish.
3. Inspect the selected audiences, target tariffs, and channels in the final plan.
4. Review the pilot history, net revenue gain, total costs, and remaining budget.
5. Use the CSV export button to download the final campaigns from that run.

The exported CSV contains final campaigns, not pilot records or financial metrics.
The demo API uses a fixed `seed=42` for reproducibility. It does not evaluate
against the organizers' hidden effects.

### Standalone Agent Evaluation

After installing the Python dependencies, run these commands from the project root:

```powershell
cd backend
..\.venv\Scripts\python.exe local_eval.py
..\.venv\Scripts\python.exe make_submission.py
```

The first command prints an evaluation report. The second creates
`backend/submission.csv` with these columns:

```text
campaign_name,filter_arpu_segment,filter_data_segment,filter_call_segment,filter_current_tariff,target_tariff,channel
```

An optional multi-seed check is available:

```powershell
..\.venv\Scripts\python.exe local_eval.py --runs 10
```

Submission artifacts are `agent.py`, the generated `submission.csv`, and the
dependency file. The website and FastAPI are not required to invoke `Agent.act(env)`.

## Data and Integrations

The application uses **synthetic data supplied with the hackathon case**, not
a real customer database. Monetary values are in arbitrary units, and tariff
identifiers do not represent Beeline's current commercial plans.

| Source | Contents and Use |
|---|---|
| `backend/customer_profile.csv` | Profiles of 23,441 subscribers, current tariffs, segments, and predicted ARPU |
| `backend/data/change_tariff.csv` | Historical tariff changes and ARPU before and after; used by the agent |
| `backend/data/arpu_monthly.csv` | Additional monthly revenue history included in the case package |
| `backend/data/traffic.csv` | Additional usage data included in the case package |
| `backend/data/dict_tariff.csv`, `backend/tariff_dictionary.csv` | Tariff dictionaries |
| `backend/feature_dictionary.csv` | Feature descriptions |

The strategy directly uses customer profiles, transition history, and tariff and
channel parameters exposed by the environment. It does not directly use the
additional monthly revenue and traffic files.

The frontend integrates with the project's own FastAPI service.
There are no live CRM, billing, SMS-provider, or advertising-platform integrations.

## Constraints and Limitations

### Hackathon Constraints

- Between 1 and 10 final campaigns, with up to 5,000 subscribers per campaign.
- Up to 20 pilots, each involving 10-200 subscribers.
- Up to 15,000 total contacts, including pilots.
- A total budget of 100,000 arbitrary units for pilots and final campaigns combined.
- Each subscriber's effect is counted once, using their best campaign.
- Agent execution must take no more than 10 minutes.

See the [participant guide](https://github.com/BAITC-Hacks/hack-2804924d-deadline-driven/blob/main/backend/PARTICIPANT_GUIDE.md)
for the original case requirements.

### Current Application Limitations

- Mock-environment results do not guarantee the same judging score or real-world profit.
- The strategy is heuristic and does not guarantee a globally optimal plan.
- There is no dataset upload through the dashboard; the application uses project files.
- Runs are stored in memory and disappear when the API restarts.
- Calculations execute sequentially. Run the backend with one Uvicorn process,
  not multiple workers.
- Authentication, persistent storage, and production infrastructure are not implemented.
- Direct browser requests are allowed from `localhost:5173` and `127.0.0.1:5173`;
  the combined launcher uses the Vite proxy.
- A static frontend build does not include the Python API. Separate deployment
  requires a running backend, API routing, and appropriate allowed origins.
- The application produces plans and calculations; it does not send real offers.

## Deployment

No public deployment URL is documented in the repository. The demonstration runs
locally using the instructions above. `localhost` and `127.0.0.1` are local
addresses, not public deployment links.

[Team Repository](https://github.com/BAITC-Hacks/hack-2804924d-deadline-driven)
