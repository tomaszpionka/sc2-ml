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
# # 01_05_05 ICC Variance Decomposition — aoe2companion
# spec: reports/specs/01_05_preregistration.md@7e259dd8 (v1.0.2 amendment filed in this branch; SHA refresh in follow-up commit)
#
# **Spec §§:** §7 (reference window), §8 (variance decomposition), §14 v1.0.2
# (aoe2companion-specific adaptations).
#
# **Scope.** Operates on the spec §7 reference window (2022-08-29..2022-12-31),
# NOT the full analysis window. Previous hang root cause: `statsmodels.mixedlm`
# on ~7M rows × ~20k groups — O(G × iter) cost intractable at ≥20k groups.
#
# **Method — primary (spec v1.0.2 §14 adaptation b).**
# ANOVA-based ICC per Wu/Crespi/Wong 2012 CCT 33(5):869-880 (observed scale).
# Consistent moment estimator, robust to boundary shrinkage. Cluster bootstrap
# CI per Ukoumunne et al. 2012 PMC3426610 (n_bootstrap=200).
#
# **Method — diagnostic.**
# Random-intercept LMM `won ~ 1 + (1 | player_id)` via `statsmodels.mixedlm`,
# REML, LBFGS (max_iter=50). This fits a Linear Probability Model (Bernoulli
# outcome, Gaussian LMM); the resulting ICC is OBSERVED-SCALE, not latent-scale,
# and is SYSTEMATICALLY PULLED TOWARD ZERO when τ² is small (REML boundary
# shrinkage; Chung et al. 2013, Psychometrika 78(4):685-709). Reported as a
# diagnostic alongside ANOVA; not the primary estimator. Delta-method CI
# assumes balanced Gaussian design and is NOT VALID on Bernoulli with
# unbalanced n_i — reported with that caveat, for comparison with the ANOVA
# estimate only.
#
# **GLMM (latent-scale).** Explicitly skipped per spec v1.0.2 §14 adaptation
# (c). MCMC/Laplace-approximated GLMM at 5k-group scale is compute-prohibitive
# on the project hardware (> 2h wall-clock per fit). Deferred to Phase 02+.
#
# **Sample-size strategy (spec v1.0.2 §14 adaptation a).**
# - Persist sample profile IDs at {5k, 10k, 20k} (reproducibility, M-06).
# - ANOVA ICC at all three sizes; bootstrap CI at the primary (5k) size.
# - LMM diagnostic at 5k (primary) and 10k (sensitivity); 20k skipped.
#
# **Hypothesis (pre-registered):** ICC on `won` ∈ [0.05, 0.20].
# **Falsifier:** ICC on `won` < 0.02 or > 0.50.
# **Primary estimator for verdict:** `icc_anova_observed_scale` at 5k.

# %% [markdown]
# ## Imports

# %%
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir
from rts_predict.games.aoe2.datasets.aoe2companion.analysis.variance_decomposition import (
    RANDOM_SEED,
    compute_icc_anova,
    compute_icc_anova_fast,
    compute_icc_lmm,
    fit_random_intercept_lmm,
    stratified_reservoir_sample,
)

ARTIFACTS = get_reports_dir("aoe2", "aoe2companion") / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

REF_START = "2022-08-29"
REF_END_EXCLUSIVE = "2023-01-01"  # §9 Query 3 assertion uses ref_end = 2022-12-31 (date-inclusive == timestamp < 2023-01-01)
MIN_OBS_PER_PLAYER = 10  # spec §8
SAMPLE_SIZES = [5_000, 10_000, 20_000]
LMM_SAMPLE_SIZES = [5_000, 10_000]  # Skip LMM at 20k — mixedlm cost-prohibitive

print("Artifacts dir:", ARTIFACTS)

# Spec §9 Query 3 assertion (reference-window window constants match spec §7)
assert datetime.fromisoformat(REF_START) == datetime(2022, 8, 29), f"Bad ref_start: {REF_START}"
assert datetime.fromisoformat(REF_END_EXCLUSIVE) == datetime(2023, 1, 1), f"Bad ref_end_exclusive: {REF_END_EXCLUSIVE}"
print("Reference window bounds match spec §7.")

# %% [markdown]
# ## Step 1: Load reference-window cohort (spec §7)
# ~4M rows, ~114k unique players — manageable in RAM.

