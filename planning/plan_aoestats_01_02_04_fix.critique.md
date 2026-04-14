# Adversarial Critique — aoestats 01_02_04 Fix Plan

Date: 2026-04-14
Plan: planning/plan_aoestats_01_02_04_fix.md
Reviewer: reviewer-adversarial

## Verdict

PROCEED WITH CONDITIONS — T01 bug fix verified correct; WARNING #3 (outlier_pct denominator undocumented) must be addressed; two other warnings should be addressed before execution.

---

## T01 Bug Fix Verification — CONFIRMED CORRECT

**Bug location confirmed.** Verified in notebook:
- matches_raw loop: line 461 — `WHERE {expr} IS NOT NULL` present
- players_raw loop: line 507 — `WHERE {expr} IS NOT NULL` present
- profile_id query: line 533 — `WHERE profile_id IS NOT NULL` present

**Fix correctness confirmed:**
1. Removing `WHERE {expr} IS NOT NULL` is correct — `COUNT(*) - COUNT({expr})` correctly computes NULLs without the filter.
2. `SUM(CASE WHEN {expr} = 0 THEN 1 ELSE 0 END)` is unaffected — NULL=0 evaluates to NULL (UNKNOWN), not 1, so NULL rows contribute 0.
3. PERCENTILE_CONT, AVG, MEDIAN, STDDEV, MIN, MAX all skip NULLs natively in DuckDB — removing WHERE IS NOT NULL does not change percentile or mean values.
4. Histogram WHERE clause correctly preserved — binning requires non-NULL values.

**n_null fix confirmed:** `feudal_age_uptime` will correctly report n_null≈93,726,448 after fix (currently shows 0.0).

---

## §3.1 Column-Level Coverage After Fix

| Metric | Status After Fix | Notes |
|--------|-----------------|-------|
| null/missing count + % | FIXED (T01) | Currently 0.0 for all numeric cols; T01 removes WHERE IS NOT NULL |
| zero count | PRESENT | Already in existing artifact as n_zero — unaffected by bug |
| cardinality | PRESENT | In categorical_matches, categorical_players, uniqueness sections |
| uniqueness ratio | PRESENT | Both overall and non-null variants |
| descriptive stats | PRESENT | min/max/mean/median/std/p05/p25/p75/p95; values unchanged by T01 (DuckDB always skips NULLs in aggregates) |
| distribution shape (skewness, kurtosis) | DEFERRED to 01_03 | Documented in Deferred Debt table (plan line 500) |
| outlier detection (IQR fences) | ADDED (T02) | IQR fence counts for all numeric cols |
| outlier detection (z-scores) | DEFERRED to 01_03 | Documented in Deferred Debt table (plan line 501) |
| top-k frequent values | PRESENT | categorical_matches and categorical_players with full value lists |
| pattern/format frequency for strings | N/A | No free-text string columns requiring regex pattern analysis |

---

## §3.2 Dataset-Level Coverage After Fix

| Metric | Status After Fix | Notes |
|--------|-----------------|-------|
| total row count | PRESENT | matches_raw=30,690,651; players_raw=107,627,584 |
| duplicate row count + % | MISSING — NOT DOCUMENTED AS DEFERRED | See WARNING #1 |
| temporal coverage | PRESENT | temporal_range section |
| class balance of target (winner) | PRESENT | Near-perfect 50/50 |
| completeness matrix (missingness heatmap) | MISSING — NOT DOCUMENTED AS DEFERRED | See WARNING #2 |
| correlation matrices | NOT PRESENT | Appropriate deferral for univariate step |
| memory footprint | MISSING | Low impact; see NOTE #1 |

---

## §3.3 Detection Tasks After Fix

| Task | Status After Fix | Notes |
|------|-----------------|-------|
| dead fields (100% null) | PRESENT | None found |
| constant columns | PRESENT | game_type, game_speed flagged |
| near-constant columns | PRESENT | 0.001 threshold cited to EDA Manual §3.3 |

---

## T02 IQR Methodology Assessment

**IQR=0 edge case:** No columns in this dataset have IQR=0 (verified: feudal_age_uptime p25=611.52, p75=774.38; all other numeric cols have non-zero IQR). The early-return handler exists but will not trigger. Not a blocker.

