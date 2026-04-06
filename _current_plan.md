# Shared DuckDB Client, DatasetConfig Registry, and AoE2 CLI

**Category:** C (Chore)
**Branch:** `chore/aoe2-cli-shared-db`
**Version bump:** patch

---

## Objective

1. Introduce a game-agnostic `DatasetConfig` dataclass + `DuckDBClient` in
   `src/rts_predict/common/db.py`.
2. Add shared CLI helpers (`add_db_subparser`, `handle_db_command`) in
   `src/rts_predict/common/db_cli.py` so neither SC2 nor AoE2 duplicate the
   argparse wiring.
3. Wire the new `db` subcommand group into the existing SC2 CLI.
4. Create a full AoE2 CLI (`src/rts_predict/aoe2/cli.py`) with the `db`
   subcommand as its first functional command, plus register the `aoe2`
   entrypoint in `pyproject.toml`.
5. Update `common/CONTRACT.md` and `CHANGELOG.md`.

---

## Confirmed Decisions

1. **Output format:** `--format csv|json|table` (default `table`) from day one.
2. **`_connect_db()` migration:** Deferred. Existing SC2 callers in `cli.py`
   are untouched. CHANGELOG notes `refactor/sc2-use-db-client` as a required
   follow-up.
3. **DuckDB resource pragmas:** `DuckDBClient.__init__` accepts keyword args
   with sensible defaults. Each game config can override at call sites.
   `ingestion.py` pragmas are untouched in this PR.
4. **`common/CONTRACT.md`:** Updated (not a new README).

---

## Design

### `DatasetConfig` — frozen dataclass

Lives in `common/db.py`. Each game's `config.py` exports:

```python
DATASETS: dict[str, DatasetConfig]
DEFAULT_DATASET: str
```

SC2 → one entry (`"sc2egset"`).
AoE2 → two entries (`"aoe2companion"`, `"aoestats"`).
Adding a third dataset requires zero structural change anywhere else.

### `DuckDBClient` — context manager

```python
class DuckDBClient:
    def __init__(
        self,
        dataset: DatasetConfig,
        *,
        memory_limit: str = "24GB",
        threads: int = 4,
        max_temp_dir_size: str = "150GB",
        read_only: bool = False,
    ) -> None: ...

    def __enter__(self) -> "DuckDBClient": ...
    def __exit__(self, *exc: object) -> None: ...

    @property
    def con(self) -> duckdb.DuckDBPyConnection: ...

    def query(self, sql: str, params: list[object] | None = None) -> duckdb.DuckDBPyRelation: ...
    def fetch_df(self, sql: str, params: list[object] | None = None) -> pd.DataFrame: ...
    def tables(self) -> list[str]: ...
    def schema(self, table_name: str) -> list[tuple[str, str]]: ...
    def row_counts(self) -> dict[str, int]: ...
```

`read_only=True` is always used for `db query` CLI commands (no accidental
mutations from ad-hoc queries).

### `common/db_cli.py` — shared argparse helpers

```python
def add_db_subparser(
    subparsers: argparse._SubParsersAction,
    datasets: dict[str, DatasetConfig],
    default_dataset: str,
) -> None: ...

def handle_db_command(
    args: argparse.Namespace,
    datasets: dict[str, DatasetConfig],
) -> None: ...
```

`handle_db_command` dispatches:
- `tables` — prints table list via tabulate
- `schema TABLE` — prints column name/type pairs via tabulate
- `query SQL [--format csv|json|table]` — runs SQL read-only, prints result

Both game CLIs call these two functions; neither duplicates argparse wiring.

---

## Steps

### Step 1 — Create `src/rts_predict/common/db.py`

**Files touched:**
- `src/rts_predict/common/db.py` (NEW)

**Content:**
- `DatasetConfig` frozen dataclass (fields: `name`, `db_file`, `temp_dir`,
  `description`)
- `DuckDBClient` context manager with full API above
- `_DEFAULT_MEMORY_LIMIT`, `_DEFAULT_THREADS`, `_DEFAULT_MAX_TEMP_DIR_SIZE`
  module-level constants

`common/db.py` imports only `duckdb`, `pandas`, `pathlib`, `dataclasses`,
`logging` — no imports from any game package (import direction strictly:
`common` ← `sc2` / `aoe2`).

**Verification:**
```bash
poetry run python -c "from rts_predict.common.db import DuckDBClient, DatasetConfig; print('OK')"
poetry run mypy src/rts_predict/common/
```
**Expected:** Import succeeds, mypy clean.

