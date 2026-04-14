---
category: A
branch: feat/aoe2companion-01-02-04-pass2
date: 2026-04-14
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [6, 7, 9]
source_artifacts:
  - sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: null
---

# Plan: aoe2companion 01_02_04 Pass 2 -- Analytics Fixes

## Scope

Quantitative analytics fixes to the existing Step 01_02_04 notebook (Univariate Census & Target Variable EDA) for the aoe2companion dataset. This pass addresses a BLOCKER (dead-field detection missing 7 profiles_raw columns that are 100% NULL) and 8 additional analytics gaps identified by adversarial review. No new plots in this pass -- all visualization work is deferred to Step 01_02_05.

Phase 01, Pipeline Section 01_02 (EDA), Step 01_02_04 (second execution pass).

## Problem Statement

The 01_02_04 notebook was augmented with empty-string investigation, exact won NULL patch, zero counts, post-game annotations, and field classification. An adversarial review identified that the dead-field detector uses `approx_cardinality <= 1` as the sole filter, which misses 7 profiles_raw columns that are 100% NULL but return phantom HyperLogLog cardinalities of 2-44. This is a BLOCKER because downstream cleaning steps will treat these genuinely dead columns as active.

Additional gaps: no skewness/kurtosis for numeric columns, incomplete leaderboards_raw profiling (missing categorical, boolean, temporal columns), incomplete profiles_raw profiling (missing categorical profiling), no duplicate row detection, no NULL co-occurrence analysis for the 0.15% cluster, no memory footprint, and the near-constant threshold flags semantically important categoricals like `map` (261 values) and `civ` (68 values) as near-constant.

## Assumptions & unknowns

- **Assumption:** The 7 profiles_raw columns (sharedHistory, twitchChannel, youtubeChannel, youtubeChannelName, discordId, discordName, discordInvitation) are 100% NULL. This is verifiable from the existing profiles_raw_null_census in the JSON artifact (all show null_pct = 100.0 but approx_cardinality > 1).
- **Assumption:** colorHex is already present in the empty_string_investigation artifact (7 entries total). Visual inspection of the artifact confirms this -- colorHex has empty_string_count=0. The assertion of "missing colorHex" from the review appears stale -- if colorHex is already present, no action needed.
- **Unknown:** Whether the two NULL clusters in matches_raw co-occur perfectly within their respective groups:
  - Cluster A (8 columns, null_count=415,649): allowCheats, lockSpeed, lockTeams, recordGame, sharedExploration, teamPositions, teamTogether, turboMode
  - Cluster B (2 columns, null_count=443,358): fullTechTree, population
  Note: fullTechTree has a different null_count (443,358) from the 8-column cluster (415,649) — these are two separate clusters. Resolves by: T06 execution.

## Literature context

EDA Manual Section 3.1 requires skewness and kurtosis for all numeric columns. Section 3.2 requires duplicate row detection, feature completeness matrix, and memory footprint. Section 3.3 requires dead-field detection using 100% NULL as the canonical criterion (HyperLogLog phantom cardinalities are a known issue in approximate counting -- Flajolet et al. 2007 describe the probabilistic error bounds that produce non-zero estimates on empty sets).

The near-constant threshold of uniqueness_ratio < 0.001 is from the EDA Manual Section 3.3 as a "reasonable starting point," but the manual explicitly notes "the threshold for flagging depends on context." At N=277M rows, every column with fewer than 277,099 distinct values is flagged, including columns like `map` (261), `civ` (68), and `leaderboard` (22) that are semantically critical game features. Splitting the detection into cardinality-based buckets is the standard mitigation.

## Execution Steps

### T01 -- Fix dead-field detection (BLOCKER)

**Objective:** Change the constant_fields detection to include columns that are 100% NULL regardless of their HyperLogLog approx_cardinality. After the fix, the 7 profiles_raw dead columns must appear in `constant_fields` in the JSON artifact.

**Instructions:**

