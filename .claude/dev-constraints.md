# Development Constraints

For package layout and game contract, see `ARCHITECTURE.md`.
This file has constraints not obvious from code structure.

## Module Ordering

Module write ordering is derived from the active dataset's ROADMAP.md. Do not
write downstream modules before upstream phase gates are met. See
docs/PHASES.md for the phase sequence.

## Surviving Legacy
`processing.py` → `create_temporal_split()`: wrong strategy, Phase 03 (Splitting & Baselines) supersedes.
All other legacy (features/, gnn/, models/, analysis/) deleted v0.13.2,
tag `pre-roadmap-cleanup`.

## Data Layout
All pipeline data lives under `data/<dataset>/` within each game's subpackage (gitignored contents, tracked skeleton):
- `src/rts_predict/sc2/data/sc2egset/raw/` — raw JSON replays (NEVER modify)
- `src/rts_predict/sc2/data/sc2egset/staging/in_game_events/` — in-game event Parquet files (reproducible)
- `src/rts_predict/sc2/data/sc2egset/db/db.duckdb` — main DuckDB database (reproducible)
- `src/rts_predict/sc2/data/sc2egset/tmp/` — DuckDB spill-to-disk temp directory

## Phase Work Execution

All Category A (phase work) code runs in sandbox notebooks, not in `src/`
modules or ad-hoc scripts. Path: `sandbox/<game>/<dataset>/XX_XX_<name>.{py,ipynb}`.
Artifacts are saved to `reports/<dataset>/artifacts/`, never to the report root.
See `sandbox/README.md` for the full contract.

## Platform
- DuckDB: 24GB RAM, 4 threads (Apple M4 Max)
- LightGBM + PyTorch: conflicting OpenMP — subprocess isolation
- GNN: force CPU (MPS sparse tensor issues)

## Feature Engineering Guards
BLOCKED until Phase 02 (Feature Engineering) produces a feature specification. See docs/PHASES.md.
Functions must: use only `match_time < T`, use `player_canonical_id`,
be testable for leakage in isolation.
