---
plan: planning/plan_aoe2companion_01_03_01.md
reviewer: reviewer-adversarial (claude-opus-4-6)
date: 2026-04-15
verdict: REVISE BEFORE EXECUTION
blockers: 2
warnings: 4
passed: 8
---

# Adversarial Critique: plan_aoe2companion_01_03_01.md

## Blockers

### B1. Skewness/kurtosis sample (Cell 10) omits 3 of 9 numeric columns and applies compounding listwise deletion that biases the sample [I7, Lens 2, Lens 3]

**Location:** Plan lines 352-397 (Cell 10)

**Finding — missing columns:** The census `matches_raw_numeric_stats` contains
9 columns: rating, ratingDiff, population, slot, color, team, speedFactor,
treatyLength, internalLeaderboardId. Cell 10's `sample_numeric_cols` list
contains only 7 — `slot`, `color`, and `team` are omitted, while
`duration_min` (a derived column not in the census numeric_stats) is added.

This means:
- `slot` (cardinality=9, p25=0, p75=3): skewness/kurtosis never computed.
- `color` (cardinality=43, p25=2, p75=5): skewness/kurtosis never computed.
- `team` (cardinality=31, p25=1, p75=2, null_pct=4.9%): skewness/kurtosis never computed.

Cell 13 (line 511) checks `if col in skewness_kurtosis:` and silently skips
columns not in the dict. The column_profiles for slot, color, and team will
have no `skewness` or `kurtosis` keys. This is an incomplete profile for a step
that claims to provide "complete statistical profile of every column."

**Finding — compounding listwise deletion:** The WHERE clause applies
simultaneous NOT NULL filters for 6 columns:

```sql
WHERE rating IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND internalLeaderboardId IS NOT NULL
```

Census null rates: rating=42.46%, ratingDiff=42.46% (co-occurring),
population=0.16%, treatyLength=0.09%, internalLeaderboardId=0.48%. After
BERNOULLI 0.02% (~55K rows), the rating/ratingDiff NULL filter alone removes
~42% of the sample. The remaining ~32K rows then face further filters.

The final `n_sample` for skewness/kurtosis reflects only rows where ALL columns
are non-null simultaneously. The skewness of `population` is then computed on a
subsample that excludes all rows where rating is NULL — but population's own
NULL rate is only 0.16%. This introduces a selection bias: the distributional
shape of population is measured only on the subset of matches that have a
rating, which may differ from the full population (e.g., unranked matches
may have different population settings).

**Evidence:** Census JSON `matches_raw_null_census` at
`01_02_04_univariate_census.json` lines 145-149 (population: null_count=443,358,
null_pct=0.16%) vs lines 3-10 (rating: null_count=117,621,413, null_pct=42.46%).

**Required fix:**
1. Add slot, color, and team to the skewness/kurtosis computation (or explicitly
   document why they are excluded with an I7-compliant justification).
2. Compute skewness/kurtosis per column independently (per-column dropna) instead
   of listwise deletion. Fetch the sample without the compound NULL filter, then
   apply `dropna()` per column before computing scipy stats. This is what Cell 22
   (QQ/ECDF sample) already does correctly — it fetches with minimal filters and
   uses `df_viz[col].dropna()` per column.

**What breaks:** The profile JSON claims to be a complete systematic profile
but is missing shape statistics for 3 of 9 numeric columns. An examiner asks
"What is the skewness of the team column?" and the answer is "We did not
compute it." Additionally, the shape statistics for near-zero-NULL columns
like population are computed on a biased subsample (~57% of rows) rather than
the full distribution.

### B2. DuckDB comment says "does not have built-in skewness/kurtosis" — this is false for DuckDB 1.5.1 [I7]

**Location:** Plan line 353

**Finding:** Cell 10 contains the comment:
```python
# DuckDB does not have built-in skewness/kurtosis; compute via scipy on sample
```

