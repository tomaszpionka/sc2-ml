# Development Constraints

For package layout and game contract, see `ARCHITECTURE.md`.
This file has constraints not obvious from code structure.

## Module Ordering
| Module | Write after |
|--------|------------|
| `sc2/data/exploration.py` | Phase 0 gate |
| `sc2/data/processing.py` views | Phase 2 gate |
| `sc2/features/` | Phase 7 gate |
| `sc2/models/baselines.py` | Phase 9 |
| `sc2/models/classical.py` | Phase 9 gate |

## Surviving Legacy
`processing.py` → `create_temporal_split()`: wrong strategy, Phase 8 supersedes.
All other legacy (features/, gnn/, models/, analysis/) deleted v0.13.2,
tag `pre-roadmap-cleanup`.

## External Data
- `~/duckdb_work/test_sc2.duckdb` — main DuckDB
- `~/duckdb_work/tmp/` — DuckDB temp dir
- `~/Downloads/SC2_Replays/` — raw JSON replays (NEVER modify)

## Platform
- DuckDB: 24GB RAM, 4 threads (Apple M4 Max)
- LightGBM + PyTorch: conflicting OpenMP — subprocess isolation
- GNN: force CPU (MPS sparse tensor issues)

## Feature Engineering Guards
BLOCKED until Phase 7 produces `07_feature_specification.md`.
Functions must: use only `match_time < T`, use `player_canonical_id`,
be testable for leakage in isolation.
