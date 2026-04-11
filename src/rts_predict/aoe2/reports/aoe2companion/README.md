> **Provenance note:** This file is a permanent acquisition provenance record
> from the pre-phase-system era (2026-04-07). The row counts, schema details,
> and dtype decisions recorded here have NOT been re-validated under the Phase
> 01 system. Phase 01 Step 01_01_02 (schema discovery) will produce
> authoritative schema artifacts. Do not cite numbers from this file as
> Phase-01-validated findings.

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

## Row counts at T_ingestion (2026-04-07T11:21:37Z)

| Table | Rows | Files |
|-------|------|-------|
| raw_matches | 277,099,059 | 2,073 |
| raw_ratings | 58,317,433 | 2,072 (736 data-bearing, 1,336 zero-row sparse) |
| raw_leaderboard | 2,381,227 | 1 |
| raw_profiles | 3,609,686 | 1 |

## Snapshot tables

- **raw_leaderboard:** T_snapshot = 2026-04-06T21:08:57Z
- **raw_profiles:** T_snapshot = 2026-04-06T21:09:07Z
- **WARNING:** These tables MUST NOT be joined to historical matches as if
  they were time-varying. They reflect state at T_snapshot only.

## Sparse rating regime

- **Boundary date:** 2025-06-26
- **Sparse files (< 1024 bytes):** 1,791
- **Date range:** 2020-08-01..2025-06-26

## Dtype strategy

- **raw_ratings:** explicit dtype map (auto_detect produced inconsistent types
  for profile_id, games, rating, date, leaderboard_id, season, rating_diff)
- **Artifact:** `archive/00_03_dtype_decision.json`

## Reconciliation

- **Strength:** DEGRADED
- **Reason:** manifest lacks per-file row counts; limited to file-count match

## Provenance rule

Every raw table has a `filename` column populated by `filename = true` on the
source read. Removing or aliasing this column in any downstream view is
forbidden.
