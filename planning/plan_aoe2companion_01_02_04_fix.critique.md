# Adversarial Critique — aoe2companion 01_02_04 Fix Plan

Date: 2026-04-14
Plan: planning/plan_aoe2companion_01_02_04_fix.md
Reviewer: reviewer-adversarial

## Verdict

PROCEED WITH CONDITIONS — WARNING #1 (execution timeout) is a deployment blocker; WARNING #3 (intra-match consistency framing) is a thesis defensibility risk; two other warnings should be addressed.

---

## §3.1 Column-Level Coverage After Fix

| Metric | Status After Fix | Notes |
|--------|-----------------|-------|
| null/missing count + % | PRESENT | SUMMARIZE-based; corrected to exact for `won` (T02); all others remain approximate |
| zero count | PRESENT (T03) | Added for numeric cols in matches_raw (9), ratings_raw (5), leaderboards_raw (10); profiles_raw omitted (only col is profileId identifier) — omission undocumented |
| cardinality | PRESENT | SUMMARIZE approx_unique in existing artifact |
| uniqueness ratio | PRESENT | Existing Section I |
| descriptive stats | PRESENT | min/max/mean/median/std/p05/p25/p75/p95 all 3 tables |
| distribution shape (skewness, kurtosis) | DEFERRED to 01_03 | Documented in Out of Scope; but no tracking artifact created |
| outlier detection (IQR fences, z-scores) | DEFERRED to 01_03 | Same |
| top-k frequent values | PRESENT | categorical_profiles top-30 per column |
| pattern/format frequency for strings | NOT ADDRESSED | High-cardinality strings (name, colorHex) have cardinality only; §3.1 requires pattern frequency |

---

## §3.2 Dataset-Level Coverage After Fix

| Metric | Status After Fix | Notes |
|--------|-----------------|-------|
| total row count | PRESENT | 277,099,059 matches; aux table counts present |
| duplicate row count + % | DEFERRED to 01_03 | Documented in Out of Scope; 277M rows — expensive, deferral justified |
| temporal coverage | PRESENT | Date range + monthly counts |
| class balance of target | PRESENT | won distribution exact after T02 |
| completeness matrix (missingness heatmap) | MISSING — NOT DOCUMENTED | NOT in Out of Scope or Deferred Debt; §3.2 requires it |
| correlation matrices | PARTIALLY DEFERRED | Covered under "Bivariate analysis — Future 01_02 or 01_03 step" |
| memory footprint | MISSING — NOT DOCUMENTED | NOT in Out of Scope or Deferred Debt |

---

## §3.3 Detection Tasks After Fix

| Task | Status After Fix | Notes |
|------|-----------------|-------|
| dead fields | PRESENT | leaderboards_raw.season: cardinality=1 |
| constant columns | PRESENT | Same detection |
| near-constant | PRESENT | uniqueness_ratio < 0.001 across all 4 tables |

---

## Findings

### WARNING #1 — T06 missing execution timeout [deployment blocker]

The T06 jupytext execute command lacks `--ExecutePreprocessor.timeout`. The default nbconvert timeout is 30 seconds per cell. New T01 and T03 cells add per-column loops over 277M rows; individual cells (especially SUMMARIZE on the large tables) will exceed 30 seconds and abort the notebook run.

**Fix:** Add `--ExecutePreprocessor.timeout=1800` to T06 command:
```bash
source .venv/bin/activate && poetry run jupytext --execute \
    sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py \
    --to notebook \
    --output sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.ipynb \
    --ExecutePreprocessor.timeout=1800
```

### WARNING #2 — T02 won patch has no defensive guard

`won_dist_df.loc[won_dist_df["won"].isna(), "cnt"].iloc[0]` raises IndexError if no NULL row exists. While this is guaranteed by the data (4.69% won=NULL), defensive code matters for a reproducibility-critical artifact.

**Fix:**
```python
null_rows = won_dist_df.loc[won_dist_df["won"].isna()]
assert len(null_rows) == 1, f"Expected exactly 1 NULL won group, got {len(null_rows)}"
won_null_exact = int(null_rows["cnt"].iloc[0])
```

### WARNING #3 — Intra-match consistency finding not framed for thesis defensibility

The notebook found 6.24% both_true + 4.74% both_false = 10.98% of 2-player matches with inconsistent `won` labels. The plan records these numbers in T07 but does not instruct the research log to frame the implication: these inconsistent labels impose a noise floor on the prediction target.

**Examiner's question:** "If 10.98% of your training matches have inconsistent won labels, what is the upper bound on your classifier's accuracy?"

**Fix:** T07 research log must include one sentence: "The 10.98% inconsistent 2-player match rate sets an empirical noise floor on the prediction target; a classifier trained on this data without cleaning the inconsistent labels cannot exceed ~94.5% accuracy from label noise alone. Root cause investigation deferred to 01_04."

### WARNING #4 — Deferred Debt table incomplete

Three EDA Manual §3.2 requirements are neither addressed nor documented as deferred:
- Feature completeness matrix (missingness heatmap)
- Memory footprint
- String pattern/format frequency for strings

**Fix:** Add these to the "Deferred Debt" table with rationale:
- Completeness matrix: deferred to 01_03 or skipped — note that the tabular null census serves the equivalent purpose for this dataset
- Memory footprint: deferred to 01_03 or add trivially (DuckDB file size)
- String pattern frequency: N/A for matches_raw (categorical VARCHARs are fully enumerated by top-k)

---

## Notes

1. **profiles_raw zero count omission** — Only numeric column is `profileId` (an identifier). Zero counts on identifiers are semantically meaningless. Add one sentence: "profiles_raw excluded from zero-count analysis — its only numeric column (profileId) is an identifier."

2. **Null count approximation asymmetry** — After T02, `won` has an exact null count while 54 other columns retain SUMMARIZE-derived approximate counts. Document this asymmetry in the markdown artifact: "SUMMARIZE approximate counts are used for all columns except `won`, where the exact GROUP BY value (12,985,561) is authoritative for the prediction target."

3. **T05 "context" temporal class undefined** — Six columns (server, privacy, status, country, shared, verified) are classified as "context" but the header in the classification dict defines only: identifier, pre_game, post_game, ambiguous_pre_or_post, target. Add: `"context": "Player-level metadata with unclear temporal availability; not match settings and not match outcomes."`

4. **color vs colorHex cardinality mismatch** — color (INTEGER, cardinality 43) vs colorHex (VARCHAR, cardinality 10). Color encodes more states than the hex representation implies. Add a one-sentence note in the field classification rationale.

5. **T05 rating classification** — classified as `ambiguous_pre_or_post` with note "42.46% NULL co-occurs with ratingDiff." This co-occurrence claim is based on matching NULL rates in SUMMARIZE output (both 42.46%) — not a row-level JOIN. The note should say "identical NULL rates suggest co-occurrence" not "co-occurs," until a row-level check is done.

---

## Invariant Compliance

```
#3 (temporal < T):      RESPECTED — ratingDiff and ratings_raw.rating_diff both flagged as
                         post_game; ambiguous rating flagged for Phase 02 investigation
#6 (reproducibility):   RESPECTED — new SQL in markdown artifact verbatim
#7 (no magic numbers):  RESPECTED — zero counts use exact equality; SUMMARIZE is documented
                         as approximate; no thresholds introduced without citation
#9 (step scope):        RESPECTED — no cleaning actions taken
```
