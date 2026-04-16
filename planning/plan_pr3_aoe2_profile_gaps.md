---
category: D
branch: fix/aoe2-01-03-01-profile-gaps
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: aoe2companion, aoestats
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [6, 7, 8, 9]
source_artifacts:
  - sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_01_systematic_profiling.py
  - sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - planning/fixes_and_next_steps.md
critique_required: true
research_log_ref: null
---

# Plan: Fix aoe2 01_03_01 profile gaps (R06, R10, R11, R12)

## Scope

Retroactive corrections to the aoestats and aoe2companion 01_03_01 systematic
profiling notebooks. Four items from `planning/fixes_and_next_steps.md`:

- R06: aoestats I3 table and completeness_matrix missing 2 matches_raw columns
- R10: aoe2companion temporal coverage absent from profile JSON
- R11: aoe2companion near-constant stratification (50/55 flagged)
- R12: aoe2companion cross_table_notes for profiles_raw dead columns

Requires modifying both notebooks and re-executing them.

## Problem Statement

R06 is a code bug: the aoestats notebook merges two dicts with overlapping
keys (`filename`, `game_id` exist in both `matches_raw` and `players_raw`),
causing the matches_raw versions to be silently overwritten by `.update()`.
The I3 table and completeness_matrix show 30 entries instead of 32.

R10, R11, R12 are completeness gaps in the aoe2companion profile: missing
temporal coverage (Manual Section 3.2), an overly broad near-constant flag
(50/55 columns, including the target variable), and missing cross-table notes
for dead columns found in profiles_raw by 01_02_04.

## Assumptions & unknowns

- **Assumption:** The aoestats `all_profiles` dict key collision is the sole
  root cause of R06. Both tables share `filename` and `game_id` column names.
- **[Critique fix: BLOCKER -- revised data availability assumption]**
  R11 near-constant stratification CANNOT be computed entirely from existing
  column_profiles IQR and top_k data. Of the 50 near-constant columns, 20 have
  NEITHER top_k NOR IQR in column_profiles (all 18 BOOLEAN columns plus `won`
  and `filename`). However, the 01_02_04 census artifact contains `boolean_census`
  (true_count/false_count for 18 BOOLEAN columns) and `won_distribution`
  (true/false/null counts for `won`). The stratification uses a hybrid approach:
  IQR/top_k where available, census data where not, cardinality+type fallback
  for `filename`.
- **Assumption:** R10 temporal coverage requires 2 efficient SQL queries
  against aoe2companion's 277M-row `matches_raw`.
- **Unknown:** Exact monthly gap pattern in aoe2companion `started` timestamps.

## Execution Steps

### T01 -- aoestats: Fix I3 table and completeness_matrix key collision (R06)

**Objective:** Eliminate the dict key collision that causes `filename` and
`game_id` from `matches_raw` to be overwritten by `players_raw` entries.

**Instructions:**

1. In the aoestats notebook, locate where `all_profiles` is constructed
   (~lines 876-878). Replace the plain dict:
   ```python
   all_profiles = {}
   all_profiles.update(matches_column_profiles)
   all_profiles.update(players_column_profiles)
   ```
   With composite-key dict:
   ```python
   all_profiles = {}
   for col, p in matches_column_profiles.items():
       all_profiles[(p["table"], col)] = p
   for col, p in players_column_profiles.items():
       all_profiles[(p["table"], col)] = p
   ```

2. Update all downstream loops to use `(table, col)` key format:
   - `completeness_data` loop
   - `critical_findings` detection loop
   - I3 table rendering loop in MD assembly

3. Add assertions:
   ```python
   assert len(all_profiles) == len(matches_column_profiles) + len(players_column_profiles), (
       f"Composite key collision: {len(all_profiles)} != "
       f"{len(matches_column_profiles)} + {len(players_column_profiles)}"
   )
   assert len(all_profiles) == 32
   ```

**Verification:**
- MD I3 table has 32 data rows (not 30)
- JSON `completeness_matrix` has 32 entries
- Both `filename | matches_raw` and `filename | players_raw` appear in MD

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T02 -- aoe2companion: Add temporal coverage (R10)

