---
category: D
branch: fix/sc2egset-01-03-01-profile-gaps
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [6, 7, 9]
source_artifacts:
  - sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - planning/fixes_and_next_steps.md
critique_required: true
research_log_ref: null
---

# Plan: sc2egset 01_03_01 Profile Gaps Fix (R07, R08, R09, R13)

## Scope

Retroactive corrections to the sc2egset 01_03_01 systematic profiling
notebook. Four gaps identified by the adversarial gate review:
- R07: Stale elapsed_game_loops claim in notebook source (moved from PR1)
- R08: Sentinel summary incomplete (2 of 7 patterns documented)
- R09: Temporal coverage absent from profile JSON (Manual Section 3.2)
- R13: startLocX/startLocY type verification missing

Requires notebook modification and re-execution (~45K rows, fast).

> **[Critique fix: R07 cross-PR]** R07 was originally assigned to PR1 (T06),
> but PR2 re-executes the notebook which regenerates the MD from the .py
> source -- overwriting PR1's MD-only fix. R07 is now handled here, at the
> source level, in a new T00 task.

## Problem Statement

The profile JSON formally documents only 2 sentinel patterns (MMR=0,
SQ=INT32_MIN) despite 5 additional sentinel-like patterns being identified
in 01_02_04 EDA. The profile lacks temporal coverage (date range, gaps)
required by Manual Section 3.2. startLocX/startLocY coordinate columns
have no type or range verification. The notebook source contains a stale
claim that the census still shows elapsed_game_loops as `in_game`, which
is no longer true.

## Assumptions & unknowns

- **Assumption:** The census JSON contains `zero_counts` entries for APM
  and handicap that can be loaded in Cell 3.
- **Assumption:** `details.timeUTC` in replays_meta_raw is VARCHAR storing
  ISO-8601 timestamps that DuckDB TRY_CAST handles correctly.
- **Unknown:** Exact count of negative MMR rows (computed at runtime).
- **Unknown:** Whether any calendar-month gaps exist in the temporal range.

## Execution Steps

### T00 -- Fix stale elapsed_game_loops claim in notebook source (R07)

**Objective:** Fix the stale "still shows it as" text at its source -- the
notebook .py file -- so that re-execution produces correct MD output.

> **[Critique fix: R07 cross-PR]** PR1 originally fixed only the generated
> MD file. Since PR2 re-executes the notebook and regenerates the MD from
> the .py source, the fix must be applied to the .py source instead.

**Instructions:**

1. In the notebook .py source, find the JSON assembly string (~line 1320-1323):
   ```python
   "elapsed_game_loops_reclassification": (
       "elapsed_game_loops reclassified as POST-GAME on 2026-04-15. "
       "The census JSON (01_02_04) still shows it as 'in_game'; "
       "this profiling step records the corrected classification."
   ),
   ```
   Replace with:
   ```python
   "elapsed_game_loops_reclassification": (
       "elapsed_game_loops classified POST-GAME, consistent with "
       "the census artifact (01_02_04) which also records it under "
       "'post_game' in the I3 classification."
   ),
   ```

2. In the notebook .py source, find the MD template string (~line 1439-1440):
   ```
   > Note: `elapsed_game_loops` was reclassified as **POST-GAME** on 2026-04-15.
   > The census artifact (01_02_04) still shows it as `in_game`; this notebook records the corrected classification.
   ```
   Replace with:
   ```
   > Note: `elapsed_game_loops` classified **POST-GAME**, consistent with the census artifact (01_02_04) which also records it under `post_game` in the I3 classification.
   ```

**Verification:**
- `grep "still shows it as" <.py file>` returns zero matches.
- Both the JSON string and the MD template contain "consistent with the census artifact".

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T01 -- Expand sentinel summary with 5 additional patterns (R08)

**Objective:** Add APM=0, MMR<0, map_size=0, handicap=0, and
selectedRace="" to the sentinel analysis.

**Instructions:**

1. In Cell 3 (Census Load and Runtime Constants), after the existing
   `SQ_SENTINEL_COUNT` extraction, add extractions for APM and handicap
   zero counts from the census JSON `zero_counts` section.

