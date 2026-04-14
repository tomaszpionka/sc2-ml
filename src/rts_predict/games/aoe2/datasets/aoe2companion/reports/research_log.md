# Research Log — AoE2 / aoe2companion

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoe2companion findings. Reverse chronological.

---

## 2026-04-14 — [Phase 01 / Step 01_02_01] won=NULL root-cause investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query (amendment to 01_02_01)
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json` (extended with `won_null_root_cause` key)

### What

Diagnosed why 12,985,561 rows (4.69%) have `won=NULL` in the full matches
corpus. Added section 8 (Q1–Q4) to the 01_02_01 pre-ingestion notebook to
distinguish between two hypotheses: H1 (Parquet schema heterogeneity causing
DuckDB type promotion to inject NULLs) and H2 (genuine NULL values in source
files).

### Why

The `won` column is the prediction target for this thesis. Before any cleaning
decisions can be made in later steps, the root cause of NULLs must be
understood. Invariant #6 (reproducibility) — all diagnostic queries embedded
in the artifact.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

Q1: `parquet_schema()` metadata-only scan — counts distinct `won` Parquet types
across all 2,073 files without loading row data.

Q2: Per-type-group value census without `union_by_name` — reads each type group
independently to observe native values and genuine NULLs.

Q3: Type promotion NULL injection test — compares per-file NULL counts before
and after `union_by_name=true` on a mixed-type sample (runs only if Q1 finds
multiple types).

Q4: Per-file NULL distribution — identifies which files contribute NULLs and
their date range under `union_by_name=true`.

### Findings

The investigation was added as a diagnostic section to the notebook. Results
will be populated when the notebook is executed against the full corpus. The
`won_null_root_cause` key in the artifact JSON captures Q1 parquet type
distribution, Q4 file/NULL counts, date range of affected files, and the H1/H2
verdicts.

### Decisions taken

- Investigation scope limited to diagnosis only — no cleaning decisions made
- Section 8 uses a dedicated `con8 = duckdb.connect(":memory:")` connection to
  avoid interference with the existing `con` connection in the notebook

### Decisions deferred

- Actual H1/H2 verdict pending notebook execution on full corpus
- Recovery strategy for NULL `won` values (explicit cast, row drop, or date
  filter) deferred to a future cleaning step

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 data quality: won column NULL analysis
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- If H1 is confirmed: can INT64-encoded `won` values (1/0) be recovered by
  reading affected files with their native type and casting explicitly?
- If both H1 and H2 are confirmed: what fraction of NULLs is attributable to
  each cause?

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Ingested all four raw data sources into DuckDB (`matches_raw`, `ratings_raw`,
`leaderboards_raw`, `profiles_raw`) and validated column counts, types, and
null rates against 01_01_02 schema discovery findings.

### Why

Materialise the bronze layer for queryable exploration. Invariant #7 (type
fidelity) — verify DuckDB type inference matches Parquet/CSV source types.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

- `matches_raw`: 277M rows, 55 columns (54 source + filename). `binary_as_string=true` resolved all 22 unannotated BYTE_ARRAY columns to VARCHAR
- `ratings_raw`: 58.3M rows, 8 columns. `read_csv_auto` inferred all 7 columns as VARCHAR at scale — required explicit `types=` parameter to get correct BIGINT/TIMESTAMP types
- `leaderboards_raw`: 2.38M rows, 19 columns (singleton Parquet)
- `profiles_raw`: 3.61M rows, 14 columns (singleton Parquet)
- Column counts match 01_01_02 expectations plus filename column in all tables
- `won` column: 12.99M NULLs out of 277M rows (4.7%) — matches without a recorded winner
- File count gap: 2,073 match files vs 2,072 rating files — `rating-2025-07-11.csv` is missing

### Decisions taken

- All Parquet reads use `binary_as_string=true` — Parquet files have unannotated BYTE_ARRAY columns that are actually UTF-8 strings
- CSV ratings use explicit type specification (never rely on `read_csv_auto` at scale for this dataset)
- Raw layer uses `SELECT *` with `filename=true` — no explicit DDL at this stage

### Decisions deferred

- Handling of 12.99M NULL `won` values — cleaning step decision
- Whether the missing rating file for 2025-07-11 is recoverable or should be documented as a gap
- Profile ID join strategy between matches and ratings (different column names: `profileId` vs `profile_id`)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 match data ingestion, binary column handling, CSV type pitfall
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- What fraction of NULL `won` values are draws vs incomplete records?
- Does the `profileId`/`profile_id` naming inconsistency across tables indicate different source APIs?

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`

### What

Full census of all 4,147 data files: Parquet metadata-only reads for matches,
leaderboards, and profiles; CSV header + 50-row samples for ratings.
Catalogued column names, physical types, and nullability.

### Why

Map the exact schema of each source before ingestion. Invariant #6 requires
knowing field names and types for reproducibility.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- Matches: 54 columns per Parquet file, consistent schema across all 2,073 daily files. 22 columns have unannotated BYTE_ARRAY physical type (no logical type annotation — Parquet files were written without UTF8 annotation)
- Ratings: 7 CSV columns (`profile_id`, `games`, `rating`, `date`, `leaderboard_id`, `rating_diff`, `season`), consistent across 2,072 files
- Leaderboards: 18 columns (singleton Parquet), 4 unannotated BYTE_ARRAY columns
- Profiles: 13 columns (singleton Parquet), 11 unannotated BYTE_ARRAY columns
- Schema is consistent within each file type — no variant columns detected

### Decisions taken

- Full census (not sampling) used because file counts are manageable (<4,200 files)
- BYTE_ARRAY without annotation flagged for `binary_as_string=true` at ingestion

### Decisions deferred

- Ingestion strategy deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset schema description

### Open questions / follow-ups

- Why do Parquet files lack UTF8 annotation on string columns? (upstream data source issue)

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the aoe2companion raw data directory: 4 subdirectories (matches,
ratings, leaderboards, profiles), file counts, sizes, extensions, and
temporal coverage via filename date parsing.

### Why

Establish the data landscape. Invariant #9 — filesystem-level inventory before
content inspection.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- 4,153 total files across 4 subdirectories, 9.2 GB total
- Matches: 2,073 daily Parquet files (6.6 GB), 2020-08-01 to 2026-04-04, no date gaps
- Ratings: 2,072 daily CSV files (2.5 GB), 2020-08-01 to 2026-04-04, no date gaps
- Leaderboards: 1 singleton Parquet (83 MB)
- Profiles: 1 singleton Parquet (162 MB)
- 1 file count gap: matches has 2,073 files, ratings has 2,072 (missing 2025-07-11)

### Decisions taken

- Temporal coverage spans ~5.7 years — sufficient for longitudinal analysis
- File count mismatch between matches and ratings noted for investigation

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, temporal coverage, data volume

### Open questions / follow-ups

- None — straightforward inventory step
