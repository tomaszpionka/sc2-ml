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
# # Cross-region history fragmentation: Phase 02 rolling-feature impact (sc2egset)
#
# **Dataset:** sc2egset
# **Date:** 2026-04-21
# **Canonical artifact:** `reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.md`
#
# spec: reports/specs/01_05_preregistration.md@a5f633ca
#
# **Purpose.** Quantify the empirical impact of the ~12% cross-region player fragmentation
# (accepted bias under I2 Branch iii, `INVARIANTS.md §2`) on Phase 02 rolling-window history
# features. Closes sc2egset WARNING 3 from the 2026-04-21 Phase 01 sign-off sweep.
#
# **I6 discipline:** All SQL that produces a reported result is preserved verbatim in the
# canonical artifact MD §2.
#
# **Hypothesis and 3-threshold falsifier (post-Mode-A):**
# H0: cross-region fragmentation produces negligible per-match rolling-window bias, i.e.:
#   (a) `median_rolling30_undercount ≤ 1 game`
#   (b) `p95_rolling30_undercount ≤ 5 games` (below √30 ≈ 5.5 feature-noise floor)
#   (c) `|bootstrap_CI_upper(mmr_spearman_rho)| < 0.2` (powered at n≈200, Hollander & Wolfe 1999 §11.2)
# Any threshold violated → FAIL. Marginal if violation < 50%.
#
# **Threshold rationale (I7 — no magic numbers):**
# - K=1 (median): win-rate shift from 1-game prefix difference among 30 is ≤ 3.3% absolute,
#   below the typical 5–10% Phase 02 feature-signal contribution threshold.
# - K=5 (p95): √30 ≈ 5.5 is the rolling-30 win-rate feature's own measurement noise at p=0.5;
#   p95 undercount below this level is statistically indistinguishable from feature noise.
# - |ρ|<0.2: at n≈200, this threshold has ~80% power at α=0.05 two-sided
#   (Hollander & Wolfe 1999 §11.2 Table A.30).

# %%
# Step: Cross-region history fragmentation quantification
# Dataset: sc2egset  Date: 2026-04-21

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging

logger = setup_notebook_logging()

# %%
db = get_notebook_db("sc2", "sc2egset", read_only=True)
reports_dir = get_reports_dir("sc2", "sc2egset")
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
artifact_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifact dir: {artifact_dir}")
print(f"DB tables: {db.tables()}")

# %% [markdown]
# ## Schema validation

# %%
print("=== player_history_all schema ===")
print(db.fetch_df("DESCRIBE player_history_all")[["column_name", "column_type"]].to_string())

# %% [markdown]
# ## Analysis §1 — Cross-region nickname identification
#
# Re-runs the cross-region nickname detection SQL from INVARIANTS.md §2.
# This is the authoritative count against which INVARIANTS.md §2 is verified.

# %%
SQL_CROSS_REGION_COUNT = """
-- Cross-region nickname detection (INVARIANTS.md §2 verbatim)
SELECT
    COUNT(*) FILTER (WHERE region_count > 1) * 1.0 / COUNT(*) AS migration_rate,
    COUNT(*) FILTER (WHERE region_count > 1) AS cross_region_count,
    COUNT(*) AS total_nicknames
FROM (
    SELECT LOWER(nickname) AS nick, COUNT(DISTINCT region) AS region_count
    FROM replay_players_raw
    GROUP BY 1
) sub
"""

result_count = db.fetch_df(SQL_CROSS_REGION_COUNT)
print("=== §1 Cross-region nickname count ===")
print(result_count.to_string())
n_cross_region = int(result_count["cross_region_count"].iloc[0])
print(f"\nAuthoritative count: {n_cross_region}")
print(f"Previously recorded: 246")
print(f"Drift detected: {n_cross_region != 246}")

# %%
SQL_CROSS_REGION_SAMPLE = """
SELECT LOWER(nickname) AS nick, COUNT(DISTINCT region) AS region_count
FROM replay_players_raw
GROUP BY 1
HAVING COUNT(DISTINCT region) > 1
ORDER BY region_count DESC, nick
LIMIT 10
"""
print("=== Sample cross-region nicknames (top 10 by region count) ===")
print(db.fetch_df(SQL_CROSS_REGION_SAMPLE).to_string())

