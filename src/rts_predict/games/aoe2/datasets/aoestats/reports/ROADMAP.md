# aoestats Dataset Roadmap

**Game:** AoE2
**Dataset:** aoestats
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`
**Research log:** `research_log.md` (sibling file — per-dataset reverse-chronological narrative)

---

> **Role: PRIMARY on patch-resolution (D5, patch_id binding);
> SUPPLEMENTARY on sample-scale (D1), temporal-coverage (D3), and
> identity-rigor (D4, Branch (v) structurally-forced); SUPPLEMENTARY
> on skill-signal (D2, ICC 0.027 pending BACKLOG F1 canonical_slot
> resolution); N/A on in-game events (D6). Assigned at 01_06 per
> `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`.
> Rationale: patch-anchored, BACKLOG F1 canonical_slot pending, Branch (v)
> structurally-forced.**

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the aoestats
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Steps are defined in a planning session before Phase work begins.

Steps are numbered `XX_YY_ZZ` where `XX` = Phase, `YY` = Pipeline Section,
`ZZ` = Step within that Pipeline Section.

---

## Source data

**aoestats.io weekly DB dumps** — community match and player statistics dataset.
Downloaded 2026-04-06. File counts and date ranges are from
Step 01_01_01 (file inventory).

| Subdirectory | Files (.parquet / .json) | Size (MB) |
|---|---|---|
| `matches/` | 172 | 610.55 |
| `players/` | 171 | 3162.86 |
| `overview/` | 1 | 0.02 |

**Total:** 344 data files (excluding 3 `.gitkeep` dotfiles and 2 root files),
3773.61 MB. Filename-derived date range: 2022-08-28 to 2026-02-07.

**Raw data is immutable. The weekly dump download will not be repeated.**
Acquisition provenance is recorded in
`src/rts_predict/games/aoe2/datasets/aoestats/reports/README.md`.

Row counts, schema, and column-level characteristics will be established
by Phase 01 Steps 01_01_02 (schema discovery) and 01_03 (systematic profiling).

---

## Phase 01 — Data Exploration

Pipeline Sections per `docs/PHASES.md`:

- `01_01` — Data Acquisition & Source Inventory
- `01_02` — Exploratory Data Analysis (Tukey-style)
- `01_03` — Systematic Data Profiling
- `01_04` — Data Cleaning
- `01_05` — Temporal & Panel EDA
- `01_06` — Decision Gates

### Step 01_01_01 — File Inventory

```yaml
step_number: "01_01_01"
name: "File Inventory"
description: "Establish a complete filesystem-level census of the aoestats raw data. This grounds all subsequent steps in verified file counts, sizes, date ranges, and directory structure — including alignment between paired directories (matches vs players)."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoestats"
question: "How many files exist in each subdirectory, what weekly date range do they span, and are the matches and players file series temporally aligned?"
method: "Full census of the raw directory tree. Count files, measure sizes, group by subdirectory. Extract weekly dates from filenames and compare paired directories for count and date-range alignment."
stratification: "By subdirectory (matches, players, overview)."
predecessors: "none — independent"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py"
inputs:
  duckdb_tables: "none — reads filesystem only"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
  report: "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Inventory counts produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "Full census — no sampling or thresholds."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json and .md exist and are non-empty."
  continue_predicate: "Inventory artifacts exist on disk."
  halt_predicate: "Raw directory does not exist or is empty."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_01_02 — Schema Discovery

```yaml
step_number: "01_01_02"
name: "Schema Discovery"
description: "Map the column-level structure of all three aoestats file types (Parquet matches, Parquet players, JSON overview). Determine whether schemas are consistent across the weekly temporal range and whether matches and players share structurally overlapping columns."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoestats"
question: "What columns exist in each file type, what are their data types, does the schema remain stable across the weekly temporal range, and do matches and players share overlapping column names?"
method: "Full census of Parquet file metadata for matches (172 files) and players (171 files). Read overview.json structure. Compare schemas within each subdirectory for consistency and cross-compare matches/players for structural overlap. Report column catalogs, types, and consistency verdicts. No DuckDB type proposals — deferred to ingestion design."
stratification: "By subdirectory. Full census within each."
predecessors:
  - "01_01_01"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_02_schema_discovery.py"
inputs:
  duckdb_tables: "none — reads raw file metadata directly"
  prior_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 1"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  report: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Schema profiles produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "Full census — no sampling or thresholds."
  - number: "9"
    how_upheld: "Conclusions limited to column-level structural observations — no value distributions or DuckDB type proposals."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json and .md exist and are non-empty."
  continue_predicate: "Schema artifacts exist and report a consistency verdict for all subdirectories."
  halt_predicate: "Any Parquet file fails to open."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_01 — DuckDB Pre-Ingestion

```yaml
step_number: "01_02_01"
name: "DuckDB Pre-Ingestion"
description: "Determine how aoestats's variant-typed columns (7 columns whose Parquet type differs across weekly files) behave under DuckDB type promotion, and whether NULL patterns in the ingested tables match the file-level column presence/absence census."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoestats"
question: "What does the raw data look like before we commit to an ingestion strategy — are there type promotion traps for variant columns, interval-type handling issues, or NULL patterns that need handling?"
method: "Full census of Parquet metadata across all weekly files to establish per-column type distributions for the 7 variant columns. Smoke-test temporally-stratified file samples into in-memory DuckDB. DESCRIBE schemas, verify type promotions and interval handling, and cross-check NULL counts against file-level column presence. Investigate the matches/players file-count asymmetry (172 vs 171). Produce a design artifact for the full-ingestion step."
stratification: "By subdirectory (matches, players, overview)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py"
inputs:
  duckdb_tables:
    - "none — investigation uses temporary in-memory DB"
  prior_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
    - "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json"
  report: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All census code, smoke-test SQL, DESCRIBE output, and NULL counts in the notebook."
  - number: "7"
    how_upheld: "Variant column type distributions from full Parquet metadata census."
  - number: "9"
    how_upheld: "Conclusions limited to type mappings, NULL patterns, and file-count reconciliation — no content profiling."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json and .md exist and are non-empty."
  continue_predicate: "Design artifact documents DuckDB types for all 3 table types AND variant columns have expected promoted types AND NULL patterns match file-level census AND smoke test passed."
  halt_predicate: "DuckDB cannot read Parquet files with union_by_name, OR smoke test reveals unresolvable type conflicts."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_02 — DuckDB Ingestion

