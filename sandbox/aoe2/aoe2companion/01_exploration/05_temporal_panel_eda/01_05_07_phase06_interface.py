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
#   kernelspec:
#     display_name: rts-predict
#     language: python
#     name: rts-predict
# ---

# %% [markdown]
# # 01_05_07 Phase 06 Interface CSV — aoe2companion
# spec: reports/specs/01_05_preregistration.md@7e259dd8
#
# **Spec §§:** §12 (Phase 06 interface flat schema)
# **Critique fix B-02:** feature_name values match actual VIEW schema (faction, map_id, rating, won);
# `notes` column documents cross-dataset alignment is on metric_name only.
# **Critique fix M-07:** Phase 06 CSV rows tagged with [POP:ranked_ladder] in notes.
#
# Pure aggregation over T03/T04/T06 artifacts. No new analysis.

# %% [markdown]
# ## Imports

# %%
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from rts_predict.common.notebook_utils import get_reports_dir

ARTIFACTS = get_reports_dir("aoe2", "aoe2companion") / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

DATASET_TAG = "aoe2companion"
REFERENCE_WINDOW_ID = "2022-Q3Q4"
DEFAULT_COHORT_THRESHOLD = 10

B02_NOTE = (
    "B-02: feature_name matches VIEW schema (faction, map_id, rating, won). "
    "Cross-dataset alignment is on metric_name only per critique pre-authorization."
)
POP_NOTE = "[POP:ranked_ladder] aoec is online-ladder dataset; findings condition on ranked-ladder participation, not overall AoE2 population."

print("Artifacts dir:", ARTIFACTS)

# %% [markdown]
# ## Load source artifacts

# %%
psi_csv_path = ARTIFACTS / "01_05_02_psi_shift_per_feature.csv"
df_psi = pd.read_csv(psi_csv_path)
print(f"Loaded PSI CSV: {len(df_psi)} rows, features: {df_psi['feature'].unique().tolist()}")

strat_csv_path = ARTIFACTS / "01_05_03_stratification_per_lb.csv"
df_strat = pd.read_csv(strat_csv_path)
print(f"Loaded stratification CSV: {len(df_strat)} rows")

icc_json_path = ARTIFACTS / "01_05_05_icc.json"
icc_data = json.loads(icc_json_path.read_text())
print(f"Loaded ICC JSON: icc_lpm={icc_data['icc_lpm_observed_scale']}")

sens_csv_path = ARTIFACTS / "survivorship_sensitivity.csv"
df_sens = pd.read_csv(sens_csv_path)
print(f"Loaded survivorship sensitivity: {len(df_sens)} rows")

# %% [markdown]
# ## Build Phase 06 interface rows

# %%
rows = []

TESTED_QUARTERS = [
    "2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4",
    "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
]

# T03: PSI rows (rating, faction, map_id, won)
for _, r in df_psi.iterrows():
    base_note = f"{POP_NOTE}; {B02_NOTE}"
    if r["feature"] == "won" and pd.notna(r.get("cohen_h")):
        rows.append({
            "dataset_tag": DATASET_TAG,
            "quarter": r["quarter"],
            "feature_name": "won",
            "metric_name": "cohen_h",
            "metric_value": round(float(r["cohen_h"]), 4),
            "metric_ci_low": None,
            "metric_ci_high": None,            "reference_window_id": REFERENCE_WINDOW_ID,
            "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
            "sample_size": int(r["n_test"]) if pd.notna(r.get("n_test")) else None,
            "notes": f"{base_note}; M-03: h vs reference p_ref",
        })
    if r["feature"] == "rating":
        if pd.notna(r.get("psi")):
            rows.append({
                "dataset_tag": DATASET_TAG,
                "quarter": r["quarter"],
                "feature_name": "rating",
                "metric_name": "psi",
                "metric_value": round(float(r["psi"]), 4),
                "metric_ci_low": None,
                "metric_ci_high": None,                "reference_window_id": REFERENCE_WINDOW_ID,
                "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
                "sample_size": int(r["n_test"]) if pd.notna(r.get("n_test")) else None,
                "notes": f"{base_note}; M-04: Yurdakul 2018 WMU #3208 thresholds not calibrated at N>10^6",
            })
        if pd.notna(r.get("cohen_d")):
            rows.append({
                "dataset_tag": DATASET_TAG,
                "quarter": r["quarter"],
                "feature_name": "rating",
                "metric_name": "cohen_d",
                "metric_value": round(float(r["cohen_d"]), 4),
                "metric_ci_low": None,
                "metric_ci_high": None,                "reference_window_id": REFERENCE_WINDOW_ID,
                "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
                "sample_size": int(r["n_test"]) if pd.notna(r.get("n_test")) else None,
                "notes": base_note,
            })
        if pd.notna(r.get("ks_stat")):
            rows.append({
                "dataset_tag": DATASET_TAG,
                "quarter": r["quarter"],
                "feature_name": "rating",
                "metric_name": "ks_stat",
                "metric_value": round(float(r["ks_stat"]), 4),
                "metric_ci_low": None,
                "metric_ci_high": None,                "reference_window_id": REFERENCE_WINDOW_ID,
                "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
                "sample_size": int(r["n_test"]) if pd.notna(r.get("n_test")) else None,
                "notes": f"{base_note}; M-08: KS on 100k subsample per quarter",
            })
    if r["feature"] in ("faction", "map_id") and pd.notna(r.get("psi")):
        unseen_note = f"__unseen__: {int(r['unseen_count'])} rows" if pd.notna(r.get("unseen_count")) else ""
        rows.append({
            "dataset_tag": DATASET_TAG,
            "quarter": r["quarter"],
            "feature_name": r["feature"],
            "metric_name": "psi",
            "metric_value": round(float(r["psi"]), 4),
            "metric_ci_low": None,
            "metric_ci_high": None,            "reference_window_id": REFERENCE_WINDOW_ID,
            "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
            "sample_size": int(r["n_test"]) if pd.notna(r.get("n_test")) else None,
            "notes": f"{base_note}; {unseen_note}; M-04: Yurdakul 2018 thresholds not calibrated at N>10^6",
        })

