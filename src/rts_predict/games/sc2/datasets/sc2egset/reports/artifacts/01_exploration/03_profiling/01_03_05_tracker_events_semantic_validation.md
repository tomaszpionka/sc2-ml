# Step 01_03_05 -- Tracker Events Semantic Validation
**Dataset:** sc2egset  
**Game:** sc2  
**Phase:** 01 -- Data Exploration  
**Pipeline section:** 01_03 -- Systematic Data Profiling  
**Predecessor:** 01_03_04  
**Generated:** 2026-05-05  
**Invariants applied:** I3, I6, I7, I9, I10
---
## GATE-14A6 decision
- **gate_14a6_decision:** `narrowed` (NOT fully closed; the planned subset is ready but the full tracker scope remains narrowed)
- **initial_phase02_subset_ready:** `True`
- **planned_subset_ready_predicate_satisfied:** `True` (scope: planned_for_phase02=yes rows only)
- **full_tracker_scope_closed_predicate_satisfied:** `False` (scope: ALL relevant tracker candidate families; only this predicate being True warrants `gate_14a6_decision = closed`)

**Rationale.** The initial Phase 02 tracker-derived subset is ready: all 12 planned_for_phase02=yes rows are eligible_for_phase02_now or eligible_with_caveat. However, the full tracker_events_raw semantic scope remains narrowed because 3 relevant candidate families are blocked with explicit reasons: ['mind_control_event_count', 'army_centroid_at_cutoff_snapshot', 'playerstats_cumulative_economy_fields']. Therefore gate_14a6_decision = narrowed and initial_phase02_subset_ready = true.
---
## Verdict summary (V1..V8)
### V1 -- PASS_WITH_CAVEAT

- **Hypothesis:** details.gameSpeed cardinality is one ('Faster') across SC2EGSet AND a single loop-to-seconds factor (22.4 lps for Faster) can be applied uniformly.
- **Falsifier:** multiple gameSpeed values; tracker loops past elapsedGameLoops on non-trivial fraction; mean tracker_to_end ratio < 0.95; no defensible loop-to-seconds source
- **Caveat:** Empirical checks pass; lps_source is empirical (not source-confirmed by s2protocol). Q2: Liquipedia stays contextual only. PASS_WITH_CAVEAT per T03 step 7 / step 10.
### V2 -- PASS

- **Hypothesis:** PlayerStats->playerId; UnitBorn/Init/OwnerChange->controlPlayerId (+upkeepPlayerId); UnitDied->killerPlayerId (killer attribution; victim is lineage_required); Upgrade->playerId; PlayerSetup->playerId. UnitTypeChange/UnitDone/UnitPositions have NO direct player-id field and require lineage.
- **Falsifier:** no stable mapping field for player-attributed rows; player-attributed match rate < 99.5% on the player_attributed slice (Amendment 3); ambiguous ties; direct fields contradict replay_players_raw
- **Notes:** All 7 direct-mapping event types HIGH confidence; 3 event types correctly classified lineage_required.
### V3 -- PASS_WITH_CAVEAT

- **Hypothesis:** PlayerStats records periodic per-player economic / military snapshots; suitable for in-game snapshot features if cadence, mapping, and field completeness pass; cumulative interpretation NOT assumed (Q3 strict).
- **Falsifier:** cadence not stable per (filename, playerId); missing PlayerStats for material number of replays; key-set drift; values cannot be classified; candidate feature family field semantics unverified
- **Notes:** snapshot cadence and key-set match; 26 safe_snapshot fields enable in-game snapshot features; cumulative-economy features blocked because s2protocol silent on cumulative semantics (Q3 strict)
### V4 -- PASS_WITH_CAVEAT

- **Hypothesis:** all 10 tracker event families have stable presence and JSON key structure across the 2016-2024 SC2EGSet corpus
- **Falsifier:** any planned-feature family missing/unstable across major year/gameVersion cohorts; key-set differs >=2 keys between non-trivial cohorts (>5% each); rare-event under-sampling blocks decision
- **Notes:** all 10 event families stable; sparse / occasionally-absent caveats on: ['UnitOwnerChange']; V8 must propagate these as feature_eligibility caveats
### V5 -- PASS_WITH_CAVEAT

- **Hypothesis:** lifecycle events record local state transitions at their loop; cutoff counts are computable without post-game leakage; lineage joins resolve owner for no-direct-id event families
- **Falsifier:** death/done/type-change before origin at material rate; lineage ambiguity from tag-recycle; missing/unstable keys; future-dependent semantics; lineage cannot resolve owner for a planned feature family
- **Notes:** ordering OK; blocked: ['UnitOwnerChange', 'UnitPositions']; caveated: ['Upgrade']
- amendment_4_compliance: True
### V6 -- PASS_WITH_CAVEAT

- **Hypothesis:** tracker coordinate fields are local observations usable descriptively if units / origin are understood and bounds are plausible
- **Falsifier:** units / origin not source-confirmed AND empirical bounds inconsistent; material out-of-bounds rate without explainable convention; UnitPositions cannot be decoded; future-dependent semantics
- **Notes:** source-confirmation gate not met (units / origin not confirmed in s2protocol); coord-bearing eligibility capped at eligible_with_caveat; blocked: ['UnitPositions']; caveated: ['UnitBorn', 'UnitInit', 'UnitDied']
- amendment_5_compliance: True
### V7 -- PASS_WITH_CAVEAT

