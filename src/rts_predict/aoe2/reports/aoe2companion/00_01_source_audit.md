# Step 0.1 — Source Inventory and Integrity Audit

**T_acquisition:** `2026-04-06T21:08:57.797026+00:00`

## File counts on disk

| Category | On-disk count |
|----------|--------------|
| matches | 2073 |
| ratings | 2072 |
| leaderboards | 1 |
| profiles | 1 |

**Total on disk:** 4147  
**Total in manifest:** 4147

## Integrity checks

- Manifest failures (missing or zero-byte): 0
- Total size mismatches: 3 (0 truncated, 3 oversized)
- Zero-byte files: 0

### Oversized files (acceptable — file grew after manifest was recorded)

> These files are larger than the manifest size. This occurs when files are
> re-downloaded or updated by the CDN after the manifest was initially recorded.
> No data loss. Gate passes.

| Key | Expected bytes | Actual bytes | Diff |
|-----|---------------|-------------|------|
| leaderboard.parquet | 87304991 | 87365391 | +60400 |
| match-2026-04-04.parquet | 5156944 | 5158107 | +1163 |
| profile.parquet | 169654119 | 169703153 | +49034 |

## Gate: PASS

Gate conditions (all must hold):
- 4147 files in manifest: OK
- Zero manifest failures (missing/zero-byte): OK
- Zero truncated files (diff < 0): OK
- Oversized files (diff > 0): NOTE: 3 oversized (acceptable)
- T_acquisition recorded: OK