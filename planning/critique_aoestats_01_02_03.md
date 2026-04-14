---
reviewer: reviewer-adversarial
plan: planning/plan_aoestats_01_02_03.md
date: 2026-04-14
verdict: APPROVE WITH REVISIONS
---

# Adversarial Critique: plan_aoestats_01_02_03.md

## Verdict

The plan is fundamentally sound for an EDA step and correctly identifies the
aoestats-specific risks that distinguish it from sc2egset. However, it contains
one critical table-naming inconsistency that will cause SQL failures at
execution, and several moderate issues around interpretive traps, performance
mitigation gaps, and an incomplete gate condition. Approve after revisions.

## Critical Issues (must fix before execution)

### C1. Table naming contradiction between 01_02_01 artifact and this plan

The plan uses table names `raw_matches`, `raw_players`, `raw_overviews`
throughout all SQL (Sections A-I). This matches what `ingestion.py` creates
(lines 27, 36, 44). However, the authoritative 01_02_01 JSON artifact
(`01_02_01_duckdb_pre_ingestion.json`, lines 6-8) records the tables as
`matches_raw`, `players_raw`, `overviews_raw`. The ROADMAP step definition for
01_02_02 (ROADMAP.md line 200) also says `matches_raw`, `players_raw`,
`overviews_raw`.

The plan acknowledges this discrepancy in its Risks section (Risk #3, plan line
462) and states it uses "ingestion module naming as source of truth." This is
the correct resolution -- `ingestion.py` is the code that actually creates the
tables. But this means:

1. The 01_02_01 artifact is wrong about table names, and this plan depends on
   01_02_01 as a predecessor. Any executor reading 01_02_01's JSON first will
   be confused.
2. The ROADMAP's 01_02_02 step definition is also wrong.
3. Step 01_02_02 has not yet been executed (STEP_STATUS.yaml line 35:
   `status: not_started`), so the tables this plan queries **do not yet exist**.

**Risk:** The plan's Prerequisite section (line 467) correctly notes 01_02_02
must be complete first. But if 01_02_02 is executed using the ROADMAP's wrong
table names, the 01_02_02 notebook's own NULL-check queries (which reference
`match_id`, `map_name`, `started`, `rating` -- columns that also do not exist)
will fail, which the plan also correctly flags (line 474). This means 01_02_03
execution is blocked by 01_02_02 bugs that are outside 01_02_03's scope.

**Required revision:** The plan must explicitly state that 01_02_02 must be
executed and pass its gate condition before 01_02_03 can begin, and that the
table naming discrepancy in the 01_02_01 artifact and ROADMAP must be
corrected as part of 01_02_02 execution (or a separate chore), not left as
implicit knowledge. This is not just a risk -- it is a blocking dependency.

### C2. Section C's 1v1-restricted winner query produces Cartesian products if raw_matches has duplicate game_ids

