# Coding Standards

## Pre-Commit Checks (MANDATORY)

Before proposing any commit, run and resolve all issues:
1. `poetry run ruff check src/ tests/`
2. `poetry run mypy src/sc2ml/`
3. `poetry run pytest tests/ -v`

## Type Hints

- All function signatures must have explicit type hints (parameters and return types)
- Use `from __future__ import annotations` or `TYPE_CHECKING` for forward references

## Style & Structure

- **Modularity:** pure functions with clear inputs/outputs; no global mutable state except config constants
- **Max function length:** ~50 lines — longer functions must be decomposed
- **Docstrings:** Google style, required on all public functions
- **Language:** variable names, comments, and code in English
- **No bare `except:`** — always catch specific exceptions
- **Constants:** named and placed in `config.py` or at the top of the relevant module; no magic numbers

## SQL

- Parameterized queries for DuckDB
- SQL views documented with their purpose

## Logging

- Use `logging.getLogger(__name__)`
- INFO for pipeline progress, DEBUG for diagnostics

## Package Layout

- `src/sc2ml/` with subpackages (`data`, `features`, `models`, `gnn`)
- Imports use `from sc2ml.* import ...`

## Linting Configuration (in `pyproject.toml`)

- **Ruff:** line-length=100, target-version=py312, rules=[E, F, W, I]
- **Mypy:** python_version=3.12, ignore_missing_imports=true
