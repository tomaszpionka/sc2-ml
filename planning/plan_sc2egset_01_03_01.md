---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [3, 6, 7, 9]
critique_required: true
source_artifacts:
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/map_aliases_raw.yaml"
  - "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_07_multivariate_eda.py"
  - "planning/plan_sc2egset_01_02_07.md"
research_log_ref: "src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-04-15-phase01-01_03_01"
---

# Plan: sc2egset Step 01_03_01 -- Systematic Data Profiling

## Scope

**Phase/Step:** 01 / 01_03_01
**Branch:** feat/census-pass3
**Action:** CREATE (new step and new pipeline section -- no prior 01_03 artifacts exist)
**Predecessor:** 01_02_07 (Multivariate EDA -- complete, artifacts on disk)

Create a systematic data profiling notebook that produces column-level profiles
(null/zero/cardinality/stats/skewness/kurtosis/IQR-outliers/top-k) for all three
sc2egset raw tables, dataset-level quality metrics (duplicates, class balance,
completeness matrix, cross-table linkage, memory footprint), critical field
detection (dead/constant/near-constant), and distribution analysis (QQ plots,
ECDFs). Output: 1 JSON profile, 1 completeness heatmap, 1 QQ multi-panel, 1
ECDF multi-panel, 1 markdown summary, ROADMAP patch, STEP_STATUS update,
research log entry.

This is the first step of pipeline section 01_03 (Systematic Data Profiling).

## Problem Statement

Steps 01_02_01 through 01_02_07 completed the Tukey-style EDA: univariate
census, visualizations, bivariate analysis, and multivariate analysis. These
steps were exploratory -- they surfaced patterns, sentinels, and anomalies
through visual inspection and summary statistics.

Step 01_03_01 transitions to **systematic profiling** (Manual 01, Section 3):
a structured, machine-readable profile of every column in every table, with
formal detection rules for dead fields, constant columns, near-constant columns,
and IQR outliers. The key differences from 01_02_04 (univariate census) are:

1. **Broader scope:** Profiles all three tables (replay_players_raw,
   replays_meta_raw struct-flat fields, map_aliases_raw), not just
   replay_players_raw.
2. **Formal detection rules:** Dead fields (null_pct == 100%), constant columns
   (cardinality == 1), near-constant (uniqueness_ratio < 0.001 OR IQR == 0),
   IQR outlier counts -- not just flagging but structured JSON output.
3. **Distribution analysis:** QQ plots and ECDFs for key numeric columns,
   providing normality assessment that feeds Phase 02 feature engineering
   decisions.
4. **Cross-table linkage:** Verifying referential integrity between
   replay_players_raw and replays_meta_raw via replayId (derived from filename).
5. **Completeness heatmap:** Visual summary of null rates across all columns
   and tables in a single figure.

The sc2egset data has zero NULLs across all tables (confirmed by 01_02_04
census), but it has sentinel values (MMR=0 for 83.65% of rows, SQ=INT32_MIN
for 2 rows) that function as effective missingness. The profiling must report
both physical NULLs and sentinel-based effective missingness.

## Assumptions & Unknowns

- **Assumption:** Census JSON at
  `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the source of truth for all sentinel thresholds and field classifications.
- **Assumption:** All three raw tables exist in the persistent DuckDB at
  `src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb`.
- **Assumption:** replay_players_raw has 44,817 rows (2 per replay for 22,390
  replays, plus 37 3+ player replays), 25 columns.
- **Assumption:** replays_meta_raw has 22,390 rows, 9 top-level columns. The
  `struct` column contains nested STRUCTs with 17 extractable scalar fields
  (per 01_02_04 struct_flat census: time_utc, game_speed_init, messageEventsErr,
  gameEventsErr, map_size_y, map_size_x, is_blizzard_map_init, is_blizzard_map,
  game_speed, elapsed_game_loops, max_players, map_name, game_version_meta,
  data_build, base_build, game_version_header, trackerEvtsErr). Note:
  gameEventsErr, messageEventsErr, trackerEvtsErr also exist as top-level
  columns -- the struct-flat versions are profiled here.
- **Assumption:** map_aliases_raw has 104,160 rows, 4 columns (tournament,
  foreign_name, english_name, filename). Per 01_02_01, all 70 tournament
  mapping files are identical (1,488 keys each): 70 * 1,488 = 104,160.
- **Assumption:** The 5 constant columns (game_speed, game_speed_init,
  gameEventsErr, messageEventsErr, trackerEvtsErr) have cardinality=1 per
  01_02_04 census.
- **Assumption:** `elapsed_game_loops` is classified as POST-GAME per the
  2026-04-15 retroactive reclassification. All profiling output must annotate
  it as POST-GAME.
- **Unknown:** Whether map_aliases_raw has any NULL values. Census 01_02_04
  did not profile map_aliases_raw null counts. Resolved during execution (T04).
- **Unknown:** Whether cross-table linkage is perfect (every replay_players_raw
  row has a matching replayId in replays_meta_raw). Expected: yes (both tables
  ingested from the same 22,390 files). Resolved during execution (T05).

## Literature Context

- Systematic data profiling methodology follows Abedjan et al. (2015),
  "Profiling Relational Data: A Survey" -- column-level profiling (single-column
  statistics, value distributions, pattern analysis) and multi-column profiling
  (functional dependencies, cross-table linkage).
- QQ plots for normality assessment follow D'Agostino & Stephens (1986),
  "Goodness-of-fit Techniques." The theoretical quantile-quantile plot against a
  normal distribution is the standard visual check before selecting parametric
  vs nonparametric methods in Phase 02/03.
- IQR-based outlier detection uses the Tukey fence: observations below
  Q1 - 1.5*IQR or above Q3 + 1.5*IQR (Tukey, 1977, "Exploratory Data
  Analysis"). This is a threshold with literature precedent (I7 compliance).
- ECDF (empirical cumulative distribution function) plots provide a
  non-parametric view of the full distribution shape without binning artifacts
  that affect histograms (Wilk & Gnanadesikan, 1968).

## Execution Steps

### T01 -- ROADMAP Patch

**Objective:** Add step 01_03_01 definition to the sc2egset ROADMAP. This is the
first step in pipeline section 01_03, so the section header must also be added.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`.
2. After the 01_02_07 step definition block and before `## Phase 02`, insert:

```yaml
### Step 01_03_01 -- Systematic Data Profiling

step_number: "01_03_01"
name: "Systematic Data Profiling"
description: "Column-level and dataset-level profiling of all three sc2egset raw tables (replay_players_raw, replays_meta_raw struct-flat fields, map_aliases_raw). Detects dead fields, constant columns, near-constant columns, IQR outliers. Produces QQ plots and ECDFs for key numeric columns. Cross-table linkage check via replayId."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "sc2egset"
question: "What is the full column-level and dataset-level quality profile of all sc2egset raw tables, including dead fields, constant columns, outlier rates, and distribution shapes?"
method: "DuckDB SQL aggregations: NULL/zero census per column per table, cardinality, descriptive stats, skewness/kurtosis, IQR outlier detection (Tukey fence at 1.5*IQR). QQ plots against normal distribution for 5 key columns. ECDFs for 3 key columns. Cross-table linkage via replayId derived from filename. Completeness heatmap across all tables."
predecessors: "01_02_07"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
    - "replays_meta_raw"
    - "map_aliases_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  plots:
    - "artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png"
    - "artifacts/01_exploration/03_profiling/01_03_01_qq_plots.png"
    - "artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png"
  report: "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Every column carries I3 temporal classification. elapsed_game_loops annotated as POST-GAME. APM, SQ, supplyCappedPercent annotated as IN-GAME."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "IQR fence multiplier 1.5 cited to Tukey (1977). All sentinel thresholds derived from census JSON at runtime."
  - number: "9"
    how_upheld: "Profiling of existing tables only. No new feature computation. Builds on 01_02_04 census and all 01_02 EDA findings."
gate:
  artifact_check: "All 5 artifacts (JSON, 3 PNGs, MD) exist and are non-empty."
  continue_predicate: "JSON contains critical_findings key with constant_columns list of exactly 5 entries. MD contains I3 classification table. All PNG files exist."
  halt_predicate: "Any artifact is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

**Verification:**
- ROADMAP.md contains a `### Step 01_03_01` section with the full YAML block.
- The step is positioned after 01_02_07 and before Phase 02.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`

---

### T02 -- Directory Creation and Notebook Setup

**Objective:** Create the profiling subdirectory, notebook file with imports,
DuckDB connection via `get_notebook_db`, census JSON load, and all runtime
constants derived from census (I7). Also create the artifact output directory.

**Instructions:**
1. Create directory `sandbox/sc2/sc2egset/01_exploration/03_profiling/`.
2. Create `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
   as a jupytext percent-format notebook.

**Cell 1 -- markdown header:**
```
# Step 01_03_01 -- Systematic Data Profiling
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** sc2egset
# **Question:** What is the full column-level and dataset-level quality
# profile of all sc2egset raw tables?
# **Invariants applied:** #3 (I3 temporal classification on every column),
# #6 (all SQL stored verbatim), #7 (all thresholds data-derived or cited),
# #9 (profiling only, no new feature computation)
# **Predecessor:** 01_02_07 (Multivariate EDA -- complete)
# **Type:** Read-only -- no DuckDB writes
```

**Cell 2 -- imports:**
```python
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

matplotlib.use("Agg")
logger = setup_notebook_logging()
```

**Cell 3 -- DuckDB connection:**
```python
conn = get_notebook_db("sc2", "sc2egset")
```

**Cell 4 -- census load and runtime constants (I7):**
```python
reports_dir = get_reports_dir("sc2", "sc2egset")
census_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "02_eda"
    / "01_02_04_univariate_census.json"
)
with open(census_json_path) as f:
    census = json.load(f)

# --- Runtime constants from census (Invariant #7) ---
RP_TOTAL_ROWS = census["null_census"]["replay_players_raw"]["total_rows"]
print(f"replay_players_raw total rows: {RP_TOTAL_ROWS}")

RM_TOTAL_ROWS = census["null_census"]["replays_meta_raw_filename"]["total_rows"]
print(f"replays_meta_raw total rows: {RM_TOTAL_ROWS}")

MMR_ZERO_COUNT = census["zero_counts"]["replay_players_raw"]["MMR_zero"]
MMR_ZERO_PCT = round(100.0 * MMR_ZERO_COUNT / RP_TOTAL_ROWS, 2)
print(f"MMR zero sentinel: {MMR_ZERO_COUNT} rows ({MMR_ZERO_PCT}%)")

SQ_SENTINEL_COUNT = census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]
INT32_MIN = int(np.iinfo(np.int32).min)
print(f"SQ sentinel (INT32_MIN={INT32_MIN}): {SQ_SENTINEL_COUNT} rows")

result_dist = {r["result"]: r["cnt"] for r in census["result_distribution"]}
N_WIN = result_dist["Win"]
N_LOSS = result_dist["Loss"]
N_UNDECIDED = result_dist.get("Undecided", 0)
N_TIE = result_dist.get("Tie", 0)
N_WINLOSS = N_WIN + N_LOSS
print(f"Win/Loss rows: {N_WINLOSS} (excluding {N_UNDECIDED} Undecided, {N_TIE} Tie)")

# I3 temporal classification from census field_classification
FIELD_CLASSIFICATION = census["field_classification"]

# Output directories
artifact_dir = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
)
artifact_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifact dir: {artifact_dir}")
```

**Cell 5 -- SQL queries dict (I6):**
This cell defines ALL SQL queries used in the notebook. Every query that
produces a reported result is stored here and written verbatim to the markdown
artifact.

```python
sql_queries = {}
```

The individual queries are defined in T03-T07 and appended to this dict.

**Verification:**
- Notebook runs through T02 cells without error.
- Census loads and all constants printed.
- `conn`, `census`, `sql_queries`, `artifact_dir` all defined.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T03 -- Column-Level Profiling: replay_players_raw

**Objective:** Produce the full column-level profile for replay_players_raw
(25 columns): null_count, null_pct, zero_count, zero_pct, cardinality,
uniqueness_ratio, descriptive stats (numeric), skewness, kurtosis, IQR outlier
count (numeric), top-k (k=5, categorical).

**Instructions:**

**Cell 6 -- replay_players_raw column-level profiling SQL:**

For numeric columns, use a single SQL query that computes all stats in one pass:

```python
sql_queries["rp_numeric_profile"] = f"""
WITH base AS (
    SELECT *
    FROM replay_players_raw
)
SELECT
    'MMR' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(MMR) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(MMR)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN MMR = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN MMR = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT MMR) AS cardinality,
    ROUND(COUNT(DISTINCT MMR)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(MMR) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY MMR) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY MMR) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY MMR) AS p95,
    MAX(MMR) AS max_val,
    ROUND(AVG(MMR), 4) AS mean_val,
    ROUND(STDDEV(MMR), 4) AS std_val,
    ROUND(SKEWNESS(MMR), 4) AS skewness,
    ROUND(KURTOSIS(MMR), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'MMR_rated_only' AS column_name,
    SUM(CASE WHEN MMR > 0 THEN 1 ELSE 0 END) AS n_rows,
    0 AS null_count,
    0.0 AS null_pct,
    0 AS zero_count,
    0.0 AS zero_pct,
    COUNT(DISTINCT CASE WHEN MMR > 0 THEN MMR END) AS cardinality,
    ROUND(COUNT(DISTINCT CASE WHEN MMR > 0 THEN MMR END)::DOUBLE
          / NULLIF(SUM(CASE WHEN MMR > 0 THEN 1 ELSE 0 END), 0), 6) AS uniqueness_ratio,
    MIN(CASE WHEN MMR > 0 THEN MMR END) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p95,
    MAX(CASE WHEN MMR > 0 THEN MMR END) AS max_val,
    ROUND(AVG(CASE WHEN MMR > 0 THEN MMR END), 4) AS mean_val,
    ROUND(STDDEV(CASE WHEN MMR > 0 THEN MMR END), 4) AS std_val,
    ROUND(SKEWNESS(MMR) FILTER (WHERE MMR > 0), 4) AS skewness,
    ROUND(KURTOSIS(MMR) FILTER (WHERE MMR > 0), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'APM' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(APM) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(APM)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN APM = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN APM = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT APM) AS cardinality,
    ROUND(COUNT(DISTINCT APM)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(APM) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY APM) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY APM) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY APM) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY APM) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY APM) AS p95,
    MAX(APM) AS max_val,
    ROUND(AVG(APM), 4) AS mean_val,
    ROUND(STDDEV(APM), 4) AS std_val,
    ROUND(SKEWNESS(APM), 4) AS skewness,
    ROUND(KURTOSIS(APM), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'SQ' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(SQ) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(SQ)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN SQ = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN SQ = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT SQ) AS cardinality,
    ROUND(COUNT(DISTINCT SQ)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(SQ) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY SQ) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) AS p95,
    MAX(SQ) AS max_val,
    ROUND(AVG(SQ), 4) AS mean_val,
    ROUND(STDDEV(SQ), 4) AS std_val,
    ROUND(SKEWNESS(SQ), 4) AS skewness,
    ROUND(KURTOSIS(SQ), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'SQ_no_sentinel' AS column_name,
    SUM(CASE WHEN SQ > {INT32_MIN} THEN 1 ELSE 0 END) AS n_rows,
    0 AS null_count,
    0.0 AS null_pct,
    SUM(CASE WHEN SQ = 0 AND SQ > {INT32_MIN} THEN 1 ELSE 0 END) AS zero_count,
    0.0 AS zero_pct,
    COUNT(DISTINCT CASE WHEN SQ > {INT32_MIN} THEN SQ END) AS cardinality,
    ROUND(COUNT(DISTINCT CASE WHEN SQ > {INT32_MIN} THEN SQ END)::DOUBLE
          / NULLIF(SUM(CASE WHEN SQ > {INT32_MIN} THEN 1 ELSE 0 END), 0), 6) AS uniqueness_ratio,
    MIN(CASE WHEN SQ > {INT32_MIN} THEN SQ END) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p95,
    MAX(CASE WHEN SQ > {INT32_MIN} THEN SQ END) AS max_val,
    ROUND(AVG(CASE WHEN SQ > {INT32_MIN} THEN SQ END), 4) AS mean_val,
    ROUND(STDDEV(CASE WHEN SQ > {INT32_MIN} THEN SQ END), 4) AS std_val,
    ROUND(SKEWNESS(SQ) FILTER (WHERE SQ > {INT32_MIN}), 4) AS skewness,
    ROUND(KURTOSIS(SQ) FILTER (WHERE SQ > {INT32_MIN}), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'supplyCappedPercent' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(supplyCappedPercent) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(supplyCappedPercent)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN supplyCappedPercent = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN supplyCappedPercent = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT supplyCappedPercent) AS cardinality,
    ROUND(COUNT(DISTINCT supplyCappedPercent)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(supplyCappedPercent) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p95,
    MAX(supplyCappedPercent) AS max_val,
    ROUND(AVG(supplyCappedPercent), 4) AS mean_val,
    ROUND(STDDEV(supplyCappedPercent), 4) AS std_val,
    ROUND(SKEWNESS(supplyCappedPercent), 4) AS skewness,
    ROUND(KURTOSIS(supplyCappedPercent), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'handicap' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(handicap) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(handicap)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN handicap = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN handicap = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT handicap) AS cardinality,
    ROUND(COUNT(DISTINCT handicap)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(handicap) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY handicap) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY handicap) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY handicap) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY handicap) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY handicap) AS p95,
    MAX(handicap) AS max_val,
    ROUND(AVG(handicap), 4) AS mean_val,
    ROUND(STDDEV(handicap), 4) AS std_val,
    ROUND(SKEWNESS(handicap), 4) AS skewness,
    ROUND(KURTOSIS(handicap), 4) AS kurtosis
FROM base
"""
```

**Cell 7 -- replay_players_raw null/cardinality profile for all columns:**
```python
sql_queries["rp_null_cardinality"] = """
SELECT
    column_name,
    COUNT(*) - COUNT(col_val) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(col_val)) / COUNT(*), 4) AS null_pct,
    COUNT(DISTINCT col_val) AS cardinality,
    ROUND(COUNT(DISTINCT col_val)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio
FROM (
    UNPIVOT replay_players_raw
    ON COLUMNS(*)
    INTO NAME column_name VALUE col_val
)
GROUP BY column_name
ORDER BY column_name
"""

# W-02: if UNPIVOT causes type coercion errors, fall back to per-column UNION ALL.
# The fallback SQL is stored in sql_queries["rp_null_cardinality_fallback"].
sql_queries["rp_null_cardinality_fallback"] = """
-- Fallback if UNPIVOT fails due to mixed-type coercion issues:
-- Per-column UNION ALL for null/cardinality profiling of replay_players_raw
SELECT 'replayId' AS col, COUNT(*) AS total, COUNT(replayId) AS non_null,
       COUNT(DISTINCT replayId) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'result' AS col, COUNT(*) AS total, COUNT(result) AS non_null,
       COUNT(DISTINCT result) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'MMR' AS col, COUNT(*) AS total, COUNT(MMR) AS non_null,
       COUNT(DISTINCT MMR) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'APM' AS col, COUNT(*) AS total, COUNT(APM) AS non_null,
       COUNT(DISTINCT APM) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'SQ' AS col, COUNT(*) AS total, COUNT(SQ) AS non_null,
       COUNT(DISTINCT SQ) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'supplyCappedPercent' AS col, COUNT(*) AS total, COUNT(supplyCappedPercent) AS non_null,
       COUNT(DISTINCT supplyCappedPercent) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'handicap' AS col, COUNT(*) AS total, COUNT(handicap) AS non_null,
       COUNT(DISTINCT handicap) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'race' AS col, COUNT(*) AS total, COUNT(race) AS non_null,
       COUNT(DISTINCT race) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'selectedRace' AS col, COUNT(*) AS total, COUNT(selectedRace) AS non_null,
       COUNT(DISTINCT selectedRace) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'highestLeague' AS col, COUNT(*) AS total, COUNT(highestLeague) AS non_null,
       COUNT(DISTINCT highestLeague) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'region' AS col, COUNT(*) AS total, COUNT(region) AS non_null,
       COUNT(DISTINCT region) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'realm' AS col, COUNT(*) AS total, COUNT(realm) AS non_null,
       COUNT(DISTINCT realm) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'isInClan' AS col, COUNT(*) AS total, COUNT(isInClan) AS non_null,
       COUNT(DISTINCT isInClan) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'clanTag' AS col, COUNT(*) AS total, COUNT(clanTag) AS non_null,
       COUNT(DISTINCT clanTag) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'playerID' AS col, COUNT(*) AS total, COUNT(playerID) AS non_null,
       COUNT(DISTINCT playerID) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'userID' AS col, COUNT(*) AS total, COUNT(userID) AS non_null,
       COUNT(DISTINCT userID) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'toon_id' AS col, COUNT(*) AS total, COUNT(toon_id) AS non_null,
       COUNT(DISTINCT toon_id) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'uid' AS col, COUNT(*) AS total, COUNT(uid) AS non_null,
       COUNT(DISTINCT uid) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'color_r' AS col, COUNT(*) AS total, COUNT(color_r) AS non_null,
       COUNT(DISTINCT color_r) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'color_g' AS col, COUNT(*) AS total, COUNT(color_g) AS non_null,
       COUNT(DISTINCT color_g) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'color_b' AS col, COUNT(*) AS total, COUNT(color_b) AS non_null,
       COUNT(DISTINCT color_b) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'color_a' AS col, COUNT(*) AS total, COUNT(color_a) AS non_null,
       COUNT(DISTINCT color_a) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'startDir' AS col, COUNT(*) AS total, COUNT(startDir) AS non_null,
       COUNT(DISTINCT startDir) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'filename' AS col, COUNT(*) AS total, COUNT(filename) AS non_null,
       COUNT(DISTINCT filename) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'name' AS col, COUNT(*) AS total, COUNT(name) AS non_null,
       COUNT(DISTINCT name) AS cardinality FROM replay_players_raw
"""
```

