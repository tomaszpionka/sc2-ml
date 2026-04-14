---
reviewer: reviewer-adversarial
plan: planning/plan_01_02_03_struct_eda.md
date: 2026-04-14
verdict: APPROVE_WITH_CHANGES
---

# Adversarial Critique: plan_01_02_03_struct_eda.md

## Verdict
**APPROVE WITH REVISIONS** — The plan is scientifically sound in scope and structure, but contains one unsupported assumption (universal Faster game speed) that could silently corrupt duration calculations, omits a required ROADMAP entry, and has gate conditions too weak to catch STRUCT path failures.

---

## Critical Issues (must fix before execution)

### 1. Game-loop conversion assumes Faster speed without verification (plan Section E)

The plan states: "convert to real seconds (game loops / 22.4 at Faster speed)" and applies this in Section E (numeric descriptive statistics) **before** Section D has established whether `details.gameSpeed` is uniformly "Faster" across all 22,390 replays.

The 22.4 constant is correct for Faster speed (16 base loops/s × 5734/4096 multiplier = 22.4). But Section E applies it unconditionally without conditioning on the Section D census of `gameSpeed` values.

**Why it matters:** If any replays use Normal, Slow, or Slower speeds, the duration calculation will be wrong by up to 2.3x, silently corrupting descriptive statistics and any downstream cleaning thresholds.

