---
category: A
branch: feat/aoestats-01-02-04-pass2
date: 2026-04-14
planner_model: claude-opus-4-6
dataset: aoestats
phase: "01"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
invariants_touched: [I6, I7, I9]
source_artifacts:
  - sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: null
---

# Plan: aoestats 01_02_04 Pass 2 — Analytics Fixes

## Scope

Second corrective pass on the aoestats 01_02_04 Univariate Census notebook. This pass addresses nine analytics gaps identified by adversarial review: skewness/kurtosis for all numeric columns, type-aware near-constant detection fix, ELO sentinel-excluded descriptive stats, z-score deferral documentation, duplicate row detection, NULL co-occurrence analysis for players_raw, DuckDB memory footprint, opening non-NULL separation, and pandas verification print cells before existing plots. No new visualizations are added — those are deferred to step 01_02_05.

## Problem Statement

The existing 01_02_04 notebook has been through one corrective pass (WHERE IS NOT NULL bug fix, IQR outliers, field classification, ELO sentinel query, artifact rename). Adversarial review surfaced nine remaining quantitative gaps:

1. EDA Manual Section 3.1 requires skewness and kurtosis for all numeric columns. These were deferred without a formal deferral note.

2. The near-constant detection flags 22 of 32 columns, including continuous numerics with thousands of distinct values (avg_elo: 22,432; duration: 13,164; match_rating_diff: 24,919). The uniqueness_ratio < 0.001 threshold is meaningless for continuous variables on a 30M/107M row dataset — a column can have 20,000 distinct values and still fall below the ratio. The detection must split into genuinely-near-constant (low absolute cardinality) versus ratio-flagged-continuous (high cardinality but low ratio due to large N).

3. team_0_elo and team_1_elo have sentinel value -1.0 (34 and 39 rows). The main descriptive stats include these sentinels. Parallel sentinel-excluded stats are needed for accurate ELO distribution characterization.

4. z-score outlier detection is listed in EDA Manual Section 3.1 as required. The notebook implements IQR outliers but has no documentation for why z-scores are deferred.

5. No duplicate row detection — EDA Manual Section 3.2 requires "duplicate row count and percentage."

6. The four high-NULL columns in players_raw (feudal_age_uptime 87%, castle_age_uptime 88%, imperial_age_uptime 91%, opening 86%) likely co-occur because they all depend on the replay_enhanced flag. A co-occurrence query confirms or denies this hypothesis.

7. EDA Manual Section 3.2 requires memory footprint.

8. The opening column's top-k profile is dominated by NaN (86%). A separate non-NULL-only profile is needed.

9. Plot cells in the notebook lack preceding pandas verification prints — every plot call should have an immediately preceding print/display of the underlying DataFrame.

## Assumptions and Unknowns

- **Assumption:** DuckDB database is intact and unchanged since the first corrective pass.
- **Assumption:** DuckDB natively supports `SKEWNESS(col)` and `KURTOSIS(col)` aggregate functions (documented in DuckDB 1.5.x).
- **Assumption:** The near-constant cardinality threshold of 100 for distinguishing genuinely low-cardinality columns from continuous numerics is empirically reasonable. Justification: the maximum cardinality among known categorical columns in this dataset is 93 (map), and the minimum cardinality among clearly continuous columns is 3,032 (old_rating). A threshold of 100 cleanly separates these groups (map=93 < 100; old_rating=3,032 >= 100). Note: civ has cardinality exactly 50 and is correctly classified as categorical under this threshold. [I7]
- **Unknown:** Whether the four high-NULL columns exactly co-occur with replay_enhanced=FALSE. The co-occurrence query will answer this.

## Literature Context

EDA Manual Section 3.1: "distribution shape (skewness, kurtosis)" and "outlier detection (IQR fences, z-scores)" are required column-level profiling metrics. The z-score deferral is acceptable if documented.

EDA Manual Section 3.2: "duplicate row count and percentage" and "memory footprint" are required dataset-level profiling metrics.

Tukey 1977 convention on IQR fences (1.5x factor) already cited in first corrective pass artifact.

The near-constant detection uses a cardinality < 50 threshold derived empirically from this dataset's observed column cardinalities, not from a literature convention. The 0.001 uniqueness-ratio threshold (from EDA Manual Section 3.3) is retained for the subset where cardinality < 50.

## Execution Steps

### T01 — Skewness and kurtosis for all numeric columns

