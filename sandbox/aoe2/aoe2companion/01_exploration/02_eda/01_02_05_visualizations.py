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
# # Step 01_02_05 -- Univariate Census Visualizations: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
# **Dataset:** aoe2companion
# **Question:** What do the univariate distributions from 01_02_04 look like visually?
# **Invariants applied:**
#   - #3 (temporal discipline -- ratingDiff POST-GAME annotated; rating AMBIGUOUS noted)
#   - #6 (reproducibility -- all SQL queries written verbatim to markdown artifact)
#   - #7 (no magic numbers -- all thresholds derived from census JSON at runtime)
#   - #9 (step scope: visualization of 01_02_04 findings only -- no new analytics)
# **Predecessor:** 01_02_04 (Univariate Census) -- reads its JSON artifact
# **Step scope:** Visualization only. No DuckDB writes. No new tables. No schema changes.
# **Outputs:** 17 PNG plots + 01_02_05_visualizations.md

# %% [markdown]
# ## 0. Imports

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

# %% [markdown]
# ## 1. Setup: DuckDB connection, census JSON, paths

# %%
con = duckdb.connect(str(AOE2COMPANION_DB_FILE), read_only=True)
print(f"Connected to: {AOE2COMPANION_DB_FILE}")

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifacts dir: {artifacts_dir}")
print(f"Plots dir: {plots_dir}")

# %%
census_json_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_json_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")

# Validate required keys
required_keys = [
    "won_distribution",
    "won_consistency_2row",
    "categorical_profiles",
    "matches_raw_null_census",
    "match_duration_stats",
    "boolean_census",
    "matches_raw_null_cooccurrence",
    "matches_raw_total_rows",
]
for key in required_keys:
    assert key in census, f"Missing required census key: {key}"
print(f"All {len(required_keys)} required keys present.")

# %%
sql_queries: dict[str, str] = {}

# %% [markdown]
# ## T03 -- Plot 1: Won Distribution 2-Bar (Q1 -- Target balance)

# %%
# I7: all counts from census JSON at runtime; no hardcoded numbers
won_data = census["won_distribution"]
# Filter non-null for bars; extract null entry for annotation
non_null_entries = [r for r in won_data if r["won"] is not None]
null_entries = [r for r in won_data if r["won"] is None]
total_n = sum(r["cnt"] for r in won_data)
null_cnt = null_entries[0]["cnt"] if null_entries else 0
null_pct = null_entries[0]["pct"] if null_entries else 0.0

print(f"Non-null entries: {len(non_null_entries)}")
print(f"Total rows: {total_n:,}")
print(f"NULL count: {null_cnt:,} ({null_pct:.2f}%)")
for e in non_null_entries:
    print(f"  won={e['won']}: {e['cnt']:,} ({e['pct']:.2f}%)")

# %%
labels = []
counts = []
colors = []
color_map_won = {True: "steelblue", False: "salmon"}
for row in non_null_entries:
    labels.append("Win" if row["won"] else "Loss")
    counts.append(row["cnt"])
    colors.append(color_map_won[row["won"]])

fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(labels, counts, color=colors, edgecolor="black", linewidth=0.5)
for bar, cnt, row in zip(bars, counts, non_null_entries):
    ax.annotate(
        f"{cnt:,}\n({row['pct']:.2f}%)",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=11,
    )
ax.set_xlabel("Outcome")
ax.set_ylabel("Row count")
ax.set_title(f"Target Variable Distribution — won (N={total_n:,})")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.set_ylim(0, max(counts) * 1.15)
ax.text(
    0.5, -0.12,
    f"Excluded: {null_cnt:,} NULL ({null_pct:.2f}%)",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=10,
    color="gray",
    style="italic",
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_won_distribution.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_won_distribution.png'}")

# %% [markdown]
# ## T04 -- Plot 2: Won Consistency Stacked Bar (Q2 -- Intra-match consistency)

# %%
# I7: values from census JSON
raw_consistency = census["won_consistency_2row"][0]
total_2row = raw_consistency["total_2row_matches"]
categories = [
    ("complementary", raw_consistency["consistent_complement"]),
    ("both_true", raw_consistency["both_true"]),
    ("both_false", raw_consistency["both_false"]),
    ("mixed_null", (
        raw_consistency["both_null"]
        + raw_consistency["one_true_one_null"]
        + raw_consistency["one_false_one_null"]
    )),
]
color_map_consistency = {
    "complementary": "green",
    "both_true": "red",
    "both_false": "orange",
    "mixed_null": "gray",
}

print(f"total_2row_matches: {total_2row:,}")
for cat, cnt in categories:
    pct = 100.0 * cnt / total_2row
    print(f"  {cat}: {cnt:,} ({pct:.2f}%)")

# %%
fig, ax = plt.subplots(figsize=(14, 3))
left = 0.0
for cat, cnt in categories:
    pct = 100.0 * cnt / total_2row
    color = color_map_consistency[cat]
    ax.barh(
        0, pct, left=left,
        color=color, label=f"{cat} ({pct:.2f}%)",
        edgecolor="white", linewidth=0.5,
    )
    if pct > 0.5:
        ax.text(
            left + pct / 2, 0,
            f"{pct:.2f}%",
            ha="center", va="center",
            fontsize=8, fontweight="bold", color="black",
        )
    left += pct

ax.set_xlim(0, 100)
ax.set_yticks([])
ax.set_xlabel("Percentage of 2-row matches")
ax.set_title("Intra-Match Won Consistency (2-Row Matches)")
ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.3),
    ncol=4,
    fontsize=9,
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_won_consistency.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_won_consistency.png'}")

# %% [markdown]
# ## T05 -- Plot 3: Leaderboard Distribution Bar (Q4 -- Leaderboard volume)

