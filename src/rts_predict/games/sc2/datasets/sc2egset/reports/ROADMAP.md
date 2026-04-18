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

### Step 01_03_04 -- Event Table Profiling

```yaml
step_number: "01_03_04"
name: "Event Table Profiling"
description: >-
  Deep structural profiling of the three event views (tracker_events_raw
  62M rows, game_events_raw 608M rows, message_events_raw 52K rows).
  These are unique to sc2egset -- neither AoE2 dataset has in-game event
  logs. Profiles event type distributions, per-replay density,
  PlayerStats periodicity, UnitBorn unit-type diversity, and event_data
  JSON schemas. No features extracted, no tables created (I9).
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "sc2egset"
question: >-
  What are the event type distributions for all three event views? What
  is the per-replay event density? Is PlayerStats periodic or variable?
  How many distinct unit types appear in UnitBorn? What JSON keys exist
  in event_data for each event type?
method: >-
  DuckDB SQL: GROUP BY evtTypeName distributions for all three views;
  per-replay density via GROUP BY filename; PlayerStats periodicity via
  LAG window function; UnitBorn unit types via json_extract_string;
  event_data JSON key sampling per type. Game events sampled at 10%
  BERNOULLI for density. All SQL stored verbatim (I6).
predecessors: "01_03_03"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_04_event_profiling.py"
inputs:
  duckdb_tables:
    - "tracker_events_raw"
    - "game_events_raw"
    - "message_events_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_03_table_utility.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - ".claude/rules/sql-data.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_04_event_profiling.json"
  report: "artifacts/01_exploration/03_profiling/01_03_04_event_profiling.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries stored verbatim in sql_queries dict and saved to artifact."
  - number: "9"
    how_upheld: "Profiling only. No rows dropped. No cleaning decisions made. No tables created."
  - number: "3"
    how_upheld: "All three event views classified IN_GAME_ONLY. No features extracted."
gate:
  artifact_check: >-
    artifacts/01_exploration/03_profiling/01_03_04_event_profiling.json and
    .md exist and are non-empty.
  continue_predicate: >-
    JSON contains: tracker_events (type_distribution with 10 types,
    per_replay_density, playerstats_periodicity, unitborn_unit_types with
    >=20 distinct types, event_data_keys for 5+ types), game_events
    (type_distribution with 23 types, event_data_keys for 2+ types),
    message_events (type_distribution, coverage). Exact totals:
    tracker=62,003,411; game=608,618,823; message=52,167.
    All SQL in sql_queries dict (I6).
  halt_predicate: "Any artifact is missing or exact row counts do not match."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_04_00 -- Source Normalization to Canonical Long Skeleton

```yaml
step_number: "01_04_00"
name: "Source Normalization to Canonical Long Skeleton"
description: >
  Creates the matches_long_raw VIEW: a canonical 10-column long skeleton with one row
  per player per match. Structural INNER JOIN of replay_players_raw x replays_meta_raw
  using the 32-char hex hash extracted from filename (same key as matches_flat in 01_04_01).
  NULLIF guard converts empty-string non-matches to NULL. No filtering, no cleaning,
  no feature computation. leaderboard_raw is NULL for all rows (SC2EGSet is an esports
  tournament dataset with no matchmaking ladder -- deliberate NULL, not missing data).
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4"
dataset: "sc2egset"
question: >
  Can replay_players_raw JOIN replays_meta_raw be projected losslessly into the canonical
  10-column long skeleton that all downstream cleaning steps will operate against?
method: >
  INNER JOIN of replay_players_raw x replays_meta_raw on NULLIF-guarded hex-hash regexp
  key. Lossless check compares VIEW count against the same JOIN computed directly on raw
  tables. Side derived as playerID - 1 (0-based). started_timestamp taken from
  rm.details.timeUTC (struct dot notation, VARCHAR). leaderboard_raw = NULL constant.
predecessors:
  - "01_04_01"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_00_source_normalization.py"
outputs:
  duckdb_views:
    - "matches_long_raw"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.md"
  schema_yaml: "data/db/schemas/views/matches_long_raw.yaml"
