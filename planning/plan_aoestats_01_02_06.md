---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: aoestats
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
critique_required: true
---

# Plan: aoestats Step 01_02_06 -- Bivariate EDA

## Scope

**Phase/Step:** 01 / 01_02_06
**Branch:** feat/census-pass3
**Action:** CREATE (step does not yet exist in ROADMAP; must be added as T01)
**Predecessor:** 01_02_05 (Univariate Visualizations -- complete, artifacts on disk)

Create a bivariate EDA notebook that investigates pairwise relationships between
features and the target variable (`winner`), resolves the `match_rating_diff`
leakage question (Phase 02 BLOCKER), and produces a Spearman correlation matrix.
8 thesis-grade PNG plots + 1 JSON artifact + 1 markdown artifact with all SQL
queries (Invariant #6).

## Problem Statement

Step 01_02_04/05 established univariate distributions for all columns in
matches_raw (30.7M rows, 18 cols) and players_raw (107.6M rows, 14 cols).
Several questions cannot be answered from univariate analysis alone:

1. **match_rating_diff leakage (BLOCKER):** The census found `match_rating_diff`
   in players_raw with mean=0.0, stddev=55.23, kurtosis=65.68. It could be
   `new_rating - old_rating` (post-game -- LEAKAGE) or an opponent-relative
   pre-game rating gap (SAFE). Phase 02 feature engineering is blocked until
   this is resolved. Resolution requires computing `new_rating - old_rating`
   per player row and comparing against `match_rating_diff`.

2. **Feature-target associations:** Do pre-game features (old_rating, avg_elo,
   team_0_elo, team_1_elo) show distributional differences conditioned on
   winner? How much predictive signal exists before modelling?

3. **Correlation structure:** Are numeric features highly correlated (e.g.,
   old_rating vs avg_elo), suggesting redundancy for feature selection?

**Critical schema correction:** The user's prompt proposed a matches_raw JOIN
players_raw approach for the leakage scatter. However, `match_rating_diff` does
NOT exist in matches_raw (18 columns per schema YAML). It exists ONLY in
players_raw (alongside `old_rating`, `new_rating`, `winner`, `game_id`). The
leakage check is therefore a single-table comparison on players_raw: compare
`match_rating_diff` to `new_rating - old_rating` per player row. No cross-table
JOIN is needed for the leakage scatter itself.

## Assumptions & Unknowns

- The census JSON at `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the single source of truth for all derived thresholds.
- `match_rating_diff` is per-player (in players_raw), not per-match.
- Duration column in DuckDB is BIGINT nanoseconds -- requires `duration / 1e9`
  for conversion to seconds (established in 01_02_05).
- ELO sentinel -1 affects <0.001% of team_0/team_1_elo rows (34 + 39 rows);
  must be excluded in bivariate ELO plots.
- Age uptime and opening columns are ~87% NULL (schema change boundary);
  bivariate analysis uses only the ~14% non-NULL subset.
- For violin/box plots of large tables, DuckDB PERCENTILE_CONT aggregation
  produces percentile data for plotting rather than exporting raw rows.
  However, DuckDB can also compute violin-style density via width_bucket +
  COUNT(*) GROUP BY, which is more memory-efficient. We use the bucket approach.

**Unknown:** The exact semantics of `match_rating_diff`. The most likely
hypotheses are:
- H1: `match_rating_diff = new_rating - old_rating` (post-game rating change; LEAKAGE)
- H2: `match_rating_diff = player_rating - opponent_rating` (pre-game; SAFE)
- H3: Something else entirely

If H1, `match_rating_diff` must be excluded from all feature sets.
If H2, it is a high-value pre-game feature.
The leakage scatter (Q3) will distinguish these.

## Literature Context

Bivariate EDA follows Tukey (1977) and Wickham's modern operationalization
("R for Data Science"): "What type of covariation occurs between my variables?"
This is the second of Wickham's two foundational EDA questions, which maps to
the bivariate layer in the standard univariate -> bivariate -> multivariate
progression (01_DATA_EXPLORATION_MANUAL.md, Section 2.1).

Tools per the manual: scatterplots, correlation coefficients (Spearman for
monotonic relationships in non-normal data), conditional boxplots/violins.
Spearman is preferred over Pearson because several features have extreme
kurtosis (match_rating_diff: 65.7, duration: 2.8M) and non-linear
relationships are expected.

## Scientific Questions

**Q1 (cross-dataset mandatory): Numeric features conditioned on winner.**
For each numeric pre-game feature in players_raw (old_rating) and matches_raw
(avg_elo, team_0_elo, team_1_elo), does the distribution differ by winner?
This directly measures pre-game predictive signal strength.

**Q2 (cross-dataset mandatory): Spearman correlation matrix.**
What are the pairwise Spearman rank correlations among all numeric columns?
Are old_rating and avg_elo near-perfectly correlated (suggesting one is
redundant)? Does match_rating_diff correlate with old_rating (expected if it
encodes pre-game skill difference)?

**Q3 (aoestats-specific -- HIGHEST PRIORITY -- Phase 02 BLOCKER):
match_rating_diff leakage resolution.**
Does `match_rating_diff` equal `new_rating - old_rating` (post-game leakage)?
Scatter plot of `match_rating_diff` vs `new_rating - old_rating` per player row
in players_raw, with Pearson r and OLS fit line. If r ~= 1.0 and slope ~= 1.0,
then H1 is confirmed and the column is LEAKAGE. If r is low or the relationship
is non-linear, the column may encode something else.

**Q4 (aoestats-specific): old_rating by winner.**
Does pre-game rating (old_rating, the authoritative pre-game rating column)
differ between winners and losers? This is the baseline pre-game signal --
the feature most likely to predict match outcome. Violin plot split by winner.

**Q5 (aoestats-specific): Duration by winner.**
Does match duration differ by winner (team 0 vs team 1)? Note: duration is
POST-GAME (Invariant #3) but the bivariate relationship is still informative
for understanding game dynamics. Annotated POST-GAME.

**Q6 (aoestats-specific): ELO values by winner.**
Do team_0_elo, team_1_elo, avg_elo differ by winner? Panel violin with
sentinel -1 excluded. Note: since winner is per-player (in players_raw) and
ELO is per-match (in matches_raw), this requires a JOIN.

**Q7 (aoestats-specific): Opening strategy and win rate.**
Among the ~14% of rows with non-NULL opening, what is the win rate per opening
strategy? Top-20 openings by count, bar chart of win rate. Annotated IN-GAME
(Invariant #3).

**Q8 (aoestats-specific): Age uptime by winner.**
Do feudal/castle/imperial age uptimes differ between winners and losers?
Violin panel, non-NULL rows only. Annotated IN-GAME.

## Part A -- ROADMAP Patch

**Action:** INSERT new Step 01_02_06 block into ROADMAP.md between 01_02_05
and the Phase 02 placeholder.

```yaml
step_number: "01_02_06"
name: "Bivariate EDA"
description: "Bivariate EDA for aoestats: 8 plots investigating pairwise feature-target relationships. Resolves match_rating_diff leakage (Phase 02 blocker). Conditional distributions by winner, Spearman correlation matrix, opening win rates. All SQL embedded (Invariant #6). Temporal annotations on in-game and post-game columns (Invariant #3)."
phase: "01 -- Data Exploration"
pipeline_section: "01_02 -- Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
dataset: "aoestats"
question: "How do pairs of variables relate to each other and to the target (winner)? Is match_rating_diff a post-game leakage feature?"
method: "Single-table and JOIN queries on DuckDB. Sampled scatter for leakage check. DuckDB width_bucket aggregation for violin-style density estimation. Spearman matrix via DuckDB corr(). All thresholds from census JSON."
stratification: "By table (matches_raw, players_raw) and by target (winner True/False)."
predecessors:
  - "01_02_05"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_05_visualizations.md"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_06_match_rating_diff_leakage_scatter.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_old_rating_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_elo_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_duration_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_numeric_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_opening_winrate.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_age_uptime_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_spearman_correlation.png"
  report: "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "duration annotated POST-GAME. opening and age uptimes annotated IN-GAME. match_rating_diff leakage status resolved by scatter and updated to LEAKAGE or PRE-GAME accordingly."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All sample fractions, bin widths, sentinel exclusion thresholds derived from census JSON at runtime. Sample size justified by census row count."
  - number: "9"
    how_upheld: "Bivariate analysis only. No model fitting, no feature engineering, no cleaning decisions."
gate:
  artifact_check: "All 8 PNG files exist under plots/. 01_02_06_bivariate_eda.json and .md exist and are non-empty."
  continue_predicate: "All 8 PNG files exist. match_rating_diff leakage status resolved in JSON artifact (field: bivariate_results[\"match_rating_diff_leakage\"][\"leakage_status\"] = 'LEAKAGE' or 'PRE_GAME'). Markdown artifact contains all SQL queries and plot index table with Temporal Annotation column. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails or match_rating_diff leakage status cannot be determined."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
  - "Chapter 4 -- Data and Methodology > 4.2 Pre-processing"
research_log_entry: "Required on completion."
```

## Part B -- Notebook Task List

### T01 -- ROADMAP Patch

**Objective:** Add the Step 01_02_06 definition to ROADMAP.md.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`.
2. INSERT the Step 01_02_06 YAML block from Part A above, after the
   Step 01_02_05 block and before the `---` separator line that precedes
   Phase 02.

**Verification:**
- ROADMAP.md contains a Step 01_02_06 block listing 8 PNG outputs.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`

### T02 -- Notebook Setup

**Objective:** Create the notebook skeleton with imports, DuckDB connection,
census JSON loading, and path configuration.

**Instructions:**
1. Create `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.py`
   with jupytext percent-format header.
2. Markdown header cell: Step 01_02_06, dataset, phase, question, invariants,
   predecessor.
3. Imports:
```python
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOESTATS_DB_FILE

matplotlib.use("Agg")
logger = setup_notebook_logging(__name__)
```
4. Connect to DuckDB read-only:
```python
conn = duckdb.connect(str(AOESTATS_DB_FILE), read_only=True)
```
5. Load census JSON:
```python
reports_dir = get_reports_dir("aoe2", "aoestats")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

census_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_path) as f:
    census = json.load(f)
