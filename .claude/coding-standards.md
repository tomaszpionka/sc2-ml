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

### SQL query organisation
DuckDB queries are written as named module-level constants (suffix `_QUERY`) in the
Python module that owns their domain. Use DuckDB's `?` parameter binding for all
variable values — never f-string or concatenate user-controlled values into query
strings. Separate `.sql` files are not used.

## Logging

- Use `logging.getLogger(__name__)`
- INFO for pipeline progress, DEBUG for diagnostics

## Package Layout

- `src/sc2ml/` with subpackages (`data`, `features`, `models`, `gnn`)
- Imports use `from sc2ml.* import ...`

## Linting Configuration (in `pyproject.toml`)

- **Ruff:** line-length=100, target-version=py312, rules=[E, F, W, I]
- **Mypy:** python_version=3.12, ignore_missing_imports=true

## Machine Learning Code Standards

### No magic numbers in model configuration
All hyperparameters must be named constants in `config.py` or passed as explicit
arguments — never hardcoded inline. A learning rate of `0.01` buried in a training
loop is invisible to ablation, tuning, and reproducibility audits.

### Random seeds must be explicit and centralised
Set seeds in one place at the top of any script or function that introduces
randomness. Use the project-wide seed from `config.py` (`RANDOM_SEED = 42`).
Never rely on default seeds or assume a library is deterministic without seeding.

### Pipelines over manual fit/transform sequences
Use `sklearn.pipeline.Pipeline` for any sequence of preprocessing + model steps.
This prevents the most common leakage pattern: fitting a scaler on the full dataset
before splitting.

### Fit only on training data
Scalers, encoders, smoothing parameters, vocabulary sets — anything that learns
from data must be fit exclusively on training split data, then applied to val and
test. This rule applies even when it feels tedious for simple transforms.

### Expanding window, not fixed window, for temporal aggregates
Rolling features (win rate, form, Elo) must use expanding windows anchored to the
current observation's position in the sequence — never a fixed lookback that could
include future games. See `features/common.py` for the approved pattern.

### Validate shapes and dtypes at pipeline boundaries
At each stage transition (ingestion → views, views → features, features → model
input), assert expected shapes, column presence, and dtypes explicitly. Silent
dimension mismatches cause wrong results without errors.

### No training inside test functions
Test functions must not train models on real data as a side effect of verifying
behaviour. Use fixtures with minimal synthetic data. Training belongs in the
pipeline, not in the test suite.

### Feature functions must be pure and stateless
A feature computation function takes data in, returns values out, and has no side
effects. It does not write to the database, modify global state, or depend on
execution order. This makes leakage testing possible in isolation.