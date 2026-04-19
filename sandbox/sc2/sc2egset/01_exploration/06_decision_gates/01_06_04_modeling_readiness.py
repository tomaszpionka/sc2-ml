# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
# ---

# %% [markdown]
# # 01_06_04 — Modeling Readiness Decision (sc2egset)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** sc2egset is READY_WITH_DECLARED_RESIDUALS — 0 BLOCKERs, 5+ HIGH/MEDIUM residuals.
# **Falsifier:** Any BLOCKER row (→ READY_CONDITIONAL/NOT_READY) or 0 HIGH/MEDIUM (→ READY_FULL).

# %%
import csv
import os

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
ARTIFACTS = os.path.join(REPO_ROOT, "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates")

# Read risk register
risks = list(csv.DictReader(open(os.path.join(ARTIFACTS, "risk_register_sc2egset.csv"))))
blockers = [r for r in risks if r["severity"] == "BLOCKER"]
high_med = [r for r in risks if r["severity"] in ("HIGH", "MEDIUM")]

print(f"BLOCKERs: {len(blockers)}")
print(f"HIGH/MEDIUM: {len(high_med)}")

assert len(blockers) == 0, f"Unexpected BLOCKERs: {blockers}"
assert len(high_med) >= 2, "Fewer than expected HIGH/MEDIUM residuals"

verdict = "READY_WITH_DECLARED_RESIDUALS"
print(f"Verdict: {verdict}")

# %%
md = f"""# Modeling Readiness Decision — sc2egset

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced by:** 01_06_04 (Phase 01 Decision Gates)
**Date:** 2026-04-19

---

## 1. Verdict

**{verdict}**

Per spec §2: zero BLOCKER risks; {len(high_med)} HIGH/MEDIUM residuals documented with Chapter 4 thesis-defence anchors.
Phase 02 proceeds **unconditionally**; residuals are addressed in the thesis text.

---

## 2. Flip-Predicate

**N/A** — READY_WITH_DECLARED_RESIDUALS has no flip-predicate. Residuals are declared and accepted;
they do not block Phase 02. To upgrade to READY_FULL, all HIGH/MEDIUM residuals would need to be
resolved as LOW or RESOLVED (not a planned action for this thesis workstream).

---

## 3. BLOCKER List

**None.** Risk register contains 0 BLOCKER rows.

---

## 4. HIGH/MEDIUM Residuals with Chapter 4 Anchors

| Risk ID | Severity | Category | Chapter 4 Anchor |
|---------|----------|----------|-----------------|
"""
for r in high_med:
    md += f"| {r['risk_id']} | {r['severity']} | {r['category']} | {r['thesis_defence_reference']} |\n"

md += f"""
### Residual details:

- **SC-R03 [HIGH] — ICC INCONCLUSIVE (0.0463):** Between-player variance is non-zero but small; CI [0.028, 0.064]
  does not permit a confident HOLDS/FALSIFIED verdict. Documented at **§4.4.5** (ICC estimator choice).
  Phase 02 skill features are included but their marginal effect may be small.

- **SC-R04 [HIGH] — Tournament-only population ([POP:tournament]):** sc2egset covers professional/competitive
  players only. Heckman (1979) selection bias applies. Documented at **§4.1.4** (population scope framing).
  Cross-dataset comparisons to aoe2companion (30.5M ranked-ladder matches) must note this scope asymmetry.

- **SC-R06 [MEDIUM] — Uncohort-filtered PSI:** Tournament structure (N=152 cohort players) prevents
  conditional PSI. Documented at **§4.4.5**. Phase 02 should note unconditional-PSI limitation in
  feature drift analysis.

- **SC-R07 [MEDIUM] — 2023-Q3 duration drift (|d|=0.544):** Medium effect-size drift in a sparse quarter
  (122 matches). Documented at **§4.1.1**. Phase 02 temporal CV should flag 2023-Q3 as a drift-sentinel
  quarter.

- **SC-R01 [MEDIUM] — Identity branch (iii) cross-region bias:** ~12% cross-region migration accepted.
  Documented at **§4.2.2** (Identity Resolution).

---

## 5. Phase 02 Go/No-Go

**GO — full scope.**

Phase 02 feature engineering for sc2egset may proceed at full scope:
- Pre-game skill features (ELO proxy via `is_mmr_missing`, win-rate, faction)
- Map/context features (map, region, start location)
- Historical match activity features
- In-game-state features (APM, SQ, supplyCappedPercent) — sc2egset-exclusive; D6 asymmetry flag noted

All features must pass I3 temporal classification check (PRE_GAME or post-game aggregates of prior history).

---

## 6. Role Assignment Summary

See cross-dataset rollup: `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`

| Dimension | sc2egset role |
|-----------|---------------|
| D1 Sample-scale | SUPPLEMENTARY (~22k 1v1 matches vs ~30.5M aoe2companion) |
| D2 Skill-signal (ICC) | **PRIMARY** (ICC 0.046; passes F1 0.046 ≥ 0.01 AND F2 INVARIANTS §5 I8 = PARTIAL which passes per spec §3 D2; largest point-estimate ICC among F1+F2 passers) |
| D3 Temporal coverage | SUPPLEMENTARY (tournament-sparse; sparse quarters below density floor) |
| D4a Identity rename-stability | SUPPLEMENTARY (Branch iii, region-scoped) |
| D4b Identity within-scope rigor | **co-PRIMARY** (within-region collision 30.6%; cross-region ~12% documented — orthogonal to aoe2companion's D4a rename-stability win per rollup §3 D4b) |
| D5 Patch resolution | SUPPLEMENTARY (no patch_id binding; version string available but not patch-anchored) |
| D6 Controlled-asymmetry flag | in-game events parseable (asymmetry flag only, not role-bearing) |
"""

out_path = os.path.join(ARTIFACTS, "modeling_readiness_sc2egset.md")
with open(out_path, "w") as f:
    f.write(md)
print(f"Wrote {out_path}")
print(f"Verdict: {verdict}")
print(f"Gate: PASS")
