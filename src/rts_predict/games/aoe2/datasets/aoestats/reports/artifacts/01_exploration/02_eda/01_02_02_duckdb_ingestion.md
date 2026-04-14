# Step 01_02_02 -- DuckDB Ingestion: aoestats


## Tables created


| Table | Rows |
|-------|------|
| raw_matches | 30,690,651 |
| raw_players | 107,627,584 |
| raw_overviews | 1 |

## Ingestion strategy


- `raw_matches` and `raw_players`: `union_by_name = true` to handle
  variant columns across weekly files.
- `raw_overviews`: `read_json_auto` on singleton overview.json.
- All tables include `filename` provenance column.

## SQL used


See `src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py` for all
SQL constants.