# T04: Stratification rows (lb=6, lb=18)
for _, r in df_strat.iterrows():
    if r["feature"] == "faction" and pd.notna(r.get("psi")):
        rows.append({
            "dataset_tag": DATASET_TAG,
            "quarter": r["quarter"],
            "feature_name": "faction",
            "metric_name": "psi",
            "metric_value": round(float(r["psi"]), 4),
            "metric_ci_low": None,
            "metric_ci_high": None,            "reference_window_id": REFERENCE_WINDOW_ID,
            "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
            "sample_size": int(r["n_test"]) if pd.notna(r.get("n_test")) else None,
            "notes": f"{base_note}; {r['scope_note']}; lb={r['leaderboard_id']}",
        })

# T06: ICC rows (LPM + ANOVA + GLMM)
# v1.0.5: CI bounds live on the SAME row as the metric, in `metric_ci_low` /
# `metric_ci_high` columns. Pre-v1.0.5 this notebook emitted
# `metric_name=icc_lpm_ci_low` and `metric_name=icc_lpm_ci_high` as separate
# rows — those names are no longer in the spec §12 closed enumeration and
# would be dropped by a schema-validating consumer.
icc_quarter = "2022Q3-2024Q4"
# ANOVA-observed-scale is the v1.0.4 §14(b) cross-dataset headline.
# Pre-v1.0.5 notebook shape: looked up `icc_anova_ci_low`/`icc_anova_ci_high` —
# those are populated post-PR #163 follow-up. Fall back to None if absent.
rows.append({
    "dataset_tag": DATASET_TAG,
    "quarter": "all",
    "feature_name": "won",
    "metric_name": "icc_anova_observed_scale",
    "metric_value": round(float(icc_data["icc_anova_observed_scale"]), 4) if icc_data.get("icc_anova_observed_scale") is not None else None,
    "metric_ci_low": round(float(icc_data["icc_anova_ci_low"]), 4) if icc_data.get("icc_anova_ci_low") is not None else None,
    "metric_ci_high": round(float(icc_data["icc_anova_ci_high"]), 4) if icc_data.get("icc_anova_ci_high") is not None else None,
    "reference_window_id": REFERENCE_WINDOW_ID,
    "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
    "sample_size": icc_data["n_players_primary"],
    "notes": f"{POP_NOTE}; v1.0.4 §14(b) PRIMARY cross-dataset headline; Wu/Crespi/Wong 2012 ANOVA observed-scale",
})

# LPM observed-scale (diagnostic per v1.0.2 §14(b)): CI bounds on same row.
rows.append({
    "dataset_tag": DATASET_TAG,
    "quarter": "all",
    "feature_name": "won",
    "metric_name": "icc_lpm_observed_scale",
    "metric_value": round(float(icc_data["icc_lpm_observed_scale"]), 4) if icc_data.get("icc_lpm_observed_scale") is not None else None,
    "metric_ci_low": round(float(icc_data["icc_lpm_ci_low"]), 4) if icc_data.get("icc_lpm_ci_low") is not None else None,
    "metric_ci_high": round(float(icc_data["icc_lpm_ci_high"]), 4) if icc_data.get("icc_lpm_ci_high") is not None else None,
    "reference_window_id": REFERENCE_WINDOW_ID,
    "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
    "sample_size": icc_data["n_players_primary"],
    "notes": f"{POP_NOTE}; B-01 diagnostic; LPM observed-scale (REML lbfgs random-intercept; Chung 2013 boundary-shrinkage caveat)",
})

if icc_data.get("icc_glmm_latent_scale") is not None:
    rows.append({
        "dataset_tag": DATASET_TAG,
        "quarter": "all",
        "feature_name": "won",
        "metric_name": "icc_glmm_latent_scale",
        "metric_value": round(float(icc_data["icc_glmm_latent_scale"]), 4),
        "metric_ci_low": None,  # GLMM CI not computed (optional tertiary)
        "metric_ci_high": None,
        "reference_window_id": REFERENCE_WINDOW_ID,
        "cohort_threshold": DEFAULT_COHORT_THRESHOLD,
        "sample_size": icc_data["n_players_primary"],
        "notes": f"{POP_NOTE}; B-01 tertiary: GLMM latent-scale ICC (Nakagawa & Schielzeth 2010)",
    })

