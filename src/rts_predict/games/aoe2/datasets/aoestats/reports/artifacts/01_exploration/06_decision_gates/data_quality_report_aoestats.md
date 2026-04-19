# Data Quality Report — aoestats

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## 1. CONSORT-Style Row Flow

| Stage | Description | Rows/matches | Excluded |
|---|---|---|---|
| S0 All matches | Raw matches from Parquet files | 30,690,651 | — |
| S1 Has players | R00: matches with player data present | 30,477,761 | 212,890 |
| S2 Structural 1v1 | R01: `player_count=2` filter | 18,438,769 | 12,038,992 |
| S3 Ranked 1v1 | R02: `leaderboard='random_map'` + distinct team_ids | 17,815,944 | 622,825 |
| S4 Final `matches_1v1_clean` | R03: consistent winner (excluded 997 inconsistent) | 17,814,947 | 997 |
| `player_history_all` | All leaderboards; no row filter | 107,626,399 | N/A |

**CONSORT note:** The 28 corrupt-duration matches identified in 01_04_02 addendum are retained in
`matches_1v1_clean` with `is_duration_suspicious=TRUE`; they are NOT row-excluded.
Duration is POST_GAME_HISTORICAL and does not affect the prediction label `team1_wins`.

## 2. Cleaning Rule Registry

| Rule | Condition | Action | Impact |
|---|---|---|---|
| R00 | profile_id != -1 / player data present | Retain only valid players | 212,890 rows excluded |
| R01 | player_count=2 (structural 1v1) | Remove non-2-player matches | 12,038,992 rows excluded |
| R02 | leaderboard='random_map' scope | Restrict to ranked 1v1 ladder | 622,825 rows excluded |
| R03 | consistent winner per match | Remove inconsistent results | 997 rows excluded |
| DS-AOESTATS-01 | old_rating=0 sentinel | NULLIF + is_unrated flag | ~2.3M rows modified |
| DS-AOESTATS-02 | avg_elo=0 sentinel | NULLIF | 0 rows excluded |
| DS-AOESTATS-03 | raw_match_type redundant | DROP column | -1 col matches_1v1_clean |
| DS-AOESTATS-04 | constants (leaderboard, num_players) | DROP 2 columns | -2 cols |
| DS-AOESTATS-08 | overviews_raw singleton | OUT-OF-SCOPE declaration | registry only |
| [PRE-canonical_slot] | team=1 skill-correlated (W3) | Flag; no row drop | BACKLOG F1 pending |

## 3. Route-Decision Table

| Column | NULL% | Mechanism | Route | Rule |
|---|---|---|---|---|
| `old_rating` (p0/p1) | ~13% | MNAR (unrated players) | NULLIF + is_unrated flag | DS-AOESTATS-01 |
| `avg_elo` | ~0.0007% | MAR | NULLIF | DS-AOESTATS-02 |
| `raw_match_type` | 7055 NULLs (MCAR) | redundant | DROP | DS-AOESTATS-03 |
| `leaderboard` | 0% | constant (n_distinct=1) | DROP | DS-AOESTATS-08 |
| `num_players` | 0% | constant (n_distinct=1) | DROP | DS-AOESTATS-08 |

## 4. Post-Cleaning Summary

| View | Rows | Columns |
|---|---|---|
| `matches_1v1_clean` | 17,814,947 | 20 (after drops/adds) |
| `player_history_all` | 107,626,399 | 14 |
| `matches_history_minimal` | 35,629,894 player rows | 9 (Phase-02-ready) |

**Validation assertions:**
- Final matches_1v1_clean: 17,814,947 = expected ✓
- player_history_all: 107,626,399 rows (all leaderboards)
- 14 [PRE-canonical_slot] columns flagged in data dictionary
