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
# # Step 01_05_05 -- Variance Decomposition (ICC)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_05 -- Temporal & Panel EDA
# **Step:** 01_05_05
# **Dataset:** aoestats
# **spec:** reports/specs/01_05_preregistration.md@7e259dd8
#
# # Hypothesis: Player-level variance explains > 15% of total variance in won
# # (ICC >= 0.15), consistent with meaningful skill signal for per-player prediction.
# # Falsifier: ICC < 0.05 -- would undermine the per-player prediction paradigm.
#
# **Critique M2:** Primary LMM (icc_lpm_observed_scale) + secondary ANOVA ICC
# (icc_anova_observed_scale, Wu/Crespi/Wong 2012 CCT 33(5):869-880).
# Optional tertiary GLMM (icc_glmm_latent_scale) -- skip if convergence fails.
# Bootstrap CI per Ukoumunne et al. 2012 PMC3426610.
#
# **Critique M3:** Stratified reservoir by n_matches_in_reference_period deciles.
# Report ICC + sensitivity at 20k and 100k. Persist icc_sample_profile_ids_*.csv.
#
# **Critique M7:** ICC computed on profile_id; per INVARIANTS §2, within-aoestats
# migration/collision unevaluable (branch v). aoec namespace bridge (VERDICT A 0.9960)
# supports stability but doesn't audit fragmentation. ICC = upper bound on per-player
# variance share.

# %%
import json
from pathlib import Path

import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir
from rts_predict.games.aoe2.datasets.aoestats.analysis.variance_decomposition import (
    RANDOM_SEED,
    compute_icc_anova,
    fit_random_intercept_lmm,
    compute_icc_lmm,
)
# stratified_reservoir_sample is no longer used in this notebook post-v1.0.4
# (sensitivity axis is now spec §6.2 cohort-threshold, not sample-group size;
# each cohort is used whole, not sub-sampled). The helper is retained in the
# analysis module for potential future use.

ARTIFACTS_DIR = get_reports_dir("aoe2", "aoestats") / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

db = get_notebook_db("aoe2", "aoestats")
print("Connected.")

# %%
REF_START = "2022-08-29"
REF_END = "2022-10-27"
REF_PATCH = 66692  # matches_raw: patch 66692 covers [2022-08-29, 2022-12-08]; spec §7 v1.0.3

# Post-PR-6 (fix/01-05-aoestats-icc-cohort-axis) restructure:
# Previous notebook requested player-count samples `{20k, 50k, 100k}`. aoestats's
# single-patch reference window only has ~744 eligible players at the spec §6.3
# default threshold N=10, so all three "sample sizes" degenerated to the full
# 744-player population — producing three identical ICC rows labeled as a
# sensitivity table. The 2026-04-19 pre-01_06 adversarial review flagged this
# as DEFEND-IN-THESIS #2 (axis confusion between §6.2 cohort-threshold and
# variance-decomposition sample-group size).
#
# v1.0.4 fix: the sensitivity axis is now spec §6.2 cohort match-count
# thresholds `N ∈ {5, 10, 20}` (how many prior matches a player must have in
# the reference window to be included). Each threshold produces a genuinely
# different cohort. The primary ICC headline is N=10 (spec §6.3 default).
MIN_MATCH_THRESHOLDS = [5, 10, 20]
PRIMARY_THRESHOLD = 10  # spec §6.3 default

COHORT_SQL_TEMPLATE = """
WITH cohort AS (
  SELECT CAST(player_id AS BIGINT) AS player_id, COUNT(*) AS n_matches
  FROM matches_history_minimal
  WHERE started_at BETWEEN TIMESTAMP '{ref_start}' AND TIMESTAMP '{ref_end}'
  GROUP BY player_id HAVING COUNT(*) >= {min_matches}
)
SELECT
  CAST(mhm.player_id AS BIGINT) AS player_id,
  mhm.faction,
  CAST(mhm.won AS INTEGER) AS won,
  m1v1.p0_old_rating,
  m1v1.avg_elo,
  c.n_matches AS n_matches_in_ref
FROM matches_history_minimal mhm
JOIN matches_1v1_clean m1v1 ON mhm.match_id = 'aoestats::' || m1v1.game_id
JOIN cohort c ON CAST(mhm.player_id AS BIGINT) = c.player_id
WHERE mhm.started_at BETWEEN TIMESTAMP '{ref_start}' AND TIMESTAMP '{ref_end}'
"""