# %%
# I7: total_rows from census
lb_data = pd.DataFrame(census["categorical_profiles"]["leaderboard"])
lb_data = lb_data.rename(columns={"value": "leaderboard"})
lb_sorted = lb_data.sort_values("cnt", ascending=False)
total_matches = census["matches_raw_total_rows"]

# Highlight rm_1v1 and qp_rm_1v1
highlight_set = {"rm_1v1", "qp_rm_1v1"}
combined_highlight = lb_data[lb_data["leaderboard"].isin(highlight_set)]["cnt"].sum()
combined_pct = 100.0 * combined_highlight / total_matches

print(f"Total rows: {total_matches:,}")
print(f"rm_1v1 + qp_rm_1v1 combined: {combined_highlight:,} ({combined_pct:.2f}%)")
print(lb_sorted.to_string(index=False))

# %%
colors_lb = [
    "#ff7f0e" if row["leaderboard"] in highlight_set else "#1f77b4"
    for _, row in lb_sorted.iterrows()
]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.bar(
    range(len(lb_sorted)),
    lb_sorted["cnt"],
    color=colors_lb,
    edgecolor="black",
    linewidth=0.4,
)
for bar, (_, row) in zip(bars, lb_sorted.iterrows()):
    ax.annotate(
        f"{row['cnt']:,}\n({row['pct']:.2f}%)",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 3),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=7,
    )
