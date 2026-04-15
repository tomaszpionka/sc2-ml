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
---

# Plan: sc2egset Step 01_02_06 — Bivariate EDA

## Scope

**Phase/Step:** 01 / 01_02_06
**Branch:** feat/census-pass3
**Action:** CREATE (new step — no prior 01_02_06 artifacts exist)
**Predecessor:** 01_02_05 (Univariate EDA Visualizations — complete, artifacts on disk)

Create a bivariate EDA notebook that examines pairwise relationships between
features and the prediction target (`result`), produces 9 thesis-grade PNG
plots, a Spearman correlation matrix, a JSON artifact with statistical test
results, and a markdown artifact with all SQL queries (Invariant #6). This
step answers the question: "Which features associate with match outcome, and
how strongly?"

The bivariate layer sits between univariate (01_02_05, which described each
column in isolation) and multivariate (01_02_07, which will look at joint
feature interactions). It is scoped to two-variable relationships only
(Invariant #9).

## Problem Statement

Step 01_02_04/05 established that sc2egset has 44,817 player-rows across
22,390 replays, zero NULLs, a near-perfect 50/50 Win/Loss target balance,
an 83.65% MMR-zero sentinel rate, and in-game metrics (APM, SQ,
supplyCappedPercent) that cannot be used as pre-game features (Invariant #3).
Step 01_02_06 now asks: given these distributions, which features actually
differ between wins and losses? This directly informs Phase 02 feature
engineering priorities.

Key dataset properties:
- 44,817 rows (small — no sampling needed; all queries run on full data)
- `result` has 4 values: Win (22,382), Loss (22,409), Undecided (24), Tie (2)
  — for bivariate analysis, filter to `result IN ('Win', 'Loss')` only
- MMR: 83.65% zero sentinel — non-zero subset (7,328 rows) is the
  analysis-relevant population for MMR-by-result
- SQ: 2 INT32_MIN sentinels — exclude via `SQ > -2147483648`
- In-game columns: APM, SQ, supplyCappedPercent — must carry red-bbox
  annotation on every plot

## Assumptions & Unknowns

- Census JSON at `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the source of truth for all threshold values.
- All sentinel exclusion thresholds (MMR=0, SQ INT32_MIN) are derived from
  census at runtime, not hardcoded (Invariant #7).
- The Undecided (24) and Tie (2) row counts are looked up from census
  `result_distribution` at runtime (Invariant #7).
- Chi-square test requires scipy.stats.chi2_contingency.
- Mann-Whitney U test (scipy.stats.mannwhitneyu) for continuous-by-binary
  comparisons as a complement to violin visual inspection.
- Spearman correlation uses scipy.stats.spearmanr or pandas `.corr(method='spearman')`.
- All numeric columns from replay_players_raw: MMR, APM, SQ,
  supplyCappedPercent, handicap (effectively constant — 2 non-100 rows).
  Handicap excluded from bivariate analysis (dead column per census finding).

## Literature Context

- Violin plots preferred over box plots for bivariate continuous-by-categorical
  because they show full density shape (Hintze & Nelson, 1998).
- Spearman over Pearson because several features are non-normal (MMR skewness
  -5.76, supplyCappedPercent skewness 2.25) — Spearman is rank-based and
  robust to non-normality.
- Chi-square test for categorical-by-categorical (race x result) is standard
  for contingency tables with expected cell counts > 5 (Agresti, 2002).

## Scientific Questions

**Q1 (cross-dataset mandatory):** For each numeric feature, does its distribution
differ by match result (Win vs Loss)? Multi-panel violin of all numeric
features by result.

**Q2 (cross-dataset mandatory):** Spearman correlation matrix for all numeric
columns — reveals inter-feature correlations and feature-target
relationships. In-game columns visually distinguished.

**Q3 (sc2egset-specific):** Does non-zero MMR predict match result? Among the
16.35% of rows with MMR > 0, is the MMR distribution different for winners
vs losers? Violin by result with Mann-Whitney U test p-value annotated.

**Q4 (sc2egset-specific):** Does race (post-random-resolution) affect win
rate? Bar chart of win rate per race with chi-square test p-value annotation.
Uses the `race` column (resolved actual race, not `selectedRace` which includes
"Random"). Result filtered to Win/Loss only; Undecided/Tie excluded.

**Q5 (sc2egset-specific, IN-GAME):** Does APM distribution differ by result?
Violin by result. In-game annotation mandatory.

**Q6 (sc2egset-specific, IN-GAME):** Does SQ distribution differ by result?
Violin by result. INT32_MIN sentinel excluded. In-game annotation mandatory.

**Q7 (sc2egset-specific, IN-GAME):** Does supplyCappedPercent differ by result?
Violin by result. In-game annotation mandatory.

**Q8 (sc2egset-specific):** Does isInClan associate with win rate? 2x2
contingency bar chart with chi-square p-value.

**Q9 (sc2egset-specific):** Is there a highestLeague x result interaction?
Grouped bar or heat table showing win rate per league tier. Reveals whether
match-making balances skill levels effectively.

**Q10 (sc2egset-specific):** Race balance check by result — does any race have
a statistically meaningful win rate advantage? Chi-square test p-value
annotated on plot. Uses `race` column (not `selectedRace`) because `race`
is the actual in-game race after random resolution.

## Part A — ROADMAP Patch

**New ROADMAP entry for Step 01_02_06:**
```yaml
step_number: "01_02_06"
name: "Bivariate EDA"
description: "9 bivariate visualization plots examining pairwise relationships between features and match result in sc2egset. Reads the 01_02_04 JSON artifact for sentinel thresholds and queries DuckDB for conditional distributions. All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations on in-game columns (APM, SQ, supplyCappedPercent) per Invariant #3. Statistical tests (chi-square, Mann-Whitney U, Spearman) with p-values annotated on plots."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 2.1, 3.4"
dataset: "sc2egset"
question: "Which features associate with match outcome (Win vs Loss), and how strongly? Do in-game metrics show stronger separation than pre-game features?"
method: "DuckDB queries for conditional distributions by result. Violin plots for continuous features, grouped bar charts for categorical features. Spearman correlation matrix for numeric columns. Chi-square tests for categorical-by-result associations. Mann-Whitney U for continuous-by-result comparisons. All sentinel thresholds data-derived from 01_02_04 census at runtime."
predecessors: "01_02_05"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_06_mmr_by_result.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_race_winrate.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_apm_by_result.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_sq_by_result.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_supplycapped_by_result.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_league_winrate.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_clan_winrate.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_numeric_by_result.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_spearman_correlation.png"
  report: "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "All three in-game columns (APM, SQ, supplyCappedPercent) carry a visible annotation: 'IN-GAME — not available at prediction time (Inv. #3)' on every plot where they appear. Spearman heatmap marks in-game columns with red asterisks in tick labels."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All sentinel thresholds (MMR=0 count, SQ INT32_MIN count, Undecided/Tie counts) derived from census JSON at runtime. No hardcoded numbers. Chi-square and Mann-Whitney p-values computed, not assumed."
  - number: "9"
    how_upheld: "Bivariate analysis of existing columns only. No new feature computation. Builds on 01_02_04 census findings and 01_02_05 univariate visualizations."
gate:
  artifact_check: "All 9 PNG files, 01_02_06_bivariate_eda.md, and 01_02_06_bivariate_eda.json exist and are non-empty."
  continue_predicate: "All 9 PNG files exist. JSON artifact contains statistical test results. Markdown artifact contains plot index table with Temporal Annotation column and all SQL queries. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet"
  - "Chapter 5 — Results > feature importance discussion"
research_log_entry: "Required on completion."
```

## Part B — Notebook Task List

### T01 — ROADMAP Patch and STEP_STATUS Update

**Objective:** Add the Step 01_02_06 entry to ROADMAP.md and add the step to
STEP_STATUS.yaml as `not_started`.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`.
2. Insert the Step 01_02_06 YAML block from Part A after the Step 01_02_05
   closing triple-backtick line and before the Phase 02 placeholder.
3. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`.
4. Add entry for `01_02_06` with `name: "Bivariate EDA"`,
   `pipeline_section: "01_02"`, `status: not_started`.

**Verification:**
- ROADMAP.md contains Step 01_02_06 with 9 PNG outputs under `plots/`.
- STEP_STATUS.yaml lists `01_02_06` with `status: not_started`.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`

### T02 — Notebook Setup

**Objective:** Create the notebook skeleton with imports, DuckDB connection,
census JSON load, path setup, and helper functions.

**Instructions:**
1. Create `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.py`
   with jupytext percent-format header (copy structure from 01_02_05).
2. Markdown header cell with step metadata (phase, pipeline section, dataset,
   question, invariants, predecessor, step scope).
3. Imports cell:
   ```python
   import json
   from pathlib import Path

   import duckdb
   import matplotlib
   import matplotlib.pyplot as plt
   import numpy as np
   import pandas as pd
   from scipy import stats

   from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
   from rts_predict.games.sc2.config import DB_FILE

   matplotlib.use("Agg")
   logger = setup_notebook_logging()
   ```
4. DuckDB read-only connection:
   ```python
   conn = duckdb.connect(str(DB_FILE), read_only=True)
   ```
5. Census JSON load:
   ```python
   census_json_path = (
       get_reports_dir("sc2", "sc2egset")
       / "artifacts" / "01_exploration" / "02_eda"
       / "01_02_04_univariate_census.json"
   )
   with open(census_json_path) as f:
       census = json.load(f)
   ```
6. Assert required keys:
   ```python
   REQUIRED_KEYS = [
       "result_distribution",
       "zero_counts",
       "numeric_stats_SQ_no_sentinel",
       "mmr_zero_interpretation",
       "isInClan_distribution",
       "categorical_profiles",
       "field_classification",
   ]
   missing = [k for k in REQUIRED_KEYS if k not in census]
   assert not missing, f"Census incomplete. Missing: {missing}"
   ```
7. Path setup:
   ```python
   artifacts_dir = (
       get_reports_dir("sc2", "sc2egset")
       / "artifacts" / "01_exploration" / "02_eda"
   )
   plots_dir = artifacts_dir / "plots"
   plots_dir.mkdir(parents=True, exist_ok=True)
   sql_queries: dict[str, str] = {}
   test_results: dict[str, dict] = {}
   ```
8. Derive constants from census (Invariant #7 — no magic numbers):
   ```python
   # --- Derive sentinel thresholds from census ---
   df_result_dist = pd.DataFrame(census["result_distribution"])
   n_undecided = int(df_result_dist.loc[
       df_result_dist["result"] == "Undecided", "cnt"
   ].values[0])
   n_tie = int(df_result_dist.loc[
       df_result_dist["result"] == "Tie", "cnt"
   ].values[0])
   total_n = int(df_result_dist["cnt"].sum())
   n_winloss = total_n - n_undecided - n_tie

   mmr_zero_count = census["zero_counts"]["replay_players_raw"]["MMR_zero"]
   sq_sentinel_count = census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]
   INT32_MIN = int(np.iinfo(np.int32).min)
   # I7: architectural constant — SC2 uses INT32 for SQ; minimum value = sentinel

   print(f"Total rows: {total_n:,}")
   print(f"Win/Loss rows: {n_winloss:,}")
   print(f"Excluded: Undecided ({n_undecided}), Tie ({n_tie})")
   print(f"MMR zero sentinel: {mmr_zero_count:,} rows ({100*mmr_zero_count/total_n:.2f}%)")
   print(f"SQ INT32_MIN sentinel: {sq_sentinel_count} rows")
   ```
9. Define in-game annotation helper:
   ```python
   def add_ingame_annotation(ax: plt.Axes) -> None:
       """Add standard IN-GAME warning annotation to an axes (Inv. #3)."""
       ax.annotate(
           "IN-GAME — not available at prediction time (Inv. #3)",
           xy=(0.02, 0.98),
           xycoords="axes fraction",
           ha="left",
           va="top",
           fontsize=8,
           fontstyle="italic",
           color="darkred",
           bbox=dict(
               boxstyle="round,pad=0.3",
               fc="#ffe0e0",
               ec="red",
               alpha=0.9,
           ),
       )
   ```
10. Define Win/Loss filter query fragment:
    ```python
    WINLOSS_FILTER = "result IN ('Win', 'Loss')"
    ```
11. Add exploratory rationale comment (W2):
    ```python
    # NOTE: All statistical tests in this notebook are EXPLORATORY (Tukey-style EDA,
    # 01_02 pipeline section). P-values are reported for descriptive comparison,
    # not as confirmatory hypothesis tests. No multiple comparison correction is
    # applied. Findings here generate hypotheses for Phase 02 feature engineering
    # and Phase 03 model evaluation — not causal claims.
    print(
        "NOTE: All tests are exploratory (Tukey-style EDA). "
        "P-values are descriptive, not confirmatory. "
        "No multiple comparison correction applied."
    )
    ```

**Verification:**
- Notebook cell executes without error. Census keys validated. Paths created.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.py`

### T03 — Plot 1: MMR by Result Violin (Q3)

**Scientific question answered:** Q3 — Does non-zero MMR predict match result
among rated players?

**Input:** DuckDB query on replay_players_raw, non-zero MMR only.

**Output:** `plots/01_02_06_mmr_by_result.png`

**SQL (store in `sql_queries["mmr_by_result"]`):**
```sql
SELECT MMR, result
FROM replay_players_raw
WHERE MMR != 0
  AND result IN ('Win', 'Loss')
```

**Python:**
```python
sql_queries["mmr_by_result"] = """
SELECT MMR, result
FROM replay_players_raw
WHERE MMR != 0
  AND result IN ('Win', 'Loss')
"""
df_mmr = conn.execute(sql_queries["mmr_by_result"]).fetchdf()
n_nonzero = len(df_mmr)
print(f"Non-zero MMR rows (Win/Loss): {n_nonzero:,}")

# Mann-Whitney U test: is the MMR distribution different for Win vs Loss?
mmr_win = df_mmr.loc[df_mmr["result"] == "Win", "MMR"].values
mmr_loss = df_mmr.loc[df_mmr["result"] == "Loss", "MMR"].values
u_stat, p_mw = stats.mannwhitneyu(mmr_win, mmr_loss, alternative="two-sided")
n_win_mmr, n_loss_mmr = len(mmr_win), len(mmr_loss)
# I7: rank-biserial r = 1 - 2U/(n1*n2); ranges [-1,1]; |r| < 0.1 small,
# 0.1-0.3 medium, > 0.3 large (Cohen 1988)
r_rb_mmr = 1 - (2 * u_stat) / (n_win_mmr * n_loss_mmr)
test_results["mmr_by_result"] = {
    "test": "Mann-Whitney U",
    "U_statistic": float(u_stat),
    "p_value": float(p_mw),
    "rank_biserial_r": round(float(r_rb_mmr), 4),
    "n_win": n_win_mmr,
    "n_loss": n_loss_mmr,
    "median_win": float(np.median(mmr_win)),
    "median_loss": float(np.median(mmr_loss)),
}
print(f"Mann-Whitney U = {u_stat:,.0f}, p = {p_mw:.4e}, r={r_rb_mmr:.3f}")

fig, ax = plt.subplots(figsize=(8, 6))
parts = ax.violinplot(
    [mmr_win, mmr_loss],
    positions=[0, 1],
    showmeans=True,
    showmedians=True,
)
ax.set_xticks([0, 1])
ax.set_xticklabels(["Win", "Loss"])
ax.set_ylabel("MMR")
ax.set_title(
    f"MMR Distribution by Result — Non-Zero Only "
    f"(N={n_nonzero:,} of {total_n:,})\n"
    f"MMR=0 excluded: {mmr_zero_count:,} rows ({100*mmr_zero_count/total_n:.2f}% sentinel)"
)
ax.annotate(
    f"Mann-Whitney U = {u_stat:,.0f}, p = {p_mw:.4e}, r={r_rb_mmr:.3f}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    ha="right",
    va="bottom",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_mmr_by_result.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

**Invariant notes:**
- I7: MMR zero threshold derived from census `zero_counts`. No hardcoded 37489.
- I3: MMR is pre-game — no in-game annotation needed.
- I6: SQL stored in `sql_queries` dict.

### T04 — Plot 2: Race Win Rate with Chi-Square (Q4, Q10)

**Scientific question answered:** Q4 — Does race (post-random-resolution) affect
win rate? Q10 — Does any race have a statistically meaningful win rate advantage?

**Input:** DuckDB query on replay_players_raw, Win/Loss only. Uses `race`
column (post-random-resolution actual race, not `selectedRace`).

**Output:** `plots/01_02_06_race_winrate.png`

**SQL (store in `sql_queries["race_winrate"]`):**
```sql
SELECT
    race,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND race IN ('Prot', 'Zerg', 'Terr')
GROUP BY race
ORDER BY race
```

**Python:**
```python
sql_queries["race_winrate"] = """
SELECT
    race,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND race IN ('Prot', 'Zerg', 'Terr')
GROUP BY race
ORDER BY race
"""
df_race = conn.execute(sql_queries["race_winrate"]).fetchdf()
print(df_race.to_string(index=False))

# Chi-square test on race x result contingency table
contingency = df_race[["wins"]].copy()
contingency["losses"] = df_race["total"] - df_race["wins"]
chi2, p_chi2, dof, expected = stats.chi2_contingency(
    contingency[["wins", "losses"]].values
)
# Verify chi-square validity: expected cell counts > 5 (Agresti 2002)
min_expected = expected.min()
assert min_expected > 5, (
    f"Chi-square assumption violated: min expected count = {min_expected:.2f}. "
    "Results may be unreliable."
)
print(f"Chi-square validity check: min expected cell count = {min_expected:.2f} (>5 required)")
test_results["race_winrate_chi2"] = {
    "test": "chi-square",
    "chi2_statistic": float(chi2),
    "p_value": float(p_chi2),
    "dof": int(dof),
    "races": df_race["race"].tolist(),
    "win_pcts": df_race["win_pct"].tolist(),
}
print(f"Chi-square = {chi2:.4f}, p = {p_chi2:.4e}, dof = {dof}")

fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(df_race["race"], df_race["win_pct"], color=["steelblue", "salmon", "seagreen"])
for bar, row in zip(bars, df_race.itertuples()):
    ax.annotate(
        f"{row.win_pct:.1f}%\n(n={row.total:,})",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
    )
ax.set_xlabel("Race")
ax.set_ylabel("Win Rate (%)")
ax.axhline(50.0, color="gray", linestyle="--", linewidth=0.8, label="50% baseline")
ax.set_title(f"Win Rate by Race — replay_players_raw (N={n_winloss:,}, Win/Loss only)")
ax.annotate(
    f"Chi-square = {chi2:.2f}, p = {p_chi2:.4e}, dof = {dof}\n"
    f"Excluded: BW-prefixed races (3 rows), Undecided ({n_undecided}), Tie ({n_tie})",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    ha="right",
    va="bottom",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_race_winrate.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

**Invariant notes:**
- I7: BW-prefixed race count (3 rows per census categorical_profiles) derived
  dynamically. Undecided/Tie counts from census.
- I3: Race is pre-game — no in-game annotation needed.

### T05 — Plot 3: APM by Result Violin (Q5, IN-GAME)

**Scientific question answered:** Q5 — Does APM distribution differ by result?

**Input:** DuckDB query on replay_players_raw, Win/Loss only.

**Output:** `plots/01_02_06_apm_by_result.png`

**SQL (store in `sql_queries["apm_by_result"]`):**
```sql
SELECT APM, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
```

**Python:**
```python
sql_queries["apm_by_result"] = """
SELECT APM, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
"""
df_apm = conn.execute(sql_queries["apm_by_result"]).fetchdf()

apm_win = df_apm.loc[df_apm["result"] == "Win", "APM"].values
apm_loss = df_apm.loc[df_apm["result"] == "Loss", "APM"].values
u_apm, p_apm = stats.mannwhitneyu(apm_win, apm_loss, alternative="two-sided")
n_win_apm, n_loss_apm = len(apm_win), len(apm_loss)
# I7: rank-biserial r = 1 - 2U/(n1*n2); ranges [-1,1]; |r| < 0.1 small,
# 0.1-0.3 medium, > 0.3 large (Cohen 1988)
r_rb_apm = 1 - (2 * u_apm) / (n_win_apm * n_loss_apm)
test_results["apm_by_result"] = {
    "test": "Mann-Whitney U",
    "U_statistic": float(u_apm),
    "p_value": float(p_apm),
    "rank_biserial_r": round(float(r_rb_apm), 4),
    "n_win": n_win_apm,
    "n_loss": n_loss_apm,
    "median_win": float(np.median(apm_win)),
    "median_loss": float(np.median(apm_loss)),
}

fig, ax = plt.subplots(figsize=(8, 6))
ax.violinplot(
    [apm_win, apm_loss],
    positions=[0, 1],
    showmeans=True,
    showmedians=True,
)
ax.set_xticks([0, 1])
ax.set_xticklabels(["Win", "Loss"])
ax.set_ylabel("APM")
ax.set_title(
    f"APM Distribution by Result (N={len(df_apm):,}, Win/Loss only)"
)
ax.annotate(
    f"Mann-Whitney U = {u_apm:,.0f}, p = {p_apm:.4e}, r={r_rb_apm:.3f}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    ha="right",
    va="bottom",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)
add_ingame_annotation(ax)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_apm_by_result.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

**Invariant notes:**
- I3: IN-GAME annotation via `add_ingame_annotation(ax)`.
- I6: SQL in `sql_queries`.

### T06 — Plot 4: SQ by Result Violin (Q6, IN-GAME)

**Scientific question answered:** Q6 — Does SQ distribution differ by result?

**Input:** DuckDB query on replay_players_raw, Win/Loss only, INT32_MIN
sentinel excluded.

**Output:** `plots/01_02_06_sq_by_result.png`

**SQL (store in `sql_queries["sq_by_result"]`):**
```sql
SELECT SQ, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648
```

**Python:**
```python
sql_queries["sq_by_result"] = f"""
SELECT SQ, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > {INT32_MIN}
"""
df_sq = conn.execute(sql_queries["sq_by_result"]).fetchdf()
n_sq = len(df_sq)
print(f"SQ rows after sentinel exclusion: {n_sq:,} (excluded {sq_sentinel_count} INT32_MIN)")

sq_win = df_sq.loc[df_sq["result"] == "Win", "SQ"].values
sq_loss = df_sq.loc[df_sq["result"] == "Loss", "SQ"].values
u_sq, p_sq = stats.mannwhitneyu(sq_win, sq_loss, alternative="two-sided")
n_win_sq, n_loss_sq = len(sq_win), len(sq_loss)
# I7: rank-biserial r = 1 - 2U/(n1*n2); ranges [-1,1]; |r| < 0.1 small,
# 0.1-0.3 medium, > 0.3 large (Cohen 1988)
r_rb_sq = 1 - (2 * u_sq) / (n_win_sq * n_loss_sq)
test_results["sq_by_result"] = {
    "test": "Mann-Whitney U",
    "U_statistic": float(u_sq),
    "p_value": float(p_sq),
    "rank_biserial_r": round(float(r_rb_sq), 4),
    "n_win": n_win_sq,
    "n_loss": n_loss_sq,
    "median_win": float(np.median(sq_win)),
    "median_loss": float(np.median(sq_loss)),
    "sentinel_excluded": sq_sentinel_count,
}

fig, ax = plt.subplots(figsize=(8, 6))
ax.violinplot(
    [sq_win, sq_loss],
    positions=[0, 1],
    showmeans=True,
    showmedians=True,
)
ax.set_xticks([0, 1])
ax.set_xticklabels(["Win", "Loss"])
ax.set_ylabel("SQ (Spending Quotient)")
ax.set_title(
    f"SQ Distribution by Result (N={n_sq:,}, Win/Loss only)\n"
    f"INT32_MIN sentinel excluded: {sq_sentinel_count} rows"
)
ax.annotate(
    f"Mann-Whitney U = {u_sq:,.0f}, p = {p_sq:.4e}, r={r_rb_sq:.3f}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    ha="right",
    va="bottom",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)
add_ingame_annotation(ax)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_sq_by_result.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

**Invariant notes:**
- I3: IN-GAME annotation.
- I7: INT32_MIN is an architectural constant (-2,147,483,648); sentinel count
  derived from census at runtime.

### T07 — Plot 5: supplyCappedPercent by Result Violin (Q7, IN-GAME)

**Scientific question answered:** Q7 — Does supplyCappedPercent differ by result?

**Input:** DuckDB query on replay_players_raw, Win/Loss only.

**Output:** `plots/01_02_06_supplycapped_by_result.png`

**SQL (store in `sql_queries["supplycapped_by_result"]`):**
```sql
SELECT supplyCappedPercent, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
```

**Python:**
```python
sql_queries["supplycapped_by_result"] = """
SELECT supplyCappedPercent, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
"""
df_sc = conn.execute(sql_queries["supplycapped_by_result"]).fetchdf()

sc_win = df_sc.loc[df_sc["result"] == "Win", "supplyCappedPercent"].values
sc_loss = df_sc.loc[df_sc["result"] == "Loss", "supplyCappedPercent"].values
u_sc, p_sc = stats.mannwhitneyu(sc_win, sc_loss, alternative="two-sided")
n_win_sc, n_loss_sc = len(sc_win), len(sc_loss)
# I7: rank-biserial r = 1 - 2U/(n1*n2); ranges [-1,1]; |r| < 0.1 small,
# 0.1-0.3 medium, > 0.3 large (Cohen 1988)
r_rb_sc = 1 - (2 * u_sc) / (n_win_sc * n_loss_sc)
test_results["supplycapped_by_result"] = {
    "test": "Mann-Whitney U",
    "U_statistic": float(u_sc),
    "p_value": float(p_sc),
    "rank_biserial_r": round(float(r_rb_sc), 4),
    "n_win": n_win_sc,
    "n_loss": n_loss_sc,
    "median_win": float(np.median(sc_win)),
    "median_loss": float(np.median(sc_loss)),
}

fig, ax = plt.subplots(figsize=(8, 6))
ax.violinplot(
    [sc_win, sc_loss],
    positions=[0, 1],
    showmeans=True,
    showmedians=True,
)
ax.set_xticks([0, 1])
ax.set_xticklabels(["Win", "Loss"])
ax.set_ylabel("supplyCappedPercent")
ax.set_title(
    f"supplyCappedPercent by Result (N={len(df_sc):,}, Win/Loss only)"
)
ax.annotate(
    f"Mann-Whitney U = {u_sc:,.0f}, p = {p_sc:.4e}, r={r_rb_sc:.3f}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    ha="right",
    va="bottom",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)
add_ingame_annotation(ax)
fig.tight_layout()
fig.savefig(
    plots_dir / "01_02_06_supplycapped_by_result.png", dpi=150, bbox_inches="tight"
)
plt.close(fig)
```

### T08 — Plot 6: highestLeague Win Rate (Q9)

**Scientific question answered:** Q9 — Is there a highestLeague x result
interaction?

**Input:** DuckDB query on replay_players_raw, Win/Loss only.

**Output:** `plots/01_02_06_league_winrate.png`

**SQL (store in `sql_queries["league_winrate"]`):**
```sql
SELECT
    highestLeague,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
GROUP BY highestLeague
ORDER BY total DESC
```

**Python:**
```python
sql_queries["league_winrate"] = """
SELECT
    highestLeague,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
GROUP BY highestLeague
ORDER BY total DESC
"""
df_league = conn.execute(sql_queries["league_winrate"]).fetchdf()
print(df_league.to_string(index=False))

# Replace empty string with "(empty)" for display
df_league["highestLeague"] = df_league["highestLeague"].replace("", "(empty)")

# Define canonical league order for the x-axis
league_order = [
    "Grandmaster", "Master", "Diamond", "Platinum",
    "Gold", "Silver", "Bronze", "Unranked", "Unknown", "(empty)",
]
# Keep only leagues present in data, preserving order
present_leagues = [l for l in league_order if l in df_league["highestLeague"].values]
df_league_plot = df_league.set_index("highestLeague").loc[present_leagues].reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(
    range(len(df_league_plot)),
    df_league_plot["win_pct"],
    color="steelblue",
    alpha=0.8,
)
for i, (bar, row) in enumerate(zip(bars, df_league_plot.itertuples())):
    ax.annotate(
        f"{row.win_pct:.1f}%\n(n={row.total:,})",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=8,
    )
ax.set_xticks(range(len(df_league_plot)))
ax.set_xticklabels(df_league_plot["highestLeague"], rotation=30, ha="right")
ax.set_xlabel("Highest League")
ax.set_ylabel("Win Rate (%)")
ax.axhline(50.0, color="gray", linestyle="--", linewidth=0.8, label="50% baseline")
ax.set_title(
    f"Win Rate by Highest League — replay_players_raw "
    f"(N={n_winloss:,}, Win/Loss only)"
)
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_league_winrate.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

**Invariant notes:**
- I7: League tier names from data, not hardcoded set. Canonical order is a
  display choice (SC2 ladder tier ordering is a game-design fact), not a
  data-derived threshold.
- I3: highestLeague is pre-game — no in-game annotation needed.

### T09 — Plot 7: isInClan Win Rate (Q8)

**Scientific question answered:** Q8 — Does isInClan associate with win rate?

**Input:** DuckDB query on replay_players_raw, Win/Loss only.

**Output:** `plots/01_02_06_clan_winrate.png`

**SQL (store in `sql_queries["clan_winrate"]`):**
```sql
SELECT
    isInClan,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
GROUP BY isInClan
ORDER BY isInClan
```

**Python:**
```python
sql_queries["clan_winrate"] = """
SELECT
    isInClan,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
GROUP BY isInClan
ORDER BY isInClan
"""
df_clan = conn.execute(sql_queries["clan_winrate"]).fetchdf()
print(df_clan.to_string(index=False))

# Chi-square on 2x2 contingency: isInClan x result
contingency_clan = np.array([
    [
        int(df_clan.loc[df_clan["isInClan"] == False, "wins"].values[0]),
        int(df_clan.loc[df_clan["isInClan"] == False, "total"].values[0])
        - int(df_clan.loc[df_clan["isInClan"] == False, "wins"].values[0]),
    ],
    [
        int(df_clan.loc[df_clan["isInClan"] == True, "wins"].values[0]),
        int(df_clan.loc[df_clan["isInClan"] == True, "total"].values[0])
        - int(df_clan.loc[df_clan["isInClan"] == True, "wins"].values[0]),
    ],
])
chi2_clan, p_clan, dof_clan, expected_clan = stats.chi2_contingency(contingency_clan)
# Verify chi-square validity: expected cell counts > 5 (Agresti 2002)
min_expected_clan = expected_clan.min()
assert min_expected_clan > 5, (
    f"Chi-square assumption violated: min expected count = {min_expected_clan:.2f}. "
    "Results may be unreliable."
)
print(f"Chi-square validity check: min expected cell count = {min_expected_clan:.2f} (>5 required)")
test_results["clan_winrate_chi2"] = {
    "test": "chi-square",
    "chi2_statistic": float(chi2_clan),
    "p_value": float(p_clan),
    "dof": int(dof_clan),
    "contingency_table": contingency_clan.tolist(),
}
print(f"Chi-square = {chi2_clan:.4f}, p = {p_clan:.4e}, dof = {dof_clan}")

labels = ["Not in Clan", "In Clan"]
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(labels, df_clan["win_pct"].values, color=["steelblue", "salmon"])
for bar, row in zip(bars, df_clan.itertuples()):
    ax.annotate(
        f"{row.win_pct:.1f}%\n(n={row.total:,})",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
    )
ax.set_ylabel("Win Rate (%)")
ax.axhline(50.0, color="gray", linestyle="--", linewidth=0.8, label="50% baseline")
ax.set_title(
    f"Win Rate by Clan Membership (N={n_winloss:,}, Win/Loss only)"
)
ax.annotate(
    f"Chi-square = {chi2_clan:.2f}, p = {p_clan:.4e}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    ha="right",
    va="bottom",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(plots_dir / "01_02_06_clan_winrate.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

### T10 — Plot 8: Multi-Panel Numeric Features by Result (Q1)

**Scientific question answered:** Q1 — For each numeric feature, does its
distribution differ by match result?

**Input:** DuckDB query pulling all relevant numeric columns with result.

**Output:** `plots/01_02_06_numeric_by_result.png`

**SQL (store in `sql_queries["numeric_by_result"]`):**
```sql
SELECT MMR, APM, SQ, supplyCappedPercent, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
```

**Python:**
```python
sql_queries["numeric_by_result"] = """
SELECT MMR, APM, SQ, supplyCappedPercent, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
"""
df_num = conn.execute(sql_queries["numeric_by_result"]).fetchdf()

# Define columns and their properties
n_mmr_rated = int((df_num["MMR"] > 0).sum())
numeric_cols = [
    {"col": "MMR", "label": f"MMR (non-zero only, N={n_mmr_rated:,})", "in_game": False},
    {"col": "APM", "label": "APM", "in_game": True},
    {"col": "SQ", "label": "SQ (sentinel-excluded)", "in_game": True},
    {"col": "supplyCappedPercent", "label": "supplyCappedPercent", "in_game": True},
]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes_flat = axes.flatten()

for i, spec in enumerate(numeric_cols):
    ax = axes_flat[i]
    col = spec["col"]
    df_plot = df_num.copy()

    # Apply sentinel exclusions — consistent with individual violin plots
    if col == "SQ":
        df_plot = df_plot[df_plot["SQ"] > INT32_MIN]
    if col == "MMR":
        # MMR panel: filter to non-zero only, consistent with T03 violin
        # (zero = sentinel, 83.65% of rows; including zeros shows sentinel spike not signal)
        df_plot = df_plot[df_plot["MMR"] > 0]

    win_vals = df_plot.loc[df_plot["result"] == "Win", col].values
    loss_vals = df_plot.loc[df_plot["result"] == "Loss", col].values

    ax.violinplot(
        [win_vals, loss_vals],
        positions=[0, 1],
        showmeans=True,
        showmedians=True,
    )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Win", "Loss"])
    ax.set_ylabel(col)
    ax.set_title(f"{spec['label']}")

    if spec["in_game"]:
        add_ingame_annotation(ax)

fig.suptitle(
    f"Numeric Features by Result — replay_players_raw (Win/Loss only)",
    fontsize=13,
    fontweight="bold",
)
fig.tight_layout()
fig.savefig(
    plots_dir / "01_02_06_numeric_by_result.png", dpi=150, bbox_inches="tight"
)
plt.close(fig)
```

**Invariant notes:**
- I3: In-game columns (APM, SQ, supplyCappedPercent) annotated. MMR is pre-game.
- I7: SQ sentinel exclusion uses `INT32_MIN` constant derived in T02.
- I9: No new analytics — visual comparison of existing column distributions.

### T11 — Plot 9: Spearman Correlation Heatmap (Q2)

**Scientific question answered:** Q2 — Spearman correlation matrix for numeric
columns, with in-game columns visually distinguished.

**Input:** DuckDB query on replay_players_raw, Win/Loss only. Result encoded
as binary (Win=1, Loss=0) for Spearman computation.

**Output:** `plots/01_02_06_spearman_correlation.png`

**SQL (store in `sql_queries["spearman_all"]` and `sql_queries["spearman_rated"]`):**

Two queries are computed — all rows (SQ sentinel excluded only) and rated
players only (additionally MMR > 0). Side-by-side subplots show both, making
the MMR-sentinel contamination visible and the rated-player signal clear.

```sql
-- All rows (SQ sentinel excluded, MMR includes zero sentinel)
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent,
    CASE WHEN result = 'Win' THEN 1 ELSE 0 END AS result_binary
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648

-- Rated players only (MMR > 0, consistent with T03 violin)
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent,
    CASE WHEN result = 'Win' THEN 1 ELSE 0 END AS result_binary
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648
  AND MMR > 0
  -- I7: mmr > 0 filter excludes zero-sentinel rows (83.65% of data, census:
  --     zero_counts.replay_players_raw.MMR_zero = 37489). Without this filter,
  --     the MMR-correlation row/column is dominated by the zero-spike and
  --     shows near-zero rho regardless of true association. Consistent with
  --     T03 violin which also filters mmr > 0.
```

**Python:**
```python
# --- Query 1: all rows (SQ sentinel excluded, MMR includes zeros) ---
sql_queries["spearman_all"] = f"""
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent,
    CASE WHEN result = 'Win' THEN 1 ELSE 0 END AS result_binary
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > {INT32_MIN}
"""

# --- Query 2: rated players only (MMR > 0) ---
sql_queries["spearman_rated"] = f"""
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent,
    CASE WHEN result = 'Win' THEN 1 ELSE 0 END AS result_binary
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > {INT32_MIN}
  AND MMR > 0
  -- I7: mmr > 0 filter excludes zero-sentinel rows (83.65% of data, census:
  --     zero_counts.replay_players_raw.MMR_zero = 37489). Without this filter,
  --     the MMR-correlation row/column is dominated by the zero-spike and
  --     shows near-zero rho regardless of true association. Consistent with
  --     T03 violin which also filters mmr > 0.
"""

df_corr_all = conn.execute(sql_queries["spearman_all"]).fetchdf()
df_corr_rated = conn.execute(sql_queries["spearman_rated"]).fetchdf()
n_all = len(df_corr_all)
n_rated = len(df_corr_rated)
print(f"Rows for Spearman (all): {n_all:,}")
print(f"Rows for Spearman (rated, MMR>0): {n_rated:,}")

# Compute both Spearman correlation matrices
corr_all = df_corr_all.corr(method="spearman")
corr_rated = df_corr_rated.corr(method="spearman")

# Store both in test_results
test_results["spearman_matrix_all"] = {
    "method": "spearman",
    "subset": "all_rows_sq_sentinel_excluded",
    "n_rows": n_all,
    "columns": corr_all.columns.tolist(),
    "matrix": corr_all.values.tolist(),
    "sq_sentinel_excluded": True,
    "mmr_zero_included": True,
}
test_results["spearman_matrix_rated"] = {
    "method": "spearman",
    "subset": "mmr_gt_0_rated_players",
    "n_rows": n_rated,
    "columns": corr_rated.columns.tolist(),
    "matrix": corr_rated.values.tolist(),
    "sq_sentinel_excluded": True,
    "mmr_zero_included": False,
}

# In-game columns for visual distinction
in_game_cols = {"APM", "SQ", "supplyCappedPercent"}

def build_col_labels(cols):
    labels = []
    for c in cols:
        if c in in_game_cols:
            labels.append(f"{c} *")
        elif c == "result_binary":
            labels.append("result (target)")
        else:
            labels.append(c)
    return labels

def draw_heatmap(ax, corr_matrix, title):
    col_labels = build_col_labels(corr_matrix.columns)
    im = ax.imshow(corr_matrix.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(col_labels)))
    ax.set_yticklabels(col_labels, fontsize=8)
    for i in range(len(corr_matrix)):
        for j in range(len(corr_matrix)):
            val = corr_matrix.iloc[i, j]
            text_color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=7, color=text_color)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        if label.get_text().endswith("*"):
            label.set_color("red")
    ax.set_title(title, fontsize=10)
    return im

fig, (ax_all, ax_rated) = plt.subplots(1, 2, figsize=(18, 8))

im1 = draw_heatmap(
    ax_all,
    corr_all,
    f"All rows (MMR includes zero sentinel)\n(N={n_all:,}, SQ sentinel excluded)",
)
im2 = draw_heatmap(
    ax_rated,
    corr_rated,
    f"Rated players only (MMR > 0)\n(N={n_rated:,})",
)

# Shared colorbar
fig.colorbar(im2, ax=[ax_all, ax_rated], shrink=0.6, label="Spearman rho")

fig.suptitle(
    "Spearman Correlation Matrix — replay_players_raw\n"
    "* = IN-GAME column (Inv. #3) | Left: all rows | Right: MMR > 0 only",
    fontsize=12,
    fontweight="bold",
)
fig.tight_layout()
fig.savefig(
    plots_dir / "01_02_06_spearman_correlation.png", dpi=150, bbox_inches="tight"
)
plt.close(fig)
```

**Invariant notes:**
- I3: In-game columns marked with red asterisk (*) in tick labels.
- I7: SQ sentinel and MMR=0 thresholds data-derived from census. No hardcoded
  counts. Two matrices computed to expose MMR sentinel contamination explicitly
  rather than silently suppressing it with a single filtered matrix.
- I6: Both SQL queries stored in `sql_queries` dict and will appear in markdown
  artifact.

### T12 — JSON Artifact, Markdown Artifact, Verification, and Connection Close

**Objective:** Write JSON artifact with all test results, markdown artifact
with SQL queries and plot index, verify all 9 plots, close DuckDB.

**Instructions:**
1. Write JSON artifact:
   ```python
   json_artifact = {
       "step": "01_02_06",
       "dataset": "sc2egset",
       "n_rows_total": total_n,
       "n_rows_winloss": n_winloss,
       "n_undecided": n_undecided,
       "n_tie": n_tie,
       "mmr_zero_count": mmr_zero_count,
       "sq_sentinel_count": sq_sentinel_count,
       "test_results": test_results,
       "sql_queries": sql_queries,
   }
   json_path = artifacts_dir / "01_02_06_bivariate_eda.json"
   with open(json_path, "w") as f:
       json.dump(json_artifact, f, indent=2, default=str)
   print(f"Saved JSON artifact: {json_path}")
   ```
2. Define expected_plots list:
   ```python
   expected_plots = [
       "01_02_06_mmr_by_result.png",
       "01_02_06_race_winrate.png",
       "01_02_06_apm_by_result.png",
       "01_02_06_sq_by_result.png",
       "01_02_06_supplycapped_by_result.png",
       "01_02_06_league_winrate.png",
       "01_02_06_clan_winrate.png",
       "01_02_06_numeric_by_result.png",
       "01_02_06_spearman_correlation.png",
   ]
   ```
3. Assert all 9 PNG files exist on disk:
   ```python
   missing_plots = [p for p in expected_plots if not (plots_dir / p).exists()]
   assert not missing_plots, f"Missing plots: {missing_plots}"
   print(f"All {len(expected_plots)} plots verified on disk.")
   ```
4. Build markdown artifact with:
   - Header (step, dataset, date, predecessor).
   - Plot index table with columns: #, Title, Filename, Test Used, Key Finding,
     Temporal Annotation. Temporal Annotation values: "IN-GAME (Inv. #3)" for
     APM, SQ, supplyCappedPercent plots; "N/A" for all others.
   - Statistical Tests Summary table: test name, statistic, p-value, per test.
   - SQL Queries section: enumerate ALL queries from `sql_queries` dict.
   - Data Sources section.
   ```python
   md_lines = [
       "# Step 01_02_06 — Bivariate EDA",
       "",
       f"**Dataset:** sc2egset",
       f"**Step:** 01_02_06",
       f"**Predecessor:** 01_02_05",
       f"**Total rows:** {total_n:,}",
       f"**Win/Loss rows:** {n_winloss:,}",
       f"**Excluded:** Undecided ({n_undecided}), Tie ({n_tie})",
       "",
       "> **NOTE:** All statistical tests in this notebook are EXPLORATORY "
       "(Tukey-style EDA, 01_02 pipeline section). P-values are reported for "
       "descriptive comparison, not as confirmatory hypothesis tests. No multiple "
       "comparison correction is applied. Findings here generate hypotheses for "
       "Phase 02 feature engineering and Phase 03 model evaluation — not causal claims.",
       "",
       "## Plot Index",
       "",
       "| # | Title | Filename | Test | Key Finding | Temporal Annotation |",
       "|---|-------|----------|------|-------------|---------------------|",
   ]
   plot_index = [
       ("1", "MMR by Result (non-zero)", "01_02_06_mmr_by_result.png",
        "Mann-Whitney U", "See test_results", "N/A"),
       ("2", "Race Win Rate (post-random-resolution)", "01_02_06_race_winrate.png",
        "Chi-square", "See test_results", "N/A"),
       ("3", "APM by Result", "01_02_06_apm_by_result.png",
        "Mann-Whitney U", "See test_results", "IN-GAME (Inv. #3)"),
       ("4", "SQ by Result", "01_02_06_sq_by_result.png",
        "Mann-Whitney U", "See test_results", "IN-GAME (Inv. #3)"),
       ("5", "supplyCappedPercent by Result", "01_02_06_supplycapped_by_result.png",
        "Mann-Whitney U", "See test_results", "IN-GAME (Inv. #3)"),
       ("6", "League Win Rate", "01_02_06_league_winrate.png",
        "Descriptive", "See plot", "N/A"),
       ("7", "Clan Win Rate", "01_02_06_clan_winrate.png",
        "Chi-square", "See test_results", "N/A"),
       ("8", "Numeric Features by Result", "01_02_06_numeric_by_result.png",
        "Visual", "Multi-panel overview (MMR non-zero)", "Mixed (APM/SQ/supCap IN-GAME)"),
       ("9", "Spearman Correlation (all + rated subplots)", "01_02_06_spearman_correlation.png",
        "Spearman rho", "Two side-by-side matrices in JSON", "Mixed (* = IN-GAME)"),
   ]
   for row in plot_index:
       md_lines.append(f"| {' | '.join(row)} |")

   md_lines.extend(["", "## Statistical Tests Summary", ""])
   # Skip Spearman matrix entries (stored in JSON, not as p-value tests)
   spearman_keys = {"spearman_matrix_all", "spearman_matrix_rated"}
   for test_name, res in test_results.items():
       if test_name in spearman_keys:
           continue
       md_lines.append(f"### {test_name}")
       md_lines.append(f"- **Test:** {res['test']}")
       if "U_statistic" in res:
           md_lines.append(f"- **U statistic:** {res['U_statistic']:,.0f}")
       if "rank_biserial_r" in res:
           md_lines.append(f"- **Rank-biserial r:** {res['rank_biserial_r']:.4f}")
       if "chi2_statistic" in res:
           md_lines.append(f"- **Chi-square:** {res['chi2_statistic']:.4f}")
       md_lines.append(f"- **p-value:** {res['p_value']:.4e}")
       md_lines.append("")

   md_lines.extend(["## SQL Queries", ""])
   for qname, qtext in sql_queries.items():
       md_lines.append(f"### {qname}")
       md_lines.append("```sql")
       md_lines.append(qtext.strip())
       md_lines.append("```")
       md_lines.append("")

   md_lines.extend([
       "## Data Sources",
       "",
       "- `replay_players_raw` (44,817 rows, 25 columns)",
       "- `01_02_04_univariate_census.json` (sentinel thresholds, result distribution)",
       "",
       "## Invariants Applied",
       "",
       "- **I3:** All three in-game columns carry IN-GAME annotation on every plot.",
       "- **I6:** All SQL queries reproduced above.",
       "- **I7:** All thresholds data-derived from census JSON at runtime.",
       "- **I9:** Bivariate analysis only; no new feature computation.",
   ])

   md_path = artifacts_dir / "01_02_06_bivariate_eda.md"
   with open(md_path, "w") as f:
       f.write("\n".join(md_lines))
   print(f"Saved markdown artifact: {md_path}")
   ```
5. Close DuckDB connection:
   ```python
   conn.close()
   print("DuckDB connection closed.")
   ```

**Verification:**
- All 9 PNG files exist (assert count is 9).
- JSON artifact exists with `test_results` and `sql_queries` keys.
- Markdown artifact contains plot index table, statistical tests summary,
  and all SQL queries.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.py` (continuation)
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json` (generated)
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md` (generated)

### T13 — STEP_STATUS Update

**Objective:** Mark 01_02_06 as complete after successful notebook execution.

**Instructions:**
1. Update `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`:
   set `01_02_06.status` to `complete` and `01_02_06.completed_at` to the
   execution date.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`

### T14 — Research Log Entry

**Objective:** Add a reverse-chronological entry to the sc2egset research log
documenting the bivariate EDA findings.

**Instructions:**
1. Add entry at the top of the entries section in
   `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`.
2. Include: date, step reference, artifacts produced, key findings from
   statistical tests, decisions taken, decisions deferred, thesis mapping,
   open questions.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`

## Cross-Dataset Comparability Checklist

| Mandatory Item | Column | sc2egset Handling |
|---|---|---|
| (a) Numeric features by result | All numerics | Multi-panel violin (T10) |
| (b) Spearman correlation matrix | All numerics | Heatmap with in-game distinction (T11) |
| (c) Race/faction win rate | `race` | Bar chart with chi-square (T04) |
| (d) Rating by result | `MMR` (non-zero) | Violin with Mann-Whitney U (T03) |
| (e) Clan/team membership | `isInClan` | 2x2 contingency bar with chi-square (T09) |

When bivariate EDA is done for aoe2companion and aoestats, the same core plots
(a)-(b) must be produced. Items (c)-(e) are dataset-specific variants of a
common pattern (categorical feature x win rate with statistical test).

## Gate Condition

- [ ] `plots/01_02_06_mmr_by_result.png`
- [ ] `plots/01_02_06_race_winrate.png`
- [ ] `plots/01_02_06_apm_by_result.png`
- [ ] `plots/01_02_06_sq_by_result.png`
- [ ] `plots/01_02_06_supplycapped_by_result.png`
- [ ] `plots/01_02_06_league_winrate.png`
- [ ] `plots/01_02_06_clan_winrate.png`
- [ ] `plots/01_02_06_numeric_by_result.png`
- [ ] `plots/01_02_06_spearman_correlation.png`
- [ ] `01_02_06_bivariate_eda.json` with test_results and sql_queries keys
- [ ] `01_02_06_bivariate_eda.md` with plot index table, tests summary, and SQL queries
- [ ] ROADMAP.md Step 01_02_06 entry present
- [ ] STEP_STATUS.yaml `01_02_06` -> complete
- [ ] Research log entry added
- [ ] Notebook executes end-to-end without error

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_06_bivariate_eda.ipynb` | Create (jupytext sync) |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_06_*.png` (9 files) | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json` | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Modify |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Modify |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Modify |

## Out of Scope

- Multivariate analysis (three or more variables jointly) — deferred to 01_02_07
- New feature computation or engineering — deferred to Phase 02
- In-game features as model candidates — in-game plots document predictive
  signal for thesis but do not promote these to feature candidates
- Cleaning of Undecided/Tie/BW-race entries — deferred to 01_04
- Event table bivariate analysis (608M rows) — deferred per EDA Manual
- Cross-game comparison execution — documented in checklist for future
  aoe2companion/aoestats bivariate EDA steps

## Open Questions

- Does higher MMR among rated players actually predict winning, or does
  tournament match-making equalize MMR between opponents in the same game?
  (Answer from T03 violin + Mann-Whitney U result.)
- Which in-game metric shows the strongest separation between Win and Loss?
  APM, SQ, or supplyCappedPercent? (Answer from T10 multi-panel visual
  comparison and T11 Spearman target correlation row.)
- Is the near-50% win rate per race genuine balance, or an artifact of the
  2-players-per-game structure? (Answer from T04 chi-square test.)

---

For Category A, adversarial critique is required before execution begins.
Dispatch reviewer-adversarial to produce `planning/plan_sc2egset_01_02_06.critique.md`.
