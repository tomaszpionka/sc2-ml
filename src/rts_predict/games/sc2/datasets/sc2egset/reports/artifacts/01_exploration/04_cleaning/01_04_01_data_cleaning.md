# Step 01_04_01 -- Data Cleaning

**Dataset:** sc2egset
**Date:** 2026-04-16
**Revision:** 1 (incorporates replay-level MMR exclusion, regexp_extract NULLIF guard, constant column exclusions, and APM=0 as documentation-only)
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
| After 1v1 decisive filter | 22,366 | 44,732 |
| Excluded (non-1v1 + indecisive) | -24 | -85 |
| After MMR<0 replay-level exclusion | 22,209 | 44,418 |
| Excluded (any MMR<0 player) | -157 | -314 |
| **matches_flat_clean (final)** | **22,209** | **44,418** |
| player_history_all (all replays) | 22,390 | 44,817 |

MMR<0 exclusion is replay-level: if any player in a replay has MMR<0, the entire
replay is excluded from prediction scope. Row-level filtering would orphan the
opponent's row, breaking the 2-per-replay invariant.

## Cleaning Registry

| Rule | Condition | Action | Impact |
|------|-----------|--------|--------|
| Exclusion: non-1v1 or indecisive | Not true_1v1_decisive | EXCLUDE from clean; RETAIN in history | 24 replays |
| Flag: unrated player | MMR = 0 | FLAG (is_mmr_missing=TRUE) | 37,422 rows (83.66%) |
| Exclusion: anomalous MMR | ANY player MMR<0 (replay-level) | EXCLUDE replay from clean; RETAIN in history | 157 replays |
| Normalise: random race | selectedRace = '' | NORMALISE to 'Random' | 1,110 rows (2.48%) |
| Correct: SQ sentinel | SQ = INT32_MIN | SQ -> NULL | 2 rows (0.0045%) |
| Flag: map size missing | mapSizeX=0 AND mapSizeY=0 | FLAG + NULL | 273 replays |
| Flag: handicap anomalous | handicap = 0 | FLAG (is_handicap_anomalous=TRUE) | 2 rows (0.0045%) |

Note: APM=0 is NOT a cleaning rule. APM=0 investigation is documentation-only.
APM is excluded from matches_flat_clean (temporal discipline) and retained in
player_history_all as a valid historical observation.

## Columns Excluded from matches_flat_clean

- APM, SQ, supplyCappedPercent, header_elapsedGameLoops (in-game metrics — temporal discipline)
- details_gameSpeed, gd_gameSpeed (constant across all replays, cardinality=1)
- gd_isBlizzardMap (duplicate of details_isBlizzardMap — zero mismatches confirmed)
- color_a, color_b, color_g, color_r (cosmetic)

## Columns Retained in player_history_all (in-game historical signals)

- APM -- actions per minute (in-game metric, valid for prior match history)
- SQ -- spending quotient (parse-failure sentinel INT32_MIN corrected to NULL)
- supplyCappedPercent -- % game time supply-blocked
- header_elapsedGameLoops -- game duration

## Validation Results

- matches_flat: 44,817 rows, 22,390 replays, 0 NULL replay_ids
- isBlizzardMap mismatch: 0 (gd_isBlizzardMap identical to details_isBlizzardMap)
- gameSpeed cardinality: 1 (both details_gameSpeed and gd_gameSpeed)
- matches_flat_clean: 44,418 rows, 22,209 replays
- Result distribution: 50.0% Win / 50.0% Loss (perfect symmetry)
- Symmetry violations: 0 (every replay has exactly 1 Win + 1 Loss row)
- Column exclusion assertion (temporal discipline + constant/duplicate cols): PASSED
- player_history_all: 44,817 rows, 22,390 replays
- SQ sentinel in player_history_all: 0
- CONSORT arithmetic verified

## Changes from Initial Design

- Replay-level MMR exclusion via CTE (mmr_valid) -- 157 replays excluded
- details_gameSpeed, gd_gameSpeed excluded (verified constant across all replays)
- gd_isBlizzardMap excluded (verified identical to details_isBlizzardMap, mismatch=0)
- NULLIF wrapper applied to regexp_extract in matches_flat JOIN (null_replay_id=0 confirmed)
- No APM-derived columns added to any VIEW

