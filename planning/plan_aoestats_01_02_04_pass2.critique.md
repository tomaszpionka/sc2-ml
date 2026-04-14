# Adversarial Review — Plan
Plan: planning/plan_aoestats_01_02_04_pass2.md
Phase: 01 / pipeline section 01_02 — Exploratory Data Analysis (Tukey-style)
Date: 2026-04-14

## Lens Assessments

- **Temporal discipline**: N/A — Phase 01 EDA, no features computed. match_rating_diff leakage deferral is correctly documented to Phase 02.
- **Statistical methodology**: N/A — no hypothesis tests or model evaluation in scope.
- **Feature engineering**: N/A — no features constructed.
- **Thesis defensibility**: ADEQUATE — see findings below regarding T02 and T03.
- **Cross-game comparability**: AT RISK — the near-constant detection uses a dataset-specific cardinality threshold (50) with no cross-dataset protocol. The parallel aoe2companion plan uses different key names (`near_constant_low_cardinality` / `near_constant_ratio_flagged`), breaking downstream automation. See Finding #3.

## Examiner's Questions

1. "Your threshold of 50 was chosen because civ has cardinality 50. But map has cardinality 93 and is unambiguously categorical. How do you justify classifying map as 'ratio_flagged_continuous'?" — The plan has no answer to this. See BLOCKER Finding #1.

2. "You exclude ELO <= 0 from the sentinel-free stats. team_0_elo has 4,824 zero-valued rows and team_1_elo has 192. Are those sentinel values or valid ratings?" — The plan does not investigate. See WARNING Finding #2.

3. "Your duplicate check for players_raw concatenates game_id and profile_id. profile_id has 1,185 NULLs. What happens to those rows in the distinct count?" — The plan does not handle this. See WARNING Finding #4.

4. "The civ column has cardinality exactly 50, and your threshold is strictly < 50. Does this mean civ is classified as ratio_flagged_continuous?" — Yes, by the plan's own logic. See Finding #1.

## Methodology Risks

### BLOCKER #1 — T02 cardinality threshold 50 is falsified by the data

The plan (line 53) claims: "the maximum cardinality among known categorical/boolean columns in this dataset is 50 (civ)." This is factually wrong. The `map` column is VARCHAR, listed as categorical in the notebook's MATCHES_CATEGORICALS, and has cardinality = 93. With threshold `< 50`, `map` (cardinality 93) would be placed in `ratio_flagged_continuous` alongside duration (13,164) and avg_elo (22,432). Calling a map-name column "ratio-flagged continuous, NOT near-constant" is analytically wrong and would be immediately challenged at examination.

Additionally, the threshold `< 50` excludes `civ` itself (cardinality exactly 50), placing it in ratio_flagged_continuous. So the column cited as justification for the threshold is itself misclassified by it.

**What breaks:** The `near_constant_detection_note.justification` string makes a false empirical claim that will be persisted into the JSON artifact and cited in the thesis. Invariant #7 is violated.

**Fix:** Set threshold to `< 100` (or `<= 100`). The gap between map (93) and old_rating (3,032) provides clean empirical separation. Document both boundaries (93 and 3,032) in the justification string.

---

### WARNING #2 — T03 sentinel exclusion silently drops zero-valued ELO rows

The plan uses `WHERE {elo_col} > 0` to exclude the -1.0 sentinel. But team_0_elo has n_zero=4,824 and team_1_elo has n_zero=192. These rows with ELO=0.0 are excluded by `> 0` but are NOT sentinel values (the only negative distinct value is -1.0).

**What breaks:** The sentinel-excluded descriptive stats will silently omit up to 4,824 + 192 potentially valid data points. If ELO=0 means "unranked/new player," that is a different analytical question from "sentinel value."

**Fix:** Use `WHERE {elo_col} != -1.0` (or `WHERE {elo_col} >= 0`) instead of `WHERE {elo_col} > 0`. If ELO=0 is also to be excluded, document the reasoning separately from the sentinel exclusion.

---

### WARNING #3 — Cross-dataset key name divergence for near-constant detection

