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
# # 01_06_03 — Risk Register (aoestats)
# **Hypothesis:** INVARIANTS.md §5 PARTIAL rows (I2, I5, I8) all covered; BLOCKER for canonical_slot present.
# **Falsifier:** BLOCKER missing; INVARIANTS row without risk_id.

# %%
import csv, os
REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates")

risks = [
    {
        "risk_id": "AO-R01",
        "category": "SLOT_ASYMMETRY",
        "description": "canonical_slot column ABSENT from matches_history_minimal. W3 ARTEFACT_EDGE (01_04_05): upstream API assigns team=1 to higher-ELO player in 80.3% of matches, creating team1_wins ~52.27% base-rate artefact. Per-slot features forbidden until BACKLOG F1 resolved.",
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json",
        "severity": "BLOCKER",
        "phase02_implication": "Per-slot features (p0_civ, p1_civ, p0_old_rating, p1_old_rating) forbidden. Aggregate / UNION-ALL-symmetric features permitted (faction, opponent_faction, old_rating via player_history_all). Scope: GO-NARROW.",
        "thesis_defence_reference": "§4.4.6",
        "mitigation_status": "OPEN (BACKLOG F1)",
    },
    {
        "risk_id": "AO-R02",
        "category": "IDENTITY",
        "description": "aoestats uses profile_id (Branch v, structurally-forced): no visible handle column exists to compare identity candidates. Migration and collision rates unevaluable within aoestats alone. Cross-dataset namespace bridge to aoe2companion confirmed VERDICT A (0.9960 agreement).",
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md §5 I2 row",
        "severity": "MEDIUM",
        "phase02_implication": "Identity key is structurally forced; no alternative candidate. Phase 02 may proceed with profile_id as-is.",
        "thesis_defence_reference": "§4.2.2",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "AO-R03",
        "category": "ICC_SIGNAL",
        "description": "ICC FALSIFIED: ANOVA ICC (N=10 cohort, n=744 players) = 0.0268 [0.0148, 0.0387]. Below 0.05 threshold. Attributed to early crawler period (2022-Q3: 744 active players). Between-player variance detectable but small.",
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.json",
        "severity": "HIGH",
        "phase02_implication": "INVARIANTS.md §5 I8 row: PARTIAL — ICC FALSIFIED in 2022-Q3 reference. Phase 02 may proceed with per-player features but thesis must document this limitation. ICC should be re-evaluated in a denser quarter.",
        "thesis_defence_reference": "§4.4.5",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "AO-R04",
        "category": "TEMPORAL_LEAKAGE",
        "description": "Temporal leakage audit PASSED (01_05_06). No temporal leakage detected. canonical_slot absent; [PRE-canonical_slot] flag ACTIVE.",
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.json",
        "severity": "RESOLVED",
        "phase02_implication": "No leakage risk. [PRE-canonical_slot] flag prevents per-slot feature extraction.",
        "thesis_defence_reference": "§4.2.3",
        "mitigation_status": "RESOLVED",
    },
    {
        "risk_id": "AO-R05",
        "category": "ICC_SIGNAL",
        "description": "B3 coincidence: reference start 2022-08-29 coincides with earliest dataset date. Match count jumps ~22x from 2022-Q3 (18k) to 2023-Q1 (404k), reflecting crawler expansion. PSI increases in early quarters may reflect population drift OR crawler expansion confound.",
        "evidence_artifact": "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md",
        "severity": "MEDIUM",
        "phase02_implication": "Counterfactual PSI (2023-Q1 reference) available to disambiguate. Phase 02 should use 2023-Q1 as secondary reference window for PSI analysis.",
        "thesis_defence_reference": "§4.1.2",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
]

blockers = [r for r in risks if r["severity"]=="BLOCKER"]
high_med = [r for r in risks if r["severity"] in ("HIGH","MEDIUM")]
print(f"BLOCKERs: {len(blockers)} (AO-R01: canonical_slot)")
assert len(blockers)==1 and blockers[0]["risk_id"]=="AO-R01"
print(f"HIGH/MEDIUM: {len(high_med)}")

csv_path = os.path.join(OUT_DIR, "risk_register_aoestats.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(risks[0].keys()))
    w.writeheader()
    w.writerows(risks)
print(f"Wrote {csv_path}")

md = "# Risk Register — aoestats\n\n**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0\n**Date:** 2026-04-19\n\n"
md += f"## Severity Distribution\n\n- BLOCKER: {len(blockers)}\n- HIGH: {len([r for r in risks if r['severity']=='HIGH'])}\n- MEDIUM: {len([r for r in risks if r['severity']=='MEDIUM'])}\n- RESOLVED: {len([r for r in risks if r['severity']=='RESOLVED'])}\n\n"
md += "**1 BLOCKER (AO-R01 canonical_slot).** Verdict: READY_CONDITIONAL. Phase 02 GO-NARROW (aggregate features only).\n\n"
for r in risks:
    md += f"### {r['risk_id']} [{r['severity']}] — {r['category']}\n\n{r['description']}\n\n"
    md += f"- **Evidence:** `{r['evidence_artifact']}`\n"
    md += f"- **Phase 02:** {r['phase02_implication']}\n"
    md += f"- **Thesis:** {r['thesis_defence_reference']}\n"
    md += f"- **Mitigation:** {r['mitigation_status']}\n\n"

md_path = os.path.join(OUT_DIR, "risk_register_aoestats.md")
with open(md_path, "w") as f:
    f.write(md)
print(f"Wrote {md_path}")