## NULL Audit

### matches_flat_clean

| Metric | Value |
|--------|-------|
| Total rows | 44,418 |
| Columns audited | 49 |
| Columns with NULLs | 2 |
| Columns fully populated | 47 |

Zero-NULL assertions passed: replay_id, toon_id, result.

### player_history_all

| Metric | Value |
|--------|-------|
| Total rows | 44,817 |
| Columns audited | 51 |
| Columns with NULLs | 3 |
| Columns fully populated | 48 |

Zero-NULL assertions passed: replay_id, toon_id, result.
Expected NULLs: SQ (R05 sentinel correction — 2 rows).

## Missingness Ledger

Full-coverage ledger (Option B): one row per column per VIEW. Zero-missingness columns
tagged mechanism=N/A / recommendation=RETAIN_AS_IS. Constant columns tagged mechanism=N/A /
recommendation=DROP_COLUMN. Target columns with missingness tagged EXCLUDE_TARGET_NULL_ROWS.

Framework: Rubin (1976) / Little & Rubin (2019) MCAR/MAR/MNAR taxonomy.
Thresholds (5/40/80%) are operational starting heuristics — van Buuren (2018) warns
against rigid global thresholds.

### Missingness Ledger — matches_flat_clean

| column                   | dtype   |   n_null |   n_sentinel |   pct_missing_total | mechanism   | recommendation           |
|:-------------------------|:--------|---------:|-------------:|--------------------:|:------------|:-------------------------|
| gd_mapSizeY              | BIGINT  |      576 |            0 |              1.2968 | MCAR        | RETAIN_AS_IS             |
| gd_mapSizeX              | BIGINT  |      542 |            0 |              1.2202 | MCAR        | RETAIN_AS_IS             |
| replay_id                | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_battleNet             | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| details_isBlizzardMap    | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| details_timeUTC          | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| header_version           | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_baseBuild       | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_dataBuild       | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_gameVersion     | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_advancedSharedControl | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_amm                   | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_clientDebugFlags      | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| gd_mapAuthorName         | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_competitive           | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_cooperative           | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_fog                   | BIGINT  |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_heroDuplicatesAllowed | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_lockTeams             | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_noVictoryOrDefeat     | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_observers             | BIGINT  |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_practice              | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_randomRaces           | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_teamsTogether         | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| gd_mapFileSyncChecksum   | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| is_map_size_missing      | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| gd_maxPlayers            | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| handicap                 | INTEGER |        0 |            2 |              0.0045 | MCAR        | CONVERT_SENTINEL_TO_NULL |
| toon_id                  | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| nickname                 | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| playerID                 | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| userID                   | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| result                   | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| MMR                      | INTEGER |        0 |        37290 |             83.9525 | MAR         | DROP_COLUMN              |
| is_mmr_missing           | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| race                     | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| selectedRace             | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| is_handicap_anomalous    | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| filename                 | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| region                   | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| realm                    | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| highestLeague            | VARCHAR |        0 |        31997 |             72.0361 | MAR         | DROP_COLUMN              |
| isInClan                 | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| clanTag                  | VARCHAR |        0 |        32840 |             73.934  | MAR         | DROP_COLUMN              |
| startDir                 | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| startLocX                | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| startLocY                | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_mapName         | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_userDifficulty        | BIGINT  |        0 |            0 |              0      | N/A         | DROP_COLUMN              |

**Columns: 49 | With missingness: 6 | Constants (DROP_COLUMN): 15**

### Missingness Ledger — player_history_all

