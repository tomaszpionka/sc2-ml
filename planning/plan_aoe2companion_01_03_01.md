---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [3, 6, 7, 9]
critique_required: true
source_artifacts:
  - "reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
  - "reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md"
  - "data/db/db.duckdb (matches_raw)"
research_log_ref: "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md"
---

# Plan: aoe2companion Step 01_03_01 -- Systematic Data Profiling Pipeline

## Scope

**Phase/Step:** 01 / 01_03_01
**Branch:** feat/census-pass3
**Action:** CREATE (step 01_03_01 does not exist in ROADMAP.md; this plan defines it)
**Predecessor:** 01_02_07 (Multivariate EDA -- complete, artifacts on disk)

Build a systematic profiling notebook that consolidates and extends 01_02 census
findings into a structured, machine-readable profile of matches_raw (277M rows).
The notebook produces five artifacts: (1) a comprehensive JSON profile with column-level
stats, dataset-level metrics, and critical findings; (2) a completeness heatmap PNG;
(3) a QQ plot PNG for numeric columns; (4) an ECDF plot for key columns; (5) a
markdown report with I3 classification table for every column.

This step is the first work in Pipeline Section 01_03 (Systematic Data Profiling).
It transitions from the exploratory Tukey-style EDA of 01_02 to structured,
auditable profiling per Manual Section 3. Key difference: 01_02 *explored*
distributions; 01_03 *profiles* them systematically with formal detection of dead
fields, constant columns, near-constant columns, and primary key integrity.

**Single table scope:** Only `matches_raw` is profiled. The other three tables
(ratings_raw, leaderboard_raw, profiles_raw) are auxiliary reference tables.
matches_raw is the prediction-relevant table containing all 277M player-match rows.

## Problem Statement

Steps 01_02_04 through 01_02_07 produced univariate census, bivariate EDA, and
multivariate analysis. These are Tukey-style exploratory outputs. Manual Section 3
requires a *systematic* profile that can be consumed programmatically by downstream
steps (01_04 cleaning rules, 02_01 pre-game boundary, thesis Chapter 4). The
systematic profile differs from the census in three ways:

1. **Formal column-level profiling schema:** Each column gets a fixed set of
   metrics (null_count, null_pct, zero_count, zero_pct, cardinality,
   uniqueness_ratio, descriptive stats, skewness, kurtosis, IQR outlier count,
   top-k values) in a single JSON structure.
2. **Critical detection with explicit flagging:** Dead fields, constant columns,
   near-constant columns are identified with machine-readable flags under a
   `critical_findings` key, not prose descriptions.
3. **Distribution analysis:** QQ plots and ECDFs provide formal normality
   assessment and distributional characterization that 01_02 histograms do not.

The 277M row count makes full-table scans expensive. The plan uses DuckDB
aggregation for exact column-level stats (NULL counts, cardinality, descriptive
stats, skewness, kurtosis) and BERNOULLI sampling for distribution visualization
(QQ, ECDF).

## Assumptions & Unknowns

- **Assumption:** The census JSON at `01_02_04_univariate_census.json` is the
  authoritative source for total_rows, NULL rates, numeric stats, categorical
  profiles, boolean census, and field classifications.
- **Assumption:** DuckDB contains the materialized `matches_raw` (277,099,059
  rows) from 01_02_02.
- **Assumption:** I3 classifications from 01_02_06 are authoritative:
  ratingDiff=POST-GAME, rating=AMBIGUOUS (01_02_06 used "RESULT PENDING" in
  the heading but "AMBIGUOUS" in the plot index and statistical test sections;
  we adopt AMBIGUOUS, which also matches the census field_classification
  `ambiguous_pre_or_post`; resolution requires Phase 02 row-level verification
  with ratings_raw, deferred to 01_04), duration_min=POST-GAME (derived from
  `finished` which is post_game per field_classification).
- **Assumption:** DuckDB >= 1.0.0 provides native `SKEWNESS(x)` and
  `KURTOSIS(x)` aggregate functions. The project pins DuckDB 1.5.1 per
  pyproject.toml. `KURTOSIS()` returns excess kurtosis (kurtosis - 3).
- **Unknown:** Exact duplicate count for `GROUP BY id` (id = matchId + profileId
  pair). Expected: very few or zero, since each daily file should contain unique
  player-match rows. The notebook computes this.
- **Unknown:** Exact skewness/kurtosis values for numeric columns. The census
  JSON contains descriptive stats (mean, std, percentiles) but not skewness or
  kurtosis. These are computed via DuckDB native aggregation over the full table.
- **Unknown:** IQR outlier counts for numeric columns. Computed from census
  percentile values (p25, p75) applied to full-table queries.

## Literature Context

Systematic data profiling follows the methodology in Manual Section 3 (derived
from Tukey 1977, Gebru et al. 2021 Datasheets for Datasets, CRISP-DM Phase 2).
QQ plots are the gold standard for normality assessment (Manual 3.4). ECDF
enables formal distributional comparison via KS-test (Manual 3.4). Near-constant
column detection at uniqueness_ratio < 0.001 follows the Manual 3.3 threshold
guideline. IQR fences (1.5 * IQR) are the standard Tukey outlier criterion.

## Execution Steps

### T01 -- ROADMAP and STEP_STATUS Patch

**Objective:** Register step 01_03_01 in ROADMAP.md and STEP_STATUS.yaml.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`.
2. Insert the following Step 01_03_01 YAML block after the Step 01_02_07 block
   (before the "Phase 02" placeholder section). Wrap it in a `### Step 01_03_01`
   heading.

```yaml
step_number: "01_03_01"
name: "Systematic Data Profiling"
description: "Systematic profiling of matches_raw per Manual Section 3. Column-level profiling (null, cardinality, descriptive stats, skewness, kurtosis, IQR outliers, top-k). Dataset-level profiling (duplicates, class balance, completeness matrix, memory footprint). Critical detection (dead fields, constant columns, near-constant columns). Distribution analysis (QQ plots, ECDFs on BERNOULLI sample). All columns carry I3 temporal classification."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "What is the complete statistical profile of every column in matches_raw? Are there dead fields, constant columns, near-constant columns, or primary key violations? What are the distributional shapes of key numeric columns?"
method: "DuckDB aggregate queries for exact column-level stats including native SKEWNESS() and KURTOSIS(). BERNOULLI sampled data for QQ plots and ECDFs. Critical detection via programmatic thresholds from census. I3 classification inherited from 01_02_04 field_classification and 01_02_06 bivariate findings."
stratification: "Full table for aggregate stats. Leaderboard-stratified (rm_1v1 + qp_rm_1v1) for rating analysis."
predecessors:
  - "01_02_04"
  - "01_02_06"
  - "01_02_07"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py"
inputs:
  duckdb_tables:
    - "matches_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
    - "artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  plots:
    - "artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png"
    - "artifacts/01_exploration/03_profiling/01_03_01_qq_plot.png"
    - "artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png"
  report: "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md"
gate:
  artifact_check: "All 5 artifact files exist and are non-empty. JSON contains critical_findings key. MD contains I3 classification table."
  continue_predicate: "Notebook executes end-to-end without error. Profile JSON validates against required schema."
  halt_predicate: "DuckDB queries fail on matches_raw or BERNOULLI sample yields zero rows."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Every column carries I3 temporal classification in both JSON and MD artifacts. POST-GAME and AMBIGUOUS columns flagged in distribution analysis."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "Near-constant threshold (uniqueness_ratio < 0.001 or IQR == 0) from Manual 3.3. Sample fraction justified by Cleveland (1993) and Wilk & Gnanadesikan (1968). IQR fences from census percentiles."
  - number: "9"
    how_upheld: "Profile consolidates and extends 01_02 findings. No new column discovery or schema changes."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

3. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`.
4. Add entry:
```yaml
  "01_03_01":
    name: "Systematic Data Profiling"
    pipeline_section: "01_03"
    status: not_started
```

