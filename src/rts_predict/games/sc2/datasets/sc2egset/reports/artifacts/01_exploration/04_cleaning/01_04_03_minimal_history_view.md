# Step 01_04_03 -- Minimal Cross-Dataset History View

**Generated:** 2026-04-18
**Dataset:** sc2egset
**Game:** SC2
**Step:** 01_04_03
**Predecessor:** 01_04_02 (Data Cleaning Execution)
**Schema version:** 9-col (ADDENDUM: duration_seconds added 2026-04-18)

## Summary

Created `matches_history_minimal` VIEW -- 9-column player-row-grain projection of
`matches_flat_clean` (2 rows per 1v1 match). Canonical TIMESTAMP temporal dtype
(via TRY_CAST of `details_timeUTC`). Per-dataset-polymorphic faction vocabulary.
Cross-dataset-harmonized substrate for Phase 02+ rating-system backtesting.
Pure non-destructive projection (I9).

ADDENDUM: Added `duration_seconds` BIGINT (column 8) between `won` and `dataset_tag`.
Source: `player_history_all.header_elapsedGameLoops / 22.4` (SC2 Faster loops/sec).
POST_GAME_HISTORICAL -- excluded from PRE_GAME features.

## Schema (9 columns)

| column | dtype | semantics |
|---|---|---|
| `match_id` | VARCHAR | `'sc2egset::'` + 32-char hex replay_id (length = 42) |
| `started_at` | TIMESTAMP | TRY_CAST of details_timeUTC; canonical cross-dataset type |
| `player_id` | VARCHAR | Battle.net toon_id |
| `opponent_id` | VARCHAR | Opposing toon_id |
| `faction` | VARCHAR | Raw race stems `Prot`/`Terr`/`Zerg` (4-char; NOT full names). PER-DATASET POLYMORPHIC |
| `opponent_faction` | VARCHAR | Opposing race (same vocabulary as faction) |
| `won` | BOOLEAN | Focal player's outcome (complementary between the 2 rows) |
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL. Duration in seconds = header_elapsedGameLoops / 22.4. 22.4 loops/sec: SC2 Faster constant (Liquipedia); details.gameSpeed cardinality=1 (research_log.md:424). |
| `dataset_tag` | VARCHAR | Constant `'sc2egset'` |

## Row-count flow

| metric | value |
|---|---|
| Source matches_flat_clean rows | 44418 |
| Source distinct replay_ids | 22209 |
| matches_history_minimal total rows | 44418 |
| distinct match_ids | 22209 |
| matches with exactly 2 rows | 22209 |
| matches with NOT 2 rows | 0 |

## duration_seconds stats (ADDENDUM gates)

| metric | value | gate |
|---|---|---|
| min_duration_seconds | 1 | report only |
| max_duration_seconds | 6073 | <= 86400 (Gate +5) |
| avg_duration_seconds | 719.5 | report only |
| non_null_count | 44418 | report only |
| null_duration_seconds | 0 | report only (Gate +2) |
| non_positive_count | 0 | 0 (Gate +3) |

## Faction vocabulary (per-dataset polymorphic)

| faction | count |
|---|---|
| `Prot` | 16121 |
| `Zerg` | 15527 |
| `Terr` | 12770 |

NOTE: sc2egset faction vocabulary is 4-char race stems (Prot/Terr/Zerg).
Consumers MUST NOT treat faction as a single categorical feature across
datasets without game-conditional encoding.

## Temporal sanity (I3)

| metric | value |
|---|---|
| min_started_at | 2016-01-07 02:21:46.002000 |
| max_started_at | 2024-12-01 23:48:45.251161 |
| null_started_at (TRY_CAST failures) | 0 |
| distinct_started_at | 22164 |

## NULL counts

| column | null count | gate |
|---|---|---|
| match_id | 0 | 0 (GATE) |
| started_at | 0 | report only |
| player_id | 0 | 0 (GATE) |
| opponent_id | 0 | 0 (GATE) |
| won | 0 | 0 (GATE) |
| duration_seconds | 0 | report only (Gate +2) |
| dataset_tag | 0 | 0 (GATE) |
| faction | 0 | report only |
| opponent_faction | 0 | report only |

## Gate verdict

| check | result |
|---|---|
| Row count 44,418 = 2 x 22,209 | PASS |
| Column count 9 (Gate +1) | PASS |
| started_at dtype TIMESTAMP | PASS |
| duration_seconds dtype BIGINT | PASS |
| I5-analog NULL-safe symmetry violations (incl. duration) = 0 | PASS |
| match_id prefix violations = 0; length = 42 | PASS |
| dataset_tag distinct count = 1 | PASS |
| Zero NULLs in match_id / player_id / opponent_id / won / dataset_tag | PASS |
| duration_seconds non-positive = 0 (Gate +3) | PASS |
| duration_seconds max <= 86400 (Gate +5 HALTING) | PASS |
| All assertions pass | PASS |

## Artifact

Validation JSON: `games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json`
