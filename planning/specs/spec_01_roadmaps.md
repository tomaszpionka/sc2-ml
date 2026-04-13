---
task_id: "T01"
task_name: "Add 01_02_01 step defs to all 3 ROADMAPs"
agent: "executor"
model: "haiku"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md"
  - "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md"
read_scope:
  - "docs/templates/step_template.yaml"
category: "A"
---

# Spec: Add 01_02_01 step defs to all 3 ROADMAPs

## Objective

Add the 01_02_01 step definition to each dataset's ROADMAP.md, defining
the DuckDB ingestion (aoe2companion, aoestats) or investigation
(sc2egset) step under Pipeline Section 01_02 (EDA).

## Instructions

1. Read `docs/templates/step_template.yaml` for the step definition schema.
2. Add the following step definitions after the existing 01_01_02 block
   in each ROADMAP.

**sc2egset** (`src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`):
```yaml
step_number: "01_02_01"
name: "DuckDB Ingestion Investigation"
description: "Investigate how DuckDB 1.5.1 read_json_auto handles sc2egset nested JSON. Test on 5-10 sample files spanning the file-size distribution. Determine table split strategy, JSON column behavior, and event array storage feasibility. Full census of all 70 map_foreign_to_english_mapping.json files. Produce a design artifact — no full ingestion."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "sc2egset"
question: "How does DuckDB 1.5.1 read_json_auto handle sc2egset's nested JSON structure (11 root keys, 7,350 keypaths, dynamic-key ToonPlayerDescMap, 3 event arrays), what table split strategy is needed, what is the estimated DuckDB storage for event arrays, and what is the schema/consistency of all 70 map_foreign_to_english_mapping.json files?"
method: "Compute per-directory avg MB/file from 01_01_01 data (total_bytes / file_count). Select 5-10 .SC2Replay.json files: 1 from smallest-avg dir, 1 from largest-avg dir, the largest individual file by byte size, and 2-3 from mid-distribution. Test read_json_auto on each: record DuckDB types per root key, check ToonPlayerDescMap (dynamic keys) preservation vs flattening, note parse errors. Event array assessment on ALL sampled files: measure JSON byte size of gameEvents/trackerEvents/messageEvents, count elements, report stats (mean/median/min/max), extrapolate to 22,390 files for SSD feasibility. Test batch ingestion on 1 mid-size tournament directory (~100-300 files). Test single-table vs split-table approaches. Full census of all 70 map_foreign_to_english_mapping.json files (at raw/TOURNAMENT/map_foreign_to_english_mapping.json, NOT inside _data/): read all 70, record root type/key count/value types per file, check cross-file schema consistency, test read_json_auto on 1 file, propose table DDL if uniform. Produce design artifact with proposed DDL for a future full-ingestion step."
stratification: "By root key group (metadata vs events vs player desc map); by tournament directory for map alias files."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/01_eda/01_02_01_duckdb_ingestion.py"
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
    - "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json"
  report: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.md"
reproducibility: "Investigation code on sample files in the notebook. File selection derived from 01_01_01 per-directory size data. Storage estimates derived from measured JSON sizes with extrapolation formula shown. All code and output paired per Invariant #6. DuckDB version 1.5.1 noted."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Sample read_json_auto tests, storage measurements, and map alias census code in the notebook."
  - number: "7"
    how_upheld: "Sample file selection thresholds derived from 01_01_01 per-directory size data (computed, not assumed)."
  - number: "9"
    how_upheld: "Investigation reads sample file content for table design feasibility. Event array sizes measured for storage estimation (design input), not content profiling. Map alias census is structural (schema, key counts), not semantic."
gate:
  artifact_check: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "Design artifact documents: (1) read_json_auto behavior for all 11 root keys with DuckDB types, (2) proposed table split strategy with rationale, (3) event array storage estimate with SSD feasibility verdict, (4) full census of all 70 map_foreign_to_english_mapping.json files with cross-file consistency assessment and proposed DDL."
  halt_predicate: "read_json_auto cannot parse any sample file, OR batch ingestion of a single directory fails."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

**aoe2companion** (`src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`):
```yaml
step_number: "01_02_01"
name: "DuckDB Ingestion"
description: "Load aoe2companion Parquet and CSV files into DuckDB tables. Inspect pyarrow logical types for binary columns across all 3 Parquet subdirectories to determine whether binary_as_string=true is required. Validate CSV type inference for ratings. Verify row and column counts. Investigate matches/ratings file count gap (2073/2072)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "Can all aoe2companion files be loaded into DuckDB tables with correct type mappings, are binary columns unannotated BYTE_ARRAY requiring binary_as_string=true, are CSV types inferred correctly for ratings, do row counts align with file inventory, and what explains the 2073/2072 file count gap?"
method: "PYARROW INSPECTION: Run pyarrow.parquet.ParquetFile.schema on sample files from each subdirectory (matches, leaderboards, profiles) to determine binary column annotation status (parquet_logical, converted_type). If unannotated BYTE_ARRAY, binary_as_string=true is required; if annotated STRING/UTF8, DuckDB handles natively. Record per-subdirectory binary column counts and annotation status. Smoke test and pre-ingestion functions live in pre_ingestion.py. SMOKE TEST: ingest 3-5 Parquet files from matches/ (earliest, middle, latest by date) + 3-5 CSV from ratings/ into temp tables with binary_as_string=true (if justified by pyarrow inspection). Verify DESCRIBE: binary columns are VARCHAR (not BLOB), CSV-inferred types are reasonable (profile_id numeric, date parsed). Cross-check column schemas across smoke-test files to assess cross-file consistency. FULL INGESTION: CREATE TABLE matches_raw AS ...; CREATE TABLE ratings_raw AS ...; CREATE TABLE leaderboards_raw/profiles_raw from singletons with binary_as_string=true and filename=true (every raw table carries filename for provenance). POST-INGESTION: DESCRIBE all 4 tables — record full DuckDB-assigned types. GATE for ratings_raw: profile_id must be INTEGER/BIGINT, date must be DATE/TIMESTAMP, games/rating/rating_diff must be INTEGER — if any is VARCHAR, re-ingest with explicit types=. Row counts per table. Column count verification (matches_raw: 54+1 filename=55, ratings_raw: 7+1=8, leaderboards_raw: 18+1=19, profiles_raw: 13+1=14). NULL count for won. Investigate 2073/2072 file gap (identify which date(s) have matches but no ratings, or vice versa)."
stratification: "By subdirectory (matches, ratings, leaderboards, profiles)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/01_eda/01_02_01_duckdb_ingestion.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "ratings_raw"
    - "leaderboards_raw"
    - "profiles_raw"
  prior_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
    - "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json"
  report: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.md"