**Verification:**
- ROADMAP.md contains Step 01_03_01 YAML block after 01_02_07.
- STEP_STATUS.yaml contains `01_03_01` entry with `status: not_started`.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`

---

### T02 -- Create Directory and Notebook Skeleton

**Objective:** Create the profiling directory and notebook with all imports,
DuckDB connection, census JSON load, path constants, sql_queries dict, and I3
classification table. All subsequent tasks build on this cell block.

**Instructions:**
1. Create directory: `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/`
2. Create `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
   with jupytext percent-format header (same kernel metadata as 01_02_07).

**Cell 1 -- markdown header:**
```
# Step 01_03_01 -- Systematic Data Profiling: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** aoe2companion
# **Question:** What is the complete statistical profile of every column
#   in matches_raw? Are there dead fields, constant columns, near-constant
#   columns, or primary key violations?
# **Invariants applied:**
#   - #3 (temporal discipline -- every column labelled with I3 classification)
#   - #6 (reproducibility -- all SQL queries written verbatim to artifacts)
#   - #7 (no magic numbers -- thresholds from Manual 3.3 and census data)
#   - #9 (step scope -- consolidates 01_02 findings into structured profile)
# **Predecessor:** 01_02_07 (Multivariate EDA)
# **Step scope:** Systematic profiling. No DuckDB writes. No new tables.
# **Outputs:** JSON profile, completeness heatmap, QQ plot, ECDF plot, MD report
```

**Cell 2 -- imports:**
```python
import json
import math
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()
matplotlib.use("Agg")
```

**Cell 3 -- DuckDB connection (read-only):**
```python
db = get_notebook_db("aoe2", "aoe2companion")
con = db.con
print("Connected via get_notebook_db: aoe2 / aoe2companion")
```

**Cell 4 -- census JSON load and path setup:**
```python
reports_dir = get_reports_dir("aoe2", "aoe2companion")
census_artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
profiling_dir = reports_dir / "artifacts" / "01_exploration" / "03_profiling"
profiling_dir.mkdir(parents=True, exist_ok=True)

census_json_path = census_artifacts_dir / "01_02_04_univariate_census.json"
with open(census_json_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")
```

**Cell 5 -- assert required census keys (including categorical_profiles per 01_02_07 critique B2):**
```python
required_keys = [
    "matches_raw_total_rows",
    "matches_raw_null_census",
    "matches_raw_numeric_stats",
    "categorical_profiles",
    "boolean_census",
    "field_classification",
    "won_distribution",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"
print(f"All {len(required_keys)} required census keys present")
```

**Cell 6 -- derive I3 classification from census field_classification + 01_02_06 overrides:**
```python
# Build I3 classification for all columns.
# Source: census field_classification (01_02_04) with 01_02_06 overrides.
# 01_02_06 confirmed: ratingDiff=POST-GAME, rating=AMBIGUOUS.
# duration_min is derived (finished - started); finished=post_game per census.
I3_CLASSIFICATION = {}
for entry in census["field_classification"]["fields"]:
    I3_CLASSIFICATION[entry["column"]] = entry["temporal_class"].upper()

# Override with 01_02_06 findings (authoritative)
I3_CLASSIFICATION["ratingDiff"] = "POST_GAME"
I3_CLASSIFICATION["rating"] = "AMBIGUOUS"  # 01_02_06 Q2: heading says "RESULT PENDING",
    # but the plot index and statistical test sections say "AMBIGUOUS", which also
    # matches the census field_classification ("ambiguous_pre_or_post").
    # Treated as AMBIGUOUS in this step; resolution requires Phase 02 row-level
    # verification with ratings_raw (deferred to 01_04).
# duration_min is a derived column (not in raw table); note for later
I3_DURATION_MIN = "POST_GAME"  # finished is POST_GAME

print(f"I3 classifications for {len(I3_CLASSIFICATION)} columns")
for col, cls in sorted(I3_CLASSIFICATION.items()):
    print(f"  {col}: {cls}")
```

**Cell 7 -- initialize sql_queries dict and constants:**
```python
sql_queries = {}

total_rows = census["matches_raw_total_rows"]  # 277,099,059

# I7: BERNOULLI sample fraction for QQ/ECDF distribution visualization.
# 277M rows * 0.02% = ~55,400 rows per sample.
# For QQ normality assessment: Cleveland (1993) recommends N > 1,000 for reliable
# normal probability plots. N=55,400 is 55x that minimum. The SE of the median
# quantile estimate is ~ sigma / (2 * sqrt(N) * f(median)) which is negligible
# at N=55K. Source: Wilk & Gnanadesikan (1968), JSTOR.
SAMPLE_PCT_VIZ = 0.02  # I7: yields ~55K rows at 277M scale
TARGET_SAMPLE_ROWS = int(total_rows * SAMPLE_PCT_VIZ / 100)
print(f"Total rows: {total_rows:,}")
print(f"BERNOULLI sample pct: {SAMPLE_PCT_VIZ}%")
print(f"Expected sample rows: ~{TARGET_SAMPLE_ROWS:,}")

# I7: near-constant thresholds from Manual 3.3
NEAR_CONSTANT_UNIQUENESS_RATIO = 0.001  # Manual 3.3
```

**Verification:**
- Notebook imports and runs through setup without error.
- Census JSON loads and all 7 key assertions pass.
- I3 classification dict populated for all columns.
- Sample percent = 0.02%, expected ~55K rows.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T03 -- Column-Level Profiling (Section 3.1)

**Objective:** Compute per-column profiling metrics for all 55 columns of
matches_raw. Null census, zero census, cardinality, uniqueness ratio. For numeric
columns: descriptive stats, skewness, kurtosis, IQR outlier count. For categorical
columns: top-k (k=5) values.

**Cell 8 -- null and cardinality profile (exact, full table):**
```python
# Reuse census null_census data (exact counts from 01_02_04, full-table scan)
null_census = {
    entry["column_name"]: entry
    for entry in census["matches_raw_null_census"]
}
print(f"Null census columns: {len(null_census)}")
```

**Cell 9 -- zero count for numeric columns (exact, full table):**
```python
numeric_cols = [s["column_name"] for s in census["matches_raw_numeric_stats"]]
print(f"Numeric columns from census: {numeric_cols}")

# Build zero-count query
zero_parts = []
for col in numeric_cols:
    zero_parts.append(f"SUM(CASE WHEN {col} = 0 THEN 1 ELSE 0 END) AS {col}_zero_count")
zero_sql = f"SELECT\n    {','.join(chr(10) + '    ' + p for p in zero_parts)}\nFROM matches_raw"
sql_queries["zero_count_numeric"] = zero_sql
print(f"Executing zero count query for {len(numeric_cols)} numeric columns...")
zero_result = con.execute(zero_sql).fetchdf().iloc[0]
zero_counts = {col: int(zero_result[f"{col}_zero_count"]) for col in numeric_cols}
for col, zc in zero_counts.items():
    pct = zc * 100.0 / total_rows
    print(f"  {col}: {zc:,} zeros ({pct:.2f}%)")
```

