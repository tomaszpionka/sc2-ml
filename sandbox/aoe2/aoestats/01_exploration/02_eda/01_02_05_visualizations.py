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
# # Step 01_02_05 -- Univariate Visualizations: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
# **Dataset:** aoestats
# **Question:** What do the univariate distributions look like visually? Are there
# visual patterns not captured by summary statistics alone?
# **Invariants applied:** #6 (reproducibility -- SQL inlined in artifact),
# #7 (no magic numbers -- all values derived from census artifact at runtime),
# #9 (step scope: visualization only)
# **Predecessor:** 01_02_04 (Univariate Census) -- this notebook reads from its JSON artifact
# **Step scope:** visualization only -- no analytical computation beyond what is
# needed for plotting
# **Type:** Read-only -- no DuckDB writes, no new tables, no schema changes

# %% [markdown]
# ## T02 -- Setup: Imports, DB Connection, Census Load

# %%
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOESTATS_DB_FILE

# %%
logger = setup_notebook_logging()
matplotlib.use("Agg")
plt.style.use("seaborn-v0_8-whitegrid")

# %%
con = duckdb.connect(str(AOESTATS_DB_FILE), read_only=True)
print(f"Connected to DuckDB (read-only): {AOESTATS_DB_FILE}")

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
artifacts_dir.mkdir(parents=True, exist_ok=True)
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifacts dir: {artifacts_dir}")
print(f"Plots dir: {plots_dir}")

# %%
census_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")
print(f"Keys: {sorted(census.keys())}")

# %%
# Assert required census keys
required_keys = [
    "winner_distribution",
    "num_players_distribution",
    "categorical_matches",
    "categorical_players",
    "numeric_stats_matches",
    "numeric_stats_players",
    "skew_kurtosis_players",
    "players_null_census",
    "matches_null_census",
    "temporal_range",
    "outlier_counts_matches",
    "elo_sentinel_counts",
]
for k in required_keys:
    assert k in census, f"Missing required census key: {k}"
print(f"All {len(required_keys)} required keys present.")

# %%
sql_queries: dict[str, str] = {}

# %% [markdown]
# ## T03 -- Winner Distribution 2-Bar (Q1)
#
# Q1: Is the winner distribution exactly 50/50 with zero NULLs?

# %%
# Verification cell
winner_data = census["winner_distribution"]
winner_df = pd.DataFrame(winner_data)
print("Winner distribution data:")
print(winner_df.to_string(index=False))

# %%
total_n = sum(r["cnt"] for r in census["winner_distribution"])
fig, ax = plt.subplots(figsize=(8, 6))
colors = {True: "steelblue", False: "salmon"}
for _, row in winner_df.iterrows():
    bar = ax.bar(str(row["winner"]), row["cnt"], color=colors[row["winner"]], edgecolor="black", linewidth=0.5)
    ax.text(
        bar[0].get_x() + bar[0].get_width() / 2,
        bar[0].get_height() + total_n * 0.005,
        f"{row['cnt']:,}\n({row['pct']:.1f}%)",
        ha="center",
        va="bottom",
        fontsize=11,
    )
