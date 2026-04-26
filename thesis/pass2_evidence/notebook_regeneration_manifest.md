# Notebook Regeneration Manifest — First Version
Generated: 2026-04-26 by T03 executor (thesis/audit-methodology-lineage-cleanup).

Purpose: Lists every sandbox notebook that may need regeneration before thesis Pass-2
review, with per-row staleness status. This is an audit-only manifest — no notebook
is executed here. Regeneration decisions are made in later tasks (T07+).

**Status vocabulary:**
- `confirmed_intact` — artifact verified intact in dependency_lineage_audit.md; no regeneration needed for thesis lineage
- `not_yet_assessed` — not directly linked to a thesis claim in Chapters 1–4 but exists in Phase 01; may be needed for downstream phases
- `flagged_stale` — artifact linked to a stale/contradictory claim; regeneration required before thesis claim can be corrected
- `phase_blocked` — Phase 02+ notebook; not yet executed; will be needed when that phase starts

**Cause taxonomy for flagged_stale rows:**
- `T16 14A.1 finding` — finding from T16 step 14A.1 data-quality report analysis forces regeneration
- `T05/Q2 BLOCKER-1 propagation` — aoe2companion `qp_rm_1v1` leaderboard-label clarification may propagate to prose
- `prose_inconsistency` — notebook artifact is correct; only thesis prose is inconsistent; no notebook regeneration needed
- `open_review_flag` — [REVIEW] flag in thesis prose pending Pass-2 verification; notebook not stale, only citation/value pending

---

## sc2egset — Phase 01 notebooks

All Phase 01 sc2egset steps are `complete` per STEP_STATUS.yaml (completed 2026-04-09 to 2026-04-19).

