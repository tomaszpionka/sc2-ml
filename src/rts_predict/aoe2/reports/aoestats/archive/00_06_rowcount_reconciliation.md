# Step 0.6 — Row-count Reconciliation (aoestats)

**Gate: PASS**  
**Reconciliation strength: DEGRADED**

> **DEGRADED reason:** The _download_manifest.json records file checksums
> but not per-file row counts. Reconciliation is limited to file-count match.

> **Notes:**
> - 1 entries had status='failed' in manifest: 2025-11-16_2025-11-22_players.parquet — excluded from expected file count.

## SQL used

```sql
-- Expected: 172
SELECT count(DISTINCT filename) AS n_files FROM raw_matches;

-- Expected: 171
SELECT count(DISTINCT filename) AS n_files FROM raw_players;

SELECT filename, count(*) AS row_count
FROM raw_matches
GROUP BY filename
ORDER BY row_count;

SELECT filename, count(*) AS row_count
FROM raw_players
GROUP BY filename
ORDER BY row_count;
```

## File-count assertions

| Table | Expected | Actual | OK? |
|-------|----------|--------|-----|
| raw_matches | 172 | 172 | OK |
| raw_players | 171 | 171 | OK |

## Per-file row-count distribution summary

### raw_matches (172 files)

Min rows: 11615  
Max rows: 264843

### raw_players (171 files)

Min rows: 53556  
Max rows: 930677