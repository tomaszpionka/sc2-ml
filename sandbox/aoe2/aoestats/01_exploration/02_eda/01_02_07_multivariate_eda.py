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
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_02_07 -- Multivariate EDA: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
# **Dataset:** aoestats
# **Question:** What is the full inter-table correlation structure? How much
# variance is concentrated in the first few principal components of pre-game features?
# **Invariants applied:**
# - #3 (temporal discipline -- POST-GAME and IN-GAME columns annotated on heatmap)
# - #6 (reproducibility -- all SQL stored verbatim in markdown artifact)
# - #7 (no magic numbers -- all thresholds from census JSON; sample size justified)
# - #9 (step scope: multivariate analysis only -- no cleaning or feature decisions)
# **Predecessor:** 01_02_06 (Bivariate EDA -- complete, artifacts on disk)
# **Step scope:** multivariate EDA only -- visualization + dimensionality assessment.
# No cleaning decisions, no feature engineering, no model fitting.
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` Step 01_02_07
# **Commit:** 59fa781
# **Date:** 2026-04-15

# %%
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging

matplotlib.use("Agg")
logger = setup_notebook_logging(__name__)

# %%
conn = get_notebook_db("aoe2", "aoestats")

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

census_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_path) as f:
    census = json.load(f)

bivariate_path = artifacts_dir / "01_02_06_bivariate_eda.json"
with open(bivariate_path) as f:
    bivariate = json.load(f)

# %%
required_census_keys = [
    "matches_null_census", "players_null_census",
    "numeric_stats_matches", "numeric_stats_players",
    "elo_sentinel_counts",
]
for k in required_census_keys:
    assert k in census, f"Missing census key: {k}"

# Verify match_rating_diff leakage resolved as PRE_GAME
assert bivariate["match_rating_diff_leakage"]["leakage_status"] == "PRE_GAME", (
    "match_rating_diff leakage must be resolved as PRE_GAME before multivariate EDA"
)
print("All required keys present. match_rating_diff = PRE_GAME (confirmed).")

# %%
sql_queries = {}
multivariate_results = {
    "step": "01_02_07",
    "dataset": "aoestats",
}

# %%
# I7: Sample size justified by cross-table JOIN cost.
# matches_raw has 30M+ rows; players_raw has 107M+ rows.
# A 20K reservoir sample keeps memory and wall time tractable.
# SE(rho) ~ 0.007 for rho=0 at N=20K -- well below any substantive threshold.
TARGET_SAMPLE_ROWS = 20_000

# I7: ELO sentinel from census
ELO_SENTINEL = -1

# I7: Row counts from census (for logging)
MATCHES_TOTAL = census["matches_null_census"]["total_rows"]
PLAYERS_TOTAL = census["players_null_census"]["total_rows"]

print(f"TARGET_SAMPLE_ROWS = {TARGET_SAMPLE_ROWS}")
print(f"ELO_SENTINEL = {ELO_SENTINEL}")
print(f"matches_raw rows: {MATCHES_TOTAL:,}")
print(f"players_raw rows: {PLAYERS_TOTAL:,}")

# %% [markdown]
# ## Analysis A -- Spearman Cluster-Ordered Heatmap (All Numeric Columns)

# %%
sql_spearman_sample = f"""
SELECT
    p.old_rating,
    p.new_rating,
    p.match_rating_diff,
    p.feudal_age_uptime,
    p.castle_age_uptime,
    p.imperial_age_uptime,
    m.avg_elo,
    m.team_0_elo,
    m.team_1_elo,
    (m.duration / 1e9) AS duration_sec
FROM players_raw p
JOIN matches_raw m ON p.game_id = m.game_id
WHERE p.old_rating >= 0
  AND m.team_0_elo != {ELO_SENTINEL}
  AND m.team_1_elo != {ELO_SENTINEL}
USING SAMPLE RESERVOIR({TARGET_SAMPLE_ROWS})
"""
sql_queries["spearman_cross_table_sample"] = sql_spearman_sample

# %%
df_spearman = conn.con.execute(sql_spearman_sample).fetchdf()
print(f"Spearman sample: {len(df_spearman)} rows, {df_spearman.shape[1]} columns")
print(f"Non-null counts:\n{df_spearman.notna().sum()}")

# %%
from scipy.stats import spearmanr as _spearmanr

cols = df_spearman.columns.tolist()

# B1 fix: use pandas .corr(method='spearman') for pairwise deletion.
# scipy.stats.spearmanr on a 2D matrix uses LISTWISE deletion (drops any
# row with any masked value), which reduces the effective sample from ~20,000
# rows to ~1,700 rows when the three ~87%-NULL age_uptime columns are present.
# pandas .corr() uses PAIRWISE deletion by default (each pair uses all rows
# where both columns are non-null), preserving the full sample for non-NULL pairs.
rho_df = df_spearman.corr(method="spearman")

# Compute p-values pairwise to match the pairwise approach above.
n_cols = len(cols)
pval_df = pd.DataFrame(np.nan, index=cols, columns=cols)
for i, col_a in enumerate(cols):
    for j, col_b in enumerate(cols):
        if i == j:
            pval_df.loc[col_a, col_b] = 0.0
        elif j > i:
            mask = df_spearman[[col_a, col_b]].notna().all(axis=1)
            a, b = df_spearman.loc[mask, col_a], df_spearman.loc[mask, col_b]
            if len(a) >= 3:
                _, p = _spearmanr(a, b)
                pval_df.loc[col_a, col_b] = p
                pval_df.loc[col_b, col_a] = p

# Assert minimum pairwise sample size (I7: no magic numbers -- 1,000 is a
# conservative floor given TARGET_SAMPLE_ROWS=20,000 and the expected
# ~13% non-NULL rate of the age uptime columns: 20,000 * 0.13 ~ 2,600).
min_pairwise_n = min(
    df_spearman[[c1, c2]].dropna().shape[0]
    for c1, c2 in [
        (c1, c2)
        for i, c1 in enumerate(cols)
        for c2 in cols[i + 1:]
    ]
)
assert min_pairwise_n >= 1_000, f"Minimum pairwise sample too small: {min_pairwise_n} rows"
print(f"Minimum pairwise N across all column pairs: {min_pairwise_n:,}")
print("Spearman matrix computed via pairwise deletion (pandas .corr) -- OK")

# %%
i3_labels = {
    "old_rating": "old_rating",
    "new_rating": "new_rating  POST-GAME*",
    "match_rating_diff": "match_rating_diff  PRE-GAME",
    "feudal_age_uptime": "feudal_age_uptime  IN-GAME*",
    "castle_age_uptime": "castle_age_uptime  IN-GAME*",
    "imperial_age_uptime": "imperial_age_uptime  IN-GAME*",
    "avg_elo": "avg_elo",
    "team_0_elo": "team_0_elo",
    "team_1_elo": "team_1_elo",
    "duration_sec": "duration_sec  POST-GAME*",
}

dist = 1 - np.abs(rho_df.values)
np.fill_diagonal(dist, 0)
dist = np.clip(dist, 0, 2)
condensed = squareform(dist, checks=False)
Z = linkage(condensed, method="average")
order = leaves_list(Z)

rho_ordered = rho_df.iloc[order, order]
ordered_labels = [i3_labels[c] for c in rho_ordered.columns]

# %%
fig, ax = plt.subplots(figsize=(12, 10))
im = ax.imshow(rho_ordered.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
cbar = fig.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label("Spearman rho", fontsize=11)

ax.set_xticks(range(len(ordered_labels)))
ax.set_yticks(range(len(ordered_labels)))
ax.set_xticklabels(ordered_labels, rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(ordered_labels, fontsize=9)

for i in range(len(ordered_labels)):
    for j in range(len(ordered_labels)):
        val = rho_ordered.values[i, j]
        if not np.isnan(val):
            color = "white" if abs(val) > 0.6 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=7, color=color)

ax.set_title(
    "Spearman Rank Correlation -- All Numeric Columns (cross-table JOIN)\n"
    f"N={len(df_spearman):,} sampled rows | * = excluded from PCA feature set",
    fontsize=11,
)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_07_spearman_heatmap_all.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_07_spearman_heatmap_all.png")

# %%
multivariate_results["spearman_heatmap"] = {
    "sample_size": len(df_spearman),
    "columns": cols,
    "cluster_order": [cols[i] for i in order],
    "rho_matrix": {
        col: {col2: round(rho_df.loc[col, col2], 4) for col2 in cols}
        for col in cols
        if not rho_df[col].isna().all()
    },
}

# %% [markdown]
# ## Analysis B -- PCA on Pre-Game Features
#
# Feature set: old_rating, match_rating_diff, avg_elo, team_0_elo, team_1_elo
# Excluded: new_rating (POST-GAME), duration_sec (POST-GAME), age uptime columns
# (IN-GAME and 87% NULL -- insufficient complete-case coverage for PCA).
#
# Invariant #3: POST-GAME and IN-GAME columns must not be used for pre-game
# prediction. PCA is descriptive only -- no component retention decision is
# made here (deferred to Phase 02 feature engineering). Invariant #9.

# %%
PCA_FEATURES = ["old_rating", "match_rating_diff", "avg_elo", "team_0_elo", "team_1_elo"]

sql_pca_sample = f"""
SELECT
    p.old_rating,
    p.match_rating_diff,
    p.winner,
    m.avg_elo,
    m.team_0_elo,
    m.team_1_elo
FROM players_raw p
JOIN matches_raw m ON p.game_id = m.game_id
WHERE p.old_rating >= 0
  AND p.match_rating_diff IS NOT NULL
  AND m.team_0_elo != {ELO_SENTINEL}
  AND m.team_1_elo != {ELO_SENTINEL}
USING SAMPLE RESERVOIR({TARGET_SAMPLE_ROWS})
"""
sql_queries["pca_cross_table_sample"] = sql_pca_sample

# %%
df_pca = conn.con.execute(sql_pca_sample).fetchdf()
print(f"PCA sample: {len(df_pca)} rows")
print(f"Null counts:\n{df_pca[PCA_FEATURES].isna().sum()}")
assert df_pca[PCA_FEATURES].isna().sum().sum() == 0, "PCA features must have no NULLs"

# %%
X = df_pca[PCA_FEATURES].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA(n_components=len(PCA_FEATURES), random_state=42)
X_pca = pca.fit_transform(X_scaled)

var_explained = pca.explained_variance_ratio_
cum_var = np.cumsum(var_explained)

print("Variance explained per component:")
for i, (v, c) in enumerate(zip(var_explained, cum_var)):
    print(f"  PC{i+1}: {v:.4f} (cumulative: {c:.4f})")

# %%
fig, ax1 = plt.subplots(figsize=(8, 5))

n_comp = len(PCA_FEATURES)
x = np.arange(1, n_comp + 1)

ax1.bar(x, var_explained, color="steelblue", alpha=0.7, label="Individual")
ax1.set_xlabel("Principal Component", fontsize=11)
ax1.set_ylabel("Variance Explained (ratio)", fontsize=11, color="steelblue")
ax1.tick_params(axis="y", labelcolor="steelblue")
ax1.set_xticks(x)
ax1.set_xticklabels([f"PC{i}" for i in x])

ax2 = ax1.twinx()
ax2.plot(x, cum_var, "o-", color="darkorange", linewidth=2, label="Cumulative")
ax2.set_ylabel("Cumulative Variance Explained", fontsize=11, color="darkorange")
ax2.tick_params(axis="y", labelcolor="darkorange")
ax2.set_ylim(0, 1.05)
ax2.axhline(
    y=0.95, color="gray", linestyle="--", alpha=0.5,
    label="conventional reference line (not a retention criterion -- see Phase 02)",
)

for i, v in enumerate(var_explained):
    ax1.text(x[i], v + 0.01, f"{v:.3f}", ha="center", fontsize=9)

ax1.set_title(
    f"PCA Scree Plot -- Pre-Game Features Only\n"
    f"Features: {', '.join(PCA_FEATURES)} | N={len(df_pca):,}",
    fontsize=11,
)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right")

fig.tight_layout()
fig.savefig(plots_dir / "01_02_07_pca_scree.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_07_pca_scree.png")

# %%
multivariate_results["pca_scree"] = {
    "features": PCA_FEATURES,
    "sample_size": len(df_pca),
    "n_components": n_comp,
    "variance_explained": [round(float(v), 6) for v in var_explained],
    "cumulative_variance": [round(float(c), 6) for c in cum_var],
    "scaler_means": [round(float(m), 4) for m in scaler.mean_],
    "scaler_stds": [round(float(s), 4) for s in scaler.scale_],
}

# %%
loadings = pca.components_.T  # shape: (n_features, n_components)

# %%
fig, ax = plt.subplots(figsize=(10, 8))

winner_col = df_pca["winner"].astype(int).values
scatter = ax.scatter(
    X_pca[:, 0], X_pca[:, 1],
    c=winner_col, cmap="coolwarm", alpha=0.15, s=5, edgecolors="none",
)

scale = max(
    np.abs(X_pca[:, 0]).max(),
    np.abs(X_pca[:, 1]).max(),
) * 0.8

for i, feature in enumerate(PCA_FEATURES):
    ax.annotate(
        "",
        xy=(loadings[i, 0] * scale, loadings[i, 1] * scale),
        xytext=(0, 0),
        arrowprops=dict(arrowstyle="->", color="black", linewidth=1.5),
    )
    ax.text(
        loadings[i, 0] * scale * 1.08,
        loadings[i, 1] * scale * 1.08,
        feature,
        fontsize=9,
        fontweight="bold",
        ha="center",
        va="center",
    )

cbar = fig.colorbar(scatter, ax=ax, shrink=0.6)
cbar.set_label("winner (0=loss, 1=win)", fontsize=10)
cbar.set_ticks([0, 1])
cbar.set_ticklabels(["Loss", "Win"])

ax.set_xlabel(f"PC1 ({var_explained[0]:.1%} variance)", fontsize=11)
ax.set_ylabel(f"PC2 ({var_explained[1]:.1%} variance)", fontsize=11)
ax.set_title(
    f"PCA Biplot -- Pre-Game Features\n"
    f"Features: {', '.join(PCA_FEATURES)} | N={len(df_pca):,}",
    fontsize=11,
)
ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
ax.axvline(x=0, color="gray", linestyle="-", alpha=0.3)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_07_pca_biplot.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_02_07_pca_biplot.png")

# %%
multivariate_results["pca_biplot"] = {
    "loadings": {
        feature: {
            f"PC{j+1}": round(float(loadings[i, j]), 6)
            for j in range(loadings.shape[1])
        }
        for i, feature in enumerate(PCA_FEATURES)
    },
}

# %% [markdown]
# ## Artifacts

# %%
json_path = artifacts_dir / "01_02_07_multivariate_analysis.json"
with open(json_path, "w") as f:
    json.dump(multivariate_results, f, indent=2)
print(f"JSON artifact written: {json_path}")

# %%
pca_results = multivariate_results["pca_scree"]

md_lines = [
    "# Step 01_02_07 -- Multivariate EDA -- aoestats\n",
    f"**Generated:** 2026-04-15",
    f"**Dataset:** aoestats (matches_raw: {MATCHES_TOTAL:,} rows; "
    f"players_raw: {PLAYERS_TOTAL:,} rows)",
    f"**Predecessor:** 01_02_06 (Bivariate EDA)\n",
    "## Column Classification\n",
    "| Column | Source Table | Temporal Class | In PCA? | In Heatmap? |",
    "|--------|-------------|---------------|---------|-------------|",
    "| old_rating | players_raw | PRE-GAME | Yes | Yes |",
    "| match_rating_diff | players_raw | PRE-GAME (confirmed 01_02_06) | Yes | Yes |",
    "| avg_elo | matches_raw | PRE-GAME | Yes | Yes |",
    "| team_0_elo | matches_raw | PRE-GAME | Yes | Yes |",
    "| team_1_elo | matches_raw | PRE-GAME | Yes | Yes |",
    "| new_rating | players_raw | POST-GAME | No | Yes (annotated*) |",
    "| duration_sec | matches_raw | POST-GAME | No | Yes (annotated*) |",
    "| feudal_age_uptime | players_raw | IN-GAME (87% NULL) | No | Yes (annotated*) |",
    "| castle_age_uptime | players_raw | IN-GAME (88% NULL) | No | Yes (annotated*) |",
    "| imperial_age_uptime | players_raw | IN-GAME (91% NULL) | No | Yes (annotated*) |",
    "",
    "**Note:** cross-table JOIN produces multiple player rows per match. Match-level "
    "columns (avg_elo, team_0_elo, team_1_elo, duration_sec) are repeated across "
    "players within the same game. Correlations between match-level columns in this "
    "heatmap reflect this duplication; per-table correlations from 01_02_06 are the "
    "authoritative within-table values.",
    "",
    "## Plot Index\n",
    "| # | Title | Filename | Temporal Annotation |",
    "|---|-------|----------|---------------------|",
    "| 1 | Spearman heatmap (all numeric, cross-table) | "
    "`01_02_07_spearman_heatmap_all.png` | Mixed -- POST-GAME* and IN-GAME* annotated on axis |",
    "| 2 | PCA scree plot (pre-game features only) | "
    "`01_02_07_pca_scree.png` | N/A (pre-game features only) |",
    "| 3 | PCA biplot (PC1 vs PC2, winner-coloured) | "
    "`01_02_07_pca_biplot.png` | N/A (pre-game features only) |",
    "",
    "## PCA Summary\n",
    f"Features: {', '.join(pca_results['features'])}",
    f"Sample size: {pca_results['sample_size']:,}\n",
    "**Note:** PC1 variance concentration is expected given the near-perfect "
    "collinearity of avg_elo, team_0_elo, and team_1_elo (pairwise rho > 0.98 "
    "per 01_02_06 Spearman matrix). PC1 dominance reflects ELO feature redundancy, "
    "not a latent factor. Retention decisions deferred to Phase 02.\n",
    "| Component | Variance Explained | Cumulative |",
    "|-----------|-------------------|------------|",
]
for i, (v, c) in enumerate(zip(
    pca_results["variance_explained"],
    pca_results["cumulative_variance"],
)):
    md_lines.append(f"| PC{i+1} | {v:.4f} | {c:.4f} |")
md_lines.append("")

md_lines.append("## SQL Queries\n")
for name, sql in sql_queries.items():
    md_lines.append(f"### {name}\n")
    md_lines.append(f"```sql\n{sql.strip()}\n```\n")

md_lines.append("## Data Sources\n")
md_lines.append(f"- `matches_raw` ({MATCHES_TOTAL:,} rows, 18 columns)")
md_lines.append(f"- `players_raw` ({PLAYERS_TOTAL:,} rows, 14 columns)")
md_lines.append("- Census artifact: `01_02_04_univariate_census.json`")
md_lines.append("- Bivariate artifact: `01_02_06_bivariate_eda.json`")

md_path = artifacts_dir / "01_02_07_multivariate_analysis.md"
md_path.write_text("\n".join(md_lines))
print(f"Markdown artifact written: {md_path}")

# %% [markdown]
# ## Conclusion
#
# ### Key scientific findings
#
# - **ELO cluster near-perfect collinearity:** avg_elo, team_0_elo, team_1_elo, old_rating,
#   and new_rating cluster together with pairwise Spearman rho of 0.977--0.998. This confirms
#   massive ELO feature redundancy across the players_raw / matches_raw join.
# - **match_rating_diff near-orthogonal to ELO cluster:** rho near zero with all ELO features.
#   Confirmed PRE-GAME by 01_02_06 bivariate leakage test; represents an independent dimension
#   of variation (PC2) not captured by the ELO axis.
# - **PCA effectively 2-dimensional:** PC1 explains 79.21% of variance (shared ELO axis);
#   PC2 explains 20.11% (match_rating_diff axis). Together they account for 99.33% of
#   total variance. PC3-5 are numerical noise (<0.4% each).
# - **Retention decisions deferred to Phase 02:** No feature engineering or column dropping
#   decisions are made here (Invariant #9). The near-perfect collinearity of the four ELO
#   features informs Phase 02 dimensionality reduction choices.
#
# ### Artifacts produced
# - `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json` -- structured results (rho matrix, PCA loadings)
# - `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md` -- human-readable report with embedded SQL
# - `reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png` -- cluster-ordered Spearman heatmap
# - `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_scree.png` -- PCA scree plot
# - `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png` -- PCA biplot coloured by winner
#
# ### Thesis mapping
# - Chapter 3 (Data & Features): multivariate structure section; supports ELO redundancy
#   discussion and dimensionality analysis for pre-game feature set.
#
# ### Follow-ups
# - Phase 02 Feature Engineering: decide which ELO features to retain vs drop/combine.
# - Consider whether match_rating_diff and old_rating are sufficient to represent
#   the pre-game rating information without avg_elo / team_0_elo / team_1_elo.

# %%
expected_plots = [
    "01_02_07_spearman_heatmap_all.png",
    "01_02_07_pca_scree.png",
    "01_02_07_pca_biplot.png",
]
for p in expected_plots:
    path = plots_dir / p
    assert path.exists() and path.stat().st_size > 0, f"Missing or empty: {p}"
    print(f"OK: {p} ({path.stat().st_size:,} bytes)")

assert md_path.exists() and md_path.stat().st_size > 0, "Markdown artifact missing"
print(f"OK: {md_path.name} ({md_path.stat().st_size:,} bytes)")

assert json_path.exists() and json_path.stat().st_size > 0, "JSON artifact missing"
print(f"OK: {json_path.name} ({json_path.stat().st_size:,} bytes)")

md_text = md_path.read_text()
for sql_name in sql_queries:
    assert sql_name in md_text, f"SQL query '{sql_name}' not in markdown artifact"
print("All SQL queries present in markdown artifact (Invariant #6 satisfied).")

print("\n=== GATE PASSED: 01_02_07 artifacts complete ===")

# %%
conn.close()
