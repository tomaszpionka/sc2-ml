# Plan: aoestats 01_02_04 Fix Pass

**Category:** A
**Step reference:** aoestats Phase 01, Pipeline Section 01_02, Step 01_02_04 — Univariate Census & Target Variable EDA (corrective pass)
**Branch:** `chore/roadmap-researchlog-step-01-02-03` (existing branch)
**Planner model:** claude-opus-4-6
**Date:** 2026-04-14
**Critique required:** yes — dispatch reviewer-adversarial before execution

---

## Scope

Fix two blockers, three warnings, and two notes found by adversarial review of step 01_02_04. The primary blocker is a SQL bug that makes every numeric column report `n_null=0.0` despite millions of NULLs visible in the same artifact's NULL census. The notebook must be corrected, artifact filenames standardized, and the research log rewritten entirely from the regenerated artifact output.

## Problem Statement

BLOCKER 1: A `WHERE {expr} IS NOT NULL` clause in the numeric stats SQL pre-filters to non-NULL rows before computing `COUNT(*) - COUNT({expr})`. This makes `n_null` always 0. The JSON artifact shows `feudal_age_uptime n_null=0.0` while the NULL census section in the same artifact shows 93,726,448 NULLs. This self-contradiction must be fixed before any numeric stats are cited.

BLOCKER 2: The now-deleted research log reported cardinalities that contradict the JSON artifact: `civ` (47 vs JSON 50), `opening` (145 vs JSON 10), `leaderboard` (7+ vs JSON 4), `map` (96 vs JSON 93). The JSON is authoritative (computed from SQL). The research log must be rewritten from the artifact.

WARNING 3: EDA Manual Section 3.1 requires "distribution shape (skewness, kurtosis)." Deferred to 01_03 — acceptable. But the IQR-based outlier counts (also required by 3.1) are trivially computable from already-computed percentiles and are added here.

WARNING 4: No systematic pre-game/post-game field annotation for matches_raw and players_raw. `new_rating` is flagged in prose; `match_rating_diff` leakage status is deferred. A structured classification of all 32 columns is required.

NOTE 5: Artifact filenames are `01_02_04_univariate_eda.json/.md` but ROADMAP specifies `01_02_04_univariate_census.json/.md`. Standardize to `_census`.

NOTE 6: `team_0_elo` and `team_1_elo` show `min_val=-1.0`. Negative Elo is unusual (likely "unranked" sentinel). Sentinel count query added.

## Assumptions and Unknowns

- DuckDB database is intact and unchanged since initial 01_02_04 run.
- Histogram SQL (Section F.4) correctly uses `WHERE IS NOT NULL` before binning — this is intentional (cannot bin NULLs). Only the aggregate stats SQL (Section F.1-F.3) has the bug.
- After fixing Section F and adding Sections F.6, F.7, K, full re-run is required.

## Literature Context

EDA Manual Section 3.1: "distribution shape (skewness, kurtosis)" and "outlier detection (IQR fences, z-scores)" are required column-level profiling metrics.

IQR outlier detection uses Tukey's standard factor of 1.5 (Tukey 1977, *Exploratory Data Analysis*, p. 44). The 1.5 value is not a magic number — it is a documented convention (Invariant #7 compliant).

Invariant #3 (temporal discipline): `new_rating` is post-match leakage. `match_rating_diff` leakage status is unknown (deferred). Field annotation captures both.

## Invariants Touched

- **I3**: Field classification — `new_rating` post_game, `match_rating_diff` deferred
- **I6**: All new SQL queries verbatim in markdown artifact
- **I7**: IQR factor 1.5 cited to Tukey 1977; uniqueness ratio denominator documented
- **I9**: No cleaning actions; read-only profiling additions

---

## T01 — Fix WHERE IS NOT NULL bug in numeric stats SQL

**Objective:** Remove the spurious `WHERE {expr} IS NOT NULL` pre-filter from the aggregate stats SQL, so that `n_null = COUNT(*) - COUNT(expr)` correctly yields the number of NULL values. DuckDB aggregate functions (AVG, MEDIAN, STDDEV, PERCENTILE_CONT, MIN, MAX) already skip NULLs natively — the WHERE clause is unnecessary for correct stats and actively breaks the NULL count.

