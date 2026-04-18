---
category: A
date: 2026-04-18
branch: feat/01-04-03-aoe2-minimal-history
phase: "01"
pipeline_section: "01_04"
step: "01_04_03"
datasets: [aoestats, aoe2companion]
game: aoe2
title: "Step 01_04_03 — Minimal Cross-Dataset History View (aoe2 datasets, combined PR)"
manual_reference: "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md §4"
invariants_touched: [I3, I5, I6, I7, I8, I9]
predecessors: ["01_04_02 (sc2egset, aoestats, aoe2companion)"]
pattern_reference: "sc2egset 01_04_03 — PR #152 (MERGED)"
---

# Step 01_04_03 — Minimal cross-dataset history view (aoe2: aoestats + aoe2companion)

## Problem Statement

Phase 02+ rating-system backtesting needs identical table shape across sc2egset / aoestats / aoe2companion. sc2egset 01_04_03 (PR #152) established the pattern. This step produces sibling views in both aoe2 datasets — bundled in one PR per user directive. Inputs differ in grain (aoestats 1-row-per-match with p0/p1 columns; aoec natively 2-rows-per-match), requiring UNION ALL pivot for aoestats and self-join for aoec.

## Scope

Two datasets, one PR. Each dataset gets its own `matches_history_minimal` VIEW emitting the 8-column cross-dataset contract (canonical TIMESTAMP `started_at`, polymorphic civ-name `faction`, 2 rows per match). Non-destructive (I9) — no upstream YAML or raw table changes. Adds 01_04_03 step to each dataset's ROADMAP + STEP_STATUS; flips PIPELINE_SECTION_STATUS 01_04 → in_progress → complete.

## Literature Context

Cleaning-stage only (I9 scope):
- Manual `01_DATA_EXPLORATION_MANUAL.md` §4.2 (non-destructive cleaning), §4.4 (post-cleaning validation).
- Tukey (1977) — raw-string vocabulary documentation via FACTION_VOCAB SQL.
- Schafer & Graham (2002) + van Buuren (2018) — missingness handling inherited from 01_04_01.

Phase 02 consumer references (not cited as this step's methodology — sc2egset 01_04_03 precedent): Elo/Glicko/Glicko-2/TrueSkill/Aligulac/BTL.

## Assumptions & Unknowns

- **A1:** aoestats `matches_1v1_clean` row count 17,814,947 (per YAML `row_count`). Decisive 1v1 filter preserved — `p0_winner XOR p1_winner` per upstream.
- **A2:** aoec `matches_1v1_clean` row count 61,062,392 player-rows = 30,531,196 matches × 2 (per 01_04_02 research_log).
- **A3:** aoestats UNION ALL erases slot bias at output level — planner-science empirically confirmed `AVG(won::INT) = 0.5` exactly (slot0=0.477329, slot1=0.522671 preserve upstream bias at pre-UNION level).
- **A4:** `CAST(TIMESTAMPTZ AT TIME ZONE 'UTC' AS TIMESTAMP)` yields naive UTC TIMESTAMP in DuckDB — matches sc2egset's TRY_CAST output semantically.
- **A5:** aoestats `p{0,1}_civ` is nominally nullable but empirically zero-NULL in 1v1 ranked scope (gate enforces at execution — plan-level WARNING from R1 adversarial, acceptable since gate catches at runtime).
- **A6:** aoec `civ` is zero-NULL per 01_04_02 YAML (stricter than sc2/aoestats — gate reflects this).
- **A7:** aoec `matchId` INTEGER → variable decimal width → numeric-tail regex with round-trip cast (no fixed-length gate).

## Summary

Create `matches_history_minimal` VIEW in **both** aoe2 datasets, inheriting the 8-column cross-dataset contract established by sc2egset 01_04_03 (PR #152). Bundled in one PR per user directive.

- **aoestats:** 1-row-per-match (`p0_*` / `p1_*` columns) → **UNION ALL** pivot to 2-rows-per-match. 17,814,947 matches × 2 = 35,629,894 rows.
- **aoe2companion:** already 2-rows-per-match (player-row native) → **self-join on match_id** (sc2egset pattern). 30,531,196 matches × 2 = 61,062,392 rows.

Both datasets emit identical 8-col contract: `match_id, started_at (TIMESTAMP), player_id, opponent_id, faction, opponent_faction, won, dataset_tag`.

**Invariants:** I3 (TIMESTAMP — aoestats cast from TIMESTAMPTZ, aoec pass-through), I5-analog (NULL-safe `IS DISTINCT FROM`; aoestats adds slot-bias gate), I6 (DDL + assertion SQLs verbatim in JSON), I7 (magic-number provenance — aoestats `game_id` VARCHAR, aoec `matchId` INTEGER), I8 (polymorphic civ-name faction vocab), I9 (pure projection).

---

## BLOCKERS

**BLOCKER-1 (aoec): variable-length `matchId`.** aoec's `matchId` is INTEGER (1–10 decimal digits). sc2egset's fixed `length == 42` gate is infeasible. Use numeric-tail regex `[0-9]+` with round-trip cast assertion. Provenance: `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml` line `matchId: INTEGER`.

**BLOCKER-2 (aoec): no slot asymmetry to check.** matches_1v1_clean is natively 2-row player-row; no slot column. Slot-bias gate is N/A for aoec. I5-analog row-pair symmetry still enforced.

**BLOCKER-3 (combined PR): faction description self-consistency.** Both dataset YAML's `faction` column description must be self-consistent at merge time — aoec + aoestats descriptions both mention "full civ names" and cross-reference sc2egset's 4-char stems. Resolved by landing both in one PR.

---

## Schema (8 columns, identical contract for both datasets)

| column | dtype | aoestats source | aoec source |
|---|---|---|---|
| `match_id` | VARCHAR | `'aoestats::' \|\| game_id` (VARCHAR passthrough) | `'aoe2companion::' \|\| CAST(matchId AS VARCHAR)` |
| `started_at` | TIMESTAMP | `CAST(started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP)` (TIMESTAMPTZ → TIMESTAMP) | `started` (pass-through; already TIMESTAMP) |
| `player_id` | VARCHAR | `CAST(p{0,1}_profile_id AS VARCHAR)` (BIGINT → VARCHAR) | `CAST(profileId AS VARCHAR)` (INTEGER → VARCHAR) |
| `opponent_id` | VARCHAR | sibling row via UNION ALL | sibling row via self-join |
| `faction` | VARCHAR | `p{0,1}_civ` | `civ` |
| `opponent_faction` | VARCHAR | sibling row | sibling row |
| `won` | BOOLEAN | `p{0,1}_winner` (POST_GAME_HISTORICAL — acceptable as TARGET per sc2egset precedent) | `won` (pass-through) |
| `dataset_tag` | VARCHAR | `'aoestats'` | `'aoe2companion'` |

Grain: 2 rows per match.

---

## Empirical preconditions (confirmed by planner-science pre-planning)

- **aoestats:** total rows after UNION = 35,629,894 (= 2 × 17,814,947). overall_won_rate = 0.5 exactly. slot0_won_rate = 0.477329; slot1_won_rate = 0.522671 (matches upstream `team1_wins ≈ 52.27%` slot bias). UNION ALL erases the slot bias at OUTPUT level (every match contributes 1 won + 1 not-won regardless of which slot won upstream).
- **aoec:** total rows = 61,062,392 (= 2 × 30,531,196). `matchId` INTEGER confirmed; decimal width variable.

---

## Execution Steps

### T01 — Register 01_04_03 in both datasets' status files

1. `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`: append 01_04_03 block after 01_04_02.
2. `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`: add `01_04_03: status: not_started`.
3. `src/rts_predict/games/aoe2/datasets/aoestats/reports/PIPELINE_SECTION_STATUS.yaml`: flip `01_04` → `in_progress`.
4. Same 3 edits for aoe2companion paths.

### T02 — Create + execute aoestats notebook

`sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py` (19 cells, jupytext-paired).

**DDL (aoestats — UNION ALL pivot):**

```sql
CREATE OR REPLACE VIEW matches_history_minimal AS
-- aoestats sibling of sc2egset.matches_history_minimal (PR #152 pattern).
-- Input: matches_1v1_clean (1 row/match, p0/p1 cols). UNION ALL -> 2 rows/match.
-- Invariants: I3 (TIMESTAMP cast from TIMESTAMPTZ), I5-analog (NULL-safe symmetry +
--   slot-bias gate), I6 (SQL verbatim in JSON), I7 (prefix cites game_id VARCHAR),
--   I8 (cross-dataset 8-col contract), I9 (no upstream modification).
WITH p0_half AS (
    SELECT
        'aoestats::' || m.game_id                                     AS match_id,
        CAST(m.started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP)     AS started_at,
        CAST(m.p0_profile_id AS VARCHAR)                              AS player_id,
        CAST(m.p1_profile_id AS VARCHAR)                              AS opponent_id,
        m.p0_civ                                                      AS faction,
        m.p1_civ                                                      AS opponent_faction,
        m.p0_winner                                                   AS won,
        'aoestats'                                                    AS dataset_tag
    FROM matches_1v1_clean m
),
p1_half AS (
    SELECT
        'aoestats::' || m.game_id                                     AS match_id,
        CAST(m.started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP)     AS started_at,
        CAST(m.p1_profile_id AS VARCHAR)                              AS player_id,
        CAST(m.p0_profile_id AS VARCHAR)                              AS opponent_id,
        m.p1_civ                                                      AS faction,
        m.p0_civ                                                      AS opponent_faction,
        m.p1_winner                                                   AS won,
        'aoestats'                                                    AS dataset_tag
    FROM matches_1v1_clean m
)
SELECT * FROM p0_half
UNION ALL
SELECT * FROM p1_half
ORDER BY started_at, match_id, player_id;
```

**Validation SQL (aoestats-specific):**

- `ROW_COUNT`: total 35,629,894; distinct match_ids 17,814,947; 2-row matches 17,814,947; not-2 = 0.
- `SYMMETRY` (I5-analog NULL-safe): same OR-chain as sc2egset with `IS DISTINCT FROM`.
- `ZERO_NULL`: match_id/player_id/opponent_id/won/dataset_tag/faction/opponent_faction all 0. (started_at report-only.)
- `PREFIX_CHECK` (aoestats-specific): `match_id LIKE 'aoestats::%'` AND `regexp_extract(match_id, '::(.+)$', 1) != ''` (game_id is VARCHAR; no fixed length; no numeric regex).
- `DATASET_TAG`: distinct = 1, value 'aoestats'.
- `FACTION_VOCAB`: exploratory (expect ~50 civs).
- **`SLOT_BIAS_GATE` (I5-NEW)**: `SELECT AVG(won::INT) FROM matches_history_minimal` must equal exactly 0.5 (tolerance 1e-9). This is the aoestats-specific assertion for the UNION-ALL-erasing-slot-bias property.
- `TEMPORAL_SANITY`: min/max/null/distinct started_at.

### T03 — Create + execute aoec notebook

`sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_03_minimal_history_view.py` (18 cells).

**DDL (aoec — self-join, sc2egset pattern):**

```sql
CREATE OR REPLACE VIEW matches_history_minimal AS
-- aoe2companion sibling. Input: matches_1v1_clean (2 rows/match native).
-- Strategy: self-join on match_id with unequal player_id (sc2egset pattern).
-- Invariants: I3 (TIMESTAMP pass-through), I5-analog (NULL-safe symmetry),
--   I6, I7 (prefix cites matchId INTEGER), I8, I9.
WITH base AS (
    SELECT
        'aoe2companion::' || CAST(m.matchId AS VARCHAR) AS match_id,
        m.started                                       AS started_at,
        CAST(m.profileId AS VARCHAR)                    AS player_id,
        m.civ                                           AS faction,
        m.won                                           AS won
    FROM matches_1v1_clean m
)
SELECT
    p.match_id,
    p.started_at,
    p.player_id,
    o.player_id       AS opponent_id,
    p.faction,
    o.faction         AS opponent_faction,
    p.won,
    'aoe2companion'   AS dataset_tag
FROM base p
JOIN base o
  ON p.match_id = o.match_id
 AND p.player_id <> o.player_id
ORDER BY p.started_at, p.match_id, p.player_id;
```

**Validation SQL (aoec-specific):**

- `ROW_COUNT`: total 61,062,392; distinct match_ids 30,531,196; 2-row = 30,531,196; not-2 = 0.
- `SYMMETRY`: same NULL-safe `IS DISTINCT FROM` OR-chain.
- `ZERO_NULL`: all 7 non-nullable cols plus faction/opponent_faction = 0 (civ is zero-NULL upstream, stricter than sc2/aoestats).
- `PREFIX_CHECK` (aoec-specific): numeric-tail regex + round-trip cast:
  ```sql
  WHERE m.match_id NOT LIKE 'aoe2companion::%'
     OR regexp_extract(m.match_id, '::([0-9]+)$', 1) = ''
     OR regexp_extract(m.match_id, '::([0-9]+)$', 1)
        <> CAST(CAST(split_part(m.match_id, '::', 2) AS BIGINT) AS VARCHAR)
  ```
  Provenance: `matches_raw.yaml` line `matchId: INTEGER` (I7).
- `DATASET_TAG`: distinct = 1, value 'aoe2companion'.
- `FACTION_VOCAB`: exploratory (full civ names).
- `TEMPORAL_SANITY`: min/max/null/distinct started_at.
- No slot-bias gate (aoec natively 2-row, no slot column).

### T04 — Close status files + research_log entries (both datasets)

1. Both `STEP_STATUS.yaml`: `01_04_03: status: complete, completed_at: "2026-04-18"`.
2. Both `PIPELINE_SECTION_STATUS.yaml`: `01_04: complete` (revert from in_progress).
3. Prepend 01_04_03 entry to each dataset's `research_log.md`.

---

## File Manifest

**NEW (10 files):**
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.{py,ipynb}`
- `sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_03_minimal_history_view.{py,ipynb}`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/matches_history_minimal.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.{json,md}`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.{json,md}`

**MODIFIED (8 files — 4 per dataset):**
- `.../aoestats/reports/{ROADMAP.md, STEP_STATUS.yaml, PIPELINE_SECTION_STATUS.yaml, research_log.md}`
- `.../aoe2companion/reports/{ROADMAP.md, STEP_STATUS.yaml, PIPELINE_SECTION_STATUS.yaml, research_log.md}`

**Files NOT touched (I9):**
- Both datasets' `matches_1v1_clean.yaml` + `matches_raw.yaml` byte-identical.
- Both `PHASE_STATUS.yaml` unchanged.

---

## Gate Condition

Per dataset, 12 gates each + aoestats slot-bias #13.

### aoestats (13 gates):
1-2. Artifacts exist; DESCRIBE returns 8 cols / dtypes match.
3-5. `total_rows=35_629_894`; `distinct_match_ids=17_814_947`; `not-2=0`.
6. Symmetry violations = 0.
7-8. Zero NULLs on 5 non-null cols + faction cols.
9. Prefix violations = 0 (`LIKE 'aoestats::%'` + non-empty tail).
10. dataset_tag = 1 distinct, 'aoestats'.
11. Validation JSON `all_assertions_pass: true` + describe_table_rows.
12. research_log entry + STEP_STATUS closure.
**13. SLOT-BIAS: `AVG(won::INT) == 0.5 exactly` (NEW — aoestats-specific).**

### aoec (12 gates, no slot-bias):
1-2. Artifacts exist; DESCRIBE 8 cols / dtypes match.
3-5. `total_rows=61_062_392`; `distinct_match_ids=30_531_196`; `not-2=0`.
6. Symmetry violations = 0.
7-8. Zero NULLs on 5 non-null cols + faction cols (civ zero-NULL upstream).
9. Prefix violations = 0 (numeric-tail regex + round-trip cast).
10. dataset_tag = 1 distinct, 'aoe2companion'.
11. Validation JSON + describe_table_rows.
12. research_log + STEP_STATUS closure.

**Halt:** any gate fails → manually revert PIPELINE_SECTION_STATUS if already flipped.

---

## Open Questions

None blocking. Empirical preconditions verified pre-planning.

---

## Adversarial summary (to be filled by reviewer)

Plan ready for one adversarial round before execution. Expected: APPROVE or APPROVE_WITH_WARNINGS.

---

## ADDENDUM — Extension: `duration_seconds` across all 3 datasets (not just aoe2)

**User directive (2026-04-18 post-exec):** add `duration_seconds BIGINT` as 9th column to `matches_history_minimal` in **all 3 datasets** (sc2egset already on master from PR #152 + aoestats + aoec on this branch). Classified as POST_GAME_HISTORICAL (quasi post-game, excluded from PRE_GAME features but useful for learning-progress tracking / rating-update weighting / retrospective analyses). Consumer can easily exclude from PRE_GAME feature set.

### New 9-column contract

Prepend after `won`, before `dataset_tag`:

| col | dtype | semantics |
|---|---|---|
| ... | ... | ...cols 1-7 unchanged... |
| `won` | BOOLEAN | TARGET (unchanged) |
| **`duration_seconds`** | **BIGINT** | **POST_GAME_HISTORICAL. Match duration in seconds. Available after match end. NOT safe as PRE_GAME feature for match T. Use cases: retrospective rating-update weighting, learning-curve analysis, game-length-conditioned BTL.** |
| `dataset_tag` | VARCHAR | IDENTITY (unchanged) |

### Per-dataset derivation (R1 BLOCKERs resolved)

| dataset | source | derivation |
|---|---|---|
| sc2egset | **`player_history_all.header_elapsedGameLoops` BIGINT** (R1-BLOCKER-A2 fix: `matches_long_raw` + `matches_flat_clean` both exclude this col per I3; `player_history_all` at line 112 retains it) | **Aggregate first per replay (A3 fix):** `JOIN (SELECT replay_id, ANY_VALUE(header_elapsedGameLoops) AS loops FROM player_history_all GROUP BY replay_id) ph ON ph.replay_id = mfc.replay_id` → `CAST(ph.loops / 22.4 AS BIGINT) AS duration_seconds`. 22.4 constant: SC2 "Faster" game-speed loops/sec, empirically justified by `details.gameSpeed` cardinality=1 in sc2egset (W02 census, 01_02_04 artifact). Cite in SQL comment (I7): `details.gameSpeed cardinality=1 per sc2egset/reports/research_log.md:333; 22.4 loops/sec per Blizzard SC2 Faster-speed constant (Liquipedia)`. |
| aoestats | `matches_raw.duration` BIGINT **(NANOSECONDS — R1-BLOCKER-A1 fix; NOT seconds)** | `CAST(r.duration / 1000000000 AS BIGINT) AS duration_seconds`. Arrow `duration[ns]` mapped to BIGINT nanoseconds per DuckDB 1.5.1 behavior. I7 provenance: `aoestats/pre_ingestion.py:271` + `aoestats/reports/research_log.md:684,867,988,996`. Both UNION halves use identical expression (symmetric; same source row). |
| aoec | `matches_raw.started` / `matches_raw.finished` TIMESTAMPs — **R1-WARNING-A6 fix: compute IN-PLACE in `_mhm_base` staging; NO additional JOIN** (matches_raw already joined at staging level — add as column). | `CAST(EXTRACT(EPOCH FROM (r.finished - r.started)) AS BIGINT) AS duration_seconds`. Gate +6 (NEW): measure NULL fraction; halt if > 1% (R1-WARNING-A7 fix — aoec `finished` is nullable for abandoned/crashed matches). |

### Invariants

- **I3:** `duration_seconds` is POST_GAME_HISTORICAL (machine-grep-able token per R1-WARNING-A8 fix). Schema YAML `notes` field first token MUST be exactly `POST_GAME_HISTORICAL.` (matching the existing IDENTITY/CONTEXT/PRE_GAME/TARGET vocabulary established in 01_04_02 + 01_04_03 sc2egset). Phase 02 feature extractors that drop POST_GAME_HISTORICAL tokens will automatically exclude this column. Plan-level doc + YAML machine-token enforce I3 at both the human-review and tooling levels.
- **I5-analog:** Both rows of a match have identical `duration_seconds` (mirror symmetry extended). Symmetry SQL extended: `a.duration_seconds IS NOT DISTINCT FROM b.duration_seconds` (NULL-safe DuckDB-verified per R1-WARNING-A5).
- **I6:** DDL + assertion SQL verbatim; describe_table_rows reflects 9-col schema.
- **I7 (EXPANDED):** Three magic-number provenance citations in schema YAMLs:
  - sc2egset: 22.4 loops/sec — cite `details.gameSpeed cardinality=1` (research_log.md:333, W02 census) + Blizzard "Faster" constant (Liquipedia SC2 Game Speed).
  - aoestats: 1_000_000_000 nanoseconds-to-seconds divisor — cite `pre_ingestion.py:271` (Arrow duration[ns] → BIGINT behavior) + `research_log.md:684,867,988,996`.
  - aoec: `EXTRACT(EPOCH FROM)` standard DuckDB function — no magic constant (empirical DuckDB test in R1-WARNING-A5).
- **I8:** All 3 datasets emit `duration_seconds` BIGINT in column 8. Cross-dataset unit: **seconds** (sc2egset `/22.4`; aoestats `/1e9`; aoec `EXTRACT EPOCH`). BIGINT across all datasets via `CAST(... AS BIGINT)`.
- **I9:** JOINs to `player_history_all` (sc2egset), `matches_raw` (aoestats, aoec) are READ-ONLY. No raw or clean mutation.

### Scope adjustment

**sc2egset (already merged in PR #152 at 8 cols) — needs UPDATE** in this PR:
- Update VIEW DDL via `CREATE OR REPLACE` with 9 cols.
- Update schema YAML (add duration_seconds col).
- Re-execute notebook (sibling cells added).
- Update validation JSON + MD.
- Append addendum entry to research_log.

**aoestats + aoec (on this branch, 8 cols in commit fa15963) — needs EXTENSION** in new commit:
- Same updates.

**Branch name `feat/01-04-03-aoe2-minimal-history`** becomes mildly misleading (now covers 3 datasets) — acceptable; PR title at creation time: "feat(01-04-03): add duration_seconds across all 3 datasets + aoe2 minimal history views (sc2egset update + aoestats/aoe2companion new)".

### Extended Gate Condition (per dataset)

Prior gates unchanged; **add**:
- Gate +1: DESCRIBE returns 9 cols in order `[..., won BOOLEAN, duration_seconds BIGINT, dataset_tag VARCHAR]`.
- Gate +2: `duration_seconds` non-null count reported; NULL count reported. Halt threshold: aoec NULL fraction > 1% halts (R1-WARNING-A7 fix); sc2egset + aoestats have no NULL expected, report-only.
- Gate +3: `duration_seconds > 0` for all non-NULL rows (sanity).
- Gate +4: Duration symmetry: `(a.duration_seconds IS NOT DISTINCT FROM b.duration_seconds)` for all match-mirror pairs — 0 violations required.
- Gate +5: Duration range reasonable: min ≥ 0, max ≤ 86400 (24 hours — sanity bound). **HALTING (R1-WARNING-A7 upgrade): if max > 86400, something is wrong (e.g., unit bug repeats A1).** This gate protects against silent nanosecond-unit regression.
- **Gate +6 (aoec-specific NEW, R1-WARNING-A7):** NULL fraction on `duration_seconds` (= NULL `finished`) ≤ 1% (else HALT). sc2egset + aoestats: N/A.

Total gates: sc2egset 17 (was 12, +5 from duration; slot-bias N/A), aoestats 18 (was 13, +5 from duration), aoec 18 (was 12, +6 from duration including A7 NULL-fraction gate).

### Assumptions (new)

- **A-D1:** sc2egset replays are recorded at "Faster" game speed (22.4 loops/sec). Corner cases with "Normal" (16 loops/sec) would underestimate duration by ~30%. Accept as minor for thesis-level precision; flag in sc2egset YAML notes as a calibration caveat. If the upstream `matches_long_raw` has a `gameSpeed` column, use it for per-replay correction; otherwise assume Faster.
- **A-D2:** aoestats `duration` column is in-game seconds (per raw YAML description "in-game duration"). Use directly; ignore `irl_duration` (wall-clock including pauses — less useful for game-length analysis).
- **A-D3:** aoec `finished - started` TIMESTAMP diff yields wall-clock duration (no pauses). Good approximation of game duration for unpaused matches.
- **A-D4:** sc2egset's join to matches_long_raw adds row multiplier concern: matches_flat_clean has 1 row per replay (wide); matches_long_raw has 2 rows per replay (long). Use aggregated subquery (`GROUP BY replay_id`) to get 1 duration per replay before joining.

### Open questions (user decision — defaults chosen, flag if override)

1. **Default:** sc2egset duration assumes 22.4 loops/sec constant. Override to per-replay lookup of `gameSpeed` if you want stricter provenance.
2. **Default:** aoestats uses `duration` (in-game seconds), not `irl_duration`. Override if you prefer wall-clock.
3. **Default:** aoec derives from `finished - started` (wall-clock). No in-game duration column available — accept wall-clock.

### Files additionally impacted (vs parent plan)

**sc2egset (UPDATE — 5 files; on master, will modify):**
- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_03_minimal_history_view.{py,ipynb}`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_history_minimal.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.{json,md}`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (addendum entry)

**aoestats + aoec (UPDATE — 5 files each):**
- Same pattern, on current branch, replacing the 8-col versions shipped in fa15963.

**CHANGELOG.md:** extend [3.14.0] entry with sc2egset update + duration_seconds column. No version re-bump (same PR scope).

### Execution order

One coordinated executor session (serial — not parallel) to keep 9-col contract consistent across all 3 datasets. Pattern:
1. sc2egset update (CREATE OR REPLACE VIEW with JOIN to matches_long_raw).
2. aoestats extension (DDL extends UNION ALL CTEs with duration_seconds).
3. aoec extension (DDL extends base CTE with JOIN to matches_raw; re-materialize TABLE).
4. All 3 research_logs addendum entries.
5. CHANGELOG extension.

---
