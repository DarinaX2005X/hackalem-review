# Akim for 5 Hours

A city decision simulator for the Astana Innovations hackathon by **Seniors**.

**The problem.** Developing a city means moving five things at once — transport, green space, social infrastructure, safety and city services — out of one limited budget. It is hard to see in advance what a given allocation does to quality of life, and harder still to see what it costs elsewhere.

**Who it is for.** City managers and analysts, and anyone learning how budget trade-offs behave.

Every participant starts with the same synthetic data and **100 budget units**. Choose exactly **five initiatives**, inspect the Astana Quality of Life Score, and explore the trade-offs. This is an educational model, not a forecast of actual conditions in Astana.

[Russian project description](README.ru.md) | [Deployment guide in Russian](DEPLOY.ru.md)

## What has been implemented

- **The full decision model.** All 14 initiatives across five categories and five districts, with implementation lags, synergy bonuses, incompatibilities and clipping. The server owns every cost, effect and score; the client cannot alter them.
- **Automatic budget control.** A plan that exceeds 100 units, repeats an initiative, breaks the per-category limit or violates an incompatibility is rejected with a reason and receives no Score at all.
- **The Astana Quality of Life Score**, reproducing the brief's published figures exactly: 52.56 with no decisions, 56.54 for the reference example.
- **AI explanation** of strengths, risks and trade-offs in Russian, Kazakh or English. The model never calculates: Python produces the numbers and the LLM describes them. Without a key the app falls back to a clearly labelled deterministic report.
- **A proven optimum.** `optimizer.py` enumerates every valid plan — 694 395 of them — so the app can show the gap between a participant's plan and the best available one, as a lookup rather than a search.
- **Demonstration scenarios** at `/demo.html`, including a controlled pair that isolates why the weakest district dominates the Score.
- **Stress testing against city shocks.** Six deterministic events — a harsh winter, a burst heating main, a population surge and others — re-score a plan under pressure, so a plan can be judged on the bad year as well as the good one.
- **Story mode:** a four-scene prologue, budget planning, five investigations with ten discoveries, connected meetings, a mid-day council and a branching epilogue built from the server's real calculation.
- **Interface:** schematic map, current/forecast comparison, saved scenario ranking, JSON export, print and PDF output, three languages, and sound, music and brightness settings.
- **110 Python tests and 14 Node suites**, covering the reference figures, every rule, API validation, private-file protection, provider failure, the optimizer's agreement with the engine, story investigations, budget allocation and the figures quoted in this file.
- **Read-only replay** is covered alongside the story investigations, budget allocation and the figures quoted in this file.
- **A living headquarters:** four transparent narrative reputation indices, five milestones, district condition markers, a saved random city event and a separate server-calculated event forecast.
- **A 2½-minute jury presentation**, plus a team and AI-transparency screen. The presentation uses its own server-evaluated example without changing the participant's progress.

## Technologies

| Area | Choice |
|---|---|
| Backend | **Python 3.10+**, standard library only — `http.server`, `json`, `urllib`. No framework, no database, no ORM. |
| Frontend | **Vanilla JavaScript** (ES modules), HTML and CSS. No framework, no bundler or build step. The presentation uses the small `canvas-confetti` browser script from jsDelivr. |
| AI | **OpenAI Responses API**, default model `gpt-4.1-mini`, with structured JSON output. Optional; the app is fully usable without it. |
| Audio | **Web Audio API**. Both pieces are synthesised from note sequences in `public/music.js`; no audio files. |
| Tests | Python `unittest`, plus Node scripts using `node:vm` for the frontend. No test framework dependency. |
| Deployment | **Render** web service via `render.yaml`. |

The third-party runtime dependencies are optional OpenAI API access and the `canvas-confetti` browser script used by the presentation. `requirements.txt` is empty by design. The server contacts `api.openai.com` only when a key is configured; the presentation loads `cdn.jsdelivr.net` for its visual celebration effect.

## Data and integrations

**Source data** is a synthetic dataset in `data/city.json`: five conditional districts with population shares, ten indicators each on a 0–100 scale where higher is better, ten indicator weights, and 14 initiatives with their costs, implementation lags and effects. It contains **no personal, real or restricted data**, as the brief requires, and is not calibrated against real Astana statistics.

