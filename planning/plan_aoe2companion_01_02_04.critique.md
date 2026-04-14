# Adversarial Critique — aoe2companion Step 01_02_04
Date: 2026-04-14
Plan: planning/plan_aoe2companion_01_02_04.md
Reviewer: reviewer-adversarial

## Verdict
PASS WITH CONDITIONS

## Critical Issues (must fix before execution)

None.

## Significant Concerns (should address)

1. **Two VARCHAR columns in matches_raw are orphaned from all analysis sections.**
   The schema (`matches_raw.yaml`) has 23 VARCHAR columns. The plan's Section D lists 20 categorical columns. Missing: `name` (VARCHAR — player in-game name) and `colorHex` (VARCHAR — hex color string). `filename` is also VARCHAR but is correctly omitted as a provenance column.

   `name` is especially important: it is the column that will become the canonical player identifier under Invariant #2 (lowercased nickname). Knowing its cardinality and NULL rate now — even in a univariate census — is directly relevant to the thesis. `colorHex` is a low-value string encoding of the `color` INTEGER, but omitting it without justification leaves a gap in the "full NULL census" claim (Gate Condition #3 says "all 55 matches_raw columns"). The full NULL census in Section A does cover all 55 columns, but the targeted categorical profiling in Section D does not. The plan should either add `name` and `colorHex` to Section D or explicitly note they are covered by the Section A census but excluded from the top-k value profile and explain why.

   **Impact:** Moderate. The Section A census will capture NULL rate and cardinality for all 55 columns including `name` and `colorHex`. But without Section D's top-k value profile for `name`, the research log will not record player name cardinality as a profiling finding — and an examiner who asks "how many distinct players are in matches_raw?" will want that number surfaced here, not deferred.

   **Recommendation:** Add `name` to Section D (cardinality only — do not print 277M distinct names). Add `colorHex` to Section D or note it is excluded as a derived representation of `color` INTEGER.

2. **Section F numeric SQL sketch hardcodes `FROM matches_raw` for both matches and ratings columns.**
   The SQL sketch says `FROM matches_raw` and `WHERE "{col}" IS NOT NULL`, but the text says "For `ratings_raw`: `rating`, `games`, `rating_diff`." The executor must use `FROM ratings_raw` for those three columns. This is a copy-paste error in the sketch that could cause the executor to query the wrong table.

   **Impact:** Low if the executor reads the prose, but the plan is supposed to be unambiguous. The sketch is the executable reference per the plan's own "Notebook Query Pattern" section.

   **Recommendation:** Add a second SQL sketch block explicitly for `ratings_raw`, or add a comment in the existing sketch noting the table changes for ratings columns.

3. **`ratings_raw` numeric profiling omits two BIGINT columns: `season` and `leaderboard_id`.**
   The `ratings_raw` schema has 8 columns: `profile_id`, `games`, `rating`, `date`, `leaderboard_id`, `rating_diff`, `season`, `filename`. The plan profiles only `rating`, `games`, and `rating_diff`. `leaderboard_id` and `season` are BIGINT columns whose distinct values and ranges are directly relevant:
   - `leaderboard_id` — needed to understand how ratings map to game modes (links to the open question about which leaderboard value corresponds to ranked 1v1)
   - `season` — if this is a season identifier, its cardinality and range tell us about temporal segmentation in the ratings data

   `profile_id` is a join key and `filename` is provenance — omitting those from descriptive statistics is reasonable. But `leaderboard_id` and `season` carry analytical content.

   **Impact:** Moderate. The Section H auxiliary census will capture NULL counts for these columns, but not descriptive statistics (min/max/median/percentiles). An examiner asking "how many distinct leaderboard IDs exist in ratings_raw?" would expect this from a univariate census step.

   **Recommendation:** Add `leaderboard_id` and `season` to the ratings_raw numeric profiling list, at least for cardinality and distinct values.

4. **The `leaderboards_raw` table has numeric columns (rank, rating, drops, losses, streak, wins, games, rankCountry, season, rankLevel) not listed in any analysis section.**
   Section H covers only NULL census and key cardinality for auxiliary tables. Section F covers numeric descriptive statistics only for matches_raw and ratings_raw. The leaderboards_raw table contains rich numeric data (rank, rating, wins, losses, games, streak, drops) that would provide valuable context — for example, the rating distribution in leaderboards_raw vs. the rating column in matches_raw could reveal whether they are on the same scale.

   The plan's Section I (dead/constant detection) will capture cardinality from Section H, but without Section F descriptive statistics for leaderboards_raw, the census is incomplete for the auxiliary tables.

   **Impact:** Low-to-moderate. This is a univariate census, not a cross-table analysis. But the plan's own title is "Univariate Census & Target Variable EDA" and the scientific rationale says "no column-level profiling has been performed on the DuckDB tables" — which implies all tables get profiled, not just matches_raw.

   **Recommendation:** Either add leaderboards_raw numeric columns to Section F, or add an explicit "Out of Scope" note explaining why auxiliary table descriptive statistics are deferred. The current "Out of Scope" section does not mention this.

