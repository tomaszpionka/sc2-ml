---
reviewer: reviewer-adversarial
plan: planning/plan_aoestats_01_03_01.md
date: 2026-04-15
verdict: REVISE BEFORE EXECUTION
blocking_count: 2
warning_count: 4
---

# Adversarial Review — aoestats 01_03_01 Plan (Systematic Data Profiling)

## Lens Assessments

- **Temporal discipline:** SOUND — All I3 classifications verified against census and bivariate artifacts. No POST-GAME or IN-GAME columns used in predictive or grouping contexts; profiling-only (descriptive) use is appropriate.
- **Statistical methodology:** AT RISK — `PERCENTILE_CONT ... WITHIN GROUP ... FILTER` syntax for ELO sentinel-excluded percentiles is uncertain in DuckDB; near-constant detection threshold produces massive false positives.
- **Feature engineering:** N/A — Phase 01 profiling step; no features constructed.
- **Thesis defensibility:** ADEQUATE — I3 classification table and dual-reporting of ELO stats are thesis-valuable. Near-constant false-positive flood weakens the critical_findings artifact.
- **Cross-game comparability:** AT RISK — This is the first 01_03 step across datasets. The profiling JSON schema established here will be replicated. The near-constant threshold problem will propagate if uncorrected.

---

## Blockers

### B1 — PERCENTILE_CONT WITHIN GROUP combined with FILTER clause: DuckDB support uncertain

**Location:** Plan Cell 12 (sql_elo_no_sentinel query), lines computing sentinel-excluded percentiles.

**Finding:** The plan uses `PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo) FILTER (WHERE team_0_elo != -1)` to compute sentinel-excluded percentiles. `PERCENTILE_CONT ... WITHIN GROUP` is an ordered-set aggregate in DuckDB. The DuckDB FILTER clause documentation states it works with aggregate functions generally, but ordered-set aggregates (`WITHIN GROUP`) are a special aggregate category. DuckDB's aggregate functions documentation does not explicitly confirm or deny FILTER support for ordered-set aggregates, and GitHub issue duckdb/duckdb#11419 shows ordered-set aggregates have known syntax limitations. If `PERCENTILE_CONT(...) WITHIN GROUP (...) FILTER (...)` is not supported, the notebook will crash at runtime.

Note: `SKEWNESS(...) FILTER (WHERE ...)` and `KURTOSIS(...) FILTER (WHERE ...)` are standard (non-ordered-set) aggregates — these should work. The risk is isolated to the `PERCENTILE_CONT` lines.

**Evidence:** DuckDB docs [Aggregate Functions](https://duckdb.org/docs/current/sql/functions/aggregates) do not document FILTER with ordered-set aggregates. DuckDB docs [FILTER Clause](https://duckdb.org/docs/stable/sql/query_syntax/filter) show examples only with standard aggregates (SUM, COUNT). GitHub issue duckdb/duckdb#11419 documents syntax limitations of ordered-set aggregates.

**Required fix:** Replace the FILTER-based approach with a CTE that pre-filters rows:
```sql
WITH elo_filtered AS (
  SELECT * FROM matches_raw
  WHERE team_0_elo != {ELO_SENTINEL} AND team_1_elo != {ELO_SENTINEL}
)
SELECT
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo) AS t0_p25,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_0_elo) AS t0_p75,
  ...
FROM elo_filtered
```
This is semantically identical and avoids the uncertain syntax. The non-percentile aggregates (AVG, STDDEV, SKEWNESS, KURTOSIS) can also use the CTE for consistency.

**What breaks if ignored:** The notebook crashes with a syntax error at runtime. The executor cannot produce ELO sentinel-excluded stats, which are a gate requirement ("ELO columns have both default stats and stats_excluding_sentinel sub-dict").

---

### B2 — Duplicate detection for players_raw uses different methodology than census, producing incomparable results

**Location:** Plan Cell for duplicate detection (sql_dup_players query).

**Finding:** The plan's duplicate detection query uses `WHERE profile_id IS NOT NULL` then `GROUP BY game_id, profile_id HAVING COUNT(*) > 1`. This excludes 1,185 rows with NULL profile_id from the duplicate check entirely. In contrast, the census (01_02_04) used a different approach: `COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__'))`. The census method INCLUDES NULL profile_ids by coalescing them to the string `'__NULL__'`, treating all NULL-profile_id rows for the same game_id as duplicates of each other.

The census found `duplicate_rows: 489`. The plan's method will find a different number because (a) it excludes NULL profile_id rows entirely, and (b) `GROUP BY game_id, profile_id` with non-NULL profile_id uses standard equality, whereas the census used string concatenation.

This is not merely a different implementation — it is a different definition of "duplicate" that will produce inconsistent results with the census artifact. The profiling step is supposed to be a superset of the census, but its duplicate count will silently diverge.

**Evidence:** Census JSON `duplicate_check_players`: `{"total_rows": 107627584, "distinct_game_player_pairs": 107627095, "duplicate_rows": 489}`. Census SQL uses `COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')`.

