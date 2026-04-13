---
category: A
branch: feat/sc2-phase01-duckdb-ingestion
date: 2026-04-13
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
step_refs: ["01_02_02"]
invariants_touched: [6, 7, 9, 10]
critique_required: true
---

# Plan: Step 01_02_02 — DuckDB Ingestion (sc2egset)

## Scope

Materialise raw sc2egset data into persistent DuckDB tables at
`src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb` using the
three-stream strategy determined by Step 01_02_01. All tables follow the
`*_raw` naming convention. Every table carries a `filename` provenance column
(Invariant I7). Execute via the skeleton notebook, validate results, and
produce report artifacts.

## Problem Statement

Step 01_02_01 established a three-stream ingestion strategy for SC2EGSet.
`ingestion.py` and its tests already exist and pass with synthetic fixtures.
However, the module uses plain table names (`replays_meta`, `replay_players`,
`map_aliases`) which must be renamed to the project-wide `*_raw` convention
(`replays_meta_raw`, `replay_players_raw`, `map_aliases_raw`). The skeleton
notebook at `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`
needs validation cells added before execution. No full-corpus run has been
performed yet.

## Three-stream strategy (from 01_02_01)

| Stream | Table | Description |
|--------|-------|-------------|
| 1 | `replays_meta_raw` | One row per replay. Scalar metadata STRUCTs (details, header, initData, metadata), ToonPlayerDescMap as VARCHAR, error flags. `filename` provenance. Event arrays excluded. |
| 2 | `replay_players_raw` | One row per (replay, player). Normalised from ToonPlayerDescMap via Python JSON extraction. `filename` provenance. |
| 3 | Events (Parquet) | gameEvents / trackerEvents / messageEvents — **out of scope for this step**, section 5 stays commented out. |
| — | `map_aliases_raw` | One row per mapping entry × tournament file. `filename` provenance. |

## Filename strategy

Every `filename` column stores a **path relative to `raw_dir`** (e.g.
`TournamentX/TournamentX_data/match.SC2Replay.json`), never an absolute path.

**Rationale:** DuckDB's `filename=true` returns absolute paths; Python's
`pathlib.Path.glob` also returns absolute paths but resolved independently.
Storing absolute paths creates a cross-stream matching hazard (symlinks,
mount points, machine portability). Stripping the common `raw_dir` prefix
before ingestion guarantees that `replays_meta_raw.filename` and
`replay_players_raw.filename` are identical strings, making the cross-table
integrity join reliable by construction.

**Per-stream implementation:**
- **Stream 1** (`replays_meta_raw`, DuckDB CTAS): strip prefix in SQL using
  `substr(filename, {raw_dir_prefix_len}) AS filename` where
  `raw_dir_prefix_len = len(str(raw_dir)) + 2` (path length + `/` + 1-based
  substr offset).
- **Stream 2** (`replay_players_raw`, Python loop): replace `str(fpath)` with
  `str(fpath.relative_to(raw_dir))` at the call site in `load_replay_players_raw`.
- **Map aliases** (`map_aliases_raw`, Python loop): replace `str(mapping_file)`
  with `str(mapping_file.relative_to(raw_dir))` in `load_map_aliases_raw`.

## Assumptions & Unknowns

- **Assumption:** `ingestion.py` is structurally correct. Only SQL table-name
  constants and string literals need updating for the `*_raw` rename.
- **Assumption:** All 22,390 replay files parse successfully (01_02_01 achieved
  100% on sampled files spanning the size distribution).
- **Assumption:** Persistent DuckDB fits within resource limits (24 GB memory,
  150 GB temp_dir) — event arrays are excluded from the metadata table.
- **Unknown:** Exact replay_players_raw row count. Expected ~44,780 (2 × 22,390)
  but non-1v1 replays or parse failures may deviate. Resolves by: T03 execution.
- **Unknown:** Parse failure rate for `load_replay_players_raw`. Resolves by:
  T03 execution (logger output).
- **Unknown:** Wall-clock time for Python-based `load_replay_players_raw`
  (22,390 JSON loads). Resolves by: T03 execution.

## Literature Context