gate:
  artifact_check: >
    JSON artifact exists with row_count, schema, lossless_check, symmetry_audit,
    and all SQL queries verbatim. matches_long_raw VIEW is queryable and returns 44,817 rows.
    Distinct side values include 0 and 1 (main players); schema YAML exists.
  continue_predicate: >
    Lossless check PASSED (matches_long_raw rows == direct JOIN count).
    STEP_STATUS.yaml has 01_04_00: complete.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      MMR retained (PRE_GAME per 01_04_01 analysis). APM, SQ, supplyCappedPercent,
      header_elapsedGameLoops excluded. I3 preserved.
  - number: "5"
    how_upheld: >
      Player-row-oriented VIEW. No slot-based pivoting. Both players in any match
      are represented with the same 10-column structure.
  - number: "6"
    how_upheld: "All SQL queries written verbatim to JSON artifact under sql_queries."
  - number: "9"
    how_upheld: >
      No features computed. No rows filtered beyond INNER JOIN unmatched exclusion.
      Raw data untouched.
research_log_entry: "Required on completion."
```

### Step 01_04_01 -- Data Cleaning

```yaml
step_number: "01_04_01"
name: "Data Cleaning — VIEW DDL + Missingness Audit (insight-gathering)"
description: >
  Two-part step with one execution pass.
  PART A (already executed in PRs #138/#139): non-destructive cleaning of
  replay_players_raw and replays_meta_raw via three DuckDB VIEWs (matches_flat,
  matches_flat_clean, player_history_all) — all DDL changes resolved in prior PRs.
  PART B (this revision): consolidated missingness audit over the analytical VIEWs
  (matches_flat_clean, player_history_all). Two coordinated census passes per VIEW —
  SQL NULL census plus sentinel census driven by per-column _missingness_spec — plus
  a runtime constants-detection check, feed one missingness ledger (CSV+JSON) per
  VIEW. The audit gathers insights for downstream cleaning decisions in 01_04_02+;
  it does NOT execute decisions, modify VIEWs, drop columns, or impute. Ends with
  an explicit "Decisions surfaced for downstream cleaning" section listing
  per-dataset open questions.
phase: "01 — Data Exploration"
pipeline_section: "01_04 — Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 3 (Profiling) and 4 (Cleaning)"
dataset: "sc2egset"
question: >
  What is the complete missingness picture (NULL + sentinel-encoded + constant
  columns) per analytical VIEW column, classified by mechanism (Rubin 1976
  MCAR/MAR/MNAR), and which open questions must downstream 01_04 steps resolve
  before Phase 02 imputation design?
method: >
  Three-step per-VIEW audit (matches_flat_clean, player_history_all):
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
  - "01_03_04"
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
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py"
inputs:
  duckdb_tables:
    - "replay_players_raw (44,817 rows)"
    - "replays_meta_raw (22,390 rows)"
  duckdb_views:
    - "matches_flat (44,817 rows / 22,390 replays)"
    - "matches_flat_clean (44,418 rows / 22,209 replays)"
    - "player_history_all (44,817 rows / 22,390 replays)"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json (sentinel and zero-distribution evidence)"
    - "artifacts/01_exploration/03_profiling/* (column-level mechanism evidence — see prior steps)"
outputs:
  duckdb_views:
    - "matches_flat (unchanged)"
    - "matches_flat_clean (unchanged)"
    - "player_history_all (unchanged)"
  schema_yamls:
    - "data/db/schemas/views/player_history_all.yaml (unchanged from PR #138/#139)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (extended with missingness_audit block)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (NEW — one row per (view, column); full-coverage Option B; zero-missingness columns tagged RETAIN_AS_IS / mechanism=N/A; constant columns tagged DROP_COLUMN / mechanism=N/A)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json (NEW — same content, machine-readable)"
  report: "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (extended)"
reproducibility: >
  Code and output in the paired notebook. All SQL verbatim in JSON sql_queries.
  Audit re-runs deterministically from raw tables.
key_findings_carried_forward:
  - "157 replays excluded due to MMR<0 (PR predecessor — kept)"
  - "MMR=0 sentinel covers 83.66% of true_1v1_decisive rows (audit confirms)"
  - "highestLeague='Unknown' covers ~72% (audit confirms)"
  - "clanTag='' covers ~74% (audit confirms via sentinel pass)"
  - "matches_flat_clean's 1v1_decisive filter excludes ~0.06% Undecided/Tie rows from result (CONSORT verified each run; Rule S2 enforced upstream of the audit)"
decisions_surfaced:
  - id: "DS-SC2-01"
    column: "MMR (sentinel=0, ~83.66%)"
    question: >
      Convert MMR=0 to NULL and drop the column from matches_flat_clean
      (per Rule S4 / >80%), OR retain MMR=0 as an explicit `unranked` categorical
      encoding alongside `is_mmr_missing`, OR run the analysis on the rated subset
      only as a sensitivity arm (per Sambasivan 2021 cascade-prevention)?
    mechanism_note: >
      Resolve MMR mechanism contradiction: this plan classifies MMR=0 as
      MAR-primary (tournament replays without ladder MMR — missingness depends
      on observed replay source); MNAR (private pro accounts) is documented as a
      sensitivity branch. Source: 01_03_01 + 01_03_03 cleaning_registry rules.
  - id: "DS-SC2-02"
    column: "highestLeague (sentinel='Unknown', ~72.16%)"
    question: >
      Drop the column entirely (Rule S4 / >50% non-primary), OR retain 'Unknown'
      as its own category (Phase 02 decides if predictive)?
  - id: "DS-SC2-03"
    column: "clanTag (sentinel='', ~74%)"
    question: >
      Drop the column (likely non-predictive at this rate), OR retain as a derived
      `is_in_clan` boolean only?
  - id: "DS-SC2-04"
    column: "result in player_history_all (Undecided/Tie sentinel; non-zero rate in player_history_all)"
    question: >
      How should NULL-target rows in player_history_all be handled when computing
      player history features (e.g., expanding-window win-rate)? Drop these rows,
      mark them as a DRAW outcome category, or retain with NaN target value (so
      games-played counts include them but win-rate denominators exclude)?
  - id: "DS-SC2-05"
    column: "selectedRace (sentinel='', ~2.48%)"
    question: >
      Already converted to 'Random' in VIEWs (PR predecessor); the audit confirms
      zero residual empty-string occurrences in the cleaned VIEWs.
  - id: "DS-SC2-06"
    columns: "gd_mapSizeX / gd_mapSizeY (sentinel=0, ~1.22%)"
    question: >
      VIEWs already CASE-WHEN to NULL (PR predecessor); audit confirms ledger
      reports the converted NULLs, not the original sentinel.
  - id: "DS-SC2-07"
    column: "gd_mapAuthorName"
    question: >
      Drop column on grounds of being a non-predictive metadata field even before
      missingness considered? Decision deferred to 01_04_02+.
  - id: "DS-SC2-08"
    columns: "go_* constants surfaced by runtime constants-detection branch"
    question: >
      Confirm the runtime constants-detection branch reports n_distinct=1 for the
      go_* columns flagged in 01_03_03 (and which exact columns are identified as
      constant in matches_flat_clean vs player_history_all). Drop these per
      Rule S4 / N/A-mechanism in 01_04_02+?
  - id: "DS-SC2-09"
    column: "handicap (sentinel=0, ~0.0045% — 2 anomalous rows)"
    question: >
      NULLIF the 2 anomalous handicap=0 rows + listwise deletion per Rule S3
      (negligible rate), OR retain 0 as an explicit `is_anomalous_handicap` flag?
      B6 deferral note — same pattern as DS-AOESTATS-02: audit will recommend
      CONVERT_SENTINEL_TO_NULL via W3 branch; spec marks
      carries_semantic_content=True (0 is documented as "anomalous game"
      indicator, semantically meaningful); downstream chooses without prejudice
      from the ledger.
  - id: "DS-SC2-10"
    column: "APM in player_history_all (sentinel=0, ~2.53%; 97.9% overlap with selectedRace='')"
    question: >
      Convert APM=0 to NULL via NULLIF in 01_04_02+ (per audit recommendation)
      OR retain APM=0 as a categorical encoding for "extremely short / unparseable
      game"? B6 deferral note — audit will recommend CONVERT_SENTINEL_TO_NULL
      via W3 branch; spec marks carries_semantic_content=True (APM=0 documented
      as correlating with selectedRace='' — meaningful game-state signal);
      downstream chooses without prejudice from the ledger.
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
    DS-SC2-01..10 with current observed rates filled in.
  continue_predicate: >
    Every column in the VIEW appears in the ledger (full-coverage Option B).
    Every column with non-zero missingness has a _missingness_spec entry; zero-
    missingness rows carry mechanism=N/A, recommendation=RETAIN_AS_IS, and
    justification="Zero missingness observed; no action needed." regardless of
    spec. Constant columns (n_distinct=1) carry mechanism=N/A,
    recommendation=DROP_COLUMN with constants-detection justification.
    Every ledger row has non-empty mechanism_justification, recommendation,
    recommendation_justification, and explicit carries_semantic_content boolean.
    Existing zero-NULL assertions (replay_id, toon_id, result in both VIEWs) still
    pass. STEP_STATUS.yaml has 01_04_01: complete.
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
name: "Data Cleaning Execution -- Act on DS-SC2-01..10"
description: >
  Acts on the 10 cleaning decisions surfaced by 01_04_01. Modifies VIEW DDL
  for matches_flat_clean and player_history_all (no raw table changes per
  Invariant I9): drops MMR (Rule S4 / 83.95%), highestLeague (Rule S4 / 72%),
  clanTag (Rule S4 / 74%), 12 go_* constants (DS-SC2-08), gd_mapAuthorName
  (DS-SC2-07 domain), gd_mapSizeX/Y from matches_flat_clean (DS-SC2-06),
  handicap (DS-SC2-09 near-constant). Modifies APM in player_history_all
  via NULLIF (DS-SC2-10) + adds is_apm_unparseable indicator. Adds
  is_decisive_result to player_history_all (DS-SC2-04). Reports CONSORT-style
  column-count flow + subgroup impact + post-cleaning invariant re-validation.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4"
dataset: "sc2egset"
question: >
  Which of the 10 decisions surfaced by 01_04_01 (DS-SC2-01..10) are
  resolved by DDL modifications, what is the column-count and subgroup
  impact, and do all post-cleaning invariants still hold?
method: >
  Modify CREATE OR REPLACE VIEW DDL for matches_flat_clean and player_history_all
  per per-DS resolutions (see plan Section 1). Apply column drops, the APM NULLIF,
  and two new derived columns (is_decisive_result, is_apm_unparseable). Re-run
  the assertion battery from 01_04_01 plus 01_04_02-specific assertions on the
  new column set. Produce a CONSORT-style column-count table and per-DS
  resolution log.
stratification: "By VIEW (matches_flat_clean vs player_history_all) and by DS-SC2-NN."
predecessors:
  - "01_04_01"
methodology_citations:
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.1 (cleaning registry), §4.2 (non-destructive), §4.3 (CONSORT impact), §4.4 (post-validation)"
  - "Liu, X. et al. (2020). Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension. BMJ, 370."
  - "Jeanselme, V. et al. (2024). Participant Flow Diagrams for Health Equity in AI. Journal of Biomedical Informatics, 152."
  - "Schafer, J.L. & Graham, J.W. (2002). Missing data: Our view of the state of the art. Psychological Methods, 7(2)."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed. CRC Press."
  - "Sambasivan, N. et al. (2021). Data Cascades in High-Stakes AI. CHI '21."
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py"
inputs:
  duckdb_views:
    - "matches_flat (44,817 rows -- structural JOIN, unchanged)"
    - "matches_flat_clean (44,418 rows / 22,209 replays -- pre-01_04_02)"
    - "player_history_all (44,817 rows / 22,390 replays -- pre-01_04_02)"
  prior_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (cleaning_registry, missingness_audit, consort_flow)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (100 rows, per-DS empirical evidence)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (decisions_surfaced reference)"
  schema_yamls:
    - "data/db/schemas/views/player_history_all.yaml (current -- to be updated)"
outputs:
  duckdb_views:
    - "matches_flat_clean (replaced via CREATE OR REPLACE -- 28 cols, 44,418 rows)"
    - "player_history_all (replaced via CREATE OR REPLACE -- 37 cols, 44,817 rows)"
  schema_yamls:
    - "data/db/schemas/views/matches_flat_clean.yaml (NEW)"
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
      No new feature computation. matches_flat_clean retains only PRE_GAME
      columns. player_history_all retains IN_GAME_HISTORICAL columns (APM, SQ,
      supplyCappedPercent, header_elapsedGameLoops) which are valid for
      historical computation per the I3 design constraint established in 01_04_01.
  - number: "5"
    how_upheld: >
      Symmetry assertion re-run: every replay_id in matches_flat_clean has
      exactly 1 Win + 1 Loss row. The is_decisive_result derivation in
      player_history_all is symmetric (depends only on result, not on player slot).
  - number: "6"
    how_upheld: >
      All DDL queries stored verbatim in JSON sql_queries. All assertion SQL
      stored verbatim. All per-DS rationale references the ledger row + ledger
      recommendation_justification by view+column.
  - number: "7"
    how_upheld: >
      Thresholds (5/40/80%) come from the 01_04_01 framework block (Schafer &
      Graham 2002 boundary; van Buuren 2018 warning). Per-DS empirical evidence
      (n_sentinel, pct_missing_total, n_distinct) is read from the 01_04_01
      ledger CSV at runtime, not hardcoded.
  - number: "9"
    how_upheld: >
      No raw tables modified. matches_flat (structural JOIN) unmodified.
      matches_long_raw (canonical skeleton from 01_04_00) unmodified. Only
      matches_flat_clean and player_history_all VIEWs are replaced via
      CREATE OR REPLACE. All inputs are 01_04_01 artifacts (predecessor) or
      this step's own DDL output.
gate:
  artifact_check: >
    artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json
    and .md exist and are non-empty. Both schema YAMLs
    (matches_flat_clean.yaml NEW, player_history_all.yaml UPDATED) exist with
    correct column counts.
  continue_predicate: >
    matches_flat_clean has exactly 28 columns. player_history_all has exactly
    37 columns. All zero-NULL assertions pass (replay_id, toon_id, result in
    both VIEWs). Symmetry violations = 0 in matches_flat_clean. CONSORT column-
    count table reproduces drop counts per DS-SC2-01..10. STEP_STATUS.yaml has
    01_04_02: complete. PIPELINE_SECTION_STATUS for 01_04 transitions to complete
    (no further 01_04_NN steps defined in ROADMAP).
  halt_predicate: >
    Any zero-NULL assertion fails; any symmetry violation; any forbidden column
    appears in matches_flat_clean; any expected NEW column missing from
    player_history_all; column count off by even one from spec.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II) > Data Cleaning Decisions"
