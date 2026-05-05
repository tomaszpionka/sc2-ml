# Phase 01 Closeout Summary — Phase 02 Entry Conditions

**Date:** 2026-05-05
**Branch:** `phase02/feature-engineering-readiness`
**Author:** T01 executor (claude-opus-4-7)
**Provenance:** Closes Phase 01 across SC2EGSet, aoestats, and aoe2companion after PR #207 (thesis methodology hardening) and PR #208 (sc2egset Step 01_03_05 tracker events semantic validation).

This is **not thesis chapter prose** and does **not update Chapter 4**. Thesis chapter prose remains governed by `thesis/pass2_evidence/audit_cleanup_summary.md` and the PR #207 review choreography; thesis chapter wording is changed only by a future Category-F PR. This summary is a Phase 02 readiness gate document, intended to be read by the Phase 02 planner-science and executor sessions.

---

## 1. Phase 01 → Phase 02 Status Table

| Dataset / Scope | Phase 01 status | Phase 02 status | Pre-game/history readiness | Notes |
|-----------------|-----------------|-----------------|----------------------------|-------|
| `sc2egset` | complete | not_started | ready (with declared residuals: MMR 83.95% missing → `is_mmr_missing` flag; cross-region fragmentation handling deferred per RISK-20) | Glicko-2 reconstructable from `player_history_all`; Battle.net MMR is structurally missing for unrated professional rows |
| `sc2egset` tracker-derived in-game snapshot | initial planned subset ready (with caveats) | not_started | initial Phase 02 subset ready; full tracker scope is not closed | Authoritative contract: `tracker_events_feature_eligibility.csv` (15 rows; per-prediction-setting columns per Amendment 2). 12 planned-yes rows (5 eligible_for_phase02_now + 7 eligible_with_caveat); 3 blocked rows. `slot_identity_consistency` is a feature-engineering sanity gate, NOT a model input. |
| `aoestats` | complete | not_started | ready under aoestats Tier 4 semantic opacity wording | Source label `leaderboard='random_map'`; queue type unverified per T05 fallback rule; thesis-safe label per `aoe2_ladder_provenance_audit.md` §4.1.7 |
| `aoe2companion` | complete | not_started | ready under aoe2companion mixed-mode wording | `internalLeaderboardId IN (6, 18)`; ID 6 = `rm_1v1` (ranked candidate, Tier 2); ID 18 = `qp_rm_1v1` (quickplay/matchmaking, Tier 3); combined scope is mixed-mode |

The phase status values above were transcribed from:

- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml` (Phase 01 = complete; Phase 02 = not_started).
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml` (Phase 01 = complete; Phase 02 = not_started).
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PHASE_STATUS.yaml` (Phase 01 = complete; Phase 02 = not_started).

The notebook regeneration manifest (`thesis/pass2_evidence/notebook_regeneration_manifest.md`) reports 86 `confirmed_intact`, 7 `not_yet_assessed`, 0 `flagged_stale`, 0 `regenerated_pending_log` across all three datasets at Phase 01 close. No stale-artifact prerequisite blocks Phase 02 entry.

**This closeout is not thesis chapter prose and does not update Chapter 4.**

---

## 2. AoE2 Source-Specific Labels (Binding for Phase 02)

`aoestats` and `aoe2companion` MUST NOT be referred to as ranked ladder without explicit qualification. The four-tier ladder governance from `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.3 is binding for every Phase 02 spec, ROADMAP description, leakage audit, and feature catalog row that names an AoE2 dataset:

| Source | Tier | Label |
|--------|------|-------|
| `aoestats` (`leaderboard='random_map'`, 1v1) | Tier 4 (aoestats Tier 4) | "aoestats 1v1 Random Map records (source label `random_map`; queue semantics unverified)" |
| `aoe2companion` ID 6 (`rm_1v1`) | Tier 2 | "aoe2companion ranked 1v1 Random Map records (`rm_1v1`, ID 6, ~54M leaderboard_raw rows)" |
| `aoe2companion` ID 18 (`qp_rm_1v1`) | Tier 3 | "aoe2companion quickplay/matchmaking 1v1 Random Map records (`qp_rm_1v1`, ID 18, ~7M leaderboard_raw rows)" |
| `aoe2companion` combined ID 6 + ID 18 | Tier 2/3 mixed | aoe2companion mixed-mode (1v1 Random Map records combining ranked ID 6 and quickplay/matchmaking ID 18) |

