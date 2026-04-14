# Plan: aoe2companion 01_02_04 Fix Pass

**Category:** A
**Step reference:** aoe2companion Phase 01, Pipeline Section 01_02, Step 01_02_04 — Univariate Census & Target Variable EDA (corrective pass)
**Branch:** `chore/roadmap-researchlog-step-01-02-03` (existing branch)
**Planner model:** claude-opus-4-6
**Date:** 2026-04-14
**Critique required:** yes — dispatch reviewer-adversarial before execution

---

## Scope

Fix three blockers and two warnings found by adversarial review of step 01_02_04. The research log entry has been deleted by the user and must be rewritten. The notebook, JSON artifact, and markdown artifact require additions. No data is modified; all changes are profiling additions and artifact corrections.

## Problem Statement

BLOCKER 1: The NULL census for 8 matches_raw columns in the now-deleted research log claimed 82-83% NULL for `difficulty`, `colorHex`, `startingAge`, `endingAge`, `civilizationSet`, `password`, `scenario`, `modDataset`. Inspection of the JSON artifact shows: `password` (82.9%), `scenario` (98.27%), `modDataset` (99.72%) have genuine high NULLs per SUMMARIZE. But `difficulty`, `colorHex`, `startingAge`, `endingAge`, `civilizationSet` show 0 NULLs in SUMMARIZE. Since these are VARCHAR columns, they may contain empty strings (`''`) that SUMMARIZE does not count as NULLs. This must be investigated with exact 3-way count queries before the research log can be written.

Note: `password` is BOOLEAN (not VARCHAR) — empty-string hypothesis does not apply to it. Its 82.9% NULL rate is genuine. `profiles_raw` is excluded from zero-count analysis (T03) — its only numeric column (`profileId`) is an identifier.

BLOCKER 2: The JSON artifact contains two conflicting counts for NULL `won` values: 12,995,946 (SUMMARIZE-derived, approximate) and 12,985,561 (GROUP BY, exact). A 10,385-row discrepancy within the same artifact. The prediction target count must be exact and internally consistent.

BLOCKER 3: `ratings_raw.rating_diff` is semantically a post-game field (rating change resulting from a match), identical in meaning to `matches_raw.ratingDiff`. The latter was flagged in prose, but `ratings_raw.rating_diff` was not annotated in the artifact. Invariant #3 applies to both.

WARNING 4: EDA Manual Section 3.1 requires zero counts for numeric columns. Not computed for any table.

WARNING 5: No structured pre-game/post-game field classification for matches_raw 55 columns exists. A preliminary annotation is required; formal boundary is deferred to Phase 02.

Additionally, the intra-match won consistency check (executed in the prior run) found 6.24% both_true and 4.74% both_false for 2-player matches. These are significant data quality findings and must appear in the new research log entry.

## Assumptions and Unknowns

- DuckDB database is intact.
- Notebook can be re-run end-to-end after changes.
- Unknown: whether `difficulty`, `colorHex`, `startingAge`, `endingAge`, `civilizationSet` contain empty strings. T01 resolves this empirically.
- `password` (BOOLEAN): cannot contain empty strings — skip from T01 investigation.

## Literature Context

EDA Manual Section 3.1: "For every variable, compute: null/missing count and percentage, zero count, cardinality..." — Zero count requirement is standard data profiling methodology.

Invariant #3 (temporal discipline): `ratingDiff` and `rating_diff` encode the outcome of a match. Annotation must be explicit in both artifact and research log.

Invariant #6 (reproducibility): All new SQL queries must appear verbatim in the markdown artifact.

## Invariants Touched

- **I3**: `ratingDiff` and `ratings_raw.rating_diff` flagged as post-game (BLOCKER 3)
- **I6**: New SQL queries in markdown artifact verbatim
- **I7**: Zero-count checks are exact equality (no magic thresholds)
- **I9**: No cleaning actions in this step

---

## T01 — Investigate empty-string vs NULL for disputed VARCHAR columns

**Objective:** Determine whether `difficulty`, `colorHex`, `startingAge`, `endingAge`, `civilizationSet` contain empty strings that SUMMARIZE does not count as NULLs. Resolves BLOCKER 1.

**Instructions:**

1. In `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`, insert a new section after Section A (NULL census) and before Section B (Target variable). Title: `## A2. Empty-string investigation for VARCHAR columns`.