Three-stream split follows SC2EGSet paper (Bialecki et al. 2023, Scientific
Data 10(1):600). Separating event arrays from metadata is standard practice
in replay analysis pipelines to avoid loading hundreds of GB for match-level
tasks. ToonPlayerDescMap stored as VARCHAR rather than MAP/STRUCT per DuckDB
type-inference findings from 01_02_01 (dynamic keys → incompatible per-file
STRUCT schemas across replays).

---

## Execution Steps

### T00 — Align all dataset ROADMAP.md Step 01_02_02 entries with plan

**Objective:** All three dataset ROADMAPs contain a Step 01_02_02 entry, but
they predate the `*_raw` naming convention and Invariant I10. Update each
ROADMAP in place so the entries match the design decisions codified in this
plan. No new steps are added — only the existing 01_02_02 blocks are edited.

**Specific changes per ROADMAP:**

**`src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`:**
- `description`: replace bare table names with `_raw` variants:
  `replays_meta` → `replays_meta_raw`, `replay_players` → `replay_players_raw`,
  `map_aliases` → `map_aliases_raw`; add note that `filename` stores path
  relative to `raw_dir`.
- `stratification`: same renames.
- `scientific_invariants_applied`: add entry for I10:
  ```yaml
  - number: "10"
    how_upheld: "filename column in all tables stores path relative to raw_dir; no absolute paths."
  ```
- `continue_predicate`: append ` filename values are relative paths (no leading /).`

**`src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`:**
- `description`: rename tables from `raw_` prefix to `_raw` suffix:
  `raw_matches` → `matches_raw`, `raw_players` → `players_raw`,
  `raw_overviews` → `overviews_raw`; add relative-path note.
- `stratification`: same renames.
- `scientific_invariants_applied`: add I10 entry (same text as sc2egset).
- `continue_predicate`: append relative-path clause.

**`src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`:**
- `description`: rename tables from `raw_` prefix to `_raw` suffix:
  `raw_matches` → `matches_raw`, `raw_ratings` → `ratings_raw`,
  `raw_leaderboard` → `leaderboard_raw`, `raw_profiles` → `profiles_raw`;
  add relative-path note.
- `stratification`: same renames.
- `scientific_invariants_applied`: add I10 entry (same text as sc2egset).
- `continue_predicate`: append relative-path clause.

4. Clear stale cell outputs from the skeleton `.ipynb`. The notebook was
   previously executed with old table names; jupytext sync preserves existing
   outputs in unchanged cells, creating a mixed-state notebook. Clear all
   outputs before any source modifications:
   ```
   source .venv/bin/activate && poetry run jupyter nbconvert \
     --clear-output --inplace \
     sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb
   ```