Section C's second query (plan line 149) joins `raw_players p JOIN raw_matches m
ON p.game_id = m.game_id WHERE m.num_players = 2`. The plan acknowledges
(line 29) that `raw_matches` has duplicates: "30.7M rows vs fewer distinct
game_ids." The 01_02_01 artifact confirms this: 30,690,651 total rows but
fewer distinct game_ids (the exact count is in the notebook output but not
in the JSON).

If a game_id appears N times in `raw_matches`, the join produces N copies of
each player row for that game_id. For the unrestricted Section C query (line
133), this does not matter because it queries `raw_players` alone. But the
1v1-restricted query joins to `raw_matches` and will inflate counts by the
duplicate factor. The resulting class balance percentages will be wrong.

**Required revision:** The 1v1-restricted query must either:
(a) Use a subquery to get distinct 1v1 game_ids first:
    `WHERE p.game_id IN (SELECT DISTINCT game_id FROM raw_matches WHERE num_players = 2)`
(b) Or use `JOIN (SELECT DISTINCT game_id, num_players FROM raw_matches) m`
(c) Or explicitly document that the Cartesian-product risk exists and the
    executor must verify join multiplicity before trusting the counts.

The same Cartesian risk applies to Section H's join integrity queries (plan
lines 258-270), though those use `COUNT(DISTINCT game_id)` which partially
mitigates the issue for the counts themselves. However, the orphan check
still joins against a table with duplicates, and `WHERE m.game_id IS NULL`
after a LEFT JOIN will produce correct distinct-game_id counts only if the
aggregation is over distinct game_ids -- which it is (line 260:
`COUNT(DISTINCT p.game_id)`). Section H is correct. Section C is not.

## Moderate Issues (should fix)

### M1. Section C winner class balance is tautological for complete matches and the plan does not explicitly call this out

The plan states (line 140): "For a well-formed 1v1 dataset with a recorded
winner, we expect approximately equal TRUE/FALSE counts." This is not merely
an expectation -- it is guaranteed by construction. Each match in `raw_players`
has exactly one winner=TRUE row and one winner=FALSE row (for complete 1v1s).
The TRUE/FALSE ratio is exactly 1:1 by definition for complete matches. The
only informative signal is the NULL count.

The plan does note that deviations signal "team games or data quality issues"
(line 141), but it does not explicitly state that the 50/50 balance is
structural, not empirical. An executor who reports "class balance is 50/50"
without this caveat presents a tautology as a finding. The research log entry
and thesis chapter would need to explain that TRUE/FALSE balance is
uninformative for `raw_players` and that the meaningful metric is the fraction
of matches with a determined outcome (non-NULL winner).

**Required revision:** Add explicit text to Section C instructions noting that
TRUE/FALSE balance in `raw_players` is guaranteed by construction for complete
matches and that the analytically meaningful output is the NULL rate and its
distribution across match types (1v1 vs team, ranked vs unranked).

### M2. PERCENTILE_CONT on 107.6M rows without explicit performance mitigation

Section F (plan line 202) proposes running `PERCENTILE_CONT` at 5 quantile
points for each numeric column on `raw_players` (107.6M rows). The Risks
section (Risk #1, line 460) says "If slow, sample-based estimates with
explicit documentation." But it provides no sampling strategy: no sample
size, no sampling method, no confidence bound on the percentile estimate.

DuckDB's `PERCENTILE_CONT` uses exact sorting, which for 107.6M rows on a
single column requires a full sort. On multiple columns (old_rating,
new_rating, match_rating_diff, plus the 3 age-uptime columns if their NULL
rate is under 95%), this could take minutes per column.

**Required revision:** Either (a) specify an explicit `USING SAMPLE n ROWS`
clause (DuckDB supports `TABLESAMPLE RESERVOIR(n)`) with documentation of
why the sample size is sufficient, or (b) use `PERCENTILE_DISC` which can
be faster for integer columns, or (c) use DuckDB's `APPROX_QUANTILE` which
is O(n) approximate. Any sampling must be documented per Invariant #7 (no
magic numbers -- the sample size needs justification).

### M3. replay_summary_raw cardinality query on 107.6M rows may OOM or timeout

Section E (plan line 188) proposes `COUNT(DISTINCT replay_summary_raw)` on
`raw_players` (107.6M rows). If `replay_summary_raw` is a high-cardinality
text field (which the plan itself suspects: "if very high near row count, this
is likely free text"), DuckDB must build a hash set of all distinct VARCHAR
values. For a free-text field on 107.6M rows, this hash set could consume
multiple GB of memory.

**Required revision:** Run a cardinality estimate first using
`APPROX_COUNT_DISTINCT(replay_summary_raw)` (HyperLogLog-based, constant
memory) before deciding whether to run exact `COUNT(DISTINCT ...)`. If
approximate cardinality exceeds a threshold (e.g., 1M), skip the exact count
and report the approximate value with a note.

### M4. No cross-check between num_players (Section D) and players-per-match (Section H)

Section D profiles `num_players` from `raw_matches` (plan line 160). Section H
profiles the actual players-per-match distribution from a `GROUP BY game_id`
on `raw_players` (plan line 274). These two measures answer the same question
from different tables. If they disagree, it indicates either data quality
issues or the match-level `num_players` column is unreliable.

The plan does not require an explicit comparison between these two
distributions. An executor could produce both results in separate cells and
never notice a discrepancy.

**Required revision:** Add an explicit cross-check instruction requiring the
executor to compare the Section D output against the Section H output and
document any discrepancy. This could be as simple as: "After Section H,
verify that the players-per-match distribution from raw_players aligns with
num_players from raw_matches. Document any discrepancy."

### M5. Gate condition does not require explicit new_rating leakage flag

The plan's gate condition (plan lines 408-419) has 12 items. Gate item #10
(line 417) requires the research log entry to mention "new_rating leakage
note." But this is buried in the research log update task (T02), not in the
gate condition as a hard requirement tied to the artifact.

The JSON artifact gate (item #6, line 413) requires descriptive statistics for
`new_rating` but does not require a leakage flag on those statistics. An
executor could produce `new_rating` descriptive statistics that look like
any other feature's statistics, without a visible warning that this column
must never be used as a feature.

**Required revision:** Either (a) add a gate item requiring the JSON artifact
to include an explicit `leakage_flags` key listing `new_rating` (and
`match_rating_diff`, which is derived from `new_rating - old_rating` and is
therefore also post-match), or (b) require the markdown artifact to visually
flag leakage-risk columns in the descriptive statistics table.

### M6. match_rating_diff is also post-match but not flagged

The plan flags `new_rating` as a leakage risk (plan line 425, Invariant #3
section). However, `match_rating_diff` (DOUBLE in `raw_players`) is
`new_rating - old_rating` -- it is the rating change caused by the match
result. It is equally post-match and equally a leakage risk. The plan
includes it in Section F numeric statistics (plan line 218) without a leakage
warning.

**Required revision:** Add `match_rating_diff` to the leakage flag alongside
`new_rating` in the Invariants Touched section and in T02's leakage note
instruction.

## Minor Issues (consider fixing)

### N1. Section I dead-field threshold 0.001 may need contextual justification

Section I (plan line 291) uses uniqueness ratio < 0.001 as the near-constant
threshold, citing EDA Manual Section 3.3. On 30.7M rows, this means a column
with 30,700 distinct values would be flagged -- which for categorical columns
like `map` (likely hundreds of maps) or `patch` (likely dozens of patches) is
not near-constant. The threshold is appropriate for continuous variables but
may produce false positives for high-cardinality categoricals.

**Suggested revision:** Either apply the 0.001 threshold only to numeric
columns, or document in the plan that categorical columns flagged by this
threshold should be interpreted differently (a categorical with 30K values
in 30M rows is not "near-constant" -- it is "moderately high cardinality").

### N2. Section F treats raw_match_type ambiguously

Plan line 209: "raw_match_type: cardinality check -- if low cardinality, treat
as categorical instead." The 01_02_01 artifact shows `raw_match_type` is DOUBLE
(promoted from mixed int64/double). The plan puts it in Section F (numerics)
with a conditional redirect to Section E (categoricals). This is the right
instinct, but the executor receives conflicting instructions: it is listed in
Section F's column list but may need to be moved to Section E mid-execution.

**Suggested revision:** Either profile `raw_match_type` in both sections
(cardinality in E, descriptive stats in F) and let the research log record
which treatment is appropriate, or move it to Section E with a note that if
cardinality exceeds 20, also compute descriptive stats.

### N3. raw_overviews is not profiled at all

The plan's "Out of Scope" section (line 439) defers unnesting
`raw_overviews` STRUCT arrays. However, the plan does not include even a
basic row-count or column-count verification of `raw_overviews` in any
section. The NULL census (Sections A-B) covers only `raw_matches` and
`raw_players`. There is no section that confirms `raw_overviews` was
ingested correctly (1 row, 9 columns including `tournament_stages` which
appears in the JSON artifact but is not mentioned in the plan's rationale
which says "9 columns" but lists only 5 STRUCT arrays: civs, openings,
patches, groupings, changelog).

**Suggested revision:** Add a minimal Section J: "Verify raw_overviews: 1
row, 9 columns, list column names and types." This is one SQL query and
confirms ingestion without touching the STRUCT content.

### N4. started_timestamp type is confirmed but filename column type is not verified

The plan correctly notes (Section G, line 240) that `started_timestamp` is
native TIMESTAMPTZ. The 01_02_01 artifact confirms this (JSON line 27:
`TIMESTAMP WITH TIME ZONE`). The plan does not need a STRPTIME cast.

However, the plan does not note that `filename` in `raw_matches` and
`raw_players` is populated by DuckDB's `filename=true` parameter, which
produces absolute paths, not relative paths. Invariant #10 requires relative
paths. The `ingestion.py` module uses `SELECT *` with `filename=true` (line
28-32) and does NOT strip the prefix. This means the `filename` values in
the ingested tables are absolute paths, violating Invariant #10.

This is not this plan's responsibility to fix (it is an ingestion issue), but
if 01_02_03 reports filename values without noticing they are absolute paths,
the research log will propagate the violation. At minimum, the plan should
note this as an observation for the executor to flag if discovered.

## Confirmed Correct

1. **Table names used in SQL are correct relative to ingestion.py.** The plan
   uses `raw_matches`, `raw_players`, `raw_overviews` which match what
   `ingestion.py` creates. The discrepancy with the 01_02_01 artifact is
   acknowledged in Risk #3.

2. **Column names in all SQL queries match the actual schema.** I verified
   every column name in Sections A-I against the 01_02_01 artifact's DESCRIBE
   output. All 18 `raw_matches` columns and all 14 `raw_players` columns are
   correctly named.

3. **started_timestamp is correctly identified as native TIMESTAMPTZ.** The
   artifact confirms `TIMESTAMP WITH TIME ZONE` (JSON line 27). No STRPTIME
   needed.

4. **Duration conversion factor (1e9) is correctly documented.** The 01_02_01
   artifact confirms BIGINT nanoseconds (JSON line 420-430).

5. **new_rating leakage risk is correctly identified.** Invariant #3 is
   referenced (plan line 425).

6. **Scope boundaries are correctly drawn.** The plan correctly defers
   bivariate analysis, cleaning, identity resolution, temporal EDA, and
   STRUCT unnesting. This respects both the EDA Manual sections listed and
   Invariant #9.

7. **game_id duplicate risk is correctly identified.** Risk #2 (plan line
   461) and Section H's use of `COUNT(DISTINCT game_id)` are appropriate.

8. **The plan correctly distinguishes this step from the sc2egset 01_02_03.**
   The seven listed differences (plan lines 38-44) are accurate and reflect
   genuine schema and scale differences.

9. **Sandbox rules are correctly cited.** No `def`/`class`/lambda, 50-line
   cell cap, loop-based cells for repetitive queries, `get_notebook_db` for
   database access, `print()` for exploration output.

10. **The prerequisite dependency on 01_02_02 is explicitly stated** (plan
    line 467), which prevents premature execution.

