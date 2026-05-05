---
spec_id: CROSS-02-02-v1
version: CROSS-02-02-v1
status: DRAFT
date: 2026-05-05
invariants_touched: [I3, I5, I6, I7, I8, I9, I10]
datasets_bound: [sc2egset, aoestats, aoe2companion]
sibling_specs: [CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1]
supersedes: null
---

# Cross-Dataset Phase 02 Feature-Engineering Plan

## CROSS-02-02-v1 (DRAFT / PR-local until reviewed, 2026-05-05)

This document is the cross-dataset Phase 02 feature-engineering plan. It defines
the per-family feature contract — prediction settings, grains, source labels,
temporal anchors, leakage falsifiers, cold-start gates, and proposed Phase 02
section-level steps — before any feature-generation notebook or table is
authored.

This is a planning/specification artifact only. It is **DRAFT / PR-local until
reviewed**: the spec becomes binding only after the reviewer-deep gate prescribed
by the active Phase 02 readiness plan returns PASS or PASS-WITH-NOTES. Until
then, no Phase 02 ROADMAP, notebook, or generated artifact may consume this
document as authoritative; CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1 remain the
sole binding cross-dataset Phase 02 contracts.

---

## §1 Scope and authority

### §1.1 What this spec is

CROSS-02-02 is the **design-time feature-engineering plan**: it enumerates the
candidate feature families per dataset and prediction setting, declares each
family's grain and temporal anchor, and lists the leakage and cold-start gates
that future feature-generation steps must satisfy. It is the bridge between the
locked Phase 02 input contract (CROSS-02-00-v3.0.1) and the locked pre-training
leakage audit (CROSS-02-01-v1.0.1) on one side, and the as-yet-unwritten Phase
02 ROADMAP entries on the other.

### §1.2 What this spec is not

This spec is **not** a feature catalog, a feature table, a notebook, or a
training pipeline. The following operations are explicitly out of scope for
this T03 step and for the spec it produces:

- no feature table generation;
- no notebooks;
- no model training;
- no thesis chapter prose;
- no raw data edits;
- no generated artifact edits;
- no ROADMAP/status updates in this T03 step.

Feature generation, materialization, encoders, splits, baselines, rating
reconstruction, calibration, and any operation that produces a new on-disk
feature value remain blocked behind future steps that themselves require a
ROADMAP entry, a reviewed scaffold notebook, validation modules, sanity checks,
and reviewer gates per `.claude/rules/data-analysis-lineage.md`.

### §1.3 Non-supersession clause

CROSS-02-02 **does not supersede or amend** the locked sibling specs. In
particular:

- `reports/specs/02_00_feature_input_contract.md` (**CROSS-02-00-v3.0.1**) remains
  the locked input contract baseline. CROSS-02-02 consumes its column-grain
  commitments (§2), join keys and per-dataset I3 anchors (§3), the cross-game
  categorical encoding protocol (§4), and the column-level classification
  (§5). When CROSS-02-02 names a column, the canonical type, classification,
  and dataset-specific anchor are read from CROSS-02-00-v3.0.1, not redefined
  here.
- `reports/specs/02_01_leakage_audit_protocol.md` (**CROSS-02-01-v1.0.1**) remains
  the locked pre-training leakage audit baseline. CROSS-02-02 design-time
  falsifiers do **not** replace the post-materialization audit gate prescribed
  by CROSS-02-01-v1.0.1 §3 / §5. Any future feature-generation step still
  requires the CROSS-02-01 audit artifact (`leakage_audit_<dataset>.json`
  + `.md`) before its consuming Pipeline Section may exit.

A future companion spec, `reports/specs/02_03_temporal_feature_audit_protocol.md`
(CROSS-02-03-v1), will later define design-time temporal feature audit
families. That spec is **not created by this T03 step**; it is reserved for a
later task in the active Phase 02 readiness plan and must complement, not
replace, CROSS-02-01-v1.0.1.

---

## §2 Lineage and consumed evidence

CROSS-02-02 reads, but does not modify, the following evidence:

| Source | Role |
|--------|------|
| `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v3.0.1) | Locked input contract — VIEW names, column grains, I3 per-dataset anchors, cross-game encoding protocol |
| `reports/specs/02_01_leakage_audit_protocol.md` (CROSS-02-01-v1.0.1) | Locked pre-training leakage audit protocol — verified after materialization |
| `thesis/pass2_evidence/phase01_closeout_summary.md` | Phase 01 → Phase 02 entry conditions; AoE2 source-specific labels; GATE-14A6 outcome |
| `thesis/pass2_evidence/phase02_readiness_hardening.md` | T16 14A.6 POST-VALIDATION UPDATE; future tracker validation route |
| `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` | Four-tier AoE2 ladder governance (T05) |
| `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` | Five-axis bounded comparability framing (T09) |
| `thesis/pass2_evidence/methodology_risk_register.md` | RISK-20 (cross-region fragmentation), RISK-21 (tracker semantics), RISK-24/25/26 |
| `thesis/pass2_evidence/notebook_regeneration_manifest.md` | Authoritative stale/current status of generated artifacts |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv` | Authoritative SC2 tracker-derived feature eligibility contract (15 rows; per-prediction-setting columns per Amendment 2 of PR #208) |
| `.claude/rules/data-analysis-lineage.md` | Anti-GIGO workflow rule binding all empirical Phase 02 steps |
| `.claude/scientific-invariants.md` | Invariants I3/I5/I6/I7/I8/I9/I10 referenced throughout |

The `tracker_events_feature_eligibility.csv` file is read in §11 below; the row
counts and family classifications cited there are derived from the CSV itself,
not from memory.

---

## §3 Prediction settings

CROSS-02-02 commits to three Phase 02 prediction settings plus an explicit
reservation for blocked / deferred families. The settings are mutually
exclusive at the feature-family level: a feature family is declared in exactly
one setting, and any cross-setting reuse requires a separate family declaration.

### §3.1 Setting definitions

| Setting | Definition | Information available at prediction time | Allowed cutoff rule |
|---------|------------|------------------------------------------|---------------------|
| `pre_game` | Prediction made before game T starts. Only static / pre-match attributes of game T plus historical aggregates over games strictly prior to T. | Game T's pre-game attributes (race/civ, map, opponent race/civ, patch/version, leaderboard/mode, calendar context); attributes of game T are NOT history. | History features must obey `history_time < target_time` (per CROSS-02-00-v3.0.1 §3.3 strict less-than rule); no game-T post-outcome value, in-game value, or final-state value may enter. |
| `history_enriched_pre_game` | A `pre_game` setting in which the focal feature is derived from a rolling/expanding aggregate over the player's (or opponent's, or matchup's) prior history. The cutoff rule is identical to `pre_game`. | Same as `pre_game`, plus rolling-window aggregates (counts, means, EWMAs, Bayesian-smoothed rates, reconstructed ratings). | `history_time < target_time` strict; cold-start gates per §9 declared per family. |
| `in_game_snapshot` | Prediction made at a chosen in-game cutoff loop within game T using only events at or before that cutoff. | All `pre_game` and `history_enriched_pre_game` features, PLUS event-derived state at or before the cutoff loop within game T. | `event.loop <= cutoff_loop` (game loops are the canonical unit; the seconds conversion `cutoff_seconds ~ cutoff_loop / 22.4` is contextual and carries the V1 caveat that the loops-per-second factor is empirically corroborated at `gameSpeed='Faster'` but not directly source-confirmed by s2protocol). |
| `blocked_or_deferred` | Reserved for candidate feature families that cannot enter any of the three settings without a future dedicated validation step. | N/A | N/A |

### §3.2 Per-dataset support matrix

| Dataset | `pre_game` | `history_enriched_pre_game` | `in_game_snapshot` | Notes |
|---------|------------|----------------------------|--------------------|------|
| sc2egset | supported | supported | supported (constrained by §11) | SC2 supports all three settings. The `in_game_snapshot` setting is gated by `tracker_events_feature_eligibility.csv` (15-row contract). |
| aoestats | supported | supported | **not supported** | aoestats records carry no in-game replay telemetry; `in_game_snapshot` is structurally unavailable. |
| aoe2companion | supported | supported | **not supported** | aoe2companion records carry no in-game replay telemetry; `in_game_snapshot` is structurally unavailable. |

**Tracker-derived constraint.** SC2 tracker-derived features are never pre-game (Amendment 2 of PR #208 / Invariant I3). Every row in `tracker_events_feature_eligibility.csv` carries `status_pre_game = not_applicable_to_pre_game`. CROSS-02-02 enforces this: no SC2 tracker-derived feature family may be declared in `pre_game` or `history_enriched_pre_game`; tracker-derived families enter Phase 02 only via `in_game_snapshot`, and only under each row's recorded `eligibility_scope` and `caveat`.

**AoE2 in-game telemetry.** AoE2 has no in-game replay telemetry in current
thesis data. The `opening` + age-uptime columns are not present (aoe2companion)
or are pre-2024-03-10-only and classified out-of-scope (aoestats). Phase 02
must not introduce an `in_game_snapshot` setting for either AoE2 source.

---

## §4 Feature table grains

Every feature family declared in §6–§8 must commit a source grain and a planned
model-input grain. CROSS-02-00-v3.0.1 §2 commits the per-dataset row grains for
the input VIEWs; CROSS-02-02 specifies how those input grains map to feature
rows for modeling.

### §4.1 Source grains (from CROSS-02-00-v3.0.1 §2)

| Dataset | `matches_history_minimal` row grain | `player_history_all` row grain |
|---------|------------------------------------|-------------------------------|
| sc2egset | 2 rows per match (one per player) | 1 row per player per match (all game types; no 1v1 filter) |
| aoestats | 2 rows per match (one per player) — note `canonical_slot` is aoestats-only and NOT in cross-dataset UNION ALL | 1 row per player per match (all leaderboards; no 1v1 filter) |
| aoe2companion | 2 rows per match (one per player) | 1 row per player per match (all leaderboards; no 1v1 filter) |

Note that aoestats' upstream `matches_raw` is one-row-per-match with
`p0_*` / `p1_*` columns; the `matches_history_minimal` VIEW projects this into
the cross-dataset 2-row-per-match focal/opponent shape via a UNION ALL with
canonical-slot-aware `(focal, opponent)` assignment (CROSS-02-00-v3.0.1 §5.2).

### §4.2 Planned model-input grains

| Grain | Definition | Used for |
|-------|------------|----------|
| `match_pair / player_match focal row` | One row per `(dataset_tag, match_id, focal_player_id, opponent_player_id, prediction_setting)`. The focal/opponent assignment is canonical and must be applied identically across datasets. | All `pre_game` and `history_enriched_pre_game` candidate features for sc2egset and aoe2companion; the post-projection grain for aoestats. |
| `match row with p0/p1 source columns` | One row per `(dataset_tag, match_id)` with `p0_*` / `p1_*` columns at source. For modeling, this **must be projected** into the focal/opponent grain before any encoder, scaler, or model consumes it. | aoestats source grain only — symmetric focal/opponent projection is a binding pre-modeling step (Invariant I5 symmetry). The unprojected p0/p1 row grain is a transport grain, not a modeling grain. |
| `in_game_snapshot candidate grain` | One row per `(dataset_tag, match_id, focal_player_id, opponent_player_id, cutoff_loop)`. Multiple cutoff loops per match are permitted; they must be enumerated explicitly, not implied. | sc2egset only; aoestats and aoe2companion are excluded by §3.2. |
| `target grain` | One row per `(dataset_tag, match_id, focal_player_id)` carrying the target label `won::BOOLEAN` from CROSS-02-00-v3.0.1 §5.1–§5.3. The target is read from `matches_history_minimal.won`; for aoestats it is the projected `won` after focal/opponent assignment. | All three datasets. |

### §4.3 Mixing rule

No Phase 02 step may consume a one-row-per-match aoestats grain alongside a
two-row-per-match sc2egset / aoe2companion grain in the same modeling matrix
without explicit symmetric focal/opponent projection. Stacking p0/p1 columns
horizontally with focal/opponent rows is an Invariant I5 symmetry violation
and is forbidden.

The future final feature-catalog grain (one row per materialized feature
column with provenance) belongs to a later Phase 02 section (per CROSS-02-00
§6 row 02_08) and is not committed here.

---

## §5 Cross-dataset commitments

The following commitments apply across all three datasets:

1. **Focal/opponent symmetry (Invariant I5).** Every per-player feature must
   be computed with the same function or SQL pattern for the focal player and
   the opponent. The output column name must be prefixed `focal_*` or
   `opponent_*` (or carry an explicit role column). For aoestats, the `p0_*`
   / `p1_*` source asymmetry must be resolved into focal/opponent before any
   feature computation that depends on player role.
2. **Cross-game categorical encoding (Invariant I8 / CROSS-02-00 §4).** Any
   per-dataset polymorphic vocabulary (race / civ, map, leaderboard) must be
   encoded within a `dataset_tag` partition. No encoder, target-encoder, or
   smoothing prior may be fit on rows from more than one dataset.
3. **Strict temporal cutoff (Invariant I3 / CROSS-02-00 §3.3).** All
   history-derived features must satisfy `history_time < target_time` strictly;
   the equality form is forbidden. The per-dataset anchor column comes from
   CROSS-02-00 §3.2 (`details_timeUTC` for sc2egset, `started_timestamp` for
   aoestats, `started` for aoe2companion).
4. **DuckDB UTC discipline (CROSS-02-00 §3.3).** Any DuckDB session that
   compares `TIMESTAMPTZ` values (e.g., aoestats `started_timestamp`) MUST
   issue `con.execute("SET TimeZone = 'UTC'")` at the start of the notebook
   or script.
5. **Generated artifact discipline (`.claude/rules/data-analysis-lineage.md`).**
   No feature family may be materialized until the upstream notebook scaffold
   has been reviewed, the validation modules have run, the falsifier has not
   fired, and the user has approved a checkpoint commit.
6. **Filename relative paths (Invariant I10).** Any `*_raw` table or feature
   table that records source filenames must store them relative to the
   dataset's `raw_dir`; absolute paths are forbidden.

---

## §6 SC2EGSet feature families

### §6.1 sc2egset `pre_game` candidate families

| Feature family | Source table / column | Grain | Temporal anchor | Allowed cutoff rule | Constraint / caveat |
|----------------|----------------------|-------|-----------------|---------------------|---------------------|
| `focal_race` / `opponent_race` | `matches_history_minimal.faction` (4-char race stems Prot / Terr / Zerg / Rand); cross-checked against `player_history_all.race` / `selectedRace` | match_pair focal row | `started_at` (CROSS-02-00 §5.1) | none (game-T attribute) | Encoded within `dataset_tag = 'sc2egset'` per Invariant I8. `Random` is a fourth declared race at pre-game; the eventual played race is post-decision and is NOT a pre-game feature for the 555 Random replays. |
| `matchup` (race × opponent_race) | derived from `focal_race` / `opponent_race` | match_pair focal row | `started_at` | none | Encoded within `dataset_tag = 'sc2egset'`; vocabulary disjoint from AoE2 civ matchup. |
| `map` | `player_history_all.metadata_mapName` (joined to focal row by `match_id` and `player_id`) | match_pair focal row | `started_at` | none | 188 distinct map names in sc2egset; encoder fit per `dataset_tag` partition. |
| `patch` / `version` | `player_history_all` patch/version columns (sc2egset specific; see CROSS-02-00 §5.4) | match_pair focal row | `started_at` | none | 46 distinct `gameVersion` values; PSI quarterly drift documented in 01_05_02. |
| `is_mmr_missing` (PRE_GAME flag) | `player_history_all.is_mmr_missing` (CROSS-02-00 §5.4) | match_pair focal row | `started_at` | none | **Use the missingness flag, not the MMR scalar.** MMR is structurally absent for 83.95% of rows (unrated professional / sentinel=0); the raw scalar is not a defensible naive skill feature for this professional corpus. Rating proxies must come from `history_enriched_pre_game` (§6.2). |

**Out of scope here:** any feature derived from final-state, post-game,
or in-game telemetry columns. These belong to `in_game_snapshot` (§6.3) or
remain blocked.

### §6.2 sc2egset `history_enriched_pre_game` candidate families

| Feature family | Source | Grain | Temporal anchor | Allowed cutoff rule | Constraint / caveat |
|----------------|--------|-------|-----------------|---------------------|---------------------|
| `focal_player_history` | rolling/expanding aggregates over `player_history_all` rows for the focal `toon_id`: prior match count, prior win rate, time since prior match, race-conditional win rate, map-conditional win rate, matchup-conditional win rate | match_pair focal row | `details_timeUTC` from `player_history_all` (per CROSS-02-00 §3.2) | `history_time < target_time` (strict) using the per-dataset anchor `ph.details_timeUTC < target.started_at` | Cold-start gate per §9. The `is_decisive_result` filter and `result` interpretation come from CROSS-02-00 §5.4. |
| `opponent_player_history` | symmetric mirror of `focal_player_history` for the opponent `toon_id` | match_pair focal row | `details_timeUTC` | `history_time < target_time` (strict) | Symmetric (Invariant I5): same SQL pattern as focal. |
| `matchup_history_aggregate` | head-to-head and matchup-conditional history aggregates (focal vs opponent across all prior games) | match_pair focal row | `details_timeUTC` | `history_time < target_time` (strict); same-match leakage forbidden | Cold-start gate per §9. Head-to-head pair counts are sparse for most professional pairings; smoothing rules in §9 apply. |
| `reconstructed_rating` (Glicko-2 or analogous) | derived from `player_history_all.result` filtered by I3 anchor | match_pair focal row | `details_timeUTC` | `history_time < target_time` (strict); rating state computed strictly from prior decisive results | **Only if temporally disciplined.** No global / batch fit; ratings must be reconstructed forward in time. Battle.net MMR is not used as the rating source for this corpus because it is structurally absent for 83.95% of rows; the reconstructed rating is the principled substitute. |
| `cross_region_fragmentation_handling` | `player_history_all.is_cross_region_fragmented` (CROSS-02-00 §5.4) | match_pair focal row | `started_at` | n/a (CONTEXT flag) | **Gated and sensitivity-aware.** Per RISK-20 / Phase 01 W=30 FAIL verdict, Phase 02 must not hard-code a retention percentage for `WHERE NOT is_cross_region_fragmented` filtering. Phase 02 must implement one of: (a) strict-exclusion sensitivity arm, (b) dual feature paths (with vs without filter), or (c) sensitivity indicator co-registered alongside the history features. The choice is deferred to a Phase 02 ROADMAP step that empirically measures retention. |
| `in_game_history_aggregate` (rolling APM / SQ / supplyCappedPercent / header_elapsedGameLoops over prior matches) | `player_history_all.APM` / `SQ` / `supplyCappedPercent` / `header_elapsedGameLoops` (IN_GAME_HISTORICAL classification per CROSS-02-00 §5.4) | match_pair focal row | `details_timeUTC` | `history_time < target_time` (strict) — these columns are safe **only** as history aggregates filtered strictly less than T | Per CROSS-02-00 §5.4 SC2 in-game telemetry scope decision: IN_GAME_HISTORICAL columns are RETAINED IN SCOPE for `history_enriched_pre_game` use; they remain forbidden as direct game-T pre-game features (which would be an Invariant I3 violation). |

### §6.3 sc2egset `in_game_snapshot` candidate families

The sc2egset `in_game_snapshot` setting is **fully constrained by**
`tracker_events_feature_eligibility.csv` (15 rows; per-prediction-setting
columns per Amendment 2 of PR #208). The §11 table summarizes the contract.
The eligibility classifications below derive from that CSV; CROSS-02-02 does
not re-derive eligibility.

Allowed planned families for sc2egset `in_game_snapshot` are exactly the rows
classified `eligible_for_phase02_now` or `eligible_with_caveat` in the CSV.
Each consumed family is bound by its row's `eligibility_scope` and `caveat`.
The cutoff rule for every tracker-derived family is `event.loop <= cutoff_loop`
(game loops are canonical; the seconds conversion `cutoff_seconds ~
cutoff_loop / 22.4` is contextual and caveated only).

**Sanity gate, not model input.** `slot_identity_consistency` is classified
`eligible_for_phase02_now` in the CSV but is a feature-engineering sanity gate
(structural validity check that PlayerSetup playerId/slotId/userId map
consistently to `replay_players_raw`). It MUST NOT be used as a model input;
its role is to gate the per-replay validity of every other tracker-derived
family.

**Blocked families remain excluded.** The three `blocked_until_additional_validation`
rows MUST NOT be declared as Phase 02 candidate families:

- `mind_control_event_count` (UnitOwnerChange) — V4 sparse coverage (absent in
  2016, present in ~25% of replays in 8 of 9 years); V5 dynamic-ownership
  blocked.
- `army_centroid_at_cutoff_snapshot` (UnitPositions) — V6 packed-items decoder
  + UnitBorn-lineage owner attribution NOT validated; coordinate units / origin
  not source-confirmed per Amendment 5.
- `playerstats_cumulative_economy_fields` — V3 Q3 strict: s2protocol cumulative
  semantics not source-confirmed for `*Lost` / `*Killed` / `*FriendlyFire` /
  `*Used` keys.

These remain `blocked_until_additional_validation` until a future dedicated
validation step lands. CROSS-02-02 does not authorize their use under any
caveat.

**Family-specific rules** drawn directly from the CSV's `caveat` and
`notes_for_phase02` columns:

| Family | Rule |
|--------|------|
| `count_units_built_by_cutoff_loop`, `count_units_killed_by_cutoff_loop`, `morph_count_by_cutoff_loop`, `building_construction_count_by_cutoff_loop` | Basic cutoff-counts; owner via UnitBorn/UnitInit lineage; exclude InvisibleTargetDummy and other engine entities at feature level (per CSV `notes_for_phase02`). |
| `count_units_lost_by_cutoff_loop` | Lineage-attributed (UnitDied → UnitBorn); orphan deaths (~0.000037%) excluded from per-player counts. |
| `count_upgrades_by_cutoff_loop` | **Use `COUNT(*)` per `(filename, playerId)`.** The `Upgrade.count` field is empirically always ~1 but its semantics are not source-confirmed; it MUST NOT be trusted as a cumulative tally. |
| `time_to_first_expansion_loop` | **Cutoff-censored only:** `MIN(loop)` over UnitBorn rows for expansion units (Hatchery / CommandCenter / Nexus) per `(filename, controlPlayerId)` with `loop <= cutoff_loop`, PLUS a `has_expansion_by_cutoff` indicator. The full-replay `MIN(loop)` interpretation is post-cutoff target leakage and is blocked. |
| `supply_used_at_cutoff_snapshot`, `food_used_max_history` | **PlayerStats fixed-point / scaling caveat.** `scoreValueFoodUsed` carries the s2protocol divide-by-4096 convention; the SC2EGSet decoded scaling is NOT source-confirmed. Phase 02 MUST resolve the SC2EGSet decoder convention (divide-by-4096 vs pre-scaled per s2protocol README) before consuming food / supply features. Until resolved, these families remain caveated and may not be materialized. |
| `army_value_at_5min_snapshot` | Snapshot value of `MineralsUsedCurrentArmy + VespeneUsedCurrentArmy` at the latest PlayerStats with `loop <= 6720` (~5 min @ 22.4 lps; V1 caveat). The 5-minute cutoff is expressed in loops; seconds is contextual only. |
| `minerals_collection_rate_history_mean` | Snapshot-history mean over PlayerStats events with `loop <= cutoff_loop`. |

---

## §7 aoestats feature families

### §7.1 Source label

aoestats is **aoestats Tier 4** semantic opacity per
`thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.1.7 / §4.3. The
recommended Phase 02 source label is:

> "aoestats 1v1 Random Map records (source label `leaderboard='random_map'`;
> queue semantics unverified against upstream API documentation; Tier 4)"

aoestats MUST NOT be called unqualified ranked ladder. The `leaderboard`
filter retains records whose upstream queue semantics (ranked vs quickplay vs
custom-lobby contamination) cannot be verified from available external
documentation.

### §7.2 aoestats `pre_game` candidate families

| Feature family | Source | Grain | Temporal anchor | Allowed cutoff rule | Constraint / caveat |
|----------------|--------|-------|-----------------|---------------------|---------------------|
| `focal_civ` / `opponent_civ` | `matches_history_minimal.faction` (full AoE2 civ name; CROSS-02-00 §5.2) | match_pair focal row (post-projection from `p0_*` / `p1_*`) | `started_at` (CROSS-02-00 §5.2 — CAST from `TIMESTAMPTZ AT TIME ZONE 'UTC'`) | none | Encoded within `dataset_tag = 'aoestats'`; 50 distinct civs in 1v1 scope per aoestats `INVARIANTS.md §1`. |
| `civ_matchup` (focal × opponent) | derived from `focal_civ` / `opponent_civ` | match_pair focal row | `started_at` | none | Up to 1,225 ordered civ pairs (RISK-25); encoder fit within `dataset_tag` partition. Mirror flag from `player_history_all.mirror`. |
| `map` | `player_history_all.map` joined by match_id and player_id | match_pair focal row | `started_at` | none | 77+ distinct map names in 1v1 ranked scope; encoder fit per `dataset_tag` partition; vocabulary disjoint from sc2egset. |
| `patch_id` (if available) | `player_history_all.patch` (CROSS-02-00 §5.5) | match_pair focal row | `started_at` | none | 19 distinct patches per aoestats Phase 01 evidence; PSI elevated in 6 of 8 quarters. |
| `temporal_calendar_features` | derived from `started_at` (CONTEXT) | match_pair focal row | `started_at` | none | Calendar context (year, quarter, month, day-of-week, etc.); no leakage at construction time. |
| `old_rating` (CONDITIONAL_PRE_GAME) | `player_history_all.old_rating` (CROSS-02-00 §5.5) | match_pair focal row | `started_timestamp` | strict-anchor conditional: `leaderboard = 'random_map' AND (time_since_prior_match_days < 7 OR time_since_prior_match_days IS NULL)` | **Conditional pre-game only.** Per CROSS-02-00 §5.5, `old_rating` is `CONDITIONAL_PRE_GAME` — it is unsafe as a generic PRE_GAME feature outside the conditional window. NULL handling is governed by aoestats `INVARIANTS.md §3`. |
| `is_unrated` flag | `player_history_all.is_unrated` (CROSS-02-00 §5.5) | match_pair focal row | `started_at` | none | TRUE iff `old_rating` was the 0 sentinel (~0.027% of rows). |

### §7.3 aoestats `history_enriched_pre_game` candidate families

| Feature family | Source | Grain | Temporal anchor | Allowed cutoff rule | Constraint / caveat |
|----------------|--------|-------|-----------------|---------------------|---------------------|
| `focal_player_history` | rolling/expanding aggregates over `player_history_all` rows for the focal `profile_id`: prior match count, prior win rate, time since prior match, civ-conditional win rate, map-conditional win rate, civ-matchup-conditional win rate | match_pair focal row | `started_timestamp` | `ph.started_timestamp < target.started_at` (strict, per CROSS-02-00 §3.3) | DuckDB session MUST run with `SET TimeZone = 'UTC'` due to `TIMESTAMPTZ` ↔ `TIMESTAMP` comparison. Cold-start gate per §9. |
| `opponent_player_history` | symmetric mirror of `focal_player_history` for the opponent `profile_id` | match_pair focal row | `started_timestamp` | `ph.started_timestamp < target.started_at` (strict) | Symmetric (Invariant I5). |
| `matchup_history_aggregate` | head-to-head and matchup-conditional history aggregates (focal vs opponent civ across all prior games) | match_pair focal row | `started_timestamp` | strict; same-match leakage forbidden | Cold-start gate per §9. |
| `reconstructed_rating` (Elo / Glicko-2) | derived from `player_history_all.winner` filtered by I3 anchor | match_pair focal row | `started_timestamp` | strict; rating state computed strictly from prior decisive results | Only if temporally disciplined; `new_rating` is POST_GAME and excluded. |

**Excluded for aoestats.** Source values and post-outcome attributes are
forbidden as Phase 02 features:

- `new_rating` (POST_GAME);
- any column tagged `POST_GAME_HISTORICAL`, `IN_GAME_HISTORICAL`, or `TARGET`
  (per CROSS-02-00 §5.5);
- raw `won`/`winner` of the target match;
- full-replay aggregates where the target match's row is in the window.

---

## §8 aoe2companion feature families

### §8.1 Source label

aoe2companion is **aoe2companion mixed-mode**: the Phase 02 cohort spans
`internalLeaderboardId IN (6, 18)`, where ID 6 is `rm_1v1` (ranked candidate;
Tier 2 per `aoe2_ladder_provenance_audit.md` §4.3) and ID 18 is `qp_rm_1v1`
(quickplay/matchmaking-derived; Tier 3). The combined scope is mixed-mode
and is not ranked-only — Phase 02 prose, label, and stratification fields
must preserve the ranked vs quickplay distinction.

The recommended Phase 02 combined-scope label is:

> "aoe2companion 1v1 Random Map records combining ranked (`rm_1v1`, ID 6,
> ~54M `leaderboard_raw` rows) and quickplay/matchmaking
> (`qp_rm_1v1`, ID 18, ~7M `leaderboard_raw` rows; external API unavailable
> 2026-04-26)"

### §8.2 aoe2companion `pre_game` candidate families

| Feature family | Source | Grain | Temporal anchor | Allowed cutoff rule | Constraint / caveat |
|----------------|--------|-------|-----------------|---------------------|---------------------|
| `focal_civ` / `opponent_civ` | `matches_history_minimal.faction` (CROSS-02-00 §5.3) | match_pair focal row | `started_at` (TIMESTAMP, pass-through from `matches_raw.started`) | none | Zero NULLs per CROSS-02-00 §5.3; encoded within `dataset_tag = 'aoe2companion'`. |
| `civ_matchup` (focal × opponent) | derived from `focal_civ` / `opponent_civ` | match_pair focal row | `started_at` | none | Up to 1,225 ordered civ pairs (RISK-25). |
| `map` | `player_history_all.map` joined by `matchId` and `profileId` | match_pair focal row | `started_at` | none | 94+ distinct AoE2 map names in 1v1 mixed-mode scope. |
| `rating` (PRE_GAME) | `player_history_all.rating` (CROSS-02-00 §5.6) | match_pair focal row | `started_at` | none | ~26% NULL (MAR; schema evolution). NULL handling is per §9 cold-start gates; `is_rating_missing` flag must be co-registered when used. |
| `gameMode` | `player_history_all.gameMode` (CROSS-02-00 §5.6) | match_pair focal row | `started_at` | none | `random_map` / `empire_wars`; encoder fit within `dataset_tag` partition. |
| `leaderboard` / `internalLeaderboardId` (mode stratification) | `player_history_all.leaderboard` + `matches_raw.internalLeaderboardId` | match_pair focal row | `started_at` | none | **Stratification field, not a generic categorical feature.** Used to preserve the ID 6 ranked candidate vs ID 18 quickplay-matchmaking distinction across modeling runs. Required for Invariant I9 source-stratified evaluation. |
| `temporal_calendar_features` | derived from `started_at` | match_pair focal row | `started_at` | none | Calendar context. |

### §8.3 aoe2companion `history_enriched_pre_game` candidate families

| Feature family | Source | Grain | Temporal anchor | Allowed cutoff rule | Constraint / caveat |
|----------------|--------|-------|-----------------|---------------------|---------------------|
| `focal_player_history` | rolling/expanding aggregates over `player_history_all` rows for the focal `profileId`: prior match count, prior win rate, time since prior match, civ-conditional win rate, map-conditional win rate, civ-matchup-conditional win rate, leaderboard-conditional win rate (ID 6 vs ID 18) | match_pair focal row | `started` (CROSS-02-00 §5.6) | `ph.started < target.started_at` (strict) | Cold-start gate per §9. Leaderboard stratification preserved per §8.4. |
| `opponent_player_history` | symmetric mirror of `focal_player_history` for the opponent `profileId` | match_pair focal row | `started` | `ph.started < target.started_at` (strict) | Symmetric (Invariant I5). |
| `matchup_history_aggregate` | head-to-head and civ-matchup-conditional history aggregates | match_pair focal row | `started` | strict; same-match leakage forbidden | Cold-start gate per §9. |
| `reconstructed_rating` (Elo / Glicko-2) | derived from `player_history_all.won` filtered by I3 anchor | match_pair focal row | `started` | strict; rating state computed strictly from prior decisive results | Only if temporally disciplined. ID-6-vs-ID-18 scope must be honored: rating reconstruction within ID 6, within ID 18, and combined are three different families and must not be silently merged. |

### §8.4 aoe2companion source-specific stratification

For all aoe2companion feature families, the following source-specific labels
must be preserved through to evaluation planning:

- ID 6 (`rm_1v1`): Tier 2 — ranked candidate.
- ID 18 (`qp_rm_1v1`): Tier 3 — quickplay/matchmaking-derived.
- ID 6 + ID 18 combined: aoe2companion mixed-mode, not ranked-only.

A stratification column `leaderboard_id` must be co-registered alongside any
aoe2companion feature row so that evaluation, error analysis, and sensitivity
arms can preserve the ranked vs quickplay distinction. The stratification
itself is declared here; the empirical stratification is performed by a future
Phase 02 step.

**Excluded for aoe2companion.** Same exclusions as aoestats: post-game values,
target-match `won`, `IN_GAME_HISTORICAL` / `POST_GAME_HISTORICAL` / `TARGET`
columns, full-replay aggregates that include the target match.

---

## §9 Cold-start handling gates

CROSS-02-02 declares **gates**, not constants. No magic pseudocount `m`,
smoothing strength, prior strength, threshold `K`, or cutoff value is fixed in
this spec. Per Invariant I7, every numeric value MUST be data-derived from
training-fold statistics or literature-cited and recorded in the per-dataset
Phase 02 ROADMAP step that materializes it.

### §9.1 Gates

| Gate | Rule | Falsifier |
|------|------|-----------|
| **G-CS-1** No magic pseudocount | No pseudocount `m`, smoothing strength `α`, prior strength `K`, or threshold `n_prior_matches >= K` may be hard-coded in Phase 02 feature code. Each numeric value must be derived from a training-fold-only empirical procedure or cited from literature. | A Phase 02 feature definition contains a numeric pseudocount or threshold without a documented empirical derivation or literature citation. |
| **G-CS-2** Cold-start flags allowed if declared | A `is_cold_start` or `n_prior_matches < K` mask is permitted as a feature, provided its meaning, the threshold derivation, and its training-fold-fit scope are declared in the per-dataset Phase 02 ROADMAP step. | A cold-start flag appears in a feature table without a documented threshold derivation. |
| **G-CS-3** Smoothing constants require empirical derivation | Bayesian-smoothing constants (e.g., per-civ prior win rate, per-matchup prior count) must be derived empirically from training folds only, OR cited from prior precedent in the literature. The derivation procedure must be reviewable before materialization. | A smoothing constant appears in a feature without a fold-aware derivation procedure. |
| **G-CS-4** Missing history must be encoded explicitly | The first-match row for any `(player_id, dataset_tag)` (or per-leaderboard partition where applicable) must not be silently dropped. Missingness must be encoded as a `is_first_match` flag, an imputed value with explicit imputation rule, or a separate cold-start branch. | A feature pipeline drops first-match rows or imputes them with a global statistic without flagging. |
| **G-CS-5** Per-source cold-start behavior must be documented | Each dataset's cold-start regime must be characterized in a Phase 02 ROADMAP step before any model training step begins. The characterization must enumerate: cold-start row count under the chosen rule, fold-aware smoothing constants (or cite the precedent), and the impact of the chosen rule on the modeling matrix. | A model training step proceeds without a documented cold-start characterization for its source dataset. |
| **G-CS-6** Train-fold-only fit | All scaling, normalization, smoothing-prior, and target-encoding statistics must be fit on training folds only (per CROSS-02-01-v1.0.1 §2.3). | A scaler, encoder, or smoothing prior is fit on the full dataset before train/test split. |

### §9.2 What this section does not commit

CROSS-02-02 does not commit:

- a value for `K` (cold-start threshold);
- a value for any pseudocount `m` or smoothing strength `α`;
- a global prior win rate;
- an imputation strategy for missing rating values;
- a specific Bayesian-smoothing functional form.

These values are deferred to a Phase 02 ROADMAP step that empirically derives
or literature-cites them, with the derivation procedure committed alongside
the value.

---

## §10 Leakage checks (planned, not implemented)

The following design-time leakage checks are declared by CROSS-02-02. They are
**planned**; their materialization belongs to a future Phase 02 step (likely
the proposed `02_03_temporal_feature_audit_protocol.md` companion spec). The
checks below do **not** replace CROSS-02-01-v1.0.1's post-materialization
audit gate.

| Check | Rule | Falsifier |
|-------|------|-----------|
| **G-L-1** Strict history cutoff | Every history-derived feature must satisfy `history_time < target_time` strictly. The per-dataset anchor column comes from CROSS-02-00 §3.2. | A history feature uses `<=` or no cutoff against the per-dataset anchor. |
| **G-L-2** Strict in-game cutoff | Every `in_game_snapshot` feature must satisfy `event.loop <= cutoff_loop` (game loops; the seconds conversion is contextual). | A tracker-derived feature reads `event.loop > cutoff_loop`, or the cutoff is expressed only in seconds without a corresponding loop value. |
| **G-L-3** No target-match final state | No feature for game T may read game T's final state, decisive result, ending loop, or post-completion column. | A feature pipeline projects a column tagged TARGET / POST_GAME_HISTORICAL / IN_GAME_HISTORICAL of the target match itself. |
| **G-L-4** No post-game rating delta | No `pre_game` or `history_enriched_pre_game` feature may read game T's post-game rating delta or rating-after value. | A feature reads `new_rating` (aoestats) or any post-match rating field for game T. |
| **G-L-5** No full-replay aggregate for cutoff snapshots | For `in_game_snapshot` features, no aggregate may include events strictly after `cutoff_loop`. Full-replay `MIN(loop)` or `MAX(loop)` is leakage when paired with a cutoff. | A tracker feature uses a full-replay min / max / count without applying the `event.loop <= cutoff_loop` filter. |
| **G-L-6** No global normalization before split | Scalers, normalizers, encoders, and smoothing priors must be fit on training folds only, never on the pooled dataset before train/test split. | A scikit-learn `Pipeline.fit_transform` is called on the full dataframe before splitting. |
| **G-L-7** No same-match leakage in head-to-head / rolling aggregates | For `(focal, opponent)` head-to-head aggregates and rolling-window aggregates, the target match's own row MUST NOT appear in the window. | A head-to-head aggregate uses `<=` instead of strict `<` and includes the target match. |
| **G-L-8** No row-order leakage from p0/p1 or focal/opponent slot asymmetry | The `(p0, p1)` source slot in aoestats and the `(focal, opponent)` projected slot must be assigned by a canonical, skill-orthogonal rule (e.g., `canonical_slot` for aoestats per CROSS-02-00 §5.2). The model must not see a slot label that correlates with the outcome. | A feature row's slot assignment is data-dependent (e.g., assigning `focal = winner`) or correlated with the target. |
| **G-L-9** No source-mode leakage via labels | Source-mode labels (aoestats Tier 4 source label; aoe2companion `internalLeaderboardId`) must be used as stratification or sensitivity controls only — not as a generic model input that aliases for a population shortcut. The label may be a feature only when its semantics are explicitly declared as a stratification / control rather than a generic categorical. | An aoe2companion `internalLeaderboardId` column is fed into the model without being declared as a stratification / control field per §8.4. |

The full materialization of these checks (machine-readable per-family
falsifiers, per-Pipeline-Section reuse, audit artifacts) belongs to the
companion spec CROSS-02-03 to be authored later. CROSS-02-02 declares the
checks; CROSS-02-03 will operationalize them.

---

## §11 SC2 tracker eligibility constraint (read from `tracker_events_feature_eligibility.csv`)

The table below summarizes the 15 rows of
`src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`.
Row counts were derived by reading the CSV directly; CROSS-02-02 does not
modify the CSV. The CSV is the authoritative contract; this table is a
planning summary and is not a substitute for reading the CSV row by row when
authoring a feature-generation step.

### §11.1 Counts by status

| `status_in_game_snapshot` | Count | Phase 02 disposition |
|---------------------------|-------|----------------------|
| `eligible_for_phase02_now` | 5 | Allowed for `in_game_snapshot` Phase 02 entry, basic cutoff-count scope only. Includes 4 model-input families plus 1 sanity gate. |
| `eligible_with_caveat` | 7 | Allowed for `in_game_snapshot` Phase 02 entry under each row's `caveat`. |
| `blocked_until_additional_validation` | 3 | Excluded from initial Phase 02 scope; require future dedicated validation. |
| **Total** | **15** | — |

### §11.2 Family disposition table

| Family | Source event family | Status (in-game snapshot) | Disposition for Phase 02 |
|--------|--------------------|--------------------------|-------------------------|
| `count_units_built_by_cutoff_loop` | UnitBorn | `eligible_for_phase02_now` | Allowed (basic cutoff-count) |
| `count_units_killed_by_cutoff_loop` | UnitDied | `eligible_for_phase02_now` | Allowed (basic cutoff-count) |
| `morph_count_by_cutoff_loop` | UnitTypeChange | `eligible_for_phase02_now` | Allowed (lineage-attributed cutoff-count) |
| `building_construction_count_by_cutoff_loop` | UnitInit / UnitDone | `eligible_for_phase02_now` | Allowed (basic cutoff-count) |
| `slot_identity_consistency` | PlayerSetup | `eligible_for_phase02_now` | **Sanity gate, not model input.** Per-replay structural validity check. |
| `minerals_collection_rate_history_mean` | PlayerStats | `eligible_with_caveat` | Allowed under V3 PASS_WITH_CAVEAT snapshot-history mean over events with `loop <= cutoff_loop` |
| `army_value_at_5min_snapshot` | PlayerStats | `eligible_with_caveat` | Allowed; cutoff at `loop <= 6720` (~5 min @ 22.4 lps; V1 caveat) |
| `supply_used_at_cutoff_snapshot` | PlayerStats | `eligible_with_caveat` | Allowed only after PlayerStats fixed-point/scaling caveat for `scoreValueFoodUsed` is resolved (s2protocol divide-by-4096 vs SC2EGSet pre-scaled) |
| `food_used_max_history` | PlayerStats | `eligible_with_caveat` | Allowed only after the same fixed-point/scaling caveat is resolved |
| `time_to_first_expansion_loop` | UnitBorn | `eligible_with_caveat` | Allowed only as cutoff-censored `MIN(loop)` over events with `loop <= cutoff_loop`, plus `has_expansion_by_cutoff` indicator. Full-replay `MIN(loop)` is leakage and is blocked. |
| `count_units_lost_by_cutoff_loop` | UnitDied | `eligible_with_caveat` | Allowed (lineage-attributed; orphan deaths excluded from per-player counts) |
| `count_upgrades_by_cutoff_loop` | Upgrade | `eligible_with_caveat` | Allowed only as `COUNT(*)` per `(filename, playerId)`. The `Upgrade.count` field MUST NOT be trusted as a cumulative tally without source confirmation. |
| `mind_control_event_count` | UnitOwnerChange | `blocked_until_additional_validation` | Excluded |
| `army_centroid_at_cutoff_snapshot` | UnitPositions | `blocked_until_additional_validation` | Excluded |
| `playerstats_cumulative_economy_fields` | PlayerStats | `blocked_until_additional_validation` | Excluded |

### §11.3 GATE-14A6 status

GATE-14A6 outcome: narrowed. The full tracker scope is not closed: per the PR
#208 §14A.6 POST-VALIDATION UPDATE, `gate_14a6_decision = narrowed`,
`planned_subset_ready_predicate_satisfied = true`, and
`full_tracker_scope_closed_predicate_satisfied = false`. CROSS-02-02 honors
this distinction: only the 12 planned-yes rows enter Phase 02; the 3
`blocked_until_additional_validation` rows remain outside scope until a future
dedicated validation step (per `phase02_readiness_hardening.md` §14A.6 future
validation route) lands.

---

## §12 Proposed Phase 02 ROADMAP steps (proposals only)

The proposals below are **not** dataset ROADMAP edits. CROSS-02-02 does not
touch any dataset ROADMAP. A future PR (separate from this T03 step) may
convert a proposal into an executed ROADMAP step with explicit user approval
and a separate commit.

Every empirical step in the sequence below MUST follow
`.claude/rules/data-analysis-lineage.md`: ROADMAP stub only first; notebook
scaffold + one validation module; execute and report; user review; commit;
next validation module; only after all validation modules pass, generate
artifacts; then research_log / STEP_STATUS / manifest; then reviewer-deep.

### §12.1 Proposed sequence

| Section | Proposed scope | Lineage rule |
|---------|----------------|--------------|
| `02_00 contract / readiness check` | Cross-dataset preflight: confirm CROSS-02-00, CROSS-02-01, CROSS-02-02 are all current; confirm all three `PHASE_STATUS.yaml` files show Phase 01 = complete and Phase 02 = not_started; confirm no manifest row is `flagged_stale` for Phase 02 entry. | Read-only; no artifact. |
| `02_01 feature-family registry skeleton` | Per-dataset registry of declared feature families from §6 / §7 / §8, with `family_id`, `dataset`, `prediction_setting`, `grain`, `temporal_anchor`, `allowed_now`, `caveats`, and `downstream_section`. Registry is a planning / catalog artifact only. | Notebook scaffold + one validation module per `.claude/rules/data-analysis-lineage.md`; no feature values produced. |
| `02_02 pre-game / history feature scaffold per dataset` | Per-dataset scaffold notebook that consumes CROSS-02-00 inputs, projects to focal/opponent grain (aoestats), and exercises one validation module per dataset (e.g., a single `is_mmr_missing` flag for sc2egset, a single `civ` encode-within-partition for aoestats / aoe2companion). No feature table is produced. | Halt before artifact generation; user review at the validation-module checkpoint per `.claude/rules/data-analysis-lineage.md`. |
| `02_03 SC2 tracker snapshot validation slice` | Tiny SC2-only validation slice that exercises one `in_game_snapshot` family at one cutoff loop (e.g., `count_units_built_by_cutoff_loop` at one cutoff) on a small set of replays. The slice's purpose is to exercise the cutoff rule, lineage attribution, and slot-identity-consistency sanity gate end-to-end. No model is trained. | One feature family at a time; user approval before adding the next family. |
| `02_04 cold-start measurement` | Per-dataset empirical characterization of cold-start regime (n_prior_matches distributions, threshold-derivation procedure, fold-aware smoothing constants). Output is a measurement report; cold-start values are only declared, not pinned, in CROSS-02-02. | No feature table; report only. |
| `02_05 leakage audit dry-run` | Per-dataset dry-run of the §10 design-time leakage checks AND the CROSS-02-01-v1.0.1 audit artifact schema, on whatever scaffold features exist at this point. Validates that the audit pipeline produces a valid `leakage_audit_<dataset>.json` + `.md` artifact set. | Audit artifact only; no model training. |
| `02_06 feature table generation only after approved validations` | First feature-generation step. Materializes feature columns for one dataset under one prediction setting, only after §12.1 sections `02_01`–`02_05` have been reviewed and committed. The CROSS-02-01-v1.0.1 audit gate fires after materialization and before any consuming step. | Feature generation requires explicit user approval after `02_01`–`02_05` are reviewed. |

### §12.2 Empirical-step discipline

Every empirical step in §12.1 MUST follow `.claude/rules/data-analysis-lineage.md`,
specifically the non-batching rule: ROADMAP, notebook, artifact, and next
step are not batched in one execution. If any sanity check fires or any
falsifier from §9 / §10 / §11 fails, the step halts before artifact
generation and the failure is reviewed.

---

## §13 Validation, sanity, falsifier, and lineage

### §13.1 Sanity check (textual / mechanical)

Every feature family declared in §6 / §7 / §8 declares:

- dataset (`sc2egset` / `aoestats` / `aoe2companion`);
- prediction setting (`pre_game` / `history_enriched_pre_game` / `in_game_snapshot`);
- grain (per §4.2);
- temporal anchor (per CROSS-02-00 §3.2);
- cutoff / leakage rule (per §5 / §10).

Tables in §6, §7, §8, and §11 carry these columns explicitly; cross-checking
this section against any feature-family row should never find a missing
field.

### §13.2 Falsifier

The following observations halt CROSS-02-02 (i.e., the spec must be revised
or the offending step must be blocked):

- any SC2 tracker-derived family appears with `prediction_setting = pre_game`
  in §6 or in any consuming Phase 02 step (Invariant I3 violation; Amendment 2
  of PR #208);
- any AoE2 source is called unqualified ranked ladder in §7, §8, §9, or
  downstream prose generated against this spec;
- any history-derived feature lacks the `history_time < target_time` strict
  cutoff in its declared rule;
- any proposed §12 step implies a notebook or generated-artifact step before
  user review of the prior validation-module checkpoint;
- any blocked tracker family from §11 (`mind_control_event_count`,
  `army_centroid_at_cutoff_snapshot`, `playerstats_cumulative_economy_fields`)
  is declared as a Phase 02 candidate;
- the spec states or implies that any feature table has been materialized,
  produced, or generated by this T03 step (this T03 step produces a planning
  document only; no on-disk feature data exists as a result of CROSS-02-02).

### §13.3 Artifact validation

CROSS-02-02 produced no generated artifact and modified no generated
artifact. The only output of this T03 step is the file
`reports/specs/02_02_feature_engineering_plan.md` itself. Status YAML files,
research logs, ROADMAPs, notebooks, and feature tables are unchanged.

### §13.4 Lineage

Input files read by CROSS-02-02 (no modification):

- `.claude/rules/data-analysis-lineage.md`
- `.claude/scientific-invariants.md`
- `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v3.0.1)
- `reports/specs/02_01_leakage_audit_protocol.md` (CROSS-02-01-v1.0.1)
- `thesis/pass2_evidence/phase01_closeout_summary.md`
- `thesis/pass2_evidence/phase02_readiness_hardening.md`
- `thesis/pass2_evidence/audit_cleanup_summary.md`
- `thesis/pass2_evidence/methodology_risk_register.md`
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PHASE_STATUS.yaml`

Output file created by CROSS-02-02 (this file):

- `reports/specs/02_02_feature_engineering_plan.md`

No other on-disk file is touched by this T03 step.

---

## §14 Spec change protocol

Version strings follow the cross-dataset spec pattern `CROSS-02-02-vN.M.K`:

- **vN+1 (major):** changes to §3 prediction settings, §4 feature table
  grains, §5 cross-dataset commitments, §10 leakage checks, or any change
  that contradicts CROSS-02-00-v3.0.1 / CROSS-02-01-v1.0.1. Requires full
  `planner-science` + reviewer-adversarial gate.
- **vN.M+1 (minor):** additions to §6 / §7 / §8 feature families, §9
  cold-start gates, §11 tracker eligibility table (only if the upstream CSV
  itself is amended through canonical lineage), §12 proposed Phase 02
  ROADMAP steps. Requires `planner-science` + `reviewer-deep` gate.
- **vN.M.K+1 (patch):** prose clarifications, typo corrections, added
  references, status transitions (DRAFT → LOCKED) — provided no table cell
  values change. May be reviewed by the standard `reviewer` only.

Any amendment requires an entry in the amendment log (§16). The `version`
and `status` fields in the frontmatter MUST be bumped in the same commit as
the amendment.

The DRAFT → LOCKED transition is itself a patch under the rules above. It
fires after the reviewer-deep gate prescribed by the active Phase 02
readiness plan returns PASS or PASS-WITH-NOTES; CROSS-02-02 then ratchets
into the binding cross-dataset Phase 02 contract triplet alongside
CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1.

---

## §15 Referenced artifacts

### §15.1 Sibling specs (binding)

- `reports/specs/02_00_feature_input_contract.md` — **CROSS-02-00-v3.0.1**, LOCKED
  2026-04-26. Authoritative input contract: VIEWs, column grains, join keys,
  per-dataset I3 anchors, cross-game encoding protocol, column-level
  classification.
- `reports/specs/02_01_leakage_audit_protocol.md` — **CROSS-02-01-v1.0.1**, LOCKED
  2026-04-26. Authoritative pre-training leakage audit protocol; binding for
  Pipeline Section 02_01 exit and reused by 02_03 / 02_06.

### §15.2 Phase 02 readiness evidence

- `thesis/pass2_evidence/phase01_closeout_summary.md` — Phase 01 → Phase 02
  entry conditions; AoE2 source-specific labels; GATE-14A6 outcome: narrowed.
- `thesis/pass2_evidence/phase02_readiness_hardening.md` — T16 14A.6
  POST-VALIDATION UPDATE; full tracker scope is not closed; future tracker
  validation route.
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` — four-tier AoE2
  ladder governance; aoestats Tier 4; aoe2companion mixed-mode (ID 6 + ID 18).
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` — five-axis
  bounded comparability framing.
- `thesis/pass2_evidence/methodology_risk_register.md` — RISK-20 (cross-region
  fragmentation), RISK-21 (tracker semantics, MITIGATED-NARROWED post-PR
  #208), RISK-24/25/26.
- `thesis/pass2_evidence/notebook_regeneration_manifest.md` — authoritative
  stale/current status for any consumed generated artifact; CROSS-02-01-v1.0.1
  §4 stale-artifact discipline references this file.
- `thesis/pass2_evidence/audit_cleanup_summary.md` — context for stale-artifact
  discipline and the post-T19 warning-resolution micro-pass.

### §15.3 Authoritative SC2 tracker contract

- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`
  — 15 rows, per-prediction-setting columns per Amendment 2 of PR #208.
  Authoritative contract for all SC2 `in_game_snapshot` families. Read-only
  for CROSS-02-02; modifications require a separate dedicated step in the
  sc2egset dataset ROADMAP.

### §15.4 Methodology

- `.claude/rules/data-analysis-lineage.md` — anti-GIGO workflow rule binding
  every empirical Phase 02 step.
- `.claude/scientific-invariants.md` — invariants I3 (temporal), I5
  (symmetry), I6 (verbatim SQL evidence), I7 (no magic numbers), I8
  (cross-game comparability), I9 (source-stratified evaluation), I10
  (filename relative paths).
- `docs/PHASES.md` — canonical Phase 02 Pipeline Section enumeration.
- `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` — Phase 02
  methodology source.

---

## §16 Amendment log

| Version | Date | Author | Classification | Summary |
|---------|------|--------|----------------|---------|
| CROSS-02-02-v1 (DRAFT) | 2026-05-05 | T03 executor (claude-opus-4-7) on branch `phase02/feature-engineering-readiness` | Initial DRAFT | Initial draft. Defines Phase 02 feature-engineering plan, prediction settings, feature table grains, per-dataset minimal feature families, leakage checks, cold-start gates, source-specific AoE2 labels, SC2 tracker eligibility constraint, and proposed Phase 02 ROADMAP steps. **DRAFT / PR-local until reviewed**: spec becomes binding only after reviewer-deep gate per the active Phase 02 readiness plan returns PASS or PASS-WITH-NOTES. Does not supersede CROSS-02-00-v3.0.1 or CROSS-02-01-v1.0.1; complement to a future CROSS-02-03 spec that will operationalize the §10 leakage checks. |