**Computed data** lives in `data/optimum.json`: the ranked output of the exhaustive search, regenerated with `export_cache()` whenever the rules or the dataset change.

**Integrations.** The OpenAI Responses API is the only external service, and only for explanation — never for calculation. The key is read solely on the server, `.env` is excluded from Git and never served over HTTP, and only the selected initiatives and already-computed synthetic results are sent. A provider failure or timeout returns a labelled deterministic report and leaves every number unchanged.

**No external service is used for anything else**: the map is a local SVG, the character portraits are local files, the fonts are the system stack, and there is no analytics, telemetry or shared storage.

## Quick start

Requires **Python 3.10+** and a modern browser. No third-party Python packages, database, Node.js or build step are needed to run the app.

```bash
python server.py
```

On Windows, use `py server.py` if needed. Open **http://127.0.0.1:8080**. Do not open `public/index.html` directly: the interface uses the server API. Stop with Ctrl+C.

The default host is `127.0.0.1`. Override it with `--host`; set the port with `--port` or the `PORT` environment variable (default 8080).

## Two-minute demo

1. Choose **Start → Free mode**: budget 100, baseline Score **52.56**, zero of five decisions.
2. Select initiatives and districts. City-wide initiatives do not require a district.
3. Inspect the map and current/forecast indicators as your choices change.
4. Load the reference example: M7, M8 and M10 in Nura, M12 city-wide, M5 in Saryarka. Cost: **95**. Score: **56.54**.
5. Evaluate the scenario to see strengths, risks, district changes and recommendations.
6. In the report, click **Show the best plan** to see the optimal five decisions, their districts and the gap between your Score and the optimum.
7. Export JSON or print the report, including to PDF through your browser. Change decisions and compare saved scenarios.

Drafts and up to 12 distinct recent reports are stored in this browser's `localStorage`; there is no shared leaderboard. Settings include Russian, Kazakh and English, sound volume/mute, and simulator brightness. Language changes apply to the interface and new reports; saved report text and user names remain unchanged. Brightness affects the app, not the monitor or printout. Sounds start after user interaction. Exiting preserves the draft.

## Story mode

1. Choose **Start → Story** to begin **"One day to save a district"**. The mode selector also offers **Free mode** and **Back to menu**. A four-scene prologue introduces your work at the city laboratory, an urgent call appointing you temporary akim, the city map and the five-hour deadline. Enter city headquarters with budget **100** and baseline Score **52.56**. An existing save resumes its current scene; **Restart story** replays the prologue.
2. Allocate spending limits, investigate before each of five meetings, choose a reply, and press **Confirm decision**. Each investigation offers two approaches and a different discovery. Continue to a city reaction before the next chapter; after transport, the mid-day council lets you keep or revisit the allocation. Later characters remember decisions and investigations, changing their replies and the evening journal.
3. After the fifth decision and its reaction, review the day. The evening scene and one of five endings explain your priorities alongside the server-calculated Score, improvements, critical indicators and initiatives left unfunded.
4. Press **Get a breakdown** to open the AI or demo report. Download it as JSON or print it, including to PDF through your browser.
5. For free choice of initiatives and districts, open **Free simulator** in the top bar. The map and indicators recalculate after each decision; the Now/Forecast toggle compares original and new district scores.
6. Change decisions and analyse again. The **Comparison** tab ranks saved scenarios by Score. **Return to meetings** resumes the story.

### Meetings and dialogue

Meetings take place in a dark headquarters: the day's agenda sits on the left, a large portrait and conversation occupy the centre, and the budget, approved decisions and city map sit on the right. Replies are spoken lines with a cost label and expandable project details. Dialogue appears gradually; **Show the full conversation** reveals it immediately. Reduced-motion preferences disable the animation. On a narrow screen the panels stack vertically. All meetings are available in Russian, Kazakh and English, and share the sound and brightness settings.

Before each meeting, a short fictional city transmission uses a different format: camera, resident message, call, news or map report. The event feed and category colours retain visible traces of confirmed choices. Select a district on the map to inspect its original and forecast indicators. The immediate resident reaction is separate from the delayed project effect: contributions come directly from the server, already adjusted for lag; the total district forecast also includes synergies and clipping.

