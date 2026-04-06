# Plan: refactor/sc2-use-db-client (Category B — Refactor)

**Branch:** `refactor/sc2-use-db-client`
**Version bump:** patch (0.18.1 → 0.18.2)
**Category:** B — Refactor

---

## Step 1 — `src/rts_predict/sc2/cli.py`: replace `_connect_db()` with `DuckDBClient`

Changes:
1. Remove `import duckdb` (line 6) — no longer referenced directly
2. Remove `DB_FILE` from the `sc2.config` import — only used in `_connect_db()`
3. Add `from rts_predict.common.db import DuckDBClient` to imports
4. Delete the `_connect_db()` function (lines 18–20)
5. Refactor `main()` init branch: replace `con = _connect_db()` / `try/finally con.close()` with:
   ```python
   with DuckDBClient(DATASETS[DEFAULT_DATASET]) as client:
       init_database(client.con, should_drop=args.force)
   ```
6. Refactor `_run_explore_command()`: same pattern with `run_phase_1_exploration(client.con, steps=steps)`
7. Refactor `_run_audit_command()`: same pattern with `run_phase_0_audit(client.con, steps=steps)`

Note: `DuckDBClient.__exit__` handles closing; the `finally: con.close(); logger.info(...)` blocks are
replaced entirely by the `with` statement.

---

## Step 2 — `src/rts_predict/sc2/tests/test_cli.py`: fix mocks + add 5 new tests

### 2a. Fix 2 broken mocks

`test_main_init` and `test_main_init_force` currently patch `duckdb` at `_CLI` level.
After the refactor, replace with patching `DuckDBClient` as a context manager:

```python
@patch(f"{_CLI}.DuckDBClient")
def test_main_init(self, m_init, m_client_cls, m_log):
    m_client = MagicMock()
    m_client_cls.return_value.__enter__ = MagicMock(return_value=m_client)
    m_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    ...
    m_init.assert_called_once_with(m_client.con, should_drop=False)
```

### 2b. Add 5 new tests to reach 100% coverage of `cli.py`

| Test | Lines covered |
|------|--------------|
| `TestMainRouting.test_main_audit_routes_to_handler` | `audit` branch |
| `TestMainRouting.test_main_explore_routes_to_handler` | `explore` branch |
| `TestMainRouting.test_main_no_command_prints_help` | `else` branch (print_help) |
| `TestRunExploreCommand.test_run_explore_command` | `_run_explore_command` body |
| `TestRunAuditCommand.test_run_audit_command` | `_run_audit_command` body |

**Lazy-import patching note:** `_run_explore_command` and `_run_audit_command` import
`run_phase_1_exploration` / `run_phase_0_audit` lazily inside the function body.
Patch at the source module, not `_CLI`:
- `@patch("rts_predict.sc2.data.exploration.run_phase_1_exploration")`
- `@patch("rts_predict.sc2.data.audit.run_phase_0_audit")`
Also patch `DuckDBClient` at `_CLI` to avoid real DB connections.

---

## Step 3 — Create `src/rts_predict/common/tests/__init__.py`

Create empty `__init__.py` to make `common/tests/` a proper Python package
(mirrors sc2 layout: `sc2/tests/__init__.py`).

---

## Step 4 — Move `tests/test_common_db.py` → `src/rts_predict/common/tests/test_db.py`

- All imports are absolute (`from rts_predict.common.db import ...`) — no changes needed
- Root `tests/conftest.py` only has a module docstring — no shared fixtures to worry about
- Tests use only `tmp_path` (built-in) and `pytest.raises` — fully portable
- After move, delete `tests/test_common_db.py`

### 4a. Add 2 new tests to reach 100% coverage of `common/db.py`

| Test | Lines covered |
|------|--------------|
| `test_client_con_raises_outside_context` | `DuckDBClient.con` property when `_con is None` (RuntimeError path) |
| `test_client_row_counts` | `row_counts()` — create 2 tables with known row counts, assert mapping matches |

---

## Step 5 — Move `tests/test_common_db_cli.py` → `src/rts_predict/common/tests/test_db_cli.py`

- All imports are absolute — no changes needed
- `mock_client` fixture is defined inside the file — not in conftest
- After move, delete `tests/test_common_db_cli.py`

### 5a. Add 3 new tests to reach 100% coverage of `common/db_cli.py`

| Test | Lines covered |
|------|--------------|
| `test_handle_db_schema_prints_columns` | `_handle_schema` — mock `client.schema()` returning pairs, verify tabulated output |
| `test_handle_db_tables_no_tables` | `_handle_tables` empty case — mock returning `[]`, verify `"(no tables)"` printed |
| `test_format_output_unknown_format_raises` | `_format_output` — call directly with `fmt="xml"`, expect `ValueError` |

---

## Step 6 — `.claude/rules/git-workflow.md`: insert coverage step into PR Creation Flow

Replace the current step 1 with an expanded coverage-aware flow:

```markdown
## PR Creation Flow (on "wrap up")

1. Run checks (skip if no .py files in diff):
   a. `poetry run ruff check src/ tests/`
   b. `poetry run mypy src/rts_predict/`
   c. `poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing | tee coverage.txt`
   d. Read and analyze `coverage.txt` — identify any lines below 100% on project code
   e. Add tests / fix code until 100% project coverage is reached
   f. Re-run step c to verify, then delete `coverage.txt`
2. Version: minor for feat/refactor/docs, patch for fix/test/chore
...
```

Remaining steps (2–7) renumber and are otherwise unchanged in content.

---

## Step 7 — Run full test suite + coverage; verify and fill any remaining gaps

```bash
poetry run ruff check src/ tests/
poetry run mypy src/rts_predict/
poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing | tee coverage.txt
```

Analyze `coverage.txt`. Fill any missed lines. Re-run until clean.

---

## Step 8 — PR wrap-up

1. Bump version: `0.18.1` → `0.18.2` in `pyproject.toml`
2. Update CHANGELOG: new `[0.18.2]` entry with summary of changes
3. Commit `chore(release): bump version to 0.18.2`
4. Write PR body to `.github/tmp/pr.txt`, `gh pr create --body-file`, then `rm .github/tmp/pr.txt`

---

## Files touched summary

| File | Action |
|------|--------|
| `src/rts_predict/sc2/cli.py` | Refactor: remove `_connect_db()`, use `DuckDBClient` |
| `src/rts_predict/sc2/tests/test_cli.py` | Fix 2 mocks + add 5 new tests |
| `src/rts_predict/common/tests/__init__.py` | Create (empty) |
| `src/rts_predict/common/tests/test_db.py` | Move from `tests/test_common_db.py` + add 2 tests |
| `src/rts_predict/common/tests/test_db_cli.py` | Move from `tests/test_common_db_cli.py` + add 3 tests |
| `tests/test_common_db.py` | Delete (moved) |
| `tests/test_common_db_cli.py` | Delete (moved) |
| `.claude/rules/git-workflow.md` | Insert coverage step into PR Creation Flow |
| `pyproject.toml` | Bump version to 0.18.2 |
| `CHANGELOG.md` | New `[0.18.2]` entry |

---

## Gate Condition

- All tests pass (`pytest` green)
- `ruff` and `mypy` clean
- 100% coverage on `rts_predict/common/db.py`, `rts_predict/common/db_cli.py`, `rts_predict/sc2/cli.py`
  (line `if __name__ == "__main__":` conventionally excluded via `# pragma: no cover`)
- No duplicate test files (root `tests/test_common_db*.py` deleted)
