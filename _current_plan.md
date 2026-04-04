# Plan: Fix mypy errors + clean up tests/ directory

## Context

All 97 tests pass but `mypy` reports 37 type errors. Additionally, the root `tests/` directory has unused files and a standalone MPS test script that isn't integrated with pytest. This plan fixes all mypy errors and cleans up `tests/`.

**Category:** B — Refactor  
**Branch:** `refactor/mypy-and-test-cleanup`

---

## Part 1: Fix 37 mypy errors

### Issue 1: `fetchone()` indexing without None guard (30 errors)

DuckDB's `fetchone()` returns `tuple[Any, ...] | None`. Code indexes directly without guarding.

**Fix:** Add `assert row is not None` before indexing, or inline with a local variable.

**Source files (4 errors + 7 errors + 7 errors = 11 total):**
- [ingestion.py:131,530,562,566](src/rts_predict/sc2/data/ingestion.py)
- [processing.py:269,316,319](src/rts_predict/sc2/data/processing.py)
- [audit.py:268,360,430-432,547-548](src/rts_predict/sc2/data/audit.py)

**Test files (19 total):**
- [test_processing.py](src/rts_predict/sc2/data/tests/test_processing.py) — 9 sites
- [test_ingestion.py](src/rts_predict/sc2/data/tests/test_ingestion.py) — 8 sites + 2 from fetchone indexing

### Issue 2: Generator fixture return types (5 errors)

Pytest fixtures using `yield` annotated as `-> T` instead of `-> Generator[T, None, None]`.

**Fix:** Change return annotations and add `from collections.abc import Generator`.

- [conftest.py:33](src/rts_predict/sc2/data/tests/conftest.py)
- [test_ingestion.py:236](src/rts_predict/sc2/data/tests/test_ingestion.py)
- [test_audit.py:228,290](src/rts_predict/sc2/data/tests/test_audit.py)
- [test_exploration.py:51](src/rts_predict/sc2/data/tests/test_exploration.py)

### Issue 3: Missing type annotation (1 error)

- [conftest.py:54](src/rts_predict/sc2/data/tests/conftest.py) — add `rows: list[dict[str, Any]] = []`

---

## Part 2: Clean up tests/ directory

### 2a: Delete `tests/helpers.py`

- Contains `make_matches_df()` and `make_series_df()` — **never imported anywhere**
- Only referenced in CHANGELOG.md and research_log.md (historical)
- Will be rebuilt when actually needed (Phase 7+)

### 2b: Clean up `tests/conftest.py`

- Currently just a docstring, no fixtures — keep the file but leave it minimal (empty conftest is fine for pytest discovery)

### 2c: Convert `tests/test_mps.py` to proper pytest

Current state: standalone script with `main()` and `print()` calls, not discoverable by pytest.

**Conversion plan:**
- Convert each function to a `test_*` pytest function
- Add `@pytest.mark.skipif(not torch.backends.mps.is_available(), reason="MPS not available")` to all tests
- Remove `print()` calls — pytest captures output; use assertions only
- Remove `main()` and `if __name__` block
- Keep `gc.collect()` / `torch.mps.empty_cache()` as a session-scoped fixture or in a finalizer
- The `tiny_training_loop` test: assert final loss decreased (already has `prev_loss` tracking)
- The `threaded_stress` tests: keep as-is logic, just wrap in test functions

**Resulting test functions:**
1. `test_mps_smoke_matmul` — matmul + sync + finite check
2. `test_mps_autograd_cpu_vs_mps` — gradient comparison
3. `test_mps_tiny_training_loop` — training converges (loss decreases)
4. `test_mps_threaded_stress` — concurrent matmul stability
5. `test_mps_threaded_stress_with_sync` — sequential matmul with per-op sync

All marked with a custom `mps` pytest marker (already registered in pyproject.toml).

### 2d: Keep `tests/__init__.py`

Needed for pytest discovery — leave as empty file.

---

## Execution Order

1. Fix source files: `ingestion.py`, `processing.py`, `audit.py`
2. Fix test type annotations: `conftest.py`, `test_ingestion.py`, `test_processing.py`, `test_audit.py`, `test_exploration.py`
3. Delete `tests/helpers.py`
4. Rewrite `tests/test_mps.py` as proper pytest
5. Verify: `mypy` → 0 errors, `pytest` → all pass, `ruff` → clean

## Verification

```bash
poetry run mypy src/rts_predict/          # 0 errors
poetry run pytest tests/ src/ -v          # all tests pass (MPS tests skip on non-MPS)
poetry run ruff check src/ tests/         # clean
```
