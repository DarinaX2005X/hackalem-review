Voice Router — Dataset

Case 2 dataset: a voice AI agent for the contact center of Saqta Insurance. The agent picks the right scenario with an LLM layer (no intent classifier) and talks like a good human operator, in Kazakh and Russian.

All data is synthetic. Saqta Insurance, its products, prices, rules, clients, addresses and clinics are fictional and simplified. They do not reflect real legislation.

Snapshot date: 2026-10-01. Treat it as "today".

Company

Saqta Insurance — general (non-life) insurer in Kazakhstan. Founded 2009, HQ in Almaty, 8 branches, ~600,000 clients. Serves individuals and companies in Kazakh and Russian.

Line	Products
Auto	OGPO (mandatory motor third-party liability), CASCO (voluntary car insurance)
Health	DMS (voluntary health insurance): mostly corporate, also individual
Travel	Medical insurance for trips abroad, 24/7 medical assistance
Property	Apartments and houses
Accident	Personal accident insurance
Not offered: life insurance, pension annuities, loans. Such requests are SYS_OUT_OF_SCOPE.

Contact center: sales Mon–Sat 08:00–20:00, claims and medical assistance 24/7.

What makes insurance calls hard

The same words mean different scenarios: "авария" can be accident right now (SC11), victim claim (SC12) or CASCO claim (SC13).
Status vs. dispute: "выплату одобрили, но мало" is a dispute (SC19), not a status request (SC17).
Urgent cases (accident on the road, illness abroad, fraud) must be recognized and handled first.
Clients switch topics and languages mid-sentence.
Many actions are irreversible (issue, change, cancel a policy, file a claim) and need explicit confirmation.
Files

File	Content
scenarios.json	40 scenarios + 3 system intents
slots.json	Slot catalog: types, formats, questions in ru/kk
actions.json	Mock backend actions and handoff queues
knowledge_base.json	Company facts: offices, products, prices, rules, documents, clinics
mock_backend.json	11 clients, 11 policies, 4 claims, 2 payments
dialogs_sample.json	10 annotated example dialogs
dev_utterances.json	104 labeled utterances for measuring accuracy
evaluate.py	Reference scorer for your router on the dev set
Scenarios

ID	Scenario	Domain	Category	Priority
SC01	OGPO price quote	auto	sales	normal
SC02	OGPO purchase	auto	sales	normal
SC03	CASCO consultation and quote	auto	sales	normal
SC04	Add driver to motor policy	auto	servicing	normal
SC05	Change vehicle or plate in policy	auto	servicing	normal
SC06	Travel insurance purchase	travel	sales	normal
SC07	Home insurance consultation	property	sales	normal
SC08	Accident insurance consultation	accident	sales	normal
SC09	Individual health insurance consultation	health	sales	normal
SC10	Corporate insurance request	corporate	sales	normal
SC11	Road accident just happened	auto	claims	urgent
SC12	Claim as victim under culprit's OGPO	auto	claims	high
SC13	CASCO damage claim	auto	claims	high
SC14	Property damage claim	property	claims	high
SC15	Medical event abroad	travel	claims	urgent
SC16	Accident injury claim	accident	claims	high
SC17	Claim status	general	claims	normal
SC18	Documents for a claim	general	claims	normal
SC19	Disagreement with claim decision	general	claims	high
SC20	Book vehicle inspection	auto	claims	normal
SC21	Doctor appointment under DMS	health	servicing	normal
SC22	DMS coverage check	health	servicing	normal
SC23	Partner clinics list	health	info	normal
SC24	DMS e-card issue	health	servicing	normal
SC25	Check policy validity	general	servicing	normal
SC26	Resend policy documents	general	servicing	normal
SC27	Policy renewal	general	sales	normal
SC28	Policy termination and refund	general	servicing	normal
SC29	Update contact details	general	servicing	normal
SC30	Charged but policy not issued	general	servicing	high
SC31	Payment methods and installments	general	info	normal
SC32	Bonus-malus class and price change	auto	info	normal
SC33	Office addresses and hours	general	info	normal
SC34	Mobile app and account help	general	info	normal
SC35	Service complaint	general	feedback	high
SC36	Callback request	general	contact	normal
SC37	Request a human operator	general	contact	normal
SC38	Suspicious call or fraud report	general	security	urgent
SC39	Certificate or document copy request	general	servicing	normal
SC40	Policy terms explanation	general	info	normal
System intents: SYS_OUT_OF_SCOPE (not about Saqta services), SYS_UNCLEAR (ask one clarifying question), SYS_GOODBYE.

scenarios.json

Field	Notes
scenario_id, slug, name	SC01…SC40
domain	auto, health, travel, property, accident, corporate, general
category	sales, claims, servicing, info, feedback, contact, security
description	What the client wants. Main input for the LLM router
not_this_if	Boundary rules: {condition, use_instead}. Use them in the router prompt
priority	normal, high, urgent. Urgent goes first in multi-intent turns
fast_path_eligible	Simple informational scenario, can be served by a cheap fast path
requires_identification	Client must be identified (phone, IIN, policy or claim number) before actions
slots.required, slots.optional	Names from slots.json. Slots can be filled from the client profile or earlier turns
actions	Names from actions.json
requires_confirmation	true if the scenario runs an irreversible action. Read back and get an explicit "yes" first
handoff	{when, queue} or null
examples	4 ru + 3 kk example utterances
responses	opening and closing lines in ru and kk. Style reference, not a script. {placeholders} come from slots or action outputs
slots.json

name, type (string, enum, integer, date, boolean, list, text), description, pattern or values, prompt.ru, prompt.kk.

Normalize spoken values: "восемь семьсот один…" → +7701…, "ертең" → date, "двадцатого года" → 2020. Dates are resolved against the snapshot date.