2. Insert a new Cell 18b (after Cell 18 -- Critical Field Detection)
   titled "## Cell 18b -- Extended Sentinel Analysis (R08)". Run three
   SQL queries:

   SQL `sentinel_mmr_negative`:
   ```sql
   SELECT
       COUNT(*) AS mmr_negative_count,
       MIN(MMR) AS mmr_min_negative,
       MAX(MMR) AS mmr_max_negative,
       ROUND(100.0 * COUNT(*) / {RP_TOTAL_ROWS}, 4) AS mmr_negative_pct
   FROM replay_players_raw
   WHERE MMR < 0
   ```

   SQL `sentinel_map_size_zero`:
   ```sql
   SELECT COUNT(*) AS map_size_zero_count
   FROM replays_meta_raw
   WHERE initData.gameDescription.mapSizeX = 0
     AND initData.gameDescription.mapSizeY = 0
   ```

   > **[Critique fix: T01.2]** map_size_zero counts replays from
   > `replays_meta_raw` (22,390 rows), not `replay_players_raw` (44,817
   > rows). The percentage MUST use `RM_TOTAL_ROWS` as denominator:
   > ```python
   > map_size_zero_pct = round(100.0 * map_size_zero_count / RM_TOTAL_ROWS, 4)
   > ```
   > The sentinel entry MUST record `"table": "replays_meta_raw"`. In the MD
   > sentinel table, add a footnote:
   > `* map_size uses replays_meta_raw (N={RM_TOTAL_ROWS:,}); all others use replay_players_raw (N={RP_TOTAL_ROWS:,})`

   SQL `sentinel_selectedrace_empty`:
   ```sql
   SELECT COUNT(*) AS selected_race_empty_count
   FROM replay_players_raw
   WHERE selectedRace = ''
   ```

   Store all three in `sql_queries` dict. Extract scalar results.

