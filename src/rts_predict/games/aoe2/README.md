# aoe2 — Age of Empires II Package

Python package for the AoE2 match-outcome prediction pipeline.

**Operational status:** Data acquisition is functional. Feature engineering and
model training are not yet implemented — do not add implementation code until
instructed (see CLAUDE.md Project Status).

## CLI

```
poetry run aoe2 --help
```

| Subcommand | Description |
|------------|-------------|
| `aoe2 db` | Ad-hoc DuckDB operations |
| `aoe2 download` | Download raw data from AoE2 sources |

## Key modules

| File | Purpose |
|------|---------|
| `config.py` | All path constants and dataset registry |
| `cli.py` | Entry point for the `aoe2` CLI |

## Paths (from `config.py`)

| Constant | Path |
|----------|------|
| `GAME_DIR` | `src/rts_predict/games/aoe2/` |
| `DATA_DIR` | `src/rts_predict/games/aoe2/datasets/` |
| `REPORTS_DIR` | `src/rts_predict/games/aoe2/datasets/` |
| `AOE2COMPANION_DIR` | `src/rts_predict/games/aoe2/datasets/aoe2companion/data/` |
| `AOE2COMPANION_DB_FILE` | `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/db.duckdb` |
| `AOESTATS_DIR` | `src/rts_predict/games/aoe2/datasets/aoestats/data/` |
| `AOESTATS_DB_FILE` | `src/rts_predict/games/aoe2/datasets/aoestats/data/db/db.duckdb` |
| `AOE2COMPANION_REPORTS_DIR` | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/` |
| `AOE2COMPANION_ARTIFACTS_DIR` | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/` |
| `AOESTATS_REPORTS_DIR` | `src/rts_predict/games/aoe2/datasets/aoestats/reports/` |
| `AOESTATS_ARTIFACTS_DIR` | `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/` |

## Datasets

| Dataset | ROADMAP | Phase status |
|---------|---------|--------------|
| aoe2companion | [ROADMAP.md](datasets/aoe2companion/reports/ROADMAP.md) | Phase 01 in progress |
| aoestats | [ROADMAP.md](datasets/aoestats/reports/ROADMAP.md) | Phase 01 in progress |

**aoe2companion** — daily API dumps from aoe2companion.com (matches, ratings,
leaderboards, profiles).

**aoestats** — weekly DB dumps from aoestats.io (matches and players Parquet
files, directories must match).

## Reports layout

```
datasets/aoe2companion/reports/
    PHASE_STATUS.yaml
    PIPELINE_SECTION_STATUS.yaml
    STEP_STATUS.yaml
    ROADMAP.md
    research_log.md
    artifacts/          # machine-generated outputs (CSV, MD, PNG)
datasets/aoestats/reports/
    PHASE_STATUS.yaml
    PIPELINE_SECTION_STATUS.yaml
    STEP_STATUS.yaml
    ROADMAP.md
    research_log.md
    artifacts/          # machine-generated outputs (CSV, MD, PNG)
```