**Objective:** Compute skewness and kurtosis for every column in MATCHES_NUMERIC_DEFS and PLAYERS_NUMERIC_DEFS, storing results in the JSON artifact. For high-NULL columns, annotate that the statistics are computed on the non-NULL subset only.

**Instructions:**

1. After the existing Section F.1/F.2 loops (which compute descriptive stats), add a new Section F.8 titled "Skewness and Kurtosis."

2. For matches_raw, add a loop over MATCHES_NUMERIC_DEFS:

```python
skew_kurt_matches = []
for table, expr, label in MATCHES_NUMERIC_DEFS:
    sql = f"""
SELECT
    ROUND(SKEWNESS({expr}), 4) AS skewness,
    ROUND(KURTOSIS({expr}), 4) AS kurtosis,
    COUNT({expr}) AS n_nonnull
FROM {table}
"""
    df = con.execute(sql).df()
    rec = df.iloc[0].to_dict()
    rec = {k: float(v) if pd.notna(v) else None for k, v in rec.items()}
    rec["label"] = label
    n_null_for_label = next(
        s for s in numeric_stats_matches if s["label"] == label
    )["n_null"]
    if n_null_for_label and n_null_for_label > 0:
        rec["note"] = (
            f"Computed on {int(rec['n_nonnull']):,} non-NULL values only; "
            f"{int(n_null_for_label):,} NULLs excluded"
        )
    skew_kurt_matches.append(rec)
    sql_queries[f"skew_kurt_matches_{label}"] = sql.strip()
    print(f"{label}: skewness={rec['skewness']}, kurtosis={rec['kurtosis']}")
```

3. Repeat identically for players_raw using PLAYERS_NUMERIC_DEFS, storing results in `skew_kurt_players`.

4. Store both lists in findings:

```python
findings["skew_kurtosis_matches"] = skew_kurt_matches
findings["skew_kurtosis_players"] = skew_kurt_players
```

**Verification:**
- JSON artifact contains keys `skew_kurtosis_matches` and `skew_kurtosis_players`
- Each entry has `skewness`, `kurtosis`, `n_nonnull`, and `label`
- High-NULL columns (feudal/castle/imperial_age_uptime) have a `note` field

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T02 — Type-aware near-constant detection fix

**Objective:** Replace the current near-constant detection logic (which flags 22 of 32 columns using ratio-only) with a type-aware two-category system that distinguishes genuinely near-constant columns from continuous numerics that merely have low ratios due to large N.

**Instructions:**

1. In Section I, replace the current detection loop with:

```python
dead_constant = []
near_constant_low_cardinality = []
near_constant_ratio_flagged = []

# [I7] Empirical threshold: max categorical cardinality in this dataset is 93 (map);
# min continuous cardinality is 3,032 (old_rating). Threshold of 100 cleanly separates groups.
# (civ cardinality=50 is correctly included as categorical under this threshold.)
# Key names aligned with aoe2companion plan for cross-dataset comparability.
NEAR_CONSTANT_CARDINALITY_THRESHOLD = 100

for row in uniqueness_rows_m + uniqueness_rows_p:
    card = int(row["cardinality"])
    ratio = float(row["uniqueness_ratio"])
    if card == 1:
        dead_constant.append(row)
    elif card < NEAR_CONSTANT_CARDINALITY_THRESHOLD and ratio < 0.001:
        near_constant_low_cardinality.append(row)
    elif ratio < 0.001:
        near_constant_ratio_flagged.append(row)

print(f"\nDead/constant fields (cardinality=1): {len(dead_constant)}")
for r in dead_constant:
    print(f"  {r['column_name']}: cardinality={r['cardinality']}")

print(f"\nNear-constant low-cardinality (cardinality < {NEAR_CONSTANT_CARDINALITY_THRESHOLD} AND ratio < 0.001): {len(near_constant_low_cardinality)}")
for r in near_constant_low_cardinality:
    print(f"  {r['column_name']}: cardinality={r['cardinality']}, ratio={r['uniqueness_ratio']}")

print(f"\nRatio-flagged (cardinality >= {NEAR_CONSTANT_CARDINALITY_THRESHOLD}, ratio < 0.001 due to large N): {len(near_constant_ratio_flagged)}")
for r in near_constant_ratio_flagged:
    print(f"  {r['column_name']}: cardinality={r['cardinality']}, ratio={r['uniqueness_ratio']}")
    print(f"    -> NOT near-constant; ratio is low only because N={r['total_rows']:,}")
```