ax.set_xlabel("winner")
ax.set_ylabel("Count")
ax.set_title(f"Target Variable Distribution -- winner (N={total_n:,})")
ax.set_ylim(0, max(winner_df["cnt"]) * 1.18)
ax.text(
    0.5, 0.02,
    "Zero NULLs -- cleanest target across all three datasets",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=9,
    fontstyle="italic",
    color="darkgreen",
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_winner_distribution.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_winner_distribution.png")

# %% [markdown]
# ## T04 -- num_players Distribution (Q2)
#
# Q2: Is 1v1 (60.56%) dominant? How do odd player counts appear?

# %%
# Verification cell
npl_data = census["num_players_distribution"]
npl_df = pd.DataFrame(npl_data)
print("num_players distribution (distinct_match_count):")
print(npl_df[["num_players", "distinct_match_count", "distinct_match_pct"]].to_string(index=False))

# %%
total_matches = sum(r["distinct_match_count"] for r in npl_data)
fig, ax = plt.subplots(figsize=(10, 6))
for _, row in npl_df.iterrows():
    num = row["num_players"]
    # I7: odd player counts (1,3,5,7) highlighted red per plan spec
    color = "red" if num % 2 != 0 else "steelblue"
    bar = ax.bar(str(num), row["distinct_match_count"], color=color, edgecolor="black", linewidth=0.3)
    if row["distinct_match_count"] > 0:
        ax.text(
            bar[0].get_x() + bar[0].get_width() / 2,
            bar[0].get_height() + total_matches * 0.002,
            f"{row['distinct_match_count']:,}\n({row['distinct_match_pct']:.2f}%)",
            ha="center",
            va="bottom",
            fontsize=8,
        )
ax.set_xlabel("num_players")
ax.set_ylabel("Distinct Match Count")
ax.set_title(f"Match Size Distribution (N={total_matches:,} distinct matches)")
ax.set_ylim(0, max(npl_df["distinct_match_count"]) * 1.18)
from matplotlib.patches import Patch as MPatch
legend_elements = [
    MPatch(facecolor="steelblue", label="Even player counts (expected)"),
    MPatch(facecolor="red", label="Odd player counts (1, 3, 5, 7)"),
]
ax.legend(handles=legend_elements, loc="upper right")
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_num_players_distribution.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_num_players_distribution.png")

# %% [markdown]
# ## T05 -- Map Top-20 Barh (Q3)
#
# Q3: Does the map distribution show power-law concentration?

# %%
# Verification: map top-20
map_top20 = census["categorical_matches"]["map"]["top_values"][:20]
map_df = pd.DataFrame(map_top20)
map_cardinality = census["categorical_matches"]["map"]["cardinality"]
print(f"Map top-20 (cardinality={map_cardinality}):")
print(map_df.to_string(index=False))

# %%
top20_coverage = sum(r["pct"] for r in map_top20[:20])
map_df_sorted = map_df.sort_values("pct", ascending=True)
fig, ax = plt.subplots(figsize=(10, 9))
bars = ax.barh(map_df_sorted["map"], map_df_sorted["pct"], color="steelblue")
for bar, (_, row) in zip(bars, map_df_sorted.iterrows()):
    ax.text(
        bar.get_width() + 0.1,
        bar.get_y() + bar.get_height() / 2,
        f"{row['cnt']:,} ({row['pct']:.2f}%)",
        va="center",
        fontsize=8,
    )
ax.set_xlabel("Percentage (%)")
ax.set_title(
    f"Map Distribution -- Top 20 of {map_cardinality} (matches_raw)\n"
    f"Top-20 coverage: {top20_coverage:.1f}%"
)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_map_top20.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_map_top20.png")

# %% [markdown]
# ## T06 -- Civilization Top-20 Barh (Q4)
#
# Q4: How does civ distribution compare to aoe2companion?

# %%
# Verification: civ top-20
civ_top20 = census["categorical_players"]["civ"]["top_values"][:20]
civ_df = pd.DataFrame(civ_top20)
civ_cardinality = census["categorical_players"]["civ"]["cardinality"]
print(f"Civ top-20 (cardinality={civ_cardinality}):")
print(civ_df.to_string(index=False))

# %%
civ_df_sorted = civ_df.sort_values("pct", ascending=True)
fig, ax = plt.subplots(figsize=(10, 9))
bars = ax.barh(civ_df_sorted["civ"], civ_df_sorted["pct"], color="darkorange")
for bar, (_, row) in zip(bars, civ_df_sorted.iterrows()):
    ax.text(
        bar.get_width() + 0.05,
        bar.get_y() + bar.get_height() / 2,
        f"{row['cnt']:,} ({row['pct']:.2f}%)",
        va="center",
        fontsize=8,
    )
ax.set_xlabel("Percentage (%)")
ax.set_title(f"Civilization Pick Rates -- Top 20 of {civ_cardinality} (players_raw)")
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_civ_top20.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_civ_top20.png")

# %% [markdown]
# ## T07 -- Leaderboard Distribution (Q5)
#
# Q5: Is random_map + team_random_map = ~96% of all matches?

# %%
# Verification cell
lb_data = census["categorical_matches"]["leaderboard"]["top_values"]
lb_df = pd.DataFrame(lb_data)
print("Leaderboard distribution:")
print(lb_df.to_string(index=False))

# %%
n_matches = census["matches_null_census"]["total_rows"]
lb_df_sorted = lb_df.sort_values("pct", ascending=False)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(lb_df_sorted["leaderboard"], lb_df_sorted["pct"], color="teal", edgecolor="black", linewidth=0.3)
for bar, (_, row) in zip(bars, lb_df_sorted.iterrows()):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.4,
        f"{row['cnt']:,}\n({row['pct']:.2f}%)",
        ha="center",
        va="bottom",
        fontsize=9,
    )
ax.set_xlabel("Leaderboard")
ax.set_ylabel("Percentage (%)")
ax.set_title(f"Leaderboard Distribution (matches_raw, N={n_matches:,})")
ax.set_ylim(0, max(lb_df_sorted["pct"]) * 1.2)
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_leaderboard_distribution.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_leaderboard_distribution.png")

# %% [markdown]
# ## T08 -- Duration Dual-Panel Histogram (Q6)
#
# Q6: How extreme is the right tail? Does the body show unimodal right-skew?
#
# I7: p95=4714.1s from census["numeric_stats_matches"] where label="duration_sec".
# duration column is BIGINT nanoseconds -- divide by 1e9 for seconds, then /60 for minutes.

# %%
sql_queries["hist_duration_body"] = """SELECT
    FLOOR((duration / 1e9) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE duration > 0
  AND (duration / 1e9) <= 4714.1
GROUP BY bin_min
ORDER BY bin_min"""
# I7: clip at p95=4714.1s = 78.6 min from census["numeric_stats_matches"][label="duration_sec"]["p95"]

sql_queries["hist_duration_full_log"] = """SELECT
    FLOOR(LOG10(GREATEST(duration / 1e9, 1))) AS log_bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE duration > 0
GROUP BY log_bin
ORDER BY log_bin"""

# %%
# Verification: left panel data
dur_body_df = con.execute(sql_queries["hist_duration_body"]).fetchdf()
print("Duration body bins (clipped at p95=78.6 min) -- first/last 5 rows:")
print(dur_body_df.head(5).to_string(index=False))
print("...")
print(dur_body_df.tail(5).to_string(index=False))
print(f"Total bins: {len(dur_body_df)}")

