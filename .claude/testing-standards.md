# Testing Standards

## Framework & Location

- **Framework:** pytest
- **Co-located tests:** tests live next to the code they test, under a `tests/` subdirectory. For `x/y/z/module.py`, tests go in `x/y/z/tests/test_module.py`.
- **Run command:** `poetry run pytest tests/ src/ -v --cov=sc2ml --cov-report=term-missing`

### Target structure

```
tests/                              # cross-cutting only
├── conftest.py
├── helpers.py                      # shared test utilities
├── integration/
│   └── test_integration.py
├── test_mps.py
└── test_sanity_validation.py

src/sc2ml/
├── data/tests/                     # tests for src/sc2ml/data/
├── features/tests/                 # tests for src/sc2ml/features/
├── models/tests/                   # tests for src/sc2ml/models/
├── gnn/tests/                      # tests for src/sc2ml/gnn/
├── analysis/tests/                 # tests for src/sc2ml/analysis/
└── tests/                          # package-root level tests (cli, validation)
```

- **Root `tests/`:** general infra tests (e.g. MPS probes) and shared helpers
- **Root `tests/integration/`:** integration tests that wire multiple packages together
- **`src/sc2ml/<subpkg>/tests/`:** unit/component tests for that subpackage only
- **`src/sc2ml/tests/`:** tests for package-root modules (cli, validation)

## Rules

- **Every new or modified function must have a corresponding test** — no commit proposals without tests
- **Tests must pass before proposing any commit**
- Test file naming: `test_<module>.py` — placed in a `tests/` subdirectory alongside the module (e.g. `src/sc2ml/data/tests/test_processing.py` for `src/sc2ml/data/processing.py`)
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

## Thesis-Critical Tests (required for any data or feature work)

- **Temporal leakage:** for a sample of 20 target games, assert that no feature
  value references any event at or after that game's match_time
- **Split integrity:** assert that no player's test target is temporally before
  any of their training examples
- **Player identity:** assert that canonical_nickname (lowercased) is used as
  the player FK everywhere — never raw toon string
- **Win rate parity:** assert that overall win rate in games_clean is exactly
  0.500 (every game has exactly one winner)
- **APM/MMR dead field:** assert that APM and MMR from ToonPlayerDescMap are
  excluded from all feature tables (confirmed zero across corpus)
  