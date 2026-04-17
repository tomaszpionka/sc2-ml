# Step 01_04_02 -- Data Cleaning Execution: Post-Cleaning Validation

**Generated:** 2026-04-17
**Dataset:** aoestats
**Step:** 01_04_02 -- Act on DS-AOESTATS-01..08

## Summary

Step 01_04_02 applies all 8 cleaning decisions (DS-AOESTATS-01..08) surfaced by the
01_04_01 missingness audit. Both VIEWs are replaced via CREATE OR REPLACE DDL.
No raw tables are modified (Invariant I9). Row counts are unchanged (column-only
cleaning step). All validation assertions pass.

**Final column counts:** matches_1v1_clean 21 -> 20 (drop 3, add 2, modify 3);
player_history_all 13 -> 14 (drop 0, add 1, modify 1).

## Per-DS Resolutions

| DS ID | Column | Decision |
|---|---|---|
| DS-AOESTATS-01 | team_0_elo, team_1_elo | NO-OP (RETAIN_AS_IS). F1 override: sentinel=-1 absent in 1v1 ranked scope. |
| DS-AOESTATS-02 | p0_old_rating, p1_old_rating (matches_1v1_clean); old_rating (player_history_all) | NULLIF(old_rating, 0) + ADD is_unrated flag in both VIEWs. mirrors sc2egset DS-SC2-10 pattern. |
| DS-AOESTATS-03 | avg_elo | NULLIF(avg_elo, 0) AS avg_elo. No companion flag (p0/p1_is_unrated covers semantic). |
| DS-AOESTATS-04 | raw_match_type | DROP_COLUMN override (NOTE-1 critique fix): n_distinct=1 in non-NULL scope overrides RETAIN_AS_IS. Column is informationally redundant with upstream leaderboard + player_count filters. |
| DS-AOESTATS-05 | team1_wins | NO-OP (RETAIN_AS_IS). F1 override: zero NULLs; decisive by upstream filter. |
| DS-AOESTATS-06 | winner | NO-OP (RETAIN_AS_IS). Zero NULLs confirmed. |
| DS-AOESTATS-07 | overviews_raw (table) | FORMALLY DECLARED OUT-OF-ANALYTICAL-SCOPE in cleaning registry. No DDL change. |
| DS-AOESTATS-08 | leaderboard, num_players | DROP leaderboard + num_players from matches_1v1_clean only. RETAIN in player_history_all. |

## Cleaning Registry (new rules in 01_04_02)

| Rule ID | Condition | Action | Justification | Impact |
|---|---|---|---|---|
| drop_matches_1v1_clean_constants | n_distinct=1 in matches_1v1_clean scope | DROP leaderboard and num_players from matches_1v1_clean | DS-AOESTATS-08: ledger constants-detection (n_distinct=1 across 17,814,947 rows); zero information content. Mirror of sc2egset DS-SC2-08 pattern. | -2 cols matches_1v1_clean |
| drop_raw_match_type_redundant | n_distinct=1 in non-NULL filtered scope of matches_1v1_clean | DROP raw_match_type from matches_1v1_clean | DS-AOESTATS-04: NOTE-1 critique fix -- constants-detection overrides RETAIN_AS_IS; redundant with upstream leaderboard='random_map' + COUNT(*)=2 filters; 7,055 NULLs are MCAR but contribute zero signal beyond what upstream filter encodes. | -1 col matches_1v1_clean |
| nullif_old_rating_indicator | old_rating = 0 in either VIEW | NULLIF(old_rating, 0) + ADD is_unrated BOOLEAN flag in both VIEWs | DS-AOESTATS-02: low-rate sentinel with semantic content; NULLIF makes IS NULL semantics consistent for Phase 02 imputation; is_unrated flag preserves missingness-as-signal (sklearn MissingIndicator pattern). | matches_1v1_clean: 0 dropped / +2 (p0_is_unrated, p1_is_unrated) / 2 modified; player_history_all: 0 dropped / +1 (is_unrated) / 1 modified |
| nullif_avg_elo | avg_elo = 0 in matches_1v1_clean | NULLIF(avg_elo, 0) AS avg_elo | DS-AOESTATS-03: lowest sentinel rate (0.0007%); NULLIF makes column safe for Phase 02 averaging operations without 0-sentinel skewing means. p0_is_unrated/p1_is_unrated already convey the unrated subgroup membership. | 1 modified col, 0 added |
| declare_overviews_oos | Always (documentation) | OVERVIEWS_RAW formally declared out-of-analytical-scope in this registry | DS-AOESTATS-07: singleton metadata table (1 row), not used by any VIEW. Registry declaration prevents inadvertent feature-source use in Phase 02+. | None (registry-only resolution) |