The final screen presents the city map, the hero's address, three strongest improvements, two remaining needs and the management style. **Show the day again** reviews the five confirmed meetings with server-evaluated decision prefixes. This is read-only: it leaves the completed story, saved progress and free-mode draft intact. Close the review to return to the ending; use the existing restart control to start a new story.

| Time | Character | Initiatives and area |
| --- | --- | --- |
| 09:00 | Aigul Sadykova, teacher | M7 / M8 / M9 in Nura: school, clinic or yard sports hubs |
| 10:00 | Dana Omarova, engineer and environmental activist | M4 / M5 in Saryarka, or city-wide M6 |
| 11:00 | Marat Ibraev, taxi driver | M1 / M3 in Almaty, or city-wide M2 |
| 12:00 | Serik Akhmetov, pensioner | M10 / M11 in Nura |
| 13:00 | Aliya Nurlanova, doctor and adviser | City-wide M12 / M14, or M13 in Nura |

Meeting timestamps mark the five chapters. The prologue also has a gentle **90-second countdown**: continue before it expires or read at your own pace afterward. It pauses when the tab is hidden or the prologue is left; expiry does not advance a scene, penalize the participant or change the budget. Indicator changes are still calculated over the original horizon of **8 quarters**, not within a single day. The story draws only on initiatives from the shared catalogue and offers one per category; the free simulator keeps the original "at most two per category" rule.

Choosing a reply highlights it first; confirming submits the decisions to `/api/evaluate`. No money is spent before confirmation. Unavailable replies explain why the remaining budget could not cover the rest of the day: the client enumerates possible completions and the server revalidates the accepted initiatives. Of 162 complete routes, 127 fit within the budget of 100; the cheapest costs 67.

Meeting progress is stored separately from the simulator draft. Version 3 saves store initiative IDs, scene phase, prologue frame, approved allocations, investigations, council choice and the day's `eventId`; versions 1 and 2 migrate automatically. Existing saves continue their scene with unrestricted envelopes until the participant opens planning. Going back does not change decisions; confirming a different reply resets later meetings. Revisited scenes use only their decision prefix, including a fresh server evaluation for their map and budget. Restarting the day requires confirmation in the simulator and preserves existing reports. Final numbers are recalculated by the server on restore rather than read from the save. The epilogue buttons **Open free mode** and **Get a breakdown** carry the story's decisions into the current draft.

### Reputation, milestones and the final review

The headquarters sidebar shows **resident trust, business support, environmental reputation and efficiency**. These are explicitly labelled **illustrative narrative indices, not a poll or Score**. Each starts at 50; fixed rules use the current server-evaluated category changes, critical indicators and confirmed implementation lags, then round and clamp to 0–100. Expand **How the indices are calculated** to see every formula. Values are derived again for the visible decision prefix, so revisiting or rendering a scene never accumulates points.

The final review includes five milestones with visible earned/locked conditions. Their Russian names match the story; all labels and conditions are also translated into Kazakh and English.

| Milestone | Condition |
| --- | --- |
| «Голос районов» / Voice of the districts | Approved initiatives target at least three districts; a citywide initiative covers all five |
| «Ни одного лишнего тенге» / Not one extra tenge | Exactly five decisions spend exactly the full 100-unit budget without overspending; the title is figurative, since units are not real tenge |
| «Зелёный курс» / A greener direction | An environmental initiative is selected and the server's environment-category delta is at least 0.9 |
| «Сначала люди» / People first | A school or clinic is funded in Nura and Nura's forecast district score improves by at least 2 points |
| «Аким за пять часов» / Akim in five hours | Five server-validated decisions complete the day within budget |

Neither reputation nor milestones add funds or Score points. The expanded ending also lists districts with positive server-calculated changes, explains trade-offs such as M11's negative T1 contribution, long implementation lags and a need with no direct improvement, and adds a social, environmental, crisis, reformer or balanced leadership profile. This profile supplements the original five ending types; it does not replace their classification or change the calculation.

