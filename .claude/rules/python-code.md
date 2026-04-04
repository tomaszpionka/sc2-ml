---
paths:
  - "**/*.py"
---

# Python Code Standards

## Pre-Commit Checks (MANDATORY)
1. `poetry run ruff check src/ tests/`
2. `poetry run mypy src/rts_predict/`
3. `poetry run pytest tests/ src/ -v`

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
- Co-located: `x/y/z/module.py` → `x/y/z/tests/test_module.py`
- Package-root tests (CLI, validation) in `src/rts_predict/sc2/tests/`
- Root `tests/` for infra and cross-package integration tests
- Test with: empty DataFrames, single rows, NaN handling, boundary conditions
- NEVER train models on real data inside tests — use synthetic fixtures
- Test temporal leakage: for sample target games, assert no feature uses data ≥ T

### Current test structure (add dirs as phases complete)
```
src/rts_predict/sc2/
├── data/tests/              # ✓ exists
└── tests/                   # ✓ exists
# Future: features/tests/ (Phase 7+), models/tests/ (Phase 9+)
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