# %%
# Per-cohort-threshold ICC fit.
icc_results = {}

for min_matches in MIN_MATCH_THRESHOLDS:
    print(f"\n=== Cohort threshold N={min_matches} (spec §6.2) ===")
    cohort_sql = COHORT_SQL_TEMPLATE.format(
        ref_start=REF_START, ref_end=REF_END, min_matches=min_matches
    )
    df_cohort = db.fetch_df(cohort_sql)
    n_players = df_cohort["player_id"].nunique()
    n_rows = len(df_cohort)
    print(f"  Cohort: {n_players:,} players, {n_rows:,} observations")

    # Persist cohort profile IDs for reproducibility (replaces the M3 reservoir-
    # sample IDs used in v1.0.1 of this notebook).
    ids_df = pd.DataFrame({"player_id": df_cohort["player_id"].unique()})
    ids_path = ARTIFACTS_DIR / f"icc_cohort_profile_ids_n{min_matches}.csv"
    ids_df.to_csv(ids_path, index=False)
    print(f"  Saved cohort IDs: {ids_path.name}")

    df_samp = df_cohort  # whole cohort; no sub-sampling
    actual_n = n_players

    # Primary: LMM (icc_lpm_observed_scale)
    icc_lmm_val, ci_lo_lmm, ci_hi_lmm = float("nan"), float("nan"), float("nan")
    convergence_warning = None
    try:
        print("  Fitting LMM...")
        lmm_result = fit_random_intercept_lmm(df_samp, "won", "player_id")
        icc_lmm_val, ci_lo_lmm, ci_hi_lmm = compute_icc_lmm(lmm_result)
        print(f"  LMM ICC = {icc_lmm_val:.4f} [{ci_lo_lmm:.4f}, {ci_hi_lmm:.4f}]")
        # Post-fix/01-05-aoestats-ngroups-ci-assert: CI sanity check.
        # A valid delta-method CI must contain its point estimate. Prior to this
        # PR, compute_icc_lmm raised AttributeError on `result.ngroups` and the
        # bare `except Exception` silently recorded it as a convergence failure.
        # The ANOVA CI was emitted uninspected and published with an inverted
        # interval on the aoestats 50k run (point=0.0268, CI=[0.0494, 0.0759]).
        if not np.isnan(icc_lmm_val) and not np.isnan(ci_lo_lmm) and not np.isnan(ci_hi_lmm):
            assert ci_lo_lmm <= icc_lmm_val + 1e-9, (
                f"LMM CI lower bound {ci_lo_lmm} > point {icc_lmm_val} (inverted CI — LMM math bug)"
            )
            assert ci_hi_lmm >= icc_lmm_val - 1e-9, (
                f"LMM CI upper bound {ci_hi_lmm} < point {icc_lmm_val} (inverted CI — LMM math bug)"
            )
    except AssertionError:
        # Sanity-check failure is a real bug, not a convergence issue. Re-raise.
        raise
    except Exception as exc:
        convergence_warning = str(exc)
        print(f"  LMM failed: {exc}")

    # Secondary: ANOVA ICC (icc_anova_observed_scale) per Wu/Crespi/Wong 2012
    print("  Computing ANOVA ICC (bootstrap CI, this may take a moment)...")
    icc_anova_val, ci_lo_anova, ci_hi_anova = compute_icc_anova(df_samp, "won", "player_id")
    print(f"  ANOVA ICC = {icc_anova_val:.4f} [{ci_lo_anova:.4f}, {ci_hi_anova:.4f}]")
    # CI sanity check — ANOVA bootstrap CI MUST contain its own point estimate.
    # Per the sc2egset pattern (variance_icc_sc2egset.py); catches bootstrap
    # resampling errors and prior aoestats 50k inverted-CI pathology.
    if not np.isnan(icc_anova_val) and not np.isnan(ci_lo_anova) and not np.isnan(ci_hi_anova):
        assert ci_lo_anova <= icc_anova_val + 1e-9, (
            f"ANOVA CI lower bound {ci_lo_anova} > point {icc_anova_val} "
            f"(inverted CI — check cluster-bootstrap resampling)"
        )
        assert ci_hi_anova >= icc_anova_val - 1e-9, (
            f"ANOVA CI upper bound {ci_hi_anova} < point {icc_anova_val} "
            f"(inverted CI — check cluster-bootstrap resampling)"
        )

    icc_results[f"n_min{min_matches}"] = {
        "min_matches_in_ref_threshold": min_matches,
        "n_players": int(actual_n),
        "n_obs": len(df_samp),
        "icc_anova_observed_scale": {
            "icc_point": round(icc_anova_val, 4) if not np.isnan(icc_anova_val) else None,
            "ci_lo": round(ci_lo_anova, 4) if not np.isnan(ci_lo_anova) else None,
            "ci_hi": round(ci_hi_anova, 4) if not np.isnan(ci_hi_anova) else None,
            "method": "ANOVA Wu/Crespi/Wong 2012 CCT 33(5):869-880 + bootstrap CI Ukoumunne 2012 PMC3426610",
        },
        "icc_lpm_observed_scale": {
            "icc_point": round(icc_lmm_val, 4) if not np.isnan(icc_lmm_val) else None,
            "ci_lo": round(ci_lo_lmm, 4) if not np.isnan(ci_lo_lmm) else None,
            "ci_hi": round(ci_hi_lmm, 4) if not np.isnan(ci_hi_lmm) else None,
            "method": "statsmodels MixedLM REML lbfgs (diagnostic; spec v1.0.4 §14(b) demotes LMM to diagnostic)",
            "convergence_warning": convergence_warning,
        },
        "icc_glmm_latent_scale": None,  # Optional — skipped (compute-prohibitive on Bernoulli)
    }

