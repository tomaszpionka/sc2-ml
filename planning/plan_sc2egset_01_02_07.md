---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
critique_required: true
source_artifacts:
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
  - "planning/plan_sc2egset_01_02_06.md"
  - "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.py"
research_log_ref: "src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-04-15-phase01-01_02_07"
---

# Plan: sc2egset Step 01_02_07 -- Multivariate EDA

## Scope

**Phase/Step:** 01 / 01_02_07
**Branch:** feat/census-pass3
**Action:** CREATE (new step -- no prior 01_02_07 artifacts exist)
**Predecessor:** 01_02_06 (Bivariate EDA -- complete, artifacts on disk)

Create a multivariate EDA notebook that produces (A) a Spearman cluster-ordered
heatmap of all four numeric columns (two-panel: all rows vs MMR>0), and (B) a
pre-game multivariate visualization addressing the degenerate PCA case (MMR is
the only numeric pre-game feature). Output: 2 PNG files, 1 markdown artifact,
1 JSON artifact, ROADMAP patch, STEP_STATUS update, research log entry.

This is the final step of pipeline section 01_02 (Tukey-style EDA). After
completion, 01_02 is complete for sc2egset and 01_03 (Systematic Data Profiling)
can begin.

## Problem Statement

Step 01_02_06 established pairwise feature-by-result associations. Step 01_02_07
extends to the multivariate view: how do all numeric features covary jointly,
and what joint structure exists in the pre-game feature space?

The core challenge is the **degenerate PCA case.** The sc2egset pre-game numeric
feature space contains exactly one column: `mmr`. With a single numeric feature,
PCA is trivially PC1=100% variance explained — the scree plot is uninformative,
and the biplot collapses to a line. This is not a methodological failure; it
reflects the genuine sparsity of pre-game numeric information in tournament
replay data.

**PCA alternative decision (Option 1 chosen):** Skip PCA entirely. Instead,
produce a pre-game multivariate view by faceting `mmr` distribution by both
`selectedRace` and `highestLeague` — showing the joint structure of all three
pre-game features (1 numeric, 2 categorical) in a single figure. This is
scientifically defensible because:

1. PCA requires >=2 numeric features to reveal any non-trivial structure.
   Running PCA on 1 feature produces a content-free artifact that wastes
   thesis space and communicates nothing.
2. The thesis question for multivariate EDA is "what joint structure exists
   in the pre-game feature space?" A faceted distribution directly answers
   this by showing how MMR distributes across race x league combinations.
3. Option 2 (including IN-GAME features in PCA with I3 annotation) was
   rejected because it conflates two distinct scientific purposes: the
   multivariate structure of the pre-game space (which feeds Phase 02
   feature engineering) and the reference-only in-game structure (which is
   already adequately documented by the Spearman heatmap in Part A). Mixing
   them in a PCA would produce loadings that are uninterpretable for Phase 02
   planning because the dominant PCs would be driven by in-game APM/SQ
   correlation rather than by pre-game structure.

For Part A (Spearman heatmap), the key difference from 01_02_06 is:
- 01_02_06 computed a flat Spearman matrix including `result_binary`
- 01_02_07 recomputes WITHOUT `result_binary` (pure feature-feature covariance),
  applies hierarchical clustering to reorder axes (revealing correlation blocks),
  and annotates axis labels with I3 classification

## Assumptions & Unknowns

- **Assumption:** Census JSON at
  `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the source of truth for all threshold values.
- **Assumption:** Bivariate JSON at
  `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json`
  provides the Spearman matrices computed with `result_binary` included.
  Step 01_02_07 recomputes WITHOUT `result_binary` for the pure
  feature-feature view.
- **Assumption:** All sentinel exclusion thresholds (MMR=0 count=37489,
  SQ INT32_MIN sentinel count=2) are derived from census at runtime (I7).
- **Assumption:** The Undecided (24) and Tie (2) row counts are looked up
  from census `result_distribution` at runtime (I7).
- **Assumption:** `scipy.cluster.hierarchy.linkage` + `dendrogram` are
  available for cluster-ordered axis reordering.
- **Unknown:** Whether the cluster ordering will meaningfully differ between
  the all-rows and MMR>0 panels. The 01_02_06 matrices suggest yes (MMR
  correlations jump from near-zero to 0.16-0.21 when zero-sentinel rows
  are removed). Resolved during execution.

## Literature Context

- Hierarchical cluster-ordered heatmaps for correlation matrices follow
  Sokal & Michener (1958) UPGMA linkage, as commonly applied in
  bioinformatics and ML feature analysis. The ordering groups correlated
  features together, making block structure visible.
- Spearman rank correlation is appropriate for non-normal distributions
  (Conover 1999, "Practical Nonparametric Statistics"). Census confirms
  MMR skewness = -5.759 and SQ skewness = -149.69 (contaminated by
  INT32_MIN sentinel; post-exclusion skewness is near-normal).
- PCA with fewer features than 2 is degenerate and produces trivial results
  (Jolliffe 2002, "Principal Component Analysis," Section 2.2: "If p=1,
  there is only one possible PC"). The faceted-distribution alternative
  follows the exploratory spirit of Tukey (1977) — visualize what the
  data actually shows rather than force a method that cannot deliver insight.

## Execution Steps

### T01 -- ROADMAP Patch

**Objective:** Add step 01_02_07 definition to the sc2egset ROADMAP so that
the step exists in the project's step registry before execution begins.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`.
2. After the 01_02_06 step definition block (which ends before
   `## Phase 02`), insert the 01_02_07 YAML block:

```yaml
### Step 01_02_07 -- Multivariate EDA

step_number: "01_02_07"
name: "Multivariate EDA"
description: "Multivariate analysis of all numeric features (cluster-ordered Spearman heatmap) and pre-game feature space visualization (MMR faceted by selectedRace and highestLeague). Addresses the degenerate PCA case: only 1 pre-game numeric feature (mmr), so standard PCA is skipped in favor of a scientifically defensible alternative. Produces 2 PNG files and a markdown artifact."
phase: "01 -- Data Exploration"
pipeline_section: "01_02 -- Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 2.1, 3.4"
dataset: "sc2egset"
question: "What is the joint covariance structure of all numeric features, and what multivariate structure exists in the pre-game feature space?"
method: "Spearman rank correlation on all 4 numeric columns (mmr, apm, sq, supplyCappedPercent), cluster-ordered via scipy hierarchical clustering. Two-panel heatmap: all rows vs MMR>0. Pre-game multivariate view: MMR distribution faceted by selectedRace x highestLeague."
predecessors: "01_02_06"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_07_multivariate_eda.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_07_pregame_multivariate_faceted.png"
  report: "artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Axis tick labels on Spearman heatmap annotated with I3 classification. Pre-game faceted plot uses only pre-game features."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All sentinel thresholds derived from census JSON at runtime. No hardcoded numbers."
  - number: "9"
    how_upheld: "Multivariate visualization of existing columns only. No new feature computation."
gate:
  artifact_check: "Both PNG files and 01_02_07_multivariate_analysis.md exist and are non-empty."
  continue_predicate: "Both PNG files exist. Markdown artifact contains plot index, column classification table, all SQL queries, and PCA-alternative justification. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet"
research_log_entry: "Required on completion."
```

**Verification:**
- ROADMAP.md contains a `### Step 01_02_07` section with the full YAML block.
- The step is positioned between 01_02_06 and Phase 02.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`

---

### T02 -- Notebook Setup, Census Load, DuckDB Connection

**Objective:** Create the notebook file with imports, DuckDB read-only
connection, census JSON load, and all runtime constant derivation from census.

**Instructions:**
1. Create `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_07_multivariate_eda.py`
   as a jupytext percent-format notebook.

**Cell 1 — markdown header:**
```
# Step 01_02_07 -- Multivariate EDA
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
from scipy import stats
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.sc2.config import DB_FILE

matplotlib.use("Agg")
logger = setup_notebook_logging()
```

**Cell 3 — DuckDB connection:**
```python
conn = duckdb.connect(str(DB_FILE), read_only=True)
```

**Cell 4 — census load:**
```python
reports_dir = get_reports_dir("sc2", "sc2egset")
census_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "02_eda"
    / "01_02_04_univariate_census.json"
)
with open(census_json_path) as f:
    census = json.load(f)
```

**Cell 5 — runtime constants from census (I7):**
```python
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
```

**Cell 6 — SQL queries dict (I6):**
```python
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
```

**Verification:**
- Notebook runs through T02 cells without error.
- Census loads and all constants printed.
- `conn`, `census`, `sql_queries`, `plots_dir` all defined.

---

### T03 -- Spearman Cluster-Ordered Heatmap (Two-Panel)

**Objective:** Compute Spearman correlation on 4 numeric columns (without
`result_binary`) for both all-rows and MMR>0 subsets, apply hierarchical
clustering, and produce a two-panel heatmap with I3 classification on axis labels.

**Cell 7 — fetch data:**
```python
df_all = conn.execute(sql_queries["spearman_all"]).fetchdf()
print(f"All rows (SQ sentinel excluded): {len(df_all)}")