research_log_entry: "Required on completion."
```

#### Addendum: Duration Augmentation (2026-04-18)

```yaml
addendum_date: "2026-04-18"
addendum_title: "Duration Augmentation -- matches_flat_clean 28 → 30 cols"
addendum_scope: >
  ADDENDUM to 01_04_02. Extends matches_flat_clean VIEW from 28 → 30 columns
  by adding duration_seconds BIGINT (POST_GAME_HISTORICAL) + is_duration_suspicious
  BOOLEAN (POST_GAME_HISTORICAL). Source: player_history_all.header_elapsedGameLoops
  aggregated per replay_id / 22.4 (SC2 Faster loops/sec constant, I7). No row
  changes (I9). STEP_STATUS stays complete per addendum precedent.
new_cols:
  - name: duration_seconds
    type: BIGINT
    token: POST_GAME_HISTORICAL
    derivation: "CAST(ANY_VALUE(header_elapsedGameLoops) / 22.4 AS BIGINT) per replay_id"
    i7_provenance: "details.gameSpeed cardinality=1 in sc2egset (research_log.md:424); Blizzard SC2 Faster=22.4 loops/sec"
  - name: is_duration_suspicious
    type: BOOLEAN
    token: POST_GAME_HISTORICAL
    derivation: "duration_seconds > 86400"
    i8_provenance: "86400s canonical sanity bound; identical across sc2egset, aoestats, aoe2companion"
