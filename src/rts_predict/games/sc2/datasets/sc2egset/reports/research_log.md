# Research Log — SC2 / sc2egset

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

SC2 / sc2egset findings. Reverse chronological.

---

## 2026-04-13 — [Phase 01 / Step 01_02_02] DuckDB ingestion

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** ingest
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md`

### What

Materialised three `*_raw` DuckDB tables from the full 22,390-file sc2egset
corpus (209 GB raw JSON) into the persistent database at
`src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb`.

### Why

Enable SQL-based EDA for subsequent profiling (01_03) and cleaning (01_04).
All data now accessible via DuckDB queries without reading raw JSON files
on every access. Invariants #6 (reproducibility), #7 (provenance), #9 (step
scope), #10 (relative filenames) upheld.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`
Module: `src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py`

### Findings

**Table row counts:**
| Table | Rows |
|-------|------|
| replays_meta_raw | 22,390 |
| replay_players_raw | 44,817 |
| map_aliases_raw | 104,160 |

**NULL rates:**
- replays_meta_raw: zero NULLs across all 6 checked columns (details, header,
  initData, metadata, ToonPlayerDescMap, filename)
- replay_players_raw: zero NULLs across all 7 checked columns (toon_id,
  nickname, MMR, race, result, APM, filename)
- map_aliases_raw: zero NULLs across all 4 columns; 70 distinct tournaments

**ToonPlayerDescMap type:** Confirmed VARCHAR (JSON text blob), not STRUCT.

**Cross-table integrity:** `orphan_player_files = 0` in both directions
(every replay_players_raw file exists in replays_meta_raw, and vice versa).

**Player count per replay:** 22,379 replays have exactly 2 players (99.95%),
3 replays have 1 player, 2 have 4, 1 has 6, 3 have 8, and 2 have 9.
The non-2-player replays are likely team games, FFA, or incomplete
replays; flagged for investigation in 01_04 (cleaning).

**map_aliases_raw dedup profile:** 1,488 unique foreign names, 193 unique
English names, 70 unique tournaments, 104,160 total rows. As expected from
01_02_01 — all 70 tournament mapping files have identical 1,488-entry key
sets.

**filename column (Invariant I10):** All three tables store paths relative to
`raw_dir` (no leading `/`). Cross-table join on `filename` has zero orphans,
confirming the relative-path strategy is consistent across streams.

### Decisions taken

- Tables use `*_raw` suffix convention (bronze layer naming)
- `replays_meta_raw` loaded per-tournament (70 batch INSERT operations) to
  avoid OOM: a single CTAS over 22,390 files peaked at 22 GB RSS and triggered
  OS kills on a 36 GB machine. Per-tournament batching keeps peak RSS under
  5 GB.
- `_MAP_ALIASES_INSERT_QUERY` (SQL with `json_each`) replaced by pure Python
  `json.loads` + `executemany` for correctness and simplicity
- `_DEFAULT_MAX_OBJECT_SIZE` set to 160 MB (1.12x headroom over largest
  observed file at 143.1 MB)
- 14 single-player replays retained as-is; deferred to cleaning step

### Decisions deferred

- Event Parquet extraction (SSD-dependent, estimated 40-80 GB compressed).
  Section 5 of the notebook remains commented out.
- Data cleaning (NULL rates and anomalies documented, not acted on). Deferred
  to pipeline section 01_04.
- Identity resolution (toon_id stored as-is). Deferred to Phase 02.

### Thesis mapping

Chapter 4, Section 4.1.1 — SC2EGSet: three-stream ingestion design,
ToonPlayerDescMap normalisation, `*_raw` bronze-layer convention.

### Open questions

- What are the 14 single-player replays? Are they observers, disconnects,
  or parse failures? (Investigate in 01_04)
- The 15 NULL MMR values and 33 NULL APM/SQ/supplyCappedPercent values: are
  these missing from the original replay metadata or parser artefacts?

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Investigated how DuckDB's `read_json_auto` handles SC2EGSet replay JSON files.
Tested single-file and batch (union_by_name) ingestion, measured event array
storage costs, probed ToonPlayerDescMap behaviour, and assessed mapping file
structure.

### Why

Determine the ingestion strategy for 22,390 replay files before committing to
a table layout. Invariant #7 (type fidelity) and #9 (step scope) apply.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