Note: Try the UNPIVOT query first. If it fails due to type coercion issues
across mixed VARCHAR/INTEGER/BIGINT/BOOLEAN columns, use the UNION ALL
fallback. Both produce the same result (null count and cardinality per column).

**Cell 8 -- replay_players_raw categorical top-k (k=5):**
```python
CATEGORICAL_COLS_RP = [
    "result", "race", "selectedRace", "highestLeague",
    "region", "realm", "isInClan", "clanTag",
]

sql_queries["rp_topk"] = {}
for col in CATEGORICAL_COLS_RP:
    sql_queries["rp_topk"][col] = f"""
    SELECT
        CAST({col} AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / {RP_TOTAL_ROWS}, 4) AS pct
    FROM replay_players_raw
    GROUP BY {col}
    ORDER BY cnt DESC
    LIMIT 5
    """
```

**Cell 9 -- replay_players_raw IQR outlier counts for numeric columns:**
```python
NUMERIC_COLS_RP = ["MMR", "APM", "SQ", "supplyCappedPercent", "handicap"]

sql_queries["rp_iqr_outliers"] = f"""
WITH stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS mmr_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS mmr_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY APM) AS apm_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY APM) AS apm_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS sq_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS sq_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY supplyCappedPercent) AS sc_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY supplyCappedPercent) AS sc_q3
    FROM replay_players_raw
)
SELECT
    SUM(CASE WHEN MMR < (s.mmr_q1 - 1.5 * (s.mmr_q3 - s.mmr_q1))
              OR MMR > (s.mmr_q3 + 1.5 * (s.mmr_q3 - s.mmr_q1))
         THEN 1 ELSE 0 END) AS mmr_iqr_outliers,
    SUM(CASE WHEN APM < (s.apm_q1 - 1.5 * (s.apm_q3 - s.apm_q1))
              OR APM > (s.apm_q3 + 1.5 * (s.apm_q3 - s.apm_q1))
         THEN 1 ELSE 0 END) AS apm_iqr_outliers,
    SUM(CASE WHEN SQ > {INT32_MIN}
              AND (SQ < (s.sq_q1 - 1.5 * (s.sq_q3 - s.sq_q1))
                   OR SQ > (s.sq_q3 + 1.5 * (s.sq_q3 - s.sq_q1)))
         THEN 1 ELSE 0 END) AS sq_iqr_outliers,
    SUM(CASE WHEN supplyCappedPercent < (s.sc_q1 - 1.5 * (s.sc_q3 - s.sc_q1))
              OR supplyCappedPercent > (s.sc_q3 + 1.5 * (s.sc_q3 - s.sc_q1))
         THEN 1 ELSE 0 END) AS sc_iqr_outliers
FROM replay_players_raw, stats s
"""

# W-03 fix: IQR for MMR-all is degenerate (Q1=Q3=0 -> IQR=0 -> every MMR>0 is an "outlier").
# The rated-only variant provides a meaningful IQR outlier count.
sql_queries["rp_iqr_outliers_mmr_rated"] = """
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS mmr_p25_rated,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS mmr_p75_rated,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) -
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS mmr_iqr_rated,
    COUNT(*) FILTER (
        WHERE MMR < PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) - 1.5 * (
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) -
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR)
        )
        OR MMR > PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) + 1.5 * (
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) -
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR)
        )
    ) AS mmr_iqr_outliers_rated
FROM replay_players_raw
WHERE MMR > 0
"""
```

Note: IQR fences use 1.5 * IQR multiplier per Tukey (1977) -- I7 compliance.
For MMR-all, the IQR is 0 (Q1=Q3=0 for all rows), so every MMR>0 row is
flagged as an "outlier" -- this is a degenerate result, not a meaningful outlier
count. The rated-only variant (`rp_iqr_outliers_mmr_rated`, WHERE MMR > 0)
provides a meaningful IQR outlier count. Both are reported in the JSON artifact:
`replay_players_raw.MMR.iqr_outliers_all` (degenerate) and
`replay_players_raw.MMR.iqr_outliers_rated_only` (meaningful). The markdown
artifact documents: "MMR IQR outlier count for all rows is degenerate (IQR=0
since Q1=Q3=0); rated-only (MMR>0) IQR outlier count is also reported." SQ
excludes INT32_MIN sentinel rows from IQR computation.

Execute all queries and collect results into a `profile_rp` dict.

**Verification:**
- `profile_rp` dict populated with numeric stats, null/cardinality, top-k, IQR outliers.
- MMR stats reported BOTH including and excluding MMR=0.
- SQ stats reported BOTH including and excluding INT32_MIN sentinel.
- MMR IQR outlier count reported BOTH for all rows (degenerate) and rated-only.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T02 outputs (conn, census, sql_queries, constants)

---

### T04 -- Column-Level Profiling: replays_meta_raw (STRUCT-Flat) and map_aliases_raw

**Objective:** Profile the 17 struct-flat fields from replays_meta_raw and all 4
columns of map_aliases_raw. For replays_meta_raw, access STRUCT fields via
DuckDB dot-notation (e.g., `struct.details.gameSpeed`).

**Instructions:**

**Cell 10 -- replays_meta_raw struct-flat profiling:**

Access struct fields via the actual column paths in replays_meta_raw. The table
has these STRUCT columns per the schema YAML:
- `details` -> details.gameSpeed, details.isBlizzardMap, details.timeUTC
- `header` -> header.elapsedGameLoops, header."version"
- `initData` -> initData.gameDescription.gameOptions.* (multiple nested fields),
  initData.gameDescription.gameSpeed, initData.gameDescription.isBlizzardMap,
  initData.gameDescription.mapAuthorName, initData.gameDescription.mapFileSyncChecksum,
  initData.gameDescription.mapSizeX, initData.gameDescription.mapSizeY,
  initData.gameDescription.maxPlayers
- `metadata` -> metadata.baseBuild, metadata.dataBuild, metadata.gameVersion,
  metadata.mapName
- Top-level: `gameEventsErr`, `messageEventsErr`, `trackerEvtsErr`, `filename`

Profile the same 17+1 fields that 01_02_04 profiled as "struct_flat":
time_utc (details.timeUTC), game_speed_init (initData.gameDescription.gameSpeed),
messageEventsErr, gameEventsErr, map_size_y, map_size_x, is_blizzard_map_init,
is_blizzard_map (details.isBlizzardMap), game_speed (details.gameSpeed),
elapsed_game_loops (header.elapsedGameLoops), max_players, map_name (metadata.mapName),
game_version_meta (metadata.gameVersion), data_build, base_build, game_version_header
(header."version"), trackerEvtsErr.

