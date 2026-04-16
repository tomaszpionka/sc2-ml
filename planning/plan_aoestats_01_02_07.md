---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: aoestats
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
source_artifacts:
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
  - "src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml"
  - "src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml"
  - "planning/plan_aoestats_01_02_06.md"
  - "temp/01_02_roadmap_finalization.md"
critique_required: true
research_log_ref: "src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md#2026-04-15-01-02-07-multivariate-eda"
---

# Plan: aoestats Step 01_02_07 -- Multivariate EDA

## Scope

**Phase/Step:** 01 / 01_02_07
**Branch:** feat/census-pass3
**Action:** CREATE (step does not yet exist in ROADMAP; must be added as T01)
**Predecessor:** 01_02_06 (Bivariate EDA -- complete, artifacts on disk)

Create a multivariate EDA notebook that produces three thesis-grade analyses:
(A) Spearman cluster-ordered heatmap of all numeric columns across both tables,
(B) PCA scree plot of pre-game features only, (C) PCA biplot (PC1 vs PC2) with
winner colouring. 3 PNG plots + 1 markdown artifact with all SQL queries
(Invariant #6). This is the final 01_02 sub-step; after completion, pipeline
section 01_02 is complete for aoestats.

## Problem Statement

Steps 01_02_04/05 (univariate) and 01_02_06 (bivariate) established per-column
distributions and pairwise relationships. Two multivariate questions remain
before pipeline section 01_02 can close:

1. **Cross-table correlation structure.** The bivariate Spearman matrices in
   01_02_06 were computed separately for matches_raw and players_raw. The
   full inter-table correlation picture (e.g., old_rating from players_raw vs
   avg_elo from matches_raw) has not been established. A single heatmap of all
   numeric columns, with I3 temporal annotations on the axis labels, provides
   the definitive correlation summary for the thesis methodology chapter.

2. **Feature redundancy and dimensionality.** Five pre-game features are
   candidates for Phase 02 feature engineering: old_rating, match_rating_diff
   (confirmed PRE_GAME in 01_02_06), avg_elo, team_0_elo, team_1_elo. PCA
   scree + biplot quantifies how much variance is concentrated in the first
   few components and whether features cluster (suggesting redundancy). This
   directly informs Phase 02 feature selection.

The aoestats dataset is large (matches_raw: 30.7M rows, players_raw: 107.6M
rows). All multivariate analyses must use RESERVOIR sampling to stay within
memory. The two tables must be joined on game_id to produce a single row with
columns from both tables, which is computationally expensive -- a 20,000-row
RESERVOIR sample at the SQL level keeps this tractable (RESERVOIR guarantees an
exact row count, unlike BERNOULLI which is probabilistic).

## Assumptions & Unknowns

- **Assumption:** The census JSON at `01_02_04_univariate_census.json` is the
  single source of truth for all runtime constants (row counts, NULL rates,
  ELO sentinel values). No magic numbers.
- **Assumption:** `match_rating_diff` is PRE_GAME per the 01_02_06 artifact
  (Pearson r=0.053 vs new_rating-old_rating). It is included in the PCA
  feature set.
- **Assumption:** The 87%-NULL columns (feudal_age_uptime, castle_age_uptime,
  imperial_age_uptime, opening) cannot contribute to PCA on the full dataset
  because their coverage is only ~13%. They are included in the Spearman
  heatmap (pairwise complete observations via pandas .corr(method='spearman'))
  but excluded from PCA.
- **Assumption:** `winner` in players_raw is BOOLEAN. For PCA biplot
  colouring, it is cast to INTEGER (1=True, 0=False).
- **Assumption:** Duration in DuckDB is BIGINT nanoseconds per the schema
  YAML. Conversion to seconds: `duration / 1e9`.
- **Assumption:** ELO sentinel value is -1 (34 + 39 rows per census).
  Excluded via `!= -1` in SQL WHERE clauses.
- **Assumption:** scipy.stats.spearmanr matrix form uses LISTWISE deletion
  (not pairwise) when nan_policy='omit', which would reduce the effective
  sample from ~20,000 rows to ~1,700 rows due to the ~87%-NULL age_uptime
  columns. pandas .corr(method='spearman') is used instead, which performs
  true pairwise deletion (each column pair uses all rows where both columns
  are non-null). Minimum pairwise sample size is asserted >= 1,000 rows.

## Literature Context

Multivariate EDA follows the univariate-bivariate-multivariate progression
from Tukey (1977) as operationalized in 01_DATA_EXPLORATION_MANUAL.md,
Section 2.1. PCA (Jolliffe 2002) is used as a descriptive tool for
dimensionality assessment, not as a feature transformation for modelling.
Spearman rank correlation is preferred over Pearson because several features
have non-normal distributions (match_rating_diff kurtosis=65.7 per census)
and monotonic relationships are the primary interest.

The scree plot criterion (cumulative variance explained) and biplot
visualization follow the standard approach in Kaiser (1960) for component
retention assessment. No component retention decision is made in this step
(deferred to Phase 02 feature engineering).

## Execution Steps

### T01 -- ROADMAP Patch

**Objective:** Insert the Step 01_02_07 definition into ROADMAP.md so that
the step is registered before execution begins.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`.
2. Insert the following YAML block after the 01_02_06 block (before the
   `---` separator preceding Phase 02):

```yaml
step_number: "01_02_07"
name: "Multivariate EDA"
description: "Multivariate EDA for aoestats: Spearman cluster-ordered heatmap of all numeric columns across both tables (I3-annotated axis labels), PCA scree + biplot on pre-game numeric features. 3 plots + markdown artifact. All SQL embedded (Invariant #6). Sample-based (20K rows from cross-table JOIN). No cleaning or feature decisions (Invariant #9)."
phase: "01 -- Data Exploration"
pipeline_section: "01_02 -- Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
dataset: "aoestats"
question: "What is the full inter-table correlation structure among numeric columns? How much variance is concentrated in the first few principal components of pre-game features? Are any pre-game features redundant?"
method: "Cross-table JOIN on game_id with RESERVOIR sampling (20K rows). Spearman correlation via pandas .corr(method='spearman') with pairwise deletion. PCA via sklearn.decomposition.PCA with StandardScaler. All thresholds from census JSON."
stratification: "Cross-table (matches_raw JOIN players_raw on game_id)."
predecessors:
  - "01_02_06"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_07_multivariate_eda.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_07_pca_scree.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png"
  report: "artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "new_rating and duration annotated POST-GAME* on heatmap axis labels. age uptime columns annotated IN-GAME*. match_rating_diff annotated PRE-GAME (resolved in 01_02_06). POST-GAME columns excluded from PCA feature set."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "Sample size (TARGET_SAMPLE_ROWS=20000) justified by cross-table JOIN cost on 30M+107M row tables. ELO sentinel value (-1) from census. All NULL rate thresholds from census JSON."
  - number: "9"
    how_upheld: "Multivariate analysis only. No model fitting, no feature engineering, no cleaning decisions. PCA is descriptive — no component retention decision."
gate:
  artifact_check: "All 3 PNG files exist under plots/. 01_02_07_multivariate_analysis.md exists and is non-empty."
  continue_predicate: "All 3 PNG files exist. Markdown artifact contains all SQL queries and plot index table with Temporal Annotation column. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

**Verification:**
- The ROADMAP.md contains a `step_number: "01_02_07"` block.
- The block appears after 01_02_06 and before the Phase 02 placeholder.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`

---

### T02 -- Notebook Setup, Census Load, DuckDB Connection

**Objective:** Create the jupytext-paired notebook with header, imports,
DuckDB read-only connection, census JSON load, and validation of required
census keys. Establish the `sql_queries` dict and `multivariate_results`
dict that accumulate throughout the notebook.

**Cell 1 — markdown header:**
```markdown
# Step 01_02_07 -- Multivariate EDA: aoestats

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
**Dataset:** aoestats
**Question:** What is the full inter-table correlation structure? How much
variance is concentrated in the first few principal components of pre-game features?
**Invariants applied:**
- #3 (temporal discipline -- POST-GAME and IN-GAME columns annotated on heatmap)
- #6 (reproducibility -- all SQL stored verbatim in markdown artifact)
- #7 (no magic numbers -- all thresholds from census JSON; sample size justified)
- #9 (step scope: multivariate analysis only -- no cleaning or feature decisions)
**Predecessor:** 01_02_06 (Bivariate EDA -- complete, artifacts on disk)
**Step scope:** multivariate EDA only -- visualization + dimensionality assessment.
No cleaning decisions, no feature engineering, no model fitting.
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
from scipy import stats as sp_stats
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOESTATS_DB_FILE

matplotlib.use("Agg")
logger = setup_notebook_logging(__name__)
```

**Cell 3 — DuckDB connection:**
```python
conn = duckdb.connect(str(AOESTATS_DB_FILE), read_only=True)
```

**Cell 4 — paths and census load:**
```python
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
```

**Cell 5 — validation:**
```python
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
```

**Cell 6 — accumulators:**
```python
sql_queries = {}
multivariate_results = {
    "step": "01_02_07",
    "dataset": "aoestats",
}
```

**Cell 7 — constants (all I7-justified):**
```python
# I7: Sample size justified by cross-table JOIN cost.
# matches_raw has 30M+ rows; players_raw has 107M+ rows.
# A 20K reservoir sample keeps memory and wall time tractable.
# SE(rho) ~ 0.007 for rho=0 at N=20K — well below any substantive threshold.
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
```

**Verification:**
- Notebook runs through T02 cells without error.
- Census keys validated. `match_rating_diff` PRE_GAME assertion passes.
- `conn`, `census`, `bivariate`, `sql_queries`, `multivariate_results` all defined.

---

### T03 -- Spearman Cluster-Ordered Heatmap (Analysis A)

**Objective:** Produce a single Spearman correlation heatmap of all numeric
columns from both matches_raw and players_raw, with I3 temporal annotations
on axis tick labels.

**Cell 8 — markdown section:**
```markdown
## Analysis A -- Spearman Cluster-Ordered Heatmap (All Numeric Columns)
```

**Cell 9 — SQL query:**
```python
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
```

**Cell 10 — fetch and validate:**
```python
df_spearman = conn.execute(sql_spearman_sample).fetchdf()
print(f"Spearman sample: {len(df_spearman)} rows, {df_spearman.shape[1]} columns")
print(f"Non-null counts:\n{df_spearman.notna().sum()}")
```

**Cell 11 — compute Spearman matrix:**
```python
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
```

**Cell 12 — I3 labels and cluster ordering:**
```python
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
```

**Cell 13 — plot:**
```python
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
```

**Cell 14 — store results:**
```python
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
```

**Verification:**
- `01_02_07_spearman_heatmap_all.png` exists and is non-empty.
- Axis labels include POST-GAME* and IN-GAME* annotations (Invariant #3).
- Sample size logged in `multivariate_results`.

---

### T04 -- PCA Scree Plot (Analysis B, Part 1)

**Objective:** Compute PCA on pre-game numeric features only and produce a
scree plot showing variance explained per component plus cumulative.

**Cell 15 — markdown section:**
```markdown
## Analysis B -- PCA on Pre-Game Features

Feature set: old_rating, match_rating_diff, avg_elo, team_0_elo, team_1_elo
Excluded: new_rating (POST-GAME), duration_sec (POST-GAME), age uptime columns
(IN-GAME and 87% NULL -- insufficient complete-case coverage for PCA).

Invariant #3: POST-GAME and IN-GAME columns must not be used for pre-game
prediction. PCA is descriptive only -- no component retention decision is
made here (deferred to Phase 02 feature engineering). Invariant #9.
```

**Cell 16 — SQL query:**
```python
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
```

**Cell 17 — fetch and validate:**
```python
df_pca = conn.execute(sql_pca_sample).fetchdf()
print(f"PCA sample: {len(df_pca)} rows")
print(f"Null counts:\n{df_pca[PCA_FEATURES].isna().sum()}")
assert df_pca[PCA_FEATURES].isna().sum().sum() == 0, "PCA features must have no NULLs"
```

**Cell 18 — scale and fit PCA:**
```python
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
```

**Cell 19 — scree plot:**
```python
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
    label="conventional reference line (not a retention criterion — see Phase 02)",
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
```

**Cell 20 — store results:**
```python
multivariate_results["pca_scree"] = {
    "features": PCA_FEATURES,
    "sample_size": len(df_pca),
    "n_components": n_comp,
    "variance_explained": [round(float(v), 6) for v in var_explained],
    "cumulative_variance": [round(float(c), 6) for c in cum_var],
    "scaler_means": [round(float(m), 4) for m in scaler.mean_],
    "scaler_stds": [round(float(s), 4) for s in scaler.scale_],
}
```

**Verification:**
- `01_02_07_pca_scree.png` exists and is non-empty.
- No NaN values in PCA features.
- Cumulative variance sums to 1.0 (within floating point tolerance).
- All 5 components shown.

---

### T05 -- PCA Biplot (Analysis B, Part 2)

**Objective:** Produce a biplot of PC1 vs PC2 with loading vectors labelled
by feature name and scatter of sampled rows coloured by winner.

**Cell 21 — compute loadings:**
```python
loadings = pca.components_.T  # shape: (n_features, n_components)
```

**Cell 22 — biplot:**
```python
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
```

**Cell 23 — store loadings:**
```python
multivariate_results["pca_biplot"] = {
    "loadings": {
        feature: {
            f"PC{j+1}": round(float(loadings[i, j]), 6)
            for j in range(loadings.shape[1])
        }
        for i, feature in enumerate(PCA_FEATURES)
    },
}
```

**Verification:**
- `01_02_07_pca_biplot.png` exists and is non-empty.
- Loading vectors labelled with feature names.
- Scatter coloured by winner with colorbar legend.
- PC1 and PC2 variance percentages in axis labels.

---

### T06 -- Markdown Artifact + JSON Artifact + Verification

**Objective:** Write the markdown artifact (plot index, column classification,
SQL queries per I6, PCA summary) and JSON artifact. Close the DuckDB connection.

**Cell 24 — markdown section:**
```markdown
## Artifacts
```

**Cell 25 — JSON artifact:**
```python
json_path = artifacts_dir / "01_02_07_multivariate_analysis.json"
with open(json_path, "w") as f:
    json.dump(multivariate_results, f, indent=2)
print(f"JSON artifact written: {json_path}")
```

**Cell 26 — markdown artifact:**
```python
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
    "`01_02_07_spearman_heatmap_all.png` | Mixed — POST-GAME* and IN-GAME* annotated on axis |",
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
```

**Cell 27 — gate verification:**
```python
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
```

**Cell 28 — close connection:**
```python
conn.close()
```

**Verification:**
- All 3 PNG files exist and non-empty.
- `01_02_07_multivariate_analysis.md` contains plot index, column classification,
  PCA summary, and all SQL queries.
- `01_02_07_multivariate_analysis.json` exists with `spearman_heatmap` and `pca_scree` keys.
- All SQL query names present in markdown text.

---

### T07 -- STEP_STATUS Update + Research Log

**Objective:** Register step completion and write a research log entry.

**Instructions:**
1. Add entry to `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`:
   ```yaml
     "01_02_07":
       name: "Multivariate EDA"
       pipeline_section: "01_02"
       status: complete
       completed_at: "2026-04-15"
   ```

2. Prepend a new entry to
   `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`
   after the header block, before the 01_02_06 entry. Entry must include:
   - Step scope and artifacts produced (3 PNGs, JSON, markdown)
   - Spearman heatmap findings: strongest cross-table correlations observed
     (avg_elo / team_0_elo / team_1_elo cluster; match_rating_diff near-zero
     correlation with ELO features)
   - PCA variance concentration findings: how many components reach 95%,
     whether ELO features are near-redundant
   - Biplot observations: whether winner separates in PC space
   - Decisions: column classification confirmed for thesis methodology chapter

**Verification:**
- STEP_STATUS.yaml contains `"01_02_07"` with status `complete`.
- research_log.md has new entry for 01_02_07 at the top (after header).

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update (T01) |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_07_multivariate_eda.py` | Create (T02–T06) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png` | Create (T03) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_scree.png` | Create (T04) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png` | Create (T05) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json` | Create (T06) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md` | Create (T06) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | Update (T07) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update (T07) |

## Gate Condition

- All 3 PNG files exist under `reports/artifacts/01_exploration/02_eda/plots/` and are non-empty.
- `01_02_07_multivariate_analysis.md` contains: plot index (3 entries), column
  classification table (10 columns), PCA summary table, and all SQL queries (I6).
- `01_02_07_multivariate_analysis.json` exists with `spearman_heatmap` and `pca_scree` keys.
- Spearman heatmap axis labels include POST-GAME* and IN-GAME* annotations (I3).
- PCA biplot coloured by winner with axis labels showing variance percentages.
- Notebook executes end-to-end without errors.
- STEP_STATUS.yaml shows `01_02_07: complete`.

## Out of Scope

- **Component retention decision.** PCA is descriptive only; deferred to Phase 02.
- **Feature cleaning.** No rows dropped or imputed. 87%-NULL columns included in
  Spearman (pairwise deletion) but excluded from PCA. No cleaning threshold decisions.
- **Model fitting.** Visualisation and dimensionality assessment only (I9).
- **irl_duration.** Excluded from heatmap (Spearman rho=1.0 with duration per 01_02_06).
- **Cross-game comparison.** Deferred to Phase 06.

## Open Questions

- **Q1: Spearman NaN handling (RESOLVED).** scipy.stats.spearmanr matrix form uses
  LISTWISE deletion, not pairwise, which would reduce the effective sample by ~10x
  when ~87%-NULL age_uptime columns are included. Resolved by switching to pandas
  .corr(method='spearman') (pairwise deletion by default). Minimum pairwise N
  assertion guards against degenerate column pairs.
- **Q2: PCA variance concentration.** If PC1 explains >95% of variance (plausible
  given near-perfect avg_elo / team_0/1_elo correlation), the scree will show extreme
  concentration. This is an expected finding informing Phase 02 feature selection.
  Resolves by: observation during execution.