1. In Section I ("Dead/constant/near-constant field detection"), locate the line:
   ```python
   constant_fields = all_census_df[all_census_df["approx_cardinality"] <= 1]
   ```

2. Merge the null_pct data into `all_census_df` before the filter. Modify the concatenation block to also include `null_pct`:
   ```python
   for table_name, census_df, total in [
       ("matches_raw", null_census_matches, total_rows),
       ("leaderboards_raw", lb_null_census, lb_total),
       ("profiles_raw", pr_null_census, pr_total),
       ("ratings_raw", rt_null_census, rt_total),
   ]:
       subset = census_df[["column_name", "approx_cardinality", "null_pct"]].copy()
       subset["table"] = table_name
       subset["total_rows"] = total
       subset["uniqueness_ratio"] = subset["approx_cardinality"] / total
       all_census.append(subset)
   ```

3. Change the constant_fields filter to:
   ```python
   constant_fields = all_census_df[
       (all_census_df["approx_cardinality"] <= 1) | (all_census_df["null_pct"] >= 100.0)
   ]
   ```

4. Add a print statement listing the dead columns by name and table:
   ```python
   print(f"Dead fields detected: {len(constant_fields)}")
   for _, row in constant_fields.iterrows():
       print(f"  {row['table']}.{row['column_name']} "
             f"(approx_cardinality={row['approx_cardinality']}, null_pct={row['null_pct']})")
   ```

5. Add an assertion that the 7 profiles_raw columns appear:
   ```python
   expected_dead_profiles = {
       "sharedHistory", "twitchChannel", "youtubeChannel",
       "youtubeChannelName", "discordId", "discordName", "discordInvitation"
   }
   actual_dead_profiles = set(
       constant_fields.loc[constant_fields["table"] == "profiles_raw", "column_name"]
   )
   missing = expected_dead_profiles - actual_dead_profiles
   assert not missing, f"BLOCKER: Dead profiles_raw columns missing: {missing}"
   ```

**Verification:**
- The assertion on expected_dead_profiles must pass.
- In the output JSON, `constant_fields` must contain at least 12 entries (5 existing + 7 new profiles_raw).

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T02 -- Skewness and kurtosis for all numeric columns

**Objective:** Compute SKEWNESS and KURTOSIS for all numeric columns across matches_raw, ratings_raw, and leaderboards_raw, as required by EDA Manual Section 3.1.

**Instructions:**

1. Add a new section after Section F (Numeric descriptive statistics). Title: `## F1b. Skewness and Kurtosis`.

2. For matches_raw numeric columns (rating, ratingDiff, population, slot, color, team, speedFactor, treatyLength, internalLeaderboardId), execute per-column:
   ```sql
   SELECT
       '{col}' AS column_name,
       ROUND(SKEWNESS("{col}"), 4) AS skewness,
       ROUND(KURTOSIS("{col}"), 4) AS kurtosis
   FROM matches_raw
   WHERE "{col}" IS NOT NULL
   ```
   Collect into list, store as `findings["matches_raw_skew_kurtosis"]`. Print as DataFrame.

3. Repeat for ratings_raw numeric columns (leaderboard_id, season, rating, games, rating_diff).
   Note: leaderboard_id and season are stored as numeric types in ratings_raw and must be
   included per the notebook's column list (5 numeric columns, not 3).
   Store as `findings["ratings_raw_skew_kurtosis"]`.

4. Repeat for leaderboards_raw numeric columns (rank, rating, wins, losses, games, streak, drops, rankCountry, season, rankLevel).
   Store as `findings["leaderboards_raw_skew_kurtosis"]`.

5. Add SQL template and results tables to the markdown artifact section F1b.

**Verification:**
- JSON artifact contains keys `matches_raw_skew_kurtosis` (9 entries), `ratings_raw_skew_kurtosis` (5 entries), `leaderboards_raw_skew_kurtosis` (10 entries).

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T03 -- leaderboards_raw categorical, boolean, and temporal profiling

