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
# # Step 01_02_05 -- Univariate EDA Visualizations
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA (Tukey-style)
# **Dataset:** sc2egset
# **Question:** What do the distributions from 01_02_04 look like visually,
# and do the visual patterns confirm or challenge the statistical summaries?
# **Invariants applied:** #3 (in-game annotations), #6 (reproducibility -- queries inlined),
# #7 (no magic numbers), #9 (step scope: visualization of 01_02_04 findings)
# **Predecessor:** 01_02_04 (univariate census -- JSON artifact required)
# **Step scope:** visualize
# **Type:** Read-only -- no DuckDB writes

# %% [markdown]
# ## T02 -- Setup: Imports, DuckDB connection, census load, paths

# %%
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.sc2.config import DB_FILE

matplotlib.use("Agg")
logger = setup_notebook_logging()
logger.info("DB_FILE: %s", DB_FILE)

# %%
conn = duckdb.connect(str(DB_FILE), read_only=True)
print(f"Connected (read-only): {DB_FILE}")

# %%
census_json_path = (
    get_reports_dir("sc2", "sc2egset")
    / "artifacts" / "01_exploration" / "02_eda"
    / "01_02_04_univariate_census.json"
)
with open(census_json_path) as f:
    census = json.load(f)
print(f"Loaded 01_02_04 artifact: {len(census)} keys")

# %%
REQUIRED_KEYS = [
    "result_distribution",
    "categorical_profiles",
    "monthly_counts",
    "mmr_zero_interpretation",
    "isInClan_distribution",
    "clanTag_top20",
]
missing = [k for k in REQUIRED_KEYS if k not in census]
assert not missing, (
    f"BLOCKER: 01_02_04 artifact incomplete. Missing keys: {missing}. "
    "Execute plan_sc2egset_01_02_04 before running this notebook."
)
print(f"Prerequisite check PASSED. All {len(REQUIRED_KEYS)} required keys present.")

# %%
artifacts_dir = (
    get_reports_dir("sc2", "sc2egset")
    / "artifacts" / "01_exploration" / "02_eda"
)
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)
sql_queries: dict = {}
print(f"Artifacts dir: {artifacts_dir}")
print(f"Plots dir: {plots_dir}")

# %% [markdown]
# ## T03 -- Plot 1: Result Distribution 2-Bar (Q1)

# %%
df_result = pd.DataFrame(census["result_distribution"])
print("=== Result distribution data for plot ===")
print(df_result.to_string(index=False))

# %%
# I7: all values from census JSON -- no hardcoded counts
n_undecided = int(df_result.loc[df_result["result"] == "Undecided", "cnt"].values[0])
n_tie = int(df_result.loc[df_result["result"] == "Tie", "cnt"].values[0])
total_n = int(df_result["cnt"].sum())
n_excluded_replays = (n_undecided + n_tie) // 2
print(f"Undecided: {n_undecided}, Tie: {n_tie}, total_n: {total_n}, excluded_replays: {n_excluded_replays}")

df_plot = df_result[df_result["result"].isin(["Win", "Loss"])].copy()
colors = {"Win": "steelblue", "Loss": "salmon"}

fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(
    df_plot["result"],
    df_plot["cnt"],
    color=[colors[r] for r in df_plot["result"]],
)
for bar, row in zip(bars, df_plot.itertuples()):
    pct = row.pct
    ax.annotate(
        f"{row.cnt:,}\n({pct:.2f}%)",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=11,
    )
ax.set_xlabel("Result")
ax.set_ylabel("Count")
ax.set_title(f"Result Distribution (N={total_n:,})")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.annotate(
    f"Excluded: Undecided ({n_undecided}), Tie ({n_tie}) — {n_excluded_replays} replays total",
    xy=(0.5, 0.02),
    xycoords="axes fraction",
    ha="center",
    va="bottom",
    fontsize=9,
    color="gray",
)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_result_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_result_bar.png'}")

# %% [markdown]
# ## T04 -- Plot 2: Categorical Distributions 3-Panel (Q2, Q12)