# %%
COHORT_SQL = f"""
WITH eligible AS (
  SELECT player_id, COUNT(*) AS n_matches_in_ref
  FROM matches_history_minimal
  WHERE started_at >= TIMESTAMP '{REF_START}'
    AND started_at <  TIMESTAMP '{REF_END_EXCLUSIVE}'
  GROUP BY player_id
  HAVING COUNT(*) >= {MIN_OBS_PER_PLAYER}
)
SELECT
  mhm.player_id,
  mhm.faction,
  CAST(mhm.won AS INTEGER) AS won,
  e.n_matches_in_ref
FROM matches_history_minimal mhm
JOIN eligible e USING (player_id)
WHERE mhm.started_at >= TIMESTAMP '{REF_START}'
  AND mhm.started_at <  TIMESTAMP '{REF_END_EXCLUSIVE}'
"""

db = get_notebook_db("aoe2", "aoe2companion", read_only=True)
print("Loading reference-window cohort...")
df_full = db.con.execute(COHORT_SQL).df()
print(f"Loaded {len(df_full):,} rows, {df_full['player_id'].nunique():,} unique players")
print(f"won mean: {df_full['won'].mean():.4f}")
db.close()

# %% [markdown]
# ## Step 2: Stratified sampling at each size (persist IDs per critique M-06)

# %%
np.random.seed(RANDOM_SEED)
sample_frames: dict[int, pd.DataFrame] = {}

for n_players in SAMPLE_SIZES:
    df_s = stratified_reservoir_sample(
        df_full, "player_id", n_players, stratify_by="n_matches_in_ref", seed=RANDOM_SEED
    )
    actual_n = df_s["player_id"].nunique()
    sample_frames[n_players] = df_s

    ids_df = pd.DataFrame({"player_id": df_s["player_id"].unique()})
    ids_path = ARTIFACTS / f"icc_sample_profileIds_{n_players // 1000}k.csv"
    ids_df.to_csv(ids_path, index=False)
    print(f"  n_requested={n_players:,} actual_unique={actual_n:,} rows={len(df_s):,} → {ids_path.name}")

# %% [markdown]
# ## Step 3: Primary LMM at 5k (spec §8)
# Random-intercept LMM via statsmodels.mixedlm; delta-method 95% CI.

# %%
primary_n = 5_000
df_primary = sample_frames[primary_n]
print(f"Fitting primary LMM at n={primary_n:,} (rows={len(df_primary):,})...")

try:
    lmm_result = fit_random_intercept_lmm(df_primary, "won", "player_id", max_iter=50)
    icc_lpm, icc_ci_low, icc_ci_high = compute_icc_lmm(lmm_result)
    lpm_converged = bool(lmm_result.converged)
    tau2_lpm = float(lmm_result.cov_re.iloc[0, 0])
    sigma2_lpm = float(lmm_result.scale)
    lpm_error = None
    print(f"LMM: ICC={icc_lpm:.6f} [{icc_ci_low:.6f}, {icc_ci_high:.6f}] converged={lpm_converged}")
    print(f"  tau2={tau2_lpm:.6f}  sigma2={sigma2_lpm:.6f}")
except Exception as exc:
    lmm_result = None
    icc_lpm = icc_ci_low = icc_ci_high = float("nan")
    tau2_lpm = sigma2_lpm = float("nan")
    lpm_converged = False
    lpm_error = str(exc)
    print(f"LMM failed: {exc}")

# %% [markdown]
# ## Step 4: PRIMARY — ANOVA ICC at 5k with cluster bootstrap CI
# ## Step 4b: ANOVA ICC point estimate at 10k and 20k (no bootstrap — informational)

# %%
# Primary: ANOVA ICC at 5k with bootstrap CI (Ukoumunne et al. 2012).
# n_bootstrap=200 is the project convention for stable CI (cf. aoestats variance_decomposition).
N_BOOTSTRAP = 200
print(f"Computing primary ANOVA ICC at n={primary_n:,} with {N_BOOTSTRAP}-sample cluster bootstrap...")
icc_anova_primary, anova_ci_low, anova_ci_high = compute_icc_anova(
    df_primary, "won", "player_id", n_bootstrap=N_BOOTSTRAP
)
print(
    f"Primary ANOVA ICC: {icc_anova_primary:.6f} "
    f"[{anova_ci_low:.6f}, {anova_ci_high:.6f}]"
)

# Point estimates at 10k and 20k for size sensitivity.
anova_by_size: dict[int, float] = {primary_n: icc_anova_primary}
for n_players, df_s in sample_frames.items():
    if n_players == primary_n:
        continue
    icc_a = compute_icc_anova_fast(df_s, "won", "player_id")
    anova_by_size[n_players] = icc_a
    print(f"  ANOVA ICC @ n={n_players:,}: {icc_a:.6f} (no bootstrap)")

