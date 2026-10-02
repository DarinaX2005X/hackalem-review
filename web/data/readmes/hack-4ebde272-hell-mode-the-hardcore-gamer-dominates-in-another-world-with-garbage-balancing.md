# Money Graph

Money Graph helps a bank's anti-money-laundering (AML) analyst answer:
**which of these 2,248 accounts should I review first, and why?**
It turns the supplied transaction files into explained roles, a priority list
and a searchable directed network, reducing the need to trace each chain manually.

## Run

Install Docker with Docker Compose. Place the supplied `nodes.parquet`,
`edges.parquet` and `transactions.parquet` files in `data/`, then run from the
repository root:

```bash
git clone https://github.com/BAITC-Hacks/hack-4ebde272-hell-mode-the-hardcore-gamer-dominates-in-another-world-with-garbage-balancing.git

cd hack-4ebde272-hell-mode-the-hardcore-gamer-dominates-in-another-world-with-garbage-balancing/

docker compose up --build -d
```

Open **[http://localhost:8501](http://localhost:8501)**. The command calculates
and validates the outputs before starting the viewer. No API key is required.
The first build downloads dependencies; core analysis and viewing run locally.

## Technologies

**Python 3.11**, **pandas**, **NumPy** and **PyArrow** process the data.
**NetworkX** computes graph metrics and Louvain communities. **Streamlit**,
**PyVis** and **Altair** provide the interface, network map and charts.
**Docker Compose** runs the pipeline and viewer together; dependency versions
are pinned in `requirements.txt` and `constraints.txt`.

## How to verify the solution

1. **Check the generated data** after startup:

   ```bash
   docker compose exec -T app python main.py --data /app/data --out /app/out --validate-only
   ```

   Expected result: `strict artifact and provenance validation: OK`. This checks
   all 2,248 identifiers, required CSV schemas, scores, cluster/top-list
   consistency and source/output hashes. `docker compose logs analytics` shows
   output row counts and runtime; the brief requires less than 300 seconds.

2. **Check the analyst workflow.** Open **Investigation queue** and read a ranked
   account's reason. Copy any `gid` from `out/nodes_roles.csv` into **Node card →
   Search arbitrary gid**. Inspect **Role evidence**, thresholds and priority
   contributions, then find its directed links in **Network explorer**. Repeat
   for three chosen gids; **Cluster review** shows their community summaries.

3. **Run automated checks**, including the browser workflow:

   ```bash
   docker compose --profile test run --build --rm tests
   ```

   The test service disables runtime networking; no live AI API is needed.

See the [architecture diagram](documentation/architecture.md) and
[five-minute walkthrough](DEMO.md) for a guided review.

## Role criteria and thresholds

Scores combine graph percentiles with available flow and temporal observations.
A candidate must pass its eligibility rule and score **at least 0.55**.

| Role | Eligibility and supporting pattern |
|---|---|
| **Consolidator** | At least 2 incoming counterparties, and either reachability from at least 2 initial case accounts or incoming degree at/above the 80th percentile. Emphasizes incoming relationships, transfers and amounts. |
| **Distributor** | At least 2 outgoing counterparties. Emphasizes outgoing relationships, transfers, amounts and links across communities. |
| **Transit** | Both incoming and outgoing relationships, plus a valid outgoing/incoming amount ratio in **[0.5, 1.5]** or two-day relay ratio **≥0.5**. |
| **Coordinator** | At least 1 observed relationship and at least 2 signals at/above the **90th percentile** among seed reach, path bridging, PageRank and cross-community degree. |
| **Terminal** | Nonseed, depth **<4**, uncensored observations, positive inflow, and outgoing amount **≤10%** of inflow; also requires zero outgoing degree or a valid outgoing/incoming ratio **≤0.10**. |
| **Peripheral** | No structural role qualifies. Strength is the strongest structurally eligible score below 0.55, or **0** if no structural gate passes. |

“Seed reach” counts initial case accounts reaching a node within four directed
hops. Two-day relay measures eligible incoming dates with outgoing activity on
the same date or either of the next two dates.

The highest eligible score wins. Exact ties follow **coordinator → consolidator
→ distributor → transit → terminal → peripheral**. Percentiles use average tied
ranks; missing score components are excluded and remaining role weights are
renormalized. Invalid seed and boundary ratios are not treated as observed zeros.

The [decision rules](documentation/decision-rules.md) contain the full weighted
formulas, priority weights and worked explanations.

## Output

Files are generated in `out/` with these exact submission schemas:

| File | Contents |
|---|---|
| `nodes_roles.csv` | One row for each of the **2,248 nodes**: role, strength, community, review priority and numeric evidence of at most **200 characters**. |
| `clusters.csv` | One row per community: population, seed count, internal turnover, leading accounts and a structural hypothesis. |
| `top_nodes.csv` | **50 ranked accounts**, ordered by descending priority then gid, with a separate explanation of why each deserves review. |

```text
nodes_roles.csv: gid,role,role_score,cluster_id,priority_score,evidence
clusters.csv: cluster_id,n_nodes,n_seed,sum_kzt_internal,top_gids,hypothesis
top_nodes.csv: rank,gid,role,priority_score,why
```

Scores are bounded by **[0,1]**. Gids remain exact int64 identifiers; import them
as text in spreadsheet software to avoid rounding.

Additional files preserve detailed metrics and rule diagnostics
(`node_features.parquet`), removal scenarios (`resilience.csv`) and provenance
(`run_metadata.json`). The viewer provides gid search, directed links, role and
cluster views, node explanations and an analyst review-list download.

## Limitations

- **Hop-4 cutoff:** missing outgoing transfers cannot establish a final recipient.
- **Incomplete inflows:** seed accounts and transfers outside the sample do not
  have complete observed balances; dependent seed ratios are unavailable.
- **Restricted sample:** July 2026 intrabank transfers of at least **5,000 KZT**.
  Other banks, smaller transfers and activity outside the period are invisible.
- **Date-only timing:** overlap does not prove payment order or movement of the
  same funds. Incomplete two-day follow-up windows are excluded.
- **No ground truth:** roles, priorities and communities are investigation
  hypotheses, not calibrated probabilities or findings of guilt. No customer
  attributes are inferred. The supplied data is restricted to hackathon use.
- **Dataset scope:** the production pipeline expects 2,248 nodes; larger-scale
  performance has not been established.

## Scaling to one million nodes

- Partition transactions and pre-aggregate edges and daily activity using a
  columnar engine such as DuckDB or Polars.
- Replace exact betweenness with reproducible sampling; use sparse PageRank and
  partitioned community/seed-reach calculations with explicit work limits.
- Replace per-node transaction scans with vectorized window joins; keep route
  searches bounded and preserve observation-availability flags.
- Precompute decisions, index gid lookups, paginate queues and render limited
  neighborhoods instead of the entire graph.

Benchmark memory, latency and approximation stability before claiming support
for that scale.