# %%
cat_race = pd.DataFrame(census["categorical_profiles"]["race"])
cat_league = pd.DataFrame(census["categorical_profiles"]["highestLeague"])
cat_region = pd.DataFrame(census["categorical_profiles"]["region"])
print("=== race data for plot ===")
print(cat_race.to_string(index=False))

# %%
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for ax, col, df in zip(
    axes,
    ["race", "highestLeague", "region"],
    [cat_race, cat_league, cat_region],
):
    df_sorted = df.sort_values("cnt", ascending=True)
    bars = ax.barh(df_sorted[col], df_sorted["cnt"], color="steelblue")
    for bar, cnt in zip(bars, df_sorted["cnt"]):
        ax.annotate(
            f"{cnt:,}",
            xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.set_title(col)
    ax.set_xlabel("Count")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.suptitle("Categorical Distributions (replay_players_raw)", fontsize=13)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_categorical_bars.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_categorical_bars.png'}")

# %% [markdown]
# ## T05 -- Plot 3: selectedRace Bar (Q2 supplement)

# %%
sel_race_data = pd.DataFrame(census["categorical_profiles"]["selectedRace"])
print("=== selectedRace data for plot ===")
print(sel_race_data.to_string(index=False))

# %%
sel_race_sorted = sel_race_data.sort_values("cnt", ascending=True)
colors_sel = [
    "tomato" if r == "" else "steelblue"
    for r in sel_race_sorted["selectedRace"]
]
labels_sel = [
    r if r != "" else "(empty string)"
    for r in sel_race_sorted["selectedRace"]
]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(labels_sel, sel_race_sorted["cnt"], color=colors_sel)
for bar, cnt in zip(bars, sel_race_sorted["cnt"]):
    ax.annotate(
        f"{cnt:,}",
        xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
        xytext=(4, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=9,
    )
ax.set_xlabel("Count")
ax.set_title("selectedRace Distribution (replay_players_raw)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_selectedrace_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_selectedrace_bar.png'}")

# %% [markdown]
# ## T06 -- Plot 4: MMR Split View (Q3)

# %%
sql_queries["hist_mmr"] = "SELECT MMR FROM replay_players_raw WHERE MMR IS NOT NULL"
mmr_data = conn.execute(sql_queries["hist_mmr"]).fetchdf()
print(f"=== Full MMR data ({len(mmr_data):,} rows) ===")
print(mmr_data["MMR"].describe().to_string())

# %%
# I7: zero count from census, not recomputed
mmr_zero_cnt = census["zero_counts"]["replay_players_raw"]["MMR_zero"]
total_mmr_rows = len(mmr_data)
mmr_zero_pct = 100.0 * mmr_zero_cnt / total_mmr_rows
print(f"MMR=0: {mmr_zero_cnt:,} ({mmr_zero_pct:.2f}%)")

mmr_nonzero = mmr_data[mmr_data["MMR"] > 0]
print(f"MMR > 0: {len(mmr_nonzero):,} rows")

# %%
fig, (ax_all, ax_nonzero) = plt.subplots(1, 2, figsize=(14, 5))

# I7: Sturges rule: ceil(1+log2(44817))=16 bins minimum; 50 bins gives
# finer resolution per Tukey (1977) EDA recommendation
ax_all.hist(mmr_data["MMR"], bins=50, color="steelblue", edgecolor="white")
ax_all.set_title(
    f"MMR — all rows (N={total_mmr_rows:,})\n"
    f"{mmr_zero_pct:.2f}% zero-valued (sentinel = not reported)"
)
ax_all.set_xlabel("MMR")
ax_all.set_ylabel("Count")
ax_all.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))

ax_nonzero.hist(mmr_nonzero["MMR"], bins=50, color="steelblue", edgecolor="white")
ax_nonzero.set_title(f"MMR — non-zero only (N={len(mmr_nonzero):,})")
ax_nonzero.set_xlabel("MMR")
ax_nonzero.set_ylabel("Count")
ax_nonzero.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))