District markers distinguish **an indicator below 40**, **an improved district score**, and **no score improvement**, in that priority order. A visible legend explains the states and category dots; a marker can remain critical even when its district score rises. Transport lines are illustrative effects on a schematic map, not real routes.

### An unexpected event during the day

After the second confirmed decision, the story draws one of four existing events: `harsh-winter`, `heating-main-burst`, `population-surge` or `traffic-accidents`. Its ID is saved once for the day in the existing version 3 save. The event card appears automatically when at least two decisions are visible; **Calculate the event forecast** sends that visible prefix to `/api/story-event`.

The response keeps the ordinary evaluation and the event forecast separate. It shows the event's Score, critical count and district changes without modifying approved decisions, the main budget, the ordinary Score or the free-mode draft. An event has deterministic effects; only its selection for a new day is random. Reopening a save does not draw another event. Changing the visible decisions or language requires a matching fresh preview; a failed request leaves the plan intact and can be retried.

### Allocate and reconsider

Five sliders set category spending ceilings. The opening allocation, derived from catalogue prices, is social 24, environment 20, transport 22, safety 12 and services 16, leaving 6 in reserve. Raising environment to 25 makes clean fuel available. Limits cannot total more than 100 or fall below already approved spending and the cheapest remaining story decision. Lower a different limit to free more reserve. Only approved allocations are saved; slider edits take effect after **Approve allocation**.

An envelope reserves spending capacity; it does not buy a project or multiply its effects. Each selected initiative still costs its fixed catalogue price and is revalidated by `/api/evaluate`. For a previously answered meeting, **Replan from this meeting** explicitly asks to cancel that decision and its successors, reevaluates the retained prefix on the server and reopens budgeting. Earlier decisions and saved reports remain intact. Ordinary navigation or cancelling the prompt changes nothing.

### Branches and endings

Each of the 14 available replies leads to its own reaction scene. The teacher's decision changes the environmental meeting and the doctor's priorities; the ecological choice changes the taxi driver's conversation; transport changes the pensioner's requests; safety changes the adviser's reply and evening scene. The adviser recalls all four earlier choices. A school or clinic changes the utility-modernization reply, and lighting plus the digital appeals platform opens a reply explaining their existing model synergy. Reactions describe resident messages and project preparation today; actual indicator changes remain the **two-year model forecast**.

Ending styles are deterministic narrative interpretations, not extra Score bonuses. The first matching rule wins:

| Ending | Rule using the evaluated plan |
| --- | --- |
| A stretched budget | At most 5 units remain and at least one indicator is below 40 |
| Faster first steps | At least three selected initiatives have a one-quarter lag |
| A city for families | M7 or M8 is selected, and social spending is a largest category (ties count) |
| A greener direction | M5 or M6 is selected, and the server's green-category delta is at least 0.9 |
| Balancing the city's needs | All remaining mixed approaches |

All five endings are reachable among the 127 affordable story routes. Spending beyond 100 is still rejected; a stretched-budget ending means unresolved needs with little reserve, not permitted overspending. Story text, save handling and the ending classifier never calculate or modify the Score.

The five characters are fictional. Portraits were produced with the built-in image generator and are included in the repository: [files and prompt descriptions](docs/character-art.md).

## Optional AI

Without a key, calculations and optimization work normally; explanations are explicitly labelled as a deterministic demo without an LLM.

Copy `.env.example` to `.env`, configure `OPENAI_API_KEY`, and restart. `OPENAI_MODEL` overrides the model configured in `ai_analysis.py`. Process environment variables take precedence.

The integration uses the Responses API with structured JSON output. The key stays on the server, `.env` is excluded from Git, and only public assets are served. Selected initiatives and calculated synthetic results are sent to the provider. Python calculates the Score; the LLM explains effects and trade-offs. Provider failures return a clearly labelled deterministic fallback.

## Menu, settings and music

The main menu's primary actions are **Start**, **Settings** and **Exit simulator**. Start opens exactly three choices: **Story**, **Free mode** and **Back to menu**. Secondary menu links open **Jury presentation · 2½ minutes** and **Team and AI transparency**. Interface sound, music, brightness and language settings are stored in this browser.

