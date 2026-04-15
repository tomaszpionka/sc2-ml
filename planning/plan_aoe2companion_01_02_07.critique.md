---
plan: planning/plan_aoe2companion_01_02_07.md
reviewer: reviewer-adversarial (claude-opus-4-6)
date: 2026-04-15
verdict: REVISE BEFORE EXECUTION
blockers: 2
warnings: 5
passed: 5
---

# Adversarial Critique: plan_aoe2companion_01_02_07.md

## Blockers

### B1. PCA near-constant filter is too lax — speedFactor and population will pollute PCA components [I7, Lens 3]

**Evidence:** Cell 12 (plan lines 430–445) uses a `p05 == p95` check to exclude
near-constant columns. Census data shows:

| Column | p05 | p25 | p75 | p95 | std | Excluded? |
|--------|-----|-----|-----|-----|-----|-----------|
| treatyLength | 0.0 | 0.0 | 0.0 | 0.0 | 6.02 | Yes (correct) |
| speedFactor | 1.70 | 1.70 | 1.70 | 2.0 | 0.09 | **No** |
| population | 200.0 | 200.0 | 200.0 | 300.0 | 57.06 | **No** |
| internalLeaderboardId | 0.0 | 0.0 | 9.0 | 21.0 | 12.93 | No |

`speedFactor` has `p05 != p95` (1.70 vs 2.0) so it survives the filter, despite
`p05 == p25 == p75` — the central 75th percentile is constant. After
StandardScaler, a column that is 75%+ constant at a single value creates a
degenerate spike in the scaled distribution. PCA on such data is not
scientifically meaningful: the first principal component will be dominated by
the one column with genuine spread (internalLeaderboardId, std=12.93), and the
loadings for speedFactor/population will be arbitrary.

**The problem:** The plan claims `p05 == p95` is a census-derived check (I7),
but this threshold is not derived from any empirical criterion or literature
precedent. It is a magic number disguised as a census lookup. The plan should
use a more defensible criterion, such as: (a) interquartile range == 0
(`p25 == p75`), which would correctly exclude speedFactor; or (b) a
documented variance ratio threshold from the literature; or (c) at minimum,
document why `p05 == p95` was chosen over alternatives.

**What breaks:** If PCA runs with 3 features where 2 are near-constant,
the scree plot and biplot will be scientifically uninterpretable. An
examiner will ask "Why did you run PCA on two near-constant features?"
and the plan provides no answer.

**Required fix:** Either (a) tighten the filter to `p25 == p75` (which
excludes speedFactor and makes PCA degenerate at 2 features, triggering
the fallback scatter), or (b) keep the `p05 == p95` check but add an
explicit second-pass filter for IQR == 0 columns with a documented
justification, or (c) document why the near-constant features are retained
and interpret the PCA results with appropriate caveats.

### B2. Cell 5 required_keys assertion is incomplete — runtime KeyError risk [I6]

**Evidence:** Cell 5 (plan lines 236–243) asserts only 3 census keys:

```python
required_keys = [
    "matches_raw_total_rows",
    "matches_raw_null_census",
    "matches_raw_numeric_stats",
]
```

But the notebook subsequently accesses:
- `census["categorical_profiles"]["leaderboard"]` in Cell 8 (line 303)
- `census["matches_raw_numeric_stats"]` in Cell 12 (line 425, already covered)

The key `"categorical_profiles"` is not in `required_keys`. If the census
JSON were missing this key (e.g., regenerated with a subset of queries),
the notebook would fail at Cell 8 with an unhelpful `KeyError` instead
of the informative assertion message in Cell 5.

**Required fix:** Add `"categorical_profiles"` to `required_keys` in Cell 5.
This is a defensive programming issue but also an I6 issue: if the
notebook fails at Cell 8, the executor sees a raw KeyError instead of a
traceable assertion pointing to the census dependency.

## Warnings

### W1. `duration_min` classified as POST-GAME without 01_02_06 authority [I9]

**Evidence:** The I3_CLASSIFICATION dict in Cell 7 (plan line 269) labels
`duration_min` as `"POST-GAME"`. The plan's Assumptions section (line 71)
cites "duration=POST-GAME (known only after match)."

However, the 01_02_06 bivariate EDA artifact (`01_02_06_bivariate_eda.md`,
line 30) classifies Q4 (Duration by Outcome) with the annotation
`"N/A (match descriptor)"` — not POST-GAME. The 01_02_06 artifact formally
resolved only two columns: `ratingDiff` as POST-GAME (Q1) and `rating` as
RESULT PENDING (Q2). Duration was investigated in Q4 but never formally
classified.

