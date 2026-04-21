# Adversarial Review — Plan (Mode A) — WP-6

**Plan:** `planning/current_plan.md` — aoestats `old_rating` Phase 01 CONDITIONAL_PRE_GAME annotation
**Branch:** `feat/aoestats-old-rating-conditional-classification`
**Base:** master `78300433` (post PR #202; version 3.41.2)
**Category:** A (Phase 01 cleaning-rule extension)
**Date:** 2026-04-21
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|------|---------|
| Temporal discipline (I3) | SOUND |
| Feature engineering (I7 threshold justification) | AT RISK |
| Statistical methodology | SOUND |
| Thesis defensibility | ADEQUATE with revisions |
| Cross-game comparability | MAINTAINED |

## BLOCKER / WARNING / NOTE findings

### BLOCKER-1 — 7-day threshold is internally inconsistent with cited evidence (I7)

Plan cites 01_04_06's stratification (<1d=0.944, 1-7d=0.859, 7-30d=0.708, >30d=0.634). Plan sets the CONDITIONAL_PRE_GAME condition at `time_since_prior_match_days < 7` — i.e., the PRE-GAME region INCLUDES the 1-7d bucket (0.859), which fails BOTH the WP-4 primary 0.95 gate AND the WP-4 stratum 0.90 gate.

Plan's own §3 cites "aligns with observed stability" and "agreement is sufficiently high (≥ 0.859)" — but 0.859 is below the stratum threshold that WP-4 itself set. The only bucket clearing any WP-4 gate is `<1d` at 0.944. I7 requires the threshold to be argued from data OR literature; the current argument is internally inconsistent (cites 0.944 as evidence while operationalizing 0.859 as the boundary).

**Fix options:**
- (a) Tighten cutoff to `< 1 day` (the only bucket clearing 0.90 stratum gate).
- (b) Keep 7-day but compute pooled `<7d` agreement in T02 and argue explicitly whether the pooled rate defensibly clears a thesis-grade stratum gate.

### BLOCKER-2 — Cross-leaderboard evidence inheritance (I7)

01_04_06's per-time-gap stratification was computed ONLY on `random_map` (per 01_04_06 SQL §5.5: `WHERE m.leaderboard = 'random_map'` inside the dedup CTE for the per-time-gap query). The other 3 leaderboards (team_random_map, co_team_random_map, co_random_map) had ONLY leaderboard-level agreement computed (0.860/0.787/0.855), NOT time-gap breakdowns.

Plan classifies `old_rating` globally as CONDITIONAL_PRE_GAME with `< 7 days` — imports `random_map` evidence to 3 other leaderboards without test. Coordinated-team / co-op matchmaking may behave differently.

**Fix options:**
- (a) Restrict CONDITIONAL_PRE_GAME condition to `leaderboard = 'random_map' AND time_since_prior_match_days < N` in INVARIANTS.md (honest scope).
- (b) Extend T02 to compute 4×4 leaderboard × time-gap stratification; if all 4 leaderboards clear 0.90 at `<7d`, generalize; otherwise scope to random_map.

### WARNING-1 — Schema-versioning pattern deviates from canonical_slot precedent

`player_history_all.yaml` currently has NO `schema_version` field (verified; spec 02_00 §2.2 explicitly states "no explicit schema_version field"). Plan T04 proposes `v1.0 → v1.1.0` — creating a new semver field from nothing. Precedent (canonical_slot amendment) uses a DESCRIPTIVE string (`'10-col (AMENDMENT: canonical_slot added 2026-04-20)'`), not semver.

**Fix:** adopt descriptive-string pattern (`'15-col (AMENDMENT: time_since_prior_match_days added 2026-04-21)'`), OR justify semver introduction explicitly + update spec 02_00 §2.2 to document the new `schema_version` field's introduction.

### WARNING-2 — Downstream "14 cols" references go silently stale

Grep confirms multiple artifacts cite `player_history_all` as 14 columns: `ROADMAP.md:1000`, `ROADMAP.md:1053`, `research_log.md:606, 634`, spec `02_00 §2.2 "Column count | 14"`. Post-amendment the column count is 15. Plan T06 updates §5.5 classification table but does NOT update §2.2's column-count cell. Spec 02_00 becomes internally contradictory (§2.2 says 14; §5.5 lists 15 rows).

**Fix:** T06 updates spec §2.2 aoestats `player_history_all` "Column count" 14 → 15. New T-step (or extension) updates ROADMAP.md:1000 current-state reference. Historical research_log entries NOT touched (historical record preserved).

### WARNING-3 — NULL-on-first-match CONDITIONAL semantics undocumented

`time_since_prior_match_days` is NULL for first match per (profile_id, leaderboard). Condition `< 7` evaluates NULL (not TRUE) under SQL three-valued logic — Phase 02 consumer applying `WHERE time_since_prior_match_days < 7` silently DROPS all first-match rows. For a player's very first rated match, `old_rating` is the aoestats API-provided starting rating (typically 1000) — arguably PRE-GAME by definition since no prior match exists.

**Fix:** INVARIANTS.md §3 revision + spec 02_00 §5.5 note must spell out NULL handling rule (recommendation: treat NULL as PRE-GAME since "no prior match" = "no cross-session risk"). T03 JSON records first-match NULL rate.

### NOTE-1 — `matches_1v1_clean` uses a different `old_rating` path

`matches_1v1_clean` exposes `p0_old_rating`/`p1_old_rating` from `matches_raw` via `p0`/`p1` CTE. These flow into Phase 02 THROUGH `matches_history_minimal` UNION-pivot. `matches_history_minimal.yaml` does not expose `old_rating` as a named column in the 10-col contract. Phase 02 rating features are to be joined from `player_history_all` only. Plan's "Out of scope / Q4" correctly defers `matches_history_minimal` propagation. Context, not risk.

### NOTE-2 — Major-vs-minor spec bump defensible per §7

Spec 02_00 §7: "any change to §2 column-grain commitments (VIEW names, row counts, column counts, schema_version values)… is major vN+1." Adding a column bumps column count 14 → 15 — squarely inside the "column counts" clause. Major bump v1 → v2 is correct per literal spec text. NO revision needed.

### NOTE-3 — Correlation-with-reset cell is sanity check, not evidence

T02's rating-reset correlation cell provides sanity check on semantic coupling with WP-4. It does not provide new evidence for the threshold choice. Plan correctly scopes as verification. No revision.

## Verdict

**REVISE BEFORE EXECUTION.** BLOCKER-1 (internal threshold inconsistency) + BLOCKER-2 (cross-leaderboard evidence inheritance) must both be addressed. WARNINGs 1-3 are substantive documentation/semantic fixes.

## If REVISE: required revisions (enumerated)

1. **BLOCKER-1:** T02 computes pooled `<Nd` agreement rate per candidate cutoff (N=1, 2, 3, 7). Pick the largest N where pooled rate ≥ 0.90 (WP-4 stratum gate). Justify the chosen N with the pooled computation in the notebook. INVARIANTS.md §3 and spec 02_00 §5.5 document the chosen N with rationale.
2. **BLOCKER-2:** T02 adds a 4×4 leaderboard × time-gap-bucket stratification table. If all 4 leaderboards clear 0.90 at the chosen cutoff, generalize the CONDITIONAL_PRE_GAME condition globally; otherwise scope the INVARIANTS.md classification to `leaderboard = 'random_map' AND time_since_prior_match_days < N`.
3. **WARNING-1:** Align T04 schema_version format with canonical_slot precedent (descriptive string, not semver).
4. **WARNING-2:** T06 updates spec 02_00 §2.2 "Column count" 14 → 15. Add sub-step updating ROADMAP.md:1000 current-state reference. Historical research_log entries NOT touched.
5. **WARNING-3:** INVARIANTS.md §3 revision + spec 02_00 §5.5 note spell out NULL-first-match rule (recommendation: NULL → PRE-GAME since no prior-match risk). T03 JSON records first-match NULL rate.
