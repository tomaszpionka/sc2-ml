# aoe2companion Dataset Roadmap

**Game:** AoE2
**Dataset:** aoe2companion
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`
**Research log:** `research_log.md` (sibling file — per-dataset reverse-chronological narrative)

---

> **Role: PRIMARY for sample-scale (D1) and temporal-coverage (D3)
> dimensions; co-PRIMARY for identity-rigor (D4); SUPPLEMENTARY on
> skill-signal (D2, ICC FALSIFIED 0.003), patch-resolution (D5), and
> N/A on in-game events (D6). Assigned at 01_06 per
> `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`.
> Rationale: 30.5M matches, rename-stable profileId at 2.57% / 3.55%
> (reconciled 2026-04-19). Skill-signal SUPPLEMENTARY status deferred
> to sc2egset primary.**

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the aoe2companion
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Steps are defined in a planning session before Phase work begins.

Steps are numbered `XX_YY_ZZ` where `XX` = Phase, `YY` = Pipeline Section,
`ZZ` = Step within that Pipeline Section.

---

## Source data

**aoe2companion CDN dump** — community match history and rating dataset.
Downloaded 2026-04-06. File counts and date ranges are from
Step 01_01_01 (file inventory).

| Subdirectory | Files | Size (MB) | Extensions |
|---|---|---|---|
| `leaderboards/` | 2 | 83.32 | `.parquet`: 1, `.gitkeep`: 1 |
| `matches/` | 2074 | 6621.52 | `.parquet`: 2073, `.gitkeep`: 1 |
| `profiles/` | 2 | 161.84 | `.parquet`: 1, `.gitkeep`: 1 |
| `ratings/` | 2073 | 2519.59 | `.csv`: 2072, `.gitkeep`: 1 |

**Total files:** 4153 (including root-level `README.md` and `_download_manifest.json`)
**Total size:** 9387.80 MB

**Raw data is immutable. The API download will not be repeated.**
Acquisition provenance is recorded in
`src/rts_predict/games/aoe2/datasets/aoe2companion/reports/README.md`.

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
description: "Establish a complete filesystem-level census of the aoe2companion raw data. This grounds all subsequent steps in verified file counts, sizes, date ranges, and directory structure."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoe2companion"
question: "How many files exist in each subdirectory, what date range do they span, and are there any temporal gaps between the matched file series (matches vs ratings)?"
method: "Full census of the raw directory tree. Count files, measure sizes, group by subdirectory. Extract dates from filenames to establish the temporal range and identify gaps."
stratification: "By subdirectory (matches, ratings, leaderboards, profiles)."
predecessors: "none — independent"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py"
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
description: "Map the column-level structure of all four aoe2companion file types (Parquet matches, CSV ratings, singleton leaderboards and profiles). Determine whether schemas are consistent across the full temporal range."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoe2companion"
question: "What columns exist in each file type, what are their data types, and does the schema remain stable across the temporal range or evolve over time?"
method: "Full census of Parquet file metadata for matches (2,073 files) and CSV headers for ratings (2,072 files). Read singleton leaderboard and profile schemas. Compare within each subdirectory for consistency and report column catalogs, types, and consistency verdicts. No DuckDB type proposals — deferred to ingestion design."
stratification: "By subdirectory. Full census within each — no sampling needed for Parquet metadata or CSV headers."
predecessors:
  - "01_01_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.py"
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
description: "Determine whether aoe2companion's four file types (Parquet matches, CSV ratings, singleton leaderboards and profiles) can be loaded into DuckDB with correct type mappings, and surface any traps (binary column encoding, CSV type inference, file-count asymmetry) before committing to full ingestion."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "What does the raw data look like before we commit to an ingestion strategy — are there type inference traps, binary column encoding issues, or NULL patterns that need handling?"
method: "Inspect Parquet binary column annotations to determine encoding strategy. Smoke-test temporally-stratified file samples into in-memory DuckDB. DESCRIBE schemas, preview rows, and assess NULL counts. Investigate the matches/ratings file-count asymmetry (2073 vs 2072). Produce a design artifact for the full-ingestion step."
stratification: "By subdirectory (matches, ratings, leaderboards, profiles)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py"
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
    how_upheld: "All smoke-test SQL, type inspection, and DESCRIBE output in the notebook."
  - number: "7"
    how_upheld: "Binary column encoding strategy justified by in-notebook Parquet metadata inspection."
  - number: "9"
    how_upheld: "Conclusions limited to type mappings, row counts, and file-count reconciliation — no content profiling."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json and .md exist and are non-empty."
  continue_predicate: "Design artifact documents DuckDB types for all 4 table types AND smoke test passed AND type inference traps identified and mitigation proposed."
  halt_predicate: "DuckDB cannot read any Parquet or CSV files, OR smoke test reveals unresolvable type conflicts."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_02 — DuckDB Ingestion

```yaml
step_number: "01_02_02"
name: "DuckDB Ingestion"
description: "Materialise raw aoe2companion data into persistent DuckDB tables: matches_raw (2,073 daily Parquet), ratings_raw (2,072 daily CSV with dtype decision from 01_02_01), leaderboard_raw (singleton Parquet), profiles_raw (singleton Parquet). All tables carry filename provenance. filename column stores path relative to raw_dir (no absolute paths)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "Can we materialise all four raw tables with correct types and provenance, applying the dtype decision from 01_02_01?"
method: "Call ingestion module functions against the persistent DuckDB. Validate with DESCRIBE, row counts, NULL rates on key fields. Verify filename column exists in all tables."
stratification: "By table (matches_raw, ratings_raw, leaderboard_raw, profiles_raw)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_02_duckdb_ingestion.py"
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
  continue_predicate: "All four DuckDB tables created with expected row counts. All tables have filename column. filename values are relative paths (no leading /)."
  halt_predicate: "Any table creation fails OR row count is zero."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_03 — Raw Schema DESCRIBE