reproducibility: "DuckDB SQL in the notebook. Parquet logical type inspection via pyarrow.parquet.ParquetFile.schema on sample files to determine binary column annotation status. Row counts verified against 01_01_01 file counts. Smoke test and pre-ingestion functions in pre_ingestion.py. All code and output paired per Invariant #6. DuckDB version 1.5.1 noted."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "DDL, ingestion SQL, DESCRIBE output, and row counts in the notebook."
  - number: "7"
    how_upheld: "binary_as_string=true justified by in-notebook pyarrow logical type inspection. File counts from 01_01_01 used as verification baseline."
  - number: "9"
    how_upheld: "Conclusions limited to: tables created, types assigned, row counts, file-count reconciliation. Binary column justification cites Parquet metadata (structural), not content."
gate:
  artifact_check: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "DuckDB tables (matches_raw, ratings_raw, leaderboards_raw, profiles_raw) exist with non-zero row counts AND full DESCRIBE output recorded for all 4 tables AND ratings_raw DESCRIBE shows profile_id as INTEGER/BIGINT, date as DATE/TIMESTAMP, and games/rating/rating_diff as INTEGER (not VARCHAR) AND smoke test passed before full ingestion."
  halt_predicate: "DuckDB cannot read any Parquet or CSV files, OR smoke test shows binary columns as BLOB (not VARCHAR), OR ratings_raw type gate fails after re-ingestion attempt."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