**Verification:**
- `grep -n "raw_matches\|raw_players\|raw_overviews\|raw_ratings\|raw_leaderboard\|raw_profiles"` in all three ROADMAP files returns no matches inside the 01_02_02 block.
- `grep -n "number: \"10\""` returns one hit in each of the three ROADMAP files.
- No other steps in any ROADMAP are touched.
- `.ipynb` has zero cell outputs after `nbconvert --clear-output`.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb` (clear outputs only)

---

### T01 — Rename tables to `*_raw` in `ingestion.py` and tests

**Objective:** Apply the `*_raw` naming convention throughout `ingestion.py`
and the corresponding test file. Every reference to a table name — SQL
constants, function bodies, docstrings, log messages, return-dict keys —
must use the `_raw` suffix. The `filename` column must be explicitly present
in every table's DDL/SELECT; confirm it is not accidentally dropped.

**Instructions:**

1. In `src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py`, rename:
   - SQL constant `_REPLAYS_META_QUERY`: change `CREATE TABLE replays_meta` →
     `CREATE TABLE replays_meta_raw`
   - SQL constant `_DROP_IF_EXISTS_QUERY` usages: all calls that pass
     `table="replays_meta"` → `table="replays_meta_raw"`
   - SQL constant `_REPLAY_PLAYERS_CREATE_QUERY`: change
     `CREATE TABLE replay_players` → `CREATE TABLE replay_players_raw`
   - SQL constant `_REPLAY_PLAYERS_INSERT_QUERY`: change
     `INSERT INTO replay_players` → `INSERT INTO replay_players_raw`
   - SQL constant `_MAP_ALIASES_CREATE_QUERY`: change
     `CREATE TABLE map_aliases` → `CREATE TABLE map_aliases_raw`
   - **Delete `_MAP_ALIASES_INSERT_QUERY` entirely.** Replace the
     `con.execute(_MAP_ALIASES_INSERT_QUERY, ...)` call in
     `load_map_aliases_raw` with pure Python dict iteration:
     ```python
     data = json.loads(json_content)
     rows = [
         (tournament_name, foreign, english, str(mapping_file.relative_to(raw_dir)))
         for foreign, english in data.items()
     ]
     con.executemany("INSERT INTO map_aliases_raw VALUES (?, ?, ?, ?)", rows)
     ```
     `json` is already imported. `TRIM(BOTH '"' FROM ...)` is no longer
     needed — `json.loads` returns proper Python strings, not JSON-encoded
     values. The `str(mapping_file.relative_to(raw_dir))` also satisfies
     the I10 filename requirement inline, superseding the separate
     map-aliases item under instruction #2 below.
   - `_count_rows` call sites: `_count_rows(con, "replays_meta")` →
     `_count_rows(con, "replays_meta_raw")`, etc.
   - Function `load_replays_meta` → `load_replays_meta_raw` (rename function,
     update all internal references)
   - Function `load_replay_players` → `load_replay_players_raw`
   - Function `load_map_aliases` → `load_map_aliases_raw`
   - Function `load_all_raw_tables`: update all three internal calls to the
     renamed functions; update return-dict keys to `"replays_meta_raw"`,
     `"replay_players_raw"`, `"map_aliases_raw"`
   - All `logger.info` strings, docstrings, and comments that reference old
     table names.

2. Apply the **relative-path filename strategy** to all three streams:

   **Stream 1 — `replays_meta_raw` (DuckDB CTAS):**
   - Add `raw_dir_prefix_len` to `_REPLAYS_META_QUERY` format parameters.
   - Change the `filename` column in the SELECT from the bare DuckDB
     `filename` alias to:
     ```sql
     substr(filename, {raw_dir_prefix_len}) AS filename,
     ```
   - In `load_replays_meta_raw`, compute and pass the prefix length:
     ```python
     raw_dir_prefix_len = len(str(raw_dir)) + 2
     con.execute(
         _REPLAYS_META_QUERY.format(
             glob=glob,
             max_object_size=max_object_size,
             raw_dir_prefix_len=raw_dir_prefix_len,
         )
     )
     ```

   **Stream 2 — `replay_players_raw` (Python loop):**
   - In `load_replay_players_raw`, at the call to `_extract_player_row`,
     change `str(fpath)` → `str(fpath.relative_to(raw_dir))`:
     ```python
     batch_rows.append(
         _extract_player_row(str(fpath.relative_to(raw_dir)), toon_id, player_data)
     )
     ```
   - `_extract_player_row` signature is unchanged — it takes a plain `str`.

   **Map aliases — `map_aliases_raw` (Python loop):**
   - In `load_map_aliases_raw`, change `str(mapping_file)` →
     `str(mapping_file.relative_to(raw_dir))`:
     ```python
     con.execute(
         _MAP_ALIASES_INSERT_QUERY,
         [tournament_name, str(mapping_file.relative_to(raw_dir)), json_content],
     )
     ```

3. In `tests/rts_predict/games/sc2/datasets/sc2egset/test_ingestion.py`,
   update all references to old table names and old function names to match
   the renamed versions (same substitutions as above). Do NOT change test
   logic — only the identifiers.

4. Run the test suite to confirm all tests still pass:
   ```
   source .venv/bin/activate && poetry run pytest tests/rts_predict/games/sc2/datasets/sc2egset/ -v
   ```

**Verification:**
- `grep -n "replays_meta[^_]"` returns no matches in `ingestion.py` or tests.
- `grep -n "replay_players[^_]"` returns no matches.
- `grep -n "map_aliases[^_]"` returns no matches.
- All tests pass.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py`
- `tests/rts_predict/games/sc2/datasets/sc2egset/test_ingestion.py`

---

### T02 — Extend notebook with validation cells

**Objective:** Add three validation sections to the skeleton notebook and
enrich the artifact payload. The existing notebook has sections for ingestion,
DESCRIBE, NULL rates, ToonPlayerDescMap type check, event extraction
(commented), and artifact writing. Add: cross-table integrity, player-count
distribution, and map_aliases dedup check.