# %%
# Falsifier check — primary headline is ANOVA @ N=10 (spec v1.0.4 §14(b)).
primary = icc_results.get(f"n_min{PRIMARY_THRESHOLD}", {})
primary_anova = primary.get("icc_anova_observed_scale", {})
primary_lmm = primary.get("icc_lpm_observed_scale", {})
icc_anova_primary = primary_anova.get("icc_point") or float("nan")
icc_lmm_primary = primary_lmm.get("icc_point") or float("nan")

# Spec v1.0.4 §14(b): ANOVA is the cross-dataset headline. LMM is a diagnostic.
primary_icc = icc_anova_primary if not np.isnan(icc_anova_primary) else icc_lmm_primary

if np.isnan(primary_icc):
    verdict = "INCONCLUSIVE"
elif primary_icc >= 0.05:
    verdict = "PASSED"
else:
    verdict = "FALSIFIED"

print(f"\n=== PRIMARY (N={PRIMARY_THRESHOLD}, ANOVA) ===")
print(f"  icc_anova_observed_scale: {icc_anova_primary}")
print(f"  icc_lpm_observed_scale (diagnostic): {icc_lmm_primary}")
print(f"  Q6 skill-signal hypothesis: {verdict}")
print("\n=== Cohort-threshold sensitivity ===")
for k, v in icc_results.items():
    print(
        f"  N={v['min_matches_in_ref_threshold']:>2}: "
        f"n_players={v['n_players']:,} "
        f"ANOVA={v['icc_anova_observed_scale']['icc_point']} "
        f"LMM={v['icc_lpm_observed_scale']['icc_point']}"
    )

# %%
# M7 limitation paragraph (verbatim per critique)
M7_PARAGRAPH = (
    "ICC computed on `profile_id`; per INVARIANTS §2, within-aoestats migration/collision "
    "unevaluable (branch v). aoec namespace bridge (VERDICT A 0.9960) supports stability "
    "but doesn't audit fragmentation. ICC = upper bound on per-player variance share."
)

