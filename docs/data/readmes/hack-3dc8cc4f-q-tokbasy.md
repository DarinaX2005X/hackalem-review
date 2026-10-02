# Career Quest

Career Quest is an HR career development dashboard. It uses the
provided synthetic employee, skill, event, and activity datasets to present a
searchable team directory, employee development profiles, career readiness,
and deterministic activity recommendations.

## Run the backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn main:app --app-dir backend --reload
```

The API is available at `http://localhost:8000`; interactive documentation is
at `http://localhost:8000/docs`.

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. To use a different API address, set
`VITE_API_URL` in a local `.env` file.

## API endpoints

- `GET /health`
- `GET /api/employees`
- `GET /api/employees/{employee_id}`
- `GET /api/employees/{employee_id}/career-gap`
- `GET /api/employees/{employee_id}/recommendations`
- `GET /api/employees/{employee_id}/ai-recommendations`
- `POST /api/employees/{employee_id}/complete-quest` with `{"event_id": "EV_005"}`
- `GET /api/events`
- `GET /api/skills`
- `GET /api/hr/dashboard`

## HR Dashboard

Switch to **HR** in the application header to see common target-grade
competency gaps, employees without a recommended next step, and aggregate
participation and completion statistics. The dashboard uses the same
deterministic career-gap logic and in-memory runtime state as the employee
experience, so completed quests are reflected immediately.

## Recommendation Engine

The recommendation pipeline uses only the supplied Career Quest dataset:

**Employee Profile → Target Grade → Skill Gap Analysis → Candidate Events →
Participation History → Multi-factor Scoring → Top 3 Recommendations**

The employee's explicit `career_goal` selects the target role and grade when
present. Otherwise, the engine derives the next grade from the ordered role
profiles in `skills.json` (a Lead remains at Lead). For every required target
skill, it calculates `gap = max(target_level - current_level, 0)`. Career
readiness is the percentage of total required proficiency already met:

```text
100 × sum(min(current level, required level)) / sum(required levels)
```

Mandatory events, events outside the target role and current/target-grade audiences, events whose
prerequisites are unmet, previously completed non-recurring events, and events
that cannot actually improve a required skill are excluded. Actual improvement
always observes the catalog cap:

```text
possible new level = min(current level + event gain, event max_level)
actual gain = possible new level - current level
```

Each eligible, useful event receives up to 100 points:

| Factor | Points | Calculation |
|---|---:|---|
| Target-grade gap severity | 35 | Weighted mean of `gap / 5` across affected skills |
| Grade relevance | 25 | `85% × weighted target-level strength + 15% × useful-gap breadth` |
| Realizable skill gain | 20 | Weighted mean of `actual_gain / catalog event gain` |
| Participation history | 10 | `5 × (history signal + 1)`, mapping `-1…1` to `0…10` |
| Explicit career-goal relevance | 5 | Awarded when the event audience matches the explicit target role |
| Audience and prerequisite eligibility | 5 | Awarded after strict eligibility filtering |

Critical target skills have weight `1.5`; other required skills have weight
`1.0`. The history signal is a recency-weighted average for activities of the
same real event type. Status weights are: completed `+1.0`, in progress
`+0.25`, overdue `-0.5`, dropped `-0.6`, declined `-0.65`, and no-show `-0.75`.
Recent records receive more weight, while a person with no similar history gets
a neutral five history points. Scores are capped at 100, rounded to one decimal,
and ties are broken by event ID.

This is more reliable than recommending the employee's numerically weakest
skill because a low skill might not be required by the target role, an event
might be capped below the employee's current level, prerequisites or audience
may make it unsuitable, or participation patterns may favor another equally
useful format. Every output includes its score components, exact skill impacts,
event gain/cap, history counts and signal, and factual reasons. There is no
randomness, LLM, or external service, so identical data always yields identical
recommendations.

## AI Career Coach

The optional coach adds a concise, personalized explanation to each of the top
three verified recommendations:

**Employee Profile → Skill Gap Analysis → Multi-factor Recommendation Engine →
Verified Top Recommendations → OpenAI Explanation Layer → Employee-facing
Career Coach**

The LLM is **not** the recommendation source of truth. The deterministic engine
continues to calculate eligibility, rankings, score components, history signals,
and exact skill impacts. OpenAI receives a small allow-listed fact object and
only makes those verified results easier to understand. Its response is nested
under `explanation`, so it cannot replace an event ID, score, or skill gain.

Copy the example environment file or set these variables in the backend
process (never commit a real key):

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

The configured model defaults to the cost-efficient `gpt-4.1-mini`. The integration uses the
official Python SDK's Responses API with strict structured JSON output. For each
recommendation, it sends only role, current/target grade, career goal, preferred
language, event ID/title, deterministic score, exact skill impacts, history
signal, and deterministic reasons. It does not send names, the full employee
record, other employees, or the complete datasets.

Each explanation has this dashboard-oriented shape:

```json
{
  "source": "openai",
  "headline": "Build your System Design skills for Senior",
  "summary": "This quest addresses a verified target-grade skill gap.",
  "why_this_quest": ["It can move System Design from level 2 to level 3."],
  "expected_impact": "System Design: 2 → 3, target 4",
  "career_connection": "This is a concrete step toward the Senior requirement.",
  "history_insight": "Your participation history was included in the score."
}
```

If the key or SDK is missing, or the API fails, times out, exhausts quota, or
returns invalid output, the same endpoint returns a deterministic explanation
with `"source": "deterministic"`. The employee dashboard therefore does not
depend on OpenAI availability. English (`en`), Russian (`ru`), and Kazakh (`kk`)
preferences are passed as output-language instructions; all underlying facts
remain unchanged.

## Quest Completion and Progress Updates

Iteration 4 adds the complete feedback loop to every recommended quest:

**Recommended Quest → Employee completes activity → Apply event gain/max_level
→ Update runtime skills → Recalculate career readiness → Recalculate
recommendations → Refresh AI explanations**

`POST /api/employees/{employee_id}/complete-quest` accepts an `event_id`, checks
that the employee and event exist, and verifies that the deterministic engine
currently considers the event eligible and useful. For each skill listed in
the real `events.json` effect, the backend applies
`min(current level + gain, event max_level, 5)` and reports the actual gain,
including zero. It records the completion in recent activity and rejects a
second completion of a non-recurring event. The profile, gap, deterministic
recommendation, and AI-coach endpoints all read the updated state immediately.

The original hackathon JSON and CSV dataset files are **never modified**.
Runtime employee skills and activity history are held only in memory for this
demo. Restarting the backend resets all quest completions and progress changes
to the original dataset snapshot.

## Validation

Run the dataset-backed unit assertions without additional packages:

```bash
PYTHONPATH=backend python -m unittest discover -s backend -p 'test_*.py' -v
```
