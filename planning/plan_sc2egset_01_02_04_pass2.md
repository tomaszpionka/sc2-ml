---
category: A
branch: fix/sc2egset-01-02-04-pass2
date: 2026-04-14
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis (Tukey-style)"
invariants_touched:
  - 6
  - 7
  - 9
source_artifacts:
  - sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: null
---

# Plan: sc2egset 01_02_04 Pass 2 -- Quantitative Analytics Fixes

## Scope

Second pass on the sc2egset step 01_02_04 (Metadata STRUCT Extraction &
Replay-Level EDA) notebook. This pass adds missing quantitative analytics
identified by adversarial review: skewness/kurtosis, SQ sentinel-excluded
stats, MMR zero-spike interpretation, struct_flat NULL census, isInClan/clanTag
profiles, completeness matrix, memory footprint, pandas verification print
cells for existing plots, and a near-constant threshold note. No new
visualizations are added -- all plots are deferred to step 01_02_05.

Phase 01, Pipeline Section 01_02, Step 01_02_04 (augmentation pass).

## Problem Statement

The 01_02_04 notebook completed its initial execution and an augmentation pass
that added zero counts, field classification, near-constant interpretive note,
and Undecided/Tie corrective query. Adversarial review identified nine
remaining analytics gaps:

1. No skewness or kurtosis for numeric columns (EDA Manual 3.1 requires
   distribution shape characterization beyond descriptive stats).
2. SQ descriptive stats include 2 INT32_MIN sentinel rows, contaminating mean
   and stddev. No parallel clean-SQ stats exist.
3. MMR=0 accounts for 83.6% of rows but no cross-tabulation with result or
   highestLeague exists to test the "sentinel = not reported" hypothesis.
4. The 17 struct_flat-extracted columns have no explicit NULL census.
5. isInClan and clanTag appear only in NULL census and cardinality sections
   with no value distributions.
6. No completeness matrix for struct_flat columns (co-occurrence of NULLs).
7. No DuckDB file size (memory footprint) measurement.
8. Existing plot cells lack pandas verification (print/display of the
   underlying DataFrame before the plot call).
9. Near-constant detection section lacks a note about threshold sensitivity
   to dataset size.

All fixes are quantitative analytics cells. No new plots.

## Assumptions & unknowns

- **Assumption:** DuckDB SKEWNESS() and KURTOSIS() functions are available in
  the installed DuckDB version (they were introduced in DuckDB 0.8.0; the
  project uses >= 0.10.0).
- **Assumption:** The struct_flat DataFrame is registered for SQL access in
  DuckDB by earlier cells in the notebook (confirmed: line 92 creates it as a
  pandas DataFrame, and the DuckDB connection auto-detects pandas DataFrames in
  queries).
- **Unknown:** Whether any struct_flat column actually has NULLs. The NULL
  census will reveal this. The completeness matrix task (T06) is conditional
  on the NULL census result from T04.

## Literature context

EDA Manual Section 3.1 specifies column-level profiling must include
"distribution shape (skewness, kurtosis)" and "outlier detection". The current
notebook computes min/max/mean/median/stddev/percentiles but omits skewness and
kurtosis. EDA Manual Section 3.2 specifies dataset-level profiling must include
"feature completeness matrix" and "memory footprint". EDA Manual Section 3.3
specifies flagging near-constant columns with "uniqueness ratio below 0.001 as
a reasonable starting point" -- the note in T09 addresses threshold sensitivity
for small datasets per this guidance.

## Execution Steps

### T01 -- Skewness and kurtosis for all numeric columns

**Objective:** Compute SKEWNESS() and KURTOSIS() for every numeric column in
replay_players_raw and for elapsed_game_loops in struct_flat. Store results in
the JSON artifact under a `skew_kurtosis` key.

**Instructions:**
1. Add a new cell after the existing Section E numeric stats block. Title the
   markdown cell: `## Section E1: Skewness and Kurtosis (EDA Manual 3.1)`.
