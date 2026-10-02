# Beeline Tariff Marketing Campaigns Agent

**It 1+1** · HackAlem AI · Track 04, Telecommunications.

## 1. Problem and user

A marketing analyst must choose audiences, target tariffs, and communication channels within a limited budget. A tariff change can reduce revenue, contacts consume resources, and small pilots provide noisy evidence. This agent learns from pilots and returns a campaign plan.

All case data and financial outcomes are synthetic. They do not describe Beeline's real business.

## 2. Implemented solution

- Historical transitions rank hypotheses and provide an initial estimate; their frequencies are not treated as measured audience conversion probabilities.
- Up to 12 initial push pilots cover promising current-tariff × ARPU cells. An OpenAI model then reviews the live evidence and proposes up to 2 extra hypothesis pilots; remaining pilots test alternatives or confirm uncertain and unexpectedly strong results.
- Pilot observations update estimates and reduce reliance on conflicting history. Widespread negative observations can stop further exploration.
- Allocation accounts for channel costs, conversion saturation, audience ordering, budget, contact limits, and campaign slots. Selected final campaigns do not repeat contacts with each other.
- The fallback retains a tested audience and reduces exposure where possible. With no usable pilot evidence at all, it still returns one minimal-exposure campaign toward the highest-price tariff, keeping the required 1–10 campaign contract; fallback profitability is not guaranteed.
- `Agent.decision_trace` stores observations, estimates, LLM advice, reasons, and warnings in memory. This six-file package does not include a report exporter or viewer.

## 3. Main workflow and case limits

Profile and history → candidate hypotheses → first-pass pilots → history calibration → LLM-suggested hypothesis pilots → adaptive follow-up pilots → estimated net value → constrained allocation → campaign list.

The organizer's `make_submission.py` runs this workflow at seed 42 and writes `submission.csv`.

| Constraint | Limit |
| --- | ---: |
| Final campaigns | 1–10 |
| Subscribers per final campaign | 5,000 |
| Total contacts, including pilots | 15,000 |
| Total communication cost, including pilots | 100,000 conventional units |
| Pilots | Up to 20, with 10–200 contacts each |
| Runtime | Up to 10 minutes in the participant guide |

Push pilots have no monetary contact cost, but consume contacts and can reduce revenue. Both pilots and final campaigns contribute to the official score. Each subscriber's effect is counted once by the evaluator, while all contact costs are charged.

## 4. Technology and AI use

The package was verified with **pandas 3.0.6 and NumPy 2.5.3**; an external review reproduced identical seed-42 results on pandas 2.3.3. `requirements.txt` therefore allows `pandas>=2.2` and `numpy>=1.26`, so the judges' Python version can install available wheels.

An OpenAI model participates in the decision loop (`llm_advisor.py`). After the deterministic first-pass pilots it receives the candidate cells with their live evidence (posterior mean, standard deviation, sample size) and the resource state, and proposes up to 2 additional hypothesis pilots from the adaptive reserve. Its suggestions then compete on measured pilot evidence like any other cell; it never edits the final campaign list directly. The key comes only from `os.environ["OPENAI_API_KEY"]`; every call is wrapped in try/except with a 20-second timeout, and any error, missing key, or invalid response falls back to the fully deterministic policy, so a model outage cannot invalidate the plan. A committed `llm_cache.json`, keyed by the exact request payload and independent of the model name, makes the seed-42 replay byte-reproducible with or without a key; on the judging environment's different effects the cache misses and the model is consulted live. A paired 7-seed live comparison measured a +39k mean mock effect from this step, with individual seeds and model draws varying in both directions.

This package demonstrates the event-wide OpenAI API requirement inside the judged agent itself.

## 5. Architecture and repository contents

This branch contains the **minimal submission package**:

| File | Purpose |
| --- | --- |
| `agent.py` | Complete policy, including `Agent.act(env)` |
| `llm_advisor.py` | LLM hypothesis-pilot advisor: prompt, validation, cache, deterministic fallback |
| `llm_cache.json` | Committed LLM responses pinning the seed-42 replay |
| `submission.csv` | Four final campaigns generated at seed 42 |
| `requirements.txt` | Python dependencies |
| `README.md` | Setup, verification, results, and limitations |

Inside `agent.py`, `build_prior` prepares history; `_candidates` proposes targets; `_explore` runs pilots and consults the LLM advisor; `_estimate` aggregates evidence; `_offers` and `_allocate` compare feasible plans; `_fallback` handles cases without a suitable regular plan.

The agent uses public environment fields and `run_pilot`. It does not import the evaluator or inspect hidden effects. The core policy was adopted from Adil Rakhaliyev's implementation; subsequent measured changes (pilot-budget shift 16→12, price-aware emergency fallback, LLM hypothesis pilots) are recorded in the branch history.

## 6. Installation and execution

1. Obtain and extract the official Beeline participant package.
2. Copy this branch's six files into the package root. Keep the organizer's environment, scorer, evaluator, generator, dictionaries, and data unchanged.
3. Optionally set `OPENAI_API_KEY` in the environment to enable the live LLM step; without it the agent runs fully deterministically. No key is needed to reproduce `submission.csv` - the committed cache answers the seed-42 request.
4. Run the commands below **from that assembled package directory**.

