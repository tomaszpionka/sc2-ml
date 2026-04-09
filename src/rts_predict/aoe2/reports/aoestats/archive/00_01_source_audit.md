# Step 0.1 — Source Inventory and Integrity Audit (aoestats)

**T_acquisition:** `2026-04-06T19:52:17.339148+00:00`

## File counts on disk

| Category | On-disk count | Expected |
|----------|--------------|---------|
| matches | 172 | 172 |
| players | 171 | 172 |

**Total on disk:** 343  
**Total in manifest:** 344

## Integrity checks

- Known download failures (status='failed' in manifest): 1
- Unexpected failures (missing or zero-byte): 0
- Size mismatches: 0
- Zero-byte files: 0

### Known failures (documented in manifest)

- `2025-11-16_2025-11-22_players.parquet`: missing_from_disk (manifest status: failed)

## Gate: PASS

Gate passes when: zero unexpected failures, zero size mismatches,
T_acquisition recorded. Known download failures (status='failed' in
manifest) are documented but do not block the gate.

- Zero unexpected failures: OK
- Zero size mismatches: OK
- T_acquisition recorded: OK