2. Define a SQL query for replay_players_raw that computes SKEWNESS(col) and
   KURTOSIS(col) for each column in this list: MMR, APM, SQ,
   supplyCappedPercent, handicap, startDir, startLocX, startLocY, color_a,
   color_b, color_g, color_r, playerID, userID. Use a loop-based approach
   (one query per column) matching the existing numeric stats pattern.
   SQL per column:
   ```sql
   SELECT
       ROUND(SKEWNESS({col}), 4) AS skewness,
       ROUND(KURTOSIS({col}), 4) AS kurtosis
   FROM replay_players_raw
   WHERE {col} IS NOT NULL
   ```
3. Add a separate query for elapsed_game_loops:
   ```sql
   SELECT
       ROUND(SKEWNESS(elapsed_game_loops), 4) AS skewness,
       ROUND(KURTOSIS(elapsed_game_loops), 4) AS kurtosis
   FROM struct_flat
   WHERE elapsed_game_loops IS NOT NULL
   ```
4. Collect results into a dict keyed by column name, print as a DataFrame.
5. In the artifact-writing section, add this dict to findings as
   `findings["skew_kurtosis"]`.
6. In the markdown artifact, add a Section E1 with the SQL template and the
   results table.

**Verification:**
- Notebook cell executes without error.
- JSON artifact contains `skew_kurtosis` key with entries for all 15 columns
  (14 replay_players_raw + 1 struct_flat).
- Each entry has both `skewness` and `kurtosis` as numeric values.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T02 -- SQ sentinel exclusion from descriptive stats

**Objective:** Produce a parallel set of SQ descriptive statistics that
excludes the INT32_MIN sentinel value (-2147483648), so downstream analysis
can reference uncontaminated SQ distribution metrics.

**Instructions:**
1. Add a new cell immediately after the existing SQ stats output. Title the
   markdown cell: `### SQ stats excluding INT32_MIN sentinel`.
2. SQL query:
   ```sql
   SELECT
       MIN(SQ) AS min_val,
       MAX(SQ) AS max_val,
       ROUND(AVG(SQ), 2) AS mean_val,
       ROUND(MEDIAN(SQ), 2) AS median_val,
       ROUND(STDDEV(SQ), 2) AS stddev_val,
       PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) AS p05,
       PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) AS p25,
       PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) AS p75,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) AS p95,
       COUNT(*) AS n_rows
   FROM replay_players_raw
   WHERE SQ IS NOT NULL AND SQ != -2147483648
   ```
3. Print the result. Add a prose markdown note:
   "The main SQ descriptive statistics (Section E) are contaminated by 2 rows
   containing the INT32_MIN sentinel value (-2147483648). The stats above
   exclude those rows. The sentinel causes the main SQ mean and stddev to be
   misleading. Refer to the sentinel-excluded stats above for the clean SQ
   distribution's actual median and range."
   Do NOT hardcode expected median or range values — derive from the query
   result printed immediately above.
4. Store the result in the JSON artifact as
   `findings["numeric_stats_SQ_no_sentinel"]`.
5. Add corresponding SQL and table to the markdown artifact under Section E.

**Verification:**
- JSON artifact contains `numeric_stats_SQ_no_sentinel` key.
- The `min_val` in the sentinel-excluded stats is >= 0.
- The `n_rows` equals total_rows minus 2 (44815).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T03 -- MMR zero-spike interpretation

**Objective:** Cross-tabulate MMR=0 against result and highestLeague to test
whether the 37,489 MMR=0 rows cluster in specific categories, supporting or
refuting the "sentinel = not reported" hypothesis.

**Instructions:**
1. Add a new cell after the zero counts section (Section E2). Title the
   markdown cell: `### MMR zero-spike interpretation`.
2. Query 1 -- MMR=0 by result:
   ```sql
   SELECT
       result,
       COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero_cnt,
       COUNT(*) AS total_cnt,
       ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 2)
           AS mmr_zero_pct
   FROM replay_players_raw
   GROUP BY result
   ORDER BY total_cnt DESC
   ```
3. Query 2 -- MMR=0 by highestLeague:
   ```sql
   SELECT
       highestLeague,
       COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero_cnt,
       COUNT(*) AS total_cnt,
       ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 2)
           AS mmr_zero_pct
   FROM replay_players_raw
   GROUP BY highestLeague
   ORDER BY total_cnt DESC
   ```
