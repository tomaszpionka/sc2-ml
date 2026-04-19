# Risk Register — aoe2companion

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## Severity Distribution

- BLOCKER: 0
- HIGH: 1
- MEDIUM: 1
- LOW: 2
- RESOLVED: 1

**0 BLOCKERs.** Verdict: READY_WITH_DECLARED_RESIDUALS. Phase 02 GO full scope.

### AC-R01 [LOW] — IDENTITY

Identity-rate reconciliation: 2.57% rename-rate (97.43% stable profiles) and 3.55% name-collision-rate (same name, multiple profileIds). Both below 15% within-scope rigor threshold. Branch (i) API-namespace, rename-stable. Cross-dataset namespace bridge to aoestats confirmed VERDICT A (0.9960 agreement). INVARIANTS.md §5 I2 row: PARTIAL (rename rate <15%, collision <5%).

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json`
- **Phase 02:** Identity key is profileId; both rename and collision rates below threshold. Phase 02 may proceed with profileId as-is.
- **Thesis:** §4.2.2
- **Mitigation:** RESOLVED (documented in thesis)

### AC-R02 [HIGH] — ICC_SIGNAL

ICC FALSIFIED: ANOVA ICC (N=5k cohort, n=360,567 player-obs) = 0.003013 [0.001724, 0.004202]. Substantially below 0.05 threshold. Consistent across sample sizes (N=10k: 0.003574; N=20k ANOVA: 0.00324). Attributed to ranked-ladder population heterogeneity (vs. tournament-selection in sc2egset). INVARIANTS.md §5 I8 row: FALSIFIED at reference window.

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc.json`
- **Phase 02:** INVARIANTS.md §5 I8 row: FALSIFIED. Per-player features included but marginal effect expected to be small. Thesis §4.4.5 must document with defence. ICC should not be re-evaluated (stable across sample sizes).
- **Thesis:** §4.4.5
- **Mitigation:** ACCEPTED (documented in thesis)

### AC-R03 [RESOLVED] — TEMPORAL_LEAKAGE

Temporal leakage audit PASSED (01_05_08, v2 post-adversarial review). All 3 checks passed: reference cohort bounds correct; quarter-label consistency 0 violations; PSI reference SQL cites spec §7 timestamp bounds verbatim. No POST_GAME tokens in PRE_GAME feature selection contexts.

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_leakage_audit.json`
- **Phase 02:** No leakage risk. I3 guard confirmed in DGP diagnostics (01_05_06).
- **Thesis:** §4.2.3
- **Mitigation:** RESOLVED

### AC-R04 [MEDIUM] — FEATURE_DRIFT

map_id PSI > 1.1 in ALL 8 quarters (flagged_for_review). Driven by regular AoE2 map pool rotations (new maps each season; DLC maps with unknown category counts of 170K–425K per quarter). faction drift from 2023-Q3 (PSI=0.252–0.482) driven by DLC civilization releases (Dynasties of India, Return of Rome). rating drift from 2023-Q3 (PSI≈0.7, Cohen's d≈0.6) from ELO inflation/matchmaking changes. `won` (target proxy) fully stable (PSI=0.0, cohen_h=0.0) in all quarters.

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_02_psi_shift.json`
- **Phase 02:** map_id requires unknown-category handling in Phase 02 temporal CV (mandatory). faction and rating drift from 2023-Q3 require temporal CV split at 2023-Q2/Q3 boundary. Documented at §4.1.2.
- **Thesis:** §4.1.2
- **Mitigation:** ACCEPTED (documented in thesis)

### AC-R05 [LOW] — DURATION_QUALITY

358 clock-skew rows (duration_seconds < 0, i.e. finished < started) and 142 outlier rows (duration > 86400s = 24h) retained in matches_1v1_clean with is_duration_negative / is_duration_suspicious flags. Duration is POST_GAME_HISTORICAL; does not affect prediction label `won`. I3 guard confirmed (duration not used as PRE_GAME feature). Total: 500 flagged rows out of 30,531,196 (rate: 0.0016%).

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json`
- **Phase 02:** Duration POST_GAME_HISTORICAL; Phase 02 must not use duration_seconds as PRE_GAME feature (I3 enforced). Flag columns available for filtering if needed.
- **Thesis:** §4.2.3
- **Mitigation:** RESOLVED (flagged, not removed; rate 0.0016%)