```yaml
step_number: "01_02_03"
name: "Raw Schema DESCRIBE"
description: "Establish the definitive column-name and column-type snapshot for every aoe2companion raw source. Uses in-memory DuckDB with the same read parameters planned for 01_02_02 (binary_as_string=true, union_by_name=true, filename=true for Parquet; explicit dtypes for CSV) and LIMIT 0 to avoid loading any row data. Output feeds the data/db/schemas/raw/*.yaml source-of-truth files consumed by all downstream steps. When 01_02_02 has been executed, this step can instead connect read-only to the persistent DuckDB."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "What are the exact column names and DuckDB types for each aoe2companion raw source — matches, ratings, leaderboards, profiles — as they will appear after ingestion?"
method: "Connect to in-memory DuckDB. DESCRIBE SELECT * FROM read_parquet/read_csv(...) LIMIT 0 for each of the four sources using the same read options as 01_02_02. Write JSON artifact. Populate data/db/schemas/raw/*.yaml schema files."
stratification: "By source (matches, ratings, leaderboards, profiles)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_03_raw_schema_describe.py"
inputs:
  duckdb_tables: "none — in-memory DuckDB, reads files directly with LIMIT 0"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json"
  schema_files:
    - "data/db/schemas/raw/matches_raw.yaml"
    - "data/db/schemas/raw/ratings_raw.yaml"
    - "data/db/schemas/raw/leaderboards_raw.yaml"
    - "data/db/schemas/raw/profiles_raw.yaml"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All DESCRIBE SQL embedded in notebook; JSON artifact records exact schema seen."
  - number: "7"
    how_upheld: "Column types and nullability taken from DESCRIBE output, not assumed."
  - number: "9"
    how_upheld: "Read-only step — no DuckDB tables created, no files modified."
  - number: "10"
    how_upheld: "filename column confirmed present across all four sources."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json exists and non-empty. data/db/schemas/raw/*.yaml files populated for all four tables."
  continue_predicate: "Column counts confirmed: matches=55, ratings=8, leaderboards=19, profiles=14."
  halt_predicate: "Any source cannot be read or DESCRIBE returns zero columns."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```


### Step 01_02_04 -- Univariate Census

```yaml
step_number: "01_02_04"
name: "Univariate Census"
description: "Full univariate profiling of all four aoe2companion raw tables. NULL census (55 columns for matches_raw), cardinality, value distributions, descriptive statistics, target variable analysis (won), skewness/kurtosis, boolean column census, and categorical top-k profiles."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "What are the NULL rates, cardinality, value distributions, and descriptive statistics for all columns? What is the target variable (won) distribution and class balance?"
method: "Single-pass SUMMARIZE over matches_raw (277M rows). Targeted aggregation queries for NULL rates, categorical top-k, boolean census, skewness/kurtosis, intra-match consistency. Results saved to JSON artifact."
predecessors:
  - "01_02_02"
  - "01_02_03"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  report: "artifacts/01_exploration/02_eda/01_02_04_univariate_census.md"
gate:
  artifact_check: "01_02_04_univariate_census.json and .md exist and are non-empty."
  continue_predicate: "JSON artifact contains all required keys including won_distribution, won_consistency_2row, categorical_profiles, boolean_census, matches_raw_null_census."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_05 -- Univariate Census Visualizations

```yaml
step_number: "01_02_05"
name: "Univariate Census Visualizations"
description: "17 visualization plots for the aoe2companion univariate census findings from 01_02_04. Reads the 01_02_04 JSON artifact and queries DuckDB for histogram bin data. All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations on post-game columns per Invariant #3."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3.4"
dataset: "aoe2companion"
question: "What do the univariate distributions from 01_02_04 look like visually?"
method: "Read 01_02_04 JSON artifact. Query DuckDB for histogram bins (rating, ratingDiff, duration, monthly volume). Produce 17 plots: won 2-bar, won consistency stacked, leaderboard bar, civ top-20, map top-20 barh, rating histogram, ratingDiff histogram (POST-GAME annotated), duration dual-panel histogram, NULL rate bar (4-tier), NULL co-occurrence annotated 2x2 table, leaderboards_raw numeric boxplots, profiles_raw NULL rate bar, leaderboards_raw leaderboard bar, boolean stacked bar, monthly volume line chart, ratings_raw rating histogram, rating/ratingDiff NULL rate timeline. Markdown artifact with SQL queries and plot index table."
predecessors:
  - "01_02_04"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_05_won_distribution.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_won_consistency.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboard_distribution.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_civ_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_map_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_rating_histogram.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_ratingdiff_histogram.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_duration_histogram.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_null_rate_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_null_cooccurrence.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboards_numeric_boxplots.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_profiles_null_rate.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboards_leaderboard_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_boolean_stacked_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_monthly_volume.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_ratings_raw_rating_histogram.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_rating_null_timeline.png"
  report: "artifacts/01_exploration/02_eda/01_02_05_visualizations.md"
gate:
  artifact_check: "All 17 PNG files exist under plots/. 01_02_05_visualizations.md exists with SQL queries (Invariant #6) and plot index table including Temporal Annotation column."
  continue_predicate: "Notebook executes end-to-end without errors."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "ratingDiff histogram carries POST-GAME annotation. matches_raw.rating subtitle notes ambiguous temporal status."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All bin widths, clip boundaries, color thresholds, and annotation values derived from census JSON at runtime. No hardcoded numbers."
  - number: "9"
    how_upheld: "Visualization of 01_02_04 findings only. No new analytical computation."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_06 — Bivariate EDA

```yaml
step_number: "01_02_06"
name: "Bivariate EDA"
description: "Bivariate exploratory data analysis for aoe2companion. Conditional distributions of numeric features by won (violin plots), Spearman correlation matrix, rating vs ratingDiff scatter (sampled), ratingDiff by leaderboard. Resolves temporal leakage status of ratingDiff (Q1) and investigates rating ambiguity (Q2). All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations per Invariant #3."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "Which numeric features differ by outcome (won)? Which feature pairs are correlated? Is ratingDiff definitively post-game? Is rating pre- or post-game?"
method: "DuckDB aggregated queries for conditional distributions (PERCENTILE_CONT by won). TABLESAMPLE BERNOULLI for scatter plots (sample fraction derived from census total_rows at runtime, I7). Spearman correlation via scipy.stats.spearmanr on BERNOULLI-sampled rows (DuckDB CORR computes Pearson only). 8 plots. Markdown artifact with all SQL (I6)."
stratification: "By leaderboard (1v1 focus: rm_1v1 + qp_rm_1v1)."
predecessors:
  - "01_02_04"
  - "01_02_05"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_06_bivariate_eda.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "ratings_raw"
    - "leaderboards_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_rating_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_rating_vs_ratingdiff.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_duration_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_numeric_by_won.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_spearman_correlation.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_leaderboard.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_06_ratingdiff_by_won_by_leaderboard.png"
  report: "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
gate:
  artifact_check: "All 8 PNG files exist under plots/. 01_02_06_bivariate_eda.md exists with SQL queries (Invariant #6) and plot index table including Temporal Annotation column."
  continue_predicate: "Notebook executes end-to-end without error. ratingDiff temporal status resolved."
  halt_predicate: "DuckDB queries fail on matches_raw or sampling yields zero rows."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "ratingDiff violin carries POST-GAME annotation. rating violin carries AMBIGUOUS annotation. Q1 result resolves ratingDiff status definitively."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "Sample fraction derived from census total_rows at runtime. All clip boundaries, bin widths, and annotation values from census JSON. No hardcoded numbers."
  - number: "9"
    how_upheld: "Bivariate analysis of features established in 01_02_04. No new column discovery or schema changes."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
  - "Chapter 4 -- Data and Methodology > 4.1.4 Temporal Leakage Audit"
research_log_entry: "Required on completion."
```

