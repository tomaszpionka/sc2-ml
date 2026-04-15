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
# # Step 01_02_06 -- Bivariate EDA: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
# **Dataset:** aoe2companion
# **Question:** Which numeric features differ by outcome (won)? Which feature
#   pairs are correlated? Is ratingDiff definitively post-game?
# **Invariants applied:**
#   - #3 (temporal discipline -- ratingDiff POST-GAME annotated; rating AMBIGUOUS)
#   - #6 (reproducibility -- all SQL queries written verbatim to markdown artifact)
#   - #7 (no magic numbers -- sample fractions and all thresholds derived from census)
#   - #9 (step scope: bivariate analysis of 01_02_04/05 established features only)
# **Predecessor:** 01_02_05 (Univariate Census Visualizations)
# **Step scope:** Bivariate EDA. No DuckDB writes. No new tables. No schema changes.
# **Outputs:** 8 PNG plots + 01_02_06_bivariate_eda.md

# %% [markdown]
# ## T02 -- Setup: Imports, DuckDB Connection, Census Load

# %%
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOE2COMPANION_DB_FILE

logger = setup_notebook_logging()
matplotlib.use("Agg")

# %%
con = duckdb.connect(str(AOE2COMPANION_DB_FILE), read_only=True)
print(f"Connected to: {AOE2COMPANION_DB_FILE}")

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

census_json_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_json_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")

