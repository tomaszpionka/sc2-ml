---
category: A
branch: feat/aoestats-01-02-05-visualizations
date: 2026-04-14
planner_model: claude-opus-4-6
dataset: aoestats
phase: "01"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
invariants_touched: [I6, I7, I9]
source_artifacts:
  - sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: null
---

# Plan: aoestats 01_02_05 — Univariate Visualizations

## Scope

New step 01_02_05 for the aoestats dataset: a dedicated visualization notebook that produces all EDA plots based on the quantitative findings from 01_02_04 (and its pass-2 augmentation). Every plot cell is preceded by a pandas verification cell. The notebook reads from the JSON artifact and DuckDB directly — no analytical computation beyond what is needed for visualization. Twelve visualization groups covering winner distribution, categorical top-k, numeric distributions with log-scale and sentinel handling, IQR outlier summary, NULL rate summary, and temporal match volume.

## Problem Statement

The 01_02_04 notebook currently mixes analytics (SQL queries, JSON artifact generation) with visualization (bar charts, histograms, boxplots, time series). After the pass-2 augmentation adds nine more analytical sections, the notebook becomes excessively long. Separating visualizations into a dedicated step provides:

1. Cleaner notebook structure: 01_02_04 is pure analytics; 01_02_05 is pure visualization.
2. Plot choices informed by 01_02_04 findings: log-scale for duration (skewness), sentinel panels for ELO, non-NULL-only for opening.
3. Every plot has a verification cell.
4. Standalone PNG artifacts for thesis figures.

## Assumptions and Unknowns

- **Assumption:** 01_02_04 pass-2 has been executed and its JSON artifact contains all keys referenced in this plan (skew_kurtosis, opening_nonnull_distribution, outlier_counts, etc.).
- **Assumption:** The notebook reads DuckDB in read-only mode for any data not already in the JSON artifact.
- **Assumption:** matplotlib is sufficient for all plots; no additional dependencies needed.
- **Unknown:** Whether thesis will ultimately use these PNG files or regenerate from code. Does not block execution — PNGs are artifacts regardless.

## Literature Context

EDA Manual Section 2.1: univariate analysis requires histograms, boxplots, and descriptive statistics. Section 3.4 recommends combining histograms with KDE for shape assessment.

Tukey 1977: "Exploratory data analysis is detective work... graphical detective work." Visualizations are not optional EDA decorations — they are the primary analytical instrument.

Anscombe's Quartet (1973): identical summary statistics, dramatically different visual patterns. This is why we produce plots even when we have full descriptive statistics.

Invariant #6: all SQL queries that produce plotted data must appear verbatim in the markdown artifact.

## Execution Steps

### T01 — Add step 01_02_05 definition to ROADMAP and STEP_STATUS

**Objective:** Register the new step in the aoestats ROADMAP and STEP_STATUS.yaml.

**Instructions:**

1. In `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`, after the step 01_02_04 YAML block, add a step 01_02_05 block matching the YAML format used by existing steps. Include: step_number, name, description, phase, pipeline_section, manual_reference, dataset, question, method, predecessors, notebook_path, inputs (duckdb_tables, prior_artifacts), outputs (plots list), scientific_invariants_applied, gate.

2. In `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`, add:
   ```yaml
   "01_02_05":
     name: "Univariate Visualizations"
     pipeline_section: "01_02"
     status: not_started
   ```

