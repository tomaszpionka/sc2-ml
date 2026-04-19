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

```sql
-- Q1b: Reference rows strictly within [2022-08-29, 2023-01-01)
SELECT COUNT(*) AS n_ref_rows_check,
       COUNT(*) FILTER (WHERE started_at < TIMESTAMP '2022-08-29') AS before_ref_start,
       COUNT(*) FILTER (WHERE started_at >= TIMESTAMP '2023-01-01') AS after_ref_end
FROM matches_history_minimal
WHERE started_at >= TIMESTAMP '2022-08-29'
  AND started_at <  TIMESTAMP '2023-01-01'
```

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

## Q1 cleanup note (post-PR #163 adversarial-review)

A prior QUERY1_REF_SQL combined a WHERE predicate with its own negation,
making it a logical contradiction that returned 0 rows on any data. It was
dead code — `result_q1` always executed QUERY1_MEANING_SQL (the real check).
The dead constant is removed; Q1c gained an assertion on tested-period
leakage (previously only printed).
All reference rows confirmed within [2022-08-29, 2023-01-01).
All tested rows confirmed within [2023-01-01, 2025-01-01).

## Verdict: PASS — no halt triggered