The jury presentation has six 25-second scenes: the city problem, temporary appointment, five decisions, forecast results, a city event and the concluding value of the simulator. It offers pause/resume, previous/next, restart and exit; hiding the tab pauses it. Its example and each decision prefix are evaluated by the server, with a separate event forecast. Presentation navigation does not modify story saves, accepted decisions, reports or the free-mode draft.

The team screen identifies Seniors and explains three responsibilities: Python validates and calculates; AI explains already calculated results; a labelled deterministic demo remains available without an AI key or after a provider error. It also shows the configured AI availability, local-save policy and which synthetic data is sent for AI analysis.

- A calm background theme plays in the menu, the settings, the free simulator and during meetings. A separate finale melody plays on the epilogue screen after the fifth decision.
- Settings carry a **Background music** toggle and a separate **music volume, 0–100%** (30% by default). Muting the interface sounds does not mute the music, and the reverse is also true. A volume of zero stops the music player entirely.
- Nothing plays before the first click or Enter/Space press: the AudioContext is created or resumed inside a user gesture, following the [Web Audio guidance](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Best_practices#autoplay_policy).
- Hiding the tab, leaving the page and exiting the simulator stop the music voices and their timer. Returning to the tab resumes the music if it was playing and enabled; it stays off on the exit screen.
- Both pieces were written for this project as note sequences and are synthesised through Web Audio. There are no external recordings, samples, downloads or libraries; the source is `public/music.js`.
- Five additional procedural scene cues in `public/preferences.js` identify headquarters, the city, a phone call, a news bulletin and an urgent alert. They follow interface-sound volume/mute, user-interaction gating and visibility/exit stopping independently of music.

Resetting the settings re-enables music at 30% volume. Saves from an earlier version pick those values up automatically while keeping their existing sound, brightness and language settings. A browser without Web Audio continues to work without sound.

## Rules

- Budget: 100. Unused money gives no bonus.
- Exactly five decisions for analysis and optimization; incomplete drafts can be evaluated.
- Each initiative may occur once; at most two initiatives per category.
- District initiatives require a target; city-wide initiatives do not.
- M1 and M3 are incompatible everywhere.
- M4/M7 and M5/M13 are incompatible within the same district.
- Order does not affect results. The server owns costs, effects, scores and validation.

The detailed assignment rules allow two initiatives in a category rather than requiring one in each category. The supplied reference example follows this interpretation.

## Calculation

The horizon is eight quarters:

```text
I'[d,k] = clip(I[d,k] + sum(effect[m,k] * (8 - lag[m]) / 8) + synergy[d,k], 0, 100)
D[d] = sum(weight[k] * I'[d,k])
D_avg = sum(population_share[d] * D[d])
N_crit = number of district/indicator pairs with I'[d,k] < 40
Score = 0.7 * D_avg + 0.3 * min(D[d]) - N_crit
```

District initiatives affect one district; city-wide initiatives affect all five. Only indicators are clipped, not the Score. Calculations use unrounded values; display uses two decimal places. Higher is always better; exactly 40 is not critical.

| Indicator | Meaning | Weight |
|---|---|---:|
| T1 | Road congestion relief | 0.10 |
| T2 | Public transport access | 0.10 |
| E1 | Green spaces | 0.09 |
| E2 | Air quality | 0.11 |
| S1 | Schools and kindergartens | 0.11 |
| S2 | Primary healthcare | 0.11 |
| B1 | Street safety | 0.09 |
| B2 | Road safety | 0.09 |
| C1 | Utility reliability | 0.10 |
| C2 | Resident request resolution | 0.10 |

Population shares: Yesil 0.27, Almaty 0.24, Saryarka 0.20, Baikonur 0.13, Nura 0.16. Synergies are not reduced by lag: M1 + M2 adds T1 +2 in M1's district; M10 + M12 adds B1 +2 in M10's district; M5 + M6 adds E2 +2 in M5's district.

Baseline: city average 56.8624, weakest district 49.18, two critical pairs, Score **52.55768**. Reference example: city average 58.0776, weakest district 52.9625, no critical pairs, Score **56.54307**.

In the interface, a category summary is the average of its two indicators with weights normalized inside the category. That is a supporting visualization; the Score is computed from all ten original indicators.

## Optimizer

`optimizer.py` exhaustively enumerates **all 694 395 valid plans** — every combination of five initiatives and every district assignment, subject to the budget, the per-category limit and the incompatibilities. The optimum is therefore proven for this dataset rather than found by heuristic.

| | Score |
|---|---:|
| No decisions | 52.56 |
| Reference example from the brief | 56.54 |
| **Proven optimum** | **57.24** |

`city_model.evaluate` remains the authority on scoring, but at ~1.4 ms per call a full sweep would take about sixteen minutes. The arithmetic is therefore duplicated over flat lists, and `verify_fast_scorer` checks the fast path against the engine on sampled plans: a divergence fails the tests rather than returning a confidently wrong answer.

The ranking is exported to `data/optimum.json`, so `POST /api/optimize` is an index lookup of roughly 76 ms rather than a full search inside a request.

```bash
py optimizer.py --top 5        # best plans
py optimizer.py --verify 300   # check the fast path against the engine
```

Regenerate the cache whenever the model rules or the data change:

```bash
python -c "from optimizer import export_cache; export_cache()"
```

This takes about a minute. A missing cache returns HTTP 503 for optimization; evaluation and analysis remain available. The `bestSingleSwap` field searches only the cached top plans and may also change a district, so the interface shows the full optimal plan rather than presenting that field as a guaranteed best single edit.

### The controlled pair

`GET /api/scenarios` returns two plans that buy **the same five initiatives for the same 100 units**, differing only in the target district:

| File | Purpose |
|---|---|
| `data/city.json` | Five districts, ten indicators, weights and 14 initiatives |
| `city_model.py` | Server validation, lags, synergies, constraints and Score |
| `ai_analysis.py` | Real AI analysis and transparent deterministic fallback |
| `server.py` | API and public-file serving |
| `public/app.js` | Interface state, map, catalog, report and comparison |
| `public/preferences.js` | Volume, brightness, language and interface sounds |
| `public/music.js` | Procedural meeting and finale music with volume controls |
| `public/i18n.js` | Russian, Kazakh and English translations |
| `public/menu.css` | Main menu, settings and exit screen |
| `public/story.js` | Three-language meetings, progress and budget checks |
| `public/narrative.js` | Localized prologue, reactions, contextual dialogue and evening scenes |
| `public/story-flow.js` | Scene navigation, save migration and ending classification |
| `public/story-budget.js` | Category spending envelopes and remaining-story feasibility |
| `public/campaign.js`, `public/campaign-view.js` | Localized investigations, council, budget screen and evening journal |
| `public/story-view.js` | Scene routing, prologue and epilogue rendering |
| `public/drama.js`, `public/drama-view.js`, `public/drama.css` | Localized city transmissions, headquarters, consequence map, finale and read-only replay |
| `public/story.css` | Dialogue frame, portraits, choices and responsive layout |
| `public/portraits/` | Five local character portraits |
| `analysis_locale.py` | Localized result explanations |
| `public/styles.css` | Responsive interface, states and print layout |
| `public/city-map.svg` | Schematic city illustration |
| `tests/` | Model, API and frontend checks |
| Plan | City average | Score |
|---|---:|---:|
| Everything into Yesil | 58.75 | 54.01 |
| Everything into Nura | 58.16 | **57.21** |

The plan with the **higher** city average loses by more than three points. That is the `0.3 × weakest district` term at work: a city is only as strong as its weakest district. Both figures are pinned by tests, so if the dataset or the formula changes the test suite fails rather than the demonstration.

### Presentation page

**http://127.0.0.1:8080/demo.html** shows this comparison side by side, in Russian or English, with every figure fetched live from `/api/scenarios` rather than written into the page. Each scenario has an **Open in the simulator** button that hands the plan to the main app, so a demonstration takes one click instead of selecting five initiatives by hand.

## City shocks

A Score describes a good year. `events.py` asks what a plan is worth in a bad one.

Six events re-score the city after the plan has been applied: a harsh winter, a burst heating main, a population surge, school overcrowding, a smog episode and a spike in road accidents. Each has **fixed deterministic effects**, so every figure below is reproducible. `/api/stress` evaluates all six; story mode separately draws one of four eligible events and saves that choice. Two events are adaptive — the main bursts in the district whose utility reliability is already lowest, and overcrowding lands where social infrastructure is weakest. Real failures do not fall on the strongest neighbourhood.

A shocked city is scored by `city_model._score_state`, the same function that scores an unshocked one. The module never re-implements the Score.

| Plan | Score | Worst case | vs doing nothing |
|---|---:|---:|---:|
| Everything into Yesil | 54.01 | 48.93 | **−3.63** |
| Everything into Nura | 57.21 | 52.13 | −0.43 |
| Proven optimum | 57.24 | 52.26 | −0.30 |

The Yesil plan spends the entire budget and still ends a harsh winter **below the 52.56 available for doing nothing at all**. The same money placed in the weakest district very nearly holds.

Resilience is reported as the worst case a plan survives to, not the size of its drop: a stronger plan has more to lose and often falls further while still landing higher.

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"decisions": [...]}' http://127.0.0.1:8080/api/stress
```

## Architecture

```text
Browser: HTML + CSS + JavaScript
    │  JSON / HTTP
    ▼