### Step 01_02_07 -- Multivariate EDA

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

> **Deviation note:** `01_02_07_pca_scree.png` was not generated — PCA degenerated on the
> profile-aggregated feature set (insufficient pre-game numeric columns survived the I3 filter).
> The degenerate biplot (`01_02_07_pca_biplot.png`) is the sole PCA artifact, consistent with the
> `description` field's "degenerate fallback if <3 features survive" clause. The gate predicate
> ("At least one PCA plot exists") is satisfied by the biplot. See research_log 01_02_07 entry
> for details.

### Step 01_03_01 -- Systematic Data Profiling

```yaml
step_number: "01_03_01"
name: "Systematic Data Profiling"
description: "Systematic profiling of matches_raw per Manual Section 3. Column-level profiling (null, cardinality, descriptive stats, skewness, kurtosis, IQR outliers, top-k). Dataset-level profiling (duplicates, class balance, completeness matrix, memory footprint). Critical detection (dead fields, constant columns, near-constant columns). Distribution analysis (QQ plots, ECDFs on BERNOULLI sample). All columns carry I3 temporal classification."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "What is the complete statistical profile of every column in matches_raw? Are there dead fields, constant columns, near-constant columns, or primary key violations? What are the distributional shapes of key numeric columns?"
method: "DuckDB aggregate queries for exact column-level stats including native SKEWNESS() and KURTOSIS(). BERNOULLI sampled data for QQ plots and ECDFs. Critical detection via programmatic thresholds from census. I3 classification inherited from 01_02_04 field_classification and 01_02_06 bivariate findings."
stratification: "Full table for aggregate stats. Leaderboard-stratified (rm_1v1 + qp_rm_1v1) for rating analysis."
predecessors:
  - "01_02_04"
  - "01_02_06"
  - "01_02_07"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py"
inputs:
  duckdb_tables:
    - "matches_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md"
    - "artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  plots:
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_completeness_heatmap.png"
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_qq_plot.png"
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_ecdf_key_columns.png"
  report: "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md"
gate:
  artifact_check: "All 5 artifact files exist and are non-empty. JSON contains critical_findings key. MD contains I3 classification table."
  continue_predicate: "Notebook executes end-to-end without error. Profile JSON validates against required schema."
  halt_predicate: "DuckDB queries fail on matches_raw or BERNOULLI sample yields zero rows."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Every column carries I3 temporal classification in both JSON and MD artifacts. POST-GAME and AMBIGUOUS columns flagged in distribution analysis."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "Near-constant threshold (uniqueness_ratio < 0.001 or IQR == 0) from Manual 3.3. Sample fraction justified by Cleveland (1993) and Wilk & Gnanadesikan (1968). IQR fences from census percentiles."
  - number: "9"
    how_upheld: "Profile consolidates and extends 01_02 findings. No new column discovery or schema changes."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_03_02 -- True 1v1 Match Identification

```yaml
step_number: "01_03_02"
name: "True 1v1 Match Identification"
description: "Identify the full population of genuine 1v1 matches in matches_raw regardless of leaderboard. Profile the matchId grouping structure: rows-per-match distribution, true 1v1 criteria (exactly 2 human players, complementary won outcome), overlap with leaderboard-based 1v1 proxy, and edge cases (AI rows, NULL won, duplicate profileId=-1). Read-only profiling -- no tables or views created."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "Among all 61.8M distinct matchIds, which ones are genuine 1v1 matches (exactly 2 human players)? How does this set compare to the leaderboard-based 1v1 proxy? What edge cases exist?"
method: "DuckDB aggregate queries over matches_raw. GROUP BY matchId with HAVING-based structural criteria. Cross-tabulation with leaderboard. Won complement analysis. All SQL verbatim in artifact (I6)."
stratification: "Full table for aggregate counts. Leaderboard-stratified for overlap analysis."
predecessors:
  - "01_03_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py"
inputs:
  duckdb_tables:
    - "matches_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
  report: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md"
gate:
  artifact_check: "01_03_02_true_1v1_profile.json and .md exist and are non-empty."
  continue_predicate: "JSON contains rows_per_match_distribution, true_1v1_criteria_funnel_raw, leaderboard_overlap, and won_complement_analysis keys."
  halt_predicate: "DuckDB queries fail on matches_raw."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries written verbatim to JSON and MD artifacts."
  - number: "7"
    how_upheld: "1v1 criteria (exactly 2 human player rows) derived empirically from match structure, not assumed. Thresholds from census data."
  - number: "9"
    how_upheld: "Read-only profiling. No tables created. No cleaning decisions made. Findings feed 01_04."
  - number: "3"
    how_upheld: "No temporal features computed. Only structural grouping analysis."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_03_03 -- Table Utility Assessment

```yaml
step_number: "01_03_03"
name: "Table Utility Assessment"
description: "Empirical assessment of all 4 raw tables (matches_raw, ratings_raw, leaderboards_raw, profiles_raw) for prediction pipeline utility. Determine which tables carry temporal data suitable for pre-game feature derivation under I3, classify leaderboards_raw and profiles_raw as singleton snapshots or time series, and resolve the matches_raw.rating pre-game vs post-game ambiguity via cross-reference with ratings_raw."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "Which tables are I3-usable? Is matches_raw.rating pre-game or post-game?"
method: "DuckDB diagnostic queries on all 4 tables. Temporal property analysis (row count per player, updatedAt distribution). Cross-reference matches_raw.rating against ratings_raw per-game entries for lb=0 (unranked) for a focal player with 3,942+ matches. Hypothesis testing: pre-game match rate vs post-game match rate."
stratification: "Full table for structural queries. Single focal player for T02 case study."
predecessors:
  - "01_03_02"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_03_table_utility_assessment.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "ratings_raw"
    - "leaderboards_raw"
    - "profiles_raw"
  prior_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_03_table_utility_assessment.json"
  report: "artifacts/01_exploration/03_profiling/01_03_03_table_utility_assessment.md"
gate:
  artifact_check: "01_03_03_table_utility_assessment.json and .md exist and are non-empty."
  continue_predicate: "JSON contains table_verdicts for all 4 tables with i3_classification and t02_rating_disambiguation with verdict=PRE_GAME or AMBIGUOUS."
  halt_predicate: "DuckDB queries fail on any raw table."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Every table classified for I3 compliance. T02 test uses date <= started for nearest-before join (strict temporal discipline)."
  - number: "6"
    how_upheld: "All SQL queries written verbatim to JSON and MD artifacts."
  - number: "7"
    how_upheld: "No thresholds assumed -- all verdicts based on empirical match rates."
  - number: "9"
    how_upheld: "Read-only profiling. No tables created. No cleaning decisions made."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_04_00 — Source Normalization to Canonical Long Skeleton

```yaml
step_number: "01_04_00"
name: "Source Normalization to Canonical Long Skeleton"
description: >
  Creates the matches_long_raw VIEW: a canonical 10-column long skeleton with one row
  per player per match. Lossless projection of matches_raw into a unified schema shared
  across all three datasets (aoe2companion, aoestats, sc2egset). No filtering, no cleaning,
  no feature computation. Side reflects the source team encoding; any side-outcome correlation
  is preserved and documented as a finding rather than corrected at this stage.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4"
