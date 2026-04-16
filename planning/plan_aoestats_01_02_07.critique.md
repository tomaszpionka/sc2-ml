---
reviewer: reviewer-adversarial
plan: planning/plan_aoestats_01_02_07.md
date: 2026-04-15
verdict: REVISE BEFORE EXECUTION
blocking_count: 2
warning_count: 5
---

# Adversarial Review — aoestats 01_02_07 Plan (Multivariate EDA)

## Lens Assessments

- **Temporal discipline:** SOUND — POST-GAME columns (new_rating, duration_sec) and IN-GAME columns (feudal/castle/imperial_age_uptime) correctly excluded from PCA feature set. Heatmap axis labels annotated with temporal class. match_rating_diff confirmed PRE-GAME per 01_02_06 artifact. I could not identify a temporal leakage path.
- **Statistical methodology:** AT RISK — scipy.stats.spearmanr with nan_policy='omit' on a 2D matrix containing ~87%-NaN columns has a documented history of misbehavior (scipy/scipy#6530, #12458, #13900). The plan includes a fallback (B3/W3), but the primary concern is that `nan_policy='omit'` on the matrix form uses listwise deletion across the full matrix, not pairwise deletion as the plan assumes (see B1). The JOINed sample also introduces non-independence (W4).
- **Feature engineering:** N/A — Phase 01 descriptive EDA; no features constructed.
- **Thesis defensibility:** ADEQUATE — Column classification table is useful for Chapter 4. I3 annotations on heatmap are a strength. However, the BERNOULLI/RESERVOIR text contradiction (W1) and unjustified old_rating > 0 filter (B2) would draw examiner questions.
- **Cross-game comparability:** N/A — Single-dataset EDA step. Cross-game deferred to Phase 06.

---

## Blockers

### B1 — scipy.stats.spearmanr nan_policy='omit' uses LISTWISE deletion on matrix form, not pairwise

**Location:** Plan lines 83–87 (Assumptions), Cell 11 (line 341–344).

**Finding:** The plan states (line 85): "it uses pairwise deletion by default with `nan_policy='omit'` when using the matrix form." This is incorrect for the matrix form. When `spearmanr(a, nan_policy='omit')` is called on a single 2D array `a`, scipy first applies `ma.masked_invalid()` across the entire array, then drops any row containing any masked value. This is **listwise** deletion, not pairwise. With ~87% NaN on the three age_uptime columns, listwise deletion would reduce the sample from ~20,000 rows to roughly ~1,700 rows (the ~13% where all three age columns are non-NULL *and* all other columns are non-NULL simultaneously). This dramatically reduces effective sample size for ALL pairwise correlations, not just those involving age columns.

The plan's stated advantage of including age_uptime columns in the Spearman heatmap "via pairwise complete observations" does not materialize with this API.

**Evidence:** scipy documentation (v1.17.0) states for nan_policy='omit': "performs the calculations ignoring nan values." The historical bugs (scipy/scipy#6530, #12458) confirm that the matrix form has never reliably done pairwise deletion; the fix in scipy 1.6.0 (#13163) addressed complete-NaN columns but did not change the deletion strategy.

**Required fix:** Either (a) remove age_uptime columns from the matrix-form `spearmanr()` call entirely and compute their pairwise correlations in a separate loop using `spearmanr(col_a, col_b)` with 1D arrays (which does true pairwise deletion), or (b) use `df.corr(method='spearman')` from pandas, which does pairwise deletion by default (`min_periods` parameter controls the minimum observation threshold). Option (b) is simpler and avoids the scipy matrix-form footgun entirely. The fallback code in Cell 11 (lines 349–366) only triggers when all-NaN columns are detected *after* the matrix computation — it does not address the listwise-deletion sample-size reduction that affects every cell.

**What breaks if ignored:** The Spearman heatmap will either (a) be computed on ~1,700 rows instead of ~20,000, making all correlation estimates 3x noisier than claimed, or (b) crash with ValueError if any pairwise comparison has < 3 observations after listwise deletion.

---

### B2 — old_rating > 0 filter is unjustified (I7 violation)

**Location:** SQL queries at lines 325 and 479.

**Finding:** Both the Spearman and PCA queries filter `WHERE p.old_rating > 0`. The plan's Assumptions section (line 81) justifies sentinel exclusion as "ELO sentinel value is -1 (34 + 39 rows per census)." But the census shows that `old_rating` (in players_raw) has `min_val: 0.0` and `n_zero: 5,937` — it does not contain the -1 sentinel. The -1 sentinel exists only in `team_0_elo` and `team_1_elo` (in matches_raw), which are correctly filtered by `!= {ELO_SENTINEL}`.

The filter `old_rating > 0` excludes 5,937 legitimate zero-rating player rows without census-based justification. This is a magic number threshold (I7). A zero ELO rating is a valid data point (likely new/unrated players), and excluding it without documentation biases the sample.

**Evidence:** Census JSON, `numeric_stats_players[0]` (label: "old_rating"): `min_val: 0.0`, `n_zero: 5,937`. Census JSON, `elo_sentinel_counts`: `team_0_elo_negative: 34`, `team_1_elo_negative: 39` — applies to matches_raw only.

**Required fix:** Change `p.old_rating > 0` to `p.old_rating >= 0` in both SQL queries (lines 325 and 479). If zero-rating players should be excluded, provide census-based justification and document it inline per I7. If the intent is to exclude sentinel -1 values, that filter already exists via `m.team_0_elo != -1 AND m.team_1_elo != -1`.

**What breaks if ignored:** An examiner will ask: "Why did you exclude 5,937 players with zero ELO from your multivariate analysis?" The plan has no documented answer.

---

## Warnings

### W1 — BERNOULLI / RESERVOIR sampling method contradiction

**Location:** Plan line 59 vs lines 328, 483.

**Finding:** The Problem Statement (line 59) states: "All multivariate analyses must use BERNOULLI sampling to stay within memory." The ROADMAP method field (line 125) also says "BERNOULLI sampling (20K rows)." But the actual SQL at lines 328 and 483 uses `USING SAMPLE RESERVOIR(...)`. BERNOULLI and RESERVOIR are different algorithms: BERNOULLI samples each row independently with a probability (returns approximate row count), RESERVOIR guarantees exact row count via in-memory reservoir. The code uses RESERVOIR — which is appropriate for a fixed 20K sample — but the prose says BERNOULLI.

**Required fix:** Change the prose at lines 59 and 125 to say "RESERVOIR sampling" to match the code. (RESERVOIR is the correct choice here since an exact sample size is needed for the analysis.)

### W2 — Joined sample introduces non-independence in Spearman matrix

**Location:** T03 SQL query (lines 311–329).

**Finding:** The cross-table JOIN produces multiple player rows per match (median 2 players per game, up to 8). This means match-level features (avg_elo, team_0_elo, team_1_elo, duration_sec) are duplicated across all player rows for the same game_id. In a 20K reservoir sample, if a game has 4 players, all 4 rows share identical values for the match-level columns. This inflates the apparent correlation between match-level columns (which will show rho near 1.0 by construction, not by genuine statistical association) and inflates correlations between player-level and match-level columns.

This does not invalidate the analysis — 01_02_06 already computed per-table Spearman matrices — but the cross-table heatmap must document this non-independence. The markdown artifact (T06) does not mention it.

**Required fix:** Add a note to the markdown artifact's Column Classification section: "Note: cross-table JOIN produces multiple player rows per match. Match-level columns (avg_elo, team_0_elo, team_1_elo, duration_sec) are repeated across players within the same game. Correlations between match-level columns in this heatmap reflect this duplication; per-table correlations from 01_02_06 are the authoritative within-table values."

### W3 — Spearman fallback code has a correctness gap

**Location:** Cell 11, lines 349–366.

**Finding:** The fallback triggers on `rho_df.columns[rho_df.isna().all()]` — columns that are entirely NaN in the computed matrix. But if listwise deletion (per B1) reduces the sample such that a pairwise comparison has e.g. 2 observations (below the minimum 3 needed for spearmanr), the matrix cell will be NaN but the column won't be *entirely* NaN. The fallback won't trigger, and the heatmap will silently contain NaN cells that are not all-NaN columns.

**Required fix:** If B1 is resolved by switching to pandas `.corr()`, this fallback becomes unnecessary. If B1 is resolved by a pairwise loop, the fallback should check individual cells, not entire columns.

### W4 — PCA on highly collinear features may produce misleading scree plot

**Location:** T04, Cell 18 (lines 498–511).

**Finding:** The PCA feature set is: old_rating, match_rating_diff, avg_elo, team_0_elo, team_1_elo. From the 01_02_06 Spearman matrix, avg_elo/team_0_elo/team_1_elo have pairwise rho > 0.98. PCA on these 5 features will trivially show PC1 explaining ~60-80% of variance, driven entirely by the three near-identical ELO features. This is a well-known PCA behavior on collinear inputs and does not constitute a genuine dimensionality finding.

This is not a methodology flaw — PCA correctly captures the variance structure — but the markdown artifact and research log must frame the finding honestly: "PC1 dominance is driven by the near-perfect collinearity of avg_elo, team_0_elo, and team_1_elo, not by a latent factor." Without this framing, the scree plot oversells the dimensionality reduction potential.

**Required fix:** Add a sentence to the PCA Summary section in the markdown artifact (T06, Cell 26) noting that PC1 variance concentration is expected given the documented collinearity of the three ELO features.

### W5 — 95% cumulative variance threshold line on scree plot is unjustified (I7)

**Location:** Cell 19, line 533.

**Finding:** The scree plot includes `ax2.axhline(y=0.95, ...)` with label "95% threshold." The plan says (line 101) "No component retention decision is made in this step (deferred to Phase 02)." Adding a 95% threshold line visually implies a retention criterion that has not been justified. The 95% threshold is conventional but not universal — Kaiser (1960) uses eigenvalue > 1; Cattell (1966) uses the scree elbow; Parallel Analysis uses random permutation.

**Required fix:** Either (a) remove the 95% threshold line entirely (consistent with "no retention decision"), or (b) label it as "conventional reference line, not a retention criterion — see Phase 02" in the plot annotation and markdown artifact.

---

## Passed Checks

1. **Census key correctness** — All five keys (`matches_null_census`, `players_null_census`, `numeric_stats_matches`, `numeric_stats_players`, `elo_sentinel_counts`) exist in the census JSON at the expected paths. Verified at census JSON lines 5, 100, 1089, 1203, 1530. PASSED.

2. **Bivariate JSON key path** — `bivariate["match_rating_diff_leakage"]["leakage_status"]` exists and equals `"PRE_GAME"` (bivariate JSON line 5). PASSED.

3. **Cross-table JOIN key** — `game_id` (VARCHAR) exists in both `matches_raw` (schema line 29) and `players_raw` (schema line 11). The JOIN key is correct. game_id is unique in matches_raw (cardinality = 30,690,651 = total_rows per census). PASSED.

4. **RESERVOIR sampling DuckDB syntax** — `USING SAMPLE RESERVOIR(N)` is valid DuckDB syntax per official documentation. The `ROWS` keyword is optional. `USING SAMPLE` is correctly placed at the end of the query (after WHERE), per DuckDB docs: "the sample clause samples after the entire from clause has been resolved." PASSED.

5. **Age uptime columns location** — feudal_age_uptime, castle_age_uptime, imperial_age_uptime are in `players_raw` (schema lines 23-31). The JOIN on game_id correctly brings them into the cross-table query. PASSED.

6. **PCA null assertion** — After filtering `old_rating > 0` (though this threshold is contested — see B2), `match_rating_diff IS NOT NULL`, and `team_0_elo/team_1_elo != -1`, all PCA features (old_rating, match_rating_diff, avg_elo, team_0_elo, team_1_elo) have zero remaining NULLs per census. The assertion `df_pca[PCA_FEATURES].isna().sum().sum() == 0` will hold for the filtered sample. PASSED (contingent on B2 resolution not introducing NULLs).

7. **winner column type** — `winner` is BOOLEAN in players_raw (schema line 10), with 0 NULLs and cardinality 2 (census lines 104-106, 1786-1789). The `.astype(int)` cast at line 588 is safe. PASSED.

8. **I3 annotation** — POST-GAME* and IN-GAME* annotations on heatmap axis labels (Cell 12, lines 371-382). PCA excludes all POST-GAME and IN-GAME columns (Cell 15-16). PASSED.

9. **I6 compliance** — All SQL queries stored in `sql_queries` dict and written verbatim to markdown artifact (Cell 26, lines 723-726). Gate verification checks this (Cell 27, lines 757-760). PASSED.

10. **I9 compliance** — No cleaning decisions, no feature engineering, no model fitting. PCA is descriptive only. PASSED.

11. **Gate conditions** — Three PNG files checked for existence and non-emptiness. Markdown artifact checked for SQL query presence. JSON artifact checked for existence. These are sufficient for a Phase 01 EDA step. PASSED.

---

## Verdict: REVISE BEFORE EXECUTION

Two blockers must be resolved before execution:
- **B1** requires switching from scipy matrix-form spearmanr to pandas `.corr(method='spearman')` or a pairwise loop.
- **B2** requires changing `old_rating > 0` to `old_rating >= 0` (or providing I7 justification for excluding zeros).

All five warnings should be addressed but are not execution-blocking.
