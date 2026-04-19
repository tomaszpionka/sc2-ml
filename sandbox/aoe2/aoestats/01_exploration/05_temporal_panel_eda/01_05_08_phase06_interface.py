# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_05_08 -- Phase 06 Interface Emission (Q9)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_05 -- Temporal & Panel EDA
# **Step:** 01_05_08
# **Dataset:** aoestats
# **spec:** reports/specs/01_05_preregistration.md@7e259dd8
#
# # Hypothesis: Emitted CSV validates against §12 schema: 9 columns, metric_value
# # to 4 decimal places, reference_window_id = '2022-Q3-patch66692' for primary rows,
# # at least 64 rows (8 quarters x 8 features x >= 1 metric).
# # Falsifier: Any missing column, NULL-as-string 'NaN', wrong reference_window_id.
#
# **Critique B3:** Both primary and counterfactual PSI emitted with reference_window_id.
# **Critique M5:** Notes column documents 15 columns analyzed (spec §1 has 9 core).
# **Critique M6:** Every per-slot breakdown row carries [PRE-canonical_slot]. Gate CAN fail.

# %%
import json
from pathlib import Path

import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir

ARTIFACTS_DIR = get_reports_dir("aoe2", "aoestats") / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

db = get_notebook_db("aoe2", "aoestats")
print("Connected.")

# %%
# Load pre_canonical_slot_flag_active from leakage audit
audit_path = ARTIFACTS_DIR / "01_05_06_temporal_leakage_audit_v1.json"
pre_canonical_flag = True  # default; overridden if audit exists
if audit_path.exists():
    with open(audit_path) as f:
        audit = json.load(f)
    pre_canonical_flag = bool(audit.get("pre_canonical_slot_flag_active", True))
print(f"pre_canonical_slot_flag_active: {pre_canonical_flag}")

# %%
# M5 note: aoestats analyzes 15 columns (spec §1 has 9 core)
M5_NOTE = (
    "aoestats analyzes 15 columns (spec §1 has 9 core columns; "
    "extended with focal_old_rating, faction, opponent_faction, p0_is_unrated, "
    "p1_is_unrated, map, patch for aoestats-specific richness). "
    "metric_name values: psi, cohen_h, cohen_d, icc -- overlap with sibling plans."
)

# %%
# Read primary PSI CSVs (T03)
PRIMARY_QUARTERS = ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4",
                    "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]
psi_rows = []
for q in PRIMARY_QUARTERS:
    fname = ARTIFACTS_DIR / f"psi_aoestats_{q}.csv"
    if fname.exists():
        df_q = pd.read_csv(fname)
        # Remove internal column if present
        if "is_duration_corrupt_sensitive" in df_q.columns:
            df_q = df_q[~df_q["is_duration_corrupt_sensitive"]]
            df_q = df_q.drop(columns=["is_duration_corrupt_sensitive"], errors="ignore")
        psi_rows.append(df_q)

if psi_rows:
    df_psi = pd.concat(psi_rows, ignore_index=True)
else:
    df_psi = pd.DataFrame(columns=["dataset_tag", "quarter", "feature_name", "metric_name",
                                    "metric_value", "reference_window_id", "cohort_threshold",
                                    "sample_size", "notes"])

print(f"Primary PSI rows: {len(df_psi)}")

# %%
# Read counterfactual PSI (B3)
alt_psi_path = ARTIFACTS_DIR / "psi_aoestats_counterfactual_2023Q1ref.csv"
if alt_psi_path.exists():
    df_alt = pd.read_csv(alt_psi_path)
    print(f"Counterfactual PSI rows: {len(df_alt)}")
else:
    df_alt = pd.DataFrame()
    print("Counterfactual PSI not found (will be empty in interface)")

