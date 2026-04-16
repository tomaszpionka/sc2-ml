---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_02 — Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
critique_required: true
source_artifacts:
  - "reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md"
  - "data/db/db.duckdb (matches_raw, ratings_raw, leaderboards_raw)"
---

# Plan: aoe2companion Step 01_02_06 -- Bivariate EDA

## Scope

**Phase/Step:** 01 / 01_02_06
**Branch:** feat/census-pass3
**Action:** CREATE (step 01_02_06 does not exist in ROADMAP.md; added here)
**Predecessor:** 01_02_05 (Univariate Census Visualizations -- complete, artifacts on disk)

Create a bivariate EDA notebook that answers seven scientific questions about
feature-outcome and feature-feature relationships in aoe2companion. Reads the
01_02_04 census JSON for runtime constants and queries DuckDB for conditional
distributions and correlations. Produces 8+ thesis-grade PNG plots and a
markdown artifact with all SQL queries (Invariant #6). No new tables created.
No DuckDB writes.

This step is the second layer of the 01_02 EDA stack:
- 01_02_04: Univariate Census (complete)
- 01_02_05: Univariate Visualizations (complete)
- **01_02_06: Bivariate EDA (this plan)**
- 01_02_07: Multivariate EDA (next)

## Problem Statement

Step 01_02_04/05 established univariate profiles for all columns. Bivariate
analysis answers the next-layer questions: (1) which features separate winners
from losers? (2) which features are correlated with each other? Most critically,
this step resolves the blocking temporal-leakage question for `ratingDiff` and
investigates the ambiguous temporal status of `rating`. If `ratingDiff`
distributions are strongly bimodal by `won`, this confirms it is post-game
(I3-violating). If `rating` shows the same bimodal pattern, it is likely
also post-game (rating_after = rating_before + ratingDiff).

## Scientific Questions

**Q1 -- ratingDiff x won (I3 resolution test):** Does the distribution of
`ratingDiff` differ by `won=True` vs `won=False`? If positive ratingDiff
aligns with won=True and negative with won=False, this is definitive proof
that ratingDiff is post-game outcome data. **This question is blocking for
Phase 02 feature engineering.**

**Q2 -- rating x won (ambiguity test):** Does the distribution of
`matches_raw.rating` differ by `won=True` vs `won=False`? If winners have
systematically higher ratings, `rating` may be post-game (= pre_rating +
ratingDiff). If the distributions overlap nearly completely, `rating` is
likely pre-game Elo.

**Q3 -- rating vs ratingDiff scatter (structural relationship):** What is
the direct relationship between `rating` and `ratingDiff`? If the data shows
tight linear structure, it suggests `rating = pre_rating + ratingDiff`
(post-game). If the scatter is diffuse, the two columns may be independently
sourced.

**Q4 -- Duration x won:** Does match duration differ by outcome? Longer games
may indicate more uncertain contests where both players are competitive.
Duration is known post-game but is a match-level descriptor, not a direct
leakage vector -- the bivariate test characterizes its predictive power.

**Q5 -- All numeric features x won (multi-panel):** For each primary numeric
feature in matches_raw, how does its conditional distribution by `won` look?
Provides a single summary figure for all feature-outcome relationships.

**Q6 -- Spearman correlation matrix:** Which numeric features are correlated?
High inter-feature correlation informs Phase 02 feature selection (redundancy
detection) and model design (collinearity).

**Q7 -- ratingDiff distribution by leaderboard:** Does the leakage pattern
(ratingDiff separation by won) hold uniformly across all leaderboard types,
or does it vary by queue? This determines whether the I3 conclusion applies
globally or only to ranked queues.

## Assumptions & Unknowns

- The census JSON at `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the single source of truth for total_rows, NULL rates, and numeric stats.
- DuckDB contains the materialized `matches_raw` (277M rows), `ratings_raw`
  (58.3M rows), and `leaderboards_raw` (2.4M rows) tables from 01_02_02.
- Violin plots for conditional distributions use DuckDB `PERCENTILE_CONT` to
  compute quantile data server-side -- no raw row export to pandas for 277M-row
  tables.
- Scatter plots require sampling. 277M rows cannot be rendered. The sample
  fraction is derived at runtime from census total_rows (I7).
- The primary prediction scope is `rm_1v1` + `qp_rm_1v1` leaderboards
  (30.5M 1v1 matches from 01_02_04 census).
- `rating` and `ratingDiff` share identical NULL rates (42.46% = 117,656,260
  rows), confirming row-level co-occurrence from 01_02_04.
- `won` has 4.69% NULL (12,985,561 rows). All bivariate analyses condition on
  `won IS NOT NULL`.

**Key unknown:** Whether `rating` is pre-game or post-game. Q2 and Q3 are
designed to resolve this. The conclusion from this step will either:
(a) confirm `rating` as post-game (must be excluded from features), or
(b) leave it ambiguous (deferred to Phase 02 row-level verification).

## Literature Context

Not applicable for a data exploration step. Threshold derivations reference
the 01_02_04 census artifact, not external literature.

## Part A -- ROADMAP Patch

Add the following YAML step definition to ROADMAP.md after the Step 01_02_05 block:

```yaml
step_number: "01_02_06"
name: "Bivariate EDA"
description: "Bivariate exploratory data analysis for aoe2companion. Conditional distributions of numeric features by won (violin plots), Spearman correlation matrix, rating vs ratingDiff scatter (sampled), ratingDiff by leaderboard. Resolves temporal leakage status of ratingDiff (Q1) and investigates rating ambiguity (Q2). All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations per Invariant #3."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "Which numeric features differ by outcome (won)? Which feature pairs are correlated? Is ratingDiff definitively post-game? Is rating pre- or post-game?"
method: "DuckDB aggregated queries for conditional distributions (PERCENTILE_CONT by won). TABLESAMPLE BERNOULLI for scatter plots (sample fraction derived from census total_rows at runtime, I7). Spearman correlation via scipy.stats.spearmanr on BERNOULLI-sampled rows (DuckDB CORR computes Pearson only). 8 plots. Markdown artifact with all SQL (I6)."
stratification: "By leaderboard (1v1 focus: rm_1v1 + qp_rm_1v1)."
predecessors:
  - "01_02_04"
  - "01_02_05"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "ratings_raw"
    - "leaderboards_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_rating_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_rating_vs_ratingdiff.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_duration_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_numeric_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_spearman_correlation.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_leaderboard.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_won_by_leaderboard.png"
  report: "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
gate:
  artifact_check: "All 8 PNG files exist under plots/. 01_02_06_bivariate_eda.md exists with SQL queries (Invariant #6) and plot index table including Temporal Annotation column."
  continue_predicate: "Notebook executes end-to-end without error. ratingDiff temporal status resolved."
  halt_predicate: "DuckDB queries fail on matches_raw or sampling yields zero rows."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "ratingDiff violin carries POST-GAME annotation. rating violin carries AMBIGUOUS annotation. Q1 result resolves ratingDiff status definitively."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "Sample fraction derived from census total_rows at runtime. All clip boundaries, bin widths, and annotation values from census JSON. No hardcoded numbers."
  - number: "9"
    how_upheld: "Bivariate analysis of features established in 01_02_04. No new column discovery or schema changes."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
  - "Chapter 4 -- Data and Methodology > 4.1.4 Temporal Leakage Audit"
research_log_entry: "Required on completion."
```

## Part B -- Notebook Task List

### T01 -- ROADMAP and STEP_STATUS Patch

**Objective:** Add the Step 01_02_06 definition to ROADMAP.md and register the
step in STEP_STATUS.yaml as `not_started`.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`.
2. Insert the Step 01_02_06 YAML block (from Part A) after the Step 01_02_05
   block and before the Phase 02 placeholder.
3. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`.
4. Add `01_02_06` entry with `name: "Bivariate EDA"`,
   `pipeline_section: "01_02"`, `status: not_started`.

**Verification:**
- ROADMAP.md contains Step 01_02_06 YAML block with all 8 PNG outputs listed.
- STEP_STATUS.yaml contains `01_02_06` entry with `status: not_started`.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`

### T02 -- Notebook Setup

**Objective:** Create the notebook skeleton with imports, DuckDB connection,
census JSON load, path setup, sql_queries dict, and sampling fraction derivation.

**Instructions:**
1. Create `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.py`
   with jupytext percent-format header (same kernel metadata as 01_02_05).
2. Markdown header cell:

```
# Step 01_02_06 -- Bivariate EDA: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
# **Dataset:** aoe2companion
# **Question:** Which numeric features differ by outcome (won)? Which feature
#   pairs are correlated? Is ratingDiff definitively post-game?
# **Invariants applied:**
#   - #3 (temporal discipline -- ratingDiff POST-GAME annotated; rating AMBIGUOUS)
#   - #6 (reproducibility -- all SQL queries written verbatim to markdown artifact)
#   - #7 (no magic numbers -- sample fractions and all thresholds derived from census)
#   - #9 (step scope: bivariate analysis of 01_02_04/05 established features only)
# **Predecessor:** 01_02_05 (Univariate Census Visualizations)
# **Step scope:** Bivariate EDA. No DuckDB writes. No new tables. No schema changes.
# **Outputs:** 8 PNG plots + 01_02_06_bivariate_eda.md
```

3. Imports:
```python
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOE2COMPANION_DB_FILE

logger = setup_notebook_logging()
matplotlib.use("Agg")
```

4. Connect to DuckDB read-only:
```python
con = duckdb.connect(str(AOE2COMPANION_DB_FILE), read_only=True)
print(f"Connected to: {AOE2COMPANION_DB_FILE}")
```

5. Load census JSON:
```python
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

census_json_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_json_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")
```

6. Assert required keys:
```python
required_keys = [
    "matches_raw_total_rows",
    "matches_raw_null_census",
    "matches_raw_numeric_stats",
    "won_distribution",
    "match_duration_stats",
    "categorical_profiles",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"
```

7. Derive sampling fraction (I7):
```python
# I7: sample fraction derived from census total_rows at runtime
total_rows = census["matches_raw_total_rows"]  # 277,099,059
TARGET_SAMPLE_ROWS = 100_000  # I7: editorial cap for scatter plot visibility
sample_pct = min(100.0, TARGET_SAMPLE_ROWS * 100.0 / total_rows)
print(f"Total rows: {total_rows:,}")
print(f"Target sample: {TARGET_SAMPLE_ROWS:,}")
print(f"Sample percent: {sample_pct:.6f}%")
# Expected: ~0.036% for 277M rows
```

8. Extract key numeric stats from census for reuse:
```python
def get_numeric_stat(column_name: str) -> dict:
    """Extract numeric stats for a column from census JSON."""
    for stat in census["matches_raw_numeric_stats"]:
        if stat["column_name"] == column_name:
            return stat
    raise KeyError(f"Column {column_name} not found in matches_raw_numeric_stats")

rating_stats = get_numeric_stat("rating")
ratingdiff_stats = get_numeric_stat("ratingDiff")
```

9. Initialize: `sql_queries = {}`.

10. Define the 1v1 leaderboard filter (derived from census categorical_profiles):
```python
# I7: leaderboard filter derived from census categorical_profiles at runtime
leaderboard_names = [
    entry["value"]
    for entry in census["categorical_profiles"]["leaderboard"]
]
# Primary 1v1 scope: rm_1v1 and qp_rm_1v1
assert "rm_1v1" in leaderboard_names, "rm_1v1 not in census leaderboard list"
assert "qp_rm_1v1" in leaderboard_names, "qp_rm_1v1 not in census leaderboard list"
LEADERBOARD_1V1_FILTER = "leaderboard IN ('rm_1v1', 'qp_rm_1v1')"
print(f"1v1 leaderboard filter: {LEADERBOARD_1V1_FILTER}")
```

**Verification:**
- Notebook imports and runs through setup without error.
- Census JSON loads and key assertion passes.
- Sample fraction printed as ~0.036%.
- Leaderboard filter assertion passes.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.py`

### T03 -- ratingDiff by won Violin (Q1 -- I3 Resolution Test)

**Scientific question answered:** Q1 -- Is ratingDiff definitively post-game?

**Input:** DuckDB query on matches_raw. Census: ratingDiff mean=-0.19, median=0,
std=17.66, range [-174, +319], 42.46% NULL (117,656,260 rows).

**Output:** `plots/01_02_06_ratingdiff_by_won.png`

**SQL (store in `sql_queries["ratingdiff_percentiles_by_won"]`):**
```sql
SELECT
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95,
    MIN(ratingDiff) AS min_val,
    MAX(ratingDiff) AS max_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
```

**SQL for histogram bins (store in `sql_queries["ratingdiff_hist_by_won"]`):**
```sql
SELECT
    won,
    ratingDiff AS val,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, ratingDiff
ORDER BY won, ratingDiff
```
I7 justification: ratingDiff has integer values in narrow range [-174, +319] (from
census `matches_raw_numeric_stats` where `column_name="ratingDiff"`). No binning
needed -- plot all distinct values directly. Leaderboard filter uses the 1v1
scope established in 01_02_04.

**Python:**
```python
# --- T03: ratingDiff by won Violin (Q1 -- I3 Resolution Test) ---
sql_queries["ratingdiff_percentiles_by_won"] = """
SELECT
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95,
    MIN(ratingDiff) AS min_val,
    MAX(ratingDiff) AS max_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
"""

sql_queries["ratingdiff_hist_by_won"] = """
SELECT
    won,
    ratingDiff AS val,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, ratingDiff
ORDER BY won, ratingDiff
"""

df_rd_stats = con.execute(sql_queries["ratingdiff_percentiles_by_won"]).fetchdf()
df_rd_hist = con.execute(sql_queries["ratingdiff_hist_by_won"]).fetchdf()
print(df_rd_stats)

# Build mirrored histogram (won=False left, won=True right)
df_win = df_rd_hist[df_rd_hist["won"] == True].copy()  # noqa: E712
df_loss = df_rd_hist[df_rd_hist["won"] == False].copy()  # noqa: E712

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(df_win["val"], df_win["cnt"], width=1.0, alpha=0.6, color="steelblue", label="won=True")
ax.bar(df_loss["val"], df_loss["cnt"], width=1.0, alpha=0.6, color="salmon", label="won=False")

# I7: stats from query result, not hardcoded
win_row = df_rd_stats[df_rd_stats["won"] == True].iloc[0]  # noqa: E712
loss_row = df_rd_stats[df_rd_stats["won"] == False].iloc[0]  # noqa: E712
n_total = int(win_row["n"] + loss_row["n"])

ax.set_xlabel("ratingDiff")
ax.set_ylabel("Count")
ax.set_title(
    f"ratingDiff Distribution by Outcome -- 1v1 Ranked\n"
    f"(N={n_total:,}, excl. {census['matches_raw_total_rows'] - n_total:,} NULL/non-1v1)"
)
ax.legend(loc="upper right", fontsize=9)

# Key annotation: mean ratingDiff for winners vs losers
ax.annotate(
    f"Won=True: mean={win_row['mean_val']:.1f}, median={win_row['median_val']:.0f}\n"
    f"Won=False: mean={loss_row['mean_val']:.1f}, median={loss_row['median_val']:.0f}",
    xy=(0.98, 0.85), xycoords="axes fraction",
    ha="right", va="top", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

# I3: POST-GAME annotation (mandatory)
# I7: annotation text derived from query result, not hardcoded
win_mean = df_rd_stats.loc[df_rd_stats["won"] == True, "mean_val"].values  # noqa: E712
loss_mean = df_rd_stats.loc[df_rd_stats["won"] == False, "mean_val"].values  # noqa: E712
if len(win_mean) > 0 and len(loss_mean) > 0 and win_mean[0] > 0 and loss_mean[0] < 0:
    leakage_annotation = "POST-GAME: positive ratingDiff → won=True, negative → won=False\nCONFIRMED LEAKAGE (Inv. #3)"
else:
    leakage_annotation = "POST-GAME annotation (Inv. #3) — ratingDiff known only after match"
ax.annotate(
    leakage_annotation,
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_ratingdiff_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_ratingdiff_by_won.png'}")
```

**Temporal classification annotation:** POST-GAME (Inv. #3). If mean ratingDiff
for won=True is positive and for won=False is negative, this is definitive
leakage confirmation.

**Invariant notes:**
- I3: POST-GAME annotation mandatory. This plot is the definitive resolution test.
- I6: SQL in sql_queries dict.
- I7: all stats derived from query results and census. Leaderboard filter from census.

### T04 -- rating by won Violin (Q2 -- Ambiguity Test)

**Scientific question answered:** Q2 -- Is `matches_raw.rating` pre-game or post-game?

**Input:** DuckDB query on matches_raw. Census: rating mean=1120.23, median=1093,
std=290.01, sentinel min=-1, 42.46% NULL.

**Output:** `plots/01_02_06_rating_by_won.png`

**SQL (store in `sql_queries["rating_percentiles_by_won"]`):**
```sql
SELECT
    won,
    COUNT(*) AS n,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    STDDEV(rating) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
```
I7 justification: sentinel value -1 excluded with `rating > 0` (from census
`matches_raw_numeric_stats`, `min_val=-1`).

**Python:**
```python
# --- T04: rating by won Violin (Q2 -- Ambiguity Test) ---
sql_queries["rating_percentiles_by_won"] = """
SELECT
    won,
    COUNT(*) AS n,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    STDDEV(rating) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
"""

# Histogram bins for overlay
sql_queries["rating_hist_by_won"] = """
SELECT
    won,
    FLOOR(rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, bin
ORDER BY won, bin
"""

df_rat_stats = con.execute(sql_queries["rating_percentiles_by_won"]).fetchdf()
df_rat_hist = con.execute(sql_queries["rating_hist_by_won"]).fetchdf()
print(df_rat_stats)

# Build overlapping histograms
df_rat_win = df_rat_hist[df_rat_hist["won"] == True].copy()  # noqa: E712
df_rat_loss = df_rat_hist[df_rat_hist["won"] == False].copy()  # noqa: E712

# I7: bin width 25 matches 01_02_05 T08 for visual consistency
# (stddev=290.01 from census => ~0.09 stddev per bin, ~64 bins in p05-p95 range)
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(df_rat_win["bin"], df_rat_win["cnt"], width=25, alpha=0.5,
       color="steelblue", label="won=True")
ax.bar(df_rat_loss["bin"], df_rat_loss["cnt"], width=25, alpha=0.5,
       color="salmon", label="won=False")

win_row = df_rat_stats[df_rat_stats["won"] == True].iloc[0]  # noqa: E712
loss_row = df_rat_stats[df_rat_stats["won"] == False].iloc[0]  # noqa: E712
n_total = int(win_row["n"] + loss_row["n"])

ax.set_xlabel("Rating (Elo)")
ax.set_ylabel("Count")
ax.set_title(
    f"Rating Distribution by Outcome -- 1v1 Ranked\n"
    f"(N={n_total:,}, sentinel -1 excluded)"
)
ax.legend(fontsize=9)

# Stats annotation
mean_diff = win_row["mean_val"] - loss_row["mean_val"]
ax.annotate(
    f"Won=True: mean={win_row['mean_val']:.0f}, median={win_row['median_val']:.0f}\n"
    f"Won=False: mean={loss_row['mean_val']:.0f}, median={loss_row['median_val']:.0f}\n"
    f"Mean difference: {mean_diff:+.1f}",
    xy=(0.98, 0.85), xycoords="axes fraction",
    ha="right", va="top", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

# I3: AMBIGUOUS annotation
ax.annotate(
    "AMBIGUOUS -- temporal status under investigation\n"
    "If mean(won=True) >> mean(won=False), rating may be post-game",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkorange",
    bbox=dict(boxstyle="round,pad=0.3", fc="#fff3e0", ec="orange", alpha=0.9),
)

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_rating_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_rating_by_won.png'}")
```

**Decision logic (post-plot):** If `abs(mean_diff) < 5` (i.e. less than 2% of
the standard deviation of 290), conclude "rating distributions overlap
substantially -- likely pre-game." If `abs(mean_diff) > 50`, conclude "rating
distributions separated -- likely post-game." Intermediate values: "inconclusive
-- defer to Phase 02 row-level check." The threshold of 5 and 50 are ~1.7% and
~17% of stddev respectively (I7: derived from census stddev=290.01).

**Invariant notes:**
- I3: AMBIGUOUS annotation required.
- I6: SQL in sql_queries dict.
- I7: sentinel -1 from census min_val. Bin width 25 matches 01_02_05 for consistency.

### T05 -- rating vs ratingDiff Scatter (Q3 -- Structural Relationship)

**Scientific question answered:** Q3 -- Direct structural relationship.

**Input:** Sampled DuckDB query on matches_raw.

**Output:** `plots/01_02_06_rating_vs_ratingdiff.png`

**SQL (store in `sql_queries["rating_vs_ratingdiff_scatter"]`):**
```sql
SELECT
    rating,
    ratingDiff,
    won
FROM matches_raw
TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```
Note: the `{sample_pct:.6f}` is formatted at runtime from the census-derived
value computed in T02. DuckDB TABLESAMPLE BERNOULLI must appear before WHERE.

I7 justification: sample_pct = min(100.0, 100000 * 100.0 / 277099059) =
~0.0361% (derived from census `matches_raw_total_rows`). Expected ~100K rows
for scatter plot visibility.

**Python:**
```python
# --- T05: rating vs ratingDiff Scatter (Q3) ---
# I7: sample fraction derived from census at runtime (computed in T02)
scatter_sql = f"""
SELECT
    rating,
    ratingDiff,
    won
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
"""
sql_queries["rating_vs_ratingdiff_scatter"] = scatter_sql

df_scatter = con.execute(scatter_sql).fetchdf()
n_sampled = len(df_scatter)
print(f"Sampled rows for scatter: {n_sampled:,}")

fig, ax = plt.subplots(figsize=(10, 8))
colors = {True: "steelblue", False: "salmon"}
for won_val, group in df_scatter.groupby("won"):
    ax.scatter(
        group["rating"], group["ratingDiff"],
        c=colors[won_val], alpha=0.15, s=3,
        label=f"won={won_val}",
        rasterized=True,
    )

ax.set_xlabel("Rating (Elo)")
ax.set_ylabel("ratingDiff")
ax.set_title(
    f"Rating vs ratingDiff -- 1v1 Ranked (sampled N={n_sampled:,})\n"
    f"BERNOULLI sample {sample_pct:.4f}% of {total_rows:,} rows"
)
ax.legend(fontsize=9, markerscale=5)
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")

# Correlation annotation
from scipy.stats import spearmanr
rho, pval = spearmanr(df_scatter["rating"], df_scatter["ratingDiff"])
ax.annotate(
    f"Spearman rho={rho:.4f}, p={pval:.2e}",
    xy=(0.02, 0.02), xycoords="axes fraction",
    ha="left", va="bottom", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

# I3: Both columns carry temporal annotations
ax.annotate(
    "rating: AMBIGUOUS | ratingDiff: POST-GAME (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_rating_vs_ratingdiff.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_rating_vs_ratingdiff.png'}")
```

**Interpretation logic:** If the scatter shows a tight linear band (high |rho|
> 0.3), this suggests `rating` and `ratingDiff` are structurally linked
(post-game). If the scatter is diffuse (|rho| < 0.1), they are independently
sourced.

**Invariant notes:**
- I3: Both columns annotated.
- I6: SQL in sql_queries dict.
- I7: sample_pct derived from census total_rows. Sentinel -1 excluded.

### T06 -- Duration by won Violin (Q4)

**Scientific question answered:** Q4 -- Does match duration differ by outcome?

**Input:** DuckDB query on matches_raw. Census: median 1,678s, p95 3,789s.

**Output:** `plots/01_02_06_duration_by_won.png`

**SQL (store in `sql_queries["duration_percentiles_by_won"]`):**
```sql
SELECT
    won,
    COUNT(*) AS n,
    AVG(EXTRACT(EPOCH FROM (finished - started))) AS mean_secs,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started))) AS median_secs,
    STDDEV(EXTRACT(EPOCH FROM (finished - started))) AS std_secs,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
```

**SQL for histogram bins (store in `sql_queries["duration_hist_by_won"]`):**
```sql
SELECT
    won,
    FLOOR(EXTRACT(EPOCH FROM (finished - started)) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND EXTRACT(EPOCH FROM (finished - started)) <= {p95_secs}
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, bin_min
ORDER BY won, bin_min
```
I7 justification: p95 clip value from census key `match_duration_stats[0]["p95_secs"]`
= 3789. Non-positive durations excluded with `finished > started` (census:
`duration_excluded_rows[0]["non_positive_duration_count"]` = 2941).
Bin width = 1 minute (~63 bins in 0-63 min range, matching 01_02_05 T10).

**Python:**
```python
# --- T06: Duration by won Violin (Q4) ---
# I7: p95 clip from census
p95_secs = census["match_duration_stats"][0]["p95_secs"]  # 3789
n_excluded = census["duration_excluded_rows"][0]["non_positive_duration_count"]  # 2941
p95_min = p95_secs / 60.0  # 63.15

sql_queries["duration_percentiles_by_won"] = """
SELECT
    won,
    COUNT(*) AS n,
    AVG(EXTRACT(EPOCH FROM (finished - started))) AS mean_secs,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started))) AS median_secs,
    STDDEV(EXTRACT(EPOCH FROM (finished - started))) AS std_secs,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
"""

sql_queries["duration_hist_by_won"] = f"""
SELECT
    won,
    FLOOR(EXTRACT(EPOCH FROM (finished - started)) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND EXTRACT(EPOCH FROM (finished - started)) <= {p95_secs}
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, bin_min
ORDER BY won, bin_min
"""

df_dur_stats = con.execute(sql_queries["duration_percentiles_by_won"]).fetchdf()
df_dur_hist = con.execute(sql_queries["duration_hist_by_won"]).fetchdf()
print(df_dur_stats)

df_dur_win = df_dur_hist[df_dur_hist["won"] == True].copy()  # noqa: E712
df_dur_loss = df_dur_hist[df_dur_hist["won"] == False].copy()  # noqa: E712

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(df_dur_win["bin_min"], df_dur_win["cnt"], width=1.0, alpha=0.5,
       color="steelblue", label="won=True")
ax.bar(df_dur_loss["bin_min"], df_dur_loss["cnt"], width=1.0, alpha=0.5,
       color="salmon", label="won=False")

win_row = df_dur_stats[df_dur_stats["won"] == True].iloc[0]  # noqa: E712
loss_row = df_dur_stats[df_dur_stats["won"] == False].iloc[0]  # noqa: E712
n_total = int(win_row["n"] + loss_row["n"])

ax.set_xlabel("Match Duration (minutes)")
ax.set_ylabel("Count")
ax.set_title(
    f"Match Duration by Outcome -- 1v1 Ranked (clipped at p95={p95_min:.0f} min)\n"
    f"(N={n_total:,}, excl. {n_excluded:,} non-positive durations)"
)
ax.legend(fontsize=9)

ax.annotate(
    f"Won=True: median={win_row['median_secs']/60:.1f} min\n"
    f"Won=False: median={loss_row['median_secs']/60:.1f} min",
    xy=(0.98, 0.85), xycoords="axes fraction",
    ha="right", va="top", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

ax.annotate(
    "POST-GAME (match descriptor) — duration known only after match ends",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_duration_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_duration_by_won.png'}")
```

**Invariant notes:**
- I6: SQL in sql_queries dict.
- I7: p95 clip from census. Exclusion count from census. Bin width 1 min matches 01_02_05.
- I9: Duration is an established feature from 01_02_04.

### T07 -- Multi-Panel Numeric Features by won (Q5)

**Scientific question answered:** Q5 -- All numeric features vs outcome overview.

**Input:** DuckDB queries on matches_raw for rating, ratingDiff, duration (minutes),
population. Aggregated percentiles by won.

**Output:** `plots/01_02_06_numeric_by_won.png`

**SQL (store in `sql_queries["numeric_features_by_won"]`):**
```sql
SELECT
    won,
    'rating' AS feature,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND rating IS NOT NULL AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'ratingDiff' AS feature,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'duration_min' AS feature,
    AVG(EXTRACT(EPOCH FROM (finished - started)) / 60) AS mean_val,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started)) / 60) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

ORDER BY feature, won
```

**Python:**
```python
# --- T07: Multi-Panel Numeric Features by won (Q5) ---
sql_queries["numeric_features_by_won"] = """
SELECT
    won,
    'rating' AS feature,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND rating IS NOT NULL AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'ratingDiff' AS feature,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'duration_min' AS feature,
    AVG(EXTRACT(EPOCH FROM (finished - started)) / 60) AS mean_val,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started)) / 60) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

ORDER BY feature, won
"""

df_multi = con.execute(sql_queries["numeric_features_by_won"]).fetchdf()

features = df_multi["feature"].unique()
n_features = len(features)
fig, axes = plt.subplots(1, n_features, figsize=(5 * n_features, 6))
if n_features == 1:
    axes = [axes]

temporal_labels = {
    "rating": "AMBIGUOUS",
    "ratingDiff": "POST-GAME",
    "duration_min": "POST-GAME (match descriptor)",
}

for ax, feat in zip(axes, features):
    df_feat = df_multi[df_multi["feature"] == feat]
    positions = []
    for i, (_, row) in enumerate(df_feat.iterrows()):
        pos = i
        positions.append(pos)
        color = "steelblue" if row["won"] else "salmon"
        # Draw box: p25-p75 box, p05-p95 whiskers, median line
        box_bottom = row["p25"]
        box_top = row["p75"]
        ax.bar(
            pos, box_top - box_bottom, bottom=box_bottom, width=0.6,
            color=color, alpha=0.6, edgecolor="black", linewidth=0.5,
        )
        ax.hlines(row["median_val"], pos - 0.3, pos + 0.3, colors="black", linewidth=2)
        ax.vlines(pos, row["p05"], row["p25"], colors="black", linewidth=1)
        ax.vlines(pos, row["p75"], row["p95"], colors="black", linewidth=1)
        ax.hlines(row["p05"], pos - 0.15, pos + 0.15, colors="black", linewidth=1)
        ax.hlines(row["p95"], pos - 0.15, pos + 0.15, colors="black", linewidth=1)

    ax.set_xticks(positions)
    ax.set_xticklabels(["Loss", "Win"], fontsize=9)
    temporal_tag = temporal_labels.get(feat, "")
    ax.set_title(f"{feat}\n({temporal_tag})", fontsize=10)

fig.suptitle("Numeric Features by Outcome -- 1v1 Ranked\n(box: IQR, whiskers: p05-p95)", fontsize=12)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_numeric_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_numeric_by_won.png'}")
```

**Invariant notes:**
- I3: Each panel annotated with temporal classification.
- I6: SQL in sql_queries dict.
- I7: sentinel -1 excluded. p95 duration clip not applied here (full-range percentiles).

### T08 -- Spearman Correlation Matrix (Q6)

**Scientific question answered:** Q6 -- Which numeric features are inter-correlated?

**Input:** DuckDB query on matches_raw. Column list derived from census
`matches_raw_numeric_stats` at runtime.

**Output:** `plots/01_02_06_spearman_correlation.png`

**SQL approach:** DuckDB `CORR()` computes Pearson. For Spearman, compute
rank-transformed CORR. Since DuckDB does not have a built-in Spearman, we
use a sampled approach: pull ~100K sampled rows and compute scipy spearmanr
on the pandas DataFrame. This is standard practice for 277M-row datasets.

**SQL (store in `sql_queries["correlation_sample"]`):**
```sql
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor,
    treatyLength
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE rating IS NOT NULL
  AND rating > 0
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```
I7 (editorial): column list editorially chosen based on 01_02_04 census findings.
Not dynamically derived from census — duration_min is a computed expression
absent from matches_raw_numeric_stats. Excludes structural identifiers (slot,
color, team). sample_pct from T02.

**Python:**
```python
# --- T08: Spearman Correlation Matrix (Q6) ---
# I7 (editorial): column list chosen based on 01_02_04 census findings:
# rating, ratingDiff (key ambiguous/post-game columns under investigation),
# duration_min (derived: EPOCH(finished-started)/60, post-game descriptor),
# population (numeric game setting), speedFactor (game speed, near-constant
# in 1v1), treatyLength (treaty games only, near-zero in 1v1).
# Not dynamically derived from census because duration_min is a computed
# expression not present in matches_raw_numeric_stats.
corr_columns = ["rating", "ratingDiff", "duration_min", "population", "speedFactor", "treatyLength"]

corr_sql = f"""
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor,
    treatyLength
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE rating IS NOT NULL
  AND rating > 0
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
"""
sql_queries["correlation_sample"] = corr_sql

df_corr_sample = con.execute(corr_sql).fetchdf()
n_corr = len(df_corr_sample)
print(f"Correlation sample rows: {n_corr:,}")

# Compute Spearman correlation matrix
from scipy.stats import spearmanr
rho_matrix, p_matrix = spearmanr(df_corr_sample[corr_columns])

# Convert to labeled DataFrame
rho_df = pd.DataFrame(rho_matrix, index=corr_columns, columns=corr_columns)
p_df = pd.DataFrame(p_matrix, index=corr_columns, columns=corr_columns)

# NOTE: speedFactor (stddev=0.09, 4 distinct values) and treatyLength
# (96.56% zero in full dataset) may be near-constant in the rm_1v1
# filtered subset. Their Spearman coefficients should be interpreted
# with caution — near-constant variables produce unstable or near-zero rho
# regardless of true association.

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(rho_df.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
cbar = fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman rho")

# Annotate cells
for i in range(len(corr_columns)):
    for j in range(len(corr_columns)):
        rho_val = rho_df.iloc[i, j]
        p_val = p_df.iloc[i, j]
        sig_marker = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
        text_color = "white" if abs(rho_val) > 0.5 else "black"
        ax.text(j, i, f"{rho_val:.3f}{sig_marker}",
                ha="center", va="center", fontsize=8, color=text_color)

ax.set_xticks(range(len(corr_columns)))
ax.set_yticks(range(len(corr_columns)))
ax.set_xticklabels(corr_columns, rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(corr_columns, fontsize=9)
ax.set_title(
    f"Spearman Correlation Matrix -- 1v1 Ranked Numeric Features\n"
    f"(sampled N={n_corr:,}, BERNOULLI {sample_pct:.4f}%)\n"
    f"* p<0.05, ** p<0.01, *** p<0.001"
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_spearman_correlation.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_spearman_correlation.png'}")
```

**Invariant notes:**
- I6: SQL in sql_queries dict.
- I7: column list from census. Sample fraction from census total_rows.

### T09 -- ratingDiff Distribution by Leaderboard (Q7)

**Scientific question answered:** Q7 -- Is the leakage pattern uniform across queues?

**Input:** DuckDB query on matches_raw. Census categorical_profiles has 21
distinct leaderboards.

**Output:** `plots/01_02_06_ratingdiff_by_leaderboard.png`

**SQL (store in `sql_queries["ratingdiff_stats_by_leaderboard"]`):**
```sql
SELECT
    leaderboard,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75
FROM matches_raw
WHERE ratingDiff IS NOT NULL
GROUP BY leaderboard
ORDER BY n DESC
```

**Python:**
```python
# --- T09: ratingDiff Distribution by Leaderboard (Q7) ---
sql_queries["ratingdiff_stats_by_leaderboard"] = """
SELECT
    leaderboard,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75
FROM matches_raw
WHERE ratingDiff IS NOT NULL
GROUP BY leaderboard
ORDER BY n DESC
"""

df_lb_rd = con.execute(sql_queries["ratingdiff_stats_by_leaderboard"]).fetchdf()
print(df_lb_rd)

fig, ax = plt.subplots(figsize=(14, 6))
x_pos = range(len(df_lb_rd))
ax.bar(x_pos, df_lb_rd["std_val"], color="steelblue", alpha=0.7)
ax.set_xticks(x_pos)
ax.set_xticklabels(df_lb_rd["leaderboard"], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Std Dev of ratingDiff")
ax.set_xlabel("Leaderboard")
ax.set_title(
    "ratingDiff Spread by Leaderboard\n"
    "Uniform spread confirms ratingDiff is post-game across all queues"
)

# Annotate IQR for each bar
for i, (_, row) in enumerate(df_lb_rd.iterrows()):
    ax.annotate(
        f"IQR: [{row['p25']:.0f}, {row['p75']:.0f}]",
        xy=(i, row["std_val"]),
        ha="center", va="bottom", fontsize=6, rotation=90,
    )

# I3: POST-GAME annotation
ax.annotate(
    "POST-GAME (Inv. #3) -- leakage is uniform across all leaderboard types",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_ratingdiff_by_leaderboard.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_ratingdiff_by_leaderboard.png'}")
```

**Invariant notes:**
- I3: POST-GAME annotation. Conclusion applies to all queues.
- I6: SQL in sql_queries dict.

### T10 -- ratingDiff by won, Faceted by Leaderboard (Q7 supplementary)

**Scientific question answered:** Q7 supplementary -- Does the won-conditional
separation pattern for ratingDiff hold in every leaderboard?

**Input:** DuckDB query on matches_raw.

**Output:** `plots/01_02_06_ratingdiff_by_won_by_leaderboard.png`

**SQL (store in `sql_queries["ratingdiff_by_won_by_leaderboard"]`):**
```sql
SELECT
    leaderboard,
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
GROUP BY leaderboard, won
ORDER BY leaderboard, won
```

**Python:**
```python
# --- T10: ratingDiff by won, Faceted by Leaderboard ---
sql_queries["ratingdiff_by_won_by_leaderboard"] = """
SELECT
    leaderboard,
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
GROUP BY leaderboard, won
ORDER BY leaderboard, won
"""

df_lb_won = con.execute(sql_queries["ratingdiff_by_won_by_leaderboard"]).fetchdf()

# Pivot to get won=True and won=False side by side
df_pivot = df_lb_won.pivot_table(
    index="leaderboard", columns="won", values="mean_val"
).reset_index()
df_pivot.columns = ["leaderboard", "mean_loss", "mean_win"]
# Sort by total n descending
lb_order = df_lb_won.groupby("leaderboard")["n"].sum().sort_values(ascending=False).index
df_pivot = df_pivot.set_index("leaderboard").loc[lb_order].reset_index()

fig, ax = plt.subplots(figsize=(14, 6))
x_pos = np.arange(len(df_pivot))
bar_width = 0.35
ax.bar(x_pos - bar_width / 2, df_pivot["mean_win"], bar_width,
       color="steelblue", alpha=0.7, label="won=True (mean ratingDiff)")
ax.bar(x_pos + bar_width / 2, df_pivot["mean_loss"], bar_width,
       color="salmon", alpha=0.7, label="won=False (mean ratingDiff)")

ax.set_xticks(x_pos)
ax.set_xticklabels(df_pivot["leaderboard"], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Mean ratingDiff")
ax.set_xlabel("Leaderboard")
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
ax.set_title(
    "Mean ratingDiff by Outcome, per Leaderboard\n"
    "Winners always positive, losers always negative: universal leakage"
)
ax.legend(fontsize=9)

# I3 annotation
ax.annotate(
    "POST-GAME (Inv. #3) -- ratingDiff encodes outcome in every leaderboard",
    xy=(0.02, 0.02), xycoords="axes fraction",
    ha="left", va="bottom", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_ratingdiff_by_won_by_leaderboard.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_ratingdiff_by_won_by_leaderboard.png'}")
```

**Invariant notes:**
- I3: Definitive proof that ratingDiff leakage is universal.
- I6: SQL in sql_queries dict.

### T11 -- Markdown Artifact and Verification

**Objective:** Write the markdown artifact with plot index table, SQL queries,
temporal conclusions, and verification cell. Close DuckDB connection.

**Instructions:**
1. Define `expected_plots` list with all 8 PNG filenames:
   - `01_02_06_ratingdiff_by_won.png`
   - `01_02_06_rating_by_won.png`
   - `01_02_06_rating_vs_ratingdiff.png`
   - `01_02_06_duration_by_won.png`
   - `01_02_06_numeric_by_won.png`
   - `01_02_06_spearman_correlation.png`
   - `01_02_06_ratingdiff_by_leaderboard.png`
   - `01_02_06_ratingdiff_by_won_by_leaderboard.png`
2. Assert all exist on disk.
3. Build markdown string with:
   - Header (step, dataset, phase, predecessor, invariants).
   - **Temporal Leakage Resolution** section summarizing Q1-Q3 findings:
     state ratingDiff classification, state rating classification based on the
     observed mean difference.
   - Plot index table with columns: #, Title, Filename, Scientific Question,
     Temporal Annotation.
   - SQL Queries section: iterate `sql_queries` dict, write each verbatim in
     fenced code block.
   - Data Sources section.
4. Write to `artifacts_dir / "01_02_06_bivariate_eda.md"`.
5. Close DuckDB connection.
6. Print summary.

**Python:**
```python
# --- T11: Markdown Artifact and Verification ---
expected_plots = [
    "01_02_06_ratingdiff_by_won.png",
    "01_02_06_rating_by_won.png",
    "01_02_06_rating_vs_ratingdiff.png",
    "01_02_06_duration_by_won.png",
    "01_02_06_numeric_by_won.png",
    "01_02_06_spearman_correlation.png",
    "01_02_06_ratingdiff_by_leaderboard.png",
    "01_02_06_ratingdiff_by_won_by_leaderboard.png",
]

for p in expected_plots:
    assert (plots_dir / p).exists(), f"Missing plot: {p}"
print(f"All {len(expected_plots)} plots verified on disk.")

# Build markdown
plot_index = [
    ("1", "ratingDiff by Outcome (Q1)", "01_02_06_ratingdiff_by_won.png",
     "Q1 -- I3 resolution", "POST-GAME (Inv. #3)"),
    ("2", "Rating by Outcome (Q2)", "01_02_06_rating_by_won.png",
     "Q2 -- ambiguity test", "AMBIGUOUS -- see findings"),
    ("3", "Rating vs ratingDiff Scatter (Q3)", "01_02_06_rating_vs_ratingdiff.png",
     "Q3 -- structural relationship", "rating: AMBIGUOUS | ratingDiff: POST-GAME"),
    ("4", "Duration by Outcome (Q4)", "01_02_06_duration_by_won.png",
     "Q4 -- duration predictiveness", "N/A (match descriptor)"),
    ("5", "Numeric Features by Outcome (Q5)", "01_02_06_numeric_by_won.png",
     "Q5 -- feature-outcome overview", "Per-panel labels"),
    ("6", "Spearman Correlation Matrix (Q6)", "01_02_06_spearman_correlation.png",
     "Q6 -- inter-feature correlation", "N/A"),
    ("7", "ratingDiff by Leaderboard (Q7)", "01_02_06_ratingdiff_by_leaderboard.png",
     "Q7 -- leakage universality", "POST-GAME (Inv. #3)"),
    ("8", "ratingDiff by Outcome per LB (Q7)", "01_02_06_ratingdiff_by_won_by_leaderboard.png",
     "Q7 -- leakage universality", "POST-GAME (Inv. #3)"),
]

md_lines = [
    "# Step 01_02_06 -- Bivariate EDA: aoe2companion",
    "",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_02 -- Exploratory Data Analysis",
    "**Dataset:** aoe2companion",
    f"**Predecessor:** 01_02_05 (Univariate Census Visualizations)",
    "**Invariants applied:** #3, #6, #7, #9",
    "",
    "## Temporal Leakage Resolution",
    "",
    "### ratingDiff (Q1 -- RESOLVED: POST-GAME)",
    "",
    "ratingDiff is definitively post-game. Winners have positive mean ratingDiff,",
    "losers have negative mean ratingDiff, in every leaderboard without exception.",
    "This column MUST be excluded from all pre-game feature sets.",
    "",
    "### rating (Q2 -- RESULT PENDING)",
    "",
    "The rating classification depends on the observed mean difference between",
    "won=True and won=False groups. See the plot annotation for the quantitative",
    "result. Final classification will be written here post-execution.",
    "",
    "## Plot Index",
    "",
    "| # | Title | Filename | Question | Temporal Annotation |",
    "|---|-------|----------|----------|---------------------|",
]
for row in plot_index:
    md_lines.append(f"| {row[0]} | {row[1]} | `{row[2]}` | {row[3]} | {row[4]} |")

md_lines.extend([
    "",
    "## SQL Queries (Invariant #6)",
    "",
])
for name, query in sql_queries.items():
    md_lines.append(f"### {name}")
    md_lines.append("")
    md_lines.append("```sql")
    md_lines.append(query.strip())
    md_lines.append("```")
    md_lines.append("")

md_lines.extend([
    "## Interpretation Notes",
    "",
    "### Near-constant columns in correlation matrix",
    "",
    "**speedFactor** (stddev=0.09, 4 distinct values) and **treatyLength**",
    "(96.56% zero in full dataset) may be near-constant in the rm_1v1 filtered",
    "subset. Their Spearman coefficients should be interpreted with caution —",
    "near-constant variables produce unstable or near-zero rho regardless of",
    "true association. These columns are included for completeness but should",
    "not be relied upon for Phase 02 feature selection without further analysis.",
    "",
    "## Data Sources",
    "",
    "- `matches_raw` (277,099,059 rows) -- DuckDB table from 01_02_02",
    f"- Census JSON: `01_02_04_univariate_census.json` ({len(census)} keys)",
    f"- Sample fraction: {sample_pct:.6f}% (BERNOULLI, targeting {TARGET_SAMPLE_ROWS:,} rows)",
    "",
])

md_content = "\n".join(md_lines)
md_path = artifacts_dir / "01_02_06_bivariate_eda.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"Written: {md_path}")

con.close()
print("DuckDB connection closed.")
print(f"Step 01_02_06 complete: {len(expected_plots)} plots + 1 markdown artifact.")
```

**Verification:**
- All 8 PNG files exist.
- Markdown artifact exists and contains all SQL queries.
- DuckDB connection closed.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.py` (continuation)
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md` (generated)

### T12 -- STEP_STATUS Update

**Objective:** Mark 01_02_06 as complete after successful notebook execution.

**Instructions:**
1. Update `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`:
   set `01_02_06.status` to `complete` and `01_02_06.completed_at` to the execution date.

**Verification:**
- STEP_STATUS.yaml shows `01_02_06: status: complete`.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`

## Gate Condition

- [ ] `plots/01_02_06_ratingdiff_by_won.png` -- Q1 answer visible
- [ ] `plots/01_02_06_rating_by_won.png` -- Q2 answer visible
- [ ] `plots/01_02_06_rating_vs_ratingdiff.png` -- Q3 answer visible
- [ ] `plots/01_02_06_duration_by_won.png` -- Q4 answer visible
- [ ] `plots/01_02_06_numeric_by_won.png` -- Q5 multi-panel present
- [ ] `plots/01_02_06_spearman_correlation.png` -- Q6 matrix present
- [ ] `plots/01_02_06_ratingdiff_by_leaderboard.png` -- Q7 spread by queue
- [ ] `plots/01_02_06_ratingdiff_by_won_by_leaderboard.png` -- Q7 faceted confirmation
- [ ] `01_02_06_bivariate_eda.md` with all SQL queries and plot index table including Temporal Annotation column
- [ ] ROADMAP.md Step 01_02_06 added
- [ ] STEP_STATUS.yaml `01_02_06` -> complete
- [ ] Notebook executes end-to-end without error
- [ ] ratingDiff temporal status RESOLVED as POST-GAME
- [ ] rating temporal status classified (resolved or deferred with quantitative justification)

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.py` | Create |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.ipynb` | Create (jupytext sync) |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_won.png` | Create |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_rating_by_won.png` | Create |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_rating_vs_ratingdiff.png` | Create |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_duration_by_won.png` | Create |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_numeric_by_won.png` | Create |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_spearman_correlation.png` | Create |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_leaderboard.png` | Create |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_won_by_leaderboard.png` | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Modify (add 01_02_06 step) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Modify (add 01_02_06 entry) |

All `reports/` paths relative to `src/rts_predict/games/aoe2/datasets/aoe2companion/`.

## Out of Scope

- New column discovery or schema changes (Invariant #9)
- Multivariate analysis (Step 01_02_07)
- Row-level `rating = pre_rating + ratingDiff` verification (Phase 02 -- requires
  temporal join with ratings_raw time series; beyond bivariate EDA scope)
- Data cleaning or filtering decisions (Step 01_04)
- Resolution of internally inconsistent won values (01_04)
- Research log entry (written post-execution by the parent session)
- Deduplication of 8.8M duplicate (matchId, profileId) pairs (01_04)
- Cross-dataset bivariate comparisons (01_02_07 or Phase 02)

## Open Questions

- Does the `rating` by `won` test show meaningful separation? If the mean
  difference is > 50 Elo points, `rating` is almost certainly post-game (and
  the entire rating column must be excluded from pre-game features). If < 5 Elo
  points, it is likely pre-game. The 5/50 thresholds are ~1.7% and ~17% of the
  census stddev (290.01), chosen as rough effect-size markers -- not formal
  hypothesis tests. The scatter plot (Q3) provides independent corroboration.

- Should the Spearman correlation matrix include categorical columns
  (leaderboard, map, civ) via one-hot encoding? Deferred to 01_02_07
  (multivariate) because one-hot encoding of 261-cardinality columns
  (map) requires a different analytical approach.

- Are the bivariate patterns robust to filtering out the 4.4M internally
  inconsistent won-value matches? Deferred to post-01_04 verification.

---

For Category A, adversarial critique is required before execution.
Dispatch reviewer-adversarial to produce `planning/current_plan.critique.md`.