DuckDB (since version 0.8+) provides the aggregate functions `skewness(x)` and
`kurtosis(x)` (excess kurtosis). These are available in the SQL interface and
documented in the DuckDB aggregate functions reference. The project pins DuckDB
1.5.1 per `pyproject.toml`.

The plan's approach — pulling ~55K rows into Python and computing via scipy —
is scientifically valid but unnecessarily imprecise. DuckDB's `skewness()` and
`kurtosis()` compute exact values over all 277M rows (for non-NULL rows of
each column independently), avoiding both the sampling error and the listwise
deletion bias identified in B1.

**Evidence:** DuckDB aggregate functions documentation lists `skewness(x)` and
`kurtosis(x)`. The plan's comment at line 353 makes a false factual claim
about the tool's capabilities.

**Required fix:** Either (a) use DuckDB's native `skewness()` and `kurtosis()`
for exact full-table computation (preferred — eliminates sampling error entirely
and resolves B1's listwise deletion bias simultaneously), or (b) correct the
comment to acknowledge the functions exist and document why the sampled scipy
approach was chosen instead (e.g., consistency with QQ/ECDF sample pipeline).
If (b), the listwise deletion bias from B1 must still be fixed independently.

**What breaks:** The plan makes a verifiably false claim about DuckDB's
capabilities. If an examiner or reviewer checks, the candidate's credibility
on tool knowledge is undermined. More importantly, the opportunity to compute
exact shape statistics on 277M rows — which DuckDB can do in a single pass —
is missed in favor of approximate statistics from a biased subsample.

## Warnings

### W1. `rating` classified as AMBIGUOUS in the plan but 01_02_06 artifact heading says "RESULT PENDING" — terminology mismatch [I3, I9]

**Location:** Plan line 277 (Cell 6), plan line 73 (Assumptions)

**Evidence:** The 01_02_06 bivariate EDA artifact (`01_02_06_bivariate_eda.md`,
line 17) says:

```
### rating (Q2 -- RESULT PENDING)
```

The same artifact's plot index table (line 28) says:
```
| 2 | Rating by Outcome (Q2) | ... | AMBIGUOUS -- see findings |
```

And the statistical test section (line 54) says:
```
- **Temporal status:** AMBIGUOUS (Inv. #3 -- temporal status unresolved)
```

The artifact itself uses two different labels for the same column: "RESULT
PENDING" in the heading and "AMBIGUOUS" in the plot index and statistical tests.
The plan picks "AMBIGUOUS" which matches two of three usages and also matches
the census field_classification (01_02_04): `"ambiguous_pre_or_post"`.

**Risk if ignored:** Minor — the plan's choice of AMBIGUOUS is defensible and
matches the census plus the majority of 01_02_06 references. But the heading
"RESULT PENDING" implies the investigation was inconclusive and Phase 02
verification is needed, while "AMBIGUOUS" could be read as a stable
classification. The plan should note that "AMBIGUOUS" means "unresolved;
requires Phase 02 row-level verification with ratings_raw" to prevent
misinterpretation.

### W2. BERNOULLI 0.02% sample fraction is copied from user specification without statistical justification [I7]

**Location:** Plan line 292 (Cell 7)

**Evidence:** The comment says: `# 0.02% BERNOULLI -> ~55K rows (per user
spec, sufficient for QQ/ECDF)`. The phrase "per user spec" traces the number
to a human decision, not to a statistical criterion.

For QQ plots and ECDFs, N=55,000 is more than adequate — the standard error
of the p-th sample quantile at N=55K is approximately
`sqrt(p(1-p)/(N*f(q_p)^2))` which is negligible for any practically relevant
quantile. The issue is not the number's adequacy but its provenance: I7
requires "derived from data or citation," and "user spec" is neither.

The predecessor notebook 01_02_06 derived its sample fraction from
`TARGET_SAMPLE_ROWS / total_rows * 100` at runtime. This plan partially
follows that pattern (line 294: `TARGET_SAMPLE_ROWS = int(total_rows *
SAMPLE_PCT / 100)`), but the initial `SAMPLE_PCT = 0.02` is the magic number.

**Risk if ignored:** Low — 55K is defensible for QQ/ECDF by any standard
reference. But the plan's I7 claim ("sample fraction derived from census
total_rows at runtime") is technically misleading: the fraction is hardcoded
at 0.02%, and only the expected count is derived from total_rows. A one-line
justification (e.g., "N > 10,000 is sufficient for reliable QQ plots per
[Wilk & Gnanadesikan 1968]") would satisfy I7.

### W3. Skewness/kurtosis minimum sample assertion is too low at 1000 [Lens 2, I7]

**Location:** Plan line 384 (Cell 10), line 872 (Cell 22)

**Evidence:** `assert n_sample >= 1000, f"Sample too small: {n_sample}"`.

Kurtosis estimators have well-known finite-sample bias. The standard error
of excess kurtosis is approximately `sqrt(24/N)`. At N=1000, SE(kurtosis) ~
0.155, which detects gross non-normality but not precise shape differences.

The plan expects ~55K rows before listwise deletion and probably ~32K after
(given the 42% rating NULL rate). The assertion at 1000 will never trigger
in practice. But it communicates intent: "1000 is our minimum acceptable
sample." A more defensible minimum would be 5000 (SE(kurtosis) ~ 0.069),
documented with the formula.

**Risk if ignored:** Low in practice — the actual sample will be much larger
than 1000. But the assertion value is a magic number (I7) and the plan should
document why 1000 was chosen over a statistically motivated threshold.

### W4. Cell 11 IQR outlier counts run one full-table scan per numeric column — unnecessary for 277M rows [Lens 6]

**Location:** Plan lines 400-444 (Cell 11)

**Evidence:** For each numeric column with IQR > 0, Cell 11 runs:
```sql
SELECT COUNT(*) AS outlier_count
FROM matches_raw
WHERE {col} IS NOT NULL AND ({col} < {lower_fence} OR {col} > {upper_fence})
```

With 9 numeric columns (minus ~3 with IQR=0), this generates ~6 separate
full-table scans of 277M rows, each returning a single integer. A single
combined query with CASE expressions would reduce this to 1 scan:

```sql
SELECT
    SUM(CASE WHEN rating IS NOT NULL AND (rating < LB OR rating > UB) THEN 1 ELSE 0 END),
    SUM(CASE WHEN slot IS NOT NULL AND (slot < LB OR slot > UB) THEN 1 ELSE 0 END),
    ...
FROM matches_raw
```

**Risk if ignored:** Execution time waste (potentially 6x slower than
necessary). Not a methodology flaw. The results will be identical.

## Passed Checks

### P1. Census key assertions (Cell 5) include `categorical_profiles` — PASSED

Cell 5 (plan lines 251-262) asserts 7 required keys including
`categorical_profiles` and `field_classification`. This addresses the
01_02_07 critique B2 finding. The plan also asserts `boolean_census`
and `won_distribution`.

### P2. I3 classifications match census field_classification — PASSED

Cell 6 (plan lines 267-284) reads `census["field_classification"]["fields"]`
and converts `temporal_class` to uppercase. The overrides for `ratingDiff`
(POST_GAME) and `rating` (AMBIGUOUS) match the 01_02_06 bivariate findings.
The census field_classification at `01_02_04_univariate_census.json`
lines 4093-4296 contains entries for all 55 columns including `won` (TARGET),
`civilizationId` (not present — `civ` is the column name, classified PRE_GAME),
and `leaderboard` (PRE_GAME).

### P3. Duplicate detection uses (matchId, profileId) composite key — PASSED

Cell 14 (plan lines 548-583) uses `GROUP BY matchId, profileId HAVING
COUNT(*) > 1`. This is the correct composite primary key for player-match
rows. The plan correctly identifies this as a "primary key integrity" check
and handles both the zero-duplicate and non-zero-duplicate cases.

### P4. `get_notebook_db("aoe2", "aoe2companion")` signature — PASSED

Cell 3 (plan line 231) calls `get_notebook_db("aoe2", "aoe2companion")`
which matches the function signature at `notebook_utils.py` line 108:
`def get_notebook_db(game: str, dataset: str, *, read_only: bool = True)`.
The default `read_only=True` is appropriate for a profiling notebook.

### P5. Connection cleanup uses `db.close()` — PASSED

Cell 28 (plan line 1229) calls `db.close()`. This matches the pattern used
by predecessor notebooks 01_02_07 and 01_02_04. The `DuckDBClient.close()`
method (db.py line 122) handles the underlying connection cleanup.

### P6. I6 compliance — all SQL queries written to markdown artifact — PASSED

Cell 26 (plan lines 1145-1146) iterates `sql_queries.items()` and writes
each query verbatim to the markdown. Cell 27 (plan lines 1213-1214) asserts
every query name appears in the markdown content. All SQL-producing cells
store their queries in `sql_queries` dict before execution.

### P7. No cleaning decisions or column retention — I9 scope respected — PASSED

The Out of Scope section (plan lines 1310-1318) explicitly excludes cleaning
decisions, column retention, feature engineering, and cross-dataset comparison.
Critical findings are documented as findings only, with no remediation applied.
The notebook creates no DuckDB tables and executes no DDL.

### P8. ROADMAP YAML block and STEP_STATUS entry — PASSED

T01 (plan lines 97-167) provides a complete ROADMAP YAML block with all
required fields (step_number, name, description, phase, pipeline_section,
manual_reference, dataset, question, method, stratification, predecessors,
notebook_path, inputs, outputs, gate, scientific_invariants_applied,
thesis_mapping, research_log_entry). The STEP_STATUS entry (plan lines
156-162) includes name, pipeline_section, and status fields.

## Verdict

**REVISE BEFORE EXECUTION**

Two blockers must be addressed:

1. **B1 (severe):** The skewness/kurtosis computation in Cell 10 (a) omits 3
   of 9 numeric columns (slot, color, team), and (b) applies compounding
   listwise deletion that biases the sample toward rows with non-NULL rating
   (only ~57% of the table). Fix: compute per-column with independent
   `dropna()`, or better yet, use DuckDB native `skewness()`/`kurtosis()`
   for exact full-table computation (see B2).

2. **B2 (factual error):** The comment "DuckDB does not have built-in
   skewness/kurtosis" is false for DuckDB 1.5.1. If the plan switches to
   DuckDB native functions, B1's listwise deletion bias is also eliminated
   (each function operates on its column's non-NULL values independently).

Recommended resolution for both blockers: Replace Cell 10's sampled scipy
approach with a single DuckDB aggregate query:
```sql
SELECT
    skewness(rating) AS rating_skew, kurtosis(rating) AS rating_kurt,
    skewness(ratingDiff) AS ratingdiff_skew, kurtosis(ratingDiff) AS ratingdiff_kurt,
    skewness(population) AS population_skew, kurtosis(population) AS population_kurt,
    skewness(slot) AS slot_skew, kurtosis(slot) AS slot_kurt,
    skewness(color) AS color_skew, kurtosis(color) AS color_kurt,
    skewness(team) AS team_skew, kurtosis(team) AS team_kurt,
    skewness(speedFactor) AS speedfactor_skew, kurtosis(speedFactor) AS speedfactor_kurt,
    skewness(treatyLength) AS treatylength_skew, kurtosis(treatyLength) AS treatylength_kurt,
    skewness(internalLeaderboardId) AS ilb_skew, kurtosis(internalLeaderboardId) AS ilb_kurt
FROM matches_raw
```
This computes exact per-column statistics in a single pass, covers all 9 columns,
requires no sampling, and has no listwise deletion. For `duration_min` (derived),
add `skewness(EXTRACT(EPOCH FROM (finished - started)) / 60.0)` with a
`WHERE finished > started` filter applied only to that expression.

Warnings W1-W4 should be addressed if time permits. W2 and W3 are low-severity
I7 concerns. W4 is a performance optimization.