**Required fix:** Either (a) replicate the census methodology exactly (string concatenation with COALESCE) for comparability and document why, or (b) use the plan's `GROUP BY game_id, profile_id` approach BUT add a separate count of NULL-profile_id rows and document the methodological difference explicitly in the profiling JSON artifact. Option (a) is preferred for I9 (consistency with prior step).

**What breaks if ignored:** The profiling step's duplicate count will contradict the census's duplicate count for the same table, creating an inconsistency that an examiner will notice when both artifacts are cited in Chapter 4.

---

## Warnings

### W1 — Near-constant detection threshold uniqueness_ratio < 0.001 produces flood of false positives on categorical columns

**Location:** Plan near-constant detection logic (critical detection cell).

**Finding:** The threshold `uniqueness_ratio < 0.001` means any column with cardinality < ~30,691 (for matches_raw) or < ~107,628 (for players_raw) will be flagged. Per the census, this includes: `map` (93 values), `leaderboard` (4 values), `starting_age` (2 values), `replay_enhanced` (2 values), `mirror` (2 values), `raw_match_type` (8 values), `patch` (19 values), `num_players` (8 values), `team` (2 values), `civ` (50 values), `opening` (10 values), and `winner` (2 values). That is 12+ columns flagged as "near-constant" — including the prediction target (`winner`) and multiple high-information features (`civ`, `map`, `leaderboard`).

**Required fix:** Add a second condition: a column is near-constant only if `uniqueness_ratio < 0.001 AND cardinality <= NEAR_CONSTANT_CARDINALITY_THRESHOLD` (e.g., 3 or 5). Alternatively, use the `IQR == 0` criterion as the primary near-constant signal for numeric columns and limit `uniqueness_ratio < 0.001` to string/categorical columns with cardinality 2-3. Document the threshold choice per I7.

**What breaks if ignored:** The `critical_findings.near_constant` list includes `civ`, `winner`, and `map`, undermining the artifact's value and making the thesis's profiling claims look unsophisticated.

---

### W2 — QQ sample for players_raw filtered by WHERE match_rating_diff IS NOT NULL, biasing sample for age uptime columns

**Location:** Plan QQ sample SQL for players_raw (sql_qq_players).

**Finding:** The QQ sample query uses `WHERE match_rating_diff IS NOT NULL`. `match_rating_diff` has only 39 NULL rows so the filter is essentially inconsequential for that column. However, the same sample is used for QQ plots of `feudal_age_uptime`, `castle_age_uptime`, and `imperial_age_uptime`, which are 87-91% NULL. After sampling 50K rows from the 107.6M non-NULL match_rating_diff population, `.dropna()` will discard most of the sample for age uptime columns, leaving approximately 6,500 rows (13% of 50K) for those QQ plots.

The plan's subtitle says `N={len(df_qq_p):,}` which will report 50,000, but for age uptime panels the actual N is ~6,500.

**Required fix:** Either (a) add a separate QQ sample filtering to `WHERE feudal_age_uptime IS NOT NULL` for age uptimes specifically, or (b) document that the effective sample for age uptime QQ is ~6,500 and update subplot titles to show actual non-null N per panel.

---

### W3 — avg_elo classified as PRE-GAME without artifact evidence