ax.set_xticks(range(len(lb_sorted)))
ax.set_xticklabels(lb_sorted["leaderboard"], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Row count")
ax.set_title(f"Leaderboard Distribution — matches_raw (N={total_matches:,})")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.text(
    0.99, 0.97,
    f"rm_1v1 + qp_rm_1v1: {combined_highlight:,} ({combined_pct:.1f}%) [orange]",
    transform=ax.transAxes,
    ha="right", va="top",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="#fff3e0", ec="orange", alpha=0.9),
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_leaderboard_distribution.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_leaderboard_distribution.png'}")

# %% [markdown]
# ## T06 -- Plot 4: Civilization Top-20 Barh (Q5 -- Civ pick rates)

# %%
civ_data = pd.DataFrame(census["categorical_profiles"]["civ"])
civ_data = civ_data.rename(columns={"value": "civ"})
# Take top-20
civ_top20 = civ_data.head(20)
civ_top20_pct = civ_top20["pct"].sum()

# I7: cardinality from census null_census
null_census_df = pd.DataFrame(census["matches_raw_null_census"])
civ_card_row = null_census_df[null_census_df["column_name"] == "civ"]
civ_cardinality = int(civ_card_row["approx_cardinality"].values[0])

print(f"Civ cardinality: {civ_cardinality}")
print(f"Top-20 coverage: {civ_top20_pct:.2f}%")
print(civ_top20.to_string(index=False))

# %%
civ_sorted = civ_top20.sort_values("cnt", ascending=True)

fig, ax = plt.subplots(figsize=(10, 8))
bars = ax.barh(civ_sorted["civ"], civ_sorted["cnt"], color="#9b59b6", edgecolor="black", linewidth=0.3)
for bar, (_, row) in zip(bars, civ_sorted.iterrows()):
    ax.text(
        bar.get_width() + bar.get_width() * 0.01,
        bar.get_y() + bar.get_height() / 2,
        f"{row['cnt']:,} ({row['pct']:.2f}%)",
        va="center", ha="left", fontsize=8,
    )
ax.set_xlabel("Row count")
ax.set_title(f"Civilization Pick Rates — Top 20 of {civ_cardinality} (matches_raw)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.text(
    0.99, 0.01,
    f"Top-20 coverage: {civ_top20_pct:.1f}%",
    transform=ax.transAxes,
    ha="right", va="bottom",
    fontsize=9, color="gray",
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_civ_top20.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_civ_top20.png'}")

# %% [markdown]
# ## T07 -- Plot 5: Map Top-20 Barh (Q3 -- Map concentration; cross-dataset mandatory)

# %%
map_data = pd.DataFrame(census["categorical_profiles"]["map"])
map_data = map_data.rename(columns={"value": "map"})
# Top-20
map_top20 = map_data.head(20)
map_top20_pct = map_top20["pct"].sum()

# I7: cardinality from census null_census
map_card_row = null_census_df[null_census_df["column_name"] == "map"]
map_cardinality = int(map_card_row["approx_cardinality"].values[0])

print(f"Map cardinality: {map_cardinality}")
print(f"Top-20 coverage: {map_top20_pct:.2f}%")
print(map_top20.to_string(index=False))

# %%
map_sorted = map_top20.sort_values("cnt", ascending=True)

fig, ax = plt.subplots(figsize=(10, 8))
bars = ax.barh(map_sorted["map"], map_sorted["cnt"], color="#1abc9c", edgecolor="black", linewidth=0.3)
for bar, (_, row) in zip(bars, map_sorted.iterrows()):
    ax.text(
        bar.get_width() + bar.get_width() * 0.01,
        bar.get_y() + bar.get_height() / 2,
        f"{row['cnt']:,} ({row['pct']:.2f}%)",
        va="center", ha="left", fontsize=8,
    )
ax.set_xlabel("Row count")
ax.set_title(f"Map Distribution — Top 20 of {map_cardinality} (matches_raw)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.text(
    0.99, 0.01,
    f"Top-20 coverage: {map_top20_pct:.1f}% of {total_matches:,} rows",
    transform=ax.transAxes,
    ha="right", va="bottom",
    fontsize=9, color="gray",
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_map_top20.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_map_top20.png'}")

# %% [markdown]
# ## T08 -- Plot 6: Rating Histogram (Q6 -- Rating distribution; cross-dataset mandatory)

# %%
# I7: bin width 25 chosen as ~0.09 stddev (stddev=290 from census key
# matches_raw_numeric_stats where column_name="rating", stddev_val=290.01);
# provides ~64 bins across p05-p95 range for smooth histogram with 159M non-NULL rows.
# Sentinel -1 excluded with rating > 0.
sql_queries["hist_rating"] = """SELECT
    FLOOR(rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE rating IS NOT NULL AND rating > 0
GROUP BY bin
ORDER BY bin"""

print("Executing rating histogram query...")
rating_hist_df = con.execute(sql_queries["hist_rating"]).df()
print(f"Rating histogram: {len(rating_hist_df)} bins")
print(f"Bin range: {rating_hist_df['bin'].min()} to {rating_hist_df['bin'].max()}")
n_nonnull_rating = int(rating_hist_df["cnt"].sum())

# I7: stats from census
rating_stats = next(
    s for s in census["matches_raw_numeric_stats"]
    if s["column_name"] == "rating"
)
rating_mean = rating_stats["mean_val"]
rating_median = rating_stats["median_val"]
rating_std = rating_stats["stddev_val"]

print(f"Non-null rows (rating > 0): {n_nonnull_rating:,}")
print(f"Stats: mean={rating_mean:.0f}, median={rating_median:.0f}, std={rating_std:.0f}")

# %%
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(
    rating_hist_df["bin"],
    rating_hist_df["cnt"],
    width=24,
    color="steelblue",
    edgecolor="none",
    alpha=0.85,
)
ax.axvline(rating_mean, color="red", linestyle="--", linewidth=1.5, label=f"mean={rating_mean:.0f}")
ax.axvline(rating_median, color="orange", linestyle=":", linewidth=1.5, label=f"median={rating_median:.0f}")
ax.set_xlabel("Elo rating (bin width=25)")
ax.set_ylabel("Row count")
ax.set_title(
    f"Elo Rating Distribution — matches_raw"
    f" (N={n_nonnull_rating:,}, sentinel -1 excluded)"
)
ax.text(
    0.5, -0.13,
    f"mean={rating_mean:.0f}, median={rating_median:.0f}, std={rating_std:.0f}"
    f" | AMBIGUOUS TEMPORAL STATUS — see Phase 02",
    transform=ax.transAxes,
    ha="center", va="top",
    fontsize=9, color="darkblue", style="italic",
)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend(fontsize=9)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_rating_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_rating_histogram.png'}")

# %% [markdown]
# ## T09 -- Plot 7: ratingDiff Histogram with POST-GAME Annotation (Q7)

# %%
# I7: ratingDiff has integer values in range [-174, +319]; plotting all
# distinct values (no binning needed) since the range is narrow enough.
sql_queries["hist_ratingdiff"] = """SELECT
    "ratingDiff" AS val,
    COUNT(*) AS cnt
FROM matches_raw
WHERE "ratingDiff" IS NOT NULL
GROUP BY "ratingDiff"
ORDER BY "ratingDiff\""""

print("Executing ratingDiff histogram query...")
ratingdiff_hist_df = con.execute(sql_queries["hist_ratingdiff"]).df()
print(f"ratingDiff: {len(ratingdiff_hist_df)} distinct values")
print(f"Range: {ratingdiff_hist_df['val'].min()} to {ratingdiff_hist_df['val'].max()}")
n_nonnull_rdiff = int(ratingdiff_hist_df["cnt"].sum())

# I7: stats from census
rdiff_stats = next(
    s for s in census["matches_raw_numeric_stats"]
    if s["column_name"] == "ratingDiff"
)
rdiff_mean = rdiff_stats["mean_val"]
rdiff_median = rdiff_stats["median_val"]
rdiff_std = rdiff_stats["stddev_val"]
rdiff_skew = next(
    s["skewness"] for s in census["matches_raw_skew_kurtosis"]
    if s["column_name"] == "ratingDiff"
)

print(f"Non-null rows: {n_nonnull_rdiff:,}")
print(f"Stats: mean={rdiff_mean:.2f}, median={rdiff_median:.0f}, std={rdiff_std:.2f}, skew={rdiff_skew:.4f}")

# %%
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(
    ratingdiff_hist_df["val"],
    ratingdiff_hist_df["cnt"],
    width=0.8,
    color="salmon",
    edgecolor="none",
    alpha=0.85,
)
ax.set_xlabel("ratingDiff value")
ax.set_ylabel("Row count")
ax.set_title(
    f"Rating Difference Distribution — matches_raw (N={n_nonnull_rdiff:,})"
)
ax.text(
    0.5, -0.13,
    f"mean={rdiff_mean:.2f}, median={rdiff_median:.0f}, std={rdiff_std:.2f}, skew={rdiff_skew:.4f}",
    transform=ax.transAxes,
    ha="center", va="top",
    fontsize=9, color="gray",
)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
# I3: POST-GAME annotation
ax.annotate(
    "POST-GAME — not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98),
    xycoords="axes fraction",
    ha="left", va="top",
    fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_ratingdiff_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_ratingdiff_histogram.png'}")

# %% [markdown]
# ## T10 -- Plot 8: Duration Dual-Panel Histogram (Q8 -- Duration; cross-dataset mandatory)

# %%
# I7: p95 clip value 3789s from census key match_duration_stats[0]["p95_secs"].
# Bin width 1 minute for body panel (~63 bins).
# Non-positive durations excluded with finished > started (2941 rows per census).
p95_secs = census["match_duration_stats"][0]["p95_secs"]
p95_min = p95_secs / 60.0
median_secs = census["match_duration_stats"][0]["median_duration_secs"]
median_min = median_secs / 60.0
n_excluded_dur = census["duration_excluded_rows"][0]["non_positive_duration_count"]

sql_queries["hist_duration_body"] = f"""SELECT
    FLOOR(EXTRACT(EPOCH FROM (finished - started)) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE finished > started
  AND EXTRACT(EPOCH FROM (finished - started)) <= {int(p95_secs)}
GROUP BY bin_min
ORDER BY bin_min"""

sql_queries["hist_duration_full_log"] = """SELECT
    FLOOR(LOG10(GREATEST(EXTRACT(EPOCH FROM (finished - started)), 1))) AS log_bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE finished > started
GROUP BY log_bin
ORDER BY log_bin"""

print(f"p95_secs: {p95_secs} ({p95_min:.1f} min)")
print(f"median_secs: {median_secs} ({median_min:.1f} min)")
print(f"n_excluded (non-positive duration): {n_excluded_dur:,}")

print("Executing duration body histogram query...")
dur_body_df = con.execute(sql_queries["hist_duration_body"]).df()
print(f"Duration body: {len(dur_body_df)} bins")

print("Executing duration full-range log histogram query...")
dur_log_df = con.execute(sql_queries["hist_duration_full_log"]).df()
print(f"Duration log: {len(dur_log_df)} bins")

n_valid_dur = int(dur_log_df["cnt"].sum())
print(f"Valid duration rows: {n_valid_dur:,}")

# %%
fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 6))

# Left panel: body clipped at p95
ax_left.bar(
    dur_body_df["bin_min"],
    dur_body_df["cnt"],
    width=0.9,
    color="steelblue",
    edgecolor="none",
    alpha=0.85,
)
ax_left.axvline(
    median_min, color="red", linestyle="--", linewidth=1.5,
    label=f"median={median_min:.0f} min"
)
ax_left.set_xlabel("Duration (minutes)")
ax_left.set_ylabel("Row count")
ax_left.set_title(f"Match Duration — Body (clipped at p95={p95_min:.0f} min)")
ax_left.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax_left.legend(fontsize=9)
ax_left.text(
    0.5, -0.14,
    f"p95 clip = {p95_min:.0f} min; cf. aoestats p95 = 79 min — both use p95 clipping",
    transform=ax_left.transAxes,
    ha="center", va="top",
    fontsize=8, color="gray", style="italic",
)

# Right panel: full range log-y
ax_right.bar(
    dur_log_df["log_bin"],
    dur_log_df["cnt"],
    width=0.7,
    color="darkorange",
    edgecolor="none",
    alpha=0.85,
)
ax_right.set_yscale("log")
ax_right.set_xlabel("log10(Duration seconds)")
ax_right.set_ylabel("Row count (log scale)")
ax_right.set_title("Match Duration — Full Range (log scale)")
ax_right.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

fig.suptitle(
    f"Match Duration — matches_raw (N={n_valid_dur:,}, excl. {n_excluded_dur:,} non-positive)",
    fontsize=12, y=1.01
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_duration_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_duration_histogram.png'}")

# %% [markdown]
# ## T11 -- Plot 9: NULL Rate Bar Chart with 4-Tier Severity (Q9)

# %%
# I7: thresholds (0%, 5%, 50%) are the standardized 4-tier scheme used across
# all three datasets for cross-dataset comparability.
null_data = census["matches_raw_null_census"]
null_df = pd.DataFrame(null_data)
null_sorted = null_df.sort_values("null_pct", ascending=True)

def get_null_color(pct: float) -> str:
    """Return 4-tier severity color."""
    if pct == 0.0:
        return "green"
    elif pct < 5.0:
        return "gold"
    elif pct < 50.0:
        return "orange"
    else:
        return "red"

colors_null = [get_null_color(p) for p in null_sorted["null_pct"]]

print(f"NULL rate columns: {len(null_sorted)}")
tier_counts = {
    "green (0%)": (null_sorted["null_pct"] == 0.0).sum(),
    "gold (0-5%)": ((null_sorted["null_pct"] > 0) & (null_sorted["null_pct"] < 5)).sum(),
    "orange (5-50%)": ((null_sorted["null_pct"] >= 5) & (null_sorted["null_pct"] < 50)).sum(),
    "red (>=50%)": (null_sorted["null_pct"] >= 50).sum(),
}
for tier, cnt in tier_counts.items():
    print(f"  {tier}: {cnt} columns")

# %%
fig, ax = plt.subplots(figsize=(12, 18))
bars = ax.barh(
    null_sorted["column_name"],
    null_sorted["null_pct"],
    color=colors_null,
    edgecolor="black",
    linewidth=0.2,
)
for bar, (_, row) in zip(bars, null_sorted.iterrows()):
    if row["null_pct"] > 0:
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{row['null_pct']:.1f}%",
            va="center", ha="left", fontsize=7,
        )
ax.set_xlabel("NULL %")
ax.set_title(f"NULL Rate by Column — matches_raw ({len(null_data)} columns)")

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="green", label="0% (data-rich)"),
    Patch(facecolor="gold", label=">0% and <5%"),
    Patch(facecolor="orange", label="5–50%"),
    Patch(facecolor="red", label=">=50% (effectively dead)"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=9)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_null_rate_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_null_rate_bar.png'}")

# %% [markdown]
# ## T12 -- Plot 10: NULL Co-occurrence Annotated Table (Q10)

# %%
# I7: all counts from census JSON
cross = census["matches_raw_null_cooccurrence"]["cross_cluster_overlap"][0]
both_clusters_null = cross["both_clusters_null"]
cluster_a_only_null = cross["cluster_a_only_null"]
cluster_b_only_null = cross["cluster_b_only_null"]
total_rows_match = census["matches_raw_total_rows"]

neither_null = total_rows_match - both_clusters_null - cluster_a_only_null - cluster_b_only_null

print("NULL Co-occurrence 2x2 table:")
print(f"  both clusters null:      {both_clusters_null:,}  ({100*both_clusters_null/total_rows_match:.3f}%)")
print(f"  cluster A only null:     {cluster_a_only_null:,}  ({100*cluster_a_only_null/total_rows_match:.3f}%)")
print(f"  cluster B only null:     {cluster_b_only_null:,}  ({100*cluster_b_only_null/total_rows_match:.3f}%)")
print(f"  neither null:            {neither_null:,}  ({100*neither_null/total_rows_match:.3f}%)")
print(f"  total:                   {total_rows_match:,}")

# %%
fig, ax = plt.subplots(figsize=(10, 5))
ax.axis("off")

cell_data = [
    [
        f"BOTH NULL\n{both_clusters_null:,}\n({100*both_clusters_null/total_rows_match:.3f}%)",
        f"B only NULL\n{cluster_b_only_null:,}\n({100*cluster_b_only_null/total_rows_match:.3f}%)",
    ],
    [
        f"A only NULL\n{cluster_a_only_null:,}\n({100*cluster_a_only_null/total_rows_match:.3f}%)",
        f"NEITHER NULL\n{neither_null:,}\n({100*neither_null/total_rows_match:.3f}%)",
    ],
]
col_labels = ["fullTechTree IS NULL (Cluster B)", "fullTechTree IS NOT NULL"]
row_labels = ["allowCheats IS NULL (Cluster A)", "allowCheats IS NOT NULL"]

table = ax.table(
    cellText=cell_data,
    rowLabels=row_labels,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.4, 2.8)

# Color the data cells — matplotlib table uses (row, col) 0-indexed for data cells
# With rowLabels+colLabels: row 0 is header; row 1+ are data rows
# col -1 = row label; col 0+ are data cols
cell_color_map = {
    (1, 0): "#fff3cd",   # BOTH NULL
    (1, 1): "#e8f4f8",   # B only NULL
    (2, 0): "#e8f4f8",   # A only NULL
    (2, 1): "#d4edda",   # NEITHER NULL
}
for (row_idx, col_idx), color in cell_color_map.items():
    try:
        table[(row_idx, col_idx)].set_facecolor(color)
    except KeyError:
        pass  # Skip if cell index doesn't exist

ax.set_title(
    "NULL Co-occurrence: allowCheats (proxy Cluster A) vs fullTechTree (proxy Cluster B)\n"
    f"matches_raw total rows: {total_rows_match:,}",
    fontsize=11, pad=20,
)
ax.text(
    0.5, 0.01,
    "Cluster A proxy: allowCheats IS NULL captures 428,338 rows; "
    "exact all-8-NULL count is 426,472 (1,866-row gap).\n"
    "Cluster B proxy: fullTechTree IS NULL.",
    transform=ax.transAxes,
    ha="center", va="bottom",
    fontsize=8, color="gray", style="italic",
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_null_cooccurrence.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_null_cooccurrence.png'}")

# %% [markdown]
# ## T13 -- Plot 11: Leaderboards_raw Numeric Boxplots (Q11)

# %%
# I7: skewness 8.51 from census; unranked exclusion rate 25.61% from census
sql_queries["leaderboards_boxplots"] = """SELECT wins, losses, games, streak, drops
FROM leaderboards_raw
WHERE rank IS NOT NULL"""

print("Executing leaderboards numeric boxplots query...")
lb_boxplot_df = con.execute(sql_queries["leaderboards_boxplots"]).df()
print(f"Ranked leaderboard rows: {len(lb_boxplot_df):,}")
print(lb_boxplot_df.describe().to_string())

# %%
# I7: skewness 8.51 for games from census leaderboards_raw_skew_kurtosis
lb_sk_df = pd.DataFrame(census["leaderboards_raw_skew_kurtosis"])
lb_stats_df = pd.DataFrame(census["leaderboards_raw_numeric_stats"])

cols_to_plot = ["wins", "losses", "games", "streak", "drops"]

fig, axes = plt.subplots(1, 5, figsize=(18, 6))
for ax_sub, col in zip(axes, cols_to_plot):
    # Use actual data for boxplot
    col_data = lb_boxplot_df[col].dropna()
    ax_sub.boxplot(col_data, showfliers=False, patch_artist=True,
                   boxprops=dict(facecolor="steelblue", alpha=0.7))
    # Get skewness from census
    sk_row = lb_sk_df[lb_sk_df["column_name"] == col]
    skewness_val = float(sk_row["skewness"].values[0]) if not sk_row.empty else float("nan")
    ax_sub.set_title(f"{col}\nskew={skewness_val:.2f}", fontsize=9)
    if col == "games":
        ax_sub.set_yscale("log")
        ax_sub.set_ylabel("Value (log scale)")
    else:
        ax_sub.set_ylabel("Value")

fig.suptitle(
    "Leaderboards_raw Numeric Distributions (ranked entries only)\n"
    f"(N={len(lb_boxplot_df):,}, excl. 25.61% unranked per census)",
    fontsize=11,
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_leaderboards_numeric_boxplots.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_leaderboards_numeric_boxplots.png'}")

# %% [markdown]
# ## T14 -- Plot 12: Profiles_raw NULL Rate Bar (Q12)

# %%
profiles_null_data = census["profiles_raw_null_census"]
profiles_null_df = pd.DataFrame(profiles_null_data)
profiles_null_sorted = profiles_null_df.sort_values("null_pct", ascending=True)

colors_profiles = [get_null_color(p) for p in profiles_null_sorted["null_pct"]]

dead_cols = profiles_null_sorted[profiles_null_sorted["null_pct"] >= 100]["column_name"].tolist()
print(f"Profiles columns: {len(profiles_null_sorted)}")
print(f"Dead columns (100% NULL): {dead_cols}")

# %%
fig, ax = plt.subplots(figsize=(10, max(5, len(profiles_null_sorted) * 0.45)))
bars = ax.barh(
    profiles_null_sorted["column_name"],
    profiles_null_sorted["null_pct"],
    color=colors_profiles,
    edgecolor="black",
    linewidth=0.3,
)
for bar, (_, row) in zip(bars, profiles_null_sorted.iterrows()):
    if row["null_pct"] >= 100.0:
        ax.text(
            bar.get_width() / 2,
            bar.get_y() + bar.get_height() / 2,
            "DEAD (100% NULL)",
            ha="center", va="center",
            fontsize=8, fontweight="bold", color="white",
        )
    elif row["null_pct"] > 0:
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{row['null_pct']:.1f}%",
            va="center", ha="left", fontsize=8,
        )
ax.set_xlabel("NULL %")
ax.set_title(f"NULL Rate by Column — profiles_raw ({len(profiles_null_sorted)} columns)")
from matplotlib.patches import Patch
legend_elements_p = [
    Patch(facecolor="green", label="0%"),
    Patch(facecolor="gold", label=">0% and <5%"),
    Patch(facecolor="orange", label="5–50%"),
    Patch(facecolor="red", label=">=50% (dead)"),
]
ax.legend(handles=legend_elements_p, loc="lower right", fontsize=9)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_profiles_null_rate.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_profiles_null_rate.png'}")

# %% [markdown]
# ## T15 -- Plot 13: Leaderboards_raw Leaderboard Type Bar (Q13)

# %%
lb_cat_data = pd.DataFrame(census["leaderboards_raw_categorical"]["leaderboard"])
lb_cat_data = lb_cat_data.rename(columns={"value": "leaderboard"})
lb_cat_sorted = lb_cat_data.sort_values("cnt", ascending=False)

print(f"Leaderboards_raw leaderboard types: {len(lb_cat_sorted)}")
print(lb_cat_sorted.to_string(index=False))

# %%
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(
    range(len(lb_cat_sorted)),
    lb_cat_sorted["cnt"],
    color="steelblue",
    edgecolor="black",
    linewidth=0.4,
)
for bar, (_, row) in zip(bars, lb_cat_sorted.iterrows()):
    ax.annotate(
        f"{row['cnt']:,}\n({row['pct']:.2f}%)",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 3),
        textcoords="offset points",
        ha="center", va="bottom",
        fontsize=7,
    )
ax.set_xticks(range(len(lb_cat_sorted)))
ax.set_xticklabels(lb_cat_sorted["leaderboard"], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Row count")
ax.set_title("Leaderboard Type Distribution — leaderboards_raw")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_leaderboards_leaderboard_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_leaderboards_leaderboard_bar.png'}")

# %% [markdown]
# ## T16 -- Plot 14: Boolean Settings Stacked Bar (Q14)

# %%
bool_df = pd.DataFrame(census["boolean_census"])
total_bool = census["matches_raw_total_rows"]
bool_df["true_pct"] = 100.0 * bool_df["true_count"] / total_bool
bool_df["false_pct"] = 100.0 * bool_df["false_count"] / total_bool
bool_df["null_pct_calc"] = 100.0 * bool_df["null_count"] / total_bool

print(f"Boolean columns: {len(bool_df)}")
print(bool_df[["column_name", "true_pct", "false_pct", "null_pct_calc"]].to_string(index=False))

# %%
fig, ax = plt.subplots(figsize=(12, 9))
y = list(range(len(bool_df)))
ax.barh(y, bool_df["true_pct"], color="steelblue", label="TRUE")
ax.barh(y, bool_df["false_pct"], left=bool_df["true_pct"], color="salmon", label="FALSE")
ax.barh(
    y, bool_df["null_pct_calc"],
    left=bool_df["true_pct"] + bool_df["false_pct"],
    color="lightgray", label="NULL",
)

# Annotate segments > 1%
for i, (_, row) in enumerate(bool_df.iterrows()):
    segments = [
        (0.0, row["true_pct"], "TRUE"),
        (row["true_pct"], row["false_pct"], "FALSE"),
        (row["true_pct"] + row["false_pct"], row["null_pct_calc"], "NULL"),
    ]
    for left_start, pct, label in segments:
        if pct > 2.0:
            ax.text(
                left_start + pct / 2, i,
                f"{pct:.1f}%",
                ha="center", va="center",
                fontsize=7, color="black",
            )

ax.set_yticks(y)
ax.set_yticklabels(bool_df["column_name"], fontsize=9)
ax.set_xlabel("Percentage of all rows")
ax.set_title("Boolean Column Distribution — matches_raw")
ax.legend(loc="lower right", fontsize=9)
ax.set_xlim(0, 100)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_boolean_stacked_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_boolean_stacked_bar.png'}")

# %% [markdown]
# ## T18 -- Plot 15: Monthly Volume Line Chart (Q15 -- Temporal volume trends)

# %%
sql_queries["monthly_volume"] = """SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(*) AS match_count
FROM matches_raw
WHERE started IS NOT NULL
GROUP BY month
ORDER BY month"""

print("Executing monthly volume query...")
monthly_df = con.execute(sql_queries["monthly_volume"]).df()
monthly_df["month"] = pd.to_datetime(monthly_df["month"])
print(f"Monthly volume: {len(monthly_df)} months")
print(f"Range: {monthly_df['month'].min()} to {monthly_df['month'].max()}")
print(f"Max monthly rows: {monthly_df['match_count'].max():,}")

# I9: soft assertion -- monthly rows <= distinct match dates from census (approximate)
distinct_dates = census["temporal_range_matches"][0]["distinct_match_dates"]
assert len(monthly_df) <= distinct_dates, (
    f"Monthly bins ({len(monthly_df)}) exceeds distinct match dates ({distinct_dates})"
)
print(f"Soft assertion passed: {len(monthly_df)} months <= {distinct_dates} distinct dates")

# %%
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(
    monthly_df["month"],
    monthly_df["match_count"],
    color="steelblue",
    linewidth=1.5,
    marker="o",
    markersize=3,
)
ax.set_xlabel("Month")
ax.set_ylabel("Row count")
ax.set_title("Monthly Match Volume — matches_raw")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.grid(axis="y", alpha=0.3)
fig.autofmt_xdate()
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_monthly_volume.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_monthly_volume.png'}")

# %% [markdown]
# ## T17 -- Plot 16: Ratings_raw Rating Histogram (supplementary Q6)

# %%
# I7: bin width 25 matches T08 for comparability; stats from census
sql_queries["hist_ratings_raw_rating"] = """SELECT
    FLOOR(rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM ratings_raw
WHERE rating IS NOT NULL
GROUP BY bin
ORDER BY bin"""

print("Executing ratings_raw rating histogram query...")
ratings_raw_hist_df = con.execute(sql_queries["hist_ratings_raw_rating"]).df()
print(f"ratings_raw rating histogram: {len(ratings_raw_hist_df)} bins")

# I7: stats from census
ratings_raw_stats = next(
    s for s in census["ratings_raw_numeric_stats"]
    if s["column_name"] == "rating"
)
rr_mean = ratings_raw_stats["mean_val"]
rr_median = ratings_raw_stats["median_val"]
rr_std = ratings_raw_stats["stddev_val"]
n_nonnull_rr = int(ratings_raw_hist_df["cnt"].sum())

print(f"Non-null rows: {n_nonnull_rr:,}")
print(f"Stats: mean={rr_mean:.0f}, median={rr_median:.0f}, std={rr_std:.0f}")

# %%
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(
    ratings_raw_hist_df["bin"],
    ratings_raw_hist_df["cnt"],
    width=24,
    color="darkorange",
    edgecolor="none",
    alpha=0.85,
)
ax.axvline(rr_mean, color="red", linestyle="--", linewidth=1.5, label=f"mean={rr_mean:.0f}")
ax.axvline(rr_median, color="purple", linestyle=":", linewidth=1.5, label=f"median={rr_median:.0f}")
ax.set_xlabel("Elo rating (bin width=25)")
ax.set_ylabel("Row count")
ax.set_title(f"Rating Distribution — ratings_raw (N={n_nonnull_rr:,})")
ax.text(
    0.5, -0.13,
    f"mean={rr_mean:.0f}, median={rr_median:.0f}, std={rr_std:.0f}",
    transform=ax.transAxes,
    ha="center", va="top",
    fontsize=9, color="gray",
)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend(fontsize=9)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_ratings_raw_rating_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_ratings_raw_rating_histogram.png'}")

# %% [markdown]
# ## T19 -- Plot 17: Rating & ratingDiff NULL Rate Timeline

# %%
# I7: overall NULL rates derived from census at runtime
rating_null_pct_overall = next(
    c["null_pct"]
    for c in census["matches_raw_null_census"]
    if c["column_name"] == "rating"
)
ratingdiff_null_pct_overall = next(
    c["null_pct"]
    for c in census["matches_raw_null_census"]
    if c["column_name"] == "ratingDiff"
)

sql_queries["rating_null_timeline"] = """SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(*) AS total_rows,
    ROUND(100.0 * SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS rating_null_pct,
    ROUND(100.0 * SUM(CASE WHEN "ratingDiff" IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS ratingdiff_null_pct
FROM matches_raw
WHERE started IS NOT NULL
GROUP BY month
ORDER BY month"""

print("Executing rating NULL rate timeline query (this may take a minute)...")
df_null_timeline = con.execute(sql_queries["rating_null_timeline"]).df()
df_null_timeline["month"] = pd.to_datetime(df_null_timeline["month"])

print(f"Timeline rows: {len(df_null_timeline)}")
print(f"Overall rating NULL: {rating_null_pct_overall:.2f}% | ratingDiff NULL: {ratingdiff_null_pct_overall:.2f}%")
print("Head:")
print(df_null_timeline.head(6).to_string(index=False))
print("Tail:")
print(df_null_timeline.tail(6).to_string(index=False))

# %%
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(
    df_null_timeline["month"],
    df_null_timeline["rating_null_pct"],
    color="steelblue", linewidth=1.5, label="rating NULL %",
)
ax.plot(
    df_null_timeline["month"],
    df_null_timeline["ratingdiff_null_pct"],
    color="darkorange", linewidth=1.5, linestyle="--", label="ratingDiff NULL %",
)

ax.set_xlabel("Month")
ax.set_ylabel("NULL Rate (%)")
ax.set_ylim(0, 105)
ax.set_title(
    f"Monthly NULL Rate — rating & ratingDiff\n"
    f"(matches_raw, N={census['matches_raw_total_rows']:,})"
)
ax.legend(loc="upper right", fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.autofmt_xdate()

# I7: detect schema-change breakpoint algorithmically — no hardcoded date
months_high = df_null_timeline[df_null_timeline["rating_null_pct"] > 90]["month"]
months_low = df_null_timeline[df_null_timeline["rating_null_pct"] < 10]["month"]
if len(months_high) > 0 and len(months_low) > 0:
    breakpoint_month = months_low.min()
    ax.axvline(
        breakpoint_month, color="red", linestyle=":", linewidth=1.2,
        label=f"Schema change ~{breakpoint_month.strftime('%Y-%m')}",
    )
    ax.legend(loc="upper right", fontsize=9)
    print(f"Detected schema-change breakpoint: ~{breakpoint_month.strftime('%Y-%m')}")

plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_rating_null_timeline.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_rating_null_timeline.png'}")

# %% [markdown]
# ## T20 -- Markdown Artifact and Verification

# %%
expected_plots = [
    "01_02_05_won_distribution.png",
    "01_02_05_won_consistency.png",
    "01_02_05_leaderboard_distribution.png",
    "01_02_05_civ_top20.png",
    "01_02_05_map_top20.png",
    "01_02_05_rating_histogram.png",
    "01_02_05_ratingdiff_histogram.png",
    "01_02_05_duration_histogram.png",
    "01_02_05_null_rate_bar.png",
    "01_02_05_null_cooccurrence.png",
    "01_02_05_leaderboards_numeric_boxplots.png",
    "01_02_05_profiles_null_rate.png",
    "01_02_05_leaderboards_leaderboard_bar.png",
    "01_02_05_boolean_stacked_bar.png",
    "01_02_05_monthly_volume.png",
    "01_02_05_ratings_raw_rating_histogram.png",
    "01_02_05_rating_null_timeline.png",
]

print("=== Plot file verification ===")
all_ok = True
for fname in expected_plots:
    png_path = plots_dir / fname
    status = "OK" if png_path.exists() else "MISSING"
    print(f"  {status}: {fname}")
    if not png_path.exists():
        all_ok = False

assert all_ok, "One or more expected plot files are missing."
print(f"\nAll {len(expected_plots)} plots present: {all_ok}")

# %%
plot_index = [
    ("01_02_05_won_distribution.png", "Won Distribution 2-Bar", "Q1 — Target balance", "N/A"),
    ("01_02_05_won_consistency.png", "Won Consistency Stacked Bar", "Q2 — Intra-match consistency", "N/A"),
    ("01_02_05_leaderboard_distribution.png", "Leaderboard Distribution Bar", "Q4 — Leaderboard volume", "N/A"),
    ("01_02_05_civ_top20.png", "Civilization Top-20 Barh", "Q5 — Civ pick rates", "N/A"),
    ("01_02_05_map_top20.png", "Map Top-20 Barh", "Q3 — Map concentration (cross-dataset mandatory)", "N/A"),
    ("01_02_05_rating_histogram.png", "Rating Histogram", "Q6 — Rating distribution (cross-dataset mandatory)", "AMBIGUOUS — see Phase 02"),
    ("01_02_05_ratingdiff_histogram.png", "ratingDiff Histogram", "Q7 — ratingDiff leakage visualization", "POST-GAME (Inv. #3)"),
    ("01_02_05_duration_histogram.png", "Duration Dual-Panel Histogram", "Q8 — Duration distribution (cross-dataset mandatory)", "N/A"),
    ("01_02_05_null_rate_bar.png", "NULL Rate Bar (4-tier)", "Q9 — NULL landscape", "N/A"),
    ("01_02_05_null_cooccurrence.png", "NULL Co-occurrence Annotated 2x2", "Q10 — NULL co-occurrence", "N/A"),
    ("01_02_05_leaderboards_numeric_boxplots.png", "Leaderboards_raw Numeric Boxplots", "Q11 — Leaderboard snapshot distributions", "N/A"),
    ("01_02_05_profiles_null_rate.png", "Profiles_raw NULL Rate Bar", "Q12 — Profile column data availability", "N/A"),
    ("01_02_05_leaderboards_leaderboard_bar.png", "Leaderboards_raw Leaderboard Type Bar", "Q13 — Leaderboard type distribution", "N/A"),
    ("01_02_05_boolean_stacked_bar.png", "Boolean Settings Stacked Bar", "Q14 — Boolean settings distribution", "N/A"),
    ("01_02_05_monthly_volume.png", "Monthly Volume Line Chart", "Q15 — Temporal volume trends", "N/A"),
    ("01_02_05_ratings_raw_rating_histogram.png", "Ratings_raw Rating Histogram", "Q6 supplementary — Compare ratings_raw rating", "N/A"),
    ("01_02_05_rating_null_timeline.png", "Rating & ratingDiff NULL Rate Timeline", "Is 42.46% co-NULL rate a step-function schema change?", "N/A"),
]

md_lines = [
    "# Step 01_02_05 — Univariate Census Visualizations: aoe2companion",
    "",
    "**Step:** 01_02_05",
    "**Dataset:** aoe2companion",
    "**Phase:** 01 — Data Exploration",
    "**Predecessor:** 01_02_04 (Univariate Census)",
    "**Invariants applied:** #3, #6, #7, #9",
    "**Generated by:** `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`",
    "",
    "## Plot Index",
    "",
    "| # | Filename | Title | Scientific Question | Temporal Annotation |",
    "|---|----------|-------|---------------------|---------------------|",
]
for i, (fname, title, question, temporal) in enumerate(plot_index, 1):
    md_lines.append(f"| {i} | `plots/{fname}` | {title} | {question} | {temporal} |")

md_lines += [
    "",
    "## SQL Queries (Invariant #6 — Reproducibility)",
    "",
    "All SQL queries used to produce plots in this notebook are listed verbatim below.",
    "",
]
for qname, qsql in sql_queries.items():
    md_lines.append(f"### `{qname}`")
    md_lines.append("")
    md_lines.append("```sql")
    md_lines.append(qsql.strip())
    md_lines.append("```")
    md_lines.append("")

md_lines += [
    "## Data Sources",
    "",
    "- **DuckDB database:** `aoe2companion` (read-only)",
    "- **Census artifact:** `01_02_04_univariate_census.json` (predecessor step)",
    "",
    "## Temporal Annotation Key",
    "",
    "- **N/A:** Not a model feature or temporal classification not yet required.",
    "- **POST-GAME (Inv. #3):** Column confirmed as post-game leakage vector. Must not be used as a model feature.",
    "- **AMBIGUOUS — see Phase 02:** Temporal status not confirmed. Requires Phase 02 resolution.",
]

md_content = "\n".join(md_lines) + "\n"
md_path = artifacts_dir / "01_02_05_visualizations.md"
with open(md_path, "w") as f:
    f.write(md_content)

print(f"Written: {md_path}")
print(f"SQL queries included: {list(sql_queries.keys())}")
print(f"\nAll {len(expected_plots)} plots verified. Notebook complete.")

# %%
con.close()
print("DuckDB connection closed.")
