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
# # 01_06_03 — Risk Register (aoe2companion)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** INVARIANTS.md §5 PARTIAL rows (I2, I8) all covered; no BLOCKER present;
#   ICC FALSIFIED 0.003 documented as HIGH residual with §4.4.5 anchor.
# **Falsifier:** BLOCKER present (→ READY_CONDITIONAL); or ICC finding without thesis anchor.

# %%
import csv, os

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates")

risks = [
    {
        "risk_id": "AC-R01",
        "category": "IDENTITY",
        "description": (
            "Identity-rate reconciliation: 2.57% rename-rate (97.43% stable profiles) and "
            "3.55% name-collision-rate (same name, multiple profileIds). Both below 15% "
            "within-scope rigor threshold. Branch (i) API-namespace, rename-stable. "
            "Cross-dataset namespace bridge to aoestats confirmed VERDICT A (0.9960 agreement). "
            "INVARIANTS.md §5 I2 row: PARTIAL (rename rate <15%, collision <5%)."
        ),
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json",
        "severity": "LOW",
        "phase02_implication": "Identity key is profileId; both rename and collision rates below threshold. Phase 02 may proceed with profileId as-is.",
        "thesis_defence_reference": "§4.2.2",
        "mitigation_status": "RESOLVED (documented in thesis)",
    },
    {
        "risk_id": "AC-R02",
        "category": "ICC_SIGNAL",
        "description": (
            "ICC FALSIFIED: ANOVA ICC (N=5k cohort, n=360,567 player-obs) = 0.003013 "
            "[0.001724, 0.004202]. Substantially below 0.05 threshold. Consistent across "
            "sample sizes (N=10k: 0.003574; N=20k ANOVA: 0.00324). Attributed to "
            "ranked-ladder population heterogeneity (vs. tournament-selection in sc2egset). "
            "INVARIANTS.md §5 I8 row: FALSIFIED at reference window."
        ),
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc.json",
        "severity": "HIGH",
        "phase02_implication": "INVARIANTS.md §5 I8 row: FALSIFIED. Per-player features included but marginal effect expected to be small. Thesis §4.4.5 must document with defence. ICC should not be re-evaluated (stable across sample sizes).",
        "thesis_defence_reference": "§4.4.5",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "AC-R03",
        "category": "TEMPORAL_LEAKAGE",
        "description": (
            "Temporal leakage audit PASSED (01_05_08, v2 post-adversarial review). "
            "All 3 checks passed: reference cohort bounds correct; quarter-label consistency "
            "0 violations; PSI reference SQL cites spec §7 timestamp bounds verbatim. "
            "No POST_GAME tokens in PRE_GAME feature selection contexts."
        ),
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_leakage_audit.json",
        "severity": "RESOLVED",
        "phase02_implication": "No leakage risk. I3 guard confirmed in DGP diagnostics (01_05_06).",
        "thesis_defence_reference": "§4.2.3",
        "mitigation_status": "RESOLVED",
    },
    {
        "risk_id": "AC-R04",
        "category": "FEATURE_DRIFT",
        "description": (
            "map_id PSI > 1.1 in ALL 8 quarters (flagged_for_review). Driven by regular "
            "AoE2 map pool rotations (new maps each season; DLC maps with unknown category "
            "counts of 170K–425K per quarter). faction drift from 2023-Q3 (PSI=0.252–0.482) "
            "driven by DLC civilization releases (Dynasties of India, Return of Rome). "
            "rating drift from 2023-Q3 (PSI≈0.7, Cohen's d≈0.6) from ELO inflation/matchmaking "
            "changes. `won` (target proxy) fully stable (PSI=0.0, cohen_h=0.0) in all quarters."
        ),
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_02_psi_shift.json",
        "severity": "MEDIUM",
        "phase02_implication": "map_id requires unknown-category handling in Phase 02 temporal CV (mandatory). faction and rating drift from 2023-Q3 require temporal CV split at 2023-Q2/Q3 boundary. Documented at §4.1.2.",
        "thesis_defence_reference": "§4.1.2",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "AC-R05",
        "category": "DURATION_QUALITY",
        "description": (
            "358 clock-skew rows (duration_seconds < 0, i.e. finished < started) and "
            "142 outlier rows (duration > 86400s = 24h) retained in matches_1v1_clean "
            "with is_duration_negative / is_duration_suspicious flags. Duration is "
            "POST_GAME_HISTORICAL; does not affect prediction label `won`. I3 guard "
            "confirmed (duration not used as PRE_GAME feature). Total: 500 flagged rows "
            "out of 30,531,196 (rate: 0.0016%)."
        ),
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json",
        "severity": "LOW",
        "phase02_implication": "Duration POST_GAME_HISTORICAL; Phase 02 must not use duration_seconds as PRE_GAME feature (I3 enforced). Flag columns available for filtering if needed.",
        "thesis_defence_reference": "§4.2.3",
        "mitigation_status": "RESOLVED (flagged, not removed; rate 0.0016%)",
    },
]

blockers = [r for r in risks if r["severity"] == "BLOCKER"]
high_med = [r for r in risks if r["severity"] in ("HIGH", "MEDIUM")]
print(f"BLOCKERs: {len(blockers)}")
print(f"HIGH/MEDIUM: {len(high_med)}")
assert len(blockers) == 0, f"Unexpected BLOCKERs: {blockers}"
assert len(high_med) >= 2, "Fewer than expected HIGH/MEDIUM residuals"
print("Gate: PASS (0 BLOCKERs)")

csv_path = os.path.join(OUT_DIR, "risk_register_aoe2companion.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(risks[0].keys()))
    w.writeheader()
    w.writerows(risks)
print(f"Wrote {csv_path}")

md = "# Risk Register — aoe2companion\n\n"
md += "**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0\n"
md += "**Date:** 2026-04-19\n\n"
md += f"## Severity Distribution\n\n"
md += f"- BLOCKER: {len(blockers)}\n"
md += f"- HIGH: {len([r for r in risks if r['severity']=='HIGH'])}\n"
md += f"- MEDIUM: {len([r for r in risks if r['severity']=='MEDIUM'])}\n"
md += f"- LOW: {len([r for r in risks if r['severity']=='LOW'])}\n"
md += f"- RESOLVED: {len([r for r in risks if r['severity']=='RESOLVED'])}\n\n"
md += "**0 BLOCKERs.** Verdict: READY_WITH_DECLARED_RESIDUALS. Phase 02 GO full scope.\n\n"
for r in risks:
    md += f"### {r['risk_id']} [{r['severity']}] — {r['category']}\n\n{r['description']}\n\n"
    md += f"- **Evidence:** `{r['evidence_artifact']}`\n"
    md += f"- **Phase 02:** {r['phase02_implication']}\n"
    md += f"- **Thesis:** {r['thesis_defence_reference']}\n"
    md += f"- **Mitigation:** {r['mitigation_status']}\n\n"

md_path = os.path.join(OUT_DIR, "risk_register_aoe2companion.md")
with open(md_path, "w") as f:
    f.write(md)
print(f"Wrote {md_path}")