2. Update findings storage:

```python
findings["dead_constant_fields"] = dead_constant
findings["near_constant_low_cardinality"] = near_constant_low_cardinality
findings["near_constant_ratio_flagged"] = near_constant_ratio_flagged
findings["near_constant_detection_note"] = {
    "cardinality_threshold": NEAR_CONSTANT_CARDINALITY_THRESHOLD,
    "justification": (
        "EDA Manual Section 3.3 uses uniqueness_ratio < 0.001 as a starting point. "
        "On a 30M/107M row dataset, this ratio flags continuous numerics with "
        "thousands of distinct values. Threshold of 100 separates genuinely "
        "low-cardinality columns (max categorical: map at 93) from continuous numerics "
        "(min: old_rating at 3,032). Columns flagged only by ratio are documented "
        "as 'near_constant_ratio_flagged' and are NOT near-constant."
    ),
}
```

3. Remove the old `near_constant_fields` key from findings.

**Verification:**
- JSON artifact has `near_constant_low_cardinality` and `near_constant_ratio_flagged` keys
- `near_constant_fields` key is removed
- `near_constant_low_cardinality` contains only columns with cardinality < 100 (civ=50, map=93 and other low-cardinality columns)
- `near_constant_ratio_flagged` contains columns like avg_elo, duration, irl_duration, team_0_elo, team_1_elo, old_rating, new_rating, match_rating_diff

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T03 — ELO sentinel-excluded descriptive stats

**Objective:** Compute parallel descriptive statistics for team_0_elo and team_1_elo excluding the -1.0 sentinel value. The main stats (including sentinel) remain unchanged for reproducibility; sentinel-excluded stats are additive.

**Instructions:**

1. After the existing Section F.7 (sentinel detection), add a new Section F.9 titled "ELO sentinel-excluded descriptive stats."

2. For each of team_0_elo and team_1_elo:

```python
for elo_col in ["team_0_elo", "team_1_elo"]:
    sql = f"""
SELECT
    COUNT({elo_col}) AS n_nonnull,
    COUNT(*) - COUNT({elo_col}) AS n_null,
    SUM(CASE WHEN {elo_col} = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN({elo_col}) AS min_val,
    MAX({elo_col}) AS max_val,
    ROUND(AVG({elo_col}), 2) AS mean_val,
    ROUND(MEDIAN({elo_col}), 2) AS median_val,
    ROUND(STDDEV({elo_col}), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p95
FROM matches_raw
WHERE {elo_col} != -1.0
-- Note: ELO=0 rows (4,824 for team_0_elo, 192 for team_1_elo) are NOT excluded here;
-- only the -1.0 sentinel (unranked marker) is excluded. ELO=0 may represent valid
-- entries and requires separate investigation if needed.
"""
    df = con.execute(sql).df()
    rec = df.iloc[0].to_dict()
    rec = {k: float(v) if pd.notna(v) else None for k, v in rec.items()}
    findings[f"{elo_col}_stats_no_sentinel"] = rec
    sql_queries[f"numeric_matches_{elo_col}_no_sentinel"] = sql.strip()
    print(f"\n=== {elo_col} (sentinel -1.0 excluded) ===")
    print(df.to_string(index=False))
```

**Verification:**
- JSON artifact contains keys `team_0_elo_stats_no_sentinel` and `team_1_elo_stats_no_sentinel`
- min_val in sentinel-excluded stats is >= 0 (not -1.0; ELO=0 rows are retained as potentially valid)

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T04 — z-score outlier deferral documentation

**Objective:** Add a structured deferral note for z-score outlier detection to the JSON artifact.

**Instructions:**

1. Before the artifact-writing Section J, add:

```python
findings["z_score_outliers_deferred"] = {
    "reason": "Deferred to Pipeline Section 01_03",
    "note": (
        "z-score outliers require mean/stddev; for highly skewed distributions "
        "(duration, age uptimes), z-scores are less informative than IQR fences. "
        "Full z-score profiling deferred to 01_03."
    ),
}
```

**Verification:**
- JSON artifact contains key `z_score_outliers_deferred` with `reason` and `note`

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T05 — Duplicate row detection

**Objective:** Check for duplicate rows in both matches_raw and players_raw.

**Instructions:**

1. After Section H (join integrity), add a new Section H.2 titled "Duplicate Row Detection."

