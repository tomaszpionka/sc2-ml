# Category A Plan: Step 01_02_04 — Metadata STRUCT Extraction & Replay-Level EDA

## Phase/Step Reference

- **Phase:** 01 — Data Exploration
- **Pipeline Section:** 01_02 — Exploratory Data Analysis (Tukey-style)
- **Step:** 01_02_04
- **Dataset:** sc2egset
- **Branch:** `feat/step-01-02-04`

---

## Scientific Rationale

Step 01_02_02 materialised three raw DuckDB tables and three event views, but the STRUCT columns in `replays_meta_raw` (`details`, `header`, `initData`, `metadata`) remain opaque blobs. The research log explicitly notes that "only 7 of 25 columns checked" for NULL rates in `replay_players_raw`, and the `SQ`, `supplyCappedPercent`, `highestLeague` columns are flagged as open questions. Step 01_02_03 captured the definitive column-name and column-type snapshot via DESCRIBE for all six `*_raw` objects and populated the `data/db/schemas/raw/*.yaml` source-of-truth files, but performed no value-level analysis. The pipeline section `01_02` (Tukey-style EDA) cannot advance toward completion without a first-pass univariate census of all available fields — this is the foundational layer of the EDA manual's three-layer approach (Section 2.1: univariate, then bivariate, then multivariate).

This step answers:

1. **What scalar fields are embedded in the metadata STRUCTs, and what are their value distributions?** (Manual Section 2.1 — univariate analysis)
2. **What is the target variable (`result`), what are its distinct values, and what is the class balance?** (Manual Section 3.2 — dataset-level profiling, target class balance)
3. **Are there NULL/zero/constant columns among the full 25-column `replay_players_raw` schema?** (Manual Section 3.1 — column-level profiling, Section 3.3 — dead/constant/near-constant field detection)
4. **What are the distinct value sets for categorical fields (`race`, `selectedRace`, `result`, `highestLeague`, `region`, `realm`)?** (Manual Section 2.1 — univariate, categorical distribution)
5. **What is the game duration distribution?** (Extracted from `header.elapsedGameLoops`; critical for cleaning thresholds in 01_04)

**Note on scope:** The NULL census and result distinct-value analysis are performed here under pipeline section 01_02, which is methodologically appropriate: NULL censusing and distinct-value enumeration are foundational univariate EDA activities (Manual Section 2.1, 3.1). These are not deferred to 01_03 — they are completed in this step.

**Manual sections partially covered:** 2.1, 3.1 (univariate census layer only — skewness, kurtosis, IQR outlier detection deferred to 01_03), 3.2 (target balance and temporal range only — duplicate detection, correlation matrices, completeness matrix deferred to 01_03), 3.3.

---

## Specific Analyses

### A. STRUCT field extraction from `replays_meta_raw`

Extract scalar fields from the four STRUCT columns into a flat view for analysis. The confirmed STRUCT types (from `data/db/schemas/raw/replays_meta_raw.yaml`, produced by step 01_02_03) are:

- `details`: `STRUCT(gameSpeed VARCHAR, isBlizzardMap BOOLEAN, timeUTC VARCHAR)`
- `header`: `STRUCT(elapsedGameLoops BIGINT, "version" VARCHAR)` — note `version` is a DuckDB reserved keyword and **must** be quoted as `header."version"` in all SQL
- `metadata`: `STRUCT(baseBuild VARCHAR, dataBuild VARCHAR, gameVersion VARCHAR, mapName VARCHAR)`
- `initData`: `STRUCT(gameDescription STRUCT(gameOptions STRUCT(...), gameSpeed VARCHAR, isBlizzardMap BOOLEAN, mapAuthorName VARCHAR, mapFileSyncChecksum BIGINT, mapSizeX BIGINT, mapSizeY BIGINT, maxPlayers BIGINT))`

Fields extracted:

- `details.gameSpeed` — expected categorical (Faster/Fast/Normal/Slow/Slower); VARCHAR
- `details.isBlizzardMap` — BOOLEAN
- `details.timeUTC` — VARCHAR timestamp
- `header.elapsedGameLoops` — game duration in game loops; BIGINT
- `header."version"` — game version string; VARCHAR; cardinality and top-k
- `metadata.baseBuild`, `metadata.dataBuild` — build identifiers; VARCHAR
- `metadata.gameVersion` — version string; VARCHAR
- `metadata.mapName` — map name; VARCHAR; cardinality, top-k, join feasibility with `map_aliases_raw`
- `initData.gameDescription.maxPlayers` — expected 2 for 1v1; BIGINT
- `initData.gameDescription.gameSpeed` — data-quality cross-check against `details.gameSpeed`; VARCHAR
- `initData.gameDescription.isBlizzardMap` — data-quality cross-check against `details.isBlizzardMap`; BOOLEAN
- `initData.gameDescription.mapSizeX`, `initData.gameDescription.mapSizeY` — map dimensions; BIGINT
- Error columns: `gameEventsErr`, `messageEventsErr`, `trackerEvtsErr` — BOOLEAN (top-level columns); count TRUE values

Note: `initData.gameDescription.gameOptions` sub-STRUCT (fields include: `advancedSharedControl`, `amm`, `battleNet`, `clientDebugFlags`, `competitive`, `cooperative`, `fog`, `heroDuplicatesAllowed`, `lockTeams`, `noVictoryOrDefeat`, `observers`, `practice`, `randomRaces`, `teamsTogether`, `userDifficulty`) is **not extracted in this step** — the fields `competitive`, `observers`, `practice`, `randomRaces` may be relevant for filtering non-competitive replays in 01_04. Document as a deferred finding in the research log entry.

Note: `initData.gameDescription.mapAuthorName` (VARCHAR) and `initData.gameDescription.mapFileSyncChecksum` (BIGINT) are also **not extracted in this step** — neither is expected to have predictive value for outcome prediction.

DuckDB SQL sketch:
```sql
SELECT
    details.gameSpeed AS game_speed,
    details.isBlizzardMap AS is_blizzard_map,
    details.timeUTC AS time_utc,
    header.elapsedGameLoops AS elapsed_game_loops,
    header."version" AS game_version_header,
    metadata.baseBuild AS base_build,
    metadata.dataBuild AS data_build,
    metadata.gameVersion AS game_version_meta,
    metadata.mapName AS map_name,
    initData.gameDescription.maxPlayers AS max_players,
    initData.gameDescription.gameSpeed AS game_speed_init,
    initData.gameDescription.isBlizzardMap AS is_blizzard_map_init,
    initData.gameDescription.mapSizeX AS map_size_x,
    initData.gameDescription.mapSizeY AS map_size_y,
    gameEventsErr,
    messageEventsErr,
    trackerEvtsErr,
    filename
FROM replays_meta_raw
```

Data-quality cross-checks between duplicate fields (e.g., `details.gameSpeed` vs `initData.gameDescription.gameSpeed`) are integrity checks, not exploratory bivariate EDA.

### B. Full NULL census of `replay_players_raw` and `replays_meta_raw.filename`

