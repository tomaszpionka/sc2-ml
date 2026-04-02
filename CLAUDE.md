# Master's Thesis: RTS Game Result Prediction

**Thesis:** "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

This project builds ML models (classical baselines, graph embeddings, and Graph Neural Networks) to predict match outcomes from replay data. All code and methodology must meet Master's thesis standards.

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
- Run tests: `poetry run pytest tests/ -v --cov=sc2ml --cov-report=term-missing`
- Lint before commits: `poetry run ruff check src/ tests/`
- Type check: `poetry run mypy src/sc2ml/`

---

## Tech Stack

Python 3.12 | Poetry | PyTorch + PyG | DuckDB | scikit-learn, XGBoost, LightGBM | pandas, numpy | matplotlib | NetworkX, Gensim | Apple M4 Max (36GB RAM, MPS-capable)

---

## Detailed Guidelines (sub-files in `.claude/`)

| File | Contents |
|------|----------|
| `.claude/python-workflow.md` | Venv, Poetry, execution rules, MPS/GPU, build deps |
| `.claude/testing-standards.md` | Coverage, test patterns, edge cases, commit gates |
| `.claude/coding-standards.md` | Style, type hints, linting, docstrings, pre-commit checks |
| `.claude/git-workflow.md` | Branches, commits, end-of-session checklist |
| `.claude/ml-protocol.md` | Experiment methodology, leakage rules, documentation artifacts |
| `.claude/project-architecture.md` | Package layout, data pipeline, design decisions |
| `.claude/aoe2-plan.md` | AoE2 integration notes (upcoming) |

---

## End-of-Session Checklist

1. All tests pass with coverage report
2. Ruff and mypy clean
3. `CHANGELOG.md` updated with code changes
4. `reports/research_log.md` updated if session involved experimentation, methodology decisions, issues, or breakthroughs
5. Proposed commit messages for all uncommitted work
6. Summary of what's ready to merge and what's still in progress