2. matches_raw -- check by game_id:

```python
DUPE_MATCHES_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR)) AS distinct_game_ids,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR)) AS duplicate_rows
FROM matches_raw
"""
sql_queries["duplicate_check_matches"] = DUPE_MATCHES_SQL
dupe_m = con.execute(DUPE_MATCHES_SQL).df()
print("matches_raw duplicate check:")
print(dupe_m.to_string(index=False))
findings["duplicate_check_matches"] = {k: int(v) for k, v in dupe_m.iloc[0].to_dict().items()}
```

3. players_raw -- check by (game_id, profile_id) composite:

```python
# COALESCE used because profile_id has 1,185 NULLs in players_raw; NULL || anything = NULL
# in SQL, which would cause those rows to be silently excluded from DISTINCT count.
DUPE_PLAYERS_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__'))
        AS distinct_game_player_pairs,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__'))
        AS duplicate_rows
FROM players_raw
"""
sql_queries["duplicate_check_players"] = DUPE_PLAYERS_SQL
dupe_p = con.execute(DUPE_PLAYERS_SQL).df()
print("players_raw duplicate check:")
print(dupe_p.to_string(index=False))
findings["duplicate_check_players"] = {k: int(v) for k, v in dupe_p.iloc[0].to_dict().items()}
```

**Verification:**
- JSON artifact contains `duplicate_check_matches` and `duplicate_check_players` keys
- Each has `total_rows`, `distinct_*`, and `duplicate_rows` fields

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T06 — NULL co-occurrence analysis for players_raw

**Objective:** Test whether the four high-NULL columns in players_raw co-occur in their NULL/non-NULL patterns.

**Instructions:**

1. After Section B (players_raw NULL census), add Section B.2 titled "NULL Co-occurrence Analysis."

2. Add:

```python
NULL_COOCCURRENCE_SQL = """
SELECT
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NULL
        AND castle_age_uptime IS NULL
        AND imperial_age_uptime IS NULL
        AND opening IS NULL) AS all_four_null,
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NOT NULL
        OR castle_age_uptime IS NOT NULL
        OR imperial_age_uptime IS NOT NULL
        OR opening IS NOT NULL) AS at_least_one_not_null,
    COUNT(*) AS total_rows
FROM players_raw
"""
sql_queries["players_raw_null_cooccurrence"] = NULL_COOCCURRENCE_SQL
cooccur_df = con.execute(NULL_COOCCURRENCE_SQL).df()
print("players_raw NULL co-occurrence:")
print(cooccur_df.to_string(index=False))
findings["players_raw_null_cooccurrence"] = {
    k: int(v) for k, v in cooccur_df.iloc[0].to_dict().items()
}
```

**Verification:**
- JSON artifact contains `players_raw_null_cooccurrence` with `all_four_null`, `at_least_one_not_null`, `total_rows`
- all_four_null + at_least_one_not_null == total_rows

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T07 — DuckDB memory footprint

**Objective:** Record the on-disk size of the DuckDB database file.

**Instructions:**

1. Near the top of the notebook (after the `con = duckdb.connect(...)` cell), add:

```python
import os
db_size_bytes = os.path.getsize(str(AOESTATS_DB_FILE))
print(f"DuckDB file size: {db_size_bytes:,} bytes ({db_size_bytes / 1e9:.2f} GB)")
findings["db_memory_footprint_bytes"] = db_size_bytes
```

**Verification:**
- JSON artifact contains `db_memory_footprint_bytes` as an integer

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T08 — opening non-NULL distribution

**Objective:** Profile the opening column's value distribution among non-NULL rows only.

**Instructions:**

1. After Section E.2 (players_raw categoricals), add Section E.3 titled "opening non-NULL distribution."

2. Add:

```python
OPENING_NONNULL_SQL = """
SELECT
    opening,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_of_nonnull
FROM players_raw
WHERE opening IS NOT NULL
GROUP BY opening
ORDER BY cnt DESC
"""
sql_queries["opening_nonnull_distribution"] = OPENING_NONNULL_SQL
opening_nn_df = con.execute(OPENING_NONNULL_SQL).df()
print(f"opening non-NULL rows: {opening_nn_df['cnt'].sum():,}")
print(opening_nn_df.to_string(index=False))
findings["opening_nonnull_distribution"] = {
    "total_nonnull": int(opening_nn_df["cnt"].sum()),
    "values": opening_nn_df.to_dict(orient="records"),
}
```