01_02_02 checked only 7 of 25 columns. This step covers all 25, including both count and percentage (EDA Manual Section 3.1 requires both). The confirmed 25-column schema (from `data/db/schemas/raw/replay_players_raw.yaml`, produced by step 01_02_03) is: `filename` (VARCHAR, NOT NULL), `toon_id` (VARCHAR, NOT NULL), `nickname` (VARCHAR), `playerID` (INTEGER), `userID` (BIGINT), `isInClan` (BOOLEAN), `clanTag` (VARCHAR), `MMR` (INTEGER), `race` (VARCHAR), `selectedRace` (VARCHAR), `handicap` (INTEGER), `region` (VARCHAR), `realm` (VARCHAR), `highestLeague` (VARCHAR), `result` (VARCHAR), `APM` (INTEGER), `SQ` (INTEGER), `supplyCappedPercent` (INTEGER), `startDir` (INTEGER), `startLocX` (INTEGER), `startLocY` (INTEGER), `color_a` (INTEGER), `color_b` (INTEGER), `color_g` (INTEGER), `color_r` (INTEGER).

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct,
    COUNT(*) - COUNT(toon_id) AS toon_id_null,
    ROUND(100.0 * (COUNT(*) - COUNT(toon_id)) / COUNT(*), 2) AS toon_id_null_pct,
    COUNT(*) - COUNT(nickname) AS nickname_null,
    ROUND(100.0 * (COUNT(*) - COUNT(nickname)) / COUNT(*), 2) AS nickname_null_pct,
    COUNT(*) - COUNT(playerID) AS playerID_null,
    COUNT(*) - COUNT(userID) AS userID_null,
    COUNT(*) - COUNT(isInClan) AS isInClan_null,
    COUNT(*) - COUNT(clanTag) AS clanTag_null,
    COUNT(*) - COUNT(MMR) AS MMR_null,
    ROUND(100.0 * (COUNT(*) - COUNT(MMR)) / COUNT(*), 2) AS MMR_null_pct,
    COUNT(*) - COUNT(race) AS race_null,
    COUNT(*) - COUNT(selectedRace) AS selectedRace_null,
    COUNT(*) - COUNT(handicap) AS handicap_null,
    COUNT(*) - COUNT(region) AS region_null,
    COUNT(*) - COUNT(realm) AS realm_null,
    COUNT(*) - COUNT(highestLeague) AS highestLeague_null,
    ROUND(100.0 * (COUNT(*) - COUNT(highestLeague)) / COUNT(*), 2) AS highestLeague_null_pct,
    COUNT(*) - COUNT(result) AS result_null,
    COUNT(*) - COUNT(APM) AS APM_null,
    COUNT(*) - COUNT(SQ) AS SQ_null,
    ROUND(100.0 * (COUNT(*) - COUNT(SQ)) / COUNT(*), 2) AS SQ_null_pct,
    COUNT(*) - COUNT(supplyCappedPercent) AS supplyCappedPercent_null,
    ROUND(100.0 * (COUNT(*) - COUNT(supplyCappedPercent)) / COUNT(*), 2) AS supplyCappedPercent_null_pct,
    COUNT(*) - COUNT(startDir) AS startDir_null,
    COUNT(*) - COUNT(startLocX) AS startLocX_null,
    COUNT(*) - COUNT(startLocY) AS startLocY_null,
    COUNT(*) - COUNT(color_a) AS color_a_null,
    COUNT(*) - COUNT(color_b) AS color_b_null,
    COUNT(*) - COUNT(color_g) AS color_g_null,
    COUNT(*) - COUNT(color_r) AS color_r_null
FROM replay_players_raw
```

Pull result to pandas `.df()` and transpose for readability. The executor may reshape this into a tidy `(column, null_count, null_pct)` table via pandas for display.

Additionally, check `replays_meta_raw.filename` for NULLs:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct
FROM replays_meta_raw
```

Note: The DESCRIBE output from step 01_02_03 marks `replays_meta_raw.filename` as `nullable=YES` (a DuckDB metadata property); per 01_02_02 findings, zero NULLs exist empirically — this census step confirms the empirical count. The `replay_players_raw.filename` column is marked `nullable=NO` by DESCRIBE.

### C. Target variable analysis

11 non-2-player replays are known from 01_02_02 findings (3 with 1 player, 2 with 4 players, etc.). These may contribute rows with unusual result values (e.g., team game outcomes). These are known anomalies, not new discoveries — report their result values separately.

```sql
SELECT result, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY result
ORDER BY cnt DESC
```

