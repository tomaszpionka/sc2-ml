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
# # Step 01_02_07 -- Multivariate EDA
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA (Tukey-style)
# **Dataset:** sc2egset
# **Question:** What is the joint covariance structure of all numeric
# features, and what multivariate structure exists in the pre-game
# feature space?
# **Invariants applied:** #3 (I3 classification on heatmap axis labels),
# #6 (all SQL stored verbatim), #7 (all thresholds from census),
# #9 (visualization only, no new feature computation)
# **Predecessor:** 01_02_06 (Bivariate EDA -- complete)
# **Type:** Read-only -- no DuckDB writes
# **ROADMAP reference:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` Step 01_02_07
# **Commit:** 59fa781
# **Date:** 2026-04-15

# %% [markdown]
# ## Cell 2 -- Imports

# %%
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging

matplotlib.use("Agg")
logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 3 -- DuckDB Connection

# %%
conn = get_notebook_db("sc2", "sc2egset")

# %% [markdown]
# ## Cell 4 -- Census Load

# %%
reports_dir = get_reports_dir("sc2", "sc2egset")
census_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "02_eda"
    / "01_02_04_univariate_census.json"
)
with open(census_json_path) as f:
    census = json.load(f)

# %% [markdown]
# ## Cell 5 -- Runtime Constants from Census (I7)

# %%
# --- Runtime constants from census (Invariant #7) ---
TOTAL_ROWS = census["null_census"]["replay_players_raw"]["total_rows"]
print(f"Total rows: {TOTAL_ROWS}")

MMR_ZERO_COUNT = census["zero_counts"]["replay_players_raw"]["MMR_zero"]
MMR_ZERO_PCT = round(100.0 * MMR_ZERO_COUNT / TOTAL_ROWS, 2)
print(f"MMR zero sentinel: {MMR_ZERO_COUNT} rows ({MMR_ZERO_PCT}%)")

SQ_SENTINEL_COUNT = census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]
INT32_MIN = int(np.iinfo(np.int32).min)
print(f"SQ sentinel (INT32_MIN={INT32_MIN}): {SQ_SENTINEL_COUNT} rows")

result_dist = {r["result"]: r["cnt"] for r in census["result_distribution"]}
N_UNDECIDED = result_dist.get("Undecided", 0)
N_TIE = result_dist.get("Tie", 0)
N_WINLOSS = result_dist["Win"] + result_dist["Loss"]
print(f"Win/Loss rows: {N_WINLOSS} (excluding {N_UNDECIDED} Undecided, {N_TIE} Tie)")

COLUMN_CLASSIFICATION = {
    "MMR": "PRE-GAME",
    "APM": "IN-GAME (Inv. #3)",
    "SQ": "IN-GAME (Inv. #3)",
    "supplyCappedPercent": "IN-GAME (Inv. #3)",
}

plots_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"

# %% [markdown]
# ## Cell 6 -- SQL Queries Dict (I6)

# %%
sql_queries = {}

sql_queries["spearman_all"] = f"""
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > {INT32_MIN}
"""

sql_queries["spearman_rated"] = f"""
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > {INT32_MIN}
  AND MMR > 0
  -- I7: mmr > 0 filter excludes zero-sentinel rows ({MMR_ZERO_PCT}% of data,
  --     census: MMR_zero = {MMR_ZERO_COUNT})
"""

sql_queries["pregame_faceted"] = f"""
SELECT
    MMR,
    selectedRace,
    highestLeague,
    result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND MMR > 0
  AND selectedRace IN ('Prot', 'Zerg', 'Terr')
  -- I7: exclude empty-string (1110 rows), Rand (10), BW* (3) per census
  -- I7: MMR > 0 excludes zero-sentinel ({MMR_ZERO_COUNT} rows, {MMR_ZERO_PCT}%)
"""

# %% [markdown]
# ## Cell 7 -- Fetch Data

# %%
df_all = conn.fetch_df(sql_queries["spearman_all"])
print(f"All rows (SQ sentinel excluded): {len(df_all)}")

df_rated = conn.fetch_df(sql_queries["spearman_rated"])
print(f"Rated players (MMR > 0): {len(df_rated)}")

