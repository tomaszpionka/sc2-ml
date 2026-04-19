# Decision Gate — 01_05 Temporal & Panel EDA (sc2egset)

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Date:** 2026-04-18
**Branch:** feat/01-05-sc2egset

## Q1..Q9 Parameter Group Execution Status

| Parameter Group | Spec Ref | Executed | Notes |
|---|---|---|---|
| Q1 Quarterly grain (time-window grain + overlap window) | §2, §3 | YES | 10 quarters 2022-Q3..2024-Q4; 10,076 rows / 5,038 matches |
| Q2 PSI N=10 equal-frequency (frozen reference edges) | §4 | YES | Uncohort-filtered PRIMARY (B2 fix); N∈{5,10,20} = sensitivity |
| Q3 Stratification + secondary regime (tournament_era) | §5 | YES | Hand-mapped 70 dirs (M2 fix); regime_id ≡ quarter noted |
| Q4 Triple survivorship (unconditional + sensitivity + labels) | §6 | YES | Unconditional: fraction_active per quarter; N cohort: 9 with span, 152 without |
| Q5 Reference + tested period definitions | §7 | YES | Ref: 2022-08-29..2022-12-31; tested: 2023-Q1..2024-Q4 |
| Q6 Variance decomposition + ICC | §8 | YES | LPM ICC=0.0456; ANOVA ICC=0.0463; GLMM failed |
| Q7 Temporal leakage audit (3 queries) | §9 | YES | PASS: future_leak=0; violations=0; window asserted |
| Q8 DGP diagnostics (duration_seconds) | §10 | YES | Max |d|=0.544 (2023-Q3); suspicious_rate=0.000 |
| Q9 Phase 06 interface CSV (spec §12) | §12 | YES | 35 rows; 9 columns; schema valid |

## Spec Deviations Triggered

| Deviation | Critique Ref | CROSS Entry | Resolution |
|---|---|---|---|
| PRIMARY PSI = uncohort-filtered | B2 | YES (research_log.md 2026-04-18) | Cohort too small for span>=30d filter in tournament data |
| B3: Three ICC estimators (LPM + ANOVA + GLMM) | B3 | Noted in research_log.md | All three reported; GLMM failed to converge |
| Schema divergence Spec §1 vs VIEW | M3 | Noted in INVARIANTS §5 I8 | Phase 06 UNION on metric_name only |
| Q1 reframed (vacuous → meaningful) | M6 | N/A | Window-containment check implemented |
| Span filter removed for ICC cohort | derived | Noted in research_log.md | Tournament structure makes span>=30d inappropriate |

## Gate Verdict

| Gate | Status | Evidence |
|---|---|---|
| All Q1..Q9 executed | PASS | Table above |
| Leakage audit PASS | PASS | leakage_audit_sc2egset.json: halt_triggered=false |
| Phase 06 interface CSV schema-valid | PASS | phase06_interface_sc2egset.csv: 9 cols, 35 rows, sc2egset constant |
| STEP_STATUS 01_05_01..01_05_08 all complete | PASS | STEP_STATUS.yaml updated |
| PIPELINE_SECTION_STATUS 01_05 complete | PASS | PIPELINE_SECTION_STATUS.yaml updated |
| research_log.md entry dated 2026-04-18 | PASS | Entry appended |
| INVARIANTS §4 populated (7+ findings) | PASS | 8 findings with SQL citations |

**Is 01_05 ready to feed Phase 02? YES.**

All 10 parameter groups executed (Q5 = reference/tested period definitions embedded in Q2/Q7).
Leakage audit PASSED. Phase 06 interface CSV schema-valid.
All spec deviations documented with CROSS entries where applicable.

## Known limitations for downstream use

1. **PSI figures are uncohort-filtered** (B2 fix). Conditional PSI requires N>=10 cohort
   which has only 152 players (no span filter), inadequate for quarter-level conditioning.
2. **ICC is borderline** (ICC=0.046, INCONCLUSIVE). Between-player variance is small but
   non-zero. Zerg-restricted ICC=0.1095 suggests faction-stratified models may be valuable.
3. **sc2egset is [POP:tournament]**. Population is competitive/professional players, not
   general playerbase. All Phase 06 rows tagged accordingly.
4. **Spec §1 schema divergence** (M3). Feature names in Phase 06 CSV match actual VIEW
   schema, not spec's idealized 9-col contract. Cross-dataset Phase 06 join must use
   metric_name only.
5. **Duration drift notable** in 2023-Q3 (|d|=0.544). This quarter had only 122 matches
   and unusually long games. Phase 02 DGP features should account for this.