Check for values beyond Win/Loss (e.g., Undecided, Disconnected, Tie). Assess class balance — critical for model evaluation design (Invariant #8).

To isolate the non-2-player replay results:
```sql
SELECT rp.result, COUNT(*) AS cnt
FROM replay_players_raw rp
JOIN replays_meta_raw rm ON rp.filename = rm.filename
WHERE rm.initData.gameDescription.maxPlayers != 2
   OR rm.filename IN (
       SELECT filename FROM replay_players_raw
       GROUP BY filename HAVING COUNT(*) != 2
   )
GROUP BY rp.result
ORDER BY cnt DESC
```

### D. Categorical field cardinality and distinct values

**Important:** This section must run before Section E. The `game_speed` census here gates the duration conversion in Section E.

For each categorical column in `replay_players_raw` — use loop-based cells iterating over a column list to stay within the 50-line cell cap:
- `race`: distinct values and counts (Protoss/Terran/Zerg/Random expected)
- `selectedRace`: distinct values and counts
- `highestLeague`: distinct values and counts (Bronze through Grandmaster)
- `region`: distinct values and counts
- `realm`: distinct values and counts

For `replays_meta_raw` extracted fields (from the Section A flat table):
- `game_speed`: distinct values and counts — **assert all values are 'Faster' before proceeding to Section E**
- `game_speed_init`: cross-check against `game_speed`
- `map_name`: cardinality and top-20 maps
- `game_version_meta`: cardinality, min/max
- `base_build` / `data_build`: cardinality

Game speed assertion cell (must pass before Section E):
```python
speed_counts = con.execute(
    "SELECT game_speed, COUNT(*) AS cnt FROM struct_flat GROUP BY game_speed ORDER BY cnt DESC"
).df()
print(speed_counts)
assert set(speed_counts["game_speed"].dropna()) == {"Faster"}, (
    f"Expected only 'Faster' game speed; found: {speed_counts['game_speed'].unique()}"
)
print("All replays confirmed Faster speed — duration conversion is safe.")
```

**Visualizations:** Bar charts of value counts for `race`, `selectedRace`, `result`, `highestLeague`, `region`. Save as PNG artifacts.

### E. Numeric field descriptive statistics

**Prerequisite:** Section D game speed assertion must have passed.

The game-loop-to-seconds conversion uses `/ 22.4`. This constant is 22.4 game loops/second (standard Faster speed: 16 base loops/second × 1.4 Faster multiplier). The assertion in Section D guarantees this constant applies to all replays in the dataset.

**In-game field distinction:** APM, SQ, and supplyCappedPercent are in-game-only fields (computed from replay actions, available only post-game). Their presence in the EDA does not imply pre-game availability. This distinction will be formally enforced at the feature engineering stage (Phase 03). Pre-game fields profiled here include MMR, race, selectedRace, highestLeague, region, and realm. The separation between pre-game and in-game fields is critical for the thesis methodology and will be documented in the research log.

Use loop-based cells iterating over column lists for Sections D and E — required to stay within the 50-line cell cap given the number of columns.

For continuous/integer columns in `replay_players_raw`:
- `MMR`: min, max, mean, median, stddev, percentiles (p5, p25, p50, p75, p95)
- `APM`: same
- `SQ`: same
- `supplyCappedPercent`: same
- `handicap`: same; check if constant (100 expected for competitive play)
- `startDir`, `startLocX`, `startLocY`: cardinality and ranges

For `replays_meta_raw` extracted fields:
- `elapsed_game_loops`: min, max, mean, median, stddev, percentiles; convert to seconds: `elapsed_game_loops / 22.4`; also convert to minutes for the duration histogram
- `map_size_x`, `map_size_y`: distinct values

SQL sketch (per column, for `replay_players_raw`):
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
FROM replay_players_raw
WHERE "{col}" IS NOT NULL
```

**Visualizations:** Histograms and boxplots for `MMR`, `APM`, `SQ`, `supplyCappedPercent`. Duration histogram in minutes (`elapsed_game_loops / 22.4 / 60`). Save as PNG artifacts.

### F. Temporal range

Use string-based MIN/MAX — ISO 8601 strings sort lexicographically, so no timestamp parsing is needed. Do not use `STRPTIME` here; the format `2016-07-29T04:50:12.5655603Z` contains 7-digit fractional seconds (.NET precision) that `%f` (6-digit) cannot handle. Full timestamp parsing is deferred to 01_05 (Temporal & Panel EDA) where date arithmetic is actually needed.

```sql
SELECT
    MIN(details.timeUTC) AS earliest,
    MAX(details.timeUTC) AS latest,
    COUNT(DISTINCT SUBSTR(details.timeUTC, 1, 7)) AS distinct_months
FROM replays_meta_raw
```

Establishes the time axis for temporal splitting (Phase 03) and temporal EDA (section 01_05).

**Visualization:** Time-series plot of replay counts over time (by month, using `SUBSTR(details.timeUTC, 1, 7)`). Save as PNG artifact.

### G. Error column census

```sql
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE gameEventsErr = TRUE) AS game_err,
    COUNT(*) FILTER (WHERE messageEventsErr = TRUE) AS msg_err,
    COUNT(*) FILTER (WHERE trackerEvtsErr = TRUE) AS tracker_err
