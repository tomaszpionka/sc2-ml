---
category: A
branch: feat/sc2egset-01-02-05-visualizations
date: 2026-04-14
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis (Tukey-style)"
invariants_touched:
  - 6
  - 7
  - 9
source_artifacts:
  - sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: null
---

# Plan: sc2egset 01_02_05 -- EDA Visualization Notebook

## Scope

New notebook step 01_02_05 for the sc2egset dataset. This notebook contains
all visualizations for the Phase 01 univariate EDA, deliberately separated
from the analytics notebook (01_02_04). Every plot cell is preceded by a
pandas verification cell that prints the data being plotted. Chart types are
chosen based on distribution characteristics established by 01_02_04.

Phase 01, Pipeline Section 01_02, Step 01_02_05.

## Problem Statement

Step 01_02_04 established the quantitative profile of all sc2egset raw
columns: NULL census, descriptive statistics, zero counts, categorical
distributions, skewness/kurtosis, and sentinel detection. Visualizations were
partially included in 01_02_04 but an adversarial review determined that the
visualization logic should be extracted into a dedicated notebook. This
separation provides two benefits: (1) 01_02_04 is a clean analytics reference
document; (2) 01_02_05 is a visual reference where every chart is
data-grounded via a preceding verification cell.

The chart selection is informed by 01_02_04's findings:
- MMR: 83.6% zero-spike requires a split-view histogram (all vs. >0 only)
- SQ: 2 INT32_MIN sentinels require a split-view (all vs. sentinel-excluded)
- Categorical fields: known cardinality from JSON artifact determines
  horizontal bar chart layout
- Temporal coverage: monthly counts line plot
- MMR zero-spike cross-tabulation: bar charts for sentinel hypothesis testing

## Assumptions & unknowns

- **Assumption:** The 01_02_04 pass 2 (plan_sc2egset_01_02_04_pass2) has been
  executed and the JSON artifact contains all keys including
  `mmr_zero_interpretation`, `isInClan_distribution`, and `clanTag_top20`.
  If pass 2 has not yet been executed, this notebook must be executed after it.
- **Assumption:** The jupytext pairing configuration at `sandbox/jupytext.toml`
  will automatically create the `.ipynb` counterpart on sync.
- **Unknown:** Whether the MMR>0 distribution is unimodal or multimodal. The
  visualization will reveal this. No assumption is made in advance.

## Literature context

EDA Manual Section 2.1 specifies the three EDA layers: univariate, bivariate,
multivariate. This notebook covers univariate visualizations. EDA Manual
Section 3.4 specifies distribution analysis methods: histograms, KDE, QQ
plots, empirical CDFs. This notebook uses histograms for numeric fields and
bar charts for categorical fields, which are the appropriate first-pass tools
per Tukey (1977) and Wickham (R for Data Science, Ch. 7). KDE and QQ plots
are deferred to bivariate EDA (01_02_06+) where comparing distributions across
groups (e.g., MMR by race) is more informative.

EDA Manual Section 3.2 specifies dataset-level profiling should include
temporal coverage visualization. Section 7 ("Seven Pitfalls") warns against
cherry-picking visualizations -- this notebook covers all numeric and
categorical fields comprehensively.

## Execution Steps

### T01 -- Create notebook skeleton and load data

**Objective:** Create the new notebook file with header, imports, DuckDB
connection, JSON artifact loading, and artifact directory setup.

**Instructions:**
1. Create file:
   `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`
2. Add jupytext header matching the project convention (see 01_02_04 header).
3. Add markdown header cell:
   ```
   # Step 01_02_05 -- Univariate EDA Visualizations

   **Phase:** 01 -- Data Exploration
   **Pipeline Section:** 01_02 -- EDA (Tukey-style)
   **Dataset:** sc2egset
   **Question:** What do the distributions from 01_02_04 look like visually,
   and do the visual patterns confirm or challenge the statistical summaries?
   **Invariants applied:** #6 (reproducibility -- queries inlined),
   #7 (no magic numbers), #9 (step scope: visualization of 01_02_04 findings)
   **Predecessor:** 01_02_04 (univariate census -- JSON artifact required)
   **Step scope:** visualize
   **Type:** Read-only -- no DuckDB writes
   ```
