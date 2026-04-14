# Adversarial Critique — aoestats Step 01_02_04
Date: 2026-04-14
Plan: planning/plan_aoestats_01_02_04.md
Reviewer: reviewer-adversarial

## Verdict
PASS WITH CONDITIONS

## Critical Issues (must fix before execution)

1. **Section C 1v1-restricted query will produce inflated counts due to duplicate game_ids in matches_raw.**
   The plan acknowledges at line 29 that "matches has duplicates (30.7M rows vs fewer distinct game_ids)" and warns about "many-to-many join risk." Yet the Section C query `players_raw p JOIN matches_raw m ON p.game_id = m.game_id WHERE m.num_players = 2` performs exactly the join that risk note warns about — without any deduplication or DISTINCT handling. If a game_id appears K times in matches_raw, every player row for that game is duplicated K times in the result. The COUNT(*) will be inflated, and the absolute counts will not reconcile with the unjoined Section C query directly above it. The proportional distribution (TRUE/FALSE/NULL ratios) is preserved by uniform duplication, but the reported absolute numbers will be wrong.

   **Fix:** Either (a) join against a deduplicated subquery: `JOIN (SELECT DISTINCT game_id, num_players FROM matches_raw) m ON ...`, or (b) document the expected count inflation explicitly and report only percentages from the joined query, not absolute counts.