- **Hypothesis:** tracker events are safe for in-game snapshot features iff event.loop <= cutoff_loop AND target setting is in-game; tracker-derived families NEVER pre-game
- **Falsifier:** any tracker-derived family marked pre-game; boundary uses future events; events beyond replay end at material rate; seconds conversion overclaimed as source-confirmed
- **Notes:** leakage boundary OK; in-game blocked: ['playerstats_cumulative_economy_fields', 'unitownerchange_dynamic_ownership', 'unitpositions_coordinate_features']; caveated: ['playerstats_snapshot_fields', 'upgrade_occurrence_counts', 'unitborn_unitinit_unitdied_direct_xy', 'time_to_first_event_features']; cutoff in loops; seconds conversion is contextual only (V1 caveat)
- amendment_2_compliance: True
### V8 -- PASS_WITH_CAVEAT

---
## Feature-family eligibility table
15 candidate feature families: 12 planned-for-Phase-02, 3 not planned (blocked with explicit reasons).

| feature_family | source | planned | in_game_snapshot | blocking_reason_if_blocked |
|---|---|---|---|---|
| `minerals_collection_rate_history_mean` | PlayerStats | yes | eligible_with_caveat |  |
| `army_value_at_5min_snapshot` | PlayerStats | yes | eligible_with_caveat |  |
| `supply_used_at_cutoff_snapshot` | PlayerStats | yes | eligible_with_caveat |  |
| `food_used_max_history` | PlayerStats | yes | eligible_with_caveat |  |
| `count_units_built_by_cutoff_loop` | UnitBorn | yes | eligible_for_phase02_now |  |
| `time_to_first_expansion_loop` | UnitBorn | yes | eligible_with_caveat | full-replay MIN(loop) is post-cutoff target leakage; that interpretation is blocked eve... |
| `count_units_killed_by_cutoff_loop` | UnitDied | yes | eligible_for_phase02_now |  |
| `count_units_lost_by_cutoff_loop` | UnitDied | yes | eligible_with_caveat |  |
| `morph_count_by_cutoff_loop` | UnitTypeChange | yes | eligible_for_phase02_now |  |
| `count_upgrades_by_cutoff_loop` | Upgrade | yes | eligible_with_caveat |  |
| `mind_control_event_count` | UnitOwnerChange | no | blocked_until_additional_validation | V4 sparse_event_family_not_broadly_available (absent in 2016, present in ~25% of replay... |
| `army_centroid_at_cutoff_snapshot` | UnitPositions | no | blocked_until_additional_validation | V6 requires_additional_unpacking_validation (items packed-triplet decoder + UnitBorn-li... |
| `building_construction_count_by_cutoff_loop` | UnitInit / UnitDone | yes | eligible_for_phase02_now |  |
| `slot_identity_consistency` | PlayerSetup | yes | eligible_for_phase02_now |  |
| `playerstats_cumulative_economy_fields` | PlayerStats | no | blocked_until_additional_validation | V3 cumulative_economy_blocked=True (Q3 strict): s2protocol does not confirm cumulative ... |

Full rows (with eligibility_scope, caveat, evidence_source, upstream_verdicts, notes_for_phase02) are in `tracker_events_feature_eligibility.csv` and the JSON artifact.
---
## Blocked families (3, all planned-no)
- **`mind_control_event_count`** (UnitOwnerChange): V4 sparse_event_family_not_broadly_available (absent in 2016, present in ~25% of replays in 8 of 9 years); V5 dynamic-ownership features blocked; not broadly available as a feature family for cross-replay learning
- **`army_centroid_at_cutoff_snapshot`** (UnitPositions): V6 requires_additional_unpacking_validation (items packed-triplet decoder + UnitBorn-lineage owner attribution NOT validated); V6 source-confirmation gap (units / origin not source-confirmed per Amendment 5)
- **`playerstats_cumulative_economy_fields`** (PlayerStats): V3 cumulative_economy_blocked=True (Q3 strict): s2protocol does not confirm cumulative semantics for *Lost / *Killed / *FriendlyFire / *Used keys; SOURCE_CONFIRMS_CUMULATIVE is empty
---
## SQL query registry
29 named queries captured per Invariant 6. Names:

- `v1_1_gamespeed_cardinality`
- `v1_2_loop_sanity`
- `v2_1_observed_keys_per_event_type`
- `v2_2_id_value_histogram`
- `v2_3_join_back_per_slot_class`
- `v2_4_control_upkeep_agreement`
- `v3_1_enumerate_stats_keys`
- `v3_2_cadence_gap_distribution`
- `v3_2_per_replay_player_coverage`
- `v3_2_same_player_duplicate_groups`
- `v3_3_field_stats`
- `v4_1_per_year_coverage`
- `v4_1_year_replay_totals`
- `v4_2_cohort_replay_totals`
- `v4_2_gameversion_cardinality`
- `v4_2_pass_a_keysets`
- `v4_2_pass_b_keysets`
- `v5_1_lifecycle_key_availability`
- `v5_2_origin_lineage_summary`
- `v5_3_lifecycle_ordering_audit`
- `v5_4_construction_audit`
- `v5_5_unit_type_change_attribution`
- `v5_6_unit_positions_structure`
- `v5_8_upgrade_count_semantics`
- `v6_1_map_bounds`
- `v6_2_direct_coord_availability`
- `v6_3_in_bounds_rate`
- `v6_4_unit_positions_structure`
- `v7_1_loop_boundary_check`

---
## Notes
- **Tracker-derived features are NEVER pre-game** (Amendment 2 / Invariant I3). Every row in the eligibility table carries `status_pre_game = not_applicable_to_pre_game`.
- **T11 does NOT implement Phase 02 features.** It validates semantics, classifies feature-family eligibility, and writes machine-readable artifacts (JSON / CSV / MD). Phase 02 must consume `tracker_events_feature_eligibility.csv` and respect each row's `eligibility_scope` and `blocking_reason_if_blocked`.
- **Initial planned-subset readiness** is NOT the same as **full tracker-events scope closure**. The two predicates are exposed separately in this artifact and in the JSON.