**Instructions:**

1. In `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`, locate the numeric stats loops:
   - matches_raw loop (approx lines 444–468): `for table, expr, label in MATCHES_NUMERIC_DEFS:`
   - players_raw loop (approx lines 490–515): `for table, expr, label in PLAYERS_NUMERIC_DEFS:`
   - profile_id range query (approx lines 526–534): `PROFILE_ID_SQL`

2. For both loops, replace the SQL template. The current broken pattern has `WHERE {expr} IS NOT NULL` as the last clause. Remove it entirely:

```sql
-- BEFORE (broken):
SELECT
    COUNT({expr}) AS n_nonnull,
    COUNT(*) - COUNT({expr}) AS n_null,   -- always 0 because WHERE pre-filters
    SUM(CASE WHEN {expr} = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN({expr}) AS min_val,
    ...
FROM {table}
WHERE {expr} IS NOT NULL                  -- BUG: remove this line

-- AFTER (fixed):
SELECT
    COUNT({expr}) AS n_nonnull,
    COUNT(*) - COUNT({expr}) AS n_null,   -- now correctly counts NULLs
    SUM(CASE WHEN {expr} = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN({expr}) AS min_val,
    MAX({expr}) AS max_val,
    ROUND(AVG({expr}), 2) AS mean_val,
    ROUND(MEDIAN({expr}), 2) AS median_val,
    ROUND(STDDEV({expr}), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {expr}), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {expr}), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {expr}), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {expr}), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {expr}), 2) AS p95
FROM {table}
```

3. Fix profile_id range query similarly — remove `WHERE profile_id IS NOT NULL`.

4. Do NOT modify histogram SQL (Section F.4). The `WHERE {expr} IS NOT NULL` in histograms is intentional — NULL values cannot be binned.

**Verification:**
After re-run:
- `feudal_age_uptime.n_null` in numeric_stats_players ≈ 93,726,448 (matches NULL census)
- `match_rating_diff.n_null` ≈ 39 (matches NULL census)
- `profile_id_range.n_null` ≈ 1,185 (matches NULL census)
- For every numeric column: `n_nonnull + n_null == total_rows` (107,627,584 for players; 30,690,651 for matches)

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py` (lines ~444–534)

---

## T02 — Add IQR-based outlier counts

**Objective:** Add Tukey IQR outlier counts for all numeric columns, satisfying EDA Manual Section 3.1. Added here rather than deferred because it is trivially computable from already-computed percentiles.

**Instructions:**

1. After the boxplots section (after current line ~674), insert a new section `## F.6 IQR-based outlier counts`:

```python
# %% [markdown]
# ### F.6 IQR-based outlier counts
#
# Outlier detection per EDA Manual Section 3.1.
# IQR = p75 - p25. Lower fence = p25 - 1.5 * IQR. Upper fence = p75 + 1.5 * IQR.
# Factor 1.5 is Tukey's standard (Tukey 1977, Exploratory Data Analysis, p. 44). [I7]
```

2. Add code cell that iterates over MATCHES_NUMERIC_DEFS and PLAYERS_NUMERIC_DEFS, using the already-computed p25 and p75 values from `numeric_stats_matches` and `numeric_stats_players`:

