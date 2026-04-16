---
reviewer: reviewer-adversarial
plan: planning/plan_aoe2companion_01_02_06.md
date: 2026-04-15
verdict: APPROVE WITH CONDITIONS
blocking_count: 2
warning_count: 5
---

# Adversarial Review — aoe2companion 01_02_06 Plan

## Lens Assessments

- **Temporal discipline:** SOUND — ratingDiff and rating plots annotated correctly; duration annotation missing on standalone T06 plot (W-02); T03 pre-assumes leakage conclusion before data confirms it (W-03).
- **Statistical methodology:** AT RISK — ROADMAP method says "Spearman via DuckDB CORR" which is factually impossible (DuckDB CORR is Pearson only). Actual implementation correctly uses scipy spearmanr (B-01). treatyLength NULLs unhandled in correlation SQL will crash scipy (B-02).
- **Feature engineering:** AT RISK — Correlation column list claimed census-derived but is actually hardcoded static list (W-01). treatyLength near-constant in 1v1 context (W-05).
- **Cross-game comparability:** MAINTAINED — methodology transferable to SC2.

## BLOCKER B-01 — ROADMAP method description factually incorrect (Invariant #6)

**Location:** Plan Part A, ROADMAP patch method field.
**Finding:** `method: "... Spearman correlation via DuckDB CORR. ..."` — DuckDB `CORR()` computes Pearson. The actual T08 implementation correctly uses scipy `spearmanr`. The ROADMAP will be a permanent artifact and will mislead any reader (thesis examiner) who reads only the step definition.
**Required fix:** Change to: `"... Spearman correlation via scipy.stats.spearmanr on BERNOULLI-sampled rows (DuckDB CORR computes Pearson only). ..."`

## BLOCKER B-02 — Missing `treatyLength IS NOT NULL` filter in correlation SQL (Invariant #7)

**Location:** T08 SQL WHERE clause.
**Finding:** WHERE clause includes `population IS NOT NULL` but omits `treatyLength IS NOT NULL`. Census shows treatyLength has 249,389 NULLs (0.09%). These become NaN in pandas. scipy `spearmanr` raises ValueError for NaN inputs (scipy >= 1.7).
**Required fix:** Add `AND treatyLength IS NOT NULL` to the correlation sample SQL.

## WARNING W-01 — Correlation column list hardcoded, not census-derived as claimed

**Location:** T08, I7 comment vs actual code.
**Finding:** I7 comment claims column list derived from `census["matches_raw_numeric_stats"]` at runtime. Code is a static Python literal. `duration_min` does not exist in `matches_raw_numeric_stats` (it is a computed expression).
**Required fix:** Either actually derive from census at runtime, or fix the comment to honestly state the list is editorially chosen.

## WARNING W-02 — Duration plot (T06) lacks temporal annotation

**Location:** T06.
**Finding:** ratingDiff (T03) has POST-GAME annotation; rating (T04) has AMBIGUOUS annotation. Standalone duration plot (T06) has none. Duration is computed from `finished - started` where `finished` is only known post-game.
**Required fix:** Add `"POST-GAME (match descriptor) — duration known only after match ends"` annotation to T06.

## WARNING W-03 — T03 annotation pre-assumes leakage before data confirms it

**Location:** T03, annotation text.
**Finding:** Annotation is hardcoded as "CONFIRMED LEAKAGE" before the query runs. If data shows unexpected patterns, the plot displays a false claim.
**Required fix:** Make annotation text conditional on query result.

## WARNING W-04 — ROADMAP patch uses ASCII `--` where existing entries use em dash `—`

**Location:** Part A ROADMAP patch, phase and pipeline_section fields.
**Required fix:** Use `—` (em dash) to match all existing ROADMAP entries.

## WARNING W-05 — speedFactor and treatyLength near-constant in 1v1 context

**Location:** T08 correlation column selection.
**Finding:** Census shows speedFactor stddev=0.09 (4 distinct values); treatyLength p05=p25=p75=p95=0.0 (96.56% zero). Including near-constant variables produces numerically unstable or misleading Spearman coefficients.
**Required fix:** Add variance/cardinality check; exclude degenerate columns or add interpretation caveat in markdown artifact.

## Summary Table

| ID | Severity | Task | Finding |
|----|----------|------|---------|
| B-01 | BLOCKER | T01 (ROADMAP) | ROADMAP method says "Spearman via DuckDB CORR" — factually wrong |
| B-02 | BLOCKER | T08 | Missing `treatyLength IS NOT NULL` in correlation SQL — scipy crash |
| W-01 | WARNING | T08 | Correlation column list hardcoded, not census-derived as claimed |
| W-02 | WARNING | T06 | Duration standalone plot lacks temporal annotation |
| W-03 | WARNING | T03 | Annotation pre-assumes leakage before data confirms it |
| W-04 | WARNING | T01 | ROADMAP patch uses `--` not `—` |
| W-05 | WARNING | T08 | speedFactor/treatyLength near-constant in 1v1 subset |

## VERDICT: APPROVE WITH CONDITIONS

Fix B-01 and B-02 before execution. Both are one-line fixes. W-01 through W-05 are strongly recommended before execution.