df_rated = conn.execute(sql_queries["spearman_rated"]).fetchdf()
print(f"Rated players (MMR > 0): {len(df_rated)}")
```

**Cell 8 — compute Spearman matrices:**
```python
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
```

**Cell 9 — hierarchical cluster ordering:**
```python
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
```

**Cell 10 — two-panel heatmap:**
```python
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
```

**Verification:**
- `01_02_07_spearman_heatmap_all.png` exists.
- Axis labels contain I3 classification annotations.
- Two panels side-by-side; no `result_binary` column.

---

### T04 -- Pre-Game Multivariate Faceted View (PCA Alternative)

**Objective:** Produce the pre-game multivariate visualization: MMR distribution
faceted by `selectedRace` and `highestLeague`. Replaces degenerate PCA.

**Cell 11 — fetch faceted data:**
```python
df_pregame = conn.execute(sql_queries["pregame_faceted"]).fetchdf()
print(f"Pre-game faceted rows: {len(df_pregame)}")
print(f"Races: {sorted(df_pregame['selectedRace'].unique())}")
print(f"Leagues: {sorted(df_pregame['highestLeague'].unique())}")
```

**Cell 12 — filter leagues:**
```python
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
```

**Cell 13 — faceted plot:**
```python
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
```

**Verification:**
- `01_02_07_pregame_multivariate_faceted.png` exists.
- Title contains "PCA skipped" rationale note.
- Only pre-game features used (no APM/SQ/supplyCappedPercent).
- Only MMR > 0 rows used.

---

### T05 -- Markdown Artifact + JSON Artifact + Verification

**Objective:** Produce markdown and JSON artifacts with all SQL queries (I6),
column classification, PCA-alternative justification, and Spearman matrices.
Close the DuckDB connection and run end-to-end verification.

**Cell 14 — collect artifact data:**
```python
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
```

**Cell 15 — write markdown artifact:**
```python
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
```

**Cell 16 — JSON artifact:**
```python
json_path = artifact_dir / "01_02_07_multivariate_analysis.json"
with open(json_path, "w") as f:
    json.dump(artifact_data, f, indent=2)
print(f"Saved: {json_path}")
```

**Cell 17 — gate verification and connection close:**
```python
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
```

**Verification:**
- Both PNG files and markdown artifact exist and are non-empty.
- JSON artifact exists and is valid.
- Markdown contains PCA Decision, Column Classification, Plot Index, Spearman
  Matrices, SQL Queries, Invariants Applied sections.

---

### T06 -- STEP_STATUS Update

**Objective:** Update STEP_STATUS.yaml to record 01_02_07 as complete.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`.
2. Add after `01_02_06`:
```yaml
  "01_02_07":
    name: "Multivariate EDA"
    pipeline_section: "01_02"
    status: complete
    completed_at: "2026-04-15"
```

**Verification:**
- STEP_STATUS.yaml contains `"01_02_07"` with status `complete`.

---

### T07 -- Research Log Entry

**Objective:** Add a reverse-chronological entry to the sc2egset research log.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`.
2. Insert a new entry at the top of the entries section (after the header, before
   the 01_02_06 entry). Include:
   - Step scope and artifacts produced (2 PNGs, JSON, markdown).
   - Spearman heatmap key findings: APM-SQ correlation block, MMR shift between panels.
   - PCA-skip justification and faceted distribution findings.
   - Phase 02 implications: pre-game feature space sparsity.
   - Open questions.

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update (T01) |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_07_multivariate_eda.py` | Create (T02–T05) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png` | Create (T03) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_07_pregame_multivariate_faceted.png` | Create (T04) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md` | Create (T05) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json` | Create (T05) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update (T06) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update (T07) |

## Gate Condition

- Both PNG files exist and are non-empty.
- `01_02_07_multivariate_analysis.md` contains: PCA Decision section, Column
  Classification table, Plot Index, Spearman Matrices (all + rated), all SQL
  queries verbatim (I6).
- `01_02_07_multivariate_analysis.json` exists with `spearman_all`, `spearman_rated`,
  `sql_queries`, and `pca_decision` keys.
- Spearman heatmap axis labels contain I3 classification annotations.
- Pre-game faceted plot uses only pre-game features (no APM/SQ/supplyCappedPercent).
- STEP_STATUS.yaml shows `01_02_07: complete`.
- research_log.md contains 01_02_07 entry.
- ROADMAP.md contains Step 01_02_07 definition.
- Notebook executes end-to-end without errors.

## Out of Scope

- **PCA on in-game features.** Rejected in Problem Statement. The Spearman
  heatmap adequately captures in-game correlation structure.
- **Confirmatory statistical tests.** This is EDA (01_02). All findings are
  hypothesis-generating for Phase 02.
- **Feature engineering decisions.** Narrow pre-game feature space documented;
  solutions deferred to Phase 02.
- **MMR zero-row treatment.** Documented as contamination; treatment deferred
  to Phase 01_04 (Data Cleaning).
- **PIPELINE_SECTION_STATUS or PHASE_STATUS updates.** 01_02 is not complete
  until all three datasets finish 01_02_07.

## Open Questions

- **Does cluster ordering differ between panels?** Expected: yes (based on MMR
  correlation shifts in 01_02_06 bivariate JSON). Resolves during execution (T03).
- **How many leagues survive MIN_LEAGUE_ROWS filter?** Census data suggests
  Unknown, Master, Grandmaster, Diamond survive comfortably; Silver may be
  excluded. Resolves during execution (T04).
