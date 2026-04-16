---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
critique_required: true
source_artifacts:
  - "reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
  - "data/db/db.duckdb (matches_raw)"
research_log_ref: "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md#2026-04-15-01-02-07-multivariate-eda"
---

# Plan: aoe2companion Step 01_02_07 -- Multivariate EDA

## Scope

**Phase/Step:** 01 / 01_02_07
**Branch:** feat/census-pass3
**Action:** CREATE (step 01_02_07 does not exist in ROADMAP.md; added here)
**Predecessor:** 01_02_06 (Bivariate EDA -- complete, artifacts on disk)

Create a multivariate EDA notebook that produces two analyses: (A) a Spearman
cluster-ordered correlation heatmap for all numeric columns in matches_raw with
I3 classification labels, and (B) a PCA analysis on pre-game numeric features
only. Because the aoe2companion dataset has very few genuinely numeric pre-game
columns after excluding POST-GAME (ratingDiff, duration) and AMBIGUOUS (rating)
columns, PCA is expected to be degenerate. The plan includes a fallback to a
feature scatter plot with documented reasoning. Produces 2-3 PNG plots plus a
markdown artifact with all SQL queries. No DuckDB writes. No new tables.

This step is the third and final layer of the 01_02 EDA stack:
- 01_02_04: Univariate Census (complete)
- 01_02_05: Univariate Visualizations (complete)
- 01_02_06: Bivariate EDA (complete)
- **01_02_07: Multivariate EDA (this plan)**

## Problem Statement

Step 01_02_06 established pairwise relationships between features and outcome.
Multivariate EDA addresses the final layer: how do features relate to each other
as a group? A cluster-ordered Spearman heatmap reveals redundancy clusters and
surprising cross-feature dependencies that are invisible in pairwise plots.
PCA (or its degenerate fallback) quantifies the effective dimensionality of the
pre-game feature space, directly informing Phase 02 feature engineering decisions.

The critical challenge for aoe2companion is feature poverty: the matches_raw
table has 9 numeric columns, but after excluding POST-GAME columns (ratingDiff,
duration), the AMBIGUOUS column (rating), and non-feature columns (slot, color --
UI/positional indices), only 4 candidates remain: population, speedFactor,
treatyLength, and internalLeaderboardId. Of these, speedFactor (std=0.09,
4 distinct values), treatyLength (96.56% zero), and population (p05=p25=p75=200)
are near-constant in 1v1 ranked play. This near-degeneracy is itself a finding:
the aoe2companion pre-game feature space is effectively empty for numeric
features, making engineered features (win rates, Elo history) critical for
Phase 02.

## Assumptions & Unknowns

- **Assumption:** The census JSON at `01_02_04_univariate_census.json` is the
  single source of truth for total_rows, NULL rates, numeric stats, and column
  inventories. All runtime constants derive from it.
- **Assumption:** DuckDB contains the materialized `matches_raw` (277,099,059
  rows) table from 01_02_02.
- **Assumption:** The I3 classifications from 01_02_06 are authoritative:
  ratingDiff=POST-GAME (confirmed), rating=AMBIGUOUS (inconclusive in 01_02_06),
  duration=POST-GAME (known only after match).
- **Unknown:** Whether PCA on the surviving pre-game features will be
  degenerate. The plan includes a deterministic branch: if fewer than 3 pre-game
  numeric features survive variance filtering, produce a labeled scatter plot
  instead of a PCA biplot. This unknown resolves at execution time by inspecting
  census stats programmatically.
- **Unknown:** The exact number of rows after NULL filtering for the Spearman
  sample. Expected to be approximately 100,000 (from BERNOULLI sampling) but
  the actual count depends on NULL co-occurrence patterns in the sample.

## Literature Context

PCA on pre-game match features is standard in esports prediction literature
(Ravari et al. 2016 used PCA for Dota 2 draft-phase features; Thompson et al.
2013 applied dimensionality reduction to SC2 build orders). The Spearman
rank-correlation matrix is preferred over Pearson for ordinal and non-normal
distributions (Sheskin 2003), which describes most game-setting columns.
Hierarchical clustering of the distance matrix (1 - |rho|) for axis ordering
follows the dendrogram-reordered heatmap convention (Wilkinson & Friendly 2009).

## Execution Steps

### T01 -- ROADMAP and STEP_STATUS Patch