plt.suptitle(f"MMR Distribution — replay_players_raw (N={total_mmr_rows:,})", fontsize=13)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_mmr_split.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_mmr_split.png'}")

# %% [markdown]
# ## T07 -- Plot 5: APM Histogram with IN-GAME Annotation (Q4)

# %%
sql_queries["hist_apm"] = "SELECT APM FROM replay_players_raw WHERE APM IS NOT NULL"
apm_data = conn.execute(sql_queries["hist_apm"]).fetchdf()
print(f"=== APM data ({len(apm_data):,} rows) ===")
print(apm_data["APM"].describe().to_string())

# %%
apm_mean = apm_data["APM"].mean()
apm_median = apm_data["APM"].median()
print(f"APM mean={apm_mean:.1f}, median={apm_median:.0f}")

fig, ax = plt.subplots(figsize=(10, 6))
# I7: Sturges rule: ceil(1+log2(44817))=16 bins minimum; 50 bins for finer shape
ax.hist(apm_data["APM"], bins=50, color="steelblue", edgecolor="white")
ax.axvline(apm_mean, color="darkorange", linestyle="--", linewidth=1.5,
           label=f"mean = {apm_mean:.0f}")
ax.axvline(apm_median, color="red", linestyle=":", linewidth=1.5,
           label=f"median = {apm_median:.0f}")
ax.set_xlabel("APM")
ax.set_ylabel("Count")
ax.set_title(
    f"APM Distribution (replay_players_raw)\n"
    f"N={len(apm_data):,}  |  mean={apm_mean:.0f}  |  median={apm_median:.0f}"
)
ax.legend(fontsize=9)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.annotate(
    "IN-GAME \u2014 not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_apm_hist.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_apm_hist.png'}")

# %% [markdown]
# ## T08 -- Plot 6: SQ Split View with IN-GAME Annotation (Q5)

# %%
sql_queries["hist_sq"] = "SELECT SQ FROM replay_players_raw WHERE SQ IS NOT NULL"
sq_data = conn.execute(sql_queries["hist_sq"]).fetchdf()
print(f"=== Full SQ data ({len(sq_data):,} rows) ===")
print(sq_data["SQ"].describe().to_string())

# %%
# I7: sentinel value from census, not hardcoded independent of artifact
sq_sentinel_count = census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]
INT32_MIN = -2147483648  # I7: standard INT32 minimum -- architecture constant
sq_clean = sq_data[sq_data["SQ"] != INT32_MIN]
print(f"SQ sentinel rows excluded: {sq_sentinel_count} (INT32_MIN={INT32_MIN:,})")
print(f"SQ clean rows: {len(sq_clean):,}")
print(sq_clean["SQ"].describe().to_string())

# %%
fig, (ax_all, ax_clean) = plt.subplots(1, 2, figsize=(14, 5))

# I7: 50 bins per Tukey (1977) EDA recommendation
ax_all.hist(sq_data["SQ"], bins=50, color="steelblue", edgecolor="white")
ax_all.set_title(f"SQ — all rows (N={len(sq_data):,})\n(INT32_MIN sentinel spike visible)")
ax_all.set_xlabel("SQ")
ax_all.set_ylabel("Count")
ax_all.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))

ax_clean.hist(sq_clean["SQ"], bins=50, color="steelblue", edgecolor="white")
ax_clean.set_title(
    f"SQ — sentinel excluded (N={len(sq_clean):,})\n"
    f"{sq_sentinel_count} INT32_MIN rows removed"
)
ax_clean.set_xlabel("SQ")
ax_clean.set_ylabel("Count")

