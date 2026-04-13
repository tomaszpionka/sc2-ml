---
category: "A"
branch: "feat/phase01-duckdb-ingestion"
date: "2026-04-13"
planner_model: "claude-opus-4-6"
dataset: "sc2egset, aoe2companion, aoestats"
phase: "01"
pipeline_section: "01_02"
invariants_touched:
  - 6
  - 7
  - 9
source_artifacts:
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  - "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
  - "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
---

# Category A Plan: Phase 01 Step 01_02_01 — DuckDB Ingestion

**Phase/Step:** Phase 01, Pipeline Section 01_02 (EDA), Step 01_02_01
**Datasets:** sc2egset, aoe2companion, aoestats

## Scope

Load all 3 datasets' raw files into DuckDB as queryable tables. Each
dataset has a different ingestion complexity reflecting the nature of
its source format:

- **sc2egset:** Investigate `read_json_auto` behavior on sample files —
  determine which root keys load as JSON columns, how event arrays and
  ToonPlayerDescMap are handled, and propose a table split strategy.
  No full ingestion — the investigation informs a future ingestion step.
- **aoe2companion:** Straightforward Parquet/CSV glob ingestion (flat,
  consistent schemas)
- **aoestats:** Parquet glob ingestion with `union_by_name=True` to handle
  7 variant columns; document nullable columns from schema transitions

After ingestion (aoe2companion, aoestats) and investigation (sc2egset),
subsequent EDA happens as DuckDB SQL for the ingested datasets, while
sc2egset ingestion is planned as a follow-up based on investigation findings.

## Problem Statement

Pipeline section 01_01 (Acquisition & Source Inventory) is complete:
we know what files exist (01_01_01) and what their schemas look like
(01_01_02). The next phase of work is EDA (01_02), and the first step
is getting the data into a queryable format.

The three datasets have fundamentally different ingestion challenges:

**sc2egset (investigation only):** 22,390 nested JSON files (~209 GiB) with
11 root keys, 7,350 keypaths, and 5-level nesting. Before committing to a
full ingestion approach, test `read_json_auto` on sample files (3-5 from
different eras). Determine: which root keys load as JSON columns, how
DuckDB handles ToonPlayerDescMap (dynamic keys), event array sizes per file,
and whether one table or multiple is needed. Also inspect
`map_foreign_to_english_mapping.json` schema. Produce a design artifact —
no full ingestion in this step.

**aoe2companion (easy):** 2,073 dated Parquet files + 2,072 CSV files +
2 singleton Parquet files. 01_01_02 identified binary-typed columns across
all 3 Parquet subdirectories — the notebook will inspect pyarrow logical
types to determine whether `binary_as_string=true` is required.
`read_csv_auto` for ratings with post-ingestion type validation (01_01_02
shows all columns as pandas `object` — types unresolved). Investigate
2073/2072 file count gap.

**aoestats (medium):** 172+171 weekly Parquet files with 7 variant columns
across matches (2) and players (5) identified by 01_01_02. The notebook
will run a full pyarrow census on all source files to determine the actual
type patterns per variant column. DuckDB 1.5.1 documentation indicates
`union_by_name=true` auto-promotes numeric types and fills NULLs for absent
columns — the notebook's smoke test will confirm this empirically on this
dataset's specific type combinations.

## Assumptions & Unknowns

- **DuckDB version: 1.5.1** (pinned as `^1.5.1` in `pyproject.toml`).
  Version-dependent behaviors relevant to this step:
  - `binary_as_string` defaults to `false` — explicit `true` required for
    legacy Parquet writers that store text as unannotated BYTE_ARRAY
  - `union_by_name` auto-promotes on type mismatch: int64↔double→DOUBLE,
    timestamp[us]↔timestamp[ns]→TIMESTAMP_NS, string↔numeric→VARCHAR
  - `duration[ns]` maps to INTERVAL (truncates nanoseconds to microseconds)
  - `read_parquet` does NOT have a `types=` parameter (the `schema=`
    parameter exists but expects MAP type and cannot combine with
    `union_by_name`)
- DuckDB is already installed and accessible via the existing config
  (`data/db/db.duckdb` per dataset).
- **All three DuckDB database files have been deleted (clean slate).**
  DuckDB creates a fresh database on first `duckdb.connect()`. No DROP
  TABLE logic is needed.
- **Raw-layer table naming convention:** `<entity>_raw` suffix.
  sc2egset: `replays_raw`, `map_foreign_to_english_mappings_raw`.
  aoe2companion: `matches_raw`, `ratings_raw`, `leaderboards_raw`,
  `profiles_raw`.  aoestats: `matches_raw`, `players_raw`,
  `overviews_raw`.