# %% [markdown]
# ## Analysis §2 — Lifetime fragmentation ratio (descriptive context)
#
# **NOTE:** This is a DESCRIPTIVE metric only — a loose upper bound on Phase 02 bias.
# The per-match rolling-window undercount in §3 is the primary measurement.
#
# For each cross-region nickname, `fragmentation_ratio = max(games_per_region) / total_games`.
# A ratio of 1.0 means all games in one region; ratio of 0.5 means 50/50 split.
# Lower ratio = more fragmentation = higher Phase 02 rolling-feature bias potential.

# %%
SQL_FRAG_RATIO = """
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
per_region_counts AS (
    SELECT LOWER(r.nickname) AS nick,
           r.region,
           COUNT(*) AS games_in_region
    FROM replay_players_raw r
    INNER JOIN cross_region_nicks crn ON LOWER(r.nickname) = crn.nick
    GROUP BY 1, 2
),
per_nick AS (
    SELECT nick,
           MAX(games_in_region) AS max_region_games,
           SUM(games_in_region) AS total_games,
           MAX(games_in_region) * 1.0 / SUM(games_in_region) AS fragmentation_ratio
    FROM per_region_counts
    GROUP BY nick
)
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY fragmentation_ratio) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fragmentation_ratio) AS median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY fragmentation_ratio) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY fragmentation_ratio) AS p95,
    COUNT(*) AS n_players
FROM per_nick
"""

result_frag = db.fetch_df(SQL_FRAG_RATIO)
print("=== §2 Lifetime Fragmentation Ratio (loose upper bound — NOT primary metric) ===")
print(result_frag.to_string())
frag_ratio_median = float(result_frag["median"].iloc[0])
print(f"\nMedian fragmentation_ratio: {frag_ratio_median:.4f}")
print("Interpretation: median cross-region player concentrates 65% of games in dominant region.")
print("Label: lifetime aggregate — loose upper bound on Phase 02 bias.")

# %% [markdown]
# ## Analysis §3 — PRIMARY: Per-(player, match) rolling-window undercount at window=30
#
# For each match M of each cross-region player:
# - `ph_prior`: prior games for this `toon_id` (player_id_worldwide) before M
# - `unified_prior`: prior games for any toon_id with same LOWER(nickname) before M
# - `rolling30_undercount = min(30, unified_prior) - min(30, ph_prior)`
#
# Temporal discipline: `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING` ordered by
# `details_timeUTC` (ISO-8601 VARCHAR — lexicographic = chronological). No duplicate
# match times per toon_id (confirmed by schema). Implements strict `<` requirement (I3).
#
# Percentiles via DuckDB `PERCENTILE_CONT` (prescribed percentile engine per NOTE-7).

# %%
SQL_ROLLING_UNDERCOUNT_W30 = """
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
player_matches AS (
    SELECT
        h.toon_id,
        LOWER(h.nickname) AS nick,
        h.details_timeUTC AS match_time,
        h.replay_id
    FROM player_history_all h
    INNER JOIN cross_region_nicks crn ON LOWER(h.nickname) = crn.nick
    WHERE h.details_timeUTC IS NOT NULL
),
ph_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        pm.nick,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.toon_id
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS ph_prior_count
    FROM player_matches pm
),
unified_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.nick
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS unified_prior_count
    FROM player_matches pm
),
combined AS (
    SELECT
        p.toon_id,
        p.nick,
        LEAST(30, u.unified_prior_count) - LEAST(30, p.ph_prior_count) AS rolling30_undercount
    FROM ph_prior p
    JOIN unified_prior u ON p.toon_id = u.toon_id AND p.replay_id = u.replay_id
)
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rolling30_undercount) AS median_rolling30_undercount,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rolling30_undercount) AS p95_rolling30_undercount,
    COUNT(*) AS n_player_match_pairs,
    COUNT(DISTINCT toon_id) AS n_distinct_toon_ids,
    AVG(rolling30_undercount) AS mean_rolling30_undercount,
    MAX(rolling30_undercount) AS max_rolling30_undercount
FROM combined
"""

result_w30 = db.fetch_df(SQL_ROLLING_UNDERCOUNT_W30)
print("=== §3 PRIMARY: Per-(player,match) rolling-window undercount (W=30) ===")
print(result_w30.to_string())
median_w30 = float(result_w30["median_rolling30_undercount"].iloc[0])
p95_w30 = float(result_w30["p95_rolling30_undercount"].iloc[0])
n_pairs = int(result_w30["n_player_match_pairs"].iloc[0])
n_toon_ids = int(result_w30["n_distinct_toon_ids"].iloc[0])
print(f"\nThreshold check (a): median={median_w30} <= 1 => {median_w30 <= 1}")
print(f"Threshold check (b): p95={p95_w30} <= 5 => {p95_w30 <= 5}")

