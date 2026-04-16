# SC2EGSet Dataset Roadmap

**Game:** SC2
**Dataset:** sc2egset
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`
**Research log:** `research_log.md` (sibling file — per-dataset reverse-chronological narrative)

---

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the sc2egset
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Steps are defined in a planning session before Phase work begins.

Steps are numbered `XX_YY_ZZ` where `XX` = Phase, `YY` = Pipeline Section,
`ZZ` = Step within that Pipeline Section.

---

## Source data

**SC2EGSet: StarCraft II Esport Replay and Game-state Dataset** — Zenodo v2.1.0.

Raw directory layout: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`
(two-level: 70 tournament directories, each containing a `_data/` subdirectory
with `.SC2Replay.json` files and a `map_foreign_to_english_mapping.json` metadata
file at the tournament level).

File counts from 01_01_01 artifact:
- `.SC2Replay.json` files: 22,390
- Metadata files (`.zip`, `.log`, `.json` at tournament level): 431
- Files at root level: 3
- Total files scanned: 22,821
- Total `.SC2Replay.json` size: 214,060.62 MB

Directory name prefix range: `2016_` through `2024_` (70 directories).

Source: Białecki, A. et al. (2023). *SC2EGSet: StarCraft II Esport Replay
and Game-state Dataset.* Scientific Data 10(1), 600.
https://doi.org/10.1038/s41597-023-02510-7 — version 2.1.0 from Zenodo:
https://zenodo.org/records/17829625

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
description: "Establish a complete filesystem-level census of the sc2egset raw data. This grounds all subsequent steps in verified file counts, sizes, and directory structure."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "sc2egset"
question: "How many replay files exist, how large are they, and how are they distributed across the two-level tournament directory structure?"
method: "Full census of the raw directory tree. Count files, measure sizes, and group by tournament subdirectory. Report summary statistics (min/max/median replays per tournament) and flag structural anomalies (e.g., missing subdirectories)."
stratification: "By tournament directory (each tournament has its own _data/ subdir)."
predecessors: "none — independent"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py"
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
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_01_02 — Schema Discovery

```yaml
step_number: "01_01_02"
name: "Schema Discovery"
description: "Map the internal structure of sc2egset JSON replay files — root-level keys, nested keypaths, data types — and determine whether the schema is consistent across all 70 tournament directories (spanning 2016-2024)."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "sc2egset"
question: "What is the internal structure of the replay JSON files, and does it remain stable across tournament eras or evolve over time?"
method: "Sample files from each of the 70 directories (deterministic selection, stratified by tournament). Enumerate root-level keys and full keypath trees. Compare schemas across directories to detect era-dependent variation and report a consistency verdict. No DuckDB type proposals — deferred to ingestion design."
stratification: "By directory (all 70 represented; temporal range 2016-2024)."
predecessors:
  - "01_01_01"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_02_schema_discovery.py"
inputs:
  duckdb_tables: "none — reads raw JSON files directly"
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
    how_upheld: "Sample size per directory justified by temporal stratification in the report."
  - number: "9"
    how_upheld: "Conclusions limited to structural observations — no value distributions or semantic interpretation."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json and .md exist and are non-empty."
  continue_predicate: "Schema artifacts exist and report a consistency verdict for all 70 directories."
  halt_predicate: "More than 30% of sampled files fail to parse."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_02_01 — DuckDB Pre-Ingestion Investigation

```yaml
step_number: "01_02_01"
name: "DuckDB Pre-Ingestion Investigation"
description: "Determine how sc2egset's deeply nested JSON (11 root keys, dynamic-key maps, 3 large event arrays) behaves when loaded into DuckDB, and decide on a table split strategy before committing to full ingestion."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "sc2egset"
question: "What does the raw data look like before we commit to an ingestion strategy — are there type inference traps, storage feasibility concerns for event arrays, or structural irregularities in the mapping files that need handling?"
method: "Smoke-test size-stratified file samples into in-memory DuckDB. DESCRIBE schemas, preview rows, and assess event array storage cost (extrapolated to full corpus). Test single-table vs split-table approaches on a mid-size tournament directory. Census all 70 tournament-level mapping files for schema consistency. Produce a design artifact with proposed DDL for a future full-ingestion step."
stratification: "By root key group (metadata vs events vs player desc map); by tournament directory for map alias files."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py"
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
    how_upheld: "All smoke-test SQL, storage measurements, and census code in the notebook."
  - number: "7"
    how_upheld: "File sample selection derived from 01_01_01 per-directory size data."
  - number: "9"
    how_upheld: "Conclusions limited to type mappings, storage estimates, and structural consistency — no content profiling."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json and .md exist and are non-empty."
  continue_predicate: "Design artifact documents: (1) read_json_auto behavior for all 11 root keys with DuckDB types, (2) proposed table split strategy with rationale, (3) event array storage estimate with SSD feasibility verdict, (4) full census of all 70 map_foreign_to_english_mapping.json files with cross-file consistency assessment and proposed DDL."
  halt_predicate: "read_json_auto cannot parse any sample file, OR batch ingestion of a single directory fails."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_02_02 — DuckDB Ingestion