**Objective:** Add categorical (leaderboard VARCHAR, country VARCHAR), boolean (active), and temporal (lastMatchTime, updatedAt) profiling for leaderboards_raw, which currently only receives numeric stats and NULL census.

**Instructions:**

1. Add a new section after H.1 (leaderboards_raw NULL census). Title: `### H.1b leaderboards_raw categorical, boolean, and temporal`.

2. Top-k for `leaderboard` VARCHAR (all values):
   ```sql
   SELECT
       leaderboard AS value,
       COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
   FROM leaderboards_raw
   GROUP BY leaderboard
   ORDER BY cnt DESC
   ```
   Print result. Store `leaderboard` list in `findings["leaderboards_raw_categorical"]["leaderboard"]`.

3. Top-k for `country` VARCHAR (top 30 + NULL count):
   ```sql
   SELECT country AS value, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
   FROM leaderboards_raw GROUP BY country ORDER BY cnt DESC LIMIT 30
   ```
   Store in `findings["leaderboards_raw_categorical"]["country"]` with `null_count` sub-key.

4. Boolean census for `active`:
   ```sql
   SELECT 'active' AS column_name,
       COUNT(*) FILTER (WHERE active = TRUE) AS true_count,
       COUNT(*) FILTER (WHERE active = FALSE) AS false_count,
       COUNT(*) - COUNT(active) AS null_count,
       COUNT(*) AS total_rows,
       ROUND(100.0 * COUNT(*) FILTER (WHERE active = TRUE) / COUNT(*), 2) AS true_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE active = FALSE) / COUNT(*), 2) AS false_pct,
       ROUND(100.0 * (COUNT(*) - COUNT(active)) / COUNT(*), 2) AS null_pct
   FROM leaderboards_raw
   ```
   Store as `findings["leaderboards_raw_boolean"]`.

5. Temporal range for `lastMatchTime` and `updatedAt` using UNION ALL MIN/MAX query.
   Store as `findings["leaderboards_raw_temporal"]`.

6. Add `leaderboard_id` distribution for ratings_raw (cardinality=15):
   ```sql
   SELECT leaderboard_id AS value, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
   FROM ratings_raw GROUP BY leaderboard_id ORDER BY cnt DESC
   ```
   Store as `findings["ratings_raw_leaderboard_id_distribution"]`.

7. Add SQL blocks to the markdown artifact.

**Verification:**
- JSON artifact contains keys `leaderboards_raw_categorical`, `leaderboards_raw_boolean`, `leaderboards_raw_temporal`, `ratings_raw_leaderboard_id_distribution`.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T04 -- profiles_raw categorical profiling

**Objective:** Add categorical profiling for profiles_raw country and clan columns, which currently only get NULL census.

**Instructions:**

1. Add a new section after H.2 (profiles_raw NULL census). Title: `### H.2b profiles_raw categorical`.

2. Top-k for `country` VARCHAR (top 30 + NULL count and NULL pct):
   ```sql
   SELECT country AS value, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
   FROM profiles_raw GROUP BY country ORDER BY cnt DESC LIMIT 30
   ```
   Store in `findings["profiles_raw_categorical"]["country"]`.

3. Top-k for `clan` VARCHAR (top 30 + cardinality + null count):
   ```sql
   SELECT clan AS value, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
   FROM profiles_raw GROUP BY clan ORDER BY cnt DESC LIMIT 30
   ```
   Store in `findings["profiles_raw_categorical"]["clan"]` with `cardinality` and `null_count` sub-keys.

4. Add a note referencing the 7 dead columns documented in constant_fields after T01 fix.

5. Add SQL blocks to the markdown artifact.

**Verification:**
- JSON artifact contains `profiles_raw_categorical` with `country` and `clan` sub-keys.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T05 -- Duplicate row detection

**Objective:** Check for duplicate composite keys in matches_raw and ratings_raw.

**Instructions:**

1. Add a new section after Section I. Title: `## I2. Duplicate row detection`.