**aoestats** (`src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`):
```yaml
step_number: "01_02_01"
name: "DuckDB Ingestion"
description: "Load aoestats Parquet files into DuckDB with union_by_name=true. Pre-ingestion variant column census determines the actual type distribution of the 7 variant columns identified by 01_01_02 across all source files. Smoke test confirms DuckDB auto-promotion handles each variant pattern correctly. Load overview.json as reference table. Document missing-week asymmetry (171 vs 172 files)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoestats"
question: "What are the actual type distributions of the 7 variant columns across all source files, can DuckDB union_by_name handle them correctly via auto-promotion (preserving native types rather than forcing VARCHAR), and do post-ingestion NULL patterns for presence/absence columns match the file-level census?"
method: "PRE-INGESTION VARIANT CENSUS: Run pyarrow.parquet.read_schema on ALL 172 matches + 171 players files. For each of the 7 variant columns identified by 01_01_02, record the type distribution across files (e.g., how many files have int64 vs double for a given column, how many have null-typed columns). This census is the authoritative source for variant column patterns — its results determine the ingestion strategy and provide the baseline for post-ingestion NULL verification. Smoke test and pre-ingestion functions live in pre_ingestion.py. SMOKE TEST: ingest 3-5 files from each subdirectory (earliest, middle, latest) into temp tables with union_by_name=true and filename=true. Verify DESCRIBE: variant columns have correct promoted types (not VARCHAR), duration/irl_duration are INTERVAL, column counts correct (matches_raw: 17+1 filename=18, players_raw: 13+1=14). FULL INGESTION: CREATE TABLE matches_raw AS ...; CREATE TABLE players_raw AS ...; CREATE TABLE overviews_raw AS SELECT * FROM read_json_auto('raw/overview/overview.json', filename=true) — produces table with filename provenance column. POST-INGESTION: DESCRIBE ALL 3 tables. Verify duration/irl_duration → INTERVAL, test EXTRACT(EPOCH FROM duration) for reasonable values. For each variant column: SELECT COUNT(*) FILTER (WHERE col IS NULL) — NULL counts must correspond to file-level absence pattern from census. Note on profile_id: if promoted to DOUBLE from mixed int64/double sources, player IDs as float64 may cause join precision issues for IDs > 2^53; flag for EDA investigation, do not alter at bronze layer. Investigate missing-week asymmetry (171 players vs 172 matches files)."
stratification: "By subdirectory (matches, players, overview)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/01_eda/01_02_01_duckdb_ingestion.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
    - "overviews_raw"
  prior_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
    - "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json"
  report: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.md"
reproducibility: "Pre-ingestion pyarrow census code and DuckDB SQL in the notebook. Variant column type distributions established by full pyarrow census in the notebook. NULL counts verified against file-level absence pattern from same census. All code and output paired per Invariant #6. DuckDB version 1.5.1 noted."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "DDL, ingestion SQL, census code, DESCRIBE output, and NULL counts in the notebook."
  - number: "7"
    how_upheld: "No type-forcing thresholds — DuckDB auto-promotion is deterministic. Variant column type distributions from full pyarrow census (not sampled)."
  - number: "9"
    how_upheld: "Conclusions limited to: tables created, types assigned (including auto-promotion results), row counts, NULL patterns matching file-level census. profile_id precision flag is structural, not semantic."
gate:
  artifact_check: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "DuckDB tables exist with non-zero row counts AND full DESCRIBE output recorded for all 3 tables AND variant columns have expected promoted types (raw_match_type: DOUBLE, started_timestamp: TIMESTAMP, profile_id: DOUBLE, opening: VARCHAR, age uptimes: DOUBLE) AND duration/irl_duration are INTERVAL AND NULL counts for presence/absence columns match file census AND smoke test passed."
  halt_predicate: "DuckDB cannot read Parquet files with union_by_name, OR smoke test shows unexpected types (e.g., variant column auto-widened to VARCHAR when numeric promotion was expected), OR overviews_raw fails to parse from overview.json."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

3. Verify all 3 ROADMAPs have the 01_02_01 step definition blocks added
   after the existing 01_01_02 block.
4. Verify artifact paths use `01_eda/` subdirectory (new pipeline section).

## Verification

- All 3 ROADMAPs contain the 01_02_01 step definition block
- Step definitions match the plan exactly (content extracted, not invented)
- `step_template.yaml` schema followed for all fields
- Artifact paths use `01_eda/` subdirectory

## Context

- Read `docs/templates/step_template.yaml` for the step definition schema
  before adding blocks.
- The step definitions are copied verbatim from the plan's T01 section
  (plan lines 174-324). No modifications except those required by
  accepted critique findings.
