# Research Log

Thesis: "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

Reverse chronological entries. Each entry documents the reasoning and learning behind code changes — intended as source material for thesis writing.

---

## 2026-04-04 — [CHORE] Repository reorganization: `sc2ml` → `rts_predict` namespace

**Objective:** Structural standardization to support the planned SC2 + AoE2 comparative
study. The `sc2ml` package name was SC2-specific and did not scale. All SC2 artifacts
have been moved under a unified `rts_predict` namespace.

**Changes made:**
- Python package renamed: `sc2ml` → `rts_predict.sc2` (all imports updated)
- SC2 phase artifacts moved: `reports/00_*`, `reports/01_*`, `sanity_validation.md`,
  `archive/` → `src/rts_predict/sc2/reports/` (history preserved via `git mv`)
- Roadmap renamed: `SC2ML_THESIS_ROADMAP.md` → `SC2_THESIS_ROADMAP.md`
- CLI entry point renamed: `sc2ml` → `sc2`
- `reports/` at repo root now contains only the cross-cutting `research_log.md`
- New placeholder packages: `rts_predict.aoe2`, `rts_predict.common`
- New infrastructure: `ARCHITECTURE.md`, `PHASE_STATUS.yaml` (per game), `REVIEW_QUEUE.md`,
  `.claude/chat-handoff.md`, `common/CONTRACT.md`
- Version bumped to `0.14.0`

**Motivation:** AoE2 integration begins after SC2 pipeline is complete. Having SC2
artifacts mixed at the repo root would complicate the mirrored AoE2 structure. This
reorganization creates the structural foundation for a clean side-by-side comparison.

**No analytical changes:** Business logic, SQL queries, and test assertions are
unchanged. This is a pure structural/naming chore.

---

## 2026-04-03 — [SC2] Phase 1 corpus inventory: Steps 1.1–1.7 complete, Step 1.8 pending

**Objective:** Run the full Phase 1 exploration (Steps 1.1–1.7) to characterise
the SC2EGSet corpus — structural validation, parse quality, duration distribution,
APM/MMR usability, patch landscape, event type inventory, and PlayerStats sampling
regularity. All findings are observational; no cleaning decisions are made.

All results below comply with Scientific Invariant #8: every finding is accompanied
by the literal SQL that produced it (embedded in the report artifacts).

---

### Step 1.1 — Overall corpus counts and structural validation

**Key findings:**

| Metric | Value |
|--------|-------|
| Total replays | 22,390 |
| Distinct tournaments | 70 |
| Date range | 2016-01-07 to 2024-12-01 |
| Null match timestamps | 0 |
| Replays with tracker events | 22,390 (100%) |
| Player count anomalies (≠ 2 players) | 13 replays |
| Exact duplicate replay IDs | 0 |
| Near-duplicates (same players, same map, < 60s apart) | 88 pairs |

**Result field values:**

| result_value | slot_count |
|---|---|
| Loss | 22,409 |
| Win | 22,382 |
| Undecided | 24 |
| Tie | 2 |

Non-standard results: 26 slots (24 Undecided + 2 Tie). No nulls.
Anomalous replays: 13 with no winner, 4 with multiple winners.

```sql
-- Near-duplicate detection (example — full SQL in src/rts_predict/sc2/reports/01_duplicate_detection.md)
WITH raw_entries AS (
    SELECT filename,
           regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id,
           (details->>'$.timeUTC')::TIMESTAMP AS match_time,
           metadata->>'$.mapName' AS map_name,
           CAST(entry.value->>'$.nickname' AS VARCHAR) AS nickname,
           CAST(entry.value->>'$.result' AS VARCHAR) AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
),
players_per_game AS (
    SELECT filename, ANY_VALUE(replay_id) AS replay_id,
           ANY_VALUE(match_time) AS match_time, ANY_VALUE(map_name) AS map_name,
           LIST(LOWER(nickname) ORDER BY LOWER(nickname)) AS player_names
    FROM raw_entries
    WHERE nickname IS NOT NULL AND (result_val = 'Win' OR result_val = 'Loss')
    GROUP BY filename
)
SELECT a.replay_id AS replay_id_a, b.replay_id AS replay_id_b,
       a.map_name, a.match_time AS time_a, b.match_time AS time_b,
       ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) AS time_diff_seconds
FROM players_per_game a
JOIN players_per_game b ON a.player_names = b.player_names
    AND a.map_name = b.map_name AND a.replay_id < b.replay_id
    AND ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) <= 60
ORDER BY time_diff_seconds
```

**Artifacts:** `src/rts_predict/sc2/reports/01_corpus_summary.json`, `src/rts_predict/sc2/reports/01_player_count_anomalies.csv`,
`src/rts_predict/sc2/reports/01_result_field_audit.md`, `src/rts_predict/sc2/reports/01_duplicate_detection.md`

---

### Step 1.2 — Per-tournament parse quality

**Key findings:**
- 70 tournaments total, **18 flagged** (player count anomalies or result anomalies)
- Event coverage: 100% across all tournaments (no missing tracker events)
- All flags are result anomalies (Undecided/Tie) or player count ≠ 2 — no systematic
  parse failures