**Objective:** Register step 01_02_07 in ROADMAP.md and STEP_STATUS.yaml so that
the step exists in the project tracking system before execution begins.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`.
2. Insert the following Step 01_02_07 YAML block after the Step 01_02_06 block
   and before the "Phase 02" placeholder section.

```yaml
step_number: "01_02_07"
name: "Multivariate EDA"
description: "Multivariate exploratory data analysis for aoe2companion. Spearman cluster-ordered heatmap for all numeric columns with I3 classification labels. PCA scree + biplot on pre-game numeric features only (degenerate fallback if <3 features survive). All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations per Invariant #3."
phase: "01 -- Data Exploration"
pipeline_section: "01_02 -- Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "How do numeric features cluster together (redundancy)? What is the effective dimensionality of the pre-game feature space?"
method: "Spearman via scipy.stats.spearmanr on BERNOULLI-sampled rows. Hierarchical clustering for axis ordering (scipy.cluster.hierarchy). PCA on StandardScaler-transformed pre-game numeric features (sklearn). Scree plot + biplot or degenerate scatter fallback. Markdown artifact with all SQL (I6)."
stratification: "1v1 ranked scope (rm_1v1 + qp_rm_1v1)."
predecessors:
  - "01_02_04"
  - "01_02_06"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_07_multivariate_eda.py"
inputs:
  duckdb_tables:
    - "matches_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_07_pca_scree.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png"
  report: "artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md"
gate:
  artifact_check: "01_02_07_spearman_heatmap_all.png exists. At least one PCA plot (scree or degenerate scatter) exists. 01_02_07_multivariate_analysis.md exists with SQL queries (Invariant #6) and feature classification table."
  continue_predicate: "Notebook executes end-to-end without error. Feature classification table complete."
  halt_predicate: "DuckDB queries fail on matches_raw or sampling yields zero rows."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Axis tick labels on Spearman heatmap carry I3 classification (POST-GAME, AMBIGUOUS, PRE-GAME). PCA excludes all POST-GAME and AMBIGUOUS columns."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "TARGET_SAMPLE_ROWS derived from census total_rows at runtime. Column selection derived from census numeric_stats. No hardcoded thresholds."
  - number: "9"
    how_upheld: "Multivariate visualization of features established in 01_02_04 and classified in 01_02_06. No new analytical computation beyond visualization."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

3. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`.
4. Add `01_02_07` entry with `name: "Multivariate EDA"`,
   `pipeline_section: "01_02"`, `status: not_started`.

**Verification:**
- ROADMAP.md contains Step 01_02_07 YAML block after 01_02_06.
- STEP_STATUS.yaml contains `01_02_07` entry with `status: not_started`.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`

---

### T02 -- Notebook Setup (census load, DuckDB connection, constants)

**Objective:** Create the notebook skeleton with all imports, DuckDB read-only
connection, census JSON load, path constants, sql_queries dict, I3 classification
table, and sampling fraction derivation. All subsequent tasks build on this cell
block.

**Instructions:**
1. Create `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_07_multivariate_eda.py`
   with jupytext percent-format header (same kernel metadata as 01_02_06).

**Cell 1 — markdown header:**
```
# Step 01_02_07 -- Multivariate EDA: aoe2companion
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
```

**Cell 2 — imports:**
```python
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOE2COMPANION_DB_FILE

logger = setup_notebook_logging()
matplotlib.use("Agg")
```

**Cell 3 — DuckDB connection (read-only):**
```python
con = duckdb.connect(str(AOE2COMPANION_DB_FILE), read_only=True)
print(f"Connected to: {AOE2COMPANION_DB_FILE}")
```

**Cell 4 — census JSON load and path setup:**
```python
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
plots_dir = artifacts_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

census_json_path = artifacts_dir / "01_02_04_univariate_census.json"
with open(census_json_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")
```

**Cell 5 — assert required census keys:**
```python
required_keys = [
    "matches_raw_total_rows",
    "matches_raw_null_census",
    "matches_raw_numeric_stats",
    "categorical_profiles",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"
```

**Cell 6 — derive sampling fraction from census (I7):**
```python
# I7: sample fraction derived from census total_rows at runtime
total_rows = census["matches_raw_total_rows"]  # 277,099,059
TARGET_SAMPLE_ROWS = 100_000  # I7: editorial cap — same as 01_02_06
sample_pct = min(100.0, TARGET_SAMPLE_ROWS * 100.0 / total_rows)
print(f"Total rows: {total_rows:,}")
print(f"Target sample: {TARGET_SAMPLE_ROWS:,}")
print(f"Sample percent: {sample_pct:.6f}%")
# Expected: ~0.036% for 277M rows
```

**Cell 7 — I3 feature classification table:**
```python
# I3 classification table — authoritative for this step.
# Source: 01_02_06 bivariate EDA findings.
# ratingDiff: POST-GAME (confirmed in 01_02_06 Q1)
# rating: AMBIGUOUS (inconclusive in 01_02_06 Q2 — deferred to Phase 02)
# duration_min: POST-GAME — computed as EXTRACT(EPOCH FROM (finished - started))/60.
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

# Pre-game columns for PCA — exclude POST-GAME, AMBIGUOUS, and nominal
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
```