---

### Step 2 — Create `src/rts_predict/common/db_cli.py`

**Files touched:**
- `src/rts_predict/common/db_cli.py` (NEW)

**Content:**
- `add_db_subparser(subparsers, datasets, default_dataset)` — registers `db`
  subparser with `--dataset` flag (choices = `datasets.keys()`), and three
  sub-subparsers: `query <sql> [--format csv|json|table]`, `tables`, `schema
  <table>`.
- `handle_db_command(args, datasets)` — resolves `DatasetConfig` from
  `args.dataset`, opens `DuckDBClient(dataset, read_only=True)` as context
  manager, dispatches to `_handle_query`, `_handle_tables`, `_handle_schema`.
- `_format_output(df, fmt)` — applies tabulate/csv/json formatting, prints to
  stdout (pipe-friendly, no logger on query output).
- `_handle_tables`, `_handle_schema`, `_handle_query` — private helpers.

Uses `tabulate` (already a project dependency).

**Verification:**
```bash
poetry run mypy src/rts_predict/common/
poetry run ruff check src/rts_predict/common/
```
**Expected:** No errors.

---

### Step 3 — Add `DATASETS` / `DEFAULT_DATASET` to SC2 config

**Files touched:**
- `src/rts_predict/sc2/config.py` (MODIFIED — additive only)

**Changes:**
```python
from rts_predict.common.db import DatasetConfig

DATASETS: dict[str, DatasetConfig] = {
    "sc2egset": DatasetConfig(
        name="sc2egset",
        db_file=DB_FILE,           # existing constant, kept for back-compat
        temp_dir=DUCKDB_TEMP_DIR,  # existing constant, kept for back-compat
        description="SC2EGSet tournament replays",
    ),
}
DEFAULT_DATASET: str = "sc2egset"
```

Existing `DB_FILE`, `DUCKDB_TEMP_DIR`, `DUCKDB_MEMORY_LIMIT` etc. are kept
unchanged — backward-compatible for existing callers.

**Verification:**
```bash
poetry run pytest src/rts_predict/sc2/ -v --tb=short
```
**Expected:** All existing tests pass.

---

### Step 4 — Add `DATASETS` / `DEFAULT_DATASET` to AoE2 config

**Files touched:**
- `src/rts_predict/aoe2/config.py` (MODIFIED — additive only)

**Changes:**
```python
from rts_predict.common.db import DatasetConfig

DATASETS: dict[str, DatasetConfig] = {
    "aoe2companion": DatasetConfig(
        name="aoe2companion",
        db_file=AOE2COMPANION_DB_FILE,   # existing constant
        temp_dir=AOE2COMPANION_TEMP_DIR, # existing constant
        description="aoe2companion.com daily API dumps",
    ),
    "aoestats": DatasetConfig(
        name="aoestats",
        db_file=AOESTATS_DB_FILE,        # existing constant
        temp_dir=AOESTATS_TEMP_DIR,      # existing constant
        description="aoestats.io weekly DB dumps",
    ),
}
DEFAULT_DATASET: str = "aoe2companion"
```

All existing path constants kept unchanged.

**Verification:**
```bash
poetry run mypy src/rts_predict/aoe2/
```
**Expected:** Mypy clean.

---

### Step 5 — Wire `db` subcommand into SC2 CLI

**Files touched:**
- `src/rts_predict/sc2/cli.py` (MODIFIED)

**Changes:**
1. Add imports:
   ```python
   from rts_predict.common.db_cli import add_db_subparser, handle_db_command
   from rts_predict.sc2.config import DATASETS, DEFAULT_DATASET
   ```
2. After the existing `explore` subparser registration, call:
   ```python
   add_db_subparser(subparsers, DATASETS, DEFAULT_DATASET)
   ```
3. Add `elif args.command == "db":` branch in `main()` calling
   `handle_db_command(args, DATASETS)`.

`_connect_db()` and all existing command handlers are **untouched**.

**Verification:**
```bash
poetry run sc2 db --help
poetry run ruff check src/rts_predict/sc2/cli.py
poetry run mypy src/rts_predict/sc2/
```
**Expected:** `db` subcommand appears in help; no lint/type errors.

---

### Step 6 — Create AoE2 CLI

**Files touched:**
- `src/rts_predict/aoe2/cli.py` (NEW)
- `src/rts_predict/aoe2/tests/__init__.py` (NEW — empty, creates test package)