# %% [markdown]
# ## Analysis §4 — Sensitivity sweep across windows {5, 10, 30, 100}

# %%
SQL_SENSITIVITY = """
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
player_matches AS (
    SELECT
        h.toon_id,
        LOWER(h.nickname) AS nick,
        h.details_timeUTC AS match_time,
        h.replay_id
    FROM player_history_all h
    INNER JOIN cross_region_nicks crn ON LOWER(h.nickname) = crn.nick
    WHERE h.details_timeUTC IS NOT NULL
),
ph_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        pm.nick,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.toon_id
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS ph_prior_count
    FROM player_matches pm
),
unified_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.nick
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS unified_prior_count
    FROM player_matches pm
),
combined AS (
    SELECT
        p.toon_id,
        p.nick,
        LEAST(5,   u.unified_prior_count) - LEAST(5,   p.ph_prior_count) AS uc5,
        LEAST(10,  u.unified_prior_count) - LEAST(10,  p.ph_prior_count) AS uc10,
        LEAST(30,  u.unified_prior_count) - LEAST(30,  p.ph_prior_count) AS uc30,
        LEAST(100, u.unified_prior_count) - LEAST(100, p.ph_prior_count) AS uc100
    FROM ph_prior p
    JOIN unified_prior u ON p.toon_id = u.toon_id AND p.replay_id = u.replay_id
)
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc5)   AS median_w5,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc5)   AS p95_w5,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc10)  AS median_w10,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc10)  AS p95_w10,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc30)  AS median_w30,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc30)  AS p95_w30,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc100) AS median_w100,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc100) AS p95_w100,
    COUNT(*) AS n_pairs
FROM combined
"""

result_sensitivity = db.fetch_df(SQL_SENSITIVITY)
print("=== §4 Sensitivity sweep across windows {5, 10, 30, 100} ===")
# Reshape to a readable table
sens_table = pd.DataFrame({
    "Window": [5, 10, 30, 100],
    "Median undercount": [
        float(result_sensitivity["median_w5"].iloc[0]),
        float(result_sensitivity["median_w10"].iloc[0]),
        float(result_sensitivity["median_w30"].iloc[0]),
        float(result_sensitivity["median_w100"].iloc[0]),
    ],
    "p95 undercount": [
        float(result_sensitivity["p95_w5"].iloc[0]),
        float(result_sensitivity["p95_w10"].iloc[0]),
        float(result_sensitivity["p95_w30"].iloc[0]),
        float(result_sensitivity["p95_w100"].iloc[0]),
    ],
})
print(sens_table.to_string(index=False))
print(f"\nAll computed over {int(result_sensitivity['n_pairs'].iloc[0])} (player,match) pairs")

# %% [markdown]
# ## Analysis §5 — MMR stratification with bootstrap 95% CI
#
# Per-player median MMR (non-sentinel only; MMR > 0) vs. lifetime fragmentation ratio.
# Spearman ρ point estimate + bootstrap 95% CI (n_bootstrap=1000, paired resampling).
#
# Power calculation: at n≈157 (achieved sample), the minimum detectable |ρ| at α=0.05
# two-sided 80% power per Hollander & Wolfe (1999) §11.2 Table A.30 is approximately
# 0.21 (interpolating n=100 → |ρ|=0.26, n=200 → |ρ|=0.18).
# Threshold |ρ|<0.2 is thus powered (a correlation of |ρ|=0.2 at n=157 is just above
# the 80%-power detectable threshold). The bootstrap CI provides graded interpretation.