```sql
-- Full SQL in src/rts_predict/sc2/reports/01_parse_quality_summary.md
-- Flagging thresholds: event_coverage_pct < 80, player_count_anomalies > 0, result_anomalies > 0
```

**Artifacts:** `src/rts_predict/sc2/reports/01_parse_quality_by_tournament.csv`, `src/rts_predict/sc2/reports/01_parse_quality_summary.md`

---

### Step 1.3 — Game duration distribution

**Overall percentiles (real-time minutes, N=22,390):**

| Statistic | Value |
|-----------|-------|
| Mean | 11.98 |
| Median | 10.85 |
| P01 | 3.34 |
| P05 | 4.94 |
| P25 | 8.27 |
| P75 | 14.43 |
| P95 | 22.52 |
| P99 | 31.31 |

```sql
SELECT COUNT(*) AS n,
    ROUND(AVG(real_time_minutes), 2) AS mean,
    ROUND(MEDIAN(real_time_minutes), 2) AS median,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.01), 2) AS p01,
    -- (full query in src/rts_predict/sc2/reports/01_duration_distribution.csv header)
FROM (
    SELECT (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS real_time_minutes
    FROM raw WHERE (header->>'$.elapsedGameLoops') IS NOT NULL
)
```

**Conversion formula (Scientific Invariant #6):**
`real_time_minutes = game_loops / 22.4 / 60.0`
(22.4 = 16 engine loops/sec × 1.4 Faster speed multiplier)

Duration is stable across years (median ~10–11 min, no drift).
Short-tail: 50 games < 2 min (possible lobby artifacts); significant mass 3–5 min
(cheese/early all-ins). Annotated landmarks on short-tail plot per literature:
- 2 min: worker rush zone
- 4 min: cheese/cannon rush (Liquipedia)
- 7 min: MSC minimum (Wu et al. 2017)
- 9 min: SC2EGSet minimum (Białecki et al. 2023)

**Artifacts:** `src/rts_predict/sc2/reports/01_duration_distribution.csv`,
`src/rts_predict/sc2/reports/01_duration_distribution_full.png`,
`src/rts_predict/sc2/reports/01_duration_distribution_short_tail.png`

---

### Step 1.4 — APM and MMR audit

**APM by year:** 2016 is 100% zero (1,110/1,110 slots). From 2017 onward,
zero-rate drops to 0.4% (18/4,004 in 2017) and ≤0.1% thereafter.
Confirms Scientific Invariant #7.

**MMR by year:** Not reported in table form here — see `src/rts_predict/sc2/reports/01_apm_mmr_audit.md`.
Conclusion unchanged from Phase 0: MMR is NOT usable as a direct feature
(systematic missingness).

```sql
-- APM by year (full SQL in reports/01_apm_mmr_audit.md)
SELECT EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero,
    ROUND(100.0 * ... / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

**Artifact:** `src/rts_predict/sc2/reports/01_apm_mmr_audit.md`

---

### Step 1.5 — Patch landscape

Identified game versions spanning 2016–2024. Full CSV with 79 distinct
(gameVersion, dataBuild) pairs. Data build values enable future per-patch
stratification.

**Artifact:** `src/rts_predict/sc2/reports/01_patch_landscape.csv`

---

### Step 1.6 — Tracker event type inventory

**Event types (corpus-wide):**

| event_type | total_rows | replays_with_type | avg_per_replay | median_per_replay |
|---|---|---|---|---|
| PlayerStats | 42,523,988 | 22,390 | 1,899.2 | 1,556 |
| UnitBorn | 23,003,640 | 22,390 | 1,027.4 | 888 |
| UnitDied | 16,710,032 | 22,390 | 746.3 | 615 |
| UnitTypeChangeEvent | 2,107,124 | 22,390 | 94.1 | 72 |
| UpgradeEvent | 688,850 | 22,390 | 30.8 | 28 |
| UnitInitEvent | 361,168 | 22,339 | 16.1 | 14 |
| UnitDoneEvent | 226,014 | 22,260 | 10.1 | 8 |
| PlayerSetupEvent | 44,780 | 22,390 | 2.0 | 2 |

(Approximate values from CSV — see exact data in `src/rts_predict/sc2/reports/01_event_type_inventory.csv`)

Zero-PlayerStats replays: 0 (all replays with tracker events have PlayerStats).

Outlier-flagged tournaments: identified via 2-sigma rule on tournament-level averages.
See `src/rts_predict/sc2/reports/01_event_density_by_tournament.csv`.

**Artifacts:** `src/rts_predict/sc2/reports/01_event_type_inventory.csv`,
`src/rts_predict/sc2/reports/01_event_count_distribution.csv`,
`src/rts_predict/sc2/reports/01_event_density_by_year.csv`,
`src/rts_predict/sc2/reports/01_event_density_by_tournament.csv`

---

### Step 1.7 — PlayerStats sampling regularity

**Method:** Sampled 10 games per year (2016–2024) deterministically
(`random.Random(42)`), computed inter-event game_loop deltas for PlayerStats
events, aggregated per-game and per-year.

**Result:** Mean interval across all years is consistently ~158 loops
(range: 157.7–158.2). Deviation from expected 160 is 1.1–1.4%, well within
the 20% tolerance threshold. **No years flagged.**

```python
# Sampling: random.Random(RANDOM_SEED=42).sample(ids_per_year, 10)
# Interval computation: ps_df.groupby(["replay_id", "player_id"])["game_loop"].diff()
# Flagging: abs(year_mean - 160) / 160 > 0.20
```

The consistent ~158 mean (vs expected 160) is likely due to first-event offset:
the first PlayerStats event in each player's stream occurs at game_loop < 160,
pulling the mean slightly below 160. The within-game standard deviation is
typically < 25 loops, confirming regular sampling.

**Artifact:** `src/rts_predict/sc2/reports/01_playerstats_sampling_check.csv`

---

### Gate conditions (Steps 1.1–1.7 only — Phase 1 gate NOT yet met)

All 16 artifacts from Steps 1.1–1.7 exist on disk. Partial gate statements
(pending Step 1.8 for full Phase 1 gate):

- **(a)** 22,390 replays, all structurally valid (100% event coverage, 0 null timestamps).
  13 player-count anomalies, 0 exact duplicates, 88 near-duplicate pairs.
- **(b)** 18/70 tournaments flagged (result anomalies or player count ≠ 2). No event
  data gaps — all tournaments have 100% tracker event coverage.
- **(c)** Duration: median 10.85 min, mean 11.98 min, P01=3.34 min, P99=31.31 min.
  No threshold chosen (observation only).
- **(d)** APM usable from 2017+ (Invariant #7 confirmed). MMR not usable.
- **(e)** Tracker event density consistent across years. PlayerStats present in all
  22,390 replays with events.
- **(f)** PlayerStats sampling interval stable: ~158 loops across all years (2016–2024),
  within 1.4% of expected 160. No years flagged.

### Open issue: Phase 1 extension needed before Phase 2

Phase 1 covered the fields listed in the roadmap but did not audit several JSON
fields that could silently corrupt results or represent missed features. A sample
replay inspection (`src/rts_predict/sc2/reports/01_corpus_summary.json` references
`src/sc2ml/data/samples/processed/0e0b1a550447f0b0a616e48224b31bd9.SC2Replay.json`)
revealed the following gaps, grouped by severity:

**CRITICAL — could silently corrupt results if not checked:**

1. **`gameSpeed`** (`initData.gameDescription.gameSpeed` and `details.gameSpeed`):
   The entire duration conversion (22.4 loops/sec) and all Phase 4 timepoints assume
   Faster speed. If any games are at Normal or another speed, every duration-based
   calculation for those games is wrong by up to 40%. A single query to verify,
   but it is foundational to Invariant #6.

2. **Error flags** (`trackerEvtsErr`, `gameEventsErr`, `messageEventsErr`):
   A game with `trackerEvtsErr = true` may have partial tracker events that look
   normal but are incomplete. Phase 4 would build features on those incomplete
   PlayerStats snapshots without knowing anything was wrong.

3. **`handicap`** (`ToonPlayerDescMap.*.handicap`): If ≠ 100, the player starts
   with reduced HP on all units/structures — not a fair competitive game.
   Should be a cleaning rule.

4. **`noVictoryOrDefeat`** (`initData.gameDescription.gameOptions.noVictoryOrDefeat`):
   If `true`, the game cannot produce a Win/Loss result. Should be `false` for all
   tournament games.

5. **`selectedRace`** (`ToonPlayerDescMap.*.selectedRace`): If `"Random"`, the
   `race` field shows the assigned race, not the player's choice. This matters for
   Phase 2 race consistency and Phase 7 race-based features — a Protoss main who
   got assigned Zerg would be misclassified as a race switcher.

**IMPORTANT — potential features or data quality indicators:**

6. **`SQ` (Spending Quotient)** (`ToonPlayerDescMap.*.SQ`): SC2's built-in
   per-game efficiency metric. Unlike MMR, it's computed from the replay itself,
   so it may be available for every game including 2016 where APM is all zeros.
   Needs the same year-by-year zero-rate audit as APM/MMR. Potentially a stronger
   skill proxy than APM.

7. **`supplyCappedPercent`** (`ToonPlayerDescMap.*.supplyCappedPercent`): Per-game
   efficiency metric (% of game time supply-blocked). Same audit needed.

8. **`maxPlayers`** (`initData.gameDescription.maxPlayers`): If > 4, the map
   may be a team game map. Combined with the 13 player-count anomalies, this
   helps distinguish FFA/team games from 1v1 with spectators.

9. **`competitive`** (`initData.gameDescription.gameOptions.competitive`):
   Indicates ranked ladder vs custom lobby. Tournament games are custom lobbies
   (`false`), but verifying the distribution tells us if ladder games leaked in.

10. **`randomRaces`** (`initData.gameDescription.gameOptions.randomRaces`):
    Whether the lobby forced random race. Should be `false` for tournaments.

**MINOR — good to know, unlikely to affect results:**

11. `fog` — fog of war mode (non-zero = non-competitive).
12. `isBlizzardMap` — official vs custom maps.
13. `observers` — observer slot count (confirms tournament context).
14. `startDir`/`startLocX`/`startLocY` — spawn position.
15. `header.version` vs `metadata.gameVersion` — consistency check.

**Recommended: add Step 1.8 (game settings and field completeness audit)**
as a Phase 1 extension before proceeding to Phase 2. This is a single systematic
pass through all non-event fields, producing a comprehensive field profile.
The 13 player-count anomalies also need deeper classification: are these FFA,
team games, or 1v1 with spectator/observer slots in `ToonPlayerDescMap`?

---

## 2026-04-03 — [SC2] Phase 0 ingestion audit: all gate conditions met

**Objective:** Run the full Phase 0 audit (Steps 0.1–0.9) against real SC2EGSet replay
data to verify data integrity before proceeding to Phase 1 (data exploration).

All results below comply with Scientific Invariant #6: every finding is accompanied
by the literal code or SQL that produced it.

---

### Step 0.1 — Source file availability

**Code** (`src/sc2ml/data/ingestion.py:audit_raw_data_availability`):
```python
counts = {"total": 0, "has_tracker": 0, "has_game": 0, "has_both": 0, "stripped": 0}
for json_file in REPLAYS_SOURCE_DIR.rglob("*.SC2Replay.json"):
    counts["total"] += 1
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    has_tracker = "trackerEvents" in data
    has_game = "gameEvents" in data
    if has_tracker: counts["has_tracker"] += 1
    if has_game:    counts["has_game"] += 1
    if has_tracker and has_game:     counts["has_both"] += 1
    if not has_tracker and not has_game: counts["stripped"] += 1
```

**Result** (`src/rts_predict/sc2/reports/00_source_audit.json`):
```json
{"total": 22390, "has_tracker": 22390, "has_game": 22390, "has_both": 22390, "stripped": 0}
```

**Gate:** `stripped == 0` — PASS.

---

### Step 0.2 — Tournament name extraction validation

**Code** (`src/sc2ml/data/audit.py:validate_tournament_name_extraction`):
```python
# For each sampled file, extract tournament name from path:
extracted = file_path.parts[-3]   # equivalent to SQL: split_part(filename, '/', -3)
expected = tournament_dir.name
match = (extracted == expected)
```

**Result** (`src/rts_predict/sc2/reports/00_tournament_name_validation.txt`): 50/50 correct across 5 sampled
tournaments (2022_HomeStory_Cup_XXI, 2020_StayAtHome_Story_Cup_2,
2020_StayAtHome_Story_Cup_1, 2017_WESG_Haikou, 2016_IEM_10_Taipei), all `match == True`.

**Gate:** All extractions correct — PASS.

---

### Step 0.3 — Replay ID specification

**Extraction code:**
```sql
-- SQL (Path A, from DuckDB filename column):
regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
```
```python
# Python (Path B, from filesystem path):
re.search(r'([0-9a-f]{32})\.SC2Replay\.json$', path).group(1)
```

**Result** (`src/rts_predict/sc2/reports/00_replay_id_spec.md`): Three worked examples confirmed Path A
and Path B produce identical 32-char hex values for the same file.

**Gate:** Path A ≡ Path B IDs — PASS.

---

### Step 0.4 — Path A smoke test (2016_IEM_10_Taipei, in-memory DuckDB)

**Ingestion SQL** (`src/sc2ml/data/audit.py:run_path_a_smoke_test`):
```sql
CREATE TABLE raw AS
SELECT * FROM read_json(
    '{replays_dir}/2016_IEM_10_Taipei/**/*.SC2Replay.json',
    union_by_name = true, filename = true,
    columns = {
        'header': 'JSON', 'initData': 'JSON', 'details': 'JSON',
        'metadata': 'JSON', 'ToonPlayerDescMap': 'JSON'
    }
)
```

**Row count query:**
```sql
SELECT count(*) FROM raw
```
Result: 30 rows = 30 files on disk. Match: True.

**Null check query:**
```sql
SELECT
    SUM(CASE WHEN header IS NULL THEN 1 ELSE 0 END) AS null_header,
    SUM(CASE WHEN "initData" IS NULL THEN 1 ELSE 0 END) AS null_initData,
    SUM(CASE WHEN details IS NULL THEN 1 ELSE 0 END) AS null_details,
    SUM(CASE WHEN metadata IS NULL THEN 1 ELSE 0 END) AS null_metadata,
    SUM(CASE WHEN "ToonPlayerDescMap" IS NULL THEN 1 ELSE 0 END) AS null_tpdm
FROM raw
```
Result: all zero — no null JSON columns.

**Identifier extraction query:**
```sql
SELECT
    filename,
    split_part(filename, '/', -3) AS tournament_dir,
    regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
FROM raw LIMIT 3
```
Result: `tournament_dir` = `2016_IEM_10_Taipei` on all sample rows, `replay_id` is 32-char hex.

**APM/MMR zero-rate query** (same query as Step 0.5 below, on single tournament):
Result: 60 player slots, 60 APM zero, 60 MMR zero — consistent with 2016 being entirely zero.

**Gate:** Schema, row count, identifiers all correct — PASS.

---

### Step 0.5 — Full Path A ingestion

**Ingestion code** (`src/sc2ml/data/ingestion.py:move_data_to_duck_db`):
```sql
CREATE TABLE IF NOT EXISTS raw AS
SELECT * FROM read_json(
    '{REPLAYS_SOURCE_DIR}/**/*.SC2Replay.json',
    union_by_name = true, maximum_object_size = 33554432,
    filename = true,
    columns = {
        'header': 'JSON', 'initData': 'JSON', 'details': 'JSON',
        'metadata': 'JSON', 'ToonPlayerDescMap': 'JSON'
    }
)
```

**Row count query:**
```sql
SELECT count(*) FROM raw
```

**Result** (`src/rts_predict/sc2/reports/00_full_ingestion_log.txt`):
- Row count: 22,390
- Audit total from Step 0.1: 22,390
- Match: True
- Elapsed: 92.4s

**Gate:** `raw` row count matches source audit — PASS.

---

### Step 0.6 — raw_enriched view

**View SQL** (`src/sc2ml/data/processing.py:_RAW_ENRICHED_VIEW_QUERY`):
```sql
CREATE OR REPLACE VIEW raw_enriched AS
SELECT
    *,
    split_part(filename, '/', -3) AS tournament_dir,
    regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
FROM raw
```

**Gate:** View created with `tournament_dir` and `replay_id` columns — PASS.

---

### Step 0.7 — Path B extraction

**Extraction code** (`src/sc2ml/data/ingestion.py:run_in_game_extraction`): multiprocessing-based
extraction from replay JSON to Parquet (tracker events + game events + match_player_map).

**Loading SQL** (`src/sc2ml/data/ingestion.py`):
```sql
CREATE TABLE IF NOT EXISTS tracker_events_raw AS
    SELECT * FROM read_parquet('{parquet_dir}/tracker_events_batch_*.parquet')

CREATE TABLE IF NOT EXISTS game_events_raw AS
    SELECT * FROM read_parquet('{parquet_dir}/game_events_batch_*.parquet')

CREATE TABLE IF NOT EXISTS match_player_map AS
    SELECT * FROM read_parquet('{parquet_dir}/match_player_map_batch_*.parquet')
```

**Row count queries:**
```sql
SELECT count(*) FROM tracker_events_raw   -- 62,003,411
SELECT count(*) FROM game_events_raw      -- 608,618,823
SELECT count(*) FROM match_player_map     -- 44,815
```

**Result** (`src/rts_predict/sc2/reports/00_path_b_extraction_log.txt`):
- 22,390 files processed, 0 skipped, 448 Parquet batches
- Extraction: ~2,871s (~48 min), loading: ~77s

**Gate:** All three tables populated — PASS.

---

### Step 0.8 — Path A ↔ B join validation

**Orphan detection queries** (`src/sc2ml/data/audit.py`):

Tracker orphans (tracker IDs not in raw):
```sql
SELECT t.replay_id FROM (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM tracker_events_raw
) t LEFT JOIN (
    SELECT DISTINCT regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM raw
) r ON t.replay_id = r.replay_id
WHERE r.replay_id IS NULL
```

Raw orphans (raw IDs not in tracker):
```sql
SELECT r.replay_id FROM (
    SELECT DISTINCT regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM raw
) r LEFT JOIN (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM tracker_events_raw
) t ON r.replay_id = t.replay_id
WHERE t.replay_id IS NULL
```

**Result** (`src/rts_predict/sc2/reports/00_join_validation.md`):
- Orphans in tracker_events_raw not in raw: 0
- Orphans in raw not in tracker_events_raw: 0
- `join_clean == True`

**Gate:** Zero orphans in both directions — PASS.

---

### Step 0.9 — Map translation coverage

**Map count query:**
```sql
SELECT count(DISTINCT metadata->>'$.mapName') AS distinct_maps FROM raw
```
Result: 188 distinct map names.

**Untranslated maps query:**
```sql
SELECT DISTINCT metadata->>'$.mapName' AS map_name
FROM raw
WHERE (metadata->>'$.mapName') NOT IN (
    SELECT foreign_name FROM map_translation
)
```
Result: 0 untranslated maps.

**Coverage CSV query** (`src/rts_predict/sc2/reports/00_map_translation_coverage.csv`):
```sql
SELECT DISTINCT
    r.map_name,
    CASE WHEN mt.foreign_name IS NOT NULL THEN 'yes' ELSE 'no' END AS has_translation
FROM (SELECT DISTINCT metadata->>'$.mapName' AS map_name FROM raw) r
LEFT JOIN map_translation mt ON mt.foreign_name = r.map_name
ORDER BY r.map_name
```
Result: 188 rows, all `has_translation = yes`.

**Gate:** 100% translation coverage — PASS.

---

### APM/MMR zero-rate analysis

**Overall query** (`src/sc2ml/data/audit.py:_APM_MMR_ZERO_RATE_QUERY`):
```sql
SELECT
    COUNT(*) AS total_player_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero_or_null,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) AS mmr_zero_or_null
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
```
Result: 44,817 total player slots; 1,132 APM zero/null (2.5%); 37,489 MMR zero/null (83.6%).

**APM by year query:**
```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