**Cell 10 -- skewness and kurtosis via DuckDB native aggregation (exact, full table):**
```python
# DuckDB >= 1.0.0 provides native SKEWNESS(x) and KURTOSIS(x) aggregate functions.
# Project pins DuckDB 1.5.1 (pyproject.toml). These compute exact values over
# all non-NULL rows per column independently -- no sampling error, no listwise
# deletion bias.
# NOTE: DuckDB KURTOSIS() returns EXCESS kurtosis (kurtosis - 3), matching the
# scipy.stats.kurtosis(excess=True) convention. Normal distribution -> 0.

# All 9 numeric columns from census + derived duration_min (10 total)
skew_kurt_sql = """
SELECT
    SKEWNESS(rating) AS rating_skew,
    KURTOSIS(rating) AS rating_kurt,
    SKEWNESS(ratingDiff) AS ratingDiff_skew,
    KURTOSIS(ratingDiff) AS ratingDiff_kurt,
    SKEWNESS(population) AS population_skew,
    KURTOSIS(population) AS population_kurt,
    SKEWNESS(slot) AS slot_skew,
    KURTOSIS(slot) AS slot_kurt,
    SKEWNESS(color) AS color_skew,
    KURTOSIS(color) AS color_kurt,
    SKEWNESS(team) AS team_skew,
    KURTOSIS(team) AS team_kurt,
    SKEWNESS(speedFactor) AS speedFactor_skew,
    KURTOSIS(speedFactor) AS speedFactor_kurt,
    SKEWNESS(treatyLength) AS treatyLength_skew,
    KURTOSIS(treatyLength) AS treatyLength_kurt,
    SKEWNESS(internalLeaderboardId) AS internalLeaderboardId_skew,
    KURTOSIS(internalLeaderboardId) AS internalLeaderboardId_kurt,
    SKEWNESS(EXTRACT(EPOCH FROM (finished - started)) / 60.0)
        FILTER (WHERE finished > started) AS duration_min_skew,
    KURTOSIS(EXTRACT(EPOCH FROM (finished - started)) / 60.0)
        FILTER (WHERE finished > started) AS duration_min_kurt
FROM matches_raw
"""
sql_queries["skewness_kurtosis"] = skew_kurt_sql
print("Computing exact skewness/kurtosis via DuckDB native aggregation...")
sk_result = con.execute(skew_kurt_sql).fetchdf().iloc[0]

# Build skewness_kurtosis dict for all 10 columns
skew_kurt_cols = [
    "rating", "ratingDiff", "population", "slot", "color", "team",
    "speedFactor", "treatyLength", "internalLeaderboardId", "duration_min",
]
skewness_kurtosis = {}
for col in skew_kurt_cols:
    sk_val = sk_result[f"{col}_skew"]
    ku_val = sk_result[f"{col}_kurt"]
    sk_float = round(float(sk_val), 4) if sk_val is not None and not np.isnan(sk_val) else None
    ku_float = round(float(ku_val), 4) if ku_val is not None and not np.isnan(ku_val) else None
    skewness_kurtosis[col] = {
        "skewness": sk_float,
        "kurtosis": ku_float,  # excess kurtosis (DuckDB convention)
    }
    print(f"  {col}: skew={sk_float}, kurtosis(excess)={ku_float}")

print(f"\nExact skewness/kurtosis computed for {len(skewness_kurtosis)} columns "
      f"(full table, {total_rows:,} rows, per-column NULL exclusion)")
```

**Cell 11 -- IQR outlier counts from census percentiles (consolidated single-scan query):**
```python
# I7: IQR fences from census p25/p75 (Tukey 1.5*IQR criterion)
numeric_stats_lookup = {
    s["column_name"]: s for s in census["matches_raw_numeric_stats"]
}

# Pre-compute fences for all columns with IQR > 0
iqr_fences = {}
iqr_outlier_counts = {}
for col in numeric_cols:
    stats = numeric_stats_lookup[col]
    p25 = stats["p25"]
    p75 = stats["p75"]
    iqr = p75 - p25
    if iqr == 0:
        # Near-constant: IQR=0 means any value != p25 is "outlier" by IQR rule
        # but this is misleading for near-constant columns; report as N/A
        iqr_outlier_counts[col] = {
            "iqr": 0.0, "lower_fence": p25, "upper_fence": p75,
            "outlier_count": None,
            "note": "IQR=0 (near-constant); IQR outlier detection not meaningful"
        }
        print(f"  {col}: IQR=0 (near-constant), outlier count N/A")
    else:
        lower_fence = p25 - 1.5 * iqr
        upper_fence = p75 + 1.5 * iqr
        iqr_fences[col] = (lower_fence, upper_fence, iqr)

# W4 fix: consolidated single-scan query for all columns with IQR > 0
if iqr_fences:
    filter_parts = []
    for col, (lower, upper, _) in iqr_fences.items():
        filter_parts.append(
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL "
            f"AND ({col} < {lower} OR {col} > {upper})) AS {col}_iqr_outliers"
        )
    iqr_sql = f"SELECT\n    {','.join(chr(10) + '    ' + p for p in filter_parts)}\nFROM matches_raw"
    sql_queries["iqr_outlier_all"] = iqr_sql
    print(f"Executing consolidated IQR outlier query for {len(iqr_fences)} columns...")
    iqr_result = con.execute(iqr_sql).fetchdf().iloc[0]

    for col, (lower, upper, iqr) in iqr_fences.items():
        outlier_count = int(iqr_result[f"{col}_iqr_outliers"])
        non_null = total_rows - null_census[col]["null_count"]
        outlier_pct = outlier_count * 100.0 / non_null if non_null > 0 else 0.0
        iqr_outlier_counts[col] = {
            "iqr": float(iqr), "lower_fence": float(lower),
            "upper_fence": float(upper),
            "outlier_count": outlier_count,
            "outlier_pct": round(outlier_pct, 4),
        }
        print(f"  {col}: IQR={iqr:.2f}, fences=[{lower:.2f}, {upper:.2f}], "
              f"outliers={outlier_count:,} ({outlier_pct:.2f}%)")
```

**Cell 12 -- top-k (k=5) for categorical columns:**
```python
# Categorical columns: leaderboard, civ, map, gameMode, gameVariant, speed,
# difficulty, startingAge, endingAge, mapSize, resources, victory,
# civilizationSet, revealMap, server, privacy, status, country,
# scenario, modDataset, colorHex
CATEGORICAL_COLS = [
    "leaderboard", "civ", "map", "gameMode", "gameVariant", "speed",
    "difficulty", "startingAge", "endingAge", "mapSize", "resources",
    "victory", "civilizationSet", "revealMap", "server", "privacy",
    "status", "country", "scenario", "modDataset", "colorHex",
]

topk_profiles = {}
K = 5
for col in CATEGORICAL_COLS:
    topk_sql = f"""
SELECT {col} AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / {total_rows}, 2) AS pct
FROM matches_raw
WHERE {col} IS NOT NULL
GROUP BY {col}
ORDER BY cnt DESC
LIMIT {K}
"""
    sql_queries[f"topk_{col}"] = topk_sql
    df_topk = con.execute(topk_sql).fetchdf()
    topk_profiles[col] = df_topk.to_dict(orient="records")

print(f"Top-{K} profiles computed for {len(CATEGORICAL_COLS)} categorical columns")
for col in CATEGORICAL_COLS[:3]:
    print(f"  {col}: {[r['value'] for r in topk_profiles[col]]}")
```