4. Import cell: json, pathlib.Path, duckdb, matplotlib, matplotlib.pyplot,
   pandas. Also import notebook_utils and sc2 config.
5. Connection cell: read-only DuckDB connection.
6. Load 01_02_04 JSON artifact:
   ```python
   census_json_path = (
       get_reports_dir("sc2", "sc2egset")
       / "artifacts" / "01_exploration" / "02_eda"
       / "01_02_04_univariate_census.json"
   )
   with open(census_json_path) as f:
       census = json.load(f)
   print(f"Loaded 01_02_04 artifact: {len(census)} keys")
   ```
7. Set up artifacts and plots directories:
   ```python
   artifacts_dir = (
       get_reports_dir("sc2", "sc2egset")
       / "artifacts" / "01_exploration" / "02_eda"
   )
   plots_dir = artifacts_dir / "plots"
   plots_dir.mkdir(parents=True, exist_ok=True)
   ```
8. **Prerequisite gate** — verify that the 01_02_04 pass-2 JSON artifact
   contains all keys required by this notebook. Add an assertion cell
   immediately after the JSON load:
   ```python
   REQUIRED_PASS2_KEYS = [
       "mmr_zero_interpretation",
       "isInClan_distribution",
       "clanTag_top20",
   ]
   missing = [k for k in REQUIRED_PASS2_KEYS if k not in census]
   assert not missing, (
       f"BLOCKER: 01_02_04 pass-2 not yet executed. Missing keys: {missing}. "
       "Execute plan_sc2egset_01_02_04_pass2 before running this notebook."
   )
   print(f"Pass-2 prerequisite check PASSED. {len(census)} keys loaded.")
   ```
   Do NOT load struct_flat SQL here — no plot in this notebook uses struct_flat.

**Verification:**
- File exists and is valid jupytext percent-format Python.
- JSON artifact loads successfully with expected keys.
- Prerequisite gate assertion passes (all 3 pass-2 keys present).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T02 -- Result distribution bar chart

**Objective:** Reproduce the result distribution bar chart with a preceding
pandas verification cell.

**Instructions:**
1. Add markdown cell: `## Plot 1: Result Distribution`.
2. Verification cell:
   ```python
   result_dist = pd.DataFrame(census["result_distribution"])
   print("=== Result distribution data for plot ===")
   print(result_dist.to_string(index=False))
   ```
3. Plot cell: vertical bar chart with count annotations. Reading from the
   JSON artifact rather than re-querying.
   Save as `plots_dir / "01_02_05_result_bar.png"`.

**Verification:**
- Plot file saved to artifacts/plots/.
- Verification cell prints the DataFrame (Win, Loss, Undecided, Tie).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T03 -- Race / highestLeague / region horizontal bar charts

**Objective:** Create horizontal bar charts for the three main categorical
fields. Horizontal bars are preferred over vertical because category labels
can be long (e.g., "Grandmaster").

**Instructions:**
1. Add markdown cell: `## Plot 2: Categorical Distributions`.
2. Create a 1x3 subplot figure (figsize 18x5).
3. For each of `race`, `highestLeague`, `region`:
   a. Verification cell: load from `census["categorical_profiles"][col]`,
      convert to DataFrame, print.
   b. Plot as horizontal bar chart (barh). Sort by count descending (largest
      at top). Annotate bars with count values.
4. Save as `plots_dir / "01_02_05_categorical_bars.png"`.

**Verification:**
- Plot file saved.
- 3 verification cells print the data, one per field.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T04 -- MMR distribution split view

**Objective:** Create a two-subplot figure showing (a) the full MMR
distribution including the zero-spike and (b) the MMR>0 distribution only,
revealing the actual rating distribution hidden behind the spike.

**Instructions:**
1. Add markdown cell:
   `## Plot 3: MMR Distribution (Split View)`.
2. Verification cell 1 -- full MMR:
   ```python
   mmr_data = con.execute(
       "SELECT MMR FROM replay_players_raw WHERE MMR IS NOT NULL"
   ).df()
   print(f"=== Full MMR data for plot ({len(mmr_data)} rows) ===")
   print(mmr_data["MMR"].describe().to_string())
   ```