**Cell 8 — initialize sql_queries and leaderboard filter:**
```python
sql_queries = {}

leaderboard_names = [
    entry["value"]
    for entry in census["categorical_profiles"]["leaderboard"]
]
assert "rm_1v1" in leaderboard_names, "rm_1v1 not in census leaderboard list"
assert "qp_rm_1v1" in leaderboard_names, "qp_rm_1v1 not in census leaderboard list"
LEADERBOARD_1V1_FILTER = "leaderboard IN ('rm_1v1', 'qp_rm_1v1')"
print(f"1v1 leaderboard filter: {LEADERBOARD_1V1_FILTER}")
```

**Verification:**
- Notebook imports and runs through setup without error.
- Census JSON loads and key assertion passes.
- Sample fraction ~0.036%.
- HEATMAP_COLUMNS has 7 entries, PCA_CANDIDATES has 4 entries.

---

### T03 -- Spearman Cluster-Ordered Heatmap (Analysis A)

**Objective:** Produce a Spearman rank-correlation heatmap for all 7 numeric
columns with meaningful variance. Axis tick labels carry I3 classification.
Hierarchical clustering reorders axes to reveal feature clusters.

**Cell 9 — SQL and sample fetch:**
```python
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
```

**Cell 10 — compute Spearman matrix and cluster ordering:**
```python
rho_matrix, p_matrix = spearmanr(df_spearman[HEATMAP_COLUMNS])
rho_df = pd.DataFrame(rho_matrix, index=HEATMAP_COLUMNS, columns=HEATMAP_COLUMNS)
p_df = pd.DataFrame(p_matrix, index=HEATMAP_COLUMNS, columns=HEATMAP_COLUMNS)

# Hierarchical clustering on distance = 1 - |rho|
dist_matrix = 1 - np.abs(rho_df.values)
np.fill_diagonal(dist_matrix, 0)
condensed_dist = squareform(dist_matrix)
Z = linkage(condensed_dist, method="average")
cluster_order = leaves_list(Z)

ordered_cols = [HEATMAP_COLUMNS[i] for i in cluster_order]
ordered_labels = [HEATMAP_LABELS[i] for i in cluster_order]
rho_ordered = rho_df.loc[ordered_cols, ordered_cols]
p_ordered = p_df.loc[ordered_cols, ordered_cols]
```

**Cell 11 — plot heatmap:**
```python
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
```

**Verification:**
- `01_02_07_spearman_heatmap_all.png` exists and is non-empty.
- Axis labels include I3 classification tags.
- Cell annotations show rho values with significance stars.

---

### T04 -- PCA Scree Plot (Analysis B, Part 1)

**Objective:** Produce a PCA scree plot for pre-game numeric features only.
Handle the degenerate case (fewer than 3 usable features) with documented reasoning.

**Cell 12 — variance check from census (I7):**
```python
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
        print(f"  EXCLUDED (near-constant): {col} — p25==p75=={stats['p25']}")
    else:
        pca_viable_cols.append(col)
        print(f"  VIABLE: {col} — p25={stats['p25']}, p75={stats['p75']}, std={stats['stddev_val']}")

print(f"\nPCA viable columns ({len(pca_viable_cols)}): {pca_viable_cols}")
print(f"PCA excluded columns ({len(pca_excluded_cols)}): {pca_excluded_cols}")
PCA_DEGENERATE = len(pca_viable_cols) < 3
print(f"PCA degenerate: {PCA_DEGENERATE}")
```

**Cell 13 — PCA (non-degenerate path):**
```python
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

    pca_sql = f"""
SELECT
    {pca_col_sql},
    won
FROM (
    SELECT *
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
```

**Cell 14 — scree plot (non-degenerate):**
```python
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
```

**Cell 15 — degenerate path note:**
```python
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
```

**Verification:**
- If non-degenerate: `01_02_07_pca_scree.png` exists with bar + line plot.
- If degenerate: degeneracy note printed, scree plot skipped.

---

### T05 -- PCA Biplot or Degenerate Fallback (Analysis B, Part 2)

**Objective:** Produce either a PCA biplot (non-degenerate) or a feature
scatter/histogram fallback (degenerate).

**Cell 16 — non-degenerate biplot:**
```python
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
```

