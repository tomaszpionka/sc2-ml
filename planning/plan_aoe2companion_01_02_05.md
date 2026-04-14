---
category: A
branch: feat/aoe2companion-01-02-05-viz
date: 2026-04-14
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [6, 7, 9]
source_artifacts:
  - sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: null
---

# Plan: aoe2companion 01_02_05 -- Univariate Census Visualizations

## Scope

New Step 01_02_05 notebook containing all visualizations for the aoe2companion univariate census. This notebook reads the JSON artifact from 01_02_04 and queries the DuckDB for histogram bin data. Every plot cell is preceded by a pandas verification cell printing the exact data being plotted. Chart types are chosen based on 01_02_04 findings.

Phase 01, Pipeline Section 01_02 (EDA), Step 01_02_05 (new).

## Problem Statement

The 01_02_04 notebook was split into analytics-only (pass 2) and visualization (this plan). Visualization is a distinct step because plots are secondary artifacts -- they illustrate findings already established by the quantitative analysis. Separating them keeps the analytics notebook lean and makes the visualization notebook independently re-runnable (it reads the JSON artifact, not the raw queries).

The 12 plots cover: target variable distribution, intra-match consistency, categorical distributions (leaderboard, civ, map), numeric distributions (rating, ratingDiff, leaderboards_raw boxplots), completeness matrix (NULL rates bar chart), profiles_raw dead-field bar, leaderboards_raw.leaderboard top-k, and boolean column stacked bars.

## Assumptions & unknowns

- **Assumption:** The 01_02_04 pass 2 JSON artifact contains all required keys before this notebook runs. This notebook depends on T10 of the 01_02_04 pass 2 plan.
- **Assumption:** `matches_raw_null_census`, `won_distribution`, `won_consistency_2row`, `categorical_profiles`, `boolean_census`, `matches_raw_numeric_stats`, `leaderboards_raw_numeric_stats`, `leaderboards_raw_categorical`, `profiles_raw_null_census`, `constant_fields` keys exist in the JSON artifact.
- **Unknown:** The exact visual appearance of the completeness matrix at 55 columns width. May require adjusting figure size. Resolves by: execution.

## Literature context

EDA Manual Section 3.4 recommends histograms for shape assessment (sensitive to bin width), boxplots for comparing distributions, and bar charts for categorical distributions. Tukey (1977) championed visual methods as primary analytical tools, not decorative afterthoughts. The completeness matrix (NULL rate bar chart) follows the "feature completeness matrix" recommendation from EDA Manual Section 3.2.

Anscombe's Quartet (1973) permanently demonstrates why summary statistics without visualization are insufficient -- identical means, variances, and correlations can mask entirely different data structures. This is the core justification for a dedicated visualization step.

## Execution Steps

### T01 -- Create notebook boilerplate

**Objective:** Create the new notebook file with standard header, imports, DB connection, and JSON artifact loading.

**Instructions:**

1. Create file `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py` with jupytext header.

2. Standard header markdown cell, then imports:
   ```python
   import json
   from pathlib import Path
   import matplotlib
   import matplotlib.pyplot as plt
   import numpy as np
   import pandas as pd
   from rts_predict.common.notebook_utils import (
       get_notebook_db, get_reports_dir, setup_notebook_logging,
   )

   logger = setup_notebook_logging()
   matplotlib.use("Agg")
   plt.style.use("seaborn-v0_8-whitegrid")
   ```

3. Connection cell:
   ```python
   db = get_notebook_db("aoe2", "aoe2companion")
   con = db.con
   print("Connected to aoe2companion DuckDB (read-only)")
   ```

4. Artifact directory setup:
   ```python
   reports_dir = get_reports_dir("aoe2", "aoe2companion")
   artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
   artifacts_dir.mkdir(parents=True, exist_ok=True)
   ```

5. JSON artifact loading:
   ```python
   census_json_path = artifacts_dir / "01_02_04_univariate_census.json"
   with open(census_json_path) as f:
       census = json.load(f)
   print(f"Loaded 01_02_04 artifact: {len(census)} keys")
   print(f"Keys: {sorted(census.keys())}")
   ```

**Verification:**
- File exists and has valid jupytext header.
- JSON loading cell prints the key count.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T02 -- Plot 1: won distribution bar chart