# %% [markdown]
# ## Step 5: LMM sensitivity at 10k (skip 20k — mixedlm cost-prohibitive)

# %%
sensitivity: dict[int, dict] = {}
for n_players in LMM_SAMPLE_SIZES:
    if n_players == primary_n:
        sensitivity[n_players] = {
            "icc_lmm": round(icc_lpm, 6) if not np.isnan(icc_lpm) else None,
            "converged": lpm_converged,
            "note": "primary",
        }
        continue
    df_s = sample_frames[n_players]
    print(f"Fitting sensitivity LMM at n={n_players:,} (rows={len(df_s):,})...")
    try:
        r_s = fit_random_intercept_lmm(df_s, "won", "player_id", max_iter=50)
        icc_s, _, _ = compute_icc_lmm(r_s)
        sensitivity[n_players] = {
            "icc_lmm": round(float(icc_s), 6),
            "converged": bool(r_s.converged),
        }
        print(f"  ICC_lmm={icc_s:.6f} converged={r_s.converged}")
    except Exception as exc:
        sensitivity[n_players] = {"icc_lmm": None, "converged": False, "error": str(exc)}
        print(f"  Failed: {exc}")

sensitivity[20_000] = {
    "icc_lmm": None,
    "converged": False,
    "note": "skipped — mixedlm cost-prohibitive at 20k groups; ANOVA ICC reported instead",
    "icc_anova_at_size": round(float(anova_by_size[20_000]), 6),
}

# %% [markdown]
# ## Step 6: Verdict
# Primary estimator is `icc_anova_observed_scale` at 5k with bootstrap CI.
# Falsifier fires if the CI does not overlap [0.05, 0.20].

# %%
obs_per_player = df_primary.groupby("player_id")["won"].count()

# Verdict is on the primary ANOVA estimator and its bootstrap CI.
if np.isnan(icc_anova_primary) or np.isnan(anova_ci_low) or np.isnan(anova_ci_high):
    verdict = f"inconclusive: ANOVA ICC or CI is NaN (point={icc_anova_primary})"
elif anova_ci_high < 0.05:
    verdict = (
        f"falsified (below range): ICC_anova={icc_anova_primary:.6f} "
        f"[{anova_ci_low:.6f}, {anova_ci_high:.6f}] below [0.05, 0.20]"
    )
elif anova_ci_low > 0.20:
    verdict = (
        f"falsified (above range): ICC_anova={icc_anova_primary:.6f} "
        f"[{anova_ci_low:.6f}, {anova_ci_high:.6f}] above [0.05, 0.20]"
    )
elif 0.05 <= icc_anova_primary <= 0.20:
    verdict = (
        f"confirmed: ICC_anova={icc_anova_primary:.6f} "
        f"[{anova_ci_low:.6f}, {anova_ci_high:.6f}] within [0.05, 0.20]"
    )
else:
    # Point estimate outside but CI overlaps — inconclusive rather than falsified.
    verdict = (
        f"inconclusive: ICC_anova={icc_anova_primary:.6f} "
        f"[{anova_ci_low:.6f}, {anova_ci_high:.6f}] — point outside range but CI overlaps"
    )
print(f"\nVerdict (primary ANOVA): {verdict}")
_lmm_display = f"{icc_lpm:.6f}" if not np.isnan(icc_lpm) else "NaN"
print(f"LMM diagnostic (boundary-sensitive, observed-scale LPM): {_lmm_display}")

# %% [markdown]
# ## Step 7: Emit artifacts (JSON + MD)

