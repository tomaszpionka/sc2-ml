# Data Quality Report — sc2egset

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced by:** 01_06_02 (Phase 01 Decision Gates)
**Date:** 2026-04-19
**Source artifacts:** 01_04_01_data_cleaning.json, 01_04_02_post_cleaning_validation.json

---

## 1. CONSORT-Style Row Flow

| Stage | Description | Rows (player-grain) | Replays | Excluded |
|---|---|---|---|---|
| S0 Raw | All `.SC2Replay.json` files ingested | 44,817 | 22,390 | — |
| S1 After R01 | Non-2-player replays removed (R01: `player_count != 2`) | 44,732 | 22,366 | 85 rows / 24 replays |
| S2 After R03 | Mixed-result replays removed (R03: Undecided/Tie excluded) | 44,418 | 22,209 | 314 rows / 157 replays |
| Final `matches_flat_clean` | After column-only cleaning (01_04_02) | 44,418 | 22,209 | column changes only |

**`player_history_all`:** 44,817 rows (includes Undecided/Tie matches; not row-filtered).

**CONSORT balance check:** 44,817 - 85 - 314 = 44,418 ✓

---

## 2. Cleaning Rule Registry

All rules traceable to `01_04_01_data_cleaning.json` and `01_04_02_post_cleaning_validation.json`.

| Rule ID | Condition | Action | Impact |
|---|---|---|---|
| R01 | player_count != 2 | Remove replay | 24 replays / 85 rows |
| R03 | result NOT IN ('Win','Loss') | Remove replay (Undecided/Tie) | 157 replays / 314 rows |
| non_1v1_indecisive_exclusion | Replay is not true_1v1_decisive (player_count != 2 OR result | EXCLUDE from matches_flat_clean; RETAIN in player_history_al | 24 replays excluded from prediction scope, retained in history |
| unrated_player_flag | MMR = 0 | FLAG (is_mmr_missing = TRUE) | 37,422 rows in true_1v1_decisive scope |
| anomalous_mmr_exclusion | ANY player in replay has MMR < 0 (replay-level exclusion) | EXCLUDE entire replay from matches_flat_clean; RETAIN in pla | 157 replays excluded from prediction scope |
| random_race_normalisation | selectedRace = '' (empty string) | NORMALISE to 'Random' in both VIEWs | 1,110 rows (2.48%) |
| sq_sentinel_correction | SQ = -2147483648 (INT32_MIN) | SQ -> NULL. SQ excluded from matches_flat_clean per temporal | 2 rows (0.0045%) |
| map_size_missing_flag | gd_mapSizeX = 0 AND gd_mapSizeY = 0 | FLAG (mapSize -> NULL; is_map_size_missing = TRUE in both VI | 273 replays (~554 rows) |
| handicap_anomaly_flag | handicap = 0 | FLAG (is_handicap_anomalous = TRUE) | 2 rows (0.0045%) |
| drop_mmr_high_sentinel | Always (column drop) | DROP MMR from matches_flat_clean and player_history_all | -1 col each VIEW; rated subset signal preserved via is_mmr_missing |
| drop_highestleague_mid_sentinel | Always | DROP highestLeague from both VIEWs | -1 col each VIEW |
| drop_clantag_mid_sentinel | Always | DROP clanTag from both VIEWs | -1 col each VIEW |
| add_is_decisive_result | result IN ('Win','Loss') | ADD is_decisive_result BOOLEAN to player_history_all | +1 col player_history_all |
| drop_mapsize_pred_view | Always | DROP gd_mapSizeX/Y/is_map_size_missing from matches_flat_cle | -3 cols matches_flat_clean |

---

## 3. Route-Decision Table (NULL/Missing ≥1%)

| Column | NULL% | Mechanism | Route | Rule |
|---|---|---|---|---|
| `mmr` | 83.95% | MNAR (professional not rated) | DROP + add `is_mmr_missing` flag | DS-SC2-01 (01_04_02) |
| `highestLeague` | 72.04% | MAR | DROP (non-primary feature) | DS-SC2-02 (01_04_02) |
| `clanTag` | 73.93% | MAR | DROP (`isInClan` retained) | DS-SC2-03 (01_04_02) |
| `APM` (= 0 sentinel) | 2.53% | MNAR (parse failure) | NULLIF + `is_apm_unparseable` flag | DS-SC2-10 (01_04_02) |
| `gd_mapSizeX/Y` | variable | parse artifacts | NULL-correct + drop from matches_flat_clean | DS-SC2-06 |
| `handicap` | near-constant | 2/44k anomalies | DROP | DS-SC2-09 |

---

## 4. Post-Cleaning Summary

| View | Rows | Replays | Columns |
|---|---|---|---|
| `matches_flat_clean` | 44,418 | 22,209 | 30 (after drops/adds from 01_04_02) |
| `player_history_all` | 44,817 | 22,390 | 37 (includes IN_GAME_HISTORICAL cols) |
| `matches_history_minimal` | 44,418 | 22,209 | 9 (Phase-02-ready cross-dataset view) |

**Validation assertions (from 01_04_02_post_cleaning_validation.json):**
- Column-only cleaning step for 01_04_02: row counts unchanged from S2.
- R01 and R03 row drops verified against raw replay counts.
- All 12 constant `go_*` columns dropped (DS-SC2-08).
- APM sentinel → NULL applied to 1,132 rows in player_history_all.
