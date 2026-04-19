# Modeling Readiness Decision — aoestats

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced by:** 01_06_04 (Phase 01 Decision Gates)
**Date:** 2026-04-19

---

## 1. Verdict

**READY_CONDITIONAL**

Per spec §2: 1 BLOCKER risk (AO-R01 `canonical_slot`). Phase 02 proceeds in **GO-NARROW** mode:
aggregate / UNION-ALL-symmetric features permitted; per-slot features deferred.

---

## 2. Flip-Predicate

**BACKLOG F1 (`canonical_slot` resolved in schema) AND W4 (INVARIANTS.md §5 I5 row transitions PARTIAL → HOLDS via schema amendment). If F1 lands without W4, verdict remains READY_CONDITIONAL with narrower aggregate-features scope.**

Coupling explanation: W3 ARTEFACT_EDGE (01_04_05) establishes that `team=1` is assigned to the
higher-ELO player in 80.3% of matches, creating a `team1_wins` base-rate artefact (~52.27%).
BACKLOG F1 (canonical_slot schema addition) is the structural fix; W4 (INVARIANTS.md §5 I5
PARTIAL → HOLDS schema amendment) is the invariant reconciliation. Both are required before
per-slot features are safe to use. If F1 lands without W4, slot-conditioned features would be
technically present but invariant-unverified — verdict remains READY_CONDITIONAL.

---

## 3. BLOCKER List

**1 BLOCKER: AO-R01 [SLOT_ASYMMETRY]**

`canonical_slot` column absent from `matches_history_minimal`. Upstream API assigns `team=1`
to higher-ELO player in 80.3% of matches (W3 ARTEFACT_EDGE, artifact:
`01_exploration/04_cleaning/01_04_05_i5_diagnosis.json`).

- **Mitigation:** BACKLOG F1 (add `canonical_slot` to `matches_history_minimal`) + W4
  (update INVARIANTS.md §5 I5 row from PARTIAL to HOLDS after F1 + schema amendment)
- **Thesis defence:** §4.4.6
- **Phase 02 implication:** Phase 02 may proceed on aggregate / UNION-ALL-symmetric features (faction, opponent_faction, old_rating via player_history_all). Per-slot features (p0_civ, p1_civ, p0_old_rating, p1_old_rating) deferred until F1 + W4 both land.

---

## 4. HIGH/MEDIUM Residuals with Chapter 4 Anchors

| Risk ID | Severity | Category | Chapter 4 Anchor |
|---------|----------|----------|-----------------|
| AO-R02 | MEDIUM | IDENTITY | §4.2.2 |
| AO-R03 | HIGH | ICC_SIGNAL | §4.4.5 |
| AO-R05 | MEDIUM | ICC_SIGNAL | §4.1.2 |

### Residual details:

- **AO-R02 [MEDIUM] — IDENTITY branch (v) structurally-forced:** aoestats uses `profile_id`
  (Branch v, structurally-forced); no handle column exists for alternative candidates.
  Cross-dataset namespace bridge to aoe2companion confirmed VERDICT A (0.9960 agreement).
  Documented at **§4.2.2**. Phase 02 proceeds with `profile_id` as-is.

- **AO-R03 [HIGH] — ICC FALSIFIED (0.0268):** Between-player variance is non-zero but small;
  ANOVA ICC = 0.0268 [0.0148, 0.0387] below 0.05 threshold. Attributed to early crawler period
  (2022-Q3: 744 active players). Documented at **§4.4.5**. Phase 02 per-player features included
  but marginal effect may be small; ICC should be re-evaluated in a denser quarter.

- **AO-R05 [MEDIUM] — B3 crawler expansion confound:** Reference start 2022-08-29 coincides
  with earliest dataset date; match count jumps ~22x from 2022-Q3 (18k) to 2023-Q1 (404k).
  PSI increases in early quarters may reflect population drift OR crawler expansion.
  Documented at **§4.1.2**. Phase 02 should use 2023-Q1 as secondary reference window.

---

## 5. Phase 02 Go/No-Go

**GO-NARROW** (READY_CONDITIONAL).

Phase 02 may proceed on aggregate / UNION-ALL-symmetric features (faction, opponent_faction, old_rating via player_history_all). Per-slot features (p0_civ, p1_civ, p0_old_rating, p1_old_rating) deferred until F1 + W4 both land.

Rationale for GO-NARROW (not STOP):
- The slot-asymmetry artefact affects `team=1` label interpretation for per-slot features only.
- Aggregate / symmetric features (faction win-rate, average ELO from `player_history_all`,
  match counts) are NOT affected by team=0/1 slot assignment.
- Temporal leakage audit PASSED (01_05_06 artifact).
- Phase 02 feature scope is validly executable at GO-NARROW immediately; F1+W4 required to
  expand to full per-slot scope.

---

## 6. Role Assignment Summary

See cross-dataset rollup: `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`

| Dimension | aoestats role |
|-----------|---------------|
| D1 Sample-scale | SUPPLEMENTARY (~17.8M 1v1 clean matches vs ~30.5M aoe2companion) |
| D2 Skill-signal (ICC) | SUPPLEMENTARY (ICC 0.0268 FALSIFIED in 2022-Q3 reference; BACKLOG F1 pending) |
| D3 Temporal coverage | SUPPLEMENTARY (2022-Q3 crawler expansion confound; use 2023-Q1 secondary ref) |
| D4a Identity rename-stability | SUPPLEMENTARY (Branch v structurally-forced; no migration evaluable within aoestats alone) |
| D4b Identity within-scope rigor | SUPPLEMENTARY (cross-dataset VERDICT A 0.9960; within-scope rates unevaluable) |
| D5 Patch resolution | **PRIMARY** (patch_id column; D5 PRIMARY role for aoestats) |
| D6 Controlled-asymmetry flag | N/A (flag only; not role-bearing) |