```yaml
step_number: "01_02_02"
name: "DuckDB Ingestion"
description: "Materialise raw aoestats data into persistent DuckDB tables: matches_raw (172 weekly Parquet with union_by_name), players_raw (171 weekly Parquet with union_by_name), overviews_raw (singleton overview.json). All tables carry filename provenance. filename column stores path relative to raw_dir (no absolute paths)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoestats"
question: "Can we materialise all three raw tables with correct type promotions for variant columns and provenance?"
method: "Call ingestion module functions against the persistent DuckDB. Validate with DESCRIBE, row counts, NULL rates on key fields. Verify filename column exists in all tables and variant columns have expected promoted types."
stratification: "By table (matches_raw, players_raw, overviews_raw)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_02_duckdb_ingestion.py"
inputs:
  duckdb_tables:
    - "none — creates tables"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json"
  report: "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All ingestion SQL in the module, validation SQL in the notebook."
  - number: "7"
    how_upheld: "All tables carry filename provenance column."
  - number: "9"
    how_upheld: "Conclusions limited to ingestion success, row counts, column types, and NULL rates."
  - number: "10"
    how_upheld: "filename column in all tables stores path relative to raw_dir; no absolute paths."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "All three DuckDB tables created with expected row counts. All tables have filename column. filename values are relative paths (no leading /)."
  halt_predicate: "Any table creation fails OR row count is zero."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_03 — Raw Schema DESCRIBE

```yaml
step_number: "01_02_03"
name: "Raw Schema DESCRIBE"
description: "Establish the definitive column-name and column-type snapshot for every aoestats *_raw table. Connects read-only to the persistent DuckDB populated by 01_02_02 and runs DESCRIBE on all three tables. Output feeds the data/db/schemas/raw/*.yaml source-of-truth files consumed by all downstream steps."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoestats"
question: "What are the exact column names and DuckDB types for matches_raw, players_raw, and overviews_raw as materialised in the persistent DuckDB?"
method: "Connect read-only to persistent DuckDB. DESCRIBE each *_raw table. Write JSON artifact. Populate data/db/schemas/raw/*.yaml schema files."
stratification: "By table (matches_raw, players_raw, overviews_raw)."
predecessors:
  - "01_02_02"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_raw_schema_describe.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
    - "overviews_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json"
  schema_files:
    - "data/db/schemas/raw/matches_raw.yaml"
    - "data/db/schemas/raw/players_raw.yaml"
    - "data/db/schemas/raw/overviews_raw.yaml"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All DESCRIBE SQL embedded in notebook; JSON artifact records exact schema seen."
  - number: "7"
    how_upheld: "Column types and nullability taken from DESCRIBE output, not assumed."
  - number: "9"
    how_upheld: "Read-only step — no tables modified."
  - number: "10"
    how_upheld: "filename column confirmed present in all three tables."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json exists and non-empty. data/db/schemas/raw/*.yaml files populated for all three tables."
  continue_predicate: "Column counts confirmed: matches_raw=18, players_raw=14, overviews_raw=9."
  halt_predicate: "Any table cannot be described or column count is zero."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_04 — Univariate Census

```yaml
step_number: "01_02_04"
name: "Univariate Census"
description: "Compute a comprehensive univariate census for all 32 columns across matches_raw (18 cols) and players_raw (14 cols). Cover target variable class balance, NULL rates, cardinality, numeric descriptive statistics (mean, median, stddev, p05/p25/p75/p95), IQR outlier counts, skewness/kurtosis, ELO sentinel detection, opening strategy non-NULL distribution, and temporal range. Output a JSON artifact consumed by Step 01_02_05 for visualization."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
dataset: "aoestats"
question: "What are the univariate distributions, NULL rates, and value profiles for every column in matches_raw and players_raw? What is the target variable class balance? What fraction is 1v1?"
method: "Full-table aggregations using DuckDB SQL. NULL census, cardinality, numeric stats (percentiles via PERCENTILE_CONT), IQR outlier counts, skewness/kurtosis, sentinel detection, opening strategy non-NULL distribution. No sampling."
stratification: "By table (matches_raw, players_raw)."
predecessors:
  - "01_02_03"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  report: "artifacts/01_exploration/02_eda/01_02_04_univariate_census.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries that produce reported statistics appear verbatim in the markdown artifact."
  - number: "7"
    how_upheld: "All bin widths, thresholds, and annotation values derived from query results — no magic numbers."
  - number: "9"
    how_upheld: "Read-only step — no DuckDB writes, no new tables, no schema changes."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json and .md exist and are non-empty."
  continue_predicate: "Census artifact contains all expected keys including skew_kurtosis_matches, elo_sentinel_counts, opening_nonnull_distribution, outlier_counts_matches, outlier_counts_players, temporal_range."
  halt_predicate: "Any SQL query fails or census artifact is missing required keys."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_05 — Univariate Visualizations

```yaml
step_number: "01_02_05"
name: "Univariate Visualizations"
description: "15 visualization plots for the aoestats univariate census findings from 01_02_04. Reads the 01_02_04 JSON artifact and queries DuckDB for histogram bin data. All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations on in-game, post-game, and leakage-unresolved columns per Invariant #3."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
dataset: "aoestats"
question: "What do the univariate distributions look like visually? Are there visual patterns not captured by summary statistics alone?"
method: "Read 01_02_04 JSON artifact. Query DuckDB for histogram bins (duration, ELO, old_rating, match_rating_diff, monthly volume). Produce 15 plots: winner 2-bar, num_players bar, map top-20 barh, civ top-20 barh, leaderboard bar, duration dual-panel, ELO 1x3 panel (sentinel excluded), old_rating histogram, match_rating_diff histogram (LEAKAGE UNRESOLVED annotated), age uptime 1x3 panel (IN-GAME annotated), opening non-NULL bar (IN-GAME annotated), IQR outlier summary, NULL rate bar (4-tier), schema change temporal boundary (IN-GAME annotated), monthly volume line chart."
stratification: "By column and table (matches_raw, players_raw)."
predecessors:
  - "01_02_04"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_05_winner_distribution.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_num_players_distribution.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_map_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_civ_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboard_distribution.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_duration_histogram.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_elo_distributions.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_old_rating_histogram.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_match_rating_diff_histogram.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_age_uptime_histograms.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_opening_nonnull.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_iqr_outlier_summary.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_null_rate_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_schema_change_boundary.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_monthly_match_count.png"
  report: "artifacts/01_exploration/02_eda/01_02_05_visualizations.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "duration annotated POST-GAME. opening and age uptimes annotated IN-GAME. match_rating_diff annotated LEAKAGE STATUS UNRESOLVED. new_rating not plotted (post-game, excluded)."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All bin widths, clip boundaries, color thresholds derived from census JSON at runtime. match_rating_diff clip at [-200, +200] is ~3.6sigma editorial choice (stddev=55.23)."
  - number: "9"
    how_upheld: "Visualization of 01_02_04 findings only. No new analytical computation."
gate:
  artifact_check: "All 15 PNG files exist under plots/. 01_02_05_visualizations.md exists with SQL queries (Invariant #6) and plot index table including Temporal Annotation column."
  continue_predicate: "All 15 PNG files exist. Markdown artifact contains plot index table with Temporal Annotation column and all SQL queries. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_06 — Bivariate EDA

```yaml
step_number: "01_02_06"
name: "Bivariate EDA"
description: "Bivariate EDA for aoestats: 8 plots investigating pairwise feature-target relationships. Resolves match_rating_diff leakage (Phase 02 blocker). Conditional distributions by winner, Spearman correlation matrix, opening win rates. All SQL embedded (Invariant #6). Temporal annotations on in-game and post-game columns (Invariant #3)."
phase: "01 -- Data Exploration"
pipeline_section: "01_02 -- Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
dataset: "aoestats"
question: "How do pairs of variables relate to each other and to the target (winner)? Is match_rating_diff a post-game leakage feature?"
method: "Single-table and JOIN queries on DuckDB. Sampled scatter for leakage check. DuckDB width_bucket aggregation for violin-style density estimation. Spearman matrix via DuckDB corr(). All thresholds from census JSON."
stratification: "By table (matches_raw, players_raw) and by target (winner True/False)."
predecessors:
  - "01_02_05"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_06_bivariate_eda.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_05_visualizations.md"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 2.1"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_06_match_rating_diff_leakage_scatter.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_old_rating_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_elo_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_duration_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_numeric_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_opening_winrate.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_age_uptime_by_winner.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_spearman_correlation.png"
  report: "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "duration annotated POST-GAME. opening and age uptimes annotated IN-GAME. match_rating_diff leakage status resolved by scatter and updated to LEAKAGE or PRE-GAME accordingly."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All sample fractions, bin widths, sentinel exclusion thresholds derived from census JSON at runtime. Sample size justified by census row count."
  - number: "9"
    how_upheld: "Bivariate analysis only. No model fitting, no feature engineering, no cleaning decisions."
gate:
  artifact_check: "All 8 PNG files exist under plots/. 01_02_06_bivariate_eda.json and .md exist and are non-empty."
  continue_predicate: "All 8 PNG files exist. match_rating_diff leakage status resolved in JSON artifact (field: bivariate_results[\"match_rating_diff_leakage\"][\"leakage_status\"] = 'LEAKAGE' or 'PRE_GAME'). Markdown artifact contains all SQL queries and plot index table with Temporal Annotation column. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails or match_rating_diff leakage status cannot be determined."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
  - "Chapter 4 -- Data and Methodology > 4.2 Pre-processing"
research_log_entry: "Required on completion."
```

### Step 01_02_07 — Multivariate EDA

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

---

### Step 01_03_01 — Systematic Data Profiling

```yaml
step_number: "01_03_01"
name: "Systematic Data Profiling"
description: "Comprehensive column-level and dataset-level profile for matches_raw (18 cols) and players_raw (14 cols). Column-level: null counts, zero counts, cardinality, descriptive stats, skewness, kurtosis, IQR outliers, top-k values. Dataset-level: row counts, duplicate detection, class balance, completeness matrix, linkage integrity, memory footprint. Critical detection: dead fields, constant columns, near-constant columns. Distribution analysis: QQ plots and empirical CDFs with RESERVOIR(50K) sampling. All columns annotated with I3 temporal class. ELO sentinels reported with and without exclusion."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoestats"
question: "What is the comprehensive column-level and dataset-level statistical profile for matches_raw and players_raw? What are the dead, constant, and near-constant columns? How do key numeric columns compare to the normal distribution?"
method: "Full-table DuckDB aggregations for column-level stats. RESERVOIR(50000) sampling for QQ plots and ECDFs. Duplicate detection via census-aligned COALESCE string-concatenation key."
stratification: "By table (matches_raw, players_raw). ELO columns: with and without sentinel."
predecessors:
  - "01_02_07"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_01_systematic_profiling.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 3"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  plots:
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_completeness_heatmap.png"
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_qq_matches.png"
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_qq_players.png"
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_ecdf_key_columns.png"
  report: "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Every column in the profile JSON carries a temporal_class annotation (PRE-GAME, IN-GAME, POST-GAME, TARGET, CONTEXT, IDENTIFIER). Classification derived from 01_02_04/01_02_06 census findings."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "No magic numbers. Sample size 50K justified by SE of quantile estimates. IQR fence multiplier 1.5 is Tukey (1977) standard. ELO sentinel -1 from census. NEAR_CONSTANT_CARDINALITY_CAP=5 justified by constant-column boundary (cardinality=1) plus buffer. All NULL thresholds from census JSON."
  - number: "9"
    how_upheld: "Profiling only. No cleaning decisions, no feature engineering, no model fitting. Critical findings are flagged for 01_04, not acted upon."
gate:
  artifact_check: "All 6 artifact files exist under reports/artifacts/01_exploration/03_profiling/ and are non-empty."
  continue_predicate: "JSON contains critical_findings key. MD contains I3 classification table. All 4 PNG files exist. Notebook executes end-to-end without errors."
  halt_predicate: "Any SQL query fails or any artifact is missing or empty."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
  - "Chapter 4 -- Data and Methodology > 4.2 Pre-processing"
research_log_entry: "Required on completion."
```

### Step 01_03_02 -- True 1v1 Match Identification

```yaml
step_number: "01_03_02"
name: "True 1v1 Match Identification"
description: "Cross-reference matches_raw.num_players against actual player row counts from players_raw to identify genuine 1v1 matches (exactly 2 active players). Compare against leaderboard-based filtering. Document discrepancies, orphaned matches, and edge cases. Profiling only -- no cleaning decisions."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoestats"
question: "Which matches are genuine 1v1 (exactly 2 active players), how does num_players relate to actual player counts, and how does the true 1v1 set compare to leaderboard='random_map'?"
method: "JOIN matches_raw with aggregated players_raw player counts per game_id. Cross-tabulate num_players vs actual_player_count. Compute leaderboard-vs-player-count overlap."
stratification: "By num_players value. By leaderboard value. By match type (true 1v1 vs label 1v1)."
predecessors:
  - "01_03_01"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 3"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
  plots:
    - "artifacts/01_exploration/03_profiling/01_03_02_match_type_breakdown.png"
  report: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "No magic numbers. All row counts, NULL rates, and thresholds from census JSON or systematic profile JSON. The 'active player' definition is schema-derived, not a magic number."
  - number: "9"
    how_upheld: "Profiling only. No cleaning decisions, no feature engineering, no model fitting. Findings are documented for 01_04, not acted upon."
gate:
  artifact_check: "All 3 artifact files exist under reports/artifacts/01_exploration/03_profiling/ and are non-empty."
  continue_predicate: "JSON contains keys: true_1v1_count, ranked_1v1_count, overlap, num_players_vs_actual_crosstab. MD contains comparison table. PNG file exists."
  halt_predicate: "Any SQL query fails or any artifact is missing or empty."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
  - "Chapter 4 -- Data and Methodology > 4.2 Pre-processing"
research_log_entry: "Required on completion."
```

### Step 01_03_03 -- Table Utility Assessment

```yaml
step_number: "01_03_03"
name: "Table Utility Assessment"
description: "Empirical assessment of all 3 raw tables for prediction pipeline utility. Column overlap, join integrity, ELO redundancy between match-level and player-level ratings, overviews_raw STRUCT content (all 6 arrays), replay_summary_raw fill rate, and evidence-backed per-table verdicts."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
dataset: "aoestats"
question: "Which tables are essential, which are redundant, and which are supplementary? Is avg_elo deterministically derivable from players_raw.old_rating? What does overviews_raw contain? Is replay_summary_raw viable as a feature source?"
method: "DESCRIBE both match-player tables. Set algebra for column overlap. Anti-join integrity checks. Formula check for avg_elo = (team_0_elo + team_1_elo)/2. Cross-table ELO derivation check for 1v1 matches. 100K RESERVOIR Spearman sample. UNNEST all 6 overviews_raw STRUCT arrays. replay_summary_raw fill-rate census."
predecessors:
  - "01_03_02"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_03_table_utility.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
    - "overviews_raw"
  prior_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_03_table_utility.json"
  report: "artifacts/01_exploration/03_profiling/01_03_03_table_utility.md"
reproducibility: "Code and output in the paired notebook. All SQL queries stored verbatim in JSON artifact."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "old_rating annotated as pre-game safe; new_rating flagged as temporal leakage (post-game)."
  - number: "6"
    how_upheld: "All SQL queries stored verbatim in sql_queries dict and written to JSON artifact."
  - number: "7"
    how_upheld: "No magic numbers. Constants derived from 01_03_01 and 01_03_02 artifacts."
  - number: "9"
    how_upheld: "Assessment only. No cleaning, no feature decisions. Verdicts documented for downstream steps."
gate:
  artifact_check: "artifacts/01_exploration/03_profiling/01_03_03_table_utility.json and .md exist and are non-empty."
  continue_predicate: "JSON contains keys t01_column_overlap, t02_join_integrity, t03_elo_redundancy, t04_overviews_and_replay, t05_verdicts. Verdicts recorded for all 4 objects."
  halt_predicate: "Any SQL query fails or any artifact is missing."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

---

## Pipeline Section 01_04 -- Data Cleaning

### Step 01_04_00 -- Source Normalization to Canonical Long Skeleton

```yaml
step_number: "01_04_00"
name: "Source Normalization to Canonical Long Skeleton"
description: >
  Creates the matches_long_raw VIEW: a canonical 10-column long skeleton with one row
  per player per match. JOIN of players_raw (per-player rows) with matches_raw (per-match
  metadata), filtered identically to player_history_all (profile_id IS NOT NULL,
  started_timestamp IS NOT NULL). Lossless validation uses an independent anchor
  (players_raw total of 107,627,584 minus independently-counted exclusions). No further
  filtering, no cleaning, no feature computation.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4"
dataset: "aoestats"
question: >
  Can players_raw JOIN matches_raw be projected losslessly into the canonical 10-column
  long skeleton that all downstream cleaning steps will operate against?
method: >
  INNER JOIN of players_raw x matches_raw on game_id, filtered identically to
  player_history_all. Lossless check uses independent anchor (players_raw total minus
  null profile_id minus orphan/null-ts rows). Symmetry audit confirms known side=1
  win asymmetry (~52.27% in random_map 1v1 scope) reappears. leaderboard_raw
  (m.leaderboard VARCHAR) allows downstream 1v1 scoping without rejoining.
predecessors:
  - "01_04_01"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_00_source_normalization.py"
outputs:
  duckdb_views:
    - "matches_long_raw"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.md"
  schema_yaml: "data/db/schemas/views/matches_long_raw.yaml"
gate:
  artifact_check: >
    JSON artifact exists with row_count, schema, lossless_check (independent anchor),
    symmetry_audit (full and 1v1-scoped), leaderboard_raw_distribution, and all SQL
    queries verbatim. matches_long_raw VIEW is queryable and returns 107,626,399 rows.
    Anchor cross-check: total_players_raw == 107,627,584.
    Schema YAML exists with row_count populated.
  continue_predicate: >
    Lossless check PASSED (view_count == total_players - null_profile - orphan_or_null_ts).
    STEP_STATUS.yaml has 01_04_00: complete.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      old_rating retained. new_rating and match_rating_diff excluded. I3 preserved.
  - number: "5"
    how_upheld: >
      Player-row-oriented VIEW. No slot-based pivoting. Both players in any match
      are represented with the same 10-column structure.
  - number: "6"
    how_upheld: "All SQL queries written verbatim to JSON artifact under sql_queries."
  - number: "9"
    how_upheld: >
      No features computed. Only rows with null profile_id or null started_timestamp
      excluded (matching player_history_all filter). Raw data untouched.
research_log_entry: "Required on completion."
```

### Step 01_04_01 -- Data Cleaning — VIEW DDL + Missingness Audit (insight-gathering)

```yaml
step_number: "01_04_01"
name: "Data Cleaning — VIEW DDL + Missingness Audit (insight-gathering)"
description: >
  Two-part step with one execution pass.
  PART A (already executed in PRs #138/#139): non-destructive cleaning of
  matches_raw and players_raw via two DuckDB VIEWs (matches_1v1_clean,
  player_history_all) — all DDL changes resolved in prior PRs.
  PART B (this revision): consolidated missingness audit over the analytical VIEWs
  (matches_1v1_clean, player_history_all). Two coordinated census passes per VIEW —
  SQL NULL census plus sentinel census driven by per-column _missingness_spec — plus
  a runtime constants-detection check, feed one missingness ledger (CSV+JSON) per
  VIEW. The audit gathers insights for downstream cleaning decisions in 01_04_02+;
  it does NOT execute decisions, modify VIEWs, drop columns, or impute. Ends with
  an explicit "Decisions surfaced for downstream cleaning" section listing
  per-dataset open questions (DS-AOESTATS-01..08).
phase: "01 — Data Exploration"
pipeline_section: "01_04 — Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 3 (Profiling) and 4 (Cleaning)"
dataset: "aoestats"
question: >
  What is the complete missingness picture (NULL + sentinel-encoded + constant
  columns) per analytical VIEW column, classified by mechanism (Rubin 1976
  MCAR/MAR/MNAR), and which open questions must downstream 01_04 steps resolve
  before Phase 02 imputation design?
method: >
  Three-step per-VIEW audit (matches_1v1_clean, player_history_all):
  Step 1 (kept verbatim): SQL NULL census per column via
  COUNT(*) FILTER (WHERE col IS NULL) over the full VIEW.
  Step 2 (NEW): sentinel census per column driven by _missingness_spec dict
  (per-column override is preferred; auto-detection from prior census artifacts is
  the secondary fallback). Sentinel SQL per column matches the spec's declared
  sentinel value(s).
  Step 3 (NEW): runtime constants detection — SELECT COUNT(DISTINCT col) per VIEW
  column; columns with n_distinct=1 get mechanism="N/A" + recommendation="DROP_COLUMN".
  Per-row recommendation derived from pct_missing_total = pct_null + pct_sentinel
  via the decision tree in temp/null_handling_recommendations.md §3.1, applying
  Rules S1-S6, with two override layers: (a) F1 zero-missingness override and
  (b) target-column override per Rule S2. The notebook produces RECOMMENDATIONS
  only; downstream 01_04 steps decide and execute.
  Reads the empirical sentinel patterns from
  artifacts/01_exploration/02_eda/01_02_04_univariate_census.json — the audit
  consolidates prior findings; it does not re-derive them.
predecessors:
  - "01_03_03"
methodology_citations:
  - "Rubin, D.B. (1976). Inference and missing data. Biometrika, 63(3), 581-592. — MCAR/MAR/MNAR taxonomy."
  - "Little, R.J. & Rubin, D.B. (2019). Statistical Analysis with Missing Data, 3rd ed. Wiley. — Authoritative mechanism classification."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed. CRC Press. — Warns against rigid percentage thresholds; threshold S4 used as starting heuristic only."
  - "Schafer, J.L. & Graham, J.W. (2002). Missing data: Our view of the state of the art. Psychological Methods, 7(2), 147-177. — Listwise deletion acceptable at <5% MCAR (boundary citation, not threshold derivation)."
  - "Sambasivan, N. et al. (2021). Everyone wants to do the model work, not the data work: Data Cascades in High-Stakes AI. CHI '21. — Rationale for surfacing decisions explicitly rather than deferring."
  - "Davis, J. et al. (2024). Methodology and Evaluation in Sports Analytics. Machine Learning, 113, 6977-7010. — Domain precedent for sports outcome data quality protocols (retained for future Phase 02/03 reference; not load-bearing in this audit step)."
  - "scikit-learn v1.8 documentation. Imputation of missing values; sklearn.impute.MissingIndicator. — Missingness-as-signal principle for Phase 02."
  - "Wirth, R. & Hipp, J. (2000). CRISP-DM: Towards a standard process model for data mining. — Cleaning report convention adopted in artifact format."
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §3 (Profiling) and §4 (Cleaning) — pipeline phase boundary (Phase 01 documents, Phase 02 transforms)."
notebook_path: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py"
inputs:
  duckdb_tables:
    - "matches_raw (30,690,651 rows)"
    - "players_raw (107,627,584 rows)"
  duckdb_views:
    - "matches_1v1_clean (17,814,947 rows)"
    - "player_history_all (107,626,399 rows)"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json (sentinel and zero-distribution evidence)"
    - "artifacts/01_exploration/03_profiling/* (column-level mechanism evidence — see prior steps)"
outputs:
  duckdb_views:
    - "matches_1v1_clean (unchanged)"
    - "player_history_all (unchanged)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (extended with missingness_audit block)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (NEW — one row per (view, column); full-coverage Option B; zero-missingness columns tagged RETAIN_AS_IS / mechanism=N/A; constant columns tagged DROP_COLUMN / mechanism=N/A)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json (NEW — same content, machine-readable)"
  report: "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (extended)"
reproducibility: >
  Code and output in the paired notebook. All SQL verbatim in JSON sql_queries.
  Audit re-runs deterministically from raw tables.
key_findings_carried_forward:
  - "997 inconsistent winner rows excluded (both players same outcome, 0.0056%)"
  - "Schema change boundary 2024-03-17: opening/age-uptime columns drop to 0% coverage"
  - "t1_win_pct 52.27%: team=1 wins more often than team=0 (slot asymmetry — I5 warning)"
  - "team_0_elo / team_1_elo: ELO=-1 sentinel absent in matches_1v1_clean scope (filtered out by ranked 1v1 restriction)"
  - "p0_old_rating / p1_old_rating: sentinel=0 present in matches_1v1_clean (n_sentinel=4730 / 188 respectively)"
  - "old_rating in player_history_all: sentinel=0, n_sentinel=5,937 (consistent with 01_02_04 census)"
  - "avg_elo: sentinel=0, n_sentinel=118 in matches_1v1_clean"
  - "leaderboard and num_players: constants in matches_1v1_clean (n_distinct=1) — DROP_COLUMN flagged"
decisions_surfaced:
  - id: "DS-AOESTATS-01"
    column: "team_0_elo / team_1_elo (sentinel=-1, absent in 1v1 filtered scope)"
    question: >
      team_0_elo / team_1_elo: ELO=-1 sentinel ABSENT in matches_1v1_clean (upstream
      filter excludes the rows that carried it — the matches_1v1_clean WHERE clause
      restricts to ranked-1v1 decisive games where the sentinel does not appear).
      Ledger reports n_sentinel=0 → RETAIN_AS_IS / mechanism=N/A. Action item: if
      the ranked-1v1 scope is ever broadened, or if a different VIEW (e.g. unranked
      or non-1v1) is added to the audit, re-audit for sentinel resurfacing and
      reapply CONVERT_SENTINEL_TO_NULL via Rule S3. The spec entry retains
      mechanism=MCAR / sentinel_value=-1 to document the design intent for the
      mechanism (raw matches_raw evidence shows the sentinel exists at low rate);
      the ledger reflects the empirical post-filter observation.
  - id: "DS-AOESTATS-02"
    column: "p0_old_rating / p1_old_rating (sentinel=0, n_zero=5,937 in players_raw)"
    question: >
      NULLIF + listwise deletion per Rule S3 in 01_04_02+ DDL pass,
      OR retain 0 as an explicit unrated categorical encoding alongside is_unrated?
      Source: players_raw_census.old_rating.zero_count=5937 (zero_pct=0.0055%).
      B6 deferral: audit recommends CONVERT_SENTINEL_TO_NULL (non-binding for
      carries_semantic_content=True). Downstream chooses without prejudice from the ledger.
  - id: "DS-AOESTATS-03"
    column: "avg_elo (n_sentinel=118 in matches_1v1_clean / n_zero=121 in matches_raw)"
    question: >
      avg_elo: n_sentinel=118 in matches_1v1_clean / n_zero=121 in matches_raw
      (numeric_stats_matches[label='avg_elo'] ground truth). Same MAR /
      CONVERT_SENTINEL_TO_NULL recommendation; the 3-row difference is the
      upstream 1v1 filter discarding 3 sentinel rows. Disposition (genuine zero
      vs sentinel) deferred to 01_04_02+ join investigation. Note: the n_zero=4,824
      figure cited in earlier drafts belongs to team_0_elo, NOT avg_elo.
  - id: "DS-AOESTATS-04"
    column: "raw_match_type (7,055 NULLs in matches_1v1_clean, 0.0396%)"
    question: >
      MCAR per Rule S3, listwise deletion candidate at 01_04_02+. Column may be redundant
      given internalLeaderboardId already constrains scope. Ledger reports RETAIN_AS_IS
      (rate < 5% MCAR boundary).
  - id: "DS-AOESTATS-05"
    column: "team1_wins (prediction target, BIGINT)"
    question: >
      0 NULLs verified (upstream WHERE p0.winner != p1.winner exclusion).
      F1 zero-missingness override: ledger reports RETAIN_AS_IS / mechanism=N/A.
      The phantom winner column referenced in v1 plan does NOT exist in matches_1v1_clean.
  - id: "DS-AOESTATS-06"
    column: "winner in player_history_all"
    question: >
      winner in player_history_all: ledger reports 0 NULLs / RETAIN_AS_IS /
      mechanism=N/A (better than plan-anticipated ~5% rate). The upstream
      players_raw filtering or the players_raw schema does not produce NULL
      winners in the loaded dataset. CONSORT note: re-verify on every dataset
      re-load; if winner NULLs surface in future loads, the target-override
      post-step (B4) will fire automatically and convert recommendation to
      EXCLUDE_TARGET_NULL_ROWS — no Phase 02 code change required.
  - id: "DS-AOESTATS-07"
    column: "overviews_raw (singleton metadata, 1 row)"
    question: >
      Formally declare out-of-analytical-scope at 01_04_02+ disposition step.
      Not used by any VIEW; triaging not required in 01_04_01 audit.
  - id: "DS-AOESTATS-08"
    column: "leaderboard, num_players (constants in matches_1v1_clean)"
    question: >
      Constants-detection branch flags both columns as n_distinct=1 in matches_1v1_clean
      (all ranked 1v1 rows have identical leaderboard='random_map' and num_players=2).
      Ledger reports DROP_COLUMN / mechanism=N/A. Confirm removal in 01_04_02+ DDL pass.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No new feature computation. No use of game T data. Audit is read-only over
      VIEWs whose I3 compliance was established in the predecessor PRs.
  - number: "6"
    how_upheld: >
      All three SQL templates (NULL census, sentinel census, constants detection)
      stored verbatim in JSON sql_queries. The per-column sentinel queries are
      reconstructible from the template + the _missingness_spec dict (also stored
      in the artifact).
  - number: "7"
    how_upheld: >
      Thresholds (5%/40%/80%) follow the operational starting heuristics in
      temp/null_handling_recommendations.md §1.2; cite Schafer & Graham 2002 for
      the <5% MCAR boundary and van Buuren 2018 for the warning against rigid
      global thresholds. Each threshold-driven recommendation surfaces as a
      downstream decision per §3.1; the audit recommends, the downstream step
      decides. Per-column mechanism justifications cite either a prior step's
      artifact (with path) or a sentinel-meaning interpretation explicitly grounded
      in domain context.
  - number: "9"
    how_upheld: >
      All facts derive from this step's SQL or from cited predecessor artifacts.
      No raw tables, no VIEWs, no schema YAMLs are modified. Audit is purely
      additive: extends artifact JSON, adds two new ledger files. No future-step
      citations.
gate:
  artifact_check: >
    JSON has "missingness_audit" block with two VIEW ledger arrays, each containing
    one row per column in the VIEW (full-coverage Option B) and the _missingness_spec
    used. The two new ledger files (CSV + JSON) exist at the paths above. MD has a
    "Missingness Ledger" section per VIEW + a final "Decisions surfaced for downstream
    cleaning (01_04_02+)" section reproducing DS-AOESTATS-01..08 with current
    observed rates filled in.
  continue_predicate: >
    Every column in each VIEW appears in the ledger (full-coverage Option B).
    Every column with non-zero missingness has a _missingness_spec entry; zero-
    missingness rows carry mechanism=N/A, recommendation=RETAIN_AS_IS, and
    justification="Zero missingness observed; no action needed." regardless of
    spec. Constant columns (n_distinct=1) carry mechanism=N/A,
    recommendation=DROP_COLUMN with constants-detection justification.
    Every ledger row has non-empty mechanism_justification, recommendation,
    recommendation_justification, and explicit carries_semantic_content boolean.
    Existing zero-NULL assertions (game_id, started_timestamp, p0_profile_id,
    p1_profile_id, p0_winner, p1_winner in matches_1v1_clean; profile_id,
    game_id, started_timestamp in player_history_all) still pass.
  halt_predicate: >
    Any column in the VIEW missing from the ledger (full-coverage violation);
    any column with non-zero missingness lacking a _missingness_spec entry; any
    ledger row missing mandatory fields; any zero-NULL identity assertion failure;
    any contradictory pairing of mechanism="N/A" with non-N/A justification.
research_log_entry: >
  Required on completion: list per-VIEW row counts in ledger, reference the
  artifact paths, summarise decisions surfaced for downstream resolution.
```

### Step 01_04_02 -- Data Cleaning Execution

```yaml
step_number: "01_04_02"
name: "Data Cleaning Execution -- Act on DS-AOESTATS-01..08"
description: >
  Acts on the 8 cleaning decisions surfaced by 01_04_01. Modifies VIEW DDL
  for matches_1v1_clean and player_history_all (no raw table changes per
  Invariant I9): drops leaderboard + num_players (DS-AOESTATS-08 constants),
  drops raw_match_type (DS-AOESTATS-04 redundant), applies NULLIF on
  p0/p1/avg_elo + old_rating (DS-AOESTATS-02/03) plus 3 new is_unrated
  indicator flags. Documents DS-AOESTATS-01 (sentinel ABSENT in 1v1 scope,
  RETAIN_AS_IS with scope-expansion contingency), DS-AOESTATS-05/06 (zero
  NULLs verified), DS-AOESTATS-07 (overviews_raw out-of-analytical-scope).
  Reports CONSORT-style column-count flow + subgroup impact + post-cleaning
  invariant re-validation.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4"
dataset: "aoestats"
question: >
  Which of the 8 decisions surfaced by 01_04_01 (DS-AOESTATS-01..08) are
  resolved by DDL modifications, what is the column-count and subgroup
  impact, and do all post-cleaning invariants still hold?
method: >
  Modify CREATE OR REPLACE VIEW DDL for matches_1v1_clean and
  player_history_all per per-DS resolutions (see plan Section 1). Apply
  column drops, NULLIF transformations, and 3 new derived is_unrated
  indicator columns. Re-run the assertion battery from 01_04_01 plus
  01_04_02-specific assertions on the new column set. Produce a
  CONSORT-style column-count table and per-DS resolution log.
stratification: "By VIEW (matches_1v1_clean vs player_history_all) and by DS-AOESTATS-NN."
predecessors:
  - "01_04_01"
methodology_citations:
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.1 (cleaning registry), §4.2 (non-destructive), §4.3 (CONSORT impact), §4.4 (post-validation)"
  - "Liu, X. et al. (2020). CONSORT-AI extension. BMJ, 370."
  - "Jeanselme, V. et al. (2024). Participant Flow Diagrams for Health Equity in AI. JBI, 152."
  - "Schafer, J.L. & Graham, J.W. (2002). Missing data: Our view of the state of the art. Psych Methods, 7(2)."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed. CRC Press."
  - "Sambasivan, N. et al. (2021). Data Cascades in High-Stakes AI. CHI '21."
notebook_path: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py"
inputs:
  duckdb_views:
    - "matches_1v1_clean (17,814,947 rows / 21 cols -- pre-01_04_02)"
    - "player_history_all (107,626,399 rows / 13 cols -- pre-01_04_02)"
  prior_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (cleaning_registry, missingness_audit, consort_flow)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (34 rows, per-DS empirical evidence)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (decisions_surfaced reference)"
  schema_yamls:
    - "data/db/schemas/views/player_history_all.yaml (current -- to be UPDATED)"
outputs:
  duckdb_views:
    - "matches_1v1_clean (replaced via CREATE OR REPLACE -- 20 cols, 17,814,947 rows)"
    - "player_history_all (replaced via CREATE OR REPLACE -- 14 cols, 107,626,399 rows)"
  schema_yamls:
    - "data/db/schemas/views/matches_1v1_clean.yaml (NEW)"
    - "data/db/schemas/views/player_history_all.yaml (UPDATED)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md"
reproducibility: >
  Code and output in the paired notebook. All DDL stored verbatim in the
  validation JSON sql_queries block (Invariant I6). All thresholds derived
  from the 01_04_01 ledger CSV at runtime (Invariant I7). Re-runs deterministically.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No new feature computation. matches_1v1_clean retains only PRE_GAME
      + IDENTITY + TARGET columns. player_history_all retains PRE_GAME
      and CONTEXT columns (old_rating PRE_GAME-safe; no IN-GAME or
      POST-GAME columns introduced).
  - number: "5"
    how_upheld: >
      Player-slot symmetry warning preserved as DDL comment (team=1 wins
      ~52.27% per 01_04_01 t1_win_pct finding); the p0/p1 columns are
      symmetrically modified (NULLIF + is_unrated applied to both slots
      identically). Phase 02 must randomise focal/opponent assignment.
  - number: "6"
    how_upheld: >
      All DDL queries stored verbatim in JSON sql_queries. All assertion
      SQL stored verbatim. All per-DS rationale references the ledger row
      + ledger recommendation_justification by view+column.
  - number: "7"
    how_upheld: >
      Thresholds (5/40/80%) come from the 01_04_01 framework block
      (Schafer & Graham 2002 boundary; van Buuren 2018 warning). Per-DS
      empirical evidence (n_sentinel, pct_missing_total, n_distinct) is
      read from the 01_04_01 ledger CSV at runtime, not hardcoded.
  - number: "9"
    how_upheld: >
      No raw tables modified. matches_long_raw (canonical skeleton from
      01_04_00) unmodified. Only matches_1v1_clean and player_history_all
      VIEWs are replaced via CREATE OR REPLACE. All inputs are 01_04_01
      artifacts (predecessor) or this step's own DDL output.
  - number: "10"
    how_upheld: >
      No filename derivation changes. The aoestats raw tables already
      satisfy I10 from 01_02_02 ingestion.
gate:
  artifact_check: >
    artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json
    and .md exist and are non-empty. Both schema YAMLs
    (matches_1v1_clean.yaml NEW, player_history_all.yaml UPDATED) exist
    with correct column counts.
  continue_predicate: >
    matches_1v1_clean has exactly 20 columns. player_history_all has
    exactly 14 columns. All zero-NULL assertions pass (game_id,
    started_timestamp, p0/p1_profile_id, p0/p1_winner, team1_wins in
    matches_1v1_clean; profile_id, game_id, started_timestamp, winner in
    player_history_all). Forbidden columns absent (DS-AOESTATS-04/-08
    drops + I3 pre-existing exclusions). NULLIF effects match ledger-derived
    expected_p0_unrated / expected_p1_unrated / expected_avg_elo_sentinel /
    expected_unrated values within +-1 row (loaded at runtime per I7).
    is_unrated indicator counts equal NULLIF NULL counts (consistency).
    Row counts unchanged. CONSORT
    column-count table reproduces drop counts per DS-AOESTATS-01..08.
    STEP_STATUS.yaml has 01_04_02: complete. PIPELINE_SECTION_STATUS for
    01_04 transitions to complete (no further 01_04_NN steps defined in
    ROADMAP).
  halt_predicate: >
    Any zero-NULL assertion fails; any inconsistent winner row appears;
    any forbidden column appears; any expected NEW column missing; column
    count off by even one from spec; NULLIF count diverges from ledger
    by more than +-1 row.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data > Data Cleaning Decisions"
research_log_entry: "Required on completion."
```

#### ADDENDUM 2026-04-18 — duration_seconds + is_duration_suspicious

Extends `matches_1v1_clean` from 20 cols to 22 cols. STEP_STATUS stays `complete`
(column-only addendum per precedent of 01_04_03 addendum pattern).

New columns added to `matches_1v1_clean`:

| Column | Type | Classification | Derivation |
|---|---|---|---|
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL | `CAST(m.duration / 1000000000 AS BIGINT)` — divisor cites `aoestats/pre_ingestion.py:271` (Arrow `duration[ns]` -> BIGINT per DuckDB 1.5.1) |
| `is_duration_suspicious` | BOOLEAN | POST_GAME_HISTORICAL | `duration_seconds > 86400` — 24h cross-dataset canonical sanity bound (I8 contract; ~25x p99 from 01_04_03 Gate+5b) |

**Gate results (all PASS):**
- 22 cols confirmed (DESCRIBE); last 2 = `duration_seconds BIGINT` + `is_duration_suspicious BOOLEAN`
- Row count 17,814,947 unchanged
- `COUNT(*) FILTER (WHERE duration_seconds IS NULL) == 0`
- `MAX(duration_seconds) = 5,574,815 <= 1,000,000,000` (unit canary PASS)
- `COUNT(*) FILTER (WHERE is_duration_suspicious) == 28` (expected 28 from 01_04_03 56 player-rows / 2)
- Schema YAML: `schema_version: "22-col (ADDENDUM: duration added 2026-04-18)"` + 22 col entries + I3/I7 invariants

**New validation artifact:** `artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation_validation.json` + `.md`

**Suspicious matches (28 game_ids with duration_seconds > 86400):** See validation artifact
`suspicious_game_ids` list. Top example: game_id 184213201 (~64.5 days = raw-data corruption).

**Duration stats:**
- min: 3s, p50: 2,455s (~40.9 min), p99: 5,729s (~95.5 min), max: 5,574,815s (~64.5 days)
- null_count: 0, suspicious_count: 28 (0.00016% of dataset)

---

### Step 01_04_03 -- Minimal Cross-Dataset History View

```yaml
step_number: "01_04_03"
name: "Minimal Cross-Dataset History View"
description: >
  Create matches_history_minimal VIEW: 8-column player-row-grain projection
  of matches_1v1_clean via UNION ALL of p0/p1 halves (pivot from 1-row-per-
  match to 2-rows-per-match). Cross-dataset-harmonized substrate for Phase
  02+ rating-system backtesting. Canonical TIMESTAMP temporal dtype (cast
  from TIMESTAMPTZ via AT TIME ZONE 'UTC'). Per-dataset-polymorphic faction
  vocabulary (full civ names). Sibling of sc2egset 01_04_03 (PR #152) and
  aoe2companion 01_04_03 (same bundled PR).
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4.2, Section 4.4"
dataset: "aoestats"
question: >
  Can matches_1v1_clean (1-row-per-match p0/p1) be projected to the cross-
  dataset 8-column contract (2-rows-per-match) via UNION ALL without slot
  bias propagation into the output won distribution?
method: >
  CREATE OR REPLACE VIEW matches_history_minimal. UNION ALL of p0_half +
  p1_half CTEs. started_at cast TIMESTAMPTZ -> TIMESTAMP via AT TIME ZONE
  'UTC'. Slot-bias assertion: AVG(won::INT) = 0.5 exactly (UNION erases
  upstream team1_wins ~52.27% slot asymmetry at output level because each
  match contributes exactly 1 won + 1 lost).
predecessors:
  - "01_04_02"
methodology_citations:
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.2, §4.4"
  - "Tukey, J. W. (1977). Exploratory Data Analysis."
notebook_path: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py"
inputs:
  duckdb_views:
    - "matches_1v1_clean (20 cols, 17,814,947 matches -- from 01_04_02)"
  schema_yamls:
    - "data/db/schemas/views/matches_1v1_clean.yaml"
outputs:
  duckdb_views:
    - "matches_history_minimal (NEW -- 8 cols, 35,629,894 rows)"
  schema_yamls:
    - "data/db/schemas/views/matches_history_minimal.yaml (NEW)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.md"
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      TIMESTAMP cast from TIMESTAMPTZ via AT TIME ZONE 'UTC'. Chronologically
      faithful ordering on canonical cross-dataset dtype.
  - number: "5"
    how_upheld: >
      Player-row symmetry (I5-analog) via IS DISTINCT FROM NULL-safe comparison.
      Slot-bias gate (aoestats-specific): AVG(won::INT) = 0.5 exactly documents
      UNION ALL erasing upstream slot asymmetry.
  - number: "6"
    how_upheld: >
      DDL + all assertion SQL verbatim in validation JSON sql_queries block.
  - number: "7"
    how_upheld: >
      Prefix check: LIKE 'aoestats::%' + non-empty tail. game_id is VARCHAR
      opaque (no numeric regex — contrast aoec's matchId INTEGER case).
  - number: "8"
    how_upheld: >
      8-col cross-dataset contract (identical to sc2egset and aoec sibling
      views). Canonical TIMESTAMP. Polymorphic faction vocabulary (~50 civ
      names; consumers MUST game-condition).
  - number: "9"
    how_upheld: >
      Pure non-destructive projection. No upstream modification.
gate:
  artifact_check: >
    Validation JSON + MD exist; matches_history_minimal.yaml exists with 8
    columns + invariants block.
  continue_predicate: >
    VIEW exists with 8 columns matching spec. 35,629,894 rows = 17,814,947 × 2.
    Zero symmetry violations, zero prefix violations, dataset_tag distinct = 1,
    zero NULLs in 7 non-nullable cols, AVG(won::INT) = 0.5 exactly.
  halt_predicate: >
    Any gate fails; dtype != TIMESTAMP; slot-bias AVG deviates from 0.5.
    Manual PIPELINE_SECTION_STATUS revert on T02 failure.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data > Cross-dataset harmonization substrate"
  - "Chapter 4 -- Data and Methodology > 4.3 Rating System Backtesting Design"
research_log_entry: "Required on completion."
```

### Step 01_04_04 -- Identity Resolution

```yaml
step_number: "01_04_04"
name: "Identity Resolution"
description: >
  Exploratory census of the aoestats identity structure. aoestats has no
  nickname column in any raw table (structural asymmetry confirmed in 01_01_02).
  profile_id (DOUBLE in players_raw; BIGINT in player_history_all) is the sole
  identity signal. Invariant I2 (lowercased nickname as canonical) is natively
  unmeetable; this step characterises the profile_id field, probes behavioural
  surrogate stability (civ-fingerprint JSD), assesses replay_summary_raw for
  hidden name extraction, and provides an empirical cross-dataset feasibility
  preview (aoestats profile_id vs aoe2companion profileId namespace overlap).
  Output routes DS-AOESTATS-IDENTITY-01..05 decisions to Phase 02.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 4 and 5"
dataset: "aoestats"
question: >
  Is profile_id reliable, sentinel-free, and globally unique? Can civ-frequency
  distribution stability substitute for nickname-based identity resolution?
  Do aoestats profile_id and aoe2companion profileId share a namespace?
method: >
  Task A -- Sentinel + NULL audit: 4 columns x 3 tables/views with n_rows,
  n_null, n_zero, n_negative, n_minus_one, min, max, cardinality.
  Task B -- Per-profile activity distribution: match-count and active-day
  quantiles on player_history_all; single-day and multi-ladder profile counts.
  Task C -- Duplicate (game_id, profile_id) census in players_raw; census-aligned
  COALESCE key methodology (anchor: 489 from 01_03_01; HALT if drift > 10).
  Task D -- Rating-trajectory monotonicity probe: 10,000-profile reservoir
  (seed=20260418); LAG(old_rating) deltas; count |delta| > 500; p99/max.
  Task E -- replay_summary_raw JSON parseability probe on 1,000-row sample;
  report format (Python dict not JSON), mean/max length, top keys (feasibility
  only -- no name extraction).
  Task F -- Civ-fingerprint JSD: profiles with >= 20 matches AND >= 180 active
  days; first-half vs second-half 50-dim civ distribution JSD (within-profile);
  10,000-random-pair cross-profile control JSD; quantiles p5/p25/p50/p75/p95/p99.
  Task G -- Cross-dataset feasibility: ATTACH aoec DB (READ_ONLY); 1,000-match
  reservoir from 2026-01-25..2026-01-31; 60s temporal + civ-set + 50-ELO block;
  agreement rate + 95% bootstrap CI + verdict rubric.
predecessors:
  - "01_04_03"
methodology_citations:
  - "Hahn, Siqueira Ruela, & Rebelo Moreira (2020). Identifying Players in StarCraft via Behavioural Fingerprinting. IEEE CoG."
  - "Fellegi, I.P. & Sunter, A.B. (1969). A theory for record linkage. JASA 64(328)."
  - "Christen, P. (2012). Data Matching. Springer -- blocking (Ch. 4)."
notebook_path: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_04_identity_resolution.py"
inputs:
  duckdb_tables:
    - "players_raw (107,627,584 rows; profile_id DOUBLE)"
  duckdb_views:
    - "player_history_all (107,626,399 rows; profile_id BIGINT)"
    - "matches_1v1_clean (17,814,947 rows; p0/p1_profile_id BIGINT)"
  attached_db:
    - "aoe2companion/data/db/db.duckdb AS aoec (READ_ONLY) -- Task G only"
  prior_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json (489 duplicate anchor)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.md"
reproducibility: >
  All SQL verbatim in JSON sql_queries (I6). Reservoir seeds documented (20260418).
  Bootstrap CI for cross-dataset agreement rate: 10,000 resamples.
scientific_invariants_applied:
  - number: "2"
    how_upheld: >
      No nickname column exists -- confirms I2 is natively unmeetable for aoestats.
      Behavioral fingerprint (civ JSD) is identified as the best available proxy,
      with explicit hedging against use as a substitute for rename detection.
  - number: "6"
    how_upheld: "All SQL queries verbatim in JSON sql_queries block."
  - number: "7"
    how_upheld: >
      500 ELO threshold (Task D) -- anecdotal RTS convention, hedged in MD.
      50 ELO blocking band (Task G) -- derived from 01_03_03 0.5-ELO redundancy
      finding (~100x conservative). 60s temporal block -- conventional API delay.
      0.10/0.30/0.50 JSD thresholds -- symmetric KL interpretation, hedged in MD.
  - number: "9"
    how_upheld: >
      Exploration only. No new VIEWs, no raw-table modifications, no schema YAML changes.
gate:
  artifact_check: >
    JSON + MD exist under artifacts/01_exploration/04_cleaning/. All SQL verbatim
    in sql_queries block. 5+ DS-AOESTATS-IDENTITY-* decisions with full fields.
  continue_predicate: >
    Task C duplicate count in 479-499 (489 +/- 10). Cross-dataset verdict stated
    with CI + sample size + rubric citation. git diff --stat empty on raw/view YAMLs.
  halt_predicate: >
    Task C duplicate count outside 479-499. Cross-dataset CI disjoint from aoec T06
    (disagree on verdict grade). Any raw/view YAML modified.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data > Identity Key Selection"
research_log_entry: "Required on completion."
```

---

### Step 01_04_05 -- Team-Slot Asymmetry Diagnosis (I5)

```yaml
step_number: "01_04_05"
name: "Team-Slot Asymmetry Diagnosis (I5)"
description: >
  Diagnoses the upstream team=1 win-rate asymmetry (52.27%) found in 01_04_01
  and documented in matches_1v1_clean.yaml. Determines whether the asymmetry is
  a genuine competitive slot edge (GENUINE_EDGE), an upstream API logging artifact
  (ARTEFACT_EDGE), or inconclusive (MIXED). Five diagnostic queries: (Q1) slot-proxy
  x ELO-ordering cross-tabulation; (Q2) Mantel-Haenszel CMH stratified by civ-pair
  x year-quarter; (Q3) hash-seeded null calibration; (Q4) profile_id control;
  (Q5) temporal drift. Supplementary ELO audit provides mechanistic confirmation.
  Path-1 ingestion audit ruled out locally-assigned team position.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
dataset: "aoestats"
completed_at: "2026-04-18"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_05_i5_diagnosis.py"
predecessors:
  - "01_04_01"
  - "01_04_02"
  - "01_04_03"
key_findings:
  verdict: "ARTEFACT_EDGE"
  cmh_effect_pp: -0.72
  elo_audit: "team=1 has higher ELO in 80.3% of games (mean +11.9 ELO points)"
  root_cause: >
    Upstream API assigns team=1 to the invite-initiating or better-matched player.
    The 52.27% win rate is fully explained by the ELO differential, not by any
    game-mechanical slot effect. team field MUST NOT be used as a Phase 02 feature.
  phase_02_action: >
    Use focal/opponent pair representation symmetrically (I5). Do not use team
    as a feature or stratification variable. UNION-ALL pivot in
    matches_history_minimal confirmed I5-compliant.
outputs:
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.md"
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No temporal leakage risk in this diagnostic step -- no feature computation,
      pure observational diagnosis of existing view.
  - number: "5"
    how_upheld: >
      Diagnosis confirms I5 violation in raw team field; UNION-ALL pivot is the
      correct I5-compliant downstream representation. team field excluded from
      Phase 02 feature engineering.
  - number: "6"
    how_upheld: "All SQL queries verbatim in JSON sql_queries block with SHA-256 checksums."
  - number: "7"
    how_upheld: >
      Effect-size thresholds: 1pp (minimum practical significance), 1.5pp
      (GENUINE_EDGE floor), 0.5pp (ARTEFACT_EDGE ceiling) -- documented as
      effect-size floors, not NHST cutoffs. Tiebreaker (MIXED -> ARTEFACT_EDGE)
      justified by schema-amendment dominance argument.
  - number: "9"
    how_upheld: >
      Exploration only. No new VIEWs, no raw-table modifications, no schema YAML changes.
research_log_entry: "Added 2026-04-18."
```

---

## Pipeline Section 01_05 -- Temporal & Panel EDA

**Spec binding:** `reports/specs/01_05_preregistration.md@7e259dd8`
**Reference window:** 2022-08-29..2022-10-27, patch 66692 (verified from `overviews_raw`)
**Primary quarters tested:** 2023-Q1..2024-Q4 (8 quarters)
**Critique fixes applied:** B1 (non-vacuous leakage check), B2 (feature-type routing in PSI), B3 (counterfactual reference); M1 (Simpson probe), M2 (secondary ANOVA ICC), M3 (stratified reservoir sample), M4 (focal_old_rating slot fix), M5 (15-column note), M6 (per-slot [PRE-canonical_slot] tagging), M7 (branch-v ICC limitation), M8 (duration sensitivity)

### Step 01_05_01 -- Quarterly Grain Audit

```yaml
step_number: "01_05_01"
name: "Quarterly Grain Audit"
description: "Audit the quarterly grain of matches_history_minimal. Verify that QUARTER() DuckDB function produces correct calendar-quarter labels (not float-valued EXTRACT formula). Assert 10 quarters 2022-Q3..2024-Q4 exist and report row counts per quarter."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_01_quarterly_grain.py"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/quarterly_grain_row_counts.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/quarterly_grain_row_counts.json"
  report: "artifacts/01_exploration/05_temporal_panel_eda/quarterly_grain_row_counts.md"
gate:
  artifact_check: "quarterly_grain_row_counts.{csv,json,md} exist and are non-empty."
  continue_predicate: "10 quarters confirmed. No float-valued quarter labels."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_02 -- PSI Pre-Game Features

```yaml
step_number: "01_05_02"
name: "PSI Pre-Game Features"
description: "Compute Population Stability Index for 8 pre-game features (focal_old_rating, avg_elo, faction, opponent_faction, mirror, p0_is_unrated, p1_is_unrated, map) across 8 quarters (2023-Q1..2024-Q4) vs 2022-Q3 reference. Feature-type routing: continuous (decile PSI), binary (Cohen's h), categorical (__unseen__ bin). M4 critique fix: focal_old_rating uses CASE WHEN CAST(player_id AS BIGINT) = p0_profile_id for slot-agnostic derivation. B3: counterfactual reference (2023-Q1) also emitted."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_02_psi_pre_game_features.py"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/psi_aoestats_{quarter}.csv (x8)"
    - "artifacts/01_exploration/05_temporal_panel_eda/psi_aoestats_counterfactual_2023Q1ref.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/01_05_02_psi_summary.json"
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_02_psi_summary.md"
gate:
  artifact_check: "8 PSI CSVs + counterfactual CSV + summary JSON exist."
  continue_predicate: "PSI verdict PASSED (rating PSI >= 0.10 in >= 2 quarters)."
falsifier: "All rating PSI values < 0.10 across all quarters."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_03 -- Stratification and Patch Regime

```yaml
step_number: "01_05_03"
name: "Stratification and Patch Regime"
description: "Map 19 patches from overviews_raw to quarters. Identify multi-patch quarters. M1 Simpson probe: compute per-patch win rates and patch heterogeneity decomposition per Chitayat et al. 2023 (arxiv.org/abs/2305.18477). Document patch transitions."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_03_stratification_patch_regime.py"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/patch_map.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/patch_quarter_distribution.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/patch_transitions_flagged.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/patch_heterogeneity_decomposition.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/patch_civ_win_rates.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/01_05_03_patch_regime_summary.json"
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_03_patch_regime_summary.md"
gate:
  artifact_check: "All CSV artifacts and summary JSON exist."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_04 -- Survivorship Triple Analysis

```yaml
step_number: "01_05_04"
name: "Survivorship Triple Analysis"
description: "Compute unconditional survivorship (fraction active per quarter) and sensitivity analysis for aoestats. Uses compute_fraction_active() and compute_n_match_cohort() from survivorship module."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_04_survivorship_triple.py"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/survivorship_unconditional.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/survivorship_sensitivity.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/01_05_04_survivorship_summary.json"
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_04_survivorship_summary.md"
gate:
  artifact_check: "Both CSV files and summary JSON exist."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_05 -- Variance Decomposition (ICC)

```yaml
step_number: "01_05_05"
name: "Variance Decomposition (ICC)"
description: "Compute ICC for won outcome using LMM (statsmodels MixedLM REML) and ANOVA (Wu/Crespi/Wong 2012 CCT 33(5):869-880) with bootstrap CI (Ukoumunne 2012 PMC3426610). M2 critique: primary LMM + secondary ANOVA. M3: stratified reservoir sample at 20k, 50k, 100k. M7: branch-v limitation documented."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_05_variance_decomposition_icc.py"
hypothesis: "ICC >= 0.15 (meaningful skill signal). Falsifier: ICC < 0.05."
result: "FALSIFIED: ANOVA ICC (50k) = 0.0268. Attributed to early crawler period (2022-Q3, 744 active players)."
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.json"
    - "artifacts/01_exploration/05_temporal_panel_eda/icc_sample_profile_ids_{20k,50k,100k}.csv"
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.md"
gate:
  artifact_check: "icc_results.json and 3 sample ID CSVs exist."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_06 -- Temporal Leakage Audit v1

```yaml
step_number: "01_05_06"
name: "Temporal Leakage Audit v1"
description: "Four-query leakage audit. Q7.1 (B1 fix): non-vacuous future-data check -- count post-reference rows for cohort players. Q7.2: POST_GAME/TARGET token scan of feature list. Q7.3: reference window assertion. Q7.4 (M6 fix): canonical_slot readiness + [PRE-canonical_slot] tagging check. Verdict: PASS."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit.py"
result: "PASS. canonical_slot absent; [PRE-canonical_slot] flag ACTIVE."
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.json"
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.md"
gate:
  artifact_check: "audit JSON and MD exist."
  continue_predicate: "Overall verdict = PASS."
  halt_predicate: "BLOCKED_FUTURE_LEAK or BLOCKED_POST_GAME_TOKEN."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_07 -- DGP Diagnostics (Duration)

```yaml
step_number: "01_05_07"
name: "DGP Diagnostics (Duration)"
description: "POST_GAME_HISTORICAL diagnostic for duration_seconds. Cohen's d vs reference for 8 primary quarters. Excluded from PSI per spec §4. DGP diagnostic CSVs for 2022-Q3Q4ref + 8 quarters."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_07_dgp_diagnostics_duration.py"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/dgp_diagnostic_aoestats_*.csv (9 files)"
    - "artifacts/01_exploration/05_temporal_panel_eda/01_05_07_dgp_diagnostic_summary.json"
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_07_dgp_diagnostic_summary.md"
gate:
  artifact_check: "9 DGP CSVs and summary JSON exist."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_08 -- Phase 06 Interface Emission

```yaml
step_number: "01_05_08"
name: "Phase 06 Interface Emission"
description: "Assemble Phase 06 interface CSV from PSI + counterfactual + ICC + DGP rows. Schema: 9 columns (dataset_tag, quarter, feature_name, metric_name, metric_value, reference_window_id, cohort_threshold, sample_size, notes). B3: both primary and counterfactual PSI. M5: notes column documents 15 columns analyzed."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.py"
result: "134 rows, 9 columns. Schema validation PASSED."
outputs:
  data_artifacts:
    - "artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv"
    - "artifacts/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface_schema_validation.json"
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface_schema_validation.md"
gate:
  artifact_check: "phase06_interface_aoestats.csv exists with 9 columns and >= 64 rows."
research_log_entry: "Added 2026-04-18."
```

### Step 01_05_09 -- Gate Memo

```yaml
step_number: "01_05_09"
name: "Gate Memo"
description: "Summarize all 01_05 step results, document BACKLOG F1 (canonical_slot absent -- Phase 02 unblocker), confirm gate passage for 01_05, and document M7 branch-v ICC limitation."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoestats"
spec: "reports/specs/01_05_preregistration.md@7e259dd8"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.py"
outputs:
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md"
gate:
  artifact_check: "gate_memo.md exists and is non-empty."
research_log_entry: "Added 2026-04-18."
```

---

### Step 01_06_01 -- Data Dictionary

```yaml
step_number: "01_06_01"
name: "Data Dictionary"
description: "Enumerate every column consumed downstream in Phase 02 from matches_1v1_clean,
  player_history_all, and matches_history_minimal. Flag team=0/team=1 columns as
  '[PRE-canonical_slot]' in invariant_notes. Assign temporal_classification per I3.
  Produce data_dictionary_aoestats.csv and .md companion per spec 01_06_readiness_criteria.md §1.1."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoestats"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_01_data_dictionary.py"
inputs:
  - "reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  - "reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json"
outputs:
  data_artifacts:
    - "reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoestats.csv"
  report: "reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoestats.md"
gate:
  artifact_check: "CSV and MD exist."
  continue_predicate: "team=0/team=1 columns flagged [PRE-canonical_slot] in invariant_notes."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > §4.1.2 AoE2 datasets"
research_log_entry: "Required on completion."
```

### Step 01_06_02 -- Data Quality Report

```yaml
step_number: "01_06_02"
name: "Data Quality Report"
description: "Consolidate aoestats 01_04 cleaning artifacts into CONSORT flow including
  the 28 corrupt-duration matches dropped in rm_1v1. Cleaning rule registry must reference
  cleaning.yaml R01..RNN with leaderboard='random_map' scope anchor.
  Produce data_quality_report_aoestats.md per spec §1.2."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoestats"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_02_data_quality_report.py"
inputs:
  - "reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json"
  - "reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  - "reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv"
outputs:
  report: "reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoestats.md"
gate:
  artifact_check: "MD exists with CONSORT flow and rule registry."
  continue_predicate: "CONSORT flow balanced."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > §4.2.3 Cleaning rules"
research_log_entry: "Required on completion."
```

### Step 01_06_03 -- Risk Register

```yaml
step_number: "01_06_03"
name: "Risk Register"
description: "Enumerate INVARIANTS.md §5 PARTIAL rows (I2 branch-v, I5 slot-asymmetry,
  I8 ICC-FALSIFIED) as risks. Add BLOCKER row for canonical_slot-pending team=1 skill
  bias (W3 ARTEFACT_EDGE; BACKLOG F1). Produce risk_register_aoestats.csv and .md per spec §1.3."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoestats"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_03_risk_register.py"
inputs:
  - "reports/INVARIANTS.md"
  - "planning/BACKLOG.md"
  - "reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md"
outputs:
  data_artifacts:
    - "reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.csv"
  report: "reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.md"
gate:
  artifact_check: "CSV and MD exist."
  continue_predicate: "BLOCKER row for BACKLOG F1 canonical_slot present."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > §4.4.6 canonical_slot flag"
research_log_entry: "Required on completion."
```

### Step 01_06_04 -- Modeling Readiness Decision

```yaml
step_number: "01_06_04"
name: "Modeling Readiness Decision"
description: "Consume 01_06_01..03 artifacts; produce READY_CONDITIONAL verdict with
  flip-predicate: BACKLOG F1 + W4 both resolved. State Phase 02 narrower scope:
  aggregate / UNION-ALL-symmetric features only; per-slot features deferred until
  F1+W4. Produce modeling_readiness_aoestats.md per spec §1.4."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoestats"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py"
inputs:
  - "reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoestats.csv"
  - "reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoestats.md"
  - "reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.csv"
outputs:
  report: "reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md"
gate:
  artifact_check: "MD exists with READY_CONDITIONAL verdict and F1+W4 flip-predicate."
  continue_predicate: "Flip-predicate explicitly states F1+W4 coupling."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > §4.1.2 AoE2 datasets"
research_log_entry: "Required on completion."
```

---

## Phase 02 — Feature Engineering (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 01 gate is met.

---

## Phase 03 — Splitting & Baselines (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 02 gate is met.

---

## Phase 04 — Model Training (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 03 gate is met.

---

## Phase 05 — Evaluation & Analysis (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 04 gate is met.

---

## Phase 06 — Cross-Domain Transfer (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 05 gate is met.

---

## Phase 07 — Thesis Writing Wrap-up (gate marker)

Per `docs/PHASES.md`, Phase 07 is a gate marker with no Pipeline Sections.
This dataset's Phase 07 gate is met when all thesis sections fed by this
dataset have reached FINAL status in `thesis/WRITING_STATUS.md`.