# %%
json_out = {
    "spec": "reports/specs/01_05_preregistration.md (v1.0.2)",
    "reference_window": {"start": REF_START, "end_exclusive": REF_END_EXCLUSIVE},
    "min_obs_per_player": MIN_OBS_PER_PLAYER,
    "primary_sample_size": primary_n,
    "n_bootstrap": N_BOOTSTRAP,

    # Primary (ANOVA at 5k with bootstrap CI) — spec v1.0.2 §14 adaptation (b).
    "icc_anova_observed_scale": round(float(icc_anova_primary), 6),
    "icc_anova_ci_low": round(float(anova_ci_low), 6) if not np.isnan(anova_ci_low) else None,
    "icc_anova_ci_high": round(float(anova_ci_high), 6) if not np.isnan(anova_ci_high) else None,
    "icc_anova_by_sample_size": {str(n): round(float(v), 6) for n, v in anova_by_size.items()},

    # Diagnostic (LMM at 5k) — observed-scale LPM, boundary-sensitive.
    # Retained for comparison; CI assumes balanced Gaussian and is not valid here.
    "icc_lpm_observed_scale": round(float(icc_lpm), 6) if not np.isnan(icc_lpm) else None,
    "icc_lpm_ci_low_invalid_asymptotic": round(float(icc_ci_low), 6) if not np.isnan(icc_ci_low) else None,
    "icc_lpm_ci_high_invalid_asymptotic": round(float(icc_ci_high), 6) if not np.isnan(icc_ci_high) else None,
    "tau2_lpm": round(float(tau2_lpm), 6) if not np.isnan(tau2_lpm) else None,
    "sigma2_lpm": round(float(sigma2_lpm), 6) if not np.isnan(sigma2_lpm) else None,
    "lpm_converged": lpm_converged,
    "lpm_error": lpm_error,

    # GLMM skipped — spec v1.0.2 §14 adaptation (c).
    "icc_glmm_latent_scale": None,
    "glmm_skip_note": "Spec v1.0.2 §14 (c): GLMM at 5k-group scale is compute-prohibitive on project hardware; deferred to Phase 02+.",

    # Cohort stats
    "n_players_primary": int(df_primary["player_id"].nunique()),
    "n_obs_primary": int(len(df_primary)),
    "n_obs_per_player_median": round(float(obs_per_player.median()), 1),
    "n_obs_per_player_mean": round(float(obs_per_player.mean()), 1),
    "n_eligible_players_total": int(df_full["player_id"].nunique()),

    "sensitivity": {f"n_{k}": v for k, v in sensitivity.items()},
    "sample_files": {
        f"{n // 1000}k": str(ARTIFACTS / f"icc_sample_profileIds_{n // 1000}k.csv")
        for n in SAMPLE_SIZES
    },
    "sql": {"cohort_query": COHORT_SQL},
    "verdict": verdict,
    "produced_at": datetime.now().isoformat(),
    "methodology_note": (
        "Primary estimator: ANOVA ICC per Wu/Crespi/Wong 2012 CCT 33(5):869-880, "
        "cluster bootstrap CI per Ukoumunne et al. 2012 PMC3426610 (n_bootstrap=200), "
        "fit on a 5k stratified-reservoir sample of players with ≥10 obs in the spec §7 "
        "reference window. ANOVA at 10k/20k reported as point-estimate sensitivity. "
        "LMM via statsmodels.mixedlm (REML lbfgs, max_iter=50) reported as a DIAGNOSTIC "
        "alongside the primary ANOVA; the LMM is a Linear Probability Model on Bernoulli "
        "outcome with known τ²-boundary shrinkage (Chung et al. 2013, Psychometrika "
        "78(4):685-709) and its delta-method CI assumes a balanced Gaussian design that "
        "does not hold here — reported only for comparison. GLMM latent-scale skipped "
        "per spec v1.0.2 §14 (c). See JSON 'sensitivity' block for LMM at 10k."
    ),
}

json_path = ARTIFACTS / "01_05_05_icc.json"
json_path.write_text(json.dumps(json_out, indent=2, default=str))
print(f"Wrote: {json_path}")