**Cell 13 -- assemble column_profiles list:**
```python
column_profiles = []
for entry in census["matches_raw_null_census"]:
    col = entry["column_name"]
    profile = {
        "column": col,
        "i3_classification": I3_CLASSIFICATION.get(col, "UNKNOWN"),
        "null_count": entry["null_count"],
        "null_pct": entry["null_pct"],
        "cardinality": entry["approx_cardinality"],
        "uniqueness_ratio": round(
            entry["approx_cardinality"] / total_rows, 8
        ),
    }
    # Zero count (numeric only)
    if col in zero_counts:
        profile["zero_count"] = zero_counts[col]
        profile["zero_pct"] = round(zero_counts[col] * 100.0 / total_rows, 4)
    # Descriptive stats (numeric only)
    if col in numeric_stats_lookup:
        ns = numeric_stats_lookup[col]
        profile["mean"] = ns["mean_val"]
        profile["std"] = ns["stddev_val"]
        profile["min"] = ns["min_val"]
        profile["p05"] = ns["p05"]
        profile["p25"] = ns["p25"]
        profile["p50"] = ns["median_val"]
        profile["p75"] = ns["p75"]
        profile["p95"] = ns["p95"]
        profile["max"] = ns["max_val"]
    # Skewness/kurtosis (numeric + duration_min)
    if col in skewness_kurtosis:
        profile["skewness"] = skewness_kurtosis[col]["skewness"]
        profile["kurtosis"] = skewness_kurtosis[col]["kurtosis"]
    # IQR outlier count
    if col in iqr_outlier_counts:
        profile["iqr_outlier"] = iqr_outlier_counts[col]
    # Top-k (categorical)
    if col in topk_profiles:
        profile["top_k"] = topk_profiles[col]
    column_profiles.append(profile)

print(f"Column profiles assembled: {len(column_profiles)} columns")

# Verify all 9 census numeric columns + duration_min have skewness/kurtosis
numeric_with_sk = [p["column"] for p in column_profiles if "skewness" in p]
print(f"Columns with skewness/kurtosis: {len(numeric_with_sk)} "
      f"({', '.join(numeric_with_sk)})")
```

**Verification:**
- column_profiles list has 55 entries (one per matches_raw column).
- All 9 census numeric columns (rating, ratingDiff, population, slot, color, team, speedFactor, treatyLength, internalLeaderboardId) have skewness/kurtosis from exact DuckDB aggregation.
- duration_min (derived) also has skewness/kurtosis.
- Categorical columns have top-k entries.
- Every column has i3_classification.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`

---

### T04 -- Dataset-Level Profiling (Section 3.2)

**Objective:** Compute dataset-level metrics: total row count, duplicate
detection (primary key integrity), class balance, completeness matrix data,
and memory footprint estimate.

**Cell 14 -- duplicate detection (primary key integrity):**
```python
# Primary key = (matchId, profileId) -- each player-match row should be unique
dup_sql = """
SELECT matchId, profileId, COUNT(*) AS cnt
FROM matches_raw
GROUP BY matchId, profileId
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 20
"""
sql_queries["duplicate_detection"] = dup_sql
print("Checking primary key (matchId, profileId) integrity...")
df_dups = con.execute(dup_sql).fetchdf()
n_dup_groups = len(df_dups)
if n_dup_groups > 0:
    total_dup_rows_sql = """
SELECT SUM(cnt) AS total_dup_rows, COUNT(*) AS dup_groups
FROM (
    SELECT matchId, profileId, COUNT(*) AS cnt
    FROM matches_raw
    GROUP BY matchId, profileId
    HAVING COUNT(*) > 1
)
"""
    sql_queries["duplicate_totals"] = total_dup_rows_sql
    dup_totals = con.execute(total_dup_rows_sql).fetchdf().iloc[0]
    dup_info = {
        "has_duplicates": True,
        "dup_groups": int(dup_totals["dup_groups"]),
        "total_dup_rows": int(dup_totals["total_dup_rows"]),
        "sample_dups": df_dups.to_dict(orient="records"),
    }
    print(f"  DUPLICATES FOUND: {dup_info['dup_groups']:,} groups, "
          f"{dup_info['total_dup_rows']:,} total rows")
else:
    dup_info = {"has_duplicates": False, "dup_groups": 0, "total_dup_rows": 0}
    print("  No duplicates found -- primary key is clean")
```

**Cell 15 -- class balance (reuse census won_distribution):**
```python
won_dist = census["won_distribution"]
class_balance = {
    "target_column": "won",
    "distribution": won_dist,
    "note": census.get("exact_won_null_note", {}).get("resolution", ""),
}
for entry in won_dist:
    print(f"  won={entry['won']}: {entry['cnt']:,} ({entry['pct']}%)")
```

**Cell 16 -- completeness matrix data (null_pct per column):**
```python
completeness_data = []
for entry in census["matches_raw_null_census"]:
    completeness_data.append({
        "column": entry["column_name"],
        "null_pct": entry["null_pct"],
        "completeness_pct": round(100.0 - entry["null_pct"], 2),
    })
# Sort by null_pct descending for heatmap ordering
completeness_data.sort(key=lambda x: x["null_pct"], reverse=True)
print(f"Completeness data: {len(completeness_data)} columns")
print(f"Most incomplete: {completeness_data[0]['column']} ({completeness_data[0]['null_pct']}% null)")
print(f"Most complete: {completeness_data[-1]['column']} ({completeness_data[-1]['null_pct']}% null)")
```

**Cell 17 -- memory footprint estimate:**
```python
footprint_sql = """
SELECT
    SUM(compressed_size) AS compressed_bytes,
    SUM(uncompressed_size) AS uncompressed_bytes
FROM pragma_storage_info('matches_raw')
"""
sql_queries["memory_footprint"] = footprint_sql
footprint_result = con.execute(footprint_sql).fetchdf().iloc[0]
memory_footprint = {
    "compressed_bytes": int(footprint_result["compressed_bytes"]),
    "uncompressed_bytes": int(footprint_result["uncompressed_bytes"]),
    "compressed_gb": round(int(footprint_result["compressed_bytes"]) / (1024**3), 2),
    "uncompressed_gb": round(int(footprint_result["uncompressed_bytes"]) / (1024**3), 2),
    "total_rows": total_rows,
}
print(f"Memory footprint: {memory_footprint['compressed_gb']:.2f} GB compressed, "
      f"{memory_footprint['uncompressed_gb']:.2f} GB uncompressed")
```

**Cell 18 -- assemble dataset_profile dict:**
```python
dataset_profile = {
    "total_rows": total_rows,
    "total_columns": len(column_profiles),
    "duplicate_detection": dup_info,
    "class_balance": class_balance,
    "completeness_data": completeness_data,
    "memory_footprint": memory_footprint,
}
print(f"Dataset profile: {total_rows:,} rows, {len(column_profiles)} columns")
```

**Verification:**
- Duplicate detection completes without error.
- Class balance matches census won_distribution.
- Memory footprint produces non-zero byte counts.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T05 -- Critical Detection (Section 3.3)

**Objective:** Identify dead fields (100% null), constant columns
(cardinality=1), and near-constant columns (uniqueness_ratio < 0.001 or IQR=0).
Store results under `critical_findings` key in the profile JSON.

**Cell 19 -- critical detection:**
```python
dead_fields = []
constant_columns = []
near_constant_columns = []

