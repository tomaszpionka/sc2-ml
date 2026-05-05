# Phase 02 Readiness Contracts Cross-Spec Consistency Report

**Spec:** CROSS-02-04-v1  
**Schema version:** v1  
**Run date:** 2026-05-05  
**Branch:** `phase02/feature-engineering-readiness`  
**Base ref:** `master`  
**HEAD SHA:** `e3cf8923bf293eb0a269a951b7b743418c01dcca`  
**Verdict:** **PASS**

## Reproduction

```
source .venv/bin/activate && poetry run python scripts/validate_phase02_readiness_contracts.py --base master --out-json reports/specs/02_04_cross_spec_consistency_report.json --out-md reports/specs/02_04_cross_spec_consistency_report.md --run-date 2026-05-05
```

## Generated outputs

These reports are written by `scripts/validate_phase02_readiness_contracts.py`. They are NOT hand-edited; their canonical regeneration path is the validator script.

- `reports/specs/02_04_cross_spec_consistency_report.json`
- `reports/specs/02_04_cross_spec_consistency_report.md`

## Reproducibility note

These reports are generated from the validator script at the recorded head_sha BEFORE the reports themselves are committed. The recorded head_sha therefore does NOT include the run's report files; the report commit lands afterwards. To reproduce a previous run byte-for-byte (apart from the run_date field), check out the recorded head_sha and re-run the recorded command_line. Determinism is guaranteed by the validator's stable list/dict ordering, sort_keys JSON output, and stdlib-only construction.

## Inputs read

- `.claude/rules/data-analysis-lineage.md`
- `planning/INDEX.md`
- `planning/current_plan.critique.md`
- `planning/current_plan.critique_resolution.md`
- `planning/current_plan.md`
- `reports/specs/02_00_feature_input_contract.md`
- `reports/specs/02_01_leakage_audit_protocol.md`
- `reports/specs/02_02_feature_engineering_plan.md`
- `reports/specs/02_03_temporal_feature_audit_protocol.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`
- `thesis/pass2_evidence/phase01_closeout_summary.md`

## Assumptions

