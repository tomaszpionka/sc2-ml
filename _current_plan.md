# Plan: Consolidate Data Into Game-Specific Source Packages

## Context

All data currently lives outside the repo (`~/duckdb_work/`, `~/Downloads/SC2_Replays/`), creating permission complexity and fragile hardcoded paths. Instead of a top-level `data/` directory (which duplicates the per-game namespace), place raw, staging, db, and tmp directories directly under each game's existing `data/` subpackage, scoped by dataset name. Simpler, no new top-level dir, Occam's razor.

## Target Structure

```
src/rts_predict/sc2/data/
├── sc2egset/                     # dataset-scoped directory
│   ├── raw/
│   │   ├── README.md             # describes contents (tracked)
│   │   └── <tournament_dirs>/    # gitignored bulk data
│   ├── staging/
│   │   ├── README.md             # describes contents (tracked)
│   │   ├── in_game_events/       # Path B parquet batches
│   │   │   └── .gitkeep
│   │   └── in_game_processing_manifest.json  # gitignored
│   ├── db/
│   │   ├── .gitkeep
│   │   └── db.duckdb             # gitignored
│   └── tmp/
│       └── .gitkeep
├── samples/          # existing development reference (unchanged)
├── tests/            # existing (unchanged)
├── README.md         # existing (update path refs)
├── __init__.py       # existing
├── ingestion.py      # existing (paths from config)
├── ...               # other existing modules
```

No top-level `data/` directory at repo root. `samples/` stays at `data/samples/` — it's a committed development reference (slimmed JSON fixture + script), not a dataset artifact.

## Implementation Steps

### Step 1: Create directory scaffold

**Create empty files:**
- `src/rts_predict/sc2/data/sc2egset/staging/in_game_events/.gitkeep`
- `src/rts_predict/sc2/data/sc2egset/db/.gitkeep`
- `src/rts_predict/sc2/data/sc2egset/tmp/.gitkeep`

**Create with content:**

`src/rts_predict/sc2/data/sc2egset/raw/README.md`:
```markdown
# SC2EGSet — Raw Replays

SC2EGSet tournament replay files as JSON. Each subdirectory is a tournament:

    raw/
    ├── 2016_IEM_10_Taipei/
    │   ├── 2016_IEM_10_Taipei_data/
    │   │   ├── <hash>.SC2Replay.json
    │   │   └── ...
    │   └── map_foreign_to_english_mapping.json
    └── ...

~22K files across 50 tournaments. **NEVER modify** — treat as immutable source.
```

`src/rts_predict/sc2/data/sc2egset/staging/README.md`:
```markdown
# SC2EGSet — Staging

Intermediate artifacts extracted from raw replays. Each subdirectory groups
a pipeline output:

| Directory | Source | Format |
|-----------|--------|--------|
| `in_game_events/` | Path B extraction (`run_in_game_extraction`) | Parquet batches |

All contents are reproducible from raw data. Safe to delete and re-extract.
```

### Step 2: Update `.gitignore`

After the existing DuckDB temp files section, add:

```gitignore
# ── Game-scoped data directories ──────────────────────────────────────────────
# Layout: data/<dataset>/{raw,staging,db,tmp}/
# Contents gitignored; only skeleton (.gitkeep, README.md) is tracked.
*.duckdb

# Un-ignore data/*/tmp/ (overrides the global tmp/ rule at line 216)
!**/data/*/tmp/
**/data/*/tmp/*
!**/data/*/tmp/.gitkeep

**/data/*/raw/**/*
!**/data/*/raw/README.md

**/data/*/staging/**/*
!**/data/*/staging/README.md
!**/data/*/staging/**/.gitkeep

**/data/*/db/*
!**/data/*/db/.gitkeep
```