5. **Dependency status is stale in the plan body but correct in STEP_STATUS.**
   The plan's "Prerequisite Dependency" section states `01_02_02: not_started`. STEP_STATUS.yaml shows `01_02_02: complete, 2026-04-13`. The plan's Risk #3 also says "Step 01_02_02 not yet complete." These sections are now factually wrong.

   **Impact:** Low — the executor will see STEP_STATUS shows completion. But stale plan text creates confusion about whether the plan was written against current state.

   **Recommendation:** Update the Prerequisite Dependency section and Risk #3 to reflect 01_02_02's completion before dispatching to executor.

## Minor Notes

- **Plan line 329: uniqueness ratio threshold < 0.001 is correctly traced to EDA Manual Section 3.3.** I could not identify a magic number violation for this threshold. The EDA Manual explicitly states "a uniqueness ratio below 0.001 is a reasonable starting point" — Invariant #7 is respected.

- **Plan Section D SQL sketch: `SELECT "{col}" AS value` with DuckDB quoted identifiers.** The double-quoted `{col}` in SELECT and GROUP BY is valid DuckDB syntax for a quoted identifier after Python string interpolation. However, the alias `AS value` means the output column will always be named `value` regardless of which categorical column is being profiled. This is fine for display but the executor should ensure the output DataFrame or report identifies which column produced which result.

- **Plan Section G: `EXTRACT(EPOCH FROM (finished - started))`.** This is valid DuckDB syntax. The `WHERE finished > started` filter correctly excludes negative or zero-duration matches. However, the plan does not ask: how many matches have `finished <= started` or `finished IS NULL` or `started IS NULL`? Reporting the count of excluded rows is important for a census step.

- **The `profiles_raw` table contains social media columns (twitchChannel, youtubeChannel, discordId, discordName, discordInvitation) that will almost certainly be dead or near-constant fields.** Section I will catch this. No action needed, but the executor should not be surprised.

- **Plan references `get_notebook_db("aoe2", "aoe2companion")`.** If this function does not exist, the notebook will fail immediately — but that is a code issue, not a methodology issue.

## Schema Verification

| Plan SQL Reference | Column Name Match | Type Match | Notes |
|---|---|---|---|
| `matches_raw.won` (BOOLEAN) | MATCH | MATCH | Correctly identified as prediction target |
| `matches_raw.matchId` | MATCH | MATCH (INTEGER) | |
| `matches_raw.profileId` | MATCH | MATCH (INTEGER) | |
| `matches_raw.leaderboard` | MATCH | MATCH (VARCHAR) | |
| `matches_raw.started` | MATCH | MATCH (TIMESTAMP) | |
| `matches_raw.finished` | MATCH | MATCH (TIMESTAMP) | |
| `matches_raw.rating` | MATCH | MATCH (INTEGER) | |
| `matches_raw.ratingDiff` | MATCH | MATCH (INTEGER) | |
| `matches_raw.speedFactor` | MATCH | MATCH (FLOAT) | |
| `matches_raw.population` | MATCH | MATCH (INTEGER) | |
| `matches_raw.slot` | MATCH | MATCH (INTEGER) | |
| `matches_raw.color` | MATCH | MATCH (INTEGER) | |
| `matches_raw.team` | MATCH | MATCH (INTEGER) | |
| `matches_raw.treatyLength` | MATCH | MATCH (INTEGER) | |
| `matches_raw.internalLeaderboardId` | MATCH | MATCH (INTEGER) | |
| `ratings_raw.profile_id` | MATCH | MATCH (BIGINT) | snake_case confirmed — not `profileId` |
| `ratings_raw.rating` | MATCH | MATCH (BIGINT) | |
| `ratings_raw.games` | MATCH | MATCH (BIGINT) | |
| `ratings_raw.rating_diff` | MATCH | MATCH (BIGINT) | |
| `ratings_raw.date` | MATCH | MATCH (TIMESTAMP) | |
| `leaderboards_raw.profileId` | MATCH | MATCH (INTEGER) | |
| `leaderboards_raw.leaderboard` | MATCH | MATCH (VARCHAR) | |
| `leaderboards_raw.rank` | MATCH | MATCH (INTEGER) | |
| `leaderboards_raw.rating` | MATCH | MATCH (INTEGER) | |
| `leaderboards_raw.steamId` | MATCH | MATCH (VARCHAR) | |
| `leaderboards_raw.country` | MATCH | MATCH (VARCHAR) | |
| `profiles_raw.profileId` | MATCH | MATCH (INTEGER) | |
| `profiles_raw.steamId` | MATCH | MATCH (VARCHAR) | |
| `profiles_raw.name` | MATCH | MATCH (VARCHAR) | |
| `profiles_raw.clan` | MATCH | MATCH (VARCHAR) | |
| `profiles_raw.country` | MATCH | MATCH (VARCHAR) | |