4. Print both DataFrames. Add a prose interpretation note based on the results.
   (If MMR=0 is uniformly ~83% across all results, that supports "not reported"
   rather than "loss-correlated".)
5. Store both DataFrames in the JSON artifact as:
   `findings["mmr_zero_interpretation"] = {"by_result": [...], "by_highestLeague": [...]}`
6. Add corresponding SQL, tables, and interpretation to the markdown artifact.

**Verification:**
- JSON artifact contains `mmr_zero_interpretation` with both sub-keys.
- Sum of `mmr_zero_cnt` across all result categories equals 37,489.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T04 -- struct_flat NULL census

**Objective:** Compute NULL counts for all 17 STRUCT-extracted columns in
struct_flat, closing the gap where only replay_players_raw has a NULL census.

**Instructions:**
1. Add a new cell after the existing NULL census section (Section B). Title:
   `### struct_flat NULL census`.
2. SQL query -- use the same pattern as the replay_players_raw NULL census:
   ```sql
   SELECT
       COUNT(*) AS total_rows,
       COUNT(*) - COUNT(time_utc) AS time_utc_null,
       COUNT(*) - COUNT(elapsed_game_loops) AS elapsed_game_loops_null,
       COUNT(*) - COUNT(game_version_header) AS game_version_header_null,
       COUNT(*) - COUNT(base_build) AS base_build_null,
       COUNT(*) - COUNT(data_build) AS data_build_null,
       COUNT(*) - COUNT(game_version_meta) AS game_version_meta_null,
       COUNT(*) - COUNT(map_name) AS map_name_null,
       COUNT(*) - COUNT(max_players) AS max_players_null,
       COUNT(*) - COUNT(game_speed) AS game_speed_null,
       COUNT(*) - COUNT(game_speed_init) AS game_speed_init_null,
       COUNT(*) - COUNT(is_blizzard_map) AS is_blizzard_map_null,
       COUNT(*) - COUNT(is_blizzard_map_init) AS is_blizzard_map_init_null,
       COUNT(*) - COUNT(map_size_x) AS map_size_x_null,
       COUNT(*) - COUNT(map_size_y) AS map_size_y_null,
       COUNT(*) - COUNT(gameEventsErr) AS gameEventsErr_null,
       COUNT(*) - COUNT(messageEventsErr) AS messageEventsErr_null,
       COUNT(*) - COUNT(trackerEvtsErr) AS trackerEvtsErr_null
   FROM struct_flat
   ```
3. Reshape into a tidy DataFrame (column, null_count, null_pct) using the same
   pattern as the replay_players_raw NULL census reshape.
4. Print the result.
5. Store in JSON as `findings["null_census"]["struct_flat"]` with
   `total_rows` and `columns` keys matching the replay_players_raw structure.
6. Add to the markdown artifact under Section B.

**Verification:**
- JSON artifact `null_census` now has three sub-keys: `replay_players_raw`,
  `replays_meta_raw_filename`, `struct_flat`.
- `total_rows` for struct_flat equals 22,390.
- All 17 columns are present in the census.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T05 -- isInClan and clanTag categorical profiles

**Objective:** Add value distribution cells for isInClan and clanTag, which
currently appear only in the NULL census and cardinality tables.

**Instructions:**
1. Add a new cell in Section D (Categorical Field Profiles), after the
   replay_players_raw categorical loop. Title: `### isInClan distribution`.
2. isInClan query:
   ```sql
   SELECT
       isInClan,
       COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
   FROM replay_players_raw
   GROUP BY isInClan
   ORDER BY cnt DESC
   ```
3. Print the result.
4. Add a second cell: `### clanTag top-20`.
5. clanTag query:
   ```sql
   SELECT
       clanTag,
       COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_of_total,
       ROUND(100.0 * COUNT(*) / (
           SELECT COUNT(*) FROM replay_players_raw
           WHERE clanTag != ''
       ), 2) AS pct_of_non_empty
   FROM replay_players_raw
   WHERE clanTag != ''
   GROUP BY clanTag
   ORDER BY cnt DESC
   LIMIT 20
   ```
   Note: clanTag has 0 NULLs per the null census, so the non-empty filter
   uses `!= ''` (empty string) rather than `IS NOT NULL`.