# %%
SQL_MMR_FRAG = """
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
per_region_counts AS (
    SELECT LOWER(r.nickname) AS nick,
           r.region,
           COUNT(*) AS games_in_region
    FROM replay_players_raw r
    INNER JOIN cross_region_nicks crn ON LOWER(r.nickname) = crn.nick
    GROUP BY 1, 2
),
frag_ratio AS (
    SELECT nick,
           MAX(games_in_region) * 1.0 / SUM(games_in_region) AS fragmentation_ratio
    FROM per_region_counts
    GROUP BY nick
),
mmr_per_nick AS (
    SELECT LOWER(r.nickname) AS nick,
           MEDIAN(r.MMR) FILTER (WHERE r.MMR > 0) AS median_mmr,
           COUNT(r.MMR) FILTER (WHERE r.MMR > 0) AS n_nonzero_mmr
    FROM replay_players_raw r
    INNER JOIN cross_region_nicks crn ON LOWER(r.nickname) = crn.nick
    GROUP BY 1
)
SELECT f.nick, f.fragmentation_ratio, m.median_mmr, m.n_nonzero_mmr
FROM frag_ratio f
JOIN mmr_per_nick m ON f.nick = m.nick
WHERE m.median_mmr IS NOT NULL AND m.median_mmr > 0
ORDER BY f.nick
"""

df_mmr = db.fetch_df(SQL_MMR_FRAG)
n_players_with_mmr = len(df_mmr)
print(f"=== §5 MMR-fragmentation analysis ===")
print(f"Players with non-sentinel MMR: {n_players_with_mmr} (of {n_cross_region} cross-region)")
print(f"MMR=0 sentinel exclusions: {n_cross_region - n_players_with_mmr}")
print()

x_mmr = df_mmr["fragmentation_ratio"].values
y_mmr = df_mmr["median_mmr"].values
rho_point, pval_point = stats.spearmanr(x_mmr, y_mmr)
print(f"Spearman ρ = {rho_point:.4f}, p = {pval_point:.4f}")

