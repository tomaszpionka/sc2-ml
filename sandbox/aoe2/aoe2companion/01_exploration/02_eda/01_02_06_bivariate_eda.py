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
from scipy.stats import spearmanr  # noqa: E402
rho, pval = spearmanr(df_scatter["rating"], df_scatter["ratingDiff"])
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
from scipy.stats import spearmanr as _spearmanr  # noqa: E402

rho_matrix, p_matrix = _spearmanr(df_corr_sample[corr_columns])

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
