---
spec_id: CROSS-02-00-v1
version: CROSS-02-00-v1
status: LOCKED
date: 2026-04-21
invariants_touched: [I2, I3, I5, I8]
supersedes: null
datasets_bound: [sc2egset, aoestats, aoe2companion]
---

# Cross-Dataset Phase 02 Feature-Engineering Input Contract

## CROSS-02-00-v1 (LOCKED 2026-04-21)

This document is the authoritative cross-dataset input contract for Phase 02
feature engineering. It formalizes the interface between Phase 01 outputs and
Phase 02 feature-engineering inputs across three datasets: sc2egset, aoestats,
and aoe2companion. It is derived exclusively from the Phase 01 VIEW schema
yamls — no column names are inherited from earlier or stale specifications.

Phase 02 feature-engineering execution reads this spec as the authoritative
source for input VIEW names, row grain, join keys, I3 temporal anchor,
cross-game categorical encoding protocol, and column-level classification.

Amendments follow the §7 change protocol.

---

## §1 Scope and Binding

### Pipeline Sections Bound

This spec's column-grain commitments (§2) bind all eight Phase 02 Pipeline
Sections (02_01 through 02_08). The §4 encoding protocol specifically binds:

- **02_05 (Categorical Encoding)** — the general rule and all named instances
  of per-dataset polymorphic vocabulary.
- **02_07 (Rating Systems & Domain Features)** — the cross-game
  faction-proficiency encoding rule.

### I2 Cross-Branch Binding Note

This spec prescribes a harmonized `player_id` join column in
`matches_history_minimal` across three datasets whose I2 identity-resolution
branch decisions differ:

- sc2egset: Branch (iii) region-scoped `toon_id` (Battle.net R-S2-G-P format).
- aoestats: Branch (v) structurally-forced `profile_id` (BIGINT; no visible
  handle column present for comparison).
- aoe2companion: Branch (i) API-namespace `profileId` (INTEGER; rename-stable;
  2.57% rename-rate; 0.9960 cross-dataset namespace bridge to aoestats).

Binding a shared join column (`player_id`) atop three I2 branches is an
I2-touching cross-dataset commitment. The harmonization happens inside each
dataset's `matches_history_minimal` VIEW construction (not in this spec). This
spec names the harmonized column as the canonical Phase 02 join key on
`matches_history_minimal`. The raw I2-branch columns (`toon_id`, `profile_id`,
`profileId`) are explicitly exposed in each dataset's `player_history_all` VIEW
and are enumerated per-dataset in §3.2 below.

Reference: `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`
§2 D4a/D4b rows for the I2 branch classification per dataset.

---

## §2 Per-Dataset Canonical Input VIEWs

### §2.1 sc2egset

**Primary VIEW — per-match features:**

| Property | Value |
|----------|-------|
| VIEW name | `matches_history_minimal` |
| Row grain | 2 rows per match (one per player) |
| Row count | 44,418 |
| Column count | 9 |
| Schema version | `9-col (ADDENDUM: duration_seconds added 2026-04-18)` |
| Source artifact | `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_history_minimal.yaml` |
| Step | `01_04_03` |

**History VIEW — rolling-window features:**

| Property | Value |
|----------|-------|
| VIEW name | `player_history_all` |
| Row grain | 1 row per player per match (all game types; no 1v1 filter) |
| Row count | 44,817 |
| Column count | 36 |
| Schema version | (see yaml; no explicit schema_version field) |
| Source artifact | `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml` |
| Step | `01_04_02` |

### §2.2 aoestats

**Primary VIEW — per-match features:**

| Property | Value |
|----------|-------|
| VIEW name | `matches_history_minimal` |
| Row grain | 2 rows per match (one per player) |
| Row count | 35,629,894 |
| Column count | 10 |
| Schema version | `10-col (AMENDMENT: canonical_slot added 2026-04-20)` |
| Source artifact | `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml` |
| Step | `01_04_03b` |