2. matches_raw -- check for duplicate (matchId, profileId) pairs:
   ```sql
   SELECT
       COUNT(*) AS total_rows,
       COUNT(DISTINCT CAST("matchId" AS VARCHAR) || '|' || CAST("profileId" AS VARCHAR))
           AS distinct_pairs,
       COUNT(*) - COUNT(DISTINCT CAST("matchId" AS VARCHAR) || '|' || CAST("profileId" AS VARCHAR))
           AS duplicate_rows
   FROM matches_raw
   ```
   Store as `findings["matches_raw_duplicate_check"]`.

3. ratings_raw -- check for duplicate (profile_id, leaderboard_id, date) triples:
   ```sql
   SELECT
       COUNT(*) AS total_rows,
       COUNT(DISTINCT CAST(profile_id AS VARCHAR) || '|'
           || CAST(leaderboard_id AS VARCHAR) || '|'
           || CAST(date AS VARCHAR))
           AS distinct_triples,
       COUNT(*) - COUNT(DISTINCT CAST(profile_id AS VARCHAR) || '|'
           || CAST(leaderboard_id AS VARCHAR) || '|'
           || CAST(date AS VARCHAR))
           AS duplicate_rows
   FROM ratings_raw
   ```
   Store as `findings["ratings_raw_duplicate_check"]`.

4. Add SQL blocks to the markdown artifact.

**Verification:**
- JSON artifact contains keys `matches_raw_duplicate_check` and `ratings_raw_duplicate_check`.
- Each entry has `total_rows`, `distinct_pairs`/`distinct_triples`, and `duplicate_rows`.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T06 -- NULL co-occurrence analysis for matches_raw NULL clusters

**Objective:** Determine co-occurrence patterns for two distinct NULL clusters in matches_raw:
- Cluster A (8 columns, null_count=415,649): allowCheats, lockSpeed, lockTeams, recordGame, sharedExploration, teamPositions, teamTogether, turboMode
- Cluster B (2 columns, null_count=443,358): fullTechTree, population

Note: fullTechTree and population have a DIFFERENT null count (443,358) from the other 8 columns (415,649). These are two separate clusters — fullTechTree does NOT belong with the 8-column cluster.

**Instructions:**

1. Add a new section after I2. Title: `## I3. NULL co-occurrence for 0.15%-0.16% clusters`.

2. Check whether all 8 Cluster A columns are simultaneously NULL:
   ```sql
   SELECT
       COUNT(*) AS all_eight_null_simultaneously,
       (SELECT COUNT(*) FROM matches_raw WHERE "allowCheats" IS NULL)
           AS allowCheats_null_count
   FROM matches_raw
   WHERE "allowCheats" IS NULL
       AND "lockSpeed" IS NULL AND "lockTeams" IS NULL
       AND "recordGame" IS NULL AND "sharedExploration" IS NULL
       AND "teamPositions" IS NULL AND "teamTogether" IS NULL
       AND "turboMode" IS NULL
   ```

3. Check whether fullTechTree and population (Cluster B) are simultaneously NULL:
   ```sql
   SELECT
       COUNT(*) AS both_null,
       (SELECT COUNT(*) FROM matches_raw WHERE "fullTechTree" IS NULL)
           AS fullTechTree_null_count,
       (SELECT COUNT(*) FROM matches_raw WHERE population IS NULL)
           AS population_null_count
   FROM matches_raw
   WHERE "fullTechTree" IS NULL AND population IS NULL
   ```

4. Test cross-cluster overlap (are Cluster A NULLs a subset of Cluster B NULLs?):
   ```sql
   SELECT
       COUNT(*) FILTER (WHERE "allowCheats" IS NULL AND "fullTechTree" IS NULL)
           AS both_clusters_null,
       COUNT(*) FILTER (WHERE "allowCheats" IS NULL AND "fullTechTree" IS NOT NULL)
           AS cluster_a_only_null,
       COUNT(*) FILTER (WHERE "allowCheats" IS NOT NULL AND "fullTechTree" IS NULL)
           AS cluster_b_only_null
   FROM matches_raw
   ```

