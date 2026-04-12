---
category: "B"
branch: "refactor/package-restructure"
date: "2026-04-12"
planner_model: "claude-opus-4-6"
---

# Category B Plan: Package Restructure — `games/<game>/datasets/<dataset>/`

## Scope

Restructure `src/rts_predict/` from concern-first (`<game>/data/<dataset>/`)
to entity-first (`games/<game>/datasets/<dataset>/{data,reports}`). Mirror
in `tests/rts_predict/`. Update all imports (68 statements), path constants
(40 constants across 2 config files), .gitignore patterns (15 data-path
rules), .claude/settings.json deny rules, 6 shell scripts, 3 sandbox
notebooks, and ~42 documentation files (~126 references).

**Impact inventory:** `temp/restructure_impact_inventory.md` (276 references
across 76 files, produced by grep scan).

## Problem Statement

The current `<game>/data/<dataset>/` structure forces the dataset name to
repeat as a child of both `data/` and `reports/`. This is the only
reporting/data structure in the project that isn't entity-first. Sandbox
already uses `<game>/<dataset>/`. The restructure aligns src/ with sandbox,
eliminates the repetition, and makes datasets the natural isolation boundary
for all concerns (data, reports, models, features — current and future).

## Assumptions & unknowns

- Raw data files (SC2: ~214GB rezipped, AoE2: ~13GB parquet) are gitignored,
  NOT git-tracked. Only .gitkeeps, READMEs, and Python modules are tracked.
- `git mv` moves tracked files only. Actual data requires filesystem `mv`.
- SC2 `*_data/` dirs have been rezipped as a safety precaution.
- `processing.py` is legacy (CLAUDE.md has a caution about it) — stays at
  game level, not dataset level.

## Execution Steps

### T01 — Update .gitignore + settings.json (MUST be first)

**Objective:** Update data-path patterns to match new structure BEFORE any
files move. Prevents 214GB of raw data from becoming untracked.