2. Add a cell with a loop over disputed columns plus the high-NULL VARCHAR columns:
```python
empty_string_cols = [
    "difficulty", "colorHex", "startingAge", "endingAge", "civilizationSet",
    "scenario", "modDataset"  # high-NULL VARCHARs — confirm genuine NULLs
]
empty_string_results = []
for col in empty_string_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" IS NULL)                                AS null_count,
        COUNT(*) FILTER (WHERE "{col}" = '')                                   AS empty_string_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL AND "{col}" != '')          AS non_empty_count,
        COUNT(*)                                                               AS total_rows
    FROM matches_raw
    """
    row = con.execute(sql).df().iloc[0]
    empty_string_results.append(row.to_dict())
    print(f"{col}: NULL={int(row['null_count']):,}  EMPTY={int(row['empty_string_count']):,}  NON_EMPTY={int(row['non_empty_count']):,}")

findings["empty_string_investigation"] = empty_string_results
```

3. Verify that for each column: `null_count + empty_string_count + non_empty_count == total_rows`.

4. Update the markdown artifact generation to include `## A2. Empty-string investigation` with the SQL verbatim (I6) and results.

**Verification:**
- JSON artifact contains `empty_string_investigation` with 7 entries.
- For each column, the three counts sum to 277,099,059.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

## T02 — Fix won NULL count to exact GROUP BY value

**Objective:** Replace the SUMMARIZE-derived approximate null_count for `won` in the matches_raw NULL census with the exact value from the GROUP BY distribution. Resolves BLOCKER 2.

**Instructions:**

1. After the `won_distribution` GROUP BY query runs (Section B), add a correction cell:
```python
# Patch won null_count with exact value from GROUP BY (SUMMARIZE is approximate)
null_rows = won_dist_df.loc[won_dist_df["won"].isna()]
assert len(null_rows) == 1, f"Expected exactly 1 NULL won group, got {len(null_rows)}"
won_null_exact = int(null_rows["cnt"].iloc[0])
won_idx = null_census_matches.index[null_census_matches["column_name"] == "won"]
null_census_matches.loc[won_idx, "null_count"] = won_null_exact
null_census_matches.loc[won_idx, "null_pct"] = round(
    100.0 * won_null_exact / total_rows, 2
)
print(f"Patched won null_count: {won_null_exact:,} (exact from GROUP BY)")
```

2. After the patch, re-emit the `matches_raw_null_census` findings key so the JSON contains only the corrected value.

3. Add an `exact_won_null_note` key to findings:
```python
findings["exact_won_null_note"] = {
    "column": "won",
    "summarize_derived_null_count": 12995946,
    "group_by_exact_null_count": won_null_exact,
    "discrepancy": 12995946 - won_null_exact,
    "resolution": "GROUP BY count is authoritative for the prediction target.",
    "approximation_note": (
        "SUMMARIZE approximate counts are used for all columns except 'won', "
        "where the exact GROUP BY value is authoritative for the prediction target."
    )
}
```

**Verification:**
- JSON `matches_raw_null_census` entry for `won` has `null_count` matching `won_distribution` NULL row's `cnt`.
- `exact_won_null_note.discrepancy` ≈ 10,385.
- No other column's null_count is affected.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

## T03 — Add zero-count queries for numeric columns across all tables

**Objective:** Compute zero counts for all numeric columns in matches_raw, ratings_raw, and leaderboards_raw. Resolves WARNING 4.

**Instructions:**

1. Insert a new section `## F2. Zero counts for numeric columns` after Section F (numeric stats) and before Section G (temporal range). `profiles_raw` is excluded — its only numeric column (`profileId`) is an identifier; zero counts on identifiers are semantically meaningless.

2. matches_raw numeric zero counts:
```python
matches_zero_cols = [
    "rating", "ratingDiff", "population", "slot", "color",
    "team", "speedFactor", "treatyLength", "internalLeaderboardId",
]
matches_zero_counts = []
for col in matches_zero_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" = 0)                                                  AS zero_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL)                                          AS non_null_count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE "{col}" = 0)
            / NULLIF(COUNT(*) FILTER (WHERE "{col}" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null
    FROM matches_raw
    """
    row = con.execute(sql).df().iloc[0]
    matches_zero_counts.append(row.to_dict())
    print(f"matches_raw.{col}: zero_count={int(row['zero_count']):,}")
findings["matches_raw_zero_counts"] = matches_zero_counts
```

3. ratings_raw numeric zero counts:
```python
ratings_zero_cols = ["rating", "games", "rating_diff", "leaderboard_id", "season"]
ratings_zero_counts = []
for col in ratings_zero_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" = 0)                                                  AS zero_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL)                                          AS non_null_count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE "{col}" = 0)
            / NULLIF(COUNT(*) FILTER (WHERE "{col}" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null
    FROM ratings_raw
    """
    row = con.execute(sql).df().iloc[0]
    ratings_zero_counts.append(row.to_dict())
    print(f"ratings_raw.{col}: zero_count={int(row['zero_count']):,}")
findings["ratings_raw_zero_counts"] = ratings_zero_counts
```