actions.json

name, description, inputs, outputs, errors, irreversible. Implement them as mocks over mock_backend.json and knowledge_base.json. queues lists handoff targets.

Errors use one format: {"error": {"code": "not_found", "message": "..."}}. Codes are listed in error_codes, expected agent behavior in error_handling. Example: unknown phone → find_client returns not_found → the agent re-asks once, then offers another identifier or an operator.

Irreversible actions: create_policy, renew_policy, update_policy, cancel_policy, create_claim, create_dispute, book_inspection, book_appointment, update_contact.

knowledge_base.json

Company facts, offices, inspection points, products with pricing formulas, clinics, claim rules and document lists, payments, cancellation, bonus-malus, app help, fraud policy, complaints. The agent must answer from this file, not invent facts.

mock_backend.json

clients, policies, claims, payments. IDs: C001, SQ-OGPO-104501, CL-500287, P-3001. Unknown IIN → bonus-malus class 3. Prices in the backend follow the formulas in the knowledge base. New IDs created by your mocks must not collide with existing ones.

dialogs_sample.json

Each dialog: dialog_id, title, tags, client_id, turns. Client turns: text, lang, scenarios (expected, in order), slots (extracted in this turn). Bot turns: text, lang, actions (mode: preview = shown for confirmation, execute = done).

Covers: scenario switch, topic switch and return, mixed speech, language switch, clarification, handoff, irreversible action with confirmation.

dev_utterances.json

id, text, lang (ru, kk, mixed), expected (ordered list of scenario IDs), type (single, multi_intent, out_of_scope, unclear). 84 single, 13 multi-intent, 4 out of scope, 3 unclear; 7 mixed-language. The jury uses a different, hidden set of the same kind.

python evaluate.py predictions.json dev_utterances.json
predictions.json: {"U001": ["SC01"], "U085": ["SC27", "SC04"], ...}. Reports primary accuracy, full match and multi-intent recall, split by language and type.

Reference architecture

 mic ──► STT (streaming) ──► Layer 1: Triage ──► Layer 2: LLM Router ──► Decision policy ──► Scenario executor ──► Response ──► TTS ──► speaker
                                   │                    │                       │                     │                 │
                                   └────────────── Dialog state (language, client, active scenario, stack, slots) ──────┘
                                                                   │
                                                             Trace panel
Layer 1 — Triage (fast, per utterance)

Language: ru, kk or mixed; reply in the client's dominant language, switch when the client switches.
Normalization: numbers, phones, plates, dates.
Urgency signals: accident now, abroad and ill, fraud.
Split multi-intent utterances into parts.
Layer 2 — LLM Router

Input: utterance (or part), dialog state, scenario catalog (description, not_this_if, a few examples).
Output (contract):
{
  "scenarios": [
    {"scenario_id": "SC30", "confidence": 0.86, "reason": "money charged, policy not issued"},
    {"scenario_id": "SC29", "confidence": 0.78, "reason": "moved, wants to change address"}
  ],
  "alternatives": [{"scenario_id": "SC26", "confidence": 0.31}],
  "language": "ru",
  "slots": {"payment_date": "2026-09-30"},
  "is_continuation": false
}
Decision policy

confidence ≥ 0.75 → run the scenario.
0.45–0.75 → SYS_UNCLEAR: one short question with the top-2 options.
< 0.45 twice in a row, or client asks → handoff with context.
Several scenarios → urgent first, then in spoken order; confirm you will handle the rest.
Continuation of the active scenario → fill slots, do not re-route.
Scenario executor — state machine per scenario: identify client if needed → ask missing slots one by one → call actions → read back and confirm irreversible actions → close. On topic switch, push the current scenario to a stack and offer to return after the new one is done.

Response — LLM generation constrained by scenario, slots, action results and the knowledge base. Never state a fact that is not in the data.

Fast path (optional) — fast_path_eligible scenarios can be served without the full LLM call. Measure the latency gain.

Conversation rules

1–2 short sentences per turn. One question at a time.
Acknowledge first, then act: "Сочувствую, давайте оформим."
Empathy in claims and complaints, calm speed in urgent cases.
Numbers for speech: "тридцать восемь тысяч тенге", not "38000 KZT".
Mask personal data when reading back: r***@mail.example.
Read back and get an explicit "yes" before irreversible actions.
If asked "are you a robot?", answer honestly.
Hand off to a human with a short context summary, so the client does not repeat themselves.
Trace (show after each client turn)

{
  "turn": 3,
  "transcript": "...",
  "language": "mixed",
  "scenarios": [{"scenario_id": "SC21", "confidence": 0.9}],
  "alternatives": [{"scenario_id": "SC23", "confidence": 0.4}],
  "reason": "...",
  "slots": {"doctor_specialty": "therapist"},
  "actions": ["find_client", "book_appointment:preview"],
  "latency_ms": {"stt": 0, "triage": 0, "router": 0, "response": 0, "tts_first_audio": 0, "total": 0}
}
Evaluation

The jury reads 10 hidden utterances live: simple, topic switch, boundary, mixed language, Kazakh, and requests that must not be routed to a business scenario.
Each utterance, up to 3 points: correct primary scenario; all scenarios for multi-intent (otherwise correct reply language); answer quality against the data.
Latency is optional and gives bonus points only; a slow solution loses nothing. Measured as end of client speech → first audio of the reply (latency_ms.total), median over the set: ≤ 1.5 s → +2, ≤ 3 s → +1, > 3 s → 0. The jury spot-checks with a stopwatch.
Personas in the hidden set use clients from mock_backend.json. Your agent must identify them by phone number and use their data.
Allowed tools

Any external or cloud LLM, STT and TTS APIs. Intent classifiers (encoder-based models trained to map utterances to intents) are not allowed for scenario selection.
