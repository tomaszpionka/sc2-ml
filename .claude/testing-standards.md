# Testing Standards

## Framework & Location

- **Framework:** pytest
- **Root tests:** `tests/` directory
- **Data subpackage tests:** `src/sc2ml/data/tests/`
- **Run command:** `poetry run pytest tests/ -v --cov=sc2ml --cov-report=term-missing`

## Rules

- **Every new or modified function must have a corresponding test** — no commit proposals without tests
- **Tests must pass before proposing any commit**
- Test file naming: `test_<module>.py` mirroring `src/sc2ml/<module>.py`
- Shared test utilities go in `tests/helpers.py`

## Test Categories

- **Data validation** — schema checks on DuckDB views, null checks, type assertions, row count sanity
- **Feature engineering** — verify no leakage (no future data), Bayesian smoothing edge cases, temporal ordering preserved
- **Model reproducibility** — fixed random seeds yield deterministic outputs
- **Graph construction** — node count matches unique players, edge count matches matches, feature dimensionality correct

## Edge Cases to Always Test

- Empty DataFrames (0 rows)
- Single-row inputs
- NaN / missing value handling
- Boundary conditions (e.g., player with exactly 1 historical match for veteran threshold)
