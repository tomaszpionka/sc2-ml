# 01_05_07 Phase 06 Interface — aoe2companion

spec: reports/specs/01_05_preregistration.md@7e259dd8

## B-02 Deviation Note (pre-authorized)

Spec §1 contract: match_id, started_at, player_id, team, chosen_civ_or_race, rating_pre, won, map_id, patch_id
VIEW schema: match_id, started_at, player_id, opponent_id, faction, opponent_faction, won, duration_seconds, dataset_tag

`feature_name` values in this CSV match the VIEW schema (faction, map_id, rating, won).
Cross-dataset alignment is on `metric_name` only per critique pre-authorization.
Spec §1 divergence documented in INVARIANTS.md §5 (I8 partial row).

## M-07 Population scope

[POP:ranked_ladder]: aoec is an online-ladder dataset. All findings condition on ranked-ladder
participation, not the overall AoE2 player population. See T10 Decision Gate memo.

## Row counts by (feature_name, metric_name)

| feature_name   | metric_name              |   count |
|:---------------|:-------------------------|--------:|
| faction        | psi                      |      40 |
| map_id         | psi                      |       8 |
| rating         | cohen_d                  |       8 |
| rating         | psi                      |       8 |
| won            | cohen_h                  |       8 |
| won            | icc_anova_observed_scale |       1 |
| won            | icc_lpm_observed_scale   |       1 |

**Total rows:** 74
**Expected minimum:** 4 features x 8 quarters x ~3 metrics = ~96 (plus ICC rows, sensitivity, lb-split)

## Sanity checks

- All `dataset_tag` = 'aoe2companion': True
- No POST_GAME tokens in `feature_name`: True
- ICC LPM value: 0.000491
- ICC ANOVA value: 0.003013

## Verdict

74 rows emitted. Schema conforms to spec §12. B-02 and M-07 deviations documented.
