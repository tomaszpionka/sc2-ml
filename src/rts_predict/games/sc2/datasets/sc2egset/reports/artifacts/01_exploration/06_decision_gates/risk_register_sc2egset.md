# Risk Register — sc2egset

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Produced by:** 01_06_03 (Phase 01 Decision Gates)
**Date:** 2026-04-19

## Severity Distribution

- BLOCKER: 0
- HIGH: 2
- MEDIUM: 4
- LOW: 0
- RESOLVED: 1

**No BLOCKER risks.** Phase 02 may proceed.

## Risk Details

### SC-R01 [MEDIUM] — IDENTITY

sc2egset uses player_id_worldwide (Branch iii, region-scoped toon_id R-S2-G-P) rather than the I2 default LOWER(nickname). Within-region collision rate 30.6% (451/1,473 pairs); cross-region migration ~12% accepted bias.

- **Evidence:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §5 I2 row`
- **Phase 02 implication:** Phase 02 player identity key is region-scoped; cross-region players appear as distinct entities. Rating-system backtesting must acknowledge this scope boundary.
- **Thesis defence:** §4.2.2
- **Mitigation:** ACCEPTED (documented in thesis)

### SC-R02 [MEDIUM] — SCHEMA_DIVERGENCE

Spec CROSS-01-05-v1 §1 9-column contract differs from sc2egset matches_history_minimal actual schema (opponent_id, faction, opponent_faction, duration_seconds, dataset_tag vs spec's team, chosen_civ_or_race, rating_pre, map_id, patch_id). 5 of 9 columns differ.

- **Evidence:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §5 I8 row`
- **Phase 02 implication:** Phase 06 cross-dataset UNION joins on metric_name only; feature_name values match actual VIEW schema, not spec idealized schema. Cross-dataset Phase 06 join must use metric_name not column_name.
- **Thesis defence:** §4.1.3
- **Mitigation:** ACCEPTED (documented in thesis)

### SC-R03 [HIGH] — ICC_SIGNAL

ICC INCONCLUSIVE: ANOVA ICC = 0.0463 [0.0283, 0.0643]. CI spans 0.01–0.09 range; cannot conclude meaningful vs negligible skill signal. GLMM latent-scale failed to converge. Between-player variance small but non-zero.

- **Evidence:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/icc.json`
- **Phase 02 implication:** Skill-signal features (ELO, win-rate) may be less discriminative than expected. Model should include skill features but results must be interpreted with ICC uncertainty noted.
- **Thesis defence:** §4.4.5
- **Mitigation:** ACCEPTED (documented in thesis)

### SC-R04 [HIGH] — POPULATION_SCOPE

sc2egset is [POP:tournament] — professional/competitive players only (Heckman 1979 selection bias). All Phase 06 rows tagged [POP:tournament]. Population estimates not representative of general SC2 playerbase.

- **Evidence:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §5 (M7 scope note)`
- **Phase 02 implication:** Phase 02 models trained on sc2egset apply to tournament players only. Thesis must state population boundary explicitly in all cross-game comparisons.
- **Thesis defence:** §4.1.4
- **Mitigation:** ACCEPTED (documented in thesis)

### SC-R05 [RESOLVED] — TEMPORAL_LEAKAGE

Temporal leakage audit PASSED (01_05_08). No future-data leakage detected. Reference window assertion PASS. Post-game token violations = 0.

- **Evidence:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/leakage_audit_sc2egset.json`
- **Phase 02 implication:** No leakage risk for Phase 02 feature engineering given current schema.
- **Thesis defence:** §4.2.3
- **Mitigation:** RESOLVED

### SC-R06 [MEDIUM] — SURVIVORSHIP

Uncohort-filtered PSI: PRIMARY PSI computed without span->=30d filter because tournament structure makes cohort N=152 players with insufficient span coverage. Conditional PSI could not be computed.

- **Evidence:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md`
- **Phase 02 implication:** PSI figures for sc2egset are unconditional (not cohort-controlled). Phase 02 feature drift analysis should note this limitation.
- **Thesis defence:** §4.4.5
- **Mitigation:** ACCEPTED (documented in thesis)

### SC-R07 [MEDIUM] — TEMPORAL_LEAKAGE

Duration drift in 2023-Q3: Cohen's d = 0.544 (medium effect). Only 122 matches in that quarter; unusually long games. May indicate a data artifact or game-mechanic change in that tournament.

- **Evidence:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/dgp_diagnostic_sc2egset.md`
- **Phase 02 implication:** Phase 02 should consider excluding 2023-Q3 from DGP-sensitive features or flagging it in temporal CV folds.
- **Thesis defence:** §4.1.1
- **Mitigation:** ACCEPTED (documented in thesis)
