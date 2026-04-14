# Adversarial Critique — sc2egset 01_02_04 Fix Plan

Date: 2026-04-14
Plan: planning/plan_sc2egset_01_02_04_fix.md
Reviewer: reviewer-adversarial

## Verdict

PROCEED WITH CONDITIONS — two warnings must be addressed before execution; three notes are informational.

---

## §3.1 Column-Level Coverage After Fix

| Metric | Status After Fix | Notes |
|--------|-----------------|-------|
| null/missing count + % | PRESENT | All 25 cols, 0% null confirmed |
| zero count | PRESENT (T01) | 15 numeric cols + elapsed_game_loops; SQ_sentinel added |
| cardinality | PRESENT | Existing artifact |
| uniqueness ratio | PRESENT | Existing artifact |
| descriptive stats | PRESENT | min/max/mean/median/std/p05/p25/p75/p95 existing |
| distribution shape (skewness, kurtosis) | DEFERRED to 01_03 | Documented in Deferred Debt table |
| outlier detection (IQR fences, z-scores) | DEFERRED to 01_03 | Documented in Deferred Debt table |
| pattern/format frequency for strings | NOT ADDRESSED | toon_id has structured format; not in plan, not deferred |
| top-k frequent values | PRESENT | categorical GROUP BY in existing artifact |

---

## §3.2 Dataset-Level Coverage After Fix

| Metric | Status After Fix | Notes |
|--------|-----------------|-------|
| total row count | PRESENT | 44,817 / 22,390 |
| duplicate row count + % | MISSING — NOT DOCUMENTED AS DEFERRED | See WARNING #1 |
| temporal coverage | PRESENT | date range + monthly counts |
| class balance of target | PRESENT | result_distribution |
| completeness matrix (missingness heatmap) | MISSING | All 0% null — trivially uniform; should state this explicitly |
| correlation matrices | DEFERRED | "Bivariate analysis — future 01_02 or 01_03 step" |
| memory footprint | MISSING — NOT DOCUMENTED | Trivial; not in plan or deferred debt |

---

## §3.3 Detection Tasks After Fix

| Task | Status After Fix | Notes |
|------|-----------------|-------|
| dead fields (100% null) | PRESENT | None found (all 0% null) |
| constant columns | PRESENT | 5 flagged: game_speed, game_speed_init, gameEventsErr, messageEventsErr, trackerEvtsErr |
| near-constant columns | PRESENT + NOTE (T03) | Interpretive note distinguishes expected categoricals from genuine degeneracy |

---

## Findings

### WARNING #1 — Duplicate row detection silently omitted [must fix or document]

EDA Manual §3.2 requires "duplicate row count and percentage." At 44,817 rows, a `COUNT(*) - COUNT(DISTINCT filename || '|' || toon_id)` query takes under one second. The plan neither includes it nor lists it in the Deferred Debt table. This is a silent gap.

**Fix:** Either add to T01:
```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(DISTINCT filename || '|' || toon_id) AS duplicate_rows
FROM replay_players_raw
```
Or add to Deferred Debt table with explicit justification.

### WARNING #2 — T04 gate condition assumes INNER JOIN completeness

The plan gate condition says `len(undecided_tie_context) == 26`. But the T04 SQL uses INNER JOINs on `filename`. If any of the 26 Undecided/Tie rows' `filename` values is absent from `replays_meta_raw`, the INNER JOIN silently drops the row — which would be a data quality finding, not an assertion failure to debug.

**Fix:** Change to LEFT JOIN, or weaker assertion: `assert len(undecided_tie_context) >= 24`.

### WARNING #3 — T05 sequencing is verbal, not structural

T05 says "Depends on: T01–T04 complete, notebook re-run complete" — but this is prose, not code. If the executor adds T01–T04 code and immediately writes T05 without re-running the notebook, the JSON artifact will not contain the new keys.

**Fix:** Add explicit sequencing instruction: "Run T01–T04 code additions first, re-run notebook end-to-end, then execute T05 against the regenerated JSON artifact."

---

## Missing from Fix Plan (EDA Manual gaps)

| Gap | Manual Ref | Assessment |
|-----|-----------|------------|
| Duplicate row detection | §3.2 | Trivial on 44,817 rows — should be added, or documented as deferred |
| String pattern/format frequency (`toon_id`) | §3.1 | `toon_id` has structured format; relevant for Invariant #2 identity resolution work; defer to identity step or acknowledge |
| Feature completeness matrix | §3.2 | Trivially all-zero — explicitly note it is skipped because all columns are 0% null |
| Memory footprint | §3.2 | Low-risk omission; add one-liner to Deferred Debt table |

---

## Notes

1. **T01** omits zero counts for `max_players`, `map_size_x`, `map_size_y` from `struct_flat`. These are integer columns where zero = data corruption. Minor gap — not required by plan scope but easy to add.

2. **T02 verification code** has a dead filter (`if k != 'classification_notes'` when iterating `replay_players_raw`). Inert — does not affect assertion correctness — but sloppy.

3. **T04 joins on `filename`** contrary to `sql-data.md` rule line 15 ("NEVER join on filename"). Unavoidable at this pipeline stage (`replay_id` not yet derived). Plan should acknowledge the rule deviation and note it migrates to `replay_id` in 01_04.

---

## Invariant Compliance

```
#3 (temporal < T):       RESPECTED — in_game fields (APM, SQ, supplyCappedPercent) classified
                          in field_classification JSON key; no feature construction in this step
#6 (reproducibility):    RESPECTED — new SQL queries mandated verbatim in markdown artifact
#7 (no magic numbers):   RESPECTED — INT32_MIN (-2147483648) is the exact sentinel from SQ.min_val;
                          0.001 threshold cited to EDA Manual §3.3
#9 (step scope):         RESPECTED — no cleaning actions, no schema changes
```