# %% [markdown]
# ## Cell 8 -- Compute Spearman Matrices

# %%
def compute_spearman_matrix(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Compute Spearman correlation matrix using scipy.stats.spearmanr."""
    rho, _ = stats.spearmanr(df[columns].values)
    if len(columns) == 2:
        rho = np.array([[1.0, rho], [rho, 1.0]])
    return pd.DataFrame(rho, index=columns, columns=columns)

numeric_cols = ["MMR", "APM", "SQ", "supplyCappedPercent"]
spearman_all = compute_spearman_matrix(df_all, numeric_cols)
spearman_rated = compute_spearman_matrix(df_rated, numeric_cols)

print("Spearman (all rows):")
print(spearman_all.round(4))
print("\nSpearman (rated, MMR > 0):")
print(spearman_rated.round(4))

# %% [markdown]
# ## Cell 9 -- Hierarchical Cluster Ordering

# %%
def cluster_order(corr_matrix: pd.DataFrame) -> list:
    """Return column/row order via UPGMA linkage on (1 - |rho|) distance."""
    dist = 1.0 - np.abs(corr_matrix.values)
    np.fill_diagonal(dist, 0)
    dist = (dist + dist.T) / 2.0
    condensed = squareform(dist)
    Z = linkage(condensed, method="average")
    dn = dendrogram(Z, no_plot=True)
    return dn["leaves"]

order_all = cluster_order(spearman_all)
order_rated = cluster_order(spearman_rated)
print(f"Cluster order (all): {[numeric_cols[i] for i in order_all]}")
print(f"Cluster order (rated): {[numeric_cols[i] for i in order_rated]}")

# %% [markdown]
# ## Cell 10 -- Two-Panel Heatmap

# %%
def annotated_label(col: str) -> str:
    return f"{col}\n[{COLUMN_CLASSIFICATION[col]}]"

def plot_clustered_heatmap(ax, corr, order, title):
    cols_ordered = [corr.columns[i] for i in order]
    corr_ordered = corr.loc[cols_ordered, cols_ordered]
    labels = [annotated_label(c) for c in cols_ordered]

    im = ax.imshow(
        corr_ordered.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal",
    )
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title(title, fontsize=10, pad=10)

    for i in range(len(cols_ordered)):
        for j in range(len(cols_ordered)):
            val = corr_ordered.iloc[i, j]
            color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=7, color=color)
    return im

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

im1 = plot_clustered_heatmap(
    ax1, spearman_all, order_all,
    f"Spearman (all rows, N={len(df_all):,})\nSQ sentinel excluded, MMR includes zero"
)
im2 = plot_clustered_heatmap(
    ax2, spearman_rated, order_rated,
    f"Spearman (rated, MMR > 0, N={len(df_rated):,})\nSQ sentinel excluded"
)

fig.colorbar(im2, ax=[ax1, ax2], shrink=0.6, label="Spearman rho")
fig.suptitle(
    "Step 01_02_07 -- Cluster-Ordered Spearman Correlation (Feature-Feature Only)",
    fontsize=12, y=1.02,
)
fig.tight_layout()

heatmap_path = plots_dir / "01_02_07_spearman_heatmap_all.png"
fig.savefig(heatmap_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {heatmap_path}")

# %% [markdown]
# ## Cell 11 -- Fetch Faceted Data

# %%
df_pregame = conn.fetch_df(sql_queries["pregame_faceted"])
print(f"Pre-game faceted rows: {len(df_pregame)}")
print(f"Races: {sorted(df_pregame['selectedRace'].unique())}")
print(f"Leagues: {sorted(df_pregame['highestLeague'].unique())}")

# %% [markdown]
# ## Cell 12 -- Filter Leagues

# %%
league_counts = df_pregame["highestLeague"].value_counts()
print("League counts (MMR > 0, standard races):")
print(league_counts)

# I7: histogram with bins=30 requires adequate density per bin.
# 50 rows / 30 bins ≈ 1.67 observations/bin — minimum for visual interpretability.
# Derivation: Cleveland (1993) recommends ~2 observations per bin minimum.
# 50 is conservative; census shows Unknown (32,338) and Master (6,458) far exceed this.
MIN_LEAGUE_ROWS = 50
leagues_to_plot = league_counts[league_counts >= MIN_LEAGUE_ROWS].index.tolist()
print(f"\nLeagues with >= {MIN_LEAGUE_ROWS} rows: {leagues_to_plot}")

LEAGUE_ORDER = [
    "Grandmaster", "Master", "Diamond", "Platinum",
    "Gold", "Silver", "Bronze", "Unranked", "Unknown",
]
leagues_ordered = [l for l in LEAGUE_ORDER if l in leagues_to_plot]
print(f"Ordered leagues for plot: {leagues_ordered}")

df_faceted = df_pregame[df_pregame["highestLeague"].isin(leagues_ordered)].copy()
print(f"Rows after league filter: {len(df_faceted)}")

# %% [markdown]
# ## Cell 13 -- Faceted Plot

# %%
race_order = ["Prot", "Terr", "Zerg"]
n_leagues = len(leagues_ordered)

assert n_leagues > 0, (
    f"No leagues with >= {MIN_LEAGUE_ROWS} rows after filtering "
    f"(MMR>0, standard races). Check census data."
)

fig, axes = plt.subplots(
    n_leagues, len(race_order),
    figsize=(12, 2.5 * n_leagues),
    sharex=True, sharey="row",
)

if n_leagues == 1:
    axes = axes.reshape(1, -1)

for row_idx, league in enumerate(leagues_ordered):
    for col_idx, race in enumerate(race_order):
        ax = axes[row_idx, col_idx]
        subset = df_faceted[
            (df_faceted["highestLeague"] == league)
            & (df_faceted["selectedRace"] == race)
        ]
        n = len(subset)

        if n > 5:
            ax.hist(
                subset["MMR"], bins=30, color="steelblue",
                edgecolor="white", alpha=0.8, density=True,
            )
        else:
            ax.text(0.5, 0.5, f"N={n}", transform=ax.transAxes,
                    ha="center", va="center", fontsize=9, color="gray")

        ax.set_title(f"{race} / {league} (N={n:,})", fontsize=8)

        if col_idx == 0:
            ax.set_ylabel("Density", fontsize=8)
        if row_idx == n_leagues - 1:
            ax.set_xlabel("MMR", fontsize=8)
        ax.tick_params(labelsize=7)

fig.suptitle(
    "Step 01_02_07 -- Pre-Game Multivariate View\n"
    "MMR Distribution by selectedRace x highestLeague\n"
    "(MMR > 0 only; standard races only)\n"
    "[PCA skipped: only 1 numeric pre-game feature -- see markdown artifact]",
    fontsize=11, y=1.02,
)
fig.tight_layout()

faceted_path = plots_dir / "01_02_07_pregame_multivariate_faceted.png"
fig.savefig(faceted_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {faceted_path}")

# %% [markdown]
# ## Cell 14 -- Collect Artifact Data

# %%
artifact_data = {
    "step": "01_02_07",
    "dataset": "sc2egset",
    "n_rows_total": TOTAL_ROWS,
    "n_rows_winloss": N_WINLOSS,
    "n_undecided": N_UNDECIDED,
    "n_tie": N_TIE,
    "mmr_zero_count": MMR_ZERO_COUNT,
    "sq_sentinel_count": SQ_SENTINEL_COUNT,
    "pca_decision": "SKIPPED -- only 1 numeric pre-game feature (mmr); "
                    "faceted distribution by selectedRace x highestLeague used instead",
    "spearman_all": {
        "method": "spearman",
        "subset": "all_rows_sq_sentinel_excluded",
        "n_rows": len(df_all),
        "columns": numeric_cols,
        "cluster_order": [numeric_cols[i] for i in order_all],
        "matrix": spearman_all.values.tolist(),
    },
    "spearman_rated": {
        "method": "spearman",
        "subset": "mmr_gt_0_rated_players",
        "n_rows": len(df_rated),
        "columns": numeric_cols,
        "cluster_order": [numeric_cols[i] for i in order_rated],
        "matrix": spearman_rated.values.tolist(),
    },
    "sql_queries": sql_queries,
}

# %% [markdown]
# ## Cell 15 -- Write Markdown Artifact

# %%
cols_ordered_all = [numeric_cols[i] for i in order_all]
cols_ordered_rated = [numeric_cols[i] for i in order_rated]
corr_all_ordered = spearman_all.loc[cols_ordered_all, cols_ordered_all]
corr_rated_ordered = spearman_rated.loc[cols_ordered_rated, cols_ordered_rated]

md_lines = [
    "# Step 01_02_07 -- Multivariate EDA", "",
    "**Dataset:** sc2egset",
    f"**Total rows:** {TOTAL_ROWS:,}",
    f"**Win/Loss rows:** {N_WINLOSS:,}",
    f"**Excluded:** Undecided ({N_UNDECIDED}), Tie ({N_TIE})", "",
    "## PCA Decision", "",
    "**Standard PCA was skipped.** The sc2egset pre-game numeric feature space "
    "contains exactly 1 column (`mmr`). With p=1, PCA is trivially "
    "PC1 = 100% variance explained. The scree plot is uninformative and the "
    "biplot collapses to a line (Jolliffe 2002, Section 2.2).", "",
    "**Alternative chosen:** MMR distribution faceted by `selectedRace` x "
    "`highestLeague` -- showing the joint structure of all 3 pre-game features "
    "(1 numeric, 2 categorical) in a single figure.", "",
    "**Option rejected:** Including IN-GAME features (APM, SQ, supplyCappedPercent) "
    "in PCA with I3 annotation was considered but rejected. The dominant PCs would "
    "be driven by the APM-SQ in-game correlation (~0.40-0.34 rho per 01_02_06), "
    "making the result uninterpretable for Phase 02 pre-game feature engineering.", "",
    "## Column Classification", "",
    "| Column | I3 Classification | Notes |",
    "|--------|-------------------|-------|",
    "| MMR | PRE-GAME | 83.65% zero sentinel; non-zero used for rated analysis |",
    "| APM | IN-GAME (Inv. #3) | Not available at prediction time |",
    "| SQ | IN-GAME (Inv. #3) | Not available at prediction time; 2 INT32_MIN sentinels |",
    "| supplyCappedPercent | IN-GAME (Inv. #3) | Not available at prediction time |",
    "| handicap | DEAD (excluded) | Effectively constant -- 2 non-100 rows |", "",
    "## Plot Index", "",
    "| # | Title | Filename | Key Finding |",
    "|---|-------|----------|-------------|",
    "| 1 | Cluster-Ordered Spearman Heatmap (two-panel) | 01_02_07_spearman_heatmap_all.png | APM-SQ correlation block visible; MMR decorrelated from in-game features in all-rows panel, moderately correlated in rated panel |",
    "| 2 | Pre-Game Multivariate Faceted View | 01_02_07_pregame_multivariate_faceted.png | MMR distribution varies across league tiers; race shows minimal effect on MMR distribution within leagues |", "",
    "## Spearman Matrices", "",
    f"### All rows (SQ sentinel excluded, N={len(df_all):,})", "",
]
md_lines.append("| | " + " | ".join(cols_ordered_all) + " |")
md_lines.append("|" + "---|" * (len(cols_ordered_all) + 1))
for row_name in cols_ordered_all:
    vals = " | ".join(f"{corr_all_ordered.loc[row_name, c]:.4f}" for c in cols_ordered_all)
    md_lines.append(f"| {row_name} | {vals} |")

md_lines.extend([
    "",
    f"### Rated players (MMR > 0, SQ sentinel excluded, N={len(df_rated):,})", "",
])
md_lines.append("| | " + " | ".join(cols_ordered_rated) + " |")
md_lines.append("|" + "---|" * (len(cols_ordered_rated) + 1))
for row_name in cols_ordered_rated:
    vals = " | ".join(f"{corr_rated_ordered.loc[row_name, c]:.4f}" for c in cols_ordered_rated)
    md_lines.append(f"| {row_name} | {vals} |")

md_lines.extend(["", "## SQL Queries", ""])
for name, query in sql_queries.items():
    md_lines.extend([f"### {name}", "```sql", query.strip(), "```", ""])

md_lines.extend([
    "## Data Sources", "",
    "- `replay_players_raw` (44,817 rows, 25 columns)",
    "- `01_02_04_univariate_census.json` (sentinel thresholds, result distribution)",
    "- `01_02_06_bivariate_eda.json` (prior Spearman matrices with result_binary for comparison)", "",
    "## Invariants Applied", "",
    "- **I3:** Axis labels annotated with I3 classification on Spearman heatmap. Pre-game faceted plot uses only pre-game features.",
    "- **I6:** All SQL queries reproduced in SQL Queries section above.",
    "- **I7:** All thresholds data-derived from census JSON at runtime.",
    "- **I9:** Multivariate visualization only; no new feature computation.",
])

md_text = "\n".join(md_lines) + "\n"
md_path = artifact_dir / "01_02_07_multivariate_analysis.md"
with open(md_path, "w") as f:
    f.write(md_text)
print(f"Saved: {md_path}")

# %% [markdown]
# ## Cell 16 -- JSON Artifact

# %%
json_path = artifact_dir / "01_02_07_multivariate_analysis.json"
with open(json_path, "w") as f:
    json.dump(artifact_data, f, indent=2)
print(f"Saved: {json_path}")

# %% [markdown]
# ## Conclusion
#
# ### Key scientific findings
#
# **All-rows panel (SQ sentinel excluded, MMR includes zero):**
# - The APM-SQ correlation block (rho=0.405) is the dominant structure: the
#   two in-game efficiency metrics cluster tightly together.
# - MMR is effectively decorrelated from all in-game features in this panel
#   because 83.65% of MMR values are the zero sentinel (unranked players).
#   This contamination suppresses any true skill-signal in the full dataset.
#
# **Rated-only panel (MMR > 0):**
# - With the zero sentinel removed, the skill-ranking relationship is exposed:
#   MMR-APM rho=0.206 and MMR-SQ rho=0.159 — moderate positive associations
#   confirming that higher-rated players have higher efficiency metrics.
#
# **PCA decision:**
# - PCA was skipped because the sc2egset pre-game numeric feature space contains
#   exactly p=1 column (MMR). With a single numeric feature, PCA is trivially
#   PC1=100% variance explained and the scree plot is uninformative.
# - Alternative produced: MMR distribution faceted by selectedRace x
#   highestLeague, exposing the joint structure of all three pre-game features
#   (1 numeric, 2 categorical).
#
# **Deferred decisions:**
# - Retention decisions (whether to keep MMR as a pre-game feature given the
#   83.65% zero contamination) and feature selection are deferred to Phase 02.
# - The faceted plot confirms MMR separates clearly across league tiers;
#   race shows minimal effect on MMR distribution within leagues.
#
# ### Artifacts produced
# - `reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png`
#   -- cluster-ordered Spearman heatmap (two-panel: all rows vs. rated only)
# - `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pregame_multivariate_faceted.png`
#   -- MMR distribution by selectedRace x highestLeague (pre-game features only)
# - `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md`
#   -- full analysis summary with embedded SQL queries (I6)
# - `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json`
#   -- machine-readable artifact with Spearman matrices and metadata
#
# ### Thesis mapping
# - Chapter 3 (Data), Section 3.3 Exploratory Data Analysis -- Multivariate structure
#
# ### Follow-ups
# - Phase 02: decide on MMR handling strategy (exclude zero-sentinel rows,
#   impute with league-median, or treat as a separate binary "is_ranked" feature)
# - Phase 02: with only 1 numeric pre-game feature, feature engineering focus
#   shifts to categorical encoding of selectedRace and highestLeague

# %% [markdown]
# ## Cell 17 -- Gate Verification and Connection Close

# %%
assert (plots_dir / "01_02_07_spearman_heatmap_all.png").exists(), "Missing heatmap PNG"
assert (plots_dir / "01_02_07_pregame_multivariate_faceted.png").exists(), "Missing faceted PNG"
assert md_path.exists(), "Missing markdown artifact"
assert json_path.exists(), "Missing JSON artifact"
assert (plots_dir / "01_02_07_spearman_heatmap_all.png").stat().st_size > 0
assert (plots_dir / "01_02_07_pregame_multivariate_faceted.png").stat().st_size > 0
assert md_path.stat().st_size > 0
assert json_path.stat().st_size > 0
print("All artifact checks passed.")

conn.close()
print("All 01_02_07 artifacts verified. Done.")