# %%
# Verification: right panel data
dur_full_df = con.execute(sql_queries["hist_duration_full_log"]).fetchdf()
print("Duration full range (log bins) -- all rows:")
print(dur_full_df.to_string(index=False))

# %%
# Derive annotation values from census [I7: all from census JSON at runtime]
dur_stats = next(s for s in census["numeric_stats_matches"] if s["label"] == "duration_sec")
median_sec = dur_stats["median_val"]    # [I7: 2619.7s]
p95_sec = dur_stats["p95"]              # [I7: 4714.1s]
median_min = median_sec / 60
p95_min = p95_sec / 60
print(f"Median: {median_min:.1f} min, P95: {p95_min:.1f} min")

fig, (ax_body, ax_full) = plt.subplots(1, 2, figsize=(16, 5))

# Left panel: body clipped at p95
ax_body.bar(dur_body_df["bin_min"], dur_body_df["cnt"], width=1.0, color="steelblue", edgecolor="none")
ax_body.axvline(median_min, color="red", linestyle="--", linewidth=1.5, label=f"Median = {median_min:.1f} min")
ax_body.set_xlabel("Duration (minutes)")
ax_body.set_ylabel("Count")
ax_body.set_title(f"Match Duration -- Body (clipped at p95={p95_min:.0f} min)")
ax_body.set_xlim(0, p95_min + 2)
ax_body.legend(fontsize=9)
ax_body.text(
    0.5, -0.16,
    f"p95 clip = {p95_min:.0f} min; cf. aoe2companion p95 = 63 min -- both use p95 clipping",
    transform=ax_body.transAxes,
    ha="center",
    va="bottom",
    fontsize=8,
    fontstyle="italic",
    color="gray",
)

# Right panel: full range, log10 bins, log-y
ax_full.bar(dur_full_df["log_bin"], dur_full_df["cnt"], width=0.9, color="steelblue", edgecolor="none")
ax_full.set_yscale("log")
ax_full.set_xlabel("log10(Duration seconds)")
ax_full.set_ylabel("Count (log scale)")
ax_full.set_title("Match Duration -- Full Range (log-log)")