5. Store as `findings["matches_raw_null_cooccurrence"]` with sub-keys:
   `cluster_a_eight_cols`, `cluster_b_fulltree_population`, `cross_cluster_overlap`.

6. Add SQL blocks to the markdown artifact.

**Verification:**
- JSON artifact contains key `matches_raw_null_cooccurrence` with 3 sub-keys.
- `cluster_a_eight_cols.all_eight_null_simultaneously` should equal `allowCheats_null_count` if co-occurring.
- `cluster_b_fulltree_population.both_null` should equal ~443,358 if co-occurring.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T07 -- Memory footprint

**Objective:** Record the DuckDB file size as a dataset-level metric (EDA Manual Section 3.2).

**Instructions:**

1. Add a cell near the beginning of the notebook (after the connection cell):
   ```python
   import os
   # Note: DB_FILE is not defined in this notebook's scope; use db._dataset.db_file
   # (where db = get_notebook_db("aoe2", "aoe2companion")).
   db_size_bytes = os.path.getsize(str(db._dataset.db_file))
   print(f"DuckDB file size: {db_size_bytes:,} bytes "
         f"({db_size_bytes / (1024**3):.2f} GB)")
   findings["db_memory_footprint_bytes"] = db_size_bytes
   ```

**Verification:**
- JSON artifact contains key `db_memory_footprint_bytes` with a positive integer value.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T08 -- Near-constant threshold fix

**Objective:** Split near-constant detection into two buckets to prevent semantically important categoricals (map, civ) from being mislabeled as near-constant at N=277M.

**Instructions:**

1. In Section I, replace the existing `near_constant` filter with two buckets:
   ```python
   # [I7] Empirical threshold: max clearly categorical cardinality is ~68 (civ);
   # next meaningful categorical is map (~261) which falls above 100.
   # Threshold of 100 cleanly separates low-cardinality semantically meaningful
   # categoricals (leaderboard=22, civ=68) from map (261) and continuous columns.
   # At N=277M rows, uniqueness_ratio < 0.001 flags all columns with < 277,000
   # distinct values — including semantically important categoricals.
   NEAR_CONSTANT_CARDINALITY_THRESHOLD = 100  # empirical: max categorical=68 (civ), min ratio-flagged=261 (map)

   # Bucket 1: genuinely low-cardinality (< 100 distinct values, not constant/dead)
   near_constant_low_card = all_census_df[
       (all_census_df["uniqueness_ratio"] < 0.001)
       & (all_census_df["approx_cardinality"] > 1)
       & (all_census_df["approx_cardinality"] < NEAR_CONSTANT_CARDINALITY_THRESHOLD)
       & (all_census_df["null_pct"] < 100.0)
   ]
   # Bucket 2: moderate-cardinality columns flagged only by ratio (NOT near-constant)
   near_constant_ratio_flagged = all_census_df[
       (all_census_df["uniqueness_ratio"] < 0.001)
       & (all_census_df["approx_cardinality"] >= NEAR_CONSTANT_CARDINALITY_THRESHOLD)
   ]
   ```

2. Update print statements to distinguish the two buckets.

3. Update findings storage:
   ```python
   findings["near_constant_low_cardinality"] = near_constant_low_card.to_dict(orient="records")
   findings["near_constant_ratio_flagged"] = near_constant_ratio_flagged.to_dict(orient="records")
   ```
   Remove the old `near_constant_fields` key.

4. Update the markdown artifact section to document both buckets and the threshold rationale citing EDA Manual Section 3.3.

**Verification:**
- JSON artifact contains `near_constant_low_cardinality` and `near_constant_ratio_flagged`.
- Old `near_constant_fields` key no longer present.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T09 -- Remove existing plot cells, add pandas verification prints

**Objective:** Remove all matplotlib plot cells from the notebook (plots move to 01_02_05) and add print/display() of the underlying DataFrame at each former plot location.

**Instructions:**