3. Verification cell 2 -- MMR > 0:
   ```python
   mmr_positive = mmr_data[mmr_data["MMR"] > 0]
   print(f"=== MMR > 0 data for plot ({len(mmr_positive)} rows) ===")
   print(mmr_positive["MMR"].describe().to_string())
   ```
4. Compute the annotation text dynamically from census before the plot cell:
   ```python
   n_mmr_zero = sum(
       r["mmr_zero_cnt"] for r in census["mmr_zero_interpretation"]["by_result"]
   )
   total_mmr = len(mmr_data)
   mmr_zero_pct = 100.0 * n_mmr_zero / total_mmr
   mmr_annotation = f"N={n_mmr_zero:,} MMR=0 ({mmr_zero_pct:.1f}%) excluded"
   ```
   Do NOT hardcode "N=37,489" or "83.6%" — derive from loaded census data.
5. Plot cell: 1x2 subplots, figsize (14, 5).
   - Subplot (a): histogram of all MMR, bins=50 (50 bins used throughout as consistent
     first-pass EDA resolution). Title: "MMR (all rows)".
   - Subplot (b): histogram of MMR > 0, bins=50. Title: "MMR (excluding zero)".
     Add annotation using `mmr_annotation` variable computed in step 4.
6. Save as `plots_dir / "01_02_05_mmr_split.png"`.

**Verification:**
- Plot file saved.
- Both verification cells print describe output.
- Subplot (b) annotation reflects the correct N and percentage.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T05 -- APM distribution histogram

**Objective:** Histogram of APM values with annotation of any outlier region.

**Instructions:**
1. Add markdown cell: `## Plot 4: APM Distribution`.
2. Verification cell:
   ```python
   apm_data = con.execute(
       "SELECT APM FROM replay_players_raw WHERE APM IS NOT NULL"
   ).df()
   print(f"=== APM data for plot ({len(apm_data)} rows) ===")
   print(apm_data["APM"].describe().to_string())
   ```
3. Plot cell: single histogram, bins=50. Mark the median with a vertical
   dashed line. Annotate if max APM (1248 per JSON) is visually far from
   the main mass.
4. Save as `plots_dir / "01_02_05_apm_hist.png"`.

**Verification:**
- Plot file saved. Verification cell prints describe.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T06 -- SQ distribution split view

**Objective:** Two-subplot figure: (a) full SQ including the INT32_MIN
sentinel and (b) SQ excluding sentinel rows, revealing the actual SQ
distribution (0-187 range).

**Instructions:**
1. Add markdown cell: `## Plot 5: SQ Distribution (Split View)`.
2. Verification cell 1 -- full SQ:
   ```python
   sq_data = con.execute(
       "SELECT SQ FROM replay_players_raw WHERE SQ IS NOT NULL"
   ).df()
   print(f"=== Full SQ data for plot ({len(sq_data)} rows) ===")
   print(sq_data["SQ"].describe().to_string())
   ```
3. Verification cell 2 -- SQ excluding sentinel:
   ```python
   sq_clean = sq_data[sq_data["SQ"] != -2147483648]
   print(f"=== SQ excluding sentinel ({len(sq_clean)} rows) ===")
   print(sq_clean["SQ"].describe().to_string())
   ```
4. Plot cell: 1x2 subplots, figsize (14, 5).
   - Subplot (a): histogram of all SQ, bins=50. Title:
     "SQ (all rows, sentinel visible)".
   - Subplot (b): histogram of SQ excluding sentinel, bins=50. Title:
     "SQ (sentinel excluded)". Annotation: "2 sentinel rows excluded".
5. Save as `plots_dir / "01_02_05_sq_split.png"`.

**Verification:**
- Plot file saved. Both verification cells print describe.
- sq_clean has exactly 2 fewer rows than sq_data.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T07 -- supplyCappedPercent distribution histogram

**Objective:** Histogram of supplyCappedPercent (expected 0-100 range).

**Instructions:**
1. Add markdown cell: `## Plot 6: supplyCappedPercent Distribution`.
2. Verification cell:
   ```python
   sc_data = con.execute(
       "SELECT supplyCappedPercent FROM replay_players_raw WHERE supplyCappedPercent IS NOT NULL"
   ).df()
   print(f"=== supplyCappedPercent data ({len(sc_data)} rows) ===")
   print(sc_data["supplyCappedPercent"].describe().to_string())
   ```