**Location:** Plan TEMPORAL_CLASS dict (`"avg_elo": "PRE-GAME"`).

**Finding:** No census or bivariate artifact explicitly establishes that `avg_elo` is PRE-GAME. The 01_02_06 bivariate artifact only tests `match_rating_diff` for leakage, not `avg_elo`. If `avg_elo` is derived from `new_rating` values (post-game), it would be POST-GAME and thus a leakage risk.

**Required fix:** Add a note stating: "avg_elo: classified PRE-GAME by convention (matches_raw team-level average ELO). Formal leakage test deferred to 01_04 or feature engineering." This makes the assumption explicit per I3.

---

### W4 — Markdown I3 classification table uses profile dtype label, not DuckDB schema type

**Location:** Plan markdown artifact I3 table generation (column header "DuckDB Type").

**Finding:** The table header says "DuckDB Type" but the values will be generic profile labels ("numeric", "categorical", "boolean") instead of actual DuckDB types (BIGINT, DOUBLE, BOOLEAN, VARCHAR).

**Required fix:** Either (a) rename the column header from "DuckDB Type" to "Profile Type", or (b) include actual DuckDB types from the schema YAML in each profile dict.

---

## Notes

### N1 — ELO IQR outlier counts use all-inclusive percentile fences despite sentinel-excluded analysis in B1

The IQR outlier query for team_0_elo correctly excludes sentinel rows from the outlier count (using FILTER), but the fences are computed from the all-inclusive percentiles. With only 34/39 sentinel rows at -1 among 30.7M rows, the impact on p25/p75 is negligible. This inconsistency is not a blocker but should be documented.

---

## Passed Checks

1. **I3 temporal annotations:** All 32 columns classified. `old_rating` as PRE-GAME, `new_rating` as POST-GAME, `winner` as TARGET, age uptimes as IN-GAME, `duration`/`irl_duration` as POST-GAME, `mirror` as POST-GAME — all consistent with available evidence (with the caveat on `avg_elo` noted in W3). PASSED.
2. **I6 SQL verbatim:** All SQL queries stored in `sql_queries` dict and written to markdown artifact. Gate check explicitly verifies each query name appears in the markdown. PASSED.
3. **I7 constants from census:** ELO_SENTINEL=-1 from census `elo_negative_distinct_values`. MATCHES_TOTAL and PLAYERS_TOTAL from census row counts. IQR multiplier 1.5 cited as Tukey (1977). SAMPLE_SIZE=50,000 justified by SE formula. PASSED.
4. **I9 step scope:** No cleaning decisions, no feature engineering, no column dropping. Critical findings flagged for 01_04. "Out of Scope" section explicitly enumerates exclusions. PASSED.
5. **DuckDB SKEWNESS/KURTOSIS:** Both are confirmed native DuckDB aggregate functions. PASSED.
6. **`get_notebook_db("aoe2", "aoestats")`:** Function exists at `src/rts_predict/common/notebook_utils.py`, returns a `DuckDBClient`. The `.fetch_df()` method exists on `DuckDBClient`. `db.close()` exists. PASSED.
7. **BOOLEAN winner cast:** `winner::INTEGER` cast in DuckDB is valid for BOOLEAN columns. PASSED.
8. **Gate artifacts:** All 6 artifacts listed (JSON, 4 PNGs, MD). Gate checks file existence AND non-empty size AND JSON structure AND markdown content. PASSED.
9. **ROADMAP patch YAML:** Contains all required fields per the step definition schema. PASSED.
10. **STEP_STATUS patch:** Correct format with name, pipeline_section, status, completed_at fields. PASSED.

---

## Verdict: REVISE BEFORE EXECUTION

Two blockers must be resolved before execution:
- **B1** requires replacing `PERCENTILE_CONT WITHIN GROUP FILTER` with a CTE pre-filter to avoid uncertain DuckDB ordered-set aggregate behavior.
- **B2** requires aligning the players_raw duplicate detection methodology with the census approach (COALESCE-based string key or explicit documentation of the divergence).

Warnings W1 (near-constant threshold false positives) and W2 (QQ sample N overcounting) are the most impactful and should also be addressed.