```python
def compute_iqr_outliers(con, table, expr, label, p25, p75):
    iqr = p75 - p25
    if iqr == 0:
        return {"label": label, "outlier_low": 0, "outlier_high": 0,
                "outlier_total": 0, "outlier_pct": 0.0,
                "denominator": "pct_of_non_null_values",
                "lower_fence": p25, "upper_fence": p75,
                "note": "IQR=0; fence-based detection not meaningful"}
    lower_fence = p25 - 1.5 * iqr
    upper_fence = p75 + 1.5 * iqr
    sql = f"""
    SELECT
        COUNT(*) FILTER (WHERE {expr} < {lower_fence}) AS outlier_low,
        COUNT(*) FILTER (WHERE {expr} > {upper_fence}) AS outlier_high,
        COUNT(*) FILTER (WHERE {expr} IS NOT NULL)     AS n_nonnull
    FROM {table}
    """
    row = con.execute(sql).df().iloc[0]
    total = int(row["outlier_low"]) + int(row["outlier_high"])
    nonnull = int(row["n_nonnull"])
    return {
        "label": label,
        "outlier_low": int(row["outlier_low"]),
        "outlier_high": int(row["outlier_high"]),
        "outlier_total": total,
        "outlier_pct": round(100.0 * total / nonnull, 2) if nonnull > 0 else 0.0,
        "denominator": "pct_of_non_null_values",
        "lower_fence": round(lower_fence, 2),
        "upper_fence": round(upper_fence, 2),
    }

outlier_counts_matches = []
for table, expr, label in MATCHES_NUMERIC_DEFS:
    stats = next(s for s in numeric_stats_matches if s["label"] == label)
    result = compute_iqr_outliers(con, table, expr, label, stats["p25"], stats["p75"])
    outlier_counts_matches.append(result)
    print(f"{label}: {result['outlier_total']:,} outliers ({result['outlier_pct']}%)")

outlier_counts_players = []
for table, expr, label in PLAYERS_NUMERIC_DEFS:
    stats = next(s for s in numeric_stats_players if s["label"] == label)
    result = compute_iqr_outliers(con, table, expr, label, stats["p25"], stats["p75"])
    outlier_counts_players.append(result)
    print(f"{label}: {result['outlier_total']:,} outliers ({result['outlier_pct']}%)")

findings["outlier_counts_matches"] = outlier_counts_matches
findings["outlier_counts_players"] = outlier_counts_players
findings["outlier_counts_note"] = (
    "outlier_pct is percentage of non-NULL values, not percentage of all rows. "
    "For high-NULL columns (e.g., feudal_age_uptime at 87% NULL), these differ "
    "substantially. See 'denominator' field in each entry."
)
```

**Verification:**
- JSON artifact contains `outlier_counts_matches` and `outlier_counts_players`.
- Each entry has `outlier_low`, `outlier_high`, `outlier_total`, `outlier_pct`, `lower_fence`, `upper_fence`.
- `duration_sec` upper outlier count > 0 (max=5.57M sec vs p95=4,714 sec).

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

## T03 — Add pre-game/post-game field annotation table (Section K)

**Objective:** Create a systematic field classification for all 32 columns (18 matches_raw + 14 players_raw) by temporal availability at prediction time. Resolves WARNING 4.

**Instructions:**

1. Add a new `## Section K: Field temporal classification` section after dead-field detection (Section I) and before artifact output (Section J):

```python
# %% [markdown]
# ## Section K: Field temporal classification
#
# Classify every column by availability at prediction time.
# Categories: identifier | pre_game | in_game | post_game | target | constant | meta | deferred
# Invariant #3: any field classified as post_game or target is excluded from
# pre-game feature engineering. Fields classified as 'deferred' require
# empirical verification before use.
```

2. Define the classification:

```python
field_classification = {
    "classification_status": "preliminary",
    "formal_boundary_deferred_to": "Phase 02 (Feature Engineering)",
    "fields": [
        # matches_raw (18 columns)
        {"table": "matches_raw", "column": "game_id",         "classification": "identifier", "rationale": "Join key"},
        {"table": "matches_raw", "column": "map",             "classification": "pre_game",   "rationale": "Known at match creation"},
        {"table": "matches_raw", "column": "started_timestamp","classification": "pre_game",  "rationale": "Match start time"},
        {"table": "matches_raw", "column": "num_players",     "classification": "pre_game",   "rationale": "Lobby size known at match start"},
        {"table": "matches_raw", "column": "avg_elo",         "classification": "pre_game",   "rationale": "Computed from pre-match ratings"},
        {"table": "matches_raw", "column": "team_0_elo",      "classification": "pre_game",   "rationale": "Team 0 pre-match rating; sentinel -1.0 = unranked"},
        {"table": "matches_raw", "column": "team_1_elo",      "classification": "pre_game",   "rationale": "Team 1 pre-match rating; sentinel -1.0 = unranked"},
        {"table": "matches_raw", "column": "leaderboard",     "classification": "pre_game",   "rationale": "Ladder type selected before match"},
        {"table": "matches_raw", "column": "game_type",       "classification": "constant",   "rationale": "Cardinality=1 across entire dataset"},
        {"table": "matches_raw", "column": "game_speed",      "classification": "constant",   "rationale": "Cardinality=1 across entire dataset"},
        {"table": "matches_raw", "column": "starting_age",    "classification": "pre_game",   "rationale": "Game setting at lobby; near-constant (cardinality=2: 'dark' 30,690,632 rows vs 'standard' 19 rows)"},
        {"table": "matches_raw", "column": "mirror",          "classification": "pre_game",   "rationale": "Derivable from civ selections at match start"},
        {"table": "matches_raw", "column": "patch",           "classification": "pre_game",   "rationale": "Game version known at match time"},
        {"table": "matches_raw", "column": "raw_match_type",  "classification": "pre_game",   "rationale": "Match type determined before match"},
        {"table": "matches_raw", "column": "replay_enhanced", "classification": "meta",       "rationale": "Data quality/source flag"},
        {"table": "matches_raw", "column": "duration",        "classification": "post_game",  "rationale": "Only known after match ends"},
        {"table": "matches_raw", "column": "irl_duration",    "classification": "post_game",  "rationale": "Only known after match ends"},
        {"table": "matches_raw", "column": "filename",        "classification": "meta",       "rationale": "Provenance column (Invariant I10)"},
        # players_raw (14 columns)
        {"table": "players_raw", "column": "game_id",         "classification": "identifier", "rationale": "Join key"},
        {"table": "players_raw", "column": "profile_id",      "classification": "identifier", "rationale": "Player identifier"},
        {"table": "players_raw", "column": "winner",          "classification": "target",     "rationale": "Prediction target (Invariant #3)"},
        {"table": "players_raw", "column": "team",            "classification": "pre_game",   "rationale": "Team assignment known at match start"},
        {"table": "players_raw", "column": "civ",             "classification": "pre_game",   "rationale": "Civilization selected at match start"},
        {"table": "players_raw", "column": "old_rating",      "classification": "pre_game",   "rationale": "Player rating before match (authoritative pre-game signal)"},
        {"table": "players_raw", "column": "new_rating",      "classification": "post_game",  "rationale": "LEAKAGE — player rating after match (Invariant #3 violation if used as feature)"},
        {"table": "players_raw", "column": "match_rating_diff","classification": "deferred",  "rationale": "Leakage status unknown — could be (new_rating - old_rating) = post_game, or (player_elo - opponent_elo) = pre_game. Requires empirical test: SELECT COUNT(*) FROM players_raw WHERE ABS(match_rating_diff - (new_rating - old_rating)) < 0.01"},
        {"table": "players_raw", "column": "opening",         "classification": "in_game",    "rationale": "Opening strategy determined during gameplay"},
        {"table": "players_raw", "column": "feudal_age_uptime","classification": "in_game",   "rationale": "Time to Feudal Age, measured during gameplay; 87% NULL"},
        {"table": "players_raw", "column": "castle_age_uptime","classification": "in_game",   "rationale": "Time to Castle Age, measured during gameplay; 88% NULL"},
        {"table": "players_raw", "column": "imperial_age_uptime","classification": "in_game", "rationale": "Time to Imperial Age, measured during gameplay; 91% NULL"},
        {"table": "players_raw", "column": "replay_summary_raw","classification": "in_game",  "rationale": "Replay data; available only after match via replay parsing"},
        {"table": "players_raw", "column": "filename",        "classification": "meta",       "rationale": "Provenance column (Invariant I10)"},
    ]
}
findings["field_classification"] = field_classification
findings["field_classification_summary"] = {
    cls: sum(1 for f in field_classification["fields"] if f["classification"] == cls)
    for cls in ["pre_game", "post_game", "in_game", "identifier", "target", "constant", "meta", "deferred"]
}
findings["field_classification_note"] = {
    "match_rating_diff_leakage_test_sql": (
        "SELECT COUNT(*) FROM players_raw "
        "WHERE ABS(match_rating_diff - (new_rating - old_rating)) < 0.01"
    ),
    "note": (
        "If result > 0, match_rating_diff encodes new_rating - old_rating = post_game "
        "(fatal leakage). If result == 0, may be pre_game differential. "
        "Run this test before Phase 02 feature engineering."
    ),
}
print("Field classification:", findings["field_classification_summary"])
```