**Verification:**
- ROADMAP.md contains a step 01_02_05 block
- STEP_STATUS.yaml lists step 01_02_05 with status not_started

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`

---

### T02 — Create notebook skeleton with imports and setup

**Objective:** Create the 01_02_05 notebook with standard header, imports, DuckDB connection, JSON artifact loading, and artifact directory setup.

**Instructions:**

1. Create `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py` with the jupytext header (matching existing notebooks in the same directory).

2. Include the following cells in order:
   - Markdown header cell documenting Phase, Pipeline Section, Dataset, Question, Invariants applied, Predecessor, Step scope, Type
   - Imports: json, pathlib.Path, duckdb, matplotlib, matplotlib.pyplot, pandas, numpy; from rts_predict: get_reports_dir, setup_notebook_logging, AOESTATS_DB_FILE
   - `con = duckdb.connect(str(AOESTATS_DB_FILE), read_only=True)`
   - `artifacts_dir = get_reports_dir("aoe2", "aoestats") / "artifacts" / "01_exploration" / "02_eda"`
   - Load JSON: `with open(census_path) as f: census = json.load(f)` then print key count
   - `sql_queries: dict = {}` (for artifact)

**Verification:**
- File exists and has valid jupytext header
- Imports include json, duckdb, matplotlib, pandas
- Census JSON loaded into `census` variable

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T03 — Winner distribution bar chart

**Objective:** Plot 1. Bar chart of winner distribution (TRUE/FALSE) counts.

**Instructions:**

1. Verification cell:
   ```python
   winner_data = census["winner_distribution"]
   winner_df = pd.DataFrame(winner_data)
   print("Winner distribution data:")
   print(winner_df.to_string(index=False))
   ```

2. Plot cell: vertical bar chart with count annotations. Color: TRUE=green, FALSE=red.
   Save as `artifacts_dir / "01_02_05_winner_distribution.png"` at dpi=150.

**Verification:**
- PNG file `01_02_05_winner_distribution.png` exists and is non-empty
- Verification print cell precedes plot cell

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T04 — Map top-20 and Civ top-20 horizontal bar charts

**Objective:** Plots 2-3. Horizontal bar charts for top-20 maps and top-20 civilizations.

**Instructions:**

1. For map top-20:
   - Verification cell: load `census["categorical_matches"]["map"]["top_values"][:20]`, print.
   - Plot: horizontal bar (barh), sorted descending, annotated with pct.
   - Save as `artifacts_dir / "01_02_05_map_top20.png"`.

2. For civ top-20:
   - Verification cell: load `census["categorical_players"]["civ"]["top_values"][:20]`, print.
   - Plot: horizontal bar (barh), sorted descending, annotated with pct.
   - Save as `artifacts_dir / "01_02_05_civ_top20.png"`.

**Verification:**
- `01_02_05_map_top20.png` and `01_02_05_civ_top20.png` exist

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T05 — Leaderboard distribution bar chart

**Objective:** Plot 4. Horizontal bar chart of leaderboard distribution (4 values only).

**Instructions:**

1. Verification cell: load `census["categorical_matches"]["leaderboard"]["top_values"]`, print.

2. Plot: horizontal bar (barh). Save as `artifacts_dir / "01_02_05_leaderboard_distribution.png"`.

**Verification:**
- `01_02_05_leaderboard_distribution.png` exists

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T06 — Duration histogram (log-scale)

**Objective:** Plot 5. Log-scale histogram of match duration, annotated to show outlier tail.

**Instructions:**

1. Query:
   ```sql
   -- duration is stored in nanoseconds (BIGINT); divide by 1e9 for seconds, then by 60 for minutes
   SELECT FLOOR(duration / 1e9 / 60) * 60 AS bin, COUNT(*) AS cnt
   FROM matches_raw WHERE duration IS NOT NULL
   GROUP BY bin ORDER BY bin
   ```
   Store in `sql_queries["hist_duration_log"]`.

2. Verification cell: print first/last 5 bins.

3. Plot: `ax.bar(...)` with `ax.set_yscale("log")`. Annotate with p95 and max values from census.
   Save as `artifacts_dir / "01_02_05_duration_histogram.png"`.

**Verification:**
- `01_02_05_duration_histogram.png` exists with log-scale y-axis

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T07 — ELO distribution panels (with and without sentinel -1.0)

**Objective:** Plot 6. Three columns (avg_elo, team_0_elo, team_1_elo), two rows (including sentinel, excluding sentinel). Row 2 only applies to team_0_elo and team_1_elo.

**Instructions:**

1. For each ELO column and each sentinel variant, execute a binned histogram query
   (bin width 25 — ELO values range 0-3500; 25-unit bins give ~140 bins covering
   the typical rated range, providing adequate resolution). [I7]
   Store all in `elo_hist_data` dict. Add all SQL to `sql_queries`. Print first 5 bins of each.

2. Plot: 2x3 subplot grid, figsize (18, 10).
   - Row 0: all values including sentinel
   - Row 1: sentinel excluded (avg_elo panel left blank / hidden)
   - Annotate sentinel count on team_0/1_elo panels — derive from
     `census["team_0_elo_stats_no_sentinel"]["n_null"]` minus the sentinel count
     stored in the artifact, NOT from hardcoded values (34/39).
   - Save as `artifacts_dir / "01_02_05_elo_distributions.png"`.

**Verification:**
- `01_02_05_elo_distributions.png` exists with 2x3 grid
- Sentinel annotation present on team_0/1_elo panels

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T08 — old_rating histogram and age uptime histograms

**Objective:** Plots 7-8. old_rating distribution and three-panel non-NULL age uptime distributions.

**Instructions:**

1. old_rating: histogram query (bin width 25 — old_rating range is 0-3500, same scale as ELO;
   25-unit bins give ~140 bins, consistent with ELO histogram resolution). [I7]
   Verification cell prints first 5 bins.
   Plot: single histogram. Save as `artifacts_dir / "01_02_05_old_rating_histogram.png"`.

2. Age uptimes: for feudal/castle/imperial_age_uptime, query non-NULL histogram bins (bin width 20
   — age uptime values are in seconds with expected range 0-2000s for most games;
   20-second bins give ~100 bins covering the typical range). [I7]
   Verification cells print first 5 bins of each.
   Plot: 1x3 subplot, figsize (18, 5). Each subplot annotated with non-NULL N and NULL pct
   derived from `census["players_null_census"]` (not hardcoded).
   Save as `artifacts_dir / "01_02_05_age_uptime_histograms.png"`.

**Verification:**
- `01_02_05_old_rating_histogram.png` and `01_02_05_age_uptime_histograms.png` exist
- Age uptime annotations show correct N and null percentage

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T09 — Opening non-NULL distribution bar chart

**Objective:** Plot 9. Bar chart of opening strategies among non-NULL rows only. This avoids the dominant NaN bar that pollutes the existing top-k.

**Instructions:**

1. **Prerequisite gate** — verify the pass-2 key exists before using it:
   ```python
   assert "opening_nonnull_distribution" in census, (
       "BLOCKER: 'opening_nonnull_distribution' not found in census. "
       "Execute plan_aoestats_01_02_04_pass2 (T08) before running T09."
   )
   ```

2. Verification cell:
   ```python
   opening_dist = census["opening_nonnull_distribution"]
   opening_df = pd.DataFrame(opening_dist["values"])
   total_nonnull = opening_dist["total_nonnull"]
   print(f"Opening non-NULL distribution: N={total_nonnull:,}")
   print(opening_df.to_string(index=False))
   ```

2. Plot: horizontal bar (barh). Title annotates total non-NULL count and 86% NULL note.
   Save as `artifacts_dir / "01_02_05_opening_nonnull.png"`.

**Verification:**
- `01_02_05_opening_nonnull.png` exists
- No NaN/NULL bar in the chart
- Title contains non-NULL count

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T10 — IQR outlier summary bar chart

**Objective:** Plot 10. Horizontal bar chart showing outlier_pct per column, color-coded by table, high-NULL columns annotated.

**Instructions:**

1. Verification cell: build a DataFrame from `census["outlier_counts_matches"]` and `census["outlier_counts_players"]`, sorted by outlier_pct ascending. Print.

2. Plot: horizontal bar (barh). Blue for matches_raw, orange for players_raw.
   Mark "*high NULL" annotation on feudal/castle/imperial_age_uptime columns (red text).
   Save as `artifacts_dir / "01_02_05_iqr_outlier_summary.png"`.

**Verification:**
- `01_02_05_iqr_outlier_summary.png` exists
- Bars color-coded by table with legend

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T11 — NULL rate bar chart for all 32 columns

**Objective:** Plot 11. Horizontal bar chart sorted by null_pct descending, color-coded by severity (>= 50% red, 5-50% orange, 0-5% yellow, 0% green).

**Instructions:**

1. Verification cell: build a DataFrame from `census["matches_null_census"]["columns"]` (prefixed "m.") and `census["players_null_census"]["columns"]` (prefixed "p."). Sort by null_pct ascending. Print.

2. Plot: horizontal bar (barh). Color per severity function. Legend for severity buckets.
   Save as `artifacts_dir / "01_02_05_null_rate_bar.png"`.

**Verification:**
- `01_02_05_null_rate_bar.png` exists with 32 bars
- High-NULL columns colored red

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T12 — Monthly match count time series

**Objective:** Plot 12. Line plot of match volume over time with mean annotation.

**Instructions:**

1. Query:
   ```sql
   SELECT DATE_TRUNC('month', started_timestamp) AS month, COUNT(*) AS match_count
   FROM matches_raw WHERE started_timestamp IS NOT NULL
   GROUP BY month ORDER BY month
   ```
   Store in `sql_queries["monthly_match_counts"]`.

2. Verification cell: print all months.

3. Plot: line plot with `marker="o"`. Mean dashed line annotated. X labels rotated 45°.
   Save as `artifacts_dir / "01_02_05_monthly_match_count.png"`.

**Verification:**
- `01_02_05_monthly_match_count.png` exists
- 42 data points (matching temporal_range.distinct_months from census)

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T13 — Artifact writing and notebook execution

**Objective:** Write the visualizations.md index artifact (plot index table + all SQL queries per Invariant #6), close the connection, and execute the full notebook.

**Instructions:**

1. Build markdown artifact with: header, plot index table (12 rows), SQL queries section (all entries from `sql_queries` dict as fenced code blocks).

2. Write to `artifacts_dir / "01_02_05_visualizations.md"`.

3. Close connection: `con.close()`.

4. Execute notebook with 1800s timeout (aoestats has 30M matches + 107M players rows):
   ```bash
   source .venv/bin/activate && poetry run jupytext --execute \
       sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py \
       --to notebook \
       --output sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.ipynb \
       --ExecutePreprocessor.timeout=1800
   ```

5. Verify all 12 PNG files exist in the artifacts directory.

6. Update STEP_STATUS.yaml: change status from `not_started` to `complete`, add `completed_at: <date>`.

**Verification:**
- All 12 PNG files exist and are non-empty
- `01_02_05_visualizations.md` exists with plot index table and all SQL queries
- Both .py and .ipynb are committed and in sync
- Notebook executes without errors

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_*.png` (12 files)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | Update |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py` | Create |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.ipynb` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_winner_distribution.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_map_top20.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_civ_top20.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_leaderboard_distribution.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_duration_histogram.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_elo_distributions.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_old_rating_histogram.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_age_uptime_histograms.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_opening_nonnull.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_iqr_outlier_summary.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_null_rate_bar.png` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_05_monthly_match_count.png` | Create |