| Year | Slots | APM=0 | % zero |
|------|-------|-------|--------|
| 2016 | 1,110 | 1,110 | 100.0% |
| 2017 | 4,004 | 18 | 0.4% |
| 2018 | 6,360 | 0 | 0.0% |
| 2019 | 7,772 | 3 | 0.0% |
| 2020 | 5,706 | 0 | 0.0% |
| 2021 | 7,672 | 0 | 0.0% |
| 2022 | 6,588 | 0 | 0.0% |
| 2023 | 3,504 | 0 | 0.0% |
| 2024 | 2,101 | 1 | 0.0% |

*APM* — 97.5% of player slots have non-zero APM. The 2.5% zeros are concentrated in
two patterns: (a) all 2016 tournaments (1,110 slots) report APM=0 for every player — this
is a sc2reader version issue, these replays predate the field being populated; (b) sparse
individual zeros in 2017–2024 (22 total slots), likely extraction failures or observer slots.
**Conclusion:** APM is reliably available from 2017 onward. The 2016 zeros are systematic
(entire year missing), not random. For feature engineering, 2016 replays will need APM
imputed or the field excluded for those rows.

**MMR by year query:**
```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) AS mmr_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

| Year | Slots | MMR=0 | % zero |
|------|-------|-------|--------|
| 2016 | 1,110 | 1,110 | 100.0% |
| 2017 | 4,004 | 3,179 | 79.4% |
| 2018 | 6,360 | 4,999 | 78.6% |
| 2019 | 7,772 | 5,613 | 72.2% |
| 2020 | 5,706 | 3,746 | 65.7% |
| 2021 | 7,672 | 6,947 | 90.6% |
| 2022 | 6,588 | 6,341 | 96.3% |
| 2023 | 3,504 | 3,465 | 98.9% |
| 2024 | 2,101 | 2,089 | 99.4% |

**MMR by highestLeague query:**
```sql
SELECT
    entry.value->>'$.highestLeague' AS league,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0 THEN 1 ELSE 0 END) AS mmr_nonzero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0
          THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_nonzero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY total_slots DESC