**Verification:**
- `len(field_classification["fields"]) == 32` (18 + 14)
- `new_rating` classified as `post_game`
- `match_rating_diff` classified as `deferred`
- `winner` classified as `target`
- `duration` and `irl_duration` classified as `post_game`
- age uptimes and `opening` classified as `in_game`
- `game_type` and `game_speed` classified as `constant`

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml`

---

## T04 — Add sentinel count query for team_0/1_elo

**Objective:** Quantify rows where `team_0_elo` and `team_1_elo` are negative (likely sentinel -1.0 = "unranked/unknown"). Resolves NOTE 6.

**Instructions:**

1. After the IQR outlier section (T02), insert subsection `## F.7 Sentinel value detection: team ELO fields`:

```python
sql_elo_sentinel = """
SELECT
    COUNT(*) FILTER (WHERE team_0_elo < 0)   AS team_0_elo_neg,
    COUNT(*) FILTER (WHERE team_1_elo < 0)   AS team_1_elo_neg,
    COUNT(*)                                  AS total_rows
FROM matches_raw
"""
elo_sentinel_row = con.execute(sql_elo_sentinel).df().iloc[0]

sql_elo_neg_distinct = """
SELECT DISTINCT team_0_elo AS elo_val FROM matches_raw WHERE team_0_elo < 0
UNION
SELECT DISTINCT team_1_elo AS elo_val FROM matches_raw WHERE team_1_elo < 0
ORDER BY elo_val
"""
elo_neg_distinct = con.execute(sql_elo_neg_distinct).df()

findings["elo_sentinel_counts"] = {
    "team_0_elo_negative": int(elo_sentinel_row["team_0_elo_neg"]),
    "team_1_elo_negative": int(elo_sentinel_row["team_1_elo_neg"]),
    "total_rows": int(elo_sentinel_row["total_rows"]),
    "team_0_pct": round(100.0 * int(elo_sentinel_row["team_0_elo_neg"]) / int(elo_sentinel_row["total_rows"]), 2),
    "team_1_pct": round(100.0 * int(elo_sentinel_row["team_1_elo_neg"]) / int(elo_sentinel_row["total_rows"]), 2),
}
findings["elo_negative_distinct_values"] = elo_neg_distinct["elo_val"].tolist()
print("ELO sentinel:", findings["elo_sentinel_counts"])
print("Distinct negative ELO values:", findings["elo_negative_distinct_values"])
```

**Verification:**
- JSON artifact contains `elo_sentinel_counts` with non-zero counts.
- `elo_negative_distinct_values` contains only -1.0 (or reveals other sentinel values).

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py`

---

## T05 — Fix artifact naming: _eda → _census

**Objective:** Align artifact filenames with ROADMAP convention (`01_02_04_univariate_census.json/.md`). Resolves NOTE 5.

**Instructions:**

1. In the notebook, locate the output path assignments (approx lines 905 and 950):
```python
# Change:
json_path = artifacts_dir / "01_02_04_univariate_eda.json"
# To:
json_path = artifacts_dir / "01_02_04_univariate_census.json"

# Change:
md_path = artifacts_dir / "01_02_04_univariate_eda.md"
# To:
md_path = artifacts_dir / "01_02_04_univariate_census.md"
```

2. After the full re-run produces `_census` files, delete the old `_eda` files:
   - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_eda.json`
   - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_eda.md`

3. PNG filenames (`01_02_04_*.png`) do not contain `_eda`/`_census` — no PNG renames needed.

**Verification:**
- `01_02_04_univariate_census.json` exists.
- `01_02_04_univariate_eda.json` does not exist.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py` (lines ~905, ~950)
- DELETE: `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_eda.json`
- DELETE: `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_eda.md`

---

## T06 — Re-run notebook and regenerate artifacts

**Instructions:**

1. Re-run the full notebook:
```bash
source .venv/bin/activate && poetry run jupytext --execute \
    sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py \
    --to notebook \
    --output sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.ipynb
```

