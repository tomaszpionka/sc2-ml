# Step 01_04_01 -- Data Cleaning

**Dataset:** sc2egset
**Date:** 2026-04-16
**Revision:** 1 (incorporates critique BLOCKER F01, WARNINGS W02-W05)
**Invariants:** I3, I6, I7, I9

---

## Summary

Applied non-destructive cleaning to two ESSENTIAL raw tables (replay_players_raw,
replays_meta_raw) and created three DuckDB VIEWs:

1. **`matches_flat`** -- structural JOIN, all rows, no filters
2. **`matches_flat_clean`** -- prediction target VIEW: 1v1 decisive, PRE-GAME only
3. **`player_history_all`** -- player feature history: all replays, IN_GAME metrics retained

## Design Constraint: Prediction Scope != Feature Scope

Prediction targets (matches_flat_clean) are restricted to 1v1 decisive replays
with pre-game features only (I3). Player history features (Phase 02) use
player_history_all which includes all replays including non-1v1 and in-game
metrics for PRIOR matches. I3 prohibits in-game metrics only at TARGET match T.

## CONSORT Flow (REPLAY units)

| Stage | Replays | Rows |
|-------|---------|------|
| Raw (replays_meta_raw) | 22,390 | -- |
| Raw (replay_players_raw) | -- | 44,817 |
| matches_flat (JOIN) | 22,390 | 44,817 |
| After R01 (true_1v1_decisive) | 22,366 | 44,732 |
| R01 excluded (non-1v1 + indecisive) | -24 | -85 |
| After R03 (MMR<0 replay-level) | 22,209 | 44,418 |
| R03 excluded (any MMR<0 player) | -157 | -314 |
| **matches_flat_clean (final)** | **22,209** | **44,418** |
| player_history_all (all replays) | 22,390 | 44,817 |

R03 is a REPLAY-LEVEL exclusion (BLOCKER F01 fix). If any player in a replay
has MMR<0, the entire replay is excluded from prediction scope. Row-level
filtering would orphan the opponent's row, breaking the 2-per-replay invariant.

## Cleaning Registry

| Rule | Condition | Action | Impact |
|------|-----------|--------|--------|
| R01 | Not true_1v1_decisive | EXCLUDE from clean; RETAIN in history | 24 replays |
| R02 | MMR = 0 | FLAG (is_mmr_missing=TRUE) | 37,422 rows (83.66%) |
| R03 | ANY player MMR<0 (replay-level) | EXCLUDE replay from clean; RETAIN in history | 157 replays |
| R04 | selectedRace = '' | NORMALIZE to 'Random' | 1,110 rows (2.48%) |
| R05 | SQ = INT32_MIN | SQ -> NULL | 2 rows (0.0045%) |
| R07 | mapSizeX=0 AND mapSizeY=0 | FLAG + NULL | 273 replays |
| R08 | handicap = 0 | FLAG (is_handicap_anomalous=TRUE) | 2 rows (0.0045%) |

Note: R06 (APM=0) is NOT a cleaning rule. APM=0 investigation (T06) is
documentation-only per W05. APM is excluded from matches_flat_clean (I3)
and retained in player_history_all as a valid historical observation.

## Columns Excluded from matches_flat_clean (I3 + W02 + W03 + W05)

- APM, SQ, supplyCappedPercent, header_elapsedGameLoops (I3: IN_GAME)
- details_gameSpeed, gd_gameSpeed (W02: constant, cardinality=1)
- gd_isBlizzardMap (W03: duplicate of details_isBlizzardMap, mismatch=0)
- color_a, color_b, color_g, color_r (cosmetic)

## Columns Retained in player_history_all (IN_GAME_HISTORICAL)

- APM -- actions per minute (in-game metric, valid for prior match history)
- SQ -- spending quotient (R05: INT32_MIN -> NULL)
- supplyCappedPercent -- % game time supply-blocked
- header_elapsedGameLoops -- game duration

## Validation Results

- matches_flat: 44,817 rows, 22,390 replays, 0 NULL replay_ids
- isBlizzardMap mismatch: 0 (gd_isBlizzardMap identical to details_isBlizzardMap)
- gameSpeed cardinality: 1 (both details_gameSpeed and gd_gameSpeed)
- matches_flat_clean: 44,418 rows, 22,209 replays
- Result distribution: 50.0% Win / 50.0% Loss (perfect symmetry)
- Symmetry violations: 0 (every replay has exactly 1 Win + 1 Loss row)
- I3 + W02 + W03 + W05 column exclusion assertion: PASSED
- player_history_all: 44,817 rows, 22,390 replays
- SQ sentinel in player_history_all: 0
- CONSORT arithmetic verified

## Critique Fixes Applied

- **F01 (BLOCKER):** R03 replay-level CTE (mmr_valid) -- 157 replays excluded
- **W02:** details_gameSpeed, gd_gameSpeed excluded (verified constant)
- **W03:** gd_isBlizzardMap excluded (verified identical, mismatch=0)
- **W04:** NULLIF wrapper on regexp_extract (null_replay_id=0)
- **W05:** No APM-derived columns in any VIEW
