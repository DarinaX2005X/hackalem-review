<div align="center">

# Money Graph

### An analyst is handed 81 accounts and a crawl of 2,248. This tells them where to act first, what to ask for next, and what the data cannot show them.

**HackAlem AI 2026 · Track 02 · Freedom**

## [Open the live case file →](https://money-graph.pages.dev/web/)

**https://money-graph.pages.dev/web/** · nothing to install, the same screen `python3 run.py --serve` builds locally

</div>

```
pip install -r requirements.txt
python3 run.py              # about a second, fifteen files in out/
python3 run.py --serve      # then open http://localhost:8000/web/
```

**Live:** https://money-graph.pages.dev (the same screen, served as a static site; `./deploy.sh` republishes it).
No API key. No network. No database. No build step. Five pinned dependencies.

## The situation on the analyst's desk

A financial monitoring analyst receives 81 flagged accounts from law enforcement and a crawl that
followed their outbound transfers four hops out through July 2026. The crawl comes back with
2,248 accounts and 4,840 transfers, 365,890,012 KZT of movement. The analyst has days, not weeks,
to say what the structure is, who holds it together, and where to spend the first week.

The obvious answer is a ranked list of suspicious accounts. A rank is a name. Freeze one account in
a group of twelve and the other eleven carry on.