4. leaderboards_raw numeric zero counts:
```python
lb_zero_cols = [
    "rank", "rating", "wins", "losses", "games",
    "streak", "drops", "rankCountry", "season", "rankLevel"
]
lb_zero_counts = []
for col in lb_zero_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" = 0)                                                  AS zero_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL)                                          AS non_null_count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE "{col}" = 0)
            / NULLIF(COUNT(*) FILTER (WHERE "{col}" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null
    FROM leaderboards_raw
    """
    row = con.execute(sql).df().iloc[0]
    lb_zero_counts.append(row.to_dict())
    print(f"leaderboards_raw.{col}: zero_count={int(row['zero_count']):,}")
findings["leaderboards_raw_zero_counts"] = lb_zero_counts
```

5. Add `## F2. Zero counts` section to markdown artifact with the SQL pattern verbatim (I6).

**Verification:**
- JSON artifact contains `matches_raw_zero_counts`, `ratings_raw_zero_counts`, `leaderboards_raw_zero_counts`.
- Each entry has `zero_count`, `non_null_count`, `zero_pct_of_non_null`.
- `leaderboards_raw.rank` zero_count = 0 (min=1 from existing stats).

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

## T04 — Flag ratings_raw.rating_diff as post-game in artifact

**Objective:** Annotate both `matches_raw.ratingDiff` and `ratings_raw.rating_diff` as post-game fields in the JSON and markdown artifacts. Resolves BLOCKER 3.

**Instructions:**

1. After the ratings_raw numeric stats section (Section F.2), add an annotation cell:
```python
findings["post_game_fields"] = [
    {
        "table": "matches_raw",
        "column": "ratingDiff",
        "type": "INTEGER",
        "reason": (
            "Rating change resulting from match outcome. Using this to predict "
            "the match it encodes would be temporal leakage (Invariant #3)."
        )
    },
    {
        "table": "ratings_raw",
        "column": "rating_diff",
        "type": "BIGINT",
        "reason": (
            "Rating change resulting from match outcome. Semantically identical "
            "to matches_raw.ratingDiff. Using this to predict the match it "
            "encodes would be temporal leakage (Invariant #3)."
        )
    },
    {
        "table": "matches_raw",
        "column": "won",
        "type": "BOOLEAN",
        "reason": "Prediction target. Post-game by definition."
    },
    {
        "table": "matches_raw",
        "column": "finished",
        "type": "TIMESTAMP",
        "reason": "Match end timestamp. Known only after match completes."
    },
]
print("Post-game field annotations recorded.")
```

2. Update markdown artifact generation to include `## Post-game field annotations` section.

**Verification:**
- JSON artifact `post_game_fields` contains 4 entries.
- Both `matches_raw.ratingDiff` and `ratings_raw.rating_diff` are present.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

---

## T05 — Add preliminary pre-game/post-game field classification for matches_raw

**Objective:** Create a structured classification of all 55 matches_raw columns by temporal status. Preliminary — formal boundary deferred to Phase 02. Resolves WARNING 5.

**Instructions:**

1. Insert a new section `## Field Classification (preliminary)` after post-game annotations (T04) and before the dead-field detection section (Section I).