The census `field_classification` (from 01_02_04) classifies `finished` as
`post_game` but does not have a `duration` or `duration_min` entry (it is
a derived column).

**Invariant #9 risk:** The plan is asserting a classification ("POST-GAME")
that was not established by any prior step's artifact. The classification
is likely correct (duration requires `finished`, which is post-game), but
the logical chain is: `finished` is post-game (01_02_04) → `duration =
finished - started` inherits post-game status → `duration_min` is
POST-GAME. This derivation should be explicitly documented in the
notebook prose, not stated as if it were a 01_02_06 finding.

**Risk if ignored:** An examiner asks "Where was duration classified as
POST-GAME?" and the candidate cannot point to a specific prior artifact.

### W2. `internalLeaderboardId` included in PCA as numeric despite being integer-encoded categorical [Lens 3, Lens 4]

**Evidence:** The plan's Open Questions (line 874) acknowledges this:
"Integer-encoded categorical (122 distinct values). Included as-is for
this exploratory step."

PCA on StandardScaler-transformed integer-coded categorical variables
treats the distance between leaderboard IDs 3 and 5 as meaningful, which
it is not — these are nominal codes. The resulting loadings and variance
explained will be artifacts of the arbitrary ID assignment.

**Risk if ignored:** The PCA biplot will show
`internalLeaderboardId` as a feature with specific loading direction
and magnitude, but this is meaningless for a nominal variable. An
examiner will ask "Why did you treat a categorical ID as continuous in
PCA?" The plan acknowledges this but does not add any plot annotation or
markdown caveat.

**Suggested fix:** Add an explicit caveat in the markdown artifact's PCA
Summary section noting that `internalLeaderboardId` is nominal and its
PCA loading should not be interpreted directionally. Better still: filter
it out of PCA and include it only in the Spearman heatmap (where rank
correlation is at least monotone-invariant).

### W3. `TARGET_SAMPLE_ROWS = 100_000` is labeled "editorial cap" but not justified [I7]

**Evidence:** Cell 6 (plan line 249) sets `TARGET_SAMPLE_ROWS = 100_000`
with the comment `# I7: editorial cap — same as 01_02_06`. The
predecessor notebook (01_02_06) uses the same value with the comment
`# I7: editorial cap for scatter plot visibility`.

"Scatter plot visibility" is a reasonable heuristic for 2D scatter plots,
but the Spearman correlation matrix in T03 is a statistical computation,
not a visualization. Spearman rho on N=100,000 rows will have extremely
tight confidence intervals (CI width ~ 1/sqrt(N) ~ 0.003), making every
rho > ~0.01 significant at p < 0.001 regardless of practical importance.
The plan includes significance stars (Cell 11, line 388) but no effect
size interpretation threshold.

The 100,000 cap is inherited from the predecessor without re-justification
for the different analytical purpose. This is a borderline I7 issue: the
number is traced to 01_02_06, but its applicability to correlation
estimation is not justified.

**Risk if ignored:** Minor — the results will be correct, just
over-powered. Every Spearman coefficient will be "significant" even if
trivially small. The examiner may ask why significance stars are reported
without an effect size threshold for practical relevance.

### W4. Spearman sample applies listwise deletion across 7 columns — effective sample size may be much smaller than 100K [Lens 2]

**Evidence:** The Spearman SQL in Cell 9 (plan lines 327–349) applies
NULL filters for ALL 7 columns simultaneously:
```sql
WHERE rating IS NOT NULL
  AND rating > 0
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND internalLeaderboardId IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```

Census null rates: `rating` 42.46% NULL, `ratingDiff` (co-occurring
with rating per census notes). The `rating > 0` filter further excludes
`rating = -1` rows. On 100K BERNOULLI-sampled rows, after the
leaderboard filter (rm_1v1 + qp_rm_1v1 = ~22% of rows), and then
rating NULL + rating=-1 exclusions, the effective sample could be
substantially smaller than 100K.

The plan's assertion `assert n_spearman > 0` (line 355) only catches
the zero-row case, not a pathologically small sample.

**Risk if ignored:** If the effective Spearman sample is very small (say
< 1000), the correlation estimates become unreliable, particularly for
the near-constant columns. A minimum sample size assertion (e.g.,
`assert n_spearman > 5000`) would be more defensive.