**aoestats-only column:** `canonical_slot VARCHAR NOT NULL` — skill-orthogonal slot
identity derived from `hash(match_id)` (01_04_03b). This column does NOT appear in
sc2egset or aoe2companion. Cross-dataset UNION ALL queries MUST project the 9 shared
columns only and exclude `canonical_slot`.

**History VIEW — rolling-window features:**

| Property | Value |
|----------|-------|
| VIEW name | `player_history_all` |
| Row grain | 1 row per player per match (all leaderboards; no 1v1 filter) |
| Row count | 107,626,399 |
| Column count | 14 |
| Schema version | (see yaml; no explicit schema_version field) |
| Source artifact | `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml` |
| Step | `01_04_02` |

### §2.3 aoe2companion

**Primary VIEW — per-match features:**

| Property | Value |
|----------|-------|
| Object name | `matches_history_minimal` |
| Object type | TABLE (materialized; DuckDB 1.5.1 bug workaround — semantics identical to VIEW) |
| Row grain | 2 rows per match (one per player) |
| Row count | 61,062,392 |
| Column count | 9 |
| Schema version | `9-col (ADDENDUM: duration_seconds added 2026-04-18)` |
| Source artifact | `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/matches_history_minimal.yaml` |
| Step | `01_04_03` |

**History VIEW — rolling-window features:**

| Property | Value |
|----------|-------|
| VIEW name | `player_history_all` |
| Row grain | 1 row per player per match (all leaderboards; no 1v1 filter) |
| Row count | 264,132,745 |
| Column count | 19 |
| Schema version | (see yaml; no explicit schema_version field) |
| Source artifact | `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/player_history_all.yaml` |
| Step | `01_04_02` |

---

## §3 Join Keys and I3 Temporal Anchor — Per-Dataset Mappings

### §3.1 `matches_history_minimal` (harmonized; cross-dataset canonical)

All three datasets share the following harmonized column contract on
`matches_history_minimal`:

| Role | Column | Type | Notes |
|------|--------|------|-------|
| Join key (player) | `player_id` | VARCHAR | Harmonized across all three datasets; raw I2-branch IDs differ per §3.2 |
| I3 temporal anchor | `started_at` | TIMESTAMP | UTC; no timezone; canonical cross-dataset dtype |
| Match key | `match_id` | VARCHAR | Prefixed `<dataset_tag>::<native_id>`; collision-safe for cross-dataset UNION ALL |
| Dataset discriminator | `dataset_tag` | VARCHAR NOT NULL | Values: `sc2egset`, `aoestats`, `aoe2companion` |

The `match_id` prefix equals the `dataset_tag` value (e.g.,
`aoestats::12345678`). This is the canonical cross-dataset UNION ALL safe
identifier.

### §3.2 `player_history_all` (per-dataset raw; NOT harmonized at source)

The corresponding join key and I3 temporal anchor columns in
`player_history_all` differ by dataset and are NOT harmonized. Phase 02
feature extractors that query `player_history_all` directly MUST use the
per-dataset column names shown below.

| Dataset | Join key column | Join key type | I3 temporal anchor column | Anchor type |
|---------|-----------------|---------------|---------------------------|-------------|
| sc2egset | `toon_id` | VARCHAR | `details_timeUTC` | VARCHAR |
| aoestats | `profile_id` | BIGINT | `started_timestamp` | TIMESTAMPTZ |
| aoe2companion | `profileId` | INTEGER | `started` | TIMESTAMP |

**Critical caution:** Writing `WHERE ph.started_at < target.started_at` against
`player_history_all` will produce a column-not-found error on all three datasets
— the column `started_at` exists in `matches_history_minimal` only (the
harmonized VIEW). The correct column name in `player_history_all` is
dataset-specific (see table above).

### §3.3 Rolling-Window I3 Guard