**Objective:** Add temporal coverage to profile JSON/MD (Manual Section 3.2).

**Instructions:**

1. Add a new cell after the completeness heatmap section, titled
   "## 5b. Temporal Coverage (Section 3.2)".

2. SQL query `temporal_coverage`:
   ```sql
   SELECT
       MIN(started) AS min_started,
       MAX(started) AS max_started,
       COUNT(DISTINCT DATE_TRUNC('month', started)) AS distinct_months
   FROM matches_raw
   WHERE started IS NOT NULL
   ```

3. SQL query `temporal_gaps`:
   ```sql
   WITH monthly AS (
       SELECT DISTINCT DATE_TRUNC('month', started) AS month
       FROM matches_raw
       WHERE started IS NOT NULL
   ),
   expected AS (
       SELECT UNNEST(GENERATE_SERIES(
           (SELECT MIN(month) FROM monthly),
           (SELECT MAX(month) FROM monthly),
           INTERVAL '1 MONTH'
       )) AS month
   )
   SELECT e.month
   FROM expected e
   LEFT JOIN monthly m ON e.month = m.month
   WHERE m.month IS NULL
   ORDER BY e.month
   ```

4. Store both in `sql_queries` dict. Assemble `temporal_coverage` dict.
5. In JSON assembly, add `temporal_coverage` key.
6. In MD assembly, add "## Temporal Coverage" section.

