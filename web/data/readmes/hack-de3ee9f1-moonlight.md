# Beeline Tariff Marketing Campaigns — Adaptive Agent

## Problem

Choose tariff campaigns for **23,441 subscribers** with unknown target-audience
effects. An offer can produce downsell, and communication costs money. Historical
switchers come from another population: the agent must learn through paid pilot
experiments before allocating the campaign budget. All supplied data are synthetic.

## Solution

`Agent.act(env)` returns a list of campaign dictionaries. This adaptive decision
system combines weak historical priors, diverse exploratory pilots, selective
confirmation, and uncertainty-aware economic allocation. It uses only Python,
pandas, numpy, the supplied historical CSV, and the documented environment API.
There are no external services, API keys, or accesses to hidden environment state.

## Why this is Agentic AI

```text
Historical data
      ↓
Prior hypotheses
      ↓
Candidate generation
      ↓
Small exploratory pilots
      ↓
Observe real target-audience response
      ↓
Update beliefs + uncertainty
      ↓
Selective confirmation pilots
      ↓
Economic channel selection
      ↓
Budget-aware campaign selection
      ↓
Final campaign plan
```

The agent does not simply predict from historical data. It interacts with the
environment, performs experiments, observes results, updates its beliefs and
changes subsequent decisions. It is a statistical decision agent; no LLM is needed.

## Algorithm

1. **Historical prior.** Group `data/change_tariff.csv` by current tariff, target
   tariff and ARPU segment; calculate relative-lift mean, count and standard
   deviation. Drop nonfinite values, negative after-ARPU and before-ARPU below 100.
   Clip relative lift to [-1, 3]. Historical segments use LOW <1000, MID 1000–5000,
   HIGH >5000; current audience labels come directly from the public profile.
2. **Candidate generation.** Pair observed current-tariff/ARPU cells with valid,
   different target tariffs. Prefer historically positive hypotheses; use neutral
   hypotheses if none exist. Historical switch frequency is not treated as the
   hidden campaign conversion probability.
3. **Diversity-aware exploration.** Rank prior expected total economic value with
   penalties for already-tested cells, target tariffs and ARPU segments.
4. **Exploratory pilots.** Run up to 12 successful 50-customer experiments. Smaller
   audiences/resources can reduce the size, but never below 10. Skips and failures
   do not count as successful experiments.
5. **Prior-informed shrinkage.** Accumulate prior and pilot estimates by precision.
   More pilot customers increase evidence weight. This is not full Bayesian inference.
6. **Uncertainty estimation.** Use the public measurement-noise formula below and
   historical uncertainty. Final ranking subtracts one standard error from the
   estimated lift. This is a risk penalty, not a calibrated confidence guarantee.
7. **Confirmation pilots.** Consider up to six follow-up hypotheses whose intervals
   can change selection versus zero, same-cell rivals or the ten-campaign boundary.
   Use 100 customers, or 200 when base-effect SE exceeds 0.15. Stop when estimated
   information value cannot justify contact opportunity cost or resources run out.
8. **Channel economics.** Compare communication costs and conversion multipliers,
   including the probability cap for call; see Channel Selection.
9. **Final selection.** Compare greedy plans at budget shadow prices derived from
   current option value/cost ratios. Maximize total risk-adjusted net value over
   reachable customers, using remaining resources after pilots. This is a heuristic,
   not an exact global optimizer. Final cells are disjoint.
10. **Conservative fallback.** If no risk-positive plan remains, return one offer on
    the cheapest valid channel with positive updated expected net value. It must
    have promising history or a valid pilot observation. Thus positive pilot
    evidence can rescue missing/negative history. This minimizes downside under
    uncertainty; push does not guarantee profit. Do not pad the plan to ten.

For historical mean `h`, standard deviation `s` and count `n`:

```text
historical_weight = min(20, 2 * log(1 + n))
prior_mean = 0.5 * h
prior_variance = s² / max(n, 1) + 0.20² + h² / 12
prior_precision = min(historical_weight / 0.804², 1 / prior_variance)
```

The weak uniform [0,1] conversion assumption has mean 0.5 and variance 1/12;
historical switcher data cannot identify campaign conversion. The count cap and
0.20 population-shift allowance prevent history from overwhelming pilots. Singleton
standard deviations default to 1; missing history has zero precision. These
modeling assumptions were not fitted to mock seeds.