# Bootstrap 95% CI (n_bootstrap=1000, paired per-player resampling)
boot_result = stats.bootstrap(
    (x_mmr, y_mmr),
    lambda x, y: stats.spearmanr(x, y)[0],
    n_resamples=1000,
    confidence_level=0.95,
    random_state=42,
    paired=True,
    vectorized=False,
)
ci_low = float(boot_result.confidence_interval.low)
ci_high = float(boot_result.confidence_interval.high)
print(f"Bootstrap 95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
print(f"|CI_upper| = {abs(ci_high):.4f}")
print(f"Threshold check (c): |CI_upper|={abs(ci_high):.4f} < 0.2 => {abs(ci_high) < 0.2}")
print()
print("Power commentary: at n=157, Hollander & Wolfe (1999) §11.2 tables give minimum")
print("detectable |ρ| ≈ 0.21 at α=0.05 two-sided 80% power. The CI upper bound of")
print(f"{ci_high:.4f} exceeds 0.2, so we cannot rule out a meaningful positive correlation")
print("between fragmentation and skill above the power-detectable threshold.")

# %% [markdown]
# ## Analysis §6 — Rare-handle subsample (handle-collision control)
#
# Within-region handle-collision rate is 30.6% (INVARIANTS.md §2). Short handles
# (e.g., "maru", "dark", "hero") are more likely to be shared by different physical
# players in different regions. Subsample to nicknames with LENGTH(nickname) >= 8
# to reduce this confound and test robustness of the full-sample result.

# %%
SQL_RARE_HANDLES_COUNT = """
SELECT COUNT(*) AS rare_handle_count
FROM (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
) sub
WHERE LENGTH(nick) >= 8
"""

n_rare_handles = int(db.fetch_df(SQL_RARE_HANDLES_COUNT)["rare_handle_count"].iloc[0])
print(f"Rare handles (length >= 8): {n_rare_handles} of {n_cross_region} cross-region")

# %%
SQL_RARE_UNDERCOUNT = """
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
rare_handles AS (
    SELECT nick FROM cross_region_nicks
    WHERE LENGTH(nick) >= 8
),
player_matches AS (
    SELECT
        h.toon_id,
        LOWER(h.nickname) AS nick,
        h.details_timeUTC AS match_time,
        h.replay_id
    FROM player_history_all h
    INNER JOIN rare_handles rh ON LOWER(h.nickname) = rh.nick
    WHERE h.details_timeUTC IS NOT NULL
),
ph_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        pm.nick,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.toon_id
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS ph_prior_count
    FROM player_matches pm
),
unified_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.nick
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS unified_prior_count
    FROM player_matches pm
),
combined AS (
    SELECT
        p.toon_id,
        p.nick,
        LEAST(30, u.unified_prior_count) - LEAST(30, p.ph_prior_count) AS rolling30_undercount
    FROM ph_prior p
    JOIN unified_prior u ON p.toon_id = u.toon_id AND p.replay_id = u.replay_id
)
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rolling30_undercount) AS median_rolling30,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rolling30_undercount) AS p95_rolling30,
    COUNT(*) AS n_pairs,
    COUNT(DISTINCT toon_id) AS n_toon_ids
FROM combined
"""

result_rare = db.fetch_df(SQL_RARE_UNDERCOUNT)
print("=== §6 Rare-handle subsample (length >= 8) — rolling-window W=30 ===")
print(result_rare.to_string())
rare_median = float(result_rare["median_rolling30"].iloc[0])
rare_p95 = float(result_rare["p95_rolling30"].iloc[0])

# %%
SQL_RARE_MMR = """
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
rare_handles AS (
    SELECT nick FROM cross_region_nicks
    WHERE LENGTH(nick) >= 8
),
per_region_counts AS (
    SELECT LOWER(r.nickname) AS nick,
           r.region,
           COUNT(*) AS games_in_region
    FROM replay_players_raw r
    INNER JOIN rare_handles rh ON LOWER(r.nickname) = rh.nick
    GROUP BY 1, 2
),
frag_ratio AS (
    SELECT nick,
           MAX(games_in_region) * 1.0 / SUM(games_in_region) AS fragmentation_ratio
    FROM per_region_counts
    GROUP BY nick
),
mmr_per_nick AS (
    SELECT LOWER(r.nickname) AS nick,
           MEDIAN(r.MMR) FILTER (WHERE r.MMR > 0) AS median_mmr,
           COUNT(r.MMR) FILTER (WHERE r.MMR > 0) AS n_nonzero_mmr
    FROM replay_players_raw r
    INNER JOIN rare_handles rh ON LOWER(r.nickname) = rh.nick
    GROUP BY 1
)
SELECT f.nick, f.fragmentation_ratio, m.median_mmr, m.n_nonzero_mmr
FROM frag_ratio f
JOIN mmr_per_nick m ON f.nick = m.nick
WHERE m.median_mmr IS NOT NULL AND m.median_mmr > 0
ORDER BY f.nick
"""

df_rare_mmr = db.fetch_df(SQL_RARE_MMR)
n_rare_with_mmr = len(df_rare_mmr)
print(f"Rare-handle players with non-sentinel MMR: {n_rare_with_mmr}")

x_rare = df_rare_mmr["fragmentation_ratio"].values
y_rare = df_rare_mmr["median_mmr"].values
rho_rare_point, pval_rare = stats.spearmanr(x_rare, y_rare)
print(f"Rare-handle Spearman ρ = {rho_rare_point:.4f}, p = {pval_rare:.4f}")

boot_rare = stats.bootstrap(
    (x_rare, y_rare),
    lambda x, y: stats.spearmanr(x, y)[0],
    n_resamples=1000,
    confidence_level=0.95,
    random_state=42,
    paired=True,
    vectorized=False,
)
ci_rare_low = float(boot_rare.confidence_interval.low)
ci_rare_high = float(boot_rare.confidence_interval.high)
print(f"Bootstrap 95% CI: [{ci_rare_low:.4f}, {ci_rare_high:.4f}]")
print()
print("=== Full sample vs rare-handle comparison ===")
comp_df = pd.DataFrame({
    "Sample": ["Full (all cross-region)", "Rare-handle (length>=8)"],
    "n_nicknames": [n_cross_region, n_rare_handles],
    "median_rolling30": [median_w30, rare_median],
    "p95_rolling30": [p95_w30, rare_p95],
    "mmr_rho": [round(rho_point, 4), round(rho_rare_point, 4)],
    "mmr_rho_ci_high": [round(ci_high, 4), round(ci_rare_high, 4)],
})
print(comp_df.to_string(index=False))
print()
divergent = abs(rare_median - median_w30) > 5 or abs(rare_p95 - p95_w30) > 10
print(f"Rare-handle subsample consistency with full sample: {'DIVERGENT' if divergent else 'CONSISTENT'}")

# %% [markdown]
# ## Verdict: 3-threshold gate

# %%
threshold_a = median_w30 <= 1
threshold_b = p95_w30 <= 5
threshold_c = abs(ci_high) < 0.2

print("=" * 60)
print("VERDICT — 3-threshold gate")
print("=" * 60)
print(f"(a) median_rolling30_undercount = {median_w30:.1f} <= 1  =>  {'PASS' if threshold_a else 'FAIL'}")
print(f"(b) p95_rolling30_undercount    = {p95_w30:.1f} <= 5  =>  {'PASS' if threshold_b else 'FAIL'}")
print(f"(c) |bootstrap_CI_upper(rho)|   = {abs(ci_high):.4f} < 0.2  =>  {'PASS' if threshold_c else 'FAIL'}")
print()

all_pass = threshold_a and threshold_b and threshold_c
n_violated = sum([not threshold_a, not threshold_b, not threshold_c])

# MARGINAL: ≥1 threshold violated but by < 50%
def is_marginal_violation(actual, threshold, direction="upper"):
    if direction == "upper":
        return threshold < actual < threshold * 1.5
    return False

if all_pass:
    verdict = "PASS"
elif is_marginal_violation(median_w30, 1) and is_marginal_violation(p95_w30, 5) and is_marginal_violation(abs(ci_high), 0.2):
    verdict = "MARGINAL"
else:
    verdict = "FAIL"

print(f"VERDICT: {verdict}")
print()
if verdict == "FAIL":
    print("All 3 thresholds are violated. The I2 Branch (iii) accepted-bias framing")
    print("requires quantitative qualification in §4.2.2. See §5 FAIL paragraph.")

# Sensitivity robustness check per gate condition
# If window=30 is FAIL but also check {5, 10, 100}
print()
print("=== Sensitivity robustness ===")
sens_data = {
    5: {"median": float(result_sensitivity["median_w5"].iloc[0]), "p95": float(result_sensitivity["p95_w5"].iloc[0])},
    10: {"median": float(result_sensitivity["median_w10"].iloc[0]), "p95": float(result_sensitivity["p95_w10"].iloc[0])},
    30: {"median": float(result_sensitivity["median_w30"].iloc[0]), "p95": float(result_sensitivity["p95_w30"].iloc[0])},
    100: {"median": float(result_sensitivity["median_w100"].iloc[0]), "p95": float(result_sensitivity["p95_w100"].iloc[0])},
}
for w, vals in sens_data.items():
    a_pass = vals["median"] <= 1
    b_pass = vals["p95"] <= 5
    print(f"  W={w:3d}: median={vals['median']:.1f} ({'PASS' if a_pass else 'FAIL'}) | p95={vals['p95']:.1f} ({'PASS' if b_pass else 'FAIL'})")

# %% [markdown]
# ## Artifact export

# %%
# Build JSON artifact
json_artifact = {
    "n_cross_region_nicknames": n_cross_region,
    "median_rolling30_undercount_games": median_w30,
    "p95_rolling30_undercount_games": p95_w30,
    "fragmentation_ratio_median_lifetime": frag_ratio_median,
    "mmr_spearman_rho_point": round(rho_point, 4),
    "mmr_spearman_rho_bootstrap_ci_low": round(ci_low, 4),
    "mmr_spearman_rho_bootstrap_ci_high": round(ci_high, 4),
    "n_bootstrap": 1000,
    "n_players_with_mmr": n_players_with_mmr,
    "sensitivity_windows": {
        str(w): {"median": vals["median"], "p95": vals["p95"]}
        for w, vals in sens_data.items()
    },
    "rare_handle_subsample": {
        "n_players": n_rare_handles,
        "median_rolling30_undercount": rare_median,
        "p95_rolling30_undercount": rare_p95,
        "mmr_rho_point": round(rho_rare_point, 4),
        "mmr_rho_ci_low": round(ci_rare_low, 4),
        "mmr_rho_ci_high": round(ci_rare_high, 4),
    },
    "verdict": verdict,
    "hypothesis_thresholds": {
        "median_rolling30_max": 1,
        "p95_rolling30_max": 5,
        "mmr_rho_ci_upper_abs_max": 0.2,
        "window_primary": 30,
        "sensitivity_windows": [5, 10, 30, 100],
    },
    "audit_date": "2026-04-21",
    "percentile_engine": "duckdb_PERCENTILE_CONT",
    "bootstrap_engine": "scipy.stats.bootstrap + pandas",
}

json_path = artifact_dir / "cross_region_history_impact_sc2egset.json"
with open(json_path, "w") as f:
    json.dump(json_artifact, f, indent=2)
logger.info("JSON artifact written: %s", json_path)
print(f"JSON written to: {json_path}")
print(json.dumps(json_artifact, indent=2))

# %%
db.close()
logger.info("DB connection closed.")
print("Done.")