3. Plot cell: single histogram, bins=50. Mark median with vertical dashed line.
4. Save as `plots_dir / "01_02_05_supplycapped_hist.png"`.

**Verification:**
- Plot file saved. Verification cell prints describe.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T08 -- MMR zero-spike by result and by highestLeague

**Objective:** Visualize the MMR zero-spike cross-tabulation from the JSON
artifact's `mmr_zero_interpretation` key, answering the sentinel hypothesis
visually.

**Instructions:**
1. Add markdown cell:
   `## Plot 7: MMR Zero-Spike by Result and by highestLeague`.
2. Verification cell 1:
   ```python
   mmr_by_result = pd.DataFrame(
       census["mmr_zero_interpretation"]["by_result"]
   )
   print("=== MMR=0 by result ===")
   print(mmr_by_result.to_string(index=False))
   ```
3. Verification cell 2:
   ```python
   mmr_by_league = pd.DataFrame(
       census["mmr_zero_interpretation"]["by_highestLeague"]
   )
   print("=== MMR=0 by highestLeague ===")
   print(mmr_by_league.to_string(index=False))
   ```
4. Plot cell: 1x2 subplots, figsize (14, 5).
   - Subplot (a): bar chart of mmr_zero_pct per result category.
   - Subplot (b): bar chart of mmr_zero_pct per highestLeague.
   - Add a horizontal dashed line at the overall MMR=0 rate derived from census:
     ```python
     overall_mmr_zero_pct = 100.0 * sum(
         r["mmr_zero_cnt"] for r in census["mmr_zero_interpretation"]["by_result"]
     ) / sum(
         r["total_cnt"] for r in census["mmr_zero_interpretation"]["by_result"]
     )
     ```
     Do NOT hardcode "83.6%".
5. Save as `plots_dir / "01_02_05_mmr_zero_interpretation.png"`.

**Verification:**
- Plot file saved. Both verification cells print the data.
- Horizontal reference line at the computed overall MMR=0 rate is visible.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T09 -- Temporal coverage line plot

**Objective:** Monthly replay count line plot showing the temporal coverage of
the dataset.

**Instructions:**
1. Add markdown cell: `## Plot 8: Temporal Coverage`.
2. Verification cell:
   ```python
   monthly = pd.DataFrame(census["monthly_counts"])
   print(f"=== Monthly counts ({len(monthly)} months) ===")
   print(monthly.to_string(index=False))
   ```
3. Plot cell: line plot (not bar -- the temporal axis is continuous). X-axis
   is month (string), Y-axis is count. Rotate x labels 90 degrees. Mark any
   months with count < 50 or gaps with annotations if practical.
4. Save as `plots_dir / "01_02_05_temporal_coverage.png"`.

**Verification:**
- Plot file saved. Verification cell prints all months.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T10 -- isInClan distribution bar chart

**Objective:** Simple bar chart of isInClan TRUE/FALSE distribution.

**Instructions:**
1. Add markdown cell: `## Plot 9: isInClan Distribution`.
2. Verification cell:
   ```python
   clan_dist = pd.DataFrame(census["isInClan_distribution"])
   print("=== isInClan distribution ===")
   print(clan_dist.to_string(index=False))
   ```
3. Plot cell: vertical bar chart with two bars (True/False). Annotate with
   counts and percentages.
4. Save as `plots_dir / "01_02_05_isinclan_bar.png"`.

**Verification:**
- Plot file saved. Verification cell prints 2 rows.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T11 -- clanTag top-20 horizontal bar chart

**Objective:** Horizontal bar chart of the 20 most frequent clan tags.

**Instructions:**
1. Add markdown cell: `## Plot 10: clanTag Top-20`.
2. Verification cell:
   ```python
   clan_top20 = pd.DataFrame(census["clanTag_top20"])
   print("=== clanTag top-20 ===")
   print(clan_top20.to_string(index=False))
   ```
3. Plot cell: horizontal bar chart (barh). Bars sorted by count descending
   (largest at top). Annotate with count values.
4. Save as `plots_dir / "01_02_05_clantag_top20.png"`.

**Verification:**
- Plot file saved. Verification cell prints 20 rows.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

