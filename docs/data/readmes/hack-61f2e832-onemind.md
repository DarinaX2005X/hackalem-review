# Smart Contractor Selection

Smart Contractor Selection helps an event customer choose the strongest candidates from an existing city-specific contractor catalog. A single orchestrator runs deterministic eligibility and ranking first, then uses AI only for evidence-grounded explanations. The result is a short, reproducible shortlist that is easier to trust and explain than an opaque sort or free-form LLM answer.

## Problem

The customer has already selected an event type and received a contractor catalog for a city. The task is not to expand that catalog, but to identify the most suitable available candidates within it.

The product's value comes from explainable selection: every returned contractor must pass explicit constraints, preserve stable ranking, and include a concrete explanation tied to catalog evidence.

## Solution

```text
User Request
-> RecommendationAgent
-> deterministic filtering and ranking tools
-> contractor evidence
-> AI explanation or deterministic fallback
-> validation
-> final recommendations
```

The deterministic Python layer is the source of truth for:

- city and category matching
- availability from `busy_dates`
- event format and budget
- optional language and duration constraints
- stable scoring and ordering
- `MATCHED`, `CATEGORY_NOT_FOUND`, and `NO_MATCH`

The AI layer produces concise, contractor-specific explanations using only evidence supplied from the official dataset. It never decides eligibility or ranking.

The validation layer requires the deterministic contractor IDs and ordering to remain unchanged, checks explanation count, association, and structure, and requires concrete literal evidence markers. Prompt instructions require grounded, contractor-specific explanations, but claim-level verification of every free-form statement is not implemented. Invalid or unavailable AI output is replaced by deterministic evidence-based explanations.

## Agentic AI

This is agentic because `RecommendationAgent` orchestrates specialized tools, inspects their structured results, requests explanations only for eligible candidates, and validates the final output before returning it. It is not a single prompt that asks an LLM to select contractors.

The actual tools are:

- `search_contractors`: runs deterministic filtering, result-state selection, diagnostics, scoring, and ranking.
- `get_contractor_details`: retrieves evidence for a selected contractor from the official catalog.
- `validate_recommendations`: reruns deterministic selection and requires the submitted IDs and ordering to match exactly.

The Streamlit transparency panel shows only observable actions and factual stage counts. It does not expose private chain-of-thought.

## Result States

- `MATCHED`: one or more contractors passed every applicable hard constraint. The response contains at most three ranked cards.
- `CATEGORY_NOT_FOUND`: the selected city contains no contractor with the requested category.
- `NO_MATCH`: the category exists in the city, but all candidates failed later constraints such as availability, format, budget, language, or duration.

For empty results, rejection counts come from the deterministic pipeline rather than the LLM.

## Dataset

The application uses the official 66-profile dataset at `data/hackathon_dataset_anonymized.csv`.

Important fields used by the application are:

- `id`, `anon_name`, `description`
- `categories`, `city`
- `price_from_kzt`
- `event_formats`, `languages`, `max_hours`
- `busy_dates`
- `synthetic`, `city_imputed`, `price_imputed`

Pipe-delimited `categories`, `event_formats`, `languages`, and `busy_dates` are normalized into multi-value collections. `busy_dates` is the source of availability: a contractor busy on the requested date cannot be returned. The preparation flags are preserved, and no rating field or external data source is invented.

## Deterministic Ranking

Ranking is applied only after all hard constraints pass. The implemented score uses exact fraction arithmetic and has three components:

```text
budget_headroom = 70 * (budget_kzt - price_from_kzt) / budget_kzt
                  when budget_kzt is nonzero, otherwise 0
language_match  = 15 when a language was requested, otherwise 0
duration_fit    = 15 * duration_hours / max_hours
                  when duration is requested and max_hours is known,
                  otherwise 0

total_score = budget_headroom + language_match + duration_fit
```

Eligible contractors are sorted by descending total score. Ties are resolved by lower `price_from_kzt`, then case-insensitive `anon_name`, then `id`. Unknown `max_hours` does not cause rejection, but it receives no duration-fit points. Identical inputs and an unchanged dataset therefore produce identical ordering.

## Installation

Python 3.10 or newer is required. Python 3.11.9 has been verified for this project.

Run all setup commands from the repository root:

```powershell
cd <repository-directory>
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## OpenAI Configuration

To enable AI-generated explanations in PowerShell:

```powershell
$env:OPENAI_API_KEY="your-api-key"
```

Alternatively, create a `.env` file in the repository root:

```text
OPENAI_API_KEY=your-api-key
```

The application loads `.env` automatically. This file is excluded by `.gitignore` and must never be committed. Never place a real API key in this README.

`OPENAI_MODEL` may optionally override the default explanation model. If `OPENAI_API_KEY` is absent, the complete application remains operational using deterministic fallback explanations. The UI labels the active mode as either a validated OpenAI explanation or a deterministic fallback explanation.

## Running The App

```powershell
streamlit run app.py
```

## Running Tests

```powershell
python -B -m unittest discover -s tests -v
```

Current verified result: **19 tests passed**.

## Demo Scenarios

### 1. Dense Category

```text
city: Алматы
event_date: 2026-11-10
event_format: корпоратив
contractor_category: Ведущий
budget_kzt: 1000000
duration_hours: 6
language: русский
```

Expected result:

```text
MATCHED
HK-88430
HK-29829
HK-44733
```

Four contractors qualify, so deterministic ranking selects the top three.

### 2. Rare Category

```text
city: Алматы
event_date: 2026-09-24
event_format: корпоратив
contractor_category: Фото и видеобудки
budget_kzt: 500000
duration_hours: 6
language: русский
```

Expected result:

```text
MATCHED
HK-90009
HK-35846
```

Only these two contractors pass all constraints, so the application explicitly returns fewer than three.

### 3. No Result

```text
city: Астана
event_date: 2026-09-24
event_format: корпоратив
contractor_category: Банкетный зал
budget_kzt: 1000000
duration_hours: 6
language: русский
```

Expected result: `NO_MATCH`.

One contractor exists for this city and category, but that contractor fails the budget constraint. The deterministic diagnostic is `budget=1`.

### 4. Date Sensitivity

Keep every dense-query parameter identical except `event_date`:

```text
2026-09-23 -> HK-29829, HK-44923, HK-27222
2026-09-24 -> HK-35215, HK-44733
```

Only the date changes. The output changes because contractor availability is checked against `busy_dates`.

### 5. Determinism

The dense-category query was executed five times. Every run returned this exact order:

```text
HK-88430
HK-29829
HK-44733
```

## Project Structure

```text
app.py                              Streamlit demo interface
SPEC.md                             Product and acceptance contract
requirements.txt                    Runtime dependencies
data/
  hackathon_dataset_anonymized.csv  Official 66-profile dataset
docs/
  hackathon_dataset_preview.html    Official dataset preview
src/
  __init__.py                       Public package interface
  models.py                         Typed request and result contracts
  catalog.py                        CSV loading and normalization
  recommender.py                    Hard filters and deterministic ranking
  tools.py                          Agent-facing deterministic tools
  agent.py                          Explanation orchestration and validation
tests/
  test_recommender.py               Deterministic-core tests
  test_agent.py                     Agent and fallback tests
```

## Testing / Acceptance

The 19-test suite covers:

- catalog normalization and multi-category matching
- busy-date, city, category, budget, language, and duration behavior
- blank `max_hours` handling
- all three result states and the three-card limit
- deterministic ordering and date-sensitive availability
- prevention of contractor injection and reordering by the agent
- contractor-to-explanation association and rejection of generic explanations
- deterministic `NO_MATCH` diagnostics
- operation without `OPENAI_API_KEY`

The acceptance audit also independently checked all returned demo contractors against every hard constraint and found zero violations.

## Design Decisions

1. Eligibility is deterministic because availability and customer constraints must never depend on probabilistic model output.
2. The LLM is limited to evidence-grounded explanation generation for contractors already selected by Python.
3. Deterministic fallback explanations keep the demo operational without an API key or during API failure.
4. Model fine-tuning is unnecessary for a structured catalog of 66 records.
5. The Streamlit UI is intentionally minimal so recommendation correctness, explanations, and visible diagnostics remain the focus.

## Limitations

- The hackathon dataset contains only 66 profiles.
- Availability is limited to the provided `busy_dates`; there is no live contractor calendar.
- There is no booking, messaging, payment, or contractor onboarding workflow.
- No model fine-tuning is used.
- AI explanations depend on API availability, with deterministic fallback when unavailable.

## Future Development

- Connect a production contractor catalog and live availability service.
- Add semantic embeddings for richer description matching.
- Model additional customer preferences while preserving deterministic hard constraints.
- Integrate booking and contractor communication workflows.