**Instructions:**
1. `.gitignore` — add new patterns alongside old ones (don't delete old yet):
   ```gitignore
   # New structure: datasets/*/data/{raw,staging,db,tmp}
   **/datasets/*/data/raw/**/*
   !**/datasets/*/data/raw/*/
   !**/datasets/*/data/raw/.gitkeep
   !**/datasets/*/data/raw/**/.gitkeep
   !**/datasets/*/data/raw/README.md
   **/datasets/*/data/staging/*
   !**/datasets/*/data/staging/README.md
   !**/datasets/*/data/staging/*/
   **/datasets/*/data/staging/*/*
   !**/datasets/*/data/staging/*/.gitkeep
   **/datasets/*/data/db/*
   !**/datasets/*/data/db/.gitkeep
   !**/datasets/*/data/db/schemas/
   !**/datasets/*/data/db/schemas/*.yaml
   **/datasets/*/data/tmp/*
   !**/datasets/*/data/tmp/.gitkeep
   **/datasets/*/api/*
   !**/datasets/*/api/.gitkeep
   ```
   Also update: `src/rts_predict/*/logs/` → add `src/rts_predict/games/*/logs/`
   And: `**/data/samples/raw/*` → add `**/datasets/*/data/samples/raw/*`
2. `.claude/settings.json` — update deny rules:
   ```json
   "Write(src/**/datasets/*/data/raw/**)",
   "Edit(src/**/datasets/*/data/raw/**)"
   ```
   Keep old rules temporarily (belt + suspenders).

**Verification:**
- `git status` shows no new untracked data files after the update
- Old patterns still match old paths (coexistence)

**File scope:** `.gitignore`, `.claude/settings.json`
**Read scope:** none

---

### T02 — git mv SC2 tracked files

**Objective:** Move all git-tracked SC2 files to the new structure.

**Instructions:**
1. Create target dirs:
   ```bash
   mkdir -p src/rts_predict/games/sc2/datasets/sc2egset/data/{raw,staging/in_game_events,db,tmp}
   mkdir -p src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition
   ```
2. git mv tracked files:
   - `git mv src/rts_predict/sc2/cli.py src/rts_predict/games/sc2/cli.py`
   - `git mv src/rts_predict/sc2/config.py src/rts_predict/games/sc2/config.py`
   - `git mv src/rts_predict/sc2/__init__.py src/rts_predict/games/sc2/__init__.py`
   - `git mv src/rts_predict/sc2/data/processing.py src/rts_predict/games/sc2/processing.py`
   - `git mv src/rts_predict/sc2/data/sc2egset/raw/README.md src/rts_predict/games/sc2/datasets/sc2egset/data/raw/README.md`
   - `git mv src/rts_predict/sc2/data/sc2egset/staging/README.md src/rts_predict/games/sc2/datasets/sc2egset/data/staging/README.md`
   - `git mv` all .gitkeep files to new locations
   - `git mv` entire reports tree: `sc2/reports/sc2egset/*` → `games/sc2/datasets/sc2egset/reports/`
3. Create new `__init__.py` files:
   - `src/rts_predict/games/__init__.py`
   - `src/rts_predict/games/sc2/datasets/__init__.py`
   - `src/rts_predict/games/sc2/datasets/sc2egset/__init__.py`
4. Delete old empty dirs and stale `__init__.py`:
   - `src/rts_predict/sc2/data/__init__.py` (was a package marker, no longer needed)
5. Do NOT move raw data files — they're gitignored and stay on disk.
   The filesystem move happens in T04.

**Verification:**
- `git status` shows renames, no deletions of data files
- `ls src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` exists

**File scope:** `src/rts_predict/sc2/` → `src/rts_predict/games/sc2/`
**Read scope:** none

---

### T03 — git mv AoE2 tracked files

**Objective:** Move all git-tracked AoE2 files to the new structure.

**Instructions:**
1. Create target dirs:
   ```bash
   mkdir -p src/rts_predict/games/aoe2/datasets/aoe2companion/data/{raw/{matches,leaderboards,profiles,ratings},db}
   mkdir -p src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition
   mkdir -p src/rts_predict/games/aoe2/datasets/aoestats/data/{raw/{matches,players,overview},db}
   mkdir -p src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition
   ```
2. git mv game-level files:
   - `git mv src/rts_predict/aoe2/cli.py src/rts_predict/games/aoe2/cli.py`
   - `git mv src/rts_predict/aoe2/config.py src/rts_predict/games/aoe2/config.py`
   - `git mv src/rts_predict/aoe2/__init__.py src/rts_predict/games/aoe2/__init__.py`
3. For each dataset (aoe2companion, aoestats):
   - git mv Python modules (acquisition.py, ingestion.py, types.py) to
     `datasets/<dataset>/` (sibling to data/, not inside it)
   - git mv `__init__.py` to `datasets/<dataset>/`
   - git mv api/ .gitkeep to `datasets/<dataset>/api/`
   - git mv raw/ README.md + .gitkeeps to `datasets/<dataset>/data/raw/`
   - git mv db/ .gitkeep to `datasets/<dataset>/data/db/`
   - git mv tmp/ .gitkeep to `datasets/<dataset>/data/tmp/` (if exists)
   - git mv entire reports tree to `datasets/<dataset>/reports/`
4. Create new `__init__.py` files:
   - `src/rts_predict/games/aoe2/datasets/__init__.py`
5. Delete old empty dirs and stale `__init__.py`:
   - `src/rts_predict/aoe2/data/__init__.py`

**Verification:**
- `git status` shows renames, no data file deletions
- Both datasets have acquisition.py accessible at new paths

**File scope:** `src/rts_predict/aoe2/` → `src/rts_predict/games/aoe2/`
**Read scope:** none

---

### T04 — Filesystem mv raw data + verify

**Objective:** Move the actual (gitignored) data files to the new directory
structure. This is a filesystem operation, not a git operation.

**Instructions:**
1. SC2 (rezipped — safe to move):
   ```bash
   # Move raw data (rezipped tournament dirs)
   mv src/rts_predict/sc2/data/sc2egset/raw/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/raw/ 2>/dev/null
   # Move staging data
   mv src/rts_predict/sc2/data/sc2egset/staging/in_game_events/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/staging/in_game_events/ 2>/dev/null
   # Move DuckDB
   mv src/rts_predict/sc2/data/sc2egset/db/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/db/ 2>/dev/null
   # Move tmp
   mv src/rts_predict/sc2/data/sc2egset/tmp/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/tmp/ 2>/dev/null
   ```
2. AoE2 companion (~9.2GB parquet):
   ```bash
   mv src/rts_predict/aoe2/data/aoe2companion/raw/matches/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/matches/ 2>/dev/null
   # Repeat for ratings/, leaderboards/, profiles/
   mv src/rts_predict/aoe2/data/aoe2companion/db/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/ 2>/dev/null
   mv src/rts_predict/aoe2/data/aoe2companion/api/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/api/ 2>/dev/null
   ```
3. AoE2 stats (~3.7GB parquet): same pattern.
4. SC2 logs: `mv src/rts_predict/sc2/logs src/rts_predict/games/sc2/logs`
5. Verify all data is accessible at new paths:
   ```bash
   ls src/rts_predict/games/sc2/datasets/sc2egset/data/raw/ | head -5
   ls src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/matches/ | head -3
   ls src/rts_predict/games/aoe2/datasets/aoestats/data/raw/matches/ | head -3
   ```
6. Verify .gitignore is working: `git status` shows NO new untracked data files.
7. Delete old empty directory trees:
   ```bash
   rm -rf src/rts_predict/sc2/
   rm -rf src/rts_predict/aoe2/
   ```

**Verification:**
- All 3 datasets' data accessible at new paths
- `git status` shows no untracked data files
- Old `src/rts_predict/sc2/` and `src/rts_predict/aoe2/` directories gone

**File scope:** filesystem only (gitignored data)
**Read scope:** none

---

### T05 — Restructure test mirror

**Objective:** Mirror the src/ restructure in tests/.

**Instructions:**
1. Create target dirs:
   ```bash
   mkdir -p tests/rts_predict/games/sc2/datasets/sc2egset
   mkdir -p tests/rts_predict/games/aoe2/datasets/{aoe2companion,aoestats}
   ```
2. git mv:
   - `tests/rts_predict/sc2/test_cli.py` → `tests/rts_predict/games/sc2/test_cli.py`
   - `tests/rts_predict/sc2/data/conftest.py` → `tests/rts_predict/games/sc2/datasets/sc2egset/conftest.py`
   - `tests/rts_predict/sc2/data/test_processing.py` → `tests/rts_predict/games/sc2/test_processing.py` (processing.py is at game level)
   - `tests/rts_predict/aoe2/test_cli.py` → `tests/rts_predict/games/aoe2/test_cli.py`
   - `tests/rts_predict/aoe2/data/aoe2companion/*` → `tests/rts_predict/games/aoe2/datasets/aoe2companion/`
   - `tests/rts_predict/aoe2/data/aoestats/*` → `tests/rts_predict/games/aoe2/datasets/aoestats/`
3. Create `__init__.py` at new levels.
4. Delete colocated test dirs in src/ (empty — just `__pycache__`):
   - `src/rts_predict/games/sc2/datasets/sc2egset/data/tests/` (if copied during move)
   - etc.
5. Delete old test dirs: `rm -rf tests/rts_predict/sc2/ tests/rts_predict/aoe2/`

**Verification:**
- `pytest --collect-only` finds all tests at new paths
- No test dirs inside src/

**File scope:** `tests/rts_predict/{sc2,aoe2}/` → `tests/rts_predict/games/`
**Read scope:** none

---

### T06 — Update config.py path constants

**Objective:** Rewrite both config files with correct `__file__`-relative
path derivation for the new structure.

**Instructions:**
1. `src/rts_predict/games/sc2/config.py`:
   ```python
   GAME_DIR = Path(__file__).resolve().parent           # games/sc2/
   ROOT_DIR = GAME_DIR.parent.parent.parent.parent      # 4 levels to repo root
   DATASETS_DIR = GAME_DIR / "datasets"
   DATASET_DIR = DATASETS_DIR / "sc2egset"
   DATA_DIR = DATASET_DIR / "data"
   REPORTS_DIR = DATASET_DIR / "reports"
   DATASET_ARTIFACTS_DIR = REPORTS_DIR / "artifacts"
   DB_FILE = DATA_DIR / "db" / "db.duckdb"
   DUCKDB_TEMP_DIR = DATA_DIR / "tmp"
   REPLAYS_SOURCE_DIR = DATA_DIR / "raw"
   IN_GAME_PARQUET_DIR = DATA_DIR / "staging" / "in_game_events"
   IN_GAME_MANIFEST_PATH = DATA_DIR / "staging" / "in_game_processing_manifest.json"
   MODELS_DIR = GAME_DIR / "models"
   ```
   Remove `DATASET_REPORTS_DIR` (redundant — `REPORTS_DIR` is already per-dataset).
2. `src/rts_predict/games/aoe2/config.py`:
   ```python
   GAME_DIR = Path(__file__).resolve().parent
   ROOT_DIR = GAME_DIR.parent.parent.parent.parent
   DATASETS_DIR = GAME_DIR / "datasets"
   AOE2COMPANION_DIR = DATASETS_DIR / "aoe2companion"
   AOE2COMPANION_DATA_DIR = AOE2COMPANION_DIR / "data"
   AOE2COMPANION_RAW_DIR = AOE2COMPANION_DATA_DIR / "raw"
   AOE2COMPANION_RAW_MATCHES_DIR = AOE2COMPANION_RAW_DIR / "matches"
   # ... (all 22 constants rebased from DATA_DIR to dataset/data/)
   AOE2COMPANION_REPORTS_DIR = AOE2COMPANION_DIR / "reports"
   AOE2COMPANION_ARTIFACTS_DIR = AOE2COMPANION_REPORTS_DIR / "artifacts"
   ```
   Remove `DATA_DIR` and `REPORTS_DIR` at game level (no longer exist).
3. Verify: `poetry run python -c "from rts_predict.games.sc2.config import REPLAYS_SOURCE_DIR; print(REPLAYS_SOURCE_DIR)"` resolves to correct path.

**Verification:**
- All path constants resolve to existing directories
- `poetry run sc2 --help` does not crash on import
- `poetry run aoe2 --help` does not crash on import

**File scope:** `src/rts_predict/games/sc2/config.py`, `src/rts_predict/games/aoe2/config.py`
**Read scope:** none

---

### T07 — Update all Python imports + pyproject.toml

**Objective:** Fix every import statement and entry point.

**Instructions:**
1. All `.py` files — systematic replacement:
   - `rts_predict.sc2.` → `rts_predict.games.sc2.`
   - `rts_predict.aoe2.` → `rts_predict.games.aoe2.`
   - `rts_predict.aoe2.data.aoe2companion.` → `rts_predict.games.aoe2.datasets.aoe2companion.`
   - `rts_predict.aoe2.data.aoestats.` → `rts_predict.games.aoe2.datasets.aoestats.`
   - `rts_predict.sc2.data.processing` → `rts_predict.games.sc2.processing`
   - String refs in tests (mock paths): same patterns
2. `src/rts_predict/common/notebook_utils.py:26`:
   `"rts_predict.{game}.config"` → `"rts_predict.games.{game}.config"`
3. `pyproject.toml`:
   - Line 10: `sc2 = "rts_predict.games.sc2.cli:main"`
   - Line 11: `aoe2 = "rts_predict.games.aoe2.cli:main"`
   - Mirror drift exemptions: update 3 paths
4. Sandbox notebooks (.py files — jupytext paired):
   - Update imports in all 3 `.py` files
   - Run `jupytext --sync` on each to update `.ipynb` pair
5. Shell scripts in `scripts/sc2egset/` — update all 6 hardcoded paths:
   `$REPO_ROOT/src/rts_predict/sc2/data/sc2egset/raw` →
   `$REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw`
6. Run full check suite:
   ```bash
   source .venv/bin/activate && poetry run pytest tests/ -v
   source .venv/bin/activate && poetry run ruff check src/ tests/
   source .venv/bin/activate && poetry run mypy src/rts_predict/
   poetry run python scripts/check_mirror_drift.py
   ```

**Verification:**
- pytest passes (all tests)
- ruff clean
- mypy clean
- mirror drift clean
- `poetry run sc2 --help` works
- `poetry run aoe2 --help` works

**File scope:** ~25 Python files, `pyproject.toml`, 6 shell scripts, 3 sandbox .py files
**Read scope:** none

---

### T08 — Update CLAUDE.md + agent definitions + rules

**Objective:** Update all path references in the Claude Code configuration layer.

**Instructions:**
1. `CLAUDE.md`: Key File Locations paths, Project Status
2. `.claude/agents/planner-science.md`: Data layout section (6 refs)
3. `.claude/agents/reviewer.md`: report artifact path (1 ref)
4. `.claude/dev-constraints.md`: data paths (4 refs)
5. `.claude/ml-protocol.md`: reports path (1 ref)
6. `.claude/rules/python-code.md`: import example, test tree example (2 refs)
7. `.claude/scientific-invariants.md`: INVARIANTS.md paths (2 refs)

**Verification:** `grep -rn "rts_predict/sc2\|rts_predict/aoe2" .claude/ CLAUDE.md`
returns zero matches (only `rts_predict/games/`)

**File scope:** 7 files in `.claude/` + `CLAUDE.md`
**Read scope:** none

---

### T09 — Update documentation + templates

**Objective:** Update all docs/, reports/, planning/ path references.

**Instructions:**
1. `docs/INDEX.md` — directory map table (2 refs)
2. `docs/TAXONOMY.md` — artifact path example (1 ref)
3. `docs/agents/AGENT_MANUAL.md` — example command (1 ref)
4. `docs/research/` — RESEARCH_LOG.md (6), RESEARCH_LOG_ENTRY.md (4), ROADMAP.md (3)
5. `docs/templates/` — dag_template (3), notebook_template (1), plan_template (1), raw_data_readme_template (6)
6. `reports/research_log.md` — dataset log links (6 refs)
7. `reports/README.md` — dataset log paths (2 refs)
8. Per-dataset files (move WITH the restructure, but internal refs need updating):
   - 3x `PHASE_STATUS.yaml` — dataset_roadmap self-reference
   - 3x `ROADMAP.md` — README reference
   - 3x `research_log.md` — artifact paths
   - 3x `raw/README.md` — heavily path-dependent (8+ refs each)
   - 3x artifact `01_01_01_file_inventory.md` — absolute path in header
9. Game READMEs — rewrite completely (paths table)
10. `thesis/THESIS_STRUCTURE.md` — ROADMAP reference (1 ref)
11. `LATER.md` — update deferred items
12. Old .gitignore patterns — delete the old `**/data/*/` patterns now that
    new `**/datasets/*/data/` patterns are confirmed working

**Verification:** `grep -rn "rts_predict/sc2\|rts_predict/aoe2" --include="*.md" --include="*.yaml" . | grep -v CHANGELOG | grep -v temp/` returns zero matches

**File scope:** ~42 documentation files
**Read scope:** none

---

### T10 — Clean up .gitignore + final verification

**Objective:** Remove old .gitignore patterns, run full verification.

**Instructions:**
1. Delete old .gitignore patterns (`**/data/*/raw/**/*` etc.) now that
   new patterns are confirmed working and all data is at new paths.
2. Delete old settings.json deny rules (keep only new ones).
3. Run comprehensive verification:
   ```bash
   # No old paths in code
   grep -rn "rts_predict\.sc2\|rts_predict\.aoe2" --include="*.py" . | grep -v .venv
   # No old paths in docs (excluding CHANGELOG)
   grep -rn "rts_predict/sc2\|rts_predict/aoe2" --include="*.md" --include="*.yaml" . | grep -v CHANGELOG | grep -v temp/
   # Tests pass
   source .venv/bin/activate && poetry run pytest tests/ -v
   # Data is still gitignored
   git status | grep -c "raw/\|staging/\|\.parquet\|\.json" || echo "0 data files exposed"
   ```

**Verification:**
- Zero old-path matches in code and docs
- pytest passes
- Zero data files exposed in git status

**File scope:** `.gitignore`, `.claude/settings.json`
**Read scope:** none

---

### T11 — CHANGELOG

**Objective:** Document the restructure.

**Instructions:**
1. Under `[Unreleased]`:
   - Changed: Package structure from `src/rts_predict/<game>/data/<dataset>/`
     to `src/rts_predict/games/<game>/datasets/<dataset>/{data,reports}`
   - Changed: All imports updated (68 statements across 18 files)
   - Changed: Both config.py files rewritten with new path derivation
   - Changed: .gitignore patterns updated for new data paths
   - Changed: 6 shell scripts, 3 sandbox notebooks, ~42 docs updated
   - Removed: Colocated test dirs inside src/ (were empty)

**File scope:** `CHANGELOG.md`
**Read scope:** none

---

## File Manifest

| File | Action |
|------|--------|
| `.gitignore` | Update (new patterns, then remove old) |
| `.claude/settings.json` | Update deny rules |
| `src/rts_predict/games/` | Create (entire new tree) |
| `src/rts_predict/sc2/` | Delete (after git mv) |
| `src/rts_predict/aoe2/` | Delete (after git mv + filesystem mv) |
| `tests/rts_predict/games/` | Create (mirror) |
| `tests/rts_predict/sc2/` | Delete (after git mv) |
| `tests/rts_predict/aoe2/` | Delete (after git mv) |
| `src/rts_predict/games/sc2/config.py` | Rewrite paths |
| `src/rts_predict/games/aoe2/config.py` | Rewrite paths |
| `pyproject.toml` | Update entry points + exemptions |
| `src/rts_predict/common/notebook_utils.py` | Update template string |
| `scripts/sc2egset/*.sh` (6 files) | Update hardcoded paths |
| `scripts/check_mirror_drift.py` | Verify (may not need changes) |
| `sandbox/**/01_01_01_file_inventory.py` (3 files) | Update imports |
| `CLAUDE.md` + `.claude/` (7 files) | Update paths |
| ~42 documentation files | Update path references |
| `CHANGELOG.md` | Update |

---

## Gate Condition

- `src/rts_predict/sc2/` does not exist
- `src/rts_predict/aoe2/` does not exist
- `src/rts_predict/games/sc2/datasets/sc2egset/data/raw/` contains data
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/matches/` contains data
- `src/rts_predict/games/aoe2/datasets/aoestats/data/raw/matches/` contains data
- `poetry run pytest tests/ -v` passes
- `poetry run ruff check src/ tests/` clean
- `poetry run mypy src/rts_predict/` clean
- `poetry run sc2 --help` works
- `poetry run aoe2 --help` works
- `poetry run python scripts/check_mirror_drift.py` exits 0
- `grep -rn "rts_predict\.sc2\|rts_predict\.aoe2" --include="*.py" . | grep -v .venv` returns zero
- `grep -rn "rts_predict/sc2\|rts_predict/aoe2" --include="*.md" --include="*.yaml" . | grep -v CHANGELOG | grep -v temp/` returns zero
- `git status` shows no untracked data files (gitignore working)
- `.claude/settings.json` deny rules match new data paths

---

## Out of Scope

- Sandbox directory restructure (already uses `<game>/<dataset>/`, no change)
- Artifact path flattening (separate future decision)
- PHASES.md consolidation (separate chore, already planned)
- New `models/` or `features/` directories under datasets (future Phase 02+)

---

## Rollback Strategy

If migration fails mid-way:
```bash
git checkout -- .          # Restore all tracked files to pre-move state
git clean -fd src/rts_predict/games/  # Remove new dirs
# Data files: if already filesystem-moved, reverse:
# mv src/rts_predict/games/sc2/datasets/sc2egset/data/raw/* \
#    src/rts_predict/sc2/data/sc2egset/raw/
```

Data is safe because: (a) SC2 is rezipped, (b) git never touches gitignored
files, (c) filesystem mv is reversible.

---

## Suggested Execution Graph

```yaml
dag_id: "dag_package_restructure"
plan_ref: "planning/current_plan.md"
category: "B"
branch: "refactor/package-restructure"
base_ref: "master"
default_isolation: "shared_branch"

jobs:
  - job_id: "J01"
    name: "Package restructure"

    task_groups:
      - group_id: "TG01"
        name: "Safety + file moves"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T01"
            name: "Update .gitignore + settings.json"
            spec_file: "planning/specs/spec_01_gitignore.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - ".gitignore"
              - ".claude/settings.json"
            depends_on: []
          - task_id: "T02"
            name: "git mv SC2 tracked files"
            spec_file: "planning/specs/spec_02_mv_sc2.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "src/rts_predict/games/sc2/"
            depends_on: ["T01"]
          - task_id: "T03"
            name: "git mv AoE2 tracked files"
            spec_file: "planning/specs/spec_03_mv_aoe2.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "src/rts_predict/games/aoe2/"
            depends_on: ["T01"]
          - task_id: "T04"
            name: "Filesystem mv raw data + verify"
            spec_file: "planning/specs/spec_04_mv_data.md"
            agent: "executor"
            parallel_safe: false
            file_scope: []
            depends_on: ["T02", "T03"]
          - task_id: "T05"
            name: "Restructure test mirror"
            spec_file: "planning/specs/spec_05_tests.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "tests/rts_predict/games/"
            depends_on: ["T02", "T03"]

      - group_id: "TG02"
        name: "Code updates"
        depends_on: ["TG01"]
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T06"
            name: "Rewrite config.py path constants"
            spec_file: "planning/specs/spec_06_config.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "src/rts_predict/games/sc2/config.py"
              - "src/rts_predict/games/aoe2/config.py"
            depends_on: []
          - task_id: "T07"
            name: "Update imports + pyproject + notebooks + scripts"
            spec_file: "planning/specs/spec_07_imports.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "pyproject.toml"
              - "src/rts_predict/common/notebook_utils.py"
              - "scripts/sc2egset/"
              - "sandbox/"
            depends_on: ["T06"]

      - group_id: "TG03"
        name: "Documentation + cleanup + CHANGELOG"
        depends_on: ["TG02"]
        review_gate:
          agent: "reviewer"
          scope: "cumulative"
          on_blocker: "halt"
        tasks:
          - task_id: "T08"
            name: "Update CLAUDE.md + agent defs + rules"
            spec_file: "planning/specs/spec_08_claude_agents.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "CLAUDE.md"
              - ".claude/"
            depends_on: []
          - task_id: "T09"
            name: "Update docs + templates + reports"
            spec_file: "planning/specs/spec_09_docs.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "docs/"
              - "reports/"
              - "thesis/"
              - "LATER.md"
            depends_on: []
          - task_id: "T10"
            name: "Clean up .gitignore + final verification"
            spec_file: "planning/specs/spec_10_cleanup.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - ".gitignore"
              - ".claude/settings.json"
            depends_on: ["T08", "T09"]
          - task_id: "T11"
            name: "Update CHANGELOG"
            spec_file: "planning/specs/spec_11_changelog.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "CHANGELOG.md"
            depends_on: ["T10"]

final_review:
  agent: "reviewer-deep"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```
