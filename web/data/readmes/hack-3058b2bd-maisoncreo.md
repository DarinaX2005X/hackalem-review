# Smart Contractor Selection

HackAlem case #79-lite: a small, reproducible contractor-shortlisting demo built
for the official anonymized catalog.

## Problem

The customer already has a city contractor catalog. The useful outcome is not a
longer list, but a shortlist of contractors who satisfy the request and are not
busy on the event date.

## Solution

The application follows one explicit pipeline:

`request → deterministic eligibility → deterministic ranking → top 3 → grounded explanation → validated fallback`

Python owns every hard fact: category, city, event format, budget, language,
duration, availability, selection, and ordering. The optional language model can
only select evidence for explaining contractors that Python has already chosen.
It cannot add, remove, or reorder recommendations.

## Features

- Filters by city, event date, event format, contractor category, and budget.
- Supports optional language and duration constraints.
- Excludes every contractor whose `busy_dates` contains the requested date.
- Returns at most three recommendations in deterministic order.
- Distinguishes `MATCHED`, `CATEGORY_NOT_FOUND`, and
  `NO_ELIGIBLE_CANDIDATES` outcomes.
- Produces contractor-specific explanations grounded in verified fields and an
  exact description excerpt.
- Works offline with deterministic fallback explanations.
- Shows unobtrusive synthetic, city-imputed, and price-imputed provenance flags.
- Includes DENSE, RARE, and NO RESULT demo presets.

## Architecture

- `app.py` loads the CSV, builds the Streamlit form and presets, calls the core,
  enriches selected cards, and renders Russian user-facing results.
- `recommendation_core.py` validates the request, applies all hard constraints,
  ranks eligible records by starting price and then stable contractor ID, and
  returns at most three cards.
- `explanation_layer.py` optionally asks OpenAI to select exact description and
  structured evidence. Python validates that evidence and constructs the final
  Russian explanation. Any rejection or provider failure uses the deterministic
  fallback.
- `data/contractors.csv` is the local source of contractor profiles and
  availability data.

In short: **Python decides WHO. AI helps explain WHY.** Strict evidence
validation and fallback prevent ungrounded model-written claims from reaching
the UI.

## Dataset

The repository contains the official anonymized dataset with 66 contractor
profiles. Its availability horizon is 2026-09-23 through 2026-12-31; dates
outside that interval are treated as unknown availability, never as free.

`price_from_kzt` is a starting price, not a final quote. The dataset also
contains `synthetic`, `city_imputed`, and `price_imputed` flags, which the UI
surfaces when applicable.

## Requirements

- Python 3.10 or newer (verified with Python 3.12.1)
- Streamlit `>=1.40,<2`, declared in `requirements.txt`

The deterministic core and OpenAI HTTP integration otherwise use the Python
standard library. No database, vector database, or OpenAI SDK is required.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python -m streamlit run app.py
```

## Optional OpenAI explanations

The application works without an API key. In that mode, every selected card
uses the deterministic grounded fallback.

To enable optional OpenAI evidence selection in the current shell:

```bash
export OPENAI_API_KEY='your-api-key'
```

The default model can be overridden if needed:

```bash
export OPENAI_EXPLANATION_MODEL='your-model-name'
```

`.env` files are not loaded automatically. Never commit API keys or other
secrets. If an API request fails or its evidence is rejected, the application
automatically falls back; selection and ordering remain unchanged.

## Demo scenarios

### DENSE

`Алматы / 2026-09-30 / корпоратив / Ведущий / 1,000,000 KZT / 6h / русский`

Demonstrates a category with enough eligible candidates for deterministic
ranking and the three-card limit.

### RARE

`Алматы / 2026-09-24 / свадьба / Ведущий церемонии / 300,000 KZT / 3h / русский`

Demonstrates a rare category where only two contractors satisfy every hard
constraint, so the application returns both and explains the shortage.

### NO RESULT

`Астана / 2026-09-28 / свадьба / Фотограф / 1,000,000 KZT / 8h / русский`

Demonstrates `NO_ELIGIBLE_CANDIDATES`: the category exists, but no contractor
meets all requested constraints for that date.

All presets use the same application pipeline as manually entered requests;
their results are not hard-coded.

## Tests

```bash
python -m unittest discover -s tests -v
```

The current suite contains 28 passing behavioral tests covering hard filters,
availability, deterministic ordering and limits, status distinctions, evidence
validation, fallback behavior, and provider failure handling. Tests do not make
live API requests.

## Determinism and safety

- All hard constraints and availability checks run in Python.
- Ranking is stable: lower starting price first, then contractor ID as the final
  tie-breaker.
- The explanation layer cannot change selected IDs or their ordering.
- Model-selected structured fields are checked against the query and profile;
  description evidence must be an exact source substring.
- Final displayed wording is constructed in Python, not copied from arbitrary
  model-authored prose.
- Deterministic fallback keeps the application usable offline.
- After the first provider or validation failure in one enrichment run, a
  circuit breaker skips further provider calls and uses fallback for the
  remaining cards.

## Known limitations

- Ranking intentionally uses only starting price and stable ID; semantic ranking
  is not implemented.
- Availability is known only within the dataset horizon.
- Data is loaded from the bundled CSV; there is no live marketplace integration
  or booking workflow.
- Strict evidence validation can reject otherwise useful model-selected
  evidence, in which case the deterministic fallback is shown.

## Reproducibility

From a clean checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

The application reads only repository data by default and does not require an
OpenAI key to run or pass the test suite.

## Future development

Possible extensions are semantic ranking, richer marketplace integration,
booking as a separate future workflow, and support for larger catalogs.