| Notebook path | Step | Artifact status | Thesis claim(s) | Regen status | Cause |
|--------------|------|----------------|-----------------|-------------|-------|
| sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py | 01_01_01 | intact | C2-01 (partial); §4.1.1 CONSORT; sec_4_1_crosswalk rows 1–2 | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_02_schema_discovery.py | 01_01_02 | intact | Background only | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py | 01_02_01 | intact | sec_4_2_crosswalk rows 1–4 | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py | 01_02_02 | intact | sec_4_2_crosswalk rows (ingestion) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_03_raw_schema_describe.py | 01_02_03 | intact | Background only | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py | 01_02_04 | intact | C2-02, C2-03; sec_4_1_crosswalk rows (date range, map cardinality, toon_id) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py | 01_02_05 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.py | 01_02_06 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_07_multivariate_eda.py | 01_02_07 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py | 01_03_01 | intact | sec_4_1_crosswalk (race dist, result dist, month gaps) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py | 01_03_02 | intact | C2-01; sec_4_1_crosswalk (555 Random, 22379 replays, 26 Undecided) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_03_table_utility.py | 01_03_03 | intact | Background only | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_04_event_profiling.py | 01_03_04 | intact | C2-04, C2-05, C2-06, C2-07; sec_4_1_crosswalk (event counts, PlayerStats period) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_00_source_normalization.py | 01_04_00 | intact | sec_4_1_crosswalk (side win_pct, matches_long_raw count) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py | 01_04_01 | intact | sec_4_1_crosswalk (missingness ledger: MMR 83.95%, APM 2.53%, clanTag, highestLeague) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py | 01_04_02 | intact | sec_4_1_crosswalk (matches_flat_clean 22209/44418/28-30 cols; 18 assertions PASS) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_duration_augmentation.py | 01_04_02 (duration ADDENDUM) | intact | §4.1.1.3 duration_seconds / is_duration_suspicious (30-col schema) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_03_minimal_history_view.py | 01_04_03 | intact | sec_4_2_crosswalk (mean games/player derivation) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04_identity_resolution.py | 01_04_04 | intact | sec_4_2_crosswalk (toon_id/nickname cardinalities) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.py | 01_04_04b | intact | §4.2.2 Branch (iii) migration_rate ~12%, collision_rate 30.6% | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_05_cross_region_annotation.py | Extra step (WP-7) | not directly linked to thesis claim | Cross-region annotation (Phase 01 supplement per PR #204) | not_yet_assessed | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_00_scaffold.py | scaffold | not_yet_assessed | No direct thesis claim | not_yet_assessed | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_01_quarterly_grain.py | 01_05_01 | intact | §4.1.1.1 temporal coverage context | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_02_psi_quarterly.py | 01_05_02 | intact | Pre-game feature stability background | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_03_stratification_regime.py | 01_05_03 | intact | Patch regime stratification | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_04_survivorship.py | 01_05_04 | intact | Survivorship analysis background | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_05_variance_icc.py | 01_05_05 | intact | C4-01 (ICC ANOVA 0.0463; [REVIEW] CI method UNVERIFIED) | confirmed_intact ([REVIEW] CI method open — not a regeneration trigger) | open_review_flag |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_06_dgp_diagnostics.py | 01_05_06 | intact | Duration distribution background | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_07_phase06_interface.py | 01_05_07 | intact | C4-08 (35/35 [POP:tournament] rows) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_sc2_leakage_audit.py | 01_05_08 | intact | Temporal leakage audit (no direct thesis number) | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_10_cross_region_history_impact.py | Extra step | not_yet_assessed | Cross-region history impact (supplement) | not_yet_assessed | — |
| sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_01_data_dictionary.py | 01_06_01 | intact | Data dictionary background | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_02_data_quality_report.py | 01_06_02 | intact | Quality report background | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_03_risk_register.py | 01_06_03 | intact | Risk register background | confirmed_intact | — |
| sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py | 01_06_04 | intact | Modeling readiness background | confirmed_intact | — |

---

## aoestats — Phase 01 notebooks

All Phase 01 aoestats steps are `complete` per STEP_STATUS.yaml (completed 2026-04-09 to 2026-04-19).

| Notebook path | Step | Artifact status | Thesis claim(s) | Regen status | Cause |
|--------------|------|----------------|-----------------|-------------|-------|
| sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py | 01_01_01 | intact | sec_4_1_crosswalk (172/171 files, 3773.61 MB, date range, 3 gaps) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_02_schema_discovery.py | 01_01_02 | intact | Background only | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py | 01_02_01 | intact | sec_4_2_crosswalk ingestion rows | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_02_duckdb_ingestion.py | 01_02_02 | intact | sec_4_2_crosswalk (union_by_name, 36 DOUBLE files) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_raw_schema_describe.py | 01_02_03 | intact | Background only | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py | 01_02_04 | intact | sec_4_1_crosswalk (profile_id cardinality 641662, max 24853897) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py | 01_02_05 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.py | 01_02_06 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_07_multivariate_eda.py | 01_02_07 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_01_systematic_profiling.py | 01_03_01 | intact | sec_4_1_crosswalk (aoestats profile counts) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py | 01_03_02 | intact | sec_4_1_crosswalk (30690651 matches_raw; 17815944; Jaccard 0.958755) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_03_table_utility.py | 01_03_03 | intact | Background only | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_00_source_normalization.py | 01_04_00 | intact | sec_4_1_crosswalk (side win_pct 52.27%; matches_long_raw 107626399) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py | 01_04_01 | intact | sec_4_1_crosswalk (p0_civ n_distinct=50; C1-01 chain; missingness ledger sentinels) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py | 01_04_02 | intact | sec_4_1_crosswalk (matches_1v1_clean 17814947; R08 -997; 20-22 cols; 33 assertions PASS) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py | 01_04_03 | intact | Background only | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.py | Extra step | intact | §4.4.6 canonical_slot amendment (BACKLOG F1 referenced) | not_yet_assessed | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_04_identity_resolution.py | 01_04_04 | intact | §4.2.2 Branch (v) structurally-forced; VERDICT A 0.9960 agreement | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_05_i5_diagnosis.py | 01_04_05 | intact | C4-04 (80.3% / +11.9 ELO audit) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.py | Extra step | not_yet_assessed | old_rating temporal audit background | not_yet_assessed | — |
| sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.py | Extra step | not_yet_assessed | old_rating conditional annotation | not_yet_assessed | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_01_quarterly_grain.py | 01_05_01 | intact | Quarterly grain background | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_02_psi_pre_game_features.py | 01_05_02 | intact | PSI shift background | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_03_stratification_patch_regime.py | 01_05_03 | intact | Patch regime stratification; C4-06 patch 66692 context | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_04_survivorship_triple.py | 01_05_04 | intact | Survivorship analysis background | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_05_variance_decomposition_icc.py | 01_05_05 | intact | C4-03 (ICC ANOVA 0.0268 [0.0148; 0.0387]) | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit.py | 01_05_06 | intact | Temporal leakage audit background | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_07_dgp_diagnostics_duration.py | 01_05_07 | intact | DGP diagnostics background | confirmed_intact | — |
| sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.py | 01_05_08 | intact | C4-05 (0 [PRE-canonical_slot] matches on 137 rows); C4-10 (aoestats implicit scope) | confirmed_intact | — |

---

## aoe2companion — Phase 01 notebooks

All Phase 01 aoe2companion steps are `complete` per STEP_STATUS.yaml (completed 2026-04-09 to 2026-04-19).

| Notebook path | Step | Artifact status | Thesis claim(s) | Regen status | Cause |
|--------------|------|----------------|-----------------|-------------|-------|
| sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py | 01_01_01 | intact | sec_4_1_crosswalk (2073/2072 files, 9387.80 MB, date range, no gaps) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.py | 01_01_02 | intact | Background only | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py | 01_02_01 | intact | sec_4_2_crosswalk ingestion rows | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_02_duckdb_ingestion.py | 01_02_02 | intact | sec_4_2_crosswalk (read_csv_auto VARCHAR inference; aoe2companion ingestion) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_03_raw_schema_describe.py | 01_02_03 | intact | Background only | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py | 01_02_04 | intact | sec_4_2_crosswalk (name cardinality 2308187 vs 2468478 discrepancy flag) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py | 01_02_05 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.py | 01_02_06 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_07_multivariate_eda.py | 01_02_07 | intact | No direct thesis claim | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py | 01_03_01 | intact | sec_4_1_crosswalk (profileId cardinality 3387273; sec_4_2_crosswalk name cardinality) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py | 01_03_02 | intact | sec_4_1_crosswalk (277099059 matches_raw; 40062975 rows_per_match=2; AI rows) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_03_table_utility_assessment.py | 01_03_03 | intact | Background only | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_00_source_normalization.py | 01_04_00 | intact | sec_4_1_crosswalk (matches_long_raw 277099059; side=0 449 rows) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_01_data_cleaning.py | 01_04_01 | intact | sec_4_1_crosswalk (rating NULL 26.20%; civ 56 distinct; NULL-cluster 11184 rows) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py | 01_04_02 | intact | sec_4_1_crosswalk (matches_1v1_clean 30531196; R01 -216M; R03 -5052; 48-51 cols) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_02_duration_augmentation.py | 01_04_02 (duration) | intact | Duration augmentation (ADDENDUM 2026-04-18) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_03_minimal_history_view.py | 01_04_03 | intact | §4.1.2.2 temporal coverage start 2020-07-31 23:30:34 UTC | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_04_identity_resolution.py | 01_04_04 | intact | §4.2.2 Branch (i) profileId; migration_rate 2.57% / collision_rate 3.55% | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_01_quarterly_grain.py | 01_05_01 | intact | Quarterly grain; D3 role matrix (24 quarters PRIMARY context) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_02_psi_shift.py | 01_05_02 | intact | PSI shift background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py | 01_05_03 | intact | Leaderboard stratification | confirmed_intact | T05/Q2 BLOCKER-1 propagation — qp_rm_1v1 (leaderboardId=18) label clarification may trigger prose update in §4.2.3; notebook artifact itself is intact |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_04_survivorship.py | 01_05_04 | intact | Survivorship analysis background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_05_icc.py | 01_05_05 | intact | C4-02 (ICC ANOVA 0.003013 [0.001724; 0.004202]; glmm_skip_note) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_06_dgp_duration.py | 01_05_06 | intact | DGP diagnostics background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_07_phase06_interface.py | 01_05_07 | intact | C4-09 (74/74 [POP:ranked_ladder] rows) | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_08_leakage_audit.py | 01_05_08 | intact | Temporal leakage audit background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.py | 01_05_09 | intact | Phase 01 exit memo background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py | 01_06_01 | intact | Data dictionary background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.py | 01_06_02 | intact | Quality report background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_03_risk_register.py | 01_06_03 | intact | Risk register background | confirmed_intact | — |
| sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py | 01_06_04 | intact | Modeling readiness background | confirmed_intact | — |

---

## Phase 02+ notebooks (all datasets)

No Phase 02+ notebooks exist yet. When created, they will be added to this manifest.

| Dataset | Phase | Status |
|---------|-------|--------|
| sc2egset | 02+ | phase_blocked — no notebooks exist |
| aoestats | 02+ | phase_blocked — no notebooks exist |
| aoe2companion | 02+ | phase_blocked — no notebooks exist |

---

## Summary

| Dataset | confirmed_intact | not_yet_assessed | flagged_stale | phase_blocked |
|---------|-----------------|-----------------|---------------|---------------|
| sc2egset (Phase 01) | 32 | 2 | 0 | 0 |
| aoestats (Phase 01) | 22 | 5 | 0 | 0 |
| aoe2companion (Phase 01) | 31 | 0 | 0 | 0 |
| Phase 02+ (all) | 0 | 0 | 0 | n/a (no notebooks exist) |
| **Total** | **85** | **7** | **0** | **0** |

**No notebooks are flagged_stale.**

The 7 `not_yet_assessed` notebooks are supplementary or extra-step notebooks not directly linked
to a thesis claim in Chapters 1–4 (cross-region annotation, scaffold, extra cleaning steps).
They require no regeneration for thesis lineage purposes.

The T05/Q2 BLOCKER-1 `qp_rm_1v1` leaderboard label issue in
`aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py` is flagged with
cause `T05/Q2 BLOCKER-1 propagation` but artifact is confirmed_intact — the notebook output
is correct; only §4.2.3 / §4.1.4 prose may need terminology clarification (class A/B edit).
No notebook regeneration is triggered by this finding alone.