3. Extend `critical_findings["sentinel_columns"]` list with 5 entries.
   All counts from runtime variables, not hardcoded (Invariant #7).
   For map_size_zero: `"table": "replays_meta_raw"`.
   For all others: `"table": "replay_players_raw"`.

4. In JSON assembly, extend `sentinel_summary` with 5 new keys.

5. In MD assembly, extend sentinel table from 2 to 7 rows with footnote.

**Verification:**
- `sentinel_summary` has exactly 7 keys
- `critical_findings.sentinel_columns` has exactly 7 entries
- All 3 new SQL queries in `sql_queries` dict (Invariant #6)
- map_size_zero percentage uses RM_TOTAL_ROWS denominator

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T02 -- Add temporal coverage section (R09)

**Objective:** Add temporal coverage (date range, gaps) to profile JSON/MD.

**Instructions:**

1. Insert a new Cell 18c (after Cell 18b) titled "## Cell 18c --
   Temporal Coverage (R09)". Run two SQL queries:

   SQL `temporal_coverage`:
   ```sql
   SELECT
       MIN(details.timeUTC) AS time_utc_min,
       MAX(details.timeUTC) AS time_utc_max,
       COUNT(DISTINCT strftime(TRY_CAST(details.timeUTC AS TIMESTAMP), '%Y-%m'))
           AS distinct_months
   FROM replays_meta_raw
   WHERE details.timeUTC IS NOT NULL
   ```

   SQL `temporal_month_gaps`:
   ```sql
   WITH parsed AS (
       SELECT strftime(TRY_CAST(details.timeUTC AS TIMESTAMP), '%Y-%m') AS ym
       FROM replays_meta_raw
       WHERE details.timeUTC IS NOT NULL
   ),
   observed AS (
       SELECT DISTINCT ym FROM parsed WHERE ym IS NOT NULL
   ),
   date_range AS (
       SELECT MIN(ym) AS min_ym, MAX(ym) AS max_ym FROM observed
   ),
   all_months AS (
       SELECT strftime(
           (SELECT TRY_CAST(min_ym || '-01' AS DATE) FROM date_range)
           + INTERVAL (i) MONTH,
           '%Y-%m'
       ) AS ym
       FROM generate_series(0,
           (SELECT DATEDIFF('month',
               TRY_CAST(min_ym || '-01' AS DATE),
               TRY_CAST(max_ym || '-01' AS DATE))
            FROM date_range)
       ) AS t(i)
   )
   SELECT am.ym AS gap_month
   FROM all_months am
   LEFT JOIN observed o ON am.ym = o.ym
   WHERE o.ym IS NULL
   ORDER BY am.ym
   ```

   Use TRY_CAST (not CAST) for robustness. Store in `sql_queries` dict.

   > **[Critique fix: T02.1]** Fallback: if the `temporal_month_gaps` CTE
   > fails, simplify to Python-side gap computation:
   > ```python
   > import pandas as pd
   > observed_months_df = conn.fetch_df(
   >     "SELECT DISTINCT strftime(TRY_CAST(details.timeUTC AS TIMESTAMP), '%Y-%m') AS ym "
   >     "FROM replays_meta_raw WHERE details.timeUTC IS NOT NULL "
   >     "AND TRY_CAST(details.timeUTC AS TIMESTAMP) IS NOT NULL ORDER BY ym"
   > )
   > observed_set = set(observed_months_df["ym"].dropna())
   > min_ym, max_ym = min(observed_set), max(observed_set)
   > all_months = set(
   >     pd.date_range(min_ym + "-01", max_ym + "-01", freq="MS").strftime("%Y-%m")
   > )
   > gap_months = sorted(all_months - observed_set)
   > ```
   > Acceptable because dataset is small (~22K replays). Record the SQL text
   > in `sql_queries` with a note that the Python fallback was used.

   > **[Critique fix: T02.2]** After executing temporal_coverage, add
   > TRY_CAST verification:
   > ```python
   > raw_distinct = conn.fetch_df(
   >     "SELECT COUNT(DISTINCT details.timeUTC) FROM replays_meta_raw "
   >     "WHERE details.timeUTC IS NOT NULL"
   > ).iloc[0, 0]
   > assert DISTINCT_MONTH_COUNT > 0, "No parseable timestamps found"
   > print(f"TRY_CAST verification: {raw_distinct} distinct raw values -> "
   >       f"{DISTINCT_MONTH_COUNT} distinct months")
   > ```
   > Record this verification query in `sql_queries` as well (Invariant #6).

2. In JSON assembly, add `temporal_coverage` to `dataset_level`.

3. In MD assembly, add "## Temporal Coverage" section.

**Verification:**
- `dataset_level.temporal_coverage` exists with all 4 keys
- MD contains "## Temporal Coverage" section
- Both SQL queries in `sql_queries` dict (Invariant #6)
- TRY_CAST verification passes (DISTINCT_MONTH_COUNT > 0)

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T03 -- startLocX/startLocY type verification (R13)

**Objective:** Verify startLocX and startLocY contain valid integer values.

**Instructions:**

1. Insert Cell 18d (after Cell 18c). SQL `startloc_verification`:
   ```sql
   SELECT
       COUNT(*) AS total_rows,
       COUNT(*) - COUNT(startLocX) AS startLocX_null,
       COUNT(*) - COUNT(startLocY) AS startLocY_null,
       SUM(CASE WHEN startLocX < 0 THEN 1 ELSE 0 END) AS startLocX_negative,
       SUM(CASE WHEN startLocY < 0 THEN 1 ELSE 0 END) AS startLocY_negative,
       MIN(startLocX) AS startLocX_min,
       MAX(startLocX) AS startLocX_max,
       MIN(startLocY) AS startLocY_min,
       MAX(startLocY) AS startLocY_max,
       COUNT(DISTINCT startLocX) AS startLocX_cardinality,
       COUNT(DISTINCT startLocY) AS startLocY_cardinality
   FROM replay_players_raw
   ```
   Store in `sql_queries`. Assert zero NULLs. Print summary.

2. In JSON assembly, add `startloc_verification` to `dataset_level`.
3. In MD assembly, add brief verification note.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T04 -- Re-execute notebook and verify artifacts

**Objective:** Execute modified notebook end-to-end, verify all artifacts.

**Instructions:**

1. Execute:
   ```bash
   source .venv/bin/activate && poetry run jupytext --to notebook \
     sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py && \
   poetry run jupyter execute \
     sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.ipynb \
     --ExecutePreprocessor.timeout=300
   ```

2. Verify artifacts exist and are non-empty (JSON, MD, 3 PNGs).

3. Validate JSON programmatically.

4. **[Critique fix: T04.1 BLOCKER]** Add these 4 explicit assertions to
   Cell 24 of the notebook source (.py file):
   ```python
   assert len(profile_chk["sentinel_summary"]) == 7, (
       f"Expected 7 sentinel_summary entries, got {len(profile_chk['sentinel_summary'])}"
   )
   assert "temporal_coverage" in profile_chk.get("dataset_level", {}), (
       "JSON missing temporal_coverage key"
   )
   assert "startloc_verification" in profile_chk.get("dataset_level", {}), (
       "JSON missing startloc_verification key"
   )
   assert len(profile_chk["critical_findings"]["sentinel_columns"]) == 7, (
       f"Expected 7 sentinel_columns, got "
       f"{len(profile_chk['critical_findings']['sentinel_columns'])}"
   )
   ```
   These must be in the notebook source, not just run ad-hoc.

**Verification:**
- Notebook executes end-to-end without errors
- All 5 artifact files exist and are non-empty
- Gate cell passes with all assertions including the 4 new ones
- `grep "still shows it as" <MD file>` returns zero matches (R07 propagated)

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.ipynb`
- `src/.../sc2egset/reports/artifacts/.../01_03_01_systematic_profile.json`
- `src/.../sc2egset/reports/artifacts/.../01_03_01_systematic_profile.md`
- `src/.../sc2egset/reports/artifacts/.../01_03_01_completeness_heatmap.png`
- `src/.../sc2egset/reports/artifacts/.../01_03_01_qq_plots.png`
- `src/.../sc2egset/reports/artifacts/.../01_03_01_ecdf_key_columns.png`

---

## File Manifest

| File | Action | Task |
|------|--------|------|
| `sandbox/sc2/sc2egset/.../01_03_01_systematic_profiling.py` | Update | T00-T04 |
| `sandbox/sc2/sc2egset/.../01_03_01_systematic_profiling.ipynb` | Rewrite | T04 |
| `src/.../sc2egset/.../01_03_01_systematic_profile.json` | Rewrite | T04 |
| `src/.../sc2egset/.../01_03_01_systematic_profile.md` | Rewrite | T04 |
| `src/.../sc2egset/.../01_03_01_completeness_heatmap.png` | Rewrite | T04 |
| `src/.../sc2egset/.../01_03_01_qq_plots.png` | Rewrite | T04 |
| `src/.../sc2egset/.../01_03_01_ecdf_key_columns.png` | Rewrite | T04 |

## Gate Condition

- Notebook executes end-to-end without errors
- `sentinel_summary` has exactly 7 keys; `sentinel_columns` has 7 entries
- `dataset_level.temporal_coverage` exists with min/max, month count, gaps
- `dataset_level.startloc_verification` exists with ranges/cardinalities
- map_size_zero percentage uses RM_TOTAL_ROWS; entry has `table: replays_meta_raw`
- TRY_CAST verification passes (DISTINCT_MONTH_COUNT > 0)
- Profile MD does NOT contain "still shows it as" (R07)
- Cell 24 contains all 4 new gate assertions
- All new SQL queries in JSON `sql_queries` section (I6)
- No magic numbers (I7); no cleaning decisions (I9)

## Implementation notes

- DuckDB connection: `conn`, method `conn.fetch_df(sql)`.
- New cells: 18b, 18c, 18d (no renumbering).
- `details.timeUTC` is VARCHAR ISO-8601 -- use TRY_CAST.
- startLocX/startLocY are INTEGER per schema YAML.
- R07 stale text in TWO .py locations: JSON assembly and MD template.
- Execution budget: ~2 min (45K rows).

## Critique fix summary

| Fix ID | Severity | Description |
|--------|----------|-------------|
| T04.1 | BLOCKER | Added 4 explicit gate assertions to T04 |
| T01.2 | WARNING | map_size_zero uses RM_TOTAL_ROWS; records replays_meta_raw |
| T02.1 | WARNING | Python fallback for generate_series CTE |
| T02.2 | WARNING | TRY_CAST NULL verification assertion |
| R07 | WARNING | Moved from PR1 to PR2 T00; fixes .py source |