2. **`match_rating_diff` not flagged as a leakage risk alongside `new_rating` (Invariant #3).**
   The plan correctly identifies `new_rating` as post-match leakage, but `match_rating_diff` — described as "rating change (DOUBLE)" — is almost certainly `new_rating - old_rating` or an equivalent post-match derived quantity. If so, it carries the same temporal contamination as `new_rating` itself. The plan profiles it in Section F and includes it in the NULL census, but it is absent from the Invariants Touched section and from the T02 leakage documentation instructions.

   **Fix:** Add `match_rating_diff` to the Invariant #3 leakage note in the T02 instructions and in the Invariants Touched section. If for some reason it is NOT a post-match derived field, that conclusion must be documented with evidence.

## Significant Concerns (should address)

1. **Age uptime unit assumption violates Invariant #9.**
   The plan states "`feudal_age_uptime`: seconds to Feudal Age" but no prior artifact has established the unit. The schema discovery reports the Arrow type as `double` — not `duration[ns]` like `duration` and `irl_duration`. The 01_02_01 research log says the columns are "DOUBLE (from double + null → NULL fill)" but does not state the unit. The word "seconds" first appears in this plan. This is a content-level conclusion not grounded in any completed step's artifact.

   **Fix:** Replace "seconds to Feudal Age" with "units TBD — to be inferred from descriptive statistics range." The descriptive statistics in Section F will reveal the plausible unit by the magnitude of typical values. Document the unit conclusion as a finding of this step, not an assumption going in.

2. **NULL census SQL is inconsistent with the plan's own stated requirement.**
   The plan header for Section A says "Cover all 18 columns with both count and percentage (EDA Manual Section 3.1 requires both)." But the SQL only computes percentage columns for 7 out of 18 matches_raw columns. Missing percentages: `game_id`, `num_players`, `replay_enhanced`, `leaderboard`, `mirror`, `patch`, `raw_match_type`, `game_type`, `game_speed`, `starting_age`, `filename`. Similarly, Section B is missing percentages for several columns. The plan notes it will "transpose into a tidy (column, null_count, null_pct) table" — so the executor could compute percentages in pandas during the reshape. But if the percentages are computed in pandas, the pandas code must appear in the markdown too (Invariant #6).

   **Fix:** Either add all missing `_pct` columns to the SQL, or explicitly note in the plan that the pandas reshape step computes the missing percentages and that the reshape code must appear in the markdown artifact.

3. **Section D `match_count` label is misleading given known duplicate game_ids.**
   The query at the num_players distribution section counts rows in `matches_raw` grouped by `num_players`, labeling the result as `match_count`. But the plan acknowledges that matches_raw has duplicate game_ids. The reported "match_count" is actually a row count, not a count of distinct matches.

   **Fix:** Either rename to `row_count`, or (better) add a parallel query with `COUNT(DISTINCT game_id)` to report the true distinct match count per num_players. The discrepancy between row count and distinct count per num_players is itself a meaningful finding about the duplicate game_id problem.

4. **95% NULL skip threshold is a magic number (Invariant #7).**
   The plan uses ">95% NULL" as the threshold for skipping descriptive statistics on age uptime columns. This threshold is not sourced from the EDA manual (Section 3.1 specifies "every variable") nor from any prior empirical finding.

   **Fix:** Either (a) compute descriptive statistics for all non-dead columns regardless of NULL rate (the WHERE clause already excludes NULLs, so the query works on whatever non-NULL rows exist), (b) cite a specific source for the 95% threshold, or (c) change the language to say "descriptive statistics may be uninformative for columns with extreme NULL rates; compute them and note the limited sample size in the findings."

## Minor Notes

- **Table naming is correct throughout.** All SQL uses `matches_raw`, `players_raw`, `overviews_raw` (suffix convention). No stale `raw_matches`/`raw_players`/`raw_overviews` prefixes found. Confirmed clean.

- **`overviews_raw` is implicitly excluded but not explicitly scoped out of the census.** The plan explains STRUCT unnesting is deferred, and the NULL census sections only cover matches_raw and players_raw. But `overviews_raw` also has non-STRUCT columns (`last_updated`, `total_match_count`, `filename`) that are trivial to census (1 row). Consider adding: "overviews_raw (1 row, reference metadata) excluded from univariate census — its scalar columns are metadata with no analytical value for match prediction."

- **`profile_id` DOUBLE precision risk is correctly deferred.** The plan notes that profile_id should be checked for `max < 2^53` and references the 01_02_01 finding. The min/max check is within scope for this step; the full precision-loss analysis is correctly deferred to 01_04. Slightly more explicit language ("this min/max check is a safety gate, not a resolution") would help.

- **`patch` appears in both Section E (categoricals) and Section F (numerics).** The plan handles this with conditional routing. Consider making the plan more directive: "Profile as categorical first (cardinality check); if cardinality is unexpectedly high (>100), also compute numeric descriptive statistics."

- **Duration `/1e9` conversion is correctly specified** for Section F and consistently applied throughout. The plan correctly notes this is BIGINT nanoseconds from Arrow `duration[ns]`, documented in 01_02_01. No errors found.

- **`winner` NULL semantics are correctly handled.** The Section C query groups by `winner` which naturally separates TRUE, FALSE, and NULL into three rows.

- **Age uptime NULL characterisation question** from 01_02_01 (are they structural zeros or missing data?) is not resolved by this plan — it just reports the NULL rate. This is appropriate for a univariate census step. However, the plan could note that cross-referencing age uptime NULLs with `replay_enhanced` in a bivariate step (out of scope for 01_02_04) would be informative.

- **STEP_STATUS.yaml staleness noted in plan is now outdated.** The plan acknowledges it will only update status for 01_02_04. The stale 01_02_02/01_02_03 status has since been corrected (STEP_STATUS now shows both as complete), so the plan's note about staleness is itself stale.

## Schema Verification

| Plan SQL reference | Column | Plan type assumption | Schema YAML type | Match? |
|---|---|---|---|---|
| `matches_raw.map` | map | VARCHAR | VARCHAR | YES |
| `matches_raw.started_timestamp` | started_timestamp | TIMESTAMP WITH TIME ZONE | TIMESTAMP WITH TIME ZONE | YES |
| `matches_raw.duration` | duration | BIGINT | BIGINT | YES |
| `matches_raw.irl_duration` | irl_duration | BIGINT | BIGINT | YES |
| `matches_raw.game_id` | game_id | VARCHAR | VARCHAR | YES |
| `matches_raw.avg_elo` | avg_elo | DOUBLE | DOUBLE | YES |
| `matches_raw.num_players` | num_players | BIGINT | BIGINT | YES |
| `matches_raw.team_0_elo` | team_0_elo | DOUBLE | DOUBLE | YES |
| `matches_raw.team_1_elo` | team_1_elo | DOUBLE | DOUBLE | YES |
| `matches_raw.replay_enhanced` | replay_enhanced | BOOLEAN | BOOLEAN | YES |
| `matches_raw.leaderboard` | leaderboard | VARCHAR | VARCHAR | YES |
| `matches_raw.mirror` | mirror | BOOLEAN | BOOLEAN | YES |
| `matches_raw.patch` | patch | BIGINT | BIGINT | YES |
| `matches_raw.raw_match_type` | raw_match_type | DOUBLE | DOUBLE | YES |
| `matches_raw.game_type` | game_type | VARCHAR | VARCHAR | YES |
| `matches_raw.game_speed` | game_speed | VARCHAR | VARCHAR | YES |
| `matches_raw.starting_age` | starting_age | VARCHAR | VARCHAR | YES |
| `matches_raw.filename` | filename | VARCHAR | VARCHAR | YES |
| `players_raw.winner` | winner | BOOLEAN | BOOLEAN | YES |
| `players_raw.game_id` | game_id | VARCHAR | VARCHAR | YES |
| `players_raw.team` | team | BIGINT | BIGINT | YES |
| `players_raw.feudal_age_uptime` | feudal_age_uptime | DOUBLE | DOUBLE | YES |
| `players_raw.castle_age_uptime` | castle_age_uptime | DOUBLE | DOUBLE | YES |
| `players_raw.imperial_age_uptime` | imperial_age_uptime | DOUBLE | DOUBLE | YES |
| `players_raw.old_rating` | old_rating | BIGINT | BIGINT | YES |
| `players_raw.new_rating` | new_rating | BIGINT | BIGINT | YES |
| `players_raw.match_rating_diff` | match_rating_diff | DOUBLE | DOUBLE | YES |
| `players_raw.replay_summary_raw` | replay_summary_raw | VARCHAR | VARCHAR | YES |
| `players_raw.profile_id` | profile_id | DOUBLE | DOUBLE | YES |
| `players_raw.civ` | civ | VARCHAR | VARCHAR | YES |
| `players_raw.opening` | opening | VARCHAR | VARCHAR | YES |
| `players_raw.filename` | filename | VARCHAR | VARCHAR | YES |

**All 32 column references match schema YAMLs.** No type mismatches or non-existent column references found.

## Gate Condition Assessment

| # | Gate condition | Assessment |
|---|---|---|
| 1 | JSON artifact exists and is valid JSON | VERIFIABLE — file existence + `json.loads()` check |
| 2 | Markdown contains inline SQL for every result (Invariant #6) | WEAK — requires manual audit; no automated check specified |
| 3 | JSON: NULL counts/pcts for all 18+14 columns | VERIFIABLE — check JSON keys. But see Significant Concern #2: SQL as written does not compute all percentages |
| 4 | JSON: winner TRUE/FALSE/NULL counts | VERIFIABLE |
| 5 | JSON: num_players distribution | VERIFIABLE |
| 6 | JSON: descriptive stats for old_rating, new_rating, duration, irl_duration, avg_elo | VERIFIABLE — check JSON keys |
| 7 | JSON: temporal range | VERIFIABLE |
| 8 | JSON: game_id join integrity check | VERIFIABLE |
| 9 | STEP_STATUS lists 01_02_04 as complete | VERIFIABLE |
| 10 | Research log mentions overviews_raw deferral and new_rating leakage | WEAK — does not require mentioning `match_rating_diff` leakage (see Critical Issue #2) |
| 11 | ROADMAP contains 01_02_04 block | VERIFIABLE |
| 12 | No fabricated numbers | UNTESTABLE by automated means — depends on executor discipline |

## Recommendation

The plan is methodologically sound in its overall design and correctly identifies the major risks (duplicate game_ids, nanosecond durations, `new_rating` leakage, `overviews_raw` deferral). Schema verification is clean — all 32 column references match the YAML source-of-truth. The two critical issues are both fixable without redesign: the Section C 1v1-restricted join needs deduplication to avoid inflated counts, and `match_rating_diff` must join `new_rating` in the leakage documentation. The significant concerns (age uptime unit assumption, incomplete percentage SQL, misleading `match_count` label, magic 95% threshold) are real but will not produce incorrect results if the executor is aware of them — they are documentation and interpretability issues rather than computational errors. Fix the two critical issues before dispatching execution; address the significant concerns in the executor briefing or accept them as post-execution cleanup.