**Tukey 1.5 factor:** Cited to Tukey 1977, p. 44. Invariant #7 compliant.

**FIELD CLASSIFICATION count:** Manually counted: matches_raw = 18 entries, players_raw = 14 entries, total = 32. Matches both schema YAMLs. Correct.

**ROADMAP consistency:** ROADMAP.md already specifies `01_02_04_univariate_census.json/.md` (lines 324-325). No ROADMAP update needed — the plan correctly omits one.

---

## Findings

### WARNING #1 — Duplicate row count missing, not documented as deferred

EDA Manual §3.2 requires "duplicate row count and percentage." Not in existing artifact, not in fix plan, not in Deferred Debt table. For 107M player rows, a full hash-based duplicate check is expensive — deferral is reasonable — but the omission must be documented.

**Fix:** Add to Deferred Debt table:
```
| Duplicate row detection | 01_03 | 107M rows — full duplicate check expensive; defer to systematic profiling |
```
Or add a cheap join-key duplicate check: `SELECT COUNT(*) - COUNT(DISTINCT game_id || '_' || profile_id) FROM players_raw`.

### WARNING #2 — Missingness heatmap missing, not documented as deferred

EDA Manual §3.2 requires "a feature completeness matrix (heatmap of missingness across all columns)." The null census tables serve the same informational purpose for this dataset (missingness is concentrated in age uptimes + opening, all tied to replay_enhanced). But the omission should be acknowledged.

**Fix:** Add to Deferred Debt table:
```
| Completeness matrix (missingness heatmap) | 01_03 | Tabular null census provides equivalent information; visual heatmap deferred |
```

### WARNING #3 — outlier_pct denominator undocumented in artifact [must fix]

The `compute_iqr_outliers` function computes `outlier_pct = 100.0 * total / nonnull` — percentage of non-NULL values that are outliers. For `feudal_age_uptime` (87% NULL), a column could show 5% outliers among non-NULL values but only 0.65% of all rows. This distinction is not stated anywhere in the artifact output.

**Examiner's question:** "You report feudal_age_uptime has X% outliers. Is that X% of all rows or X% of the 13% that have values?" — The candidate cannot answer from the artifact.

**Fix:** Add `denominator` field to each outlier entry:
```python
return {
    ...
    "outlier_pct": ...,
    "denominator": "pct_of_non_null_values",
    ...
}
```
Or add a top-level note in the `outlier_counts_players` section: `"note": "outlier_pct is % of non-NULL values, not % of all rows."`.

---

## Notes

1. **Memory footprint missing (§3.2).** Trivial: `os.path.getsize('data/db/db.duckdb')`. Low impact but an easy add.

2. **Branch name mismatch.** Plan uses `chore/roadmap-researchlog-step-01-02-03` for Category A work on step 01_02_04. Housekeeping issue — does not affect methodology. The existing branch can be reused since all work stays in `planning/` and the sandbox/reports scope.

3. **IQR=0 handler edge case.** For a hypothetical column where p25=p75=X and values exist outside X, the current handler returns outlier_total=0. No such column exists in this dataset. The handler's `note` field documents the limitation. Not a blocker.

4. **match_rating_diff percentiles unaffected by T01 fix.** After removing WHERE IS NOT NULL, PERCENTILE_CONT still skips NULLs by design. The near-zero mean (0.0) and symmetric distribution (p05=-59, p95=59) will remain unchanged. The empirical leakage test for this column should be prioritized in the next planning step.

5. **starting_age classified as pre_game with near-constant values** (cardinality=2: "dark" 30,690,632; "standard" 19). Correct classification but the near-constant nature is worth noting in the field rationale.

---

## Invariant Compliance

```
#3 (temporal < T):      RESPECTED — new_rating flagged as post_game;
                         match_rating_diff classified as deferred with empirical test documented;
                         duration/irl_duration flagged as post_game
#6 (reproducibility):   RESPECTED — new SQL in markdown artifact verbatim; Tukey 1977 cited
#7 (no magic numbers):  RESPECTED — IQR factor 1.5 cited to Tukey 1977; 0.001 threshold cited
                         to EDA Manual §3.3
#9 (step scope):        RESPECTED — no cleaning actions; only profiling additions
```
