---
spec_id: CROSS-02-03-v1
version: CROSS-02-03-v1.0.1
status: LOCKED
date: 2026-05-06
invariants_touched: [I3, I5, I6, I7, I8, I9, I10]
datasets_bound: [sc2egset, aoestats, aoe2companion]
sibling_specs: [CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1, CROSS-02-02-v1]
supersedes: null
---

# Cross-Dataset Phase 02 Design-Time Temporal Feature Audit Protocol

## CROSS-02-03-v1.0.1 (LOCKED 2026-05-06; PR #209 merged ef3fc627 on 2026-05-05T21:00:02Z)

This document is the cross-dataset Phase 02 **design-time temporal feature
audit protocol**. It defines the per-feature-family checks that must pass at
design time — i.e., before any feature-generation notebook is authored or any
feature column is materialized. It is the design-time sibling to
CROSS-02-01-v1.0.1's post-materialization / pre-training leakage audit gate.

This spec is **LOCKED 2026-05-06** as `CROSS-02-03-v1.0.1` via the §13 patch lane after the reviewer-deep gate prescribed by the PR #209 readiness plan returned PASS-WITH-NOTES with 0 unresolved BLOCKERs (PR #209 merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` on 2026-05-05T21:00:02Z; cross-spec consistency verdict PASS / 0 blockers / head_sha `e3cf8923` per `reports/specs/02_04_cross_spec_consistency_report.json`); it now joins `CROSS-02-00-v3.0.1` and `CROSS-02-01-v1.0.1` in the binding cross-dataset Phase 02 contract triplet, complementing CROSS-02-01-v1.0.1's post-materialization audit gate without replacing it. This is an administrative lock transition only — no audit dimension D1–D15 semantics changed; the validator is not re-run; the `02_04` consistency reports remain on master under PR #209's recorded `head_sha`.

---

## §1 Scope and authority

### §1.1 What this spec is

CROSS-02-03 is a **design-time audit protocol**. It audits feature-family
**definitions** — i.e., the rows of CROSS-02-02-v1 §6 / §7 / §8 (and any
subsequent additions) — against a fixed set of temporal, source-label,
focal/opponent-symmetry, and lineage-discipline checks **before** feature
materialization. The audit object is a feature-family declaration, not a
feature value. The audit verdict is a per-family disposition that gates
whether the family may proceed to a Phase 02 ROADMAP step that materializes
it.

### §1.2 What this spec is not

This spec is **not** a feature catalog, a feature table, a notebook, an
audit artifact, or a training pipeline. The following operations are
explicitly out of scope:

- no feature generation;
- no notebooks;
- no generated artifacts;
- no model training;
- no thesis chapter prose;
- no ROADMAP edits;
- no research_log edits;
- no status YAML updates;
- no raw data edits.

The audit pipeline that consumes CROSS-02-03 (a future Phase 02 step) will
itself be created through the canonical lineage chain (ROADMAP stub →
notebook scaffold → validation module → user review → commit → artifact
generation → research_log / STEP_STATUS / manifest) per
`.claude/rules/data-analysis-lineage.md`.

### §1.3 Non-supersession clause

CROSS-02-03 **does not replace CROSS-02-01-v1.0.1**. The two specs are
complementary, not redundant:

- **CROSS-02-01-v1.0.1** (LOCKED 2026-04-26) remains the **post-materialization
  / pre-training leakage audit gate**. After a Phase 02 step materializes
  feature columns, CROSS-02-01-v1.0.1 §3 requires a `leakage_audit_<dataset>.json`
  + `.md` artifact with `verdict = "PASS"` before any consuming Pipeline
  Section may exit. CROSS-02-03 does not weaken, replace, or amend this gate.
- **CROSS-02-03-v1** (this spec) is a **design-time audit** that fires at the
  earlier moment of feature-family definition. A family that fails CROSS-02-03
  must not enter materialization. A family that passes CROSS-02-03 still must
  pass CROSS-02-01-v1.0.1 after materialization.

The two specs audit different objects at different points in the Phase 02
lifecycle. CROSS-02-03 audits **definitions**; CROSS-02-01-v1.0.1 audits
**materialized columns**. Both gates are mandatory.

### §1.4 Relationship to sibling specs

| Spec | Status | Role | CROSS-02-03 dependency |
|------|--------|------|-------------------------|
| `reports/specs/02_00_feature_input_contract.md` (**CROSS-02-00-v3.0.1**) | LOCKED 2026-04-26 | Authoritative input contract: VIEW names, column grain, join keys, per-dataset I3 anchors, cross-game encoding protocol, column-level classification | CROSS-02-03 reads §3.2 anchor table, §5 column classification, §4 encoding protocol |
| `reports/specs/02_01_leakage_audit_protocol.md` (**CROSS-02-01-v1.0.1**) | LOCKED 2026-04-26 | Authoritative post-materialization / pre-training leakage audit gate | CROSS-02-03 complements but does not replace |
| `reports/specs/02_02_feature_engineering_plan.md` (**CROSS-02-02-v1.0.1**) | LOCKED 2026-05-06 | Feature-engineering plan: feature families, prediction settings, grains, source labels, leakage-check declarations, cold-start gates, proposed Phase 02 ROADMAP steps | CROSS-02-03 audits the feature-family rows declared by CROSS-02-02-v1.0.1 §6 / §7 / §8 |

CROSS-02-03 does not modify any of the three sibling specs.

---

## §2 Lineage and consumed evidence

CROSS-02-03 reads, but does not modify, the following evidence:

| Source | Role |
|--------|------|
| `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v3.0.1) | Per-dataset I3 anchor table (§3.2), column-level classification (§5), cross-game encoding protocol (§4) |
| `reports/specs/02_01_leakage_audit_protocol.md` (CROSS-02-01-v1.0.1) | Post-materialization leakage audit dimensions (§2), audit artifact schema (§3), gate condition (§5) |
| `reports/specs/02_02_feature_engineering_plan.md` (CROSS-02-02-v1) | Feature-family rows; prediction settings; cold-start gate declarations; planned leakage checks G-L-1 through G-L-9; tracker eligibility summary |
| `thesis/pass2_evidence/phase01_closeout_summary.md` | Phase 01 → Phase 02 entry conditions; AoE2 source-specific labels; GATE-14A6 outcome |
| `thesis/pass2_evidence/phase02_readiness_hardening.md` | T16 14A.6 POST-VALIDATION UPDATE; future tracker validation route |
| `thesis/pass2_evidence/methodology_risk_register.md` | RISK-20 (cross-region fragmentation), RISK-21 (tracker semantics, MITIGATED-NARROWED post-PR #208), RISK-24 (focal/opponent slot asymmetry), RISK-25 (civ-pair cardinality), RISK-26 (SC2 Random race semantics) |
| `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` | Four-tier AoE2 ladder governance |
| `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` | Five-axis bounded comparability framing |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv` | Authoritative SC2 tracker-derived feature eligibility (15 rows; per-prediction-setting columns per Amendment 2 of PR #208) |
| `.claude/rules/data-analysis-lineage.md` | Anti-GIGO workflow rule |
| `.claude/scientific-invariants.md` | Invariants I3 (temporal), I5 (symmetry), I6 (verbatim SQL evidence), I7 (no magic numbers), I8 (cross-game comparability), I9 (source-stratified evaluation), I10 (filename relative paths) |

---

## §3 Audit object

The unit being audited by CROSS-02-03 is a **feature-family declaration**:
one row corresponding to one entry in CROSS-02-02-v1 §6 / §7 / §8 (or any
later-amended row). For each feature-family row, CROSS-02-03 commits the
following declared fields:

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `feature_family_id` | string | CROSS-02-02-v1 §6 / §7 / §8 row label | e.g., `sc2egset.history_enriched_pre_game.focal_player_history`, `aoestats.pre_game.civ_matchup`, `sc2egset.in_game_snapshot.count_units_built_by_cutoff_loop` |
| `dataset` | enum {`sc2egset`, `aoestats`, `aoe2companion`} | CROSS-02-02-v1 §6 / §7 / §8 column | Mandatory |
| `prediction_setting` | enum {`pre_game`, `history_enriched_pre_game`, `in_game_snapshot`, `blocked_or_deferred`} | CROSS-02-02-v1 §3 | Mandatory; mutually exclusive at the family level |
| `source_table_or_event_family` | string | CROSS-02-02-v1 row "Source" column | e.g., `matches_history_minimal.faction`, `player_history_all.metadata_mapName`, `tracker_events_raw.UnitBorn` |
| `source_grain` | enum from CROSS-02-00 §2 / CROSS-02-02-v1 §4.1 | CROSS-02-00-v3.0.1 §2 row grain | `2 rows per match (one per player)` (sc2egset / aoe2companion / aoestats post-projection); `1 row per player per match` for `player_history_all`; `1 event per row` for tracker event families |
| `model_input_grain` | enum from CROSS-02-02-v1 §4.2 | CROSS-02-02-v1 §4.2 | `match_pair / player_match focal row`, `match row with p0/p1 source columns` (pre-projection only), `in_game_snapshot candidate grain`, `target grain` |
| `target_grain` | string | CROSS-02-02-v1 §4.2 target row | One row per `(dataset_tag, match_id, focal_player_id)`; target column `won::BOOLEAN` |
| `temporal_anchor` | string | CROSS-02-00-v3.0.1 §3.2 + tracker CSV | Per-dataset native anchor on `player_history_all`: `details_timeUTC` (sc2egset), `started_timestamp` (aoestats), `started` (aoe2companion); harmonized anchor on `matches_history_minimal`: `started_at`; in-game tracker anchor: `event.loop` |
| `allowed_cutoff_rule` | string | CROSS-02-02-v1 §5 / §10 | `history_time < target_time` (strict; per CROSS-02-00-v3.0.1 §3.3) for history families; `event.loop <= cutoff_loop` for in-game snapshot families; `n/a` for static pre-game attributes of game T |
| `candidate_leakage_modes` | list of strings | CROSS-02-02-v1 §10 G-L-1 through G-L-9 | Family-specific subset (e.g., `target_match_final_state`, `post_game_rating_delta`, `full_replay_aggregate_for_cutoff`, `same_match_in_h2h`, `slot_asymmetry`, `source_mode_label_misuse`, `global_normalization_pre_split`) |
| `cold_start_handling` | string | CROSS-02-02-v1 §9 | One of: `no_cold_start_relevant`, `cold_start_flag_declared`, `bayesian_smoothing_with_fold_aware_prior_to_be_derived`, `first_match_explicitly_handled`. Constants are NOT pinned at this layer (per Invariant I7). |
| `status` | enum {`allowed`, `allowed_with_caveat`, `blocked_until_validation`, `sanity_gate_not_model_input`} | output of CROSS-02-03 audit | Per §10 below |

A feature-family row that omits any field above is **incomplete** and is
treated by CROSS-02-03 as `blocked_until_validation` until the missing
field is supplied through a CROSS-02-02 amendment.

---

## §4 Design-time audit dimensions

CROSS-02-03 audits each feature-family row against the following 15
dimensions. Every dimension is binary (PASS / FAIL); a single FAIL routes
the family to `blocked_until_validation` unless an explicit caveat is
declared and accepted (in which case the verdict is `allowed_with_caveat`,
with the caveat recorded in the per-family entry).

### §4.1 Dimension table

| ID | Dimension | Pass condition | Failure routes to |
|----|-----------|----------------|-------------------|
| **D1** | Prediction setting admissibility | The declared `prediction_setting` is one of `pre_game`, `history_enriched_pre_game`, `in_game_snapshot`, `blocked_or_deferred`, AND is supported by the dataset (per CROSS-02-02-v1 §3.2: AoE2 sources do not support `in_game_snapshot`). | FAIL → `blocked_until_validation` |
| **D2** | Source classification and temporal availability | Every column referenced in `source_table_or_event_family` has a column-level classification per CROSS-02-00-v3.0.1 §5 (IDENTITY / CONTEXT / PRE_GAME / TARGET / POST_GAME_HISTORICAL / IN_GAME_HISTORICAL / CONDITIONAL_PRE_GAME). The classification is consistent with the declared `prediction_setting`: PRE_GAME columns may enter `pre_game` directly; POST_GAME / IN_GAME / TARGET columns may enter only via history-aggregated / cutoff-snapshot constructions. | FAIL → `blocked_until_validation` (e.g., a TARGET column projected as a `pre_game` feature) |
| **D3** | Source grain vs model grain | The declared `source_grain` is reconcilable with `model_input_grain` through a documented projection: e.g., aoestats `1 row per match with p0_*/p1_*` projects into `match_pair / player_match focal row` via the canonical-slot focal/opponent assignment (CROSS-02-00-v3.0.1 §5.2). No family is allowed to mix one-row-per-match and two-row-per-match semantics in a single modeling matrix without explicit projection. | FAIL → `blocked_until_validation` |
| **D4** | Temporal anchor correctness | `temporal_anchor` matches the per-dataset anchor in CROSS-02-00-v3.0.1 §3.2 for the declared source. For history features against `player_history_all`: `details_timeUTC` (sc2egset), `started_timestamp` (aoestats), `started` (aoe2companion). For target-row references against `matches_history_minimal`: `started_at`. For in-game tracker features: `event.loop`. The cross-dataset alias `started_at` MUST NOT be used as the `player_history_all` anchor. | FAIL → `blocked_until_validation` |
| **D5** | Cutoff operator correctness | For history features, the cutoff rule is `history_time < target_time` strict (operator `<`, not `<=`, `=`, `>=`). For in-game snapshot features, the cutoff rule is `event.loop <= cutoff_loop`. Equality on the history side is forbidden. | FAIL → `blocked_until_validation` |
| **D6** | Target-game exclusion | No feature for game T may read game T's own row in any mode that yields its outcome / final state / ending loop. Target-game rows are excluded from rolling windows; the strict `<` operator (D5) enforces this for history features; for in-game snapshot features, `event.loop <= cutoff_loop` (NOT `<= header_elapsedGameLoops`) enforces exclusion of post-cutoff state. | FAIL → `blocked_until_validation` |
| **D7** | Post-game token exclusion | The family does not read columns classified TARGET / POST_GAME_HISTORICAL / IN_GAME_HISTORICAL of the target match itself. CROSS-02-00-v3.0.1 §5 column classifications are authoritative. IN_GAME_HISTORICAL columns of *prior* matches (filtered strictly `<` target) are admissible only under `history_enriched_pre_game` and only per CROSS-02-00-v3.0.1 §5.4 SC2 telemetry-scope decision. | FAIL → `blocked_until_validation` |
| **D8** | Full-replay aggregate exclusion for in-game snapshots | For `in_game_snapshot` families, no aggregator reads events with `loop > cutoff_loop`. Full-replay `MIN(loop)`, `MAX(loop)`, `COUNT(*)`, or `MEAN(...)` without the `loop <= cutoff_loop` filter is leakage. The CSV's `time_to_first_expansion_loop` row carries this rule explicitly: `full_replay_min_loop_blocked = True`. | FAIL → `blocked_until_validation` |
| **D9** | Normalization / encoder fit-scope | Any scaler, normalizer, encoder, target-encoding statistic, or smoothing prior is declared as fit-on-training-fold-only (per CROSS-02-01-v1.0.1 §2.3). No scikit-learn `fit_transform` may be declared on the pooled dataset before split. K-fold target encoding declares fold-mask discipline. | FAIL → `blocked_until_validation` |
| **D10** | Focal/opponent symmetry and p0/p1 projection | Every per-player feature is computed by the same SQL pattern or function for the focal player and the opponent (Invariant I5). For aoestats, the `p0_*` / `p1_*` source asymmetry is resolved via the `canonical_slot` focal/opponent assignment (CROSS-02-00-v3.0.1 §5.2; aoestats-only column) before any feature computation that depends on player role. RISK-24 routes the operationalization to a Phase 02 ROADMAP step. | FAIL → `blocked_until_validation` (e.g., asymmetric construction; data-dependent slot assignment that correlates with outcome) |
| **D11** | Cold-start handling declared but constants not magic | The family declares one of the cold-start handling categories from §3 above. No numeric constant (pseudocount `m`, threshold `K`, smoothing strength `α`, prior strength) is hard-coded at the CROSS-02-02-v1 / CROSS-02-03-v1 layer; per Invariant I7, every numeric value is data-derived from training-fold statistics or literature-cited and recorded in the per-dataset Phase 02 ROADMAP step that materializes it. | FAIL → `blocked_until_validation` (a magic constant appears without empirical derivation or literature citation) |
| **D12** | Source-mode label handling / stratification vs model input | Source-mode labels (aoestats source label `leaderboard='random_map'`; aoe2companion `internalLeaderboardId` ∈ {6, 18}) are declared as **stratification or sensitivity controls** when they enter modeling, NOT as generic categorical features that alias for a population shortcut. CROSS-02-02-v1 §8.4 is binding. RISK-26 routes SC2 Random race semantics: the focal race for Random-pickers is `Random` at pre-game time; the eventual race is post-decision and is NOT a pre-game feature. | FAIL → `blocked_until_validation` |
| **D13** | SC2 tracker eligibility constraint | Every SC2 `in_game_snapshot` family appears in `tracker_events_feature_eligibility.csv` with `status_in_game_snapshot ∈ {eligible_for_phase02_now, eligible_with_caveat}`. Families with `status_in_game_snapshot = blocked_until_additional_validation` are routed to `blocked_until_validation`. The CSV-row `eligibility_scope` and `caveat` are honored verbatim. `slot_identity_consistency` is `sanity_gate_not_model_input` and is NOT used as a model input. | FAIL → `blocked_until_validation` (or `sanity_gate_not_model_input` for the slot-identity row) |
| **D14** | AoE2 source-label discipline | aoestats is labeled aoestats Tier 4 (source label `leaderboard='random_map'`; queue semantics unverified). aoestats MUST NOT be called unqualified ranked ladder. aoe2companion ID 6 is labeled `rm_1v1` ranked candidate (Tier 2). aoe2companion ID 18 is labeled `qp_rm_1v1` quickplay/matchmaking-derived (Tier 3). The combined ID 6 + ID 18 scope is aoe2companion mixed-mode and is not ranked-only. | FAIL → `blocked_until_validation` (e.g., a feature row uses an unqualified ranked-ladder label for aoestats or for the aoe2companion combined scope) |
| **D15** | Artifact-lineage readiness / anti-GIGO stop condition | The family declaration is consistent with the empirical lineage discipline in `.claude/rules/data-analysis-lineage.md`: it does not assume that a feature value, a notebook output, or a generated artifact already exists for it. It does not pre-commit to artifact generation that bypasses the ROADMAP-stub → notebook-scaffold → validation-module → user-review → commit → artifact-generation sequence. | FAIL → `blocked_until_validation` (e.g., the family description implies that a notebook or an artifact has already been produced) |

### §4.2 Dimension applicability

Some dimensions are inapplicable to specific prediction settings or datasets:

- **D8** (full-replay aggregate exclusion) is applicable only to `in_game_snapshot` families.
- **D13** (SC2 tracker eligibility) is applicable only to sc2egset `in_game_snapshot` families.
- **D14** (AoE2 source-label discipline) is applicable only to aoestats and aoe2companion families.

When a dimension is inapplicable, it is recorded as `N/A` in the audit
verdict; an `N/A` does not count as a FAIL.

---

## §5 Dataset-specific temporal anchor table

The per-dataset temporal anchor mapping is read from CROSS-02-00-v3.0.1
§3.2 (history side) and from the SC2 tracker contract (in-game side):

| Source | Anchor column | Type | Cutoff rule | DuckDB session discipline |
|--------|---------------|------|-------------|---------------------------|
| sc2egset `player_history_all` (history side) | `details_timeUTC` | VARCHAR | `ph.details_timeUTC < target.started_at` (strict) | n/a (string comparison after CAST in I3-guarded SQL) |
| aoestats `player_history_all` (history side) | `started_timestamp` | TIMESTAMPTZ | `ph.started_timestamp < target.started_at` (strict) | **`SET TimeZone = 'UTC'`** required at session start (per CROSS-02-00-v3.0.1 §3.3) |
| aoe2companion `player_history_all` (history side) | `started` | TIMESTAMP | `ph.started < target.started_at` (strict) | n/a |
| `matches_history_minimal` (target side, all three datasets) | `started_at` | TIMESTAMP | n/a (target anchor); `target.started_at` is the right-hand side of the strict-less-than history filter | UTC discipline applies whenever any cross-column comparison involves a TIMESTAMPTZ value |
| sc2egset `tracker_events_raw` (in-game side) | `event.loop` | INTEGER (game loops) | `event.loop <= cutoff_loop` | n/a |

### §5.1 Strict less-than rule for history features

For every feature with `prediction_setting ∈ {pre_game with history aggregation,
history_enriched_pre_game}`, the cutoff rule is `history_time < target_time`
strictly. The equality form (`<=`) is forbidden because a history row at
exactly the same anchor time as the target is not strictly prior history;
admitting it would risk including the target match's own row in the
aggregation window.

The cross-dataset alias `started_at` MUST NOT be used as the
`player_history_all` anchor; it exists only in `matches_history_minimal`.
Writing `WHERE ph.started_at < target.started_at` against `player_history_all`
will produce a column-not-found error on all three datasets per CROSS-02-00
§3.3.

### §5.2 In-game cutoff rule

For every `in_game_snapshot` family, the cutoff rule is
`event.loop <= cutoff_loop`. Game loops are the canonical unit. The seconds
conversion `cutoff_seconds ~ cutoff_loop / 22.4` is contextual and caveated
only — the loops-per-second factor is empirically corroborated at
`gameSpeed='Faster'` but not directly source-confirmed by s2protocol (V1
caveat from PR #208). Phase 02 features that express cutoffs only in seconds,
without a corresponding loop value, fail D5.

### §5.3 Full-replay aggregate exclusion for cutoff snapshots

Aggregators such as `MIN(loop)`, `MAX(loop)`, `COUNT(*)`, `SUM(...)`, or
`MEAN(...)` over events with `loop > cutoff_loop` are forbidden when the
target prediction setting is `in_game_snapshot`. The
`time_to_first_expansion_loop` row in the SC2 tracker CSV makes this rule
explicit: full-replay `MIN(loop)` is blocked even though the cutoff-censored
`MIN(loop) WHERE loop <= cutoff_loop` (paired with a `has_expansion_by_cutoff`
indicator) is admissible.

---

## §6 Prediction-setting rules

### §6.1 `pre_game`

A `pre_game` family reads only static pre-match attributes of game T plus
historical aggregates over games strictly prior to T. Specifically:

- **Allowed:** game-T pre-game attributes (race / civ, opponent race / civ,
  map, patch / version, leaderboard / mode, calendar context); flags that
  are decidable at pre-game time (e.g., `is_mmr_missing`, `is_unrated`);
  rolling/expanding aggregates over `player_history_all` rows filtered by the
  strict history cutoff (D4 / D5).
- **Forbidden:** any game-T tracker event (SC2 tracker-derived families are
  never pre-game; per Amendment 2 of PR #208 / Invariant I3, every row in
  `tracker_events_feature_eligibility.csv` carries
  `status_pre_game = not_applicable_to_pre_game`); any post-game value of game
  T; any target-game final-state column (TARGET / POST_GAME_HISTORICAL /
  IN_GAME_HISTORICAL of the target row); any column whose CROSS-02-00 §5
  classification is incompatible with PRE_GAME admission for the chosen
  setting.

### §6.2 `history_enriched_pre_game`

A `history_enriched_pre_game` family reads only prior records relative to
game T:

- **Allowed:** rolling/expanding aggregates over `player_history_all` rows
  for the focal `player_id` (per dataset's native ID column), the opponent
  `player_id`, or the head-to-head pairing — filtered by
  `history_time < target_time` strictly. IN_GAME_HISTORICAL columns of
  prior matches are admissible per CROSS-02-00-v3.0.1 §5.4 SC2 telemetry-scope
  decision (sc2egset only); their use as direct game-T pre-game features
  remains forbidden (D7).
- **Forbidden:** any aggregation window that includes the target match's
  own row (D5); any post-game rating delta of game T (e.g., aoestats
  `new_rating`); any column that appears in the target match's row at the
  prediction time but is classified as POST_GAME_HISTORICAL.

### §6.3 `in_game_snapshot`

An `in_game_snapshot` family reads events at or before a chosen cutoff loop
within game T. This setting is **SC2-only** in current thesis data:

- **Allowed (SC2):** rows of `tracker_events_feature_eligibility.csv` with
  `status_in_game_snapshot ∈ {eligible_for_phase02_now, eligible_with_caveat}`;
  cutoff rule `event.loop <= cutoff_loop`; per-row `eligibility_scope` and
  `caveat` honored verbatim.
- **Forbidden (SC2):** rows with
  `status_in_game_snapshot = blocked_until_additional_validation`; any
  full-replay aggregate (D8); any feature that reads the `Upgrade.count`
  field as a cumulative tally (the field is empirically always ~1 but its
  semantics are not source-confirmed; `COUNT(*)` is the canonical
  alternative).
- **Forbidden (AoE2):** AoE2 sources do not support `in_game_snapshot` —
  aoestats and aoe2companion records carry no in-game replay telemetry in
  current thesis data. The `opening` + age-uptime columns are not present
  (aoe2companion) or are pre-2024-03-10-only and classified out-of-scope
  (aoestats).

### §6.4 Cross-setting prohibition

A feature family is declared in **exactly one** prediction setting. Reuse
across settings requires a separate family declaration with its own audit
verdict. In particular, an SC2 tracker-derived family declared in
`in_game_snapshot` may not be silently re-declared as `pre_game` or
`history_enriched_pre_game` even if its values are aggregated forward in
time; **tracker-derived features are never pre-game** (see also §6.1).

---

## §7 SC2 tracker constraints

### §7.1 Binding to the tracker eligibility CSV

Every SC2 `in_game_snapshot` feature family MUST trace to a row in
`src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`
(15 rows; per-prediction-setting columns per Amendment 2 of PR #208). The
CSV is the authoritative contract; CROSS-02-03 does not re-derive
eligibility.

Only rows with `status_in_game_snapshot ∈ {eligible_for_phase02_now,
eligible_with_caveat}` may be considered as Phase 02 candidates (12 of 15
rows). The remaining 3 rows are `blocked_until_additional_validation` and
remain outside Phase 02 scope:

- `mind_control_event_count` (UnitOwnerChange) — V4 sparse coverage; V5
  dynamic-ownership blocked.
- `army_centroid_at_cutoff_snapshot` (UnitPositions) — V6 packed-items
  decoder + UnitBorn-lineage owner attribution NOT validated; coordinate
  units / origin not source-confirmed per Amendment 5.
- `playerstats_cumulative_economy_fields` — V3 Q3 strict: s2protocol
  cumulative semantics not source-confirmed for `*Lost` / `*Killed` /
  `*FriendlyFire` / `*Used` keys.

### §7.2 Sanity gate, not model input

`slot_identity_consistency` is classified `eligible_for_phase02_now` in
the CSV but is a feature-engineering sanity gate (per-replay structural
validity check that PlayerSetup playerId / slotId / userId map consistently
to `replay_players_raw`). Its CROSS-02-03 verdict is
`sanity_gate_not_model_input`. It is NOT a model input; its role is to gate
the per-replay validity of every other tracker-derived family.

### §7.3 GATE-14A6

GATE-14A6 outcome: narrowed. The full tracker scope is not closed. Per the
PR #208 §14A.6 POST-VALIDATION UPDATE, `gate_14a6_decision = narrowed`,
`planned_subset_ready_predicate_satisfied = true`, and
`full_tracker_scope_closed_predicate_satisfied = false`. Promotion of a
currently-blocked tracker family to `eligible_*` requires a future
dedicated validation step per `phase02_readiness_hardening.md` §14A.6
future validation route; CROSS-02-03 does not authorize unilateral
promotion.

### §7.4 Loops vs seconds

The cutoff rule is expressed in game loops: `event.loop <= cutoff_loop`. The
seconds conversion `cutoff_seconds ~ cutoff_loop / 22.4` is contextual and
caveated only — the V1 caveat from PR #208 records that the
loops-per-second factor is empirically corroborated at `gameSpeed='Faster'`
but not directly source-confirmed by s2protocol. Features that express
cutoffs only in seconds without a corresponding loop value FAIL D5.

---

## §8 AoE2 source label constraints

### §8.1 aoestats Tier 4

aoestats is **aoestats Tier 4** semantic opacity per
`thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.1.7 / §4.3. The
recommended Phase 02 source label is "aoestats 1v1 Random Map records
(source label `leaderboard='random_map'`; queue semantics unverified
against upstream API documentation; Tier 4)". aoestats MUST NOT be called
unqualified ranked ladder. A feature row that uses an unqualified
ranked-ladder label for aoestats FAILs D14.

### §8.2 aoe2companion ID 6 / ID 18

- **ID 6** (`internalLeaderboardId = 6`, `rm_1v1`): Tier 2 — ranked
  candidate.
- **ID 18** (`internalLeaderboardId = 18`, `qp_rm_1v1`): Tier 3 —
  quickplay/matchmaking-derived per on-disk classification and the T05
  fallback rule (external API unavailable as of 2026-04-26).
- **ID 6 + ID 18 combined**: aoe2companion mixed-mode, not ranked-only.
  Phase 02 prose, label, and stratification fields must preserve the
  ranked vs quickplay/matchmaking distinction.

A feature row that uses an unqualified ranked-ladder label for the
aoe2companion combined scope (ID 6 + ID 18), or that drops the ID-18
quickplay/matchmaking qualifier, FAILs D14.

---

## §9 Design-time audit artifact — future schema only

### §9.1 No artifact in T04

T04 produces this specification document only. **No design-time audit
artifact (JSON / CSV / Markdown) is produced by this T04 step.** No
notebook is created. No generated artifact is created or modified.

### §9.2 Future artifact schema (proposed)

A future Phase 02 step (see CROSS-02-02-v1 §12 proposed sequence) will
operationalize CROSS-02-03 into a machine-readable design-time audit
artifact. The proposed artifact format and field set, **for future
realization only**, is:

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | string | `"CROSS-02-03-v1"` (or the major.minor version active at the time the artifact is produced; patch-level changes do not bump the artifact literal — convention follows CROSS-02-01 §9 amendment-log note) |
| `feature_family_id` | string | Audited family identifier per §3 |
| `dataset` | enum {`sc2egset`, `aoestats`, `aoe2companion`} | Per §3 |
| `prediction_setting` | enum from §3 | Per §3 |
| `source_table_or_event_family` | string | Per §3 |
| `source_grain` | string | Per §3 / CROSS-02-00 §2 |
| `model_input_grain` | string | Per CROSS-02-02-v1 §4.2 |
| `temporal_anchor` | string | Per §5 |
| `cutoff_rule` | string | `history_time < target_time` or `event.loop <= cutoff_loop` or `n/a` |
| `audit_dimensions_passed` | list of dimension IDs | Subset of {D1, …, D15} that returned PASS |
| `caveats` | list of strings | Per-row caveats (e.g., aoestats Tier 4; PlayerStats fixed-point/scaling; loops-per-seconds V1 caveat) |
| `blocking_reason` | string | Populated when `verdict = blocked_until_validation`; cites the failing dimension(s) and the corrective action required |
| `verdict` | enum {`allowed`, `allowed_with_caveat`, `blocked_until_validation`, `sanity_gate_not_model_input`} | Per §10 |
| `reviewer_notes` | string | Free-form notes from the reviewer-deep gate |

### §9.3 Future artifact production

The future audit artifact must itself be produced through the canonical
lineage chain per `.claude/rules/data-analysis-lineage.md`:

1. ROADMAP stub for the audit step.
2. Notebook scaffold + one validation module.
3. Execute and report.
4. User review.
5. Commit checkpoint.
6. Next validation module.
7. Generate the audit artifact only after all validation modules pass.
8. Update research_log / STEP_STATUS / manifest.
9. Reviewer-deep gate.

CROSS-02-03 declares the schema; it does not generate the artifact.

---

## §10 Gate outcomes

### §10.1 Verdicts

CROSS-02-03 produces one of four verdicts per audited feature family:

| Verdict | Meaning | Downstream consequence |
|---------|---------|------------------------|
| `allowed` | All applicable dimensions PASS; no caveats. | Family may proceed to a Phase 02 ROADMAP step that materializes it, subject to subsequent CROSS-02-01-v1.0.1 post-materialization audit. |
| `allowed_with_caveat` | All applicable dimensions PASS, but one or more caveats are recorded (e.g., aoestats Tier 4 source label; PlayerStats fixed-point/scaling for SC2 food/supply features; loops-per-second V1 caveat). | Family may proceed; the caveat is documented in the per-family registry and propagates to the future audit artifact (§9). |
| `blocked_until_validation` | At least one applicable dimension FAILed and no accepted caveat covers it. | Family does NOT proceed; it stays out of Phase 02 scope until a future dedicated validation step lands. |
| `sanity_gate_not_model_input` | Family is structurally valid but is reserved as a feature-engineering sanity gate, not a model input. | Family runs as a per-replay / per-row validity check that gates other families; it never enters the modeling matrix. |

### §10.2 Blocking examples

The following observations route a family directly to
`blocked_until_validation`:

- **Missing grain.** `source_grain` or `model_input_grain` is unset.
- **Missing prediction setting.** `prediction_setting` is unset.
- **Ambiguous temporal anchor.** `temporal_anchor` is unset, references
  the cross-dataset alias `started_at` for `player_history_all` (which
  does not exist on `player_history_all`), or is dataset-incorrect.
- **History feature lacking strict `<`.** A history feature declares
  `<=`, `=`, `>=`, or no cutoff against the per-dataset anchor.
- **SC2 tracker feature absent from CSV.** A claimed sc2egset
  `in_game_snapshot` family does not appear in
  `tracker_events_feature_eligibility.csv`, OR appears only with
  `status_in_game_snapshot = blocked_until_additional_validation`.
- **AoE2 source-label regression.** A feature row uses an unqualified
  ranked-ladder label for aoestats (Tier 4), or drops the ID-18
  quickplay/matchmaking qualifier from the aoe2companion combined scope
  (mixed-mode), or asserts that ID 6 + ID 18 is ranked-only.
- **Pseudocount / smoothing constant without empirical derivation.** A
  numeric pseudocount `m`, threshold `K`, smoothing strength `α`, prior
  strength, or imputation constant is hard-coded without a fold-aware
  empirical derivation procedure or a literature citation.
- **Feature table generation attempted before audit.** The family
  declaration assumes that a feature table, a notebook output, or a
  generated artifact already exists for it; or the declaration would
  imply batching ROADMAP, notebook, artifact, and next-step in one
  empirical execution.

### §10.3 Tracker-derived family special case

A family declared on an SC2 tracker event MUST NOT carry
`prediction_setting = pre_game` or `history_enriched_pre_game`; tracker-derived
features are never pre-game (Amendment 2 of PR #208 / Invariant I3). Such a
declaration FAILs D1 and D6 simultaneously and is routed to
`blocked_until_validation`.

---

## §11 Relationship to T05 cross-spec consistency pass

T05 (cross-spec consistency pass; per the active Phase 02 readiness plan)
must verify that the new docs introduced in this PR — including
CROSS-02-03-v1 — are internally consistent and do not contradict the
locked sibling specs or the Phase 02 evidence chain. T05 must verify:

- **No contradiction with CROSS-02-00-v3.0.1.** Per-dataset I3 anchors
  match §5; column classifications referenced match CROSS-02-00 §5;
  cross-game encoding protocol references match CROSS-02-00 §4.
- **No contradiction with CROSS-02-01-v1.0.1.** CROSS-02-03 does not
  weaken, replace, or amend the post-materialization audit gate;
  CROSS-02-01-v1.0.1 §3 / §5 remain binding.
- **No contradiction with CROSS-02-02-v1.** Feature families audited by
  CROSS-02-03 are exactly the rows declared by CROSS-02-02-v1 §6 / §7 / §8;
  prediction settings, grains, and per-dataset anchors line up.
- **No ranked-ladder regression for AoE2.** No new doc calls aoestats
  unqualified ranked ladder; no new doc calls the aoe2companion combined
  scope ranked-only.
- **No tracker pre-game regression.** No new doc declares an SC2
  tracker-derived family in `pre_game` or `history_enriched_pre_game`.
- **No regression that asserts the full tracker scope is closed.** GATE-14A6
  outcome remains `narrowed`; the full tracker scope is not closed.
- **No notebook / artifact / status / ROADMAP changes.** T05 confirms via
  `git diff master..HEAD --name-only` that this PR touches only
  documentation / specification / rule files; no notebooks, generated
  artifacts, raw data, ROADMAPs, research_logs, status YAMLs, or thesis
  chapter prose are modified.

T05 produces no generated artifact; its output is a textual consistency
report routed to T06 reviewer-deep gate.

---

## §12 Validation, sanity, falsifier, and lineage (T04)

### §12.1 Sanity (textual / mechanical)

CROSS-02-03 carries the following mandatory phrases verbatim:

- `history_time < target_time`
- `event.loop <= cutoff_loop`
- `tracker-derived features are never pre-game`
- `GATE-14A6 outcome: narrowed`
- `full tracker scope is not closed`
- `aoestats Tier 4`
- `aoe2companion mixed-mode`
- `does not replace CROSS-02-01-v1.0.1`

The 15-dimension audit table (§4.1) declares D1–D15 with PASS conditions
and failure routes. The dataset-specific temporal anchor table (§5) is
read from CROSS-02-00-v3.0.1 §3.2. The SC2 tracker constraint (§7) is read
from `tracker_events_feature_eligibility.csv`. The AoE2 source-label
constraint (§8) is read from
`thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.3.

### §12.2 Falsifier

The following observations halt CROSS-02-03 (i.e., the spec must be
revised or the offending step must be blocked):

- any wording implies that this T04 step generated feature values, model
  outputs, or any new on-disk feature data;
- any wording implies that this T04 step created a notebook;
- any wording implies that this T04 step modified or generated an artifact
  through the canonical Phase 02 lineage chain (this T04 step produces a
  specification document only);
- any wording implies that this T04 step edited a dataset ROADMAP, a
  research_log, a STEP_STATUS / PIPELINE_SECTION_STATUS / PHASE_STATUS yaml,
  a generated artifact, or thesis chapter prose;
- any statement asserts that CROSS-02-03 replaces, supersedes, or weakens
  CROSS-02-01-v1.0.1; CROSS-02-03 complements but does not replace the
  locked post-materialization audit gate;
- any sc2egset tracker-derived family is allowed in `pre_game` or
  `history_enriched_pre_game` (Invariant I3 violation; Amendment 2 of
  PR #208 violation);
- any AoE2 source is called unqualified ranked ladder, or the aoe2companion
  combined scope is asserted as ranked-only.

### §12.3 Artifact validation

CROSS-02-03 produced no generated artifact and modified no generated
artifact. The only output of this T04 step is the file
`reports/specs/02_03_temporal_feature_audit_protocol.md` itself. Status
YAML files, research logs, ROADMAPs, notebooks, and feature tables are
unchanged.

### §12.4 Lineage

Input files read by CROSS-02-03 (no modification):

- `.claude/rules/data-analysis-lineage.md`
- `.claude/scientific-invariants.md`
- `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v3.0.1)
- `reports/specs/02_01_leakage_audit_protocol.md` (CROSS-02-01-v1.0.1)
- `reports/specs/02_02_feature_engineering_plan.md` (CROSS-02-02-v1)
- `thesis/pass2_evidence/phase01_closeout_summary.md`
- `thesis/pass2_evidence/phase02_readiness_hardening.md`
- `thesis/pass2_evidence/methodology_risk_register.md`
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`

Output file created by CROSS-02-03 (this file):

- `reports/specs/02_03_temporal_feature_audit_protocol.md`

No other on-disk file is touched by this T04 step.

---

## §13 Spec change protocol

Version strings follow the cross-dataset spec pattern `CROSS-02-03-vN.M.K`:

- **vN+1 (major):** changes to §4 audit dimensions, §5 anchor table, §6
  prediction-setting rules, or §10 verdicts; or any change that
  contradicts CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1, or CROSS-02-02-v1.
  Requires full `planner-science` + reviewer-adversarial gate.
- **vN.M+1 (minor):** additions to §4 dimensions, §9 future artifact
  schema fields, §10 blocking examples, §11 cross-spec consistency
  obligations. Requires `planner-science` + `reviewer-deep` gate.
- **vN.M.K+1 (patch):** prose clarifications, typo corrections,
  references, status transitions (DRAFT → LOCKED) — provided no table
  cell values change. May be reviewed by the standard `reviewer` only.

The DRAFT → LOCKED transition is itself a patch under the rules above.
It fires after the reviewer-deep gate prescribed by the active Phase 02
readiness plan returns PASS or PASS-WITH-NOTES.

Per CROSS-02-01-v1.0.1 §9 amendment-log convention, the JSON-schema
`spec_version` literal in any future audit artifact records the spec
major.minor (NOT patch) revision; patch versions do not change artifact
literal values to avoid invalidating `confirmed_intact` lineage of
pre-existing audit artifacts.

---

## §14 Referenced artifacts

### §14.1 Sibling specs (binding)

- `reports/specs/02_00_feature_input_contract.md` — **CROSS-02-00-v3.0.1**,
  LOCKED 2026-04-26. Authoritative input contract.
- `reports/specs/02_01_leakage_audit_protocol.md` — **CROSS-02-01-v1.0.1**,
  LOCKED 2026-04-26. Authoritative post-materialization / pre-training
  leakage audit gate. CROSS-02-03 does not replace CROSS-02-01-v1.0.1.
- `reports/specs/02_02_feature_engineering_plan.md` — **CROSS-02-02-v1**,
  DRAFT 2026-05-05. Feature-engineering plan; CROSS-02-03 audits the rows
  declared by CROSS-02-02-v1 §6 / §7 / §8.

### §14.2 Phase 02 readiness evidence

- `thesis/pass2_evidence/phase01_closeout_summary.md` — Phase 01 → Phase 02
  entry conditions; AoE2 source-specific labels; GATE-14A6 outcome:
  narrowed.
- `thesis/pass2_evidence/phase02_readiness_hardening.md` — T16 14A.6
  POST-VALIDATION UPDATE; future tracker validation route.
- `thesis/pass2_evidence/methodology_risk_register.md` — RISK-20, RISK-21
  (MITIGATED-NARROWED post-PR #208), RISK-24, RISK-25, RISK-26.
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` — four-tier AoE2
  ladder governance.
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` — five-axis
  bounded comparability framing.

### §14.3 Authoritative SC2 tracker contract

- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`
  — 15 rows, per-prediction-setting columns per Amendment 2 of PR #208.
  Read-only for CROSS-02-03; modifications require a separate dedicated
  step in the sc2egset dataset ROADMAP.

### §14.4 Methodology

- `.claude/rules/data-analysis-lineage.md` — anti-GIGO workflow rule.
- `.claude/scientific-invariants.md` — invariants I3 (temporal), I5
  (symmetry), I6 (verbatim SQL evidence), I7 (no magic numbers), I8
  (cross-game comparability), I9 (source-stratified evaluation), I10
  (filename relative paths).
- `docs/PHASES.md` — canonical Phase 02 Pipeline Section enumeration.
- `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` — Phase 02
  methodology source.

---

## §15 Amendment log

| Version | Date | Author | Classification | Summary |
|---------|------|--------|----------------|---------|
| CROSS-02-03-v1 (DRAFT) | 2026-05-05 | T04 executor (claude-opus-4-7) on branch `phase02/feature-engineering-readiness` | Initial DRAFT | Initial draft. Defines the design-time temporal feature audit protocol: audit object, 15 audit dimensions (D1–D15), per-dataset temporal anchor table, prediction-setting rules, SC2 tracker constraints, AoE2 source-label constraints, future audit artifact schema, gate outcomes, and relationship to T05 cross-spec consistency pass. **DRAFT / PR-local until reviewed**: spec becomes binding only after reviewer-deep gate per the active Phase 02 readiness plan returns PASS or PASS-WITH-NOTES. **Does not replace CROSS-02-01-v1.0.1**; complements the locked post-materialization audit gate. Does not modify CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1, or CROSS-02-02-v1. |
| CROSS-02-03-v1.0.1 (LOCKED) | 2026-05-06 | T01 executor on branch `docs/phase02-contracts-lock-and-planning-cleanup` | Patch (status transition) per §13 | DRAFT → LOCKED via §13 patch lane after reviewer-deep PASS-WITH-NOTES on PR #209 (0 unresolved BLOCKERs); PR #209 merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` on 2026-05-05T21:00:02Z. No table cell values changed in §4 / §5 / §6 / §7 / §8 / §9 / §10 / §11 / §12; no audit dimension D1–D15 semantics changed. Frontmatter `version` and `status` bumped, body title and §1 hedge sentence collapsed to LOCKED, §14.1 sibling pointer for CROSS-02-02 updated to v1.0.1 / LOCKED. Sibling cross-dataset Phase 02 triplet now binding (CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1, CROSS-02-03-v1.0.1). Complementary to CROSS-02-01-v1.0.1's post-materialization audit gate; does not replace it. Validator and `02_04_cross_spec_consistency_report.{json,md}` unchanged in this commit. |