Every rolling-window query over `player_history_all` MUST apply a strict
less-than filter on the I3 temporal anchor (equality forbidden; a match at
exactly the same timestamp as the target is NOT prior history):

```sql
-- Placeholder pattern — substitute ph.<anchor> with the per-dataset column
-- from §3.2. Do NOT hard-code started_at here.
WHERE ph.<anchor> < target.started_at
```

The per-dataset anchor column comes from §3.2. Phase 02 implementations MUST
resolve `<anchor>` to the concrete per-dataset column before any SQL is
executed.

**CAUTION:** Any query written as `WHERE ph.started_at < target.started_at`
applied to `player_history_all` will fail for all three datasets (sc2egset:
column is `details_timeUTC`; aoestats: column is `started_timestamp`;
aoe2companion: column is `started`). This is a structural failure, not a
data-quality failure.

**Additional I3 rules:**

1. Columns tagged `POST_GAME_HISTORICAL`, `IN_GAME_HISTORICAL`, or `TARGET` in
   `player_history_all` MUST be aggregated only over rows filtered by the I3
   guard; they must NOT be projected directly as game-T features.
2. Columns tagged `PRE_GAME` or `CONTEXT` in `player_history_all` are safe as
   direct game-T features without the rolling-window I3 filter (they were
   available before game T started).
3. The I3 guard applies to all Phase 02 Pipeline Sections, not only 02_03.
   Any Section that touches `player_history_all` inherits this constraint.

### §3.4 Cross-Dataset Player-History Joins

When UNION-ALL'ing player histories across datasets for cross-game analysis
(Phase 06 or cross-dataset Phase 02 feature parity checks), a composite key
`(dataset_tag, player_id)` is required. Bare `player_id` is per-dataset-scoped
only; cross-dataset string collisions of raw IDs are structurally possible
because sc2egset `toon_id` and aoe2companion `profileId` occupy different
namespaces but are both exposed as strings at the application layer.

One harmonization option is to wrap each dataset's `player_history_all` in a
Phase-02-owned canonicalizing VIEW that renames the raw anchor column to
`started_at` and the raw join key to `player_id`. This option should be named
as a candidate pattern but NOT prescribed here — Phase 02 02_01 kickoff picks
the concrete strategy.

---

## §4 Cross-Game Categorical Encoding Protocol (I8 Compliance)

### §4.1 General Binding Rule

Any column whose vocabulary is per-dataset (disjoint, non-interchangeable
values across `dataset_tag` partitions) MUST be encoded within a `dataset_tag`
partition.

**Explicitly forbidden patterns:**

- `GROUP BY <polymorphic_col>` without a `WHERE dataset_tag = '<value>'` or
  equivalent partition filter — this treats game-specific categoricals as
  shared vocabulary and violates I8.
- `OneHotEncoder(<polymorphic_col>)` fit on rows from multiple datasets — the
  encoder learns a combined vocabulary that does not exist as a coherent
  semantic space.

Reference: `.claude/scientific-invariants.md` I8.

### §4.2 Known Instances of Per-Dataset Polymorphic Vocabulary (Non-Exhaustive)

The following instances are known at Phase 01 exit. New instances discovered
during Phase 02 require a spec amendment (§7 change protocol).

**(a) Faction / race / civ — vocabulary + column-name asymmetry**

The `faction` column in `matches_history_minimal` and the race/civ columns in
`player_history_all` encode the player's chosen faction but differ in both
vocabulary and column name:

| Dataset | MHM column | PH column | Sample vocabulary |
|---------|-----------|-----------|-------------------|
| sc2egset | `faction` | `race` | Prot, Terr, Zerg, Rand (4-char abbreviations) |
| aoestats | `faction` | `civ` | Mongols, Franks, Britons, Persians, … (~50 distinct civ names) |
| aoe2companion | `faction` | `civ` | Franks, Mongols, Britons, … (full civ names; zero NULLs) |