# Full ICC results JSON
icc_json = {
    "step": "01_05_05",
    "spec": "reports/specs/01_05_preregistration.md@7e259dd8 (v1.0.4)",
    "reference_window": {"start": REF_START, "end": REF_END, "patch": REF_PATCH},
    "primary_threshold": PRIMARY_THRESHOLD,
    "primary_estimator": "icc_anova_observed_scale",
    "primary_icc_point": round(float(icc_anova_primary), 4) if not np.isnan(icc_anova_primary) else None,
    "falsifier_verdict": verdict,
    "icc_by_cohort_threshold": icc_results,
    "m7_branch_v_limitation": M7_PARAGRAPH,
    "random_seed": RANDOM_SEED,
    "post_v1_0_4_restructure_note": (
        "v1.0.4 (PR fix/01-05-aoestats-icc-cohort-axis): sensitivity axis "
        "changed from requested-sample-size {20k,50k,100k} (which degenerated to "
        "the 744-player population) to spec §6.2 cohort match-count thresholds "
        "N ∈ {5,10,20}. Primary headline is ANOVA @ N=10 per spec v1.0.4 §14(b)."
    ),
}
icc_path = ARTIFACTS_DIR / "01_05_05_icc_results.json"
with open(icc_path, "w") as f:
    json.dump(icc_json, f, indent=2, default=str)
print(f"\nWrote {icc_path}")

# Validation
assert "icc_point" in primary.get("icc_anova_observed_scale", {}), "primary ICC missing icc_point"
assert not np.isnan(icc_anova_primary), "ANOVA primary is NaN — check cohort-threshold pipeline"

# %%
# Summary MD
_sens_rows = "\n".join(
    f"| N={v['min_matches_in_ref_threshold']:>2} | {v['n_players']:,} | "
    f"{v['icc_anova_observed_scale']['icc_point']} | "
    f"[{v['icc_anova_observed_scale']['ci_lo']}, {v['icc_anova_observed_scale']['ci_hi']}] | "
    f"{v['icc_lpm_observed_scale']['icc_point']} |"
    for v in icc_results.values()
)

md_text = f"""# Variance Decomposition ICC — aoestats

**spec:** reports/specs/01_05_preregistration.md v1.0.4 §14(b) (ANOVA-primary headline)
**Step:** 01_05_05

## Primary Result (ANOVA @ N={PRIMARY_THRESHOLD}, spec v1.0.4 §14(b))

| Metric | Value |
|---|---|
| `icc_anova_observed_scale` | **{icc_anova_primary}** |
| `icc_anova_ci_low` | {primary_anova.get('ci_lo')} |
| `icc_anova_ci_high` | {primary_anova.get('ci_hi')} |
| `icc_lpm_observed_scale` (diagnostic) | {icc_lmm_primary} |

## Falsifier verdict

**Q6 skill-signal hypothesis:** {verdict}
(Hypothesis range per spec §8: ICC ∈ [0.05, 0.20]; ANOVA primary estimate
{icc_anova_primary} is below the lower bound 0.05.)

## Cohort-threshold sensitivity (§6.2)

| Threshold | n_players | ANOVA ICC | ANOVA CI | LMM ICC (diagnostic) |
|---|---|---|---|---|
{_sens_rows}

**Bootstrap CI** per Ukoumunne et al. 2012 PMC3426610 (n=200).
**Cohort-threshold axis** (§6.2): each N produces a distinct cohort of
players with ≥N prior matches in the reference window [2022-08-29,
2022-10-27] (patch 66692). Larger N = smaller but more-active cohort.

## Restructure note (v1.0.4)

Prior to v1.0.4 this notebook requested player-count samples `{{20k, 50k,
100k}}` via stratified reservoir sampling. aoestats's single-patch reference
window has only ~744 eligible players at N=10, so all three "sample sizes"
degenerated to the full population — producing three identical ICC rows
labeled as sensitivity. The 2026-04-19 pre-01_06 adversarial review flagged
this as DEFEND-IN-THESIS #2 (axis confusion between §6.2 cohort-threshold
and variance-decomposition sample-group size). v1.0.4 realigns the
sensitivity axis to spec §6.2 cohort match-count thresholds.

## M7 Branch-v Limitation

{M7_PARAGRAPH}
"""
(ARTIFACTS_DIR / "01_05_05_icc_results.md").write_text(md_text)

print(f"Q6 skill-signal hypothesis: {verdict}")
print("Step 01_05_05 complete.")
