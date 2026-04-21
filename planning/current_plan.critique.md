# Adversarial Review — Plan (Mode A) — WP-4

**Plan:** `planning/current_plan.md` — aoestats `old_rating` PRE-GAME classification empirical closure
**Branch:** `fix/aoestats-old-rating-pregame-closure`
**Base:** master `b6e642be` (post PR #200; version 3.41.0)
**Category:** D (fix)
**Date:** 2026-04-21
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|------|---------|
| Temporal discipline (I3) | AT RISK — unpartitioned LAG() leaks cross-leaderboard structure |
| Statistical methodology | AT RISK — 95% threshold unsourced; ceremonial CI_lower gate; no multi-test rule |
| Feature engineering | N/A (no feature engineering; diagnostic test) |
| Thesis defensibility | ADEQUATE (if BLOCKER 1 fixed) |
| Cross-game comparability | N/A (single-dataset diagnostic) |

## Invariant compliance

- **I3:** AT RISK — LAG() is not scoped to a leaderboard-stable rating sequence.
- **I6:** RESPECTED — plan commits to SQL verbatim in T03 MD §2.
- **I7:** VIOLATED — the 0.95 / 0.90 thresholds are declared "argued" but no citation or empirical derivation is given.
- **I9:** RESPECTED.

## BLOCKER / WARNING / NOTE findings

### BLOCKER 1 — LAG() partitioning scope must be (profile_id, leaderboard), not (profile_id)

AoE2 has independent rating systems per ladder (`random_map`, `empire_wars`, `team_random_map`, `deathmatch`, etc. — per `01_03_01_systematic_profile.md:272`). A naive `LAG() OVER (PARTITION BY profile_id ORDER BY started_timestamp)` across all leaderboards pairs a match on leaderboard A (time t) with a match on leaderboard B (time t+1) — these use different rating systems and will disagree by construction.

`players_raw.yaml:34-41`: old_rating/new_rating are per-player-per-match. `matches_raw.yaml:50-53`: leaderboard lives on `matches_raw`. A JOIN `players_raw → matches_raw ON game_id` is required to expose leaderboard for partitioning.

Plan's §Assumptions says "test runs on matches_1v1_clean scope" but T02 Analysis §1 uses `players_raw` directly with no leaderboard predicate. Internal contradiction.

**Fix:** T02 Analysis §1 rewritten to `PARTITION BY (profile_id, leaderboard)` with explicit JOIN; scope explicitly declared (either single-leaderboard `random_map` OR per-leaderboard verdicts).

### BLOCKER 2 — `profile_id` DOUBLE→BIGINT cast missing in Setup

`INVARIANTS.md §1`: `profile_id` in `players_raw` is DOUBLE (promoted across 171 files' type variance). Discipline `DS-AOESTATS-IDENTITY-04` requires `CAST(profile_id AS BIGINT)` before identity-keyed operations. T02 Setup does not mention this cast.

**Fix:** T02 Setup includes `CAST(profile_id AS BIGINT) AS profile_id_i64` as partition key with citation.

### WARNING 3 — The ≥ 0.95 threshold violates I7

Plan says "argued as the conventional floor for declaring a categorical classification empirically verified." This is tautological. No literature citation; no empirical derivation. I7 requires either a cited threshold or empirical justification.

**Fix (choose one):** (a) Decision-theoretic: "disagreement rate > 5% means ≥ 5% of old_rating values are potentially POST-GAME contaminated, exceeding DS-AOESTATS-02's ~0.03% cleaning-loss tolerance by 2 orders of magnitude"; OR (b) Cite literature; OR (c) Empirically-derived pilot threshold.

### WARNING 4 — `CI_95_lower ≥ 0.90` is ceremonial at n ~ 35M pairs

The test runs on `matches_1v1_clean`-scoped players_raw (17.8M matches × 2 player-rows × some fraction with ≥2 consecutive). This is tens of millions of pairs. Wilson CI half-width at p=0.95, n=10M is ~±0.0001. `CI_95_lower ≥ 0.90` is satisfied whenever point estimate ≥ 0.9001 — trivially redundant with "agreement_rate ≥ 0.90".

**Fix:** Either (a) drop the second threshold as redundant; OR (b) replace with a non-trivial constraint, e.g., "max |old_rating[t+1] − new_rating[t]| < 50 rating units" (tests rounding/seasonal-drift hypothesis).

### WARNING 5 — Tie-rate must be measured, not silently dropped

Plan's T02 §1 filter "drop tied-timestamp pairs." Without measuring the tie-rate first, this could silently drop a large fraction (aoestats batch imports share second-precision timestamps). Also, `INVARIANTS.md §1` mentions 489 duplicate `(game_id, profile_id)` rows not addressed by the plan.

**Fix:** T02 Analysis §1 must (i) report `COUNT` of ties before filter; (ii) require filter non-destructive (< 1% pairs); (iii) handle duplicate-rows explicitly.

### WARNING 6 — No stratification-conflict resolution rule

T02 Analysis §4 stratifies by leaderboard + time-gap bucket but doesn't specify how to combine results. If `random_map` shows 0.96 and `empire_wars` shows 0.80, what is the overall verdict? Pooling can mask systematic drift.

**Fix:** T02 Verdict cell specifies a rule, e.g., "PASS iff (a) pooled gate passes AND (b) every leaderboard stratum passes AND (c) every time-gap-bucket stratum at ≥ 0.90 (relaxed for sub-strata)."

### WARNING 7 — No catastrophic-fail escalation threshold

Plan's FAIL path lists 3 follow-up candidates but does not specify which applies at what agreement rate. If agreement is 0.60, "retain with caveat" would be negligent.

**Fix:** Add to Gate Condition: "If `agreement_rate < 0.80`, executor HALTS; PR does not merge; user decision required (likely WP-4 redesign)."

### NOTE 8 — Thesis §4.2.3 current state unverified

Plan T05 Thesis mapping conditions on "§4.2.3 currently invokes old_rating as PRE-GAME." This has not been verified in the plan's research. Cannot condition a Pass-2 update on an unverified property.

**Fix:** T05 drops the conditional; OR T01 adds explicit read of `thesis/chapters/04_data_and_methodology.md` §4.2.3.

### NOTE 9 — Cat D classification + patch bump confirmed correct

Not a finding. Patch version bump (3.41.0 → 3.41.1) per "patch for fix/test/chore" is correct.

### NOTE 10 — 01_05 spec-binding hook scope confirmed N/A

Not a finding. 01_04 notebooks are not matched by the hook glob.

## Verdict

**REVISE BEFORE EXECUTION.** BLOCKER 1 alone would make the test answer the wrong question. BLOCKER 2 produces silently-wrong numerical joins. WARNINGs 3/4/6/7 reduce defensibility. NOTE 8 prevents over-claiming downstream.

## If REVISE: required revisions (in order of criticality)

1. **BLOCKER 1:** Rewrite T02 Analysis §1: `PARTITION BY (profile_id, leaderboard)` with explicit `players_raw JOIN matches_raw USING (game_id)`. Explicitly scope (either single `leaderboard='random_map'` OR per-leaderboard verdicts). Document the choice.
2. **BLOCKER 2:** T02 Setup: `CAST(profile_id AS BIGINT)` with DS-AOESTATS-IDENTITY-04 citation.
3. **WARNING 3:** Argue the 0.95 threshold via decision-theoretic reasoning linked to DS-AOESTATS-02 rate tolerance, OR cite literature.
4. **WARNING 4:** Drop redundant `CI_95_lower ≥ 0.90` OR replace with disagreement-magnitude threshold (max |Δ| < 50 rating units).
5. **WARNING 5:** T02 Analysis §1 measures tie-rate + handles duplicate `(game_id, profile_id)` rows explicitly.
6. **WARNING 6:** T02 Verdict cell specifies stratification-conflict resolution rule.
7. **WARNING 7:** Gate Condition adds catastrophic-fail HALT threshold (agreement < 0.80).
8. **NOTE 8:** T05 drops the unverified conditional on §4.2.3 OR T01 verifies it.