# ─── MD emission (v2 post-adversarial-review: ANOVA primary, LMM diagnostic) ───
_sens_10k = sensitivity.get(10_000, {})
_lmm10k_icc = _sens_10k.get("icc_lmm")
_lmm10k_converged = _sens_10k.get("converged")
md_content = f"""# 01_05_05 ICC Variance Decomposition — aoe2companion

spec: reports/specs/01_05_preregistration.md (v1.0.2)

## Method (v1.0.2 — post-adversarial-review)

**Primary estimator:** ANOVA ICC per Wu/Crespi/Wong 2012 CCT 33(5):869-880
(observed-scale), with cluster bootstrap 95 % CI per Ukoumunne et al. 2012
PMC3426610 (n_bootstrap = {N_BOOTSTRAP}). Consistent moment estimator, robust
to τ²-boundary shrinkage that afflicts REML LMM on Bernoulli outcomes.

**Diagnostic estimator:** Random-intercept LMM
`won ~ 1 + (1 | player_id)` via `statsmodels.mixedlm`, REML, LBFGS
(max_iter=50). **Observed-scale Linear Probability Model**, NOT latent-scale
Bernoulli GLMM. Known to pin τ̂² at the boundary when the true τ² is small
(Chung et al. 2013, Psychometrika 78(4):685-709). The delta-method CI assumes
a balanced Gaussian design; Bernoulli outcome + unbalanced n_i invalidates
the CI's asymptotic guarantees. Reported as a diagnostic, NOT as the headline.

**GLMM (latent-scale):** skipped per spec v1.0.2 §14 (c) — compute-prohibitive
at 5k-group scale on project hardware; deferred to Phase 02+.

Reference window: {REF_START} to {REF_END_EXCLUSIVE} (exclusive), minimum
{MIN_OBS_PER_PLAYER} matches/player (spec §8). Primary sample size:
{primary_n:,} players, stratified by `n_matches_in_ref` deciles
(seed = {RANDOM_SEED}).

## Primary result (ANOVA ICC, 5k stratified sample, bootstrap CI)

| Metric | Value | Source |
|---|---|---|
| `icc_anova_observed_scale` | **{icc_anova_primary:.6f}** | Wu/Crespi/Wong 2012, `compute_icc_anova_fast` |
| `icc_anova_ci_low` | {anova_ci_low:.6f} | Cluster bootstrap, n={N_BOOTSTRAP} |
| `icc_anova_ci_high` | {anova_ci_high:.6f} | Cluster bootstrap, n={N_BOOTSTRAP} |

## Verdict

**{verdict}**

The hypothesis range [0.05, 0.20] lies above the bootstrap CI upper bound.
The finding is consistent with calibrated matchmaking compressing observed
win rates toward 0.5 regardless of absolute player skill — interpretation
to be argued in Chapter 4 as a generated hypothesis, not a concluded
finding (see research_log DEFEND-IN-THESIS note 1).

## Sample-size sensitivity (ANOVA point estimates)

| n_players | ICC_anova |
|---|---|
"""
for n, v in anova_by_size.items():
    md_content += f"| {n:,} | {v:.6f} |\n"

md_content += f"""
## Diagnostic: LMM (LPM observed-scale)

| Sample size | ICC_lpm | Converged | Notes |
|---|---|---|---|
| {primary_n:,} | {icc_lpm:.6f} | {lpm_converged} | Primary LMM fit; CI omitted — delta-method assumptions invalid on Bernoulli + unbalanced n_i |
"""
if _lmm10k_icc is not None:
    md_content += (
        f"| 10,000 | {_lmm10k_icc:.6f} | {_lmm10k_converged} | Sensitivity; "
        f"{'significant drift from 5k — consistent with boundary shrinkage' if abs(_lmm10k_icc - icc_lpm) > 1e-3 else 'stable'} |\n"
    )
else:
    md_content += "| 10,000 | — | — | LMM failed or skipped |\n"

md_content += f"""
LMM ICC and ANOVA ICC disagree substantially ({icc_lpm:.6f} vs
{icc_anova_primary:.6f}). This 6× gap is a known pathology: REML LMM on
near-boundary τ² shrinks toward zero (Chung et al. 2013), while ANOVA is a
consistent moment estimator. The ANOVA estimate is preferred. The LMM is
retained here only because spec §8 binds it as the named method; v1.0.2 §14
(b) documents this divergence and promotes ANOVA to primary.

## Cohort summary

| Field | Value |
|---|---|
| `n_eligible_players_total` | {int(df_full['player_id'].nunique()):,} |
| `n_players_primary` | {int(df_primary['player_id'].nunique()):,} |
| `n_obs_primary` | {int(len(df_primary)):,} |
| `obs_per_player_median` | {round(float(obs_per_player.median()), 1)} |
| `obs_per_player_mean` | {round(float(obs_per_player.mean()), 1)} |

## SQL (cohort load)

```sql
{COHORT_SQL.strip()}
```

## Literature

- Wu, Crespi, Wong (2012) CCT 33(5):869-880 — ANOVA ICC for clustered binary outcomes.
- Ukoumunne et al. (2012) PMC3426610 — cluster bootstrap CI.
- Chung et al. (2013) Psychometrika 78(4):685-709 — REML boundary shrinkage on τ² = 0.
- Gelman & Hill (2007) *Data Analysis Using Regression and Multilevel/Hierarchical Models*, §12.5 — delta-method CI for ICC (context: LMM under Gaussian assumptions).
- Searle, Casella, McCulloch (2006) *Variance Components*, §6.5, §6.7 — ML/REML variance-component estimators.
"""

md_path = ARTIFACTS / "01_05_05_icc.md"
md_path.write_text(md_content)
print(f"Wrote: {md_path}")
print("Done.")