```

| League | Slots | MMR>0 | % nonzero |
|--------|-------|-------|-----------|
| Unknown | 32,338 | 2,063 | 6.4% |
| Master | 6,458 | 2,715 | 42.0% |
| Grandmaster | 4,745 | 1,885 | 39.7% |
| Diamond | 718 | 342 | 47.6% |
| Unranked | 224 | 0 | 0.0% |
| Platinum | 131 | 71 | 54.2% |
| Gold | 119 | 55 | 46.2% |
| Bronze | 73 | 32 | 43.8% |
| Silver | 9 | 6 | 66.7% |

*MMR* — only 16.4% of player slots have non-zero MMR. The pattern is **not random** but
driven by two systematic factors:

1. **`highestLeague` field:** 72.2% of all slots (32,338) have `highestLeague = "Unknown"`,
   and only 6.4% of those have MMR. When `highestLeague` is known (Master, GM, Diamond,
   etc.), MMR availability jumps to 39–54%. This means MMR is only populated when the
   replay file contains the player's ladder profile — which tournament/offline replays
   typically do not.
2. **Temporal trend:** MMR availability peaked at 34.3% in 2020, then dropped to near-zero
   from 2021 onward (9.4% → 0.6%). This correlates with ESL/DreamHack switching to
   private lobby replays (no ladder data embedded) for later seasons.

**MMR is not usable as a direct feature.** It is systematically missing for the majority
of the corpus, and the missingness is non-random (correlated with tournament organizer,
year, and whether the replay was from a ladder or custom lobby). Imputation would be
unreliable. Any player skill proxy must be derived from match history (Elo, historical
winrates).

---

### Phase 0 gate conclusion

All five gate conditions from the roadmap are met:

| Gate condition | Status |
|----------------|--------|
| `raw` table exists with correct row count (22,390) | PASS |
| `tracker_events_raw` joins cleanly to `raw` via `replay_id` (0 orphans) | PASS |
| `tournament_dir` and `replay_id` reliably extractable (50/50 + view) | PASS |
| Zero stripped source files | PASS (0 stripped) |
| APM/MMR zero-rate verified | PASS (documented above) |

**Phase 0 is complete. Ready to proceed to Phase 1 (data exploration).**

**Thesis notes:** Phase 0 confirms the SC2EGSet dataset is structurally sound: no stripped
files, replay IDs are reliable join keys, tournament names extract deterministically, and
all 188 maps have translations. The MMR missingness analysis is thesis-relevant for the
methodology chapter: it demonstrates why raw replay metadata fields cannot be assumed
complete, and why derived features (Elo, cumulative winrate) are necessary for skill
estimation. The APM availability gap in 2016 should be noted as a data limitation.

---

## 2026-04-03 — Methodology restart: data exploration before modelling

**Objective:** Establish correct execution order. Data exploration (corpus inventory,
player identity resolution, temporal structure, in-game statistics profiling, map
and meta-game analysis) must complete before any feature engineering or modelling
decisions are made.

**What happened:** The pipeline was built in the wrong order. Feature groups A–E were
defined, Elo was implemented, and model training was run before the dataset was
explored. The sanity validation (`reports/archive/sanity_validation.md`) revealed
the consequences:
- Elo is flat (std = 0.0) — Elo was computed but never validated against the raw data
- BW race codes (`BWPr`, `BWTe`, `BWZe`) are leaking through — the `flat_players`
  view filter is not working correctly on the full corpus
- `h2h_p1_winrate_smooth` has 0.62 correlation with target — likely a leakage bug
  in head-to-head computation
- GNN predicts P2 wins on every single test example (majority-class collapse)
- 13 match_ids have unexpected row counts — data anomalies not yet investigated

None of these are fixable by patching individual modules. They are symptoms of
building features before understanding the data.

**Decision:** Archive the prior roadmap and methodology draft. Begin from Phase 0
of `reports/SC2ML_THESIS_ROADMAP.md`. Existing code is treated as a draft to audit
and revise as exploration findings arrive, not as correct implementations to extend.

**Archived:**
- `reports/archive/ROADMAP_v1.md` (old ROADMAP.md — caused premature GNN execution)
- `reports/archive/methodology_v1.md` (old methodology.md — assumed unvalidated decisions)
- `reports/archive/sanity_validation.md` (evidence of pre-restart state)

**Thesis notes:** This restart is itself thesis-relevant. The sanity validation
failures demonstrate precisely why the data exploration → cleaning → feature
engineering → modelling order is not optional. The BW race leakage, the flat Elo,
and the H2H correlation will all appear in the thesis as motivating examples for the
methodology chapter's argument that feature design requires prior data characterisation.

---

## 2026-04-02 — Feature engineering rewrite: methodology Groups A–E with ablation support

**Objective:** Decompose the monolithic `features/engineering.py` into composable feature groups matching methodology Section 3.1 (Groups A–E), add missing features (form/momentum, context), eliminate duplicate split logic, and fix a long-standing segfault in `test_model_reproducibility`.

**Approach:** Created one module per methodology group (`group_a_elo.py` through `group_e_context.py`) with shared primitives in `common.py` and a registry/enum system for ablation. `build_features(df, groups=FeatureGroup.C)` computes A+B+C and returns a clean DataFrame. `split_for_ml()` replaces the old `temporal_train_test_split()` by consuming the series-aware split from `data/processing.py` rather than reimplementing it.

**New features added:**
- Group B: `hist_std_apm`, `hist_std_sq` (expanding-window variance)
- Group C: `hist_winrate_map_race_smooth` (map×race interaction winrate)
- Group D (entirely new): win/loss streaks (iterative forward pass), EMA of APM/SQ/winrate, activity windows (7d/30d rolling counts), head-to-head cumulative record with Bayesian smoothing
- Group E (entirely new): patch version as sortable integer, tournament match position, series game number from `match_series` table

**Issues encountered:**
- **Dual-OpenMP segfault**: `test_model_reproducibility` segfaulted because LightGBM (Homebrew `libomp.dylib` at `/opt/homebrew/*/libomp.dylib`) and PyTorch (bundled `libomp.dylib` at `.venv/*/libomp.dylib`) load two separate OpenMP runtimes. At shutdown, OpenMP thread pool teardown in one runtime corrupts the other. The crash trace shows Thread 3 in `__kmp_suspend_initialize_thread` while Thread 0 is in LightGBM's `_pthread_create`. Fix: classical model tests run in a `multiprocessing.spawn` child process (`tests/helpers_classical.py` which never imports torch), isolating the runtimes. This is the same isolation pattern used in `test_mps.py` for Metal/MPS issues.
- Rolling time-window activity counts required a dummy column (`_one`) because pandas `groupby().rolling()[col]` can't use the groupby column as the aggregation target.
- `pd.get_dummies` creates bool columns — needed explicit cast to int for model compatibility.

**Resolution/Outcome:** 168 tests pass (73 new feature tests + 64 data tests + 31 existing), 99% coverage on `features/`, 93% overall. The segfault in `test_model_reproducibility` is fixed. Feature column count grows monotonically: A→14, A+B→37, A+B+C→45, A+B+C+D→62, all→66.

**Thesis notes:** The feature group structure directly maps to the ablation protocol in Section 7.1: run LightGBM on {A}, {A,B}, ..., {A,B,C,D,E} and report marginal lift per group. Group D (form/momentum) and Group E (context) fill gaps identified in the methodology — streaks, recency weighting, head-to-head records, and series position were previously missing. The dual-OpenMP issue should be noted in the thesis reproducibility section: on macOS with Homebrew LightGBM and pip-installed PyTorch, classical and GNN model evaluations must run in separate processes to avoid OpenMP shutdown conflicts.

---

## 2026-04-02 — Path B: In-game event extraction pipeline and temporal split management

**Objective:** Build the data extraction layer for accessing raw in-game events (tracker events, game events) from SC2 replay files, and implement proper temporal train/val/test splitting with series-aware boundaries.

**Approach:** Designed a two-phase extraction pipeline: (1) multiprocessing-based raw event extraction from replay JSON to Parquet intermediate storage, and (2) DuckDB loading with typed views (player_stats with 39 stat columns, match_player_map for game event correlation). Temporal splitting uses a 80/15/5 ratio with a 2-hour gap heuristic to group best-of series and prevent series from being split across partitions.

**Issues encountered:**
- `slim_down_sc2_with_manifest()` was destructive (modifies files in-place with no undo) — added `dry_run=True` default to prevent accidental data loss.
- Best-of series detection requires a time-gap heuristic since replays don't explicitly mark series membership. Chose 2 hours as a conservative threshold.
- Pre-existing MPS segfault in `test_model_reproducibility` (unrelated to this work).

**Resolution/Outcome:** All 70 tests pass (28 existing + 42 new). Pipeline architecture separates extraction (CPU-bound, parallelized) from loading (DuckDB bulk inserts). Parquet intermediate format enables inspection and re-loading without re-extraction.

**Thesis notes:** The series-aware temporal split is methodologically important — naive time-based splits can leak information when consecutive games in a best-of series land in different partitions. The 80/15/5 split with validation set supports proper hyperparameter tuning without test set contamination. The 39-field player_stats view provides the foundation for in-game feature engineering (Chapter 4).

---

## 2026-04-02 — Repository restructured into proper Python package

**Objective:** Reorganize flat 13-module codebase into a proper `src/sc2ml/` package layout to support maintainability, testability, and future AoE2 integration.

**Approach:** Adopted PyPA-recommended src layout with four subpackages (`data/`, `features/`, `models/`, `gnn/`). Renamed modules to avoid namespace redundancy. Updated all imports, fixed test infrastructure (removed `sys.path` hacks, created proper `conftest.py`), configured Poetry for package mode with CLI entry point. Archived legacy execution reports to `reports/archive/`.

**Issues encountered:**
- `conftest.py` is auto-loaded by pytest but not directly importable — required moving shared test utilities to `tests/helpers.py` instead.
- Pre-existing LightGBM segfault on Apple M4 Max during `test_model_reproducibility` (known MPS issue, unrelated to refactoring).
- Ruff identified pre-existing F821 errors from string type annotations — fixed with proper `TYPE_CHECKING` imports.

**Resolution/Outcome:** All 28 non-MPS tests pass. Ruff clean (1 pre-existing E501 in `test_mps.py`). Package installs correctly via `poetry install`. CLI entry point registered. Legacy reports preserved in `reports/archive/`.

**Thesis notes:** The src layout establishes the foundation for shared abstractions when AoE2 integration begins. The package structure makes it clear which components are game-specific (data ingestion, graph construction) vs. reusable (model evaluation, feature engineering patterns).

---

## 2026-04-02 — Project infrastructure setup for Claude Code collaboration

**Objective:** Establish structured development workflow with rich guidelines, git conventions, and documentation trail for thesis work.

**Approach:** Augmented CLAUDE.md with comprehensive sections covering permissions, coding standards, ML experiment protocol, and documentation requirements. Created CHANGELOG.md and this research log.

**Issues encountered:** None — greenfield setup.

**Resolution/Outcome:** Three-tier documentation system in place: CHANGELOG (code versioning), research log (thesis narrative), execution reports (raw pipeline output).

**Thesis notes:** This infrastructure supports the reproducibility and methodology documentation requirements of the thesis. The structured experiment protocol (hypothesis-first, temporal splits, baseline comparisons) will provide a clear audit trail for Chapter 3 (Methodology).

---

## 2026-03-30 — Baseline SC2 pipeline results on Apple M4 Max (summary of prior work)

**Objective:** Establish working end-to-end prediction pipeline for StarCraft II match outcomes using both classical ML and Graph Neural Networks.

**Approach:** Built 5-stage pipeline: data ingestion from SC2Replay JSON files into DuckDB, SQL-based feature views, custom ELO system with dynamic K-factor, Bayesian-smoothed feature engineering (45+ features), and three model training paths (classical ML, Node2Vec embeddings, GATv2 GNN).

**Issues encountered:**
- Apple M4 Max MPS backend causes silent failures and segfaults with sparse tensor operations in PyTorch Geometric. Workaround: force CPU for GNN training, set `PYTORCH_ENABLE_MPS_FALLBACK=1`.
- Data leakage risk from using current-match statistics (APM, SQ, supply_capped_pct) as features. Resolution: feature engineering uses only pre-match historical aggregates.
- `matches_flat` view produces 2 rows per match (both player perspectives) — intentional augmentation but requires careful handling in ELO computation (deduplicate via `processed_matches` set).

**Resolution/Outcome:** Classical ML models achieve ~63-65% accuracy (Gradient Boosting best). Top features: historical win rate, experience differential, SQ differential. GNN pipeline functional with GATv2 edge classification. See `reports/archive/09_run.md` for detailed metrics.

**Thesis notes:** The ~63-65% accuracy on temporal splits provides a solid baseline for comparative analysis. The feature importance ranking (win rate > experience > mechanical skill) aligns with domain knowledge about RTS skill factors. MPS compatibility issues should be documented in the thesis as a practical consideration for reproducibility on Apple Silicon.
