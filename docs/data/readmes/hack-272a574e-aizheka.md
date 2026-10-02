# Beeline Campaign Agent

Python hackathon agent for AIZheka. It builds a deterministic campaign shortlist,
learns from public pilot observations, and selects campaigns under budget and
contact limits. The runnable release is **offline**: no API key, GCP instance,
web server, or Vercel hosting deployment is needed.

## Release status

Updated 2026-09-23. Milestones 1-5 are implemented. The default `Agent.act(env)`
uses the tested Bayesian strategy and deterministic pilot preflight checks.

`portfolio.py` is an experimental overlap-aware beam-search selector, **not the
default**, because its measured median regressed. `ai_provider.py`,
`semantic_features.py`, and `verified_cascade.py` are experimental modules with
offline contract tests. They are **not wired into Agent.act**. Setting AI
environment variables does not enable AI in the submitted agent. Milestones
6-11 are not all complete; publishing this snapshot does not imply otherwise.

## Deploy and run

Use Python 3.11. Run all commands from the repository root: the supplied runners
resolve data paths relative to the working directory. The repository includes
the case inputs and generated shortlist. Keep the original participant package
unchanged.

### Windows PowerShell

For a new clone (skip cloning if this directory already exists):

```powershell
Set-Location D:\hackalem
git clone https://github.com/BAITC-Hacks/hack-272a574e-aizheka.git
Set-Location hack-272a574e-aizheka
git switch main
$env:PIP_CACHE_DIR = 'D:\hackalem\.pip-cache'
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe local_eval.py
.\.venv\Scripts\python.exe local_eval.py --runs 10
.\.venv\Scripts\python.exe make_submission.py
```

For an existing clean clone, use `git switch main` and `git pull --ff-only`, then
the install/test/run commands above. Do not discard local changes to update.
If the console cannot encode evaluator output, set
`$env:PYTHONIOENCODING = 'utf-8'`. Calling the environment's Python directly
avoids PowerShell activation-policy issues and keeps dependencies on D:.

### Linux or WSL

```bash
git clone https://github.com/BAITC-Hacks/hack-272a574e-aizheka.git
cd hack-272a574e-aizheka
git switch main
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python local_eval.py --runs 10
.venv/bin/python make_submission.py
```

Use a separate clone/environment for Linux; a Windows `.venv` cannot be reused
in WSL. If Git on `/mnt/d` produces chmod/config.lock errors, use Windows Git
for that clone, or a Linux-filesystem clone. GPU/cloud compute is unnecessary
for the current workload: 20 tests ran in about 2 seconds and ten evaluations
in about 4 seconds on the development machine (excluding installation).

## Submission deployment

The entry point is `agent.py` / `Agent.act(env)`, not an HTTP service. For a
complete local evaluation deployment, clone the repository and follow setup.
For a judging upload, the default agent's explicit file dependency list is:

```text
agent.py
adaptive_pilots.py
action_gate.py
analysis/candidate_shortlist.csv
requirements.txt
submission.csv
```

Preserve the `analysis/` directory. The organizer supplies the environment;
local reproduction additionally needs the supplied harness files, dictionaries,
customer profile, and `data/` from this repository. Confirm with organizers that
supporting modules and the shortlist CSV are accepted before submitting. An
isolated submission archive has not yet been tested. Do not zip the whole working
directory: exclude `.env.local`, keys, `.venv`, `.cache`, and local artifacts.

`make_submission.py` regenerates seed-42 campaigns. Two runs on this release
produced identical bytes and SHA-256:

```text
2c38b5a2e2b2ba26cffa8744de434f34555f346e1bd4c5b2164705ca74b2f53d
```

The resulting row is `adaptive_1_tariff_8_tariff_10`, current tariff `tariff_8`,
ARPU segment `MID`, target `tariff_10`, channel `sms`. Hidden-environment
decisions may differ; the row is generated, not hardcoded.

## Architecture and completed results

Public inputs -> 32-candidate shortlist -> Bayesian adaptive pilots ->
resource-aware final selection -> submission. No hidden effects or sampled
customer IDs are read by the agent.

- Imported all 16 participant-package files and recorded original hashes in
  `SOURCE_MANIFEST.sha256`.
- Data analysis identified disjoint historical/target populations and evidence
  for 451 of 1,260 transition groups, with median historical support 11.
- Enumerated 5,040 combinations and retained 32 diversified evidence-backed
  candidates. Historical effects are weak priors, not conversion forecasts.
- Implemented normal-normal posterior updates and value-of-information pilot
  selection. Exploration is capped at eight attempts, 1,600 contacts, and 20,000
  campaign-budget units, with deployment reserves.
- Added a deterministic gate immediately before pilots: validates sample size,
  tariffs, channel costs, audience freshness, remaining budget, and contacts.
- Current verification: **20/20 offline tests passed**. Coverage includes
  Bayesian updates, resource bounds, rejection fallback, shortlist consistency,
  AI answer contracts, cache keys, outage handling, evidence claims, and cost
  accounting. These tests do not establish live model quality.

