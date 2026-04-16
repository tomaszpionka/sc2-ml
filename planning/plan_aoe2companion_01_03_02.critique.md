## Critique: plan_aoe2companion_01_03_02

Adversarial Review — Plan
Plan: planning/plan_aoe2companion_01_03_02.md
Phase: 01 / 01_03_02
Date: 2026-04-16

### Blockers (must fix before execution)

**B1. `ANY_VALUE(leaderboard)` is non-deterministic and silently wrong for ~13M matchIds.**

Three SQL queries (T06 Cells 13, 14, 15) use `ANY_VALUE(leaderboard) AS leaderboard`
inside a `GROUP BY matchId` CTE. This assumes every row for a given matchId has the
same leaderboard value. That assumption is empirically false.

**Proof from existing artifacts:** The 01_02_04 census artifact
(`01_02_04_univariate_census.json`) reports `match_structure_by_leaderboard` with
per-leaderboard `COUNT(DISTINCT matchId)`. Summing those counts yields 74,788,989 —
but the total distinct matchId cardinality is 61,799,126. The difference of ~13M means
approximately 13 million matchIds appear under two or more leaderboard values across
their player rows.

With `ANY_VALUE`, the leaderboard assigned to a matchId is non-deterministic and may
differ between query executions. This corrupts:
- The leaderboard overlap analysis (T06 Cell 13): a matchId that has rows in both
  `rm_1v1` and `unranked` could be classified as either, making the confusion matrix
  unreproducible.
- The proxy vs. structural confusion matrix (T06 Cell 14): same issue.
- The expanded proxy confusion (T06 Cell 15): same issue.

**Fix required:** Replace `ANY_VALUE(leaderboard)` with either:
  (a) a deterministic aggregation like `MIN(leaderboard)`, or
  (b) restructure to join matchId with its set of leaderboard values using
      `ARRAY_AGG(DISTINCT leaderboard)` and classify matchIds that span multiple
      leaderboards as a separate category.

Option (b) is scientifically preferable because it surfaces the multi-leaderboard
phenomenon rather than hiding it. Additionally, add a diagnostic query before T06
that counts how many matchIds have more than one distinct leaderboard value.

**Invariants at risk:** I6 (SQL as written produces non-reproducible results), I7
(implicit assumption that leaderboard is match-level is ungrounded).


### Warnings (should fix)

**W1. Research log for 01_03_01 contradicts the 01_03_01 artifact on primary key integrity.**

The research log entry states: "Primary key integrity (matchId, profileId): No duplicates
— primary key is clean." However, the 01_03_01 JSON artifact reports `has_duplicates: true`,
`dup_groups: 3,589,428`, `total_dup_rows: 12,401,433`.

The plan itself correctly identifies the duplicate complication (funnel L5 criterion).
However, the contradiction in the research log is a provenance hazard — if the thesis cites
the research log claim, it will be wrong. The research log entry for 01_03_01 should be
corrected before T11 executes (the 01_03_02 research log entry must not inherit the false
claim).

**W2. `SAMPLE_PCT_VIZ` is defined but never used in any SQL query.**

The method field says "BERNOULLI sampling for distribution plots only" but no subsequent
cell uses `SAMPLE_PCT_VIZ` or `TABLESAMPLE BERNOULLI`. This is dead code that will pollute
the notebook with an unused constant. Fix: either remove the constant entirely (this step
has no visualization that requires sampling), or add a histogram/bar chart cell that uses it.

**W3. Funnel L1–L4 counts `COUNT(*)` without deduplication; 12.4M duplicate rows may
cause genuine 1v1 matchIds to fail the L1 criterion.**

A matchId with 2 human player rows plus 1 duplicate AI row has `COUNT(*) = 3` and would be
excluded at L1 (raw COUNT criterion), even though it may represent a genuine 1v1 with a
spurious duplicate record. The plan addresses this at L5 (`distinct_real_profiles = 2`)
but the "both approaches" promise in the plan commentary is not fulfilled in the SQL — only
the raw-count funnel is implemented. Add a parallel funnel using
`COUNT(DISTINCT profileId) FILTER (WHERE status = 'player')` to reveal the magnitude of
this effect.


### Suggestions (nice-to-have)

**S1. Add a `leaderboard` cardinality-per-matchId diagnostic as a precursor to T06.**

```sql
SELECT n_leaderboards, COUNT(*) AS n_matches
FROM (SELECT matchId, COUNT(DISTINCT leaderboard) AS n_leaderboards
      FROM matches_raw GROUP BY matchId)
GROUP BY n_leaderboards ORDER BY n_leaderboards
```
This would quantify the multi-leaderboard phenomenon before any overlap analysis depends on it.

**S2. Consider adding `slot` to the match_stats CTE in T05.**

The schema shows `slot` ranges 0-7. For true 1v1 matches, slots should be 0 and 1.
Profiling slot values in structural 1v1 matches would catch ingestion anomalies where the
same physical player appears in multiple slots.

**S3. The Markdown report's Section 9 (Thesis Implications) uses placeholder template text.**

Lines like "**Observation 1:** [Rows-per-match distribution] -> [cohort size] -> 01_04" will
be written literally to the artifact if the executor follows the plan verbatim. These should
either be computed dynamically from the data or the plan should instruct the executor to fill
them with actual findings.


### Verdict

**BLOCKED** — B1 (`ANY_VALUE(leaderboard)`) must be fixed before execution. The leaderboard
overlap analysis (T06), which is the core of question Q3 and a primary thesis-relevant finding,
will produce non-reproducible results as currently specified.

After B1 is resolved, the remaining warnings are addressable. W1 (research log contradiction)
and W3 (unfulfilled "both approaches" promise) should ideally be fixed in the plan revision.