**Verification:**
- JSON artifact contains `opening_nonnull_distribution` with `total_nonnull` and `values`
- No entry in `values` has opening=None or opening=NaN

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T09 — Pandas verification print cells before all existing plots

**Objective:** For every existing plot cell in the notebook, add an immediately preceding print/display of the underlying DataFrame.

**Instructions:**

1. Before the winner bar chart (Section C), add:
   ```python
   print("Data feeding winner bar chart:")
   print(winner_df.to_string(index=False))
   ```

2. Before the categorical bars for matches_raw (Section E.3), add a loop printing the top values for each categorical column being plotted.

3. Before the categorical bars for players_raw (Section E.3), add a similar loop.

4. Before the matches numeric histograms (Section F.4), add a loop printing the first/last 5 bins of each histogram DataFrame.

5. Before the players numeric histograms (Section F.4), add a similar loop.

6. Before the boxplots (Section F.5), add a loop printing precomputed percentiles.

7. Before the monthly time series plot (Section G), add:
   ```python
   print(f"Monthly match counts: {len(monthly_df)} months")
   print(monthly_df.to_string(index=False))
   ```

**Verification:**
- Every plot cell in the notebook has an immediately preceding cell with print() or display()

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T10 — Re-run notebook and regenerate artifacts

**Objective:** Execute the full notebook end-to-end, regenerating the JSON and markdown artifacts with all new findings.

**Instructions:**

1. Execute via jupytext: `source .venv/bin/activate && poetry run jupytext --execute sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py --to notebook --output sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.ipynb`

2. Verify the regenerated JSON artifact contains all new keys:
   - `skew_kurtosis_matches`, `skew_kurtosis_players`
   - `near_constant_low_cardinality`, `near_constant_ratio_flagged`, `near_constant_detection_note`
   - `team_0_elo_stats_no_sentinel`, `team_1_elo_stats_no_sentinel`
   - `z_score_outliers_deferred`
   - `duplicate_check_matches`, `duplicate_check_players`
   - `players_raw_null_cooccurrence`
   - `db_memory_footprint_bytes`
   - `opening_nonnull_distribution`

3. Verify the old key `near_constant_fields` no longer exists in the JSON.

**Verification:**
- JSON artifact is valid JSON and contains all expected keys
- `near_constant_fields` key is absent; replaced by `near_constant_low_cardinality` and `near_constant_ratio_flagged`
- `near_constant_detection_note.cardinality_threshold` equals 100
- Notebook executes without errors

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py` | Update |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.ipynb` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` | Rewrite |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` | Rewrite |

## Gate Condition

- JSON artifact contains all 13 new keys: `skew_kurtosis_matches`, `skew_kurtosis_players`, `near_constant_low_cardinality`, `near_constant_ratio_flagged`, `near_constant_detection_note`, `team_0_elo_stats_no_sentinel`, `team_1_elo_stats_no_sentinel`, `z_score_outliers_deferred`, `duplicate_check_matches`, `duplicate_check_players`, `players_raw_null_cooccurrence`, `db_memory_footprint_bytes`, `opening_nonnull_distribution`
- Old key `near_constant_fields` is absent from JSON
- `near_constant_detection_note.cardinality_threshold` is 100 (not 50)
- Every plot cell in the notebook has an immediately preceding print cell
- Notebook executes end-to-end without errors

## Out of Scope

- **Field classification updates:** deferred, no source documentation available
- **Research log entries:** deferred until notebooks are polished
- **Any new visualizations:** deferred to step 01_02_05
- **STEP_STATUS.yaml updates:** not changed; 01_02_04 was already marked complete
- **z-score outlier computation:** explicitly deferred to Pipeline Section 01_03

## Open Questions

- Whether all four high-NULL columns in players_raw perfectly co-occur — the T06 query resolves this empirically
- Whether DuckDB SKEWNESS/KURTOSIS functions handle the 30M/107M row scale within notebook execution timeout — resolves during T10 execution

## Deferred Debt

| Item | Target Step | Rationale |
|------|-------------|-----------|
| z-score outlier detection | 01_03 | IQR fences sufficient for univariate pass; z-scores less informative for skewed distributions |
| Completeness matrix (visual heatmap) | 01_03 | NULL co-occurrence documented tabularly in T06 |
| match_rating_diff empirical leakage test | Phase 02 | Temporal boundary ambiguous; test deferred to feature engineering planning |
