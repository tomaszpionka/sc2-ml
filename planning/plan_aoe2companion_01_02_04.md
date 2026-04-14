# Category A Plan: Step 01_02_04 — Univariate Census & Target Variable EDA (aoe2companion)

## Phase/Step Reference

- **Phase:** 01 — Data Exploration
- **Pipeline Section:** 01_02 — Exploratory Data Analysis (Tukey-style)
- **Step:** 01_02_04
- **Dataset:** aoe2companion
- **Branch:** `feat/step-01-02-04`

---

## Scientific Rationale

Step 01_02_01 characterised the raw Parquet/CSV files pre-ingestion and diagnosed
the `won` column NULL root cause (genuine NULLs, 4.69%, uniformly distributed).
Step 01_02_02 materialises four raw DuckDB tables. Step 01_02_03 established the
definitive column-name and column-type baseline for all four raw sources, producing
the `data/db/schemas/raw/*.yaml` source-of-truth files (matches_raw: 55 columns,
ratings_raw: 8, leaderboards_raw: 19, profiles_raw: 14). However, after ingestion
and schema documentation, no column-level profiling has been performed on the DuckDB
tables. The pipeline section 01_02 (Tukey-style EDA) cannot advance toward completion
without a first-pass univariate census of all available fields across all four tables.

The aoe2companion dataset differs structurally from sc2egset in critical ways:
no STRUCT columns (all flat scalars), a BOOLEAN target variable (`won`) instead
of a VARCHAR `result`, four tables instead of three, 277M rows versus ~22k,
and mixed game modes (1v1, team games, FFA) requiring leaderboard-based
filtering. These differences shape every analysis in this step.

This step answers:

1. **What is the full NULL/zero/constant census across all columns of all four
   raw tables?** (EDA Manual Section 3.1 — column-level profiling; Section 3.3
   — dead/constant/near-constant field detection)
2. **What is the target variable (`won`) distribution and class balance, both
   overall and stratified by leaderboard?** (EDA Manual Section 3.2 — target
   class balance; Invariant #8 — cross-game comparability requires knowing
   the target encoding)
3. **What are the distinct value sets and cardinality for categorical fields
   (`leaderboard`, `civ`, `map`, `gameMode`, `speed`, `victory`, `server`,
   `country`, `status`, `difficulty`, `startingAge`, `endingAge`, `gameVariant`,
   `resources`, `revealMap`, `mapSize`, `civilizationSet`, `name`, `colorHex`)?** (EDA Manual
   Section 2.1 — univariate categorical distribution)
4. **What are the descriptive statistics for numeric fields (`rating`,
   `ratingDiff`, `population`, `slot`, `color`, `team`, `speedFactor`,
   `treatyLength`) and the rating table equivalents (`rating`, `games`,
   `rating_diff`, `leaderboard_id`, `season`)?** (EDA Manual Section 2.1 — univariate numeric
   distribution)
5. **What is the temporal range and duration distribution?** (`started`,
   `finished` timestamps in `matches_raw`; `date` in `ratings_raw`)
6. **What is the match structure breakdown?** (avg rows per match by
   leaderboard — resolves the open question of whether avg_rows_per_match
   = 3.71 is driven by team games)
7. **What does the leaderboard/profiles/ratings table census look like?**
   (NULL rates and cardinality for the three auxiliary tables — these have
   not been profiled at all)

**EDA Manual sections covered:** 2.1 (univariate census layer only), 3.1
(column-level profiling — NULL counts, zero counts, cardinality), 3.2
(target balance), 3.3 (dead/constant/near-constant field detection).

**EDA Manual sections deferred:** Bivariate analysis, outlier detection
(IQR fences, z-scores), correlation matrices, completeness heatmap,
distribution shape (skewness, kurtosis).

---

## Specific Analyses

### Notebook Query Pattern

