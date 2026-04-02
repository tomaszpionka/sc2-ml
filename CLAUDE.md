# Master's Thesis: RTS Game Result Prediction

**Thesis:** "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

This project builds ML models (classical baselines, graph embeddings, and Graph Neural Networks) to predict match outcomes from replay data. The SC2 pipeline is semi-functional but still a subject for dev works; AoE2 is not yet started. All code, methodology, and documentation must meet Master's thesis standards — reproducibility, proper methodology justification, and clean separation of concerns. The efforts need to be documented thoroughly (including encountered issues and breakthroughs) in a form of report log so it can be later used for writing thesis document.

---

## Permissions & Safety Boundaries

### Autonomous (no confirmation needed)
- Read and write any files within `/Users/tomaszpionka/Projects/sc2-ml/`
- Run Python scripts, pytest, and poetry commands within the project
- Read-only git operations: `git status`, `git log`, `git diff`, `git branch`, `git show`

### Ask before proceeding
- Reading files outside the repo directory (e.g. `~/duckdb_work/`, `~/Downloads/SC2_Replays/`) — state which path and why, then wait for acknowledgment

### User review required (pass the command, wait for explicit confirmation)
- All git write operations: `git add`, `git commit`, `git push`, `git rebase`, etc. — Claude proposes exact commands; user reviews and executes
- Writing files outside `/Users/tomaszpionka/Projects/sc2-ml/`
- System-level installs (`brew install`, global pip installs)
- Any operation that modifies the DuckDB database at `~/duckdb_work/test_sc2.duckdb`

> **Future:** These permissions will be revised when Docker/Colima container isolation is configured.

---

## Git Workflow & Session Management

### Feature branches
Each work session maps to a feature branch. Claude proposes a branch name at session start using conventional prefixes:
- `feat/` — new functionality (e.g. `feat/aoe2-data-pipeline`)
- `fix/` — bug fixes (e.g. `fix/elo-dedup-race-condition`)
- `refactor/` — code restructuring (e.g. `refactor/poetry-setup`)
- `docs/` — documentation only (e.g. `docs/claude-md-guidelines`)
- `test/` — adding or improving tests (e.g. `test/feature-leakage-checks`)
- `chore/` — maintenance tasks (e.g. `chore/gitignore-cleanup`)