2. Gate check (single-line):
```bash
source .venv/bin/activate && poetry run python -c "
import json
d = json.load(open('src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json'))
ps = [s for s in d.get('numeric_stats_players', []) if s.get('label') == 'feudal_age_uptime']
assert ps and ps[0]['n_null'] != 0.0, f'Bug not fixed: feudal_age_uptime n_null={ps[0][\"n_null\"] if ps else \"missing\"}'
assert 'outlier_counts_matches' in d
assert 'field_classification' in d
assert len(d['field_classification']['fields']) == 32
print('All gate checks passed')
"
```

3. Delete old `_eda` artifact files (see T05).

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.ipynb` (regenerated)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` (new)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` (new)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_*.png` (regenerated)

---

## Task Dependencies

```
T01 ──┐
T02 ──┤
T03 ──┼── T06
T04 ──┤
T05 ──┘
```

T01–T05 are notebook edits (sequential in file, independent in logic). T06 is the full re-run. T07 is the research log rewrite.

---

## File Manifest

| File | Action | Task(s) |
|------|--------|---------|
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py` | MODIFY | T01, T02, T03, T04, T05 |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.ipynb` | REGENERATE | T06 |
| `.../reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` | CREATE (replaces _eda) | T06 |
| `.../reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` | CREATE (replaces _eda) | T06 |
| `.../reports/artifacts/01_exploration/02_eda/01_02_04_univariate_eda.json` | DELETE | T05/T06 |
| `.../reports/artifacts/01_exploration/02_eda/01_02_04_univariate_eda.md` | DELETE | T05/T06 |
| `.../reports/artifacts/01_exploration/02_eda/01_02_04_*.png` | REGENERATE | T06 |

---

## Gate Conditions

1. `feudal_age_uptime.n_null` in `numeric_stats_players` ≠ 0.0 and equals NULL census value (~93,726,448).
2. For every numeric column: `n_nonnull + n_null == total_rows` for the respective table.
3. JSON `field_classification.fields` has exactly 32 entries; `new_rating` classified as `post_game`; `match_rating_diff` classified as `deferred`.
4. JSON `elo_sentinel_counts` present with non-trivial counts for negative ELO.
5. JSON `outlier_counts_matches` and `outlier_counts_players` present with `outlier_low`, `outlier_high`, `lower_fence`, `upper_fence`, `denominator` per column.
6. `01_02_04_univariate_census.json` exists; `01_02_04_univariate_eda.json` deleted.

## Out of Scope

- Skewness and kurtosis (deferred to Pipeline Section 01_03 — ROADMAP 01_03 steps must be defined to capture this debt)
- z-score outlier detection (deferred to 01_03)
- match_rating_diff empirical leakage test (deferred — SQL test documented in field classification rationale)
- Schema YAML description updates
- STEP_STATUS.yaml / PHASE_STATUS.yaml changes (step remains `complete`)
- Research log rewrite for 01_02_04 (deferred until notebook is fully polished)

## Deferred Debt

| Item | Deferred To | Note |
|------|-------------|------|
| Skewness and kurtosis | Pipeline Section 01_03 | Must be added to ROADMAP 01_03 step definitions |
| z-score outlier detection | Pipeline Section 01_03 | Must be added to ROADMAP 01_03 step definitions |
| `match_rating_diff` leakage verification | Next planning step | SQL test: `WHERE ABS(match_rating_diff - (new_rating - old_rating)) < 0.01` |
| ELO sentinel -1.0 cleaning strategy | Step 01_04 | Count quantified in T04; cleaning action deferred |
| `profile_id` DOUBLE precision loss check | Step 01_04 | Already tracked from 01_02_01 |
| `opening` 86% NULL — usability for feature engineering | Phase 02 Feature Engineering | Low coverage limits use |
| Duplicate row detection | Pipeline Section 01_03 | 107M rows — cheap check: `COUNT(*) - COUNT(DISTINCT game_id \|\| '_' \|\| profile_id)` |
| Completeness matrix (missingness heatmap) | Pipeline Section 01_03 | Tabular null census provides equivalent information; visual heatmap deferred |
| Memory footprint (DuckDB file size) | Informational | `os.path.getsize('data/db/db.duckdb')` |
