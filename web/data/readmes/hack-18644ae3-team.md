# Career Quest

Career Quest is a gamified employee career development platform built for a
hackathon. It connects courses, workshops, certifications, mentoring, and other
development activities to an employee's career goal and measurable skill gaps.

Employees can see what to learn next and why it matters. HR can review career
progress and find suitable participants for activities. Learning & Development
(L&D) specialists maintain the catalog and record course results.

The application uses **Go, PostgreSQL, and plain HTML/CSS/JavaScript**. Its
recommendation engine and course planner work **without an LLM or API key**.

## Contents

- [What Career Quest does](#what-career-quest-does)
- [Run locally](#run-locally)
- [Demo accounts and registration](#demo-accounts-and-registration)
- [Employee features](#employee-features)
- [HR features](#hr-features)
- [Learning & Development features](#learning--development-features)
- [How recommendations and planning work](#how-recommendations-and-planning-work)
- [Career Navigator](#career-navigator)
- [Data and persistence](#data-and-persistence)
- [Access control](#access-control)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Suggested demo walkthrough](#suggested-demo-walkthrough)
- [Current scope and limitations](#current-scope-and-limitations)

## What Career Quest does

The central workflow is:

```mermaid
flowchart LR
    A[Current role and assessed skills] --> B[Career goal]
    B --> C[Missing skills and critical requirements]
    C --> D[Recommended courses and learning path]
    D --> E[Complete external training]
    E --> F[L&D assessment and skill rewards]
    F --> C
```

For example, a Junior Backend Engineer aiming for Middle might need to improve
API Design from level 2 to 3 and System Design from level 1 to 2. Career Quest
looks for eligible activities that develop those skills, explains the projected
improvement, and can identify a foundation course needed before a later activity.

Career goals are presented as a **main quest**. Development activities become
quests, skill gaps show the remaining work, and career readiness makes progress
visible. Required training is tracked separately from voluntary recommendations.

## Run locally

### Requirements

- Go 1.23 or later.
- Docker with Docker Compose, or an existing PostgreSQL instance. The included
  Compose configuration uses PostgreSQL 16.
- A browser. Node.js is only needed to run the frontend tests.

From the repository root:

```powershell
docker compose up -d db
go run ./cmd/server
```

Open [Career Quest locally](http://localhost:8081).

On startup, the server connects to PostgreSQL, applies embedded SQL migrations,
imports the supplied seed data, and serves both the API and frontend. Seeding
uses stable IDs and conflict handling so repeated starts do not duplicate the
imported records. Database data persists in the Compose volume
`careerquest_postgres`.

The default local connection is:

```text
postgres://careerquest:careerquest@localhost:55432/careerquest?sslmode=disable
```

The container exposes PostgreSQL on host port `55432`; the web server listens on
`8081`. To use another database or HTTP port:

```powershell
$env:DATABASE_URL = "postgres://user:password@localhost:5432/careerquest?sslmode=disable"
go run ./cmd/server -addr :8090
```

### Server configuration

| Flag | Default | Purpose |
|---|---|---|
| `-addr` | `:8081` | HTTP listen address |
| `-database-url` | `DATABASE_URL`, otherwise the local connection above | PostgreSQL connection; the flag overrides the environment variable |
| `-data` | `case_1/career_quest_dataset` | Seed dataset directory |
| `-web` | `web` | Frontend asset directory |
| `-seed` | `true` | Import seed data; use `-seed=false` to skip import on an initialized database |

Migrations still run when seeding is disabled. A fresh installation needs the
initial seed to load role requirements, the skill catalog, and demo accounts.

## Demo accounts and registration

All three seeded demo accounts use the password **`demo`**.

| Workspace | Email | Main purpose |
|---|---|---|
| Employee | `employee@careerquest.demo` | Personal career workspace for employee `E0001` |
| HR | `hr@careerquest.demo` | Employee development, registrations, and candidate targeting |
| L&D Specialist | `ld@careerquest.demo` | Activity catalog, sessions, and course assessments |

Signing in redirects each account to its workspace. These shared credentials
are intended for the local demonstration.

### Registration approval

1. A person submits a registration request from the sign-in page.
2. The account stays `PENDING` and cannot sign in yet.
3. HR opens **Registration requests** and reviews the applicant.
4. HR either creates a new employee record with a role and grade or links an
   existing employee record to the account.
5. Approval changes the account to `ACTIVE`; HR can also reject the request.

New employee IDs are generated in the `E0001` format when an ID is not supplied.
Optional profile details can remain empty. An employee ID supplied by an
applicant is a request for HR to verify; it does not grant access to that record.

## Employee features

| Feature | What the employee can do |
|---|---|
| My Career dashboard | View the current role, target, readiness, next suggested activity, critical gaps, and current activities |
| Career goals | Set, change, or clear a target role and grade; recommendations and skill gaps recalculate for the new target |
| My Quests | Browse recommended, planned/enrolled, in-progress, completed, and mandatory activities |
| Suggested learning path | Follow an ordered sequence of up to three activities, including prerequisite courses |
| Skills view | Compare current and required levels, with separate views for critical blockers and other growth skills |
| Career Path | See the learning sequence, projected skill gains, total study hours, remaining gaps, and projected readiness |
| Course search | Search the activity catalog and open external training links when configured |
| Career Navigator | Read explanations of recommendations, promotion blockers, and suggested next steps |
| My Profile | View personal details, department, team, manager, career goal, last review date, and effective skill levels |

Skills use levels **0–5**, from no knowledge to expert. Effective skill levels
include applicable completed activities after the employee's last review, while
avoiding rewards already applied to the stored skill record.

When no career goal is set, recommendations use requirements for the current
role and grade. Career readiness is shown after the employee selects a goal.

## HR features

| Feature | What HR can do |
|---|---|
| Employee directory | Search by name, email, employee ID, department, team, role, or grade, and apply department/team/role/grade filters |
| Employee creation | Create an employee record with an automatic or supplied ID and optional contact and organization details |
| Registration requests | Approve or reject applications and create or link employee records during approval |
| Employee overview | Switch between employees to inspect readiness, skill gaps, recommendations, and activity history |
| Goal management | Set, change, or clear an employee's career target |
| Activity status | Review completed, planned/in-progress, and mandatory activity records |
| Events and courses | Browse and search the learning catalog |
| Candidate targeting | Open an event's ranked eligible employees and jump to their development profiles |
| Development analytics | View employee counts, career-goal adoption, voluntary activity counts, session counts, and workforce distribution by role |
| Recommendation explanations | Inspect the evidence behind a selected employee's recommendation |

Candidate targeting uses the same eligibility and skill-gap rules as employee
recommendations. It returns employees for whom the activity is currently useful
and eligible; it does not enroll or assign them automatically.

## Learning & Development features

### Course and event management

L&D specialists can create and edit activities with:

- A title, description, duration, and external learning link.
- An activity type: course, workshop, mentoring, certification, meetup,
  compliance, or onboarding.
- A delivery format: online, offline, or self-paced.
- A mandatory flag and target roles and grades.
- Skills developed, the gain for each skill, and the maximum level the activity
  can teach.
- Prerequisite skills and minimum entry levels.
- Upcoming session dates for scheduled activities.

The dashboard summarizes catalog size, optional development activities, session
counts, configured external links, and the mix of delivery formats. The
**Upcoming Sessions** view lists scheduled learning opportunities.

### Participants and assessments

L&D can inspect an activity's enrolled participants and record:

- A `PASSED` or `FAILED` result.
- An optional score from 0 to 100.
- Written feedback.

A passing assessment marks the enrollment completed and applies the configured
skill rewards in a database transaction. Failed assessments award no skills.
Rewards cannot be applied twice to the same enrollment, and a course's level
cap cannot reduce an existing skill level. Updated results are reflected when
career data is loaded again.

### Course analytics

Activity analytics report participation records, unique participants, average
completion percentage, and counts by status. The participant view also shows
assessment results and scores. L&D has access to this course information without
access to the HR directory or private career profiles.

## How recommendations and planning work

The backend uses structured employee skills, role requirements, course effects,
prerequisites, and activity history. Course selection does not require language
generation or model inference.

### 1. Calculate skill gaps and readiness

The engine compares effective skill levels with the selected target profile.
Critical requirements receive twice the weight of other requirements.

For each required skill, fulfillment is the current level divided by its
required level, capped at 1. Career readiness is the weighted average of these
fulfillment values, expressed as a percentage. It measures the recorded skill
requirements for the target; promotion decisions remain outside the app.

### 2. Filter eligible activities

An immediate recommendation must:

- Be voluntary and develop at least one useful skill.
- Match the employee's current role and grade or the career goal's role and grade.
- Have prerequisites the employee already meets.
- Be self-paced or have a session on or after the dataset snapshot date.
- Have no recorded completion, except the explicitly recurring club `EV_036`.
- Have no latest activity status of `planned`, `enrolled`, or `in_progress`.
- Close at least part of a target skill gap within the course's level cap.

Mandatory activities are displayed through their assignment history and are
excluded from voluntary recommendations and learning plans.

### 3. Rank individual recommendations

The match score combines three factors:

```text
score = 70 × weighted gap coverage
      + 20 × useful share of available skill gains
      + 10 × role/goal alignment
      − previous-attempt penalty
```

Coverage is the fraction of the employee's total weighted missing skill levels
that the course can close. The useful share compares those gains with all gains
the course could still provide. Critical skills count twice in both measures.
Alignment is 1 for a career-goal match, or for a current-role match when no goal
is set; it is 0.5 for a current-role-only match when a goal exists.

A latest failed, dropped, declined, or no-show attempt subtracts 10 points.
Scores are bounded to 0–100. Ties favor greater projected readiness improvement,
then fewer study hours, then event ID. The score is a ranking measure, not a
probability of success.

Each recommendation includes the relevant skills, current/projected/required
levels, critical requirements, session availability, and an explanation. When
a goal exists, it also includes projected readiness before and after completion.

### 4. Plan several courses ahead

The planner searches sequences of **up to three activities**, keeping up to
**64 candidate paths at each depth**. After each simulated completion it checks
the next activity's prerequisites against the projected skills.

This allows a foundation course to be useful even when it does not directly
close a career-goal gap. An illustrative path is:

```text
SQL Foundations → Cloud Basics → Advanced Architecture
```

The planner favors the highest projected weighted readiness, then fewer total
study hours, fewer steps, and earlier progress for otherwise equivalent paths.
It avoids repeating an event within the path and checks scheduled session order.
The result is a useful short plan, not a guaranteed globally optimal curriculum
or a booked calendar.

The API returns the plan as `learning_plan` alongside individual recommendations
when a useful path is found. The employee dashboard, My Quests, Career Path, and
Navigator's next-step prompt use it. Planned gains are projections and do not
change the employee's actual skills.

## Career Navigator

The interface calls this feature **AI Career Navigator**. Its current
implementation uses deterministic explanations and keyword-based question
routing, with no external LLM connection.

Supported prompts include:

- **“What should I do next?”** — explains the suggested learning sequence.
- **“What blocks my promotion?”** — summarizes missing target requirements.
- **“Why this quest?”** — explains a selected recommendation's skill impact.
- **“What happens if I change my career goal?”** — describes how the target
  changes the assessment and recommendations.

The answers use computed career data and templates. The Navigator is a focused
career explanation tool; arbitrary conversational understanding is not part of
the current implementation.

## Data and persistence

PostgreSQL is the application's persistent store for employees, skills, role
requirements, goals, courses, sessions, enrollments, activity history, accounts,
and assessments. The JSON/CSV dataset is used for initial seeding and automated
tests.

The supplied synthetic dataset contains:

| Data | Size |
|---|---|
| Employee profiles | 200 |
| Skills | 60 |
| Job roles | 8 |
| Grades | Junior, Middle, Senior, Lead |
| Role/grade requirement profiles | 32 |
| Activities | 40 |
| Participation history records | 2,743 |

The dataset snapshot is **2026-10-01**, which the recommendation engine treats
as its availability reference date. History covers **2024-10-01 to 2026-09-30**.
These are demo snapshot dates, rather than a continuously advancing calendar.

See the [dataset documentation](case_1/career_quest_dataset/README.md) for field
definitions and the [product context](docs/PROJECT_CONTEXT.md) for the original
design brief. The runtime implementation uses PostgreSQL; the in-memory dataset
adapter remains available to tests and the seed loader.

## Access control

| Capability | Employee | HR | L&D |
|---|---|---|---|
| Browse activity catalog | Yes | Yes | Yes |
| View career profile, gaps, recommendations, and history | Own record | All employees | No |
| Change career goals | Own goal | Any employee goal | No |
| Use Navigator for career data | Own record | Any employee | No |
| Search/create employee records | No | Yes | No |
| Approve/reject registrations | No | Yes | No |
| View ranked event candidates | No | Yes | No |
| Create/edit courses and sessions | No | No | Yes |
| View aggregate course analytics | No | Yes | Yes |
| View participants and submit assessments | No | No | Yes |

Passwords are stored as bcrypt hashes. Authentication uses session cookies with
`HttpOnly` and `SameSite=Lax`; the cookie's `Secure` flag is set when the request
uses TLS. Logout ends the session. Authorization is enforced on the backend,
including checks that employee accounts access only their linked record.

## API reference

The frontend and API are served by the same Go application. Requests and
responses use JSON, and authenticated calls use the login session cookie.
“Owner/HR” below means the employee who owns the record or an HR account.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `GET` | `/health` | Public | Service health response |
| `POST` | `/auth/register` | Public | Submit a pending employee account request |
| `POST` | `/auth/login` | Public | Sign in with an active account |
| `GET` | `/auth/me` | Signed in | Get current user and workspace redirect |
| `POST` | `/auth/logout` | Signed in | End the session |
| `GET` | `/catalog` | Signed in | Get skills, roles, grades, and reference data |
| `GET` | `/registrations` | HR | List requests; optional `status`, default `PENDING` |
| `POST` | `/registrations/{id}/approve` | HR | Create and link a new employee or link an existing one |
| `POST` | `/registrations/{id}/reject` | HR | Reject a request |
| `GET` | `/employees` | HR | Search with `q`, `department`, `team`, `role`, and `grade` |
| `POST` | `/employees` | HR | Create an employee record |
| `GET` | `/employees/{id}` | Owner/HR | Get employee details and effective skills |
| `GET` | `/employees/{id}/career-path` | Owner/HR | Get career target, readiness, and gap summary |
| `GET` | `/employees/{id}/skill-gaps` | Owner/HR | Get the full skill assessment |
| `GET` | `/employees/{id}/recommendations` | Owner/HR | Get ranked activities and optional learning plan |
| `GET` | `/employees/{id}/mandatory-quests` | Owner/HR | Get recorded mandatory assignments, with overdue items first |
| `GET` | `/employees/{id}/activities` | Owner/HR | Get activity history and status categories |
| `PUT` | `/employees/{id}/career-goal` | Owner/HR | Set a target or clear it with `{"clear": true}` |
| `GET` | `/events` | Signed in | Search with `q`, `type`, `role`, and `grade` |
| `GET` | `/events/{id}` | Signed in | Get activity details |
| `POST` | `/events` | L&D | Create an activity |
| `PUT` | `/events/{id}` | L&D | Update activity metadata and sessions |
| `GET` | `/events/{id}/candidates` | HR | Get ranked eligible employees |
| `GET` | `/events/{id}/analytics` | HR/L&D | Get participation and completion aggregates |
| `GET` | `/events/{id}/participants` | L&D | Get enrolled participants and assessment details |
| `POST` | `/enrollments/{id}/assessment` | L&D | Record pass/fail, score, feedback, and applicable skill rewards |
| `POST` | `/navigator/chat` | Owner/HR | Explain career data for the requested employee |

Example career-goal body:

```json
{
  "target_role": "Backend Engineer",
  "target_grade": "Middle"
}
```

Example Navigator body:

```json
{
  "employee_id": "E0001",
  "question": "What should I do next?"
}
```

Add `event_id` to ask about a specific currently recommended activity.

## Project structure

```text
cmd/server/                    Server startup and configuration
internal/auth/                 Accounts, sessions, and authorization
internal/career/               Effective skills, gaps, and readiness
internal/recommendation/       Activity ranking and course sequence planning
internal/navigator/            Deterministic career explanations
internal/events/               Activity history and analytics
internal/assessment/           Assessment validation and service
internal/domain/               Shared data models
internal/repository/           Persistence interfaces
internal/postgres/             PostgreSQL implementation and seed import
internal/postgres/migrations/  Embedded SQL migrations
internal/dataset/              Dataset loading, validation, and test adapter
internal/httpapi/              Routes, JSON handlers, and frontend serving
web/                          Employee, HR, and L&D interfaces
web/tests/                    Frontend regression and startup checks
case_1/career_quest_dataset/   Synthetic seed data
docs/PROJECT_CONTEXT.md        Original product brief
```

The backend uses Go's HTTP server and PostgreSQL through `pgx`. The frontend
uses browser JavaScript and static assets, so running the application does not
require an npm install or a frontend build step.

## Testing

Run Go tests and compile all packages:

```powershell
go test ./...
go build ./...
```

Run the frontend tests with Node.js:

```powershell
node --test web/tests/*.test.cjs
```

To include PostgreSQL integration checks against the local Compose database:

```powershell
$env:TEST_DATABASE_URL = "postgres://careerquest:careerquest@localhost:55432/careerquest?sslmode=disable"
go test ./internal/postgres -count=1
```

These checks create and remove isolated test schemas. They cover registration
approval and skill reward persistence, including protection against duplicate
rewards and reduced skill levels. They are skipped when `TEST_DATABASE_URL` is
not set.

With a seeded server running, include frontend startup checks for all three
workspaces:

```powershell
$env:CAREER_QUEST_TEST_URL = "http://localhost:8081"
node --test web/tests/*.test.cjs
```

The live startup checks sign in with the demo accounts and exercise frontend
startup against the API. They are skipped without `CAREER_QUEST_TEST_URL`.
Other tests cover career assessments, recommendation eligibility and ranking,
prerequisite paths, Navigator plan explanations, API access rules, and UI state.

## Suggested demo walkthrough

1. Sign in as the employee and review **My Career**, including the target,
   readiness, critical gaps, and suggested next step.
2. Open **Career Path** to explain the course order and projected skill gains.
3. Change the career goal and show the recalculated gaps and recommendations.
4. Ask Navigator **“What should I do next?”** and inspect a quest explanation.
5. Sign in as HR, search for an employee, and open an event's candidate list.
6. Submit a new registration and show HR approving it with a newly created or
   existing employee record.
7. Sign in as L&D, edit a course's skill effects and prerequisites, then inspect
   its sessions, analytics, and participant assessments. Submitting a passing
   assessment changes the participant's stored skills and activity status.

## Current scope and limitations

- Training is delivered externally through configured learning links. The app
  manages career planning and results; it does not host course lessons.
- Enrollments and mandatory assignments are tracked from existing records.
  There is currently no self-enrollment or HR assignment creation endpoint/UI.
  Marking a course mandatory does not create assignments for employees.
- The planner searches up to three steps ahead and estimates skill progress.
  Employees must confirm session timing and successfully complete the training
  before those gains become actual results.
- Recommendation quality depends on accurate employee skill assessments, role
  requirements, course effects, and prerequisites. Missing employee skill
  entries are treated as level 0.
- Navigator supports its defined career prompts through templates and keyword
  routing. A general conversational assistant is not connected.
- Availability is evaluated using the dataset snapshot date. The current demo
  does not advance that reference date automatically with the wall clock.
