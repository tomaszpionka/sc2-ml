# aoestats -- Raw Data Provenance

Permanent provenance record for the aoestats raw data. This file is
independent of the phase system and is not archived when phases are reset.
For full details, see `archive/` (original INVARIANTS.md and Phase 0
artifacts).

---

## Acquisition

- **Download date:** 2026-04-06
- **Script:** `poetry run aoe2 download aoestats --force`
- **Branch:** `feat/aoe2-phase0-acquisition`
- **Source:** aoestats.io

## File inventory

- **Weekly entries:** 188 (2022-08-28 to 2026-04-04)
- **Non-zero weeks:** 172 (16 zero-match weeks skipped)
- **Total files:** 344 (172 match parquets + 172 player parquets, minus 1 known failure = 343 on disk)

## Known download failure

- `2025-11-16_2025-11-22_players.parquet`: missing_from_disk, documented in
  manifest with status='failed'. This is a known gap, not silent corruption.

## Row counts at T_ingestion (2026-04-07T16:36:52Z)

| Table | Rows | Files |
|-------|------|-------|
| raw_matches | 30,690,651 | 172 |
| raw_players | 107,627,584 | 171 |

## Schema drift

Type drift resolved by DuckDB `union_by_name = true` (widest compatible type):

**raw_matches:**
- `raw_match_type`: DOUBLE to BIGINT

**raw_players:**
- `feudal_age_uptime`: DOUBLE to INTEGER
- `castle_age_uptime`: DOUBLE to INTEGER
- `imperial_age_uptime`: DOUBLE to INTEGER
- `profile_id`: DOUBLE to BIGINT
- `opening`: VARCHAR to INTEGER

## Reconciliation

- **Strength:** DEGRADED
- **Reason:** manifest lacks per-file row counts; limited to file-count match

## Provenance rule

Every raw table has a `filename` column populated by `filename = true` on the
source read. Removing or aliasing this column in any downstream view is
forbidden.