1. Remove these plot cells entirely:
   - Section B won distribution bar chart (`01_02_04_won_distribution.png`)
   - Section D categorical bar charts (`01_02_04_categorical_topk.png`)
   - Section F.4 histograms (`01_02_04_numeric_histograms.png`)
   - Section F.4 boxplots (`01_02_04_numeric_boxplots.png`)
   - Section G temporal match counts line chart (`01_02_04_temporal_match_counts.png`)

2. Remove `import matplotlib`, `import matplotlib.pyplot as plt`, and `matplotlib.use("Agg")` from the imports section.

3. At each removed-plot location, add a verification print cell:
   ```python
   # Verification: <data name> (deferred to 01_02_05 for plotting)
   print("=== <data name> (feeds <chart type>) ===")
   print(<df>.to_string(index=False))
   ```

4. Remove the `01_02_04_*.png` references from the markdown artifact.

**Verification:**
- No matplotlib import in the notebook.
- No `.savefig()` calls.
- No `plt.` calls.
- Every former plot location has a print verification cell.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

### T10 -- Regenerate JSON and markdown artifacts

**Objective:** Run the notebook end-to-end to regenerate the JSON and markdown artifacts with all fixes from T01-T09.

**Instructions:**

1. Execute the full notebook via jupytext with `--ExecutePreprocessor.timeout=1800`.
2. Verify the JSON artifact contains all new keys:
   - `matches_raw_skew_kurtosis`, `ratings_raw_skew_kurtosis`, `leaderboards_raw_skew_kurtosis`
   - `ratings_raw_leaderboard_id_distribution`
   - `leaderboards_raw_categorical`, `leaderboards_raw_boolean`, `leaderboards_raw_temporal`
   - `profiles_raw_categorical`
   - `matches_raw_duplicate_check`, `ratings_raw_duplicate_check`
   - `matches_raw_null_cooccurrence`
   - `db_memory_footprint_bytes`
   - `near_constant_low_cardinality`, `near_constant_ratio_flagged`
3. Verify `constant_fields` contains the 7 profiles_raw dead columns.
4. Verify old `near_constant_fields` key is absent.
5. Verify no PNG references in the markdown artifact.
6. Sync the .ipynb.

**Verification:**
- JSON artifact is valid JSON.
- All new keys present.
- Notebook executes end-to-end without errors within 1800s timeout.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py` | Rewrite |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb` | Rewrite |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` | Rewrite |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` | Rewrite |

## Gate Condition

- `constant_fields` in JSON artifact contains 12+ entries, including 7 profiles_raw dead columns.
- BLOCKER assertion passes (`expected_dead_profiles` all present).
- All 14 new JSON keys present (list in T10).
- `near_constant_fields` key absent; replaced by two-bucket keys.
- No matplotlib imports or `.savefig()` calls in the .py file.
- Every removed-plot location has a DataFrame print verification cell.
- JSON artifact is valid JSON.
- Notebook executes end-to-end without errors.

## Out of scope

- All visualization (deferred to 01_02_05).
- Field classification revision (deferred -- no source documentation).
- Research log entries (deferred until notebooks polished).
- STEP_STATUS.yaml update (no step completion -- this is a revision pass).
- Bivariate or multivariate analysis (Pipeline Section 01_03+).
- colorHex empty-string check (already present in existing artifact per plan inspection).

## Open questions

- colorHex empty-string investigation: if the executor confirms colorHex is already present in the artifact (7 entries total), no action needed. If somehow missing, add it to the existing empty_string_investigation loop in Section A2.

## Deferred Debt

| Item | Target Step | Rationale |
|------|-------------|-----------|
| String pattern/format frequency for name, colorHex | 01_03 | High-cardinality strings; pattern analysis deferred |
| Completeness matrix (visual heatmap) | 01_03 | NULL patterns documented in tabular census; visual in 01_02_05 |
| Memory footprint visual (pie/bar) | 01_03 | Scalar value sufficient for univariate step |
| Bivariate analysis | 01_03+ | Out of scope for univariate census |