![The investigator's funnel: 81 names given, 2,248 accounts crawled, 653 structures found, 25 priority targets, one breaking point per structure](docs/img/journey.png)

*81 names given, 2,248 accounts crawled, 653 structures found, 25 priority targets, and one breaking point per structure.*

## What the analyst does with it on Monday morning

1. **Act on the breaking point of the top funnel.** Row 1 of `out/formations.csv` is a funnel of
   4 accounts carrying 12,684,846 KZT. Three payers send a dominant share of their outflow into
   account …369100, and removing that one account cuts all three off
   (`breaking_point_method` = articulation, `breaking_point_effect` = 3). One case, not four.
2. **Send the ranked data request.** Row 1 of `out/next_data_request.csv` asks for one more crawl hop
   from the 444 accounts at the depth limit; that single request resolves 444 accounts and
   56,672,165 KZT whose onward path is unrecorded. Rows 2 to 4 are costed the same way.
3. **Open the live case file and type any account id.** The screen at
   https://money-graph.pages.dev/web/ returns one sentence: the role, the rule that fired and its
   numbers, money in and out, hop from a listed account, and the accounts around it on a map.

## The edge of the map, as a number

The crawl followed money outward only. Whoever funds the 81 flagged accounts was never followed, so
they are absent from the data by construction. The 81 sent out 55,294,178 KZT; only 14,849,167 KZT
was seen arriving. **40,445,011 KZT arrived with no recorded payer.** The system states that as a
computed output (`src/moneygraph/completeness.py`, `out/next_data_request.csv` row 3, section 07 of
the screen) rather than drawing a controller it cannot see.

## How this differs, in three checkable facts

| Instead of | This hands over | Where |
|---|---|---|
| Ranked accounts | 653 structures, each naming the one member whose removal breaks it and by how much | `out/formations.csv`, columns `breaking_point_gid`, `breaking_point_effect` |
| A label for every row | Abstention on 558 accounts where the crawl gives no basis for a role, 444 at the depth limit and 114 with fewer than three transfers, each row saying why | `out/nodes_roles.csv`, roles `abstained_boundary` and `abstained_single_observation` |
| A caveat in a footnote | The blind spot and the next data request as ranked outputs with KZT figures | `out/completeness.csv`, `out/next_data_request.csv` |

On the screen the same things are labelled in plain words: the 81 seeds are "listed accounts",
a breaking point is the "key account", and formations are "linked account groups" (`web/i18n.js`).

## Where each rubric criterion is met

| Criterion | Fact | Proof |
|---|---|---|
| Compliance and functionality | The three fixed-schema CSVs (2,248 roles, 91 clusters, 25 priority rows) plus a review screen with search by id, asserted before exit | `out/nodes_roles.csv`, `out/clusters.csv`, `out/top_nodes.csv`, `web/index.html`, `run.py`; table below |
| Technical implementation | Eight named rules with thresholds in one dict, zero model calls; breaking points by articulation point and dominator analysis; HITS made deterministic | `src/moneygraph/roles.py:44`, `src/moneygraph/formations.py:394` and `:510`, `src/moneygraph/features.py:34` |
| README and reproducibility | Two commands, about one second, fifteen files byte-identical to the committed `out/`, five dependencies pinned to exact versions | `requirements.txt`, `run.py`, `out/` |
| Value and applicability | Top formation recomputed by hand from the raw parquet to its score of 0.6944; data requests costed in accounts and KZT | `docs/FORMATIONS.md`, `out/next_data_request.csv` |
| Development potential and originality | Structures with breaking points, abstention as an output, the blind spot quantified at 40,445,011 KZT | `src/moneygraph/formations.py`, `src/moneygraph/roles.py`, `src/moneygraph/completeness.py:94` |

Everything below is the evidence for the claims above, criterion by criterion.

---

## Why this matters to a bank, and to the state

**Today.** The case specification sets out the analyst's position (`docs/case-spec-full.txt`, line 479): only the bottom of the chain is known, and who collects, moves and controls the money is reconstructed by hand. One customer across four hops costs hours of analyst work (lines 483 to 484). Only the bottom level gets blocked, and the organisers rebuild within days (line 488). Review priority is decided intuitively (line 489).

**On the desk, with this output.** 2,248 accounts become 25 priority targets (`out/top_nodes.csv`) and 653 linked groups, each naming a key account (`out/formations.csv`). Removing the top 20 leaves 1,917 accounts reachable from the listed ones, against 2,248 before, so 331 fewer (`out/resilience.csv`, row `20,1616,172,1917`): a measured effect, not an assumed one. The first data request resolves 444 accounts and 56,672,165 KZT (`out/next_data_request.csv`, row 1). The specification's own impact statement is "weeks of manual tracing" to "minutes" (line 491); the measured run is about one second (`run.py` console, `completed in 0.88 s`).

**Beyond a ranked list or a generic graph tool.** Three facts. It acts on groups, not names: row 1 of `out/formations.csv` is four accounts and 12,684,846 KZT resting on one member. It declines to label 558 accounts the data cannot support, 444 at the crawl boundary and 114 with a single observation, each row saying why (`out/nodes_roles.csv`, roles `abstained_boundary` and `abstained_single_observation`). It reports the blind spot, 40,445,011 KZT arriving at the listed accounts with no recorded payer (`src/moneygraph/completeness.py:331`, printed by `run.py`), and the request that closes it, so the bank's request to law enforcement names accounts, hop and amount rather than asking for more data.

**Fit with the process.** The case sits in a second-tier bank's financial monitoring function (line 493). The analyst receives 81 accounts from law enforcement (line 495) and finishes with a review list and a request to law enforcement (line 499). `out/next_data_request.csv` is that request, written by the pipeline and ranked by what each item resolves. Every group is a hypothesis for review, not a finding against anyone.

**Next.** The path to a million accounts is the "Scaling" paragraph under "Development potential and originality" below. `docs/COMPLETENESS.md` states what one further hop from the 444 boundary accounts would resolve.

---

## Compliance and functionality

Every mandatory requirement, where it is met, and how to check it.

| Requirement | Satisfied by | Verify |
|---|---|---|
| `nodes_roles.csv`, one row per node | `out/nodes_roles.csv`, asserted at `run.py` `assert len(nodes_roles) == report["nodes_declared"]` | `wc -l out/nodes_roles.csv` gives 2249 with header |
| Role from the taxonomy, extensions documented | `src/moneygraph/roles.py:37` `ROLES`; extension in `docs/COMPLETENESS.md` | `python3 -c "from src.moneygraph.roles import ROLES; print(ROLES)"` |
| Numeric evidence per node, under 200 characters | `roles.py:92` `_classify` returns evidence with the figures it fired on | `python3 -c "import pandas as pd; print(pd.read_csv('out/nodes_roles.csv').evidence.str.len().max())"` prints 161 |
| `clusters.csv` with a hypothesis per cluster | `out/clusters.csv`, 91 rows; `src/moneygraph/hypotheses.py` writes each sentence from that cluster's figures | asserted at `run.py` `cluster_table.hypothesis.str.len().gt(0).all()` |
| `top_nodes.csv`, at least 20 rows | `out/top_nodes.csv`, 25 rows; `src/moneygraph/priority.py:18` | asserted at `run.py` `assert len(top) >= 20` |
| Search any account by id | `web/index.html`, one search box in the top bar; returns the plain-language assessment, the rule and its numbers, money in and out, hop, group, priority, knowledge state, and the accounts around it on a map | `python3 run.py --serve`, type any gid |
| Roles are explainable, not a black box | `roles.py:44` `THRESHOLDS`, eight named rules, zero model calls in the repository | `grep -rn "openai\|anthropic\|import requests" src/` returns nothing |
| No hardcoded account lists | no gid literal in any `.py` or `.html` | `grep -rnE '1000000[0-9]{11}' src/ web/ tools/ run.py` returns nothing |
| No external enrichment, three parquet files in, fifteen files out | `src/moneygraph/dataio.py:27` `load` reads three files and nothing else | `grep -rln "urllib\|socket\|http" src/*/*.py` returns only `serve.py`, the local file server |
| Runs in under five minutes on a clean machine | About one second, measured from a fresh clone and virtual environment | `time python3 run.py` |
| Findings are hypotheses, never accusations | every generated string uses "the figures suggest", "worth checking as", "consistent with" | `grep -il "launder\|criminal\|fraud\|guilty" out/*` returns nothing |

The fifteen files in `out/` are committed. They regenerate byte for byte from `python3 run.py`, so a
judge can diff rather than trust.

---

## Technical implementation

![Five steps from the raw crawl to three files and a review screen: load, measure, apply the rules, find the structures, hand over](docs/img/solution-schema.png)

*One command turns the raw crawl into three files and a screen. Load the crawl (2,248 accounts, 4,840 transfers, 366m KZT), measure each account, apply eight plain rules with no model call, find 653 structures each with a breaking point, hand over roles for all 2,248, 91 clusters, 25 priority targets and a review screen.*

### The rule bank

![Accounts per role as horizontal bars, with the two abstention classes grouped and marked as the system declining to guess](docs/img/roles.png)

*69% of accounts are dead ends, and 444 of those are only dead ends because the crawl stopped. Terminal 1,091, peripheral 476, transit 72, distributor 26, coordinator 20, consolidator 5, and two abstention classes, 444 and 114, where the system declined to guess.*

Eight rules in one function, thresholds in one dict, each threshold placed against the observed
distribution and the reason written beside it in `src/moneygraph/roles.py:44`.

| Role | Count | Rule | Why the cutoff sits there |
|---|---:|---|---|
| `consolidator` | 5 | in-degree >= 8, pass-through <= 0.5 | The case declares a fan-in band of 8 to 24. Observed maximum is exactly 24 |
| `transit` | 72 | 0.8 <= pass-through <= 1.2 | Reproduces the 72 pass-through accounts the case declares, exactly |
| `distributor` | 26 | out-degree >= 20 | Falls in an empty bin. Observed values run 19, 19, 19, then 21, 21, 21 |
| `coordinator` | 20 | in-degree >= 4 and out-degree >= 4 | The weakest cutoff, and labelled as such in the code. A smooth decay, not a gap |
| `terminal` | 1,091 | money in, nothing out, not at the depth limit | The 444 truncated dead ends are excluded by construction |
| `peripheral` | 476 | below every threshold above | Includes the 19 accounts with no transfers at all, scored 0.1 |
| `abstained_boundary` | 444 | hop 4, no outgoing edge | Pass-through is zero because the crawl stopped, not because money stayed |
| `abstained_single_observation` | 114 | fewer than three transfers in total | A ratio from one pair of numbers is not a rate |

Precedence is widest fan-in, then widest fan-out, then relay ratio, then two-sided activity, because
an account can satisfy more than one rule and the earlier one is the stronger claim about it. That
order has a cost and the code says so: the transfer-count floor sits below transit, so **27 of the 72
transit accounts rest on a single transfer each way**. Moving the floor up would drop transit to 45 and
break the exact match with the case's declared 72. The rule stays and all 27 rows say in their own
evidence that the ratio is one observation rather than a rate.

The two abstention classes are held apart because the remedy differs: one more crawl hop resolves every
one of the 444 and none of the 114.

### Formations and breaking points

![The top 8 structures found, each with its breaking point account and the money touching it](docs/img/formations.png)

*Every structure has a breaking point, the one account whose removal disconnects the rest of it. The top formation is a funnel of 4 accounts carrying 12,684,846 KZT that breaks at account …369100.*

`src/moneygraph/formations.py:95` groups accounts into five kinds, each with a one-sentence rule:

| Kind | Found | Rule |
|---|---:|---|
| `funnel` | 8 | A collection point plus the payers sending it a dominant share of their outflow |
| `chain` | 51 | A directed path of relay accounts moving money onward with little retained |
| `reciprocal_loop` | 377 | A pair or short cycle returning funds to where they came from |
| `fan_out` | 45 | A distributor and the accounts it pays that have no outgoing transfer of their own |
| `bridge` | 172 | A small set whose removal splits an otherwise connected community |

The breaking point is computed by articulation point (`formations.py:394`), by dominator analysis from
the formation's entry (`formations.py:510`), or by flow where neither applies, and the method is
reported beside the number so 3 members is never confused with 3 tenge. Weights live in
`formations.py:54` and `:66`. `docs/FORMATIONS.md` recomputes the top formation by hand from the raw
parquet to its score of 0.6944, so a reviewer can check a row without running anything.

Fan-outs count their receivers in two groups, observed to the end and at the crawl boundary, because
92 of the 965 receiving accounts sit at hop 4 where nothing downstream was ever collected. Four
fan-outs have more boundary receivers than observed ones and say so in their own hypothesis.

### Why the ranking is not PageRank with extra steps

![Slope chart comparing the top 15 by PageRank with their position under the evidence rules; only one account stays at the top](docs/img/rank-disagreement.png)

*14 of the 15 accounts a money-weighted PageRank would chase fall out of the top 15 once the rules are applied. The one both methods agree on is the coordinator ranked first.*

Of the 15 accounts a money-weighted PageRank puts at the top, 14 fall out of the top 15 once the rule
bank is applied, most to `peripheral` at positions 40 to 173. The single account both methods agree on
is the coordinator ranked first. The comparison is written to `out/pagerank_vs_evidence.csv` on every
run by `src/moneygraph/exhibits.py`.

### What the crawl could not see, as a computed output

![Two bars comparing 55.3m KZT sent out by the 81 seed accounts with 14.8m KZT seen arriving, the 40.4m KZT gap having no recorded payer](docs/img/blind-spot.png)

*The 81 seed accounts sent out 55.3m KZT and only 14.8m KZT was seen arriving at them. The 40.4m KZT gap has no recorded payer, because the crawl never followed money inward.*

`src/moneygraph/completeness.py:94` assigns every account a knowledge state and a confidence score
from `CONFIDENCE_WEIGHTS` at line 44, and checks its own figures against the case's declared ground
truth at line 81.

| Knowledge state | Accounts | Share of money touched |
|---|---:|---:|
| `fully_observed` | 644 | 63.98% |
| `inbound_only` | 1,091 | 18.89% |
| `outbound_only` | 50 | 9.38% |
| `truncated_at_depth` | 444 | 7.74% |
| `isolated` | 19 | 0.00% |

1,604 accounts, 71.35% of the set, are not fully observed. The priority list reads two ways and both
are reported: only 2 of the top 20 rest directly on incomplete observation, but 15 of the top 20 send
money onward into the crawl boundary, with a mean 14.4% of everything beneath them sitting at hop 4 on
an unrecorded path. The uncertainty is not in the ranking. It is one hop underneath it.

### The pipeline

```
data/*.parquet
  dataio.py        three tables in, graph built from nodes.parquet not the edge list,
                   because 19 seeds appear in no edge and vanish otherwise (line 34)
  features.py      degrees, flows, PageRank, HITS with a fixed start vector (line 34),
                   pass-through, dwell, truncated_by_depth and genuine_terminal (lines 46 to 47)
  roles.py         the rule bank
  clusters.py      Louvain, seeded, plus weakly connected components
  hypotheses.py    one sentence per cluster from that cluster's own figures
  flows.py         reciprocal pairs, cycles, seed chains, the resilience curve
  formations.py    five kinds, breaking points, ranking
  completeness.py  knowledge state, confidence, the next data request
  priority.py      weighted ranking, WEIGHTS at line 11
  exhibits.py      where PageRank and the rules disagree
  timeline.py      the month cut by day, one row per date, payer and receiver
  echoes.py        relays, splits and fan splits: money leaving in the shape it arrived
  viewdata.py      graph.json, every gid serialised as a string (line 38)
  run.py           writes fifteen files and asserts on them before exiting
```

Account ids are 18 digits and exceed `Number.MAX_SAFE_INTEGER`, so two different accounts compare
as equal in JavaScript the moment either becomes a number. Every gid leaves Python as a string and
every map in the review screen is keyed on `String(id)`.

### Money that leaves in the shape it arrived

The edge list is the month folded flat. `src/moneygraph/timeline.py` unfolds it into one row per day,
payer and receiver, and `src/moneygraph/echoes.py` reads the dated transfers for amounts that go out
the way they came in. A **relay** is X received and X sent to one account the same day or the next. A
**split** is X received and two or more transfers sent over two days that sum to X. A **fan split** is
the same exact amount sent to three or more receivers on one day. The tolerance is one constant,
`ECHO_TOLERANCE = 0.02`, and a transfer takes part in at most one echo so money is never counted twice.

| | Found | Of which exact to the tenge |
|---|---:|---:|
| relay | 135 | |
| split | 61 | |
| fan split | 7 | |
| **all echoes** | **203 on 114 accounts** | **127** |

Together they carry 15,222,449 KZT, 4.16% of turnover. The largest is 652,000 KZT received and sent
straight back to the payer on the same day. Each is written as a sentence an analyst can read without
the table: "received 652,000 KZT on 2026-07-22 from …1668100 and sent 652,000 KZT the same day back to
…1668100 (exact)". A relay of 23,000 KZT, the median, can be rent passed on. A fan split of 30,000 KZT
to three accounts can be a payday. They are hypotheses, ranked by size and exactness, for a person to
test. On the screen they are section 06, Matching amounts; the same dated transfers drive section 05,
Transfers by day.

### The review screen

Live at **https://money-graph.pages.dev/web/**, or `python3 run.py --serve` then `http://localhost:8000/web/`. One HTML page and three modules, no
framework, no build step, no request to anything but its own `graph.json`. It is laid out as seven
numbered sections in a rail, with one search box that takes an account id from anywhere.

It opens in Russian. A RU/KZ/EN switch in the top bar changes it to Kazakh or English and remembers
the choice. The evidence strings, hypotheses and reasons are generated by the pipeline in English and
are shown as they are. Two colour schemes, Light by default and Dark for a projector, both drawn
from one token set, so the maps follow the switch.

**Deploying without Python.** The current build is published at https://money-graph.pages.dev on Cloudflare Pages; `./deploy.sh` uploads `index.html`, `.nojekyll`, `web/` and `out/` and nothing else. The screen is static: it needs only `web/` and `out/` next to each
other, and `out/graph.json` is committed. It runs from GitHub Pages (Settings → Pages → Deploy
from a branch → `main`, `/ (root)`) or from any static host pointed at the repository root; the
root `index.html` redirects to `web/`, and `.nojekyll` keeps Pages from filtering the folders. The
pipeline is only needed to regenerate `out/`.

| | Section | What it holds |
|---|---|---|
| 01 | Overview | The six figures of the extract, three accounts and three linked account groups to start with, the busiest day, the matching-amount count, the number of accounts at the edge of the data |
| 02 | Priority accounts | The 25 ranked accounts, each with its role and the rule's own numbers |
| 03 | Account | Who paid it on the left, who it paid on the right, arrows the way the money moved, width by KZT. The panel beside it reads as sentences |
| 04 | Linked account groups | The 653 groups ranked, each on its own map with the key account in amber |
| 05 | Transfers by day | July day by day on the hop layout: play, scrub, a 31-bar strip of daily KZT, a fading trail of the previous days |
| 06 | Matching amounts | The 203 matches as in → account → out diagrams with the amounts on the lines |
| 07 | Data limitations | The boundary figures, the ranked data requests, where centrality misleads, the removal test |

A hop is the number of transfers away from a listed account (one of the 81 named by law
enforcement). Hovering any role name shows its definition in one sentence.

---

## README and reproducibility

**Clean clone.** Copy the repository to an empty directory, create a virtual environment, install
from `requirements.txt`, run. Fifteen files in about a second, checksums matching the committed `out/`.

**Determinism, and what it took.** Three separate processes into three directories produce byte
identical output for all fifteen files. This was not free: `networkx.hits` draws its ARPACK starting
vector from operating system entropy, so `nodes_roles.csv` had a different hash on every run until an
explicit uniform `nstart` was passed at `features.py:34`. Because the fix depends on solver
behaviour, all five dependencies are pinned to exact PyPI versions, not floors.

**Assertions before exit**, all in `run.py`: exactly 2,248 role rows with non-empty evidence, at least
20 top nodes, a non-empty hypothesis on every cluster, every formation has members and a real
breaking point, completeness covers all 2,248 with confidence in 0 to 1, every secondary CSV written
and non-empty, `graph.json` parsed back with the keys the screen reads. A broken run fails loudly.

**The integrity report** prints before anything else and every line is checked against the case notes:

```
  nodes_declared                   2248
  nodes_in_graph                   2248
  edges                            3119
  transactions                     4840
  turnover_kzt                     365890012.01
  period                           ('2026-07-01', '2026-07-31')
  seeds                            81
  seeds_absent_from_edges          19
  seeds_without_outgoing           31
  dead_ends                        1554
  dead_ends_truncated_depth4       444
  dead_ends_genuine                1110
  weakly_connected_components      35
  edges_match_transactions         True
```

**Outputs**

| File | Rows | What an analyst does with it |
|---|---:|---|
| `nodes_roles.csv` | 2,248 | Look up any account and read why it has the role it has |
| `clusters.csv` | 91 | Read one sentence per community before opening anything else |
| `top_nodes.csv` | 25 | Start here on Monday morning |
| `formations.csv` | 653 | Pick a structure, act on its breaking point |
| `formation_members.csv` | 4,752 | See who else is in that structure and in what part |
| `completeness.csv` | 2,248 | Know how much to trust each row above |
| `next_data_request.csv` | 5 | Send this to whoever owns the data, ranked |
| `resilience.csv` | 6 | Show a manager what acting on the top 20 does |
| `pagerank_vs_evidence.csv` | 15 | Answer "why not just PageRank" |
| `echoes.csv` | 203 | Money that left an account in the shape it arrived: relays, splits, fan splits |
| `timeline.csv` | 4,286 | The month unfolded by day, what the replay plays |
| `reciprocal_pairs.csv`, `cycles.csv` | 177, 1,541 | Return flows and closed loops up to six hops |
| `graph.json`, `integrity.json` | | The review screen's data (committed, so the screen deploys as a static site) and the integrity report |

---

## Value and applicability

![Accounts still followable from the seeds as the top ranked accounts are removed, falling from 2,248 to 1,917 after 20 removals](docs/img/resilience.png)

*Accounts still followable from the seeds fall from 2,248 to 1,917 when the top 20 ranked accounts are removed. Twenty of those are the removed accounts, so 311 further accounts drop out of reach.*

**Who uses it.** An analyst on a financial monitoring or compliance team who has been handed a crawl
and a deadline. Not a data scientist. The outputs are CSVs they already know how to open and a screen
that answers "which account is this" in one search.

**What changes on Monday.** Instead of a list of 2,248 rows sorted by a score, the analyst opens
`formations.csv`, takes the top funnel, sees that three payers each send it 89% to 100% of their
outflow and that removing one account cuts all three off, and writes that up as one case rather than
four. Then they open `next_data_request.csv` and ask for one more crawl hop, because the file tells
them it would resolve 444 accounts and 56.7m KZT, and for hour-level timestamps, because that would
resolve 327 more.

| Rank | Ask for | Resolves | Illuminates |
|---:|---|---:|---:|
| 1 | One more crawl hop from the 444 nodes at the depth limit | 444 accounts | 56,672,165 KZT |
| 2 | Hour-level timestamps in place of calendar dates | 327 accounts | 65,673,806 KZT |
| 3 | Inbound transfers to the 81 seeds, one hop back | 81 accounts | 40,445,011 KZT |
| 4 | Account opening dates | 36 accounts | 3,749,141 KZT |
| 5 | Counterparty bank or institution | rejected | no figure would change |

Request 5 is kept and marked unevaluable on purpose. Nothing in the three tables stands in for an
institution, so a number here would be an opinion. Saying so is more useful than a plausible figure.

**What it protects against.** A confident organisational chart with a controller at the top is what
this data invites and cannot support. An analyst who acts on one goes looking for someone the crawl
never touched. The blind spot output exists so that does not happen.

**Where it already fits.** Any outbound crawl from a seed list has the same shape: a bank's own
transaction monitoring, a payment processor's fraud team, a regulator's request to a bank. The rule
bank reads one row at a time and does not change with scale. The parts that do, cycle enumeration and
chain path enumeration, are bounded by parameters in `flows.py` and `formations.py:28` and would come
down before the graph goes up.

---

## Development potential and originality

**Three things here are not in the starter script or the obvious build.**

1. **Formations with breaking points.** Everyone will rank accounts. Ranking structures, and naming the
   member that breaks each one, turns analytics into an instruction.
2. **Abstention as a first-class output.** 558 accounts are not labelled because the crawl gives no
   basis for a label, and each row says why. The two abstention classes are kept apart because they
   need different data to resolve.
3. **The blind spot, quantified.** Outbound-only crawls cannot see who funds the seeds. That is stated
   as a number, 40,445,011 KZT with no recorded payer, and ranked in the data request rather than
   left as a caveat.

**Where it goes next.** Amount echoes already use the transaction dates. The next step is
synchronisation: accounts that move money on the same days, in the same order, are being operated
together, and a same-day activity set is a sixth formation kind that is one `groupby` on a table
already loaded. After that, the replay becomes a diff between two months.

**Scaling.** 2,248 accounts run in under a second. At a million accounts Louvain and HITS go out of
core and would move to a graph store; nothing in the rule bank or the evidence format changes.

---

## Limitations, stated rather than discovered

| Limitation | Effect | What the pipeline does about it |
|---|---|---|
| The crawl is outbound-only | The funding source of the whole structure is outside the data | Quantified at 40,445,011 KZT and ranked in the next data request |
| In-degree is censored, out-degree is not | Fan-in and fan-out cannot be compared; the 8 funnels are a floor, not a count | Stated here and in `docs/FORMATIONS.md`; no claim about the network's overall shape is made from that comparison |
| The crawl stops at hop 4 | 444 accounts look like terminals and are not | Their own class, excluded from `terminal`, counted separately inside fan-outs, first in the data request |
| Dates, not timestamps | Same-day ordering is unresolved on 327 accounts | Second in the data request, with the turnover it would resolve |
| No balances | Seed funding is a residual, not a measurement | Labelled as "no observed payer", never as "outside money" |
| 27 transit roles rest on one transfer each way | A ratio from a single pair is not a rate | Kept to preserve the declared 72, and said so in each of the 27 evidence strings |
| Coordinator cutoff at 4 and 4 | A smooth curve, not a natural break | Said so in the code comment rather than dressed up as measured |

---

## Data handling

The dataset is anonymised and provided for this competition. Account identifiers are opaque. Nothing
in this repository enriches them from any outside source, and nothing leaves the machine it runs on.
Every finding is a hypothesis for an analyst to test. Transfer patterns are not proof of anything, and
no output of this system says they are.

---

<div align="center">

**Sam Yarasani and Karina Shalia**

</div>

---

## How this would be deployed in production for a government financial monitoring body

Nothing below is built. It is the deployment path, stated so that a reader can judge how far the prototype is from service.

**Where it runs.** On a server inside the authority's own network, or in the state cloud, with no outbound connection. The pipeline makes no network request and calls no model (`src/`, verify with `grep -rln "urllib\|socket\|http" src/*/*.py`, which returns only the local file server), so the transaction data never leaves the building. One virtual machine with Python 3.11 and the five pinned packages in `requirements.txt` is the whole runtime. The current extract runs in about a second; the "Scaling" paragraph above states what changes at one million accounts.

**How a case flows through it.** Law enforcement or the authority supplies the list of accounts and the bank supplies the transfer extract, in the three-file format in `docs/DATASET-README.md`. A scheduled or on-demand job runs `python3 run.py` per case and writes the fifteen files in `out/` to a case folder. The analyst opens the screen (`web/`, served behind the authority's single sign-on rather than the demo file server) in Russian, Kazakh or English, works the priority list and the groups, and exports `next_data_request.csv` as the formal request for the next extract. When the next hop arrives, the job runs again on the wider extract, so the request loop closes inside the same tool.

**Why an auditor can accept its output.** Every role is a named rule with a numeric threshold in one file (`src/moneygraph/roles.py`, `THRESHOLDS`), so a compliance officer can read, sign off and version the rules without reading the rest of the code. The outputs are deterministic: the same extract and the same pinned versions reproduce the same fifteen files byte for byte, so an output can be re-derived in a dispute. Every row carries its evidence with the figures the rule used, and every finding is worded as a hypothesis for review, never as a finding against a person.

**What would be added before service.** Access control and an audit log of who opened which account; retention and deletion rules for case folders; a signed release of the rule thresholds with a change history; a check of the extract's schema at intake with a rejection report; and a test suite run against each new extract, of which `tests/` and `qa/independent/` are the start.

**Who it serves.** The second-tier bank's financial monitoring function that the case specification describes (`docs/case-spec-full.txt`, lines 493 to 499), the authority that receives its reports, and the law enforcement unit that supplies the list and receives the request. The same output file serves all three, which is the point: one computed request instead of three separately drafted ones.

### How it would integrate with the state's existing process

The integration points are the two files at each end, which is deliberate: an authority can adopt a tool that reads one format and writes one format without changing its systems.

**Intake.** Banks already produce transaction extracts for the financial monitoring authority on request. The three-file format this pipeline reads (`docs/DATASET-README.md`) is a plain description of an account list, a transfer list and a transaction list; a bank's compliance system can produce it from its existing reporting, and the same format works for every bank, so the authority can run one job over extracts from several banks and see a group that spans them.

**Output into case management.** The three required files, `nodes_roles.csv`, `clusters.csv` and `top_nodes.csv`, plus `formations.csv`, are flat tables with an account id in every row. They load into the authority's case management system as they are, and each row carries its evidence, so the case record shows why an account was flagged without a link back to this tool.

**The request as an inter-agency document.** `next_data_request.csv` ranks the extracts to ask for next, with the accounts it resolves and the amount it illuminates. That is the content of the authority's request to the bank, or to another agency, in a form that can be sent, tracked and answered, and answered extracts feed the next run.

**Shared rules across institutions.** Because every role is a numeric threshold in one file (`src/moneygraph/roles.py`), the authority can publish the thresholds it accepts and every bank applies the same rules to its own data before reporting, which makes reports from different banks comparable. A change to a threshold is a change to one line with a written reason beside it, which is how a regulator prefers rules to be kept.

**Data stays in the country and in the institution.** No external service is called at any stage, so the tool can run inside a bank, inside the authority, or in the state cloud, and the extract need only move as far as the law already allows it to move.