Key details:
- `**/data/*/` matches any dataset directory under any game's `data/`
- `raw/**/*` and `staging/**/*` use recursive glob to handle nested subdirectories
- README.md tracked in `raw/` and `staging/` (replaces .gitkeep role)
- `.gitkeep` tracked in `staging/*/` subdirs, `db/`, and `tmp/`
- Manifest at `staging/in_game_processing_manifest.json` is gitignored by the `staging/**/*` rule
- `*.duckdb` is intentionally global — DuckDB binaries should never be committed (tests use `:memory:`)
- The `tmp/` rule at line 216 ignores all `tmp/` dirs. The `!**/data/*/tmp/` negation un-ignores the directory, `**/data/*/tmp/*` re-ignores contents, `!**/data/*/tmp/.gitkeep` exempts the skeleton file
- Must verify with `git check-ignore -v` after writing

### Step 3: Update `config.py`

**File:** [config.py](src/rts_predict/sc2/config.py) (lines 3–18)

Replace with:
```python
# ── Project paths ──────────────────────────────────────────────────────────────
GAME_DIR: Path = Path(__file__).resolve().parent                # src/rts_predict/sc2/
ROOT_DIR: Path = GAME_DIR.parent.parent.parent                  # repo root
DATA_DIR: Path = GAME_DIR / "data"                              # src/rts_predict/sc2/data/
DATASET_DIR: Path = DATA_DIR / "sc2egset"                       # src/rts_predict/sc2/data/sc2egset/
REPORTS_DIR: Path = GAME_DIR / "reports"
DB_FILE: Path = DATASET_DIR / "db" / "db.duckdb"

# DuckDB configuration
DUCKDB_TEMP_DIR: Path = DATASET_DIR / "tmp"

# Raw replay files location
REPLAYS_SOURCE_DIR: Path = DATASET_DIR / "raw"

# ── In-game data (Path B) ─────────────────────────────────────────────────────
IN_GAME_PARQUET_DIR: Path = DATASET_DIR / "staging" / "in_game_events"
IN_GAME_MANIFEST_PATH: Path = DATASET_DIR / "staging" / "in_game_processing_manifest.json"
```

Changes:
- **Add `DATASET_DIR`** — scopes all data to the SC2EGSet dataset
- **Add `DATA_DIR`** — single base path for the data subtree
- `DB_FILE`: `~/duckdb_work/test_sc2.duckdb` → `DATASET_DIR / "db" / "db.duckdb"`
- `DUCKDB_TEMP_DIR`: `~/duckdb_work/tmp` → `DATASET_DIR / "tmp"`
- `REPLAYS_SOURCE_DIR`: `~/Downloads/SC2_Replays` → `DATASET_DIR / "raw"`
- `IN_GAME_PARQUET_DIR`: `~/duckdb_work/in_game_parquet` → `DATASET_DIR / "staging" / "in_game_events"`
- `IN_GAME_MANIFEST_PATH`: `GAME_DIR / "in_game_processing_manifest.json"` → `DATASET_DIR / "staging" / "in_game_processing_manifest.json"`
- **Remove `IN_GAME_DB_PATH`** — dead code, never imported anywhere (confirmed via grep)

### Step 4: Add `mkdir` safety nets

**4a. [ingestion.py](src/rts_predict/sc2/data/ingestion.py)** — Add `DUCKDB_TEMP_DIR.mkdir(parents=True, exist_ok=True)` at top of `move_data_to_duck_db()` (before the SET queries loop).

**4b. [cli.py](src/rts_predict/sc2/cli.py)** — Add helper to replace three bare `duckdb.connect(str(DB_FILE))` calls:

```python
def _connect_db() -> duckdb.DuckDBPyConnection:
    """Open a connection to the SC2 DuckDB, creating parent dirs if needed."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_FILE))
```

### Step 5: Update documentation

**5a. [dev-constraints.md](.claude/dev-constraints.md)** — Replace "External Data" section:
```markdown
## Data Layout
All pipeline data lives under `data/<dataset>/` within each game's subpackage (gitignored contents, tracked skeleton):
- `src/rts_predict/sc2/data/sc2egset/raw/` — raw JSON replays (NEVER modify)
- `src/rts_predict/sc2/data/sc2egset/staging/in_game_events/` — in-game event Parquet files (reproducible)
- `src/rts_predict/sc2/data/sc2egset/db/db.duckdb` — main DuckDB database (reproducible)
- `src/rts_predict/sc2/data/sc2egset/tmp/` — DuckDB spill-to-disk temp directory
```