DuckDB SQL is the primary query layer — aggregations, NULL census, GROUP BY,
cardinality. Pull results to pandas with `.df()` for display and light analysis
helpers. Never load full raw tables into pandas. All SQL that produces a
reported result must appear verbatim in the markdown artifact (Invariant #6).

### A. Full NULL census of `matches_raw` (all 55 columns)

01_02_01 checked only 3 columns (matchId, profileId, won). This step covers
all 55 columns (54 source + filename), with both count and percentage.

Because 277M rows make a single-query per-column approach impractical to
display, use DuckDB's `SUMMARIZE` or a looped approach across column batches.

SQL sketch (batch approach):
```sql
-- For each column col_name:
SELECT
    '{col_name}' AS column_name,
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT("{col_name}") AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT("{col_name}")) / COUNT(*), 2) AS null_pct,
    COUNT(DISTINCT "{col_name}") AS cardinality
FROM matches_raw
```

The executor should iterate over column names obtained from
`DESCRIBE matches_raw` and collect results into a tidy
`(column_name, null_count, null_pct, cardinality)` DataFrame.

### B. Target variable analysis (`won`)

```sql
SELECT
    won,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY won
ORDER BY cnt DESC
```

Then stratified by leaderboard:
```sql
SELECT
    leaderboard,
    won,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(PARTITION BY leaderboard), 2) AS pct
FROM matches_raw
GROUP BY leaderboard, won
ORDER BY leaderboard, won
```

This resolves the open question: does filtering to a specific leaderboard
(e.g., ranked 1v1) reduce the won=NULL rate?

**Visualization:** Bar chart of `won` value counts (TRUE / FALSE / NULL) —
overall distribution. Render in notebook and save as PNG artifact.

### C. Match structure by leaderboard

Resolves the open question from 01_02_01 about avg_rows_per_match = 3.71.

```sql
SELECT
    leaderboard,
    COUNT(DISTINCT matchId) AS distinct_matches,
    COUNT(*) AS total_rows,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT matchId), 2) AS avg_rows_per_match
FROM matches_raw
GROUP BY leaderboard
ORDER BY total_rows DESC
```

If the ranked 1v1 leaderboard shows avg_rows_per_match close to 2.0, the
team-game hypothesis is confirmed. Document the leaderboard value string
for 1v1 — this is critical for Phase 02 filtering.

### D. Categorical field cardinality and distinct values

For each categorical column in `matches_raw`, compute distinct values and
top-k counts. Use loop-based cells iterating over a column list to stay
within the 50-line cell cap.

Columns to profile:
- `leaderboard`: distinct values and counts (identifies game modes)
- `civ`: distinct values and counts (civilisation pick — the AoE2 equivalent of SC2's `race`)
- `map`: cardinality and top-20 maps
- `gameMode`: distinct values and counts
- `speed`: distinct values and counts (game speed setting)
- `victory`: distinct values and counts (victory condition)
- `server`: distinct values and counts
- `country`: cardinality (high expected)
- `status`: distinct values and counts
- `difficulty`: distinct values and counts (AI difficulty — may indicate vs-AI matches to exclude)
- `startingAge`: distinct values and counts
- `endingAge`: distinct values and counts
- `gameVariant`: distinct values and counts
- `resources`: distinct values and counts
- `revealMap`: distinct values and counts
- `mapSize`: distinct values and counts
- `civilizationSet`: distinct values and counts
- `privacy`: distinct values and counts
- `scenario`: cardinality
- `modDataset`: cardinality
- `name`: cardinality count only — report `COUNT(DISTINCT name)` and NULL rate.
  Do NOT print top-k values (millions of distinct player names would be
  meaningless to display). Player name cardinality is directly relevant
  as an indicator of distinct player count in the dataset.
- `colorHex`: excluded from top-k value listing; this is a derived string
  representation of the `color` INTEGER column. Report cardinality and NULL
  rate only to confirm it mirrors `color`.

SQL sketch (per column, for columns with top-k):
```sql
SELECT
    "{col}" AS value,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY "{col}"
ORDER BY cnt DESC
LIMIT 30
```

SQL sketch (for `name` — cardinality only):
```sql
SELECT
    COUNT(DISTINCT name) AS distinct_names,
    COUNT(*) - COUNT(name) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(name)) / COUNT(*), 2) AS null_pct
FROM matches_raw
```

**Visualization:** Bar charts of top-k value frequencies for selected
categorical columns (at minimum: `leaderboard`, `civ`, `map` top-20).
Render in notebook and save as PNG artifacts.

### E. Boolean field census

The matches schema has many boolean columns: `mod`, `fullTechTree`,
`allowCheats`, `empireWarsMode`, `lockSpeed`, `lockTeams`, `hideCivs`,
`recordGame`, `regicideMode`, `sharedExploration`, `suddenDeathMode`,
`antiquityMode`, `teamPositions`, `teamTogether`, `turboMode`, `password`,
`shared`, `verified`.

For each boolean column, compute TRUE/FALSE/NULL counts:
```sql
SELECT
    '{col}' AS column_name,
    COUNT(*) FILTER (WHERE "{col}" = TRUE) AS true_count,
    COUNT(*) FILTER (WHERE "{col}" = FALSE) AS false_count,
    COUNT(*) - COUNT("{col}") AS null_count
FROM matches_raw
```

This identifies game-setting booleans that may be needed for filtering
(e.g., `mod`, `allowCheats`, `password` — matches with these may be
non-standard).

### F. Numeric field descriptive statistics

For continuous/integer columns in `matches_raw`:
- `rating`: min, max, mean, median, stddev, percentiles (p5, p25, p50, p75, p95)
- `ratingDiff`: same
- `population`: same (population limit setting)
- `slot`: cardinality and range
- `color`: cardinality and range
- `team`: distinct values
- `speedFactor`: distinct values
- `treatyLength`: distinct values and distribution
- `internalLeaderboardId`: distinct values

SQL sketch for `matches_raw` numeric columns (per column):
```sql
SELECT
    MIN("{col}") AS min_val,
    MAX("{col}") AS max_val,
    ROUND(AVG("{col}"), 2) AS mean_val,
    ROUND(MEDIAN("{col}"), 2) AS median_val,
    ROUND(STDDEV("{col}"), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY "{col}") AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY "{col}") AS p95
FROM matches_raw
WHERE "{col}" IS NOT NULL
```

For `ratings_raw`:
- `rating`: min, max, mean, median, stddev, percentiles
- `games`: same (game count per player)
- `rating_diff`: same (rating change per snapshot)
- `leaderboard_id`: cardinality, distinct values, min, max
- `season`: cardinality, distinct values, min, max

SQL sketch for `ratings_raw` numeric columns (per column):
```sql
SELECT
    MIN("{col}") AS min_val,
    MAX("{col}") AS max_val,
    ROUND(AVG("{col}"), 2) AS mean_val,
    ROUND(MEDIAN("{col}"), 2) AS median_val,
    ROUND(STDDEV("{col}"), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY "{col}") AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY "{col}") AS p95
FROM ratings_raw
WHERE "{col}" IS NOT NULL
```

For `leaderboards_raw`:
- `rank`: min, max, mean, median, stddev, p25, p75
- `rating`: min, max, mean, median, stddev, p25, p75
- `wins`: min, max, mean, median, stddev, p25, p75
- `losses`: min, max, mean, median, stddev, p25, p75
- `games`: min, max, mean, median, stddev, p25, p75
- `streak`: min, max, mean, median, stddev, p25, p75
- `drops`: min, max, mean, median, stddev, p25, p75
- `rankCountry`: min, max, mean, median, stddev, p25, p75
- `season`: cardinality, distinct values, min, max
- `rankLevel`: cardinality, distinct values, min, max

SQL sketch for `leaderboards_raw` numeric columns (per column):
```sql
SELECT
    MIN("{col}") AS min_val,
    MAX("{col}") AS max_val,
    ROUND(AVG("{col}"), 2) AS mean_val,
    ROUND(MEDIAN("{col}"), 2) AS median_val,
    ROUND(STDDEV("{col}"), 2) AS stddev_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS p75
FROM leaderboards_raw
WHERE "{col}" IS NOT NULL
```

**Visualization:** Histograms (distribution shape) and boxplots (outlier
visibility) for key numeric columns. At minimum: `rating` and `ratingDiff`
from `matches_raw`, `rating` from `ratings_raw`, `rating` from
`leaderboards_raw`. Render in notebook and save as PNG artifacts.

### G. Temporal range

```sql
SELECT
    MIN(started) AS earliest_match,
    MAX(started) AS latest_match,
    MIN(finished) AS earliest_finish,
    MAX(finished) AS latest_finish,
    COUNT(DISTINCT CAST(started AS DATE)) AS distinct_match_dates
FROM matches_raw
```

```sql
SELECT
    MIN(date) AS earliest_rating,
    MAX(date) AS latest_rating,
    COUNT(DISTINCT CAST(date AS DATE)) AS distinct_rating_dates
FROM ratings_raw
```

Match duration distribution (derived):
```sql
SELECT
    ROUND(AVG(EXTRACT(EPOCH FROM (finished - started))), 2) AS avg_duration_secs,
    ROUND(MEDIAN(EXTRACT(EPOCH FROM (finished - started))), 2) AS median_duration_secs,
    MIN(EXTRACT(EPOCH FROM (finished - started))) AS min_duration_secs,
    MAX(EXTRACT(EPOCH FROM (finished - started))) AS max_duration_secs,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p05_secs,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p95_secs
FROM matches_raw
WHERE finished > started
```

Unlike SC2's `elapsed_game_loops` which requires a game-speed conversion
factor, AoE2's `started` and `finished` are real-world timestamps — no
speed conversion is needed.

**Excluded rows count:** Report the number of matches excluded from the
duration distribution by the `WHERE finished > started` filter. This
includes matches where `finished <= started` (zero or negative duration)
and matches where either timestamp is NULL. These counts are important
for the census — they indicate data quality issues that cleaning (01_04)
must address.

```sql
SELECT
    COUNT(*) FILTER (WHERE finished IS NULL OR started IS NULL) AS null_timestamp_count,
    COUNT(*) FILTER (WHERE finished IS NOT NULL AND started IS NOT NULL AND finished <= started) AS non_positive_duration_count
FROM matches_raw
```

**Visualization:** Time-series plot of match counts over time (monthly or
weekly buckets from `started`). Render in notebook and save as PNG artifact.

### H. Auxiliary table census: leaderboards_raw, profiles_raw, ratings_raw

These three tables have not been profiled at all. For each:
- Row count (already known from ingestion, verify)
- Full NULL census (all columns)
- Cardinality of key columns

```sql
-- leaderboards_raw
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT profileId) AS distinct_profiles,
    COUNT(DISTINCT leaderboard) AS distinct_leaderboards,
    COUNT(*) - COUNT(rank) AS rank_null,
    COUNT(*) - COUNT(rating) AS rating_null,
    COUNT(*) - COUNT(steamId) AS steamId_null,
    COUNT(*) - COUNT(country) AS country_null
FROM leaderboards_raw
```

```sql
-- profiles_raw
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT profileId) AS distinct_profiles,
    COUNT(*) - COUNT(steamId) AS steamId_null,
    COUNT(*) - COUNT(name) AS name_null,
    COUNT(*) - COUNT(clan) AS clan_null,
    COUNT(*) - COUNT(country) AS country_null
FROM profiles_raw
```

```sql
-- ratings_raw
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT profile_id) AS distinct_profiles,
    COUNT(DISTINCT leaderboard_id) AS distinct_leaderboards,
    COUNT(*) - COUNT(rating) AS rating_null,
    COUNT(*) - COUNT(games) AS games_null,
    COUNT(*) - COUNT(rating_diff) AS rating_diff_null
FROM ratings_raw
```

### I. Dead/constant/near-constant field detection

For all columns across all four tables, flag:
- Cardinality = 1: constant (dead field per EDA Manual Section 3.3)
- Uniqueness ratio < 0.001: near-constant (threshold from EDA Manual Section 3.3)

Use the cardinality values computed in Section A and Section H.

**Expectation note:** The `profiles_raw` social media columns (`twitchChannel`,
`youtubeChannel`, `youtubeChannelName`, `discordId`, `discordName`,
`discordInvitation`) will very likely appear as dead or near-constant fields.
The executor should not be surprised by this outcome — these are optional
profile fields that most players do not populate. Document their NULL rates
explicitly in the findings as candidates for exclusion in cleaning (01_04).

---

## Expected Artifacts

| Artifact | Path |
|----------|------|
| JSON report | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` |
| Markdown summary | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` |
| Notebook (py) | `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py` |
| Notebook (ipynb) | `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb` |
| PNG: target distribution | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_won_distribution.png` |
| PNG: categorical bar charts | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_categorical_topk.png` |
| PNG: numeric histograms | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_numeric_histograms.png` |
| PNG: numeric boxplots | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_numeric_boxplots.png` |
| PNG: temporal match counts | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_temporal_match_counts.png` |

The markdown artifact must contain every SQL query verbatim (Invariant #6).

---

## Tasks

### T00 — Add step to ROADMAP

**Objective:** Register 01_02_04 in ROADMAP.md before STEP_STATUS.yaml is
updated. STEP_STATUS.yaml is derived from the ROADMAP — writing STEP_STATUS
without a ROADMAP entry violates the project's derivation chain.

**Instructions:**
1. Read `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
   to locate the existing step schema.
2. Append a step definition block for `01_02_04` after the `01_02_03` block,
   using the same YAML schema (step_number, name, description, phase,
   pipeline_section, predecessors, notebook_path, inputs, outputs, gate,
   thesis_mapping, research_log_entry).
   - `step_number`: `"01_02_04"`
   - `name`: "Univariate Census & Target Variable EDA"
   - `predecessors`: `[01_02_03]`

**Verification:**
- ROADMAP.md contains a valid `01_02_04` step block with all required fields.
- The `predecessors` field lists `01_02_03` (not `01_02_02`).

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`

---

### T01 — Create the notebook

**Objective:** Create the jupytext-paired notebook implementing analyses A–I,
including visualizations.

**Prerequisites:** Step 01_02_02 is complete — all four DuckDB tables
(`matches_raw`, `ratings_raw`, `leaderboards_raw`, `profiles_raw`) exist
in the persistent database. Step 01_02_03 is also complete — the
`data/db/schemas/raw/*.yaml` files exist and confirm the column counts
(matches=55, ratings=8, leaderboards=19, profiles=14).

**Instructions:**
1. Create `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`
   with jupytext `percent` format header.
2. Section 1: Full NULL census of `matches_raw` — iterate over all 55
   columns from `DESCRIBE matches_raw`, querying NULL count, NULL percentage,
   and cardinality for each. Collect into a tidy DataFrame. Print summary
   table. (See Section A above.)
3. Section 2: Target variable analysis — `won` value distribution overall
   (TRUE/FALSE/NULL with counts and percentages) and stratified by leaderboard.
   **Visualization:** Bar chart of TRUE/FALSE/NULL counts.
   (See Section B above.)
4. Section 3: Match structure by leaderboard — avg_rows_per_match by
   leaderboard value. (See Section C above.)
5. Section 4: Categorical field profiles — distinct value counts for all
   categorical columns listed in Section D, including `name` (cardinality
   only) and `colorHex` (cardinality only). Use loop-based cells iterating
   over a column list to stay within the 50-line cell cap.
   **Visualization:** Bar charts of top-k value frequencies for `leaderboard`,
   `civ`, and `map` (top-20).
6. Section 5: Boolean field census — TRUE/FALSE/NULL counts for all boolean
   columns listed in Section E. Use loop-based cells.
7. Section 6: Numeric descriptive statistics — for all numeric columns listed
   in Section F, across `matches_raw`, `ratings_raw`, and `leaderboards_raw`.
   Use DuckDB `PERCENTILE_CONT`. Use loop-based cells. Print tables via `.df()`.
   **Visualization:** Histograms and boxplots for key numeric columns (`rating`
   and `ratingDiff` from `matches_raw`, `rating` from `ratings_raw`, `rating`
   from `leaderboards_raw`).
8. Section 7: Temporal range — `started`/`finished` range from `matches_raw`,
   `date` range from `ratings_raw`, match duration distribution, and excluded
   rows count (matches with `finished <= started` or NULL timestamps). No
   game-speed conversion needed (unlike SC2 — timestamps are real-world
   clock times).
   **Visualization:** Time-series plot of match counts over time (monthly or
   weekly buckets).
   (See Section G above.)
9. Section 8: Auxiliary table census — full NULL census and key cardinality
   for `leaderboards_raw`, `profiles_raw`, and `ratings_raw`. (See Section H
   above.)
10. Section 9: Dead/constant/near-constant field detection — flag columns
    with cardinality = 1 (constant) or uniqueness ratio < 0.001 (near-constant,
    threshold from EDA Manual Section 3.3). Use data from Sections A and H.
    Note the expectation that `profiles_raw` social media columns will appear
    as dead/near-constant fields.
11. Section 10: Write JSON and markdown artifacts. All SQL queries must appear
    verbatim in the markdown (Invariant #6). Save all visualization PNGs to
    the artifacts directory.
12. All database access via `get_notebook_db("aoe2", "aoe2companion")`
    (read-only). Use `print()` for exploration output; `.df()` for display.
13. No `def`, `class`, or lambda in any cell (sandbox hard rule #1). No cell
    exceeds 50 lines (sandbox hard rule #2).
14. Use `matplotlib` for all visualizations. Use a consistent style
    (`plt.style.use("seaborn-v0_8-whitegrid")` or equivalent). Save figures
    with `plt.savefig()` to the artifacts directory before `plt.show()`.
    Close figures with `plt.close()` after saving to avoid memory leaks.

**Performance note:** `matches_raw` contains 277M rows. NULL census and
descriptive statistics queries will be slower than sc2egset's ~22k rows.
The executor should:
- Use single-pass aggregation queries where possible (avoid per-column
  sequential queries if a batch approach is feasible).
- Consider DuckDB's `SUMMARIZE matches_raw` as a starting point for the NULL
  census, then supplement with targeted queries for columns it does not cover
  well.
- Print progress logging for long-running queries.

**Verification:**
- Notebook runs to completion: `source .venv/bin/activate && poetry run jupyter execute sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb`
- Both `.py` and `.ipynb` files exist and are paired.
- JSON artifact exists and is valid JSON.
- Markdown artifact exists and contains inline SQL for every result table.
- All PNG visualization artifacts exist in the artifacts directory.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py`
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_won_distribution.png`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_categorical_topk.png`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_numeric_histograms.png`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_numeric_boxplots.png`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_temporal_match_counts.png`

---

### T02 — Update status files and research log

**Objective:** Record step completion in STEP_STATUS.yaml and research_log.md.
Depends on T00 (ROADMAP entry must exist) and T01 (artifact must exist).

**Instructions:**
1. Add `01_02_04` to `STEP_STATUS.yaml` with status `complete` and
   `completed_at` set to execution date.
2. Add a research log entry at the top of `research_log.md` (reverse
   chronological — the most recent entry is currently 01_02_03 dated
   2026-04-14) following existing entry format. The new entry is for step
   `01_02_04`. Include: What, Why, How, Findings (with key numbers from the
   artifact), Decisions taken, Decisions deferred, Thesis mapping, Open
   questions.
3. Findings section must reference specific numbers from the JSON artifact —
   no fabricated values.
4. Decisions deferred must include:
   - Leaderboard-based filtering strategy for isolating ranked 1v1 matches
     (defer to 01_04 cleaning).
   - Handling of boolean game-setting columns (mod, allowCheats, password)
     as potential non-standard-match filters (defer to 01_04 cleaning).
   - Impact assessment of won=NULL by leaderboard on thesis scope.
5. Open questions must address:
   - Which specific `leaderboard` value(s) correspond to ranked 1v1 in
     AoE2 Definitive Edition?
   - Is `difficulty` non-NULL only for vs-AI matches? If so, this is a
     cleaning filter criterion.
   - Do profiles_raw and leaderboards_raw join cleanly to matches_raw on
     profileId? (Cross-table join integrity — deferred to a subsequent step.)

**Verification:**
- `STEP_STATUS.yaml` lists `01_02_04` with status `complete`.
- `research_log.md` has a new entry at the top referencing step `01_02_04`.
- Research log entry mentions leaderboard filtering deferral.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

**Read scope (depends on T01):**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update (T00) |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py` | Create (T01) |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_won_distribution.png` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_categorical_topk.png` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_numeric_histograms.png` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_numeric_boxplots.png` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_temporal_match_counts.png` | Create (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Update (T02) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Update (T02) |

---

## Gate Condition

All of the following must be true before this step is marked complete:

1. JSON artifact `01_02_04_univariate_census.json` exists and is valid JSON.
2. Markdown artifact `01_02_04_univariate_census.md` contains inline SQL for
   every reported result (Invariant #6).
3. JSON artifact contains: NULL counts and percentages for all 55 `matches_raw`
   columns, `won` value distribution with TRUE, FALSE, and NULL counts,
   avg_rows_per_match by leaderboard, temporal range with earliest and latest
   dates, descriptive statistics for at least `rating` and `ratingDiff`.
4. JSON artifact contains NULL census for all three auxiliary tables
   (`leaderboards_raw`, `profiles_raw`, `ratings_raw`).
5. JSON artifact contains a dead/constant/near-constant field list.
6. JSON artifact contains descriptive statistics for `leaderboards_raw`
   numeric columns (`rank`, `rating`, `wins`, `losses`, `games`, `streak`,
   `drops`, `rankCountry`).
7. JSON artifact contains `ratings_raw` profiling for `leaderboard_id` and
   `season` (at minimum cardinality, min, max).
8. All PNG visualization artifacts exist: `01_02_04_won_distribution.png`,
   `01_02_04_categorical_topk.png`, `01_02_04_numeric_histograms.png`,
   `01_02_04_numeric_boxplots.png`, `01_02_04_temporal_match_counts.png`.
9. `STEP_STATUS.yaml` lists `01_02_04` as `complete`.
10. `research_log.md` has a dated entry for step `01_02_04` that mentions
    leaderboard filtering deferral.
11. ROADMAP.md contains a valid `01_02_04` step block with `predecessors: [01_02_03]`.
12. No numbers in artifacts were fabricated — all derive from SQL executed
    in the notebook.

---

## Invariants Touched

- **#3 (temporal discipline):** Not directly applicable to univariate
  profiling. The temporal range finding establishes the time axis needed for
  future temporal splits.
- **#6 (reproducibility):** All SQL in the markdown artifact. All code in the
  notebook.
- **#7 (no magic numbers):** Cardinality thresholds: 1 (dead field), 0.001
  uniqueness ratio (near-constant) — both justified by EDA Manual Section 3.3.
- **#8 (cross-game comparability):** Target variable encoding documented
  (BOOLEAN won vs VARCHAR result in SC2). Class balance reported. This
  information feeds the cross-game evaluation protocol design in Phase 03+.
- **#9 (step scope):** Conclusions limited to univariate distributions, NULL
  rates, and cardinality. No cleaning actions taken, no bivariate analysis.

---

## Out of Scope

- **Bivariate analysis** (e.g., rating vs won, civ vs win rate by leaderboard)
  — deferred to a subsequent 01_02 step or 01_03.
- **Cleaning actions** — NULL-rich or constant columns are flagged but not
  excluded. Cleaning is 01_04.
- **Leaderboard filtering** — the 1v1 leaderboard value is identified but
  no rows are excluded. Filtering is 01_04.
- **Cross-table join integrity** (matches_raw to profiles_raw/leaderboards_raw
  on profileId; matches_raw to ratings_raw on profileId/profile_id) — deferred
  to a subsequent step.
- **Identity resolution** (profileId vs profile_id naming, profileId
  canonicalisation) — deferred to Phase 02 per Invariant #2.
- **Temporal analysis** (stationarity, drift, panel structure) — deferred to
  section 01_05.
- **Full Section 3.1/3.2 profiling** (zero counts beyond what cardinality
  reveals, skewness, kurtosis, IQR outlier detection, duplicate detection,
  correlation matrices, completeness matrix) — deferred to 01_03 (Systematic
  Data Profiling).
- **Cross-game comparability sections** — not included at this stage by
  explicit decision; cross-game comparison will be addressed in a later phase.
- **Leaderboards_raw out-of-scope decisions** — descriptive statistics for
  `leaderboards_raw` numeric columns are included in the census, but
  decisions about how to use them (e.g., whether `leaderboards_raw.rating`
  and `matches_raw.rating` are on the same scale) are deferred to subsequent
  analysis steps.

---

## Open Questions

- What leaderboard value(s) correspond to ranked 1v1 in AoE2 DE? (Resolves
  in T01 Section 4 — leaderboard distinct values.)
- Is avg_rows_per_match close to 2.0 for the 1v1 leaderboard? (Resolves in
  T01 Section 3.)
- Does won=NULL rate differ meaningfully by leaderboard? (Resolves in T01
  Section 2.)
- Are there dead or near-constant fields that can be dropped pre-modelling?
  (Resolves in T01 Section 9.)
- Is `difficulty` populated only for vs-AI matches? (Resolves in T01
  Section 4.)
- What fraction of matches use non-standard settings (mod=TRUE,
  allowCheats=TRUE, password=TRUE)? (Resolves in T01 Section 5.)
- What fraction of matches have non-positive duration (`finished <= started`)
  or NULL timestamps? (Resolves in T01 Section 7.)

---

## Risks

1. **Query performance on 277M rows.** DuckDB handles columnar scans
   efficiently, but per-column iteration over 55 columns may be slow.
   Mitigation: batch queries, progress logging, consider `SUMMARIZE`
   as a fast first pass.
2. **High cardinality of `map`, `country`, `scenario` columns.** Top-k
   queries with LIMIT 30 will capture the distribution shape without
   memory issues. Full distinct value lists are deferred to the artifact
   JSON.
3. **Step 01_02_02 is complete. No blocking dependencies remain.**

---

## Prerequisite Dependency

The STEP_STATUS currently shows:
- `01_01_01` File Inventory: `complete` (2026-04-09)
- `01_01_02` Schema Discovery: `complete` (2026-04-12)
- `01_02_01` DuckDB Pre-Ingestion: `complete` (2026-04-13)
- `01_02_02` DuckDB Ingestion: `complete` (2026-04-13)
- `01_02_03` Raw Schema DESCRIBE: `complete` (2026-04-14) — produced
  `data/db/schemas/raw/*.yaml` source-of-truth files

Step 01_02_04 requires **both** of the following to be complete:
1. **01_02_02** — the persistent DuckDB must contain all four tables
   (`matches_raw`, `ratings_raw`, `leaderboards_raw`, `profiles_raw`) so
   that `get_notebook_db("aoe2", "aoe2companion")` returns a working
   connection.
2. **01_02_03** — the schema YAMLs must exist, confirming the column counts
   (matches=55, ratings=8, leaderboards=19, profiles=14) that the notebook's
   queries rely on.

Both prerequisites are satisfied.

---

**Critique gate:** For Category A, adversarial critique is required before
execution begins. Dispatch reviewer-adversarial to produce
`planning/current_plan.critique.md`.
