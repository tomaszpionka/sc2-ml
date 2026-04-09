# aoe2companion Raw Data Download Report

**Date:** 2026-04-06
**Branch:** feat/aoe2-phase0-acquisition
**Script:** `poetry run aoe2 download aoe2companion`

---

## Summary

| Category | Expected | Downloaded | Failed | On-disk size |
|----------|----------|-----------|--------|-------------|
| match parquets | 2,073 | 2,058 | 15 | 6.93 GB |
| rating CSVs | 2,072 | 2,072 | 0 | 2.64 GB |
| leaderboard parquet | 1 | 0 | 1 | 0 |
| profile parquet | 1 | 0 | 1 | 0 |
| **Total** | **4,147** | **4,130** | **17** | **~9.57 GB** |

---

## Failures (17 files)

### Category A — Live CDN files with stale manifest size (3 files)

These files are updated on the CDN independently of the manifest snapshot.
The manifest `size` field becomes stale within hours.

| File | Manifest size (B) | CDN delivered (B) | Delta |
|------|------------------|-------------------|-------|
| `leaderboard.parquet` | 87,304,991 | 87,365,391 | +60,400 |
| `profile.parquet` | 169,654,119 | 169,703,153 | +49,034 |
| `match-2026-04-04.parquet` | 5,156,944 | 5,158,107 | +1,163 |

**Resolution:** Size check relaxed for `leaderboard`/`profile` categories
(`expected_size=None` → only checks file exists and is non-empty). For all
categories, oversized downloads are now accepted with a warning rather than
rejected. Re-run will acquire all three files.

### Category B — Truncated downloads (11 files, got < expected)

Network connections dropped mid-transfer. The downloaded bytes were fewer than
the manifest size, indicating the files are incomplete.

| File | Expected (B) | Got (B) | Ratio |
|------|-------------|---------|-------|
| `match-2020-09-03.parquet` | 510,115 | 376,832 | 74% |
| `match-2021-02-18.parquet` | 922,316 | 475,136 | 52% |
| `match-2021-06-17.parquet` | 805,989 | 622,592 | 77% |
| `match-2021-06-21.parquet` | 878,530 | 638,976 | 73% |
| `match-2021-08-20.parquet` | 1,001,688 | 770,048 | 77% |
| `match-2021-08-31.parquet` | 785,754 | 557,056 | 71% |
| `match-2021-09-01.parquet` | 695,848 | 409,600 | 59% |
| `match-2021-12-26.parquet` | 1,076,561 | 966,656 | 90% |
| `match-2022-02-08.parquet` | 1,028,582 | 737,280 | 72% |
| `match-2022-02-25.parquet` | 960,194 | 606,208 | 63% |

**Resolution:** Size check retained — truncated files are correctly rejected and
deleted. Re-run will retry all 10. The `< expected_size` guard remains strict.

### Category C — Broken pipe (3 files)

Network connection reset mid-transfer (no bytes written or partial).

| File | Error |
|------|-------|
| `match-2020-08-20.parquet` | `[Errno 32] Broken pipe` |
| `match-2020-10-19.parquet` | `[Errno 32] Broken pipe` |
| `match-2022-03-17.parquet` | `[Errno 32] Broken pipe` |

**Resolution:** Retry on next run.

---

## Code fix applied

**File:** `src/rts_predict/aoe2/data/aoe2companion/acquisition.py`

Three changes:

1. **`is_already_downloaded(target_path, expected_size: int | None)`** — accepts
   `None` for live files; checks `on_disk >= expected` rather than exact equality.

2. **`download_file(..., expected_size: int | None)`** — rejects only if
   `actual < expected` (truncation); logs a warning if `actual > expected` (CDN
   update) and accepts the file.

3. **`run_download`** — passes `expected_size=None` for `leaderboard` and
   `profile` category entries.

---

## Re-run

```bash
poetry run aoe2 download aoe2companion
```

The 4,130 already-downloaded files are skipped (size check passes). Only the
17 failed files are retried.

---

## Retry run result (2026-04-06)

After applying the size-check relaxation, a re-run was executed:

- **Downloaded:** 17 (the 17 previously failed files)
- **Skipped:** 4,130 (already on disk, size check passed)
- **Failed:** 0

All 4,147 targets acquired. Final on-disk state:

| Directory | Files | Size |
|-----------|-------|------|
| matches | 2,073 | 6.5 GB |
| leaderboards | 1 | 97 MB |
| profiles | 1 | 176 MB |
| ratings | 2,072 | 2.5 GB |
| **Total** | **4,147** | **~9.3 GB** |

Download log: `src/rts_predict/aoe2/data/aoe2companion/raw/_download_manifest.json`