```python
sql_queries["rm_struct_profile"] = """
SELECT
    COUNT(*) AS n_rows,
    -- elapsed_game_loops (POST-GAME)
    COUNT(*) - COUNT(header.elapsedGameLoops) AS elapsed_game_loops_null,
    COUNT(DISTINCT header.elapsedGameLoops) AS elapsed_game_loops_cardinality,
    MIN(header.elapsedGameLoops) AS elapsed_game_loops_min,
    MAX(header.elapsedGameLoops) AS elapsed_game_loops_max,
    ROUND(AVG(header.elapsedGameLoops), 4) AS elapsed_game_loops_mean,
    ROUND(STDDEV(header.elapsedGameLoops), 4) AS elapsed_game_loops_std,
    ROUND(SKEWNESS(header.elapsedGameLoops), 4) AS elapsed_game_loops_skew,
    ROUND(KURTOSIS(header.elapsedGameLoops), 4) AS elapsed_game_loops_kurt,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS elapsed_game_loops_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS elapsed_game_loops_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS elapsed_game_loops_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS elapsed_game_loops_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS elapsed_game_loops_p95,
    -- map_name
    COUNT(*) - COUNT(metadata.mapName) AS map_name_null,
    COUNT(DISTINCT metadata.mapName) AS map_name_cardinality,
    -- max_players
    COUNT(*) - COUNT(initData.gameDescription.maxPlayers) AS max_players_null,
    COUNT(DISTINCT initData.gameDescription.maxPlayers) AS max_players_cardinality,
    -- game_speed (CONSTANT expected)
    COUNT(DISTINCT details.gameSpeed) AS game_speed_cardinality,
    -- game_speed_init (CONSTANT expected)
    COUNT(DISTINCT initData.gameDescription.gameSpeed) AS game_speed_init_cardinality,
    -- map_size
    COUNT(DISTINCT initData.gameDescription.mapSizeX) AS map_size_x_cardinality,
    COUNT(DISTINCT initData.gameDescription.mapSizeY) AS map_size_y_cardinality,
    -- error booleans (CONSTANT expected: all FALSE)
    COUNT(DISTINCT gameEventsErr) AS gameEventsErr_cardinality,
    COUNT(DISTINCT messageEventsErr) AS messageEventsErr_cardinality,
    COUNT(DISTINCT trackerEvtsErr) AS trackerEvtsErr_cardinality,
    -- version / build
    COUNT(DISTINCT metadata.gameVersion) AS game_version_meta_cardinality,
    COUNT(DISTINCT header."version") AS game_version_header_cardinality,
    COUNT(DISTINCT metadata.baseBuild) AS base_build_cardinality,
    COUNT(DISTINCT metadata.dataBuild) AS data_build_cardinality,
    -- blizzard map flags
    COUNT(DISTINCT details.isBlizzardMap) AS is_blizzard_map_cardinality,
    COUNT(DISTINCT initData.gameDescription.isBlizzardMap) AS is_blizzard_map_init_cardinality,
    -- time_utc
    COUNT(*) - COUNT(details.timeUTC) AS time_utc_null,
    COUNT(DISTINCT details.timeUTC) AS time_utc_cardinality
FROM replays_meta_raw
"""
```

**Cell 11 -- replays_meta_raw IQR outliers for elapsed_game_loops:**
```python
sql_queries["rm_egl_iqr_outliers"] = """
WITH stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS q3
    FROM replays_meta_raw
)
SELECT
    q1,
    q3,
    q3 - q1 AS iqr,
    q1 - 1.5 * (q3 - q1) AS lower_fence,
    q3 + 1.5 * (q3 - q1) AS upper_fence,
    SUM(CASE WHEN header.elapsedGameLoops < (s.q1 - 1.5 * (s.q3 - s.q1))
              OR header.elapsedGameLoops > (s.q3 + 1.5 * (s.q3 - s.q1))
         THEN 1 ELSE 0 END) AS iqr_outlier_count
FROM replays_meta_raw, stats s
GROUP BY q1, q3
"""
```

**Cell 12 -- map_aliases_raw profiling:**
```python
sql_queries["ma_profile"] = """
SELECT
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(tournament) AS tournament_null,
    COUNT(*) - COUNT(foreign_name) AS foreign_name_null,
    COUNT(*) - COUNT(english_name) AS english_name_null,
    COUNT(*) - COUNT(filename) AS filename_null,
    COUNT(DISTINCT tournament) AS tournament_cardinality,
    COUNT(DISTINCT foreign_name) AS foreign_name_cardinality,
    COUNT(DISTINCT english_name) AS english_name_cardinality,
    COUNT(DISTINCT filename) AS filename_cardinality
FROM map_aliases_raw
"""

sql_queries["ma_topk_tournament"] = """
SELECT
    tournament,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM map_aliases_raw), 4) AS pct
FROM map_aliases_raw
GROUP BY tournament
ORDER BY cnt DESC
LIMIT 5
"""
```

Execute all queries and collect results.

**Verification:**
- `profile_rm` dict with struct-flat field stats, including elapsed_game_loops
  marked POST-GAME.
- `profile_ma` dict with map_aliases_raw stats.
- Constant column cardinality values confirmed (game_speed=1, game_speed_init=1,
  gameEventsErr=1, messageEventsErr=1, trackerEvtsErr=1).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T02 outputs (conn, census, sql_queries, constants)

---

### T05 -- Dataset-Level Profiling

**Objective:** Compute dataset-level quality metrics: row counts per table,
duplicate detection, class balance, completeness matrix, cross-table linkage
integrity, and memory footprint estimate.

**Instructions:**

**Cell 13 -- row counts:**
```python
sql_queries["row_counts"] = """
SELECT 'replay_players_raw' AS table_name, COUNT(*) AS n_rows FROM replay_players_raw
UNION ALL
SELECT 'replays_meta_raw', COUNT(*) FROM replays_meta_raw
UNION ALL
SELECT 'map_aliases_raw', COUNT(*) FROM map_aliases_raw
"""
```

**Cell 14 -- duplicate detection:**
```python
# W-04: Duplicate detection uses (replayId, playerID) to match census 01_02_04 methodology.
# Note: 'playerID' in replay_players_raw is the per-replay slot index (0 or 1 for 1v1),
# while 'toon_id' is the global Battle.net player identifier. Using (replayId, playerID)
# is the correct primary key for detecting within-file duplicates, consistent with census.
# toon_id-based detection would identify cross-replay same-player rows, which is NOT
# a duplication concern for this schema.
sql_queries["rp_duplicates"] = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT (replayId, playerID)) AS distinct_pairs,
    COUNT(*) - COUNT(DISTINCT (replayId, playerID)) AS duplicate_rows
FROM replay_players_raw
"""
```

**Cell 15 -- class balance:**
```python
sql_queries["class_balance"] = """
SELECT
    result,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replay_players_raw
GROUP BY result
ORDER BY cnt DESC
"""
```

**Cell 16 -- completeness matrix:**
Build a DataFrame with one row per column per table, columns: table, column,
null_pct. This feeds the completeness heatmap.

**Cell 17 -- cross-table linkage:**
```python
sql_queries["cross_table_linkage"] = """
WITH rp_replays AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM replay_players_raw
),
rm_replays AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM replays_meta_raw
)
SELECT
    (SELECT COUNT(*) FROM rp_replays) AS rp_distinct_replays,
    (SELECT COUNT(*) FROM rm_replays) AS rm_distinct_replays,
    (SELECT COUNT(*) FROM rp_replays WHERE replay_id NOT IN (SELECT replay_id FROM rm_replays)) AS rp_orphans,
    (SELECT COUNT(*) FROM rm_replays WHERE replay_id NOT IN (SELECT replay_id FROM rp_replays)) AS rm_orphans
"""
```

