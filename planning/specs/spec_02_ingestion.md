---
task_id: "T02"
task_name: "DuckDB ingestion for all 3 datasets (parameterized)"
agent: "executor"
model: "opus"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
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
datasets:
  - id: sc2egset
    game: sc2
    complexity: "investigation only — test read_json_auto, no full ingestion"
  - id: aoe2companion
    game: aoe2
    complexity: "easy — flat Parquet + CSV glob"
  - id: aoestats
    game: aoe2
    complexity: "medium — Parquet with variant columns"
category: "A"
---

# Spec: DuckDB ingestion for all 3 datasets

## Objective

Create and execute 3 ingestion notebooks, produce artifacts, write
research log entries, update STEP_STATUS, and write a CROSS entry.
Parameterized task — different complexity per dataset, same output
structure.

## Instructions

### Per-dataset parameters

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
    step_scope: "query"

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
    step_scope: "query"

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
    step_scope: "query"
```

### Per-dataset method

#### sc2egset — investigation only

1. Select 5-10 sample `.SC2Replay.json` files spanning the per-file-size
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

#### aoe2companion — full ingestion

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
   d. NULL count for `won` column in matches_raw: report as structural
      fact (column `won`, type bool, N rows NULL). Do NOT interpret
      semantically — just record the count for downstream steps.
   e. Document matches/ratings file count gap: 2,073 match files vs
      2,072 rating files per 01_01_01. Identify which date has matches
      but no ratings. Report in artifact (analogous to aoestats
      missing-week documentation).
7. Report: tables created, full DESCRIBE output per table, DDL,
   row counts per table, file-to-row ratios, column counts,
   matches/ratings date gap, won NULL count

#### aoestats — full ingestion with variant column census

1. PRE-INGESTION VARIANT CENSUS:
   Run pyarrow.parquet.read_schema on ALL 172 matches + 171 players
   files. For each of the 7 variant columns identified by 01_01_02,
   record the type distribution across files (e.g., how many files
   have int64 vs double, how many have null-typed columns). This
   census is the authoritative source for variant column patterns —
   its results determine the ingestion strategy and provide the
   baseline for post-ingestion NULL verification.
   Empirical testing on DuckDB 1.5.1 confirms union_by_name auto-
   handles:
     int64 ↔ double → DOUBLE (numeric promotion)
     timestamp[us] ↔ timestamp[ns] → TIMESTAMP_NS (precision promotion)
     double ↔ null → DOUBLE (NULL fill)
     string ↔ null → VARCHAR (NULL fill)
   The smoke test (step 2) will confirm these behaviors on this
   dataset's specific type combinations.
   No types= parameter exists in read_parquet. No CAST workarounds
   should be needed if auto-promotion works as expected.
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
   correct (matches_raw: 17+1 filename=18, players_raw: 13+1=14), no
   parse errors. If smoke test passes, drop temp tables and proceed.
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
     'raw/overview/overview.json', filename=true)
   This produces a table with one row and columns per root key. The
   list-valued columns become DuckDB JSON arrays. Normalizing into
   separate lookup tables is deferred to EDA. Document the decision
   and record DESCRIBE output. NOTE: filename=true included per
   Design Decision #9 — every raw table carries filename provenance.
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
      = 18, players_raw: 13+1 = 14 per 01_01_02). DESCRIBE ALL 3
      tables (including overviews_raw) — record full DuckDB-assigned
      types in the artifact.
   c. Confirm duration/irl_duration → INTERVAL, test
      EXTRACT(EPOCH FROM duration) produces reasonable values.
8. Report: tables created, full DESCRIBE output per table (all 3),
   DDL, row counts, column counts, variant column type census
   results (full pyarrow census on all source files), DuckDB
   auto-promotion types documented, NULL counts per variant column
   matched to file census, duration/irl_duration type confirmation,
   profile_id precision flag, missing-week documentation

### Common instructions (all datasets)

1. Create artifact directory if needed:
   `mkdir -p <artifacts_dir>`
2. Create the notebook (jupytext-paired `.py`) at the dataset's path.
   Create the `01_eda/` subdirectory under the sandbox path if needed.
3. For datasets that write to DuckDB (aoe2companion, aoestats): the
   notebook needs write access. Use `duckdb.connect(str(db_path))` or
   `get_notebook_db(game, dataset, read_only=False)`. sc2egset
   investigation may use a temporary in-memory DB for sample tests.
3a. Smoke test and pre-ingestion functions (pyarrow census, binary
   column inspection) go in
   `src/rts_predict/games/<game>/datasets/<dataset>/pre_ingestion.py`.
   The notebook imports from `pre_ingestion`, NOT from `ingestion.py`
   (which is from prior experiments with obsolete naming). Use `_raw`
   suffix table naming convention for all raw-layer tables.
4. Execute the dataset-specific method described above.
5. Run fresh-kernel execution (if feasible within timeout):
   `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 <notebook>.ipynb`
   For sc2egset: if full ingestion exceeds timeout, run the ingestion
   function interactively and capture results in the notebook.
6. Sync jupytext:
   `source .venv/bin/activate && poetry run jupytext --sync <notebook>.ipynb`
7. Write JSON artifact with: tables created, full DESCRIBE output per
   table, DDL, row counts, errors, dataset-specific details (mapping
   file census for sc2egset, variant transition table for aoestats,
   ratings type inference for aoe2companion).
8. Write Markdown artifact with: summary, DESCRIBE output, DDL, row
   count table.
9. Write research log entry per template:
   - Set `step_scope: query`
   - Report: tables created, row counts, ingestion strategy
   - Per Invariant #9: conclusions limited to what ingestion produced
     (tables, counts, errors). No value distributions or semantic
     analysis.
10. Update STEP_STATUS.yaml to mark 01_02_01 as complete.

### After all 3 complete

11. Write CROSS entry in `reports/research_log.md`:
    - Ingestion complexity comparison (hard/easy/medium)
    - Tables created per dataset
    - Row counts per dataset
    - Cross-dataset timestamp precision: aoe2companion uses
      timestamp[ms], aoestats uses timestamp[us] — document this
      asymmetry as a structural fact for downstream join awareness
    - No semantic comparison of data content

## Verification

Per dataset:
- DuckDB file exists at `data/db/db.duckdb` (aoe2companion, aoestats
  only — sc2egset uses in-memory DB, no file expected)
- Artifacts exist at
  `artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.{json,md}`
- `.ipynb` / `.py` pair synced
- Research log entry has `step_scope: query`
- STEP_STATUS.yaml updated
- DuckDB tables have non-zero row counts (aoe2companion, aoestats)

Gate conditions:
- aoe2companion: 4 tables exist, DESCRIBE recorded, ratings_raw types
  validated, file count gap documented, smoke test passed
- aoestats: 3 tables exist (including overviews_raw), DESCRIBE
  recorded for all 3, variant columns have expected promoted types,
  duration/irl_duration → INTERVAL, NULL counts match file census,
  smoke test passed
- sc2egset: design artifact documents read_json_auto behavior,
  proposed table split strategy, event array storage estimate, full
  census of 70 mapping files

Cross-cutting:
- CROSS entry in reports/research_log.md
- Full test suite passes: `source .venv/bin/activate && poetry run pytest tests/ -v --cov`

## Context

- Read `.claude/scientific-invariants.md` — invariants #6, #7, #9
  apply to this step.
- Read `docs/templates/research_log_entry_template.yaml` for research
  log entry format.
- Read each dataset's 01_01_01 and 01_01_02 artifacts for file counts,
  column counts, and schema details.
- Raw-layer table naming: `<entity>_raw` suffix (e.g., `matches_raw`).
  Existing `ingestion.py` modules use obsolete `raw_<entity>` prefix —
  do not use those modules.
- Every raw table carries `filename=true` for provenance — no
  exceptions, including singletons and overview.json.
- DuckDB version 1.5.1 (pinned as `^1.5.1` in `pyproject.toml`).
