# SC2EGSet — Staging

Intermediate artifacts extracted from raw replays. Each subdirectory groups
a pipeline output:

| Directory | Source | Format |
|-----------|--------|--------|
| `in_game_events/` | Path B extraction (`run_in_game_extraction`) | Parquet batches |

All contents are reproducible from raw data. Safe to delete and re-extract.