## Gate Condition

- All 12 PNG files exist and are non-empty
- `01_02_05_visualizations.md` exists with complete plot index and all SQL queries
- ROADMAP.md contains step 01_02_05 definition
- STEP_STATUS.yaml contains step 01_02_05 with status complete after execution
- Notebook executes end-to-end without errors
- Every plot cell has an immediately preceding print/display cell
- Both .py and .ipynb files committed and in sync

## Out of Scope

- **Bivariate and multivariate plots:** deferred to 01_02_06 or later
- **Research log entries:** deferred until notebooks polished
- **Field classification updates:** deferred, no source documentation
- **Thesis-quality figure formatting:** current plots are EDA-grade
- **KDE overlays:** deferred to 01_03

## Open Questions

- Whether the 01_02_04 pass-2 JSON artifact will contain `opening_nonnull_distribution` at execution time — T09 reads this key. Resolves by: executing pass-2 plan first.

## Deferred Debt

| Item | Target Step | Rationale |
|------|-------------|-----------|
| Bivariate plots (winner by civ, winner by map) | 01_02_06+ | Bivariate analysis belongs to next EDA layer |
| KDE overlays | 01_03 | More informative for group comparisons |
| Thesis-quality figure formatting | Thesis writing phase | EDA plots are exploratory; final figures regenerated |