Note the column-name asymmetry in `player_history_all`: sc2egset uses `race`;
aoestats and aoe2companion use `civ`. Phase 02 feature extractors must branch
on `dataset_tag` for both the column name and the vocabulary.

**(b) Map / map name — disjoint vocabularies**

The map columns encode the map played but have disjoint vocabularies across
games:

| Dataset | MHM column | PH column | Scope |
|---------|-----------|-----------|-------|
| sc2egset | (via player_history_all) | `metadata_mapName` | SC2 map names (e.g., "Catalyst LE", "Gresvan LE") |
| aoestats | (not in MHM) | `map` | 77 distinct AoE2 map names in 1v1 ranked scope |
| aoe2companion | (not in MHM) | `map` | 94 distinct AoE2 map names in 1v1 ranked scope |

SC2 and AoE2 map names are empirically disjoint. Any cross-game map encoder
trained on pooled rows will learn a nonsensical combined vocabulary. Encoding
MUST be within `dataset_tag` partition.

**(c) Leaderboard — asymmetric presence**

`leaderboard` is present in aoestats `player_history_all` and aoe2companion
`player_history_all` but absent from sc2egset `player_history_all`. This is not
a vocabulary-polymorphism case but has the same Phase 02 consequence: any join
or encoder involving `leaderboard` must branch on `dataset_tag`. Treating
absence as a null value in a cross-dataset encoder would be incorrect (sc2egset
has no leaderboard concept in its raw data).

### §4.3 Acceptable Encoding Patterns

The following patterns are I8-compliant:

- **(α) Per-game separate encoders:** fit and transform `OneHotEncoder` (or
  target encoder) called within a `dataset_tag` partition. No single encoder
  ever sees vocabulary from more than one game.
- **(β) Synthesized cross-game categorical:** e.g.,
  `faction_family := 'sc2_race' IF dataset_tag = 'sc2egset' ELSE 'aoe2_civ'`
  — used as a grouping column for cross-game comparisons at an abstracted level
  that does not conflate sc2 race stems with AoE2 civ names.
- **(γ) Game-conditional target encoding:** fit target-encoding statistics
  separately per `dataset_tag`, apply per-partition.

### §4.4 Spec-Maintenance Note

New cross-dataset polymorphic categoricals discovered during Phase 02 require a
spec amendment (see §7 change protocol). The list in §4.2 is exhaustive at the
time of Phase 01 exit; it is not a permanent closed list.

---

## §5 Column-Level Classification Summary

The tables below reproduce the authoritative classification tags from each VIEW
yaml. Phase 02 consumers MUST cite this section, not the source yamls directly,
to ensure a single versioned reference.

Tag vocabulary: `IDENTITY`, `CONTEXT`, `PRE_GAME`, `TARGET`,
`POST_GAME_HISTORICAL`, `IN_GAME_HISTORICAL`.

### §5.1 `matches_history_minimal` — sc2egset (9 cols)

| Column | Type | Classification | Notes |
|--------|------|----------------|-------|
| `match_id` | VARCHAR | IDENTITY | Prefixed `sc2egset::<32-hex-replay_id>` |
| `started_at` | TIMESTAMP | CONTEXT | I3 temporal anchor; TRY_CAST from details_timeUTC |
| `player_id` | VARCHAR | IDENTITY | Battle.net toon_id |
| `opponent_id` | VARCHAR | IDENTITY | Battle.net toon_id of opponent |
| `faction` | VARCHAR | PRE_GAME | 4-char race stems (Prot/Terr/Zerg/Rand); I8 polymorphic |
| `opponent_faction` | VARCHAR | PRE_GAME | Mirror of faction from opponent row |
| `won` | BOOLEAN | TARGET | TRUE = focal player won |
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL | DO NOT use as PRE_GAME feature (I3) |
| `dataset_tag` | VARCHAR | IDENTITY | Constant `'sc2egset'` |