**5b. [CLAUDE.md](CLAUDE.md)** — Simplify permissions:
```markdown
**Ask first:** Reading outside repo
```
Remove the specific `~/duckdb_work/` and `~/Downloads/SC2_Replays/` references.

**5c. [data/README.md](src/rts_predict/sc2/data/README.md)** — Update path references to `src/rts_predict/sc2/data/sc2egset/raw/...`.

**5d. [ARCHITECTURE.md](ARCHITECTURE.md)** — Replace data subdirectory rows in game package contract table:
```markdown
| `data/<dataset>/raw/` | Raw source data (gitignored contents, README tracked) | Yes |
| `data/<dataset>/staging/` | Intermediate artifacts by type (gitignored, README tracked) | When extraction exists |
| `data/<dataset>/db/` | DuckDB database file (gitignored, `.gitkeep` tracked) | Yes |
| `data/<dataset>/tmp/` | DuckDB spill-to-disk directory (gitignored, `.gitkeep` tracked) | Yes |
```

### Step 6: Run verification

```bash
source .venv/bin/activate && poetry run ruff check src/ tests/
source .venv/bin/activate && poetry run mypy src/rts_predict/
source .venv/bin/activate && poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing
```

Then verify gitignore rules:
```bash
git check-ignore -v src/rts_predict/sc2/data/sc2egset/tmp/.gitkeep        # NOT ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/raw/README.md       # NOT ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/staging/README.md   # NOT ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/staging/in_game_events/.gitkeep  # NOT ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/db/.gitkeep         # NOT ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/db/db.duckdb        # SHOULD be ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/raw/test.json       # SHOULD be ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/tmp/somefile        # SHOULD be ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/staging/in_game_events/batch.parquet  # SHOULD be ignored
git check-ignore -v src/rts_predict/sc2/data/sc2egset/staging/in_game_processing_manifest.json  # SHOULD be ignored
```

### Step 7: User performs data migration (manual, post-merge)

```bash
cp -r ~/Downloads/SC2_Replays/* src/rts_predict/sc2/data/sc2egset/raw/
cp -r ~/duckdb_work/in_game_parquet/* src/rts_predict/sc2/data/sc2egset/staging/in_game_events/
cp ~/duckdb_work/test_sc2.duckdb src/rts_predict/sc2/data/sc2egset/db/db.duckdb
```

Verify: `poetry run sc2 explore --steps 1.1`

## What Does NOT Change

- **Tests**: All mock config constants via `@patch` / `monkeypatch.setattr` with `tmp_path`. Zero test changes.
- **`audit.py`, `exploration.py`, `processing.py`**: Import constants from config — values change transparently.
- **`samples/` directory**: Stays as-is — committed development reference (slimmed JSON fixture + script), not a dataset artifact.
- **`cli.py` / `ingestion.py`**: `_connect_db()` and `DUCKDB_TEMP_DIR.mkdir()` safety nets already handle arbitrary depth.

## Branch

`chore/consolidate-data-dirs` (Category C per CLAUDE.md workflow)

## Risk Notes

- **`tmp/` gitignore conflict**: Global `tmp/` (line 216) vs per-dataset negation. Verified via `git check-ignore` in Step 6.
- **`*.duckdb` global**: Also catches any DuckDB file in `src/` or `tests/`. Correct — tests use `:memory:`.
- **Disk space**: 22K JSON replays ~66GB. Symlinks are a viable alternative for raw data.
- **Manifest relocation**: `IN_GAME_MANIFEST_PATH` moves from `GAME_DIR` to `DATASET_DIR / "staging"`. Existing manifest file at old location becomes orphaned — user should delete or move it after migration.
