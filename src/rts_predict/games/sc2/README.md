# sc2 — StarCraft II Package

Python package for the SC2 match-outcome prediction pipeline.

## CLI

```
poetry run sc2 --help
```

| Subcommand | Description |
|------------|-------------|
| `sc2 export-schemas` | Export DuckDB table schemas to YAML files |
| `sc2 db` | Ad-hoc DuckDB operations |

## Key modules

| File | Purpose |
|------|---------|
| `config.py` | All path constants and dataset registry |
| `cli.py` | Entry point for the `sc2` CLI |

## Paths (from `config.py`)

| Constant | Path |
|----------|------|
| `GAME_DIR` | `src/rts_predict/games/sc2/` |
| `DATA_DIR` | `src/rts_predict/games/sc2/datasets/sc2egset/data/` |
| `DATASET_DIR` | `src/rts_predict/games/sc2/datasets/sc2egset/data/` |
| `DB_FILE` | `src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb` |
| `REPORTS_DIR` | `src/rts_predict/games/sc2/datasets/sc2egset/reports/` |
| `DATASET_REPORTS_DIR` | `src/rts_predict/games/sc2/datasets/sc2egset/reports/` |
| `DATASET_ARTIFACTS_DIR` | `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/` |

## Datasets

| Dataset | ROADMAP | Phase status |
|---------|---------|--------------|
| sc2egset | [ROADMAP.md](datasets/sc2egset/reports/ROADMAP.md) | Phase 01 in progress |

SC2EGSet v2.1.0 — ~22,000 competitive 1v1 replays from 70+ tournaments (2016–2024).

## Reports layout

```
datasets/sc2egset/reports/
    PHASE_STATUS.yaml
    PIPELINE_SECTION_STATUS.yaml
    STEP_STATUS.yaml
    ROADMAP.md
    research_log.md
    artifacts/          # machine-generated outputs (CSV, MD, PNG)
```
