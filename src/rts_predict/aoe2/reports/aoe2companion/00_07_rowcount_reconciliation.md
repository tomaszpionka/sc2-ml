# Step 0.7 — Row-count Reconciliation

**Gate: PASS**  
**Reconciliation strength: DEGRADED**

> **DEGRADED reason:** The _download_manifest.json records file sizes and
> download status but not per-file row counts. Reconciliation is limited to
> (a) exact file-count match and (b) zero-row rating files matching the
> sparse-regime population from Step 0.3.

## SQL used

```sql
-- Expected: 2073
SELECT count(DISTINCT filename) AS n_files FROM raw_matches;

-- Expected: 2072
SELECT count(DISTINCT filename) AS n_files FROM raw_ratings;

-- Expected: 1
SELECT count(DISTINCT filename) AS n_files FROM raw_leaderboard;

-- Expected: 1
SELECT count(DISTINCT filename) AS n_files FROM raw_profiles;

-- Per-file row count distributions
SELECT filename, count(*) AS row_count
FROM raw_matches
GROUP BY filename
ORDER BY row_count;

SELECT filename, count(*) AS row_count
FROM raw_ratings
GROUP BY filename
ORDER BY row_count;
```

## File-count assertions

**Note for raw_ratings:** Header-only sparse files (63 bytes) produce 0 rows
and do not appear as distinct filenames in DuckDB. The 'effective' count
adds on-disk zero-row files back for the manifest comparison.

| Table | Expected | DuckDB distinct | Zero-row files | Effective | OK? |
|-------|----------|----------------|---------------|----------|-----|
| raw_matches | 2073 | 2073 | N/A | 2073 | OK |
| raw_leaderboard | 1 | 1 | N/A | 1 | OK |
| raw_profiles | 1 | 1 | N/A | 1 | OK |
| raw_ratings | 2072 | 736 | 1336 | 2072 | OK |

**Zero-row rating files on disk (header-only sparse):** 1336

## Per-file row-count distribution summary

### raw_matches

Total files: 2073  
Min rows per file: 15735  
Max rows per file: 522055

### raw_ratings (data-bearing files only)

Data-bearing files in DuckDB: 736  
Zero-row (header-only) files on disk: 1336  
Min rows (non-zero files): 1  
Max rows: 288089