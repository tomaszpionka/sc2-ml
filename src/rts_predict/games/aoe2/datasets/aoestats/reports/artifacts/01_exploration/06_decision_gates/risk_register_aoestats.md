# Risk Register — aoestats

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## Severity Distribution

- BLOCKER: 1
- HIGH: 1
- MEDIUM: 2
- RESOLVED: 1

**1 BLOCKER (AO-R01 canonical_slot).** Verdict: READY_CONDITIONAL. Phase 02 GO-NARROW (aggregate features only).

### AO-R01 [BLOCKER] — SLOT_ASYMMETRY

canonical_slot column ABSENT from matches_history_minimal. W3 ARTEFACT_EDGE (01_04_05): upstream API assigns team=1 to higher-ELO player in 80.3% of matches, creating team1_wins ~52.27% base-rate artefact. Per-slot features forbidden until BACKLOG F1 resolved.

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json`
- **Phase 02:** Per-slot features (p0_civ, p1_civ, p0_old_rating, p1_old_rating) forbidden. Aggregate / UNION-ALL-symmetric features permitted (faction, opponent_faction, old_rating via player_history_all). Scope: GO-NARROW.
- **Thesis:** §4.4.6
- **Mitigation:** OPEN (BACKLOG F1)

### AO-R02 [MEDIUM] — IDENTITY

aoestats uses profile_id (Branch v, structurally-forced): no visible handle column exists to compare identity candidates. Migration and collision rates unevaluable within aoestats alone. Cross-dataset namespace bridge to aoe2companion confirmed VERDICT A (0.9960 agreement).

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md §5 I2 row`
- **Phase 02:** Identity key is structurally forced; no alternative candidate. Phase 02 may proceed with profile_id as-is.
- **Thesis:** §4.2.2
- **Mitigation:** ACCEPTED (documented in thesis)

### AO-R03 [HIGH] — ICC_SIGNAL

ICC FALSIFIED: ANOVA ICC (N=10 cohort, n=744 players) = 0.0268 [0.0148, 0.0387]. Below 0.05 threshold. Attributed to early crawler period (2022-Q3: 744 active players). Between-player variance detectable but small.

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.json`
- **Phase 02:** INVARIANTS.md §5 I8 row: PARTIAL — ICC FALSIFIED in 2022-Q3 reference. Phase 02 may proceed with per-player features but thesis must document this limitation. ICC should be re-evaluated in a denser quarter.
- **Thesis:** §4.4.5
- **Mitigation:** ACCEPTED (documented in thesis)

### AO-R04 [RESOLVED] — TEMPORAL_LEAKAGE

Temporal leakage audit PASSED (01_05_06). No temporal leakage detected. canonical_slot absent; [PRE-canonical_slot] flag ACTIVE.

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.json`
- **Phase 02:** No leakage risk. [PRE-canonical_slot] flag prevents per-slot feature extraction.
- **Thesis:** §4.2.3
- **Mitigation:** RESOLVED

### AO-R05 [MEDIUM] — ICC_SIGNAL

B3 coincidence: reference start 2022-08-29 coincides with earliest dataset date. Match count jumps ~22x from 2022-Q3 (18k) to 2023-Q1 (404k), reflecting crawler expansion. PSI increases in early quarters may reflect population drift OR crawler expansion confound.

- **Evidence:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md`
- **Phase 02:** Counterfactual PSI (2023-Q1 reference) available to disambiguate. Phase 02 should use 2023-Q1 as secondary reference window for PSI analysis.
- **Thesis:** §4.1.2
- **Mitigation:** ACCEPTED (documented in thesis)