```yaml
step_number: "01_02_02"
name: "DuckDB Ingestion"
description: "Materialise raw sc2egset data into persistent DuckDB tables using the three-stream strategy determined by 01_02_01. Stream 1 (replays_meta_raw): one row per replay with metadata STRUCT columns and ToonPlayerDescMap as VARCHAR. Stream 2 (replay_players_raw): normalised from ToonPlayerDescMap, one row per (replay, player). Stream 3 (events): optional Parquet extraction for gameEvents, trackerEvents, messageEvents. Also: map_aliases_raw table from all 70 tournament mapping files. filename column stores path relative to raw_dir (no absolute paths)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "sc2egset"
question: "Can we materialise the three-stream ingestion strategy into persistent tables and verify row counts, column types, and NULL rates?"
method: "Call ingestion module functions against the persistent DuckDB. Validate with DESCRIBE, row counts, NULL rates on key fields. Verify ToonPlayerDescMap is VARCHAR, event arrays are excluded from replays_meta, and map_aliases has tournament provenance."
stratification: "By table (replays_meta_raw, replay_players_raw, map_aliases_raw)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py"
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
  continue_predicate: "All three DuckDB tables created with expected row counts. ToonPlayerDescMap is VARCHAR. All tables have filename column. filename values are relative paths (no leading /)."
  halt_predicate: "Any table creation fails OR row count is zero."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_02_03 — Raw Schema DESCRIBE

```yaml
step_number: "01_02_03"
name: "Raw Schema DESCRIBE"
description: "Establish the definitive column-name and column-type snapshot for every sc2egset *_raw object — three persistent tables (replays_meta_raw, replay_players_raw, map_aliases_raw) and three event views (game_events_raw, tracker_events_raw, message_events_raw). Connects read-only to the persistent DuckDB populated by 01_02_02 and runs DESCRIBE on all six objects. Output feeds the data/db/schemas/raw/*.yaml source-of-truth files consumed by all downstream steps."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "sc2egset"
question: "What are the exact column names and DuckDB types for all six sc2egset *_raw objects — the three persistent tables and three event views — as materialised in the persistent DuckDB?"
method: "Connect read-only to persistent DuckDB. DESCRIBE each *_raw table and view. Write JSON artifact. Populate data/db/schemas/raw/*.yaml schema files."
stratification: "By object (3 tables: replays_meta_raw, replay_players_raw, map_aliases_raw; 3 views: game_events_raw, tracker_events_raw, message_events_raw)."
predecessors:
  - "01_02_02"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_03_raw_schema_describe.py"