2. Define the classification dict with these key temporal classes:
```python
field_classification = {
    "table": "matches_raw",
    "classification_status": "preliminary",
    "formal_boundary_deferred_to": "Phase 02 (Feature Engineering)",
    "classification_notes": {
        "pre_game": "Known before match starts. Usable as prediction features without temporal leakage.",
        "post_game": "Known only after match ends. Using as feature is temporal leakage (Invariant #3).",
        "ambiguous_pre_or_post": "Temporal status unknown; requires Phase 02 investigation before use.",
        "identifier": "Player/match identity columns. Not features.",
        "target": "Prediction target. Never a feature.",
        "context": "Player-level metadata with unclear temporal availability; not match settings and not match outcomes.",
    },
    "fields": [
        # Identifiers
        {"column": "matchId",             "temporal_class": "identifier",            "notes": "Match identifier"},
        {"column": "profileId",           "temporal_class": "identifier",            "notes": "Player identifier"},
        {"column": "name",                "temporal_class": "identifier",            "notes": "Player name"},
        {"column": "filename",            "temporal_class": "identifier",            "notes": "Source file provenance (I10)"},
        # Target
        {"column": "won",                 "temporal_class": "target",               "notes": "Prediction target"},
        # Post-game
        {"column": "ratingDiff",          "temporal_class": "post_game",            "notes": "Rating change from match outcome (Invariant #3)"},
        {"column": "finished",            "temporal_class": "post_game",            "notes": "Match end timestamp"},
        # Ambiguous — needs Phase 02 investigation
        {"column": "rating",              "temporal_class": "ambiguous_pre_or_post", "notes": "Could be pre-match or post-match snapshot — identical 42.46% NULL rate suggests co-occurrence with ratingDiff (unverified; needs row-level check)"},
        # Pre-game (match settings)
        {"column": "started",             "temporal_class": "pre_game",             "notes": "Match start timestamp"},
        {"column": "leaderboard",         "temporal_class": "pre_game",             "notes": "Ranked queue / game mode"},
        {"column": "internalLeaderboardId","temporal_class": "pre_game",            "notes": "Numeric leaderboard ID"},
        {"column": "map",                 "temporal_class": "pre_game",             "notes": "Map selection"},
        {"column": "mapSize",             "temporal_class": "pre_game",             "notes": "Map size setting"},
        {"column": "civ",                 "temporal_class": "pre_game",             "notes": "Civilization selection"},
        {"column": "gameMode",            "temporal_class": "pre_game",             "notes": "Game mode"},
        {"column": "gameVariant",         "temporal_class": "pre_game",             "notes": "Game variant"},
        {"column": "speed",               "temporal_class": "pre_game",             "notes": "Game speed setting"},
        {"column": "speedFactor",         "temporal_class": "pre_game",             "notes": "Speed multiplier"},
        {"column": "population",          "temporal_class": "pre_game",             "notes": "Population cap"},
        {"column": "resources",           "temporal_class": "pre_game",             "notes": "Resource setting"},
        {"column": "startingAge",         "temporal_class": "pre_game",             "notes": "Starting age setting"},
        {"column": "endingAge",           "temporal_class": "pre_game",             "notes": "Ending age setting"},
        {"column": "victory",             "temporal_class": "pre_game",             "notes": "Victory condition"},
        {"column": "difficulty",          "temporal_class": "pre_game",             "notes": "AI difficulty setting"},
        {"column": "civilizationSet",     "temporal_class": "pre_game",             "notes": "Civ set restriction"},
        {"column": "revealMap",           "temporal_class": "pre_game",             "notes": "Map visibility setting"},
        {"column": "treatyLength",        "temporal_class": "pre_game",             "notes": "Treaty length setting"},
        {"column": "mod",                 "temporal_class": "pre_game",             "notes": "Mod enabled flag"},
        {"column": "fullTechTree",        "temporal_class": "pre_game",             "notes": "Full tech tree toggle"},
        {"column": "allowCheats",         "temporal_class": "pre_game",             "notes": "Cheats toggle"},
        {"column": "empireWarsMode",      "temporal_class": "pre_game",             "notes": "Empire Wars toggle"},
        {"column": "lockSpeed",           "temporal_class": "pre_game",             "notes": "Lock speed toggle"},
        {"column": "lockTeams",           "temporal_class": "pre_game",             "notes": "Lock teams toggle"},
        {"column": "hideCivs",            "temporal_class": "pre_game",             "notes": "Hide civs toggle"},
        {"column": "recordGame",          "temporal_class": "pre_game",             "notes": "Record game toggle"},
        {"column": "regicideMode",        "temporal_class": "pre_game",             "notes": "Regicide toggle"},
        {"column": "sharedExploration",   "temporal_class": "pre_game",             "notes": "Shared exploration toggle"},
        {"column": "suddenDeathMode",     "temporal_class": "pre_game",             "notes": "Sudden death toggle"},
        {"column": "antiquityMode",       "temporal_class": "pre_game",             "notes": "Antiquity mode toggle"},
        {"column": "teamPositions",       "temporal_class": "pre_game",             "notes": "Team positions toggle"},
        {"column": "teamTogether",        "temporal_class": "pre_game",             "notes": "Team together toggle"},
        {"column": "turboMode",           "temporal_class": "pre_game",             "notes": "Turbo mode toggle"},
        {"column": "color",               "temporal_class": "pre_game",             "notes": "Player color slot"},
        {"column": "colorHex",            "temporal_class": "pre_game",             "notes": "Player color hex code"},
        {"column": "slot",                "temporal_class": "pre_game",             "notes": "Player slot number"},
        {"column": "team",                "temporal_class": "pre_game",             "notes": "Team assignment"},
        {"column": "password",            "temporal_class": "pre_game",             "notes": "Password-protected match (BOOLEAN, 82.9% NULL)"},
        {"column": "scenario",            "temporal_class": "pre_game",             "notes": "Scenario name (98.27% NULL)"},
        {"column": "modDataset",          "temporal_class": "pre_game",             "notes": "Mod dataset name (99.72% NULL)"},
        # Context
        {"column": "server",              "temporal_class": "context",              "notes": "Server (97.99% NULL)"},
        {"column": "privacy",             "temporal_class": "context",              "notes": "Player privacy setting"},
        {"column": "status",              "temporal_class": "context",              "notes": "Player status"},
        {"column": "country",             "temporal_class": "context",              "notes": "Player country"},
        {"column": "shared",              "temporal_class": "context",              "notes": "Shared flag"},
        {"column": "verified",            "temporal_class": "context",              "notes": "Verified flag"},
    ]
}
findings["field_classification"] = field_classification
print(f"Field classification: {len(field_classification['fields'])} columns annotated")
```