### W5. Bivariate EDA already produced a Spearman correlation matrix (Q6) — scope overlap with 01_02_07 [I9]

**Evidence:** The 01_02_06 bivariate EDA artifact (line 33) includes:
`| 6 | Spearman Correlation Matrix (Q6) | 01_02_06_spearman_correlation.png |`

The 01_02_06 artifact also includes a `correlation_sample` SQL query
(lines 224–244) that computes Spearman on the same 6 numeric columns
(rating, ratingDiff, duration_min, population, speedFactor, treatyLength).

The plan's T03 adds `internalLeaderboardId` (7th column) and cluster
ordering. The value-add is the dendrogram-reordered axis ordering and
I3 classification labels on the axes.

**Risk if ignored:** An examiner may ask "How does the 01_02_07 Spearman
heatmap differ from the 01_02_06 Spearman heatmap?" The plan should
explicitly document the delta (cluster ordering + I3 labels + additional
column) in the markdown artifact to avoid the appearance of redundant
work.

## Passed Checks

### P1. Census key correctness — PASSED

All census keys used in the plan exist in the census JSON:
- `matches_raw_total_rows`: exists
- `matches_raw_null_census`: exists
- `matches_raw_numeric_stats`: exists
- `categorical_profiles`: exists (contains `leaderboard` sub-key)
- `categorical_profiles.leaderboard[*].value`: entries include `rm_1v1` and `qp_rm_1v1`

### P2. I3 classifications for ratingDiff and rating match bivariate findings — PASSED

- `ratingDiff`: classified POST-GAME in plan, matches 01_02_06 Q1 resolution
- `rating`: classified AMBIGUOUS in plan, matches 01_02_06 Q2 "RESULT PENDING"

### P3. DuckDB read-only compliance — PASSED

`con = duckdb.connect(..., read_only=True)` in Cell 3 (line 217). No DDL,
no temp views, no CREATE/INSERT/UPDATE. All queries are SELECT-only.

### P4. BERNOULLI TABLESAMPLE syntax — PASSED

`TABLESAMPLE BERNOULLI({sample_pct:.6f} PERCENT)` is the same syntax
used in the predecessor notebook `01_02_06_bivariate_eda.py` (lines 319,
593), which executed successfully. DuckDB documentation confirms both
`TABLESAMPLE` and `USING SAMPLE` are valid, and `PERCENT` is accepted.

### P5. I6 compliance — all SQL queries written to markdown artifact — PASSED

Cell 18 (lines 731–732) iterates over `sql_queries` dict and writes
each query verbatim to the markdown artifact. The `spearman_sample_all`
and (conditionally) `pca_sample` / `degenerate_scatter` queries are all
added to `sql_queries` before Cell 18 executes. Gate verification in
Cell 19 (lines 792–794) asserts each query name appears in the
markdown content.

### P6. Leaderboard filter — PASSED

The filter `leaderboard IN ('rm_1v1', 'qp_rm_1v1')` is validated at
runtime by asserting both values exist in
`census["categorical_profiles"]["leaderboard"]` (Cell 8, lines 305–306).
Census data confirms both values are present (rm_1v1: 53.7M rows,
qp_rm_1v1: 7.4M rows).

### P7. treatyLength correctly excluded by PCA degeneracy logic — PASSED

Census shows `treatyLength: p05=0.0, p95=0.0`, so `p05 == p95` is True.
The Cell 12 filter will correctly exclude treatyLength from PCA candidates.

### P8. Gate conditions — ADEQUATE

Gate checks (Cell 19) verify:
- All expected PNG files exist and are non-empty
- Markdown artifact exists and is non-empty
- All SQL query names appear in markdown content
- Feature classification table ("I3 Classification") present in markdown

Missing: no check on minimum Spearman sample size (see W4), no check
on PCA explained variance reasonableness.

## Verdict

**REVISE BEFORE EXECUTION**

Two blockers must be addressed:
1. **B1:** The PCA near-constant filter `p05 == p95` is too lax and will
   admit speedFactor (75th percentile constant) into PCA, producing
   uninterpretable results. Either tighten the filter, remove speedFactor
   from PCA explicitly, or document the deliberate inclusion with caveats.
2. **B2:** Add `"categorical_profiles"` to the `required_keys` assertion
   in Cell 5 to prevent an unhelpful runtime KeyError.

Warnings W1–W5 should be addressed if time permits; W2
(internalLeaderboardId as numeric in PCA) is the most thesis-relevant.
