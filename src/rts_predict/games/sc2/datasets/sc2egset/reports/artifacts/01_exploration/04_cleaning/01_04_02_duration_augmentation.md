# Step 01_04_02 ADDENDUM -- Duration Augmentation (matches_flat_clean 28 → 30)

**Generated:** 2026-04-18
**Dataset:** sc2egset
**Step:** 01_04_02 ADDENDUM -- duration_seconds + is_duration_suspicious

## Summary

ADDENDUM to 01_04_02. Extends `matches_flat_clean` VIEW from 28 → 30 columns by adding:
- `duration_seconds` BIGINT (POST_GAME_HISTORICAL): game duration in seconds.
- `is_duration_suspicious` BOOLEAN (POST_GAME_HISTORICAL): TRUE where duration_seconds > 86,400s.

Source: `player_history_all.header_elapsedGameLoops` aggregated per `replay_id`, divided by 22.4
(SC2 "Faster" loops/sec constant, I7). No row changes (I9). STEP_STATUS stays `complete`.

## CONSORT Column-Count Flow

| VIEW | Cols before addendum | Cols added | Cols after addendum |
|---|---|---|---|
| matches_flat_clean | 28 | 2 | 30 |

## Duration Stats (sc2egset)

| Stat | Value |
|---|---|
| min_seconds | 1 |
| p50_seconds | 651.0 |
| p99_seconds | 1876.0 |
| max_seconds | 6073 |
| null_count | 0 |
| suspicious_count (>86400s) | 0 |

## I7 Provenance (22.4 loops/sec)

- `details.gameSpeed` cardinality=1 in sc2egset (W02 census, research_log.md:424)
- Blizzard SC2 "Faster" game speed = 22.4 loops/sec (official documentation)
- Established in 01_04_03 ADDENDUM (matches_history_minimal duration_seconds derivation)

## I8 Provenance (86,400s threshold)

Cross-dataset canonical sanity bound (~25x p99 for sc2egset: p99=1,876s, max=6,073s).
Identical across sc2egset, aoestats, aoe2companion per plan A1 + I8 cross-dataset comparability.

## Validation Results

| Assertion | Status |
|---|---|
| gate_1_col_count_30 | PASS |
| gate_2_last_col_duration_seconds_bigint | PASS |
| gate_2_last_col_is_duration_suspicious_boolean | PASS |
| gate_3_row_count_44418 | PASS |
| gate_4_null_duration_seconds_zero | PASS |
| gate_5_max_duration_le_1e9 | PASS |
| gate_6_symmetry_violations_zero | PASS |
| gate_6b_suspicious_count_zero | PASS |
| regression_zero_null_replay_id | PASS |
| regression_zero_null_toon_id | PASS |
| regression_zero_null_result | PASS |
| regression_zero_non_decisive | PASS |
| regression_i5_symmetry | PASS |
| regression_i3_no_ingame_cols | PASS |

## SQL Queries (Invariant I6)

All DDL and assertion SQL stored verbatim in `01_04_02_duration_augmentation.json`
under the `sql_queries` key.