FROM replays_meta_raw
```

If any are non-zero, the corresponding replays may need flagging in 01_04 (cleaning).

### H. Dead/constant/near-constant field detection

For all 25 `replay_players_raw` columns plus all extracted STRUCT fields, compute cardinality and the uniqueness ratio defined as `COUNT(DISTINCT col) / COUNT(*)`. Always report the raw ratio. Flag any column with cardinality = 1 (constant, per EDA Manual Section 3.3) or uniqueness ratio < 0.001 (near-constant, threshold from EDA Manual Section 3.3).

```sql
SELECT '{col}' AS column_name,
       COUNT(DISTINCT {col}) AS cardinality,
       COUNT(*) AS total_rows,
       ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio
FROM {table}
```

---

## Expected Artifacts

| Artifact | Path |
|----------|------|
| JSON report | `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_struct_eda.json` |
| Markdown summary | `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_struct_eda.md` |
| Notebook (py) | `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.py` |
| Notebook (ipynb) | `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.ipynb` |
| Plot PNGs | `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_04_*.png` |

The markdown artifact must contain every SQL query verbatim (Invariant #6).

PNG artifacts (minimum required):
- `01_02_04_mmr_histogram.png`
- `01_02_04_result_bar.png`
- `01_02_04_duration_histogram.png`
- `01_02_04_replays_over_time.png`
- `01_02_04_race_bar.png`
- Additional per-column histograms and boxplots

---

## Tasks

### T00 — Add step to ROADMAP

**Objective:** Register 01_02_04 in ROADMAP.md before STEP_STATUS.yaml is updated. STEP_STATUS.yaml is derived from the ROADMAP — writing STEP_STATUS without a ROADMAP entry violates the project's derivation chain.

**Instructions:**
1. Read `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` to locate the existing step schema.
2. Append a step definition block for `01_02_04` after the `01_02_03` block, using the same YAML schema.
   - `name`: "Metadata STRUCT Extraction & Replay-Level EDA"
   - `predecessors`: `[01_02_03]`

**Verification:**
- ROADMAP.md contains a valid `01_02_04` step block with all required fields.
- The `predecessors` field lists `01_02_03`.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`

---

### T01 — Create the notebook

**Objective:** Create the jupytext-paired notebook implementing analyses A–H plus visualizations.

