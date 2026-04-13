# Research Log — SC2 / sc2egset

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

SC2 / sc2egset findings. Reverse chronological.

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