duration_stats:
  min_seconds: 1
  p50_seconds: 651.0
  p99_seconds: 1876.0
  max_seconds: 6073
  null_count: 0
  suspicious_count: 0
schema_version: "30-col (ADDENDUM: duration added 2026-04-18)"
new_artifact: "artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.json"
new_artifact_md: "artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.md"
notebook: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_duration_augmentation.py"
gates_all_pass: true
```

### Step 01_04_03 -- Minimal Cross-Dataset History View

```yaml
step_number: "01_04_03"
name: "Minimal Cross-Dataset History View"
description: >
  Create matches_history_minimal VIEW: 9-column player-row-grain projection (post-ADDENDUM 2026-04-18)
  of matches_flat_clean (2 rows per 1v1 match). Cross-dataset-harmonized
  substrate for Phase 02+ rating-system backtesting. Canonical TIMESTAMP
  temporal dtype; per-dataset-polymorphic faction vocabulary. Pattern-
  establisher -- aoestats and aoe2companion emit identically-shaped sibling
  views in follow-up PRs (I8).
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4.2 (non-destructive cleaning), Section 4.4 (post-cleaning validation)"
dataset: "sc2egset"
question: >
  What is the minimum cross-dataset-harmonized shape for per-player match
  history required by Phase 02 rating-system backtesting? Does a pure
  projection of matches_flat_clean with TIMESTAMP-cast started_at satisfy
  the I3/I5-analog/I6/I7/I8/I9 contract?
