# Step 01_04_02 -- Data Cleaning Execution: Post-Cleaning Validation

**Generated:** 2026-04-17
**Dataset:** aoe2companion
**Step:** 01_04_02 -- Act on DS-AOEC-01..08

## Summary

Step 01_04_02 applies all 8 cleaning decisions (DS-AOEC-01..08) surfaced by the
01_04_01 missingness audit. Both VIEWs are replaced via CREATE OR REPLACE DDL.
No raw tables are modified (Invariant I9). Row counts are unchanged (column-only
cleaning step). All validation assertions pass.

**Final column counts:** matches_1v1_clean 54 -> 48 (drop 7, add 1, modify 0);
player_history_all 20 -> 19 (drop 1, add 0, modify 0).

## Per-DS Resolutions

| DS ID | Column | Decision |
|---|---|---|
| DS-AOEC-01 | server, scenario, modDataset, password | DROP all 4 from matches_1v1_clean per Rule S4 (van Buuren 2018). |
| DS-AOEC-02 | antiquityMode (DROP), hideCivs (RETAIN+FLAG) | antiquityMode DROPPED (60.06%, 40-80% non-primary band). hideCivs RETAINED with FLAG_FOR_IMPUTATION (37.18%, 5-40% band) deferred to Phase 02. |
| DS-AOEC-03 | All low-NULL game settings (<5%) | NO-OP (RETAIN_AS_IS). All low-NULL game settings retained verbatim. |
| DS-AOEC-03b | mod, status (matches_1v1_clean); status (player_history_all) | DROP mod and status from matches_1v1_clean; DROP status from player_history_all. Constants-detection override supersedes low-NULL RETAIN_AS_IS. |
| DS-AOEC-04 | rating (matches_1v1_clean) + rating_was_null flag (NEW) | rating RETAINED in matches_1v1_clean. ADD rating_was_null BOOLEAN flag (sklearn MissingIndicator pattern; DS-AOEC-04 / Rule S4 primary feature exception). No NULLIF needed -- upstream VIEW already filters rating >= 0. |
| DS-AOEC-05 | country | country RETAINED in both VIEWs per cross-dataset convention. Phase 02 strategy TBD ('Unknown' encoding or country_was_null indicator). |
| DS-AOEC-06 | won (matches_1v1_clean) | NO-OP (RETAIN_AS_IS). Zero NULLs by R03 complementarity. |
| DS-AOEC-07 | won (player_history_all) | DOCUMENTED: won in player_history_all has ~19,251 NULLs (0.0073%). EXCLUDE_TARGET_NULL_ROWS rule documented in cleaning registry. Physical exclusion deferred to Phase 02 feature-computation per Rule S2. |
| DS-AOEC-08 | leaderboards_raw (singleton 2-row), profiles_raw (7 dead columns 100% NULL) | FORMALLY DECLARED OUT-OF-ANALYTICAL-SCOPE in cleaning registry. No DDL change, no DROP TABLE. |

## Cleaning Registry (new rules in 01_04_02)

| Rule ID | Condition | Action | Impact |
|---|---|---|---|
| drop_high_null_columns_clean | n_null > 40% in matches_1v1_clean scope (Rule S4 / van Buuren 2018) | DROP server, scenario, modDataset, password from matches_1v1_clean | -4 cols matches_1v1_clean |
| drop_schema_evolution_columns_clean | n_null in 40-80% band, non-primary feature, schema-evolution column | DROP antiquityMode from matches_1v1_clean | -1 col matches_1v1_clean |
| drop_constants_clean | n_distinct=1 in matches_1v1_clean scope | DROP mod, status from matches_1v1_clean | -2 cols matches_1v1_clean |
| drop_constants_hist | n_distinct=1 in player_history_all scope | DROP status from player_history_all | -1 col player_history_all |
| add_rating_was_null_flag_clean | rating IS NULL in matches_1v1_clean (primary feature, ~26.20% NULL) | ADD (rating IS NULL) AS rating_was_null BOOLEAN to matches_1v1_clean | +1 col matches_1v1_clean (rating_was_null BOOLEAN) |
| declare_leaderboards_profiles_oos | Always (documentation only) | leaderboards_raw (2-row singleton reference) + profiles_raw (7 dead columns, 100% NULL) declared OUT-OF-ANALYTICAL-SCOPE | None (registry-only resolution) |