**All plan SQL column references match the schema YAMLs.** The `profileId` vs `profile_id` naming inconsistency (matches/leaderboards/profiles use `profileId` INTEGER; ratings uses `profile_id` BIGINT) is correctly noted in the plan's research log deferral. The plan does not attempt any cross-table joins, so the inconsistency does not create a runtime error at this step.

## Gate Condition Assessment

| # | Gate Condition | Assessment | Reasoning |
|---|---|---|---|
| 1 | JSON artifact exists and is valid JSON | VERIFIABLE | Standard file existence and `json.loads()` check |
| 2 | Markdown contains inline SQL for every result (Invariant #6) | VERIFIABLE | Grep for SQL blocks in markdown; count must match reported tables |
| 3 | JSON contains NULL counts for all 55 matches_raw columns, won distribution, avg_rows_per_match, temporal range, descriptive stats for rating and ratingDiff | VERIFIABLE | Each sub-condition maps to a specific JSON key that can be checked |
| 4 | JSON contains NULL census for all three auxiliary tables | VERIFIABLE | Check for leaderboards_raw, profiles_raw, ratings_raw keys |
| 5 | JSON contains dead/constant/near-constant field list | VERIFIABLE | Check for a list key with entries |
| 6 | STEP_STATUS.yaml lists 01_02_04 as complete | VERIFIABLE | YAML key check |
| 7 | research_log.md has entry for 01_02_04 mentioning leaderboard filtering deferral | VERIFIABLE | Grep for step number and "leaderboard" |
| 8 | ROADMAP.md contains 01_02_04 block with predecessors: [01_02_03] | VERIFIABLE | YAML parse within markdown |
| 9 | No fabricated numbers | WEAK | This is an integrity constraint, not a testable gate. The reviewer must trace artifact numbers back to notebook cell outputs. An automated check cannot verify this — it requires human or adversarial review of the notebook execution output vs. the JSON artifact. |

## Lens Assessments

**Temporal discipline: SOUND.** This is a univariate census of static raw tables. No features are computed, no rolling windows are defined, no predictions are made. The temporal range finding (Section G) establishes the time axis needed for future temporal splits but does not itself use temporal ordering for any computation. Invariant #3 is not at risk.

**Statistical methodology: N/A.** No statistical tests, no model evaluation, no hypothesis testing. This is descriptive profiling only.

**Feature engineering: N/A.** No features are constructed. The profiling results will inform future feature engineering, but this step does not create any features.

**Thesis defensibility: ADEQUATE.** The plan is methodologically sound as a first-pass univariate census. It correctly identifies the target variable, correctly scopes the analysis to descriptive profiling without cleaning, and correctly defers cross-table joins. The concerns above (orphaned columns, incomplete auxiliary profiling) weaken the "completeness" claim but do not invalidate the methodology.

**Cross-game comparability: MAINTAINED.** The plan explicitly documents the SC2-vs-AoE2 differences (BOOLEAN won vs VARCHAR result, 277M rows vs 22k, 4 tables vs 3, mixed game modes). The cross-game comparability note correctly links target encoding documentation to Invariant #8.

## Recommendation

The plan is well-structured, correctly scoped, and methodologically sound for a univariate census step. The five concerns above are all addressable with minor edits — none requires a redesign. The most important fix is Concern #1 (add `name` column profiling), because player identity cardinality is directly load-bearing for the thesis and an examiner will expect it. Concern #2 (SQL sketch table name) and Concern #5 (stale dependency status) are copy-paste errors that should be corrected to avoid executor confusion. Concerns #3 and #4 (ratings and leaderboards column coverage) are scope decisions that should be made explicit rather than left as implicit omissions.

Proceed after addressing Concerns #1, #2, and #5. Concerns #3 and #4 can be addressed during execution if the executor has latitude, or deferred to a follow-up profiling step if scope is strict.
