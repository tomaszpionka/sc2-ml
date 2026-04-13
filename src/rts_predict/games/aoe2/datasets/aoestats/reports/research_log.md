# Research Log — AoE2 / aoestats

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoestats findings. Reverse chronological.

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Ingested all three raw data sources into DuckDB (`matches_raw`, `players_raw`,
`overviews_raw`) and validated types, null rates, and variant column behaviour
against 01_01_02 schema discovery findings.

### Why

Materialise the bronze layer. This dataset has known variant columns
(type changes across weekly Parquet files) requiring `union_by_name=true`.
Invariant #7 (type fidelity) — verify DuckDB's automatic type promotion.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

- `matches_raw`: 30.7M rows, 18 columns. Two variant columns: `started_timestamp` (mixed us/ns precision across files, promoted to TIMESTAMP WITH TIME ZONE), `raw_match_type` (mixed int64/double, promoted to DOUBLE)
- `players_raw`: 107.6M rows, 14 columns. Five variant columns: `feudal_age_uptime`, `castle_age_uptime`, `imperial_age_uptime` (double in 82/81/81 files, null-typed in 89/90/90 files — promoted to DOUBLE with NULL fill); `profile_id` (int64 in 135 files, double in 36 files — promoted to DOUBLE); `opening` (string in 82 files, null-typed in 89 — promoted to VARCHAR)
- `overviews_raw`: 1 row, 9 columns. Contains STRUCT arrays for civs, openings, patches, groupings, changelog
- `duration` and `irl_duration` mapped from Arrow duration[ns] to BIGINT nanoseconds (not INTERVAL as might be expected)
- `profile_id` as DOUBLE: precision loss risk for IDs > 2^53, but only 1,185 NULLs out of 107.6M rows
- Missing week: `2025-11-16_2025-11-22` has matches but no player-level data (1 week gap out of 172)

### Decisions taken

- Raw layer uses `SELECT *` with `union_by_name=true, filename=true` — let DuckDB handle type promotion at bronze layer
- `profile_id` DOUBLE type flagged but not altered — precision check deferred to cleaning step
- Duration stored as BIGINT nanoseconds — will need division by 1e9 for seconds in queries

### Decisions deferred

- `profile_id` DOUBLE→BIGINT cast: need to verify no precision loss for actual ID values in the dataset
- Whether the 89 null-typed `opening` files represent a schema change or genuinely absent data
- Whether `feudal_age_uptime` NULLs (87% of rows) indicate games not reaching Feudal Age or missing data

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, variant column handling
- Chapter 4, §4.2.1 — Ingestion validation, DuckDB type promotion behaviour

### Open questions / follow-ups

- Is `profile_id` precision loss actually occurring for any real IDs in this dataset?
- What caused the schema break in player files around week 89/172 (~mid-2024)?
- Are the age uptime NULLs meaningful (game ended before that age) or data quality issues?

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md`

### What

Full census of all 344 Parquet files plus the singleton overview JSON.
Catalogued column names, physical types, nullability, and critically —
variant columns where physical type changes across weekly files.

### Why

Map the exact schema per file, identifying type inconsistencies that will
affect DuckDB ingestion. Invariant #6 requires knowing field types.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- Matches: 17 columns, 2 variant columns (`started_timestamp` mixed us/ns precision, `raw_match_type` mixed int64/double)
- Players: 13 columns, 5 variant columns (`feudal_age_uptime`, `castle_age_uptime`, `imperial_age_uptime` appear as double or null-typed; `profile_id` appears as int64 or double; `opening` appears as string or null-typed)
- Overview: singleton JSON with nested STRUCT arrays (civs, openings, patches, groupings, changelog)
- `duration` and `irl_duration` are Arrow duration[ns] type (not timestamp)

### Decisions taken

- Full census used (344 files is manageable)
- Variant columns documented with exact file counts per type — critical input for ingestion

### Decisions deferred

- How to handle variant columns at ingestion — deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset schema, variant column documentation

### Open questions / follow-ups

- Why do player files switch from having `opening`/age uptimes to not having them mid-dataset?
- Is the `profile_id` int64→double transition a data source version change?

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the aoestats raw data directory: 3 subdirectories (matches, players,
overview), file counts, sizes, extensions, and temporal coverage via filename
date range parsing.

### Why

Establish the data landscape. Invariant #9 — filesystem-level inventory before
content inspection.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- 349 total files across 3 subdirectories, 3.7 GB total
- Matches: 172 weekly Parquet files (611 MB), 2022-08-28 to 2026-02-07
- Players: 171 weekly Parquet files (3.2 GB), aligned with matches minus 1 week
- Overview: 1 singleton JSON (22 KB)
- 3 temporal gaps identified: 43-day gap at 2024-07-20→2024-09-01, plus two 8-day gaps
- File count mismatch: 172 match weeks vs 171 player weeks (1 week has matches but no players)

### Decisions taken

- Weekly granularity confirmed — files named by date range (e.g., `2022-08-28_2022-09-03`)
- Temporal gaps documented for downstream awareness

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, temporal coverage, data gaps

### Open questions / follow-ups

- Is the 43-day gap (July–September 2024) a data collection outage or intentional?
