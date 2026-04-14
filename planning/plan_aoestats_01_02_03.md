# Category A Plan: Step 01_02_03 — Univariate Census & Target Variable EDA

## Phase/Step Reference

- **Phase:** 01 — Data Exploration
- **Pipeline Section:** 01_02 — Exploratory Data Analysis (Tukey-style)
- **Step:** 01_02_03
- **Dataset:** aoestats
- **Branch:** `feat/aoestats-01-02-03-univariate-eda`

---

## Scientific Rationale

Step 01_02_01 performed smoke tests on variant column types, profile_id precision, duration ranges, game_id uniqueness, and winner NULL rates — but these were targeted readiness checks, not a systematic column-level census. Step 01_02_02 materialises the three raw tables (`raw_matches`, `raw_players`, `raw_overviews`) but performs only spot NULL checks on a handful of columns (the notebook itself is not yet complete — status `not_started`). Neither step has produced:

1. A full NULL census covering all 18 `raw_matches` columns and all 14 `raw_players` columns (EDA Manual Section 3.1)
2. A target variable (`winner`) value distribution with TRUE/FALSE/NULL class balance (EDA Manual Section 3.2)
3. Descriptive statistics for continuous columns (EDA Manual Section 2.1 — univariate layer)
4. Categorical field cardinality and distinct-value sets (EDA Manual Section 2.1)
5. Dead/constant/near-constant field detection (EDA Manual Section 3.3)
6. Temporal range from `started_timestamp` (EDA Manual Section 3.2)

The pre-ingestion step (01_02_01) established the following facts that are inputs to this step:
- `raw_matches`: ~30.7M rows, 18 columns (17 Parquet + `filename`)
- `raw_players`: ~107.6M rows, 14 columns (13 Parquet + `filename`)
- 5 variant columns in players have high NULL rates: `feudal_age_uptime` (87.1%), `castle_age_uptime` (87.9%), `imperial_age_uptime` (91.5%), `opening` (86.0%), `profile_id` (~0%)
- `duration` and `irl_duration` are BIGINT nanoseconds (divide by 1e9 for seconds)
- `game_id` has zero NULLs in both tables; matches has duplicates (30.7M rows vs fewer distinct game_ids)
- `winner` has an established NULL rate (~4.69% based on aoe2companion finding; aoestats-specific rate to be verified)

**Crucially, aoestats has NO STRUCT columns in its main tables.** The sc2egset 01_02_03 plan was titled "Metadata STRUCT Extraction & Replay-Level EDA" because its central task was flattening opaque STRUCT blobs. For aoestats, the schema is already flat — the primary work is the univariate census itself.

The `raw_overviews` table (1 row, 9 columns) DOES contain STRUCT arrays (`civs`, `openings`, `patches`, `groupings`, `changelog`). These are reference lookup tables, not analytical data. They are relevant for mapping coded values to human-readable labels (e.g., civ names, patch numbers to dates), but unnesting them is not univariate profiling of the match/player data. STRUCT array unnesting is deferred to a dedicated step.

**This step differs from the sc2egset equivalent in these specific ways:**
1. No STRUCT extraction needed — schema is flat
2. Target variable is `winner` (BOOLEAN: TRUE/FALSE/NULL) not `result` (VARCHAR with multiple string values)
3. Two tables to census (`raw_matches` + `raw_players`) joined by `game_id`, instead of one metadata table + one players table with replay_id
4. Duration is in nanoseconds (BIGINT), not game loops — no game-speed conversion gate needed
5. `game_speed` is a categorical column to profile, not a gate condition for duration conversion
6. `raw_players` is ~107.6M rows — queries must be designed for scale (no full-table pulls to pandas)
7. The `num_players` column in `raw_matches` gates a critical thesis scope question: what fraction of data is 1v1?

**Manual sections partially covered:** 2.1, 3.1 (univariate census layer only — zero counts, skewness, kurtosis, IQR outlier detection deferred to 01_03), 3.2 (target balance and temporal range only — duplicate detection, correlation matrices, completeness matrix deferred to 01_03), 3.3.

---

## Specific Analyses

