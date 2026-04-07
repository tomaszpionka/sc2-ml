# Test Coverage Improvement — `src/rts_predict/aoe2` to 99%

**Branch:** `feat/aoe2-phase0-ingestion`
**Category:** C (chore — no new science)

## Current state

| File | Stmts | Miss | Cover | Uncovered lines |
|------|-------|------|-------|-----------------|
| `cli.py` | 41 | 11 | 73% | 20-34, 99 |
| `aoe2companion/acquisition.py` | 130 | 2 | 98% | 217, 341 |
| `aoe2companion/audit.py` | 512 | 55 | 89% | 255-269, 325, 421-437, 475, 506-507, 525-526, 536-537, 565-567, 576-587, 842, 844, 865, 867, 883-888, 902-904, 1017-1019, 1068-1073, 1181, 1430, 1542, 1553-1554, 1557-1558, 1561, 1564-1566 |
| `aoestats/acquisition.py` | 118 | 9 | 92% | 181-184, 336-339, 346 |
| `aoestats/audit.py` | 356 | 9 | 97% | 98, 527, 529, 1091, 1094, 1097, 1100-1102 |

**Total stmts:** 1303, **Total miss:** 86, **Current coverage:** 93.40%
**Target:** 99% (max 13 missed lines)
**Lines to cover:** at least 73 more

---

## Uncovered code analysis (line-by-line)

### File 1: `cli.py` (11 missed lines)

| Lines | What it does | Testable? |
|-------|-------------|-----------|
| 20-34 | `_handle_download()` — dispatches download to aoe2companion or aoestats module based on `args.source`, passes `dry_run`, `log_interval`, `force` | Yes — mock both acquisition modules and call `main()` via `sys.argv` |
| 99 | `elif args.command == "download":` branch in `main()` — routes to `_handle_download` | Yes — covered by the above test |

### File 2: `aoe2companion/acquisition.py` (2 missed lines)

| Lines | What it does | Testable? |
|-------|-------------|-----------|
| 217 | `tmp_path.unlink()` inside `except` block of `download_file()` — cleanup when network fails AND tmp file exists | Yes — mock `urlopen` to write partial data then raise |
| 341 | `logger.info("Progress: ...")` inside `run_download()` — log progress every `log_interval` files | Yes — use `log_interval=1` so the modulo fires |

### File 3: `aoe2companion/audit.py` (55 missed lines)