**Cell 18 -- memory footprint:**
```python
sql_queries["memory_footprint"] = """
SELECT
    database_name,
    table_name,
    estimated_size,
    column_count,
    index_count
FROM duckdb_tables()
WHERE table_name IN ('replay_players_raw', 'replays_meta_raw', 'map_aliases_raw')
ORDER BY table_name
"""
```

Execute all queries, collect into `dataset_profile` dict.

**Verification:**
- Row counts match expected: replay_players_raw=44,817, replays_meta_raw=22,390,
  map_aliases_raw=104,160.
- Duplicate count is 0 (confirmed by 01_02_04).
- Class balance shows Win~22,382, Loss~22,409, Undecided=24, Tie=2.
- Cross-table orphan counts are 0 (expected).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T02, T03, T04 outputs

---

### T06 -- Critical Detection

**Objective:** Apply formal detection rules to identify dead fields (null_pct ==
100%), constant columns (cardinality == 1), and near-constant columns
(uniqueness_ratio < 0.001 OR IQR == 0). Collect all findings into a structured
`critical_findings` dict.

**Instructions:**

**Cell 19 -- critical detection logic:**

Using the profiles from T03 and T04, classify columns:

```python
critical_findings = {
    "dead_fields": [],       # null_pct == 100%
    "constant_columns": [],  # cardinality == 1
    "near_constant": [],     # uniqueness_ratio < 0.001 OR IQR == 0
    "sentinel_columns": [],  # columns with known sentinel values
}

# W-01 fix: derive near_constant list programmatically from profile data,
# not from a hardcoded enumeration. The census flagged 20 near-constant columns
# across replay_players_raw and replays_meta_raw struct-flat -- the code must
# collect all of them dynamically.
```

For dead fields: scan all column profiles for null_pct == 100.0. Expected: none
(01_02_04 census shows 0 NULLs everywhere).

For constant columns: scan cardinality == 1. Expected 5 from
replays_meta_raw struct-flat:
- game_speed (cardinality=1)
- game_speed_init (cardinality=1)
- gameEventsErr (cardinality=1)
- messageEventsErr (cardinality=1)
- trackerEvtsErr (cardinality=1)

For near-constant: scan uniqueness_ratio < 0.001 OR IQR == 0. Illustrative
candidates from census include: playerID (card=9, ratio=0.000201), handicap
(card=2, ratio=0.000045), isInClan (card=2, ratio=0.000045), color_a (card=2,
ratio=0.000045), result (card=4, ratio=0.000089). Also check IQR==0: MMR (all
rows) has Q1=Q3=0, handicap has Q1=Q3=100.

Note: The 5 examples above are illustrative. The detection logic must scan ALL
column profiles programmatically at runtime and collect every column matching the
criteria (not just those listed here). The JSON artifact must reflect the
complete list.

For sentinel columns:
- MMR: zero_count=37,489 (83.65%), sentinel value=0
- SQ: sentinel_count=2, sentinel value=INT32_MIN (-2,147,483,648)

Assert constant_columns list has exactly 5 entries.

**Verification:**
- `critical_findings["constant_columns"]` has exactly 5 entries.
- `critical_findings["dead_fields"]` is empty (expected).
- `critical_findings["sentinel_columns"]` lists MMR and SQ.
- `critical_findings["near_constant"]` populated with all qualifying columns
  (derived programmatically, not from a hardcoded list).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T03, T04, T05 outputs

---

### T07 -- Completeness Heatmap

**Objective:** Produce a heatmap showing null_pct (and sentinel-based effective
missingness) per column for all three tables. Since sc2egset has zero physical
NULLs, the heatmap must include sentinel-based effective missingness to be
informative.

**Instructions:**

**Cell 20 -- completeness heatmap:**

Build a DataFrame with columns: table, column_name, null_pct,
effective_missing_pct. For most columns, effective_missing_pct == null_pct == 0.
For MMR, effective_missing_pct = MMR_ZERO_PCT (83.65%). For SQ,
effective_missing_pct = 100.0 * SQ_SENTINEL_COUNT / RP_TOTAL_ROWS.

Plot as a grouped heatmap with three row-sections (one per table), columns as
column names, cell color by effective_missing_pct. Use diverging colormap
(e.g., `YlOrRd`) with 0 = green/white and high = red.

Title: "Step 01_03_01 -- Data Completeness (Physical NULL + Sentinel Missingness)"
Annotate: "Physical NULL rate is 0% for all columns. Sentinel-based effective
missingness: MMR=0 (83.65%), SQ=INT32_MIN (0.004%)."

Save to `artifact_dir / "01_03_01_completeness_heatmap.png"`.

**Verification:**
- PNG file exists and is non-empty.
- MMR column shows high effective missingness visually.
- All other columns show near-zero.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T03, T04 outputs (column profiles)

---

### T08 -- QQ Plots

**Objective:** Produce QQ plots against the normal distribution for 5 key
numeric columns: MMR (rated only, MMR > 0), APM, SQ (sentinel excluded),
supplyCappedPercent, elapsed_game_loops (POST-GAME).

**Instructions:**

**Cell 21 -- fetch data for QQ plots:**

```python
# B-01 fix: split QQ data into two queries to avoid MMR sentinel filter
# polluting APM/SQ/supplyCappedPercent distributions.

sql_queries["qq_mmr"] = """
SELECT MMR
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND MMR > 0
-- I7: MMR > 0 excludes sentinel-coded unrated players (83.65% of rows per census).
-- QQ shows MMR distribution among rated players only.
"""

sql_queries["qq_ingame"] = f"""
SELECT APM, SQ, supplyCappedPercent, elapsed_game_loops
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > {INT32_MIN}
-- I7: SQ > INT32_MIN excludes 2 sentinel rows (value=-2,147,483,648, per census).
-- APM, supplyCappedPercent, elapsed_game_loops: no additional filter needed.
-- Full Win/Loss population minus 2 SQ sentinel rows.
"""

sql_queries["qq_egl_data"] = """
SELECT header.elapsedGameLoops AS elapsed_game_loops
FROM replays_meta_raw
"""

df_qq_mmr = conn.fetch_df(sql_queries["qq_mmr"])
df_qq_ingame = conn.fetch_df(sql_queries["qq_ingame"])
df_qq_egl = conn.fetch_df(sql_queries["qq_egl_data"])
```

**Cell 22 -- QQ plot figure (5 panels):**

Use `scipy.stats.probplot` against `dist="norm"` for each column. 5-panel
figure (1 row x 5 cols or 2 rows). Each panel titled with column name, I3
classification, population filter, and sample size:

- `f"MMR [PRE-GAME (Inv. #3), rated only N={len(df_qq_mmr):,}]"`
- `f"APM [IN-GAME (Inv. #3), N={df_qq_ingame['APM'].count():,}]"`
- `f"SQ [IN-GAME (Inv. #3), sentinel excluded, N={df_qq_ingame['SQ'].dropna().count():,}]"`
- `f"supplyCappedPercent [IN-GAME (Inv. #3), N={df_qq_ingame['supplyCappedPercent'].count():,}]"`
- `f"elapsed_game_loops [POST-GAME (Inv. #3), N={df_qq_egl['elapsed_game_loops'].count():,}]"`

The MMR panel uses `df_qq_mmr["MMR"]`. The APM, SQ, and supplyCappedPercent
panels use the corresponding columns from `df_qq_ingame`. The
elapsed_game_loops panel uses `df_qq_egl["elapsed_game_loops"]`.

