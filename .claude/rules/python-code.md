---
paths:
  - "**/*.py"
---

# Python Code Standards

## Pre-Commit Checks

`ruff check` and `mypy` run automatically as pre-commit hooks on every `git commit` — no manual run needed. If a commit is blocked by a hook, fix the reported error and re-stage.

`pytest` is NOT a pre-commit hook (too slow at ~8s per commit). Run it manually after every code change:
- `source .venv/bin/activate && poetry run pytest tests/ -v`

## Style
- Type hints on all function signatures (params and return)
- Google-style docstrings on all public functions
- Max ~50 lines per function — decompose if longer
- No bare `except:` — always catch specific exceptions
- Constants in `config.py` or module-level UPPER_SNAKE_CASE — no magic numbers
- Use `logging.getLogger(__name__)`, not `print()`
- Imports: `from rts_predict.sc2.* import ...`

## SQL in Python
- Named module-level constants with `_QUERY` suffix
- DuckDB `?` parameter binding — NEVER f-string user values
- CTEs over nested subqueries for readability

## Testing
- Every new/modified function MUST have a test
- Mirrored tree: `src/rts_predict/<path>/module.py` → `tests/rts_predict/<path>/test_module.py`
- Infrastructure tests (MPS, DuckDB connectivity): `tests/infrastructure/`
- Integration tests (cross-module): `tests/integration/`
- Root `tests/conftest.py` for cross-cutting fixtures
- Per-subtree `conftest.py` for scoped fixtures (e.g., `tests/rts_predict/sc2/data/conftest.py`)
- Test with: empty DataFrames, single rows, NaN handling, boundary conditions
- NEVER train models on real data inside tests — use synthetic fixtures
- Test temporal leakage: for sample target games, assert no feature uses data >= T
- NEVER create a `tests/` directory inside `src/rts_predict/` — all tests live in the mirrored tree

### Current test structure
```
tests/
├── conftest.py
├── infrastructure/        # MPS, connectivity, mirror-drift checker
└── rts_predict/           # Mirrors src/rts_predict/ exactly
    ├── sc2/
    │   ├── test_cli.py
    │   └── data/
    │       ├── conftest.py
    │       └── test_*.py
    ├── aoe2/
    │   ├── test_cli.py
    │   └── data/
    │       ├── aoe2companion/
    │       │   └── test_*.py
    │       └── aoestats/
    │           └── test_*.py
    └── common/
        └── test_*.py
```

## ML Code
- sklearn Pipelines over manual fit/transform (prevents leakage)
- Fit scalers/encoders ONLY on training split
- Expanding windows for temporal aggregates — never fixed lookback
- Assert shapes and dtypes at each pipeline stage boundary
- Feature functions must be pure and stateless
- Random seeds: use `RANDOM_SEED = 42` from config.py everywhere

## Environment
- Python 3.12, Poetry, venv at `.venv/`
- MPS fallback: `PYTORCH_ENABLE_MPS_FALLBACK=1` in `~/.zshrc`
- ARM64 deps: `brew install libomp` for LightGBM/XGBoost