- tracker_events_feature_eligibility.csv (15 rows; 5/7/3 split) is the authoritative SC2 in-game-snapshot contract per Amendment 2 of PR #208.
- CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1 are LOCKED and binding; CROSS-02-02-v1 and CROSS-02-03-v1 must not supersede or amend them.
- AoE2 four-tier ladder governance per thesis/pass2_evidence/aoe2_ladder_provenance_audit.md is binding (aoestats Tier 4; aoe2companion ID 6 = rm_1v1 ranked candidate; ID 18 = qp_rm_1v1 quickplay/matchmaking-derived; combined = mixed-mode).
- GATE-14A6 outcome is narrowed; full tracker scope is not closed (PR #208 14A.6 POST-VALIDATION UPDATE).
- T01-T04 outputs are documentation/specification only; no notebooks, generated artifacts, raw data, ROADMAPs, research_logs, status YAMLs, or thesis chapters are touched in this PR.

## Sanity checks

- Working tree state and git diff against base reflect only the declared File Manifest plus T05 reports.
- Each T01-T04 output contains its required positive phrases and zero literal banned substrings.
- Tracker CSV split (5/7/3) and family names match the canonical contract.
- CROSS-02-02-v1 and CROSS-02-03-v1 frontmatter declare supersedes: null.

## Falsifiers

- Any out-of-manifest file in the PR diff is a BLOCKER.
- Any required phrase missing in its mandated file is a BLOCKER.
- Any forbidden substring present is a BLOCKER.
- Any AoE2 source-label regression (unqualified ranked ladder for aoestats; combined scope as ranked-only) is a BLOCKER.
- Any tracker-derived feature in pre_game/history_enriched_pre_game is a BLOCKER.
- Any 'full tracker scope is closed' assertion is a BLOCKER.
- Any commit of CROSS-02-03 framed as replacing CROSS-02-01-v1.0.1 is a BLOCKER.

## Checks summary

| # | Check | Verdict | Details |
|---|---|---|---|
| 1 | 1. PR file scope | PASS | PR diff matches declared File Manifest (8 expected paths; T05 outputs allowed if present). |
| 2 | 2. Required positive phrases | PASS | All required positive phrases present in their mandated files. |
| 3 | 3. Forbidden substrings | PASS | No forbidden substrings; all 'ranked ladder' / 'ranked-only' occurrences in negation or source-specific context. |
| 4 | 4. Non-supersession of CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1 | PASS | CROSS-02-02-v1 and CROSS-02-03-v1 explicitly declare non-supersession of locked sibling specs. |
| 5 | 5. SC2 tracker eligibility consistency | PASS | Tracker counts (5/7/3) and family names verified against CSV; T03/T04 represent all 15 families with correct status. |
| 6 | 6. AoE2 source-label discipline | PASS | AoE2 source labels (Tier 4, mixed-mode, ID 6 ranked candidate, ID 18 quickplay/matchmaking) all preserved. |
| 7 | 7. Temporal leakage rules | PASS | history_time < target_time, event.loop <= cutoff_loop, per-dataset anchors, and UTC discipline all preserved. |
| 8 | 8. Cold-start / no-magic-number gates | PASS | Cold-start gates declared; no magic-number commits detected. |
| 9 | 9. CROSS-02-03 D1-D15 + future audit schema completeness | PASS | D1-D15 declared (15); future audit artifact schema covers all 14 fields; T04 declares no artifact/notebook generated. |

## Per-check evidence

### 1. PR file scope

- git diff --name-only master..HEAD
- .claude/rules/data-analysis-lineage.md
- planning/INDEX.md
- planning/current_plan.critique.md
- planning/current_plan.critique_resolution.md
- planning/current_plan.md
- reports/specs/02_02_feature_engineering_plan.md
- reports/specs/02_03_temporal_feature_audit_protocol.md
- scripts/validate_phase02_readiness_contracts.py
- thesis/pass2_evidence/phase01_closeout_summary.md

### 2. Required positive phrases

- .claude/rules/data-analysis-lineage.md: 'A generated artifact is not evidence' x1
- .claude/rules/data-analysis-lineage.md: 'aoe2companion ID 6 + ID 18 is mixed-mode' x1
- .claude/rules/data-analysis-lineage.md: 'aoestats is Tier 4' x1
- .claude/rules/data-analysis-lineage.md: 'halt before artifact generation' x1
- reports/specs/02_02_feature_engineering_plan.md: 'GATE-14A6 outcome: narrowed' x2
- reports/specs/02_02_feature_engineering_plan.md: 'aoe2companion mixed-mode' x3
- reports/specs/02_02_feature_engineering_plan.md: 'aoestats Tier 4' x3
- reports/specs/02_02_feature_engineering_plan.md: 'event.loop <= cutoff_loop' x4
- reports/specs/02_02_feature_engineering_plan.md: 'full tracker scope is not closed' x2
- reports/specs/02_02_feature_engineering_plan.md: 'history_time < target_time' x10
- reports/specs/02_02_feature_engineering_plan.md: 'tracker-derived features are never pre-game' x1
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'GATE-14A6 outcome: narrowed' x2
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'aoe2companion mixed-mode' x3
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'aoestats Tier 4' x6
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'does not replace CROSS-02-01-v1.0.1' x3
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'event.loop <= cutoff_loop' x9
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'full tracker scope is not closed' x3
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'history_time < target_time' x6
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'tracker-derived features are never pre-game' x2
- thesis/pass2_evidence/phase01_closeout_summary.md: 'GATE-14A6 outcome: narrowed' x3
- thesis/pass2_evidence/phase01_closeout_summary.md: 'aoe2companion mixed-mode' x5
- thesis/pass2_evidence/phase01_closeout_summary.md: 'aoestats Tier 4' x5
- thesis/pass2_evidence/phase01_closeout_summary.md: 'full tracker scope is not closed' x3
- thesis/pass2_evidence/phase01_closeout_summary.md: 'tracker-derived features are never pre-game' x1

### 3. Forbidden substrings

- .claude/rules/data-analysis-lineage.md:151 OK_SOURCE_SPECIFIC (ranked ladder): line='- aoestats is Tier 4 semantic opacity and must not be called unqualified ranked ' ctx='- aoestats is Tier 4 semantic opacity and must not be called unqualified ranked ladder. - aoe2companion ID 6 is rm_1v1 ranked candidate.'
- .claude/rules/data-analysis-lineage.md:154 OK_NEGATION (ranked-only): line='- aoe2companion ID 6 + ID 18 is mixed-mode and must not be called ranked-only.' ctx='- aoe2companion ID 18 is qp_rm_1v1 quickplay/matchmaking-derived. - aoe2companion ID 6 + ID 18 is mixed-mode and must not be called ranked-only.'
- reports/specs/02_02_feature_engineering_plan.md:315 OK_NEGATION (ranked ladder): line='aoestats MUST NOT be called unqualified ranked ladder. The `leaderboard`' ctx='aoestats MUST NOT be called unqualified ranked ladder. The `leaderboard` filter retains records whose upstream queue semantics (ranked vs quickplay vs'
- reports/specs/02_02_feature_engineering_plan.md:360 OK_NEGATION (ranked-only): line='and is not ranked-only — Phase 02 prose, label, and stratification fields' ctx='(quickplay/matchmaking-derived; Tier 3). The combined scope is mixed-mode and is not ranked-only — Phase 02 prose, label, and stratification fields must preserv'
- reports/specs/02_02_feature_engineering_plan.md:398 OK_NEGATION (ranked-only): line='- ID 6 + ID 18 combined: aoe2companion mixed-mode, not ranked-only.' ctx='- ID 18 (`qp_rm_1v1`): Tier 3 — quickplay/matchmaking-derived. - ID 6 + ID 18 combined: aoe2companion mixed-mode, not ranked-only.'
- reports/specs/02_02_feature_engineering_plan.md:584 OK_NEGATION (ranked ladder): line='- any AoE2 source is called unqualified ranked ladder in §7, §8, §9, or' ctx='of PR #208); - any AoE2 source is called unqualified ranked ladder in §7, §8, §9, or   downstream prose generated against this spec;'
- reports/specs/02_03_temporal_feature_audit_protocol.md:168 OK_NEGATION (ranked-only): line='| **D14** | AoE2 source-label discipline | aoestats is labeled aoestats Tier 4 (' ctx='| **D13** | SC2 tracker eligibility constraint | Every SC2 `in_game_snapshot` family appears in `tracker_events_feature_eligibility.csv` with `status_in_game_sn'
- reports/specs/02_03_temporal_feature_audit_protocol.md:168 OK_SOURCE_SPECIFIC (ranked ladder): line='| **D14** | AoE2 source-label discipline | aoestats is labeled aoestats Tier 4 (' ctx='| **D13** | SC2 tracker eligibility constraint | Every SC2 `in_game_snapshot` family appears in `tracker_events_feature_eligibility.csv` with `status_in_game_sn'
- reports/specs/02_03_temporal_feature_audit_protocol.md:368 OK_NEGATION (ranked ladder): line='unqualified ranked ladder. A feature row that uses an unqualified' ctx='against upstream API documentation; Tier 4)". aoestats MUST NOT be called unqualified ranked ladder. A feature row that uses an unqualified ranked-ladder label '
- reports/specs/02_03_temporal_feature_audit_protocol.md:378 OK_NEGATION (ranked-only): line='- **ID 6 + ID 18 combined**: aoe2companion mixed-mode, not ranked-only.' ctx='fallback rule (external API unavailable as of 2026-04-26). - **ID 6 + ID 18 combined**: aoe2companion mixed-mode, not ranked-only.   Phase 02 prose, label, and '
- reports/specs/02_03_temporal_feature_audit_protocol.md:471 OK_NEGATION (ranked-only): line='(mixed-mode), or asserts that ID 6 + ID 18 is ranked-only.' ctx='quickplay/matchmaking qualifier from the aoe2companion combined scope   (mixed-mode), or asserts that ID 6 + ID 18 is ranked-only. - **Pseudocount / smoothing c'
- reports/specs/02_03_temporal_feature_audit_protocol.md:509 OK_NEGATION (ranked ladder): line='unqualified ranked ladder; no new doc calls the aoe2companion combined' ctx='- **No ranked-ladder regression for AoE2.** No new doc calls aoestats   unqualified ranked ladder; no new doc calls the aoe2companion combined   scope ranked-on'
- reports/specs/02_03_temporal_feature_audit_protocol.md:510 OK_NEGATION (ranked-only): line='scope ranked-only.' ctx='unqualified ranked ladder; no new doc calls the aoe2companion combined   scope ranked-only. - **No tracker pre-game regression.** No new doc declares an SC2'
- reports/specs/02_03_temporal_feature_audit_protocol.md:568 OK_NEGATION (ranked ladder): line='- any AoE2 source is called unqualified ranked ladder, or the aoe2companion' ctx='PR #208 violation); - any AoE2 source is called unqualified ranked ladder, or the aoe2companion   combined scope is asserted as ranked-only.'
- reports/specs/02_03_temporal_feature_audit_protocol.md:569 OK_NEGATION (ranked-only): line='combined scope is asserted as ranked-only.' ctx='- any AoE2 source is called unqualified ranked ladder, or the aoe2companion   combined scope is asserted as ranked-only.'
- thesis/pass2_evidence/phase01_closeout_summary.md:35 OK_NEGATION (ranked ladder): line='`aoestats` and `aoe2companion` MUST NOT be referred to as ranked ladder without ' ctx='`aoestats` and `aoe2companion` MUST NOT be referred to as ranked ladder without explicit qualification. The four-tier ladder governance from `thesis/pass2_evide'
- thesis/pass2_evidence/phase01_closeout_summary.md:95 OK_SOURCE_SPECIFIC (ranked ladder): line='- `aoestats` is described as simply ranked ladder without the Tier 4 hedge;' ctx='- a sentence implies the full SC2 tracker scope is `closed` (must remain `narrowed`); - `aoestats` is described as simply ranked ladder without the Tier 4 hedge'
- thesis/pass2_evidence/phase01_closeout_summary.md:96 OK_SOURCE_SPECIFIC (ranked ladder): line='- `aoe2companion` ID 6 + ID 18 combined is described as ranked ladder without th' ctx='- `aoestats` is described as simply ranked ladder without the Tier 4 hedge; - `aoe2companion` ID 6 + ID 18 combined is described as ranked ladder without the mi'

### 4. Non-supersession of CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1

- reports/specs/02_02_feature_engineering_plan.md: 'does not supersede or amend' present
- reports/specs/02_02_feature_engineering_plan.md: 'supersedes: null' present
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'does not replace CROSS-02-01-v1.0.1' present
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'supersedes: null' present

### 5. SC2 tracker eligibility consistency

- blocked_until_additional_validation (3): army_centroid_at_cutoff_snapshot, mind_control_event_count, playerstats_cumulative_economy_fields
- eligible_for_phase02_now (5): building_construction_count_by_cutoff_loop, count_units_built_by_cutoff_loop, count_units_killed_by_cutoff_loop, morph_count_by_cutoff_loop, slot_identity_consistency
- eligible_with_caveat (7): army_value_at_5min_snapshot, count_units_lost_by_cutoff_loop, count_upgrades_by_cutoff_loop, food_used_max_history, minerals_collection_rate_history_mean, supply_used_at_cutoff_snapshot, time_to_first_expansion_loop
- reports/specs/02_02_feature_engineering_plan.md: slot_identity_consistency marked as sanity gate

### 6. AoE2 source-label discipline

- reports/specs/02_02_feature_engineering_plan.md: 'aoe2companion mixed-mode' x3
- reports/specs/02_02_feature_engineering_plan.md: 'aoestats Tier 4' x3
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'aoe2companion mixed-mode' x3
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'aoestats Tier 4' x6
- thesis/pass2_evidence/phase01_closeout_summary.md: 'aoe2companion mixed-mode' x5
- thesis/pass2_evidence/phase01_closeout_summary.md: 'aoestats Tier 4' x5

### 7. Temporal leakage rules

- reports/specs/02_02_feature_engineering_plan.md: 'event.loop <= cutoff_loop' x4
- reports/specs/02_02_feature_engineering_plan.md: 'history_time < target_time' x10
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'event.loop <= cutoff_loop' x9
- reports/specs/02_03_temporal_feature_audit_protocol.md: 'history_time < target_time' x6

### 8. Cold-start / no-magic-number gates

- reports/specs/02_02_feature_engineering_plan.md: gate marker 'Invariant I7' present
- reports/specs/02_02_feature_engineering_plan.md: gate marker 'No magic' present
- reports/specs/02_02_feature_engineering_plan.md: gate marker 'training fold' present
- reports/specs/02_02_feature_engineering_plan.md: gate marker 'training-fold' present
- reports/specs/02_03_temporal_feature_audit_protocol.md: gate marker 'Invariant I7' present
- reports/specs/02_03_temporal_feature_audit_protocol.md: gate marker 'training-fold' present

### 9. CROSS-02-03 D1-D15 + future audit schema completeness

- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D1 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D10 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D11 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D12 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D13 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D14 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D15 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D2 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D3 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D4 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D5 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D6 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D7 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D8 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: dimension D9 declared
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'audit_dimensions_passed' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'blocking_reason' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'caveats' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'cutoff_rule' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'dataset' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'feature_family_id' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'model_input_grain' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'prediction_setting' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'reviewer_notes' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'source_grain' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'source_table_or_event_family' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'spec_version' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'temporal_anchor' declared (backticked)
- reports/specs/02_03_temporal_feature_audit_protocol.md: future schema field 'verdict' declared (backticked)