Suptitle: "Step 01_03_01 -- Normal QQ Plots for Key Numeric Columns"

Save to `artifact_dir / "01_03_01_qq_plots.png"`.

**Verification:**
- PNG file exists and is non-empty.
- All 5 panels present with I3 temporal classification in titles.
- elapsed_game_loops marked POST-GAME.
- MMR panel uses rated-only data (~7,328 rows).
- APM/SQ/supplyCappedPercent panels use full Win/Loss population (~44,789 rows).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T02 outputs (conn, sql_queries, constants)

---

### T09 -- ECDF Plots

**Objective:** Produce ECDF plots for 3 key columns: MMR (rated only), APM,
SQ (sentinel excluded). ECDFs provide a non-parametric, binning-free view of
the full distribution shape.

**Instructions:**

**Cell 23 -- ECDF figure (3 panels):**

Reuse the data fetched in T08 (df_qq_mmr for MMR, df_qq_ingame for APM and SQ).
For each column, compute the ECDF:
```python
sorted_vals = np.sort(values)
ecdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
```

3-panel figure. Each panel titled with column name and I3 classification:
- MMR [PRE-GAME, rated only, MMR > 0]
- APM [IN-GAME (Inv. #3)]
- SQ [IN-GAME (Inv. #3), sentinel excluded]

Suptitle: "Step 01_03_01 -- Empirical CDF for Key Numeric Columns"

Save to `artifact_dir / "01_03_01_ecdf_key_columns.png"`.

**Verification:**
- PNG file exists and is non-empty.
- All 3 panels present with I3 temporal classification in titles.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T08 outputs (fetched data)

---

### T10 -- JSON Artifact

**Objective:** Assemble all profiling results into a single structured JSON
artifact at `01_03_01_systematic_profile.json`.

**Instructions:**

**Cell 24 -- build JSON structure:**

```python
profile_json = {
    "step": "01_03_01",
    "dataset": "sc2egset",
    "tables": {
        "replay_players_raw": {
            "n_rows": RP_TOTAL_ROWS,
            "n_cols": 25,
            "column_profiles": { ... },  # from T03
            "iqr_outliers": {
                "all_rows": { ... },           # from T03 rp_iqr_outliers
                "MMR": {
                    "iqr_outliers_all": ...,           # from rp_iqr_outliers (degenerate)
                    "iqr_outliers_rated_only": ...,    # from rp_iqr_outliers_mmr_rated (W-03)
                    "note": "MMR IQR outlier count for all rows is degenerate (IQR=0 since Q1=Q3=0); rated-only (MMR>0) IQR outlier count is also reported."
                },
            },
            "topk_categorical": { ... },  # from T03
        },
        "replays_meta_raw": {
            "n_rows": RM_TOTAL_ROWS,
            "n_top_level_cols": 9,
            "n_struct_flat_fields": 17,
            "struct_field_profiles": { ... },  # from T04
            "elapsed_game_loops_iqr": { ... }, # from T04
        },
        "map_aliases_raw": {
            "n_rows": ...,               # from T04/T05
            "n_cols": 4,
            "column_profiles": { ... },  # from T04
        },
    },
    "dataset_level": {
        "duplicate_check": { ... },      # from T05
        "class_balance": { ... },        # from T05
        "cross_table_linkage": { ... },  # from T05
        "memory_footprint": { ... },     # from T05
    },
    "critical_findings": { ... },        # from T06
    "field_classification": FIELD_CLASSIFICATION,  # from census
    "sql_queries": sql_queries,          # I6 compliance
    "sentinel_summary": {
        "MMR": {
            "sentinel_value": 0,
            "count": MMR_ZERO_COUNT,
            "pct": MMR_ZERO_PCT,
            "interpretation": "MMR=0 means unrated player"
        },
        "SQ": {
            "sentinel_value": INT32_MIN,
            "count": SQ_SENTINEL_COUNT,
            "pct": round(100.0 * SQ_SENTINEL_COUNT / RP_TOTAL_ROWS, 4),
            "interpretation": "INT32_MIN sentinel for missing SQ value"
        }
    },
}
```

Write to `artifact_dir / "01_03_01_systematic_profile.json"`.

Note: `sql_queries` dict contains nested dicts (e.g., rp_topk). Ensure JSON
serialization handles this correctly.

**Verification:**
- JSON file exists, is valid JSON, and is non-empty.
- Top-level key `critical_findings` exists.
- `critical_findings.constant_columns` has exactly 5 entries.
- `sql_queries` key is populated (I6).
- `tables.replay_players_raw.iqr_outliers.MMR.iqr_outliers_rated_only` exists (W-03).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- T03, T04, T05, T06 outputs

---

### T11 -- Markdown Artifact

**Objective:** Produce a human-readable markdown summary of the systematic
profile, including the I3 classification table, all SQL queries (I6), critical
findings, and plot index.

**Instructions:**

**Cell 25 -- write markdown artifact:**

The markdown must contain these sections:
1. **Header:** Step, dataset, predecessor.
2. **I3 Temporal Classification Table:** Every column from all 3 tables,
   with classification (IDENTIFIER, PRE-GAME, IN-GAME, POST-GAME, CONSTANT,
   TARGET). Sourced from census `field_classification`.
3. **Table Summaries:** Row count, column count, duplicate status for each table.
4. **Column-Level Profile Summary:** Tabular summary of key stats per numeric
   column (min, max, mean, std, skewness, kurtosis, IQR outlier count).
   For MMR, include both all-rows (degenerate) and rated-only IQR outlier counts
   with explanatory note: "MMR IQR outlier count for all rows is degenerate
   (IQR=0 since Q1=Q3=0); rated-only (MMR>0) IQR outlier count is also reported."
5. **Categorical Profile Summary:** Top-5 for each categorical column.
6. **Critical Findings:**
   - Dead fields (expected: none)
   - Constant columns (expected: 5)
   - Near-constant columns (with complete list, derived programmatically)
   - Sentinel columns (MMR, SQ)
7. **Cross-Table Linkage:** Orphan counts.
8. **Class Balance:** Win/Loss/Undecided/Tie with percentages.
9. **Plot Index:** Table of all 3 PNG files with filenames and descriptions.
10. **SQL Queries:** All queries verbatim (I6).
11. **Invariants Applied:** I3, I6, I7, I9.

Write to `artifact_dir / "01_03_01_systematic_profile.md"`.

**Verification:**
- MD file exists and is non-empty.
- Contains I3 classification table.
- Contains all SQL queries verbatim.
- Contains critical findings section with 5 constant columns.
- Contains MMR IQR degenerate-case documentation (W-03).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

**Read scope:**
- All prior task outputs

---

### T12 -- Gate Verification and Connection Close

**Objective:** Run end-to-end gate checks and close the DuckDB connection.

**Instructions:**

**Cell 26 -- gate verification:**
```python
# Gate check: all 5 artifacts exist and are non-empty
json_path = artifact_dir / "01_03_01_systematic_profile.json"
md_path = artifact_dir / "01_03_01_systematic_profile.md"
heatmap_path = artifact_dir / "01_03_01_completeness_heatmap.png"
qq_path = artifact_dir / "01_03_01_qq_plots.png"
ecdf_path = artifact_dir / "01_03_01_ecdf_key_columns.png"

for p in [json_path, md_path, heatmap_path, qq_path, ecdf_path]:
    assert p.exists(), f"Missing artifact: {p}"
    assert p.stat().st_size > 0, f"Empty artifact: {p}"

# Gate check: JSON contains critical_findings
with open(json_path) as f:
    profile = json.load(f)
assert "critical_findings" in profile, "JSON missing critical_findings key"
assert len(profile["critical_findings"]["constant_columns"]) == 5, (
    f"Expected 5 constant columns, got {len(profile['critical_findings']['constant_columns'])}"
)

# Gate check: MD contains I3 classification table
md_text = md_path.read_text()
assert "I3" in md_text or "Temporal Classification" in md_text, (
    "MD missing I3 classification table"
)

# Gate check: MMR rated-only IQR exists in JSON (W-03)
assert "iqr_outliers_rated_only" in str(profile), (
    "JSON missing MMR rated-only IQR outlier count"
)

print("All 01_03_01 gate checks passed.")

conn.close()
print("DuckDB connection closed. Done.")
```

**Verification:**
- All 5 artifact files exist and are non-empty.
- JSON has `critical_findings` key with exactly 5 constant columns.
- MD has I3 classification table.
- JSON has MMR rated-only IQR outlier count.
- No assertion errors.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T13 -- STEP_STATUS Update

**Objective:** Update STEP_STATUS.yaml to record 01_03_01 as complete.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`.
2. Add after the `01_02_07` entry:
```yaml
  "01_03_01":
    name: "Systematic Data Profiling"
    pipeline_section: "01_03"
    status: complete
    completed_at: "2026-04-15"
```

**Verification:**
- STEP_STATUS.yaml contains `"01_03_01"` with status `complete`.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`

---

### T14 -- Research Log Entry

**Objective:** Add a reverse-chronological entry to the sc2egset research log.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`.
2. Insert a new entry at the top of the entries section (after the header,
   before the 01_02_07 entry). Include:
   - Step scope and artifacts produced (1 JSON, 3 PNGs, 1 MD).
   - Critical findings: 0 dead fields, 5 constant columns (list), near-constant
     columns (list), sentinel columns (MMR, SQ).
   - Cross-table linkage: 0 orphans.
   - Class balance: near-perfect 50/50 Win/Loss.
   - QQ plot findings: which columns are approximately normal, which are skewed.
   - Phase 02 implications: which columns to drop (constant, dead), sentinel
     handling strategy needed for MMR/SQ.
   - elapsed_game_loops marked POST-GAME.
   - MMR IQR degenerate-case note: IQR for MMR-all is degenerate (Q1=Q3=0);
     rated-only IQR also reported.

**Verification:**
- Research log contains 01_03_01 entry at the top.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update (T01) |
| `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py` | Create (T02-T12) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json` | Create (T10) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png` | Create (T07) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_qq_plots.png` | Create (T08) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png` | Create (T09) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md` | Create (T11) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update (T13) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update (T14) |

## Gate Condition

- All 5 artifact files exist and are non-empty:
  `01_03_01_systematic_profile.json`, `01_03_01_completeness_heatmap.png`,
  `01_03_01_qq_plots.png`, `01_03_01_ecdf_key_columns.png`,
  `01_03_01_systematic_profile.md`.
- JSON contains `critical_findings` key.
- `critical_findings.constant_columns` list has exactly 5 entries:
  game_speed, game_speed_init, gameEventsErr, messageEventsErr, trackerEvtsErr.
- JSON contains `tables.replay_players_raw.iqr_outliers.MMR.iqr_outliers_rated_only` (W-03).
- MD contains I3 temporal classification table covering all columns from all
  three tables.
- MD contains all SQL queries verbatim (I6).
- MD documents MMR IQR degenerate-case (W-03).
- elapsed_game_loops annotated as POST-GAME in all artifacts.
- MMR statistics reported both including and excluding MMR=0 sentinel.
- SQ statistics reported both including and excluding INT32_MIN sentinel.
- QQ plots use separate dataframes: MMR from rated-only query, APM/SQ/supplyCappedPercent from full Win/Loss query (B-01).
- STEP_STATUS.yaml shows `01_03_01: complete`.
- research_log.md contains 01_03_01 entry.
- ROADMAP.md contains Step 01_03_01 definition.
- Notebook executes end-to-end without errors.

## Out of Scope

- **Data cleaning decisions.** Critical findings are documented; actual
  cleaning (drop/impute/recode) deferred to Phase 01_04 (Data Cleaning).
- **Feature engineering.** Column suitability for features is noted but not
  acted upon -- deferred to Phase 02.
- **Event table profiling.** game_events_raw, tracker_events_raw,
  message_events_raw are views into Parquet event files. Profiling them
  requires a separate step due to different access patterns and much larger
  row counts.
- **Deeply nested STRUCT profiling.** Only top-level struct-flat fields are
  profiled. initData.gameDescription.gameOptions subfields are not individually
  profiled (they are game configuration booleans with low information content
  for match outcome prediction).
- **PIPELINE_SECTION_STATUS or PHASE_STATUS updates.** 01_03 is not complete
  until all profiling steps are finished.
- **Normality tests.** QQ plots provide visual normality assessment. Formal
  tests (Shapiro-Wilk, Anderson-Darling) are deferred to Phase 02/03 where
  distributional assumptions matter for specific models.

## Open Questions

- **Does UNPIVOT work cleanly across mixed-type columns in DuckDB?** If the
  rp_null_cardinality query (T03 Cell 7) fails due to type coercion issues
  with UNPIVOT, fall back to per-column UNION ALL stored in
  `sql_queries["rp_null_cardinality_fallback"]` (W-02). Resolves during
  execution.
- **Are there any NULL values in map_aliases_raw?** Census 01_02_04 did not
  profile map_aliases_raw null counts. Expected: zero (all columns are
  NOT NULL per schema YAML). Resolves during execution (T04).
- **What is the IQR outlier rate for elapsed_game_loops?** Census shows
  skewness=2.03, kurtosis=10.66, suggesting a right-skewed distribution with
  some very long games. The IQR outlier count will quantify this.
  Resolves during execution (T04).

---

**Critique gate:** For Category A, adversarial critique is required before
execution begins. Dispatch reviewer-adversarial to produce
`planning/plan_sc2egset_01_03_01.critique.md`.
```

---

**Key files referenced in this plan (absolute paths):**

- `/Users/tomaszpionka/Projects/rts-outcome-prediction/.claude/scientific-invariants.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/docs/PHASES.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml` (25 columns, 44,817 rows)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml` (9 top-level columns with nested STRUCTs, 22,390 rows)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/map_aliases_raw.yaml` (4 columns, 104,160 rows)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/planning/plan_sc2egset_01_02_07.md` (format reference)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/docs/templates/planner_output_contract.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/sandbox/README.md`

**Data corrections from the prompt:**
- The prompt stated replay_players_raw has "~25 columns, 92,274 rows" -- the actual count is 25 columns, 44,817 rows (per census and schema YAML). The plan uses the verified figure.
- The prompt stated map_aliases_raw has "4 cols, ~100-200 rows" -- the actual count is 4 columns, 104,160 rows (70 tournaments x 1,488 mappings each). The plan uses the verified figure.

**Connection pattern:** The plan uses `get_notebook_db("sc2", "sc2egset")` which returns a `DuckDBClient`. Queries use `conn.fetch_df(sql)` (not `conn.execute(sql).fetchdf()`).
