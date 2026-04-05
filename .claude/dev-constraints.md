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

## Data Layout
All pipeline data lives under `data/<dataset>/` within each game's subpackage (gitignored contents, tracked skeleton):
- `src/rts_predict/sc2/data/sc2egset/raw/` — raw JSON replays (NEVER modify)
- `src/rts_predict/sc2/data/sc2egset/staging/in_game_events/` — in-game event Parquet files (reproducible)
- `src/rts_predict/sc2/data/sc2egset/db/db.duckdb` — main DuckDB database (reproducible)
- `src/rts_predict/sc2/data/sc2egset/tmp/` — DuckDB spill-to-disk temp directory

## Platform
- DuckDB: 24GB RAM, 4 threads (Apple M4 Max)
- LightGBM + PyTorch: conflicting OpenMP — subprocess isolation
- GNN: force CPU (MPS sparse tensor issues)

## Feature Engineering Guards
BLOCKED until Phase 7 produces `07_feature_specification.md`.
Functions must: use only `match_time < T`, use `player_canonical_id`,
be testable for leakage in isolation.