### Notebook Query Pattern

DuckDB SQL is the primary query layer — aggregations, NULL census, GROUP BY, cardinality. Pull results to pandas with `.df()` for display and light analysis helpers. Never load full raw tables into pandas. All SQL that produces a reported result must appear verbatim in the markdown artifact (Invariant #6).

### A. Full NULL census of `raw_matches`

Cover all 18 columns with both count and percentage (EDA Manual Section 3.1 requires both):

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(map) AS map_null,
    ROUND(100.0 * (COUNT(*) - COUNT(map)) / COUNT(*), 2) AS map_null_pct,
    COUNT(*) - COUNT(started_timestamp) AS started_timestamp_null,
    ROUND(100.0 * (COUNT(*) - COUNT(started_timestamp)) / COUNT(*), 2) AS started_timestamp_null_pct,
    COUNT(*) - COUNT(duration) AS duration_null,
    ROUND(100.0 * (COUNT(*) - COUNT(duration)) / COUNT(*), 2) AS duration_null_pct,
    COUNT(*) - COUNT(irl_duration) AS irl_duration_null,
    ROUND(100.0 * (COUNT(*) - COUNT(irl_duration)) / COUNT(*), 2) AS irl_duration_null_pct,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    COUNT(*) - COUNT(avg_elo) AS avg_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(avg_elo)) / COUNT(*), 2) AS avg_elo_null_pct,
    COUNT(*) - COUNT(num_players) AS num_players_null,
    COUNT(*) - COUNT(team_0_elo) AS team_0_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team_0_elo)) / COUNT(*), 2) AS team_0_elo_null_pct,
    COUNT(*) - COUNT(team_1_elo) AS team_1_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team_1_elo)) / COUNT(*), 2) AS team_1_elo_null_pct,
    COUNT(*) - COUNT(replay_enhanced) AS replay_enhanced_null,
    COUNT(*) - COUNT(leaderboard) AS leaderboard_null,
    COUNT(*) - COUNT(mirror) AS mirror_null,
    COUNT(*) - COUNT(patch) AS patch_null,
    COUNT(*) - COUNT(raw_match_type) AS raw_match_type_null,
    COUNT(*) - COUNT(game_type) AS game_type_null,
    COUNT(*) - COUNT(game_speed) AS game_speed_null,
    COUNT(*) - COUNT(starting_age) AS starting_age_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM raw_matches
```

Pull to pandas `.df()` and transpose into a tidy `(column, null_count, null_pct)` table for display.

### B. Full NULL census of `raw_players`

All 14 columns:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(winner) AS winner_null,
    ROUND(100.0 * (COUNT(*) - COUNT(winner)) / COUNT(*), 2) AS winner_null_pct,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    COUNT(*) - COUNT(team) AS team_null,
    COUNT(*) - COUNT(feudal_age_uptime) AS feudal_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(feudal_age_uptime)) / COUNT(*), 2) AS feudal_age_uptime_null_pct,
    COUNT(*) - COUNT(castle_age_uptime) AS castle_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(castle_age_uptime)) / COUNT(*), 2) AS castle_age_uptime_null_pct,
    COUNT(*) - COUNT(imperial_age_uptime) AS imperial_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(imperial_age_uptime)) / COUNT(*), 2) AS imperial_age_uptime_null_pct,
    COUNT(*) - COUNT(old_rating) AS old_rating_null,
    ROUND(100.0 * (COUNT(*) - COUNT(old_rating)) / COUNT(*), 2) AS old_rating_null_pct,
    COUNT(*) - COUNT(new_rating) AS new_rating_null,
    ROUND(100.0 * (COUNT(*) - COUNT(new_rating)) / COUNT(*), 2) AS new_rating_null_pct,
    COUNT(*) - COUNT(match_rating_diff) AS match_rating_diff_null,
    ROUND(100.0 * (COUNT(*) - COUNT(match_rating_diff)) / COUNT(*), 2) AS match_rating_diff_null_pct,
    COUNT(*) - COUNT(replay_summary_raw) AS replay_summary_raw_null,
    ROUND(100.0 * (COUNT(*) - COUNT(replay_summary_raw)) / COUNT(*), 2) AS replay_summary_raw_null_pct,
    COUNT(*) - COUNT(profile_id) AS profile_id_null,
    COUNT(*) - COUNT(civ) AS civ_null,
    ROUND(100.0 * (COUNT(*) - COUNT(civ)) / COUNT(*), 2) AS civ_null_pct,
    COUNT(*) - COUNT(opening) AS opening_null,
    ROUND(100.0 * (COUNT(*) - COUNT(opening)) / COUNT(*), 2) AS opening_null_pct,
    COUNT(*) - COUNT(filename) AS filename_null
FROM raw_players
```