**Verification:**
- JSON contains `temporal_coverage` with min/max dates, distinct_months, gaps
- MD contains "Temporal Coverage" section
- SQL queries in `sql_queries` dict (Invariant #6)

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T03 -- aoe2companion: Add near-constant stratification (R11)

**Objective:** Stratify the 50 near-constant columns into
"genuinely_uninformative" vs "low_cardinality_categorical" using a hybrid
approach.

> **[Critique fix: BLOCKER]** 20 of 50 near-constant columns have NEITHER
> top_k NOR IQR in column_profiles (18 BOOLEANs, `won`, `filename`). The
> hybrid approach uses: (1) IQR from column_profiles for numeric cols,
> (2) top_k from column_profiles for categorical cols, (3) boolean_census
> and won_distribution from the 01_02_04 census artifact for the 20 missing
> cols, (4) cardinality+type heuristic for `filename` only. No new SQL.

**Instructions:**

1. After the critical_findings dict is built, load boolean_census and
   won_distribution from the already-loaded census dict:
   ```python
   # Build dominant-value percentage lookup from boolean_census
   boolean_dominant_pct = {}
   for entry in census["boolean_census"]:
       col = entry["column_name"]
       non_null = entry["true_count"] + entry["false_count"]
       if non_null > 0:
           dominant = max(entry["true_count"], entry["false_count"])
           boolean_dominant_pct[col] = dominant * 100.0 / non_null

   # won from won_distribution (exclude NULLs)
   won_non_null = sum(
       e["cnt"] for e in census["won_distribution"] if e["won"] is not None
   )
   won_dominant = max(
       e["cnt"] for e in census["won_distribution"] if e["won"] is not None
   )
   boolean_dominant_pct["won"] = won_dominant * 100.0 / won_non_null
   ```

2. Hybrid stratification with 5-rule cascade:

   > **[Critique fix: WARNING I7]** 95% threshold justified:
   > ```python
   > # I7: 95% dominant-value threshold follows scikit-learn VarianceThreshold
   > # and caret nearZeroVar conventions (default frequency ratio 95/5).
   > # At 277M rows, dominant value must account for >263M rows to trigger.
   > DOMINANT_VALUE_THRESHOLD = 95.0
   > ```

   ```python
   genuinely_uninformative = []
   low_cardinality_categorical = []

   for nc in near_constant_columns:
       col = nc["column"]

       # Rule 0: TARGET is never uninformative
       if nc["i3_classification"] == "TARGET":
           low_cardinality_categorical.append(col)
           continue

       # Rule 1: IQR available and IQR == 0
       if nc.get("iqr") is not None and nc["iqr"] == 0:
           genuinely_uninformative.append(col)
           continue

       # Rule 2: top_k available -- check top-1 percentage
       col_profile = next(
           (p for p in column_profiles if p["column"] == col), None
       )
       if col_profile and "top_k" in col_profile and col_profile["top_k"]:
           top1_pct = col_profile["top_k"][0]["pct"]
           if top1_pct > DOMINANT_VALUE_THRESHOLD:
               genuinely_uninformative.append(col)
           else:
               low_cardinality_categorical.append(col)
           continue

       # Rule 3: boolean_census available
       if col in boolean_dominant_pct:
           if boolean_dominant_pct[col] > DOMINANT_VALUE_THRESHOLD:
               genuinely_uninformative.append(col)
           else:
               low_cardinality_categorical.append(col)
           continue

       # Rule 4: cardinality heuristic fallback (only filename expected here)
       if nc["i3_classification"] == "IDENTIFIER":
           low_cardinality_categorical.append(col)
       elif nc["cardinality"] == 1:
           genuinely_uninformative.append(col)
       else:
           low_cardinality_categorical.append(col)
   ```

3. Add to `critical_findings`:
   ```python
   critical_findings["near_constant_stratification"] = {
       "genuinely_uninformative": genuinely_uninformative,
       "genuinely_uninformative_count": len(genuinely_uninformative),
       "low_cardinality_categorical": low_cardinality_categorical,
       "low_cardinality_categorical_count": len(low_cardinality_categorical),
       "stratification_criteria": {
           "genuinely_uninformative": (
               "IQR=0 (numeric) OR dominant value > 95% of non-null rows "
               "(from top_k or boolean_census)"
           ),
           "low_cardinality_categorical": (
               "Flagged by uniqueness_ratio < 0.001 only due to large table "
               "size; dominant value <= 95% indicates meaningful variation"
           ),
           "threshold_justification": (
               "I7: 95% dominant-value threshold follows scikit-learn "
               "VarianceThreshold and caret nearZeroVar conventions "
               "(default frequency ratio 95/5)."
           ),
       },
       "data_sources": {
           "iqr": "column_profiles (9 numeric columns)",
           "top_k": "column_profiles (21 categorical columns)",
           "boolean_census": "01_02_04 census (18 BOOLEAN columns)",
           "won_distribution": "01_02_04 census (target column)",
           "cardinality_heuristic": "column_profiles cardinality + I3 class (filename only)",
       },
       # [Critique fix: WARNING I8]
       "cross_notebook_asymmetry_note": (
           "The aoestats notebook applies NEAR_CONSTANT_CARDINALITY_CAP=5 in "
           "near-constant detection, resulting in 3 flagged columns vs 50 here. "
           "The difference is due to the much larger row count (277M vs 30M) "
           "making the uniqueness_ratio threshold more aggressive. The "
           "stratification resolves this by separating genuinely uninformative "
           "columns from low-cardinality categoricals."
       ),
   }
   ```

4. Assert counts:
   ```python
   assert (
       len(genuinely_uninformative) + len(low_cardinality_categorical)
       == len(near_constant_columns)
   )
   ```

5. In MD assembly, add "### Near-constant Stratification" subsection with
   both lists, the I7 justification, and the I8 asymmetry note.

**Verification:**
- `genuinely_uninformative_count + low_cardinality_categorical_count == 50`
- `won` in `low_cardinality_categorical` (TARGET rule)
- `civ`, `map` in `low_cardinality_categorical`
- `speedFactor`, `population`, `treatyLength` in `genuinely_uninformative` (IQR=0)
- MD contains I7 justification comment and I8 asymmetry note
- No column left unclassified

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T04 -- aoe2companion: Add cross_table_notes (R12)

**Objective:** Document profiles_raw 7 dead columns. Static note, no SQL.

**Instructions:**

1. In JSON assembly, add `cross_table_notes` key:
   ```python
   "cross_table_notes": {
       "profiles_raw_dead_columns": [
           "sharedHistory", "twitchChannel", "youtubeChannel",
           "youtubeChannelName", "discordId", "discordName",
           "discordInvitation",
       ],
       "source": "01_02_04 univariate census",
       "note": "profiles_raw contains 7 columns that are 100% NULL. "
               "Not re-profiled in 01_03_01 (matches_raw scope only).",
   }
   ```

2. In MD assembly, add "## Cross-Table Notes" section.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### T05 -- Re-execute aoestats notebook and verify

**Objective:** Re-execute after R06 fix. Budget ~10 min (30M rows).

1. Execute the notebook.
2. Verify MD I3 table has 32 rows (not 30).
3. Verify JSON `completeness_matrix` has 32 entries.
4. Sync jupytext .py file.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_01_systematic_profiling.ipynb`
- `src/.../aoestats/reports/artifacts/.../01_03_01_systematic_profile.json`
- `src/.../aoestats/reports/artifacts/.../01_03_01_systematic_profile.md`

---

### T06 -- Re-execute aoe2companion notebook and verify

**Objective:** Re-execute after R10, R11, R12 fixes. Budget ~30 min (277M rows).

1. Execute the notebook.
2. Verify JSON contains `temporal_coverage`, `near_constant_stratification`,
   `cross_table_notes`.
3. Verify `near_constant_stratification` counts sum to 50.
4. Verify `won` is in `low_cardinality_categorical`.
5. Verify MD contains all new sections including I7 and I8 notes.
6. Sync jupytext .py file.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.ipynb`
- `src/.../aoe2companion/reports/artifacts/.../01_03_01_systematic_profile.json`
- `src/.../aoe2companion/reports/artifacts/.../01_03_01_systematic_profile.md`

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/.../01_03_01_systematic_profiling.py` | Update |
| `sandbox/aoe2/aoestats/.../01_03_01_systematic_profiling.ipynb` | Re-execute |
| `src/.../aoestats/.../01_03_01_systematic_profile.json` | Rewrite |
| `src/.../aoestats/.../01_03_01_systematic_profile.md` | Rewrite |
| `sandbox/aoe2/aoe2companion/.../01_03_01_systematic_profiling.py` | Update |
| `sandbox/aoe2/aoe2companion/.../01_03_01_systematic_profiling.ipynb` | Re-execute |
| `src/.../aoe2companion/.../01_03_01_systematic_profile.json` | Rewrite |
| `src/.../aoe2companion/.../01_03_01_systematic_profile.md` | Rewrite |

## Gate Condition

- Both notebooks execute end-to-end without errors
- aoestats: `completeness_matrix` has 32 entries, I3 table has 32 rows
- aoe2companion: `temporal_coverage` exists with valid min/max timestamps
- aoe2companion: `near_constant_stratification` counts sum to 50
- **[Critique fix: BLOCKER]** `won` in `low_cardinality_categorical`, NOT `genuinely_uninformative`
- **[Critique fix: BLOCKER]** All 50 near-constant columns classified (no unresolved)
- **[Critique fix: I7]** `threshold_justification` present in JSON
- **[Critique fix: I8]** `cross_notebook_asymmetry_note` present in JSON
- aoe2companion: `cross_table_notes` exists with 7 column names
- All existing gate assertions still pass
- No cleaning decisions made (I9)

## Critique fix summary

| Fix ID | Severity | Description |
|--------|----------|-------------|
| T03 BLOCKER | BLOCKER | Hybrid stratification using IQR + top_k + boolean_census + cardinality; TARGET rule for `won` |
| I8 asymmetry | WARNING | Added cross_notebook_asymmetry_note documenting aoestats vs aoe2companion detection difference |
| I7 threshold | WARNING | 95% justified with scikit-learn VarianceThreshold / caret nearZeroVar citation |

## Out of scope

- Research log corrections (PR 1)
- sc2egset notebook updates (PR 2)
- KDE justification (PR 1)
- PIPELINE_SECTION_STATUS updates (PR 1)
- Any data cleaning or feature engineering decisions (01_04)
- Harmonizing aoestats near-constant detection (documented via I8 note instead)
