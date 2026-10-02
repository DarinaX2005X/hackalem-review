# Sobytie — Event Contractor Shortlist

**Up to three suitable contractors, source-backed explanations, and a verified next step when your request has too few matches.**

Sobytie ("Событие", Russian for "event") is a working MVP for the Kazakhstan event-contractor hackathon task **#79-lite**. It searches the supplied 66-profile catalogue, enforces every requested constraint, and explains the result. The interface is in Russian to match the source data; this guide is for evaluators.

## Run the entire project with one command

Prerequisite: Docker Desktop (running, Linux containers) or Docker Engine with Docker Compose. Port **8000** must be available. The first build requires internet access to download the Python image and pinned dependencies.

From the repository root:

```sh
docker-compose up --build -d
```

Modern Compose also accepts the equivalent `docker compose up --build -d`.

Open **[http://localhost:8000](http://localhost:8000)**. Allow a few seconds for startup after the command returns.

That command builds and starts **both the API and the frontend**, installs all runtime dependencies inside the image, and loads the bundled catalogue. No local Python, Node.js, npm install, database, migration, seed command, AI preprocessing, or second web server is required. A `.env` file is optional.

- Application: [localhost:8000](http://localhost:8000)
- Interactive API documentation: [localhost:8000/docs](http://localhost:8000/docs)
- Readiness: [localhost:8000/api/health](http://localhost:8000/api/health)
- Dictionaries, examples and AI capabilities: [localhost:8000/api/meta](http://localhost:8000/api/meta)

```sh
docker-compose ps
docker-compose logs --tail 50 backend
docker-compose down
```

## What makes the solution useful

- **Strict eligibility:** a busy, over-budget, wrong-city or otherwise incompatible contractor cannot be added by a model.
- **Traceable differences:** prices, budget headroom, languages, hours and attributed description excerpts have visible sources.
- **Actionable empty states:** date and budget suggestions are checked by running the complete selection algorithm again. Each suggestion changes exactly one field and increases the number of displayed options.
- **Honest limits:** starting prices are not quotes; calendar availability is not a booking; synthetic and imputed data are labelled.
- **Reliable demo:** the form, all eight presets, ranking and suggestions work without an API key. External AI adds natural-language input and richer explanations.

## API credentials: two independent AI stages

Create an optional `.env` in the repository root using [`.env.example`](.env.example) as a reference. Docker Compose reads it automatically. After changing credentials or models, run the same startup command again; a plain `restart` does not reload environment settings.

### Simplest setup: one provider for both stages

OpenAI:

```dotenv
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-6-luna
```

Or Anthropic:

```dotenv
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-sonnet-5
```

Use API credentials with model access and available provider quota. A ChatGPT or Claude chat subscription is not an API credential. Keep keys in `.env` or the host environment; never put them in frontend code. `.env` is ignored by Git and excluded from the image. Keys are passed only to the backend at runtime.

### Separate credentials and models for each stage

For example, use OpenAI for parsing and Anthropic for the final explanations:

```dotenv
# Leave shared keys empty when separating providers.
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

PARSE_OPENAI_API_KEY=your-openai-api-key
PARSE_OPENAI_MODEL=gpt-6-luna
PARSE_ANTHROPIC_API_KEY=

ANSWER_OPENAI_API_KEY=
ANSWER_ANTHROPIC_API_KEY=your-anthropic-api-key
ANSWER_ANTHROPIC_MODEL=claude-sonnet-5
```

The four independent credential variables are:

- `PARSE_OPENAI_API_KEY` / `PARSE_ANTHROPIC_API_KEY`: free-text interpretation.
- `ANSWER_OPENAI_API_KEY` / `ANSWER_ANTHROPIC_API_KEY`: final card explanations.

Each has a matching model variable: `PARSE_OPENAI_MODEL`, `PARSE_ANTHROPIC_MODEL`, `ANSWER_OPENAI_MODEL`, `ANSWER_ANTHROPIC_MODEL`.

**Selection rules, independently for each stage:**

1. `PARSE_ENABLED=false` or `ANSWER_ENABLED=false` disables that stage.
2. A non-empty stage-specific key overrides the shared key for that provider.
3. If an effective OpenAI key exists, use OpenAI. Otherwise, use Anthropic if its effective key exists.
4. Model selection follows stage-specific model → shared provider model → built-in default.
5. With no key, text input is disabled and catalogue-based explanations remain available.

An invalid OpenAI key still has priority. Runtime failures do **not** silently switch providers or incur a second provider charge: parsing reports an error, while explanations fall back to the catalogue response. Remove the OpenAI key to select Anthropic. `/api/meta` reports the configured provider/model for each stage, never the keys; `enabled` means configured, not that provider access has been verified.

### Suggested models

The following API IDs were checked against official documentation on **2026-09-23**. Account availability and quotas vary. The defaults below are application choices for a short extraction task, not a benchmark result.

**OpenAI — three choices:**

- `gpt-6-luna` — default for this app; suitable starting point for focused extraction and excerpt selection.
- `gpt-6-sol` — a balanced option if your examples need stronger interpretation.
- `gpt-6-astra` — highest-capability option for difficult briefs; allow for greater cost and latency.

See the [official OpenAI model catalogue](https://developers.openai.com/api/docs/models) and [structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs). The app uses the Responses API with strict JSON output and `store=false`; GPT-5/6 calls use low reasoning effort for interactive latency.

**Anthropic — three choices:**

- `claude-sonnet-5` — default; a practical starting point for this app's quality/latency tradeoff.
- `claude-haiku-4-5-20251001` — a faster alternative for short, straightforward briefs.
- `claude-opus-5-5` — a stronger option for difficult interpretation; heavier models may exceed the interactive deadline.

See the [official Anthropic model catalogue](https://platform.claude.com/docs/en/models/overview) and [structured outputs guide](https://platform.claude.com/docs/en/build-with-claude/structured-outputs). The app uses Messages with `output_config.format`. These are direct provider APIs, not Azure or Bedrock credentials.

Each AI call has an **8-second total deadline**, with no automatic retry. The browser allows 12 seconds per endpoint request. A text-driven search can make two sequential calls: parsing and then explanation generation. Provider latency is external; a slow answer falls back to the functioning catalogue search.

## User flow

### Form

Choose a city, date, event format, contractor category and budget in KZT. Language and attendance duration are optional. Click **«Подобрать варианты»**. The page shows up to three cards, supporting evidence, exclusion reasons and useful alternatives.

### Natural language

When parsing credentials are configured, enter a request in **«Или опишите своими словами»**, for example:

> Нужен ведущий в Алматы на корпоратив 14 ноября 2026, бюджет 700 тысяч тенге, на русском языке, на 6 часов.

Click **«Разобрать и подобрать»**. A complete, unambiguous interpretation fills the form and starts the same search. Missing or uncertain values fill a partial form and require clarification before searching. Unmentioned fields never inherit values from a previous request or preset.

The parser normalizes clear synonyms into catalogue values, validates dates and numeric bounds, and must provide a literal supporting text span for every extracted value. It does not silently choose among multiple services or invent a missing budget. Unsupported constraints and inferred years require review. Model interpretation is still fallible: all applied values remain visible and editable in the form.

### Final explanations with AI

The backend first determines eligible candidates and their order. Only then does the answer model see the accepted query and up to three selected profiles. It selects a distinguishing excerpt and an emphasis (price, language or hours). The server validates the IDs and exact quote membership, computes every number, and assembles the final card text with sources.

This is **grounded AI-assisted answer generation**: the model chooses useful content; code supplies factual wording and arithmetic. It cannot change eligibility, ranking, prices, counts, diagnostics or suggestions. Invalid IDs, invented quotes, malformed output, refusal, rate limits and timeouts produce the normal catalogue explanations with a visible notice. Empty results need no model call: their reasons and alternatives are computed directly.

## Demo guide for judges

The eight buttons under **«Попробуйте на примере»** send ordinary API requests against the bundled CSV. They are not prerecorded answers.

1. **Halls, Almaty, 13 November, 7M KZT:** six eligible profiles, three displayed (`HK-64395`, `HK-58236`, `HK-90011`) in the default ranking.
2. **The same halls on 14 November:** two eligible profiles; the interface explains calendar exclusions.
3. **Florist, Almaty, 13 November, 500K KZT:** one result; `max_hours=null` is handled without inventing unlimited attendance.
4. **Decorator in Astana:** the category is absent there. Other cities are labelled as catalogue presence, not a promise of availability or travel.
5. **Halls on 19 December:** no match; applying 18 or 20 December actually produces a candidate.
6. **Host on 14 November, 600K KZT:** no match; the verified 650K threshold adds a candidate.
7. **Hosts on 12 December:** no match due to the calendar; an increased budget is not presented as a cure.
8. **Live bands, Almaty, 13 November, Kazakh, 1.2M KZT:** two similarly priced profiles. With AI enabled, inspect the source excerpts for differences in musical composition. Without descriptions, the interface honestly states when the structured fields cannot distinguish them.

Repeat any query to demonstrate the same card order. Change the date, inspect **«Источники»**, apply a suggested correction, and show the resulting request parameters.

## Selection rules and architecture

One FastAPI/Uvicorn process serves the API and plain HTML/CSS/JavaScript on the same origin. Python 3.13 and dependency versions are pinned in the Dockerfile and constraints file. Runtime provider HTTP calls use HTTPX. No database is required: the 66 immutable profiles are parsed once into memory.

```text
Form -------------------------------> validated query
Free text -> optional provider -> editable/validated query
                                         |
                                         v
CSV -> city/category -> ALL hard filters -> deterministic top 3
                         |                       |
                         v                       v
                exclusion diagnostics     optional answer provider
                         |                -> exact source validation
                         v                       |
             date/budget re-evaluation           v
                         +--------------> cards + evidence + next steps
```

Hard filters enforce exact category membership, exact city, date not in `busy_dates`, accepted event format, starting price within budget, and optional language/hours. `max_hours=null` means the attendance-hours constraint is inapplicable; it never bypasses the calendar.

The order is `(-E, price_from_kzt, id)`. `E` is a direct format witness from a complete, previously reviewed offline registry, if supplied. The default checkout has no such registry, so all E values are zero and ordering is ascending starting price, then ID. This is a disclosed product heuristic, not a quality score. Runtime AI excerpts **never** change E or ordering. Model wording/excerpt selection may vary between calls; the underlying selection and order do not.

There are three explicit outcomes: `found`, `no_category_in_city`, `all_filtered`. Suggestions run through the same `evaluate()` function and must increase `min(3, eligible_count)`. Exclusion counters overlap because a contractor may fail several constraints.

### Source data and limits

- Data: [`backend/data/catalog.csv`](backend/data/catalog.csv), 66 anonymized profiles, including 13 labelled synthetic profiles.
- Original CSV SHA-256: `6a724b6b7dfb5973343e68ba18dadb60fc807d87e3d78f03ee86fb26cb089f7d`.
- Calendar: **2026-09-23 through 2026-12-31**, inclusive. Dates outside it are rejected.
- Budget: for one contractor service, in integer KZT, up to JavaScript's safe integer limit.
- Starting prices, imputed city/price values, and description claims are presented with their limitations.
- Quotes are exact excerpts, not independent fact-checking. Automatic substring validation cannot prove semantic completeness.
- No booking, payments, authentication, contractor messaging or claims of guaranteed availability.
- This is a local hackathon MVP. Public hosting with paid API keys needs access/rate controls.

### Optional offline registry

The earlier reviewed-registry workflow is retained in [`backend/ai/README.md`](backend/ai/README.md). It is **not a startup requirement** for either the no-key mode or the live OpenAI/Anthropic features. No generation job or 66-profile paid batch runs during startup.

A compatible `backend/data/facts.json`, if supplied before building, enables `approved_facts`. Missing or invalid registries fall back to structured fields. Runtime excerpts use `live_quotes` and are never mislabelled as a fully reviewed offline registry. The legacy offline preparation CLI currently uses OpenAI; it is separate from the two-provider runtime integration.

## API

- `GET /api/health`: catalogue readiness, count and version hashes; does not make a paid provider request.
- `GET /api/meta`: dictionaries, calendar, eight demo queries and per-stage AI configuration.
- `POST /api/parse-request`: `{ "text": "..." }` → partial/complete query, missing fields, review fields and warnings. Returns 503 when parsing is disabled or unavailable.
- `POST /api/recommendations`: validated query → cards, evidence, counts, diagnostics and checked suggestions. `answer_generation.status` is `disabled`, `generated`, `fallback` or `not_needed`.

Example request body for `/api/recommendations`:

```json
{
  "city": "Алматы",
  "date": "2026-11-13",
  "event_format": "корпоратив",
  "category": "Банкетный зал",
  "budget_kzt": 7000000,
  "duration_hours": 6,
  "language": "русский"
}
```

Invalid input returns 422 with an error envelope and field errors. Missing/broken catalogue data returns 503. Provider failure during explanation generation returns a valid recommendation response with a fallback notice. Keys, upstream error bodies and stack traces are not sent to the browser. Only application assets are publicly served; tests and developer tools return 404.

## Verification and development

Verification snapshot (2026-09-23): **139 backend tests, 12 frontend contract checks, and 24 browser scenarios passed**. The no-key Docker application was exercised with 27 live HTTP requests across all eight demo scenarios, plus the browser/API integration check. Provider protocol and text-to-recommendation tests use simulated OpenAI/Anthropic HTTP responses. **No live paid provider call was verified in the delivery environment because credentials were not configured**; the optional live-AI command below checks that boundary with your credentials.

The running image includes a dependency-free HTTP smoke checker:

```sh
docker-compose exec -T backend python -m backend.smoke
```

It exercises all eight examples, repeated ordering, and suggested changes against the live API. With answer credentials configured, it makes real provider requests; use no keys or `ANSWER_ENABLED=false` for an offline demonstration. To require successful live AI excerpts instead of accepting fallback:

```sh
docker-compose exec -T backend python -m backend.smoke --require-live-ai
```

`--require-facts` is a separate check for the optional reviewed offline registry and is expected to fail when that registry is absent. It is not the live-AI readiness check.

For contributors, automated backend tests live in `backend/tests` and frontend contract/browser checks in `frontend/tests`. Backend tests use HTTP provider mocks, exercise both wire protocols and fallback behavior, and do not spend API credits. Development-only checks can be run inside the container:

```sh
docker-compose exec -T backend python -m pip install -r backend/requirements-dev.txt
docker-compose exec -T backend python -m pytest -c backend/pytest.ini backend/tests -q
```

Those development commands are **not required to run the application**. Frontend contract checks require Node.js only for development: `node --test frontend/tests/contracts.test.mjs`. The optional browser harness uses Playwright and Chrome; see [`frontend/HANDOFF.md`](frontend/HANDOFF.md).

### Key files

- `backend/app/main.py`: routes, startup and public static asset allowlist.
- `backend/app/catalog.py`, `selection.py`, `suggestions.py`: source loading and deterministic business logic.
- `backend/app/explanations.py`: catalogue explanations and real field differences.
- `backend/app/llm.py`: shared OpenAI/Anthropic transport and deadline handling.
- `backend/app/text_input.py`, `ai_answers.py`: prompts, output schemas, validation and AI behavior.
- `backend/app/core/config.py`: provider priority and credential/model settings.
- `frontend/`: accessible form, text input, results, evidence and suggestion controls.
- `docker-compose.yml`, `backend/Dockerfile`, `.env.example`: complete runnable delivery.

## Troubleshooting

- **Docker cannot connect:** start Docker Desktop and enable Linux containers, then rerun the startup command.
- **Port 8000 is occupied:** stop the process using it or change only the host side of `8000:8000` in Compose.
- **Text input is disabled:** check `PARSE_ENABLED`, the parsing/shared credentials and `/api/meta`; recreate the container with the startup command after editing `.env`.
- **AI falls back:** verify the selected provider, exact model ID, quota and key permissions. An OpenAI key takes priority even if invalid. Catalogue search remains usable.
- **A valid-looking date is rejected:** the supplied calendar covers only the documented 2026 window.
- **No or few results:** inspect the exclusion reasons and verified suggestions. The app never relaxes your constraints silently.
- **Source catalogue or accepted facts changed:** rebuild with the startup command; data is a startup snapshot, not a hot-reloaded file.