for ax_panel in [ax_all, ax_clean]:
    ax_panel.annotate(
        "IN-GAME \u2014 not available at prediction time (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )

plt.suptitle("SQ Distribution (replay_players_raw)", fontsize=13)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_sq_split.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_sq_split.png'}")

# %% [markdown]
# ## T09 -- Plot 7: supplyCappedPercent Histogram with IN-GAME Annotation (Q6)

# %%
sql_queries["hist_supplycapped"] = (
    "SELECT supplyCappedPercent FROM replay_players_raw"
    " WHERE supplyCappedPercent IS NOT NULL"
)
sc_data = conn.execute(sql_queries["hist_supplycapped"]).fetchdf()
print(f"=== supplyCappedPercent data ({len(sc_data):,} rows) ===")
print(sc_data["supplyCappedPercent"].describe().to_string())

# %%
sc_median = sc_data["supplyCappedPercent"].median()
sc_mean = sc_data["supplyCappedPercent"].mean()
print(f"supplyCappedPercent median={sc_median:.1f}, mean={sc_mean:.2f}")

fig, ax = plt.subplots(figsize=(10, 6))
# I7: 50 bins per Tukey (1977) EDA recommendation
ax.hist(sc_data["supplyCappedPercent"], bins=50, color="steelblue", edgecolor="white")
ax.axvline(sc_median, color="darkorange", linestyle="--", linewidth=1.5,
           label=f"median = {sc_median:.1f}")
ax.axvline(sc_mean, color="red", linestyle=":", linewidth=1.5,
           label=f"mean = {sc_mean:.2f}")
ax.set_xlabel("supplyCappedPercent")
ax.set_ylabel("Count")
ax.set_title(
    f"supplyCappedPercent Distribution (replay_players_raw)\n"
    f"N={len(sc_data):,}  |  median={sc_median:.1f}  |  mean={sc_mean:.2f}"
)
ax.legend(fontsize=9)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.annotate(
    "IN-GAME \u2014 not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_supplycapped_hist.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_supplycapped_hist.png'}")

# %% [markdown]
# ## T10 -- Plot 8: Duration Dual-Panel with POST-GAME Annotation (Q7)

# %%
sql_queries["hist_duration"] = (
    "SELECT header.elapsedGameLoops AS elapsed_game_loops"
    " FROM replays_meta_raw"
    " WHERE header.elapsedGameLoops IS NOT NULL"
)
duration_data = conn.execute(sql_queries["hist_duration"]).fetchdf()
print(f"=== Duration data ({len(duration_data):,} replays) ===")

# I7: SC2 Faster game speed = 22.4 game loops per real second
# Source: Blizzard SC2 engine specification (Faster speed constant)
LOOPS_PER_SECOND = 22.4
duration_data["duration_min"] = (
    duration_data["elapsed_game_loops"] / LOOPS_PER_SECOND / 60
)
print(duration_data["duration_min"].describe().to_string())

# %%
# I7: CLIP_SECONDS is data-derived from census p95, not hardcoded
p95_loops = census["duration_stats"]["p95"]
CLIP_MINUTES = p95_loops / LOOPS_PER_SECOND / 60
print(f"p95 game loops = {p95_loops:.1f} => {CLIP_MINUTES:.1f} min clip threshold")

n_over_p95 = (duration_data["duration_min"] > CLIP_MINUTES).sum()
dur_body = duration_data[duration_data["duration_min"] <= CLIP_MINUTES]
print(f"Rows <= p95 clip: {len(dur_body):,}, rows > p95 clip: {n_over_p95:,}")

# %%
fig, (ax_body, ax_full) = plt.subplots(1, 2, figsize=(14, 5))

# I7: 50 bins per Tukey (1977) EDA recommendation
ax_body.hist(dur_body["duration_min"], bins=50, color="steelblue", edgecolor="white")
ax_body.set_title(f"Game Duration — Body (clipped at p95={CLIP_MINUTES:.0f} min)")
ax_body.set_xlabel("Duration (minutes)")
ax_body.set_ylabel("Count")
ax_body.annotate(
    f"p95 clip = {CLIP_MINUTES:.0f} min; cf. aoe2companion 63 min, aoestats 79 min",
    xy=(0.5, 0.97), xycoords="axes fraction",
    ha="center", va="top", fontsize=7, color="gray",
)

ax_full.hist(duration_data["duration_min"], bins=50, color="steelblue", edgecolor="white")
ax_full.set_yscale("log")
ax_full.set_title("Game Duration — Full Range (log y-scale)")
ax_full.set_xlabel("Duration (minutes)")
ax_full.set_ylabel("Count (log scale)")
ax_full.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}"))