For a pilot with channel multiplier `m <= 1` and actual sample size `n`:

```text
pilot_base_estimate = observed_lift_ratio / m
pilot_precision = n * m² / 0.804²
updated_mean = (prior_precision * prior_mean
                + sum(pilot_precision * pilot_base_estimate))
               / (prior_precision + sum(pilot_precision))
updated_SE = sqrt(1 / (prior_precision + sum(pilot_precision)))
```

### Audit of PILOT_STD = 0.804

The supplied **`environment.py:52`**, not a fitted mock model, explicitly defines:

```python
PER_CUSTOMER_STD = 0.804
```

The public pilot mechanics in **`environment.py:172–173`** use:

```python
noise = _rng.normal(0.0, PER_CUSTOMER_STD / np.sqrt(n_actual))
observed_ratio = float(_true_lift_ratio(picked, target_tariff, channel).mean() + noise)
```

The file's comments document per-person noise and standard error scaling. Its
module documentation states that judging uses the same environment class with a
different effect model. Relying on 0.804 is therefore justified under the supplied
public contract; it is not a hidden effect or a constant tuned from mock scores.
If organizers change the noise mechanics, uncertainty must be reassessed.
The agent does not import private helpers or inspect the effect model.

`run_pilot()` exposes noisy relative/total lift, actual sample count, cost and
remaining resources, but no customer IDs or confidence interval. Total lift is
derived from the same noisy ratio and is not independent evidence.

## Exploration vs Exploitation

Exploration is a real campaign cost, not a free rehearsal. Before each call, check
`pilots_left > 0`, `remaining_contacts >= pilot_size` and
`remaining_budget >= pilot_size * cost_per_contact`. Current call sites request
only 50, 100 or 200 people; samples below 10 are skipped.

Exploration consumes at most **15% of starting money** and **2,000 contacts**, and
reserves at least one contact for final selection. Stage 2 stops when further
information is unlikely to change a decision. Final plans start from the public
remaining budget/contacts after pilots, so those costs are always included.

## Channel Selection

The organizer's public scoring rule (`scoring_core.py:167–172`) is:

```text
lift_ratio = tariff_change * min(conversion_probability * conversion_multiplier, 1)
net = credited incremental ARPU - contacts * cost_per_contact
```

Both channel fields come from `env.channels`. **HIGH ARPU does not automatically
mean call.** Expensive channels must justify cost and reduced affordable reach.
The planner also considers cheap channels over a larger audience.

Pilots use channels with multiplier <=1, measuring the shared base effect
`tariff_change * conversion_probability` without saturation. For call (1.2), the
scale relative to that base lies in [1, 1.2]. Use its midpoint for expectation and
add its half-width to the risk penalty. Do not assume an unconditional 1.2x gain.

Exact tariff/ARPU filters, ascending `ID_NUMBER`, the first 5,000 people, and
remaining money/contact caps match public scoring order. Prefix sums use actual
audience ARPU. No unsupported final audience-size field is emitted.

Final campaigns use different current-tariff/ARPU cells, preventing final/final
overlap. Pilot IDs are unavailable. Risk scores subtract an upper bound on possible
pilot-overlap ARPU; expected value uses a conservative random-sampling overlap
estimate. Negative effects are never discounted away. All repeated contacts still
cost money and reach; the organizer credits each customer once, by their best offer.

## Robustness

Current validation after final hardening:

| Check | Result |
| --- | ---: |
| Positive runs, seeds 0–9 | **10/10** |
| Median net result | **+1,153,902** |
| Minimum | **+714,869** |
| Maximum | **+1,509,310** |
| Single-run net, seed 42 | **+910,618** |
| Single-run gross | 972,300 |
| Total communication cost | 61,682 / 100,000 |
| Total contacts, including pilots | 4,547 / 15,000 |
| Final campaigns | 6 |
| Pilots | 17 |
| Pilot contacts | 1,100 |
| Pilot communication cost | 14,900 |

No campaigns were rejected and no execution exceptions occurred. The evaluator's
23-campaign total includes 17 pilots plus 6 final campaigns. Its remaining-resource
lines describe the state after pilots; total cost/contacts also include finals.
The ten seed results remain unchanged by the fallback correctness fix.
All **10 project tests passed** (19.8 seconds total, including ten-seed integration
and CSV reproduction). A separately measured seed-42 `Agent.act` took **0.949
seconds** on this workspace. The regenerated CSV is nonempty and unchanged.

