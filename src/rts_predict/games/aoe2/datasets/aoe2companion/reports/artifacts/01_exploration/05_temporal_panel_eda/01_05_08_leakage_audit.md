# 01_05_08 Temporal Leakage Audit — aoe2companion

spec: reports/specs/01_05_preregistration.md@7e259dd8

## Summary

| Check | Status | Description |
|---|---|---|
| check_1_temporal_bin_edges | PASS | v2 post-PR #162 adversarial-review fix: the v1 Check 1a/1b had a mutually-exclus... |
| check_2_post_game_token_scan | PASS | AST/regex scan of T03/T04 notebooks for POST_GAME tokens in pre-game feature sel... |
| check_3_normalization_window | PASS | Assert T03 JSON frozen_reference_edges.ref_start == '2022-08-29' and ref_end == ... |

**Overall verdict: PASS**

## Check 1 Redesign Note (v2, post-PR #162 adversarial review)

The v1 implementation of Check 1a/1b (pre-fix/01-05-aoec-adversarial-followup)
had a mutually-exclusive WHERE clause `(A ∧ B) ∧ (¬A ∨ ¬B)` that returned 0
regardless of data — a tautology posing as a gate. The adversarial reviewer
of PR #162 flagged this as BLOCKER 2. The v2 replacement below provides three
substantive sub-checks.

- **Check 1a (ref-cohort range integrity):** `min(started_at) = 2022-08-29 00:00:31`,
  `max(started_at) = 2022-12-31 23:59:58`, `count = 4,013,826` → PASS
- **Check 1b (quarter-label consistency):** 8 quarters checked,
  0 violations → PASS
- **Check 1c (PSI ref SQL cites §7 bounds):** missing tokens = `[]` → PASS

## Check 2: POST_GAME token scan

Scanned: 01_05_02_psi_shift.py, 01_05_03_stratification.py
Tokens scanned: ['duration_seconds', 'finished', 'is_duration_negative', 'is_duration_suspicious', 'ratingDiff']
Tokens found in pre-game context: NONE

## Check 3: Normalization window constants

T03 JSON asserts:
- ref_start = '2022-08-29T00:00:00' (expected '2022-08-29'): OK
- ref_end = '2022-12-31T00:00:00' (expected '2022-12-31'): OK
- assertion_passed = True

## Reference period row hash (M-06)

MD5 of (match_id || player_id) for reference period rows: `f9aa56bb5f22e247615fb9e33f30e688`
Use for reproducibility verification across DB rebuilds (reservoir-sample caveat applies).

## SQL

### Check 1a (ref-range integrity)
```sql

SELECT
    MIN(started_at) AS ref_min,
    MAX(started_at) AS ref_max,
    COUNT(*) AS ref_count
FROM matches_history_minimal
WHERE started_at >= TIMESTAMP '2022-08-29'
  AND started_at <  TIMESTAMP '2023-01-01'

```

### Check 1b (quarter-label consistency)
```sql

SELECT
    derived_quarter,
    MIN(started_at) AS qmin,
    MAX(started_at) AS qmax,
    COUNT(*) AS n
FROM (
    SELECT
        started_at,
        CONCAT(
            CAST(EXTRACT(YEAR FROM started_at) AS VARCHAR),
            '-Q',
            CAST(CEIL(EXTRACT(MONTH FROM started_at) / 3.0) AS INTEGER)::VARCHAR
        ) AS derived_quarter
    FROM matches_history_minimal
    WHERE started_at >= TIMESTAMP '2023-01-01'
      AND started_at <  TIMESTAMP '2025-01-01'
)
GROUP BY derived_quarter
ORDER BY derived_quarter

```