```
6. Assert required census keys:
```python
required_keys = [
    "winner_distribution", "numeric_stats_matches", "numeric_stats_players",
    "elo_sentinel_counts", "players_null_census", "matches_null_census",
    "categorical_players", "opening_nonnull_distribution",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"
```
7. Initialize dictionaries:
```python
sql_queries = {}
bivariate_results = {
    "step": "01_02_06",
    "dataset": "aoestats",
}
```

**Verification:**
- Notebook imports and runs through setup without error.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.py`

### T03 -- match_rating_diff Leakage Scatter (Q3 -- HIGHEST PRIORITY)

**Scientific question answered:** Q3 -- Is `match_rating_diff` a post-game
leakage feature?

**Input:** DuckDB query on players_raw only (both `match_rating_diff` and
`new_rating - old_rating` are in the same table).

**Output:** `plots/01_02_06_match_rating_diff_leakage_scatter.png`

**Rationale for single-table approach:** The user's prompt proposed a JOIN
between matches_raw and players_raw using `match_id`. However:
(a) The join key is `game_id`, not `match_id` (per schema YAML).
(b) `match_rating_diff` is in players_raw, NOT matches_raw (which has 18
columns, none named match_rating_diff).
(c) `new_rating` and `old_rating` are also in players_raw.
Therefore the leakage check is a single-table comparison: `match_rating_diff`
vs `new_rating - old_rating` per player row.

**SQL (store in sql_queries["leakage_scatter_sample"]):**
```sql
SELECT
    match_rating_diff,
    CAST(new_rating - old_rating AS DOUBLE) AS rating_delta
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND old_rating > 0
  AND new_rating > 0
USING SAMPLE RESERVOIR(200000)
```

I7 justification: Sample size 200,000 rows from 107.6M non-NULL rows = ~0.19%
sample. 200K is sufficient to establish Pearson r with negligible standard
error (SE ~= 1/sqrt(N) ~= 0.002). RESERVOIR sampling for exact count.
`old_rating > 0` excludes 5,937 zero-rated rows (census: `numeric_stats_players`
label `old_rating`, `n_zero=5937`). `new_rating > 0` excludes 5,187 zero-rated
rows (census label `new_rating`, `n_zero=5187`).

```python
# I7: old_rating > 0 excludes 5,937 zero-rated rows (census: n_zero=5937).
# Zero treated as unrated/new-player sentinel by domain convention (ELO
# systems assign zero before first rating calculation). Different from
# team_0_elo / team_1_elo sentinel of -1.0 (confirmed in census
# elo_sentinel_counts). The zero-exclusion assumption is domain-grounded,
# not arbitrary.
```

**SQL (store in sql_queries["leakage_exact_match_count"]):**
```sql
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN ABS(match_rating_diff - (new_rating - old_rating)) < 0.01
        THEN 1 ELSE 0 END) AS exact_match_count,
    ROUND(100.0 * SUM(CASE WHEN ABS(match_rating_diff - (new_rating - old_rating)) < 0.01
        THEN 1 ELSE 0 END) / COUNT(*), 4) AS exact_match_pct
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND old_rating > 0
  AND new_rating > 0
```

I7 justification: Tolerance 0.01 accounts for floating-point representation
(`match_rating_diff` is DOUBLE, `new_rating - old_rating` is BIGINT difference
cast to DOUBLE). This is run on the FULL table (not sampled) for a definitive
answer.

**Python (scatter plot):**
```python
# --- T03: match_rating_diff Leakage Scatter (Q3 -- BLOCKER) ---

# I7: old_rating > 0 excludes 5,937 zero-rated rows (census: n_zero=5937).
# Zero treated as unrated/new-player sentinel by domain convention (ELO
# systems assign zero before first rating calculation). Different from
# team_0_elo / team_1_elo sentinel of -1.0 (confirmed in census
# elo_sentinel_counts). The zero-exclusion assumption is domain-grounded,
# not arbitrary.

# Step 1: Full-table exact match count
sql_exact = """
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN ABS(match_rating_diff - (new_rating - old_rating)) < 0.01
        THEN 1 ELSE 0 END) AS exact_match_count,
    ROUND(100.0 * SUM(CASE WHEN ABS(match_rating_diff - (new_rating - old_rating)) < 0.01
        THEN 1 ELSE 0 END) / COUNT(*), 4) AS exact_match_pct
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND old_rating > 0
  AND new_rating > 0
"""
sql_queries["leakage_exact_match_count"] = sql_exact
exact_result = conn.execute(sql_exact).fetchdf()
print("Exact match census:")
print(exact_result.to_string(index=False))

total_rows = int(exact_result["total_rows"].iloc[0])
exact_match_count = int(exact_result["exact_match_count"].iloc[0])
exact_match_pct = float(exact_result["exact_match_pct"].iloc[0])

# Step 2: Sampled scatter data
sql_scatter = """
SELECT
    match_rating_diff,
    CAST(new_rating - old_rating AS DOUBLE) AS rating_delta
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND old_rating > 0
  AND new_rating > 0
USING SAMPLE RESERVOIR(200000)
"""
sql_queries["leakage_scatter_sample"] = sql_scatter
df_scatter = conn.execute(sql_scatter).fetchdf()

# Step 3: Compute Pearson r and OLS
pearson_r, pearson_p = sp_stats.pearsonr(
    df_scatter["match_rating_diff"], df_scatter["rating_delta"]
)
slope, intercept, r_value, p_value, std_err = sp_stats.linregress(
    df_scatter["match_rating_diff"], df_scatter["rating_delta"]
)

# Step 4: Determine leakage status
# I7: 0.99 = practical certainty threshold for N > 100M rows (Cohen 1988,
#     r > 0.9 = very large effect; 0.99 chosen as near-identity threshold)
LEAKAGE_R_THRESHOLD = 0.99
# I7: 99.0% exact match = near-identity relationship allowing for floating point
LEAKAGE_EXACT_MATCH_THRESHOLD = 99.0
# I7: slope within 0.05 of 1.0 = ±5% of identity slope (editorial)
LEAKAGE_SLOPE_TOLERANCE = 0.05
# I7: 0.3 = conventional "weak correlation" boundary (Cohen 1988)
PREGAME_R_THRESHOLD = 0.3

if exact_match_pct > LEAKAGE_EXACT_MATCH_THRESHOLD and abs(pearson_r) > LEAKAGE_R_THRESHOLD and abs(slope - 1.0) < LEAKAGE_SLOPE_TOLERANCE:
    leakage_status = "LEAKAGE"
    leakage_detail = (
        f"match_rating_diff = new_rating - old_rating in {exact_match_pct:.2f}% "
        f"of rows (Pearson r={pearson_r:.6f}, slope={slope:.6f}). "
        f"POST-GAME variable -- must exclude from all feature sets (Inv. #3)."
    )
elif abs(pearson_r) < PREGAME_R_THRESHOLD:
    leakage_status = "PRE_GAME"
    leakage_detail = (
        f"match_rating_diff does NOT correlate with new_rating - old_rating "
        f"(Pearson r={pearson_r:.4f}). Likely a pre-game feature."
    )
else:
    leakage_status = "AMBIGUOUS"
    leakage_detail = (
        f"Partial correlation (Pearson r={pearson_r:.4f}, slope={slope:.4f}, "
        f"exact_match={exact_match_pct:.2f}%). Manual investigation required."
    )

print(f"LEAKAGE STATUS: {leakage_status}")
print(f"Detail: {leakage_detail}")

bivariate_results["match_rating_diff_leakage"] = {
    "leakage_status": leakage_status,
    "detail": leakage_detail,
    "pearson_r": float(pearson_r),
    "pearson_p": float(pearson_p),
    "ols_slope": float(slope),
    "ols_intercept": float(intercept),
    "ols_r_squared": float(r_value ** 2),
    "exact_match_count": exact_match_count,
    "exact_match_pct": exact_match_pct,
    "total_rows_tested": total_rows,
    "sample_size_scatter": len(df_scatter),
}

# Step 5: Scatter plot
fig, ax = plt.subplots(figsize=(8, 8))

# Subsample for visual clarity (scatter with 200K points is dense)
# I7: 20K points is a common scatter plot ceiling for matplotlib rasterized
# rendering; beyond this, overplotting obscures density structure
# (Cleveland 1993, "Visualizing Data"). Not derived from census — editorial
# visualization choice.
PLOT_SAMPLE_SIZE = 20_000
plot_sample_size = min(PLOT_SAMPLE_SIZE, len(df_scatter))
plot_idx = np.random.default_rng(42).choice(len(df_scatter), plot_sample_size, replace=False)
ax.scatter(
    df_scatter["match_rating_diff"].iloc[plot_idx],
    df_scatter["rating_delta"].iloc[plot_idx],
    alpha=0.15, s=3, color="steelblue", rasterized=True,
)

# OLS fit line
x_range = np.array([df_scatter["match_rating_diff"].min(), df_scatter["match_rating_diff"].max()])
ax.plot(x_range, slope * x_range + intercept, color="red", linewidth=2, label="OLS fit")

# Identity line (y = x) for reference
ax.plot(x_range, x_range, color="gray", linewidth=1, linestyle="--", label="y = x")

ax.set_xlabel("match_rating_diff (players_raw)")
ax.set_ylabel("new_rating - old_rating (players_raw)")
ax.set_title(
    f"Leakage Check: match_rating_diff vs rating delta\n"
    f"(N={len(df_scatter):,} sampled; Pearson r={pearson_r:.4f}, "
    f"slope={slope:.4f}, intercept={intercept:.4f})"
)
ax.legend(loc="upper left")

# Leakage status annotation
annotation_color = "darkred" if leakage_status == "LEAKAGE" else "darkgreen"
annotation_bg = "#ffe0e0" if leakage_status == "LEAKAGE" else "#e0ffe0"
annotation_ec = "red" if leakage_status == "LEAKAGE" else "green"
ax.annotate(
    f"LEAKAGE STATUS: {leakage_status}\n"
    f"Exact match: {exact_match_pct:.2f}% of {total_rows:,} rows",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=9, fontstyle="italic", color=annotation_color,
    bbox=dict(boxstyle="round,pad=0.3", fc=annotation_bg, ec=annotation_ec, alpha=0.9),
)

fig.tight_layout()
fig.savefig(
    plots_dir / "01_02_06_match_rating_diff_leakage_scatter.png",
    dpi=150, bbox_inches="tight",
)
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_match_rating_diff_leakage_scatter.png'}")
```

**Invariant notes:**
- I3: Resolves leakage status. Annotation updated accordingly.
- I6: Both SQL queries stored in `sql_queries`.
- I7: Sample size 200K justified by SE ~= 0.002. Plot subsample 20K for
  visual clarity. Tolerance 0.01 for float comparison. `old_rating > 0`
  excludes 5,937 rows; `new_rating > 0` excludes 5,187 rows (from census).
- I9: Empirical leakage test only; no cleaning or feature engineering.

### T04 -- old_rating by Winner Violin (Q4)

**Scientific question answered:** Q4 -- Does pre-game rating predict outcome?

**Input:** DuckDB query on players_raw.

**Output:** `plots/01_02_06_old_rating_by_winner.png`

**SQL (store in sql_queries["old_rating_by_winner_buckets"]):**
```sql
SELECT
    winner,
    FLOOR(old_rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE old_rating > 0
GROUP BY winner, bin
ORDER BY winner, bin
```

I7 justification: bin width 25 ELO points (same as 01_02_05 univariate
histogram, ~0.09 stddev). Excludes 5,937 zero-rated rows.

**SQL (store in sql_queries["old_rating_by_winner_stats"]):**
```sql
SELECT
    winner,
    COUNT(*) AS n,
    ROUND(AVG(old_rating), 2) AS mean_val,
    ROUND(MEDIAN(old_rating), 2) AS median_val,
    ROUND(STDDEV(old_rating), 2) AS stddev_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS p75
FROM players_raw
WHERE old_rating > 0
GROUP BY winner
ORDER BY winner
```

**Python:**
```python
# --- T04: old_rating by Winner (Q4) ---

sql_bins = """
SELECT
    winner,
    FLOOR(old_rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE old_rating > 0
GROUP BY winner, bin
ORDER BY winner, bin
"""
sql_queries["old_rating_by_winner_buckets"] = sql_bins

sql_stats = """
SELECT
    winner,
    COUNT(*) AS n,
    ROUND(AVG(old_rating), 2) AS mean_val,
    ROUND(MEDIAN(old_rating), 2) AS median_val,
    ROUND(STDDEV(old_rating), 2) AS stddev_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS p75
FROM players_raw
WHERE old_rating > 0
GROUP BY winner
ORDER BY winner
"""
sql_queries["old_rating_by_winner_stats"] = sql_stats

df_bins = conn.execute(sql_bins).fetchdf()
df_stats = conn.execute(sql_stats).fetchdf()
print("old_rating by winner stats:")
print(df_stats.to_string(index=False))

bivariate_results["old_rating_by_winner"] = df_stats.to_dict(orient="records")

# Build overlapping histograms (pseudo-violin via mirrored histograms)
fig, ax = plt.subplots(figsize=(10, 6))
for winner_val, color, label in [(False, "salmon", "Loser"), (True, "steelblue", "Winner")]:
    subset = df_bins[df_bins["winner"] == winner_val]
    ax.step(
        subset["bin"], subset["cnt"],
        where="mid", color=color, alpha=0.7, linewidth=1.5, label=label,
    )
    ax.fill_between(subset["bin"], subset["cnt"], step="mid", alpha=0.2, color=color)

# Add median lines from stats
for _, row in df_stats.iterrows():
    label_text = "Winner" if row["winner"] else "Loser"
    ax.axvline(
        row["median_val"], linestyle="--", linewidth=1.5,
        color="steelblue" if row["winner"] else "salmon",
        label=f"{label_text} median={row['median_val']:.0f}",
    )

ax.set_xlabel("old_rating (ELO)")
ax.set_ylabel("Count per 25-ELO bin")
stats_w = df_stats[df_stats["winner"] == True].iloc[0]
stats_l = df_stats[df_stats["winner"] == False].iloc[0]
ax.set_title(
    f"Pre-Game Rating (old_rating) by Winner -- players_raw\n"
    f"Winner median={stats_w['median_val']:.0f} vs Loser median={stats_l['median_val']:.0f} "
    f"(diff={stats_w['median_val'] - stats_l['median_val']:.0f})"
)
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_old_rating_by_winner.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_old_rating_by_winner.png'}")
```

**Invariant notes:**
- I6: Both SQL queries stored.
- I7: bin width 25 from 01_02_05 precedent. Zero exclusion from census.

### T05 -- ELO by Winner Panel (Q6)

**Scientific question answered:** Q6 -- Do match-level ELO values differ by
winner?

**Input:** DuckDB JOIN query (matches_raw for ELO, players_raw for winner).
Since `winner` is in players_raw and ELO columns are in matches_raw, a JOIN
on `game_id` is required. To avoid the full 107.6M-row JOIN, aggregate winner
at match level first (compute which team won), then join.

**Output:** `plots/01_02_06_elo_by_winner.png`

**SQL (store in sql_queries["elo_by_winner_buckets"]):**
```sql
WITH match_winner AS (
    SELECT
        game_id,
        -- For each match, determine winning team's perspective
        -- winner=True player exists, so we can identify winning team
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    FLOOR(m.avg_elo / 25) * 25 AS avg_elo_bin,
    FLOOR(CASE WHEN m.team_0_elo > 0 THEN m.team_0_elo END / 25) * 25 AS t0_elo_bin,
    FLOOR(CASE WHEN m.team_1_elo > 0 THEN m.team_1_elo END / 25) * 25 AS t1_elo_bin,
    COUNT(*) AS cnt
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.avg_elo > 0
  AND m.team_0_elo > 0
  AND m.team_1_elo > 0
GROUP BY mw.winning_team, avg_elo_bin, t0_elo_bin, t1_elo_bin
ORDER BY mw.winning_team, avg_elo_bin
```

NOTE: This query is complex and may be slow on 30.7M rows. A simpler approach
is to query the ELO difference (team_0_elo - team_1_elo) conditioned on which
team won:

**SQL (store in sql_queries["elo_diff_by_winning_team"]):**
```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    FLOOR((m.team_0_elo - m.team_1_elo) / 10) * 10 AS elo_diff_bin,
    COUNT(*) AS cnt
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.team_0_elo > 0
  AND m.team_1_elo > 0
GROUP BY mw.winning_team, elo_diff_bin
ORDER BY mw.winning_team, elo_diff_bin
```

**SQL (store in sql_queries["elo_by_winning_team_stats"]):**
```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    ROUND(AVG(m.team_0_elo), 2) AS mean_t0_elo,
    ROUND(AVG(m.team_1_elo), 2) AS mean_t1_elo,
    ROUND(AVG(m.avg_elo), 2) AS mean_avg_elo,
    ROUND(AVG(m.team_0_elo - m.team_1_elo), 2) AS mean_elo_diff,
    COUNT(*) AS n
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.team_0_elo > 0
  AND m.team_1_elo > 0
GROUP BY mw.winning_team
ORDER BY mw.winning_team
```

I7 justification: ELO bin width 10 for difference (smaller than 25 used for
absolute values because difference range is narrower). Sentinel -1 excluded
(34 + 39 rows from census `elo_sentinel_counts`). Zero-valued ELO excluded
(4,824 + 192 rows from census `numeric_stats_matches`).

**Python:**
```python
# --- T05: ELO by Winner (Q6) ---

sql_elo_diff = """
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    FLOOR((m.team_0_elo - m.team_1_elo) / 10) * 10 AS elo_diff_bin,
    COUNT(*) AS cnt
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.team_0_elo > 0
  AND m.team_1_elo > 0
GROUP BY mw.winning_team, elo_diff_bin
ORDER BY mw.winning_team, elo_diff_bin
"""
sql_queries["elo_diff_by_winning_team"] = sql_elo_diff

sql_elo_stats = """
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    ROUND(AVG(m.team_0_elo), 2) AS mean_t0_elo,
    ROUND(AVG(m.team_1_elo), 2) AS mean_t1_elo,
    ROUND(AVG(m.avg_elo), 2) AS mean_avg_elo,
    ROUND(AVG(m.team_0_elo - m.team_1_elo), 2) AS mean_elo_diff,
    COUNT(*) AS n
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.team_0_elo > 0
  AND m.team_1_elo > 0
GROUP BY mw.winning_team
ORDER BY mw.winning_team
"""
sql_queries["elo_by_winning_team_stats"] = sql_elo_stats

df_elo_diff = conn.execute(sql_elo_diff).fetchdf()
df_elo_stats = conn.execute(sql_elo_stats).fetchdf()

# W6 / Assert no game_ids have NULL winning_team (would indicate matches
# where no player has winner=true — edge case from census surplus of
# false rows over true rows)
null_winner_count = conn.execute(
    "SELECT COUNT(*) FROM (SELECT game_id, MAX(CASE WHEN winner=true THEN team END) "
    "AS winning_team FROM players_raw GROUP BY game_id) WHERE winning_team IS NULL"
).fetchone()[0]
print(f"Game IDs with no winner: {null_winner_count}")
# Log but don't crash — these are edge cases; downstream queries drop them
# via JOIN (NULLs don't match any match row)
bivariate_results["null_winner_game_count"] = int(null_winner_count)

print("ELO stats by winning team:")
print(df_elo_stats.to_string(index=False))

bivariate_results["elo_by_winning_team"] = df_elo_stats.to_dict(orient="records")

# Plot: ELO difference distribution by winning team
fig, ax = plt.subplots(figsize=(10, 6))
for team_val, color, label in [(0, "steelblue", "Team 0 wins"), (1, "salmon", "Team 1 wins")]:
    subset = df_elo_diff[df_elo_diff["winning_team"] == team_val]
    ax.step(
        subset["elo_diff_bin"], subset["cnt"],
        where="mid", color=color, alpha=0.7, linewidth=1.5, label=label,
    )
    ax.fill_between(subset["elo_diff_bin"], subset["cnt"], step="mid", alpha=0.2, color=color)

row_t0 = df_elo_stats[df_elo_stats["winning_team"] == 0].iloc[0]
row_t1 = df_elo_stats[df_elo_stats["winning_team"] == 1].iloc[0]
ax.set_xlabel("team_0_elo - team_1_elo")
ax.set_ylabel("Count per 10-ELO bin")
ax.set_title(
    f"ELO Difference (team_0 - team_1) by Winning Team\n"
    f"When T0 wins: mean diff={row_t0['mean_elo_diff']:.1f}; "
    f"When T1 wins: mean diff={row_t1['mean_elo_diff']:.1f}"
)
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_elo_by_winner.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_elo_by_winner.png'}")
```

**Invariant notes:**
- I6: All three SQL queries stored.
- I7: Sentinel and zero exclusion from census. Bin width 10 documented.

### T06 -- Duration by Winner (Q5)

**Scientific question answered:** Q5 -- Does match duration differ by winner?

**Input:** DuckDB JOIN query. Duration is in matches_raw; winner is in
players_raw. Use the same CTE pattern as T05.

**Output:** `plots/01_02_06_duration_by_winner.png`

**SQL (store in sql_queries["duration_by_winner_buckets"]):**
```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    FLOOR((m.duration / 1e9) / 60) AS dur_min_bin,
    COUNT(*) AS cnt
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.duration > 0
  AND (m.duration / 1e9) <= 4714.1
GROUP BY mw.winning_team, dur_min_bin
ORDER BY mw.winning_team, dur_min_bin
```

I7 justification: p95 clip at 4,714.1s (from census `numeric_stats_matches`
label `duration_sec`, `p95=4714.1`). Bin width 1 minute (same as 01_02_05).
`duration / 1e9` for nanosecond to seconds conversion.

**SQL (store in sql_queries["duration_by_winner_stats"]):**
```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    ROUND(AVG(m.duration / 1e9), 2) AS mean_dur_sec,
    ROUND(MEDIAN(m.duration / 1e9), 2) AS median_dur_sec,
    COUNT(*) AS n
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.duration > 0
GROUP BY mw.winning_team
ORDER BY mw.winning_team
```

**Python:**
```python
# --- T06: Duration by Winner (Q5) ---

sql_dur_bins = """
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    FLOOR((m.duration / 1e9) / 60) AS dur_min_bin,
    COUNT(*) AS cnt
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.duration > 0
  AND (m.duration / 1e9) <= 4714.1
GROUP BY mw.winning_team, dur_min_bin
ORDER BY mw.winning_team, dur_min_bin
"""
sql_queries["duration_by_winner_buckets"] = sql_dur_bins

sql_dur_stats = """
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    ROUND(AVG(m.duration / 1e9), 2) AS mean_dur_sec,
    ROUND(MEDIAN(m.duration / 1e9), 2) AS median_dur_sec,
    COUNT(*) AS n
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.duration > 0
GROUP BY mw.winning_team
ORDER BY mw.winning_team
"""
sql_queries["duration_by_winner_stats"] = sql_dur_stats

df_dur_bins = conn.execute(sql_dur_bins).fetchdf()
df_dur_stats = conn.execute(sql_dur_stats).fetchdf()
print("Duration by winner stats:")
print(df_dur_stats.to_string(index=False))

bivariate_results["duration_by_winner"] = df_dur_stats.to_dict(orient="records")

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
for team_val, color, label in [(0, "steelblue", "Team 0 wins"), (1, "salmon", "Team 1 wins")]:
    subset = df_dur_bins[df_dur_bins["winning_team"] == team_val]
    ax.step(
        subset["dur_min_bin"], subset["cnt"],
        where="mid", color=color, alpha=0.7, linewidth=1.5, label=label,
    )
    ax.fill_between(subset["dur_min_bin"], subset["cnt"], step="mid", alpha=0.2, color=color)

ax.set_xlabel("Duration (minutes)")
ax.set_ylabel("Count per 1-min bin")
row_t0 = df_dur_stats[df_dur_stats["winning_team"] == 0].iloc[0]
row_t1 = df_dur_stats[df_dur_stats["winning_team"] == 1].iloc[0]
ax.set_title(
    f"Match Duration by Winning Team (clipped at p95={4714.1/60:.0f} min)\n"
    f"Team 0 wins median={row_t0['median_dur_sec']/60:.1f} min; "
    f"Team 1 wins median={row_t1['median_dur_sec']/60:.1f} min"
)
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

# POST-GAME annotation
ax.annotate(
    "POST-GAME -- not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_duration_by_winner.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_duration_by_winner.png'}")
```

**Invariant notes:**
- I3: POST-GAME annotation.
- I6: Both SQL queries stored.
- I7: p95 clip and bin width from census/01_02_05 precedent.

### T07 -- Multi-Panel Numeric Features by Winner (Q1)

**Scientific question answered:** Q1 -- Conditional distributions of all
numeric pre-game features by winner.

**Input:** DuckDB query on players_raw for old_rating. Additional numeric
pre-game features from matches_raw require the match_winner CTE JOIN. The
pre-game numeric features are: `old_rating` (players_raw), `avg_elo`,
`team_0_elo`, `team_1_elo` (matches_raw). NOTE: duration and irl_duration
are POST-GAME; match_rating_diff leakage status resolved in T03; new_rating
is POST-GAME. Age uptimes are IN-GAME (covered separately in T09).

**Output:** `plots/01_02_06_numeric_by_winner.png`

**SQL (store in sql_queries["numeric_pregame_by_winner_stats"]):**
```sql
-- old_rating from players_raw (directly has winner)
SELECT
    'old_rating' AS feature,
    winner,
    COUNT(*) AS n,
    ROUND(AVG(old_rating), 2) AS mean_val,
    ROUND(MEDIAN(old_rating), 2) AS median_val,
    ROUND(STDDEV(old_rating), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY old_rating) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY old_rating) AS p95
FROM players_raw
WHERE old_rating > 0
GROUP BY winner
ORDER BY winner
```

**SQL (store in sql_queries["match_elo_by_winner_stats"]):**
```sql
WITH match_winner AS (
    SELECT game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    feature,
    winning_team AS winner_team,
    COUNT(*) AS n,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY val) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY val) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY val) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY val) AS p95
FROM (
    SELECT mw.winning_team, 'avg_elo' AS feature, m.avg_elo AS val
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.avg_elo > 0
    UNION ALL
    SELECT mw.winning_team, 'team_0_elo', m.team_0_elo
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.team_0_elo > 0
    UNION ALL
    SELECT mw.winning_team, 'team_1_elo', m.team_1_elo
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.team_1_elo > 0
) sub
GROUP BY feature, winning_team
ORDER BY feature, winning_team
```

**Python:**
```python
# --- T07: Multi-panel Numeric Features by Winner (Q1) ---

# Query old_rating by winner (direct from players_raw)
sql_or = """
SELECT
    'old_rating' AS feature,
    winner,
    COUNT(*) AS n,
    ROUND(AVG(old_rating), 2) AS mean_val,
    ROUND(MEDIAN(old_rating), 2) AS median_val,
    ROUND(STDDEV(old_rating), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY old_rating) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY old_rating) AS p95
FROM players_raw
WHERE old_rating > 0
GROUP BY winner
ORDER BY winner
"""
sql_queries["numeric_pregame_by_winner_stats"] = sql_or

sql_elo_m = """
WITH match_winner AS (
    SELECT game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    feature,
    winning_team AS winner_team,
    COUNT(*) AS n,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY val) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY val) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY val) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY val) AS p95
FROM (
    SELECT mw.winning_team, 'avg_elo' AS feature, m.avg_elo AS val
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.avg_elo > 0
    UNION ALL
    SELECT mw.winning_team, 'team_0_elo', m.team_0_elo
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.team_0_elo > 0
    UNION ALL
    SELECT mw.winning_team, 'team_1_elo', m.team_1_elo
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.team_1_elo > 0
) sub
GROUP BY feature, winning_team
ORDER BY feature, winning_team
"""
sql_queries["match_elo_by_winner_stats"] = sql_elo_m

df_or_stats = conn.execute(sql_or).fetchdf()
df_elo_m_stats = conn.execute(sql_elo_m).fetchdf()

print("old_rating by winner:")
print(df_or_stats.to_string(index=False))
print("Match ELO features by winning team:")
print(df_elo_m_stats.to_string(index=False))

bivariate_results["numeric_pregame_by_winner"] = {
    "old_rating": df_or_stats.to_dict(orient="records"),
    "match_elo_features": df_elo_m_stats.to_dict(orient="records"),
}

# Plot: 2x2 panel showing box-like summary for each feature
features_data = []
# old_rating: winner is boolean
for _, row in df_or_stats.iterrows():
    features_data.append({
        "feature": "old_rating",
        "group": "Winner" if row["winner"] else "Loser",
        "median": row["median_val"],
        "p25": row["p25"],
        "p75": row["p75"],
        "p05": row["p05"],
        "p95": row["p95"],
        "mean": row["mean_val"],
    })
# ELO features: winning_team is 0/1
for _, row in df_elo_m_stats.iterrows():
    features_data.append({
        "feature": row["feature"],
        "group": f"Team {int(row['winner_team'])} wins",
        "median": row["median_val"],
        "p25": row["p25"],
        "p75": row["p75"],
        "p05": row["p05"],
        "p95": row["p95"],
        "mean": row["mean_val"],
    })

df_panel = pd.DataFrame(features_data)
feature_list = ["old_rating", "avg_elo", "team_0_elo", "team_1_elo"]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()
for idx, feat in enumerate(feature_list):
    ax = axes[idx]
    sub = df_panel[df_panel["feature"] == feat]
    groups = sub["group"].values
    positions = range(len(groups))
    for i, (_, row) in enumerate(sub.iterrows()):
        # Box-whisker from p05 to p95, box from p25 to p75
        ax.bar(
            i, row["p75"] - row["p25"], bottom=row["p25"],
            width=0.5, color="steelblue" if "Winner" in row["group"] or "0" in row["group"] else "salmon",
            alpha=0.6, edgecolor="black",
        )
        ax.plot([i, i], [row["p05"], row["p95"]], color="black", linewidth=1)
        ax.plot(i, row["median"], "o", color="white", markersize=8, markeredgecolor="black")
        ax.annotate(f"med={row['median']:.0f}", (i, row["median"]),
                    textcoords="offset points", xytext=(30, 0), fontsize=8)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups, fontsize=9)
    ax.set_title(feat, fontsize=11, fontweight="bold")
    ax.set_ylabel("ELO")
    ax.grid(axis="y", alpha=0.3)

fig.suptitle("Pre-Game Numeric Features by Winner/Winning Team", fontsize=13)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_numeric_by_winner.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_numeric_by_winner.png'}")
```

### T08 -- Opening Win Rate Bar Chart (Q7)

**Scientific question answered:** Q7 -- Does opening strategy correlate with
win rate?

**Input:** DuckDB query on players_raw, non-NULL opening rows only (~15M rows,
14% of total).

**Output:** `plots/01_02_06_opening_winrate.png`

**SQL (store in sql_queries["opening_winrate"]):**
```sql
SELECT
    opening,
    COUNT(*) AS total_games,
    SUM(CASE WHEN winner = true THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN winner = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM players_raw
WHERE opening IS NOT NULL
GROUP BY opening
ORDER BY total_games DESC
LIMIT 20
```

I7 justification: Top-20 by count ensures sufficient sample per opening for
meaningful win rates. Census shows 10 distinct openings in
`opening_nonnull_distribution` so LIMIT 20 captures all.

**Python:**
```python
# --- T08: Opening Win Rate (Q7) ---

sql_opening = """
SELECT
    opening,
    COUNT(*) AS total_games,
    SUM(CASE WHEN winner = true THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN winner = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM players_raw
WHERE opening IS NOT NULL
GROUP BY opening
ORDER BY total_games DESC
LIMIT 20
"""
sql_queries["opening_winrate"] = sql_opening
df_opening = conn.execute(sql_opening).fetchdf()
print("Opening win rates:")
print(df_opening.to_string(index=False))

# Rename column for convenience (SQL returns win_pct as percentage 0-100;
# convert to proportion 0-1 for CI calculation)
df_opening["win_rate"] = df_opening["win_pct"] / 100.0
df_opening["total"] = df_opening["total_games"]

# I7: 95% CI uses Wilson score interval for proportions (more robust than
# normal approximation at boundary win rates)
try:
    from statsmodels.stats.proportion import proportion_confint
    ci_low, ci_high = zip(*[
        proportion_confint(int(r * n), n, alpha=0.05, method="wilson")
        for r, n in zip(df_opening["win_rate"], df_opening["total"])
    ])
    df_opening["ci_low"] = ci_low
    df_opening["ci_high"] = ci_high
except ImportError:
    # Fallback: normal approximation
    df_opening["ci"] = 1.96 * np.sqrt(
        df_opening["win_rate"] * (1 - df_opening["win_rate"]) / df_opening["total"]
    )
    df_opening["ci_low"] = df_opening["win_rate"] - df_opening["ci"]
    df_opening["ci_high"] = df_opening["win_rate"] + df_opening["ci"]

bivariate_results["opening_winrate"] = df_opening.to_dict(orient="records")

# Plot: horizontal bar chart of win rate per opening
fig, ax = plt.subplots(figsize=(10, 6))
df_op_sorted = df_opening.sort_values("win_pct", ascending=True)
colors = ["steelblue" if wp > 50 else "salmon" for wp in df_op_sorted["win_pct"]]
bars = ax.barh(df_op_sorted["opening"], df_op_sorted["win_pct"], color=colors, edgecolor="black", alpha=0.7)

# Add 95% CI error bars (converted back to percentage scale for the plot)
x_vals = df_op_sorted["win_pct"].values
y_vals = range(len(df_op_sorted))
xerr_low = (df_op_sorted["win_rate"] - df_op_sorted["ci_low"]).values * 100
xerr_high = (df_op_sorted["ci_high"] - df_op_sorted["win_rate"]).values * 100
ax.errorbar(
    x_vals, y_vals,
    xerr=[xerr_low, xerr_high],
    fmt="none", color="black", capsize=3,
)

# Annotate with win rate and sample size
for bar, (_, row) in zip(bars, df_op_sorted.iterrows()):
    ax.text(
        bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
        f"{row['win_pct']:.1f}% (N={row['total_games']:,})",
        va="center", fontsize=8,
    )

ax.axvline(50, color="gray", linestyle="--", linewidth=1, label="50% baseline")
ax.set_xlabel("Win Rate (%)")
total_nonnull = int(census["opening_nonnull_distribution"]["total_nonnull"])
total_players = int(census["players_null_census"]["total_rows"])
ax.set_title(
    f"Win Rate by Opening Strategy (non-NULL only: {total_nonnull:,} of {total_players:,} rows, "
    f"{100 * total_nonnull / total_players:.1f}%)"
)
ax.legend(loc="lower right")

# IN-GAME annotation
ax.annotate(
    "IN-GAME -- not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_opening_winrate.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_opening_winrate.png'}")
```

**Invariant notes:**
- I3: IN-GAME annotation. Opening is derived from in-game replay analysis.
- I6: SQL stored.
- I7: Top-20 captures all 10 distinct openings.

### T09 -- Age Uptime by Winner Violin (Q8)

**Scientific question answered:** Q8 -- Do age uptimes differ by winner?

**Input:** DuckDB query on players_raw, non-NULL rows only.

**Output:** `plots/01_02_06_age_uptime_by_winner.png`

**SQL (store in sql_queries["age_uptime_by_winner_stats"]):**
```sql
SELECT
    feature,
    winner,
    COUNT(*) AS n,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY val) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY val) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY val) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY val) AS p95
FROM (
    SELECT 'feudal_age_uptime' AS feature, winner, feudal_age_uptime AS val
    FROM players_raw WHERE feudal_age_uptime IS NOT NULL
    UNION ALL
    SELECT 'castle_age_uptime', winner, castle_age_uptime
    FROM players_raw WHERE castle_age_uptime IS NOT NULL
    UNION ALL
    SELECT 'imperial_age_uptime', winner, imperial_age_uptime
    FROM players_raw WHERE imperial_age_uptime IS NOT NULL
) sub
GROUP BY feature, winner
ORDER BY feature, winner
```

**Python:**
```python
# --- T09: Age Uptime by Winner (Q8) ---

sql_age = """
SELECT
    feature,
    winner,
    COUNT(*) AS n,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY val) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY val) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY val) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY val) AS p95
FROM (
    SELECT 'feudal_age_uptime' AS feature, winner, feudal_age_uptime AS val
    FROM players_raw WHERE feudal_age_uptime IS NOT NULL
    UNION ALL
    SELECT 'castle_age_uptime', winner, castle_age_uptime
    FROM players_raw WHERE castle_age_uptime IS NOT NULL
    UNION ALL
    SELECT 'imperial_age_uptime', winner, imperial_age_uptime
    FROM players_raw WHERE imperial_age_uptime IS NOT NULL
) sub
GROUP BY feature, winner
ORDER BY feature, winner
"""
sql_queries["age_uptime_by_winner_stats"] = sql_age
df_age = conn.execute(sql_age).fetchdf()
print("Age uptime by winner:")
print(df_age.to_string(index=False))

bivariate_results["age_uptime_by_winner"] = df_age.to_dict(orient="records")

# Plot: 1x3 panel
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for idx, feat in enumerate(["feudal_age_uptime", "castle_age_uptime", "imperial_age_uptime"]):
    ax = axes[idx]
    sub = df_age[df_age["feature"] == feat]
    for i, (_, row) in enumerate(sub.iterrows()):
        group_label = "Winner" if row["winner"] else "Loser"
        color = "steelblue" if row["winner"] else "salmon"
        ax.bar(
            i, row["p75"] - row["p25"], bottom=row["p25"],
            width=0.5, color=color, alpha=0.6, edgecolor="black",
            label=group_label,
        )
        ax.plot([i, i], [row["p05"], row["p95"]], color="black", linewidth=1)
        ax.plot(i, row["median_val"], "o", color="white", markersize=8, markeredgecolor="black")
        ax.annotate(
            f"med={row['median_val']:.0f}s\nN={row['n']:,}",
            (i, row["p95"]), textcoords="offset points", xytext=(0, 8),
            ha="center", fontsize=7,
        )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Loser", "Winner"])
    ax.set_title(feat.replace("_", " ").title(), fontsize=10)
    ax.set_ylabel("Seconds")
    ax.grid(axis="y", alpha=0.3)

    # IN-GAME annotation
    ax.annotate(
        "IN-GAME (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=7, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.2", fc="#ffe0e0", ec="red", alpha=0.9),
    )

fig.suptitle(
    "Age Uptimes by Winner (non-NULL rows only; ~14% of players_raw)",
    fontsize=12,
)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_age_uptime_by_winner.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_age_uptime_by_winner.png'}")
```

**Invariant notes:**
- I3: IN-GAME annotation on all three panels.
- I6: SQL stored.
- I9: Bivariate visualization only; no cleaning or imputation.

### T10 -- Spearman Correlation Matrix (Q2)

**Scientific question answered:** Q2 -- What is the pairwise correlation
structure among numeric columns?

**Input:** DuckDB query. For players_raw numeric columns (old_rating,
new_rating, match_rating_diff, feudal_age_uptime, castle_age_uptime,
imperial_age_uptime), Spearman correlation is computed on a sample.
Match-level columns (avg_elo, team_0_elo, team_1_elo, duration) require
a JOIN. Simplification: compute separate correlation matrices for
players_raw columns and matches_raw columns, since cross-table correlations
require the expensive JOIN.

**Output:** `plots/01_02_06_spearman_correlation.png`

**SQL (store in sql_queries["spearman_sample_players"]):**
```sql
SELECT
    old_rating,
    new_rating,
    match_rating_diff,
    feudal_age_uptime,
    castle_age_uptime,
    imperial_age_uptime
FROM players_raw
WHERE old_rating > 0
  AND match_rating_diff IS NOT NULL
USING SAMPLE RESERVOIR(500000)
```

I7 justification: 500K sample from 107.6M rows for Spearman computation.
Standard error of Spearman r at N=500K is ~0.001, negligible. RESERVOIR
for exact count.

**SQL (store in sql_queries["spearman_sample_matches"]):**
```sql
SELECT
    avg_elo,
    team_0_elo,
    team_1_elo,
    (duration / 1e9) AS duration_sec,
    (irl_duration / 1e9) AS irl_duration_sec
FROM matches_raw
WHERE avg_elo > 0
  AND team_0_elo > 0
  AND team_1_elo > 0
USING SAMPLE RESERVOIR(500000)
```

**Python:**
```python
# --- T10: Spearman Correlation Matrix (Q2) ---

sql_samp_p = """
SELECT
    old_rating,
    new_rating,
    match_rating_diff,
    feudal_age_uptime,
    castle_age_uptime,
    imperial_age_uptime
FROM players_raw
WHERE old_rating > 0
  AND match_rating_diff IS NOT NULL
USING SAMPLE RESERVOIR(500000)
"""
sql_queries["spearman_sample_players"] = sql_samp_p

sql_samp_m = """
SELECT
    avg_elo,
    team_0_elo,
    team_1_elo,
    (duration / 1e9) AS duration_sec,
    (irl_duration / 1e9) AS irl_duration_sec
FROM matches_raw
WHERE avg_elo > 0
  AND team_0_elo > 0
  AND team_1_elo > 0
USING SAMPLE RESERVOIR(500000)
"""
sql_queries["spearman_sample_matches"] = sql_samp_m

df_p = conn.execute(sql_samp_p).fetchdf()
df_m = conn.execute(sql_samp_m).fetchdf()

# Compute Spearman correlations
corr_p = df_p.corr(method="spearman")
corr_m = df_m.corr(method="spearman")

bivariate_results["spearman_correlation"] = {
    "players_raw": corr_p.round(4).to_dict(),
    "matches_raw": corr_m.round(4).to_dict(),
    "sample_size_players": len(df_p),
    "sample_size_matches": len(df_m),
}

# Plot: 1x2 panel heatmap
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Players heatmap
im1 = ax1.imshow(corr_p.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
ax1.set_xticks(range(len(corr_p.columns)))
ax1.set_yticks(range(len(corr_p.columns)))
ax1.set_xticklabels(corr_p.columns, rotation=45, ha="right", fontsize=8)
ax1.set_yticklabels(corr_p.columns, fontsize=8)
ax1.set_title(f"Spearman Correlation -- players_raw\n(N={len(df_p):,} sampled)", fontsize=10)
for i in range(len(corr_p)):
    for j in range(len(corr_p)):
        val = corr_p.values[i, j]
        color = "white" if abs(val) > 0.5 else "black"
        ax1.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7, color=color)
plt.colorbar(im1, ax=ax1, shrink=0.8)

# Matches heatmap
im2 = ax2.imshow(corr_m.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
ax2.set_xticks(range(len(corr_m.columns)))
ax2.set_yticks(range(len(corr_m.columns)))
ax2.set_xticklabels(corr_m.columns, rotation=45, ha="right", fontsize=8)
ax2.set_yticklabels(corr_m.columns, fontsize=8)
ax2.set_title(f"Spearman Correlation -- matches_raw\n(N={len(df_m):,} sampled)", fontsize=10)
for i in range(len(corr_m)):
    for j in range(len(corr_m)):
        val = corr_m.values[i, j]
        color = "white" if abs(val) > 0.5 else "black"
        ax2.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7, color=color)
plt.colorbar(im2, ax=ax2, shrink=0.8)

# Mark post-game and leakage-unresolved columns with asterisk in tick labels
POST_GAME_COLS = ["new_rating", "match_rating_diff"]  # from 01_02_04 classification
# Players heatmap: relabel ax1 ticks
xlabels1 = [lbl.get_text() for lbl in ax1.get_xticklabels()]
ylabels1 = [lbl.get_text() for lbl in ax1.get_yticklabels()]
ax1.set_xticklabels(
    [f"{l}*" if l in POST_GAME_COLS else l for l in xlabels1],
    rotation=45, ha="right", fontsize=8,
)
ax1.set_yticklabels(
    [f"{l}*" if l in POST_GAME_COLS else l for l in ylabels1],
    fontsize=8,
)
ax1.annotate(
    "* = POST-GAME or LEAKAGE-UNRESOLVED column (Inv. #3)",
    xy=(0.02, 0.02), xycoords="figure fraction",
    fontsize=7, color="darkred", fontstyle="italic",
)

fig.suptitle("Spearman Rank Correlation Matrices", fontsize=13)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_spearman_correlation.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_spearman_correlation.png'}")
```

**Invariant notes:**
- I6: Both sampling SQL queries stored.
- I7: Sample size 500K, SE ~0.001.
- I9: Correlation analysis only; no feature selection decisions.

### T11 -- JSON Artifact, Markdown Artifact, and Verification

**Objective:** Write JSON artifact with all bivariate results. Write markdown
artifact with all SQL queries and plot index. Verify all plots exist. Close
connection.

**Instructions:**
1. Write `bivariate_results` dict to
   `artifacts_dir / "01_02_06_bivariate_eda.json"`.
2. Define `expected_plots` list with all 8 PNG filenames.
3. Assert all exist on disk.
4. Build markdown with:
   - Header.
   - Leakage Resolution Summary (the single most important finding).
   - Plot index table with columns: #, Title, Filename, Observation,
     Temporal Annotation. Temporal Annotation column: "POST-GAME (Inv. #3)"
     for duration, "IN-GAME (Inv. #3)" for age uptimes and opening,
     "LEAKAGE STATUS: {resolved_status} (Inv. #3)" for match_rating_diff
     scatter, "N/A" for all others.
   - SQL Queries section: iterate sql_queries dict. Must enumerate ALL
     queries.
   - Data Sources section.
5. Write to `artifacts_dir / "01_02_06_bivariate_eda.md"`.
6. Close DuckDB connection.

**Python:**
```python
# --- T11: Artifacts and Verification ---

# Write JSON artifact
import json as json_mod  # avoid shadowing earlier import
json_path = artifacts_dir / "01_02_06_bivariate_eda.json"
with open(json_path, "w") as f:
    json_mod.dump(bivariate_results, f, indent=2, default=str)
print(f"Saved JSON artifact: {json_path}")

# Verify plots
expected_plots = [
    "01_02_06_match_rating_diff_leakage_scatter.png",
    "01_02_06_old_rating_by_winner.png",
    "01_02_06_elo_by_winner.png",
    "01_02_06_duration_by_winner.png",
    "01_02_06_numeric_by_winner.png",
    "01_02_06_opening_winrate.png",
    "01_02_06_age_uptime_by_winner.png",
    "01_02_06_spearman_correlation.png",
]
missing = [p for p in expected_plots if not (plots_dir / p).exists()]
assert not missing, f"Missing plots: {missing}"
print(f"All {len(expected_plots)} plots verified on disk.")

# Build markdown
leakage = bivariate_results["match_rating_diff_leakage"]
md_lines = [
    "# Step 01_02_06 -- Bivariate EDA -- aoestats",
    "",
    f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d')}",
    f"**Dataset:** aoestats (matches_raw: 30,690,651 rows; players_raw: 107,627,584 rows)",
    f"**Predecessor:** 01_02_05 (Univariate Visualizations)",
    "",
    "## Leakage Resolution: match_rating_diff",
    "",
    f"**Status: {leakage['leakage_status']}**",
    "",
    f"{leakage['detail']}",
    "",
    f"- Pearson r: {leakage['pearson_r']:.6f}",
    f"- OLS slope: {leakage['ols_slope']:.6f}",
    f"- OLS intercept: {leakage['ols_intercept']:.6f}",
    f"- R-squared: {leakage['ols_r_squared']:.6f}",
    f"- Exact match (tolerance 0.01): {leakage['exact_match_count']:,} / {leakage['total_rows_tested']:,} ({leakage['exact_match_pct']:.2f}%)",
    "",
    "## Plot Index",
    "",
    "| # | Title | Filename | Temporal Annotation |",
    "|---|-------|----------|---------------------|",
]

temporal_annotations = {
    "match_rating_diff_leakage_scatter": f"LEAKAGE STATUS: {leakage['leakage_status']} (Inv. #3)",
    "old_rating_by_winner": "N/A (pre-game)",
    "elo_by_winner": "N/A (pre-game)",
    "duration_by_winner": "POST-GAME (Inv. #3)",
    "numeric_by_winner": "N/A (pre-game features)",
    "opening_winrate": "IN-GAME (Inv. #3)",
    "age_uptime_by_winner": "IN-GAME (Inv. #3)",
    "spearman_correlation": "Mixed -- includes post-game columns",
}

for i, plot_name in enumerate(expected_plots, 1):
    short_name = plot_name.replace("01_02_06_", "").replace(".png", "")
    annotation = temporal_annotations.get(short_name, "N/A")
    md_lines.append(f"| {i} | {short_name} | `{plot_name}` | {annotation} |")

md_lines.extend([
    "",
    "## SQL Queries",
    "",
])
for query_name, query_sql in sql_queries.items():
    md_lines.extend([
        f"### {query_name}",
        "",
        "```sql",
        query_sql.strip(),
        "```",
        "",
    ])