**Instructions:**

1. Open `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`.
   Apply the following renames (matching T01):
   - Individual loader calls: `load_replays_meta` → `load_replays_meta_raw`,
     `load_replay_players` → `load_replay_players_raw`,
     `load_map_aliases` → `load_map_aliases_raw`.
   - **`load_all_raw_tables` is NOT renamed** — the wrapper keeps its name.
     Do not change the import or call at line 38/53.
   - SQL strings: every `FROM replays_meta`, `FROM replay_players`,
     `FROM map_aliases` → `_raw` variants (lines 81, 99, 107, 128).
   - Markdown prose strings and artifact builder text: line 47–48 markdown
     cell names and lines 188–201 artifact builder table names must also be
     updated — these are not SQL but must match the actual table names per
     Invariant I6.

2. Move `db.close()` from its current position (line 135, after section 4)
   to **after section 6** (after the artifact writing). The connection must
   remain open for sections 4b, 4c, 4d. The artifact section (section 6)
   only reads Python variables and does not need the connection, but closing
   at the very end is the safest pattern.

   Current line 135: `db.close()` — delete from here.
   New position: append `db.close()` as the final cell after `print(f"Report written: {md_path}")` at line 206.

2. After existing section 4 (ToonPlayerDescMap type check), add section
   **"4b. Cross-table integrity"**:
   ```sql
   SELECT
       COUNT(DISTINCT rp.filename)                                             AS player_files,
       COUNT(DISTINCT rm.filename)                                             AS meta_files,
       COUNT(DISTINCT rp.filename)
           - COUNT(DISTINCT CASE WHEN rm.filename IS NOT NULL
                                 THEN rp.filename END)                        AS orphan_player_files
   FROM replay_players_raw rp
   LEFT JOIN replays_meta_raw rm ON rp.filename = rm.filename
   ```
   Print the result. Expected: `orphan_player_files = 0`.

3. After section 4b, add section **"4c. Player count per replay"**:
   ```sql
   SELECT players_per_replay, COUNT(*) AS replay_count
   FROM (
       SELECT filename, COUNT(*) AS players_per_replay
       FROM replay_players_raw
       GROUP BY filename
   )
   GROUP BY players_per_replay
   ORDER BY players_per_replay
   ```
   Print the result. Reveals non-1v1 replays or parse anomalies.

4. After section 4c, add section **"4d. map_aliases_raw dedup check"**:
   ```sql
   SELECT
       COUNT(DISTINCT foreign_name)  AS unique_foreign,
       COUNT(DISTINCT english_name)  AS unique_english,
       COUNT(DISTINCT tournament)    AS unique_tournaments,
       COUNT(*)                      AS total_rows
   FROM map_aliases_raw
   ```
   Print the result. Expected: `unique_foreign = 1488`, `unique_tournaments = 70`.

5. In section 6 (artifact writing), enrich `artifact_data` with:
   - `tables_created`: per-table schema (DESCRIBE output) and row counts.
   - `null_rates`: from section 3 output.
   - `cross_table_integrity`: from section 4b output (dict with
     `player_files`, `meta_files`, `orphan_player_files`).
   - `players_per_replay_distribution`: from section 4c output (list of dicts).
   - `map_aliases_dedup`: from section 4d output.
   - `tpdm_type`: from section 4 output.
   - `ingestion_strategy`: short string `"three-stream; see 01_02_01"`.

6. Extend the markdown artifact builder with a section for each validation
   check, including the inline SQL that produced it (Invariant I6).

7. Sandbox rules: no `def`/`class`/`lambda` in cells; no cell exceeds 50
   lines. Validation SQL stays inline in notebook cells.

8. Sync the `.ipynb`:
   ```
   source .venv/bin/activate && poetry run jupytext --sync sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py
   ```

**Verification:**
- Notebook `.py` has sections 4b, 4c, 4d and extended section 6.
- No cell exceeds 50 lines; no `def`/`class`/`lambda`.
- `.ipynb` is in sync.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb`

**Read scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py` (post-T01)
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

---

### T03 — Execute notebook against full corpus

**Objective:** Run the complete notebook to materialise all three DuckDB tables
from 22,390 replay files and 70 mapping files into the persistent DuckDB.
Record all outputs and write report artifacts.

