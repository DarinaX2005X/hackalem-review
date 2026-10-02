# MeysQosAI — «Аким на 5 часов»

A Russian-language city-management simulator for HackAlem. Compare five alternative
plans for Astana, each with exactly five initiatives within 100 virtual budget units.
Code calculates quality-of-life scores; optional AI explains trade-offs and gives
source-linked advice. This is a hackathon demonstration, not a municipal forecast.

## Quick start for organizers and AI testers

Requirements: Git, Bash (macOS/Linux or WSL), Python **3.12 or 3.13** with venv,
Node.js **22.12+** and npm. Internet is needed to install packages. No Docker,
database server, API key, or Codex installation is required for the mock demo.
Run all commands from the repository root.

```bash
git clone https://github.com/BAITC-Hacks/hack-50d7d5d5-meysqosai.git
cd hack-50d7d5d5-meysqosai
./scripts/setup.sh
./scripts/check.sh
```

Setup creates backend/.venv, installs backend development dependencies and locked
frontend dependencies with npm ci, and creates .env from .env.example only when
absent. Existing configuration is preserved.

Terminal 1 (force mock even if your saved configuration enables live AI):

```bash
AI_PROVIDER=mock backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload --port 8000
```

Terminal 2:

```bash
npm --prefix frontend run dev
```

