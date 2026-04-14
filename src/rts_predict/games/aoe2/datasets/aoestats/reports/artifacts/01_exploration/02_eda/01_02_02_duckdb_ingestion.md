# Step 01_02_02 -- DuckDB Ingestion: aoestats


## Tables created


| Table | Rows |
|-------|------|
| matches_raw | 30,690,651 |
| players_raw | 107,627,584 |
| overviews_raw | 1 |

## Ingestion strategy


- `matches_raw` and `players_raw`: `union_by_name = true` to handle
  variant columns across weekly files.
- `overviews_raw`: `read_json_auto` on singleton overview.json.
- All tables include `filename` provenance column.

## SQL used


See `src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py` for all
SQL constants.