6. Print the result.
7. Store in JSON as `findings["isInClan_distribution"]` and
   `findings["clanTag_top20"]`.
8. Add to the markdown artifact under Section D.

**Verification:**
- JSON artifact contains `isInClan_distribution` (list of 2 records:
  true/false) and `clanTag_top20` (list of 20 records).
- isInClan counts sum to 44,817.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T06 -- Completeness matrix for struct_flat

**Objective:** Determine whether any struct_flat NULLs co-occur (are on the
same rows). If all struct_flat columns are 0% NULL, store a note confirming
this. If any have NULLs, compute co-occurrence.

**Instructions:**
1. Add a new cell after the struct_flat NULL census cell (T04). Title:
   `### struct_flat completeness note`.
2. This task depends on T04's output. Inspect the struct_flat null census
   DataFrame computed in T04.
3. If all null_count values are 0:
   - Print: "All 17 struct_flat columns have 0 NULLs. No missingness
     co-occurrence to analyze."
   - Store in JSON:
     `findings["struct_flat_completeness_note"] = "All 17 columns 0% NULL. No missingness co-occurrence."`
4. If any columns have NULLs:
   - For each pair of columns with NULLs, count rows where both are NULL:
     ```sql
     SELECT COUNT(*) AS both_null
     FROM struct_flat
     WHERE {col_a} IS NULL AND {col_b} IS NULL
     ```
   - Build a co-occurrence matrix (DataFrame), print it.
   - Store in JSON as
     `findings["struct_flat_completeness_note"] = {"type": "co_occurrence", "matrix": {...}}`.
5. Add to the markdown artifact.

**Verification:**
- JSON artifact contains `struct_flat_completeness_note`.
- If all-zero NULLs: value is a string.
- If any NULLs: value is a dict with a co-occurrence matrix.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T07 -- Memory footprint

**Objective:** Measure and record the DuckDB file size as a dataset-level
profiling metric (EDA Manual Section 3.2).

**Instructions:**
1. Add a new cell near the beginning of the notebook (after the connection
   cell). Title: `### Database memory footprint`.
2. Python code:
   ```python
   import os
   db_size_bytes = os.path.getsize(str(DB_FILE))
   db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
   print(f"DuckDB file size: {db_size_bytes:,} bytes ({db_size_mb} MB)")
   ```
3. Store in JSON as `findings["db_memory_footprint_bytes"] = db_size_bytes`.
4. Add to the markdown artifact (a one-line entry in a suitable location).

**Verification:**
- JSON artifact contains `db_memory_footprint_bytes` as a positive integer.
- Printed MB value is reasonable (expected: tens to hundreds of MB).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T08 -- Pandas verification print cells for existing plots

**Objective:** Add a `print()` or `.describe()` call immediately before each
of the 5 existing histogram/bar-chart plot cells, grounding the visual output
in inspectable tabular data.

**Instructions:**
1. Identify the 5 existing numeric plot cell blocks in the notebook:
   - MMR histogram+boxplot: data source is `mmr_data`
   - APM histogram+boxplot: data source is `apm_data`
   - SQ histogram+boxplot: data source is `sq_data`
   - supplyCappedPercent histogram+boxplot: data source is `sc_data`
   - Duration histogram: data source is `dur_data`
   Note: The categorical bar charts already print their source DataFrames in
   the categorical profiles loop. No additional verification needed for those.
2. For each of the 5 numeric plot cells, add a verification cell immediately
   before the plot cell:
   ```python
   print(f"=== {col_name} data for plot ({len(df)} rows) ===")
   print(df.describe().to_string())
   ```
   Where `col_name` and `df` are the appropriate variable names for each plot.
3. These are pass-through additions -- they do not change the plot code.

**Verification:**
- Notebook executes without error.
- Each of the 5 numeric plots is preceded by a cell that prints `.describe()`
  of the underlying DataFrame.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T09 -- Near-constant detection threshold note