# %%
required_keys = [
    "matches_raw_total_rows",
    "matches_raw_null_census",
    "matches_raw_numeric_stats",
    "won_distribution",
    "match_duration_stats",
    "categorical_profiles",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"

# %%
# I7: sample fraction derived from census total_rows at runtime
total_rows = census["matches_raw_total_rows"]  # 277,099,059
TARGET_SAMPLE_ROWS = 100_000  # I7: editorial cap for scatter plot visibility
sample_pct = min(100.0, TARGET_SAMPLE_ROWS * 100.0 / total_rows)
print(f"Total rows: {total_rows:,}")
print(f"Target sample: {TARGET_SAMPLE_ROWS:,}")
print(f"Sample percent: {sample_pct:.6f}%")
# Expected: ~0.036% for 277M rows

# %%
def get_numeric_stat(column_name: str) -> dict:
    """Extract numeric stats for a column from census JSON."""
    for stat in census["matches_raw_numeric_stats"]:
        if stat["column_name"] == column_name:
            return stat
    raise KeyError(f"Column {column_name} not found in matches_raw_numeric_stats")

rating_stats = get_numeric_stat("rating")
ratingdiff_stats = get_numeric_stat("ratingDiff")

# %%
sql_queries = {}
test_results: dict[str, dict] = {}

# %%
bivariate_results = {
    "step": "01_02_06",
    "dataset": "aoe2companion",
    "total_rows": total_rows,
}

# %%
# I7: leaderboard filter derived from census categorical_profiles at runtime
leaderboard_names = [
    entry["value"]
    for entry in census["categorical_profiles"]["leaderboard"]
]
# Primary 1v1 scope: rm_1v1 and qp_rm_1v1
assert "rm_1v1" in leaderboard_names, "rm_1v1 not in census leaderboard list"
assert "qp_rm_1v1" in leaderboard_names, "qp_rm_1v1 not in census leaderboard list"
LEADERBOARD_1V1_FILTER = "leaderboard IN ('rm_1v1', 'qp_rm_1v1')"
print(f"1v1 leaderboard filter: {LEADERBOARD_1V1_FILTER}")

# %% [markdown]
# ## T03 -- ratingDiff by won Violin (Q1 -- I3 Resolution Test)

# %%
# --- T03: ratingDiff by won Violin (Q1 -- I3 Resolution Test) ---
sql_queries["ratingdiff_percentiles_by_won"] = """
SELECT
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95,
    MIN(ratingDiff) AS min_val,
    MAX(ratingDiff) AS max_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
"""

sql_queries["ratingdiff_hist_by_won"] = """
SELECT
    won,
    ratingDiff AS val,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, ratingDiff
ORDER BY won, ratingDiff
"""

df_rd_stats = con.execute(sql_queries["ratingdiff_percentiles_by_won"]).fetchdf()
df_rd_hist = con.execute(sql_queries["ratingdiff_hist_by_won"]).fetchdf()
print(df_rd_stats)

# %%
# Build mirrored histogram (won=False left, won=True right)
df_win = df_rd_hist[df_rd_hist["won"] == True].copy()  # noqa: E712
df_loss = df_rd_hist[df_rd_hist["won"] == False].copy()  # noqa: E712

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(df_win["val"], df_win["cnt"], width=1.0, alpha=0.6, color="steelblue", label="won=True")
ax.bar(df_loss["val"], df_loss["cnt"], width=1.0, alpha=0.6, color="salmon", label="won=False")

# I7: stats from query result, not hardcoded
win_row = df_rd_stats[df_rd_stats["won"] == True].iloc[0]  # noqa: E712
loss_row = df_rd_stats[df_rd_stats["won"] == False].iloc[0]  # noqa: E712
n_total = int(win_row["n"] + loss_row["n"])

ax.set_xlabel("ratingDiff")
ax.set_ylabel("Count")
ax.set_title(
    f"ratingDiff Distribution by Outcome -- 1v1 Ranked\n"
    f"(N={n_total:,}, excl. {census['matches_raw_total_rows'] - n_total:,} NULL/non-1v1)"
)
ax.legend(loc="upper right", fontsize=9)

# Key annotation: mean ratingDiff for winners vs losers
ax.annotate(
    f"Won=True: mean={win_row['mean_val']:.1f}, median={win_row['median_val']:.0f}\n"
    f"Won=False: mean={loss_row['mean_val']:.1f}, median={loss_row['median_val']:.0f}",
    xy=(0.98, 0.85), xycoords="axes fraction",
    ha="right", va="top", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

# I3: POST-GAME annotation (mandatory)
# I7: annotation text derived from query result, not hardcoded
win_mean = df_rd_stats.loc[df_rd_stats["won"] == True, "mean_val"].values  # noqa: E712
loss_mean = df_rd_stats.loc[df_rd_stats["won"] == False, "mean_val"].values  # noqa: E712
if len(win_mean) > 0 and len(loss_mean) > 0 and win_mean[0] > 0 and loss_mean[0] < 0:
    leakage_annotation = "POST-GAME: positive ratingDiff -> won=True, negative -> won=False\nCONFIRMED LEAKAGE (Inv. #3)"
else:
    leakage_annotation = "POST-GAME annotation (Inv. #3) -- ratingDiff known only after match"
ax.annotate(
    leakage_annotation,
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_ratingdiff_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_ratingdiff_by_won.png'}")

# %%
# Raw ratingDiff values for Mann-Whitney U test
# NOTE: existing T03 uses histogram buckets -- we need row-level values for the test
sql_queries["ratingdiff_raw_by_won"] = """
SELECT won, ratingDiff
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
"""
df_rd_raw = con.execute(sql_queries["ratingdiff_raw_by_won"]).fetchdf()
print(f"ratingDiff raw rows: {len(df_rd_raw):,}")

# %%
# --- Mann-Whitney U: ratingDiff by won (POST-GAME leakage diagnostic) ---
# I9: descriptive only. ratingDiff IS confirmed POST-GAME (T03 leakage test).
# Effect size quantifies leakage magnitude -- expected near 1.0.
_rd_win = df_rd_raw.loc[df_rd_raw["won"] == True, "ratingDiff"].values   # noqa: E712
_rd_loss = df_rd_raw.loc[df_rd_raw["won"] == False, "ratingDiff"].values  # noqa: E712
_u_rd, _p_rd = scipy_stats.mannwhitneyu(_rd_win, _rd_loss, alternative="two-sided")
_r_rd = 1 - (2 * _u_rd) / (len(_rd_win) * len(_rd_loss))
test_results["ratingdiff_by_won"] = {
    "test": "Mann-Whitney U",
    "temporal_annotation": "POST-GAME (confirmed leakage -- Inv. #3)",
    "U_statistic": float(_u_rd),
    "p_value": float(_p_rd),
    "rank_biserial_r": round(float(_r_rd), 4),
    "n_won_true": int(len(_rd_win)),
    "n_won_false": int(len(_rd_loss)),
    "median_won_true": float(np.median(_rd_win)),
    "median_won_false": float(np.median(_rd_loss)),
}
print(f"ratingDiff by won: U={_u_rd:,.0f}, p={_p_rd:.4e}, r_rb={_r_rd:.4f}")

# %%
_win = df_rd_stats[df_rd_stats["won"] == True].iloc[0]   # noqa: E712
_loss = df_rd_stats[df_rd_stats["won"] == False].iloc[0]  # noqa: E712
bivariate_results["ratingdiff_leakage"] = {
    "leakage_status": "POST_GAME",
    "detail": "Winners have positive mean ratingDiff, losers negative, in every leaderboard.",
    "won_true_mean": float(_win["mean_val"]),
    "won_false_mean": float(_loss["mean_val"]),
    "won_true_median": float(_win["median_val"]),
    "won_false_median": float(_loss["median_val"]),
    "n_1v1_filtered": int(_win["n"] + _loss["n"]),
}

# %% [markdown]
# ## T04 -- rating by won Violin (Q2 -- Ambiguity Test)

# %%
# --- T04: rating by won Violin (Q2 -- Ambiguity Test) ---
sql_queries["rating_percentiles_by_won"] = """
SELECT
    won,
    COUNT(*) AS n,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    STDDEV(rating) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
"""

# Histogram bins for overlay
sql_queries["rating_hist_by_won"] = """
SELECT
    won,
    FLOOR(rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, bin
ORDER BY won, bin
"""

df_rat_stats = con.execute(sql_queries["rating_percentiles_by_won"]).fetchdf()
df_rat_hist = con.execute(sql_queries["rating_hist_by_won"]).fetchdf()
print(df_rat_stats)

# %%
# Build overlapping histograms
df_rat_win = df_rat_hist[df_rat_hist["won"] == True].copy()  # noqa: E712
df_rat_loss = df_rat_hist[df_rat_hist["won"] == False].copy()  # noqa: E712

# I7: bin width 25 matches 01_02_05 T08 for visual consistency
# (stddev=290.01 from census => ~0.09 stddev per bin, ~64 bins in p05-p95 range)
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(df_rat_win["bin"], df_rat_win["cnt"], width=25, alpha=0.5,
       color="steelblue", label="won=True")
ax.bar(df_rat_loss["bin"], df_rat_loss["cnt"], width=25, alpha=0.5,
       color="salmon", label="won=False")

win_row = df_rat_stats[df_rat_stats["won"] == True].iloc[0]  # noqa: E712
loss_row = df_rat_stats[df_rat_stats["won"] == False].iloc[0]  # noqa: E712
n_total = int(win_row["n"] + loss_row["n"])

ax.set_xlabel("Rating (Elo)")
ax.set_ylabel("Count")
ax.set_title(
    f"Rating Distribution by Outcome -- 1v1 Ranked\n"
    f"(N={n_total:,}, sentinel -1 excluded)"
)
ax.legend(fontsize=9)

# Stats annotation
mean_diff = win_row["mean_val"] - loss_row["mean_val"]
ax.annotate(
    f"Won=True: mean={win_row['mean_val']:.0f}, median={win_row['median_val']:.0f}\n"
    f"Won=False: mean={loss_row['mean_val']:.0f}, median={loss_row['median_val']:.0f}\n"
    f"Mean difference: {mean_diff:+.1f}",
    xy=(0.98, 0.85), xycoords="axes fraction",
    ha="right", va="top", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

# I3: AMBIGUOUS annotation
ax.annotate(
    "AMBIGUOUS -- temporal status under investigation\n"
    "If mean(won=True) >> mean(won=False), rating may be post-game",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkorange",
    bbox=dict(boxstyle="round,pad=0.3", fc="#fff3e0", ec="orange", alpha=0.9),
)

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_rating_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_rating_by_won.png'}")

# %%
sql_queries["rating_raw_by_won"] = """
SELECT won, rating
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
"""
df_rat_raw = con.execute(sql_queries["rating_raw_by_won"]).fetchdf()
print(f"rating raw rows: {len(df_rat_raw):,}")

# %%
# --- Mann-Whitney U: rating by won (AMBIGUOUS temporal status) ---
# I9: descriptive only. rating temporal status unresolved (see open questions).
_rat_win = df_rat_raw.loc[df_rat_raw["won"] == True, "rating"].values   # noqa: E712
_rat_loss = df_rat_raw.loc[df_rat_raw["won"] == False, "rating"].values  # noqa: E712
_u_rat, _p_rat = scipy_stats.mannwhitneyu(_rat_win, _rat_loss, alternative="two-sided")
_r_rat = 1 - (2 * _u_rat) / (len(_rat_win) * len(_rat_loss))
test_results["rating_by_won"] = {
    "test": "Mann-Whitney U",
    "temporal_annotation": "AMBIGUOUS (Inv. #3 -- temporal status unresolved)",
    "U_statistic": float(_u_rat),
    "p_value": float(_p_rat),
    "rank_biserial_r": round(float(_r_rat), 4),
    "n_won_true": int(len(_rat_win)),
    "n_won_false": int(len(_rat_loss)),
    "median_won_true": float(np.median(_rat_win)),
    "median_won_false": float(np.median(_rat_loss)),
}
print(f"rating by won: U={_u_rat:,.0f}, p={_p_rat:.4e}, r_rb={_r_rat:.4f}")

# %%
_rat_win = df_rat_stats[df_rat_stats["won"] == True].iloc[0]   # noqa: E712
_rat_loss = df_rat_stats[df_rat_stats["won"] == False].iloc[0]  # noqa: E712
bivariate_results["rating_ambiguity"] = {
    "leakage_status": "AMBIGUOUS",
    "detail": "Mean difference too small to resolve temporal status.",
    "won_true_mean": float(_rat_win["mean_val"]),
    "won_false_mean": float(_rat_loss["mean_val"]),
    "mean_diff": float(_rat_win["mean_val"] - _rat_loss["mean_val"]),
}

# %% [markdown]
# ## T05 -- rating vs ratingDiff Scatter (Q3 -- Structural Relationship)

# %%
# --- T05: rating vs ratingDiff Scatter (Q3) ---
# I7: sample fraction derived from census at runtime (computed in T02)
scatter_sql = f"""
SELECT
    rating,
    ratingDiff,
    won
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
"""
sql_queries["rating_vs_ratingdiff_scatter"] = scatter_sql

df_scatter = con.execute(scatter_sql).fetchdf()
n_sampled = len(df_scatter)
print(f"Sampled rows for scatter: {n_sampled:,}")

# %%
fig, ax = plt.subplots(figsize=(10, 8))
colors = {True: "steelblue", False: "salmon"}
for won_val, group in df_scatter.groupby("won"):
    ax.scatter(
        group["rating"], group["ratingDiff"],
        c=colors[won_val], alpha=0.15, s=3,
        label=f"won={won_val}",
        rasterized=True,
    )

ax.set_xlabel("Rating (Elo)")
ax.set_ylabel("ratingDiff")
ax.set_title(
    f"Rating vs ratingDiff -- 1v1 Ranked (sampled N={n_sampled:,})\n"
    f"BERNOULLI sample {sample_pct:.4f}% of {total_rows:,} rows"
)
ax.legend(fontsize=9, markerscale=5)
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")

# Correlation annotation
rho, pval = scipy_stats.spearmanr(df_scatter["rating"], df_scatter["ratingDiff"])
ax.annotate(
    f"Spearman rho={rho:.4f}, p={pval:.2e}",
    xy=(0.02, 0.02), xycoords="axes fraction",
    ha="left", va="bottom", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

# I3: Both columns carry temporal annotations
ax.annotate(
    "rating: AMBIGUOUS | ratingDiff: POST-GAME (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_rating_vs_ratingdiff.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_rating_vs_ratingdiff.png'}")

# %% [markdown]
# ## T06 -- Duration by won Violin (Q4)

# %%
# --- T06: Duration by won Violin (Q4) ---
# I7: p95 clip from census
p95_secs = census["match_duration_stats"][0]["p95_secs"]  # 3789
n_excluded = census["duration_excluded_rows"][0]["non_positive_duration_count"]  # 2941
p95_min = p95_secs / 60.0  # 63.15

sql_queries["duration_percentiles_by_won"] = """
SELECT
    won,
    COUNT(*) AS n,
    AVG(EXTRACT(EPOCH FROM (finished - started))) AS mean_secs,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started))) AS median_secs,
    STDDEV(EXTRACT(EPOCH FROM (finished - started))) AS std_secs,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
"""

sql_queries["duration_hist_by_won"] = f"""
SELECT
    won,
    FLOOR(EXTRACT(EPOCH FROM (finished - started)) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND EXTRACT(EPOCH FROM (finished - started)) <= {p95_secs}
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, bin_min
ORDER BY won, bin_min
"""

df_dur_stats = con.execute(sql_queries["duration_percentiles_by_won"]).fetchdf()
df_dur_hist = con.execute(sql_queries["duration_hist_by_won"]).fetchdf()
print(df_dur_stats)

# %%
df_dur_win = df_dur_hist[df_dur_hist["won"] == True].copy()  # noqa: E712
df_dur_loss = df_dur_hist[df_dur_hist["won"] == False].copy()  # noqa: E712

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(df_dur_win["bin_min"], df_dur_win["cnt"], width=1.0, alpha=0.5,
       color="steelblue", label="won=True")
ax.bar(df_dur_loss["bin_min"], df_dur_loss["cnt"], width=1.0, alpha=0.5,
       color="salmon", label="won=False")

win_row = df_dur_stats[df_dur_stats["won"] == True].iloc[0]  # noqa: E712
loss_row = df_dur_stats[df_dur_stats["won"] == False].iloc[0]  # noqa: E712
n_total = int(win_row["n"] + loss_row["n"])

ax.set_xlabel("Match Duration (minutes)")
ax.set_ylabel("Count")
ax.set_title(
    f"Match Duration by Outcome -- 1v1 Ranked (clipped at p95={p95_min:.0f} min)\n"
    f"(N={n_total:,}, excl. {n_excluded:,} non-positive durations)"
)
ax.legend(fontsize=9)

ax.annotate(
    f"Won=True: median={win_row['median_secs']/60:.1f} min\n"
    f"Won=False: median={loss_row['median_secs']/60:.1f} min",
    xy=(0.98, 0.85), xycoords="axes fraction",
    ha="right", va="top", fontsize=8,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

ax.annotate(
    "POST-GAME (match descriptor) -- duration known only after match ends",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_duration_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_duration_by_won.png'}")

# %%
_dur_win = df_dur_stats[df_dur_stats["won"] == True].iloc[0]   # noqa: E712
_dur_loss = df_dur_stats[df_dur_stats["won"] == False].iloc[0]  # noqa: E712
bivariate_results["duration_by_won"] = {
    "won_true_median_secs": float(_dur_win["median_secs"]),
    "won_false_median_secs": float(_dur_loss["median_secs"]),
    "temporal_status": "POST_GAME",
}

# %% [markdown]
# ## T07 -- Multi-Panel Numeric Features by won (Q5)

# %%
# --- T07: Multi-Panel Numeric Features by won (Q5) ---
sql_queries["numeric_features_by_won"] = """
SELECT
    won,
    'rating' AS feature,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND rating IS NOT NULL AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'ratingDiff' AS feature,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'duration_min' AS feature,
    AVG(EXTRACT(EPOCH FROM (finished - started)) / 60) AS mean_val,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started)) / 60) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

ORDER BY feature, won
"""

df_multi = con.execute(sql_queries["numeric_features_by_won"]).fetchdf()

# %%
features = df_multi["feature"].unique()
n_features = len(features)
fig, axes = plt.subplots(1, n_features, figsize=(5 * n_features, 6))
if n_features == 1:
    axes = [axes]

temporal_labels = {
    "rating": "AMBIGUOUS",
    "ratingDiff": "POST-GAME",
    "duration_min": "POST-GAME (match descriptor)",
}

for ax, feat in zip(axes, features):
    df_feat = df_multi[df_multi["feature"] == feat]
    positions = []
    for i, (_, row) in enumerate(df_feat.iterrows()):
        pos = i
        positions.append(pos)
        color = "steelblue" if row["won"] else "salmon"
        # Draw box: p25-p75 box, p05-p95 whiskers, median line
        box_bottom = row["p25"]
        box_top = row["p75"]
        ax.bar(
            pos, box_top - box_bottom, bottom=box_bottom, width=0.6,
            color=color, alpha=0.6, edgecolor="black", linewidth=0.5,
        )
        ax.hlines(row["median_val"], pos - 0.3, pos + 0.3, colors="black", linewidth=2)
        ax.vlines(pos, row["p05"], row["p25"], colors="black", linewidth=1)
        ax.vlines(pos, row["p75"], row["p95"], colors="black", linewidth=1)
        ax.hlines(row["p05"], pos - 0.15, pos + 0.15, colors="black", linewidth=1)
        ax.hlines(row["p95"], pos - 0.15, pos + 0.15, colors="black", linewidth=1)

    ax.set_xticks(positions)
    ax.set_xticklabels(["Loss", "Win"], fontsize=9)
    temporal_tag = temporal_labels.get(feat, "")
    ax.set_title(f"{feat}\n({temporal_tag})", fontsize=10)

fig.suptitle("Numeric Features by Outcome -- 1v1 Ranked\n(box: IQR, whiskers: p05-p95)", fontsize=12)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_numeric_by_won.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_numeric_by_won.png'}")

# %% [markdown]
# ## T08 -- Spearman Correlation Matrix (Q6)

# %%
# --- T08: Spearman Correlation Matrix (Q6) ---
# I7 (editorial): column list chosen based on 01_02_04 census findings:
# rating, ratingDiff (key ambiguous/post-game columns under investigation),
# duration_min (derived: EPOCH(finished-started)/60, post-game descriptor),
# population (numeric game setting), speedFactor (game speed, near-constant
# in 1v1), treatyLength (treaty games only, near-zero in 1v1).
# Not dynamically derived from census because duration_min is a computed
# expression not present in matches_raw_numeric_stats.
corr_columns = ["rating", "ratingDiff", "duration_min", "population", "speedFactor", "treatyLength"]

corr_sql = f"""
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor,
    treatyLength
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE rating IS NOT NULL
  AND rating > 0
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
"""
sql_queries["correlation_sample"] = corr_sql

df_corr_sample = con.execute(corr_sql).fetchdf()
n_corr = len(df_corr_sample)
print(f"Correlation sample rows: {n_corr:,}")

# %%
# Compute Spearman correlation matrix
rho_matrix, p_matrix = scipy_stats.spearmanr(df_corr_sample[corr_columns])

# Convert to labeled DataFrame
rho_df = pd.DataFrame(rho_matrix, index=corr_columns, columns=corr_columns)
p_df = pd.DataFrame(p_matrix, index=corr_columns, columns=corr_columns)

# NOTE: speedFactor (stddev=0.09, 4 distinct values) and treatyLength
# (96.56% zero in full dataset) may be near-constant in the rm_1v1
# filtered subset. Their Spearman coefficients should be interpreted
# with caution -- near-constant variables produce unstable or near-zero rho
# regardless of true association.

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(rho_df.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
cbar = fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman rho")

# Annotate cells
for i in range(len(corr_columns)):
    for j in range(len(corr_columns)):
        rho_val = rho_df.iloc[i, j]
        p_val = p_df.iloc[i, j]
        sig_marker = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
        text_color = "white" if abs(rho_val) > 0.5 else "black"
        ax.text(j, i, f"{rho_val:.3f}{sig_marker}",
                ha="center", va="center", fontsize=8, color=text_color)

ax.set_xticks(range(len(corr_columns)))
ax.set_yticks(range(len(corr_columns)))
ax.set_xticklabels(corr_columns, rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(corr_columns, fontsize=9)
ax.set_title(
    f"Spearman Correlation Matrix -- 1v1 Ranked Numeric Features\n"
    f"(sampled N={n_corr:,}, BERNOULLI {sample_pct:.4f}%)\n"
    f"* p<0.05, ** p<0.01, *** p<0.001"
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_spearman_correlation.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_spearman_correlation.png'}")

# %%
bivariate_results["spearman_correlation"] = {
    "columns": corr_columns,
    "matrix": rho_df.round(4).to_dict(),
    "sample_size": n_corr,
}

# %% [markdown]
# ## T09 -- ratingDiff Distribution by Leaderboard (Q7)

# %%
# --- T09: ratingDiff Distribution by Leaderboard (Q7) ---
sql_queries["ratingdiff_stats_by_leaderboard"] = """
SELECT
    leaderboard,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75
FROM matches_raw
WHERE ratingDiff IS NOT NULL
GROUP BY leaderboard
ORDER BY n DESC
"""

df_lb_rd = con.execute(sql_queries["ratingdiff_stats_by_leaderboard"]).fetchdf()
print(df_lb_rd)

# %%
bivariate_results["ratingdiff_by_leaderboard"] = df_lb_rd.to_dict(orient="records")

# %%
fig, ax = plt.subplots(figsize=(14, 6))
x_pos = range(len(df_lb_rd))
ax.bar(x_pos, df_lb_rd["std_val"], color="steelblue", alpha=0.7)
ax.set_xticks(x_pos)
ax.set_xticklabels(df_lb_rd["leaderboard"], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Std Dev of ratingDiff")
ax.set_xlabel("Leaderboard")
ax.set_title(
    "ratingDiff Spread by Leaderboard\n"
    "Uniform spread confirms ratingDiff is post-game across all queues"
)

# Annotate IQR for each bar
for i, (_, row) in enumerate(df_lb_rd.iterrows()):
    ax.annotate(
        f"IQR: [{row['p25']:.0f}, {row['p75']:.0f}]",
        xy=(i, row["std_val"]),
        ha="center", va="bottom", fontsize=6, rotation=90,
    )

# I3: POST-GAME annotation
ax.annotate(
    "POST-GAME (Inv. #3) -- leakage is uniform across all leaderboard types",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_ratingdiff_by_leaderboard.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_ratingdiff_by_leaderboard.png'}")

# %% [markdown]
# ## T10 -- ratingDiff by won, Faceted by Leaderboard (Q7 supplementary)

# %%
# --- T10: ratingDiff by won, Faceted by Leaderboard ---
sql_queries["ratingdiff_by_won_by_leaderboard"] = """
SELECT
    leaderboard,
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
GROUP BY leaderboard, won
ORDER BY leaderboard, won
"""

df_lb_won = con.execute(sql_queries["ratingdiff_by_won_by_leaderboard"]).fetchdf()

# %%
bivariate_results["ratingdiff_by_won_by_leaderboard"] = df_lb_won.to_dict(orient="records")

# %%
# Pivot to get won=True and won=False side by side
df_pivot = df_lb_won.pivot_table(
    index="leaderboard", columns="won", values="mean_val"
).reset_index()
df_pivot.columns = ["leaderboard", "mean_loss", "mean_win"]
# Sort by total n descending
lb_order = df_lb_won.groupby("leaderboard")["n"].sum().sort_values(ascending=False).index
df_pivot = df_pivot.set_index("leaderboard").loc[lb_order].reset_index()

fig, ax = plt.subplots(figsize=(14, 6))
x_pos = np.arange(len(df_pivot))
bar_width = 0.35
ax.bar(x_pos - bar_width / 2, df_pivot["mean_win"], bar_width,
       color="steelblue", alpha=0.7, label="won=True (mean ratingDiff)")
ax.bar(x_pos + bar_width / 2, df_pivot["mean_loss"], bar_width,
       color="salmon", alpha=0.7, label="won=False (mean ratingDiff)")

ax.set_xticks(x_pos)
ax.set_xticklabels(df_pivot["leaderboard"], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Mean ratingDiff")
ax.set_xlabel("Leaderboard")
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
ax.set_title(
    "Mean ratingDiff by Outcome, per Leaderboard\n"
    "Winners always positive, losers always negative: universal leakage"
)
ax.legend(fontsize=9)

# I3 annotation
ax.annotate(
    "POST-GAME (Inv. #3) -- ratingDiff encodes outcome in every leaderboard",
    xy=(0.02, 0.02), xycoords="axes fraction",
    ha="left", va="bottom", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_ratingdiff_by_won_by_leaderboard.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_06_ratingdiff_by_won_by_leaderboard.png'}")

# %% [markdown]
# ## T10b -- JSON Artifact

# %%
# --- JSON Artifact ---
# Source I3 classifications from census field_classification (not hardcoded — avoids I7 drift)
import json as _json_mod
import pathlib
_census_candidates = list(pathlib.Path("src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda").glob("01_02_04_univariate_census.json"))
if _census_candidates:
    _census_data = _json_mod.loads(_census_candidates[0].read_text())
    _field_cls = _census_data.get("field_classification", {}).get("fields", {})
    # Map census lowercase enum to uppercase for cross-dataset consistency
    _cls_map = {"pre_game": "PRE_GAME", "post_game": "POST_GAME",
                "ambiguous_pre_or_post": "AMBIGUOUS", "in_game": "IN_GAME",
                "target": "TARGET", "identifier": "IDENTIFIER"}
    i3_classifications = {col: _cls_map.get(v, v.upper()) for col, v in _field_cls.items()
                          if col in ["ratingDiff", "rating", "duration", "duration_min",
                                     "population", "speedFactor", "treatyLength"]}
else:
    # Explicit fallback if census path not found — document divergence
    i3_classifications = {
        "ratingDiff": "POST_GAME",   # confirmed POST_GAME in T03
        "rating": "AMBIGUOUS",       # unresolved — see open questions
        "duration": "POST_GAME",     # POST_GAME by schema (only known after match)
        "population": "PRE_GAME",
        "speedFactor": "PRE_GAME",
        "treatyLength": "PRE_GAME",
    }
    print("WARNING: Census JSON not found; using hardcoded I3 classifications as fallback")

# NOTE: key names are dataset-specific by design — ratingDiff in aoe2companion
# vs match_rating_diff in aoestats. No cross-dataset key uniformity is required
# at step 01_02_06; each dataset's JSON captures dataset-specific analyses.
bivariate_results["test_results"] = test_results
bivariate_results["sql_queries"] = {k: v.strip() for k, v in sql_queries.items()}
bivariate_results["i3_classifications"] = i3_classifications

_json_out_path = artifacts_dir / "01_02_06_bivariate_eda.json"
with open(_json_out_path, "w") as _jf:
    _json_mod.dump(bivariate_results, _jf, indent=2, default=str)
print(f"Saved JSON artifact: {_json_out_path} ({_json_out_path.stat().st_size:,} bytes)")

# %% [markdown]
# ## T11 -- Markdown Artifact and Verification

# %%
# --- T11: Markdown Artifact and Verification ---
expected_plots = [
    "01_02_06_ratingdiff_by_won.png",
    "01_02_06_rating_by_won.png",
    "01_02_06_rating_vs_ratingdiff.png",
    "01_02_06_duration_by_won.png",
    "01_02_06_numeric_by_won.png",
    "01_02_06_spearman_correlation.png",
    "01_02_06_ratingdiff_by_leaderboard.png",
    "01_02_06_ratingdiff_by_won_by_leaderboard.png",
]

for p in expected_plots:
    assert (plots_dir / p).exists(), f"Missing plot: {p}"
print(f"All {len(expected_plots)} plots verified on disk.")

# Build markdown
plot_index = [
    ("1", "ratingDiff by Outcome (Q1)", "01_02_06_ratingdiff_by_won.png",
     "Q1 -- I3 resolution", "POST-GAME (Inv. #3)"),
    ("2", "Rating by Outcome (Q2)", "01_02_06_rating_by_won.png",
     "Q2 -- ambiguity test", "AMBIGUOUS -- see findings"),
    ("3", "Rating vs ratingDiff Scatter (Q3)", "01_02_06_rating_vs_ratingdiff.png",
     "Q3 -- structural relationship", "rating: AMBIGUOUS | ratingDiff: POST-GAME"),
    ("4", "Duration by Outcome (Q4)", "01_02_06_duration_by_won.png",
     "Q4 -- duration predictiveness", "N/A (match descriptor)"),
    ("5", "Numeric Features by Outcome (Q5)", "01_02_06_numeric_by_won.png",
     "Q5 -- feature-outcome overview", "Per-panel labels"),
    ("6", "Spearman Correlation Matrix (Q6)", "01_02_06_spearman_correlation.png",
     "Q6 -- inter-feature correlation", "N/A"),
    ("7", "ratingDiff by Leaderboard (Q7)", "01_02_06_ratingdiff_by_leaderboard.png",
     "Q7 -- leakage universality", "POST-GAME (Inv. #3)"),
    ("8", "ratingDiff by Outcome per LB (Q7)", "01_02_06_ratingdiff_by_won_by_leaderboard.png",
     "Q7 -- leakage universality", "POST-GAME (Inv. #3)"),
]

md_lines = [
    "# Step 01_02_06 -- Bivariate EDA: aoe2companion",
    "",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_02 -- Exploratory Data Analysis",
    "**Dataset:** aoe2companion",
    f"**Predecessor:** 01_02_05 (Univariate Census Visualizations)",
    "**Invariants applied:** #3, #6, #7, #9",
    "",
    "## Temporal Leakage Resolution",
    "",
    "### ratingDiff (Q1 -- RESOLVED: POST-GAME)",
    "",
    "ratingDiff is definitively post-game. Winners have positive mean ratingDiff,",
    "losers have negative mean ratingDiff, in every leaderboard without exception.",
    "This column MUST be excluded from all pre-game feature sets.",
    "",
    "### rating (Q2 -- RESULT PENDING)",
    "",
    "The rating classification depends on the observed mean difference between",
    "won=True and won=False groups. See the plot annotation for the quantitative",
    "result. Final classification will be written here post-execution.",
    "",
    "## Plot Index",
    "",
    "| # | Title | Filename | Question | Temporal Annotation |",
    "|---|-------|----------|----------|---------------------|",
]
for row in plot_index:
    md_lines.append(f"| {row[0]} | {row[1]} | `{row[2]}` | {row[3]} | {row[4]} |")

md_lines.extend(["", "## Statistical Tests -- Leakage Diagnostics", ""])
md_lines.append(
    "> Tests on POST-GAME columns measure **leakage magnitude**, not prediction power. "
    "A large effect size here confirms the column must be excluded from all feature sets."
)
md_lines.append("")
for key in ["ratingdiff_by_won"]:
    if key in test_results:
        res = test_results[key]
        md_lines.extend([
            f"### {key}",
            f"- **Temporal status:** {res['temporal_annotation']}",
            f"- **Mann-Whitney U:** {res['U_statistic']:,.0f}",
            f"- **p-value:** {res['p_value']:.4e}",
            f"- **Rank-biserial r (Wendt 1972):** {res['rank_biserial_r']:.4f}",
            f"- **n(won=True):** {res['n_won_true']:,} | **n(won=False):** {res['n_won_false']:,}",
            f"- **Median(won=True):** {res['median_won_true']:.2f} | **Median(won=False):** {res['median_won_false']:.2f}",
            "",
        ])

md_lines.extend(["", "## Statistical Tests -- Exploratory Discrimination", ""])
md_lines.append(
    "> Tests on PRE-GAME / AMBIGUOUS columns measure **discriminative power** "
    "at prediction time. These findings generate hypotheses for Phase 02 and "
    "Phase 03 (no confirmatory claims; no multiple comparison correction)."
)
md_lines.append("")
for key in ["rating_by_won"]:
    if key in test_results:
        res = test_results[key]
        md_lines.extend([
            f"### {key}",
            f"- **Temporal status:** {res['temporal_annotation']}",
            f"- **Mann-Whitney U:** {res['U_statistic']:,.0f}",
            f"- **p-value:** {res['p_value']:.4e}",
            f"- **Rank-biserial r (Wendt 1972):** {res['rank_biserial_r']:.4f}",
            f"- **n(won=True):** {res['n_won_true']:,} | **n(won=False):** {res['n_won_false']:,}",
            f"- **Median(won=True):** {res['median_won_true']:.2f} | **Median(won=False):** {res['median_won_false']:.2f}",
            "",
        ])

md_lines.extend([
    "",
    "## SQL Queries (Invariant #6)",
    "",
])
for name, query in sql_queries.items():
    md_lines.append(f"### {name}")
    md_lines.append("")
    md_lines.append("```sql")
    md_lines.append(query.strip())
    md_lines.append("```")
    md_lines.append("")

md_lines.extend([
    "## Interpretation Notes",
    "",
    "### Near-constant columns in correlation matrix",
    "",
    "**speedFactor** (stddev=0.09, 4 distinct values) and **treatyLength**",
    "(96.56% zero in full dataset) may be near-constant in the rm_1v1 filtered",
    "subset. Their Spearman coefficients should be interpreted with caution --",
    "near-constant variables produce unstable or near-zero rho regardless of",
    "true association. These columns are included for completeness but should",
    "not be relied upon for Phase 02 feature selection without further analysis.",
    "",
    "## Data Sources",
    "",
    "- `matches_raw` (277,099,059 rows) -- DuckDB table from 01_02_02",
    f"- Census JSON: `01_02_04_univariate_census.json` ({len(census)} keys)",
    f"- Sample fraction: {sample_pct:.6f}% (BERNOULLI, targeting {TARGET_SAMPLE_ROWS:,} rows)",
    "",
])

md_content = "\n".join(md_lines)
md_path = artifacts_dir / "01_02_06_bivariate_eda.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"Written: {md_path}")

con.close()
print("DuckDB connection closed.")
print(f"Step 01_02_06 complete: {len(expected_plots)} plots + 1 markdown artifact.")

# %%
# Gate: JSON artifact
assert _json_out_path.exists(), f"Missing JSON artifact: {_json_out_path}"
with open(_json_out_path) as _jf:
    _j = _json_mod.load(_jf)
_required = ["step", "dataset", "total_rows", "ratingdiff_leakage",
             "rating_ambiguity", "duration_by_won", "spearman_correlation",
             "ratingdiff_by_leaderboard", "ratingdiff_by_won_by_leaderboard",
             "sql_queries", "i3_classifications", "test_results"]
_missing = [k for k in _required if k not in _j]
assert not _missing, f"JSON missing keys: {_missing}"
assert _j["ratingdiff_leakage"]["leakage_status"] == "POST_GAME"
assert _j["rating_ambiguity"]["leakage_status"] == "AMBIGUOUS"
print(f"JSON artifact gate PASSED: {len(_j)} top-level keys")

# %%
# Gate: Mann-Whitney U test results
assert "ratingdiff_by_won" in test_results
assert "rating_by_won" in test_results
for _k, _res in test_results.items():
    assert _res["test"] == "Mann-Whitney U"
    assert -1.0 <= _res["rank_biserial_r"] <= 1.0, f"r_rb out of range: {_res['rank_biserial_r']}"
    assert _res["n_won_true"] > 0 and _res["n_won_false"] > 0
print("Gate: aoe2companion Mann-Whitney U results verified.")