### §5.2 `matches_history_minimal` — aoestats (10 cols; canonical_slot is aoestats-local)

| Column | Type | Classification | Notes |
|--------|------|----------------|-------|
| `match_id` | VARCHAR | IDENTITY | Prefixed `aoestats::<game_id>` |
| `started_at` | TIMESTAMP | CONTEXT | I3 temporal anchor; CAST from TIMESTAMPTZ AT TIME ZONE 'UTC' |
| `player_id` | VARCHAR | IDENTITY | CAST(p{0,1}_profile_id AS VARCHAR) |
| `opponent_id` | VARCHAR | IDENTITY | CAST of opponent profile_id |
| `faction` | VARCHAR | PRE_GAME | Full AoE2 civ names; I8 polymorphic |
| `opponent_faction` | VARCHAR | PRE_GAME | Mirror of faction from opponent row |
| `won` | BOOLEAN | TARGET | TRUE = focal player won; AVG(won::INT)=0.5 verified |
| `canonical_slot` | VARCHAR | PRE_GAME | aoestats-ONLY; slot_A/slot_B; hash-on-match_id; skill-orthogonal; NOT in MHM UNION ALL |
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL | DO NOT use as PRE_GAME feature (I3) |
| `dataset_tag` | VARCHAR | IDENTITY | Constant `'aoestats'` |

### §5.3 `matches_history_minimal` — aoe2companion (9 cols)

| Column | Type | Classification | Notes |
|--------|------|----------------|-------|
| `match_id` | VARCHAR | IDENTITY | Prefixed `aoe2companion::<decimal-matchId>` |
| `started_at` | TIMESTAMP | CONTEXT | I3 temporal anchor; pass-through from matches_raw.started |
| `player_id` | VARCHAR | IDENTITY | CAST(profileId AS VARCHAR) |
| `opponent_id` | VARCHAR | IDENTITY | CAST of opponent profileId |
| `faction` | VARCHAR | PRE_GAME | Full AoE2 civ names; zero NULLs; I8 polymorphic |
| `opponent_faction` | VARCHAR | PRE_GAME | Mirror of faction from opponent row; zero NULLs |
| `won` | BOOLEAN | TARGET | TRUE = focal player won; zero NULLs |
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL | DO NOT use as PRE_GAME feature (I3) |
| `dataset_tag` | VARCHAR | IDENTITY | Constant `'aoe2companion'` |

### §5.4 `player_history_all` — sc2egset (36 cols; abbreviated — key columns shown)

Full column list is in the source yaml. Key columns for Phase 02 feature
engineering:

| Column | Type | Classification | Notes |
|--------|------|----------------|-------|
| `replay_id` | VARCHAR | IDENTITY | Canonical join key |
| `toon_id` | VARCHAR | IDENTITY | I2 join key for player_history_all (raw; not harmonized) |
| `details_timeUTC` | VARCHAR | CONTEXT | I3 anchor (VARCHAR); use as `ph.details_timeUTC < target.started_at` |
| `race` | VARCHAR | PRE_GAME | Actual race played (Protoss/Zerg/Terran abbreviated) |
| `region` | VARCHAR | PRE_GAME | Battle.net region label |
| `isInClan` | BOOLEAN | PRE_GAME | Clan membership flag |
| `result` | VARCHAR | TARGET | Win/Loss/Undecided/Tie |
| `is_decisive_result` | BOOLEAN | POST_GAME_HISTORICAL | TRUE if Win or Loss |
| `metadata_mapName` | VARCHAR | PRE_GAME | Human-readable map name |
| `APM` | INTEGER | IN_GAME_HISTORICAL | Actions per minute; safe only as history aggregate filtered < T |
| `SQ` | INTEGER | IN_GAME_HISTORICAL | Spending Quotient; safe only as history aggregate filtered < T |
| `supplyCappedPercent` | INTEGER | IN_GAME_HISTORICAL | % supply-capped; safe only as history aggregate filtered < T |
| `header_elapsedGameLoops` | BIGINT | IN_GAME_HISTORICAL | Game duration in loops; safe only as history aggregate filtered < T |
| `is_mmr_missing` | BOOLEAN | PRE_GAME | TRUE if MMR=0 (unrated professional; MNAR) |