## CONSORT Column-Count Flow

| VIEW | Cols before | Cols dropped | Cols added | Cols modified | Cols after |
|---|---|---|---|---|---|
| matches_1v1_clean | 21 | 3 | 2 | 3 (avg_elo, p0_old_rating, p1_old_rating NULLIF) | 20 |
| player_history_all | 13 | 0 | 1 | 1 (old_rating NULLIF) | 14 |

## CONSORT Match-Count Flow (column-only -- no row changes)

| Stage | matches_1v1_clean rows | matches_1v1_clean game_ids | player_history_all rows |
|---|---|---|---|
| Before 01_04_02 (post 01_04_01) | 17,814,947 | 17,814,947 | 107,626,399 |
| After 01_04_02 column-only changes | 17,814,947 | 17,814,947 | 107,626,399 |

## Subgroup Impact (Jeanselme et al. 2024)

| Affected column | Source decision | Subgroup most affected | Impact |
|---|---|---|---|
| leaderboard (dropped from matches_1v1_clean) | DS-AOESTATS-08 | Constant in scope -- none affected | Information neutral (n_distinct=1 in 17,814,947 rows); no subgroup differentially affected |
| num_players (dropped from matches_1v1_clean) | DS-AOESTATS-08 | Constant in scope -- none affected | Information neutral (n_distinct=1 in 17,814,947 rows); no subgroup differentially affected |
| raw_match_type (dropped from matches_1v1_clean) | DS-AOESTATS-04 | n_distinct=1 in non-NULL filtered scope | Information neutral; 7,055 NULL rows remain in VIEW (MCAR <5% boundary per Schafer & Graham 2002) |
| p0_old_rating NULLIF + p0_is_unrated | DS-AOESTATS-02 | Unrated-team0 players (4730 of 17,814,947 = 0.0266%) | Sentinel->NULL converts 0-rating to missing-rating; p0_is_unrated flag preserves rated/unrated signal |
| p1_old_rating NULLIF + p1_is_unrated | DS-AOESTATS-02 | Unrated-team1 players (188 of 17,814,947 = 0.0011%) | Same as p0 -- symmetric NULLIF+flag applied |
| old_rating NULLIF + is_unrated (player_history_all) | DS-AOESTATS-02 | Unrated-player rows (5937 of 107,626,399 = 0.0055%) | Sentinel->NULL; is_unrated flag preserves signal for Phase 02 win-rate denominator selection |
| avg_elo NULLIF | DS-AOESTATS-03 | Matches with >=1 unrated player (118 of 17,814,947 = 0.0007%) | Sentinel->NULL eliminates 0-skew in ELO averaging operations; p0/p1_is_unrated already capture the subgroup |

## Validation Results

| Assertion | Status |
|---|---|
| col_count_clean_20 | PASS |
| col_count_hist_14 | PASS |
| zero_null_game_id_clean | PASS |
| zero_null_started_timestamp_clean | PASS |
| zero_null_p0_profile_id_clean | PASS |
| zero_null_p1_profile_id_clean | PASS |
| zero_null_p0_winner_clean | PASS |
| zero_null_p1_winner_clean | PASS |
| zero_null_team1_wins_clean | PASS |
| zero_null_profile_id_hist | PASS |
| zero_null_game_id_hist | PASS |
| zero_null_started_timestamp_hist | PASS |
| zero_null_winner_hist | PASS |
| no_duplicate_game_id | PASS |
| no_inconsistent_winner_rows | PASS |
| team1_wins_equals_p1_winner | PASS |
| forbidden_newly_dropped_absent_clean | PASS |
| forbidden_prior_i3_absent_clean | PASS |
| new_col_p0_is_unrated_present | PASS |
| new_col_p1_is_unrated_present | PASS |
| new_col_is_unrated_hist_present | PASS |
| new_cols_boolean_type | PASS |
| p0_nullif_count_matches_ledger | PASS |
| p0_is_unrated_consistency | PASS |
| p1_nullif_count_matches_ledger | PASS |
| p1_is_unrated_consistency | PASS |
| avg_elo_nullif_count_matches_ledger | PASS |
| hist_nullif_count_matches_ledger | PASS |
| hist_is_unrated_consistency | PASS |
| row_count_clean_unchanged | PASS |
| row_count_hist_unchanged | PASS |
| hist_leaderboard_retained | PASS |
| hist_player_count_retained | PASS |

## SQL Queries (Invariant I6)

All DDL and assertion SQL is stored verbatim in `01_04_02_post_cleaning_validation.json`
under the `sql_queries` key. Ledger-derived expected values are stored under
`ledger_derived_expected_values`.