for p in column_profiles:
    col = p["column"]
    # Dead fields: 100% null
    if p["null_pct"] == 100.0:
        dead_fields.append({"column": col, "null_pct": 100.0})

    # Constant columns: cardinality == 1
    if p["cardinality"] == 1:
        constant_columns.append({
            "column": col, "cardinality": 1,
            "null_pct": p["null_pct"],
        })

    # Near-constant: uniqueness_ratio < 0.001 OR IQR == 0 for numeric
    is_near_constant = False
    reasons = []
    if p["uniqueness_ratio"] < NEAR_CONSTANT_UNIQUENESS_RATIO:
        is_near_constant = True
        reasons.append(f"uniqueness_ratio={p['uniqueness_ratio']:.8f} < {NEAR_CONSTANT_UNIQUENESS_RATIO}")
    if "iqr_outlier" in p and p["iqr_outlier"].get("iqr") == 0:
        is_near_constant = True
        reasons.append("IQR=0")
    if is_near_constant and p["cardinality"] > 1:
        near_constant_columns.append({
            "column": col,
            "cardinality": p["cardinality"],
            "uniqueness_ratio": p["uniqueness_ratio"],
            "iqr": p.get("iqr_outlier", {}).get("iqr"),
            "reasons": reasons,
            "i3_classification": p["i3_classification"],
        })

critical_findings = {
    "dead_fields": dead_fields,
    "dead_fields_count": len(dead_fields),
    "constant_columns": constant_columns,
    "constant_columns_count": len(constant_columns),
    "near_constant_columns": near_constant_columns,
    "near_constant_columns_count": len(near_constant_columns),
    "thresholds": {
        "near_constant_uniqueness_ratio": NEAR_CONSTANT_UNIQUENESS_RATIO,
        "iqr_zero_flagged": True,
        "source": "Manual 3.3 + census percentiles (I7)",
    },
}

print(f"Dead fields: {len(dead_fields)}")
for d in dead_fields:
    print(f"  {d['column']}")
print(f"Constant columns: {len(constant_columns)}")
for c in constant_columns:
    print(f"  {c['column']} (null_pct={c['null_pct']}%)")
print(f"Near-constant columns: {len(near_constant_columns)}")
for nc in near_constant_columns:
    print(f"  {nc['column']}: {', '.join(nc['reasons'])}")
```

**Verification:**
- critical_findings dict has all three sub-keys.
- speedFactor, population, treatyLength are flagged as near-constant (IQR=0 per census).
- No runtime errors.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T06 -- Leaderboard-Stratified Rating Profile

**Objective:** Compute rating and ratingDiff stats separately for the full table
and for the 1v1 ranked subset (`leaderboard IN ('rm_1v1', 'qp_rm_1v1')`). This
captures the known rating NULL pattern (42.46%) and its concentration in
non-ranked leaderboards.

**Cell 20 -- stratified rating profile:**
```python
LEADERBOARD_1V1_FILTER = "leaderboard IN ('rm_1v1', 'qp_rm_1v1')"

rating_strat_sql = f"""
SELECT
    'full_table' AS scope,
    COUNT(*) AS n_rows,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) AS rating_null,
    ROUND(SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS rating_null_pct,
    ROUND(AVG(rating), 2) AS rating_mean,
    ROUND(STDDEV(rating), 2) AS rating_std,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating) AS rating_median,
    SUM(CASE WHEN ratingDiff IS NULL THEN 1 ELSE 0 END) AS ratingdiff_null,
    ROUND(AVG(ratingDiff), 4) AS ratingdiff_mean
FROM matches_raw

UNION ALL

SELECT
    '1v1_ranked' AS scope,
    COUNT(*) AS n_rows,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) AS rating_null,
    ROUND(SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS rating_null_pct,
    ROUND(AVG(rating), 2) AS rating_mean,
    ROUND(STDDEV(rating), 2) AS rating_std,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating) AS rating_median,
    SUM(CASE WHEN ratingDiff IS NULL THEN 1 ELSE 0 END) AS ratingdiff_null,
    ROUND(AVG(ratingDiff), 4) AS ratingdiff_mean
FROM matches_raw
WHERE {LEADERBOARD_1V1_FILTER}
"""
sql_queries["rating_stratified"] = rating_strat_sql
df_rating_strat = con.execute(rating_strat_sql).fetchdf()
rating_stratified = df_rating_strat.to_dict(orient="records")
print("Rating stratification:")
for row in rating_stratified:
    print(f"  {row['scope']}: n={row['n_rows']:,}, "
          f"rating_null={row['rating_null_pct']}%, "
          f"rating_mean={row['rating_mean']}, "
          f"ratingdiff_mean={row['ratingdiff_mean']}")
```

**Verification:**
- Two rows returned: full_table and 1v1_ranked.
- 1v1_ranked rating_null_pct expected to be much lower than full table.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T07 -- Completeness Heatmap (Artifact 2)

**Objective:** Produce a completeness heatmap showing null_pct per column,
sorted by missingness severity.

**Cell 21 -- completeness heatmap:**
```python
# Sort columns by null_pct descending
comp_df = pd.DataFrame(completeness_data)
# Only show columns with non-zero null_pct (otherwise heatmap is trivially green)
comp_nonzero = comp_df[comp_df["null_pct"] > 0].copy()
comp_nonzero = comp_nonzero.sort_values("null_pct", ascending=True)

fig, ax = plt.subplots(figsize=(8, max(6, len(comp_nonzero) * 0.35)))
colors = comp_nonzero["null_pct"].values
y_pos = range(len(comp_nonzero))
bars = ax.barh(y_pos, comp_nonzero["null_pct"].values, color=plt.cm.RdYlGn_r(
    comp_nonzero["null_pct"].values / 100.0))
ax.set_yticks(y_pos)
ax.set_yticklabels(comp_nonzero["column"].values, fontsize=8)
ax.set_xlabel("NULL %")
ax.set_title(
    f"Completeness Profile -- aoe2companion matches_raw\n"
    f"({total_rows:,} rows, {len(comp_nonzero)} columns with NULLs "
    f"of {len(comp_df)} total)"
)

# Annotate bars with percentages
for i, (pct, col) in enumerate(zip(comp_nonzero["null_pct"].values, comp_nonzero["column"].values)):
    ax.text(pct + 0.5, i, f"{pct:.1f}%", va="center", fontsize=7)