### §5.5 `player_history_all` — aoestats (14 cols)

| Column | Type | Classification | Notes |
|--------|------|----------------|-------|
| `profile_id` | BIGINT | IDENTITY | I2 join key (raw; CAST from DOUBLE verified in 01_04_02 schema migration) |
| `game_id` | VARCHAR | IDENTITY | Join key to matches_raw |
| `started_timestamp` | TIMESTAMPTZ | CONTEXT | I3 anchor; use as `ph.started_timestamp < target.started_at` |
| `leaderboard` | VARCHAR | CONTEXT | All game types; no restriction |
| `map` | VARCHAR | PRE_GAME | Map name; 77+ distinct in 1v1 scope |
| `patch` | BIGINT | CONTEXT | Game patch number |
| `civ` | VARCHAR | PRE_GAME | Civilization name; Phase 02 faction proficiency feature |
| `old_rating` | BIGINT | PRE_GAME | ELO before match; NULL=unrated (NULLIF 0 in 01_04_02) |
| `is_unrated` | BOOLEAN | PRE_GAME | TRUE if old_rating was 0 sentinel |
| `winner` | BOOLEAN | TARGET | Win outcome; retain for win-rate computation |
| `mirror` | BOOLEAN | PRE_GAME | Both players played same civ |

### §5.6 `player_history_all` — aoe2companion (19 cols; abbreviated — key columns shown)

| Column | Type | Classification | Notes |
|--------|------|----------------|-------|
| `profileId` | INTEGER | IDENTITY | I2 join key (raw; API-namespace; rename-stable) |
| `matchId` | INTEGER | IDENTITY | Match join key |
| `started` | TIMESTAMP | CONTEXT | I3 anchor; use as `ph.started < target.started_at` |
| `leaderboard` | VARCHAR | CONTEXT | 21 distinct values; all game types |
| `map` | VARCHAR | PRE_GAME | Map name (e.g., arabia, arena, black_forest); 94+ distinct |
| `civ` | VARCHAR | PRE_GAME | Civilization name; zero NULLs |
| `rating` | INTEGER | PRE_GAME | ELO entering match; ~39.63% NULL in full history |
| `gameMode` | VARCHAR | PRE_GAME | Game mode (random_map, empire_wars) |
| `won` | BOOLEAN | TARGET | Win outcome; ~0.0073% NULL from unranked leaderboards |
| `country` | VARCHAR | IDENTITY / CONTEXT | ISO 3166-1 alpha-2; ~8.30% NULL |
| `team` | INTEGER | CONTEXT | Team number; sentinel 255 exists |

---

## §6 Cross-Reference Table for Phase 02 Pipeline Sections

This table maps each of the 8 Phase 02 Pipeline Sections (per `docs/PHASES.md`)
to the expected input column sets and transformation types from this spec.
Column names are abstract — concrete feature names are defined in 02_08.