| Lines | What it does | Testable? |
|-------|-------------|-----------|
| 255-269 | Report section for oversized files (actual > expected) in `run_source_audit` markdown output | Yes — create manifest entry with expected_size < actual_size |
| 325 | `raise FileNotFoundError` in `profile_match_schema` when no match parquets exist | Yes — pass an empty matches dir |
| 421-437 | Schema drift report section in `profile_match_schema` when `stability == "DRIFTED"` | Yes — create fixture with drifted match parquets |
| 475 | `raise FileNotFoundError` in `profile_rating_schema` when no CSVs exist | Yes — pass raw_dir with empty ratings dir |
| 506-507 | `_pick()` inner branch when `len(lst) > n` — stepped sampling | Yes — provide >3 CSVs to the profile function |
| 525-526 | `except` branch in per-sample DESCRIBE of CSV — schema = ERROR | Hard to trigger naturally; requires a corrupt CSV that makes DuckDB DESCRIBE fail. Testable via corrupt file or mock. |
| 536-537 | `except` branch in union DESCRIBE of all CSVs — schema = ERROR | Same as above — paired with 525-526 |
| 565-567 | Type-inconsistency detection + `type_consistent = False` in `profile_rating_schema` | Yes — provide CSVs with different column types |
| 576-587 | DtypeDecision `explicit` path — builds explicit dtype_map when CSV schemas disagree | Yes — same test as 565-567 (they're the resulting branch) |
| 842 | `raise FileNotFoundError` in `run_smoke_test` — no match parquets | Yes — empty matches dir |
| 844 | `raise FileNotFoundError` in `run_smoke_test` — no rating CSVs | Yes — empty ratings dir |
| 865 | `raise FileNotFoundError` in `run_smoke_test` — no sparse CSVs | Defensive — requires all CSVs to be dense AND no header-only files. Testable with a fixture of only dense CSVs. |
| 867 | `raise FileNotFoundError` in `run_smoke_test` — no dense CSVs | Defensive — requires all CSVs to be sparse/header-only. Testable. |
| 883-888 | Explicit dtype path in `run_smoke_test` SQL construction | Yes — pass DtypeDecision with strategy="explicit" |
| 902-904 | `_exec()` exception handler — error logged when SQL fails | Yes — provide a corrupt parquet/CSV that causes DuckDB error |
| 1017-1019 | Smoke test error section written to report markdown | Yes — covered by the same corrupt-file test |
| 1068-1073 | Explicit dtype path in `run_full_ingestion` SQL construction | Yes — pass DtypeDecision with strategy="explicit" |
| 1181 | `on_disk_zero_row_ratings = sum(...)` counting header-only CSVs for reconciliation | Yes — include a header-only CSV in fixture |
| 1430 | STRICT reconciliation line in `write_phase0_summary` INVARIANTS.md | Yes — pass audit_results with `strength: "STRICT"` |
| 1542 | `DtypeDecision.from_json(decision_path)` in `run_phase_0_audit` when step 0.3 is skipped | Yes — pre-write a decision artifact then skip step 0.3 |
| 1553-1554 | `run_smoke_test(raw_dir, decision, reports_dir)` via orchestrator step 0.5 | Yes — run orchestrator with steps including "0.5" |
| 1557-1558 | `run_full_ingestion(con, raw_dir, decision, reports_dir)` via orchestrator step 0.6 | Yes — run orchestrator with steps including "0.6" |
| 1561 | `run_rowcount_reconciliation(...)` via orchestrator step 0.7 | Yes — run orchestrator with steps including "0.7" |
| 1564-1566 | `write_phase0_summary(...)` via orchestrator step 0.8 | Yes — run orchestrator with steps including "0.8" |

### File 4: `aoestats/acquisition.py` (9 missed lines)

| Lines | What it does | Testable? |
|-------|-------------|-----------|
| 181-184 | `except` cleanup in `download_file` — remove tmp file on failure | Yes — mock `urlopen` to write partial then raise, with tmp file existing |
| 336-339 | Failed download error handling in `run_download` — log + build log entry with "failed" status | Yes — mock `download_file` to raise, with `force=True` |
| 346 | Progress log every `log_interval` files | Yes — use `log_interval=1` |

### File 5: `aoestats/audit.py` (9 missed lines)

| Lines | What it does | Testable? |
|-------|-------------|-----------|
| 98 | `raise FileNotFoundError` in `_profile_parquet_schema` when no files match glob | Yes — pass empty dir |
| 527 | `raise FileNotFoundError` in `run_smoke_test` — need at least 2 match files | Yes — provide only 1 match file |
| 529 | `raise FileNotFoundError` in `run_smoke_test` — need at least 2 player files | Yes — provide only 1 player file |
| 1091 | `run_smoke_test(raw_dir, ...)` via orchestrator step 0.4 | Yes — run orchestrator with steps including "0.4" |
| 1094 | `run_full_ingestion(con, ...)` via orchestrator step 0.5 | Yes — run orchestrator with steps including "0.5" |
| 1097 | `run_rowcount_reconciliation(...)` via orchestrator step 0.6 | Yes — run orchestrator with steps including "0.6" |
| 1100-1102 | `write_phase0_summary(...)` via orchestrator step 0.7 | Yes — run orchestrator with steps including "0.7" |

---

## Execution steps

### Step 1 — `cli.py` tests (covers 11 lines)

**File:** `src/rts_predict/aoe2/tests/test_cli.py`

Add a new `TestCLIDownloadDispatch` class with two tests:

1. **`test_download_dispatches_to_aoe2companion`** (covers lines 20-27, 34, 99)
   - `patch("sys.argv", ["aoe2", "download", "aoe2companion", "--dry-run"])`
   - `patch("rts_predict.aoe2.cli.setup_logging")`
   - `patch("rts_predict.aoe2.data.aoe2companion.acquisition.run_download", return_value={"downloaded": 0})` as `mock_dl`
   - Call `main()`
   - Assert `mock_dl.assert_called_once_with(dry_run=True)`

2. **`test_download_dispatches_to_aoestats_with_force`** (covers lines 20-22, 28-34, 99)
   - `patch("sys.argv", ["aoe2", "download", "aoestats", "--force", "--log-interval", "10"])`
   - `patch("rts_predict.aoe2.cli.setup_logging")`
   - `patch("rts_predict.aoe2.data.aoestats.acquisition.run_download", return_value={"downloaded": 0})` as `mock_dl`
   - Call `main()`
   - Assert `mock_dl.assert_called_once_with(dry_run=False, force=True, log_interval=10)`

### Step 2 — `aoe2companion/acquisition.py` tests (covers 2 lines)

**File:** `src/rts_predict/aoe2/data/aoe2companion/tests/test_acquisition.py`

1. **`TestDownloadFile.test_cleans_up_existing_tmp_on_partial_failure`** (covers line 217)
   - Create a pre-existing `.tmp` file at the expected tmp location
   - Mock `urlopen` to raise `urllib.error.URLError` AFTER creating the tmp file
   - More precisely: mock the response context manager's `read()` to write some data first, then raise `OSError`
   - Assert `pytest.raises(OSError)` and that no `.tmp` file remains
   - Note: the existing test `test_cleans_up_temp_file_on_network_failure` covers the `except` path but not the `if tmp_path.exists(): tmp_path.unlink()` inner branch because `urlopen` fails before the tmp is created

2. **`TestRunDownload.test_progress_log_fires`** (covers line 341)
   - Set up manifest with 2 entries, `log_interval=1`
   - Use `monkeypatch` on acquisition module paths
   - Run with `dry_run=True` so no actual downloads happen
   - Assert result includes expected counts (proves the modulo branch ran)
   - Optionally verify the log message via `caplog`

### Step 3 — `aoe2companion/audit.py` tests — source audit oversized branch (covers ~16 lines)

**File:** `src/rts_predict/aoe2/data/aoe2companion/tests/test_audit.py`

1. **`test_source_audit_oversized_file_passes_gate`** (covers lines 255-269)
   - Create a manifest entry where `size` is smaller than the actual file size on disk (oversized case)
   - The actual file exists and is non-zero
   - Call `run_source_audit`
   - Assert `result["passed"] is True` (oversized files pass the gate)
   - Assert `len(result["oversized_mismatches"]) == 1`
   - Read the markdown report and assert it contains "Oversized files"

### Step 4 — `aoe2companion/audit.py` tests — schema profiling edge cases (covers ~24 lines)

**File:** `src/rts_predict/aoe2/data/aoe2companion/tests/test_audit.py`

1. **`test_profile_match_schema_empty_dir_raises`** (covers line 325)
   - Create a raw_dir with empty `matches/` directory
   - Call `profile_match_schema(raw_dir, reports_dir)`
   - `pytest.raises(FileNotFoundError, match="No match parquets")`

2. **`test_profile_match_schema_drifted_columns`** (covers lines 421-437)
   - Create 5 match parquets: 4 with schema `{id: INT64, score: INT64}` and 1 with `{id: INT64, score: DOUBLE}` (or add an extra column to one file)
   - Call `profile_match_schema`
   - Assert `result["stability"] == "DRIFTED"`
   - Read the report markdown and assert it contains "Schema drift" section
   - Assert the missing/drifted column name appears in the report

3. **`test_profile_rating_schema_empty_dir_raises`** (covers line 475)
   - Create raw_dir with empty `ratings/` directory
   - `pytest.raises(FileNotFoundError, match="No rating CSVs")`

4. **`test_profile_rating_schema_many_csvs_triggers_stepped_pick`** (covers lines 506-507)
   - Create raw_dir with >3 dense CSVs (e.g. 5 dense CSVs)
   - Call `profile_rating_schema`
   - Assert the function succeeds and the number of dense_samples in internals is 3 (verify indirectly via result containing schemas)

5. **`test_profile_rating_schema_type_inconsistency_triggers_explicit`** (covers lines 565-567, 576-587)
   - Create 2+ CSVs with different column types: one CSV has `rating` parsed as INTEGER, another as DOUBLE (due to mixed content)
   - Simplest: write one CSV with only integer rating values and another with decimal rating values so DuckDB infers different types
   - Call `profile_rating_schema`
   - Assert `decision.strategy == "explicit"`
   - Assert `decision.dtype_map` is non-empty
   - Assert `decision.rationale` mentions "inconsistent"

### Step 5 — `aoe2companion/audit.py` tests — smoke test edge cases (covers ~18 lines)

**File:** `src/rts_predict/aoe2/data/aoe2companion/tests/test_audit.py`

1. **`test_smoke_test_no_match_parquets_raises`** (covers line 842)
   - Create raw_dir with empty `matches/` but valid `ratings/`
   - `pytest.raises(FileNotFoundError, match="No match parquets")`

2. **`test_smoke_test_no_rating_csvs_raises`** (covers line 844)
   - Create raw_dir with valid matches but empty `ratings/`
   - `pytest.raises(FileNotFoundError, match="No rating CSVs")`

3. **`test_smoke_test_no_sparse_csvs_raises`** (covers line 865)
   - Create raw_dir with only dense CSVs (all >= 1024 bytes), no sparse/header-only
   - `pytest.raises(FileNotFoundError, match="No sparse")`

4. **`test_smoke_test_no_dense_csvs_raises`** (covers line 867)
   - Create raw_dir with only header-only CSVs (all <= 63 bytes), no dense
   - `pytest.raises(FileNotFoundError, match="No dense")`

5. **`test_smoke_test_explicit_dtype_path`** (covers lines 883-888)
   - Create valid raw_dir with sparse + dense CSVs
   - Pass `DtypeDecision(strategy="explicit", rationale="test", dtype_map={"rating": "INTEGER"})`
   - Assert `result["passed"]` succeeds or check the report contains `dtypes =`

6. **`test_smoke_test_sql_error_captured`** (covers lines 902-904, 1017-1019)
   - Create raw_dir with a corrupt match parquet (e.g. `b"NOT PARQUET"`) but valid ratings/leaderboard/profiles
   - Pass `DtypeDecision(strategy="auto_detect", rationale="test")`
   - Assert `result["passed"] is False`
   - Assert `len(result["errors"]) > 0`
   - Read report and assert `"## Errors"` in markdown

### Step 6 — `aoe2companion/audit.py` tests — ingestion explicit dtype + reconciliation (covers ~6 lines)

**File:** `src/rts_predict/aoe2/data/aoe2companion/tests/test_audit.py`

1. **`test_run_full_ingestion_explicit_dtype`** (covers lines 1068-1073)
   - Call `run_full_ingestion` with `DtypeDecision(strategy="explicit", rationale="test", dtype_map={"profile_id": "BIGINT", "rating": "INTEGER", ...})`
   - Use the standard raw_dir fixture
   - Assert tables are created and report mentions `dtypes =`

2. **`test_rowcount_reconciliation_counts_zero_row_ratings`** (covers line 1181)
   - Ensure the raw_dir fixture has a header-only CSV (already does: `rating-2020-08-01.csv` is sparse)
   - Load tables, run `run_rowcount_reconciliation`
   - The fixture already has this but the specific `ratings_dir.exists()` branch with `on_disk_zero_row_ratings` counting may need a manifest that references ratings correctly
   - Verify `result` contains `zero_row_ratings >= 0`

### Step 7 — `aoe2companion/audit.py` tests — write_phase0_summary STRICT branch + orchestrator (covers ~10 lines)

**File:** `src/rts_predict/aoe2/data/aoe2companion/tests/test_audit.py`

1. **`test_write_phase0_summary_strict_reconciliation`** (covers line 1430)
   - Pass `audit_results["0.7"]["strength"] = "STRICT"` to `write_phase0_summary`
   - Assert INVARIANTS.md contains "per-file actual_rows == manifest_rows"

2. **`test_run_phase_0_audit_later_steps`** (covers lines 1542, 1553-1554, 1557-1558, 1561, 1564-1566)
   - Pre-write a `00_03_dtype_decision.json` to disk (so step 0.3 can be skipped and decision loads from file — covers line 1542)
   - Call `run_phase_0_audit` with `steps=["0.5", "0.6", "0.7", "0.8"]`
   - Assert `"0.5" in results` (covers 1553-1554)
   - Assert `"0.6" in results` (covers 1557-1558)
   - Assert `"0.7" in results` (covers 1561)
   - Assert `"0.8" in results` (covers 1564-1566)

### Step 8 — `aoestats/acquisition.py` tests (covers 9 lines)

**File:** `src/rts_predict/aoe2/data/aoestats/tests/test_acquisition.py`

1. **`TestDownloadFile.test_cleans_up_existing_tmp_on_partial_failure`** (covers lines 181-184)
   - Same pattern as aoe2companion: mock the response read to produce partial data then raise `OSError`
   - Assert no `.tmp` file remains after the exception

2. **`TestRunDownload.test_download_failure_logged`** (covers lines 336-339)
   - `monkeypatch` module paths
   - `monkeypatch.setattr(mod, "download_file", side_effect=ValueError("simulated"))` 
   - Call `run_download(dry_run=False, force=True)`
   - Assert `result["failed"] > 0`
   - Read the download log and check at least one entry has `"status": "failed"`

3. **`TestRunDownload.test_progress_log_fires`** (covers line 346)
   - Set up manifest with 2 entries
   - Call `run_download(dry_run=True, force=False, log_interval=1)`
   - Assert result totals are correct (proves modulo branch executed)

### Step 9 — `aoestats/audit.py` tests (covers 9 lines)

**File:** `src/rts_predict/aoe2/data/aoestats/tests/test_audit.py`

1. **`test_profile_schema_empty_dir_raises`** (covers line 98)
   - Create a raw_dir with empty `matches/` directory
   - Call `profile_match_schema(raw_dir, reports_dir)` (which calls `_profile_parquet_schema`)
   - `pytest.raises(FileNotFoundError, match="No files matching")`

2. **`test_smoke_test_insufficient_match_files_raises`** (covers line 527)
   - Create raw_dir with only 1 match file and 2 player files
   - `pytest.raises(FileNotFoundError, match="Need at least 2 match")`

3. **`test_smoke_test_insufficient_player_files_raises`** (covers line 529)
   - Create raw_dir with 2 match files and only 1 player file
   - `pytest.raises(FileNotFoundError, match="Need at least 2 player")`

4. **`test_run_phase_0_audit_later_steps`** (covers lines 1091, 1094, 1097, 1100-1102)
   - Call `run_phase_0_audit` with `steps=["0.4", "0.5", "0.6", "0.7"]`
   - Use the standard fixtures (raw_dir, db_con, manifest_file)
   - Assert `"0.4" in results` (covers 1091)
   - Assert `"0.5" in results` (covers 1094)
   - Assert `"0.6" in results` (covers 1097)
   - Assert `"0.7" in results` (covers 1100-1102)

---

## Lines intentionally left uncovered (defensive / hard to trigger)

| File | Lines | Reason |
|------|-------|--------|
| `aoe2companion/audit.py` | 525-526, 536-537 | Exception handlers in DuckDB DESCRIBE queries on CSV files. These fire only when a CSV file is so corrupt that DuckDB cannot even describe it. Triggering this reliably requires writing a file that passes `glob()` but makes DuckDB's CSV sniffer crash — fragile and version-dependent. **4 lines.** |

With these 4 lines remaining uncovered, the total missed would be 86 - 82 = 4, which is well under the 13-line threshold for 99%.

If during execution lines 525-526 and 536-537 prove easy to cover (e.g. by writing a file with only non-UTF8 binary content), they should be covered. Otherwise the 4-line margin is safe.

---

## Gate condition

```bash
poetry run pytest tests/ src/ -v --cov --cov-report=term-missing
```

**Pass criteria:**
- All tests pass (0 failures)
- `src/rts_predict/aoe2` aggregate coverage >= 99% (at most 13 of 1303 lines missed)
- No regressions in existing tests
- `poetry run ruff check src/ tests/` passes
- `poetry run mypy src/rts_predict/` passes

---

## Fixture strategy

Most new tests reuse the existing `raw_dir`, `db_con`, and `manifest_file` fixtures from conftest.py. New fixtures needed:

1. **`aoe2companion/tests/conftest.py`**: No new session-scoped fixtures needed. Individual test functions will create their own edge-case raw dirs inline using the existing `_write_match_parquet` helper and `tmp_path`.

2. **`aoestats/tests/conftest.py`**: No new fixtures. Inline `tmp_path`-based setup for edge cases (1 match file, 1 player file, empty dirs).

## Execution order

Steps 1-9 are independent and can be executed in any order. However, the recommended order is as written (files with greatest impact first), running tests after each step to catch regressions early:

```bash
# After each step:
poetry run pytest src/rts_predict/aoe2/ -v --cov=rts_predict.aoe2 --cov-report=term-missing
```
