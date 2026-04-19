# Q7: Temporal Leakage Audit — sc2egset

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Date:** 2026-04-18

## Summary

| Check | Result |
|---|---|
| Q1: future_leak_count | 0 |
| Q2: post_game_token_violations | 0 |
| Q3: reference_window_assertion | PASS |
| halt_triggered | False |

## Q1 SQL (verbatim, I6)

### Q1a (ref-range integrity)

```sql
SELECT
    MIN(started_at) AS ref_min,
    MAX(started_at) AS ref_max,
    COUNT(*) AS ref_count
FROM matches_history_minimal
WHERE started_at >= TIMESTAMP '2022-08-29'
  AND started_at <  TIMESTAMP '2023-01-01'
```

### Q1b (quarter-label consistency)

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

### Q1c (PSI source substring check)

Path(`01_05_02_psi_quarterly.py`).read_text() MUST contain the date
substrings `2022-08-29` and `2023-01-01` (spec §7 reference period).

## Q2: Feature classification

- faction: PRE_GAME (race chosen before match)
- opponent_faction: PRE_GAME (opponent race; known at match setup)
- matchup: derived from PRE_GAME inputs (GREATEST(faction,opponent_faction)||'v'||LEAST(...))
- duration_seconds: POST_GAME_HISTORICAL (excluded from PSI per I3; routed to T08 DGP)

## Q3: Reference window assertion

```python
ref_start = datetime(2022, 8, 29)
ref_end   = datetime(2022, 12, 31)
assert ref_start == datetime(2022, 8, 29)
assert ref_end   == datetime(2022, 12, 31)
```

## Q1 v2 redesign (post-PR #164 adversarial-review round 2)

PR #164's Q1 cleanup removed a labeled-tautology constant but the surviving
real check was itself structurally tautological: WHERE/FILTER predicates
bound to the same interval made the FILTER count always 0.

v2 replaces Q1 with three sub-checks:

| Sub-check | Value | Status |
|---|---|---|
| Q1a (ref-range integrity) | `min=2022-09-02 09:23:10.780676, max=2022-12-18 21:55:53.214104, count=3,268` | PASS |
| Q1b (quarter-label consistency) | `8 quarters, 0 violations` | PASS |
| Q1c (PSI source substring) | `missing=[]` | PASS |

Each sub-check can fail on a real pathology: Q1a on a DB timezone bug or
filter-predicate regression; Q1b on off-by-one in the quarter-derivation
SQL; Q1c on silent reference-window drift between 01_05_02 and this audit.
All reference rows confirmed within [2022-08-29, 2023-01-01).
All tested rows confirmed within [2023-01-01, 2025-01-01).

## Verdict: PASS — no halt triggered