**Content of `cli.py`:**
- `setup_logging()` — mirrors SC2 pattern, writes to `aoe2_pipeline.log`
- `build_parser()` — returns `ArgumentParser` with `db` as the only subcommand
  (via `add_db_subparser(subparsers, DATASETS, DEFAULT_DATASET)`)
- `main()` — `setup_logging()`, `build_parser()`, dispatch
- Top-of-file docstring: "AoE2 CLI — add `init`, `audit`, `explore` subcommands
  as data acquisition phases complete."

**Verification:**
```bash
poetry run mypy src/rts_predict/aoe2/
poetry run ruff check src/rts_predict/aoe2/
```
**Expected:** No errors (before entrypoint registration).

---

### Step 7 — Register AoE2 entrypoint in `pyproject.toml`

**Files touched:**
- `pyproject.toml` (MODIFIED)

**Diff:**
```toml
[project.scripts]
sc2 = "rts_predict.sc2.cli:main"
aoe2 = "rts_predict.aoe2.cli:main"
```

Then:
```bash
poetry install
poetry run aoe2 --help
```

**Expected:** Top-level help lists `db` subcommand.

---

### Step 8 — Write tests for `DuckDBClient`

**Files touched:**
- `tests/test_common_db.py` (NEW)

**Test cases (9 tests):**

| Test | Fixture | Assert |
|------|---------|--------|
| `test_client_context_manager_closes` | `tmp_path` | `con` is closed after `__exit__` |
| `test_client_creates_parent_dirs` | `tmp_path` | parent dirs created on `__enter__` |
| `test_client_read_only_flag` | `tmp_path` | `read_only=True` raises on INSERT |
| `test_client_applies_memory_pragma` | `tmp_path` | `PRAGMA memory_limit` returns set value |
| `test_client_query_returns_relation` | `tmp_path` | result has expected columns/rows |
| `test_client_fetch_df_returns_dataframe` | `tmp_path` | return type is `pd.DataFrame` |
| `test_client_tables_lists_tables` | `tmp_path` | created table appears in `.tables()` |
| `test_client_schema_returns_columns` | `tmp_path` | column names/types match DDL |
| `test_dataset_config_is_frozen` | — | assignment raises `FrozenInstanceError` |

**Verification:**
```bash
poetry run pytest tests/test_common_db.py -v
```
**Expected:** 9 tests pass.

---

### Step 9 — Write tests for `db_cli` helpers

**Files touched:**
- `tests/test_common_db_cli.py` (NEW)

**Test cases (6 tests):**

| Test | Mock | Assert |
|------|------|--------|
| `test_add_db_subparser_registers_subcommands` | — | `query`, `tables`, `schema` in subparser |
| `test_handle_db_query_table_format` | `DuckDBClient` | tabulate output to stdout |
| `test_handle_db_query_csv_format` | `DuckDBClient` | CSV output to stdout |
| `test_handle_db_query_json_format` | `DuckDBClient` | JSON output to stdout |
| `test_handle_db_tables_prints_list` | `DuckDBClient.tables` | table names printed |
| `test_handle_db_dataset_flag_selects_config` | `DuckDBClient` | correct `DatasetConfig` passed |

**Verification:**
```bash
poetry run pytest tests/test_common_db_cli.py -v
```
**Expected:** 6 tests pass.

---

### Step 10 — Write AoE2 CLI tests

**Files touched:**
- `src/rts_predict/aoe2/tests/test_cli.py` (NEW)

**Test cases (3 tests):**

| Test | Assert |
|------|--------|
| `test_main_no_command_exits_with_help` | SystemExit raised (argparse help) |
| `test_main_db_routes_to_handler` | `handle_db_command` called once |
| `test_db_default_dataset_is_aoe2companion` | default dataset name correct |

**Verification:**
```bash
poetry run pytest src/rts_predict/aoe2/tests/ -v
```
**Expected:** 3 tests pass.

---

### Step 11 — Add `db` tests to SC2 CLI test file

**Files touched:**
- `src/rts_predict/sc2/tests/test_cli.py` (MODIFIED — additive only)

**Test cases added (2 tests):**

| Test | Assert |
|------|--------|
| `test_main_db_routes_to_handler` | `handle_db_command` called once |
| `test_db_default_dataset_is_sc2egset` | default dataset name correct |

**Verification:**
```bash
poetry run pytest src/rts_predict/sc2/tests/test_cli.py -v
```
**Expected:** All existing + 2 new tests pass.

---

### Step 12 — Update `common/CONTRACT.md`