**Objective:** Add a comment in the near-constant detection section noting that
the 0.001 uniqueness ratio threshold works for small datasets but may need
adjustment for large-N datasets.

**Instructions:**
1. In Section H (Dead/Constant/Near-Constant Field Detection), locate the
   existing "Interpretation Note" at the end of the section.
2. Add a new paragraph at the end of the interpretation note (both in the
   notebook markdown cell and in the markdown artifact generation):
   "**Threshold sensitivity note:** The uniqueness_ratio < 0.001 threshold
   is appropriate for this dataset (N=44,817 rows). For larger datasets
   (N > 1M), the same threshold would flag more columns as near-constant
   because uniqueness_ratio = cardinality / N decreases with N even for
   columns with stable cardinality. Re-evaluate the threshold for each
   dataset based on its row count and the cardinality distribution."
3. This is a prose-only addition -- no SQL or Python computation.

**Verification:**
- Markdown artifact contains the threshold sensitivity note paragraph.
- The note appears in Section H.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T10 -- Rebuild JSON and markdown artifacts

**Objective:** Re-run the artifact-writing section to incorporate all new
findings from T01-T09 into the JSON and markdown output files.

**Instructions:**
1. Ensure all new findings keys are added to the `findings` dict before the
   JSON write cell:
   - `skew_kurtosis` (T01)
   - `numeric_stats_SQ_no_sentinel` (T02)
   - `mmr_zero_interpretation` (T03)
   - `null_census` → `struct_flat` sub-key (T04) — use `findings["null_census"]["struct_flat"]` notation
   - `struct_flat_completeness_note` (T06)
   - `isInClan_distribution` (T05)
   - `clanTag_top20` (T05)
   - `db_memory_footprint_bytes` (T07)
2. Ensure all new markdown sections are added to the `md_lines` list.
3. Execute the full notebook end-to-end and confirm both artifacts are written.

**Verification:**
- JSON artifact at
  `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  contains all new keys.
- Markdown artifact at
  `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`
  contains all new sections.
- Notebook executes end-to-end without error.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.ipynb`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py` | Update |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.ipynb` | Update (jupytext sync) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` | Rewrite |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` | Rewrite |

## Gate Condition

- JSON artifact contains all 8 new keys: `skew_kurtosis`,
  `numeric_stats_SQ_no_sentinel`, `mmr_zero_interpretation`,
  `null_census` → `struct_flat` sub-key (i.e. `findings["null_census"]["struct_flat"]`),
  `struct_flat_completeness_note`,
  `isInClan_distribution`, `clanTag_top20`, `db_memory_footprint_bytes`.
- Markdown artifact contains sections for all 9 task outputs.
- Notebook executes end-to-end without error.
- 5 numeric plot cells each preceded by a pandas verification cell.

## Out of scope

- **Field classification refinement** -- deferred; no source documentation
  available to validate pre-game vs. in-game categorization.
- **Research log entries** -- deferred until the notebook is fully polished
  (after 01_02_05 is also complete).
- **New visualizations** -- all plots deferred to 01_02_05.
- **STEP_STATUS.yaml update** -- status already "complete"; this is a
  quality augmentation pass, not a new step.

## Open questions

- **struct_flat NULL census results**: If any struct_flat columns have NULLs,
  T06 will produce a co-occurrence matrix. The interpretation of this matrix
  (whether NULLs indicate missing STRUCT fields in source JSON vs. DuckDB
  extraction artifacts) requires domain knowledge that may need user input.
  Resolves by: T04 execution revealing the data, then user decision if
  non-trivial.

## Deferred Debt

| Item | Target Step | Rationale |
|------|-------------|-----------|
| Field classification refinement (temporal boundaries) | Phase 02 | Source documentation required |
| z-score outlier detection | 01_03 | IQR fences sufficient for univariate pass |
| Completeness heatmap (visual) | 01_03 | All replay_players_raw columns are 0% NULL; tabular census is sufficient |
| toon_id format validation | 01_03 | Regex pattern analysis for identifier columns |
