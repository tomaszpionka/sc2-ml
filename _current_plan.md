# Chore: Repository Reorganization — `sc2ml` to `rts_predict` Package Structure

## Context

The repository is sanitized from legacy ML code (PR #23) and ready for structural
standardization. The current layout has SC2-specific artifacts scattered at the
repo root (`reports/`, `models/`, `logs/`, `in_game_processing_manifest.json`) and
the Python package named `sc2ml` — which doesn't scale to the planned AoE2
comparative study. This reorganization:

1. Renames the package from `sc2ml` to `rts_predict.sc2` under a unified namespace
2. Moves SC2-specific artifacts into the game package directory
3. Creates the mirrored structure for AoE2 and shared code (placeholders)
4. Updates every live reference in tracked `.md` and `.py` files
5. Adds per-game phase tracking (`PHASE_STATUS.yaml`), thesis review handoff
   infrastructure (`REVIEW_QUEUE.md`, `.claude/chat-handoff.md`), a shared-code
   contract (`common/CONTRACT.md`), and a formal `ARCHITECTURE.md`
6. Sets the foundation for AoE2 integration and paired Claude Code + Claude Chat
   thesis writing workflow

**Category C — chore/maintenance**

---

## Branch

`chore/repo-reorganization`

---

## Target Structure

```
rts-outcome-prediction/
├── .claude/
│   ├── aoe2-plan.md                    # Updated: minor ref fixes
│   ├── chat-handoff.md                 # NEW: Pass 1→2 handoff protocol
│   ├── coding-standards.md             # Updated: paths, commands
│   ├── git-workflow.md                 # Updated: paths, commands
│   ├── ml-protocol.md                  # Updated: report paths
│   ├── project-architecture.md         # Major rewrite
│   ├── python-workflow.md              # Updated: commands
│   ├── scientific-invariants.md        # Updated: roadmap filename
│   ├── testing-standards.md            # Updated: paths, commands
│   ├── thesis-writing.md              # Updated: report paths, Pass 1/2 refs
│   └── settings.local.json             # No change
├── .gitignore                          # Updated: artifact paths under rts_predict
├── ARCHITECTURE.md                     # NEW: package layout, game contract, extension guide
├── CHANGELOG.md                        # Updated: [Unreleased] documents this chore
├── CLAUDE.md                           # Major rewrite: all paths, commands, layout
├── README.md                           # Updated: commands, paths
├── _current_plan.md                    # Overwritten with this plan
├── pyproject.toml                      # Updated: package config, scripts, tools
├── poetry.lock                         # Regenerated
│
├── reports/                            # Cross-cutting research artifacts
│   └── research_log.md                 # Unified narrative (tagged [SC2]/[AoE2]/[CROSS])
│
├── thesis/                             # Cross-cutting thesis (no structural changes)
│   ├── THESIS_STRUCTURE.md             # Updated: SC2ML → SC2, report path refs
│   ├── WRITING_STATUS.md               # No change
│   ├── chapters/
│   │   ├── 01_introduction.md
│   │   ├── 02_theoretical_background.md
│   │   ├── 03_related_work.md
│   │   ├── 04_data_and_methodology.md
│   │   ├── 05_experiments_and_results.md
│   │   ├── 06_discussion.md
│   │   ├── 07_conclusions.md
│   │   └── REVIEW_QUEUE.md             # NEW: Pass 1→2 handoff tracker
│   ├── figures/
│   ├── tables/
│   └── references.bib
│
├── tests/                              # Root integration/infra tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── helpers.py
│   └── test_mps.py
│
└── src/
    └── rts_predict/                    # Top-level Python package
        ├── __init__.py                 # __version__ = "0.14.0", package docstring
        │
        ├── sc2/                        # StarCraft II game package
        │   ├── __init__.py             # Game-specific docstring only (NO __version__)
        │   ├── cli.py
        │   ├── config.py              # GAME_DIR, ROOT_DIR, REPORTS_DIR centralized
        │   ├── PHASE_STATUS.yaml       # NEW: machine-readable phase progress
        │   ├── data/
        │   │   ├── __init__.py
        │   │   ├── ingestion.py
        │   │   ├── processing.py
        │   │   ├── exploration.py     # Remove local REPORTS_DIR, import from config
        │   │   ├── audit.py           # Remove local REPORTS_DIR, import from config
        │   │   ├── schemas.py
        │   │   ├── samples/
        │   │   │   ├── README.md
        │   │   │   ├── SC2EGSet_datasheet.pdf
        │   │   │   ├── process_sample.py
        │   │   │   ├── raw/
        │   │   │   └── processed/
        │   │   ├── sc2_events_extraction.sh
        │   │   ├── sc2_extract_in_game_events.sh
        │   │   └── tests/
        │   │       ├── __init__.py
        │   │       ├── conftest.py
        │   │       ├── test_audit.py
        │   │       ├── test_exploration.py
        │   │       ├── test_ingestion.py
        │   │       └── test_processing.py
        │   ├── reports/                # SC2-specific phase artifacts (tracked)
        │   │   ├── SC2_THESIS_ROADMAP.md   # Renamed from SC2ML_
        │   │   ├── 00_full_ingestion_log.txt
        │   │   ├── 00_join_validation.md
        │   │   ├── 00_map_translation_coverage.csv
        │   │   ├── 00_path_a_smoke_test.md
        │   │   ├── 00_path_b_extraction_log.txt
        │   │   ├── 00_replay_id_spec.md
        │   │   ├── 00_source_audit.json
        │   │   ├── 00_tournament_name_validation.txt
        │   │   ├── 01_apm_mmr_audit.md
        │   │   ├── 01_corpus_summary.json
        │   │   ├── 01_duplicate_detection.md
        │   │   ├── 01_duration_distribution.csv
        │   │   ├── 01_duration_distribution_full.png
        │   │   ├── 01_duration_distribution_zoomed.png
        │   │   ├── 01_event_count_distribution.csv
        │   │   ├── 01_event_density_by_tournament.csv
        │   │   ├── 01_event_density_by_year.csv
        │   │   ├── 01_event_type_inventory.csv
        │   │   ├── 01_parse_quality_by_tournament.csv
        │   │   ├── 01_parse_quality_summary.md
        │   │   ├── 01_patch_landscape.csv
        │   │   ├── 01_player_count_anomalies.csv
        │   │   ├── 01_playerstats_sampling_check.csv
        │   │   ├── 01_result_field_audit.md
        │   │   ├── sanity_validation.md
        │   │   └── archive/           # Old roadmap versions (18+ files)
        │   ├── models/                # SC2 model artifacts (gitignored)
        │   │   └── results/
        │   ├── logs/                  # SC2 pipeline logs (gitignored)
        │   └── tests/                 # SC2 package-root tests (cli, validation)
        │       ├── __init__.py
        │       └── test_cli.py
        │
        ├── aoe2/                      # AoE2 game package (placeholder)
        │   ├── __init__.py            # NEW: docstring-only placeholder
        │   ├── PHASE_STATUS.yaml      # NEW: placeholder, current_phase: null
        │   └── .gitkeep               # Mirrors sc2/ when populated
        │
        └── common/                    # Shared evaluation framework (future)
            ├── __init__.py            # NEW: docstring-only placeholder
            └── CONTRACT.md            # NEW: defines shared vs game-specific boundary
```

---

## Execution Steps

### Step 0 — Create branch

```bash
git checkout -b chore/repo-reorganization
```

---

### Step 1 — Create new directory structure and move Python package

Use `git mv` for all tracked file moves to preserve history.

```bash
# Create rts_predict namespace package
mkdir -p src/rts_predict

# Move the entire sc2ml package to rts_predict/sc2
git mv src/sc2ml src/rts_predict/sc2

# Move aoe2 placeholder
git mv src/aoe2 src/rts_predict/aoe2

# Create common placeholder
mkdir -p src/rts_predict/common
touch src/rts_predict/common/.gitkeep
git add src/rts_predict/common/.gitkeep
```

Create `src/rts_predict/__init__.py`:
```python
"""RTS Predict: Comparative ML analysis for RTS game result prediction."""

__version__ = "0.14.0"
```

---

### Step 2 — Move SC2 reports into game package

```bash
# Create target directory
mkdir -p src/rts_predict/sc2/reports

# Move all phase artifacts
git mv reports/00_* src/rts_predict/sc2/reports/
git mv reports/01_* src/rts_predict/sc2/reports/

git mv reports/sanity_validation.md src/rts_predict/sc2/reports/

# Rename roadmap during move
git mv reports/SC2ML_THESIS_ROADMAP.md src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md

# Move archive
git mv reports/archive src/rts_predict/sc2/reports/archive

# Verify research_log.md remains at reports/
# (reports/ dir stays with just research_log.md)
```

Create gitignored artifact directories:
```bash
mkdir -p src/rts_predict/sc2/models/results
mkdir -p src/rts_predict/sc2/logs
```

---

### Step 2.5 — Create per-game PHASE_STATUS.yaml files

Create `src/rts_predict/sc2/PHASE_STATUS.yaml`:
```yaml
# SC2 phase progress — machine-readable status for Claude Code session start
# Updated after each phase gate is met. Claude Code reads this FIRST to know
# where the project stands without parsing the full roadmap.
#
# Statuses: not_started | in_progress | complete
# gate_date: ISO date when the gate condition was verified
# notes: brief context for the current state

game: sc2
roadmap: src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md
current_phase: 1  # The phase currently being worked on (highest non-complete)

phases:
  0:
    name: "Ingestion audit and raw table design"
    status: complete
    gate_date: "2026-04-03"
    notes: "22,390 replays, 62M tracker rows, 609M game events, 188 maps. All 5 gate conditions met."
  1:
    name: "Corpus inventory and data exploration"
    status: in_progress
    started: "2026-04-04"
    notes: "Steps 1.1–1.7 complete (16 report artifacts produced). Step 1.8 (game settings and field completeness audit) pending."
  2:
    name: "Player identity resolution"
    status: not_started
  3:
    name: "Games table construction"
    status: not_started
  4:
    name: "In-game statistics profiling"
    status: not_started
  5:
    name: "Meta-game analysis"
    status: not_started
  6:
    name: "Data cleaning"
    status: not_started
  7:
    name: "Feature engineering"
    status: not_started
  8:
    name: "Train/val/test split"
    status: not_started
  9:
    name: "Baselines"
    status: not_started
  10:
    name: "Model training and evaluation"
    status: not_started
```

Create `src/rts_predict/aoe2/PHASE_STATUS.yaml`:
```yaml
# AoE2 phase progress — placeholder
# Will be populated when AoE2 roadmap is created after SC2 pipeline is complete.

game: aoe2
roadmap: null  # Not yet created
current_phase: null

phases: {}
```

---

### Step 2.6 — Create shared-code contract

Create `src/rts_predict/common/CONTRACT.md`:
```markdown
# Common Package Contract

This package contains code shared across all game-specific packages (SC2, AoE2).
The boundary rule is simple: if it's game-agnostic, it goes here. If it requires
knowledge of a specific game's mechanics, data format, or domain, it goes in the
game package.

## What belongs here

- **Evaluation metrics**: log-loss, AUC-ROC, Brier score, calibration curves,
  bootstrap confidence intervals. These are identical across games.
- **Split validation utilities**: temporal leakage checks, class balance verification,
  subgroup distribution comparison. Game-agnostic by design.
- **Report formatting**: markdown table generation, figure export helpers,
  research log entry templates.
- **Cross-game comparison protocol**: the implementation of Scientific Invariant #10
  (shared evaluation protocol, identical metrics, matched experimental conditions).
- **Base classes / interfaces**: abstract feature group, abstract data pipeline step,
  if these patterns emerge and prove useful. Do not create them speculatively.

## What does NOT belong here

- Data ingestion (game-specific file formats: SC2Replay.json vs AoE2 recorded games)
- Feature engineering (races vs civilizations, APM semantics, economy models differ)
- Cleaning rules (game-specific anomalies, duration thresholds, player ID schemes)
- CLI entry points (each game has its own CLI)
- Config (DB paths, replay directories, game constants)
- Rating systems implementation (shared in principle, but calibration and
  cold-start handling may differ per game — start in game packages, extract
  to common only if implementations converge)

## When to extract to common

Do NOT pre-emptively create abstractions. The rule is:
1. Build it in the first game package (SC2)
2. Build it again in the second game package (AoE2)
3. If the implementations are >80% identical, extract to common
4. If they diverge meaningfully, keep them separate with a comment explaining why

This avoids premature abstraction, which is worse than duplication in a
two-game thesis project.
```

Create `src/rts_predict/common/__init__.py`:
```python
"""Shared evaluation and utility code for cross-game RTS prediction analysis."""
```

Create `src/rts_predict/aoe2/__init__.py`:
```python
"""Age of Empires II game package — placeholder for future integration."""
```

---

### Step 2.7 — Create thesis review handoff infrastructure

Create `thesis/chapters/REVIEW_QUEUE.md`:
```markdown
# Thesis Review Queue — Pass 1 → Pass 2 Handoff

This file tracks thesis sections that Claude Code has drafted (Pass 1) and
that need external validation in Claude Chat (Pass 2).

## Workflow

1. Claude Code drafts a section and runs the Critical Review Checklist
   (see `.claude/thesis-writing.md`)
2. Claude Code plants `[REVIEW: ...]` and other inline flags
3. Claude Code appends an entry to the Pending table below
4. User brings the section + referenced artifacts to Claude Chat for Pass 2
5. After Pass 2 corrections are applied, move the entry to Completed

## Pending Pass 2 reviews

| Section | Chapter file | Drafted date | Flag count | Key artifacts | Pass 2 status |
|---------|-------------|-------------|------------|---------------|---------------|
| *(none yet)* | | | | | |

## Completed Pass 2 reviews

| Section | Reviewed date | Reviewer notes |
|---------|--------------|----------------|
| *(none yet)* | | |

## How to use this in Claude Chat

When bringing a section for Pass 2 review, provide Claude Chat with:
1. The section text from `thesis/chapters/XX_*.md`
2. The report artifacts listed in the "Key artifacts" column
3. The specific `[REVIEW: ...]` flags from the draft
4. Any `[NEEDS CITATION]` flags (Claude Chat will search the literature)

Claude Chat will return: resolved flags, suggested citations, methodology
alignment checks, and any corrections to statistical interpretation.
```

Create `.claude/chat-handoff.md`:
```markdown
# Claude Code → Claude Chat Handoff Protocol

This file tells Claude Code what to prepare when a session produces work
that needs Claude Chat review (Pass 2 of the thesis writing workflow).

---

## When to prepare a handoff

After any Category F (thesis writing) session where:
- A section was drafted or revised
- `[REVIEW: ...]` flags were planted
- Statistical interpretations were made that need literature validation
- Methodological choices were made that might diverge from field norms

## What Claude Code must produce at end of session

At the end of any session that triggers a handoff, Claude Code appends a
structured summary block to the session output. This block is what the user
copy-pastes into Claude Chat. Format:

```
## Chat Handoff Summary

### Section drafted
- File: `thesis/chapters/XX_*.md`
- Section: §X.Y.Z — [title]
- Status: DRAFTED (first draft / revision)

### Inline flags planted
1. `[REVIEW: ...]` — [line number or context] — [what needs checking]
2. `[NEEDS CITATION]` — [line number or context] — [what claim needs a source]
3. `[NEEDS JUSTIFICATION]` — [line number or context] — [what threshold/parameter]
4. `[UNVERIFIED: source?]` — [line number or context] — [what number is untraceable]

### Report artifacts referenced
- `src/rts_predict/sc2/reports/XX_artifact.md` — [what data it contains]
- `src/rts_predict/sc2/reports/XX_artifact.csv` — [what data it contains]

### Specific questions for Claude Chat
1. [Concrete question about methodology, interpretation, or literature]
2. [Another concrete question]

### Numbers verified against artifacts (Pass 1 checklist item 1)
- [number] ← [artifact file, line/key] ✓
- [number] ← [artifact file, line/key] ✓
```

## What Claude Code must NOT do

- Do not attempt to resolve `[REVIEW: ...]` flags — these require literature access
- Do not invent citations — plant `[NEEDS CITATION]` and let Claude Chat find them
- Do not guess whether a methodology is standard — flag it for review
- Do not produce thesis text that claims alignment with "common practice" unless
  the practice is documented in the project's own scientific invariants

## REVIEW_QUEUE.md update

After producing the handoff summary, Claude Code must also update
`thesis/chapters/REVIEW_QUEUE.md` with a new row in the Pending table.
```

---

### Step 3 — User action: move local gitignored files

> **User must run manually** (these are gitignored, not tracked):
> ```bash
> # Move model artifacts
> mv models/*.joblib src/rts_predict/sc2/models/ 2>/dev/null
> mv models/*.pt src/rts_predict/sc2/models/ 2>/dev/null
> mv models/results/* src/rts_predict/sc2/models/results/ 2>/dev/null
>
> # Move logs
> mv logs/sc2_pipeline.log src/rts_predict/sc2/logs/ 2>/dev/null
>
> # Move manifest
> mv in_game_processing_manifest.json src/rts_predict/sc2/ 2>/dev/null
>
> # Remove now-empty root dirs
> rmdir models/results models logs 2>/dev/null
> ```

---

### Step 4 — Update `src/rts_predict/sc2/config.py`

Replace `ROOT_PROJECTS_DIR` with centralized game-aware paths:

**Remove:**
```python
ROOT_PROJECTS_DIR: Path = Path(__file__).resolve().parent.parent.parent
```

**Add:**
```python
# Game-scoped directories (derived from this file's location)
GAME_DIR: Path = Path(__file__).resolve().parent                # src/rts_predict/sc2/
ROOT_DIR: Path = GAME_DIR.parent.parent.parent                  # repo root
REPORTS_DIR: Path = GAME_DIR / "reports"
```

**Update derived paths:**
```python
# Old: IN_GAME_MANIFEST_PATH: Path = ROOT_PROJECTS_DIR / "in_game_processing_manifest.json"
IN_GAME_MANIFEST_PATH: Path = GAME_DIR / "in_game_processing_manifest.json"

# Old: MODELS_DIR: Path = ROOT_PROJECTS_DIR / "models"
MODELS_DIR: Path = GAME_DIR / "models"

# Old: GNN_VIZ_OUTPUT_PATH: Path = ROOT_PROJECTS_DIR / "reports" / "gnn_space_map.png"
GNN_VIZ_OUTPUT_PATH: Path = REPORTS_DIR / "gnn_space_map.png"

# Old: RESULTS_DIR: Path = ROOT_PROJECTS_DIR / "models" / "results"
RESULTS_DIR: Path = MODELS_DIR / "results"
```

---

### Step 5 — Update Python imports in all source files

**Global find-replace patterns (in all `.py` files under `src/rts_predict/sc2/`):**

| Old | New |
|-----|-----|
| `from sc2ml.` | `from rts_predict.sc2.` |
| `import sc2ml.` | `import rts_predict.sc2.` |
| `"sc2ml.` (in test patch strings) | `"rts_predict.sc2.` |

**Files requiring import changes (all under `src/rts_predict/sc2/`):**

1. `cli.py` — 5 import refs: `from rts_predict.sc2.config import ...`, etc.
2. `data/ingestion.py` — 2 import refs
3. `data/processing.py` — 1 import ref
4. `data/audit.py` — 3 import refs + **remove local `REPORTS_DIR` definition (line 29)**, add `REPORTS_DIR` to the config import
5. `data/exploration.py` — 1 import ref + **remove local `REPORTS_DIR` definition (line 26)**, add `REPORTS_DIR` to a new config import
6. `data/samples/process_sample.py` — 1 docstring ref
7. `data/tests/conftest.py` — 1 docstring ref
8. `data/tests/test_audit.py` — 4+ import refs, 2+ patch string refs
9. `data/tests/test_exploration.py` — 20+ import refs, `REPORTS_DIR` patching refs
10. `data/tests/test_ingestion.py` — 15+ import refs, 25+ patch string refs
11. `data/tests/test_processing.py` — 1 import ref
12. `tests/test_cli.py` — 9+ import refs, `_CLI = "rts_predict.sc2.cli"`, `sys.argv` with `"sc2"` (matches new CLI name)

**`src/rts_predict/sc2/__init__.py`:**
- Remove `__version__` (now in `src/rts_predict/__init__.py`)
- Keep/update docstring to: `"""StarCraft II game package for RTS outcome prediction."""`

---

### Step 5.5 — Import verification checkpoint

Run tests immediately after the import rename to catch breakage early:

```bash
poetry install
poetry run pytest tests/ src/ -x --tb=short --no-header 2>&1 | tail -20
```

If any tests fail on `ImportError` or `ModuleNotFoundError`, fix the missed
import before continuing. Do not proceed to Step 6 with broken imports.

Also verify no orphaned `sc2ml` references remain in Python files:

```bash
grep -r "from sc2ml\." src/ tests/ --include="*.py" | grep -v __pycache__
grep -r "import sc2ml" src/ tests/ --include="*.py" | grep -v __pycache__
grep -r '"sc2ml\.' src/ tests/ --include="*.py" | grep -v __pycache__
```

All three commands must return empty output.

---

### Step 6 — Update `pyproject.toml`

```toml
[project.scripts]
# Old: sc2ml = "sc2ml.cli:main"
sc2 = "rts_predict.sc2.cli:main"

[tool.poetry]
# Old: packages = [{include = "sc2ml", from = "src"}]
packages = [{include = "rts_predict", from = "src"}]

[tool.coverage.run]
# Old: source = ["src/sc2ml"]
source = ["src/rts_predict"]
```

Also update the version field if it exists in `pyproject.toml` to `0.14.0`.

---

### Step 7 — Update `.gitignore`

Replace root-level artifact patterns with game-scoped ones:

```gitignore
# Old:
# models/*.joblib
# models/*.pt
# logs/
# in_game_processing_manifest.json

# New — game-scoped artifacts:
src/rts_predict/*/models/*.joblib
src/rts_predict/*/models/*.pt
src/rts_predict/*/logs/
src/rts_predict/*/in_game_processing_manifest.json
```

---

### Step 8 — Update all `.claude/*.md` documentation

Every occurrence of the following patterns must be updated across all `.claude/*.md` files:

| Old pattern | New pattern |
|-------------|-------------|
| `src/sc2ml/` | `src/rts_predict/sc2/` |
| `from sc2ml.` | `from rts_predict.sc2.` |
| `poetry run sc2ml` | `poetry run sc2` |
| `python -m sc2ml.cli` | `python -m rts_predict.sc2.cli` |
| `--cov=sc2ml` | `--cov=rts_predict` |
| `poetry run mypy src/sc2ml/` | `poetry run mypy src/rts_predict/` |
| `reports/SC2ML_THESIS_ROADMAP.md` | `src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md` |
| `reports/00_` | `src/rts_predict/sc2/reports/00_` |
| `reports/01_` | `src/rts_predict/sc2/reports/01_` |
| `reports/archive/` | `src/rts_predict/sc2/reports/archive/` |
| `SC2ML_THESIS_ROADMAP.md` | `SC2_THESIS_ROADMAP.md` (when just filename) |

**Files and specific changes:**

#### `.claude/coding-standards.md`
- Line 7: `poetry run mypy src/sc2ml/` → `poetry run mypy src/rts_predict/`
- Line 42: `src/sc2ml/` → `src/rts_predict/sc2/`
- Line 43: `from sc2ml.* import ...` → `from rts_predict.sc2.* import ...`

#### `.claude/git-workflow.md`
- Line 37: `--cov=sc2ml` → `--cov=rts_predict`
- Lines 87, 99: `src/sc2ml/__init__.py` → `src/rts_predict/__init__.py`
- Line 122: `--cov=sc2ml` → `--cov=rts_predict`
- Line 124: `poetry run mypy src/sc2ml/` → `poetry run mypy src/rts_predict/`

#### `.claude/project-architecture.md`
- **Major rewrite**: update entire Package Layout section to match new tree
- All path references throughout
- Line 213: `reports/SC2ML_THESIS_ROADMAP.md` → `src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md`
- Directories section: update `reports/`, `models/`, `logs/` to new locations
- Add reference to `ARCHITECTURE.md` at repo root as the canonical structural guide
- Add reference to `PHASE_STATUS.yaml` as the per-game progress tracker

#### `.claude/python-workflow.md`
- Line 13: `poetry run python -m sc2ml.cli` → `poetry run python -m rts_predict.sc2.cli`
- Line 14: `--cov=sc2ml` → `--cov=rts_predict`
- Line 16: `poetry run mypy src/sc2ml/` → `poetry run mypy src/rts_predict/`

#### `.claude/testing-standards.md`
- Line 7: `--cov=sc2ml` → `--cov=rts_predict`
- Lines 20-32, 38: All `src/sc2ml/` → `src/rts_predict/sc2/`

#### `.claude/scientific-invariants.md`
- Line 87: `SC2ML_THESIS_ROADMAP.md` → `SC2_THESIS_ROADMAP.md`

#### `.claude/ml-protocol.md`
- Line 28: `log results in reports/` → `log results in the game-specific reports directory (e.g. src/rts_predict/sc2/reports/)`
- Line 47: `reports/research_log.md` — **keep as-is** (stays at root)
- Line 54: `reports/archive/XX_run.md` → `src/rts_predict/sc2/reports/archive/XX_run.md`

#### `.claude/thesis-writing.md`
- Line 92-93: `reports/01_duration_distribution_full.png` → `src/rts_predict/sc2/reports/01_duration_distribution_full.png`
- Line 113: `report artifacts (CSVs, PNGs, MDs in reports/)` → update path guidance to `src/rts_predict/sc2/reports/`
- Lines 262-296 (phase-to-section mapping): update report dir references
- Add reference to `thesis/chapters/REVIEW_QUEUE.md` in the two-pass workflow section
- Add reference to `.claude/chat-handoff.md` in the Pass 1 output requirements
- After the "Two-pass writing workflow" section, add:
  ```
  After completing Pass 1, Claude Code must also:
  - Update `thesis/chapters/REVIEW_QUEUE.md` with a new Pending entry
  - Produce a Chat Handoff Summary block (see `.claude/chat-handoff.md`)
  ```

#### `.claude/aoe2-plan.md`
- Any `src/aoe2/` references → `src/rts_predict/aoe2/`
- Add note: "Phase progress tracked in `src/rts_predict/aoe2/PHASE_STATUS.yaml`"

---

### Step 9 — Update `CLAUDE.md`

Every reference pattern listed in Step 8, plus:

- Package Layout section: describe `src/rts_predict/` with sub-packages
- All command examples: `poetry run sc2`, `--cov=rts_predict`, `mypy src/rts_predict/`
- Test location description: `src/rts_predict/sc2/<subpkg>/tests/`
- Version bump path: `src/rts_predict/__init__.py` (single location, not sc2)
- Roadmap reference: `src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md`
- Report paths in progress tracking section

**Add to Reference Files table:**

| File | Contents |
|------|----------|
| `ARCHITECTURE.md` | Package layout, game contract, how to add a new game |
| `.claude/chat-handoff.md` | Pass 1→2 handoff protocol for thesis writing |
| `src/rts_predict/sc2/PHASE_STATUS.yaml` | SC2 phase progress (machine-readable) |
| `thesis/chapters/REVIEW_QUEUE.md` | Thesis sections pending Claude Chat review |

**Update Progress Tracking section** — add as the FIRST bullet:

```markdown
- **At session start:** Read the relevant `PHASE_STATUS.yaml` (e.g.
  `src/rts_predict/sc2/PHASE_STATUS.yaml`) to determine the current phase.
  This is faster and more reliable than parsing the full roadmap. Read the
  full roadmap only when you need step-level detail for the current phase.
```

**Update end-of-session — add:**

```markdown
- **After completing a phase gate:** Update the relevant `PHASE_STATUS.yaml`:
  set the completed phase to `status: complete` with `gate_date`, advance
  `current_phase` to the next phase number.
- **After Category F work:** Update `thesis/chapters/REVIEW_QUEUE.md` and
  produce a Chat Handoff Summary (see `.claude/chat-handoff.md`).
```

---

### Step 10 — Update `README.md`

- Command examples: `poetry run sc2 --help`, `--cov=rts_predict`
- Roadmap reference
- Any structural description
- Add mention of `ARCHITECTURE.md` for contributors/reviewers

---

### Step 11 — Update `CHANGELOG.md`

- Add this work under `[Unreleased]` section with version `0.14.0`

**Added:**
- `ARCHITECTURE.md` — package layout and game extension guide
- `.claude/chat-handoff.md` — Pass 1→2 thesis writing handoff protocol
- `thesis/chapters/REVIEW_QUEUE.md` — thesis section review queue
- `src/rts_predict/sc2/PHASE_STATUS.yaml` — machine-readable SC2 phase progress
- `src/rts_predict/aoe2/PHASE_STATUS.yaml` — AoE2 placeholder phase progress
- `src/rts_predict/common/CONTRACT.md` — shared vs game-specific code boundary
- `src/rts_predict/common/__init__.py` — common package placeholder
- `src/rts_predict/aoe2/__init__.py` — AoE2 package placeholder

**Changed:**
- Renamed Python package from `sc2ml` to `rts_predict.sc2`
- Moved SC2 reports from `reports/` to `src/rts_predict/sc2/reports/`
- Renamed `SC2ML_THESIS_ROADMAP.md` → `SC2_THESIS_ROADMAP.md`
- CLI entry point renamed from `sc2ml` to `sc2`
- `REPORTS_DIR` centralized in `config.py` (removed duplicate definitions in `audit.py` and `exploration.py`)
- Updated all `.claude/*.md`, `CLAUDE.md`, `README.md` path references
- Version bumped to `0.14.0`

- **Historical entries**: Add a single note at the top of the changelog:
  > Note: Entries before v0.14.0 reference the old `sc2ml` package name and
  > root-level `reports/` paths. See the repo reorganization in v0.14.0.

---

### Step 12 — Update `reports/research_log.md`

- Add a dated entry documenting this reorganization
- Update path references in existing entries that Claude would use for context
  (recent entries from Phase 0 and Phase 1 that reference `reports/` paths)
- Add `[SC2]` tags to existing entries for consistency with new convention
- Do NOT rewrite historical entries — they are records of what happened at that time

---

### Step 13 — Update `thesis/THESIS_STRUCTURE.md`

- Line 19: `SC2ML roadmap phases` → `SC2 roadmap phases`
- Any `reports/` path references → `src/rts_predict/sc2/reports/`

---

### Step 14 — Clean up old root directories

```bash
# Remove old src/sc2ml (now at src/rts_predict/sc2/)
# (should be empty after git mv)

# Remove old src/aoe2 (now at src/rts_predict/aoe2/)
# (should be empty after git mv)

# Remove old root models/ dir (gitignored files moved in Step 3)
# (user does this manually since contents are gitignored)

# Remove old root logs/ dir (same)
```

---

### Step 15 — Reinstall package and regenerate lock

```bash
poetry lock --no-update
poetry install
```

---

### Step 16 — Create `ARCHITECTURE.md`

Create `ARCHITECTURE.md` at the repo root:

```markdown
# Architecture

This document describes the package structure of `rts-outcome-prediction` and
the conventions for extending it.

## Package layout

```
src/rts_predict/
├── __init__.py          # Package version (__version__), single source of truth
├── sc2/                 # StarCraft II — complete game package
├── aoe2/                # Age of Empires II — placeholder, mirrors sc2/ when populated
└── common/              # Shared evaluation code — see common/CONTRACT.md
```

Each game package is self-contained: it has its own CLI, config, data pipeline,
reports, models directory, and tests. The top-level `rts_predict` package provides
the namespace and version; it contains no game-specific logic.

## Game package contract

Every game package (`sc2/`, `aoe2/`, ...) must contain:

| Item | Purpose | Required? |
|------|---------|-----------|
| `__init__.py` | Docstring identifying the game. NO `__version__`. | Yes |
| `cli.py` | CLI entry point registered in `pyproject.toml` | Yes |
| `config.py` | `GAME_DIR`, `ROOT_DIR`, `REPORTS_DIR`, DB paths, constants | Yes |
| `PHASE_STATUS.yaml` | Machine-readable phase progress | Yes |
| `data/` | Ingestion, processing, exploration, audit modules | Yes |
| `data/tests/` | Co-located unit tests for data modules | Yes |
| `reports/` | Phase artifacts (tracked in git) | Yes |
| `reports/<GAME>_THESIS_ROADMAP.md` | Authoritative execution plan | Yes |
| `models/` | Serialised model artifacts (gitignored) | When modelling begins |
| `logs/` | Pipeline logs (gitignored) | When pipeline exists |
| `tests/` | Package-root tests (CLI, validation) | Yes |

## Adding a new game

1. Create `src/rts_predict/<game>/` mirroring the `sc2/` structure above
2. Create `PHASE_STATUS.yaml` with `current_phase: null`
3. Create `<GAME>_THESIS_ROADMAP.md` in the reports directory
4. Register the CLI entry point in `pyproject.toml`
5. Update `.gitignore` patterns (already use `rts_predict/*/` wildcards)
6. Do NOT create shared abstractions until the second game's implementation
   reveals genuine code overlap (see `common/CONTRACT.md`)

## Cross-cutting files (not game-specific)

| File | Location | Purpose |
|------|----------|---------|
| Research log | `reports/research_log.md` | Unified chronological narrative, tagged `[SC2]`/`[AoE2]`/`[CROSS]` |
| Thesis | `thesis/` | Chapters, figures, tables, bibliography |
| Review queue | `thesis/chapters/REVIEW_QUEUE.md` | Pass 1→2 handoff for thesis writing |
| Scientific invariants | `.claude/scientific-invariants.md` | Methodology constraints (apply to all games) |
| Chat handoff | `.claude/chat-handoff.md` | Claude Code → Claude Chat protocol |

## Progress tracking

Phase progress per game is tracked in `PHASE_STATUS.yaml` files. Claude Code reads
these at session start to determine the current phase without parsing full roadmaps.

Thesis section progress is tracked in `thesis/WRITING_STATUS.md` (per-section status)
and `thesis/chapters/REVIEW_QUEUE.md` (Pass 2 review queue).

The changelog (`CHANGELOG.md`) tracks code changes per version. The research log
(`reports/research_log.md`) tracks analytical findings per phase.

## Version management

- Single version source: `src/rts_predict/__init__.py`
- Game packages do NOT have their own version
- Version is bumped at PR creation time (see `.claude/git-workflow.md`)
- Bumped in three places atomically: `pyproject.toml`, `__init__.py`, `CHANGELOG.md`

## Thesis writing workflow (two-pass)

See `.claude/thesis-writing.md` for full details. Summary:

- **Pass 1 (Claude Code):** Draft section, run critical review checklist,
  plant `[REVIEW: ...]` flags, update `REVIEW_QUEUE.md`
- **Pass 2 (Claude Chat):** External validation against literature, resolve
  flags, check methodology alignment with field norms

The handoff protocol is defined in `.claude/chat-handoff.md`.
```

---

### Step 17 — Full verification

After all changes:

```bash
# 1. Tests pass
poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing

# 2. Linting clean
poetry run ruff check src/ tests/

# 3. Type checking clean
poetry run mypy src/rts_predict/

# 4. CLI works
poetry run sc2 --help

# 5. Verify no orphaned sc2ml references remain
grep -r "sc2ml" src/ tests/ --include="*.py" | grep -v __pycache__
grep -r "sc2ml" .claude/ CLAUDE.md README.md --include="*.md"
# (CHANGELOG.md historical entries and research_log.md old entries are expected exceptions)

# 6. Verify report artifacts are in new location
ls src/rts_predict/sc2/reports/00_source_audit.json
ls src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md

# 7. Verify Python imports resolve
poetry run python -c "from rts_predict.sc2.config import GAME_DIR; print(GAME_DIR)"

# 8. Verify new infrastructure files exist
test -f ARCHITECTURE.md
test -f src/rts_predict/sc2/PHASE_STATUS.yaml
test -f src/rts_predict/aoe2/PHASE_STATUS.yaml
test -f src/rts_predict/common/CONTRACT.md
test -f thesis/chapters/REVIEW_QUEUE.md
test -f .claude/chat-handoff.md

# 9. Verify version consistency
poetry run python -c "from rts_predict import __version__; assert __version__ == '0.14.0', __version__"
grep -q '0.14.0' pyproject.toml
```

---

## Scope Confirmation

This chore **DOES**:
- Rename `sc2ml` → `rts_predict.sc2` (Python package + all references)
- Move SC2 reports, models, logs, manifest into `src/rts_predict/sc2/`
- Create `rts_predict.aoe2` and `rts_predict.common` placeholders with proper `__init__.py`
- Centralize `REPORTS_DIR` in config.py (removes duplicate definitions in audit.py/exploration.py)
- Rename `SC2ML_THESIS_ROADMAP.md` → `SC2_THESIS_ROADMAP.md`
- Update CLI entry point from `sc2ml` to `sc2`
- Update all `.md` documentation references
- Create `ARCHITECTURE.md` documenting the package structure and extension guide
- Create `PHASE_STATUS.yaml` files for machine-readable phase progress tracking
- Create `common/CONTRACT.md` defining shared vs game-specific code boundaries
- Create `thesis/chapters/REVIEW_QUEUE.md` for Pass 1→2 thesis writing handoff
- Create `.claude/chat-handoff.md` defining the Claude Code → Claude Chat protocol
- Bump version to `0.14.0`

This chore does **NOT**:
- Change any business logic, SQL queries, or test assertions
- Modify thesis chapter content
- Add new features or fix bugs
- Change DuckDB database paths or external data paths
- Add new tests (existing tests are updated for new import paths only)