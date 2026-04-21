# Modeling Readiness Decision — aoestats

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced by:** 01_06_04 (Phase 01 Decision Gates)
**Date:** 2026-04-19

---

## 1. Verdict

**READY_WITH_DECLARED_RESIDUALS**

Per spec §2: 0 BLOCKER risks (AO-R01 resolved 2026-04-20). Phase 02 proceeds in **GO-FULL** mode:
per-slot features permitted via `canonical_slot`; see `matches_history_minimal.yaml` 10-col schema.

---

## 2. Flip-Predicate

**SATISFIED (2026-04-20): BACKLOG F1 landed; W4 operational content (INVARIANTS §5 I5 PARTIAL → HOLDS) bundled in same PR.**

~~BACKLOG F1 (`canonical_slot` resolved in schema) AND W4 (INVARIANTS.md §5 I5 row transitions PARTIAL → HOLDS via schema amendment). If F1 lands without W4, verdict remains READY_CONDITIONAL with narrower aggregate-features scope.~~

Coupling explanation: W3 ARTEFACT_EDGE (01_04_05) establishes that `team=1` is assigned to the
higher-ELO player in 80.3% of matches, creating a `team1_wins` base-rate artefact (~52.27%).
BACKLOG F1 (canonical_slot schema addition) is the structural fix; W4 (INVARIANTS.md §5 I5
PARTIAL → HOLDS schema amendment) is the invariant reconciliation. Both are required before
per-slot features are safe to use. If F1 lands without W4, slot-conditioned features would be
technically present but invariant-unverified — verdict remains READY_CONDITIONAL.

---

## 3. BLOCKER List

**0 BLOCKERS (AO-R01 resolved 2026-04-20)**

~~**1 BLOCKER: AO-R01 [SLOT_ASYMMETRY]**~~ — RESOLVED 2026-04-20 (BACKLOG F1 + W4).

Historical record: `canonical_slot` column was absent from `matches_history_minimal`. Upstream API assigns `team=1`
to higher-ELO player in 80.3% of matches (W3 ARTEFACT_EDGE, artifact:
`01_exploration/04_cleaning/01_04_05_i5_diagnosis.json`).

- **Mitigation:** RESOLVED — canonical_slot VARCHAR column added via hash-on-match_id derivation (01_04_03b); INVARIANTS.md §5 I5 PARTIAL → HOLDS (W4).
- **Thesis defence:** §4.4.6
- **Phase 02 implication:** GO-FULL. Per-slot features (canonical_slot-conditioned old_rating, civ, faction stratifiers) now invariant-safe.

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

**GO-FULL** (READY_WITH_DECLARED_RESIDUALS; per-slot features permitted via canonical_slot; see matches_history_minimal.yaml 10-col schema).

~~**GO-NARROW** (READY_CONDITIONAL).~~

Phase 02 may proceed on all feature types including per-slot features (canonical_slot-conditioned
old_rating, civ, faction stratifiers). The slot-asymmetry blocker (AO-R01) is resolved. Phase 02 feature extractors bind to the cross-dataset `reports/specs/02_00_feature_input_contract.md §2` canonical input spec (version CROSS-02-00-v1, LOCKED 2026-04-21); this memo's scope ends at the Phase 01 output.

Historical rationale for previous GO-NARROW (retained for audit provenance):
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