The aoestats plan produces keys: `genuinely_near_constant_fields`, `ratio_flagged_continuous`, `near_constant_detection_note`. The parallel aoe2companion plan produces different keys: `near_constant_low_cardinality`, `near_constant_ratio_flagged`. Any downstream code or thesis chapter that iterates over both datasets' artifacts will break on key mismatch. Invariant #8 requires the evaluation protocol to be identical for both games.

**Fix:** Align key names across both plans before execution.

---

### WARNING #4 — T05 duplicate check for players_raw silently mishandles NULL profile_id

The plan uses string concatenation: `CAST(game_id AS VARCHAR) || '_' || CAST(profile_id AS VARCHAR)`. The players_raw schema shows profile_id is DOUBLE with 1,185 NULLs. In SQL, `NULL || anything = NULL`. These 1,185 rows produce NULL composite keys, and `COUNT(DISTINCT NULL)` returns 0.

**What breaks:** The duplicate_check_players finding will silently miscount. Violates Invariant #6 (reproducibility requires accurate derivation).

**Fix:** Use `COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')` in the concatenation, or use a GROUP BY approach:
```sql
SELECT game_id, profile_id, COUNT(*) FROM players_raw GROUP BY 1, 2 HAVING COUNT(*) > 1
```
DuckDB's GROUP BY treats NULLs as equal, which is the correct behavior for duplicate detection.

---

## Notes (Non-blocking)

- **NOTE #5**: T01 skewness/kurtosis lookup into `numeric_stats_matches` via `next(s for s in numeric_stats_matches if s["label"] == label)` is correct — `numeric_stats_matches` is a list and the lookup pattern matches the existing notebook. Variable names confirmed: MATCHES_NUMERIC_DEFS, PLAYERS_NUMERIC_DEFS, numeric_stats_matches, numeric_stats_players all confirmed in current notebook.
- **NOTE #6**: T07 uses `AOESTATS_DB_FILE` correctly — imported at notebook line 42 from `rts_predict.games.aoe2.config`.
- **NOTE #7**: T09 variable names confirmed: winner_df, hist_data, monthly_df, cat_profiles_matches, cat_profiles_players all match the notebook's actual variable names.
- **NOTE #8**: T06 NULL co-occurrence DuckDB FILTER syntax is valid — already used in notebook with similar conditions.
- **NOTE #9**: T08 opening non-NULL distribution: JSON artifact confirms categorical_players.opening exists with cardinality=10. Key name `opening_nonnull_distribution` is new and does not conflict.
- **NOTE #10**: Removing `near_constant_fields` key is safe — no downstream gate in ROADMAP or STEP_STATUS references this key by name.

## Invariant Compliance

| Invariant | Status | Note |
|-----------|--------|------|
| #1 per-player split | N/A | Phase 01, no splitting |
| #2 canonical nickname | N/A | No identity resolution |
| #3 temporal < T | RESPECTED | match_rating_diff leakage deferred to Phase 02 |
| #4 prediction target | N/A | No prediction in scope |
| #5 symmetric treatment | N/A | No feature pipeline |
| #6 reproducibility | AT RISK | T05 NULL concatenation bug |
| #7 no magic numbers | VIOLATED | T02 threshold of 50 falsified by map (cardinality 93) |
| #8 cross-game protocol | AT RISK | Key name divergence with aoe2companion plan |
| #9 research pipeline | RESPECTED | Step scope appropriate |

## Verdict: REVISE BEFORE EXECUTION

**Required changes before execution:**

(a) **T02**: Fix threshold to `< 100` (not `< 50`). Fix the boundary condition so `civ` (cardinality 50) is correctly classified as categorical. Update justification string to document max categorical cardinality = 93 (map) and min continuous = 3,032 (old_rating).

(b) **T03**: Change ELO filter from `> 0` to `!= -1.0` (or `>= 0`). Document whether ELO=0 rows are valid or sentinel in a comment.

(c) **T05**: Handle NULL profile_id in composite key concatenation using COALESCE or GROUP BY.

**Additionally recommended (non-blocking):**

(d) Align near-constant detection key names with aoe2companion plan.
