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
| `GAME_DIR` | `src/rts_predict/aoe2/` |
| `DATA_DIR` | `src/rts_predict/aoe2/data/` |
| `REPORTS_DIR` | `src/rts_predict/aoe2/reports/` |
| `AOE2COMPANION_DIR` | `src/rts_predict/aoe2/data/aoe2companion/` |
| `AOE2COMPANION_DB_FILE` | `src/rts_predict/aoe2/data/aoe2companion/db/db.duckdb` |
| `AOESTATS_DIR` | `src/rts_predict/aoe2/data/aoestats/` |
| `AOESTATS_DB_FILE` | `src/rts_predict/aoe2/data/aoestats/db/db.duckdb` |

## Datasets

| Dataset | ROADMAP | Phase status |
|---------|---------|--------------|
| aoe2companion | [ROADMAP.md](reports/aoe2companion/ROADMAP.md) | Phase 01 in progress |
| aoestats | [ROADMAP.md](reports/aoestats/ROADMAP.md) | Phase 01 in progress |

**aoe2companion** — daily API dumps from aoe2companion.com (matches, ratings,
leaderboards, profiles).

**aoestats** — weekly DB dumps from aoestats.io (matches and players Parquet
files, directories must match).

## Reports layout

```
reports/
    aoe2companion/
        PHASE_STATUS.yaml
        PIPELINE_SECTION_STATUS.yaml
        STEP_STATUS.yaml
        ROADMAP.md
        research_log.md
        artifacts/          # machine-generated outputs (CSV, MD, PNG)
    aoestats/
        PHASE_STATUS.yaml
        PIPELINE_SECTION_STATUS.yaml
        STEP_STATUS.yaml
        ROADMAP.md
        research_log.md
        artifacts/          # machine-generated outputs (CSV, MD, PNG)
```