- **Pre-ingestion code lives in `pre_ingestion.py`.**  Step 01_02_01
  performs smoke tests and pyarrow inspection, not full ingestion.
  Functions for this step go in
  `src/rts_predict/games/<game>/datasets/<dataset>/pre_ingestion.py`.
  Existing `ingestion.py` modules (aoe2companion, aoestats) and
  `aoe2companion/types.py` (`DtypeDecision`) are from prior experiments
  — they use the obsolete `raw_<entity>` prefix naming and presuppose
  answers the notebook should discover (e.g., whether ratings CSVs need
  explicit dtype handling). These modules are not used in this step and
  will be reconciled in a future full-ingestion step.
- sc2egset uses bronze-layer approach: load root keys as JSON columns,
  defer flattening. This avoids the complex design-before-ingestion
  bottleneck.
- sc2egset ingestion may take significant time (~209 GiB of JSON parsing).
  The notebook timeout should be extended or the ingestion run as a
  callable function with progress logging.
- aoe2companion and aoestats ingestion should be fast (Parquet is columnar,
  DuckDB reads it natively).
- **Parquet type mapping requires pyarrow schema awareness.** DuckDB's
  `read_parquet` maps Arrow types to DuckDB types, but some mappings are
  non-obvious: Arrow `binary` → BLOB or VARCHAR (controlled by
  `binary_as_string`), Arrow `duration[ns]` → INTERVAL (truncates to
  microseconds). The ingestion notebooks must validate DuckDB's type
  choices post-ingestion via DESCRIBE for ALL tables.
- **aoe2companion binary columns require notebook investigation.** 01_01_02
  identified binary-typed columns across all 3 subdirectories. Column names
  suggest text content, which would indicate a legacy Parquet writer that
  failed to set STRING/UTF8 annotations. The notebook will run pyarrow
  logical-type inspection on sample files to determine whether these are
  unannotated BYTE_ARRAY (requiring `binary_as_string=true`) or annotated
  STRING/UTF8 (where DuckDB handles them natively).
- **aoestats variant columns (7 total) require notebook census.** 01_01_02
  identified type inconsistencies across files. DuckDB documentation
  indicates `union_by_name=true` auto-promotes numeric types to DOUBLE,
  timestamp precision to TIMESTAMP_NS, and fills NULLs for absent columns.
  The notebook will run a full pyarrow census on all source files to
  determine the exact type distribution per variant column, then the smoke
  test will confirm DuckDB handles each case correctly. No `types=`
  parameter exists in `read_parquet`. If `profile_id` is promoted to
  DOUBLE from mixed sources, flag for EDA investigation (join precision
  risk for IDs > 2^53) — do not alter at bronze layer.
- sc2egset `map_foreign_to_english_mapping.json` files (70 total, one per
  tournament directory) were inventoried by 01_01_01 but NOT schema-profiled
  by 01_01_02. Their structure is unknown. The investigation step includes
  a full census of all 70 files to establish schema, cross-file consistency,
  and DuckDB loadability.

## Literature Context

Not directly applicable — DuckDB ingestion is data engineering, not
methodology. The sc2egset flattening draws on the SC2EGSet paper
(Bialecki et al. 2023) for understanding the replay JSON structure.

## Open Questions

1. sc2egset: Can `read_json_auto` load all 11 root keys as JSON columns
   in one table, or do event arrays (gameEvents, trackerEvents,
   messageEvents) force a split into separate tables? The notebook must
   investigate this empirically on a sample file.