method: >
  CREATE OR REPLACE VIEW on top of matches_flat_clean via self-join on
  replay_id to materialize (player_row, opponent_row) symmetric pairs.
  match_id prefixed 'sc2egset::' for cross-dataset UNION uniqueness.
  started_at via TRY_CAST to canonical TIMESTAMP dtype. Faction strings
  raw (per-dataset polymorphic vocabulary). Validate: row-count parity,
  schema shape, I5-analog NULL-safe symmetry (IS DISTINCT FROM), prefix
  uniqueness, dataset_tag constancy, temporal sanity.
stratification: "By match_id (2 symmetric rows); by faction for vocabulary documentation."
predecessors:
  - "01_04_02"
methodology_citations:
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.2 (non-destructive cleaning)"
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.4 (post-cleaning validation)"
  - "Tukey, J. W. (1977). Exploratory Data Analysis. Addison-Wesley. (raw-string vocabulary documentation)"
  - "Schafer, J. L., & Graham, J. W. (2002). Missing data: Our view of the state of the art. Psychological Methods."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data (2nd ed.). CRC Press."
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_03_minimal_history_view.py"
inputs:
  duckdb_views:
    - "matches_flat_clean (44,418 rows / 22,209 replays -- from 01_04_02)"
  prior_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  schema_yamls:
    - "data/db/schemas/views/matches_flat_clean.yaml"
