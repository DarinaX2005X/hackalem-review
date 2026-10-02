# Task Catalog MVP

A 5-hour hackathon MVP that helps businesses turn rough needs into structured, readiness-rated tasks, publish them to an open catalog, receive student-team proposals, and manually choose who to work with.

## Architecture and tech stack

- Python and Flask for routes and server-side rendering
- HTML/CSS for the small user interface
- SQLite (`task_catalog.db`) for published tasks and proposals
- OpenAI API for clarification questions only

The flow is deliberately simple: rough description → AI clarification → editable
task card → deterministic readiness rating → publish → catalog → proposal →
manual Accept/Reject decision.

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set the API key only in the shell session; do not put a real key in source code
or commit it to Git:

```powershell
$env:OPENAI_API_KEY = "your_api_key"
python app.py
```

Open `http://127.0.0.1:5000`. If the key is absent, invalid, or the OpenAI
request returns invalid JSON, the app shows fallback clarification questions so
the demo can continue. The key is never displayed by the application.

## Storage and demo data

SQLite storage is created automatically in `task_catalog.db`. The database has
one table for published tasks and one for proposals. It persists while the file
remains in the project folder.

To add synthetic demo data to an empty catalog, run:

```powershell
python app.py --seed-demo-data
```

This creates exactly five published tasks, five distinct team identities, and
five proposals. It does nothing when any task already exists, preventing
duplicate seed records. Normal application startup never seeds data.

## Readiness scoring

Scoring is deterministic Python logic; AI does not calculate it.

| Category | Points |
| --- | ---: |
| Context + Business need | 20 |
| Available data/materials | 20 |
| Expected result | 15 |
| Success criteria | 15 |
| Constraints | 10 |
| Target users | 10 |
| Business connection (contact + interaction format) | 10 |

Paired categories are split evenly: Context and Business need are worth 10 each;
Business contact and Interaction format are worth 5 each. A non-empty,
user-provided field receives its points. The total is 100.

- 0–39: Draft
- 40–69: Working
- 70–89: Ready
- 90–100: Priority

Low-rated tasks are still publishable and visible in the catalog. The catalog
sorts published tasks from highest readiness score to lowest and supports simple
topic and readiness-level filters.

## Complete user flow

1. A business user enters a rough task description.
2. OpenAI asks at least three clarification questions, or fallback questions
   are used when the AI is unavailable.
3. The business user reviews and edits the task card.
4. The user confirms the card to see the transparent readiness breakdown.
5. The task can be published at any readiness level.
6. A student opens the public task, submits a proposal, and may do so alongside
   any number of other teams.
7. The business opens the proposal page and manually selects **Accept** or
   **Reject** for each proposal.

AI never ranks, selects, or assigns teams. The final decision is always manual.

## Manual test scenarios

1. **Improve a weak task:** Create a task with only a business need, calculate
   its low score, edit the missing scoring fields, calculate again, and confirm
   the score and readiness level increase.
2. **Publish and decide:** Publish a task, locate it in the catalog, submit a
   team proposal, open the business proposal page, then manually Accept or
   Reject it.
3. **AI fallback:** Start the app without `OPENAI_API_KEY`, submit a rough
   description, and confirm that fallback clarification questions are shown.

## MVP limitations

There is no authentication, chat, notification system, uploads, calendar,
automatic team selection, or production deployment infrastructure. The catalog
and business views are public demo routes by design.