server.py ─────► city_model.py ─────► data/city.json
    │               │
    │          validation + deterministic calculation
    │               │
    │               └──► optimizer.py ──► data/optimum.json
    ▼
ai_analysis.py ─────► OpenAI Responses API (when a key is set)
    └──────────────► rule-based explanation (demo / provider failure)
```

| File | Purpose |
|---|---|
| `data/city.json` | Five districts, ten indicators, weights, 14 initiatives |
| `city_model.py` | Server-side validation, lags, synergies, constraints, Score |
| `optimizer.py`, `data/optimum.json` | Exhaustive search and cached ranking |
| `scenarios.py` | Named demonstration scenarios, including the controlled pair |
| `events.py` | Deterministic city shocks, full stress test and separate story-event forecasts |
| `ai_analysis.py`, `analysis_locale.py` | Optional AI analysis and localized deterministic explanations |
| `server.py` | JSON API and serving of public files only |
| `public/app.js` | Interface state, map, catalogue, report, comparison |
| `public/story.js`, `public/story-view.js`, `public/story.css` | Meetings, dialogue, epilogue and their layout |
| `public/civic.js`, `public/civic-view.js`, `public/civic.css` | Transparent narrative reputation, five milestones, leadership profiles, district states and final trade-offs |
| `public/live-city.js`, `public/live-city.css` | Saved random-event cards, decision news, gentle prologue timer and team/AI transparency |
| `public/jury.js`, `public/jury.css` | Six-scene jury presentation, controlled timer and independent demonstration state |
| `public/portraits/` | Five local character portraits |
| `public/preferences.js`, `public/menu.css` | Volume, brightness, language, main menu |
| `public/i18n.js` | Interface and catalogue translations |
| `public/styles.css`, `public/city-map.svg` | Responsive interface and schematic map, no external map service |
| `render.yaml`, `requirements.txt` | Render web service configuration |
| `tests/` | Model, optimizer, API, story and frontend checks |

## API

- `GET /api/bootstrap` — catalogue, source data, budget, baseline calculation and AI availability.
- `GET /api/scenarios` — the demonstration scenarios with freshly recalculated figures.
- `GET /health` — server health.
- `POST /api/evaluate` — validate and evaluate a draft.
- `POST /api/analyze` — validate exactly five decisions and return the evaluation plus an explanation.
- `GET /api/events` — the shock catalogue.
- `POST /api/stress` — re-score a plan under every city shock.
- `POST /api/story-event` — validate 0–5 decisions and calculate one eligible event separately from the ordinary evaluation; accepts `eventId` and optional `language`.
- `POST /api/optimize` — validate five decisions and return the gap to the proven optimum. `POST /api/advice` is an alias of the same operation.

Example request body:

```json
{
  "language": "en",
  "decisions": [
    {"categoryId": "social", "initiativeId": "M7", "districtId": "nura"},
    {"categoryId": "social", "initiativeId": "M8", "districtId": "nura"},
    {"categoryId": "safety", "initiativeId": "M10", "districtId": "nura"},
    {"categoryId": "services", "initiativeId": "M12"},
    {"categoryId": "green", "initiativeId": "M5", "districtId": "saryarka"}
  ]
}
```

Optional `language`: `ru` (default), `kk`, or `en`. The response includes `analysis.language`; language does not affect the model's numbers. An invalid plan returns HTTP 400 with an explanation and no Score. Client changes are committed only after successful server validation; if the connection drops, the last confirmed scenario is kept.

For a story-event preview, use the same decision format plus an allowed `eventId`:

```json
{"language":"en","eventId":"harsh-winter","decisions":[]}
```

`/api/story-event` returns `{event, evaluation, forecast}`. `evaluation` is the unchanged ordinary calculation; `forecast` contains the separate event Score, delta, critical count and district indicators. The API accepts empty or incomplete valid plans, even though the story card is introduced after two decisions. Unknown events, extra fields, invalid initiatives and budget violations are rejected. `/api/stress`, `/api/analyze` and optimization retain their five-decision requirement.

## Deployment

Create a Render account, connect this repository, choose **New > Blueprint**, and select the branch containing `render.yaml`. Review the service configuration before creating it. The blueprint starts `python server.py --host 0.0.0.0`, reads the platform's `PORT`, and checks `/health`. The service starts in demo mode; an AI key can be configured through its environment settings.

**No live deployment URL has been created yet.** After deployment, verify the reference example and the optimizer, then add the working demo URL here. Follow [the Russian deployment guide](DEPLOY.ru.md). Configuration reference: [Render Blueprints](https://render.com/docs/blueprint-spec).

## Verification

```bash
python -m unittest discover -s tests -v
```

Tests need no API key and make no paid requests. They cover the reference calculations, the constraints, synergies, API validation, private-file protection, provider failures, the optimizer and the documented figures in this file. Some optimizer tests repeat the exhaustive search and take longer.

Optional frontend checks require Node.js 18+; `frontend_smoke.mjs` also needs a server running on port 8080:

```bash
node tests/frontend_smoke.mjs
node tests/preferences.test.mjs
node tests/story.test.mjs
node tests/demo_page.test.mjs
node tests/story-flow.test.mjs
node tests/story-budget.test.mjs
node tests/narrative.test.mjs
node tests/campaign.test.mjs
node tests/drama.test.mjs
node tests/civic.test.mjs
node tests/jury.test.mjs
node tests/live-city.test.mjs
node tests/music.test.mjs
```

These exercise JavaScript, screen generation, the menu, settings, the full story, every budget branch, returning to meetings, corrupted saves, transitions, language, sound events, brightness, loading the example, export, late responses and server failure. They do not launch a browser and do not check visual layout or audibility on a physical device. No paid AI requests are made.

The new suites can also be run with `npm run test:civic`, `npm run test:jury` and `npm run test:live-city`. They cover reputation formulas and exact milestone conditions, causal map states, jury pause/seek behaviour, the gentle countdown and event-preview isolation. Backend event checks exercise partial drafts and keep the ordinary evaluation separate from the shocked forecast.

Reproduce the headline figures directly:

| Check | Expected |
|---|---|
| Evaluate with no decisions | Score **52.56** |
| The reference example, cost 95 | Score **56.54** |
| `py optimizer.py --top 1` | Score **57.24** |
| `py optimizer.py --verify 300` | 0 divergences from the engine |
| `TEST_PORT=8080 node tests/demo_page.test.mjs` | controlled pair intact, handover verified |

Music tests use a fake AudioContext and a controlled clock: they check autoplay gating, scene changes, independent volume, muting, visibility, exit and delayed audio operations without playing sound. To listen manually, open the main menu, adjust music in Settings, finish five meetings, hide and restore the tab, then exit the simulator.

## Limitations

There is no shared database, real geography or calibration against real city statistics. Random story events use a small predefined catalogue with deterministic synthetic effects; they do not predict actual emergencies. The standard-library HTTP server is intended for a hackathon demo. A public production service needs a suitable production server, authentication, AI request limits and shared storage.
