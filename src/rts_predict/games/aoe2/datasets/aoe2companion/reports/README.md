# aoe2companion -- Raw Data Provenance

Permanent provenance record for the aoe2companion raw data. This file is
independent of the phase system and is not archived when phases are reset.

---

## Acquisition

- **Download date:** 2026-04-06
- **Script:** `poetry run aoe2 download aoe2companion`
- **Branch:** `feat/aoe2-phase0-acquisition`
- **Source:** aoe2companion API (CDN-hosted parquet and CSV files)

## File inventory

- **Total files:** 
- **Final on-disk size:**

## Download failures and resolution

- **First run:** 17 failures (3 stale manifest size, 11 truncated, 3 broken pipe)
- **Retry run:** all 17 resolved; 0 failures final

## Reconciliation

- **Strength:** DEGRADED
- **Reason:** manifest lacks per-file row counts; limited to file-count match

## Provenance rule