**Objective:** Bar chart of won value distribution with exact NULL count annotation.

**Instructions:**

1. Verification cell:
   ```python
   won_dist = pd.DataFrame(census["won_distribution"])
   print("=== won_dist (feeds bar chart) ===")
   print(won_dist.to_string(index=False))
   ```

2. Plot cell: vertical bar chart with count and pct annotations for TRUE, FALSE, NULL.
   Color scheme: TRUE=green (#2ecc71), FALSE=red (#e74c3c), NULL=gray (#95a5a6).
   Save as `artifacts_dir / "01_02_05_won_distribution.png"`.

**Verification:**
- PNG file exists at expected path.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T03 -- Plot 2: Intra-match consistency stacked bar

**Objective:** Stacked bar showing intra-match won consistency categories for 2-player matches. This chart visualizes the inconsistent label finding from the 01_02_04 notebook. The annotation percentage must be computed dynamically from census data — do not hardcode.

**Instructions:**

1. Verification cell:
   ```python
   consistency = pd.DataFrame(census["won_consistency_2row"])
   print("=== won_consistency_2row (feeds stacked bar) ===")
   print(consistency.to_string(index=False))
   ```

2. Plot cell: single horizontal stacked bar with categories:
   - consistent_complement (one TRUE, one FALSE) -- green
   - both_true -- orange
   - both_false -- orange
   - both_null -- gray
   - one_true_one_null -- yellow
   - one_false_one_null -- yellow

3. Annotate with percentage labels for each segment. Compute percentages dynamically from the loaded census data — do NOT hardcode any percentage values.

4. Compute the inconsistency annotation dynamically:
   ```python
   consistency = pd.DataFrame(census["won_consistency_2row"])
   total_rows = consistency["count"].sum()
   inconsistent_count = consistency.loc[
       consistency["category"].isin(["both_true", "both_false"]), "count"
   ].sum()
   inconsistent_pct = 100.0 * inconsistent_count / total_rows
   annotation = (
       f"~{inconsistent_pct:.2f}% of 2-player matches have both_true or both_false "
       f"won labels (empirical noise floor on prediction target accuracy).\n"
       f"Note: this counts only both_true+both_false; other inconsistent categories "
       f"(one_true_one_null, etc.) are shown but not counted here."
   )
   ```
   Do NOT hardcode "10.98%" — this value refers only to both_true+both_false, not all
   inconsistent categories (all inconsistencies total ~11.44%). Derive from census.

5. Save as `artifacts_dir / "01_02_05_won_consistency.png"`.

**Verification:**
- PNG file exists.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T04 -- Plots 3-5: Leaderboard, Civ top-20, Map top-20 horizontal bars

**Objective:** Three horizontal bar charts for the major categorical columns.

**Instructions:**

1. For each of leaderboard (all values), civ (top 20), map (top 20):
   a. Verification cell: load from `census["categorical_profiles"]["<col>"]`,
      convert to DataFrame, print.
   b. Horizontal bar chart (barh). Sort by count descending (largest at top).
      Annotate bars with count values.

2. Generate three separate PNG files:
   - `artifacts_dir / "01_02_05_leaderboard_distribution.png"`
   - `artifacts_dir / "01_02_05_civ_top20.png"`
   - `artifacts_dir / "01_02_05_map_top20.png"`

**Verification:**
- Three PNG files exist at expected paths.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T05 -- Plots 6-7: rating and ratingDiff histograms

**Objective:** Histograms for matches_raw.rating and matches_raw.ratingDiff with non-NULL sample size annotations.

**Instructions:**

1. Query DuckDB for binned histogram data:
   ```sql
   SELECT (FLOOR(rating / 100) * 100)::INTEGER AS bin, COUNT(*) AS cnt
   FROM matches_raw WHERE rating IS NOT NULL
   GROUP BY bin ORDER BY bin
   ```

2. Verification cell: print `rating_hist_df`.

3. Plot with annotation showing non-NULL count, total count, and NULL pct.
   Title: `matches_raw.rating (N=<non_null> non-NULL of <total> total, <null_pct>% NULL excluded)`.
   Save as `artifacts_dir / "01_02_05_rating_histogram.png"`.

4. Repeat for ratingDiff (binned by 10):
   ```sql
   SELECT (FLOOR("ratingDiff" / 10) * 10)::INTEGER AS bin, COUNT(*) AS cnt
   FROM matches_raw WHERE "ratingDiff" IS NOT NULL
   GROUP BY bin ORDER BY bin
   ```
   Save as `artifacts_dir / "01_02_05_ratingDiff_histogram.png"`.

**Verification:**
- `01_02_05_rating_histogram.png` and `01_02_05_ratingDiff_histogram.png` exist.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T06 -- Plot 8: leaderboards_raw numeric boxplots

**Objective:** Boxplots for leaderboards_raw rank, rating, wins, losses, games with annotations for zero counts.

**Instructions:**

1. Verification cell: load `census["leaderboards_raw_numeric_stats"]` into DataFrame, print.

2. Plot: use `ax.bxp()` with p05/p25/median_val/p75/p95 from the numeric stats (these are
   the whiskers and box bounds). The center line is `median_val` — the field is named
   `median_val` in the `leaderboards_raw_numeric_stats` artifact, NOT `p50`. Using `p50`
   will cause a KeyError at execution time.

3. Annotate each boxplot with the zero count from `census["leaderboards_raw_zero_counts"]`.

4. Save as `artifacts_dir / "01_02_05_leaderboards_boxplots.png"`.

**Verification:**
- `01_02_05_leaderboards_boxplots.png` exists.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T07 -- Plot 9: Completeness matrix (NULL rate bar chart for 55 matches_raw columns)

**Objective:** Horizontal bar chart of NULL percentages for all 55 matches_raw columns, sorted descending, color-coded by severity.

**Instructions:**

1. Verification cell:
   ```python
   null_df = pd.DataFrame(census["matches_raw_null_census"])
   print(f"=== matches_raw NULL rates ({len(null_df)} columns) ===")
   print(null_df.sort_values("null_pct", ascending=False).to_string(index=False))
   ```

2. Plot:
   ```python
   null_df = null_df.sort_values("null_pct", ascending=True)
   colors = []
   for pct in null_df["null_pct"]:
       if pct < 1:
           colors.append("#2ecc71")   # green: < 1%
       elif pct < 10:
           colors.append("#f39c12")   # orange: 1-10%
       else:
           colors.append("#e74c3c")   # red: > 10%

   fig, ax = plt.subplots(figsize=(12, 16))
   ax.barh(null_df["column_name"], null_df["null_pct"], color=colors)
   ax.set_xlabel("NULL %")
   ax.set_title("matches_raw: Column NULL Rates (55 columns)")
   ax.axvline(x=1, color="gray", linestyle="--", alpha=0.5, label="1%")
   ax.axvline(x=10, color="gray", linestyle=":", alpha=0.5, label="10%")
   ax.legend()
   plt.tight_layout()
   plt.savefig(artifacts_dir / "01_02_05_completeness_matrix.png", dpi=150)
   plt.close()
   ```

**Verification:**
- `01_02_05_completeness_matrix.png` exists and shows 55 bars.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T08 -- Plot 10: profiles_raw NULL rates

**Objective:** Bar chart distinguishing 100% NULL (dead) columns from others in profiles_raw.

**Instructions:**

1. Verification cell: load `census["profiles_raw_null_census"]` into DataFrame, print.

2. Plot: horizontal bars. Color dead columns (null_pct >= 100) in red, others in blue.
   Annotate dead bars with "DEAD" label.

3. Save as `artifacts_dir / "01_02_05_profiles_null_rates.png"`.

**Verification:**
- `01_02_05_profiles_null_rates.png` exists.
- 7 bars colored red (dead fields).

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T09 -- Plot 11: leaderboards_raw.leaderboard top-k

**Objective:** Horizontal bar chart of all leaderboard values from leaderboards_raw.

**Instructions:**

1. Verification cell: load `census["leaderboards_raw_categorical"]["leaderboard"]`, print.

2. Horizontal bar chart (same pattern as T04). Save as
   `artifacts_dir / "01_02_05_lb_leaderboard_distribution.png"`.

**Verification:**
- `01_02_05_lb_leaderboard_distribution.png` exists.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T10 -- Plot 12: Boolean columns stacked bar

**Objective:** Stacked bar chart showing TRUE/FALSE/NULL proportions for all matches_raw boolean columns.

**Instructions:**

1. Verification cell:
   ```python
   bool_df = pd.DataFrame(census["boolean_census"])
   print(f"=== boolean_census ({len(bool_df)} columns) ===")
   print(bool_df.to_string(index=False))
   ```

2. Plot:
   ```python
   total = census["matches_raw_total_rows"]
   bool_df["true_pct"] = 100.0 * bool_df["true_count"] / total
   bool_df["false_pct"] = 100.0 * bool_df["false_count"] / total
   bool_df["null_pct_calc"] = 100.0 * bool_df["null_count"] / total

   fig, ax = plt.subplots(figsize=(12, 8))
   y = range(len(bool_df))
   ax.barh(y, bool_df["true_pct"], color="#2ecc71", label="TRUE")
   ax.barh(y, bool_df["false_pct"], left=bool_df["true_pct"],
           color="#e74c3c", label="FALSE")
   ax.barh(y, bool_df["null_pct_calc"],
           left=bool_df["true_pct"] + bool_df["false_pct"],
           color="#95a5a6", label="NULL")
   ax.set_yticks(list(y))
   ax.set_yticklabels(bool_df["column_name"])
   ax.set_xlabel("Percentage")
   ax.set_title("Boolean Column Proportions -- matches_raw")
   ax.legend(loc="lower right")
   plt.tight_layout()
   plt.savefig(artifacts_dir / "01_02_05_boolean_stacked.png", dpi=150)
   plt.close()
   ```

**Verification:**
- `01_02_05_boolean_stacked.png` exists with 18 bars.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T11 -- Write markdown summary artifact and close

**Objective:** Write a markdown artifact listing all plots with their paths and a brief caption. Close the DB connection.

**Instructions:**

1. Build a markdown string with one section per plot (number, title, filename, one-sentence caption based on execution output).

2. Per Invariant #6 (reproducibility), add a "SQL Queries" section to the markdown
   artifact that lists verbatim the DuckDB SQL queries used in T05 (rating and
   ratingDiff histograms), since those plots derive from direct DuckDB queries rather
   than the JSON artifact. These queries must appear in the markdown so the plots can
   be reproduced from scratch.

3. Write to `artifacts_dir / "01_02_05_visualizations.md"`.

4. Close DB connection: `con.close()`.

5. Print summary of all plot files produced.

6. Execute notebook with 1800s timeout (aoe2companion has 277M rows):
   ```bash
   source .venv/bin/activate && poetry run jupytext --execute \
       sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py \
       --to notebook \
       --output sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.ipynb \
       --ExecutePreprocessor.timeout=1800
   ```

**Verification:**
- `01_02_05_visualizations.md` exists and lists all 12 PNG files.
- `.ipynb` file is created.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md`

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py` | Create |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.ipynb` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_won_distribution.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_won_consistency.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_leaderboard_distribution.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_civ_top20.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_map_top20.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_rating_histogram.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_ratingDiff_histogram.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_leaderboards_boxplots.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_completeness_matrix.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_profiles_null_rates.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_lb_leaderboard_distribution.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_05_boolean_stacked.png` | Create |

## Gate Condition

- All 12 PNG files exist in the artifacts directory.
- `01_02_05_visualizations.md` exists and references all 12 PNGs.
- Every plot cell has a preceding pandas verification cell.
- Notebook executes end-to-end without errors (timeout=1800s).
- No DuckDB writes (read-only notebook).

## Out of scope

- Quantitative analytics (all in 01_02_04).
- Bivariate or multivariate plots (Pipeline Section 01_03+).
- Research log entries (deferred until notebooks polished).
- STEP_STATUS.yaml update (deferred -- parent session responsibility).
- ROADMAP.md update with 01_02_05 step definition (parent session responsibility).

## Open questions

- Whether the leaderboards_raw_categorical key will exist at execution time depends on 01_02_04 pass 2 completing first. Execution ordering: 01_02_04 pass 2 first, then 01_02_05.

## Deferred Debt

| Item | Target Step | Rationale |
|------|-------------|-----------|
| Bivariate plots (won by leaderboard, rating by civ) | 01_03+ | Bivariate analysis out of scope for univariate step |
| KDE / QQ plots | 01_03+ | More informative when comparing groups |
| Intra-match consistency root cause | 01_04 | Cleaning step; investigation deferred |