**Cell 17 — degenerate fallback:**
```python
if PCA_DEGENERATE:
    if len(pca_viable_cols) == 0:
        print("No viable pre-game numeric features. Biplot skipped entirely.")
    elif len(pca_viable_cols) == 1:
        col = pca_viable_cols[0]
        scatter_sql = f"""
SELECT {col}, won
FROM (SELECT * FROM matches_raw TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)) sub
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
FROM (SELECT * FROM matches_raw TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)) sub
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
```

**Verification:**
- If non-degenerate: `01_02_07_pca_biplot.png` exists with scatter + loading arrows.
- If degenerate: `01_02_07_pca_biplot.png` exists as scatter fallback.

---

### T06 -- Markdown Artifact and Verification

**Objective:** Write the `01_02_07_multivariate_analysis.md` artifact with plot
index table, all SQL queries (I6), feature classification table. Verify all outputs.

**Cell 18 — build and write markdown:**
```python
classification_rows = []
for col, cls in I3_CLASSIFICATION.items():
    in_heatmap = "Yes" if col in HEATMAP_COLUMNS else "No"
    in_pca = "Yes" if col in pca_viable_cols else "No"
    excluded_reason = ""
    if col in [c for c, _ in pca_excluded_cols]:
        excluded_reason = dict(pca_excluded_cols).get(col, "")
    elif cls == "POST-GAME":
        excluded_reason = "POST-GAME (I3)"
    elif cls == "AMBIGUOUS":
        excluded_reason = "AMBIGUOUS — deferred to Phase 02"
    elif cls == "NOT-A-FEATURE":
        excluded_reason = "UI/positional index"
    classification_rows.append((col, cls, in_heatmap, in_pca, excluded_reason))

plot_entries = [
    ("1", "Spearman Cluster-Ordered Heatmap", "01_02_07_spearman_heatmap_all.png",
     "Feature redundancy clusters", "All — I3-labelled axes"),
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
```

**Cell 19 — gate verification:**
```python
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

print("\nAll gate checks passed.")
```

**Cell 20 — close connection:**
```python
con.close()
```

**Verification:**
- `01_02_07_multivariate_analysis.md` exists, non-empty, contains all SQL queries.
- Feature classification table present.
- All expected PNG files exist and are non-empty.

---

### T07 -- STEP_STATUS Update + Research Log

**Objective:** Mark step 01_02_07 as complete and write a research log entry.

**Instructions:**
1. Update `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`:
   change `01_02_07` status to `complete`, add `completed_at: "2026-04-15"`.
2. Prepend a research log entry to
   `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`
   after the header block, before the 01_02_06 entry. Entry should include:
   - Number of plots produced (2 or 3 depending on PCA viability).
   - Spearman heatmap findings: notable clusters (ratingDiff/rating correlation,
     feature independence patterns).
   - PCA outcome: degenerate or not; effective dimensionality.
   - Pre-game feature poverty conclusion.
   - I3 classification decisions applied.

**Verification:**
- STEP_STATUS.yaml shows `01_02_07: status: complete`.
- research_log.md has new entry for 01_02_07 at the top.

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update (T01) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Update (T01, T07) |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_07_multivariate_eda.py` | Create (T02–T06) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md` | Create (T06) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png` | Create (T03) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_scree.png` | Create (T04, if non-degenerate) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png` | Create (T05) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Update (T07) |

## Gate Condition

- `01_02_07_spearman_heatmap_all.png` exists under `plots/` and is non-empty.
- At least one PCA-related plot exists (`01_02_07_pca_scree.png` or `01_02_07_pca_biplot.png`).
- `01_02_07_multivariate_analysis.md` exists with: SQL queries (I6), feature
  classification table (I3), and plot index.
- Notebook executes end-to-end without error.
- STEP_STATUS.yaml shows `01_02_07: status: complete`.
- research_log.md has entry for 01_02_07.

## Out of Scope

- **New table creation or DuckDB writes.** This step is read-only visualization (I9).
- **Resolving rating temporal ambiguity.** Rating remains AMBIGUOUS per 01_02_06.
  Resolution requires Phase 02 row-level verification with ratings_raw.
- **Cross-dataset comparison.** Deferred to Phase 01 Decision Gate (01_06).
- **Feature engineering.** PCA findings inform Phase 02 but no features created here.
- **Categorical PCA or MCA.** Numeric columns only; categorical analysis in Phase 02.

## Open Questions

- **Will PCA be degenerate?** Resolves at execution time. Census data suggests 3
  viable features (population, speedFactor, internalLeaderboardId) after treatyLength
  exclusion. The plan includes full degenerate fallback paths.
- **Should internalLeaderboardId be treated as numeric or categorical for PCA?**
  Integer-encoded categorical (122 distinct values). Included as-is for this
  exploratory step. Phase 02 determines proper encoding.