fig.tight_layout()
heatmap_path = profiling_dir / "01_03_01_completeness_heatmap.png"
fig.savefig(heatmap_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {heatmap_path}")
```

**Verification:**
- `01_03_01_completeness_heatmap.png` exists and is non-empty.
- Columns with 0% null are excluded from the plot (all-complete columns add visual noise).
- Bars are color-coded by severity.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T08 -- QQ Plots (Artifact 3)

**Objective:** Produce QQ plots for key numeric columns against a normal reference
distribution. Uses BERNOULLI sample.

**Cell 22 -- fetch BERNOULLI sample for QQ/ECDF:**
```python
# Shared sample for QQ and ECDF (T08+T09)
# Use a fresh sample with broad NULL tolerance (per-column dropna in plotting)
qq_ecdf_sql = f"""
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI({SAMPLE_PCT_VIZ} PERCENT)
) sub
WHERE finished > started
"""
sql_queries["qq_ecdf_sample"] = qq_ecdf_sql
print("Fetching BERNOULLI sample for QQ/ECDF...")
df_viz = con.execute(qq_ecdf_sql).fetchdf()
n_viz = len(df_viz)
print(f"QQ/ECDF sample rows: {n_viz:,}")
# I7: 5000 minimum for reliable distributional visualization.
# SE of sample quantile at N=5000 is negligible for practical normality assessment.
# Cleveland (1993) recommends N > 1,000 for normal probability plots;
# 5000 provides ~5x safety margin. At N=5000, SE(median) ~ sigma/(2*sqrt(N)*f(median))
# is < 1% of sigma for any symmetric unimodal distribution.
assert n_viz >= 5000, (
    f"QQ/ECDF sample too small: n={n_viz}. "
    f"Expected ~{TARGET_SAMPLE_ROWS:,} rows from BERNOULLI {SAMPLE_PCT_VIZ}%."
)
```

**Cell 23 -- QQ plots:**
```python
qq_columns = ["rating", "ratingDiff", "duration_min", "population", "speedFactor"]
qq_i3_labels = {
    "rating": "AMBIGUOUS",
    "ratingDiff": "POST_GAME",
    "duration_min": "POST_GAME",
    "population": "PRE_GAME",
    "speedFactor": "PRE_GAME",
}

n_cols = len(qq_columns)
fig, axes = plt.subplots(1, n_cols, figsize=(4 * n_cols, 4))
if n_cols == 1:
    axes = [axes]

for ax, col in zip(axes, qq_columns):
    data = df_viz[col].dropna().values
    if len(data) < 10:
        ax.text(0.5, 0.5, f"Insufficient data\n(n={len(data)})",
                transform=ax.transAxes, ha="center", va="center")
        ax.set_title(f"{col}\n[{qq_i3_labels[col]}]", fontsize=9)
        continue
    scipy_stats.probplot(data, dist="norm", plot=ax)
    ax.set_title(f"{col}\n[{qq_i3_labels[col]}]", fontsize=9)
    ax.get_lines()[0].set_markersize(1)
    ax.get_lines()[0].set_alpha(0.3)

fig.suptitle(
    f"QQ Plots (Normal Reference) -- aoe2companion matches_raw\n"
    f"BERNOULLI {SAMPLE_PCT_VIZ}% sample (N={n_viz:,})",
    fontsize=11, y=1.02
)
fig.tight_layout()
qq_path = profiling_dir / "01_03_01_qq_plot.png"
fig.savefig(qq_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {qq_path}")
```

**Verification:**
- `01_03_01_qq_plot.png` exists and is non-empty.
- 5 subplots, each with I3 classification label in title.
- Points plotted with transparency for readability.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T09 -- ECDF Plots (Artifact 4)

**Objective:** Produce ECDF plots for key columns: rating, ratingDiff,
duration_min.

**Cell 24 -- ECDF plots:**
```python
ecdf_columns = ["rating", "ratingDiff", "duration_min"]
ecdf_i3_labels = {
    "rating": "AMBIGUOUS",
    "ratingDiff": "POST_GAME",
    "duration_min": "POST_GAME",
}

fig, axes = plt.subplots(1, len(ecdf_columns), figsize=(5 * len(ecdf_columns), 4))

for ax, col in zip(axes, ecdf_columns):
    data = df_viz[col].dropna().values
    if len(data) < 10:
        ax.text(0.5, 0.5, f"Insufficient data\n(n={len(data)})",
                transform=ax.transAxes, ha="center", va="center")
        ax.set_title(f"ECDF: {col}\n[{ecdf_i3_labels[col]}]", fontsize=9)
        continue
    sorted_data = np.sort(data)
    ecdf_y = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax.step(sorted_data, ecdf_y, where="post", linewidth=1, color="steelblue")
    ax.set_xlabel(col)
    ax.set_ylabel("ECDF")
    ax.set_title(f"ECDF: {col}\n[{ecdf_i3_labels[col]}]", fontsize=9)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)

    # Annotate percentiles from census
    if col in numeric_stats_lookup:
        ns = numeric_stats_lookup[col]
        for pctl, label in [(ns["p05"], "p05"), (ns["p50"], "p50"), (ns["p95"], "p95")]:
            ax.axvline(pctl, color="red", linestyle=":", linewidth=0.5, alpha=0.5)
            ax.text(pctl, 0.02, label, fontsize=6, color="red", rotation=90)

fig.suptitle(
    f"ECDFs -- aoe2companion matches_raw\n"
    f"BERNOULLI {SAMPLE_PCT_VIZ}% sample (N={n_viz:,})",
    fontsize=11, y=1.02
)
fig.tight_layout()
ecdf_path = profiling_dir / "01_03_01_ecdf_key_columns.png"
fig.savefig(ecdf_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {ecdf_path}")
```

**Verification:**
- `01_03_01_ecdf_key_columns.png` exists and is non-empty.
- 3 subplots with I3 labels in titles.
- Census percentile markers overlaid.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T10 -- JSON Profile Assembly and Write (Artifact 1)

**Objective:** Assemble all profiling results into a single JSON file.

**Cell 25 -- assemble and write JSON:**
```python
profile_json = {
    "step": "01_03_01",
    "dataset": "aoe2companion",
    "table": "matches_raw",
    "total_rows": total_rows,
    "total_columns": len(column_profiles),
    "column_profiles": column_profiles,
    "dataset_profile": dataset_profile,
    "critical_findings": critical_findings,
    "rating_stratified": rating_stratified,
    "sample_info": {
        "bernoulli_pct_viz": SAMPLE_PCT_VIZ,
        "skewness_kurtosis_method": "DuckDB native SKEWNESS()/KURTOSIS() -- exact, full table",
        "skewness_kurtosis_columns": len(skewness_kurtosis),
        "kurtosis_convention": "excess kurtosis (kurtosis - 3); DuckDB KURTOSIS() default",
        "qq_ecdf_sample_rows": n_viz,
    },
    "sql_queries": sql_queries,
}

json_path = profiling_dir / "01_03_01_systematic_profile.json"
with open(json_path, "w") as f:
    json.dump(profile_json, f, indent=2, default=str)
print(f"Saved: {json_path} ({json_path.stat().st_size:,} bytes)")
```

**Verification:**
- `01_03_01_systematic_profile.json` exists and is non-empty.
- JSON contains `critical_findings` key.
- JSON contains `column_profiles` with 55 entries.
- JSON contains `sql_queries` dict.
- JSON `sample_info` documents exact skewness/kurtosis method and kurtosis convention.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T11 -- Markdown Report (Artifact 5)

**Objective:** Write the systematic profile markdown with I3 classification
table for all columns, critical findings summary, and all SQL queries.

**Cell 26 -- build and write markdown:**
```python
md_lines = [
    "# Step 01_03_01 -- Systematic Data Profiling: aoe2companion",
    "",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_03 -- Systematic Data Profiling",
    "**Dataset:** aoe2companion",
    "**Predecessor:** 01_02_07 (Multivariate EDA)",
    "**Invariants applied:** #3, #6, #7, #9",
    f"**Table:** matches_raw ({total_rows:,} rows, {len(column_profiles)} columns)",
    "",
    "## I3 Temporal Classification Table",
    "",
    "| Column | I3 Classification | Null % | Cardinality | Uniqueness Ratio | Notes |",
    "|--------|-------------------|--------|-------------|------------------|-------|",
]

for p in column_profiles:
    col = p["column"]
    cls = p["i3_classification"]
    null_pct = p["null_pct"]
    card = p["cardinality"]
    uniq = p["uniqueness_ratio"]
    notes = ""
    # Flag critical findings
    if any(d["column"] == col for d in dead_fields):
        notes = "DEAD FIELD"
    elif any(c["column"] == col for c in constant_columns):
        notes = "CONSTANT"
    elif any(nc["column"] == col for nc in near_constant_columns):
        reasons = [nc for nc in near_constant_columns if nc["column"] == col]
        if reasons:
            notes = f"NEAR-CONSTANT ({', '.join(reasons[0]['reasons'])})"
    md_lines.append(
        f"| {col} | {cls} | {null_pct} | {card:,} | {uniq:.8f} | {notes} |"
    )

md_lines.extend([
    "",
    "## Dataset-Level Summary",
    "",
    f"- **Total rows:** {total_rows:,}",
    f"- **Total columns:** {len(column_profiles)}",
    f"- **Duplicates (matchId, profileId):** {dup_info['dup_groups']:,} groups"
    f" ({dup_info['total_dup_rows']:,} rows)",
    f"- **Memory footprint:** {memory_footprint['compressed_gb']:.2f} GB compressed"
    f" / {memory_footprint['uncompressed_gb']:.2f} GB uncompressed",
    "",
    "### Class Balance (won)",
    "",
    "| won | Count | Pct |",
    "|-----|-------|-----|",
])
for entry in won_dist:
    md_lines.append(f"| {entry['won']} | {entry['cnt']:,} | {entry['pct']}% |")

md_lines.extend([
    "",
    "## Critical Findings",
    "",
    f"- **Dead fields ({len(dead_fields)}):** "
    + (", ".join(d["column"] for d in dead_fields) if dead_fields else "None"),
    f"- **Constant columns ({len(constant_columns)}):** "
    + (", ".join(c["column"] for c in constant_columns) if constant_columns else "None"),
    f"- **Near-constant columns ({len(near_constant_columns)}):** "
    + (", ".join(nc["column"] for nc in near_constant_columns) if near_constant_columns else "None"),
    "",
    f"### Near-constant threshold: uniqueness_ratio < {NEAR_CONSTANT_UNIQUENESS_RATIO} OR IQR == 0 (Manual 3.3, I7)",
    "",
])

# Near-constant detail table
if near_constant_columns:
    md_lines.extend([
        "| Column | Cardinality | Uniqueness Ratio | IQR | Reasons | I3 |",
        "|--------|-------------|------------------|-----|---------|-----|",
    ])
    for nc in near_constant_columns:
        md_lines.append(
            f"| {nc['column']} | {nc['cardinality']} | {nc['uniqueness_ratio']:.8f} "
            f"| {nc['iqr']} | {', '.join(nc['reasons'])} | {nc['i3_classification']} |"
        )
    md_lines.append("")

md_lines.extend([
    "## Rating Stratification",
    "",
    "| Scope | N Rows | Rating NULL % | Rating Mean | Rating Std | Rating Median | RatingDiff Mean |",
    "|-------|--------|---------------|-------------|------------|---------------|-----------------|",
])
for row in rating_stratified:
    md_lines.append(
        f"| {row['scope']} | {row['n_rows']:,} | {row['rating_null_pct']}% "
        f"| {row['rating_mean']} | {row['rating_std']} | {row['rating_median']} "
        f"| {row['ratingdiff_mean']} |"
    )

md_lines.extend([
    "",
    "## Skewness/Kurtosis (Exact, Full Table)",
    "",
    "Computed via DuckDB native `SKEWNESS()` and `KURTOSIS()` aggregate functions",
    "over all non-NULL rows per column (no sampling, no listwise deletion).",
    "Kurtosis values are **excess kurtosis** (kurtosis - 3); normal = 0.",
    "",
    "| Column | Skewness | Kurtosis (excess) | I3 |",
    "|--------|----------|-------------------|-----|",
])
for col in skew_kurt_cols:
    sk_data = skewness_kurtosis[col]
    i3 = I3_CLASSIFICATION.get(col, I3_DURATION_MIN if col == "duration_min" else "UNKNOWN")
    md_lines.append(
        f"| {col} | {sk_data['skewness']} | {sk_data['kurtosis']} | {i3} |"
    )

md_lines.extend([
    "",
    "## Artifact Index",
    "",
    "| # | Artifact | Filename | Description |",
    "|---|----------|----------|-------------|",
    "| 1 | Systematic Profile JSON | `01_03_01_systematic_profile.json` | Machine-readable profile with all metrics |",
    "| 2 | Completeness Heatmap | `01_03_01_completeness_heatmap.png` | NULL rate per column, color-coded |",
    "| 3 | QQ Plots | `01_03_01_qq_plot.png` | Normal reference QQ for 5 numeric columns |",
    "| 4 | ECDF Plots | `01_03_01_ecdf_key_columns.png` | Empirical CDFs for rating, ratingDiff, duration_min |",
    "| 5 | This Report | `01_03_01_systematic_profile.md` | Human-readable summary |",
    "",
    "## SQL Queries (Invariant #6)",
    "",
])

for name, query in sql_queries.items():
    md_lines.extend([f"### {name}", "", "```sql", query.strip(), "```", ""])

md_lines.extend([
    "## Data Sources",
    "",
    f"- `matches_raw` ({total_rows:,} rows) -- DuckDB table from 01_02_02",
    f"- Census JSON: `01_02_04_univariate_census.json`",
    f"- Bivariate findings: `01_02_06_bivariate_eda.md` (I3 classifications)",
    f"- Multivariate findings: `01_02_07_multivariate_analysis.md`",
    f"- Skewness/kurtosis: DuckDB native SKEWNESS()/KURTOSIS() -- exact, full table, "
    f"{len(skewness_kurtosis)} columns",
    f"- BERNOULLI sample: {SAMPLE_PCT_VIZ}% ({n_viz:,} rows for QQ/ECDF visualization)",
    "",
])

md_text = "\n".join(md_lines)
md_path = profiling_dir / "01_03_01_systematic_profile.md"
with open(md_path, "w") as f:
    f.write(md_text)
print(f"Saved: {md_path} ({md_path.stat().st_size:,} bytes)")
```

**Verification:**
- `01_03_01_systematic_profile.md` exists and is non-empty.
- Contains "I3 Temporal Classification Table" with all columns.
- Contains "Critical Findings" section.
- Contains "Skewness/Kurtosis (Exact, Full Table)" section with all 10 columns.
- Contains all SQL queries.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T12 -- Gate Verification and Connection Close

**Objective:** Assert all 5 artifacts exist, JSON schema is valid, MD contains
required sections. Close DuckDB connection.

**Cell 27 -- gate verification:**
```python
expected_artifacts = [
    profiling_dir / "01_03_01_systematic_profile.json",
    profiling_dir / "01_03_01_completeness_heatmap.png",
    profiling_dir / "01_03_01_qq_plot.png",
    profiling_dir / "01_03_01_ecdf_key_columns.png",
    profiling_dir / "01_03_01_systematic_profile.md",
]

for artifact in expected_artifacts:
    assert artifact.exists(), f"Missing artifact: {artifact}"
    assert artifact.stat().st_size > 0, f"Empty artifact: {artifact}"
    print(f"  OK: {artifact.name} ({artifact.stat().st_size:,} bytes)")

# Verify JSON schema
with open(expected_artifacts[0]) as f:
    profile_check = json.load(f)
assert "critical_findings" in profile_check, "JSON missing critical_findings key"
assert "column_profiles" in profile_check, "JSON missing column_profiles key"
assert len(profile_check["column_profiles"]) == len(column_profiles), (
    f"JSON column_profiles count mismatch: {len(profile_check['column_profiles'])} "
    f"vs expected {len(column_profiles)}"
)
print(f"  OK: JSON has critical_findings and {len(profile_check['column_profiles'])} column_profiles")

# Verify JSON sample_info documents skewness/kurtosis method
assert "skewness_kurtosis_method" in profile_check["sample_info"], (
    "JSON sample_info missing skewness_kurtosis_method"
)
assert "exact" in profile_check["sample_info"]["skewness_kurtosis_method"].lower(), (
    "JSON sample_info should document exact skewness/kurtosis computation"
)
print("  OK: JSON documents exact skewness/kurtosis method")

# Verify MD contains I3 classification table
md_check = expected_artifacts[4].read_text()
assert "I3 Temporal Classification Table" in md_check, "MD missing I3 classification table"
assert "Critical Findings" in md_check, "MD missing Critical Findings section"
assert "Skewness/Kurtosis (Exact, Full Table)" in md_check, (
    "MD missing Skewness/Kurtosis section"
)
for qname in sql_queries:
    assert qname in md_check, f"SQL query '{qname}' missing from markdown"
print("  OK: MD contains I3 table, Critical Findings, Skewness/Kurtosis, and all SQL queries")

# Verify every column has i3_classification
for cp in profile_check["column_profiles"]:
    assert "i3_classification" in cp, f"Column {cp['column']} missing i3_classification"
print(f"  OK: All {len(profile_check['column_profiles'])} columns have i3_classification")

# Verify all 9 census numeric columns have skewness/kurtosis in profile
numeric_cols_in_profile = [
    cp["column"] for cp in profile_check["column_profiles"]
    if "skewness" in cp
]
expected_numeric = [
    "rating", "ratingDiff", "population", "slot", "color", "team",
    "speedFactor", "treatyLength", "internalLeaderboardId",
]
for nc in expected_numeric:
    assert nc in numeric_cols_in_profile, (
        f"Numeric column {nc} missing skewness/kurtosis in profile"
    )
print(f"  OK: All {len(expected_numeric)} census numeric columns have skewness/kurtosis")

print("\nAll gate checks passed.")
```

**Cell 28 -- close connection:**
```python
db.close()
print("DuckDB connection closed.")
```

**Verification:**
- All 5 artifacts exist and are non-empty.
- JSON contains `critical_findings` key.
- JSON `column_profiles` has entries for all columns.
- JSON `sample_info` documents exact skewness/kurtosis method.
- MD contains I3 classification table.
- MD contains Skewness/Kurtosis section.
- MD contains all SQL queries.
- Every column profile has `i3_classification`.
- All 9 census numeric columns have skewness/kurtosis.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T13 -- STEP_STATUS Update + Research Log

**Objective:** Mark step 01_03_01 as complete and write a research log entry.

**Instructions:**
1. Update `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`:
   change `01_03_01` status to `complete`, add `completed_at: "<execution date>"`.
2. Prepend a research log entry to
   `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`
   after the header block, before the most recent entry. Entry should include:
   - 5 artifacts produced.
   - Column-level profiling: 55 columns, exact skewness/kurtosis for all 10
     numeric columns (9 from census + duration_min) via DuckDB native
     SKEWNESS()/KURTOSIS() aggregation over full table, top-k for 21
     categorical columns.
   - Dataset-level: duplicate detection result, class balance, memory footprint.
   - Critical findings: dead field count, constant column count, near-constant
     column count (specifically: speedFactor IQR=0, population IQR=0,
     treatyLength IQR=0).
   - Distribution analysis: QQ normality assessment, ECDF characterization
     (BERNOULLI 0.02% sample, ~55K rows).
   - I3 classification applied to all columns. Rating classified as AMBIGUOUS
     (01_02_06 terminology: heading "RESULT PENDING", body "AMBIGUOUS";
     resolution deferred to 01_04).
   - Rating stratification finding (full table vs 1v1 ranked NULL rates).
   - IQR outlier counts computed via single consolidated full-table scan.

**Verification:**
- STEP_STATUS.yaml shows `01_03_01: status: complete`.
- research_log.md has new entry for 01_03_01 at the top.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

---

## File Manifest

| File | Action | Task |
|------|--------|------|
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update | T01 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Update | T01, T13 |
| `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py` | Create | T02--T12 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json` | Create | T10 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png` | Create | T07 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_qq_plot.png` | Create | T08 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png` | Create | T09 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md` | Create | T11 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Update | T13 |

## Gate Condition

All of the following must hold:

1. All 5 artifact files exist under `reports/artifacts/01_exploration/03_profiling/` and are non-empty:
   - `01_03_01_systematic_profile.json`
   - `01_03_01_completeness_heatmap.png`
   - `01_03_01_qq_plot.png`
   - `01_03_01_ecdf_key_columns.png`
   - `01_03_01_systematic_profile.md`
2. JSON contains `critical_findings` key with `dead_fields`, `constant_columns`, and `near_constant_columns` sub-keys.
3. JSON `column_profiles` has entries for all matches_raw columns (55).
4. Every column profile entry has `i3_classification`.
5. All 9 census numeric columns (rating, ratingDiff, population, slot, color, team, speedFactor, treatyLength, internalLeaderboardId) have `skewness` and `kurtosis` in their column profile, computed via DuckDB native aggregation (exact, full table).
6. MD contains "I3 Temporal Classification Table" with all columns.
7. MD contains "Skewness/Kurtosis (Exact, Full Table)" section with all 10 numeric columns.
8. MD contains all SQL queries (Invariant #6).
9. Notebook executes end-to-end without error.
10. STEP_STATUS.yaml shows `01_03_01: status: complete`.
11. research_log.md has entry for 01_03_01.

## Out of Scope

- **New table creation or DuckDB writes.** This step is read-only profiling (I9).
- **Resolving rating temporal ambiguity.** Rating remains AMBIGUOUS per 01_02_06.
  Resolution requires Phase 02 row-level verification with ratings_raw.
- **Cross-dataset comparison.** Deferred to Phase 01 Decision Gate (01_06).
- **Data cleaning.** Profiling findings feed 01_04 but no cleaning rules are applied here.
- **ratings_raw, leaderboard_raw, profiles_raw profiling.** Only matches_raw is the
  prediction-relevant table. Auxiliary tables were characterized in 01_02_04.
- **Feature engineering.** Near-constant findings inform Phase 02 exclusions but
  no features are created here.

## Open Questions

- **How many (matchId, profileId) duplicates exist?** Resolves at execution time.
  Expected: few or zero based on the daily-file ingestion design.
- **What are the exact skewness/kurtosis values for numeric columns?** The census
  has mean/std/percentiles but not shape statistics. Computed via DuckDB native
  `SKEWNESS()`/`KURTOSIS()` over the full table (exact, not sampled).
- **Does the rating NULL rate differ significantly between 1v1 ranked and full table?**
  Computed in T06. Expected: much lower in 1v1 ranked (most NULLs are in unranked
  and team leaderboards).
```

---

For Category A, adversarial critique is required before execution. Dispatch reviewer-adversarial to produce `planning/plan_aoe2companion_01_03_01.critique.md`.

---

**Key files referenced:**

- `/Users/tomaszpionka/Projects/rts-outcome-prediction/.claude/scientific-invariants.md` -- 10 invariants, I3/I6/I7/I9 most relevant
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md` -- Manual Section 3 is the methodology source
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` -- step 01_03_01 to be added
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` -- authoritative census data (277M rows, 55 columns, null rates, numeric stats, field_classification, categorical_profiles, boolean_census)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md` -- I3 classification overrides (ratingDiff=POST-GAME, rating=AMBIGUOUS)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/planning/plan_aoe2companion_01_02_07.md` -- format reference for the task structure
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/common/notebook_utils.py` -- `get_notebook_db()` returns `DuckDBClient` with `.con` property; `get_reports_dir()` returns reports path
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/common/db.py` -- `DuckDBClient` class with `.con` property and `.fetch_df()` method
