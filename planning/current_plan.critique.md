# Adversarial Review — Plan (Mode A) — WP-1

**Plan:** `planning/current_plan.md`
**Branch:** `docs/phase02-interface-contract`
**Base:** `master` @ `d1e25b47` (post PR #197)
**Date:** 2026-04-21
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|---|---|
| Scope discipline | ADEQUATE — §6 Phase 02 cross-ref is borderline scope-creep but is explicitly constrained to abstract entries in T02 instruction 7. §4 encoding protocol does not over-commit to encoder classes (it gives acceptable patterns, not a mandated library). |
| Assumption load-bearingness | AT RISK — two of five assumptions are falsified on first contact with the yamls (details below). |
| Spec completeness | AT RISK — three likely-imminent amendments flagged. |
| Interface-contract precedent | WEAK — 01_05 has LOCKED, amendment log (§14), binding mechanism (§13), spec_id/spec_version frontmatter, and 16 sections. The plan's spec has only a fraction. |
| Gate condition verifiability | ADEQUATE — 7/8 conditions observable; §5 classification spot-check is soft but acceptable. |
| File manifest accuracy | AT RISK — rollup's GO-NARROW aoestats text is stale; T04 adds a backlink without refreshing it. `docs/INDEX.md` not updated. |
| Invariant-touched list | AT RISK — I2 (player_id branch polymorphism) and I9 (research pipeline discipline; see cold-start NOTE below) are both touched but not declared. |
| Tight-vs-complete tension | ADEQUATE with risks — scope is minimum-viable for the 3 audit closures; §6 adds mild gold-plating but is defensible as Phase 02 anchoring. |
| Execution realism | ADEQUATE — 1 session plausible; T02 is the pressure point (~8 sections, ~6–8 yamls read). |

## BLOCKER / WARNING / NOTE findings

1. **[BLOCKER] Plan §3 SQL rule names columns that do not exist in `player_history_all`.** T02 instruction 4 prescribes: "every rolling-window query MUST include `WHERE ph.started_at < target.started_at` as the I3 guard." The three `player_history_all` yamls use three different column names and two different dtypes for the temporal anchor: sc2egset = `details_timeUTC` (VARCHAR, not TIMESTAMP, per `player_history_all.yaml:173-177`), aoestats = `started_timestamp` (TIMESTAMPTZ, per `player_history_all.yaml:21-29`), aoe2companion = `started` (TIMESTAMP, per `player_history_all.yaml:26-29`). Only `matches_history_minimal` exposes `started_at` (canonical). If the spec LOCKS that exact SQL pattern, every Phase 02 extractor that reads `player_history_all` will emit a column-not-found error. This is a spec-correctness failure, not a spec-fidelity nit. The spec must either (a) name the per-dataset `player_history_all` temporal column explicitly in §3, or (b) require Phase 02 to wrap `player_history_all` in a dataset-specific VIEW that canonicalizes the anchor to `started_at` before consumption.

2. **[BLOCKER] Plan §3 "Canonical join keys: `player_id`" is wrong for `player_history_all`.** sc2egset PH exposes `toon_id` (`player_history_all.yaml:22-26`); aoestats PH exposes `profile_id` (`player_history_all.yaml:10-14`); aoe2companion PH exposes `profileId` (`player_history_all.yaml:15-19`). Only `matches_history_minimal` exposes the harmonized `player_id`. A join spec that prescribes `ph.player_id = target.player_id` fails for all three. Same remediation as #1 (either name them explicitly, or require a canonicalizing VIEW before Phase 02).

3. **[WARNING] Precedent spec `01_05_preregistration.md` §1 declares a *different* 9-column `matches_history_minimal` contract than the yamls actually have.** 01_05 §1 lists `{match_id, started_at, player_id, team, chosen_civ_or_race, rating_pre, won, map_id, patch_id}`. The actual yamls (post-PR #197) expose `{match_id, started_at, player_id, opponent_id, faction, opponent_faction, won, duration_seconds, dataset_tag}`. Only 4 column names overlap. 01_05 §14 v1.1.0 records canonical_slot as the one addition, but does not amend §1 to match the current schema. The plan's T02 correctly treats the yamls as authoritative (instructions 4–5), but the plan cites 01_05 as "the pattern to follow" (Scope §, line 60). An executor may mirror 01_05 §1's stale column list into the new spec's §2 instead of deriving from the yamls. Recommendation: T02 instruction 3 should explicitly say "do NOT inherit column names from 01_05 §1; derive from yamls exclusively."

4. **[WARNING] §4 encoding protocol is under-scoped; faction is not the only cross-game polymorphic categorical Phase 02 will hit.** The plan's assumption-block claim (plan line 67) is true only for `matches_history_minimal`. For `player_history_all` (which Phase 02 consumes for rolling-window features per §6 rows 02_03 and 02_04), at least three additional columns have per-dataset polymorphic vocabulary: `map`/`metadata_mapName` (sc2 map names vs aoe2 map names, empirically disjoint — 94 distinct aoec maps per `matches_1v1_clean.yaml:48`; 77 distinct aoestats maps per `matches_1v1_clean.yaml:26`; sc2 map names like "Catalyst LE"), `leaderboard` (aoestats + aoe2companion only; sc2egset has none — asymmetric, not polymorphic), and the column-name asymmetry `civ` (aoestats/aoe2companion) vs `race` (sc2egset). §4 as drafted (T02 step 5) stops at `faction` and forbids `GROUP BY faction` across `dataset_tag`, but a Phase 02 implementer could cheerfully one-hot encode `map` across all three datasets — a semantically identical I8 violation. §4 should declare a general rule (any column whose vocabulary is per-dataset must be encoded within a `dataset_tag` partition) and name `faction`/`map` as illustrative instances, not as the exclusive scope.

5. **[NOTE] Invariant-touched list omits I2 and understates I7.** Plan frontmatter declares `invariants_touched: [I3, I5, I8]`. The spec §3 commits to the canonical `player_id` for rolling-window joins across three datasets whose I2 branch resolutions differ: sc2egset = Branch (iii) region-scoped toon_id; aoestats = Branch (v) structurally-forced profile_id; aoe2companion = Branch (i) API-namespace profileId (per `cross_dataset_phase01_rollup.md:34`). Binding a shared join column atop three I2 branches IS an I2-touching decision. Also: if the spec commits to "10 matches minimum history" or similar cold-start threshold, I7 applies.

6. **[NOTE] Missing `player_id` cross-dataset collision discussion.** `matches_history_minimal.match_id` is prefixed with `<dataset_tag>::` (collision-safe across datasets; see sc2egset `matches_history_minimal.yaml:14-18`). But `matches_history_minimal.player_id` is NOT prefixed — it is the raw toon_id / CAST profile_id / CAST profileId. On cross-dataset UNION ALL, an sc2egset toon_id string numerically equal to an aoec profileId string would collide. Probability of accidental collision on large-N is low but non-zero. The plan's §3 open-question Q2 asks about `dataset_tag` synthesis but doesn't flag the player_id collision risk. The spec should at least acknowledge that cross-dataset player_id joins require `(dataset_tag, player_id)` composite keys, not bare player_id.

7. **[NOTE] Rollup's aoestats "GO-NARROW" text is stale.** Bonus finding during file inventory: `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md:15` still says "**GO-NARROW** (aggregate / UNION-ALL-symmetric features; per-slot deferred until F1+W4)" for aoestats. That text became stale 2026-04-20 when canonical_slot landed (PR #185); `modeling_readiness_aoestats.md:13,76-78` now say GO-FULL. T04 adds a backlink to the rollup without refreshing the stale text. Adding new text next to internally-contradictory existing text is a thesis-defensibility liability. Out of scope per the plan's closure targets (plan does NOT claim to refresh the rollup generally), but flagged for a separate Cat E follow-up or as an in-scope expansion of T04.

## Verdict

**REVISE BEFORE EXECUTION.** Findings #1 and #2 are BLOCKER class — the plan will produce a spec whose central binding rule (§3 join + I3 guard SQL pattern) names columns that do not exist in two-thirds of the source tables it is supposed to describe. This is not a cosmetic issue: if Phase 02 planner-science consumes the spec at face value, they will draft queries that fail at execution time, and a version bump (CROSS-02-00-v2) will be required before any feature is computed. Applying one revision round (per the symmetric 1-revision cap) is the right call.

## If REVISE: required revisions (enumerated list)

1. **Rewrite plan assumption #3** (line 66) to distinguish: "`started_at` is the canonical I3 anchor in `matches_history_minimal` (all three datasets). The corresponding anchor in `player_history_all` has three different names (sc2egset: `details_timeUTC`; aoestats: `started_timestamp`; aoe2companion: `started`) and two dtypes (VARCHAR, TIMESTAMPTZ, TIMESTAMP). The spec must either list these per-dataset or prescribe a canonicalizing VIEW."

2. **Rewrite T02 instruction 4** so §3 declares per-dataset join-key and anchor-column mappings for BOTH `matches_history_minimal` (canonical `player_id`/`started_at`) and `player_history_all` (per-dataset raw column names) — OR prescribes a Phase 02-owned canonicalizing VIEW. The SQL example in the spec must not name columns that don't exist in every table it applies to.

3. **Add T01 sub-step** explicitly contrasting column-name sets across `matches_history_minimal` vs `player_history_all` vs `01_05_preregistration.md §1` — executor flags the 01_05 §1 staleness before drafting §5.

4. **Broaden T02 instruction 5 (§4 encoding)** to declare a general rule ("any column with per-dataset polymorphic vocabulary must be encoded within a `dataset_tag` partition"), then name `faction`, `map`, and `race`/`civ` column-name asymmetry as concrete instances. Drop the plan-line-67 "faction is the only cross-game polymorphic categorical" assumption.

5. **Add frontmatter field `invariants_touched: [I2, I3, I5, I8]`** and a one-sentence §1 note that binding a shared join column atop three I2 branches is an I2-touching cross-dataset commitment.

6. **Add §3 clause**: "Cross-dataset player-history joins use composite key `(dataset_tag, player_id)`; bare `player_id` is per-dataset only."

7. **Remove claim** (plan line 77) that 01_05 is "the pattern to follow" verbatim; restate as "01_05 is the frontmatter/versioning-discipline reference; §1 column contract is dataset-specific and not inherited."

8. **Optionally, add T06** (or T03 sub-step): refresh `cross_dataset_phase01_rollup.md:15` to change aoestats "GO-NARROW" → "GO-FULL" (stale per `modeling_readiness_aoestats.md:13,78` post-2026-04-20 canonical_slot landing). Otherwise the file the plan edits contains internally-contradictory text next to the new backlink. If out of scope for WP-1, file a separate Cat E follow-up.