outputs:
  duckdb_views:
    - "matches_history_minimal (NEW -- 8 cols, 44,418 rows)"
  schema_yamls:
    - "data/db/schemas/views/matches_history_minimal.yaml (NEW)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.md"
reproducibility: >
  CREATE OR REPLACE VIEW DDL + every assertion SQL stored verbatim in the
  validation JSON sql_queries block (I6). DESCRIBE result captured in the
  validation JSON describe_table_rows for reproducibility of nullable flags
  written to schema YAML.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      TIMESTAMP cast (via TRY_CAST) enables chronologically faithful ordering.
      Upstream VARCHAR details_timeUTC has 7 distinct sub-second precision
      lengths (22-28 chars); lex ordering would be non-monotonic across
      formats. Phase 02 consumers use TIMESTAMP started_at as strict-
      less-than anchor.
  - number: "5"
    how_upheld: >
      Player-row symmetry (I5-analog). SYMMETRY_I5_ANALOG_SQL uses
      IS DISTINCT FROM for NULL-safe comparison. Every match_id has exactly
      2 rows; (player_id, opponent_id) pair appears in both directions; won
      values are complementary; faction / opponent_faction are mirrored.
  - number: "6"
    how_upheld: >
      DDL + every assertion SQL + DESCRIBE snapshot in validation JSON.
  - number: "7"
    how_upheld: >
      Magic literals 32 / 42 in PREFIX_CHECK_SQL cite
      src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_long_raw.yaml
      join_key regex [0-9a-f]{32} for provenance.
  - number: "8"
    how_upheld: >
      8-column cross-dataset contract: identical column names + dtypes;
      canonical TIMESTAMP temporal dtype (no TZ); per-dataset-polymorphic
      faction vocabulary (consumers MUST game-condition). aoestats sibling
      PR projects 1-row-per-match to 2-rows with p0/p1 UNION ALL (team1_wins
      slot-asymmetry awareness required).
  - number: "9"
    how_upheld: >
      Pure non-destructive projection. No upstream modification. Only new
      VIEW created.
gate:
  artifact_check: >
    Validation JSON + MD exist. matches_history_minimal.yaml exists with
    8 columns (started_at TIMESTAMP) + invariants block + I8 per-dataset-
    polymorphic faction warning.
  continue_predicate: >
    VIEW exists with 9 columns matching spec (post-ADDENDUM 2026-04-18). 44,418 rows = 22,209 x 2.
    Zero NULL-safe symmetry violations. Zero prefix violations. dataset_tag
    constancy = 1. Zero NULLs in match_id / player_id / opponent_id / won /
    dataset_tag. STEP_STATUS 01_04_03 -> complete. PIPELINE_SECTION_STATUS
    01_04 -> complete.
  halt_predicate: >
    Symmetry violation > 0; row-count discrepancy; prefix violation; NULL in
    non-nullable spec column; column count != 9; started_at dtype != TIMESTAMP;
    upstream YAML byte-diff detected. ON HALT: manually revert
    PIPELINE_SECTION_STATUS 01_04 -> complete before aborting.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet > Cross-dataset harmonization substrate"
  - "Chapter 4 -- Data and Methodology > 4.3 Rating System Backtesting Design (downstream consumer)"