md_lines.extend([
    "## Data Sources",
    "",
    "- `matches_raw` (30,690,651 rows, 18 columns)",
    "- `players_raw` (107,627,584 rows, 14 columns)",
    "- Census artifact: `01_02_04_univariate_census.json`",
])

md_path = artifacts_dir / "01_02_06_bivariate_eda.md"
with open(md_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"Saved markdown artifact: {md_path}")

# Close connection
conn.close()
print("DuckDB connection closed.")
```

**Verification:**
- All 8 PNG files exist.
- JSON artifact has `bivariate_results["match_rating_diff_leakage"]["leakage_status"]` field (nested path; flat key `match_rating_diff_leakage_status` does not exist).
- Markdown artifact contains all SQL queries.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.py` (continuation)
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json` (generated)
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md` (generated)

### T12 -- STEP_STATUS Update

**Objective:** Mark 01_02_06 as complete.

**Instructions:**
1. Add 01_02_06 entry to `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`:
```yaml
  "01_02_06":
    name: "Bivariate EDA"
    pipeline_section: "01_02"
    status: complete
    completed_at: "<execution date>"
```

**Verification:**
- STEP_STATUS.yaml contains 01_02_06 with status `complete`.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`

## Cross-Dataset Comparability Checklist

| Mandatory Bivariate Plot | Column | aoestats Treatment |
|---|---|---|
| (a) Rating by winner | `old_rating` (players_raw) | Direct query -- winner in same table |
| (b) Spearman correlation | numeric columns | Two-panel: players_raw + matches_raw |
| (c) Duration by winner | `duration / 1e9` (matches_raw) | JOIN via match_winner CTE; POST-GAME annotated |
| (d) Numeric features by winner panel | pre-game features | old_rating direct; ELO features via JOIN |

**aoestats-specific additions:** leakage scatter (Q3, blocker), opening win
rate (Q7, IN-GAME), age uptime by winner (Q8, IN-GAME).

## Performance Notes

The match_winner CTE (`SELECT game_id, MAX(CASE WHEN winner=true THEN team END) AS winning_team FROM players_raw GROUP BY game_id`) scans all 107.6M rows of players_raw. This will execute in ~30-60 seconds on SSD. It is used in T05, T06, and T07.

```python
# NOTE: match_winner logic is a CTE (not a TEMP VIEW) because DuckDB read-only
# connections do not allow DDL. The CTE is inlined in each query.
# CTE pattern:
# WITH match_winner AS (
#     SELECT game_id, MAX(CASE WHEN winner = true THEN team END) AS winning_team
#     FROM players_raw GROUP BY game_id
# )
```

The CTE is repeated in T05, T06, and T07 to stay compatible with `read_only=True`. DuckDB will recompute the aggregation for each query; this is acceptable because each task runs once and the total wall-clock overhead is bounded (~30-60s per execution).

## Gate Condition

- [ ] `plots/01_02_06_match_rating_diff_leakage_scatter.png`
- [ ] `plots/01_02_06_old_rating_by_winner.png`
- [ ] `plots/01_02_06_elo_by_winner.png`
- [ ] `plots/01_02_06_duration_by_winner.png`
- [ ] `plots/01_02_06_numeric_by_winner.png`
- [ ] `plots/01_02_06_opening_winrate.png`
- [ ] `plots/01_02_06_age_uptime_by_winner.png`
- [ ] `plots/01_02_06_spearman_correlation.png`
- [ ] `01_02_06_bivariate_eda.json` with `match_rating_diff_leakage.leakage_status` field
- [ ] `01_02_06_bivariate_eda.md` with all SQL queries and plot index table including Temporal Annotation column
- [ ] ROADMAP.md Step 01_02_06 added
- [ ] STEP_STATUS.yaml `01_02_06` -> complete
- [ ] Notebook executes end-to-end without error

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.py` | Create |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.ipynb` | Create (jupytext sync) |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_*.png` (8 files) | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json` | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Modify |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | Modify |

All paths are relative to `src/rts_predict/games/aoe2/datasets/aoestats/`.
Notebook path is relative to repo root.

## Out of Scope

- Multivariate analysis (Step 01_02_07)
- Feature engineering decisions (Phase 02)
- Cleaning or filtering decisions (Step 01_04)
- Research log entry (written post-execution by parent)
- Cross-dataset bivariate comparison (separate coordination step)
- `new_rating` bivariate analysis -- classified POST-GAME in 01_02_04;
  appears only in Spearman matrix for completeness (annotated)
- Model training or hyperparameter selection

## Open Questions

- If `match_rating_diff` leakage status is AMBIGUOUS (neither clearly
  LEAKAGE nor PRE_GAME), a follow-up investigation step will be needed
  before Phase 02 can proceed.
- Does the old_rating winner/loser difference vary by ELO bracket?
  (Deferred to 01_02_07 multivariate EDA if warranted.)
- Should the match_winner CTE be materialized as a persistent DuckDB
  view for reuse in future steps? (Low-priority optimization.)

---

For Category A, adversarial critique is required before execution.
Dispatch reviewer-adversarial to produce
`planning/plan_aoestats_01_02_06.critique.md`.
