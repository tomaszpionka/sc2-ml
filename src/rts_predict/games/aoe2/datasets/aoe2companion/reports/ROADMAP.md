# aoe2companion Dataset Roadmap

**Game:** AoE2
**Dataset:** aoe2companion
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`
**Research log:** `research_log.md` (sibling file — per-dataset reverse-chronological narrative)

---

> **Role: TO BE DETERMINED.** Role assignment (PRIMARY vs SUPPLEMENTARY
> VALIDATION) will be formalized at the Phase 01 Decision Gate (01_06) based
> on comparative data quality findings. Until then, this dataset runs all
> Phases at full scope per `docs/PHASES.md`.

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