research_log_entry: "Required on completion."
```

### Step 01_04_04 -- Identity Resolution

```yaml
step_number: "01_04_04"
name: "Identity Resolution"
description: >
  Exploratory record-linkage census on sc2egset identity columns (toon_id,
  nickname, region, realm, userID, playerID). Classifies the Phase-01
  hypothesis "toon_id > nickname as multi-account trace" into Fellegi-
  Sunter-style agreement patterns. Produces 8-query SQL ledger + 5
  DS-SC2-IDENTITY-* decisions routed to Phase 02. No VIEW DDL; no raw
  modification (I9).
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4 (cleaning census pattern) + Section 5 (panel-EDA feed-forward)"
dataset: "sc2egset"
question: >
  What fraction of the observed toon_id > nickname asymmetry in sc2egset
  is produced by multi-region accounts (Battle.net server-scoping), and
  what fraction by common-handle collisions? Feeds thesis §4.2.2 [REVIEW]
  marker closure.
method: >
  Five-key uniqueness census (toon_id; (region,realm,toon_id);
  LOWER(nickname); (LOWER(nickname),region); (LOWER(nickname),region,realm))
  + toon_id cross-region audit + nickname cross-region detail list with
  temporal windows + Fellegi-Sunter Class A/B/C temporal-overlap
  classification + within-region handle-collision audit + userID
  refutation cross-check + region/realm sanity + robustness cross-check
  against matches_flat_clean.
stratification: "By candidate identity key; by region/realm label."
predecessors:
  - "01_04_01"
  - "01_04_02"
  - "01_04_03"
methodology_citations:
  - "Fellegi, I. P. & Sunter, A. B. (1969). A Theory for Record Linkage. JASA 64(328)."
  - "Christen, P. (2012). Data Matching. Springer (Ch. 5 false-merge rate thresholds)."
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.2 (non-destructive cleaning), §5 (panel-EDA feed-forward)"
  - ".claude/scientific-invariants.md Invariant #2 (canonical identifier)"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04_identity_resolution.py"
inputs:
  duckdb_views:
    - "matches_flat (44,817 rows, IDENTITY cols intact)"
    - "matches_flat_clean (44,418 rows, robustness cross-check)"
    - "matches_long_raw (44,817 rows, canonical skeleton)"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.md (2.26 baseline)"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md"
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (DS-SC2-01..10 precedent)"
outputs:
  duckdb_views: []  # none; exploration only (I9)
  schema_yamls: []  # none
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json (8 SQL queries verbatim per I6)"
    - "artifacts/01_exploration/04_cleaning/01_04_04_cross_region_nicknames.csv (246 rows)"
    - "artifacts/01_exploration/04_cleaning/01_04_04_within_region_handle_collisions.csv (451 rows)"
    - "artifacts/01_exploration/04_cleaning/plots/01_04_04_key_cardinality_bars.png"
    - "artifacts/01_exploration/04_cleaning/plots/01_04_04_toon_region_heatmap.png"
    - "artifacts/01_exploration/04_cleaning/plots/01_04_04_nickname_cross_region_stacked.png"
  report: "artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.md"
reproducibility: >
  All 8 SQL queries stored verbatim in validation JSON sql_queries block
  (I6). Deterministic census; no random sampling in sc2egset slice.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No in-game columns used for identity derivation (APM/SQ excluded).
      Nickname, region, realm, toon_id all PRE_GAME or IDENTITY per 01_04_02
      classification.
  - number: "6"
    how_upheld: >
      All SQL stored verbatim in validation JSON sql_queries. 8 keys:
      single_key_census, toon_id_cross_region_audit, nickname_cross_region_audit,
      temporal_overlap_classification, within_region_handle_collision,
      userid_refutation, region_realm_sanity, robustness_crosscheck.
  - number: "7"
    how_upheld: >
      2.26 ratio baseline cites 01_02_04 census (toon_id=2495, nickname=1106);
      5% within-region collision threshold cites Christen 2012 Ch. 5;
      ±1% robustness delta cites 399/44,817=0.89% empirical basis.
  - number: "8"
    how_upheld: >
      Decision ledger language identical to aoestats + aoe2companion sibling
      01_04_04 plans; verdict rubric (A/B/C) cross-dataset consistent.
  - number: "9"
    how_upheld: >
      Pure read-only analysis. No raw-table mutation. No new VIEW created.
      All 3 sc2egset view YAMLs byte-identical post-execution.