**Instructions:**
1. Create `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.py` with jupytext `percent` format header.
2. Section 1: STRUCT field extraction — flatten all four metadata STRUCTs into scalar columns via DuckDB SQL. Store result as `struct_flat` DataFrame. Print shape and first 5 rows.
3. Section 2: Full NULL census — query all 25 columns of `replay_players_raw` with both count and percentage (Section B SQL). Also query NULL counts for `replays_meta_raw.filename`. Pull to pandas `.df()`, reshape into tidy `(column, null_count, null_pct)` table for display.
4. Section 3: Target variable analysis — `result` value distribution with counts and percentages. Print table. Separately query and report result values for rows associated with the 11 known non-2-player replays (Section C second SQL).
5. Section 4: Categorical field profiles — distinct value counts for `race`, `selectedRace`, `highestLeague`, `region`, `realm`, `game_speed`, `game_speed_init`, `map_name`, `game_version_meta`, `base_build`, `data_build`. **Use loop-based cells.** End with the `game_speed` assertion cell — execution must stop here if assertion fails. **Visualizations:** Bar charts for `race`, `selectedRace`, `result`, `highestLeague`, `region`. Save as PNG.
6. Section 5: Numeric descriptive statistics — **only runs after Section 4 assertion passes.** `MMR`, `APM`, `SQ`, `supplyCappedPercent`, `handicap`, `elapsed_game_loops / 22.4` (seconds; comment: "22.4 game loops/second (standard Faster speed: 16 base loops/second × 1.4 Faster multiplier)"), `map_size_x`, `map_size_y`. Use DuckDB `PERCENTILE_CONT`. **Use loop-based cells.** Print tables via `.df()`. **Visualizations:** Histograms and boxplots for `MMR`, `APM`, `SQ`, `supplyCappedPercent`. Duration histogram in minutes (`elapsed_game_loops / 22.4 / 60`). Save as PNG.
7. Section 6: Temporal range — use `MIN`/`MAX` on VARCHAR (no STRPTIME). Print results. **Visualization:** Time-series plot of replay counts by month. Save as PNG.
8. Section 7: Error column census — count TRUE values. Print results.
9. Section 8: Dead/constant/near-constant field detection — cardinality and uniqueness ratio (`COUNT(DISTINCT col) / COUNT(*)`) for all columns; always report the raw ratio; flag cardinality = 1 or uniqueness ratio < 0.001. Print flagged list and full ratio table.
10. Section 9: Write JSON and markdown artifacts. All SQL queries must appear verbatim in the markdown (Invariant #6). JSON artifact must include a list of generated plot filenames.
11. All database access via `get_notebook_db("sc2", "sc2egset")` (read-only). Use `print()` for exploration output; `.df()` for display.
12. No `def`, `class`, or lambda in any cell (sandbox hard rule #1). No cell exceeds 50 lines (sandbox hard rule #2).
13. Use `matplotlib` for all visualizations. Use a consistent style. Save figures with `plt.savefig()` before `plt.show()`. Close with `plt.close()`.

**Verification:**
- Notebook runs to completion: `source .venv/bin/activate && poetry run jupyter execute sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.ipynb`
- Both `.py` and `.ipynb` files exist and are paired.
- JSON artifact exists and is valid JSON.
- Markdown artifact exists and contains inline SQL for every result table.
- PNG plot files exist in the plots artifact directory.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.py`
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.ipynb`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_struct_eda.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_struct_eda.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_04_*.png`

---

### T02 — Update status files and research log

**Objective:** Record step completion in `STEP_STATUS.yaml` and `research_log.md`. Depends on T00 and T01.

**Instructions:**
1. Verify that `01_02_03` is listed in `STEP_STATUS.yaml` as `complete` (it should already be present — completed 2026-04-14). Then append `01_02_04` with status `complete` and `completed_at` set to execution date.
2. Add a research log entry for step `01_02_04` at the top of `research_log.md` (reverse chronological) following existing entry format. Include: What, Why, How, Findings (with key numbers from the artifact), Decisions taken, Decisions deferred, Thesis mapping, Open questions.
3. Findings section must reference specific numbers from the JSON artifact — no fabricated values.
4. Findings section must include: "APM, SQ, and supplyCappedPercent are in-game-only fields (computed from replay actions, available only post-game). Their presence in the EDA does not imply pre-game availability. This distinction will be formally enforced at the feature engineering stage (Phase 03)."
5. Findings section must include: "The NULL census and result distinct-value analysis were performed in this step (01_02_04) as foundational univariate EDA activities under pipeline section 01_02."
6. Decisions deferred must include: "`initData.gameDescription.gameOptions` sub-fields (`competitive`, `observers`, `practice`, `randomRaces`, and 11 additional fields including `advancedSharedControl`, `amm`, `battleNet`, `clientDebugFlags`, `cooperative`, `fog`, `heroDuplicatesAllowed`, `lockTeams`, `noVictoryOrDefeat`, `teamsTogether`, `userDifficulty`) were not extracted — defer to 01_04 cleaning step as potential filters for non-competitive replays."

**Verification:**
- `STEP_STATUS.yaml` lists `01_02_04` with status `complete`.
- `01_02_03` is confirmed present in `STEP_STATUS.yaml` as `complete`.
- `research_log.md` has a new entry at the top referencing step `01_02_04`.
- Research log entry mentions `gameOptions` deferral.
- Research log entry includes the in-game field distinction note.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`

**Read scope (depends on T01):**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_struct_eda.json`

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update (T00) |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.py` | Create (T01) |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_struct_eda.ipynb` | Create (T01) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_struct_eda.json` | Create (T01) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_struct_eda.md` | Create (T01) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_04_*.png` | Create (T01) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update (T02) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update (T02) |

---

## Gate Condition

All of the following must be true before this step is marked complete:

1. JSON artifact `01_02_04_struct_eda.json` exists and is valid JSON.
2. Markdown artifact `01_02_04_struct_eda.md` contains at least 8 SQL blocks corresponding to Sections A–H (Invariant #6).
3. JSON artifact contains: NULL counts and percentages for all 25 `replay_players_raw` columns, `result` value distribution with at least Win and Loss counts, temporal range with earliest and latest dates, error column counts, descriptive statistics for at least `MMR`, `APM`, `elapsed_game_loops`.
4. At least 3 extracted STRUCT fields have non-NULL rate > 0% in the JSON artifact (guards against wrong STRUCT paths silently producing all-NULL results). Note: this check catches total extraction failure; it is a minimum bar against silent STRUCT path errors, not a data quality guarantee.
5. `STEP_STATUS.yaml` lists `01_02_04` as `complete`.
6. `research_log.md` has a dated entry for step `01_02_04` that mentions `gameOptions` deferral.
7. ROADMAP.md contains a valid `01_02_04` step block with `predecessors: [01_02_03]`.
8. No numbers in artifacts were fabricated — all derive from SQL executed in the notebook.
9. PNG plot files exist in `reports/artifacts/01_exploration/02_eda/plots/` for at least: MMR histogram, result bar chart, and duration histogram.

---

## Invariants Touched

- **#3 (temporal discipline):** Not directly applicable to univariate profiling. The temporal range finding establishes the time axis needed for future temporal splits.
- **#6 (reproducibility):** All SQL in the markdown artifact. All code in the notebook.
- **#7 (no magic numbers):** Cardinality thresholds: 1 (dead field), 0.001 uniqueness ratio (near-constant) — both justified by EDA Manual Section 3.3. Duration conversion: 22.4 game loops/second (standard Faster speed: 16 base loops/second × 1.4 Faster multiplier).
- **#9 (step scope):** Conclusions limited to univariate distributions and NULL rates. No cleaning actions taken.

---

## Out of Scope

- **Bivariate analysis** (e.g., MMR vs result, race vs win rate) — deferred to a subsequent 01_02 step.
- **Data-quality cross-checks** between duplicate fields (e.g., `details.gameSpeed` vs `initData.gameDescription.gameSpeed`) are integrity checks only, not exploratory bivariate EDA.
- **Cleaning actions** — NULL-rich or constant columns are flagged but not excluded. Cleaning is 01_04.
- **Identity resolution** (toon_id canonicalisation) — deferred to Phase 02 per Invariant #2.
- **Temporal analysis** (stationarity, drift, panel structure) — deferred to section 01_05.
- **Full timestamp parsing** — deferred to 01_05; `timeUTC` 7-digit fractional-second format requires special handling not needed for this step.
- **`gameOptions` sub-fields** (`competitive`, `observers`, `practice`, `randomRaces`, and 11 additional fields) — deferred to 01_04 cleaning.
- **`mapAuthorName` and `mapFileSyncChecksum`** from `initData.gameDescription` — not extracted; neither is expected to have predictive value.
- **Full Section 3.1/3.2 profiling** (skewness, kurtosis, IQR outlier detection, duplicate detection, correlation matrices, completeness matrix) — deferred to 01_03 (Systematic Data Profiling).
- **Advanced visualizations** (scatter plots, correlation heatmaps, pair plots) — deferred to bivariate/multivariate EDA steps. Basic univariate histograms, boxplots, and bar charts ARE in scope.

---

## Open Questions

- What values does `result` take beyond Win/Loss? (Resolves in T01 Section 3)
- Are `SQ` and `supplyCappedPercent` fully populated or mostly NULL? (Resolves in T01 Section 2)
- Do any error boolean columns have TRUE values? (Resolves in T01 Section 7)
- Are all replays at Faster game speed? (Resolves in T01 Section 4 assertion — blocks Section 5 if not)

---

## Risks

1. **STRUCT access performance.** Extracting nested fields from ~22k rows should be fast in DuckDB. Mitigation: test Section A query with `LIMIT 100` first.
2. **Game speed not uniformly Faster.** If the Section D assertion fails, Section E cannot run — this is by design. The finding must be reported and the conversion formula updated before proceeding.

---

**Critique gate:** For Category A, adversarial critique is required before execution begins. Dispatch reviewer-adversarial to produce `planning/current_plan.critique.md`.