**Instructions:**

1. Ensure directory exists:
   `src/rts_predict/games/sc2/datasets/sc2egset/data/db/`.

2. Execute:
   ```
   source .venv/bin/activate && poetry run jupyter execute \
     sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb \
     --timeout=3600
   ```

3. After execution, verify artifacts exist and are non-empty:
   - `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json`
   - `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md`

4. Spot-check the persistent database:
   ```
   source .venv/bin/activate && poetry run python -c "
   import duckdb
   con = duckdb.connect('src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb', read_only=True)
   for t in con.execute('SHOW TABLES').fetchall():
       print(t[0], con.execute(f'SELECT COUNT(*) FROM \"{t[0]}\"').fetchone()[0])
   con.close()
   "
   ```

5. Confirm gate conditions:
   - Tables present: `replays_meta_raw`, `replay_players_raw`, `map_aliases_raw`.
   - Row counts non-zero (expected: ~22,390 / ~44,780 / ~104,160).
   - `ToonPlayerDescMap` column in `replays_meta_raw` is VARCHAR.
   - `filename` column present in all three tables.
   - `orphan_player_files = 0`.

6. If execution fails: document the failure, diagnose, apply minimal fix to
   `ingestion.py`, add a regression test in T04, re-run.

**Verification:**
- `db.duckdb` non-empty with three `*_raw` tables.
- Both artifact files exist.
- Row counts in expected ranges.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb` (outputs)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json` (created)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md` (created)
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb` (created)

---

### T04 — Verify and extend tests

**Objective:** Tests pass after T01 renames. Add one missing edge-case test
for `_extract_player_row` with an absent `color` subdict.

**Instructions:**

1. Run tests:
   ```
   source .venv/bin/activate && poetry run pytest tests/rts_predict/games/sc2/datasets/sc2egset/ -v
   ```

2. Add two tests in `test_ingestion.py`:

   **a) Missing color subdict edge case:**
   ```python
   def test_extract_player_row_missing_color() -> None:
       """_extract_player_row must handle absent 'color' key gracefully."""
       row = _extract_player_row(
           "TournamentX/TournamentX_data/test.SC2Replay.json",
           "1-S2-1-999",
           {"nickname": "TestPlayer", "playerID": 99},
       )
       # color_a, color_b, color_g, color_r are last 4 positional values
       assert row[-4:] == (None, None, None, None)
   ```

   **b) Relative filename in all three tables:**
   Extend (or add) table-level tests to assert that no `filename` value in
   `replays_meta_raw`, `replay_players_raw`, or `map_aliases_raw` starts with
   `/` (i.e., is not an absolute path). Use the existing synthetic fixture
   setup (`tmp_path`, minimal JSON files) and call each loader function.
   Example assertion:
   ```python
   filenames = con.execute("SELECT DISTINCT filename FROM replays_meta_raw").fetchall()
   assert all(not f[0].startswith("/") for f in filenames), \
       "replays_meta_raw.filename must be relative, not absolute"
   ```
   Apply the same assertion for `replay_players_raw` and `map_aliases_raw`.

3. If T03 required any code fixes to `ingestion.py`, add targeted regression
   tests here.

4. Run full project suite:
   ```
   source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing
   ```

**Verification:**
- All tests pass; coverage does not decrease.

**File scope:**
- `tests/rts_predict/games/sc2/datasets/sc2egset/test_ingestion.py`

---

### T05 — Update status files and research log

**Objective:** Mark step 01_02_02 complete and write the research log entry.

**Instructions:**

1. `STEP_STATUS.yaml`: set `01_02_02` → `complete`, add `completed_at: "2026-04-13"`.

2. `PIPELINE_SECTION_STATUS.yaml`: if `01_02_01` and `01_02_02` are now the
   only steps in section `01_02`, update section status to `complete`.

3. Prepend research log entry to
   `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`:
   - Date, step ref `01_02_02`, category A
   - Artifacts: JSON + MD paths
   - What: materialised three `*_raw` DuckDB tables
   - Why: enable SQL-based EDA for subsequent profiling and cleaning
   - How: notebook path
   - Findings: actual row counts, NULL rates, cross-table integrity result,
     player-count distribution, ToonPlayerDescMap VARCHAR confirmation,
     map_aliases dedup profile
   - Decisions taken: any anomaly handling (non-1v1 replays, parse failures)
   - Decisions deferred: event Parquet extraction (SSD-dependent), data cleaning
   - Thesis mapping: Chapter 4, §4.1.1
   - Open questions: any issues surfaced by validation

