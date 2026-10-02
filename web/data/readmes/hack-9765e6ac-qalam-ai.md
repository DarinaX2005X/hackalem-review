# Qalam AI / Alem

A local HackAlem AI MVP that helps businesses improve task briefs and connect with student teams.

Businesses describe a problem, answer clarification questions, review an editable task card, and confirm it before publication. Students choose projects and submit proposals. Businesses select teams manually and confirm completed milestones.

The interface is in Russian; this README is in English. Accounts and student verification are simulated. Data is saved in the current browser. This is a hackathon demonstration, not a shared production service.

## Quick start

Requirements: **Python 3.10+** and a modern browser. Demo mode requires no API key, npm installation, build step, or internet connection.

1. Extract the **entire** ZIP archive.
2. Open the extracted `qalam-ai` folder and run `start.bat` on Windows.
3. The browser opens [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
4. Keep the server window open. Press Ctrl+C in that window to stop it.

The launcher checks the Windows Python launcher, the bundled Codex Python runtime if available, and then `python` on PATH. Codex itself is not required.

```bash
# Windows: manual start
python server.py --open

# macOS / Linux
python3 server.py --open

# If port 8000 is occupied
python server.py --port 8001 --open
```

Use HTTP rather than opening `index.html` as a `file://` page: the app uses ES modules and an API gateway. The server listens on `127.0.0.1` only.

## HackAlem evaluation criteria

These are the case's **judging weights**, separate from the task-readiness score. This table maps features to criteria; it does not guarantee a jury score.

| Criterion | Weight | Implementation and presentation evidence |
|---|---:|---|
| End-to-end workflow | 20 | Draft → clarification questions → editable card → human confirmation → publication → student proposal → manual decision → milestone reward. |
| Task-card quality | 15 | Fourteen editable fields, at least three clarification questions, and explicit business confirmation. |
| Business gamification | 25 | Transparent 0–100 readiness score, weighted breakdown, four levels, improvement after confirmation, and updated catalog position. |
| Catalog and proposals | 15 | Public catalog sorted by readiness, topic/readiness filters, proposals even on draft-level tasks, and manual selection of zero, one, or multiple teams. |
| AI function | 10 | Explicit demo stub plus OpenAI/Ollama gateways; prompt, input/output contract, validation, error handling, and human review. |
| Technical quality | 10 | Reproducible local HTTP launch, modular code, persistence, validation, tests, and documentation. |
| Demonstration | 5 | Five initial business examples, five team profiles, five proposals, and the five-minute script below. |
| **Total** | **100** | The case permits a clearly identified AI stub for the hackathon demonstration. |

Full production authentication is outside the minimum hackathon scope. The additional registration and verification screens demonstrate the intended workflow.

## Features and roles

- Create and save business drafts; request clarification questions.
- Edit structured cards and preview readiness before confirming facts.
- Publish a confirmed card at any score, including zero; low scores do not block proposals.
- Browse and filter the catalog; inspect businesses and public responders.
- Submit an idea, plan, timeline, and HTTP(S) prototype link.
- Submit proposals to different businesses or multiple proposals to one task.
- Manually accept multiple proposals, reject them, or leave them pending.
- Award **+10 team progress points once** when a business confirms a milestone on an accepted proposal. These points do not change task readiness.
- Restore tasks, proposals, decisions, and the latest demo profile after reload.

The role selector is a presentation tool, not real authentication.

| Role | Actions |
|---|---|
| Guest | Browse tasks and public participant information. |
| Student awaiting verification | View the cabinet and submit a demo verification request; cannot submit project proposals. |
| Verified student | Submit proposals and view proposals associated with the current local profile. |
| Business | Manage its own tasks and their proposals; view other businesses. |
| Moderator | Approve or return the current simulated verification request. |

A business attempting to submit a student proposal sees a student sign-in prompt. Select the example businesses `К1`–`К5` in the business cabinet. New registered businesses receive separate local IDs. Students also receive local IDs so another profile's proposals are not shown as their own.

Ownership checks exist in the UI model, but they do not protect against someone modifying browser code. There is no password login, account directory, or shared user database.

## Student-verification demonstration

Registration requests a first name, last name, phone, email, institution, and skills. Use fictional data. No email or SMS is sent; contact fields do not create a server account.

1. Register a fictional student and open the verification form.
2. Select a test document or the university-confirmation option.
3. For a document, select a test PDF/JPG/PNG up to 5 MB. Enter an institution and study period.
4. Submit, switch to the moderator role, and approve or return the request.
5. Switch back to the student view to inspect the result.

Documents are not uploaded, read, or authenticated. University confirmation is also simulated. There is no eGov, Kaspi, or university integration. Public profiles do not expose verification documents or private registration contacts.

## Task-readiness score

Formula version: `confirmed-completeness-v3`. Only confirmed information contributes to the published score.

| Group | Maximum points |
|---|---:|
| Context and business need | 20 |
| Data and materials | 20 |
| Expected result | 15 |
| Success criteria | 15 |
| Constraints | 10 |
| Users | 10 |
| Business communication | 10 |
| **Total** | **100** |

Empty values, recognized placeholders, values without letters, and text shorter than ten characters earn zero. Partial information earns half the criterion's weight, rounded up. Full credit depends on the criterion: data needs both a description and source; success needs a metric and numeric target; communication needs a contact, consultation format, and feedback process.

| Score | Level | Catalog and proposals |
|---|---|---|
| 0–39 | Draft | Available after confirmation and publication |
| 40–69 | Working | Available |
| 70–89 | Ready | Available |
| 90–100 | Priority | Available |

Saving a draft leaves the published card and score unchanged. Confirming edits updates them. Removing confirmed information can decrease the score. Ties in the catalog are resolved by numeric task ID.

Fresh data scores: `К1=30`, `К2=48`, `К3=70`, `К4=100`, `К5=50`. The four prepared answers raise `К1` to **73** after confirmation. Saved user edits can produce different values. The expanded `К4` example contains explicitly synthetic source, target, and contact details.

This is a completeness heuristic, not a truth detector or semantic evaluator. A business must review each field. Exact rules are in `js/domain.mjs`; [RATING.md](RATING.md) provides additional notes in Russian.

## AI modes and contract

### Demo: default, no model required

The deterministic stub selects questions from missing fields and copies only user-provided text. It returns five questions and is explicitly labeled as a demo. It never confirms facts or publishes a task.

### OpenAI: optional

Run `configure-openai.bat` or `python configure_openai.py`. Enter an API key in the local terminal; input is hidden. Configuration is saved to `.env`, which must not be shared. The gateway preserves the original default model, `gpt-4.1-mini`; access depends on the API project.

Select OpenAI in the editor. Requesting analysis sends the description and filled card fields to OpenAI and may consume API credits. The key remains on the server. The implementation uses Responses API structured output through `text.format`, JSON Schema, and `strict: true`. See the [official structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

### Ollama: optional

With Ollama and a suitable model already installed, set the exact model name before starting the server:

```powershell
$env:OLLAMA_MODEL = 'your-installed-model-name'
$env:OLLAMA_URL = 'http://127.0.0.1:11434'
python server.py
```

### Validation and failures

Before a live request, the browser checks `/api/health`. If the selected provider is not configured, it shows setup instructions and **does not send** `/api/ai/analyze`. The user can explicitly select the demo fallback button. There is no silent fallback.

Configuration presence does not prove connectivity or available quota. Real network, authentication, quota, timeout, and provider failures are still reported. Invalid output is rejected without applying it to the task card.

| Contract part | Content |
|---|---|
| Input | `text`, `answers`, and `provider` (`openai` or `ollama`). |
| Output | `card` with all defined fields and `questions` with 3–10 distinct clarification questions. |
| Grounding | Existing answers must stay unchanged; new nonempty values must be exact continuous quotations from the description. |
| Human control | The business reviews, applies, edits, and confirms suggestions. A valid quotation may still be assigned to the wrong field. |
| Source | Full prompt, field keys, and schema: `ai-contract.json`. |

Responses arriving after the form was edited are ignored. Live OpenAI/Ollama calls were not made during this review; gateway tests use mocked responses and errors. Additional setup notes: [OPENAI-SETUP.md](OPENAI-SETUP.md) (Russian).

## Architecture and storage

```text
index.html / style.css / app.js   Browser UI
js/bootstrap.mjs                 Startup and module loading
js/domain.mjs                    Validation and scoring
js/store.mjs                     Storage, confirmations, publications, events
js/ui-model.mjs                  UI adapter, owners, profiles, application actions
js/ai.mjs                        Demo, gateway client, response validation
js/participant-data.mjs          Example drafts, cards, teams, and proposals
js/index.mjs / fixtures.mjs      Module exports
server.py                        Local HTTP server and AI gateways
ai-contract.json                 AI prompt, fields, and JSON schema
ai_settings.py                   Server configuration reader
configure_openai.py              Local API-key setup
tests/                           Logic, integration, and server tests
```

Task data uses browser `localStorage` key `ai-sana.part3.v1`; the demo profile uses `qalam.demo-profile.v1`. Different browsers, hostnames, or ports have separate data. There is no cross-device synchronization or conflict resolution for simultaneous edits in multiple tabs.

Unreadable storage is not replaced with empty data. Existing edits are not overwritten by updated examples. Older proposals without author IDs are not assigned to a newly registered student. Older completed proposals without reward records do not receive points retroactively.

## Tests and verification

Run commands from the project directory. Node.js 20+ is required only for the command-line JavaScript suite.

```bash
# JavaScript logic and integration; writes test-report.json
node tests/run.mjs

# Python server, configuration, and mocked gateway tests
python -m unittest discover -s tests -p "test_*.py" -v

# HTTP smoke check against an already running server
python tests/check_browser.py --url http://127.0.0.1:8000
```

Alternatively, open [tests.html](http://127.0.0.1:8000/tests.html) on the running server to run the JavaScript suite without installing Node. Tests use separate in-memory stores and do not edit saved user tasks.

Latest results: **82/82 JavaScript tests and 28/28 Python tests passed**. The browser suite passed 82/82. Manual checks covered phone validation, missing-provider messages, explicit demo fallback, and the task/proposal/milestone workflow. JSON reports are included; [VERIFICATION.md](VERIFICATION.md) records scope and limitations in Russian.

Live AI, production accounts, actual document verification, cross-device use, load testing, and a full mobile-device matrix were not verified. Passing tests do not guarantee the absence of every possible defect.

## Five-minute presentation

Use a fresh browser origin or separate profile for the expected seed scores. Do not clear a profile containing work you need to keep.

| Time | Action and expected evidence |
|---|---|
| 0:00–0:40 | Show the catalog, filters, and `К1` at 30. Explain which facts already exist in the example. |
| 0:40–2:00 | Choose the business role and `К1`, open its editor, request demo questions, then expand the prepared `К1` answers and apply answers 1–4. Preview score: 73. |
| 2:00–2:40 | Save the draft: the published score stays 30. Confirm the fields: it becomes 73 and the catalog position changes. |
| 2:40–3:40 | Switch to a verified student and submit an idea, plan, timeline, and prototype link. |
| 3:40–4:30 | Return to the owning business and select the proposal manually. Explain that multiple selections or no selection are allowed. |
| 4:30–5:00 | Confirm the milestone, show the one-time +10 team reward, and reload to demonstrate persistence. |

To demonstrate creation from scratch, use Create task, enter a weak description, request questions, fill the card, and confirm it. Publication always requires a human action. Keep optional live-provider setup outside the timed demonstration.

## Troubleshooting and latest fixes

| Symptom | Resolution |
|---|---|
| Invalid phone `pattern` expression in DevTools | Parentheses and the hyphen are now escaped for HTML's Unicode-sets regular expression mode. `+7 (700) 000-00-00` passes; alphabetic values fail. See [HTML pattern documentation](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/pattern). |
| AI returned 503 with no configured provider | The client now checks configuration first and offers an explicit demo button. For real AI, configure the selected provider locally. |
| A configured provider still fails | Read the in-page error; check the service, network, key, or quota as indicated. Configuration alone is not a connectivity check. |
| Old interface still appears | Stop the old server, extract the updated archive, run its `start.bat`, and hard-refresh with Ctrl+F5. Preserve any existing `.env` privately if needed. |
| Port already in use | Stop the previous server or start with `--port 8001`. |
| `file://` or module error | Launch through `start.bat` and use the HTTP URL. |

## Handoff and production work

Share the complete archive, including `js/`, `tests/`, and `ai-contract.json`. Do not share `.env`, real student documents, or private browser data. The original Downloads source folder was not modified during review.

A public deployment still needs server authentication, authorization on every operation, a shared database, real student-status verification, private document storage, contact confirmation, and retention/deletion controls. The role selector and local checks must not be treated as production access control.
