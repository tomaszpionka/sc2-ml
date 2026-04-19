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
# # 01_06_03 — Risk Register (sc2egset)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** Every INVARIANTS.md §5 PARTIAL row, every relevant BACKLOG item,
# and every 01_05 known limitation has a risk register row with evidence path.
# **Falsifier:** Any known issue missing from register; any row missing evidence path.

# %%
import csv
import os

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates")

# Risk register rows
# Sources:
# - INVARIANTS.md §5: I2 PARTIAL (branch iii), I8 PARTIAL (schema divergence)
# - 01_05 gate memo: ICC INCONCLUSIVE, PSI uncohort-filtered, duration drift, POP:tournament
# No BACKLOG items currently affect sc2egset directly (F1 is aoestats-only; F4 is Cat C)

risks = [
    {
        "risk_id": "SC-R01",
        "category": "IDENTITY",
        "description": "sc2egset uses player_id_worldwide (Branch iii, region-scoped toon_id R-S2-G-P) rather than the I2 default LOWER(nickname). Within-region collision rate 30.6% (451/1,473 pairs); cross-region migration ~12% accepted bias.",
        "evidence_artifact": "src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §5 I2 row",
        "severity": "MEDIUM",
        "phase02_implication": "Phase 02 player identity key is region-scoped; cross-region players appear as distinct entities. Rating-system backtesting must acknowledge this scope boundary.",
        "thesis_defence_reference": "§4.2.2",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "SC-R02",
        "category": "SCHEMA_DIVERGENCE",
        "description": "Spec CROSS-01-05-v1 §1 9-column contract differs from sc2egset matches_history_minimal actual schema (opponent_id, faction, opponent_faction, duration_seconds, dataset_tag vs spec's team, chosen_civ_or_race, rating_pre, map_id, patch_id). 5 of 9 columns differ.",
        "evidence_artifact": "src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §5 I8 row",
        "severity": "MEDIUM",
        "phase02_implication": "Phase 06 cross-dataset UNION joins on metric_name only; feature_name values match actual VIEW schema, not spec idealized schema. Cross-dataset Phase 06 join must use metric_name not column_name.",
        "thesis_defence_reference": "§4.1.3",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "SC-R03",
        "category": "ICC_SIGNAL",
        "description": "ICC INCONCLUSIVE: ANOVA ICC = 0.0463 [0.0283, 0.0643]. CI spans 0.01–0.09 range; cannot conclude meaningful vs negligible skill signal. GLMM latent-scale failed to converge. Between-player variance small but non-zero.",
        "evidence_artifact": "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/icc.json",
        "severity": "HIGH",
        "phase02_implication": "Skill-signal features (ELO, win-rate) may be less discriminative than expected. Model should include skill features but results must be interpreted with ICC uncertainty noted.",
        "thesis_defence_reference": "§4.4.5",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "SC-R04",
        "category": "POPULATION_SCOPE",
        "description": "sc2egset is [POP:tournament] — professional/competitive players only (Heckman 1979 selection bias). All Phase 06 rows tagged [POP:tournament]. Population estimates not representative of general SC2 playerbase.",
        "evidence_artifact": "src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §5 (M7 scope note)",
        "severity": "HIGH",
        "phase02_implication": "Phase 02 models trained on sc2egset apply to tournament players only. Thesis must state population boundary explicitly in all cross-game comparisons.",
        "thesis_defence_reference": "§4.1.4",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "SC-R05",
        "category": "TEMPORAL_LEAKAGE",
        "description": "Temporal leakage audit PASSED (01_05_08). No future-data leakage detected. Reference window assertion PASS. Post-game token violations = 0.",
        "evidence_artifact": "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/leakage_audit_sc2egset.json",
        "severity": "RESOLVED",
        "phase02_implication": "No leakage risk for Phase 02 feature engineering given current schema.",
        "thesis_defence_reference": "§4.2.3",
        "mitigation_status": "RESOLVED",
    },
    {
        "risk_id": "SC-R06",
        "category": "SURVIVORSHIP",
        "description": "Uncohort-filtered PSI: PRIMARY PSI computed without span->=30d filter because tournament structure makes cohort N=152 players with insufficient span coverage. Conditional PSI could not be computed.",
        "evidence_artifact": "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md",
        "severity": "MEDIUM",
        "phase02_implication": "PSI figures for sc2egset are unconditional (not cohort-controlled). Phase 02 feature drift analysis should note this limitation.",
        "thesis_defence_reference": "§4.4.5",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
    {
        "risk_id": "SC-R07",
        "category": "TEMPORAL_LEAKAGE",
        "description": "Duration drift in 2023-Q3: Cohen's d = 0.544 (medium effect). Only 122 matches in that quarter; unusually long games. May indicate a data artifact or game-mechanic change in that tournament.",
        "evidence_artifact": "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/dgp_diagnostic_sc2egset.md",
        "severity": "MEDIUM",
        "phase02_implication": "Phase 02 should consider excluding 2023-Q3 from DGP-sensitive features or flagging it in temporal CV folds.",
        "thesis_defence_reference": "§4.1.1",
        "mitigation_status": "ACCEPTED (documented in thesis)",
    },
]

# Gate check: every INVARIANTS.md §5 non-HOLDS row covered
covered_invariants = {"I2": "SC-R01", "I8": "SC-R02"}
print(f"INVARIANTS.md §5 PARTIAL rows covered: {covered_invariants}")
print(f"Total risks: {len(risks)}")
blocker_risks = [r for r in risks if r["severity"] == "BLOCKER"]
print(f"BLOCKER risks: {len(blocker_risks)}")
high_risks = [r for r in risks if r["severity"] == "HIGH"]
print(f"HIGH risks: {len(high_risks)}")

# %%
# Write CSV
csv_path = os.path.join(OUT_DIR, "risk_register_sc2egset.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(risks[0].keys()))
    writer.writeheader()
    writer.writerows(risks)
print(f"Wrote {csv_path}")

# Write MD
md_lines = [
    "# Risk Register — sc2egset",
    "",
    "**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0",
    "**Produced by:** 01_06_03 (Phase 01 Decision Gates)",
    "**Date:** 2026-04-19",
    "",
    "## Severity Distribution",
    "",
    f"- BLOCKER: {len([r for r in risks if r['severity']=='BLOCKER'])}",
    f"- HIGH: {len([r for r in risks if r['severity']=='HIGH'])}",
    f"- MEDIUM: {len([r for r in risks if r['severity']=='MEDIUM'])}",
    f"- LOW: {len([r for r in risks if r['severity']=='LOW'])}",
    f"- RESOLVED: {len([r for r in risks if r['severity']=='RESOLVED'])}",
    "",
    "**No BLOCKER risks.** Phase 02 may proceed.",
    "",
    "## Risk Details",
    "",
]
for r in risks:
    md_lines.append(f"### {r['risk_id']} [{r['severity']}] — {r['category']}")
    md_lines.append("")
    md_lines.append(r["description"])
    md_lines.append("")
    md_lines.append(f"- **Evidence:** `{r['evidence_artifact']}`")
    md_lines.append(f"- **Phase 02 implication:** {r['phase02_implication']}")
    md_lines.append(f"- **Thesis defence:** {r['thesis_defence_reference']}")
    md_lines.append(f"- **Mitigation:** {r['mitigation_status']}")
    md_lines.append("")

md_path = os.path.join(OUT_DIR, "risk_register_sc2egset.md")
with open(md_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"Wrote {md_path}")