Phase 02 feature-engineering plans, leakage audit protocols, and ROADMAP descriptions MUST stratify AoE2 features by source label and `internalLeaderboardId` where present, and MUST NOT collapse `aoe2companion` ID 6 + ID 18 into a single ranked-ladder umbrella term without the mixed-mode qualifier.

The five-axis bounded comparability framing from `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §2 (game / data-regime / population / feature-availability / inference) is binding for any cross-dataset Phase 02 claim. Observed differences between SC2 and AoE2 results MUST be interpreted as differences in method, data regime, and population — NOT as pure game-mechanic differences.

---

## 3. SC2 Tracker-Derived Feature Scope (PR #208 Outcome)

GATE-14A6 outcome: narrowed.

The full tracker scope is not closed. Per PR #208 (Step 01_03_05, branch `phase01/sc2egset-tracker-events-semantic-validation`):

- The initial Phase 02 tracker-derived subset is ready under each row's `eligibility_scope` and `caveat`.
- Three SC2 tracker blocked candidate families remain `blocked_until_additional_validation` and remain outside initial Phase 02 scope:
  1. `playerstats_cumulative_economy_fields` — V3 Q3 strict; s2protocol cumulative semantics not source-confirmed for `*Lost` / `*Killed` / `*FriendlyFire` / `*Used` keys.
  2. `mind_control_event_count` (UnitOwnerChange dynamic ownership) — V4 sparse coverage (absent in 2016, present in ~25% of replays in 8 of 9 years); V5 dynamic-ownership blocked.
  3. `army_centroid_at_cutoff_snapshot` (UnitPositions coordinate) — V6 packed-items decoder + UnitBorn-lineage owner attribution NOT validated; coordinate units/origin not source-confirmed per Amendment 5.
- Tracker-derived features are never pre-game (Amendment 2 / Invariant I3); every row in `tracker_events_feature_eligibility.csv` carries `status_pre_game = not_applicable_to_pre_game`. Cutoff rule for any in-game snapshot is `event.loop <= cutoff_loop` (game loops; the seconds conversion `cutoff_seconds ~ cutoff_loop / 22.4` carries the V1 caveat that the loops-per-second factor is empirically corroborated at `gameSpeed='Faster'` but not directly source-confirmed by s2protocol).

The 12 `planned_for_phase02 = "yes"` rows in `tracker_events_feature_eligibility.csv` comprise 11 candidate feature/model-input families plus 1 feature-engineering sanity gate (`slot_identity_consistency`, structural validity check, NOT a model input).

---

## 4. Evidence-Lineage Table

| Claim | Source file | Source step or spec | Current verdict | Phase 02 consequence |
|-------|-------------|---------------------|-----------------|----------------------|
| sc2egset Phase 01 = complete; Phase 02 = not_started | `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml` | PHASE_STATUS yaml | confirmed | Phase 02 may begin under the new `02_02_feature_engineering_plan.md` (CROSS-02-02-v1) contract |
| aoestats Phase 01 = complete; Phase 02 = not_started | `src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml` | PHASE_STATUS yaml | confirmed | Phase 02 may begin under aoestats Tier 4 wording |
| aoe2companion Phase 01 = complete; Phase 02 = not_started | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PHASE_STATUS.yaml` | PHASE_STATUS yaml | confirmed | Phase 02 may begin under aoe2companion mixed-mode wording |
| GATE-14A6 outcome: narrowed (initial Phase 02 subset ready under tracker eligibility CSV; three blocked tracker families remain `blocked_until_additional_validation`) | `thesis/pass2_evidence/phase02_readiness_hardening.md` §14A.6 POST-VALIDATION UPDATE | PR #208 T11/T12 | confirmed | Phase 02 consumes the 12 planned-yes rows of `tracker_events_feature_eligibility.csv`; do NOT use the 3 blocked families |
| Authoritative tracker-derived feature contract (15 rows; per-prediction-setting columns) | `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv` | PR #208 Step 01_03_05 T11 | confirmed | feature-engineering plan and audit protocol consume this CSV without re-deriving family eligibility |
| AoE2 four-tier ladder mapping; aoestats Tier 4; aoe2companion mixed-mode (ID 6 ranked + ID 18 quickplay) | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.3, §4.4 | T05 (PR #207) | confirmed | feature-engineering plan must stratify AoE2 features by source label and `internalLeaderboardId` |
| Five-axis bounded comparability for cross-dataset claims | `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §2 | T09 (PR #207) | confirmed | cross-dataset Phase 02 claims must acknowledge data-regime + population + feature-availability + inference asymmetries |
| Notebook regeneration manifest: 86 `confirmed_intact`, 0 `flagged_stale`, 0 `regenerated_pending_log` | `thesis/pass2_evidence/notebook_regeneration_manifest.md` | T03/T07/T08/T12 lifecycle | confirmed | no stale-artifact prerequisite blocks Phase 02 entry |
| Methodology risk register: RISK-21 mitigated-narrowed; RISK-20 deferred (cross-region fragmentation retention %) | `thesis/pass2_evidence/methodology_risk_register.md` (T10 + post-Round-2 patch) | T10 (PR #207) | confirmed | Phase 02 must use Phase 01 cross-region empirical FAIL verdict at W=30 (median undercount 16.0 games, p95 29.0 games) but MUST NOT hard-code a retention percentage until Phase 02 measures it |
| Spec versions LOCKED at Phase 02 entry: CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1 | `reports/specs/02_00_feature_input_contract.md`, `reports/specs/02_01_leakage_audit_protocol.md` | T15 (PR #207) | confirmed | new specs in this PR (CROSS-02-02-v1 and CROSS-02-03-v1) do NOT supersede or amend the locked specs; they consume them |

---

## 5. Sanity / Falsifier / Validation / Lineage

### Sanity check

Every closeout claim above has a source path; every dataset has Phase 01 = complete and Phase 02 = not_started transcribed from the dataset PHASE_STATUS.yaml files; the tracker eligibility CSV is the single authoritative contract for SC2 in-game snapshot source families.

### Falsifier

This document is invalid if any of the following holds:

- a sentence implies the full SC2 tracker scope is `closed` (must remain `narrowed`);
- `aoestats` is described as simply ranked ladder without the Tier 4 hedge;
- `aoe2companion` ID 6 + ID 18 combined is described as ranked ladder without the mixed-mode qualifier;
- any tracker-derived family is described as available for the pre-game prediction setting (Invariant I3 violation; Amendment 2 violation).

### Artifact validation

The mandatory phrases for downstream readers and Phase 02 sessions, all present verbatim above, are:

- `GATE-14A6 outcome: narrowed`
- `full tracker scope is not closed`
- `aoestats Tier 4`
- `aoe2companion mixed-mode`
- `tracker-derived features are never pre-game`

### Lineage

This summary cites:

- PR #208 tracker artifacts: `tracker_events_feature_eligibility.csv`, `01_03_05_tracker_events_semantic_validation.md`, `01_03_05_tracker_events_semantic_validation.json` (all under `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/`).
- `thesis/pass2_evidence/phase02_readiness_hardening.md` (T16 sub-step decisions + PR #208 §14A.6 POST-VALIDATION UPDATE).
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` (T05 four-tier ladder governance).
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` (T09 five-axis bounded comparability).
- `thesis/pass2_evidence/notebook_regeneration_manifest.md` (T03/T07/T08/T12 lifecycle).
- `thesis/pass2_evidence/methodology_risk_register.md` (T10 + post-Round-2 patch).
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml`.
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml`.
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PHASE_STATUS.yaml`.

Out of scope for this closeout (deferred to downstream specs and PRs):

- feature-generation notebook authoring;
- model-ready feature table materialization;
- thesis chapter prose updates;
- closing the full tracker scope (requires future Step(s) per `thesis/pass2_evidence/phase02_readiness_hardening.md` §14A.6 future validation route).
