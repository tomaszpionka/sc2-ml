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

- **Total files:** 

## Known download failure

- `2025-11-16_2025-11-22_players.parquet`: missing_from_disk, documented in
  manifest with status='failed'. This is a known gap, not silent corruption.

## Reconciliation

- **Strength:** DEGRADED
- **Reason:** manifest lacks per-file row counts; limited to file-count match

## Provenance rule