2. sc2egset: At ~209 GiB, full ingestion may exceed the 600s nbconvert
   timeout. If so, the ingestion function logs progress to a file
   referenced from the notebook (Invariant #6 compliance path).
3. aoestats: Variant column type changes may affect `union_by_name`
   behavior. DuckDB documentation indicates auto-promotion for numeric
   and timestamp types, but empirical confirmation on this dataset's
   specific type combinations is needed. The notebook's pre-ingestion
   census + smoke test will resolve this.

---

## Execution Steps

### T01 — Update all 3 ROADMAPs with 01_02_01 step definitions

**Objective:** Add the 01_02_01 step definition to each dataset's ROADMAP.

**Instructions:**
1. Read `docs/templates/step_template.yaml` for the schema.
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
method: "PRE-INGESTION VARIANT CENSUS: Run pyarrow.parquet.read_schema on ALL 172 matches + 171 players files. For each of the 7 variant columns identified by 01_01_02, record the type distribution across files (e.g., how many files have int64 vs double for a given column, how many have null-typed columns). This census is the authoritative source for variant column patterns — its results determine the ingestion strategy and provide the baseline for post-ingestion NULL verification. Smoke test and pre-ingestion functions live in pre_ingestion.py. SMOKE TEST: ingest 3-5 files from each subdirectory (earliest, middle, latest) into temp tables with union_by_name=true and filename=true. Verify DESCRIBE: variant columns have correct promoted types (not VARCHAR), duration/irl_duration are INTERVAL, column counts correct (matches_raw: 17+1 filename=18, players_raw: 13+1=14). FULL INGESTION: CREATE TABLE matches_raw AS ...; CREATE TABLE players_raw AS ...; CREATE TABLE overviews_raw AS SELECT * FROM read_json_auto('raw/overview/overview.json') — produces 8-column table. POST-INGESTION: DESCRIBE ALL 3 tables. Verify duration/irl_duration → INTERVAL, test EXTRACT(EPOCH FROM duration) for reasonable values. For each variant column: SELECT COUNT(*) FILTER (WHERE col IS NULL) — NULL counts must correspond to file-level absence pattern from census. Note on profile_id: if promoted to DOUBLE from mixed int64/double sources, player IDs as float64 may cause join precision issues for IDs > 2^53; flag for EDA investigation, do not alter at bronze layer. Investigate missing-week asymmetry (171 players vs 172 matches files)."
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

**Verification:**
- All 3 ROADMAPs have 01_02_01 step definition blocks
- Artifact paths use `01_eda/` subdirectory (new pipeline section)

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`

**Read scope:**
- `docs/templates/step_template.yaml`

---

### T02 — Execute DuckDB ingestion for all 3 datasets

**Objective:** Create and execute 3 ingestion notebooks, produce artifacts,
write research log entries, update STEP_STATUS, and write a CROSS entry.

Parameterized task — different complexity per dataset, same output structure.

**Datasets:**

```yaml
datasets:
  - id: sc2egset
    game: sc2
    complexity: "investigation only — test read_json_auto, no full ingestion"
    notebook: sandbox/sc2/sc2egset/01_exploration/01_eda/01_02_01_duckdb_ingestion.py
    artifacts_dir: src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_eda/
    research_log: src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
    step_status: src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml
    db_path: src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb
    raw_dir: src/rts_predict/games/sc2/datasets/sc2egset/data/raw/
    prior_artifacts:
      - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json
      - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json
    step_scope: "content"
    method: |
      INVESTIGATION (no full ingestion):
      1. Select 5-10 sample .SC2Replay.json files spanning the per-file-size
         distribution: compute avg MB/file per directory from 01_01_01 data
         (total_bytes / file_count), then pick 1 from the smallest-avg dir,
         1 from the largest-avg dir, the literal largest individual file by
         byte size, plus 2-3 from the middle of the distribution. This
         ensures read_json_auto is tested across the full file-size range.
      2. Test read_json_auto on each sample:
         - Record which of the 11 root keys become columns
         - Record DuckDB types assigned to each column
         - Check if ToonPlayerDescMap (dynamic keys) is preserved as JSON
           or erroneously flattened
         - Note any parse errors or warnings
      3. Event array storage assessment on ALL sampled files (5-10):
         - Measure JSON byte size of gameEvents, trackerEvents, messageEvents
         - Count elements in each array
         - Report mean, median, min, max across sampled files
         - Extrapolate to 22,390 files: estimated total DuckDB storage
           if event arrays are ingested as JSON columns
         - Report whether this fits comfortably on local SSD
         (1 file is insufficient — per-file sizes range 2.5x across eras)
      4. Test batch ingestion on 1 full tournament directory:
         - Pick a mid-size directory (~100-300 files)
         - Test read_json_auto on the directory glob
         - Check DuckDB memory behavior (SET memory_limit awareness)
         - Report time and memory usage
      5. Test single-table approach: can all 11 root keys coexist in one
         table? If event arrays blow up row size, test split-table approach
         (metadata keys vs event keys in separate tables)
      6. map_foreign_to_english_mapping.json — full census of all 70 files:
         01_01_01 identified 70 such files (one per tournament directory,
         at `raw/TOURNAMENT/map_foreign_to_english_mapping.json` — NOT
         inside `_data/`). 01_01_02 did not examine their schema at all.
         This step fills that gap:
         a. Read ALL 70 files (trivially small I/O — no sampling justified)
         b. For each: record root type (dict/list), key count, value types
         c. Check cross-file schema consistency: do all 70 share the same
            structure (same root type, same key set)?
         d. If dict: record sample key-value pair pattern (map foreign
            name → English name, or more complex?)
         e. Record total combined size of all 70 files
         f. If all uniform: propose single DuckDB table DDL for future
            ingestion (e.g., map_aliases table with columns tournament,
            foreign_name, english_name — or as JSON column if structure
            is too variable)
         g. If variant across files: document which files differ and how
         h. Test read_json_auto on 1 file — does DuckDB parse it
            correctly, or does it need Python-based loading?
      7. Produce design artifact with:
         - read_json_auto behavior per root key (type, success/failure)
         - Event array storage estimate (mean/median/range + total-corpus)
         - Batch ingestion test results (time, memory, errors)
         - Proposed table split strategy with rationale
         - map_foreign_to_english_mapping.json: full census results,
           cross-file consistency, proposed table DDL
         - Recommended DDL for a FUTURE ingestion step
         - filename column requirement documented
      8. Do NOT load all 22,390 files — this is investigation only

  - id: aoe2companion
    game: aoe2
    complexity: "easy — flat Parquet + CSV glob"
    notebook: sandbox/aoe2/aoe2companion/01_exploration/01_eda/01_02_01_duckdb_ingestion.py
    artifacts_dir: src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_eda/
    research_log: src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md
    step_status: src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml
    db_path: src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/db.duckdb
    raw_dir: src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/
    prior_artifacts:
      - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json
      - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json
    step_scope: "content"
    method: |
      1. PYARROW BINARY COLUMN INSPECTION:
         Run pyarrow.parquet.ParquetFile.schema on sample files from each
         Parquet subdirectory (matches, leaderboards, profiles). For each
         binary-typed column: record parquet_logical and converted_type.
         Determine whether unannotated BYTE_ARRAY (requiring
         binary_as_string=true) or annotated STRING/UTF8. Record per-
         subdirectory binary column counts and annotation status.
      2. SMOKE TEST — ingest a small sample before full load:
         Pick 3-5 Parquet files from matches/ (earliest, middle, latest
         by filename date) and 3-5 CSV files from ratings/ (same spread).
         Ingest into temporary tables:
           CREATE TEMP TABLE smoke_matches_raw AS SELECT * FROM read_parquet(
             ['raw/matches/match-2020-08-01.parquet', ...],
             filename=true, binary_as_string=true)
           CREATE TEMP TABLE smoke_ratings_raw AS SELECT * FROM read_csv_auto(
             ['raw/ratings/rating-2020-08-01.csv', ...],
             filename=true)
         Verify: DESCRIBE output — confirm binary columns are VARCHAR
         (not BLOB), confirm CSV-inferred types are reasonable (profile_id
         numeric, date parsed, etc.), row counts > 0, column counts match
         01_01_02 (+1 for filename). Cross-check column schemas across
         smoke-test files to assess cross-file consistency. If smoke test
         passes, drop temp tables and proceed to full ingestion.
      3. FULL INGESTION — matches/:
         CREATE TABLE matches_raw AS SELECT * FROM read_parquet(
           'raw/matches/*.parquet', filename=true, binary_as_string=true)
         NOTE: binary_as_string=true is applied based on step 1's pyarrow
         inspection results. DuckDB 1.5.1 defaults binary_as_string=false
         — without the explicit flag, unannotated BYTE_ARRAY columns
         become BLOB and string comparisons silently return 0 rows.
      4. FULL INGESTION — ratings/:
         CREATE TABLE ratings_raw AS SELECT * FROM read_csv_auto(
           'raw/ratings/*.csv', filename=true)
         NOTE: 01_01_02 shows ALL 7 columns as pandas `object` — types are
         unresolved. The post-ingestion type check (step 6c) is a GATE:
         if read_csv_auto infers wrong types, the executor must re-ingest
         with explicit types= parameter.
      5. Ingest singletons:
         CREATE TABLE leaderboards_raw AS SELECT * FROM read_parquet(
           'raw/leaderboards/leaderboard.parquet', binary_as_string=true,
           filename=true)
         CREATE TABLE profiles_raw AS SELECT * FROM read_parquet(
           'raw/profiles/profile.parquet', binary_as_string=true,
           filename=true)
         NOTE: singletons also include filename=true for provenance
         consistency — every raw-layer table carries a filename column.
      6. Post-ingestion verification:
         a. Row counts: SELECT COUNT(*) per table — report total rows and
            file-to-row ratio (01_01_01 has file counts but not row counts)
         b. Column counts: verify column count per table matches 01_01_02
            schema discovery (matches_raw: 54+1 filename, ratings_raw: 7+1
            filename, leaderboards_raw: 18+1 filename, profiles_raw: 13+1
            filename). A mismatch means silent column drop during ingestion.
         c. DESCRIBE ALL 4 tables: record full DuckDB-assigned types.
            For ratings_raw specifically: GATE — verify:
              profile_id → INTEGER or BIGINT (not VARCHAR)
              date → DATE or TIMESTAMP (not VARCHAR)
              games, rating, rating_diff → INTEGER (not VARCHAR)
              season → INTEGER or VARCHAR (both acceptable)
            If any expected-numeric column is VARCHAR, re-ingest with
            explicit types= parameter. If date is VARCHAR, add
            dateformat= parameter.
         d. NULL count for `won` column in matches_raw: report as structural fact
            (column `won`, type bool, N rows NULL). Do NOT interpret semantically
            — just record the count for downstream steps.
         e. Document matches/ratings file count gap: 2,073 match files vs
            2,072 rating files per 01_01_01. Identify which date has matches
            but no ratings. Report in artifact (analogous to aoestats
            missing-week documentation).
      7. Report: tables created, full DESCRIBE output per table, DDL,
         row counts per table, file-to-row ratios, column counts,
         matches/ratings date gap, won NULL count

  - id: aoestats
    game: aoe2
    complexity: "medium — Parquet with variant columns"
    notebook: sandbox/aoe2/aoestats/01_exploration/01_eda/01_02_01_duckdb_ingestion.py
    artifacts_dir: src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_eda/
    research_log: src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
    step_status: src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml
    db_path: src/rts_predict/games/aoe2/datasets/aoestats/data/db/db.duckdb
    raw_dir: src/rts_predict/games/aoe2/datasets/aoestats/data/raw/
    prior_artifacts:
      - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json
      - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json
    step_scope: "content"
    method: |
      1. PRE-INGESTION VARIANT CENSUS:
         Run pyarrow.parquet.read_schema on ALL 172 matches + 171 players
         files. For each of the 7 variant columns identified by 01_01_02,
         record the type distribution across files (e.g., how many files
         have int64 vs double, how many have null-typed columns). This
         census is the authoritative source for variant column patterns —
         its results determine the ingestion strategy and provide the
         baseline for post-ingestion NULL verification.
         DuckDB documentation indicates union_by_name auto-handles:
           int64 ↔ double → DOUBLE (numeric promotion)
           timestamp[us] ↔ timestamp[ns] → TIMESTAMP_NS (precision promotion)
           double ↔ null → DOUBLE (NULL fill)
           string ↔ null → VARCHAR (NULL fill)
         The smoke test (step 2) will confirm these behaviors empirically.
         No types= parameter exists in read_parquet. No CAST workarounds
         should be needed if auto-promotion works as documented.
         NOTE on profile_id: if promoted to DOUBLE from mixed int64/double,
         player IDs as float64 may cause join precision issues for IDs
         > 2^53. Flag for EDA investigation — do not alter at bronze layer.
      2. SMOKE TEST — ingest a small sample before full load:
         Pick 3-5 files from each subdirectory (earliest, middle, latest
         by filename date). Ingest into temporary tables:
           CREATE TEMP TABLE smoke_matches_raw AS SELECT * FROM read_parquet(
             ['raw/matches/file1.parquet', ...],
             union_by_name=true, filename=true)
           CREATE TEMP TABLE smoke_players_raw AS SELECT * FROM read_parquet(
             ['raw/players/file1.parquet', ...],
             union_by_name=true, filename=true)
         Verify: DESCRIBE output — variant columns have correct promoted
         types (raw_match_type: DOUBLE, started_timestamp: TIMESTAMP,
         profile_id: DOUBLE, opening: VARCHAR, age uptimes: DOUBLE),
         duration/irl_duration are INTERVAL, row counts > 0, column counts
         correct (matches_raw: 17+1 filename=18, players_raw: 13+1=14), no parse
         errors. If smoke test passes, drop temp tables and proceed.
         NOTE on duration columns: `duration` and `irl_duration` are Arrow
         `duration[ns]`. DuckDB maps these to INTERVAL type (truncates
         nanoseconds to microseconds — acceptable for game durations).
         Verify typeof(duration) = 'INTERVAL' during smoke test.
      3. FULL INGESTION — matches/:
         CREATE TABLE matches_raw AS SELECT * FROM read_parquet(
           'raw/matches/*.parquet',
           union_by_name=true, filename=true)
      4. FULL INGESTION — players/:
         CREATE TABLE players_raw AS SELECT * FROM read_parquet(
           'raw/players/*.parquet',
           union_by_name=true, filename=true)
      5. Ingest overview/:
         CREATE TABLE overviews_raw AS SELECT * FROM read_json_auto(
           'raw/overview/overview.json')
         This produces an 8-column table (one per root key). The
         list-valued columns become DuckDB JSON arrays. Normalizing into
         separate lookup tables is deferred to EDA. Document the decision
         and record DESCRIBE output.
      6. Document missing-week asymmetry:
         171 players files vs 172 matches files — investigate which week(s)
         of matches have no player-level data. Verify after ingestion:
         matches from gap week(s) should have no corresponding player rows
         in any future join. Record the gap in the artifact.
      7. Verify:
         a. For each variant column: SELECT COUNT(*) FILTER (WHERE col
            IS NULL) — NULL counts should correspond to files with
            null-typed columns (from census) or absent columns (from
            union_by_name)
         b. Row count + column count verification (matches_raw: 17+1 filename
            = 18, players_raw: 13+1 = 14 per 01_01_02). DESCRIBE ALL 3 tables
            (including overviews_raw) — record full DuckDB-assigned types in
            the artifact.
         c. Confirm duration/irl_duration → INTERVAL, test
            EXTRACT(EPOCH FROM duration) produces reasonable values.
      8. Report: tables created, full DESCRIBE output per table (all 3),
         DDL, row counts, column counts, variant column type census
         results (full pyarrow census on all source files), DuckDB
         auto-promotion types documented, NULL counts per variant column
         matched to file census, duration/irl_duration type confirmation,
         profile_id precision flag, missing-week documentation
```

**Instructions (per dataset):**
1. Create artifact directory if needed:
   `mkdir -p <artifacts_dir>`
2. Create the notebook (jupytext-paired `.py`) at the dataset's path.
   Create the `01_eda/` subdirectory under the sandbox path if needed.
3. For datasets that write to DuckDB (aoe2companion, aoestats): the
   notebook needs write access. Use `duckdb.connect(str(db_path))` or
   `get_notebook_db(game, dataset, read_only=False)`. sc2egset
   investigation may use a temporary in-memory DB for sample tests.
3a. Smoke test and pre-ingestion functions (pyarrow census, binary column
   inspection) go in `src/rts_predict/games/<game>/datasets/<dataset>/pre_ingestion.py`.
   The notebook imports from `pre_ingestion`, NOT from `ingestion.py`
   (which is from prior experiments with obsolete naming). Use `_raw`
   suffix table naming convention for all raw-layer tables.
4. Execute the dataset-specific method described above.
4. Run fresh-kernel execution (if feasible within timeout):
   `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 <notebook>.ipynb`
   For sc2egset: if full ingestion exceeds timeout, run the ingestion
   function interactively and capture results in the notebook.
5. Sync jupytext:
   `source .venv/bin/activate && poetry run jupytext --sync <notebook>.ipynb`
6. Write JSON artifact with: tables created, full DESCRIBE output per table,
   DDL, row counts, errors, dataset-specific details (mapping file census
   for sc2egset, variant transition table for aoestats, ratings type
   inference for aoe2companion).
7. Write Markdown artifact with: summary, DESCRIBE output, DDL, row count table.
8. Write research log entry per template:
   - Set `step_scope: content`
   - Report: tables created, row counts, ingestion strategy
   - Per Invariant #9: conclusions limited to what ingestion produced
     (tables, counts, errors). No value distributions or semantic analysis.
9. Update STEP_STATUS.yaml to mark 01_02_01 as complete.

**After all 3 complete:**
10. Write CROSS entry in `reports/research_log.md`:
    - Ingestion complexity comparison (hard/easy/medium)
    - Tables created per dataset
    - Row counts per dataset
    - Cross-dataset timestamp precision: aoe2companion uses timestamp[ms],
      aoestats uses timestamp[us] — document this asymmetry as a structural
      fact for downstream join awareness
    - No semantic comparison of data content

**Verification (per dataset):**
- DuckDB file exists at `data/db/db.duckdb`
- Artifacts exist at `artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.{json,md}`
- `.ipynb` / `.py` pair synced
- Research log entry has `step_scope: content`
- STEP_STATUS.yaml updated
- DuckDB tables have non-zero row counts

**File scope:**
- 3 notebooks (`.ipynb` + `.py` each)
- 3 artifact directories (JSON + MD each)
- 3 DuckDB files (created/populated)
- 3 research logs
- 3 STEP_STATUS.yaml
- `reports/research_log.md` (CROSS entry)

**Read scope:**
- `.claude/scientific-invariants.md`
- `docs/templates/research_log_entry_template.yaml`
- Each dataset's prior artifacts (01_01_01 + 01_01_02)

---

## File Manifest

| File | Action | Task |
|------|--------|------|
| `src/.../sc2egset/reports/ROADMAP.md` | Add 01_02_01 step def | T01 |
| `src/.../aoe2companion/reports/ROADMAP.md` | Add 01_02_01 step def | T01 |
| `src/.../aoestats/reports/ROADMAP.md` | Add 01_02_01 step def | T01 |
| `src/.../sc2egset/pre_ingestion.py` | Create | T02 |
| `src/.../aoe2companion/pre_ingestion.py` | Create | T02 |
| `src/.../aoestats/pre_ingestion.py` | Create | T02 |
| `sandbox/.../sc2egset/01_eda/01_02_01_duckdb_ingestion.{ipynb,py}` | Create + execute | T02 |
| `sandbox/.../aoe2companion/01_eda/01_02_01_duckdb_ingestion.{ipynb,py}` | Create + execute | T02 |
| `sandbox/.../aoestats/01_eda/01_02_01_duckdb_ingestion.{ipynb,py}` | Create + execute | T02 |
| `src/.../sc2egset/reports/artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.{json,md}` | Generate | T02 |
| `src/.../aoe2companion/reports/artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.{json,md}` | Generate | T02 |
| `src/.../aoestats/reports/artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.{json,md}` | Generate | T02 |
| `src/.../sc2egset/data/db/db.duckdb` | Create + populate | T02 |
| `src/.../aoe2companion/data/db/db.duckdb` | Create + populate | T02 |
| `src/.../aoestats/data/db/db.duckdb` | Create + populate | T02 |
| `src/.../sc2egset/reports/research_log.md` | Add entry | T02 |
| `src/.../aoe2companion/reports/research_log.md` | Add entry | T02 |
| `src/.../aoestats/reports/research_log.md` | Add entry | T02 |
| `src/.../sc2egset/reports/STEP_STATUS.yaml` | Mark complete | T02 |
| `src/.../aoe2companion/reports/STEP_STATUS.yaml` | Mark complete | T02 |
| `src/.../aoestats/reports/STEP_STATUS.yaml` | Mark complete | T02 |
| `reports/research_log.md` | Add CROSS entry | T02 |

## Gate Condition

- 3 ROADMAPs have 01_02_01 step definitions
- 3 `pre_ingestion.py` modules created with smoke test and inspection functions
- 3 notebooks executed without error
- 6 artifact files exist (JSON + MD per dataset)
- aoe2companion + aoestats DuckDB files exist with non-zero row counts
- aoe2companion artifact includes full DESCRIBE output for all 4 tables
- aoe2companion ratings_raw types validated (profile_id, date, rating not VARCHAR)
- aoe2companion matches/ratings file count gap documented
- sc2egset design artifact documents read_json_auto behavior (no DuckDB tables)
- sc2egset design artifact includes full census of all 70 map_foreign_to_english_mapping.json files
- `.ipynb` / `.py` pairs synced
- 3 research log entries with `step_scope: content`
- 3 STEP_STATUS.yaml show 01_02_01 complete
- CROSS entry is structural only (includes timestamp precision asymmetry)
- sc2egset design artifact proposes table split strategy
- aoestats variant columns have expected auto-promoted types (raw_match_type: DOUBLE, started_timestamp: TIMESTAMP, profile_id: DOUBLE, opening: VARCHAR, age uptimes: DOUBLE)
- aoestats variant column census in notebook documents type distribution for all 7 variant columns with per-file counts
- aoestats NULL counts for presence/absence columns match file census
- aoestats DESCRIBE for ALL 3 tables (including overviews_raw) confirms duration/irl_duration → INTERVAL
- aoestats profile_id precision flag documented in artifact
- Smoke tests passed for both aoe2companion and aoestats before full ingestion
- Full test suite passes: `pytest tests/ -v --cov`

## Design Decisions

1. **Same step number (01_02_01), different scope.** aoe2companion and
   aoestats do full DuckDB ingestion. sc2egset does investigation only
   (test read_json_auto on samples, produce design artifact). Full
   sc2egset ingestion is a follow-up step informed by these findings.

2. **01_02, not 01_01.** Ingestion is the first step of EDA (01_02),
   not part of acquisition (01_01). Acquisition established what exists
   and what it looks like. EDA begins with making the data queryable.
   This is a classification judgment — ingestion falls between "source
   inventory" and "Tukey-style EDA" — but the Manual §1 scope ends
   at "schema information" and this step goes beyond that.

3. **Clean slate — databases deleted.** All three DuckDB database files
   were deleted prior to this step. DuckDB creates a fresh database on
   first `duckdb.connect()`. No table enumeration or DROP logic needed.

4. **sc2egset: investigate first, ingest later.** The JSON structure
   is too complex to commit to a loading strategy without testing
   read_json_auto behavior. This step tests on samples and produces a
   design artifact. Full ingestion is a separate follow-up step.

5. **aoestats: variant columns expected to be handled by DuckDB
   auto-promotion.** 01_01_02 identified 7 variant columns with type
   inconsistencies. DuckDB 1.5.1 documentation indicates
   `union_by_name=true` auto-promotes numeric types and fills NULLs for
   absent columns. The notebook's pre-ingestion census will determine the
   specific type patterns, and the smoke test will confirm DuckDB handles
   them correctly. No `types=` parameter exists in `read_parquet`. The
   bronze layer preserves DuckDB's auto-promoted types. If `profile_id`
   is promoted to DOUBLE from mixed sources, flag for EDA investigation
   — join precision risk for IDs > 2^53.

5a. **Smoke test before full ingestion.** Both aoe2companion and aoestats
   run a small-sample ingestion (3-5 files spanning the date range) into
   temporary tables before committing to the full glob. The smoke test
   validates: DESCRIBE output matches expectations (binary→VARCHAR for
   aoe2companion, variant columns auto-promoted to correct types for
   aoestats, duration→INTERVAL), column counts match 01_01_02 (+1 for
   filename), row counts > 0, no parse errors. Full ingestion proceeds
   only after smoke test passes.

5b. **aoe2companion: binary_as_string=true expected to be needed.**
   01_01_02 identified binary-typed columns across all subdirectories.
   Column names suggest text content, indicating a possible legacy Parquet
   writer that failed to set STRING/UTF8 annotations. The notebook will
   run pyarrow logical-type inspection to confirm they are unannotated
   BYTE_ARRAY before applying binary_as_string=true. DuckDB 1.5.1
   defaults binary_as_string=false — if unannotated, the explicit flag
   is required.

6. **2 consolidated specs.** T01 (ROADMAPs, haiku) and T02 (notebooks +
   docs, sonnet). No intermediate review gate.

7. **sc2egset timeout strategy.** If full ingestion exceeds 600s,
   implement as a callable function that logs progress to a file
   referenced from the notebook. The log file is committed as an
   auxiliary artifact for Invariant #6 compliance.

8. **step_scope: content.** This step reads and parses raw file content
   (209 GiB of JSON for sc2egset). The scope designation is `content`,
   not `query`, because the primary activity is loading raw files.

9. **filename column on every raw table.** Every raw-layer DuckDB table
   includes a `filename` column from `read_parquet(filename=true)` or
   equivalent — including singletons (leaderboards_raw, profiles_raw).
   Removing this column in any downstream view is forbidden. This enables
   provenance tracking back to source files.

10. **Raw-layer table naming: `<entity>_raw` suffix.** All DuckDB tables
   created at the bronze layer use `_raw` suffix (e.g., `matches_raw`,
   `players_raw`, `replays_raw`). This distinguishes raw tables from
   future cleaned/derived tables. Existing `ingestion.py` modules
   (aoe2companion, aoestats) and `aoe2companion/types.py` use the
   obsolete `raw_<entity>` prefix convention from prior experiments —
   they will be reconciled when full ingestion is implemented.

11. **Pre-ingestion functions in `pre_ingestion.py`.** Step 01_02_01
   performs smoke tests and schema inspection, not full ingestion.
   Reusable functions (pyarrow census, binary column inspection, smoke
   test helpers) go in `datasets/<dataset>/pre_ingestion.py`. The
   notebook imports from this module. The existing `ingestion.py`
   modules are not used in this step.

---

## Suggested Execution Graph

```yaml
dag_id: "dag_duckdb_ingestion"
plan_ref: "planning/current_plan.md"
category: "A"
branch: "feat/phase01-duckdb-ingestion"
base_ref: "master"
default_isolation: "shared_branch"
phase_ref: "01"
pipeline_section_ref: "01_02"
step_refs:
  - "01_02_01"

jobs:
  - job_id: "J01"
    name: "01_02_01 — DuckDB ingestion, all datasets"
    task_groups:
      - group_id: "TG01"
        name: "ROADMAP step definitions"
        depends_on: []
        tasks:
          - task_id: "T01"
            name: "Add 01_02_01 step defs to all 3 ROADMAPs"
            spec_file: "planning/specs/spec_01_roadmaps.md"
            agent: "executor"
            model: "haiku"
            parallel_safe: false
            file_scope:
              - "src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md"
              - "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md"
              - "src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md"
            read_scope:
              - "docs/templates/step_template.yaml"
            depends_on: []

      - group_id: "TG02"
        name: "Notebooks + ingestion + docs"
        depends_on: ["TG01"]
        tasks:
          - task_id: "T02"
            name: "DuckDB ingestion for all 3 datasets (parameterized)"
            spec_file: "planning/specs/spec_02_ingestion.md"
            agent: "executor"
            model: "sonnet"
            parallel_safe: false
            file_scope:
              - "sandbox/sc2/sc2egset/01_exploration/01_eda/"
              - "sandbox/aoe2/aoe2companion/01_exploration/01_eda/"
              - "sandbox/aoe2/aoestats/01_exploration/01_eda/"
              - "src/rts_predict/games/sc2/datasets/sc2egset/pre_ingestion.py"
              - "src/rts_predict/games/sc2/datasets/sc2egset/reports/"
              - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/"
              - "src/rts_predict/games/aoe2/datasets/aoe2companion/pre_ingestion.py"
              - "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/"
              - "src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/"
              - "src/rts_predict/games/aoe2/datasets/aoestats/pre_ingestion.py"
              - "src/rts_predict/games/aoe2/datasets/aoestats/reports/"
              - "src/rts_predict/games/aoe2/datasets/aoestats/data/db/"
              - "reports/research_log.md"
            read_scope:
              - ".claude/scientific-invariants.md"
              - "docs/templates/research_log_entry_template.yaml"
              - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
              - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
              - "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
              - "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
              - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
              - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
            depends_on: []

final_review:
  agent: "reviewer-adversarial"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```

## Dependency Graph

```
TG01: T01 (3 ROADMAPs — haiku)
  |
TG02: T02 (3 notebooks + DuckDB + artifacts + research logs + CROSS — sonnet)
```