The assembled directory must contain `environment.py`, `scoring_core.py`, `mock_environment.py`, `local_eval.py`, `make_submission.py`, `customer_profile.csv`, and the organizer's `data/` directory. The latter includes `change_tariff.csv`, `dict_tariff.csv`, `traffic.csv`, and `arpu_monthly.csv`. These organizer assets are supplied separately; they are not part of this six-file branch.

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -X utf8 local_eval.py
.venv\Scripts\python.exe -X utf8 make_submission.py
```

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -X utf8 local_eval.py
.venv/bin/python -X utf8 make_submission.py
```

UTF-8 mode supports the organizer tools' Russian output on Windows.

## 7. Validation and reproduction

Use the organizer's unchanged tools in the assembled directory. In the commands below, `python` means the virtual environment's executable shown above:

```sh
python -X utf8 local_eval.py
python -X utf8 local_eval.py --runs 10
python -X utf8 make_submission.py
```

Check that evaluation completes, no campaigns are discarded, pilots are used, and resource limits hold. The reported combined campaign count includes pilots: 24 campaigns at seed 42 means 20 pilots plus 4 final campaigns, within the final-plan limit.

Recorded seed-42 evaluation:

| Metric | Result |
| --- | ---: |
| Status | PASS |
| Net gain | 4,869,704 |
| Communication cost | 93,440 / 100,000 |
| Contacts, including pilots | 9,594 / 15,000 |
| Pilots | 20 |
| Final campaigns | 4 |

In the recorded run the LLM's suggested pilots confirmed cells the adaptive loop also prioritizes, so the final plan matches the deterministic one - live model advice varies and can also add campaigns. Replay reproducibility (cache answers seed 42 without network) is verified separately from live integration (fresh seeds make real API calls, e.g. seed 999: net 5,144,353 PASS in `llm_live` mode). Generator runs live, cache-only, and keyless reproduced the committed CSV byte for byte. Its SHA-256 is `95bbd022ca3c51f634540c8a2cd23e28d17600ffa04cc9782026a0a329ea96a7`. Line endings can differ across platforms. Hidden-environment campaigns may differ from seed 42 because pilot outcomes and live model advice differ.

## 8. Data and integrations

The profile supplies current tariffs, ARPU and usage segments, and `predicted_arpu`. Historical `data/change_tariff.csv` supplies initial hypotheses. `env.tariffs` and `env.channels` define valid actions, and current effects are learned through pilot responses.

The agent does not read `traffic.csv` or `arpu_monthly.csv` directly because derived features are already in the profile. Customer data remains in the participant package and is not published here. The OpenAI API (via `llm_advisor.py`) is the only external integration; there is no web service or graphical viewer in this package.

## 9. Reproducible mock results

The organizer command `python -X utf8 local_eval.py --runs 10` evaluates seeds **0-9**. Without an API key the current package produced the following net gains, rounded to whole conventional units:

| Metric | Submitted agent (deterministic path) |
| --- | ---: |
| Mean net gain | 4,997,973 |
| Median net gain | 5,025,029 |
| Minimum | 4,646,599 |
| Maximum | 5,245,303 |
| Positive runs | 10/10 |

With a key set, the LLM step alters exploration per run; the paired 7-seed comparison above measured a +39k mean effect with per-seed deltas from -164k to +353k. Different seeds change pilot randomness; they do not change the mock business-effect model. These results do not establish profit under hidden judging effects.

## 10. Limitations

- Random seeds of one mock model test pilot noise, not transfer to a different effect model. Profit and leaderboard position are not guaranteed.
- Candidate search keeps at most two target tariffs per audience cell, ranked using history when available. Adaptive follow-up and LLM suggestions choose among the precomputed candidate list; cells outside it are never piloted. Allocation is greedy; global optimality is not established.
- The historical prior closely matches how the supplied mock computes effects. Strong mock results do not establish robustness when history is misleading or current effects change direction.
- Follow-up choice and early stopping are adaptive. Pilot size is normally 200 and decreases with eligible audience size or remaining contacts, rather than being optimized from observed uncertainty.
- Uncertainty estimates and risk margins are heuristic, not calibrated confidence guarantees. Historical transitions alone do not identify causal effects.
- Pilot IDs are hidden. Final campaigns can overlap pilots, and the in-memory projected net does not subtract that overlap or represent the full realized official score.
- The emergency fallback (used only when every pilot observation fails) targets the highest-price tariff with the smallest audience; it bounds exposure but can still lose money.
- LLM responses vary between live calls; the committed cache pins the recorded seed-42 run, and off-cache runs, including judging, can take different exploration paths.
- The trace is not a complete reporting API: it has no attached official evaluation, and fallback campaigns are not fully represented in its campaign list.

## 11. Deployment and submission

This is an offline submission; no deployed URL is required. Submit `agent.py`, `llm_advisor.py`, `llm_cache.json`, the generated `submission.csv`, and `requirements.txt` with this README, following the case's platform instructions. Use the separately supplied participant package for local evaluation.

Pushing a Git commit or generating a CSV does not itself complete the platform's **Submit Solution** step.