---

### T12 -- Write summary markdown artifact and close connection

**Objective:** Write a summary markdown artifact listing all plots produced,
their data sources, and key observations. Close the DuckDB connection.

**Instructions:**
1. Build a markdown string listing all 10 plots with:
   - Plot number and title
   - Filename
   - One-sentence observation (written by executor based on what the plot
     shows when executed)
2. Write to:
   `artifacts_dir / "01_02_05_visualizations.md"`
3. Close DuckDB connection.
4. Print summary of all plot files produced.

**Verification:**
- Markdown artifact exists at the expected path.
- All 10 plot PNG files exist in the plots directory.
- Notebook executes end-to-end without error.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.ipynb`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png`

---

### T13 -- Add step to ROADMAP.md and STEP_STATUS.yaml

**Objective:** Register step 01_02_05 in the dataset's ROADMAP and
STEP_STATUS so it is tracked alongside other steps.

**Instructions:**
1. Add a new step definition block to
   `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` after the
   01_02_04 block, following the same YAML-in-markdown format:
   ```yaml
   step_number: "01_02_05"
   name: "Univariate EDA Visualizations"
   description: "Dedicated visualization notebook for all univariate distributions profiled in 01_02_04."
   phase: "01 -- Data Exploration"
   pipeline_section: "01_02 -- EDA (Tukey-style)"
   manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 2.1, 3.4"
   dataset: "sc2egset"
   question: "What do the distributions from 01_02_04 look like visually?"
   method: "Histograms for numeric, bar charts for categorical, line plot for temporal."
   predecessors: "01_02_04"
   notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py"
   ```
2. Add to STEP_STATUS.yaml:
   ```yaml
   "01_02_05":
     name: "Univariate EDA Visualizations"
     pipeline_section: "01_02"
     status: complete
     completed_at: "<execution date>"
   ```

**Verification:**
- ROADMAP.md contains step 01_02_05.
- STEP_STATUS.yaml contains step 01_02_05 with status "complete".

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.ipynb` | Create (jupytext sync) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_result_bar.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_categorical_bars.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_mmr_split.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_apm_hist.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_sq_split.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_supplycapped_hist.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_mmr_zero_interpretation.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_temporal_coverage.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_isinclan_bar.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/plots/01_02_05_clantag_top20.png` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update |

## Gate Condition

- Notebook executes end-to-end without error.
- All 10 PNG plot files exist under `reports/artifacts/.../plots/`.
- Summary markdown artifact `01_02_05_visualizations.md` exists and lists all
  10 plots.
- Every plot cell is preceded by a verification cell that prints the data.
- ROADMAP.md and STEP_STATUS.yaml are updated.

## Out of scope

- **Field classification refinement** -- deferred; no source documentation available.
- **Research log entries** -- deferred until both 01_02_04 pass 2 and 01_02_05
  are fully polished.
- **Bivariate plots** (e.g., MMR by race, APM by result) -- belong to a
  future bivariate EDA step (01_02_06+).
- **KDE and QQ plots** -- deferred to bivariate EDA.
- **Completeness heatmap** -- given that both replay_players_raw and struct_flat
  have 0% NULLs, a heatmap of all-zero missingness is uninformative.
- **Duration histogram (struct_flat.elapsed_game_loops)** -- struct_flat SQL is
  not loaded in this notebook (no other plot uses it). Duration distribution
  deferred to bivariate EDA where it can be compared across race/result groups.
- **selectedRace** -- not a column in replay_players_raw schema; intentionally
  excluded from coverage.

## Open questions

- **Execution ordering**: This notebook depends on 01_02_04 pass 2 being
  complete (for `mmr_zero_interpretation`, `isInClan_distribution`,
  `clanTag_top20` keys in the JSON artifact). Execute plan_sc2egset_01_02_04_pass2
  first.

## Deferred Debt

| Item | Target Step | Rationale |
|------|-------------|-----------|
| Bivariate plots (MMR by race, APM by result) | 01_02_06+ | Bivariate analysis belongs to next EDA layer |
| KDE / QQ plots | 01_02_06+ | More informative when comparing groups |
| Completeness heatmap (visual) | 01_03 | Both tables are 0% NULL; heatmap uninformative |