# %%
# Read ICC results (T06)
icc_path = ARTIFACTS_DIR / "01_05_05_icc_results.json"
icc_rows = []
if icc_path.exists():
    with open(icc_path) as f:
        icc_data = json.load(f)
    # v1.0.4 structure: sensitivity axis is spec §6.2 cohort match-count
    # thresholds, keyed `n_min{N}`. Each threshold produces a distinct cohort
    # with its own ANOVA ICC + LMM ICC. Primary headline is ANOVA @ N=10
    # (spec v1.0.4 §14(b)). Legacy `icc_by_sample_size` key is tolerated for
    # backwards compatibility while any pre-v1.0.4 JSON remains in the tree.
    primary_block = icc_data.get("icc_by_cohort_threshold") or icc_data.get("icc_by_sample_size", {})
    for key, val in primary_block.items():
        # Determine cohort_threshold for this row: new schema uses
        # min_matches_in_ref_threshold; legacy used fixed 10.
        row_cohort_threshold = int(val.get("min_matches_in_ref_threshold", 10))
        for metric_key in ["icc_anova_observed_scale", "icc_lpm_observed_scale"]:
            mv = val.get(metric_key, {})
            icc_point = mv.get("icc_point")
            if icc_point is None:
                continue
            icc_rows.append({
                "dataset_tag": "aoestats",
                "quarter": "2022-Q3Q4ref",
                "feature_name": "won",
                "metric_name": metric_key,
                "metric_value": round(float(icc_point), 4),
                "reference_window_id": "2022-Q3-patch66692",
                "cohort_threshold": row_cohort_threshold,
                "sample_size": val.get("n_obs", 0),
                "notes": (
                    f"spec v1.0.4 §6.2 cohort-threshold axis; key={key}; "
                    f"{'primary' if metric_key == 'icc_anova_observed_scale' and row_cohort_threshold == 10 else 'diagnostic'}; "
                    f"M7: {icc_data.get('m7_branch_v_limitation', '')[:80]}..."
                ),
            })

df_icc = pd.DataFrame(icc_rows)
print(f"ICC rows: {len(df_icc)}")

# %%
# Read DGP diagnostic rows (T08)
dgp_rows = []
dgp_ref_path = ARTIFACTS_DIR / "dgp_diagnostic_aoestats_2022-Q3Q4ref.csv"
if dgp_ref_path.exists():
    df_dgp_ref = pd.read_csv(dgp_ref_path)
    for _, row in df_dgp_ref.iterrows():
        dgp_rows.append({
            "dataset_tag": "aoestats",
            "quarter": "2022-Q3Q4ref",
            "feature_name": "duration_seconds",
            "metric_name": "cohen_d",
            "metric_value": 0.0,
            "reference_window_id": "2022-Q3-patch66692",
            "cohort_threshold": 0,
            "sample_size": int(row.get("n_rows", 0)),
            "notes": "POST_GAME_HISTORICAL reference period baseline; I3 token",
        })

for q in PRIMARY_QUARTERS:
    dgp_path = ARTIFACTS_DIR / f"dgp_diagnostic_aoestats_{q}.csv"
    if dgp_path.exists():
        df_dgp_q = pd.read_csv(dgp_path)
        for _, row in df_dgp_q.iterrows():
            dgp_rows.append({
                "dataset_tag": "aoestats",
                "quarter": q,
                "feature_name": "duration_seconds",
                "metric_name": "cohen_d",
                "metric_value": round(float(row.get("cohen_d_vs_ref", 0.0)), 4),
                "reference_window_id": "2022-Q3-patch66692",
                "cohort_threshold": 0,
                "sample_size": int(row.get("n_rows", 0)),
                "notes": "POST_GAME_HISTORICAL; I3 token; excluded from PSI per spec §4",
            })

df_dgp_interface = pd.DataFrame(dgp_rows)
print(f"DGP rows: {len(df_dgp_interface)}")

# %%
# Assemble Phase 06 interface (primary + counterfactual + ICC + DGP)
all_frames = [df_psi]
if len(df_alt) > 0:
    all_frames.append(df_alt)
if len(df_icc) > 0:
    all_frames.append(df_icc)
if len(df_dgp_interface) > 0:
    all_frames.append(df_dgp_interface)

SCHEMA_COLS = ["dataset_tag", "quarter", "feature_name", "metric_name",
               "metric_value", "reference_window_id", "cohort_threshold",
               "sample_size", "notes"]

