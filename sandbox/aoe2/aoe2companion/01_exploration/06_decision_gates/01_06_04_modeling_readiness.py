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
# # 01_06_04 — Modeling Readiness Decision (aoe2companion)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** aoe2companion is READY_WITH_DECLARED_RESIDUALS — 0 BLOCKERs; ICC FALSIFIED
#   (0.003013) is a HIGH residual with §4.4.5 defence anchor; not a blocker.
#   Phase 02 proceeds unconditionally at full scope. Flip-predicate N/A.
# **Falsifier:** Any BLOCKER row (→ READY_CONDITIONAL) or 0 HIGH/MEDIUM (→ READY_FULL).

# %%
import csv
import os

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
ARTIFACTS = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates")

# Read risk register
risks = list(csv.DictReader(open(os.path.join(ARTIFACTS, "risk_register_aoe2companion.csv"))))
blockers = [r for r in risks if r["severity"] == "BLOCKER"]
high_med = [r for r in risks if r["severity"] in ("HIGH", "MEDIUM")]

print(f"BLOCKERs: {len(blockers)}")
print(f"HIGH/MEDIUM: {len(high_med)}")

assert len(blockers) == 0, f"Expected 0 BLOCKERs, got {len(blockers)}: {blockers}"
assert len(high_med) >= 1, f"Expected ≥1 HIGH/MEDIUM residuals: {len(high_med)}"

verdict = "READY_WITH_DECLARED_RESIDUALS"
print(f"Verdict: {verdict}")

# %%
md = f"""# Modeling Readiness Decision — aoe2companion

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced by:** 01_06_04 (Phase 01 Decision Gates)
**Date:** 2026-04-19

---

## 1. Verdict

**{verdict}**

Per spec §2: zero BLOCKER risks; {len(high_med)} HIGH/MEDIUM residuals documented with Chapter 4
thesis-defence anchors. Phase 02 proceeds **unconditionally** at full scope; residuals are
addressed in the thesis text.

---

## 2. Flip-Predicate

**N/A** — READY_WITH_DECLARED_RESIDUALS has no flip-predicate. Residuals are declared and
accepted; they do not block Phase 02. To upgrade to READY_FULL, all HIGH/MEDIUM residuals
would need to be resolved as LOW or RESOLVED (not a planned action for this thesis workstream).

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

- **AC-R02 [HIGH] — ICC FALSIFIED (0.003013):** Between-player variance is non-zero but
  extremely small; ANOVA ICC = 0.003013 [0.001724, 0.004202] substantially below 0.05 threshold.
  Consistent across sample sizes (N=5k/10k/20k). Attributed to ranked-ladder population
  heterogeneity — the full AoE2 playerbase includes all skill levels, diluting ICC signal.
  Documented at **§4.4.5**. Phase 02 per-player features included for cross-dataset consistency
  with sc2egset; marginal effect expected to be small. Note: aoe2companion ICC=0.003 is
  substantially lower than sc2egset ICC=0.046 (INCONCLUSIVE), reflecting the tournament-vs-ladder
  population difference.

- **AC-R04 [MEDIUM] — Feature drift (map_id, faction, rating):** map_id PSI > 1.1 in all
  8 quarters due to regular map pool rotations. faction drift from 2023-Q3 due to DLC
  civilization releases. rating drift from 2023-Q3 (d≈0.6). `won` target proxy fully stable.
  Documented at **§4.1.2**. Phase 02 temporal CV must treat map_id as high-churn categorical
  with unknown-category handling mandatory; temporal split at 2023-Q2/Q3 boundary for
  faction/rating features.

---

## 5. Phase 02 Go/No-Go

**GO — full scope.**

Phase 02 feature engineering for aoe2companion may proceed at full scope:
- Pre-game skill features (rating, is_unrated_proxy, win-rate)
- Faction / civilization features (with unknown-category handling for map_id)
- Historical match activity features
- Identity features (profileId Branch (i), rename/collision rates documented)

All features must pass I3 temporal classification check (PRE_GAME or post-game aggregates
of prior history). duration_seconds is POST_GAME_HISTORICAL — must not be used as a PRE_GAME
feature (I3 guard confirmed in 01_05_06).

---

## 6. Role Assignment Summary

See cross-dataset rollup: `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`

| Dimension | aoe2companion role |
|-----------|--------------------|
| D1 Sample-scale | **PRIMARY** (~30.5M 1v1 clean matches; largest of 3 datasets) |
| D2 Skill-signal (ICC) | SUPPLEMENTARY (ICC 0.003 FALSIFIED; sc2egset is D2 PRIMARY) |
| D3 Temporal coverage | **PRIMARY** (2020-Q3 to 2026-Q2; longest span; all quarters above density floor) |
| D4a Identity rename-stability | **co-PRIMARY** (Branch i API-namespace; 2.57% rename; 3.55% collision; below 15% threshold) |
| D4b Identity within-scope rigor | **co-PRIMARY** (within-scope rates documented with SQL; VERDICT A 0.9960 cross-dataset) |
| D5 Patch resolution | SUPPLEMENTARY (no patch_id column; patch version available in separate table but not bound to matches) |
| D6 Controlled-asymmetry flag | N/A (flag only; not role-bearing) |
"""

out_path = os.path.join(ARTIFACTS, "modeling_readiness_aoe2companion.md")
with open(out_path, "w") as f:
    f.write(md)
print(f"Wrote {out_path}")
print(f"Verdict: {verdict}")
print(f"Gate: PASS")