gate:
  artifact_check: >
    JSON + MD + 2 CSVs + 3 PNGs all exist non-empty.
  continue_predicate: >
    Ratio K1/K_cs = 2.2559 within 2.257 +/- 0.05 (I7 baseline). 0 cross-region
    toon_ids (Battle.net scoping). 5 DS-SC2-IDENTITY-* decisions populated.
    I9 empty diff on all sc2egset view + raw YAMLs. STEP_STATUS 01_04_04
    -> complete; PIPELINE_SECTION 01_04 -> complete (roundtrip restore).
  halt_predicate: >
    Ratio drift > 0.05 (upstream change / SQL bug); cross-region toon_id
    count > 0 (data-pipeline bug OR Battle.net legacy). Manual revert of
    PIPELINE_SECTION_STATUS before aborting.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.2.2 Rozpoznanie tozsamosci gracza (operational evidence closes [REVIEW] marker)"
  - "Chapter 4 -- Data and Methodology > 4.4.1 Per-player split justification (feeds Phase 02 grouping-key choice)"
research_log_entry: "Required on completion."
decisions_surfaced:
  - id: "DS-SC2-IDENTITY-01"
    scope: "Phase 02 canonical player primary key"
    evidence: "K1=2495 toon_ids; K_cs=1106 case-sensitive nicks; K4=(LOWER(nick),region)=1473; K5=1487; 0 cross-region toon_ids; 294 Class A cross-region-overlap nickname pairs; 451/1473=30.6% within-region collision rate"
    recommendation: "REJECT toon_id-alone AND REJECT LOWER(nickname)-alone; use composite key with behavioral disambiguation -- deferred to Phase 02"
    routed_to: "Phase 02 / 02_07 Rating Systems"
  - id: "DS-SC2-IDENTITY-02"
    scope: "LOWER(nickname)-alone as primary key"
    evidence: "30.6% within-region LOWER(nickname) collision rate (451/1473) >> Christen 2012 5% threshold"
    recommendation: "REJECT"
    routed_to: "Phase 02 / 02_07"
  - id: "DS-SC2-IDENTITY-03"
    scope: "Class A/B temporal-overlap pairs handling"
    evidence: "294 Class A (overlap, multi-account candidate); 15,474 Class B (disjoint, migration OR different player); 317 Class C (degenerate)"
    recommendation: "Phase 02 entity-resolution: Class A MERGE candidates (pending behavioral-fingerprint disambiguation); Class B conservative-separate; Class C insufficient evidence"
    routed_to: "Phase 02 / 02_07"
  - id: "DS-SC2-IDENTITY-04"
    scope: "region='Unknown' bucket (~12.83% of rows)"
    evidence: "Unknown region is a valid value, not a sentinel -- pre-metadata-capture tournaments"
    recommendation: "Treat Unknown as distinct region value; do NOT merge with known regions"
    routed_to: "Phase 02 / 02_03 Cold Starts"
  - id: "DS-SC2-IDENTITY-05"
    scope: "Composite canonical identity VIEW design (player_identity_canonical)"
    evidence: "Multi-signal required: (region, realm, toon_id) granular base + optional nickname-based MERGE for Class A overlap + behavioral-fingerprint confirmation (APM per Hahn et al. 2020)"
    recommendation: "Design player_identity_canonical VIEW in Phase 02 after running 01_04_04 augmentation PR for sc2egset worldwide-identity classifier"
    routed_to: "Phase 02 / 02_07 + 01_04_04 augmentation PR (this branch: feat/01-04-04-sc2egset-worldwide-identity)"
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

### Step 01_04_04b -- Stub worldwide identity VIEW (decomposition-based)

```yaml
step_number: "01_04_04b"
name: "Worldwide Identity VIEW (decomposition-based)"
description: >
  Create player_identity_worldwide VIEW that decomposes toon_id (full Battle.net R-S2-G-P qualifier)
  into human-readable columns (region_code, realm_code, profile_id, region_label, realm_label,
  nickname_case_sensitive). Investigate 2 empty-toon_id outlier rows. No hashing, no composite
  encoding -- toon_id IS the worldwide identifier (region-scoped per Blizzard design).
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
parent_step: "01_04_04"
plan_version: "R4"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.py"
completed_at: "2026-04-18"
outputs:
  view: "player_identity_worldwide (2,494 rows, 7 cols)"
  schema_yaml: "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_identity_worldwide.yaml"
  artifacts:
    - "reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.json"
    - "reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.md"
key_findings:
  - "toon_id stores full Battle.net R-S2-G-P qualifier -- no hashing needed"
  - "273 toon_ids have multiple nicknames; VIEW picks modal nickname per toon_id"
  - "userID cardinality=16 = local Battle.net profile slot indices (0..15), NOT player IDs"
  - "2 empty-toon_id rows are observer-profile ghost entries (handicap=0, color_rgba=0)"
  - "Outliers from 2 different tournaments (IEM 2017, HSC 2019) -- not systematic"
  - "No external bridge available for cross-region toon_id merge (R2 confirmed)"
```