## CONSORT Column-Count Flow

| VIEW | Cols before | Cols dropped | Cols added | Cols modified | Cols after |
|---|---|---|---|---|---|
| matches_1v1_clean | 54 | 7 (server/scenario/modDataset/password/antiquityMode/mod/status) | 1 (rating_was_null) | 0 | 48 |
| player_history_all | 20 | 1 (status) | 0 | 0 | 19 |

## CONSORT Match-Count Flow (column-only -- no row changes)

| Stage | matches_1v1_clean rows | matches_1v1_clean matches | player_history_all rows |
|---|---|---|---|
| Before 01_04_02 (post 01_04_01) | 61,062,392 | 30,531,196 | 264,132,745 |
| After 01_04_02 column-only changes | 61,062,392 | 30,531,196 | 264,132,745 |

## Subgroup Impact (Jeanselme et al. 2024)

| Affected column | Source decision | Subgroup most affected | Impact |
|---|---|---|---|
| server (dropped from matches_1v1_clean) | DS-AOEC-01 | ~2.6% of rows had non-NULL server; those matches lose server-location information | 97.39% NULL; MNAR. ~2.6% of rows (1,592,568) had non-NULL server info. That subgroup loses location information; deemed not predictive for ranked 1v1. |
| scenario (dropped from matches_1v1_clean) | DS-AOEC-01 | 100% NULL -- no subgroup affected | 100.00% NULL; MAR. No subgroup loses anything. |
| modDataset (dropped from matches_1v1_clean) | DS-AOEC-01 | 100% NULL -- no subgroup affected | 100.00% NULL; MAR. No subgroup loses anything. |
| password (dropped from matches_1v1_clean) | DS-AOEC-01 | ~22.4% of rows had non-NULL password (password-protected lobby) | 77.57% NULL; MAR. ~13,695,195 rows had password-protected lobby info. Deemed not predictive for ranked 1v1. |
| antiquityMode (dropped from matches_1v1_clean) | DS-AOEC-02 | Pre-patch matches (60.1% NULL) lose this flag; post-patch matches retain downstream patch-stratification | 60.06% NULL; MAR (schema-evolution boundary). ~24,386,243 non-NULL rows had this flag. Patch-stratification captures the same boundary for Phase 02. |
| mod (dropped from matches_1v1_clean) | DS-AOEC-03b | Constant -- no subgroup affected | n_distinct=1 constant across 61,062,392 rows; zero information content. |
| status (dropped from both VIEWs) | DS-AOEC-03b | Constant -- no subgroup affected | n_distinct=1 constant in both VIEWs (61,062,392 clean, 264,132,745 hist); zero information content. |
| rating_was_null (added to matches_1v1_clean) | DS-AOEC-04 | ~26.20% of matches_1v1_clean rows have rating IS NULL (unrated focal player) | 15,999,234 rows (26.20%) have rating IS NULL. Flag preserves rated/unrated signal for Phase 02 (sklearn MissingIndicator pattern). |

## Validation Results

| Assertion | Status |
|---|---|
| col_count_clean_48 | PASS |
| col_count_hist_19 | PASS |
| zero_null_matchId_clean | PASS |
| zero_null_started_clean | PASS |
| zero_null_profileId_clean | PASS |
| zero_null_won_clean | PASS |
| zero_null_matchId_hist | PASS |
| zero_null_profileId_hist | PASS |
| zero_null_started_hist | PASS |
| r03_complementarity_0_violations | PASS |
| forbidden_newly_dropped_absent_clean | PASS |
| forbidden_newly_dropped_absent_hist | PASS |
| forbidden_prior_i3_absent_clean | PASS |
| hist_won_retained | PASS |
| hist_rating_retained | PASS |
| hist_country_retained | PASS |
| hist_team_retained | PASS |
| new_col_rating_was_null_present | PASS |
| new_col_rating_was_null_boolean | PASS |
| rating_was_null_equals_rating_is_null | PASS |
| rating_was_null_no_inconsistency | PASS |
| rating_was_null_count_matches_ledger | PASS |
| row_count_clean_unchanged | PASS |
| row_count_hist_unchanged | PASS |

## SQL Queries (Invariant I6)

All DDL and assertion SQL is stored verbatim in `01_04_02_post_cleaning_validation.json`
under the `sql_queries` key. Ledger-derived expected values are stored under
`ledger_derived_expected_values`.