inputs:
  duckdb_tables:
    - "replays_meta_raw"
    - "replay_players_raw"
    - "map_aliases_raw"
    - "game_events_raw (view)"
    - "tracker_events_raw (view)"
    - "message_events_raw (view)"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json"
  schema_files:
    - "data/db/schemas/raw/replays_meta_raw.yaml"
    - "data/db/schemas/raw/replay_players_raw.yaml"
    - "data/db/schemas/raw/map_aliases_raw.yaml"
    - "data/db/schemas/raw/game_events_raw.yaml"
    - "data/db/schemas/raw/tracker_events_raw.yaml"
    - "data/db/schemas/raw/message_events_raw.yaml"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All DESCRIBE SQL embedded in notebook; JSON artifact records exact schema seen."
  - number: "7"
    how_upheld: "Column types and nullability taken from DESCRIBE output, not assumed."
  - number: "9"
    how_upheld: "Read-only step — no tables or views modified."
  - number: "10"
    how_upheld: "filename column confirmed present in all six objects."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json exists and non-empty. data/db/schemas/raw/*.yaml files populated for all six objects."
  continue_predicate: "Column counts confirmed: replays_meta_raw=9, replay_players_raw=25, map_aliases_raw=4, game_events_raw=4, tracker_events_raw=4, message_events_raw=4."
  halt_predicate: "Any object cannot be described or column count is zero."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

---

### Step 01_02_04 -- Metadata STRUCT Extraction & Univariate Census

```yaml
step_number: "01_02_04"
name: "Metadata STRUCT Extraction & Univariate Census"
description: "Flatten the four STRUCT columns from replays_meta_raw into scalar fields, run a full NULL census across all raw columns, and produce univariate statistical profiles (descriptive stats, zero counts, categorical distributions, skewness/kurtosis, sentinel detection) for all sc2egset raw fields."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 2.1, 3.4"
dataset: "sc2egset"
question: "What are the distributions of all raw fields, what NULLs and sentinels exist, and what is the temporal coverage of the dataset?"
method: "DuckDB SQL aggregations: NULL census, GROUP BY counts, descriptive statistics, skewness/kurtosis. Categorical cardinality via value_counts. Sentinel detection via range checks (INT32_MIN for SQ). Temporal coverage via monthly GROUP BY."
predecessors: "01_02_03"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py"
```

### Step 01_02_05 -- Univariate EDA Visualizations

```yaml
step_number: "01_02_05"
name: "Univariate EDA Visualizations"
description: "14 visualization plots for the sc2egset univariate census findings from 01_02_04. Reads the 01_02_04 JSON artifact and queries DuckDB for histogram bin data. All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations on in-game columns (APM, SQ, supplyCappedPercent) and post-game column (elapsed_game_loops) per Invariant #3."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 2.1, 3.4"
dataset: "sc2egset"
question: "What do the distributions from 01_02_04 look like visually, and do the visual patterns confirm or challenge the statistical summaries?"
method: "Read 01_02_04 JSON artifact. Query DuckDB for histogram bins (MMR, APM, SQ, supplyCappedPercent, duration). Produce 14 plots: result 2-bar, categorical 3-panel (race/highestLeague/region), selectedRace bar, MMR split view, APM histogram (IN-GAME), SQ split view (IN-GAME), supplyCappedPercent histogram (IN-GAME), duration dual-panel (POST-GAME), MMR zero-spike cross-tab, temporal coverage line, isInClan bar, clanTag top-20, map top-20 barh, player repeat frequency. Markdown artifact with SQL queries."
predecessors: "01_02_04"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
    - "replays_meta_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_05_result_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_categorical_bars.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_selectedrace_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_mmr_split.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_apm_hist.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_sq_split.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_supplycapped_hist.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_duration_hist.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_mmr_zero_interpretation.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_temporal_coverage.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_isinclan_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_clantag_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_map_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_player_repeat_frequency.png"
  report: "artifacts/01_exploration/02_eda/01_02_05_visualizations.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: >-
      Three in-game columns (APM, SQ, supplyCappedPercent) carry
      'IN-GAME — not available at prediction time (Inv. #3)'.
      Post-game column (elapsed_game_loops) carries
      'POST-GAME — total duration; only known after match ends (Inv. #3)'.
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All bin widths, clip boundaries, sentinel thresholds derived from census JSON at runtime. No hardcoded numbers."
  - number: "9"
    how_upheld: "Visualization of 01_02_04 findings only. No new analytical computation."
gate:
  artifact_check: "All 14 PNG files and 01_02_05_visualizations.md exist and are non-empty."
  continue_predicate: "All 14 PNG files exist. Markdown artifact contains plot index table with Temporal Annotation column and all SQL queries. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet"
research_log_entry: "Required on completion."
```

### Step 01_02_06 — Bivariate EDA

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
    how_upheld: "All three in-game columns (APM, SQ, supplyCappedPercent) carry a visible annotation: 'IN-GAME -- not available at prediction time (Inv. #3)' on every plot where they appear. Spearman heatmap marks in-game columns with red asterisks in tick labels."
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

### Step 01_02_07 -- Multivariate EDA

```yaml
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

---

## Phase 01 — Pipeline Section 01_03: Systematic Data Profiling

### Step 01_03_01 -- Systematic Data Profiling

```yaml
step_number: "01_03_01"
name: "Systematic Data Profiling"
description: "Column-level and dataset-level profiling of all three sc2egset raw tables (replay_players_raw, replays_meta_raw struct-flat fields, map_aliases_raw). Detects dead fields, constant columns, near-constant columns, IQR outliers. Produces QQ plots and ECDFs for key numeric columns. Cross-table linkage check via replayId."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "sc2egset"
question: "What is the full column-level and dataset-level quality profile of all sc2egset raw tables, including dead fields, constant columns, outlier rates, and distribution shapes?"
method: "DuckDB SQL aggregations: NULL/zero census per column per table, cardinality, descriptive stats, skewness/kurtosis, IQR outlier detection (Tukey fence at 1.5*IQR). QQ plots against normal distribution for 5 key columns. ECDFs for 3 key columns. Cross-table linkage via replayId derived from filename. Completeness heatmap across all tables."
predecessors: "01_02_05"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
    - "replays_meta_raw"
    - "map_aliases_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  plots:
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_completeness_heatmap.png"
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_qq_plots.png"
    - "artifacts/01_exploration/03_profiling/plots/01_03_01_ecdf_key_columns.png"
  report: "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "Every column carries I3 temporal classification. elapsed_game_loops annotated as POST-GAME (reclassified 2026-04-15). APM, SQ, supplyCappedPercent annotated as IN-GAME."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "IQR fence multiplier 1.5 cited to Tukey (1977). All sentinel thresholds derived from census JSON at runtime."
  - number: "9"
    how_upheld: "Profiling of existing tables only. No new feature computation. Builds on 01_02_04 census and all 01_02 EDA findings."
gate:
  artifact_check: "All 5 artifacts (JSON, 3 PNGs, MD) exist and are non-empty."
  continue_predicate: "JSON contains critical_findings key with constant_columns list of exactly 5 entries. MD contains I3 classification table. All PNG files exist."
  halt_predicate: "Any artifact is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_03_02 -- True 1v1 Match Identification

```yaml
step_number: "01_03_02"
name: "True 1v1 Match Identification"
description: "Profile every replay to determine which are genuine 1v1 matches (exactly 2 active player rows with decisive Win/Loss results) vs non-1v1 (team games, observer contamination, incomplete replays). Produces a replay-level classification without dropping any rows (cleaning deferred to 01_04)."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "sc2egset"
question: "Which of the 22,390 replays are genuine 1v1 matches, and what characterises the non-1v1 replays?"
method: "DuckDB SQL: per-replay player row counts, cross-reference with max_players struct field, selectedRace/result analysis of non-2-player rows, observer setting profiling. Multi-signal classification of each replay."
predecessors: "01_03_01"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
    - "replays_meta_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
  report: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "Standard race list derived dynamically from 01_02_04 census categorical_profiles.selectedRace at runtime (list comprehension + assertion guard). All other thresholds from census JSON."
  - number: "9"
    how_upheld: "Classification and profiling only. No rows dropped, no new features computed, no cleaning decisions made."
  - number: "3"
    how_upheld: "elapsed_game_loops annotated as POST-GAME wherever referenced. No temporal features computed."
gate:
  artifact_check: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json and .md exist and are non-empty."
  continue_predicate: "JSON contains: true_1v1_decisive_count, true_1v1_indecisive_count, total_replay_count, observer_row_analysis, players_per_replay_distribution, max_players_distribution, replay_classification. MD contains comparison summary table. true_1v1_decisive_count + true_1v1_indecisive_count + sum(non_1v1 categories) = total_replay_count."
  halt_predicate: "Any artifact is missing, or classification totals do not sum to 22,390."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_03_03 -- Table Utility Assessment

```yaml
step_number: "01_03_03"
name: "Table Utility Assessment"
description: >-
  Empirical assessment of all 6 raw data objects (replay_players_raw,
  replays_meta_raw, map_aliases_raw, game_events_raw, tracker_events_raw,
  message_events_raw) for prediction pipeline utility. Verify the
  replay_id join key between the two core tables. Enumerate all 31 struct
  leaf fields of replays_meta_raw. Characterize loop=0 initialization
  events. Assess map_aliases_raw necessity. Produce evidence-backed
  utility verdicts.
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "sc2egset"
question: >-
  Which data objects are essential, utility-conditional, in-game-only,
  or low-utility? What is the replay_id join key between replay_players_raw
  and replays_meta_raw? Are map names already in English? What do loop=0
  events represent?
method: >-
  DuckDB SQL: DESCRIBE both core tables; extract all 31 struct leaf fields;
  verify replay_id join via regexp_extract; cross-reference metadata.mapName
  against map_aliases_raw; query loop=0 evtTypeName distributions; COUNT
  tracker_events_raw and message_events_raw; sample game_events_raw (COUNT
  from schema YAML). All verdicts data-derived.
predecessors: "01_03_02"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_03_table_utility.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
    - "replays_meta_raw"
    - "map_aliases_raw"
    - "game_events_raw"
    - "tracker_events_raw"
    - "message_events_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - ".claude/rules/sql-data.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_03_table_utility.json"
  report: "artifacts/01_exploration/03_profiling/01_03_03_table_utility.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: >-
      All event views classified IN_GAME (loop >= 0). timestamp
      (details.timeUTC) classified PRE_GAME. header.elapsedGameLoops
      reclassified POST_GAME. No feature computation performed.
  - number: "6"
    how_upheld: "All SQL queries stored verbatim in sql_queries dict and saved to artifact."
  - number: "9"
    how_upheld: "Profiling only. No rows dropped. No cleaning decisions made."
gate:
  artifact_check: >-
    artifacts/01_exploration/03_profiling/01_03_03_table_utility.json and
    .md exist and are non-empty.
  continue_predicate: >-
    JSON contains: table_verdicts (6 entries), join_key (matched_replay_ids
    == 22390, orphan counts == 0), struct_leaf_fields.confirmed_31_fields ==
    true, map_name_analysis, event_row_counts, tracker_events_loop_range.
    MD contains utility verdict table and all SQL queries.
  halt_predicate: "Any artifact is missing or join verification fails."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
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