### Before and after: same seeds 0-9

Values below are simulated net ARPU gain, not API spend. Rounded to whole units.
Starter measurements are from the earlier baseline report; both current-policy
and experimental-portfolio results were rerun on 2026-09-23.

| Metric | Starter | Retained Bayesian default | Experimental portfolio |
| --- | ---: | ---: | ---: |
| Median | -357,948 | 488,485 | 47,307 |
| Minimum | -1,019,431 | 28,584 | 43,975 |
| Maximum | -76,493 | 489,719 | 488,889 |
| Positive runs | 0/10 | 10/10 | 10/10 |
| Seed 42 net | -1,035,279 | 489,248 | 47,668 |

| Seed | Retained default | Experimental portfolio |
| --- | ---: | ---: |
| 0 | 488,503 | 45,217 |
| 1 | 489,719 | 47,362 |
| 2 | 196,745 | 196,745 |
| 3 | 489,119 | 46,399 |
| 4 | 488,889 | 488,889 |
| 5 | 28,707 | 47,410 |
| 6 | 488,467 | 43,975 |
| 7 | 489,527 | 46,935 |
| 8 | 28,584 | 47,252 |
| 9 | 487,626 | 487,626 |

The experimental selector raised the minimum on these seeds but substantially
reduced the median, frequently choosing a tiny fallback. It remains available
for research, not promoted to the default. Its final-to-final overlap is exact
for public ID ordering; pilot overlap is only an expected-coverage approximation
because pilot IDs are private.

Current default seed 42: **PASS**, gross gain 513,448, communication cost 24,200,
net gain 489,248, eight pilots plus one final campaign, 2,914 total contacts and
2,644 unique customers. After pilots, 82,680 budget and 13,806 contacts remained.

Previously reported Bayesian seeds 10-29: median 194,221, minimum 319, maximum
637,120, positive 20/20. These were not rerun for this publication and are now
known evaluation seeds, not fresh holdout evidence. A rejected confirmation-pilot
variant had median -25,172 and only 3/10 positive runs; it was removed.

**Mock scores validate mechanics, not future judging performance.** Hidden
effects differ. No measured Jev or cascade score improvement exists yet.

## Vercel / Jev status and credentials

Vercel is used as a potential model gateway, not as project hosting. Optional
SDK dependencies can be installed with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ai.txt
```

Put a Vercel **AI Gateway** key in ignored `.env.local` as
`AI_GATEWAY_API_KEY=...`, or supply it through the process environment. Never
commit a real value. Do not overwrite an existing `.env.local` when updating.
Verify exclusion with `git check-ignore .env.local`. Rotate any key previously
shared in chat. Ignore rules are not encryption.

The experimental Gateway uses `https://ai-gateway.vercel.sh/typesafe` and model
`typesafe-ai/jev`, with the TypeSafe SDK appending `/v1/systemone`. Four independent
questions cover offer fit, consumption fit, negative-reaction risk, and evident
needs mismatch. Score criteria are ordered arrays; responses retain probability
distributions. See the [TypeSafe Score contract](https://docs.typesafe.ai/primitives/score)
and [Vercel TypeSafe integration](https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe).

Live checks on 2026-09-23 found and corrected an invalid Score request shape.
The latest corrected request still returned **HTTP 403: AI Gateway requires a
valid credit card on file**. Check billing on the same team that owns the key.
No successful inference or provider-reported billed usage was returned; lack of
usage data is not proof of zero charges. No OpenRouter fallback or direct OpenAI
balance was used. The user's total authorized initial test allowance is $1;
this is not an automatically enabled runtime budget.

The helper reserves estimated in-flight costs, limits calls/time, disables SDK
retries, and reconciles reported cost when available. These local estimates do
not guarantee a provider-side dollar ceiling or persist across processes.
Keep cumulative spending records and use provider-side limits before more tests.

The draft -> deterministic evidence check -> Jev verification -> one escalation
-> verification helper follows the
[verified-cascade recipe](https://openrouter.ai/docs/cookbook/evaluate-and-optimize/jev-verified-cascade).
It has not been live-validated; draft/escalation models are not selected, and
thresholds are not calibrated. Its proposals cannot execute agent actions.

## Remaining work

- Revisit portfolio risk/overlap modeling and compare on new evaluation seeds.
- Complete a successful Vercel contract test and representative labeled fixtures.
- Wire optional semantic features into the agent only after paired ablations.
- Pin and test draft/escalation models; assess false acceptance and abstention
  against human-reviewed labels, not Jev alone.
- Finish broader robustness tests, isolated package reproduction, and organizer
  confirmation of network, supporting-module, and data-file submission rules.

Detailed records: [game plan](docs/GAME_PLAN.md),
[baseline](docs/BASELINE_REPORT.md), [data economics](docs/DATA_ECONOMICS.md),
[shortlist](docs/SHORTLIST_REPORT.md), and
[Bayesian pilots](docs/BAYESIAN_PILOTS_REPORT.md). Earlier reports are historical
snapshots; this README describes the current release.