# T05: Sensitivity rows
for _, r in df_sens.iterrows():
    if r["n_threshold"] != DEFAULT_COHORT_THRESHOLD:
        rows.append({
            "dataset_tag": DATASET_TAG,
            "quarter": r["quarter"],
            "feature_name": r["feature"],
            "metric_name": "psi",
            "metric_value": round(float(r["psi"]), 4) if pd.notna(r.get("psi")) else None,
            "metric_ci_low": None,
            "metric_ci_high": None,            "reference_window_id": REFERENCE_WINDOW_ID,
            "cohort_threshold": int(r["n_threshold"]),
            "sample_size": int(r["n_matches"]) if pd.notna(r.get("n_matches")) else None,
            "notes": f"{POP_NOTE}; survivorship sensitivity N={r['n_threshold']}",
        })

print(f"Total Phase 06 rows: {len(rows)}")

# %% [markdown]
# ## Emit CSV

# %%
df_out = pd.DataFrame(rows, columns=[
    "dataset_tag", "quarter", "feature_name", "metric_name", "metric_value",
    "metric_ci_low", "metric_ci_high",
    "reference_window_id", "cohort_threshold", "sample_size", "notes",
])

# v1.0.5 closed-enum validator: reject out-of-enumeration metric_name values.
# CI bounds live in metric_ci_low/metric_ci_high columns, NOT as separate rows.
VALID_METRIC_NAMES = {
    "psi", "cohen_h", "cohen_d", "ks_stat",
    "icc_lpm_observed_scale", "icc_anova_observed_scale", "icc_glmm_latent_scale",
}
_invalid_metrics = set(df_out["metric_name"].unique()) - VALID_METRIC_NAMES
assert not _invalid_metrics, (
    f"v1.0.5 enum violation: metric_name values not in closed set: {_invalid_metrics}"
)

# Verify no POST_GAME tokens in feature_name (I3)
post_game_tokens = {"duration_seconds", "is_duration_suspicious", "is_duration_negative", "ratingDiff", "finished"}
found_tokens = set(df_out["feature_name"].unique()) & post_game_tokens
assert len(found_tokens) == 0, f"POST_GAME tokens found in Phase 06 CSV: {found_tokens}"
print(f"I3 check passed: no POST_GAME tokens in feature_name")

# Verify all dataset_tag values
assert (df_out["dataset_tag"] == DATASET_TAG).all(), "dataset_tag mismatch"
print(f"dataset_tag check passed: all = '{DATASET_TAG}'")

csv_path = ARTIFACTS / "01_05_phase06_interface_aoe2companion.csv"
df_out.to_csv(csv_path, index=False)
print(f"Wrote: {csv_path} ({len(df_out)} rows)")

# %% [markdown]
# ## Emit MD validation

# %%
row_counts = df_out.groupby(["feature_name", "metric_name"]).size().reset_index(name="count")
row_counts_md = row_counts.to_markdown(index=False)

md_content = f"""# 01_05_07 Phase 06 Interface — aoe2companion

spec: reports/specs/01_05_preregistration.md@7e259dd8

## B-02 Deviation Note (pre-authorized)

Spec §1 contract: match_id, started_at, player_id, team, chosen_civ_or_race, rating_pre, won, map_id, patch_id
VIEW schema: match_id, started_at, player_id, opponent_id, faction, opponent_faction, won, duration_seconds, dataset_tag

`feature_name` values in this CSV match the VIEW schema (faction, map_id, rating, won).
Cross-dataset alignment is on `metric_name` only per critique pre-authorization.
Spec §1 divergence documented in INVARIANTS.md §5 (I8 partial row).

## M-07 Population scope

[POP:ranked_ladder]: aoec is an online-ladder dataset. All findings condition on ranked-ladder
participation, not the overall AoE2 player population. See T10 Decision Gate memo.

## Row counts by (feature_name, metric_name)

{row_counts_md}

**Total rows:** {len(df_out)}
**Expected minimum:** 4 features x 8 quarters x ~3 metrics = ~96 (plus ICC rows, sensitivity, lb-split)

## Sanity checks

- All `dataset_tag` = '{DATASET_TAG}': {(df_out['dataset_tag'] == DATASET_TAG).all()}
- No POST_GAME tokens in `feature_name`: {len(set(df_out['feature_name'].unique()) & post_game_tokens) == 0}
- ICC LPM value: {icc_data['icc_lpm_observed_scale']}
- ICC ANOVA value: {icc_data['icc_anova_observed_scale']}

## Verdict

{len(df_out)} rows emitted. Schema conforms to spec §12. B-02 and M-07 deviations documented.
"""

md_path = ARTIFACTS / "01_05_07_phase06_interface.md"
md_path.write_text(md_content)
print("Wrote:", md_path)

# %% [markdown]
# ## Verdict

# %%
print(f"# Verdict: Phase 06 interface CSV emitted with {len(df_out)} rows.")
print(f"Schema: {list(df_out.columns)}")
print("Done.")