### C. Target variable analysis

The prediction target is `winner` (BOOLEAN). Unlike sc2egset's `result` (VARCHAR with Win/Loss/Undecided/...), this is a three-state column: TRUE, FALSE, NULL.

```sql
SELECT
    winner,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM raw_players
GROUP BY winner
ORDER BY cnt DESC
```

This establishes class balance — critical for model evaluation design (Invariant #8). For a well-formed 1v1 dataset with a recorded winner, we expect approximately equal TRUE/FALSE counts. Deviations signal either team games (more than 2 players per match) or data quality issues.

Additional check — winner distribution restricted to 1v1 matches only:

```sql
SELECT
    p.winner,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM raw_players p
JOIN raw_matches m ON p.game_id = m.game_id
WHERE m.num_players = 2
GROUP BY p.winner
ORDER BY cnt DESC
```

### D. Player-count distribution (thesis scope gate)

The thesis focuses on 1v1 match prediction. The `num_players` column determines what fraction of the dataset falls within thesis scope.

```sql
SELECT
    num_players,
    COUNT(*) AS match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM raw_matches
GROUP BY num_players
ORDER BY num_players
```

### E. Categorical field cardinality and distinct values

For each categorical column, compute distinct values and counts. Use loop-based cells iterating over column lists to stay within 50-line cell cap.

**`raw_matches` categoricals:**
- `map`: cardinality and top-20 maps
- `leaderboard`: distinct values and counts (expected: ranked/unranked variants)
- `game_type`: distinct values and counts
- `game_speed`: distinct values and counts
- `starting_age`: distinct values and counts
- `replay_enhanced`: TRUE/FALSE distribution
- `mirror`: TRUE/FALSE distribution
- `patch`: cardinality and top-10 patches

**`raw_players` categoricals:**
- `civ`: cardinality and top-20 civilisations
- `opening`: cardinality and top-20 openings (NOTE: 86% NULL rate expected — report both NULL count and non-NULL value distribution)
- `team`: distinct values and counts (expected: team indices 0, 1, ...)
- `replay_summary_raw`: cardinality — if very high (near row count), this is likely free text and not useful as a categorical

SQL sketch for each categorical (templated, not per-column):
```sql
SELECT {col}, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM {table}
GROUP BY {col}
ORDER BY cnt DESC
LIMIT 20
```

### F. Numeric field descriptive statistics

For continuous/integer columns, compute: min, max, mean, median, stddev, percentiles (p5, p25, p50, p75, p95). Use DuckDB `PERCENTILE_CONT`. Use loop-based cells iterating over column lists.

**`raw_matches` numerics:**
- `duration / 1e9` (seconds) — nanoseconds-to-seconds conversion via `/1e9`, no game-speed gate needed
- `irl_duration / 1e9` (seconds)
- `avg_elo`: match-level average Elo
- `team_0_elo`, `team_1_elo`: per-team Elo
- `raw_match_type`: cardinality check — if low cardinality, treat as categorical instead
- `patch`: if continuous-like, include descriptive stats; if categorical-like, move to Section E

**`raw_players` numerics:**
- `old_rating`: pre-match Elo/rating
- `new_rating`: post-match Elo/rating
- `match_rating_diff`: rating change
- `feudal_age_uptime`: seconds to Feudal Age (skip if >95% NULL — check Section B)
- `castle_age_uptime`: seconds to Castle Age (skip if >95% NULL)
- `imperial_age_uptime`: seconds to Imperial Age (skip if >95% NULL)
- `profile_id`: min/max only (ID, not continuous variable) — confirm max < 2^53 (profile_id precision safety from 01_02_01)

SQL sketch (per-column, templated):
```sql
SELECT
    MIN({col}) AS min_val,
    MAX({col}) AS max_val,
    ROUND(AVG({col}), 2) AS mean_val,
    ROUND(MEDIAN({col}), 2) AS median_val,
    ROUND(STDDEV({col}), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {col}), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col}), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {col}), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col}), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {col}), 2) AS p95
FROM {table}
WHERE {col} IS NOT NULL
```

### G. Temporal range

Use DuckDB native TIMESTAMPTZ operations — unlike sc2egset's VARCHAR `timeUTC` that required string-based MIN/MAX, aoestats `started_timestamp` is already `TIMESTAMP WITH TIME ZONE`.

```sql
SELECT
    MIN(started_timestamp) AS earliest,
    MAX(started_timestamp) AS latest,
    COUNT(DISTINCT DATE_TRUNC('month', started_timestamp)) AS distinct_months,
    COUNT(DISTINCT DATE_TRUNC('week', started_timestamp)) AS distinct_weeks
FROM raw_matches
```

Establishes the time axis for temporal splitting (Phase 03) and temporal EDA (section 01_05). Cross-validate against the filename-derived date range from 01_01_01 (2022-08-28 to 2026-02-07).

### H. game_id join integrity

Verify that the matches-players join key is well-behaved:

```sql
SELECT
    'players_without_match' AS check_name,
    COUNT(DISTINCT p.game_id) AS cnt
FROM raw_players p
LEFT JOIN raw_matches m ON p.game_id = m.game_id
WHERE m.game_id IS NULL
UNION ALL
SELECT
    'matches_without_players' AS check_name,
    COUNT(DISTINCT m.game_id) AS cnt
FROM raw_matches m
LEFT JOIN raw_players p ON m.game_id = p.game_id
WHERE p.game_id IS NULL
```

Also verify players-per-match distribution:

```sql
SELECT
    player_count,
    COUNT(*) AS match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM (
    SELECT game_id, COUNT(*) AS player_count
    FROM raw_players
    GROUP BY game_id
)
GROUP BY player_count
ORDER BY player_count
```

### I. Dead/constant/near-constant field detection

For all 18 `raw_matches` columns plus all 14 `raw_players` columns, compute cardinality. Flag any column with cardinality = 1 (constant, per EDA Manual Section 3.3) or uniqueness ratio < 0.001 (near-constant, threshold from EDA Manual Section 3.3).

```sql
SELECT '{col}' AS column_name,
       COUNT(DISTINCT {col}) AS cardinality,
       COUNT(*) AS total_rows,
       ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio
FROM {table}
```

Iterate over column lists with a loop-based approach.

---

## Expected Artifacts

| Artifact | Path |
|----------|------|
| JSON report | `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_03_univariate_eda.json` |
| Markdown summary | `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_03_univariate_eda.md` |
| Notebook (py) | `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.py` |
| Notebook (ipynb) | `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.ipynb` |

The markdown artifact must contain every SQL query verbatim (Invariant #6).

---

## Tasks

### T00 — Add step to ROADMAP

**Objective:** Register 01_02_03 in ROADMAP.md before STEP_STATUS.yaml is updated.

**Instructions:**
1. Read `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` to locate the existing step schema.
2. Append a step definition block for `01_02_03` after the `01_02_02` block, using the same YAML schema.
   - `name`: "Univariate Census & Target Variable EDA"
   - `question`: "What are the NULL rates, value distributions, cardinality, and descriptive statistics across all columns in raw_matches and raw_players, what is the class balance of the target variable (winner), and what fraction of data is 1v1?"
   - `manual_reference`: `docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Sections 2.1, 3.1, 3.2, 3.3`
   - `predecessors`: `[01_02_02]`

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`

---

### T01 — Create the notebook

**Objective:** Create the jupytext-paired notebook implementing analyses A–I.

**Instructions:**
1. Create `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.py` with jupytext `percent` format header.
2. Section 1: Full NULL census of `raw_matches` — all 18 columns with count and percentage (Section A SQL). Pull to pandas `.df()`, reshape into tidy `(column, null_count, null_pct)` table.
3. Section 2: Full NULL census of `raw_players` — all 14 columns (Section B SQL). Same tidy-table treatment.
4. Section 3: Target variable analysis — `winner` value distribution (TRUE/FALSE/NULL) with counts and percentages (Section C SQL). Also run the 1v1-restricted variant.
5. Section 4: Player-count distribution — `num_players` from `raw_matches` (Section D SQL). This establishes thesis scope.
6. Section 5: Categorical field profiles — distinct value counts for all categoricals listed in Section E. **Use loop-based cells** iterating over column lists to stay within the 50-line cell cap.
7. Section 6: Numeric descriptive statistics — for all numerics listed in Section F. Skip columns with >95% NULL (check Section 2 results). **Use loop-based cells.** Duration columns: divide by 1e9 for human-readable seconds.
8. Section 7: Temporal range — use TIMESTAMPTZ MIN/MAX (Section G SQL). Cross-validate against 01_01_01 filename-derived range.
9. Section 8: game_id join integrity — orphan counts and players-per-match distribution (Section H SQL).
10. Section 9: Dead/constant/near-constant field detection (Section I SQL). Print flagged list.
11. Section 10: Write JSON and markdown artifacts. All SQL queries must appear verbatim in the markdown (Invariant #6).
12. All database access via `get_notebook_db("aoe2", "aoestats")` (read-only). Use `print()` for exploration output; `.df()` for display.
13. No `def`, `class`, or lambda in any cell (sandbox hard rule #1). No cell exceeds 50 lines (sandbox hard rule #2).

**Performance note:** `raw_players` has ~107.6M rows. All queries must use DuckDB SQL aggregations — never pull raw data to pandas.

**Verification:**
- Notebook runs to completion: `source .venv/bin/activate && poetry run jupyter execute sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.ipynb`
- Both `.py` and `.ipynb` files exist and are paired.
- JSON artifact exists and is valid JSON.
- Markdown artifact contains inline SQL for every result table.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.py`
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_03_univariate_eda.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_03_univariate_eda.md`

---

### T02 — Update status files and research log

**Objective:** Record step completion. Depends on T00 and T01.

**Instructions:**
1. Add `01_02_03` to `STEP_STATUS.yaml` with status `complete` and `completed_at` set to execution date.
2. Add a research log entry at the top of `research_log.md` (reverse chronological). Include: What, Why, How, Findings (with key numbers from the artifact), Decisions taken, Decisions deferred, Thesis mapping, Open questions.
3. Findings must reference specific numbers from the JSON artifact — no fabricated values.
4. Decisions deferred must include:
   - "Unnesting `raw_overviews` STRUCT arrays (civs, openings, patches, groupings, changelog) — defer to a dedicated reference-data step."
   - "`replay_summary_raw` content parsing — high-cardinality VARCHAR field; defer to 01_04 or a dedicated step."
   - "Whether the missing player-week (2025-11-16 to 2025-11-22) matches should be excluded — defer to 01_04."
5. Leakage note: `new_rating` is the post-match rating — must not be used as a feature for game T (Invariant #3). Document explicitly.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update (T00) |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.py` | Create (T01) |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_univariate_eda.ipynb` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_03_univariate_eda.json` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_03_univariate_eda.md` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | Update (T02) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update (T02) |

---

## Gate Condition

1. JSON artifact exists and is valid JSON.
2. Markdown artifact contains inline SQL for every reported result (Invariant #6).
3. JSON contains: NULL counts and percentages for all 18 `raw_matches` and all 14 `raw_players` columns.
4. JSON contains: `winner` distribution with TRUE, FALSE, and NULL counts.
5. JSON contains: `num_players` distribution establishing the 1v1 fraction.
6. JSON contains: descriptive statistics for at least `old_rating`, `new_rating`, `duration`, `irl_duration`, `avg_elo`.
7. JSON contains: temporal range with earliest and latest timestamps.
8. JSON contains: game_id join integrity results (orphan counts on both sides).
9. `STEP_STATUS.yaml` lists `01_02_03` as `complete`.
10. `research_log.md` entry mentions deferred `raw_overviews` unnesting and `new_rating` leakage note.
11. ROADMAP.md contains a valid `01_02_03` step block.
12. No fabricated numbers — all derive from SQL executed in the notebook.

---

## Invariants Touched

- **#3 (temporal discipline):** `old_rating` is the pre-match rating (safe for features); `new_rating` is post-match (leakage risk). Document explicitly in research log.
- **#6 (reproducibility):** All SQL in the markdown artifact.
- **#7 (no magic numbers):** Dead field threshold: cardinality = 1. Near-constant threshold: uniqueness ratio < 0.001. Both from EDA Manual Section 3.3. Duration conversion: `/ 1e9` from Arrow `duration[ns]` → BIGINT nanoseconds (documented in 01_02_01 artifact).
- **#8 (cross-game comparability):** Target variable encoding documented (BOOLEAN `winner` vs VARCHAR `result` in SC2). Class balance reported.
- **#9 (step scope):** Univariate distributions and join integrity only. No cleaning actions, no bivariate analysis.

---

## Out of Scope

- Bivariate analysis — deferred to a subsequent 01_02 step.
- Cleaning actions — flagging only, no exclusions. Cleaning is 01_04.
- Identity resolution (profile_id DOUBLE-to-BIGINT cast) — deferred to Phase 02 per Invariant #2.
- Temporal analysis (stationarity, drift, panel structure) — deferred to section 01_05.
- Unnesting `raw_overviews` STRUCT arrays — deferred to a dedicated step.
- `replay_summary_raw` content parsing — deferred.
- Full Section 3.1/3.2 profiling (skewness, kurtosis, IQR fences, duplicate detection, correlation matrices) — deferred to 01_03.
- Filtering to 1v1 only — profiled to establish scope, not applied here.
- game_id deduplication in `raw_matches` — profiled but not deduplicated.

---

## Open Questions

- What is the `winner` NULL rate in aoestats specifically? (Resolves in T01 Section 3.)
- What fraction of matches are 1v1? (Resolves in T01 Section 4.)
- Is `replay_summary_raw` categorical or free-text? (Resolves in T01 Section 5.)
- Are `raw_match_type` and `patch` continuous or categorical in practice? (Resolves in T01 Sections 5/6.)
- How many orphaned game_ids exist on each side? (Resolves in T01 Section 8.)
- Does `started_timestamp` range match the filename-derived range from 01_01_01? (Resolves in T01 Section 7.)

---

## Risks

1. **Query performance on 107.6M-row `raw_players`.** Use `PERCENTILE_CONT` (DuckDB-optimised). If slow, sample-based estimates with explicit documentation.
2. **Many-to-many join risk.** `raw_matches` has duplicate game_ids. Section H join queries must use `COUNT(DISTINCT game_id)` to avoid inflated counts.
3. **Table naming discrepancy.** Pre-ingestion artifact uses `matches_raw`/`players_raw`/`overviews_raw` but the ingestion module creates `raw_matches`/`raw_players`/`raw_overviews`. This plan uses ingestion module naming as source of truth. If 01_02_02 creates differently named tables, SQL must be updated.

---

## Prerequisite

**Step 01_02_02 (DuckDB Ingestion) must be complete** before executing this plan. STEP_STATUS currently shows 01_02_02 as `not_started`.

---

## Observations Surfaced During Planning

**Column naming in 01_02_02 notebook.** The 01_02_02 notebook's NULL-check queries reference `match_id`, `map_name`, `started`, `rating` — columns that do not exist in the actual schema. Real columns are `game_id`, `map`, `started_timestamp`, `old_rating`/`new_rating`. These errors will surface when 01_02_02 is executed and must be fixed then.

**Critique required.** For Category A, adversarial critique is required before execution. Dispatch `reviewer-adversarial` to produce `planning/current_plan.critique.md`.