**Fix:** Add a sequencing dependency: the Section E duration conversion cell must first assert that all replays have `gameSpeed = 'Faster'` using the Section D census result, or branch to use per-replay speed. Add the Liquipedia multiplier citation rather than bare "22.4" (Invariant #7 — no magic numbers without citation).

### 2. Step 01_02_03 missing from ROADMAP

The ROADMAP defines only steps 01_01_01, 01_01_02, 01_02_01, 01_02_02. STEP_STATUS.yaml header states: "Derived from ROADMAP.md step definitions. If this file disagrees with the ROADMAP, this file is wrong."

T02 instructs the executor to add 01_02_03 to STEP_STATUS.yaml, but there is no instruction to add the step definition to the ROADMAP first.

**Fix:** Add a T00 pre-task (or prepend to T02) that adds the 01_02_03 step definition to ROADMAP.md using the same YAML schema as existing steps (step_number, name, description, phase, pipeline_section, predecessors, notebook_path, inputs, outputs, gate, thesis_mapping, research_log_entry). Add `ROADMAP.md` to T02's file scope.

---

## Moderate Issues (should fix)

### 3. Gate conditions cannot detect STRUCT path failures

Gate condition #3 requires valid JSON with NULL counts and descriptive statistics. But DuckDB returns NULL (not an error) when accessing a non-existent STRUCT field path. A notebook that runs on wrong STRUCT paths will produce all-NULL results — which is valid JSON and does "contain" statistics (all NULL/NaN). The gate passes.

**Fix:** Add explicit gate condition: "At least 3 extracted STRUCT fields must have non-NULL rate > 0%." Or add a sanity-check assertion cell after Section A: assert `COUNT(*) WHERE game_speed IS NOT NULL > 0`.

### 4. `timeUTC` full parsing risk (Section F)

The SC2EGSet `timeUTC` format is `2016-07-29T04:50:12.5655603Z` — 7-digit fractional seconds (.NET 100-nanosecond precision). DuckDB's `STRPTIME %f` handles only 6 digits; 7 digits may fail.

**Fix:** In Section F, use string-based MIN/MAX (ISO 8601 strings sort lexicographically) and `SUBSTR(details.timeUTC, 1, 7)` for month extraction — no STRPTIME needed. Reserve full timestamp parsing for 01_05 (Temporal & Panel EDA).

### 5. `header."version"` quoting inconsistency

SQL sketch correctly uses `header."version"` (quoted, since `version` is a DuckDB reserved keyword), but prose references use unquoted `header.version`. Unquoted form will fail with a parse error.

**Fix:** Standardize to `header."version"` throughout. Add a one-line note warning the executor that `version` must be quoted.

### 6. EDA Manual Section 3.1/3.2 coverage claims are overstated

The plan claims to cover Manual Sections 3.1 and 3.2, but omits required items:

- **Section 3.1** requires: zero count, skewness, kurtosis, outlier detection (IQR fences, z-scores), pattern/format frequency for strings, uniqueness ratio as per-column metric.
- **Section 3.2** requires: duplicate row count/percentage, feature completeness matrix, correlation matrices, memory footprint. These belong in 01_03 (Systematic Data Profiling).

**Fix:** Change the Scientific Rationale to say "partially covers Manual Sections 3.1 and 3.2 — univariate census layer; remaining profiling metrics (zero counts, skewness, kurtosis, IQR outlier detection, correlation matrices, duplicate detection) deferred to 01_03."

---

## Minor Issues (consider fixing)

### 7. Cross-check analyses technically bivariate

Section A proposes cross-checking `details.gameSpeed` vs `initData.gameDescription.gameSpeed`. This is technically bivariate. The plan defers all bivariate analysis but includes these.

**Fix:** Add a note to Out of Scope: "Data-quality cross-checks between duplicate fields are included as integrity checks, not exploratory bivariate EDA."

### 8. `gameOptions` sub-STRUCT fields not documented

`initData.gameDescription.gameOptions` contains fields (`competitive`, `observers`, `practice`, `randomRaces`) not extracted. `gameOptions.competitive` could be relevant for filtering non-competitive replays in 01_04.

**Fix:** Add a note to the research_log template that these fields exist and may be relevant for 01_04 cleaning filters.

### 9. Section D and E cell count risk

Sections D (10 categorical fields) and E (8+ numeric fields) may exceed the 50-line cell cap if implemented as per-column cells.

**Fix:** T01 instructions should explicitly state that Sections D and E use loop-based cells iterating over column lists — matching the pattern in 01_02_02's for-loop cells.

### 10. NULL census missing null percentage

Section B's NULL census SQL computes raw null counts but not null percentages. EDA Manual Section 3.1 requires "null/missing count **and percentage**."

**Fix:** Add `ROUND(100.0 * (COUNT(*) - COUNT(col)) / COUNT(*), 2)` columns, or compute in a follow-up cell.

---

## Confirmed Correct

1. **All STRUCT field paths are valid.** Every path in the SQL sketch was cross-referenced against the 01_02_02 ingestion artifact schema — all match (`details.gameSpeed`, `header.elapsedGameLoops`, `metadata.mapName`, `initData.gameDescription.mapSizeX`, etc.).

2. **The 25-column NULL census is complete and correct.** All 25 columns listed match the `replay_players_raw` schema from the ingestion artifact exactly.

3. **`result` column exists in `replay_players_raw`.** Confirmed from ingestion.py (`result VARCHAR`). Target variable analysis will work.

4. **22.4 loops/second constant is arithmetically correct for Faster speed.** 16 base × 5734/4096 = 22.4. The problem is unconditional application, not the constant itself.

5. **Invariant #6 compliance correctly planned.** T01 instruction 10 requires SQL queries verbatim in the markdown; gate condition 2 re-states it. Matches 01_02_02 pattern.

6. **Invariant #9 compliance correctly planned.** Conclusions limited to univariate distributions and NULL rates. No cleaning, no features, no identity resolution. Out of Scope section explicitly documents the boundaries.

7. **`SUBSTR(details.timeUTC, 1, 7)` for month extraction is robust.** Given confirmed ISO 8601 format, this produces correct `YYYY-MM` keys that sort lexicographically. MIN/MAX on raw VARCHAR is also correct.

8. **`get_notebook_db("sc2", "sc2egset")` read-only access is correct.** No DDL/DML needed; the step only queries existing tables.

---
reviewer: reviewer-adversarial
plan: planning/plan_aoe2companion_01_02_03.md
date: 2026-04-14
verdict: APPROVE_WITH_CHANGES
---

# Adversarial Critique: plan_aoe2companion_01_02_03.md

## Verdict
**APPROVE WITH REVISIONS** — The plan is scientifically sound in scope and structure, but has a blocking prerequisite (01_02_02 not yet run), partial SQL sketches in the auxiliary table census that contradict the "full census" claim, two missing columns in the categorical analysis (`name`, `colorHex`), and a vague cross-game target encoding documentation requirement.

---

## Critical Issues (must fix before execution)

### 1. Prerequisite 01_02_02 is not_started — execution is blocked

STEP_STATUS.yaml lists `01_02_02` as `status: not_started`. No ingestion artifact exists and no DuckDB tables have been materialised. The plan acknowledges this in a "Prerequisite Dependency" section below the task definitions, but T01's instructions do not gate on this explicitly.

**Fix:** Add to T01 instructions, item 0 (before item 1): "HALT: Before proceeding, verify that `STEP_STATUS.yaml` shows `01_02_02: complete` AND that artifact `01_02_02_duckdb_ingestion.json` exists on disk. If either is false, abort."

---

## Moderate Issues (should fix)

### 1. Section H claims "full NULL census" but SQL sketches are partial

- **`leaderboards_raw`** (18 columns): plan SQL covers only 7. Missing: `name`, `lastMatchTime`, `drops`, `losses`, `streak`, `wins`, `games`, `updatedAt`, `rankCountry`, `active`, `season`, `rankLevel` — including `wins`, `losses`, `games`, `streak` relevant to pre-game feature engineering.
- **`profiles_raw`** (13 columns): plan SQL covers only 6. Missing: `avatarhash`, `sharedHistory`, `twitchChannel`, `youtubeChannel`, `youtubeChannelName`, `discordId`, `discordName`, `discordInvitation`.
- **`ratings_raw`** (8 columns): plan SQL misses `date`, `season`, `filename`. `date` NULL rate is needed for Section G temporal analysis.

**Fix:** Either (a) use the `DESCRIBE` + iterate approach for auxiliary tables the same as Section A, or (b) explicitly rename "full NULL census" to "key-column NULL census" and list deferred columns.

### 2. Section D categorical list missing `name` and `colorHex`

`name` (in-game player name) is the foundational field for Invariant #2 identity resolution in Phase 02. Its cardinality and NULL rate must be profiled at this step. `colorHex` (hex string) also absent. Both appear in the schema but are not in Section D's column list.

**Fix:** Add `name` (with note: cardinality + top-k needed for Phase 02 identity resolution baseline) and `colorHex` to Section D.

### 3. `matchId` and `profileId` not in Section F numerics

These are INT32 identifiers. `profileId` cardinality = distinct player count — a prominent thesis-citable number that should be in the artifact explicitly, not buried in Section A's cardinality column.

**Fix:** Add `matchId` and `profileId` to Section F's numeric list with a note that these are identifiers profiled for structural characterisation.

### 4. Cross-game target encoding documentation is vague

The plan states "Target variable encoding documented (BOOLEAN won vs VARCHAR result in SC2)" but does not specify what the artifact must record to enable future cross-game mapping. sc2egset has `'Tie'` and `'Undecided'` values with no aoe2companion equivalent. The artifact should explicitly document the mapping gap.

**Fix:** Add to T02 decisions deferred: "Cross-game target alignment: sc2egset `result` includes 'Tie' and 'Undecided' which have no aoe2companion equivalent. Binary target definition must be harmonised before Phase 03."

---

## Minor Issues (consider fixing)

### 1. Section A iteration must include `filename` column

If the executor uses a hardcoded 54-column list from the schema discovery artifact rather than `DESCRIBE matches_raw` output, `filename` (column 55, added by ingestion) will be missed. Add a note: "Use `DESCRIBE matches_raw` output, not a hardcoded column list."

### 2. `SUMMARIZE` uses approximate cardinality (`approx_unique`)

If `SUMMARIZE` is used for the NULL census, all cardinality values reported in the artifact must come from exact `COUNT(DISTINCT ...)` queries — not `approx_unique`. `SUMMARIZE` may be used as a fast sanity check only.

### 3. Uniqueness ratio definition ambiguous at 277M rows

At 277M rows, a column with 277 distinct values has uniqueness ratio 0.000001 — near-constant by the 0.001 threshold. Moderate-cardinality categoricals may be false-flagged. Add a note: at this scale, near-constant flagging requires domain judgment.

### 4. Boolean census is 18 separate full-table scans

Section E's loop approach produces 18 sequential scans of 277M rows. A single query with all 18 `FILTER` clauses is more efficient. Suggest a batch approach matching Section A's philosophy.

---

## Confirmed Correct

1. **Table names match `ingestion.py` exactly** — `matches_raw`, `ratings_raw`, `leaderboards_raw`, `profiles_raw` all verified.
2. **Column names in Sections B, C, D, E, F match the schema discovery artifact** (with exceptions noted above).
3. **`ratings_raw` underscore vs camelCase convention correctly handled** — `profile_id`, `leaderboard_id`, `rating_diff` for ratings vs `profileId`, `ratingDiff` for matches.
4. **`won` is per-player, not per-match** — the plan correctly treats `matches_raw` as one-row-per-player-per-match.
5. **`avg_rows_per_match = 3.71` interpretation is sound** — correctly identified as evidence of team-game data; Section C decomposes by leaderboard.
6. **Section G needs no speed conversion** — `started`/`finished` are real-world timestamps unlike sc2egset's game loops.
7. **Invariant #9 compliance correctly scoped** — bivariate analysis, cleaning, filtering all deferred explicitly.
8. **Invariant #7 thresholds cited correctly** — dead field (cardinality=1) and near-constant (0.001) both trace to EDA Manual Section 3.3.
