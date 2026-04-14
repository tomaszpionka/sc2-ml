# Research Log — AoE2 / aoe2companion

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoe2companion findings. Reverse chronological.

---

## 2026-04-14 — [Phase 01 / Step 01_02_03] Raw schema DESCRIBE

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml`

### What

Captured the exact DuckDB column names and types for all four aoe2companion raw sources. Since step 01_02_02 had not yet been executed, no persistent DuckDB exists; the notebook uses in-memory DuckDB and reads source files directly with `LIMIT 0` to obtain schema without loading row data. Same read parameters as planned for 01_02_02 ingestion (`binary_as_string=true`, `union_by_name=true`, `filename=true` for Parquet; explicit `dtypes=` for CSV).

### Why

Establish the source-of-truth bronze-layer schema before full ingestion runs. The `data/db/schemas/raw/*.yaml` files are consumed by all downstream steps (feature engineering, cleaning, documentation). Invariant #6 — all DESCRIBE SQL embedded in artifact.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_03_raw_schema_describe.py`

- matches: `read_parquet(glob, binary_as_string=true, union_by_name=true, filename=true) LIMIT 0`
- ratings: `read_csv(glob, dtypes={profile_id: BIGINT, games: BIGINT, rating: BIGINT, date: TIMESTAMP, leaderboard_id: BIGINT, rating_diff: BIGINT, season: BIGINT}, union_by_name=true, filename=true) LIMIT 0`
- leaderboards, profiles: `read_parquet(singleton, binary_as_string=true, filename=true) LIMIT 0`

### Findings

| Source | Columns | Notable types |
|--------|---------|---------------|
| matches | 55 | `won` BOOLEAN (prediction target); `matchId`/`profileId` INTEGER; `started`/`finished` TIMESTAMP; `speedFactor` FLOAT |
| ratings | 8 | `profile_id` BIGINT; `date` TIMESTAMP; all numerics BIGINT |
| leaderboards | 19 | `profileId` INTEGER; `lastMatchTime`/`updatedAt` TIMESTAMP |
| profiles | 14 | `profileId` INTEGER; all string columns VARCHAR |

Key observations:
- `won` (BOOLEAN, nullable) confirmed as prediction target column
- Naming inconsistency cross-confirmed: `profileId` (camelCase, INTEGER) in matches and leaderboards vs `profile_id` (snake_case, BIGINT) in ratings — noted for Phase 02 join design
- `speedFactor` is FLOAT (only non-integer numeric in matches)
- All four schema YAMLs populated in `data/db/schemas/raw/`

### Decisions taken

- Schema YAMLs populated from this DESCRIBE output — source-of-truth for all downstream steps
- No ingestion or schema changes at this step — read-only

### Decisions deferred

- Column descriptions (`TODO: fill`) in `*.yaml` files — deferred to systematic profiling (01_03)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: bronze-layer schema catalog

### Open questions / follow-ups

- None — schema fully captured

---

## 2026-04-14 — [Phase 01 / Step 01_02_02] DuckDB ingestion

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** ingest
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md`

### What

Materialised four `*_raw` DuckDB tables from the full aoe2companion corpus (2,073 daily match Parquets, 2,072 daily rating CSVs, 1 leaderboard Parquet, 1 profile Parquet) into the persistent database at `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/db.duckdb`.

### Why

Enable SQL-based EDA for subsequent profiling (01_03) and cleaning (01_04). Invariants #6 (reproducibility), #9 (step scope), #10 (relative filenames) upheld.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`
Module: `src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py`

### Findings

**Table row counts:**
| Table | Rows |
|-------|------|
| `matches_raw` | 277,099,059 |
| `ratings_raw` | 58,317,433 |
| `leaderboards_raw` | 2,381,227 |
| `profiles_raw` | 3,609,686 |

**Dtype strategy for `ratings_raw`:** Explicit `dtypes=` map (BIGINT/TIMESTAMP) required — `read_csv_auto` infers all 7 columns as VARCHAR at scale (2,072 files). Strategy established in Step 01_02_01.

**NULL rates (key fields):**
- `matches_raw.won`: 12,985,561 NULLs / 277,099,059 rows (4.69%) — root cause established in 01_02_01 won=NULL investigation
- `matches_raw.matchId`: 0 NULLs
- `matches_raw.filename`: 0 NULLs
- `ratings_raw.profile_id`: 0 NULLs
- `ratings_raw.filename`: 0 NULLs

**Invariant I10 (relative filenames):** All four tables pass — filenames stored relative to `raw_dir`. Enforced inline via `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)` in every CTAS. No post-load UPDATE (would OOM on 277M-row `matches_raw`).

**Parquet binary columns:** All Parquet reads use `binary_as_string=true` for the unannotated BYTE_ARRAY columns in matches/leaderboards/profiles. Established in 01_02_01.

### Decisions taken

- All tables use `*_raw` suffix convention (bronze layer)
- Inline `SELECT * REPLACE` for I10 relativization — never post-load UPDATE
- Explicit dtype map for ratings CSV ingestion — never `read_csv_auto` at scale
- `binary_as_string=true` for all Parquet sources

### Decisions deferred

- Handling of 12.99M NULL `won` values — deferred to Step 01_04 (data cleaning)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: four-table ingestion, dtype strategy, I10 compliance

### Artifact note

The `.json` artifact `sql` key records pre-fix SQL (`SELECT * FROM read_parquet(...)` without `REPLACE`). The actual ingestion code uses `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)`. The DuckDB on disk is correct; the artifact should be regenerated from a fresh notebook run to reflect the inline I10 pattern.

### Open questions / follow-ups

- Full NULL profiles for all 55 `matches_raw` columns — deferred to 01_03 (systematic profiling)

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

**H1 REJECTED.** `parquet_schema()` scan across all 2,073 match files found a
single `won` Parquet type: `BOOLEAN`. There is no schema heterogeneity. DuckDB
type promotion under `union_by_name=true` is not the cause of NULLs.

**H2 SUPPORTED.** 12,985,561 genuine NULL `won` values exist in the source
files. Every single file (2,073 of 2,073) contributes NULLs — the date range
of affected files is 2020-08-01 to 2026-04-04, i.e., the entire corpus
history. There is no temporal step-change or isolated bad period: NULLs are
a structural property of the dataset from day one.

Additional context from the existing artifact:
- `avg_rows_per_match = 3.71` — the dataset contains substantial team-game
  data beyond 1v1 (expected avg would be 2.0 for pure 1v1). This means
  `won=NULL` cannot be attributed to a single-player record issue.
- NULL rate: 4.69% of 277,099,059 total rows = 12,985,561 NULL `won` values.
- The aoe2companion API simply does not record a winner for some matches — the
  root cause is upstream (API-level recording gap), not a data engineering
  artefact.

### Decisions taken

- H1 definitively rejected: no INT64-to-BOOLEAN cast recovery needed.
- H2 confirmed: NULLs are genuine and uniformly distributed across the entire
  dataset history — not concentrated in a time window that could be excluded.
- Investigation scope limited to diagnosis only — no cleaning decisions made
  at this step.

### Decisions deferred

- Handling strategy for NULL `won` rows (row-level drop, match-level drop,
  or leaderboard-filtered subset) deferred to Step 01_04 (data cleaning).
- Impact on thesis scope: whether to restrict analysis to the 95.31% of rows
  with recorded winners, or characterise the NULL population separately.
- Whether `avg_rows_per_match = 3.71` implies a leaderboard filter is needed
  to isolate 1v1 matches before the prediction task is scoped.

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 data quality: won column NULL analysis
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- What leaderboard value(s) correspond to ranked 1v1 in aoe2companion? Does
  filtering to that leaderboard reduce the NULL rate?
- Is `avg_rows_per_match = 3.71` driven by FFA/team-game leaderboards only,
  or does it affect the ranked 1v1 population too?

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Pre-ingestion investigation using in-memory DuckDB and direct Parquet/CSV
queries to characterise the four aoe2companion data sources before committing
to a DuckDB ingestion design. Binary column inspection, smoke test, full-corpus
NULL rate census, and match_id uniqueness check. No DuckDB tables were created
at this step — that is step 01_02_02.

### Why

Determine ingestion strategy before materialising 277M rows. Invariants #7
(type fidelity) and #9 (step scope) — pre-ingestion characterisation is a
distinct step from ingest. The binary column issue (unannotated BYTE_ARRAY)
and the CSV type inference pitfall at scale must be resolved before 01_02_02.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

**Binary column inspection** (metadata read on `match-2020-08-01.parquet` sample):
- matches: 22 of 54 columns are BYTE_ARRAY with no logical type annotation
  (no UTF-8 annotation) — strings stored without Parquet STRING annotation
- leaderboards: 4 of 18 columns BYTE_ARRAY unannotated
- profiles: 11 of 13 columns BYTE_ARRAY unannotated
- All require `binary_as_string=true` at ingestion to resolve to VARCHAR

**Smoke test** (sampled subset of files):
- matches sample: 491,099 rows × 55 columns
- ratings sample: 266,508 rows × 8 columns

**Full-corpus NULL rates** (direct Parquet queries on all 2,073 match files):
- Total rows: 277,099,059; `matchId` and `profileId` 100% populated
- `won` column: 12,985,561 NULLs (4.69%) — see 2026-04-14 won-NULL root-cause entry

**Match_id uniqueness** (full corpus):
- 74,788,989 distinct `matchId` values; avg 3.71 rows per match
- avg > 2.0 indicates substantial team-game data beyond 1v1

**CSV ratings at scale:**
- `read_csv_auto` infers all 7 columns as VARCHAR when scanning all 2,072 files
  simultaneously — explicit `types=` required for correct BIGINT/TIMESTAMP types
- Missing file: `rating-2025-07-11.csv` — 2,073 match files vs 2,072 rating files

### Decisions taken

- All Parquet reads require `binary_as_string=true`
- CSV ratings require explicit column type map — never `read_csv_auto` at scale
- Raw layer uses `SELECT *` with `filename=true`; no explicit DDL at this step
- Full row counts for ratings/leaderboards/profiles deferred to 01_02_02

### Decisions deferred

- Handling of 12.99M NULL `won` values — see 2026-04-14 root-cause entry;
  cleaning decision deferred to Step 01_04
- Whether missing `rating-2025-07-11.csv` is recoverable or a permanent gap
- `profileId` vs `profile_id` naming inconsistency across tables — deferred
  to Phase 02 join design

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: binary column handling, CSV type pitfall
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- Full row counts for ratings_raw, leaderboards_raw, profiles_raw — confirmed
  in 01_02_02 artifact
- Does restricting to ranked 1v1 leaderboard reduce the won=NULL rate and
  bring avg_rows_per_match close to 2.0? — investigate in 01_03 or 01_04

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