3. Verify count is exactly 55 (matching matches_raw schema).

**Verification:**
- `len(findings["field_classification"]["fields"]) == 55`
- `ratingDiff` classified as `post_game`
- `won` classified as `target`
- `rating` classified as `ambiguous_pre_or_post`

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml` (verify column count)

---

## T06 — Re-run notebook and regenerate artifacts

**Instructions:**

1. Re-run notebook end-to-end:
```bash
source .venv/bin/activate && poetry run jupytext --execute \
    sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py \
    --to notebook \
    --output sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb \
    --ExecutePreprocessor.timeout=1800
```

2. Spot-check JSON artifact after re-run (single-line):
```bash
source .venv/bin/activate && poetry run python -c "import json; d=json.load(open('src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json')); checks=[('empty_string_investigation' in d), ('exact_won_null_note' in d), ('matches_raw_zero_counts' in d), ('ratings_raw_zero_counts' in d), ('leaderboards_raw_zero_counts' in d), ('post_game_fields' in d), ('field_classification' in d), (len(d['field_classification']['fields'])==55)]; print('All OK' if all(checks) else f'FAIL: {[i for i,c in enumerate(checks) if not c]}')"
```

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` (regenerated)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` (regenerated)
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb` (re-executed)

---

## File Manifest

| File | Action | Task(s) |
|------|--------|---------|
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py` | UPDATE | T01, T02, T03, T04, T05 |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb` | REGENERATE | T06 |
| `.../reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` | REGENERATE | T06 |
| `.../reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` | REGENERATE | T06 |

---

## Gate Conditions

1. JSON `empty_string_investigation` contains 7 entries (5 zero-null + 2 high-null VARCHAR columns); each triple sums to 277,099,059.
2. JSON `matches_raw_null_census` entry for `won` has `null_count` = exact GROUP BY value (≈12,985,561).
3. JSON `exact_won_null_note.discrepancy` ≈ 10,385.
4. JSON `matches_raw_zero_counts`, `ratings_raw_zero_counts`, `leaderboards_raw_zero_counts` all present with zero_count, non_null_count, zero_pct_of_non_null per column.
5. JSON `post_game_fields` contains entries for both `matches_raw.ratingDiff` and `ratings_raw.rating_diff`.
6. JSON `field_classification.fields` has exactly 55 entries.
7. Notebook re-runs end-to-end without errors.

## Out of Scope

- Skewness, kurtosis, outlier detection (deferred to 01_03)
- Duplicate detection (deferred to 01_03)
- Schema YAML description updates
- STEP_STATUS.yaml / PHASE_STATUS.yaml changes (step remains `complete`)
- Formal pre-game/post-game boundary for `matches_raw.rating` (deferred to Phase 02)
- Research log rewrite for 01_02_04 (deferred until notebook is fully polished)

## Deferred Debt

| Item | Deferred To |
|------|-------------|
| Skewness, kurtosis, IQR outlier detection, z-scores | Pipeline Section 01_03 |
| Duplicate row detection | Pipeline Section 01_03 |
| won inconsistency root cause (both_true/both_false) | Step 01_04 |
| Empty strings as NULLs — cleaning decision | Step 01_04 |
| `matches_raw.rating` temporal classification | Phase 02 Feature Engineering |
| Bivariate analysis (leaderboard × win rate, civ × win rate) | Future 01_02 or 01_03 step |
| Completeness matrix (missingness heatmap) | Pipeline Section 01_03 |
| Memory footprint (DuckDB file size) | Informational |
| String pattern/format frequency for `name`, `colorHex` | N/A — categorical VARCHARs fully enumerated by top-k |