**Files touched:**
- `src/rts_predict/common/CONTRACT.md` (MODIFIED)

**Changes:**
Add to "What belongs here":
```markdown
- `DuckDBClient` and `DatasetConfig` — game-agnostic DB infrastructure.
  Zero game-domain content; exempt from the "build twice then extract" rule.
- `db_cli.py` — shared argparse helpers for the `db` CLI subcommand group.
```

**Verification:** Visual review only.

---

### Step 13 — Update `CHANGELOG.md`

**Files touched:**
- `CHANGELOG.md` (MODIFIED)

**Under `[Unreleased] → Added`:**
- `DatasetConfig` frozen dataclass and `DuckDBClient` context manager in
  `common/db.py` — game-agnostic DuckDB connection with configurable resource
  pragmas
- Shared `add_db_subparser` / `handle_db_command` helpers in `common/db_cli.py`
- `sc2 db query <sql> [--format csv|json|table]` — ad-hoc DuckDB queries
- `sc2 db tables` / `sc2 db schema <table>` subcommands
- `aoe2` CLI entrypoint with same `db` subcommand group supporting
  `--dataset aoe2companion|aoestats`
- `DATASETS` / `DEFAULT_DATASET` registry added to both `sc2/config.py` and
  `aoe2/config.py`
- 20 new tests (9 + 6 + 3 + 2)

**Under `[Unreleased] → Changed`:**
- `common/CONTRACT.md` updated to include DB infrastructure as in-scope

**Follow-up note (under Changed):**
```
- **Follow-up required:** `refactor/sc2-use-db-client` — migrate `_connect_db()`
  callers in `sc2/cli.py` to use `DuckDBClient` directly (deferred to keep this
  chore focused)
```

**Verification:**
```bash
head -50 CHANGELOG.md
```

---

### Step 14 — Full verification

**Files touched:** None (verification only)

```bash
poetry run ruff check src/ tests/
poetry run mypy src/rts_predict/
poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing
```

**Expected:**
- Zero ruff violations
- Zero mypy errors
- All tests pass, coverage does not drop
- No circular imports (`common` ← `sc2`/`aoe2`, never the reverse)

---

## Files-Changed Summary

| File | Action | Step |
|------|--------|------|
| `src/rts_predict/common/db.py` | NEW | 1 |
| `src/rts_predict/common/db_cli.py` | NEW | 2 |
| `src/rts_predict/sc2/config.py` | MODIFIED (additive) | 3 |
| `src/rts_predict/aoe2/config.py` | MODIFIED (additive) | 4 |
| `src/rts_predict/sc2/cli.py` | MODIFIED | 5 |
| `src/rts_predict/aoe2/cli.py` | NEW | 6 |
| `src/rts_predict/aoe2/tests/__init__.py` | NEW (empty) | 6 |
| `pyproject.toml` | MODIFIED | 7 |
| `tests/test_common_db.py` | NEW | 8 |
| `tests/test_common_db_cli.py` | NEW | 9 |
| `src/rts_predict/aoe2/tests/test_cli.py` | NEW | 10 |
| `src/rts_predict/sc2/tests/test_cli.py` | MODIFIED (additive) | 11 |
| `src/rts_predict/common/CONTRACT.md` | MODIFIED | 12 |
| `CHANGELOG.md` | MODIFIED | 13 |

**Total: 14 files (6 new, 8 modified), 14 steps, 20 new tests.**

---

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Import cycle `common` ↔ `sc2`/`aoe2` | Low | `common/db.py` imports zero game packages |
| Breaking existing `_connect_db()` callers | None | `_connect_db()` untouched in this PR |
| `poetry install` needed after entrypoint change | Certain | Step 7 includes `poetry install` |
| AoE2 `db tables` returns `[]` (no DB yet) | Expected | `DuckDBClient` creates parent dirs; empty result is valid |
| mypy strictness on `duckdb` types | Low | `ignore_missing_imports = true` already set |

---

## Gate Condition

All of the following must be true before opening the PR:

1. `poetry run sc2 db --help` lists `query`, `tables`, `schema`
2. `poetry run aoe2 db --help` lists same with `--dataset aoe2companion|aoestats`
3. `poetry run aoe2 --help` shows top-level help
4. All existing SC2 tests pass unchanged
5. 20 new tests pass (9 + 6 + 3 + 2)
6. `poetry run ruff check src/ tests/` — zero violations
7. `poetry run mypy src/rts_predict/` — zero errors
8. No circular imports between `common/`, `sc2/`, `aoe2/`
