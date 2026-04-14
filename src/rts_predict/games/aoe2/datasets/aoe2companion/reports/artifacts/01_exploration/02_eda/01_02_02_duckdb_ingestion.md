# Step 01_02_02 — DuckDB Ingestion: aoe2companion


## Tables created


| Table | Rows |
|-------|------|
| `matches_raw` | 277,099,059 |
| `ratings_raw` | 58,317,433 |
| `leaderboards_raw` | 2,381,227 |
| `profiles_raw` | 3,609,686 |

## Dtype strategy: `explicit`


**Rationale:** read_csv_auto inferred all 7 columns as VARCHAR on the full 2,072-file ratings load. Explicit BIGINT/TIMESTAMP types required to preserve numeric fidelity. Confirmed in Step 01_02_01 ratings_type_inference artifact.

## NULL rates


- `matches_raw.won`: 12,985,561 NULLs / 277,099,059 total rows (4.69%)
- `ratings_raw.profile_id`: 0 NULLs

## Invariant I10


All four `filename` columns verified relative (no leading `/`, contains `/`).