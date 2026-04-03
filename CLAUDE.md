# Master's Thesis: RTS Game Result Prediction

**Thesis:** "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

This project builds ML models (classical baselines, graph embeddings, and Graph Neural Networks) to predict match outcomes from replay data. All code and methodology must meet Master's thesis standards.

---

## ⚠️ Read First: Scientific Invariants

**Before doing any work in this repository — data exploration, feature engineering,
modelling, evaluation, or even reading other files — read `.claude/scientific-invariants.md`.**

It contains the non-negotiable thesis methodology constraints. They take precedence over
any implementation convenience described elsewhere. Violating them produces results that
cannot be defended at examination.

---

## Project Status: Starting from Correct Foundations

The repository contains existing code written before proper data exploration was conducted.
**Treat all existing modules as legacy drafts, not as correct implementations.**

The authoritative execution plan is `reports/SC2ML_THESIS_ROADMAP.md`. Every session
must begin by reading it to understand which phase is current and what the gate condition
is for advancing. Do not implement features, models, or splits until the phase that
motivates them is complete and its artifacts exist.

The old `reports/ROADMAP.md` is superseded. Do not use it to determine what to work on.

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

## Python Execution (MANDATORY)

- **ALWAYS** use `poetry run <command>` or activate `.venv/` first
- **NEVER** use bare `python3`, `python3 -c`, or `pip install`
- Run scripts: `poetry run python -m sc2ml.cli`
- Run tests: `poetry run pytest tests/ src/ -v --cov=sc2ml --cov-report=term-missing`
- **Test location:** Tests are co-located with source — `x/y/z/module.py` → `x/y/z/tests/test_module.py`. Package-internal `tests/` = unit/component tests only. Root `tests/integration/` = cross-package integration tests. Root `tests/` also holds general infra tests and shared helpers. Package-root tests (cli, validation) go in `src/sc2ml/tests/`.
- Lint before commits: `poetry run ruff check src/ tests/`
- Type check: `poetry run mypy src/sc2ml/`

---

## Tech Stack

Python 3.12 | Poetry | PyTorch + PyG | DuckDB | scikit-learn, XGBoost, LightGBM | pandas, numpy | matplotlib | NetworkX, Gensim | Apple M4 Max (36GB RAM, MPS-capable)

---

## Reference Files (sub-files in `.claude/`)

| File | Contents |
|------|----------|
| `.claude/scientific-invariants.md` | **Thesis methodology constraints — read before any work** |
| `.claude/project-architecture.md` | Structural guidance: package layout, patterns, identifier design, legacy code warnings |
| `.claude/ml-protocol.md` | Experiment methodology, leakage rules, documentation artifacts |
| `.claude/python-workflow.md` | Venv, Poetry, execution rules, MPS/GPU, build deps |
| `.claude/testing-standards.md` | Coverage, test patterns, edge cases, commit gates |
| `.claude/coding-standards.md` | Style, type hints, linting, docstrings, pre-commit checks |
| `.claude/git-workflow.md` | Branches, commits, end-of-session checklist |
| `.claude/aoe2-plan.md` | AoE2 integration notes (upcoming) |
| `reports/SC2ML_THESIS_ROADMAP.md` | **The authoritative phase-by-phase execution plan** |
| `reports/methodology.md` | Full thesis specification (RQs, features, models, evaluation) |

---

## Progress Tracking (MANDATORY)

- **Before starting any work:** Read `.claude/scientific-invariants.md`, then read `reports/SC2ML_THESIS_ROADMAP.md` to identify the current phase and its gate condition.
- **Do not begin a phase** until all artifacts from the previous phase exist on disk.
- **After completing a step:** Update `reports/research_log.md` with findings, decisions, and any deviations from the roadmap.
- **After code changes:** Follow `.claude/git-workflow.md` — conventional branch names, atomic commits, conventional commit messages. Every session must end with the checklist below.

## End-of-Session Checklist

> See `.claude/git-workflow.md` for full details on branches, commits, and conventions.

**If wrapping up into a PR:** follow the full PR creation flow in `.claude/git-workflow.md`
— this includes autonomous version bump in `pyproject.toml`, `CHANGELOG.md`, and
`src/sc2ml/__init__.py` before proposing the push.

**If not wrapping up into a PR:**

1. All tests pass with coverage report
2. Ruff and mypy clean
3. `CHANGELOG.md` updated — current work documented under `[Unreleased]`; version is
   not bumped until PR creation
4. Phase artifacts from `reports/SC2ML_THESIS_ROADMAP.md` verified to exist on disk
5. `reports/research_log.md` updated with findings, decisions, and any issues encountered
6. Proposed commit messages for all uncommitted work
7. Summary of what's ready to merge and what's still in progress