**The mock environment validates mechanics and robustness. Judging effects are
different, so the strategy is not tuned to specific mock effects.**

## Reproducibility

Run from the project root with Python 3.12:

```sh
pip install -r requirements.txt
python local_eval.py
python local_eval.py --runs 10
python make_submission.py
python -m unittest -v test_agent
```

This Windows workspace uses `.venv\Scripts\python.exe` in place of `python`.
Dependencies remain numpy and pandas only. Candidate order is deterministic; the
environment controls seeded sampling. `make_submission.py` uses seed 42. The test
suite validates the generated CSV against a fresh run; run generation before tests.
Local environments, caches, `.vscode/` and `.env` are ignored by Git.

## Files

| File | Purpose |
| --- | --- |
| `agent.py` | Submit: adaptive `Agent.act(env)` implementation |
| `submission.csv` | Submit: reproducible six-campaign output |
| `requirements.txt` | Submit: minimal numpy/pandas dependencies |
| `test_agent.py` | Deterministic edge-case and ten-seed integration checks |
| `README.md` | Approach, public mechanics, commands and limitations |
| `environment.py`, `mock_environment.py` | Unmodified organizer environment and mock factory |
| `scoring_core.py`, `local_eval.py` | Unmodified organizer scoring and evaluation |
| `make_submission.py` | Unmodified organizer CSV generator |
| `customer_profile.csv`, `data/`, dictionaries, guides, template | Unmodified participant inputs/reference files |

All 15 files from the participant ZIP were compared byte-for-byte and are unchanged.

## Constraints

| Competition limit | Enforcement |
| --- | --- |
| 1–10 final campaigns when a positive feasible plan is available | Positive-value selection; at most one fallback |
| 5,000 customers per final campaign | Explicit planner reach cap matching scorer |
| 15,000 total contacts, pilots included | Preflight pilot checks; finals use remaining contacts |
| 100,000 total communication budget | Actual pilot-size cost check; finals use remaining money |
| 20 pilots maximum | Check public `pilots_left` before every call |
| 10–200 customers per pilot | Bounded call sites; skip undersized samples |
| Valid tariffs, channels and filters | Public dictionaries and observed valid tariff/ARPU cells |
| Runtime below 10 minutes | Small local computations; exploration deadline at 540 seconds |
| No hidden state, mock effects or embedded secrets | Only documented environment API and supplied historical data |

If every feasible estimate is nonpositive, or no contacts remain, return an empty
plan rather than fabricate a profitable offer. Unknown true effects cannot be
certified positive in advance. All required local runs return valid nonempty plans.

## Failure Handling

Catch `RuntimeError`, `ValueError` and `OSError` only around pilot calls, warn, and
continue with other candidates. Reject malformed/nonfinite pilot responses.
Any contacts consumed by a failed or malformed response remain accounted for.
Historical-file read/schema failures yield neutral hypotheses; invalid historical
numbers are filtered. Programming errors are not hidden by a blanket exception
handler. There is no misleading partial-plan recovery claim.

Tests cover constrained resources, pilot failures, malformed observations, prior
reliability, call saturation, belief reversal after negative pilots, missing/invalid
history, positive-pilot fallback without history, deterministic output, valid
filters, exploration caps, runtime, full limits across ten seeds, and CSV reproduction.

## Known Limitations

- Historical population differs from the target population. Positive-history
  screening can miss transitions that become attractive under judging effects.
- Pilot observations are noisy; uncertainty and information value are approximate.
  One-standard-error ranking can select false positives after adaptive selection.
- Overlap can only be handled using public information; pilot identities are not
  exposed, and confirmation can resample previously contacted customers.
- Call saturation is bounded, not identified by call pilots. Weak conversion and
  population-shift priors are assumptions that pilots should override.
- Allocation is heuristic, with no global optimality guarantee. Data/call
  subsegments and multiple channels within a final cell are not optimized.
- Hidden judging effects differ from mock effects. Ten positive mock runs do not
  guarantee judging profit, and public noise changes would require reassessment.
- The documented API cannot interrupt an indefinitely blocking `run_pilot` call;
  the deadline controls when further exploration may start.