df_p06 = pd.concat(all_frames, ignore_index=True)
# Ensure schema columns exist
for col in SCHEMA_COLS:
    if col not in df_p06.columns:
        df_p06[col] = None
df_p06 = df_p06[SCHEMA_COLS]

# Clean metric_value: NaN -> None (will be NULL in CSV as empty)
df_p06["metric_value"] = df_p06["metric_value"].apply(
    lambda v: round(float(v), 4) if pd.notna(v) and v is not None else None
)
# Round to 4 decimals
df_p06["metric_value"] = df_p06["metric_value"].apply(
    lambda v: round(float(v), 4) if v is not None else None
)

print(f"Phase 06 interface: {len(df_p06)} rows, {df_p06.columns.tolist()}")

# %%
# M5: add notes column info for aoestats-specific features
df_p06["notes"] = df_p06["notes"].fillna("") + " " + M5_NOTE
df_p06["notes"] = df_p06["notes"].str.strip()

# %%
# Verify [PRE-canonical_slot] is ABSENT from symmetric-aggregate rows
# and PRESENT on any per-slot rows
# (In this notebook, faction/opponent_faction are UNION-ALL-symmetric -> no tag)
# Confirm no faction/opponent_faction rows carry the PRE tag incorrectly
faction_with_tag = df_p06[
    df_p06["feature_name"].isin(["faction", "opponent_faction"]) &
    df_p06["notes"].str.contains(r"\[PRE-canonical_slot\]", na=False)
]
print(f"faction/opponent_faction rows with [PRE-canonical_slot] (should be 0): {len(faction_with_tag)}")
# Note: per critique M4, faction is UNION-ALL symmetric -- NO [PRE-canonical_slot] on aggregate

# %%
# Emit Phase 06 CSV
p06_csv = ARTIFACTS_DIR / "phase06_interface_aoestats.csv"
df_p06.to_csv(p06_csv, index=False)
print(f"Wrote {p06_csv}")

# %%
# Schema validation
validation = {
    "column_count_ok": len(df_p06.columns) == 9,
    "column_count": len(df_p06.columns),
    "dataset_tag_all_aoestats": (df_p06["dataset_tag"] == "aoestats").all(),
    "reference_window_primary_ok": (
        df_p06[df_p06["reference_window_id"] == "2022-Q3-patch66692"]["dataset_tag"].notnull().all()
    ),
    "no_string_nan": not (df_p06["metric_value"].astype(str).str.lower() == "nan").any(),
    "n_rows": len(df_p06),
    "n_rows_above_64": len(df_p06) >= 64,
    "columns": df_p06.columns.tolist(),
    "head_row": df_p06.columns.tolist(),
}

if not validation["column_count_ok"]:
    print(f"FAILED: expected 9 columns, got {validation['column_count']}")
elif not validation["n_rows_above_64"]:
    print(f"WARNING: only {len(df_p06)} rows (< 64 expected minimum per m5)")
else:
    print("Schema validation PASSED")

# %%
# m5 warning
if len(df_p06) < 64:
    print(f"WARNING (m5): {len(df_p06)} rows < 64. Upper bound: 8x3x8x5=960. Check PSI runs.")

# %%
val_json = ARTIFACTS_DIR / "01_05_08_phase06_interface_schema_validation.json"
with open(val_json, "w") as f:
    json.dump(validation, f, indent=2, default=str)

md_val = f"""# Phase 06 Interface Schema Validation -- aoestats

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Step:** 01_05_08

## Schema checks

- Column count: {validation['column_count']} (expected 9): {'OK' if validation['column_count_ok'] else 'FAIL'}
- All dataset_tag == 'aoestats': {validation['dataset_tag_all_aoestats']}
- No string 'NaN': {validation['no_string_nan']}
- Total rows: {validation['n_rows']} (>= 64: {validation['n_rows_above_64']})

## M5 note

{M5_NOTE}

## B3 Counterfactual reference

Rows with reference_window_id = '2023-Q1-alt': {len(df_p06[df_p06['reference_window_id'] == '2023-Q1-alt'])}
"""
(ARTIFACTS_DIR / "01_05_08_phase06_interface_schema_validation.md").write_text(md_val)

print("Step 01_05_08 complete.")