for ax_panel in [ax_body, ax_full]:
    ax_panel.annotate(
        "POST-GAME \u2014 total duration; only known after match ends (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )

plt.suptitle(
    f"Game Duration — elapsed_game_loops / {LOOPS_PER_SECOND} / 60 (replays_meta_raw)",
    fontsize=12,
)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_duration_hist.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_duration_hist.png'}")

# %% [markdown]
# ## T11 -- Plot 9: MMR Zero-Spike Cross-Tab (Q8)

# %%
mmr_by_result = pd.DataFrame(census["mmr_zero_interpretation"]["by_result"])
mmr_by_league = pd.DataFrame(census["mmr_zero_interpretation"]["by_highestLeague"])
print("=== MMR=0 by result ===")
print(mmr_by_result.to_string(index=False))
print("=== MMR=0 by highestLeague ===")
print(mmr_by_league.to_string(index=False))

# %%
# I7: overall rate computed from census cross-tab, not hardcoded
overall_mmr_zero_pct = 100.0 * sum(
    r["mmr_zero_cnt"] for r in census["mmr_zero_interpretation"]["by_result"]
) / sum(
    r["total_cnt"] for r in census["mmr_zero_interpretation"]["by_result"]
)
print(f"Overall MMR=0 rate: {overall_mmr_zero_pct:.2f}%")

fig, (ax_result, ax_league) = plt.subplots(1, 2, figsize=(14, 5))

ax_result.bar(mmr_by_result["result"], mmr_by_result["mmr_zero_pct"], color="steelblue")
ax_result.axhline(
    overall_mmr_zero_pct, color="darkorange", linestyle="--", linewidth=1.5,
    label=f"Overall {overall_mmr_zero_pct:.1f}%",
)
ax_result.set_title("MMR=0 Rate by Result")
ax_result.set_xlabel("Result")
ax_result.set_ylabel("MMR=0 %")
ax_result.set_ylim(0, 100)
ax_result.legend(fontsize=8)

ax_league.bar(
    mmr_by_league["highestLeague"], mmr_by_league["mmr_zero_pct"], color="steelblue"
)
ax_league.axhline(
    overall_mmr_zero_pct, color="darkorange", linestyle="--", linewidth=1.5,
    label=f"Overall {overall_mmr_zero_pct:.1f}%",
)
ax_league.set_title("MMR=0 Rate by highestLeague")
ax_league.set_xlabel("highestLeague")
ax_league.set_ylabel("MMR=0 %")
ax_league.set_ylim(0, 100)
ax_league.legend(fontsize=8)
plt.setp(ax_league.get_xticklabels(), rotation=30, ha="right")

plt.suptitle("MMR Zero-Spike Cross-Tabulation (replay_players_raw)", fontsize=13)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_mmr_zero_interpretation.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_mmr_zero_interpretation.png'}")

# %% [markdown]
# ## T12 -- Plot 10: Temporal Coverage Line Chart (Q9)

# %%
monthly = pd.DataFrame(census["monthly_counts"])
print(f"=== Monthly counts ({len(monthly)} months) ===")
print(monthly.head(10).to_string(index=False))

# %%
monthly["month"] = pd.to_datetime(monthly["month"])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(monthly["month"], monthly["cnt"], marker="o", linewidth=1.5,
        markersize=4, color="steelblue")

low_months = monthly[monthly["cnt"] < 50]
for _, row in low_months.iterrows():
    ax.annotate(
        f"{int(row['cnt'])}",
        xy=(row["month"], row["cnt"]),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        fontsize=7,
        color="tomato",
    )

ax.set_xlabel("Month")
ax.set_ylabel("Replay Count")
ax.set_title("Monthly Replay Volume — sc2egset")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_temporal_coverage.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_temporal_coverage.png'}")

# %% [markdown]
# ## T13 -- Plot 11: isInClan Bar (Q10)

# %%
clan_dist = pd.DataFrame(census["isInClan_distribution"])
print("=== isInClan distribution ===")
print(clan_dist.to_string(index=False))

# %%
total_clan = int(clan_dist["cnt"].sum())

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(
    [str(v) for v in clan_dist["isInClan"]],
    clan_dist["cnt"],
    color="steelblue",
)
for bar, row in zip(bars, clan_dist.itertuples()):
    pct = 100.0 * row.cnt / total_clan
    ax.annotate(
        f"{row.cnt:,}\n({pct:.1f}%)",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
    )
ax.set_xlabel("isInClan")
ax.set_ylabel("Count")
ax.set_title(f"isInClan Distribution (replay_players_raw, N={total_clan:,})")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_isinclan_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_isinclan_bar.png'}")

# %% [markdown]
# ## T14 -- Plot 12: clanTag Top-20 Barh (Q10 supplement)

# %%
clan_top20 = pd.DataFrame(census["clanTag_top20"])
print("=== clanTag top-20 ===")
print(clan_top20.to_string(index=False))

# %%
clan_sorted = clan_top20.sort_values("cnt", ascending=True)

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(clan_sorted["clanTag"], clan_sorted["cnt"], color="steelblue")
for bar, cnt in zip(bars, clan_sorted["cnt"]):
    ax.annotate(
        f"{cnt:,}",
        xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
        xytext=(4, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=8,
    )
ax.set_xlabel("Count")
ax.set_title("Top-20 clanTag by Frequency (replay_players_raw)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_clantag_top20.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_clantag_top20.png'}")

# %% [markdown]
# ## T15 -- Plot 13: Map Top-20 Barh (Q11)

# %%
map_data = pd.DataFrame(census["categorical_profiles"]["map_name"])
# I7: total_replays from census, not hardcoded
total_replays = census["null_census"]["replays_meta_raw_filename"]["total_rows"]
# I7: cardinality from census cardinality list
map_cardinality_entry = next(
    c for c in census["cardinality"] if c["column"] == "map_name"
)
map_cardinality = int(map_cardinality_entry["cardinality"])
total_in_top20 = int(map_data["cnt"].sum())
pct_top20 = 100.0 * total_in_top20 / total_replays
print(f"Total replays: {total_replays:,}, map cardinality: {map_cardinality}")
print(f"Top-20 coverage: {total_in_top20:,} / {total_replays:,} = {pct_top20:.1f}%")

# %%
map_sorted = map_data.sort_values("cnt", ascending=True)

fig, ax = plt.subplots(figsize=(12, 10))
bars = ax.barh(map_sorted["map_name"], map_sorted["cnt"], color="steelblue")
for bar, row in zip(bars, map_sorted.itertuples()):
    pct = 100.0 * row.cnt / total_replays
    ax.annotate(
        f"{row.cnt:,} ({pct:.1f}%)",
        xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
        xytext=(4, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=8,
    )
ax.set_xlabel("Count")
ax.set_title(
    f"Map Distribution — Top 20 of {map_cardinality} (replays_meta_raw)\n"
    f"Top-20 coverage: {pct_top20:.1f}% of {total_replays:,} replays"
)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_map_top20.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_map_top20.png'}")

# %% [markdown]
# ## T16 -- Plot 14: Player Repeat Frequency (Games per toon_id)

# %%
# I7: n_unique_players and total_n derived from census at runtime
cardinality_entry = next(
    (c for c in census["cardinality"] if c["column"] == "toon_id" and "replay" in c.get("table", "")),
    next(c for c in census["cardinality"] if c["column"] == "toon_id")
)
n_unique_players = int(cardinality_entry["cardinality"])
total_n = int(census["null_census"]["replay_players_raw"]["total_rows"])
mean_games = total_n / n_unique_players
print(f"n_unique_players={n_unique_players:,}, total_n={total_n:,}, mean_games={mean_games:.1f}")

# %%
sql_queries["hist_player_repeat"] = """
SELECT games_per_player, COUNT(*) AS player_count
FROM (
    SELECT toon_id, COUNT(*) AS games_per_player
    FROM replay_players_raw
    GROUP BY toon_id
)
GROUP BY games_per_player
ORDER BY games_per_player
"""

df_repeat = conn.execute(sql_queries["hist_player_repeat"]).fetchdf()
print(f"Distinct games_per_player values: {len(df_repeat)}")
print(df_repeat.head(10).to_string(index=False))

# %%
# Compute median from distribution (cumulative sum approach)
df_repeat["cum_players"] = df_repeat["player_count"].cumsum()
median_games = int(
    df_repeat.loc[
        df_repeat["cum_players"] >= n_unique_players / 2, "games_per_player"
    ].iloc[0]
)
print(f"Median games per player: {median_games}")

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(
    df_repeat["games_per_player"],
    df_repeat["player_count"],
    color="steelblue", alpha=0.8, width=0.8,
)
ax.set_yscale("log")
ax.set_xlabel("Games per player (toon_id)")
ax.set_ylabel("Number of players (log scale)")
ax.set_title(
    f"Player Repeat Frequency — replay_players_raw\n"
    f"N_players = {n_unique_players:,}  |  N_rows = {total_n:,}  |  "
    f"mean = {mean_games:.1f} games/player"
)
ax.axvline(mean_games, color="darkorange", linestyle="--", linewidth=1.2,
           label=f"mean = {mean_games:.1f}")
ax.axvline(median_games, color="red", linestyle=":", linewidth=1.2,
           label=f"median = {median_games}")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_player_repeat_frequency.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_player_repeat_frequency.png'}")

# %% [markdown]
# ## T17 -- Markdown Artifact, Verification, Connection Close

# %%
# Verify all 14 plot files exist
expected_plots = [
    "01_02_05_result_bar.png",
    "01_02_05_categorical_bars.png",
    "01_02_05_selectedrace_bar.png",
    "01_02_05_mmr_split.png",
    "01_02_05_apm_hist.png",
    "01_02_05_sq_split.png",
    "01_02_05_supplycapped_hist.png",
    "01_02_05_duration_hist.png",
    "01_02_05_mmr_zero_interpretation.png",
    "01_02_05_temporal_coverage.png",
    "01_02_05_isinclan_bar.png",
    "01_02_05_clantag_top20.png",
    "01_02_05_map_top20.png",
    "01_02_05_player_repeat_frequency.png",
]
missing_plots = [p for p in expected_plots if not (plots_dir / p).exists()]
assert not missing_plots, f"Missing plots: {missing_plots}"
print(f"All {len(expected_plots)} plot files verified present.")

# %%
md_lines = [
    "# Step 01_02_05 -- Univariate EDA Visualizations",
    "",
    "**Dataset:** sc2egset",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_02 -- EDA (Tukey-style)",
    "**Predecessor:** 01_02_04 (univariate census)",
    "**Invariants applied:** #3 (IN-GAME annotations), #6 (SQL queries inlined), #7 (no magic numbers), #9 (step scope: visualize)",
    "",
    "## Plot Index",
    "",
    "| # | Title | Filename | Observation | Temporal Annotation |",
    "|---|-------|----------|-------------|---------------------|",
    "| 1 | Result Distribution | 01_02_05_result_bar.png | Near-perfect 50/50 Win/Loss split (22,382 vs 22,409). Undecided=24 and Tie=2 excluded (13 replays total). Confirms clean binary outcome for modeling. | N/A |",
    "| 2 | Categorical Distributions | 01_02_05_categorical_bars.png | race: Prot/Zerg/Terr ~36/35/29%. highestLeague: 72% Unknown, 14% Master, 11% Grandmaster. region: 47% Europe, 28% US. | N/A |",
    "| 3 | selectedRace Distribution | 01_02_05_selectedrace_bar.png | 1,110 empty strings (2.48%, red bar) and 10 Rand picks; anomalous entries absent from the race column. | N/A |",
    "| 4 | MMR Split View | 01_02_05_mmr_split.png | Left panel dominated by zero-spike (83.65% sentinel). Right panel (MMR>0) reveals unimodal distribution with long right tail toward Grandmaster. | N/A |",
    "| 5 | APM Histogram | 01_02_05_apm_hist.png | Near-symmetric distribution (skewness=-0.20) centered around median. Esports-grade players: median ~349 APM. | IN-GAME (Inv. #3) |",
    "| 6 | SQ Split View | 01_02_05_sq_split.png | Left panel shows INT32_MIN sentinel as isolated spike far below main mass. Right panel (sentinel excluded) shows continuous distribution in -51 to 187 range. | IN-GAME (Inv. #3) |",
    "| 7 | supplyCappedPercent Histogram | 01_02_05_supplycapped_hist.png | Right-skewed (skewness=2.25) with median near 6; 95th percentile at 16, confirming most players rarely hit supply cap. | IN-GAME (Inv. #3) |",
    "| 8 | Duration Dual-Panel | 01_02_05_duration_hist.png | Body panel clipped at p95=22.5 min shows main mass. Full-range log-y panel reveals extreme outliers. SC2 games shorter than AoE2 (cf. 63 min / 79 min). | POST-GAME (Inv. #3) |",
    "| 9 | MMR Zero Cross-Tab | 01_02_05_mmr_zero_interpretation.png | MMR=0 rate uniform across result categories (~83%) and league tiers, confirming zero is a missing-data sentinel not correlated with outcome. | N/A |",
    "| 10 | Temporal Coverage | 01_02_05_temporal_coverage.png | 2016-2024 span. Monthly volume generally increases through mid-period with visible gap in early 2016. Low-count months annotated. | N/A |",
    "| 11 | isInClan Bar | 01_02_05_isinclan_bar.png | 74% not in clan, 26% in clan. Minority feature worth retaining for feature engineering. | N/A |",
    "| 12 | clanTag Top-20 | 01_02_05_clantag_top20.png | Top esports organizations dominate clan tags; top-20 clans account for a substantial share of non-empty clan entries. | N/A |",
    "| 13 | Map Top-20 | 01_02_05_map_top20.png | 188 distinct maps. Top-20 shown as barh with count and percentage. Ladder map rotation pattern visible. | N/A |",
    "| 14 | Player Repeat Frequency | 01_02_05_player_repeat_frequency.png | 2,495 unique players across 44,817 rows (~18 games/player average). Heavily right-skewed: small pool of recurring tournament regulars. Informs Phase 03 player-aware splitting strategy. | N/A |",
    "",
    "## SQL Queries",
    "",
    "All DuckDB SQL queries used in this notebook (Invariant #6: reproducibility):",
    "",
    "**hist_mmr:**",
    "```sql",
    sql_queries["hist_mmr"],
    "```",
    "",
    "**hist_apm:**",
    "```sql",
    sql_queries["hist_apm"],
    "```",
    "",
    "**hist_sq:**",
    "```sql",
    sql_queries["hist_sq"],
    "```",
    "",
    "**hist_supplycapped:**",
    "```sql",
    sql_queries["hist_supplycapped"],
    "```",
    "",
    "**hist_duration:**",
    "```sql",
    sql_queries["hist_duration"],
    "```",
    "",
    "**hist_player_repeat:**",
    "```sql",
    sql_queries["hist_player_repeat"].strip(),
    "```",
    "",
    "## Data Sources",
    "",
    "- `replay_players_raw` (DuckDB persistent table): player-level fields",
    "- `replays_meta_raw` (DuckDB persistent table): replay-level metadata including elapsed_game_loops",
    "- `01_02_04_univariate_census.json`: pre-computed distributions for result, categorical profiles,",
    "  monthly counts, MMR zero-spike cross-tabulation, isInClan, clanTag top-20, cardinality",
]

md_content = "\n".join(md_lines) + "\n"
md_path = artifacts_dir / "01_02_05_visualizations.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"Written markdown artifact: {md_path}")

# %%
conn.close()
print("DuckDB connection closed.")
print(f"Step 01_02_05 complete. {len(expected_plots)} plots + 1 markdown artifact produced.")
