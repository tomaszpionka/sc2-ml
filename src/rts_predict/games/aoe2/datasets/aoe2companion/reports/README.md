# aoe2companion -- Raw Data Provenance

Permanent provenance record for the aoe2companion raw data. This file is
independent of the phase system and is not archived when phases are reset.
For full details, see `archive/` (original INVARIANTS.md, download report,
and Phase 0 artifacts).

---

## Acquisition

- **Download date:** 2026-04-06
- **Script:** `poetry run aoe2 download aoe2companion`
- **Branch:** `feat/aoe2-phase0-acquisition`
- **Source:** aoe2companion API (CDN-hosted parquet and CSV files)

## File inventory

- **Total files:** 4,147
  - 2,073 match parquets
  - 2,072 rating CSVs
  - 1 leaderboard parquet
  - 1 profile parquet
- **Final on-disk size:** ~9.3 GB

## Download failures and resolution

- **First run:** 17 failures (3 stale manifest size, 11 truncated, 3 broken pipe)
- **Retry run:** all 17 resolved; 0 failures final

## Reconciliation

- **Strength:** DEGRADED
- **Reason:** manifest lacks per-file row counts; limited to file-count match

## Provenance rule

Every raw table has a `filename` column populated by `filename = true` on the
source read. Removing or aliasing this column in any downstream view is
forbidden.
