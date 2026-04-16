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
# # Step 01_02_07 -- Multivariate EDA: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
# **Dataset:** aoe2companion
# **Question:** How do numeric features cluster together (redundancy)?
#   What is the effective dimensionality of the pre-game feature space?
# **Invariants applied:**
#   - #3 (temporal discipline -- all columns labelled PRE/POST/AMBIGUOUS on heatmap)
#   - #6 (reproducibility -- all SQL queries written verbatim to markdown artifact)
#   - #7 (no magic numbers -- sample fractions and all thresholds from census)
#   - #9 (step scope: multivariate visualization of 01_02_04/06 findings only)
# **Predecessor:** 01_02_06 (Bivariate EDA)
# **Step scope:** Multivariate EDA. No DuckDB writes. No new tables.
# **Outputs:** 2-3 PNG plots + 01_02_07_multivariate_analysis.md
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` Step 01_02_07
# **Commit:** 59fa781
# **Date:** 2026-04-15

# %% -- Cell 2: imports
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()
matplotlib.use("Agg")

# %% -- Cell 3: DuckDB connection (read-only)
db = get_notebook_db("aoe2", "aoe2companion")
con = db.con
print(f"Connected via get_notebook_db: aoe2 / aoe2companion")

# %% -- Cell 4: census JSON load and path setup
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

census_json_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_json_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")

# %% -- Cell 5: assert required census keys
required_keys = [
    "matches_raw_total_rows",
    "matches_raw_null_census",
    "matches_raw_numeric_stats",
    "categorical_profiles",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"

# %% -- Cell 6: derive sampling fraction from census (I7)
# I7: sample fraction derived from census total_rows at runtime
total_rows = census["matches_raw_total_rows"]  # 277,099,059
TARGET_SAMPLE_ROWS = 100_000  # I7: editorial cap -- same as 01_02_06
sample_pct = min(100.0, TARGET_SAMPLE_ROWS * 100.0 / total_rows)
print(f"Total rows: {total_rows:,}")
print(f"Target sample: {TARGET_SAMPLE_ROWS:,}")
print(f"Sample percent: {sample_pct:.6f}%")
# Expected: ~0.036% for 277M rows

# %% -- Cell 7: I3 feature classification table
# I3 classification table -- authoritative for this step.
# Source: 01_02_06 bivariate EDA findings.
# ratingDiff: POST-GAME (confirmed in 01_02_06 Q1)
# rating: AMBIGUOUS (inconclusive in 01_02_06 Q2 -- deferred to Phase 02)
# duration_min: POST-GAME -- computed as EXTRACT(EPOCH FROM (finished - started))/60.
#   `finished` is classified post_game in 01_02_04 census field_classification.
#   `duration_min` inherits post-game status because it requires `finished`.
# slot, color, team: NOT-A-FEATURE (UI/positional index)

I3_CLASSIFICATION = {
    "rating": "AMBIGUOUS",
    "ratingDiff": "POST-GAME",
    "duration_min": "POST-GAME",
    "population": "PRE-GAME",
    "speedFactor": "PRE-GAME",
    "treatyLength": "PRE-GAME",
    "internalLeaderboardId": "PRE-GAME",
    "slot": "NOT-A-FEATURE",
    "color": "NOT-A-FEATURE",
    "team": "NOT-A-FEATURE",
}

# Columns to include in the Spearman heatmap
HEATMAP_COLUMNS = [
    "rating", "ratingDiff", "duration_min",
    "population", "speedFactor", "treatyLength", "internalLeaderboardId",
]
HEATMAP_LABELS = [
    f"{col} [{I3_CLASSIFICATION[col]}]" for col in HEATMAP_COLUMNS
]

# Pre-game columns for PCA -- exclude POST-GAME, AMBIGUOUS, and nominal
# integer-coded categoricals. internalLeaderboardId is explicitly excluded:
# it has 122 distinct values with arbitrary integer codes; PCA loadings on
# arbitrary ID assignments are not meaningfully interpretable (W2).
# It is retained in the Spearman heatmap where rank correlation is at least
# monotone-invariant.
PCA_CANDIDATES = [
    col for col in HEATMAP_COLUMNS
    if I3_CLASSIFICATION[col] == "PRE-GAME"
    and col != "internalLeaderboardId"
]
print(f"Heatmap columns ({len(HEATMAP_COLUMNS)}): {HEATMAP_COLUMNS}")
print(f"PCA candidates ({len(PCA_CANDIDATES)}): {PCA_CANDIDATES}")

# %% -- Cell 8: initialize sql_queries and leaderboard filter
sql_queries = {}

leaderboard_names = [
    entry["value"]
    for entry in census["categorical_profiles"]["leaderboard"]
]
assert "rm_1v1" in leaderboard_names, "rm_1v1 not in census leaderboard list"
assert "qp_rm_1v1" in leaderboard_names, "qp_rm_1v1 not in census leaderboard list"
LEADERBOARD_1V1_FILTER = "leaderboard IN ('rm_1v1', 'qp_rm_1v1')"
print(f"1v1 leaderboard filter: {LEADERBOARD_1V1_FILTER}")

# %% -- Cell 9: SQL and sample fetch (Spearman)
spearman_sql = f"""
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor,
    treatyLength,
    internalLeaderboardId
FROM (
    SELECT
        rating,
        ratingDiff,
        finished,
        started,
        population,
        speedFactor,
        treatyLength,
        internalLeaderboardId,
        leaderboard
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE rating IS NOT NULL
  AND rating > 0
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND internalLeaderboardId IS NOT NULL
  AND {LEADERBOARD_1V1_FILTER}
"""
sql_queries["spearman_sample_all"] = spearman_sql

df_spearman = con.execute(spearman_sql).fetchdf()
n_spearman = len(df_spearman)
print(f"Spearman sample rows: {n_spearman:,}")
assert n_spearman > 0, "BERNOULLI sample yielded zero rows"
assert n_spearman >= 1_000, (
    f"Spearman sample too small: {n_spearman} rows after listwise deletion. "
    f"Check NULL rates in matches_raw (rating NULL rate ~42%). "
    f"Consider increasing TARGET_SAMPLE_ROWS."
)

# %% -- Cell 10: compute Spearman matrix and cluster ordering
rho_matrix, p_matrix = spearmanr(df_spearman[HEATMAP_COLUMNS])
rho_df = pd.DataFrame(rho_matrix, index=HEATMAP_COLUMNS, columns=HEATMAP_COLUMNS)
p_df = pd.DataFrame(p_matrix, index=HEATMAP_COLUMNS, columns=HEATMAP_COLUMNS)

# Near-constant columns (e.g. speedFactor, treatyLength) can cause NaN in the
# Spearman matrix because their rank variance is effectively zero.
# Fill NaN with 0 (treat as uncorrelated) before computing the distance matrix.
nan_cells = rho_df.isna().sum().sum()
if nan_cells > 0:
    print(f"WARNING: {nan_cells} NaN cells in rho matrix -- filling with 0 (uncorrelated).")
    print("Affected columns:", [c for c in HEATMAP_COLUMNS if rho_df[c].isna().any()])
rho_arr = rho_df.fillna(0).values.copy()
# Restore diagonal to 1 (self-correlation)
np.fill_diagonal(rho_arr, 1.0)
rho_df_clean = pd.DataFrame(rho_arr, index=HEATMAP_COLUMNS, columns=HEATMAP_COLUMNS)

# Hierarchical clustering on distance = 1 - |rho|
dist_arr = 1 - np.abs(rho_arr)
np.fill_diagonal(dist_arr, 0)
# Ensure symmetry (floating point can break it marginally)
dist_matrix = (dist_arr + dist_arr.T) / 2.0
condensed_dist = squareform(dist_matrix)
Z = linkage(condensed_dist, method="average")
cluster_order = leaves_list(Z)

ordered_cols = [HEATMAP_COLUMNS[i] for i in cluster_order]
ordered_labels = [HEATMAP_LABELS[i] for i in cluster_order]
rho_ordered = rho_df_clean.loc[ordered_cols, ordered_cols]
p_df_clean = p_df.fillna(1.0)  # NaN p-values -> not significant
p_ordered = p_df_clean.loc[ordered_cols, ordered_cols]

# %% -- Cell 11: plot heatmap
fig, ax = plt.subplots(figsize=(10, 8))
cax = ax.imshow(rho_ordered.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
cbar = fig.colorbar(cax, ax=ax, shrink=0.8)
cbar.set_label("Spearman rho", fontsize=10)

for i in range(len(ordered_cols)):
    for j in range(len(ordered_cols)):
        rho_val = rho_ordered.iloc[i, j]
        p_val = p_ordered.iloc[i, j]
        stars = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
        text_color = "white" if abs(rho_val) > 0.6 else "black"
        ax.text(j, i, f"{rho_val:.2f}{stars}",
                ha="center", va="center", fontsize=7, color=text_color)

ax.set_xticks(range(len(ordered_cols)))
ax.set_yticks(range(len(ordered_cols)))
ax.set_xticklabels(ordered_labels, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(ordered_labels, fontsize=8)
ax.set_title(
    f"Spearman Correlation Matrix -- Cluster-Ordered, All Numeric\n"
    f"aoe2companion 1v1 Ranked (sampled N={n_spearman:,}, BERNOULLI {sample_pct:.4f}%)\n"
    f"* p<0.05, ** p<0.01, *** p<0.001"
)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_07_spearman_heatmap_all.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_07_spearman_heatmap_all.png'}")

# %% -- Cell 12: variance check from census (I7)
def get_numeric_stat(column_name: str) -> dict:
    """Extract numeric stats for a column from census JSON."""
    for stat in census["matches_raw_numeric_stats"]:
        if stat["column_name"] == column_name:
            return stat
    raise KeyError(f"Column {column_name} not in matches_raw_numeric_stats")

pca_viable_cols = []
pca_excluded_cols = []
for col in PCA_CANDIDATES:
    stats = get_numeric_stat(col)
    # Near-constant check: IQR == 0 means the central 50% is constant, which is
    # more conservative than p05==p95 and correctly excludes speedFactor
    # (p25==p75==1.70) and population (p25==p75==200.0).
    if stats["p25"] == stats["p75"]:
        pca_excluded_cols.append((col, f"p25==p75=={stats['p25']}"))
        print(f"  EXCLUDED (near-constant): {col} -- p25==p75=={stats['p25']}")
    else:
        pca_viable_cols.append(col)
        print(f"  VIABLE: {col} -- p25={stats['p25']}, p75={stats['p75']}, std={stats['stddev_val']}")

print(f"\nPCA viable columns ({len(pca_viable_cols)}): {pca_viable_cols}")
print(f"PCA excluded columns ({len(pca_excluded_cols)}): {pca_excluded_cols}")
PCA_DEGENERATE = len(pca_viable_cols) < 3
print(f"PCA degenerate: {PCA_DEGENERATE}")

# %% -- Cell 13: PCA (non-degenerate path)
if not PCA_DEGENERATE:
    pca_col_sql_parts = []
    for col in pca_viable_cols:
        if col == "duration_min":
            pca_col_sql_parts.append("EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min")
        else:
            pca_col_sql_parts.append(col)
    pca_col_sql = ",\n    ".join(pca_col_sql_parts)
    null_filters = " AND ".join(
        f"{col} IS NOT NULL" for col in pca_viable_cols if col != "duration_min"
    )
    if "duration_min" in pca_viable_cols:
        null_filters += " AND finished > started"

    # Build the raw column list for the subquery.
    # For duration_min the outer expression uses finished and started;
    # all other viable cols are stored directly.
    pca_raw_cols = []
    for col in pca_viable_cols:
        if col == "duration_min":
            pca_raw_cols.extend(["finished", "started"])
        else:
            pca_raw_cols.append(col)
    pca_raw_cols.extend(["won", "leaderboard"])
    pca_subq_cols = ",\n        ".join(dict.fromkeys(pca_raw_cols))
    pca_sql = f"""
SELECT
    {pca_col_sql},
    won
FROM (
    SELECT
        {pca_subq_cols}
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE won IS NOT NULL
  AND {null_filters}
  AND {LEADERBOARD_1V1_FILTER}
"""
    sql_queries["pca_sample"] = pca_sql

    df_pca = con.execute(pca_sql).fetchdf()
    n_pca = len(df_pca)
    print(f"PCA sample rows: {n_pca:,}")
    assert n_pca > 0, "PCA sample yielded zero rows"

    X = df_pca[pca_viable_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_components = len(pca_viable_cols)
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    explained = pca.explained_variance_ratio_
    cumulative = np.cumsum(explained)
    print(f"Explained variance: {explained}")
    print(f"Cumulative: {cumulative}")

# %% -- Cell 14: scree plot (non-degenerate)
if not PCA_DEGENERATE:
    fig, ax = plt.subplots(figsize=(8, 5))
    components = range(1, n_components + 1)

    ax.bar(components, explained * 100, color="steelblue", alpha=0.7, label="Individual")
    ax.plot(components, cumulative * 100, "o-", color="darkorange",
            linewidth=2, markersize=6, label="Cumulative")

    ax.set_xlabel("Principal Component")
    ax.set_ylabel("Variance Explained (%)")
    ax.set_title(
        f"PCA Scree Plot -- Pre-Game Numeric Features\n"
        f"aoe2companion 1v1 Ranked (sampled N={n_pca:,})\n"
        f"Features: {', '.join(pca_viable_cols)}"
    )
    ax.set_xticks(components)
    ax.legend(loc="center right")
    ax.set_ylim(0, 105)

    for i, v in enumerate(explained):
        ax.text(i + 1, v * 100 + 2, f"{v * 100:.1f}%", ha="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(plots_dir / "01_02_07_pca_scree.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {plots_dir / '01_02_07_pca_scree.png'}")

# %% -- Cell 15: degenerate path note
if PCA_DEGENERATE:
    print(f"PCA is degenerate: only {len(pca_viable_cols)} viable pre-game numeric features.")
    print("Scree plot skipped. See T05 for degenerate fallback scatter plot.")
    pca_degeneracy_note = (
        f"PCA is degenerate for aoe2companion: only {len(pca_viable_cols)} "
        f"pre-game numeric features survive after excluding POST-GAME "
        f"(ratingDiff, duration), AMBIGUOUS (rating), NOT-A-FEATURE "
        f"(slot, color, team), and near-constant columns "
        f"({', '.join(c for c, _ in pca_excluded_cols)}). "
        f"This confirms that aoe2companion's pre-game feature space is "
        f"effectively low-dimensional for raw numeric columns. Phase 02 "
        f"must engineer features from temporal history (win rates, Elo "
        f"trajectories, civ matchup stats) to build a useful feature set."
    )
    print(pca_degeneracy_note)

# %% -- Cell 16: non-degenerate biplot
if not PCA_DEGENERATE:
    fig, ax = plt.subplots(figsize=(10, 8))

    won_mask = df_pca["won"].values
    ax.scatter(X_pca[won_mask == False, 0], X_pca[won_mask == False, 1],
               c="salmon", alpha=0.3, s=5, label="won=False", rasterized=True)
    ax.scatter(X_pca[won_mask == True, 0], X_pca[won_mask == True, 1],
               c="steelblue", alpha=0.3, s=5, label="won=True", rasterized=True)

    loadings = pca.components_.T
    max_pc = max(np.abs(X_pca[:, :2]).max(), 1.0)
    arrow_scale = max_pc * 0.8

    for i, col in enumerate(pca_viable_cols):
        ax.arrow(0, 0,
                 loadings[i, 0] * arrow_scale,
                 loadings[i, 1] * arrow_scale,
                 head_width=arrow_scale * 0.03, head_length=arrow_scale * 0.02,
                 fc="black", ec="black", linewidth=1.5)
        ax.text(loadings[i, 0] * arrow_scale * 1.12,
                loadings[i, 1] * arrow_scale * 1.12,
                col, fontsize=9, fontweight="bold",
                ha="center", va="center")

    ax.set_xlabel(f"PC1 ({explained[0] * 100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({explained[1] * 100:.1f}% variance)")
    ax.set_title(
        f"PCA Biplot -- Pre-Game Numeric Features\n"
        f"aoe2companion 1v1 Ranked (sampled N={n_pca:,})\n"
        f"Features: {', '.join(pca_viable_cols)}"
    )
    ax.legend(loc="upper right", fontsize=9, markerscale=3)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="gray", linewidth=0.5, linestyle="--")

    fig.tight_layout()
    fig.savefig(plots_dir / "01_02_07_pca_biplot.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {plots_dir / '01_02_07_pca_biplot.png'}")

# %% -- Cell 17: degenerate fallback
if PCA_DEGENERATE:
    if len(pca_viable_cols) == 0:
        # Produce a text summary plot documenting the degeneracy finding.
        # All numeric pre-game candidates are near-constant in 1v1 ranked play.
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.axis("off")
        excluded_text = "\n".join(
            f"  - {col}: p25 == p75 == {val.split('==')[-1].strip()}"
            for col, val in pca_excluded_cols
        )
        summary = (
            "PCA Degeneracy Summary\n\n"
            "All pre-game numeric candidates excluded:\n"
            f"{excluded_text}\n\n"
            "internalLeaderboardId: excluded (nominal categorical, arbitrary integer codes)\n\n"
            "Conclusion: aoe2companion pre-game numeric feature space\n"
            "is effectively empty. Phase 02 must engineer features\n"
            "from temporal match history (Elo, win rates, civ stats)."
        )
        ax.text(0.05, 0.95, summary, transform=ax.transAxes,
                fontsize=9, verticalalignment="top", fontfamily="monospace",
                bbox={"boxstyle": "round", "facecolor": "lightyellow", "alpha": 0.8})
        ax.set_title("Degenerate PCA: No Viable Pre-Game Numeric Features\naoe2companion 1v1 Ranked")
        fig.tight_layout()
        fig.savefig(plots_dir / "01_02_07_pca_biplot.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved degenerate 0-feature summary: {plots_dir / '01_02_07_pca_biplot.png'}")
    elif len(pca_viable_cols) == 1:
        col = pca_viable_cols[0]
        scatter_sql = f"""
SELECT {col}, won
FROM (
    SELECT {col}, won, leaderboard
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE won IS NOT NULL AND {col} IS NOT NULL AND {LEADERBOARD_1V1_FILTER}
"""
        sql_queries["degenerate_scatter"] = scatter_sql
        df_deg = con.execute(scatter_sql).fetchdf()
        fig, ax = plt.subplots(figsize=(8, 5))
        for w, color, label in [(True, "steelblue", "won=True"), (False, "salmon", "won=False")]:
            subset = df_deg[df_deg["won"] == w][col]
            ax.hist(subset, bins=30, alpha=0.5, color=color, label=label)
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
        ax.set_title(
            f"Degenerate PCA Fallback: {col} by Outcome\n"
            f"(only 1 viable pre-game numeric feature)"
        )
        ax.legend()
        fig.tight_layout()
        fig.savefig(plots_dir / "01_02_07_pca_biplot.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved degenerate 1D fallback: {plots_dir / '01_02_07_pca_biplot.png'}")
    else:
        col1, col2 = pca_viable_cols[0], pca_viable_cols[1]
        scatter_sql = f"""
SELECT {col1}, {col2}, won
FROM (
    SELECT {col1}, {col2}, won, leaderboard
    FROM matches_raw
    TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)
) sub
WHERE won IS NOT NULL AND {col1} IS NOT NULL AND {col2} IS NOT NULL
  AND {LEADERBOARD_1V1_FILTER}
"""
        sql_queries["degenerate_scatter"] = scatter_sql
        df_deg = con.execute(scatter_sql).fetchdf()
        fig, ax = plt.subplots(figsize=(8, 6))
        for w, color, label in [(False, "salmon", "won=False"), (True, "steelblue", "won=True")]:
            mask = df_deg["won"] == w
            ax.scatter(df_deg.loc[mask, col1], df_deg.loc[mask, col2],
                       c=color, alpha=0.3, s=5, label=label, rasterized=True)
        ax.set_xlabel(col1)
        ax.set_ylabel(col2)
        ax.set_title(
            f"Degenerate PCA Fallback: {col1} vs {col2} by Outcome\n"
            f"(only 2 viable pre-game numeric features; PCA not meaningful)"
        )
        ax.legend(markerscale=3)
        fig.tight_layout()
        fig.savefig(plots_dir / "01_02_07_pca_biplot.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved degenerate 2D fallback: {plots_dir / '01_02_07_pca_biplot.png'}")

# %% -- Cell 18: build and write markdown artifact
classification_rows = []
for col, cls in I3_CLASSIFICATION.items():
    in_heatmap = "Yes" if col in HEATMAP_COLUMNS else "No"
    in_pca = "Yes" if col in pca_viable_cols else "No"
    excluded_reason = ""
    if col in [c for c, _ in pca_excluded_cols]:
        excluded_reason = dict(pca_excluded_cols).get(col, "")
    elif col == "internalLeaderboardId":
        excluded_reason = "nominal categorical (122 distinct IDs) -- excluded from PCA, retained in heatmap"
    elif cls == "POST-GAME":
        excluded_reason = "POST-GAME (I3)"
    elif cls == "AMBIGUOUS":
        excluded_reason = "AMBIGUOUS -- deferred to Phase 02"
    elif cls == "NOT-A-FEATURE":
        excluded_reason = "UI/positional index"
    classification_rows.append((col, cls, in_heatmap, in_pca, excluded_reason))

plot_entries = [
    ("1", "Spearman Cluster-Ordered Heatmap", "01_02_07_spearman_heatmap_all.png",
     "Feature redundancy clusters", "All -- I3-labelled axes"),
    # Delta from 01_02_06: adds internalLeaderboardId (7th column), applies
    # hierarchical cluster ordering (UPGMA on 1-|rho| distance), and annotates
    # axis labels with I3 temporal classification.
]
if not PCA_DEGENERATE:
    plot_entries.append(
        ("2", "PCA Scree Plot", "01_02_07_pca_scree.png",
         "Effective dimensionality", "PRE-GAME only")
    )
    plot_entries.append(
        ("3", "PCA Biplot (PC1 vs PC2)", "01_02_07_pca_biplot.png",
         "Feature loading directions + outcome separation", "PRE-GAME only")
    )
else:
    plot_entries.append(
        ("2", "Degenerate PCA Fallback", "01_02_07_pca_biplot.png",
         "Feature scatter (PCA degenerate)", "PRE-GAME only")
    )

md_lines = [
    "# Step 01_02_07 -- Multivariate EDA: aoe2companion",
    "",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_02 -- Exploratory Data Analysis",
    f"**Dataset:** aoe2companion",
    "**Predecessor:** 01_02_06 (Bivariate EDA)",
    "**Invariants applied:** #3, #6, #7, #9",
    "",
    "## Feature Classification Table (I3)",
    "",
    "| Column | I3 Classification | In Heatmap | In PCA | PCA Exclusion Reason |",
    "|--------|-------------------|------------|--------|---------------------|",
    *[f"| {col} | {cls} | {hm} | {pca} | {reason} |"
      for col, cls, hm, pca, reason in classification_rows],
    "",
    "## Plot Index",
    "",
    "| # | Title | Filename | Question | Feature Scope |",
    "|---|-------|----------|----------|---------------|",
    *[f"| {num} | {title} | `{fname}` | {question} | {scope} |"
      for num, title, fname, question, scope in plot_entries],
    "",
    "## SQL Queries (Invariant #6)",
    "",
]

for name, query in sql_queries.items():
    md_lines.extend([f"### {name}", "", "```sql", query.strip(), "```", ""])

if PCA_DEGENERATE:
    md_lines.extend([
        "## PCA Degeneracy Note", "",
        pca_degeneracy_note, "",
    ])
elif not PCA_DEGENERATE:
    md_lines.extend([
        "## PCA Summary", "",
        f"Components: {n_components}",
        f"Features: {', '.join(pca_viable_cols)}",
        f"Variance explained: {', '.join(f'{v:.1%}' for v in explained)}",
        f"Cumulative at PC2: {cumulative[1]:.1%}" if n_components >= 2 else "",
        "",
    ])

md_lines.extend([
    "## Interpretation Notes", "",
    "### Near-constant columns",
    "speedFactor (stddev=0.09, 4 distinct values) and treatyLength (96.56% zero) "
    "are near-constant in 1v1 ranked play. Their Spearman coefficients should be "
    "interpreted with caution.", "",
    "### Pre-game feature poverty",
    "aoe2companion matches_raw has very few genuinely numeric pre-game features. "
    "Phase 02 must engineer features from temporal match history (rolling win rates, "
    "Elo trajectories, head-to-head stats, civ matchup statistics) to build a "
    "useful prediction feature set.", "",
    "## Data Sources", "",
    f"- `matches_raw` ({total_rows:,} rows) -- DuckDB table from 01_02_02",
    f"- Census JSON: `01_02_04_univariate_census.json` ({len(census)} keys)",
    f"- Bivariate findings: `01_02_06_bivariate_eda.md` (I3 classifications)",
    f"- Sample fraction: {sample_pct:.6f}% (BERNOULLI, targeting {TARGET_SAMPLE_ROWS:,} rows)",
    "",
])

md_text = "\n".join(md_lines)
md_path = artifacts_dir / "01_02_07_multivariate_analysis.md"
with open(md_path, "w") as f:
    f.write(md_text)
print(f"Saved: {md_path}")

# %% -- Cell 19: write JSON artifact
# Mirror schema used by aoestats and sc2egset for cross-dataset consistency.
pca_decision: dict = {
    "degenerate": PCA_DEGENERATE,
    "viable_features": len(pca_viable_cols),
    "reason": (
        "All pre-game numeric features have IQR=0 (near-constant)"
        if PCA_DEGENERATE
        else "PCA viable"
    ),
}

json_artifact: dict = {
    "step": "01_02_07",
    "dataset": "aoe2companion",
    "spearman_matrix": {
        col: {
            other: round(float(rho_df_clean.loc[col, other]), 4)
            for other in HEATMAP_COLUMNS
        }
        for col in HEATMAP_COLUMNS
    },
    "pca_decision": pca_decision,
    "column_classification": I3_CLASSIFICATION,
}

json_path = artifacts_dir / "01_02_07_multivariate_analysis.json"
with open(json_path, "w") as f:
    json.dump(json_artifact, f, indent=2)
print(f"Saved: {json_path}")

# %% [markdown]
# ## Conclusion
#
# ### Key scientific findings
#
# **PCA is degenerate for aoe2companion.** All pre-game numeric candidates
# (population, speedFactor, treatyLength) have IQR=0 in 1v1 ranked play —
# they are near-constant across matches. Zero viable features remain after
# excluding POST-GAME (ratingDiff, duration_min), AMBIGUOUS (rating),
# NOT-A-FEATURE (slot, color, team), and near-constant columns. No scree
# plot or biplot is produced; a text-summary fallback PNG documents the
# degeneracy finding.
#
# **Spearman heatmap findings.** The cluster-ordered heatmap shows weak
# pairwise correlations among all seven numeric columns in 1v1 ranked play.
# speedFactor and treatyLength yield NaN Spearman coefficients (filled with
# 0 = uncorrelated) because their near-zero rank variance makes the
# denominator degenerate. ratingDiff is confirmed POST-GAME. rating is
# AMBIGUOUS (deferred to Phase 02).
#
# **Phase 02 implications.** aoe2companion's raw numeric pre-game feature
# space is effectively empty. Phase 02 must engineer features from temporal
# match history — rolling win rates, Elo trajectories, head-to-head stats,
# and civilisation matchup statistics — to build a useful prediction feature
# set.
#
# ### Artifacts produced
# - `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_07_spearman_heatmap_all.png` — cluster-ordered Spearman heatmap (all numeric columns, I3-labelled)
# - `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png` — degenerate PCA fallback summary (text plot)
# - `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md` — full analysis markdown (SQL embedded per I6)
# - `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json` — machine-readable summary (step, dataset, spearman_matrix, pca_decision, column_classification)
#
# ### Thesis mapping
# - thesis/chapters/02_data_exploration.md — Section: Pre-game Feature Space Assessment
#
# ### Follow-ups
# - Phase 02: engineer temporal features (Elo, win rates, civ matchup stats) — raw numeric space is insufficient
# - Phase 02: revisit `rating` AMBIGUOUS classification; resolve with temporal analysis of rating changes around match time

# %% -- Cell 21: gate verification
expected_plots = ["01_02_07_spearman_heatmap_all.png"]
if not PCA_DEGENERATE:
    expected_plots.append("01_02_07_pca_scree.png")
expected_plots.append("01_02_07_pca_biplot.png")

for plot_name in expected_plots:
    path = plots_dir / plot_name
    assert path.exists(), f"Missing plot: {path}"
    assert path.stat().st_size > 0, f"Empty plot: {path}"
    print(f"  OK: {plot_name} ({path.stat().st_size:,} bytes)")

assert md_path.exists() and md_path.stat().st_size > 0, "Missing or empty markdown artifact"
print(f"  OK: 01_02_07_multivariate_analysis.md ({md_path.stat().st_size:,} bytes)")

md_content = md_path.read_text()
for qname in sql_queries:
    assert qname in md_content, f"SQL query '{qname}' missing from markdown artifact"
    print(f"  OK: SQL query '{qname}' found in markdown")

assert "I3 Classification" in md_content, "Feature classification table missing"
print("  OK: Feature classification table present")

assert json_path.exists(), f"Missing JSON artifact: {json_path}"
assert json_path.stat().st_size > 0, f"Empty JSON artifact: {json_path}"
with open(json_path) as _f:
    _j = json.load(_f)
assert _j["step"] == "01_02_07", "JSON step field mismatch"
assert _j["dataset"] == "aoe2companion", "JSON dataset field mismatch"
assert "spearman_matrix" in _j, "JSON missing spearman_matrix"
assert "pca_decision" in _j, "JSON missing pca_decision"
assert "column_classification" in _j, "JSON missing column_classification"
print(f"  OK: 01_02_07_multivariate_analysis.json ({json_path.stat().st_size:,} bytes)")

print("\nAll gate checks passed.")

# %% -- Cell 22: close connection
db.close()