| column                   | dtype   |   n_null |   n_sentinel |   pct_missing_total | mechanism   | recommendation           |
|:-------------------------|:--------|---------:|-------------:|--------------------:|:------------|:-------------------------|
| gd_mapSizeY              | BIGINT  |      606 |            0 |              1.3522 | MCAR        | RETAIN_AS_IS             |
| gd_mapSizeX              | BIGINT  |      554 |            0 |              1.2361 | MCAR        | RETAIN_AS_IS             |
| SQ                       | INTEGER |        2 |            0 |              0.0045 | MCAR        | RETAIN_AS_IS             |
| details_isBlizzardMap    | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| gd_mapAuthorName         | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| gd_mapFileSyncChecksum   | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| details_timeUTC          | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| header_version           | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_baseBuild       | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_dataBuild       | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_gameVersion     | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_advancedSharedControl | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_amm                   | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_battleNet             | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_clientDebugFlags      | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_competitive           | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_cooperative           | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_fog                   | BIGINT  |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_heroDuplicatesAllowed | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_lockTeams             | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_noVictoryOrDefeat     | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_observers             | BIGINT  |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_practice              | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_randomRaces           | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| go_teamsTogether         | BOOLEAN |        0 |            0 |              0      | N/A         | DROP_COLUMN              |
| gd_maxPlayers            | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| replay_id                | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| filename                 | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| metadata_mapName         | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| toon_id                  | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| nickname                 | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| playerID                 | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| userID                   | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| result                   | VARCHAR |        0 |           26 |              0.058  | MNAR        | EXCLUDE_TARGET_NULL_ROWS |
| MMR                      | INTEGER |        0 |        37489 |             83.6491 | MAR         | DROP_COLUMN              |
| is_mmr_missing           | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| race                     | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| selectedRace             | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| handicap                 | INTEGER |        0 |            2 |              0.0045 | MCAR        | CONVERT_SENTINEL_TO_NULL |
| region                   | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| realm                    | VARCHAR |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| highestLeague            | VARCHAR |        0 |        32338 |             72.1557 | MAR         | DROP_COLUMN              |
| isInClan                 | BOOLEAN |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| clanTag                  | VARCHAR |        0 |        33210 |             74.1013 | MAR         | DROP_COLUMN              |
| APM                      | INTEGER |        0 |         1132 |              2.5258 | MAR         | CONVERT_SENTINEL_TO_NULL |
| supplyCappedPercent      | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| header_elapsedGameLoops  | BIGINT  |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| startDir                 | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| startLocX                | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| startLocY                | INTEGER |        0 |            0 |              0      | N/A         | RETAIN_AS_IS             |
| go_userDifficulty        | BIGINT  |        0 |            0 |              0      | N/A         | DROP_COLUMN              |

**Columns: 51 | With missingness: 9 | Constants (DROP_COLUMN): 15**

## Decisions Surfaced for Downstream Cleaning (01_04_02+)

The following open questions are surfaced by this audit for 01_04_02+ to resolve.
The audit RECOMMENDS but does NOT decide or execute. All rates below are from the VIEWs
(filtered scope); raw-table rates differ.

| ID | Column | Observed pct_missing_total | Question |
|----|--------|---------------------------|----------|
| DS-SC2-01 | MMR (sentinel=0) | ~83.66% | Convert MMR=0 to NULL + drop (Rule S4 >80%), OR retain as 'unranked' encoding + is_mmr_missing, OR rated-subset sensitivity arm? |
| DS-SC2-02 | highestLeague (sentinel='Unknown') | ~72.16% | Drop entirely, OR retain 'Unknown' as its own category? |
| DS-SC2-03 | clanTag (sentinel='') | ~74% | Drop (non-predictive at this rate), OR retain as is_in_clan boolean? |
| DS-SC2-04 | result in player_history_all (Undecided/Tie) | runtime | How to handle NULL-target rows in player_history_all for win-rate feature computation? |
| DS-SC2-05 | selectedRace (sentinel='') | 0% in VIEWs | Already normalised to 'Random' in VIEWs; audit confirms zero residual. |
| DS-SC2-06 | gd_mapSizeX / gd_mapSizeY (sentinel=0) | n_sentinel=0 in VIEWs | VIEWs CASE-WHEN to NULL; audit confirms ledger reports converted NULLs. |
| DS-SC2-07 | gd_mapAuthorName | runtime | Drop as non-predictive metadata? |
| DS-SC2-08 | go_* constants | runtime | Confirm which go_* are constant in each VIEW; drop in 01_04_02+? |
| DS-SC2-09 | handicap (sentinel=0, 2 rows) | ~0.0045% | NULLIF + listwise deletion (Rule S3), OR retain is_anomalous_handicap flag? (carries_semantic_content=True) |
| DS-SC2-10 | APM (sentinel=0, ~2.53%) | ~2.53% in hist | Convert to NULL via NULLIF, OR retain as encoding for 'unparseable game'? (carries_semantic_content=True) |

Ledger artifacts: `artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` (CSV)
and `artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json` (JSON).