4. Jupytext sync (if not done in T02):
   ```
   source .venv/bin/activate && poetry run jupytext --sync sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py
   ```

**Verification:**
- `STEP_STATUS.yaml` shows `01_02_02: complete`.
- `research_log.md` has a new top entry.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`

---

## File Manifest

| File | Action | Task |
|------|--------|------|
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update (table names to `_raw` suffix, add I10) | T00 |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update (table names to `_raw` suffix, add I10) | T00 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update (table names to `_raw` suffix, add I10) | T00 |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb` | Clear outputs (`nbconvert --clear-output`) | T00 |
| `src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py` | Update (rename tables + functions to `*_raw`) | T01 |
| `tests/rts_predict/games/sc2/datasets/sc2egset/test_ingestion.py` | Update (rename refs + add edge-case test) | T01, T04 |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py` | Update (rename refs + new validation sections) | T02 |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb` | Update (jupytext sync + execution outputs) | T02, T03 |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb` | Create | T03 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json` | Create | T03 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md` | Create | T03 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update | T05 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` | Update | T05 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update | T05 |

Note: `ingestion.py` is also a conditional Update if T03 surfaces runtime
issues requiring code fixes.

## Gate Condition

1. Tables `replays_meta_raw`, `replay_players_raw`, `map_aliases_raw` exist
   in `db.duckdb` with non-zero row counts (~22,390 / ~44,780 / ~104,160).
2. `filename` column present in all three tables, storing **relative paths from `raw_dir`** (no leading `/`). I7 satisfied.
3. `ToonPlayerDescMap` column in `replays_meta_raw` is VARCHAR.
4. Cross-table integrity: `orphan_player_files = 0`.
5. Artifact files `01_02_02_duckdb_ingestion.{json,md}` exist and are non-empty.
6. `pytest tests/rts_predict/games/sc2/datasets/sc2egset/ -v` — all pass.
7. `grep -rn "replays_meta[^_]\|replay_players[^_]\|map_aliases[^_]" src/ tests/` — no matches.
8. `STEP_STATUS.yaml` shows `01_02_02: complete`.
9. `research_log.md` has a dated entry for this step.

## Out of Scope

- **Event Parquet extraction.** Section 5 of the notebook stays commented out.
  Deferred to when in-game features are needed (Phase 02). The 01_02_01
  artifact estimates ~368 GB for raw JSON event volume (extrapolated from 7
  files, mean skewed by one 431K-event outlier); actual zstd-compressed Parquet
  output is likely 40–80 GB. SSD headroom should be verified at execution time.
  **When implemented:** `extract_events_to_parquet` currently uses `fpath.name`
  (bare basename) for the `filename` column — this must be changed to
  `str(fpath.relative_to(raw_dir))` per Invariant I10 before execution. Bare
  basenames are ambiguous across tournament subdirectories.
- **Data cleaning.** NULL rates and anomalies are documented, not acted on.
  Pipeline Section 01_04.
- **Feature engineering.** Raw data ingested as-is. No derived columns beyond
  `CAST(ToonPlayerDescMap AS VARCHAR)`.
- **Identity resolution.** `toon_id` stored as-is. Cross-player deduplication
  is Phase 02.
- **AoE2 datasets.** Separate step once sc2egset Phase 01 is further along.

## Thesis Mapping

- Chapter 4, §4.1.1 — SC2EGSet: three-stream ingestion design, ToonPlayerDescMap
  normalisation, `*_raw` bronze-layer convention.

## Open Questions

- What are the 14 single-player replays? Are they observers, disconnects,
  or parse failures? (Deferred to 01_04 cleaning step)
- The 15 NULL MMR values and 33 NULL APM/SQ/supplyCappedPercent values: are
  these missing from the original replay metadata or parser artefacts?
  (Deferred to 01_04)
- Event Parquet extraction sizing: actual zstd compression ratio at scale
  unknown. Smoke test showed 16.88x on one file. (Deferred to Phase 02)
