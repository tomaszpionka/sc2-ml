# Python Workflow

## Execution Rules (MANDATORY)

- **ALWAYS** use `poetry run <command>` or activate `.venv/` first
- **NEVER** use bare `python3`, `python3 -c`, or `pip install`
- Activate venv: `source /Users/tomaszpionka/Projects/sc2-ml/.venv/bin/activate`

## Common Commands

| Task | Command |
|------|---------|
| Run pipeline | `poetry run python -m sc2ml.cli` |
| Run tests | `poetry run pytest tests/ -v --cov=sc2ml --cov-report=term-missing` |
| Lint | `poetry run ruff check src/ tests/` |
| Type check | `poetry run mypy src/sc2ml/` |
| Add dependency | `poetry add <package>` |
| Add dev dependency | `poetry add --group dev <package>` |

## Environment

- **Runtime:** Python 3.12 (venv at `.venv/`)
- **Dependency management:** Poetry with `pyproject.toml`
- **Python constraint:** `>=3.12,<3.13`
- **Lock file:** `poetry.lock` committed to git for reproducibility

## MPS / GPU

- `PYTORCH_ENABLE_MPS_FALLBACK=1` is set in `~/.zshrc` to route unsupported ops to CPU
- GNN training forces CPU explicitly due to MPS sparse tensor issues (silent failures, segfaults)

## Build Dependencies

- `brew install libomp` (required for LightGBM/XGBoost on ARM64)
- `pip install torch-cluster torch-scatter torch-sparse --no-build-isolation` (PyG extensions — manual install only)