| Pipeline Section | Name | Input Views | Key Columns / Column Sets | Transformation Type |
|-----------------|------|-------------|--------------------------|---------------------|
| 02_01 | Pre-Game vs In-Game Boundary | `matches_history_minimal` (all datasets) | All PRE_GAME and CONTEXT columns from §5.1–§5.3; exclude POST_GAME_HISTORICAL and IN_GAME_HISTORICAL | Temporal boundary classification; tag propagation |
| 02_02 | Symmetry & Difference Features | `matches_history_minimal` (all datasets) | `player_id`, `opponent_id`, `faction`, `opponent_faction`, `won` | Pairwise difference construction; canonical `(focal, opponent)` assignment |
| 02_03 | Temporal Features, Windows, Decay, Cold Starts | `player_history_all` (all datasets) joined to `matches_history_minimal` via (player_id, `ph.<anchor>` < target.started_at) | Per-dataset anchor columns from §3.2; result/winner column; rating/ELO columns | Rolling window aggregation; EWMA; cold-start Bayesian smoothing |
| 02_04 | Feature Quality Assessment | Output of 02_01–02_03 | Candidate feature matrix | Cohen's d, mutual information, univariate AUROC per feature |
| 02_05 | Categorical Encoding | `matches_history_minimal` + `player_history_all` | `faction`/`race`/`civ`, `map`/`metadata_mapName`, `leaderboard` (per §4.2); encode within `dataset_tag` partition | Per-game encoders (§4.3 patterns α, β, or γ); unknown-category handling for map |
| 02_06 | Feature Selection | Output of 02_01–02_05 | All candidate features | Filter / wrapper / embedded selection methods |
| 02_07 | Rating Systems & Domain Features | `player_history_all` (all datasets) | `old_rating`/`rating` (PRE_GAME); `result`/`winner` (TARGET, history-filtered < T) | Elo/Glicko backcalculation; faction-proficiency rates within `dataset_tag` partition |
| 02_08 | Feature Documentation & Catalog | All output features from 02_01–02_07 | Full feature set | Provenance tagging; thesis-citable feature catalog |

---

## §7 Spec Change Protocol

Version strings follow the pattern `CROSS-02-00-vN.M.K`:

- **vN+1 (major):** any change to §2 column-grain commitments (VIEW names,
  row counts, column counts, schema_version values) or to the §4 encoding rule
  (general binding rule or explicitly-forbidden list). Requires full
  `planner-science` + `reviewer-adversarial` gate.
- **vN.M+1 (minor):** amendments to §4.2 known-instances list, §5 column
  classification table, §6 cross-reference table, or §8 referenced artifacts
  list — provided these do not alter §2 column-grain commitments or the §4
  general binding rule. Requires `planner-science` + `reviewer-adversarial`
  gate.
- **vN.M.K+1 (patch):** prose clarifications, typo corrections, added notes —
  provided no table cell values change. May be reviewed by `reviewer` (standard)
  only.

Any amendment requires an entry in the amendment log below. The `version` field
in the frontmatter MUST be bumped in the same commit as the amendment.

### Amendment Log

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| CROSS-02-00-v1 | 2026-04-21 | planner-science | Initial LOCKED version. Closes sc2egset WARNING 1, aoestats NOTE 3, sc2egset NOTE 4 from 2026-04-21 Phase 01 sign-off audits. |

---

## §8 Referenced Artifacts

### Invariants and Methodology

- `.claude/scientific-invariants.md` — invariants I2 (identity), I3 (temporal),
  I5 (symmetry), I8 (cross-game comparability). Binding for all Phase 02 work.
- `docs/PHASES.md` — canonical Phase 02 Pipeline Section enumeration
  (02_01–02_08); source of §6 table rows.
- `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` — Phase 02
  methodology source (§1–§10 map to 02_01–02_08).

### Pattern Reference

- `reports/specs/01_05_preregistration.md` — frontmatter and versioning-discipline
  pattern reference for this spec. Note: §1 of that spec lists a 9-column
  `matches_history_minimal` contract that is **stale** relative to current
  yamls (4 of 9 column names overlap: `match_id`, `started_at`, `player_id`,
  `won`; the other 5 — `team`, `chosen_civ_or_race`, `rating_pre`, `map_id`,
  `patch_id` — do not exist in current yamls). Column names in this spec
  (02_00) are derived exclusively from the current yamls.

### Phase 01 Decision Gate Artifacts (binding inputs to this spec)

- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_history_minimal.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/matches_history_minimal.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/player_history_all.yaml`
- `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md`
