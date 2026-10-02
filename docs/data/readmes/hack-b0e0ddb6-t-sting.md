# QOL-SIM

An AI-powered mayor (akim) simulator for teams, urban analysts, and anyone who wants to explore the consequences of city policy decisions.

With a limited budget, a useful initiative does not necessarily make the whole city better. QOL-SIM lets you choose **exactly five of 14 measures** for five simulated districts of Astana, then reviews the plan like a chess game: it calculates the Astana Quality of Life Score, each decision's contribution, the plan's rank among all valid plans, and the best replacements. An analyst explains the results and trade-offs using the engine's calculations.

![Plan review: score, districts, measure contributions, and recommendations](docs/images/review.png)

## Live demo

Try the deployed app: [QOL-SIM](https://hackalem.cedra.team/).

## Demo Video

[Watch the demo video](https://drive.google.com/file/d/1oXhBEGuC_Tg0gTjOR1tAu-iqICBbg92n/view?usp=sharing).

## Five hours. Three people. Four messages.

We wanted to leave with a simulator people could try and a reason for someone outside the hackathon to open it. We started looking for those people while the app was still being built.

**Sayazhan built the application.** He explored interface designs, challenged implementation choices, picked the features and worked through them with Codex. He owned the main repository.

**Dos worked out what to build and whom to show it to.** He researched the case, shaped the product logic, found contacts and prepared the outreach workflow.

**Margulan kept the build connected to that search.** He found design references, worked with Sayazhan on the user flow, filmed the team, kept the log and sent the messages. We made product decisions together and wrote this account together.

One plan did not make the cut: a separate agent-orchestration extension. We ran out of time to integrate it and dropped it from this submission. It is not part of the delivered product.

By the end of the build, we had sent four messages asking for expert feedback or offering the simulator as a training exercise. The [outreach log](#outreach-for-adoption) records the recipients and proposals. No replies are confirmed in the latest log. Our next step is to show the working scenario, ask where the model gets things wrong, and find out whether it belongs in a classroom for public officials.

> **Watch the five hours behind the demo.** See the team working through screens, building the app and reaching out to people who might use it—all during the same build window.
>
> **Build and outreach video diary — Google Drive link to be added.**

## Doc files

- [Build story](docs/BUILD_STORY.md) — The hackathon development timeline, including product decisions, implementation milestones, and lessons from testing.
- [Source dataset](docs/data/astana-dataset.md) — The scenario's district indicators and measure catalog, including costs, implementation lags, and effects.
- [Implementation plan](docs/superpowers/plans/2026-09-23-plan-review-simulator.md) — The original simulator plan, covering architecture, API contracts, implementation steps, and validation checks.
- [External tools](docs/EXTERNAL_TOOLS.md) — The inventory of vendored agent skills, their sources and pinned revisions, attribution, licensing, and update instructions.

## How it works

You play the mayor of a simulated Astana. Your goal is to improve life in the city with a limited budget.

1. **Explore the city.** Open the [live demo](https://hackalem.cedra.team/) and look at the districts to see where schools, transport, healthcare, and other services need help.
2. **Build a plan.** Choose five different measures, pick a district where needed, and stay within the budget of 100. You can load an example plan to get started.
3. **Review the results.** See your city's quality-of-life score, which districts benefit, and which choices help or hurt. Read the analyst's explanation of the strengths and risks.
4. **Improve your choices.** Try a suggested replacement and review the updated result. You can also bring the plan to the mayor's council, hear different views, and accept a proposed change.
5. **Compare with other teams.** Submit your plan under a team name. The registry keeps your team's best score so you can compare results and try again.

The city data is synthetic: this is a way to explore trade-offs and learn from decisions, not a prediction of real-world outcomes.

## Tech Stack

- **Language and runtime:** TypeScript 5.9, Node.js 24, and npm 10 workspaces for the shared frontend/backend repository.
- **Frontend:** React 19, React DOM, and Vite 8 with the React plugin; CSS and SVG for the interface, district map, and charts.
- **Backend:** NestJS 12 with its Express adapter and `reflect-metadata` for the HTTP API and application services.
- **Simulation engine:** Plain TypeScript for plan validation, scoring, exhaustive plan comparison, exact Shapley contributions, and suggested replacements.
- **Database:** PostgreSQL 17, TypeORM 0.3, and the `pg` driver for migrations, team submissions, and council history, including JSONB records.
- **External AI API:** OpenAI Chat Completions, called through native server-side `fetch`, with `gpt-4.1-mini` as the default configurable model. Tool calling supports the analyst and council chair; offline templates keep the flow working without an API key.
- **Live council updates:** Server-Sent Events (SSE), RxJS, and the browser's `EventSource` API for streaming and replaying saved session events.
- **Environment configuration:** `dotenv` and environment variables for database settings, server-only API credentials, model selection, and timeouts.
- **Unit and component tests:** Vitest with V8 coverage, React Testing Library, `jest-dom`, `user-event`, and jsdom; line and branch coverage are enforced at 100%.
- **Browser and integration tests:** Playwright with Chromium, plus Node.js smoke scripts that check the running frontend, API, database, and council flow.
- **Code quality:** ESLint, typescript-eslint, React Hooks lint rules, Prettier, and TypeScript type checking.
- **Local development:** Docker and Docker Compose for the app and database, Nest CLI for backend builds and watch mode, `ts-node` for TypeORM tooling, and `concurrently` to run both development servers.
- **Version control and CI:** Git, GitHub, and GitHub Actions for pull requests, static checks, coverage, builds, browser tests, and Compose smoke/migration checks.
- **Deployment setup:** The [developer guide](docs/DEVELOPMENT.md#digitalocean-app-platform) covers DigitalOcean App Platform and Managed PostgreSQL, including pre-deploy migrations and database TLS certificates.
- **AI development tools:** Codex and Claude Code, with shared repository instructions and vendored Vercel skills for React composition, performance, view transitions, and interface reviews. Sources and licensing are recorded in [External tools](docs/EXTERNAL_TOOLS.md).

## Outreach for adoption

On September 23, alongside development, we contacted four recipients about expert feedback and potential use of the city management simulator:

- **Asad Bokhari, NU GSPP** — feedback on where our model diverges from practice, drawing on his research into AI, e-government, and smart cities.
- **Didar Yedilkhan, Director of AITU's Smart City Research Center** ([d.yedilkhan@astanait.edu.kz](mailto:d.yedilkhan@astanait.edu.kz)) — an invitation to review the working version and take it forward at the Center, which works on SmartCity models and urban data in Astana.
- **Zhanar Ismailova and GSPP Executive Education** ([zhanar.ismailova@nu.edu.kz](mailto:zhanar.ismailova@nu.edu.kz), [execed.gspp@nu.edu.kz](mailto:execed.gspp@nu.edu.kz)) — a proposal to use the simulator as a training exercise for serving public officials whose work involves allocating budgets.

The simulator is offered free of charge, with no obligations. **No replies had been received by the time of the final presentation.** The outreach is recorded in our [build story](docs/BUILD_STORY.md#september-23--outreach-for-adoption).

## One-command startup

Requires Docker with Compose v2. From the repository root:

```sh
cp .env.example .env
docker compose up --build --wait --wait-timeout 180
```

Open [localhost:5173](http://localhost:5173). API: [localhost:3000/api/scenario](http://localhost:3000/api/scenario). On startup, the API applies migrations and enumerates the plan space once. PostgreSQL stores the team registry and council session history; scenario data is versioned in code.

**The core flow does not require an AI API key.** With an empty `OPENAI_API_KEY`, the deterministic offline analyst and the full council session still work. If the provider fails, times out, or returns an invalid response, the app uses a template for the affected response and clearly labels its source.

```sh
npm run smoke           # Check the running stack; requires local Node
# Run the same check without local Node:
docker compose exec -T web node scripts/smoke.mjs http://localhost:5173 http://api:3000
docker compose logs -f
docker compose down     # Stop services and preserve PostgreSQL data
```

Compose uses the project name `testing-workspace`, binds ports to localhost, and stores the database in a named volume. This is a development environment with hot reload. Rebuild the containers after changing dependencies or environment variables. The example password is for local development only; changing `.env` does not change the password of an existing database.

For DigitalOcean App Platform, run migrations in a separate pre-deploy Job and set `POSTGRES_CA_CERT` for a verified TLS connection to Managed PostgreSQL. [Setup and commands](docs/DEVELOPMENT.md#digitalocean-app-platform).

## Mayor's council

From a completed review, select **"bring to council"**, then **"start session"**. Seven fictional participants discuss the plan, propose valid replacements, and vote on the chair's verified recommendation. These are educational characters identified only by their roles; the data is synthetic.

![Council: roundtable and validated statements](docs/images/council.png)

| Participant        | Score component and metric                                            |
| ------------------ | --------------------------------------------------------------------- |
| Transport          | T1, T2 · weight 0.20; weighted contribution to the city average score |
| Environment        | E1, E2 · 0.20; the same contribution metric                           |
| Social services    | S1, S2 · 0.22; the same contribution metric                           |
| Safety             | B1, B2 · 0.18; the same contribution metric                           |
| Municipal services | C1, C2 · 0.20; the same contribution metric                           |
| Ombudsman          | Lowest district score minus the number of critically low values       |
| Finance            | Score gain over the do-nothing baseline per 10 budget units           |
| Chair              | Final Score, validity, and the cost of trade-offs                     |

The five sector contributions add up to the city average score. The engine determines positions, up to three candidates for each participant, replacement impacts, objections, and votes. The LLM writes the dialogue; numbers and IDs are checked against the allowed facts. Validating numeric literals does not establish the semantic truth of arbitrary text: the calculation log is available alongside the dialogue.

```text
Engine briefs → seven parallel statements → validation of each statement
→ proposed amendments → up to two objections → the author's response
→ chair: evaluate_package / get_amendment_impacts, up to four steps
→ verified recommendation only → vote → saved minutes
→ accept an amendment or package → updated plan → new review
```

An invalid ID, unsupported number, malformed JSON, or timeout replaces only the affected statement with a template. If the chair fails, the minutes are assembled from engine-verified options. Without a key, every stage uses templates with the same events. The interface labels the source of the dialogue and minutes; disconnecting the browser does not stop the session on the server.

PostgreSQL stores the original plan, events, and minutes. SSE publishes events after they are saved; reconnection resumes the history from the event ID. Saved sessions can be opened and replayed. After an API restart, an unfinished session is marked as interrupted; completed minutes remain available. The local stack is designed for a single API process.

**One-minute demo:** strong example → council → compare light rail transit (LRT) in Nura and Esil → environmental objection → rejected package costing 104 → vote → accept LRT in Nura → new Score **57.21**. The engine calculates the numbers; mockups are not a source of calculations.

Clarification of the original plan and mockups: replacing **M10@Nura → M14** gives **56.62718 → 56.63**, a gain of **0.08411 → +0.08**. The reference value of 56.64 was inaccurate. The benchmark for LRT in Nura is **57.20556 → 57.21**, a change of **+0.66249 → +0.66**; the vote is **5 in favor / 1 abstention / 1 against**.

### Connecting OpenAI

Add your key to the root `.env` when it is ready:

```dotenv
OPENAI_API_KEY=your_key_from_platform.openai.com
AI_MODEL=gpt-4.1-mini
AI_COUNCIL_MODEL=gpt-4.1-mini
AI_TIMEOUT_MS=25000
AI_COUNCIL_TIMEOUT_MS=12000
```

After changing `.env`, restart the local API or run `docker compose up -d --build api`. An empty `AI_COUNCIL_MODEL` falls back to `AI_MODEL`. Only the server reads the key; there are no `VITE_` variables for it. Availability of the selected model depends on your OpenAI project. The integration is tested with deterministic provider responses and offline mode; calls using a real key have not been verified.

## How results are calculated

The data is **synthetic**, and the map boundaries are **schematic**. The simulator explains the defined model rather than forecasting the real urban economy.

```text
Realized effect = full effect × (8 − lag) / 8
I'[district, indicator] = clip(baseline value + effects + synergies, 0, 100)
D[district] = Σ weight[indicator] × I'[district, indicator]
D_avg = Σ population_share[district] × D[district]
Score = 0.7 × D_avg + 0.3 × min(D) − N_crit
N_crit = number of values strictly below 40
```

The horizon is eight quarters. Synergies are fixed and are not scaled by lag. Unspent budget earns no bonus. The engine retains full precision internally; HTTP responses and the interface round values for display. Ranks use unrounded values, and tied results share a rank.

Rules: exactly five distinct measures, total cost no greater than 100, at most two measures per sector, and a district required for district-level measures but forbidden for citywide measures. M1 and M3 are incompatible regardless of district; M4/M7 and M5/M13 are incompatible within the same district. All five sectors are available, but covering all five is not mandatory: the dataset contains no such constraint.

The Score change is calculated before rounding: for the example, it is **3.98539**, displayed as **+3.99**. Subtracting the already rounded values 56.54 and 52.56 gives 3.98, so the client receives a separate engine-calculated `scoreDelta` field.

**Each move's contribution is its exact Shapley value** across all subsets of the plan. The contributions add up to the Score change from the do-nothing baseline. A move's rating accounts for the best valid single replacement:

| Rating                    | Rule                                                                                                       |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Blunder (`blunder`)       | Negative contribution                                                                                      |
| Mistake (`mistake`)       | Best replacement gains ≥ 1.0                                                                               |
| Inaccuracy (`inaccuracy`) | Best replacement gains ≥ 0.3                                                                               |
| Good (`good`)             | Best replacement gains > 0.05                                                                              |
| Best (`best`)             | Replacement improves the score by no more than 0.05                                                        |
| Brilliant (`brilliant`)   | Rated `best`, with either removal bringing back a critically low value or the measure activating a synergy |

Efficiency = `(Score − baseline Score) / (optimum − baseline Score) × 100%`; it can be negative for a harmful plan. Percentile reflects the plan's position in the full space of valid plans. The histogram uses the same results with a bin width of 0.25.

## Benchmark checks

`npm test` verifies the source scenario's numbers without network requests or a database:

| Check                               | Result                                               |
| ----------------------------------- | ---------------------------------------------------- |
| Do nothing                          | 52.56, two critically low values in Nura             |
| Strong example                      | 56.54; budget 95; 0 critically low values            |
| Number of valid plans               | 694,395                                              |
| Optimum                             | 57.24; M2, M3@Nura, M8@Nura, M9@Nura, M14; budget 98 |
| Worst valid plan                    | 52.04                                                |
| Plans worse than doing nothing      | 20,003                                               |
| Example's rank                      | 566; percentile 99.9; efficiency about 85%           |
| Example's contributions             | 1.45, 1.40, 0.49, 0.47, 0.17; exact sum 3.98539      |
| Example's best replacement          | M5@Saryarka → M3@Nura; 57.21, gain 0.66              |
| Trap plan                           | 52.45; budget 86; M11@Almaty contribution −0.87      |
| Best plan covering all five sectors | 56.34                                                |

<a id="архитектура"></a>

## Architecture

```text
React / Vite → same-origin /api proxy → NestJS
                                          ├─ SimulationService → pure TypeScript engine
                                          │    ├─ astana-v1 version, rules, Score
                                          │    └─ exhaustive search, Shapley values, replacements, move ratings
                                          ├─ AnalysisService → engine tools → OpenAI
                                          │    └─ offline analyst when the key is missing or an error occurs
                                          ├─ CouncilService → briefs → OpenAI / templates → minutes
                                          │    └─ PostgreSQL jsonb → history / SSE → React
                                          └─ SubmissionsService → TypeORM → PostgreSQL
```

- `apps/api/src/simulation/engine`: data, validation, scoring formula, exhaustive search, exact contributions, and best replacements. No Nest or database dependency.
- `apps/api/src/simulation`: HTTP parser and service that assembles the Review. Invalid plans do not receive a Score.
- `apps/api/src/analysis`: LLM adapter, bounded tool loop, JSON validation, and offline explanations. The HTTP adapter is isolated in `llm-client.ts`.
- `apps/api/src/submissions`: server-side recalculation of results and plan persistence.
- `apps/api/src/council`: metrics, briefs, amendments, agents, voting, streaming, and session persistence.
- `apps/web/src/features`: builder, review, council, registry, and tutorial (`onboarding`). The browser does not implement the Score formula; the lag control calculates only the tutorial example.
- `apps/*/tests`: behavior tests whose structure mirrors the source files.

The agent uses `evaluate_plan`, `explain_contributions`, `get_rank`, `find_best_swaps`, and `evaluate_alternative`. It is limited to six steps, with an overall timeout of 25 seconds by default. Numbers and valid alternatives come from the tools. The final response is checked for structural validity. An additional check rejects numeric literals absent from the tool results, allowing for rounding. It does not verify whether a number refers to the correct district or claim; this is not full semantic validation. The offline review formats engine results directly.

The registry is public and has no authentication: a team name is a label, not a protected account. Names are compared case-insensitively. Submission history is retained, and the table shows each team's best result; when Scores are equal, the earlier submission wins.

## Challenge requirements

We track the challenge's requirements and supporting evidence in the [version 0.1 plan](docs/compliance/PLAN.md) and the [initial requirements map](docs/compliance/RULES_MAP.md). These are **works in progress**: further detail and final README coverage are still being developed, and full compliance is not yet claimed.

| Requirement / criterion                          | Implementation                                      | Verification                                                            |
| ------------------------------------------------ | --------------------------------------------------- | ----------------------------------------------------------------------- |
| Shared budget and data; criterion 1              | `simulation/engine/scenario.ts`, `/api/scenario`    | `simulation/engine/scoring.test.ts`, `simulation/simulation.test.ts`    |
| Decisions across five sectors                    | Catalog of 14 measures, builder filters             | `simulation/engine/scoring.test.ts`, `features/Builder.test.tsx`        |
| Budget control; criterion 2                      | `validation.ts`, server-side rejection of reviews   | `simulation/engine/scoring.test.ts`, `simulation/simulation.test.ts`    |
| Measures change indicators; criterion 3          | `scoring.ts`, lags and synergies                    | `simulation/engine/scoring.test.ts`                                     |
| Astana Quality of Life Score calculation         | `scoring.ts`, `landscape.ts`                        | `simulation/engine/review.test.ts`, `scripts/smoke.mjs`                 |
| AI analysis and clear trade-offs; criterion 4    | `analysis/analyst-agent.ts`, `offline-analyst.ts`   | `analysis/analyst-agent.test.ts`, `analysis/offline-analyst.test.ts`    |
| Minutes and the cost of trade-offs; criterion 4  | Mayor's council, dissenting opinions, and voting    | `council/agents.test.ts`, `council/domain-numerics.test.ts`             |
| AI recommendations for improvement               | Verified council amendments and packages            | `council/domain.test.ts`, `e2e/council.spec.ts`                         |
| Technical implementation: agents with tools      | Parallel statements, bounded chair agent, saved log | `council/agents.test.ts`, `council/sessions.test.ts`                    |
| Strengths, risks, consequences                   | Structured analyst report                           | `analysis/offline-analyst.test.ts`, `features/Review.test.tsx`          |
| Changing the plan changes the Score; criterion 5 | `swaps.ts`, a new review after replacement          | `simulation/engine/review.test.ts`, `scripts/smoke.mjs`                 |
| Team comparison                                  | PostgreSQL, `submissions.service.ts`                | `submissions/submission.test.ts`                                        |
| Visualization of changes                         | Map, indicator table, histogram                     | `components/Map.test.tsx`, `features/Review.test.tsx`; browser test run |

Backend test paths are relative to `apps/api/tests`; frontend test paths are relative to `apps/web/tests`. Exact commands are in the [developer guide](docs/DEVELOPMENT.md).

## Limitations

- **A simplified city model.** The five districts, 14 measures, effects, and map are synthetic or schematic. Scores describe the fixed `astana-v1` scenario; they are not forecasts based on live city data.
- **One planning round.** Each plan contains five measures evaluated over a fixed eight-quarter horizon. There are no unexpected city events, quarter-by-quarter budget changes, or NPC opponents yet.
- **AI explanations are only partly verified.** The engine calculates scores and checks proposed plans. Text validation rejects unsupported numbers and IDs, but cannot guarantee that every sentence interprets those facts correctly. The calculation log is available for inspection.
- **Generated dialogue depends on OpenAI.** Without an API key, or when a provider response fails validation or times out, the affected explanation uses a labelled template. Scoring and the council flow still work, but the fallback does not generate new dialogue.
- **No protected team accounts.** Team names are public labels, so another person can submit under the same name. The application does not implement authentication or request rate limits.
- **Council sessions require one API process.** Live meetings are managed in server memory, with events saved to PostgreSQL. A server restart interrupts unfinished meetings; saved events and completed minutes remain available. There is no distributed worker to resume a meeting or coordinate multiple API instances.
- **Verification has a limited scope.** Automated OpenAI tests use fake provider responses, and browser tests run in Chromium with AI disabled. These checks do not establish live model quality or Firefox and Safari compatibility.

## Roadmap

- Unexpected city events and budget reallocation.
- NPC rivals and comparisons of their positions between sessions.
- A quarter-by-quarter tournament and comparisons of decision sequences.
- Verification of every numerical LLM claim against tool results.
- Team authentication, rate limits, and public deployment configuration.

See the [developer guide](docs/DEVELOPMENT.md) for detailed local development commands, environment variables, the HTTP API, and migrations.