- `read_json_auto` succeeds on all 7 sampled files (100% success rate), producing 11 root-level columns
- ToonPlayerDescMap is inferred as STRUCT with dynamic player-ID keys per file; with `union_by_name=true` it promotes to `MAP(VARCHAR, STRUCT(...))`
- Event arrays dominate file size: gameEvents ~327 GB, trackerEvents ~41 GB, messageEvents ~0.1 GB (total ~368 GB estimated across 22,390 files)
- Batch ingestion of 64 files from one tournament completed in 1.66 seconds within 24 GB memory limit
- Mean vs median storage estimates diverge significantly (right-skewed distribution) — median is the conservative estimate
- Mapping files (`map_foreign_to_english_mapping.json`): all 70 are flat `{str: str}` dicts with 1,488 entries each; cross-file consistency confirmed (all identical key sets)
- `read_json_auto` misinterprets mapping files as a single row with 1,488 columns — not suitable for direct DuckDB ingestion

### Decisions taken

- Three-stream split strategy: replay scalars (DuckDB), players normalised from ToonPlayerDescMap (DuckDB), events to zstd Parquet (not DuckDB)
- ToonPlayerDescMap stored as VARCHAR in `replays_meta` (text blob for provenance); normalised to per-player rows in `replay_players`
- Event Parquet extraction uses Python+PyArrow (not DuckDB) due to the heterogeneous STRUCT[] problem
- Every raw table includes `filename` column for provenance tracing

### Decisions deferred

- Whether mapping files need a DuckDB table at all — pending cross-tournament variation analysis and superset check (added to notebook section 7b)
- `profile_id` DOUBLE→BIGINT precision check deferred to aoestats investigation
- Filename uniqueness across tournaments — added as notebook section 1b, pending execution

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet dataset description, three-stream ingestion rationale
- Chapter 4, §4.2.1 — Ingestion and validation methodology

### Open questions / follow-ups

- Are replay filenames (MD5 hashes) unique across all 70 tournament directories? (section 1b)
- Do mapping files grow over time or are all 70 identical? (section 7b)
- What is the actual zstd compression ratio at scale? Smoke test showed 16.88x on one file.

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md`

### What

Examined internal structure of SC2EGSet JSON replay files and mapping files.
Catalogued root-level keys, enumerated full keypath tree, analysed event array
struct heterogeneity, and checked schema consistency across all 70 tournament
directories.

### Why

Understand the data shape before designing ingestion. Invariant #6
(reproducibility) requires knowing exact field names and types.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- 11 root-level keys per replay: ToonPlayerDescMap, details, gameEvents, gameEventsErr, header, initData, messageEvents, messageEventsErr, metadata, trackerEvents, trackerEvtsErr
- Schema consistent across all 70 directories (no era-dependent variation)
- 70 files checked for root schema, 210 for keypath enumeration
- Event arrays contain heterogeneous structs — gameEvents has 10+ distinct event types (CameraUpdate, SelectionDelta, Cmd, etc.), trackerEvents has 9+ (PlayerSetup, UnitBorn, PlayerStats, etc.)
- Nested sub-structures present within events (e.g., target positions, unit types)

### Decisions taken

- Systematic temporal stratification sampling: 1 file per directory for root schema, 3 per directory for keypaths
- Event array heterogeneity confirms that DuckDB's STRUCT[] union approach creates unusably wide schemas — separate extraction needed

### Decisions deferred

- Mapping file schema discovery added in this session (cell 5b) — pending notebook re-execution
- Ingestion strategy deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet schema description
- Appendix A — Full field catalog

### Open questions / follow-ups

- ToonPlayerDescMap field stability across eras (2016–2024)
- Exact sub-field types for metadata STRUCTs (details, header, initData, metadata)

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the SC2EGSet raw data directory: directory structure, file counts,
sizes, and extensions across all 70 tournament directories.

### Why

Establish the data landscape before any content inspection. Invariant #9
requires sequential step discipline.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- Two-level layout: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`
- 70 top-level tournament directories spanning 2016–2024
- 22,390 replay JSON files totalling 209 GB
- 431 metadata files (mapping files, summaries, processed mappings) at tournament root level
- All replay files have `.json` extension (no mixed formats)
- No directories missing `_data` subdirectory

### Decisions taken

- Layout confirmed as suitable for glob-based ingestion (`*/*_data/*.SC2Replay.json`)
- Tournament directory name serves as temporal/provenance key

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet dataset description, data volume

### Open questions / follow-ups

- None — straightforward inventory step