Open [the app](http://localhost:5173) or [API documentation](http://localhost:8000/docs).

```bash
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/simulator
```

Health should report status "ok" and ai_provider "mock"; it does not test credentials.
Stop with Ctrl-C and restart with the same commands. For occupied ports, use backend
--port 8010 and run the frontend with
`VITE_API_PROXY=http://127.0.0.1:8010 npm --prefix frontend run dev -- --port 5199`.
Open the port printed by Vite.

## Acceptance path

1. Select M7, M8, M10 in Nura, M12 citywide, and M5 in Saryarka: cost **95**.
2. Complete the scenario explicitly; the next remains locked until validation passes.
   Copy or edit choices and complete all five scenarios.
3. Submit «Рассчитать все 5 сценариев». The dialog shows the overall conclusion and
   best scenario(s) first, then individual reports.
4. Example score: **56.5431**, baseline **52.5577**. Five identical plans must share
   first place. “Best” means best among submitted plans, not a global optimum.
5. Incomplete plans, duplicate measures and forbidden pairs must return reasons,
   never a computed score.

[requests.http](requests.http) contains executable request examples.
[API contracts](docs/api.md) document validation, simulation, comparison and evidence.
Drafts persist in browser localStorage per origin; completion flags are session-only.
Editing earlier choices revokes later confirmations while preserving their selections.
Clear browser site data to remove drafts.

## Environments and configuration

Backend settings load from root .env; shell variables override them. Restart after
changes. Never commit .env or put credentials in frontend variables.

| Variable | Default | Purpose |
| --- | --- | --- |
| APP_ENV | development | Health label only, not a security switch |
| DATA_PATH | data/app.db | Writable SQLite evidence cache, created on startup |
| SIMULATOR_DATA_PATH | data/simulator.json | Versioned synthetic fixture |
| FRONTEND_ORIGIN | http://localhost:5173 | Allowed CORS origin |
| AI_PROVIDER | mock | mock or openai |
| AI_MODEL | gpt-5-mini | Configurable model; account access required |
| AI_API_KEY | empty | Server-side credential for live AI |
| AI_BASE_URL | empty | Optional; leave empty for standard OpenAI endpoint |
| VITE_API_PROXY | http://127.0.0.1:8000 | Development proxy; set in frontend process environment |

- **Mock demo:** scoring and reports require no external AI. Remote map tiles and
  fonts still need internet; bundled district polygons remain available.
- **Tests:** backend/tests/conftest.py forces mock, clears provider credentials and
  uses a temporary database. Tests do not mutate the real evidence cache.
  Frontend checks are lint, TypeScript and production build; no automated browser suite exists.
- **Live AI:** set AI_PROVIDER=openai, your key and model in ignored .env, then
  start without the mock shell override. Reports require Responses structured
  output; research also requires web_search. A custom endpoint must support these
  APIs: generic chat compatibility, including NVIDIA, is not enough and is unverified.
  Calls cost money and send scenario/context data to the provider.
- **Production:** public deployment is not verified. Follow
  [deployment requirements](docs/deployment.md); protect paid endpoints before exposure.

## Rules and model

Each scenario has its own budget of 100 and exactly five unique measures. Unused
budget gives no bonus. District measures require a district; city measures do not
target one. Maximum two measures per direction implies at least three directions.
M1/M3 conflict globally; M4/M7 and M5/M13 conflict within the same district.
Decision order does not affect results. Invalid sets receive no score.

The fixture contains five districts, ten indicators and fourteen initiatives.
Code applies delayed effects, fixed synergies, weighted district quality, the
weakest district and critical-indicator penalties. See the exact formulas in
[architecture](docs/architecture.md). AI does not control validation, scores or winners.

## AI, retrieval and limitations

Official-source research is an optional manual refresh. It searches an allowlist
(gov.kz, stat.gov.kz, data.egov.kz, budget.egov.kz, rkastana.gov.kz), stores structured
claims in SQLite, and retrieves by initiative direction. This is lightweight RAG,
not vector/embedding search or an exhaustive city-news crawler. News never
automatically changes scores.

- A fresh clone has no evidence cache. Mock refresh does not fabricate sources;
  advice returns HTTP 409 until evidence exists. Failed refresh preserves existing,
  potentially stale evidence.
- Failed or invalid AI responses return explicitly marked mock-fallback reports.
  Successful simulation alone does not prove live AI worked: inspect provider
  metadata. Live calls can be slow; cancellation does not guarantee cancelled charges.
- Schema and citation checks cannot guarantee truth, causal impact, or faithful
  prose. Announcements are not proof of success. Humans must inspect original
  links, dates, source limitations and local applicability.
- Indicators, population weights, costs and effects are **synthetic**, not current
  Astana statistics. Budget units are not tenge. This is not deployment-ready policy advice.
- Geography currency and redistribution terms are unverified. Saraishyk is context
  only, outside the five-district model. See [data provenance](data/README.md).
  The hero illustration is AI-generated, not photographic evidence.
- No authentication, rate limits, multi-user isolation, background jobs, or
  production monitoring. SQLite is for a single-instance demo. Scenarios are
  browser-local, not persisted on the server. No personal data is needed.
- Frontend dependencies are locked; backend versions have bounded ranges, not a
  full transitive lock. Clean-machine installation and public hosting require
  separate verification. No repository-wide license grant is documented.

## Repository map and development

| Path | Responsibility |
| --- | --- |
| frontend/src/ | React UI, map and styles |
| backend/app/services/simulator.py | Pure validation and scoring |
| backend/app/services/ai.py | Individual and comparative explanations |
| backend/app/services/evidence.py | Research, retrieval and sourced advice |
| backend/app/database.py | Evidence cache and refresh history |
| backend/tests/ | API, rules, calculation and fallback tests |
| data/ | Synthetic fixture and provenance; ignored runtime database |
| ai/ | Prompt registry and evaluation notes |
| docs/ | API, architecture, demo, deployment and submission |
| scripts/ | Setup and verification |
| skills/ and AGENTS.md | Repository-local AI development workflows |

Run `./scripts/check.sh` and `git diff --check` before commits. Keep changes small
and preserve the credential-free path. The [master prompt](docs/master-implementation-prompt.md)
is a planning brief, not proof every requested feature exists. Actual runtime prompts
are indexed in [ai/prompts.md](ai/prompts.md); tester instructions are in [AGENTS.md](AGENTS.md).