### Commit messages
After each meaningful code change, Claude proposes a commit message in [Conventional Commits](https://www.conventionalcommits.org/) format:
```
type(scope): short description

Optional body with context.
```
Examples: `feat(gnn): add temporal edge masking`, `fix(elo): prevent duplicate updates per match`

### Atomic commits
Each commit should be a single logical unit — don't bundle unrelated changes. Prefer multiple small commits over one large one.

### End-of-session checklist
Before wrapping up a work session, ensure:
1. `CHANGELOG.md` updated with code changes made during the session
2. `reports/research_log.md` updated if the session involved experimentation, methodology decisions, issues, or breakthroughs
3. Proposed commit messages provided for all uncommitted work
4. Summary of what's ready to merge and what's still in progress

---

## Tech Stack & Environment

- **Runtime:** Python 3.12 (venv at `.venv/`)
- **Hardware:** Apple M4 Max (36GB RAM, ARM64, MPS-capable GPU)
- **Dependency management:** Poetry with `pyproject.toml`
- **Core libraries:**
  - PyTorch + PyTorch Geometric (GATv2Conv, Node2Vec)
  - DuckDB (SQL-based data processing)
  - scikit-learn, XGBoost, LightGBM (classical ML baselines)
  - pandas, numpy, scipy (data manipulation)
  - matplotlib (visualization)
  - NetworkX, Gensim, node2vec (graph embeddings)
- **MPS fallback:** `PYTORCH_ENABLE_MPS_FALLBACK=1` is set in `~/.zshrc` to route unsupported ops to CPU. GNN training currently forces CPU explicitly due to MPS sparse tensor issues (silent failures, segfaults).
- **Build deps:** `brew install libomp` and `pip install torch-cluster torch-scatter torch-sparse --no-build-isolation`

---

## Project Structure

### Package layout (`src/sc2ml/`)
- `cli.py` — pipeline orchestrator, configurable model selection (`CLASSIC`, `NODE2VEC`, `GNN`)
- `config.py` — path constants, ML hyperparameters, reproducibility settings
- `data/ingestion.py` — replay JSON parsing, DuckDB loading, map translations
- `data/processing.py` — SQL view creation (`flat_players`, `matches_flat`), data validation
- `features/engineering.py` — feature engineering (45+ features, Bayesian smoothing), temporal train/test split
- `features/elo.py` — custom ELO rating with dynamic K-factor (K=64 new, K=32 veteran)
- `models/classical.py` — classical ML training/evaluation (LR, RF, GB, XGB, LGBM)
- `models/tuning.py` — RandomizedSearchCV for Random Forest
- `gnn/model.py` — SC2EdgeClassifier (GATv2Conv-based edge classifier)
- `gnn/pipeline.py` — graph construction from player features (node + edge features)
- `gnn/trainer.py` — GNN training loop with early stopping
- `gnn/visualizer.py` — t-SNE visualization of learned GNN embeddings
- `gnn/embedder.py` — Node2Vec embeddings via NetworkX/Gensim

### Directories
- `models/` — serialized model artifacts (`.joblib`, `.pt`)
- `reports/` — research log and visualization outputs
- `reports/archive/` — legacy pipeline execution logs (`01_run.md` through `09_run.md`)
- `logs/` — pipeline log file (`sc2_pipeline.log`)
- `tests/` — pytest test suite

### External data paths (from `config.py`)
- `~/duckdb_work/test_sc2.duckdb` — main DuckDB database
- `~/duckdb_work/tmp/` — DuckDB temp directory
- `~/Downloads/SC2_Replays/` — raw SC2Replay JSON files

---

## Data Pipeline

The pipeline runs in 5 stages (orchestrated by `main.py`):

1. **Ingestion** — `slim_down_sc2_with_manifest()` strips heavy replay events; `move_data_to_duck_db()` loads JSON into DuckDB `raw` table; `load_map_translations()` populates map name lookup
2. **SQL Processing** — `create_ml_views()` creates `flat_players` (one row per player per match) and `matches_flat` (paired players per match with features)
3. **ELO Computation** — `add_elo_features()` computes pre-match ELO with dynamic K-factor
4. **Feature Engineering** — `perform_feature_engineering()` builds historical rolling features (Bayesian-smoothed win rates, cumulative stats, race-specific rates). Drops post-match leakage columns.
5. **Model Training** (3 paths):
   - `CLASSIC` — tabular ML models with temporal split
   - `NODE2VEC` — graph embeddings appended to tabular features, then classical models
   - `GNN` — end-to-end GATv2-based edge classification

### Data leakage rules (critical for thesis quality)
- Never use current-match stats (APM, SQ, supply_capped_pct, game_loops) as features — only pre-match historical aggregates
- GNN node features should ideally be recomputed from training edges only
- Any new feature must respect this principle — validate before integrating

---

## Coding Standards

- **Type hints:** all function signatures must have explicit type hints (parameters and return types)
- **Modularity:** pure functions with clear inputs/outputs; no global mutable state except config constants
- **SQL:** parameterized queries for DuckDB; SQL views documented with their purpose
- **Logging:** use `logging.getLogger(__name__)`; INFO for pipeline progress, DEBUG for diagnostics
- **Constants:** named and placed in `config.py` or at the top of the relevant module; no magic numbers
- **Language:** variable names, comments, and code in English
- **Package layout:** `src/sc2ml/` with subpackages (`data`, `features`, `models`, `gnn`); imports use `from sc2ml.* import ...`

---

## Testing

- **Framework:** pytest
- **Location:** `tests/` directory
- **Categories:**
  - Data validation — schema checks on DuckDB views, null checks, type assertions, row count sanity
  - Feature engineering — verify no leakage (no future data), Bayesian smoothing edge cases, temporal ordering preserved
  - Model reproducibility — fixed random seeds yield deterministic outputs
  - Graph construction — node count matches unique players, edge count matches matches, feature dimensionality correct
- **Run:** `poetry run pytest tests/ -v`

---

## Dependency Management

- **Tool:** Poetry with `pyproject.toml` at project root
- **Python constraint:** `>=3.12,<3.13`
- **Dev dependencies:** pytest, ruff (linting), mypy (type checking)
- **Lock file:** `poetry.lock` committed to git for reproducibility
- **Adding deps:** `poetry add <package>` or `poetry add --group dev <package>`

---

## ML Experiment Protocol

1. **Hypothesis first** — before modifying any model or feature, document what you're changing and why it should help
2. **Run and log** — after every experiment, log results in `reports/` following the `XX_run.md` naming convention
3. **Compare baselines** — always compare against established results (~63-65% accuracy for classical models)
4. **Temporal splits only** — no random shuffling; use `GLOBAL_TEST_SIZE` from `main.py` for consistency
5. **Fixed seeds** — random seed 42 is the convention; all experiments must be reproducible
6. **Validate inputs/outputs** — at each pipeline stage, check data shapes, nulls, distributions, and edge cases before proceeding
7. **Report both metrics** — include "all test" and "veterans only" (3+ historical matches) accuracy figures

---

## Documentation & Thesis Trail

Three documentation artifacts serve different purposes:

### CHANGELOG.md (code versioning)
- [Keep a Changelog](https://keepachangelog.com/) format with `[Unreleased]` section at top
- Concise one-liners grouped by: `Added`, `Changed`, `Fixed`, `Removed`
- Maps directly to commits and feature branches
- Updated every session that changes code

### reports/research_log.md (thesis material)
- Reverse chronological, date-stamped entries
- Each entry uses structured fields: **Objective**, **Approach**, **Issues encountered**, **Resolution/Outcome**, **Thesis notes**
- References execution reports (`reports/archive/XX_run.md`) and specific commits where relevant
- Directly usable as source material when writing thesis chapters
- Updated every session involving experimentation, methodology decisions, issues, or breakthroughs

### reports/archive/XX_run.md (pipeline execution output)
- Legacy pipeline execution results and metrics (ChatGPT/Gemini era)
- Archived for reference — reports 07-09 contain primary baseline metrics (~64.5% accuracy)
- Referenced from research log entries, not replaced by them

---

## Known Design Decisions

- `matches_flat` produces 2 rows per match (p1/p2 and p2/p1 perspective) — intentional data augmentation; raw row count is ~2x actual unique matches
- ELO system processes each unique `match_id` only once via `processed_matches` set, despite the paired rows
- Feature engineering's cumulative operations assume chronological sorting — **never shuffle the dataframe before feature engineering**
- The GNN uses **edge classification** (predicting match outcome from player node embeddings + edge features), not node classification — a less common PyG pattern
- DuckDB configured for 24GB RAM, 4 threads (tuned for high-memory machine)
- `processing_manifest.json` (2MB) tracks which replay files have been processed; committed to git

---

## AoE2 Integration (Upcoming)

- AoE2 data pipeline does not exist yet
- Architecture goal: shared abstractions where possible (feature engineering patterns, model evaluation framework) with game-specific modules
- AoE2 has different mechanics (civilizations vs races, different economy model, different replay format) — feature engineering needs adaptation, not copy-paste
- Comparative analysis framework needed: same model architectures on both games with consistent metrics