# POST-GAME annotation on both panels [I3]
for ax_panel in [ax_body, ax_full]:
    ax_panel.annotate(
        "POST-GAME -- not available at prediction time (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )

fig.suptitle("Duration Distribution (matches_raw)", y=1.02)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_duration_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_duration_histogram.png")

# %% [markdown]
# ## T09 -- ELO Distributions 1x3 Panel (Q7)
#
# Q7: Do avg_elo, team_0_elo, team_1_elo show similar bell-shaped distributions?
#
# I7: bin width 25 = ~0.08 stddev (stddev=309.5 from census avg_elo).
# Sentinel -1 excluded for team_0/1_elo per census elo_sentinel_counts.
# avg_elo excludes 121 zero-valued rows for consistency with team_0/1_elo sentinel exclusion.

# %%
sql_queries["hist_elo_3panel"] = """-- avg_elo (exclude zero sentinels for consistency with team panels):
SELECT FLOOR(avg_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE avg_elo > 0
GROUP BY bin ORDER BY bin;

-- team_0_elo (exclude sentinel -1 and zero):
SELECT FLOOR(team_0_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE team_0_elo > 0
GROUP BY bin ORDER BY bin;

-- team_1_elo (exclude sentinel -1 and zero):
SELECT FLOOR(team_1_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE team_1_elo > 0
GROUP BY bin ORDER BY bin"""
# I7: avg_elo excludes 121 zero-valued rows for consistency with team_0/1_elo sentinel exclusion
# (34+39 sentinel -1 rows). Asymmetry: avg_elo has no -1 sentinels, only zeros.

# %%
avg_elo_df = con.execute(
    "SELECT FLOOR(avg_elo / 25) * 25 AS bin, COUNT(*) AS cnt FROM matches_raw WHERE avg_elo > 0 GROUP BY bin ORDER BY bin"
).fetchdf()
team0_elo_df = con.execute(
    "SELECT FLOOR(team_0_elo / 25) * 25 AS bin, COUNT(*) AS cnt FROM matches_raw WHERE team_0_elo > 0 GROUP BY bin ORDER BY bin"
).fetchdf()
team1_elo_df = con.execute(
    "SELECT FLOOR(team_1_elo / 25) * 25 AS bin, COUNT(*) AS cnt FROM matches_raw WHERE team_1_elo > 0 GROUP BY bin ORDER BY bin"
).fetchdf()

print(f"avg_elo bins: {len(avg_elo_df)}, team_0_elo bins: {len(team0_elo_df)}, team_1_elo bins: {len(team1_elo_df)}")
print("avg_elo first 5 bins:")
print(avg_elo_df.head(5).to_string(index=False))

# %%
# Derive annotation values from census [I7]
avg_elo_stats = next(s for s in census["numeric_stats_matches"] if s["label"] == "avg_elo")
team0_elo_stats = next(s for s in census["numeric_stats_matches"] if s["label"] == "team_0_elo")
team1_elo_stats = next(s for s in census["numeric_stats_matches"] if s["label"] == "team_1_elo")

avg_elo_median = avg_elo_stats["median_val"]
team0_elo_median = team0_elo_stats["median_val"]
team1_elo_median = team1_elo_stats["median_val"]

sentinel_0 = census["elo_sentinel_counts"]["team_0_elo_negative"]  # [I7: 34]
sentinel_1 = census["elo_sentinel_counts"]["team_1_elo_negative"]  # [I7: 39]
avg_elo_zero = int(avg_elo_stats["n_zero"])                          # [I7: 121]
n_total_matches = census["matches_null_census"]["total_rows"]

n_avg_elo = n_total_matches - avg_elo_zero
n_team0 = n_total_matches - sentinel_0 - int(team0_elo_stats["n_zero"])
n_team1 = n_total_matches - sentinel_1 - int(team1_elo_stats["n_zero"])

print(f"avg_elo: median={avg_elo_median}, excl. {avg_elo_zero} zeros, N={n_avg_elo:,}")
print(f"team_0_elo: median={team0_elo_median}, excl. {sentinel_0} sentinel, N={n_team0:,}")
print(f"team_1_elo: median={team1_elo_median}, excl. {sentinel_1} sentinel, N={n_team1:,}")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

panels = [
    ("avg_elo", avg_elo_df, avg_elo_median, n_avg_elo, avg_elo_zero, "zero", "steelblue"),
    ("team_0_elo", team0_elo_df, team0_elo_median, n_team0, sentinel_0, "sentinel", "darkorange"),
    ("team_1_elo", team1_elo_df, team1_elo_median, n_team1, sentinel_1, "sentinel", "green"),
]

for ax, (col, df, median, n_valid, n_excl, excl_type, color) in zip(axes, panels):
    ax.bar(df["bin"], df["cnt"], width=25, color=color, edgecolor="none")
    ax.axvline(median, color="red", linestyle="--", linewidth=1.5, label=f"Median = {median:.0f}")
    ax.set_xlabel(col)
    ax.set_ylabel("Count")
    ax.set_title(f"{col} Distribution\n(N={n_valid:,}, excl. {n_excl} {excl_type})")
    ax.legend(fontsize=8)

fig.suptitle("ELO Distributions (matches_raw)", y=1.02)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_elo_distributions.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_elo_distributions.png")

# %% [markdown]
# ## T10 -- old_rating Histogram (Q8)
#
# Q8: What does the authoritative pre-game rating look like?
#
# I7: bin width 25 = ~0.09 stddev (stddev=286.9). Zero excluded (5,937 rows).

# %%
sql_queries["hist_old_rating"] = """SELECT FLOOR(old_rating / 25) * 25 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE old_rating > 0
GROUP BY bin ORDER BY bin"""
# I7: bin width 25 = ~0.09 stddev (stddev=286.9 from census). Excludes 5,937 zero rows.

# %%
old_rating_df = con.execute(sql_queries["hist_old_rating"]).fetchdf()
print(f"old_rating bins: {len(old_rating_df)}")
print("old_rating first 5 bins:")
print(old_rating_df.head(5).to_string(index=False))

# %%
# Derive annotation values from census [I7]
or_stats = next(s for s in census["numeric_stats_players"] if s["label"] == "old_rating")
or_median = or_stats["median_val"]   # [I7: 1066]
or_p05 = or_stats["p05"]             # [I7: 665]
or_p95 = or_stats["p95"]             # [I7: 1580]
n_zero_or = int(or_stats["n_zero"])  # [I7: 5937]
n_valid_or = int(or_stats["n_nonnull"]) - n_zero_or
print(f"old_rating: median={or_median}, p05={or_p05}, p95={or_p95}, excl. {n_zero_or} zeros, N={n_valid_or:,}")

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(old_rating_df["bin"], old_rating_df["cnt"], width=25, color="steelblue", edgecolor="none")
ax.axvline(or_median, color="red", linestyle="--", linewidth=1.5, label=f"Median = {or_median:.0f}")
ax.axvline(or_p05, color="orange", linestyle="--", linewidth=1.5, label=f"P05 = {or_p05:.0f}")
ax.axvline(or_p95, color="purple", linestyle="--", linewidth=1.5, label=f"P95 = {or_p95:.0f}")
ax.set_xlabel("old_rating")
ax.set_ylabel("Count")
ax.set_title(f"Pre-Game Rating (old_rating) -- players_raw\n(N={n_valid_or:,}, excl. {n_zero_or} zero)")
ax.legend()
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_old_rating_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_old_rating_histogram.png")

# %% [markdown]
# ## T11 -- match_rating_diff Histogram (Q9)
#
# Q9: What is the shape of this leakage-unresolved column?
#
# I7: editorial clip at ~3.6sigma (stddev=55.23 from census key skew_kurtosis_players
# where label='match_rating_diff'); shows leptokurtic tail without [-2185,+2185] extremes.
# Not p05/p95 derived. Bin width 5 = ~0.09 stddev; produces 80 bins.

# %%
sql_queries["hist_match_rating_diff"] = """SELECT
    FLOOR(match_rating_diff / 5) * 5 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND match_rating_diff BETWEEN -200 AND 200
GROUP BY bin ORDER BY bin"""
# I7: editorial clip at ~3.6sigma (stddev=55.23); full range [-2185,+2185].

# %%
mrd_df = con.execute(sql_queries["hist_match_rating_diff"]).fetchdf()
n_clipped = int(mrd_df["cnt"].sum())
print(f"match_rating_diff bins: {len(mrd_df)}, clipped N={n_clipped:,}")
print("First/last 5 bins:")
print(mrd_df.head(5).to_string(index=False))
print("...")
print(mrd_df.tail(5).to_string(index=False))

# %%
# Derive annotation values from census [I7]
mrd_sk = next(s for s in census["skew_kurtosis_players"] if s["label"] == "match_rating_diff")
kurt = mrd_sk["kurtosis"]           # [I7: 65.6753]
mrd_stats = next(s for s in census["numeric_stats_players"] if s["label"] == "match_rating_diff")
stddev = mrd_stats["stddev_val"]    # [I7: 55.23]
print(f"stddev={stddev:.2f}, kurtosis={kurt:.2f}")

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(mrd_df["bin"], mrd_df["cnt"], width=5, color="steelblue", edgecolor="none")
ax.set_xlabel("match_rating_diff")
ax.set_ylabel("Count")
ax.set_title(f"match_rating_diff -- players_raw (N={n_clipped:,}, clipped to [-200, +200])")
ax.text(
    0.5, -0.12,
    f"stddev={stddev:.2f}, kurtosis={kurt:.2f} -- leptokurtic; full range [-2185, +2185]",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=8,
    fontstyle="italic",
    color="gray",
)
ax.set_xlim(-205, 205)

# LEAKAGE UNRESOLVED annotation [I3]
ax.annotate(
    "LEAKAGE STATUS UNRESOLVED -- do not use as feature until verified (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_match_rating_diff_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_match_rating_diff_histogram.png")

# %% [markdown]
# ## T12 -- Age Uptime 1x3 Panel (Q10)
#
# Q10: What do age uptime distributions look like for the ~14% non-NULL subset?
#
# I7: bin widths chosen to produce ~43 bins across p05-p95 range:
# feudal 10s = (962.6-535.1)/10 = 43 bins;
# castle 20s = (1752.1-889.1)/20 = 43 bins;
# imperial 30s = (2933.0-1681.1)/30 = 42 bins.

# %%
sql_queries["hist_age_uptimes"] = """-- feudal_age_uptime:
SELECT FLOOR(feudal_age_uptime / 10) * 10 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE feudal_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin;

-- castle_age_uptime:
SELECT FLOOR(castle_age_uptime / 20) * 20 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE castle_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin;

-- imperial_age_uptime:
SELECT FLOOR(imperial_age_uptime / 30) * 30 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE imperial_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin"""

# %%
feudal_df = con.execute(
    "SELECT FLOOR(feudal_age_uptime / 10) * 10 AS bin, COUNT(*) AS cnt FROM players_raw WHERE feudal_age_uptime IS NOT NULL GROUP BY bin ORDER BY bin"
).fetchdf()
castle_df = con.execute(
    "SELECT FLOOR(castle_age_uptime / 20) * 20 AS bin, COUNT(*) AS cnt FROM players_raw WHERE castle_age_uptime IS NOT NULL GROUP BY bin ORDER BY bin"
).fetchdf()
imperial_df = con.execute(
    "SELECT FLOOR(imperial_age_uptime / 30) * 30 AS bin, COUNT(*) AS cnt FROM players_raw WHERE imperial_age_uptime IS NOT NULL GROUP BY bin ORDER BY bin"
).fetchdf()

print(f"feudal bins: {len(feudal_df)}, castle bins: {len(castle_df)}, imperial bins: {len(imperial_df)}")
print("feudal first 5 bins:")
print(feudal_df.head(5).to_string(index=False))

# %%
# Derive annotation values from census [I7]
def get_player_stats(label: str) -> dict:
    return next(s for s in census["numeric_stats_players"] if s["label"] == label)

feudal_stats = get_player_stats("feudal_age_uptime")
castle_stats = get_player_stats("castle_age_uptime")
imperial_stats = get_player_stats("imperial_age_uptime")

print(f"feudal: N={feudal_stats['n_nonnull']:.0f}, median={feudal_stats['median_val']:.1f}s")
print(f"castle: N={castle_stats['n_nonnull']:.0f}, median={castle_stats['median_val']:.1f}s")
print(f"imperial: N={imperial_stats['n_nonnull']:.0f}, median={imperial_stats['median_val']:.1f}s")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

age_configs = [
    ("feudal_age_uptime", feudal_df, feudal_stats, 10, "steelblue"),
    ("castle_age_uptime", castle_df, castle_stats, 20, "darkorange"),
    ("imperial_age_uptime", imperial_df, imperial_stats, 30, "green"),
]

for ax_panel, (label, df, stats, bw, color) in zip(axes, age_configs):
    ax_panel.bar(df["bin"], df["cnt"], width=bw, color=color, edgecolor="none")
    ax_panel.axvline(stats["median_val"], color="red", linestyle="--", linewidth=1.5,
                     label=f"Median = {stats['median_val']:.0f}s")
    ax_panel.set_xlabel(f"{label} (seconds)")
    ax_panel.set_ylabel("Count")
    ax_panel.set_title(f"{label.replace('_', ' ').title()}\n(N={stats['n_nonnull']:.0f} non-NULL)")
    ax_panel.legend(fontsize=8)

    # IN-GAME annotation [I3]
    ax_panel.annotate(
        "IN-GAME -- not available at prediction time (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )

fig.suptitle("Age Uptime Distributions (players_raw, non-NULL only)", y=1.02)
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_age_uptime_histograms.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_age_uptime_histograms.png")

# %% [markdown]
# ## T13 -- Opening Non-NULL Bar Chart (Q11)
#
# Q11: Among the ~14% non-NULL subset, what are the opening frequencies?

# %%
# Verification cell
opening_dist = census["opening_nonnull_distribution"]
opening_df = pd.DataFrame(opening_dist["values"])
total_nonnull = opening_dist["total_nonnull"]
total_players = census["players_null_census"]["total_rows"]
pct_nonnull = 100.0 * total_nonnull / total_players
print(f"Opening non-NULL distribution: N={total_nonnull:,} of {total_players:,} ({pct_nonnull:.1f}%)")
print(opening_df.to_string(index=False))

# %%
opening_df_sorted = opening_df.sort_values("pct_of_nonnull", ascending=True)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(opening_df_sorted["opening"], opening_df_sorted["pct_of_nonnull"], color="mediumseagreen")
for bar, (_, row) in zip(bars, opening_df_sorted.iterrows()):
    ax.text(
        bar.get_width() + 0.2,
        bar.get_y() + bar.get_height() / 2,
        f"{row['cnt']:,} ({row['pct_of_nonnull']:.2f}%)",
        va="center",
        fontsize=9,
    )
ax.set_xlabel("% of non-NULL rows")
ax.set_title("Opening Strategy Distribution (players_raw)")
ax.text(
    0.5, -0.12,
    f"Non-NULL subset only: {total_nonnull:,} of {total_players:,} rows ({pct_nonnull:.1f}%)",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=9,
    fontstyle="italic",
    color="gray",
)
ax.set_xlim(0, max(opening_df_sorted["pct_of_nonnull"]) * 1.25)

# IN-GAME annotation [I3]
ax.annotate(
    "IN-GAME -- not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_opening_nonnull.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_opening_nonnull.png")

# %% [markdown]
# ## T14 -- IQR Outlier Summary (Q12)
#
# Q12: How many outliers exist per numeric column?

# %%
# Verification cell
outlier_matches = pd.DataFrame(census["outlier_counts_matches"])
outlier_matches["table"] = "matches_raw"
outlier_players = pd.DataFrame(census["outlier_counts_players"])
outlier_players["table"] = "players_raw"
outlier_all = pd.concat([outlier_matches, outlier_players], ignore_index=True)
outlier_all_sorted = outlier_all.sort_values("outlier_pct", ascending=True)
print("IQR outlier summary:")
print(outlier_all_sorted[["label", "table", "outlier_pct", "outlier_total"]].to_string(index=False))

# %%
colors_table = {"matches_raw": "steelblue", "players_raw": "darkorange"}
bar_colors = [colors_table[t] for t in outlier_all_sorted["table"]]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(
    outlier_all_sorted["label"],
    outlier_all_sorted["outlier_pct"],
    color=bar_colors,
)

for bar, (_, row) in zip(bars, outlier_all_sorted.iterrows()):
    ax.text(
        bar.get_width() + 0.05,
        bar.get_y() + bar.get_height() / 2,
        f"{row['outlier_total']:,} ({row['outlier_pct']:.2f}%)",
        va="center",
        fontsize=8,
    )

from matplotlib.patches import Patch as MPatch2
legend_elements = [
    MPatch2(facecolor="steelblue", label="matches_raw"),
    MPatch2(facecolor="darkorange", label="players_raw"),
]
ax.legend(handles=legend_elements, loc="lower right")
ax.set_xlabel("Outlier Percentage (IQR method, %)")
ax.set_title("IQR Outlier Rates -- matches_raw Numeric Columns")
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_iqr_outlier_summary.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_iqr_outlier_summary.png")

# %% [markdown]
# ## T15 -- NULL Rate Bar Chart with 4-Tier Severity (Q13)
#
# Q13: Which columns are fully populated vs. have the 87% NULL block?
#
# I7: 4-tier color scheme: green=0%, gold=>0%<5%, orange=5-50%, red>=50%.

# %%
# Verification cell
null_matches = pd.DataFrame(census["matches_null_census"]["columns"])
null_matches["col_label"] = "m:" + null_matches["column"]
null_players = pd.DataFrame(census["players_null_census"]["columns"])
null_players["col_label"] = "p:" + null_players["column"]
null_all = pd.concat(
    [null_matches[["col_label", "null_pct"]], null_players[["col_label", "null_pct"]]],
    ignore_index=True,
)
null_all_sorted = null_all.sort_values("null_pct", ascending=False)
print(f"NULL rate summary ({len(null_all_sorted)} columns):")
print(null_all_sorted.to_string(index=False))

# %%
def null_color(pct: float) -> str:
    if pct >= 50.0:
        return "red"
    elif pct >= 5.0:
        return "orange"
    elif pct > 0.0:
        return "gold"
    else:
        return "green"

bar_colors_null = [null_color(p) for p in null_all_sorted["null_pct"]]

fig, ax = plt.subplots(figsize=(12, 9))
ax.barh(null_all_sorted["col_label"], null_all_sorted["null_pct"], color=bar_colors_null)
ax.set_xlabel("NULL Rate (%)")
ax.set_title("NULL Rate by Column -- matches_raw + players_raw")

from matplotlib.patches import Patch as MPatch3
legend_elements = [
    MPatch3(facecolor="red", label=">= 50% NULL"),
    MPatch3(facecolor="orange", label="5-50% NULL"),
    MPatch3(facecolor="gold", label="> 0% and < 5% NULL"),
    MPatch3(facecolor="green", label="0% NULL"),
]
ax.legend(handles=legend_elements, loc="lower right")
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_null_rate_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_null_rate_bar.png")

# %% [markdown]
# ## T16 -- Schema Change Temporal Boundary (Q: Step-function boundary or uniform missingness?)
#
# Do the ~86-91%-NULL columns in players_raw (feudal_age_uptime, castle_age_uptime,
# imperial_age_uptime, opening) transition from ~100% NULL to ~0% NULL at a common
# temporal boundary (schema change), or is missingness distributed uniformly?
#
# I7: column list derived from census at runtime; >80% threshold editorial,
# documented: 80% < lowest observed rate (86.05%), includes all four co-NULL
# columns identified in players_raw_null_cooccurrence census section.
# Week parsed from filename column at chars 9-18.

# %%
# I7: column list derived from census at runtime; >80% threshold editorial,
# documented: 80% < lowest observed rate (86.05%), includes all four co-NULL
# columns identified in players_raw_null_cooccurrence census section.
NULL_THRESHOLD = 80.0
high_null_cols = [
    c["column"]
    for c in census["players_null_census"]["columns"]
    if c["null_pct"] > NULL_THRESHOLD
]
print(f"High-NULL columns (>{NULL_THRESHOLD:.0f}%): {high_null_cols}")
assert len(high_null_cols) >= 4, (
    f"Expected >=4 high-NULL columns, got {len(high_null_cols)}: {high_null_cols}"
)

# %%
# Build SQL dynamically from census-derived column list [I6]
null_rate_exprs = ",\n    ".join(
    f'ROUND(100.0 * (COUNT(*) - COUNT("{col}")) / COUNT(*), 2) AS {col}_null_pct'
    for col in high_null_cols
)
sql = f"""
SELECT
    CAST(SUBSTR(filename, 9, 10) AS DATE) AS week_start,
    COUNT(*) AS total_rows,
    {null_rate_exprs}
FROM players_raw
GROUP BY week_start
ORDER BY week_start
"""
sql_queries["weekly_null_rate_high_null_cols"] = sql
print("SQL built dynamically from census-derived high-NULL column list:")
print(sql[:400] + "...")

# %%
df_weekly_null = con.execute(sql).fetchdf()
df_weekly_null["week_start"] = pd.to_datetime(df_weekly_null["week_start"])
print(f"Weekly null rate data: {len(df_weekly_null)} weeks")
print(df_weekly_null.head(5).to_string(index=False))

# %%
fig, ax = plt.subplots(figsize=(14, 6))
for col in high_null_cols:
    ax.plot(
        df_weekly_null["week_start"],
        df_weekly_null[f"{col}_null_pct"],
        marker=".", markersize=3, linewidth=1.2, label=col,
    )

ax.set_xlabel("Week (from players_raw filename)")
ax.set_ylabel("NULL Rate (%)")
ax.set_ylim(0, 105)
ax.set_title(
    f"Weekly NULL Rate -- High-NULL Columns (>{NULL_THRESHOLD:.0f}%) in players_raw"
)
ax.legend(loc="center right", fontsize=9)
ax.grid(axis="y", alpha=0.3)

# IN-GAME annotation: all four are in-game columns per Invariant #3
ax.annotate(
    "IN-GAME -- not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_schema_change_boundary.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_schema_change_boundary.png'}")

# %% [markdown]
# ## T17 -- Monthly Match Volume Line Chart (Q14)
#
# Q14: Does match volume increase or plateau? Are temporal gaps visible?

# %%
sql_queries["monthly_match_counts"] = """SELECT
    DATE_TRUNC('month', started_timestamp) AS month,
    COUNT(*) AS match_count
FROM matches_raw
WHERE started_timestamp IS NOT NULL
GROUP BY month
ORDER BY month"""

# %%
monthly_df = con.execute(sql_queries["monthly_match_counts"]).fetchdf()
distinct_months_census = census["temporal_range"]["distinct_months"]
# Soft assertion: actual months <= census distinct_months [I9: visualization only]
assert len(monthly_df) <= distinct_months_census, (
    f"Monthly query returned {len(monthly_df)} months, exceeds census {distinct_months_census}"
)
print(f"Monthly data: {len(monthly_df)} months (census distinct_months={distinct_months_census})")
print(monthly_df.to_string())

# %%
mean_count = monthly_df["match_count"].mean()
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(
    monthly_df["month"],
    monthly_df["match_count"],
    marker="o",
    linewidth=1.5,
    markersize=4,
    color="steelblue",
)
ax.axhline(mean_count, color="red", linestyle="--", linewidth=1.5, label=f"Mean = {mean_count:,.0f}")
ax.set_xlabel("Month")
ax.set_ylabel("Match Count")
ax.set_title("Monthly Match Volume -- matches_raw")
ax.legend()
fig.autofmt_xdate()
plt.tight_layout()
fig.savefig(plots_dir / "01_02_05_monthly_match_count.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_05_monthly_match_count.png")

# %% [markdown]
# ## T18 -- Markdown Artifact and Final Verification

# %%
# Assert all 15 PNG files exist
expected_plots = [
    "01_02_05_winner_distribution.png",
    "01_02_05_num_players_distribution.png",
    "01_02_05_map_top20.png",
    "01_02_05_civ_top20.png",
    "01_02_05_leaderboard_distribution.png",
    "01_02_05_duration_histogram.png",
    "01_02_05_elo_distributions.png",
    "01_02_05_old_rating_histogram.png",
    "01_02_05_match_rating_diff_histogram.png",
    "01_02_05_age_uptime_histograms.png",
    "01_02_05_opening_nonnull.png",
    "01_02_05_iqr_outlier_summary.png",
    "01_02_05_null_rate_bar.png",
    "01_02_05_schema_change_boundary.png",
    "01_02_05_monthly_match_count.png",
]

missing_pngs = []
for fname in expected_plots:
    p = plots_dir / fname
    if not p.exists() or p.stat().st_size == 0:
        missing_pngs.append(fname)

if missing_pngs:
    raise AssertionError(f"MISSING or empty PNGs: {missing_pngs}")
print(f"All {len(expected_plots)} PNG files present and non-empty.")

# %%
# Assert all 8 SQL query groups present
required_sql_keys = [
    "hist_duration_body",
    "hist_duration_full_log",
    "hist_elo_3panel",
    "hist_old_rating",
    "hist_match_rating_diff",
    "hist_age_uptimes",
    "weekly_null_rate_high_null_cols",
    "monthly_match_counts",
]
for k in required_sql_keys:
    assert k in sql_queries, f"Missing SQL query key: {k}"
print(f"All {len(required_sql_keys)} SQL query groups present: {list(sql_queries.keys())}")

# %%
# Build markdown artifact with plot index table including Temporal Annotation column
plot_index_rows = [
    ("1",  "01_02_05_winner_distribution.png",          "Winner distribution 2-bar (players_raw)",                                "N/A"),
    ("2",  "01_02_05_num_players_distribution.png",     "Match size distribution bar (matches_raw)",                              "N/A"),
    ("3",  "01_02_05_map_top20.png",                    "Top-20 maps horizontal barh (matches_raw)",                              "N/A"),
    ("4",  "01_02_05_civ_top20.png",                    "Top-20 civilizations horizontal barh (players_raw)",                     "N/A"),
    ("5",  "01_02_05_leaderboard_distribution.png",     "Leaderboard distribution bar (matches_raw)",                             "N/A"),
    ("6",  "01_02_05_duration_histogram.png",           "Duration dual-panel: body (p95 clip) + full range (log)",                "POST-GAME (Inv. #3)"),
    ("7",  "01_02_05_elo_distributions.png",            "ELO 1x3 panel: avg_elo, team_0_elo, team_1_elo (sentinel excluded)",     "N/A"),
    ("8",  "01_02_05_old_rating_histogram.png",         "Pre-game rating (old_rating) histogram (players_raw)",                   "N/A"),
    ("9",  "01_02_05_match_rating_diff_histogram.png",  "match_rating_diff histogram clipped [-200,+200] (players_raw)",          "LEAKAGE UNRESOLVED (Inv. #3)"),
    ("10", "01_02_05_age_uptime_histograms.png",        "Age uptime 1x3 panel: feudal/castle/imperial (non-NULL only)",           "IN-GAME (Inv. #3)"),
    ("11", "01_02_05_opening_nonnull.png",              "Opening strategy bar (non-NULL only, players_raw)",                      "IN-GAME (Inv. #3)"),
    ("12", "01_02_05_iqr_outlier_summary.png",          "IQR outlier rates barh (all numeric columns)",                          "N/A"),
    ("13", "01_02_05_null_rate_bar.png",                "NULL rate barh for all columns (4-tier severity)",                       "N/A"),
    ("14", "01_02_05_schema_change_boundary.png",       "Weekly NULL rate for high-NULL columns (schema change boundary)",        "IN-GAME (Inv. #3)"),
    ("15", "01_02_05_monthly_match_count.png",          "Monthly match volume line chart (matches_raw)",                          "N/A"),
]

table_header = "| # | File | Description | Temporal Annotation |"
table_sep = "|---|------|-------------|---------------------|"
table_rows_str = "\n".join(
    f"| {n} | `{fn}` | {desc} | {ann} |"
    for n, fn, desc, ann in plot_index_rows
)

sql_blocks = "\n\n".join(
    f"### `{key}`\n\n```sql\n{sql.strip()}\n```"
    for key, sql in sql_queries.items()
)

md_content = f"""# Step 01_02_05 -- Univariate Visualizations: aoestats

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
**Dataset:** aoestats
**Invariants applied:** #6 (SQL reproducibility), #7 (no magic numbers), #9 (step scope: visualization only)
**Predecessor artifact:** `01_02_04_univariate_census.json`

## Plot Index

{table_header}
{table_sep}
{table_rows_str}

## SQL Queries (Invariant #6)

All SQL queries that produce plotted data appear verbatim below.

{sql_blocks}

## Data Sources

- `matches_raw`: {census["matches_null_census"]["total_rows"]:,} rows
- `players_raw`: {census["players_null_census"]["total_rows"]:,} rows
- Census artifact: `01_02_04_univariate_census.json`
"""

md_path = artifacts_dir / "01_02_05_visualizations.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"Written markdown artifact: {md_path}")
print(f"Markdown contains {len(sql_queries)} SQL query groups.")

# %%
con.close()
print("DuckDB connection closed.")
print(f"Step 01_02_05 complete -- 15 PNG files and markdown artifact written.")