dataset: "aoe2companion"
question: >
  Can matches_raw be projected losslessly into the canonical 10-column long skeleton
  that all downstream cleaning steps will operate against?
method: >
  Pure column rename and projection -- matches_raw is already in long format (one row
  per player per match). Lossless check confirms row count equality. Symmetry audit
  documents side-outcome correlation. leaderboard_raw (internalLeaderboardId) is
  included to allow downstream 1v1 scoping without rejoining matches_raw.
predecessors:
  - "01_04_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_00_source_normalization.py"
outputs:
  duckdb_views:
    - "matches_long_raw"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.md"
  schema_yaml: "data/db/schemas/views/matches_long_raw.yaml"
gate:
  artifact_check: >
    JSON artifact exists with row_count, schema, lossless_check, symmetry_audit
    (full and 1v1-scoped), leaderboard_raw_distribution, and all SQL queries verbatim.
    matches_long_raw VIEW is queryable and returns 277,099,059 rows.
    Schema YAML exists with row_count populated.
  continue_predicate: >
    Lossless check PASSED (matches_long_raw rows == matches_raw rows).
    STEP_STATUS.yaml has 01_04_00: complete.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      started (temporal anchor) retained. ratingDiff and finished excluded.
      No post-game data included.
  - number: "5"
    how_upheld: >
      Player-row-oriented VIEW. No slot-based pivoting. Both players in any match
      are represented with the same 10-column structure.
  - number: "6"
    how_upheld: "All SQL queries written verbatim to JSON artifact under sql_queries."
  - number: "9"
    how_upheld: "No features computed. No rows filtered. Raw data untouched."
research_log_entry: "Required on completion."
```

### Step 01_04_01 — Data Cleaning — VIEW DDL + Missingness Audit (insight-gathering)

```yaml
step_number: "01_04_01"
name: "Data Cleaning — VIEW DDL + Missingness Audit (insight-gathering)"
description: >
  Two-part step with one execution pass.
  PART A (already executed in PRs #138/#139): non-destructive cleaning of
  matches_raw via three DuckDB VIEWs (matches_1v1_clean, player_history_all,
  ratings_clean) — all DDL changes resolved in prior PRs.
  PART B (this revision): consolidated missingness audit over the analytical VIEWs
  (matches_1v1_clean, player_history_all). Two coordinated census passes per VIEW —
  SQL NULL census plus sentinel census driven by per-column _missingness_spec — plus
  a runtime constants-detection check, feed one missingness ledger (CSV+JSON) per
  VIEW. The audit gathers insights for downstream cleaning decisions in 01_04_02+;
  it does NOT execute decisions, modify VIEWs, drop columns, or impute. Ends with
  an explicit "Decisions surfaced for downstream cleaning" section listing
  per-dataset open questions.
phase: "01 — Data Exploration"
pipeline_section: "01_04 — Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 3 (Profiling) and 4 (Cleaning)"
dataset: "aoe2companion"
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
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_01_data_cleaning.py"
inputs:
  duckdb_tables:
    - "matches_raw (raw player-match rows)"
    - "ratings_raw (per-player rating history)"
  duckdb_views:
    - "matches_1v1_clean (54 columns: 53 from matches_raw + is_null_cluster derived)"
    - "player_history_all (all game types, player-row-oriented)"
    - "ratings_clean (games column Winsorized at p99.9)"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json (sentinel and null-distribution evidence)"
    - "artifacts/01_exploration/03_profiling/* (column-level mechanism evidence — see prior steps)"
outputs:
  duckdb_views:
    - "matches_1v1_clean (unchanged)"
    - "player_history_all (unchanged)"
    - "ratings_clean (unchanged)"
  schema_yamls:
    - "data/db/schemas/views/player_history_all.yaml (unchanged from PR predecessor)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (extended with missingness_audit block)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (NEW — one row per (view, column); full-coverage Option B; zero-missingness columns tagged RETAIN_AS_IS / mechanism=N/A; constant columns tagged DROP_COLUMN / mechanism=N/A)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json (NEW — same content, machine-readable)"
  report: "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (extended)"
reproducibility: >
  Code and output in the paired notebook. All SQL verbatim in JSON sql_queries.
  Audit re-runs deterministically from raw tables.
key_findings_carried_forward:
  - "R01: scope restriction to rm_1v1 + qp_rm_1v1 leaderboards (IDs 6 and 18)"
  - "R02: deduplication by (matchId, profileId) ORDER BY started; profileId=-1 excluded"
  - "R03: won-complementarity filter — exactly 50/50 won distribution in matches_1v1_clean"
  - "R04: NULL cluster flagged (is_null_cluster) — tiny fraction (<0.02%), spans full date range"
  - "R05: ratings_raw.games Winsorized at empirical p99.9 threshold"
  - "NULL cluster MNAR finding: 10 game-settings simultaneously NULL correlates with schema-era boundary"
  - "rating ~26% NULL in matches_1v1_clean (ranked 1v1 scope); primary feature exception per Rule S4"
decisions_surfaced:
  - id: "DS-AOEC-01"
    columns: >
      server (97.39% in matches_1v1_clean / ~98% in raw matches_raw), scenario (100.00%
      / ~98.3%), modDataset (100.00% / ~99.7%), password (77.57% via 40-80%
      MAR-non-primary path / ~82.9% raw)
    question: >
      All four -> DROP_COLUMN at 01_04_02+ (per Rule S4). 'scenario' and 'modDataset'
      are 100% NULL in cleaned scope (every row is NULL — drop is unambiguous).
      'password' falls below the 80% boundary in the cleaned scope and is routed
      through the 40-80% non-primary cost-benefit path; intent (drop) is the same.
      Note: VIEW rates differ from raw rates due to the matches_1v1_clean ranked-
      1v1 filter — see the plan's note_on_rates for the principle.
  - id: "DS-AOEC-02"
    columns: >
      antiquityMode (60.06% in matches_1v1_clean / ~68.66% in raw — falls in 40-80%
      non-primary band -> DROP_COLUMN), hideCivs (37.18% in matches_1v1_clean /
      ~49.30% in raw — now falls in 5-40% band -> FLAG_FOR_IMPUTATION, NOT DROP_COLUMN
      as raw-rate framing implied)
    question: >
      Phase 02 decides if the imputed-with-indicator hideCivs is predictive; if not,
      drop in 01_04_02+. The recommendation drift between raw-rate (~49% suggesting
      drop) and VIEW-rate (37% suggesting flag) is a direct consequence of the
      matches_1v1_clean filter narrowing the scope; the audit reports VIEW-rate as
      authoritative.
  - id: "DS-AOEC-03"
    columns: >
      mod, map, difficulty, startingAge, fullTechTree, allowCheats, empireWarsMode,
      endingAge, gameMode, lockSpeed, lockTeams, mapSize, population, recordGame,
      regicideMode, gameVariant, resources, sharedExploration, speed, speedFactor,
      suddenDeathMode, civilizationSet, teamPositions, teamTogether, treatyLength,
      turboMode, victory, revealMap
    question: >
      Low-NULL game settings group. Each column individually enumerated in _missingness_spec
      with 01_02_04-grounded justification. Downstream disposition is RETAIN_AS_IS /
      FLAG_FOR_IMPUTATION per the observed rate. Constants-detection branch (W7) backs up
      any column not individually spec'd.
  - id: "DS-AOEC-04"
    column: "rating in matches_1v1_clean (~26% NULL in 1v1 scope per VIEW)"
    question: >
      Primary feature exception per Rule S4. Phase 02 imputation strategy
      (median-within-leaderboard + add_indicator) must be specified before Phase 02 begins.
  - id: "DS-AOEC-05"
    column: "country (~12.6% in raw, lower in 1v1 VIEW)"
    question: "Phase 02 — 'Unknown' category encoding or add_indicator."
  - id: "DS-AOEC-06"
    column: "won in matches_1v1_clean"
    question: >
      0 NULLs (R03 guarantees) — per F1 zero-missingness override, ledger reports
      RETAIN_AS_IS / mechanism=N/A. Target-override post-step does NOT fire (n_total_missing=0).
  - id: "DS-AOEC-07"
    column: "won in player_history_all (~5%)"
    question: >
      MAR; per the target-override post-step, recommendation becomes EXCLUDE_TARGET_NULL_ROWS.
      Feature computation (expanding-window win-rate) must skip NULL-target rows.
  - id: "DS-AOEC-08"
    columns: "leaderboards_raw, profiles_raw"
    question: >
      NOT_USABLE per 01_03_03; profiles_raw has 7 dead columns (100% NULL).
      Formally declare out-of-analytical-scope at 01_04_02+ — these tables do not
      enter any VIEW and do not need triage.
note_on_rates: >
  All triage rates in the ledger derive from VIEWs (filtered scope), not raw tables.
  A column with 42% NULL in matches_raw can be ~26% NULL in matches_1v1_clean.
  The ledger is authoritative for downstream decisions because Phase 02 features
  are computed from the VIEWs.
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
    JSON has "missingness_audit" block with two VIEW sub-blocks, each containing
    a "ledger" array (one row per column in the VIEW — full-coverage Option B) and the
    "_missingness_spec" used. The two new ledger files (CSV + JSON) exist at the
    paths above. MD has a "Missingness Ledger" section per VIEW + a final
    "Decisions surfaced for downstream cleaning (01_04_02+)" section reproducing
    DS-AOEC-01..08 with current observed rates filled in.
  continue_predicate: >
    Every column in the VIEW appears in the ledger (full-coverage Option B).
    Every column with non-zero missingness has a _missingness_spec entry; zero-
    missingness rows carry mechanism=N/A, recommendation=RETAIN_AS_IS, and
    justification="Zero missingness observed; no action needed." regardless of spec.
    Constant columns (n_distinct=1) carry mechanism=N/A, recommendation=DROP_COLUMN
    with constants-detection justification.
    Every ledger row has non-empty mechanism_justification, recommendation,
    recommendation_justification, and explicit carries_semantic_content boolean.
    Existing zero-NULL assertions (matchId, profileId, started) still pass.
    STEP_STATUS.yaml has 01_04_01: complete.
  halt_predicate: >
    Any column in the VIEW missing from the ledger (full-coverage violation);
    any column with non-zero missingness lacking a _missingness_spec entry; any
    ledger row missing mandatory fields; any zero-NULL identity assertion failure;
    any contradictory pairing of mechanism="N/A" with non-N/A justification.
research_log_entry: >
  Required on completion: list per-VIEW row counts in ledger, reference the
  artifact paths, summarise decisions surfaced for downstream resolution.
```

### Step 01_04_02 — Data Cleaning Execution (act on DS-AOEC-01..08)

> **ADDENDUM 2026-04-18:** Extended to 51 cols via `duration_seconds`, `is_duration_suspicious` (>86400s),
> and `is_duration_negative` (strict <0, aoe2companion-specific for 342 clock-skew rows). See
> research_log 01_04_02 ADDENDUM entry and `01_04_02_duration_augmentation.{md,json}` artifacts for
> gate details. STEP_STATUS 01_04_02 remains `complete`; the ADDENDUM retrofit does not re-open the step.

```yaml
step_number: "01_04_02"
name: "Data Cleaning Execution (act on DS-AOEC-01..08)"
description: >
  Apply VIEW DDL changes implementing all 8 cleaning decisions surfaced
  by the 01_04_01 missingness audit. Replaces matches_1v1_clean and
  player_history_all VIEWs via CREATE OR REPLACE (no raw table changes
  per Invariant I9). Produces post-cleaning validation artifact (JSON+MD),
  creates matches_1v1_clean.yaml schema, updates player_history_all.yaml.
  ratings_clean VIEW unchanged.
phase: "01 — Data Exploration"
pipeline_section: "01_04 — Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4 (Cleaning)"
dataset: "aoe2companion"
question: >
  What concrete VIEW DDL implements DS-AOEC-01..08, and does the
  post-cleaning state satisfy all I3/I5/I6/I7/I9/I10 invariants?
method: >
  Per-DS resolution: 7 columns dropped from matches_1v1_clean (4 high-NULL
  per Rule S4, 1 schema-evolution per Rule S4 cost-benefit, 2 constants
  via constants-detection override); 1 column added to matches_1v1_clean
  (rating_was_null BOOLEAN flag, sklearn MissingIndicator pattern for the
  primary feature exception per van Buuren 2018 Rule S4); 1 column
  dropped from player_history_all (status constant). Post-cleaning
  assertion battery covers zero-NULL identity, R03 complementarity,
  forbidden-column absence, new-column type, and rating_was_null flag
  consistency (within ±1 row of ledger expected count per I7).
predecessors:
  - "01_04_01"
methodology_citations:
  - "Rubin, D.B. (1976). Inference and missing data. Biometrika, 63(3)."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed."
  - "Schafer, J.L. & Graham, J.W. (2002). Missing data: Our view of the state of the art."
  - "Liu, X. et al. (2020). CONSORT-AI extension. BMJ 370."
  - "Jeanselme, V. et al. (2024). Participant Flow Diagrams for Health Equity in AI."
  - "Sambasivan, N. et al. (2021). Data Cascades. CHI '21."
  - "scikit-learn v1.8 documentation. sklearn.impute.MissingIndicator."
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py"
inputs:
  duckdb_views:
    - "matches_1v1_clean (54 cols, 61,062,392 rows — pre-01_04_02 state)"
    - "player_history_all (20 cols, 264,132,745 rows — pre-01_04_02 state)"
  prior_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv"
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json"
outputs:
  duckdb_views:
    - "matches_1v1_clean (48 cols, 61,062,392 rows — post-01_04_02; -7 / +1)"
    - "player_history_all (19 cols, 264,132,745 rows — post-01_04_02; -1 / +0)"
    - "ratings_clean (unchanged)"
  schema_yamls:
    - "data/db/schemas/views/matches_1v1_clean.yaml (NEW — 48 cols + invariants block; prose-format notes)"
    - "data/db/schemas/views/player_history_all.yaml (UPDATED — 19 cols; status removed; step bumped to 01_04_02)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
    - "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md"
reproducibility: >
  All SQL DDL + assertion SQL stored verbatim in
  01_04_02_post_cleaning_validation.json under sql_queries.
  ledger_derived_expected_values block records the runtime-derived
  I7 expected counts. Notebook re-runs deterministically via
  CREATE OR REPLACE VIEW (idempotent).
key_findings_carried_forward:
  - "DS-AOEC-01 resolved: server/scenario/modDataset/password DROPPED from matches_1v1_clean per Rule S4 (van Buuren 2018)."
  - "DS-AOEC-02 resolved: antiquityMode DROPPED (60.06% NULL, 40-80% non-primary band); hideCivs RETAINED with FLAG_FOR_IMPUTATION deferred to Phase 02."
  - "DS-AOEC-03b resolved: mod (matches_1v1_clean) + status (both VIEWs) DROPPED via constants-detection override."
  - "DS-AOEC-04 resolved: rating RETAINED in matches_1v1_clean; rating_was_null BOOLEAN flag ADDED (sklearn MissingIndicator pattern; Phase 02 imputation: median-within-leaderboard)."
  - "DS-AOEC-05 deferred: country FLAG_FOR_IMPUTATION; Phase 02 strategy TBD."
  - "DS-AOEC-06 resolved: won in matches_1v1_clean RETAIN_AS_IS (zero NULLs by R03)."
  - "DS-AOEC-07 documented: won in player_history_all has ~19,251 NULLs (0.0073%); EXCLUDE_TARGET_NULL_ROWS rule documented in cleaning registry; physical exclusion deferred to Phase 02 feature-computation per Rule S2."
  - "DS-AOEC-08 documented: leaderboards_raw (singleton 2-row reference) + profiles_raw (7 dead columns) FORMALLY DECLARED OUT-OF-ANALYTICAL-SCOPE in cleaning registry."
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No new POST-GAME columns introduced. ratingDiff and finished
      remain excluded (verified by Section 3.3b assertion).
      rating_was_null derives from the PRE_GAME rating column only.
  - number: "5"
    how_upheld: >
      matches_1v1_clean retains player-row orientation (2 rows per match).
      No slot-asymmetry introduced; both player rows treated identically.
  - number: "6"
    how_upheld: >
      All DDL + assertion SQL stored verbatim in JSON sql_queries.
  - number: "7"
    how_upheld: >
      All expected counts loaded at runtime from
      01_04_01_missingness_ledger.csv via ledger_val() helper. No
      magic numbers in notebook code. Plan cites ledger values as
      expected guidance; notebook derives them.
  - number: "9"
    how_upheld: >
      Raw tables UNTOUCHED. Only VIEW DDL changes via CREATE OR REPLACE.
      leaderboards_raw + profiles_raw declared out-of-scope but not
      dropped (no DROP TABLE statements).
  - number: "10"
    how_upheld: >
      No filename derivation changes. The aoec raw tables already
      satisfy I10 from 01_02_02 ingestion.
gate:
  artifact_check: >
    JSON exists at the path above with all keys: cleaning_registry,
    consort_flow_columns, consort_flow_matches, subgroup_impact,
    validation_assertions (all True), sql_queries, decisions_resolved,
    ledger_derived_expected_values. MD report exists with 6 tables.
    matches_1v1_clean.yaml exists with 48 column entries + invariants.
    player_history_all.yaml updated with 19 columns + step="01_04_02".
  continue_predicate: >
    Notebook executes end-to-end with all assertions PASS.
    DESCRIBE matches_1v1_clean returns 48 columns; DESCRIBE
    player_history_all returns 19 columns. Row counts unchanged.
    STEP_STATUS.yaml has 01_04_02: complete.
  halt_predicate: >
    Any AssertionError in notebook; any forbidden column present;
    row count change; rating_was_null inconsistent with rating IS NULL;
    validation_assertions has any False value.
research_log_entry: >
  Required on completion: full CONSORT column-flow tables, 8 DS
  resolutions, ledger-derived expected counts, artifact paths.
```

#### Addendum: Duration Augmentation (2026-04-18)

**Branch:** feat/01-04-02-duration-augmentation
**Scope:** Extended `matches_1v1_clean` VIEW from 48 to 51 columns by adding duration derivation
and outlier flags upstream at the cleaning stage.

**New columns (appended at end, after is_null_cluster):**

| Column | Type | Category | Formula |
|---|---|---|---|
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL | `CAST(EXTRACT(EPOCH FROM (r.finished - d.started)) AS BIGINT)` |
| `is_duration_suspicious` | BOOLEAN | POST_GAME_HISTORICAL | `duration_seconds > 86400` |
| `is_duration_negative` | BOOLEAN | POST_GAME_HISTORICAL | `duration_seconds < 0` (strict) |

**JOIN pattern:** LEFT JOIN aggregated subquery `(SELECT matchId, MIN(finished) AS finished FROM matches_raw GROUP BY matchId)` — avoids cartesian blow-up (matches_raw is pre-dedup). DuckDB 1.5.1 empirically verified: VIEW works for this pattern (no self-reference, unlike 01_04_03 which self-references and requires TABLE workaround).

**Threshold justification (I7):** 86,400s (24h) from 01_04_03 Gate+5b empirical precedent (~25x p99=3,458s); Tukey (1977) EDA sanity bound; I8: identical threshold across sc2egset/aoestats/aoe2companion.

**Duration statistics:**
- min: -3,041s (342 clock-skew rows; is_duration_negative = TRUE, strict <0)
- p50: 1,433s (~24 min)
- p99: 3,458s (~58 min)
- max: 3,279,303s (~38 days — 142 bogus wall-clock rows; is_duration_suspicious = TRUE)
- null_count: 0 (0.0% — finished empirically non-NULL in 1v1 ranked scope)
- zero_duration_count: 16 (UNFLAGGED by both flags; known state for Phase 02)

**STEP_STATUS:** stays `complete` (addendum pattern; no phase-gate regression).

**New artifacts:**
- `artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.json` (validation, all_assertions_pass: true)
- `artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.md`
- `data/db/schemas/views/matches_1v1_clean.yaml` updated to 51 cols + schema_version ADDENDUM

---

### Step 01_04_03 — Minimal Cross-Dataset History View

```yaml
step_number: "01_04_03"
name: "Minimal Cross-Dataset History View"
description: >
  Create matches_history_minimal VIEW: 8-column player-row-grain projection
  of matches_1v1_clean (natively 2-row player-grain) via self-join on
  matchId with unequal profileId (sc2egset pattern). Cross-dataset-
  harmonized substrate for Phase 02+ rating-system backtesting. Canonical
  TIMESTAMP temporal dtype (pass-through). Per-dataset-polymorphic faction
  vocabulary (full civ names). Sibling of sc2egset 01_04_03 (PR #152) and
  aoestats 01_04_03 (same bundled PR).
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4.2, Section 4.4"
dataset: "aoe2companion"
question: >
  Can matches_1v1_clean (natively 2-row player-grain) be projected to the
  cross-dataset 8-column contract via sc2egset-style self-join preserving
  R03 complementarity and NULL-safe symmetry?
method: >
  CREATE OR REPLACE VIEW matches_history_minimal. Self-join on matchId with
  p.player_id <> o.player_id (sc2egset pattern). started_at pass-through
  (already TIMESTAMP). Prefix check uses numeric-tail regex [0-9]+ with
  round-trip cast (aoec matchId is INTEGER, variable decimal width; no
  fixed-length gate).
predecessors:
  - "01_04_02"
methodology_citations:
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.2, §4.4"
  - "Tukey, J. W. (1977). Exploratory Data Analysis."
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_03_minimal_history_view.py"
inputs:
  duckdb_views:
    - "matches_1v1_clean (48 cols, 61,062,392 player-rows / 30,531,196 matches -- from 01_04_02)"
  schema_yamls:
    - "data/db/schemas/views/matches_1v1_clean.yaml"
    - "data/db/schemas/raw/matches_raw.yaml  # I7 provenance for matchId INTEGER"
outputs:
  duckdb_views:
    - "matches_history_minimal (NEW -- 8 cols, 61,062,392 rows)"
  schema_yamls:
    - "data/db/schemas/views/matches_history_minimal.yaml (NEW)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.md"
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      TIMESTAMP pass-through (upstream `started` is already TIMESTAMP per
      matches_raw.yaml; no cast required; chronologically faithful).
  - number: "5"
    how_upheld: >
      Player-row symmetry via self-join. NULL-safe IS DISTINCT FROM. Slot-
      bias gate N/A for aoec (natively 2-row player-grain; no slot column).
  - number: "6"
    how_upheld: >
      DDL + all assertion SQL verbatim in validation JSON.
  - number: "7"
    how_upheld: >
      Numeric-tail regex [0-9]+ with round-trip cast cites
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml
      line matchId:INTEGER (no fixed-length gate — contrast sc2egset 32-char hex).
  - number: "8"
    how_upheld: >
      8-col cross-dataset contract (identical to sc2egset and aoestats).
      Polymorphic faction vocabulary (full civ names; consumers MUST game-
      condition; civ is zero-NULL upstream — stricter gate than sc2/aoestats).
  - number: "9"
    how_upheld: >
      Pure non-destructive projection. No upstream modification.
gate:
  artifact_check: >
    Validation JSON + MD exist; matches_history_minimal.yaml exists with 8
    columns + invariants block.
  continue_predicate: >
    VIEW exists with 8 columns matching spec. 61,062,392 rows = 30,531,196 × 2.
    Zero symmetry violations, zero prefix violations, dataset_tag distinct = 1,
    zero NULLs in 7 non-nullable cols (including faction / opponent_faction).
  halt_predicate: >
    Any gate fails; dtype != TIMESTAMP; NULL in any gated non-null col.
    Manual PIPELINE_SECTION_STATUS revert on T03 failure.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data > Cross-dataset harmonization substrate"
  - "Chapter 4 -- Data and Methodology > 4.3 Rating System Backtesting Design"
research_log_entry: "Required on completion."
```

### Step 01_04_04 — Identity Resolution

```yaml
step_number: "01_04_04"
name: "Identity Resolution"
description: >
  Empirical characterisation of the aoe2companion identity signals (profileId,
  name, country) across all three raw tables. Produces a census of rename
  history (how many distinct names per profileId), alias collision rates
  (how many profileIds per name), join-integrity set-difference audits
  (matches_raw vs profiles_raw vs ratings_raw), and country temporal
  stability. Includes a cross-dataset feasibility preview: does aoec
  profileId share a namespace with aoestats profile_id? Findings route to
  DS-AOEC-IDENTITY-01..05 decisions for Phase 02 identity-key design.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md §4 + §5"
dataset: "aoe2companion"
question: >
  Which column or column combination should serve as the canonical player
  identifier in Phase 02 rating-system backtesting? Does profileId share a
  namespace with aoestats, enabling a name-bridge for Invariant I2?
method: >
  Cardinality baseline across three tables (matches_raw, ratings_raw,
  profiles_raw): n_rows, n_distinct, min, max, null, sentinel=-1.
  Name-history-per-profileId (player_history_all rm_1v1 scope): distribution
  of COUNT(DISTINCT name) per profileId, rename-timing bins (rapid_30d,
  within_180d). Name-to-profileId collision distribution and top-100
  exemplars. Join-integrity set-difference audit (three bilateral pairs).
  Country temporal stability distribution. Cross-dataset feasibility via
  ATTACH aoestats READ_ONLY: 2026-01-25..2026-01-31 window, direct
  ID-equality test, 95% bootstrap CI, verdict rubric A/B/C.
predecessors:
  - "01_04_03"
methodology_citations:
  - "Fellegi, I. P. & Sunter, A. B. (1969). A theory for record linkage. JASA 64(328)."
  - "Christen, P. (2012). Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection. Springer."
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_04_identity_resolution.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "ratings_raw"
    - "profiles_raw"
    - "player_history_all"
  duckdb_views:
    - "matches_1v1_clean"
  attached_dbs:
    - "aoestats (READ_ONLY ATTACH for cross-dataset feasibility)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.md"
scientific_invariants_applied:
  - number: "2"
    how_upheld: >
      Characterises the profileId-vs-name trade-off for the canonical player
      identifier. DS-AOEC-IDENTITY-01 records the Phase 02 recommendation.
  - number: "6"
    how_upheld: >
      All SQL queries stored verbatim in the JSON sql_queries block and
      reproduced in the markdown artifact.
  - number: "7"
    how_upheld: >
      All thresholds (1% NULL fraction, sentinel=-1, 60s temporal window,
      50-ELO proximity) carry inline provenance in the notebook.
  - number: "8"
    how_upheld: >
      Cross-dataset feasibility preview addresses whether aoec profileId
      can serve as identity bridge to aoestats (enabling I8 cross-game
      comparability via a common player identifier).
  - number: "9"
    how_upheld: >
      Exploration-only. No VIEWs, no raw-table modifications. aoestats
      ATTACH is READ_ONLY.
gate:
  artifact_check: >
    JSON + MD exist and parse. sql_queries block populated (I6 verbatim).
    5+ DS-AOEC-IDENTITY-* decisions defined. Verdict A/B/C stated with
    CI and sample size.
  continue_predicate: >
    All 6 JSON blocks populated. Cross-dataset verdict with CI. I9 empty
    diff on aoec views/raw + aoestats.
  halt_predicate: >
    Any JSON block empty. aoestats READ_ONLY violated. Cross-dataset
    verdict missing CI.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.2.2 Identity Resolution"
research_log_entry: "Required on completion."
```

---

### Step 01_05_01 — Quarterly Grain Row Counts

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_02 — PSI Shift (Pre-Game Features)

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_03 — Stratification (Per-Leaderboard)

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_04 — Survivorship Triple Analysis

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_05 — Variance Decomposition (ICC)

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_06 — DGP Diagnostics (Duration)

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_07 — Phase 06 Interface Emission

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_08 — Temporal Leakage Audit v1

Inherited from 01_05 execution (see STEP_STATUS.yaml; completed 2026-04-19).

### Step 01_05_09 — 01_05 exit memo

```yaml
step_number: "01_05_09"
name: "01_05 exit memo"
description: "Consolidate 01_05 findings into a single exit memo for Phase 01 gate
  consumption. Authored in T07 as part of the 01_06 bundled PR (retroactive Step
  addition). Covers ICC verdict, PSI audit, leakage audit, temporal drift,
  survivorship, 01_05_05 sensitivity."
phase: "01 -- Data Exploration"
pipeline_section: "01_05 -- Temporal & Panel EDA"
dataset: "aoe2companion"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.py"
outputs:
  report: "artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md"
gate: "memo exists; cites all 01_05 artifacts by path"
```

---

### Step 01_06_01 — Data Dictionary

```yaml
step_number: "01_06_01"
name: "Data Dictionary"
description: "Enumerate every column consumed downstream in Phase 02 from matches_1v1_clean,
  player_history_all, and matches_history_minimal. Flag identity-rate reconciliation
  (2026-04-19: 2.57%/3.55% rm_1v1 scope) in invariant_notes for profileId. Note Branch (i)
  API-namespace identifier. Produce data_dictionary_aoe2companion.csv and .md per spec §1.1."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoe2companion"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py"
inputs:
  - "reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  - "reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json"
outputs:
  data_artifacts:
    - "reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.csv"
  report: "reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.md"
gate:
  artifact_check: "CSV and MD exist."
  continue_predicate: "profileId row has identity-rate reconciliation note in invariant_notes."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > §4.1.2 AoE2 datasets"
research_log_entry: "Required on completion."
```

### Step 01_06_02 — Data Quality Report

```yaml
step_number: "01_06_02"
name: "Data Quality Report"
description: "Consolidate aoe2companion 01_04 cleaning artifacts into CONSORT flow.
  Include 2.25% country NULL retention (MissingIndicator route, MAR primary / MNAR
  sensitivity per §4.2.3). Note rating=0 / ratings_raw empty for lb=6 as scope-boundary.
  Produce data_quality_report_aoe2companion.md per spec §1.2."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoe2companion"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.py"
inputs:
  - "reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json"
  - "reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  - "reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv"
outputs:
  report: "reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md"
gate:
  artifact_check: "MD exists with CONSORT flow and rule registry."
  continue_predicate: "CONSORT flow balanced."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > §4.2.3 Cleaning rules"
research_log_entry: "Required on completion."
```

### Step 01_06_03 — Risk Register

```yaml
step_number: "01_06_03"
name: "Risk Register"
description: "Enumerate INVARIANTS.md §5 rows: I2 PARTIAL (identity-rate 2.57%/3.55%).
  LOW RESOLVED for identity-rate reconciliation. HIGH for ICC FALSIFIED 0.003 (§4.4.5
  defence). No BLOCKERs expected. Produce risk_register_aoe2companion.csv and .md per spec §1.3."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoe2companion"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_03_risk_register.py"
inputs:
  - "reports/INVARIANTS.md"
  - "planning/BACKLOG.md"
  - "reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md"
outputs:
  data_artifacts:
    - "reports/artifacts/01_exploration/06_decision_gates/risk_register_aoe2companion.csv"
  report: "reports/artifacts/01_exploration/06_decision_gates/risk_register_aoe2companion.md"
gate:
  artifact_check: "CSV and MD exist."
  continue_predicate: "I2 PARTIAL row has corresponding risk_id; no BLOCKER rows."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > §4.4.5 ICC estimator"
research_log_entry: "Required on completion."
```

### Step 01_06_04 — Modeling Readiness Decision

```yaml
step_number: "01_06_04"
name: "Modeling Readiness Decision"
description: "Consume 01_06_01..03 artifacts; produce READY_WITH_DECLARED_RESIDUALS verdict.
  ICC FALSIFIED 0.003 is a HIGH skill-signal residual with §4.4.5 defence anchor. I2 PARTIAL
  at 2.57% rename rate is defence item with §4.2.2 anchor. 342 duration clock-skew rows
  retained is MEDIUM residual. No BLOCKER; Phase 02 proceeds unconditionally.
  Produce modeling_readiness_aoe2companion.md per spec §1.4."
phase: "01 -- Data Exploration"
pipeline_section: "01_06 -- Decision Gates"
dataset: "aoe2companion"
spec: "reports/specs/01_06_readiness_criteria.md v1.0"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py"
inputs:
  - "reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.csv"
  - "reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md"
  - "reports/artifacts/01_exploration/06_decision_gates/risk_register_aoe2companion.csv"
outputs:
  report: "reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md"
gate:
  artifact_check: "MD exists with READY_WITH_DECLARED_RESIDUALS verdict."
  continue_predicate: "Verdict stated verbatim; HIGH ICC residual has §4.4.5 anchor."
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
