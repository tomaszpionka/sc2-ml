---
category: E
branch: docs/phase02-interface-contract
date: 2026-04-21
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: null
invariants_touched: [I2, I3, I5, I8]
source_artifacts:
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_history_minimal.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/matches_1v1_clean.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/matches_history_minimal.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/player_history_all.yaml
  - reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md
  - reports/specs/01_05_preregistration.md
  - docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md
  - thesis/reviews_and_others/pass2_status.md
  - .claude/scientific-invariants.md
  - docs/PHASES.md
critique_required: true
research_log_ref: null
---

# Plan: WP-1 — Phase 01 → Phase 02 Interface Contract Spec

## Scope

This plan creates a single cross-dataset methodology spec that formalizes the interface between Phase 01 outputs and Phase 02 feature-engineering inputs. The spec names canonical input VIEWs per dataset, join keys, the I3 temporal anchor, the cross-game faction encoding protocol, and a column-level classification summary. It closes three Phase 01 sign-off audit findings (reviewer-adversarial sweep 2026-04-21):

- **sc2egset WARNING 1** — no explicit Phase-02-facing join/table-grain specification.
- **aoestats NOTE 3** — `player_history_all` structurally load-bearing but not formalized in interface docs.
- **sc2egset NOTE 4** — cross-game faction encoding protocol undefined.

Scope is intentionally tight: one new spec document + 4 cross-links + version bump. **Not** a Phase 02 architecture exercise — this spec describes Phase 02 **inputs**, not Phase 02 **decisions**. WP-2 through WP-5 (leakage-audit protocol, empirical quantifications, old_rating closure, 43-day gap provenance) are separate PRs.

## Problem Statement

The 3 reviewer-adversarial Phase 01 sign-off audits (2026-04-21) returned READY_WITH_CAVEATS across sc2egset / aoestats / aoe2companion. Zero BLOCKERs. A cross-cutting caveat: Phase 01 gate artifacts (`modeling_readiness_*.md` memos + `cross_dataset_phase01_rollup.md`) describe *what was done* in Phase 01 but do not formalize *what Phase 02 feature-engineering extractors consume*. The memos list permitted feature categories but do not enumerate:

- The canonical input VIEW names per dataset.
- The row grain (per-match vs per-player) each VIEW commits to.
- The join keys Phase 02 will use for rolling-window features.
- The I3 temporal anchor column each dataset commits to.
- The cross-game encoding protocol for polymorphic categoricals (`faction` is flagged as per-game polymorphic in the yamls but no artifact writes down the encoding rule).

Consequences if unaddressed before Phase 02 kickoff:

- Phase 02 `planner-science` reverse-engineers the Phase 01→02 interface from scattered yamls + research-log entries, producing a plan that may silently diverge per dataset.
- Three-dataset harmonization for RQ3 (cross-game comparison) risks divergent input assumptions; an examiner asking "which table feeds what for the cross-game feature engineering?" receives dataset-specific answers with no canonical source.
- The `faction` polymorphism flag in the yamls is non-binding — Phase 02 implementers could inadvertently encode faction as a single cross-game categorical, violating I8.

The `reports/specs/01_05_preregistration.md` spec provides the **frontmatter and versioning-discipline reference** for this kind of LOCKED spec (YAML frontmatter with spec_id + version + status, amendment log, change protocol). Its §1 column contract is dataset-specific and is NOT inherited here — the column lists in the new spec are derived from the current yamls exclusively (01_05 §1 pre-dates PR-TG3's 9-col harmonization + PR #185's canonical_slot addition, and only 4 of its 9 column names overlap with the current yamls). This plan produces `reports/specs/02_00_feature_input_contract.md` as the cross-dataset analog for Phase 02 input, using 01_05's structural pattern but NOT its column-content.

## Assumptions & unknowns

- **Assumption:** All three datasets have both `matches_history_minimal` and `player_history_all` yamls on disk (verified by Glob 2026-04-21 pre-planning — all 6 files exist). T01 re-verifies their column schemas.
- **Assumption:** The cross-dataset 9-col `matches_history_minimal` contract from PR-TG3 remains authoritative; aoestats's local 10-col extension (canonical_slot per PR #185) does not break UNION ALL projections when limited to the shared 9 columns.
- **Assumption (MHM anchor):** `started_at` (TIMESTAMP) is the canonical I3 temporal anchor in `matches_history_minimal` across all three datasets — confirmed by the Phase 01 leakage audits (`leakage_audit_*.json`) that used this column as the reference for past-only filtering.
- **Assumption (PH anchors are NOT canonical):** The corresponding temporal anchor in `player_history_all` has three different column names and two different dtypes across datasets: sc2egset `details_timeUTC` (VARCHAR), aoestats `started_timestamp` (TIMESTAMPTZ), aoe2companion `started` (TIMESTAMP). The spec MUST enumerate these per-dataset rather than prescribing a single SQL pattern that names `started_at` on `player_history_all`. An executor that writes `WHERE ph.started_at < target.started_at` against `player_history_all` produces a column-not-found error on 2 of 3 datasets.
- **Assumption (PH join keys are NOT harmonized):** `matches_history_minimal` exposes the harmonized `player_id`, but `player_history_all` exposes raw per-dataset IDs: sc2egset `toon_id`, aoestats `profile_id`, aoe2companion `profileId`. The spec MUST enumerate these per-dataset.
- **Assumption (cross-game polymorphism is NOT limited to `faction`):** At least three additional columns have per-dataset polymorphic vocabulary that Phase 02 will hit: `map`/`metadata_mapName` (sc2 map names vs aoe2 map names are empirically disjoint — 94 distinct aoec maps + 77 distinct aoestats maps + sc2 map names like "Catalyst LE"), `leaderboard` (aoestats + aoe2companion only; sc2egset has none — asymmetric presence), and the column-name asymmetry `civ` (aoestats/aoe2companion) vs `race` (sc2egset). §4 encoding protocol must declare a GENERAL rule covering any per-dataset polymorphic categorical, not just `faction`.
- **Unknown:** Whether the spec must also document how `canonical_slot` (aoestats-only) propagates to Phase 02 per-slot features. **Resolution:** in scope as §2 aoestats sub-section (with explicit "aoestats-only; sibling datasets do not require this key" note); does NOT require its own § in the spec.
- **Unknown:** Whether `dataset_tag` / `game` already exists as a column in `matches_history_minimal` or is computed on-demand during cross-dataset UNION. **Resolution:** T01 inspects the yamls. If absent, spec §4 prescribes it as a synthesized column for cross-game encoders.

## Literature context

Not applicable at thesis-citation level — this is an internal project methodology spec. Reference materials consulted:

- `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` §1–§2 (defines what Phase 02 consumes; scope-of-inputs for this spec).
- `.claude/scientific-invariants.md` (I3 temporal, I5 symmetry, I8 cross-dataset — the three invariants this spec operationalizes).
- `reports/specs/01_05_preregistration.md` (pattern reference: spec structure, version-locking discipline, frontmatter format).
- `docs/PHASES.md` §Phase 02 (the 8 Pipeline Sections — 02_01 through 02_08 — this spec supports).

## Execution Steps

### T01 — Inventory current-state VIEW schemas

**Objective:** Before drafting the spec, capture the authoritative column-level schema of the Phase 01 → Phase 02 input VIEWs across the three datasets. Flag any schema surprises that would require spec revision.

**Instructions:**
1. Read all 6 canonical yamls:
   - `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_history_minimal.yaml`
   - `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml`
   - `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml`
   - `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml`
   - `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/matches_history_minimal.yaml`
   - `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views/player_history_all.yaml`
2. For each, capture: (a) schema_version; (b) column count; (c) column list with classification tags (PRE_GAME / POST_GAME_HISTORICAL / CONTEXT / IDENTITY / TARGET); (d) row grain (per-match / per-player / 2-row-per-match).
3. Also read `matches_1v1_clean.yaml` for aoestats + aoe2companion (these are the cleaned tables preceding `matches_history_minimal`; not Phase 02 inputs themselves but necessary for the spec's §2 provenance chain).
4. Tabulate `matches_history_minimal` side-by-side (sc2egset 9 cols, aoestats 10 cols incl. canonical_slot, aoe2companion N cols — confirm N from yaml).
5. Verify all three `matches_history_minimal` share the same 9-col contract (the aoestats 10th col is additive, not substitutive).
6. **Column-set contrast:** tabulate `matches_history_minimal` column names vs `player_history_all` column names vs `reports/specs/01_05_preregistration.md §1` column list (all three sources). Flag that 01_05 §1 lists {match_id, started_at, player_id, team, chosen_civ_or_race, rating_pre, won, map_id, patch_id} — only 4 of these names (`match_id`, `started_at`, `player_id`, `won`) exist in the current `matches_history_minimal` yamls. 01_05 §1 is STALE relative to post-PR-TG3 and post-PR-#185 schemas. Executor MUST NOT inherit column names from 01_05 §1 into the new spec §2 or §5. All column names in the new spec derive from the yamls EXCLUSIVELY.
7. Identify temporal-anchor columns in `player_history_all` per dataset (sc2egset `details_timeUTC` VARCHAR, aoestats `started_timestamp` TIMESTAMPTZ, aoe2companion `started` TIMESTAMP) and join-key columns (sc2egset `toon_id`, aoestats `profile_id`, aoe2companion `profileId`). These are the per-dataset raw columns §3.2 of the new spec will enumerate.
8. If ANY yaml is missing or schema-unstable, HALT and report back to user; do NOT proceed to T02 silently.

**Verification:**
- Executor's working notes include a column-count tally for all 6 yamls.
- Side-by-side `matches_history_minimal` table comparison confirms the 9-col shared contract.
- Per-dataset `player_history_all` anchor + join-key columns enumerated (3 datasets × 2 columns = 6 entries).
- 01_05 §1 staleness explicitly flagged in executor's notes (not silently ignored).
- No missing files.

**File scope:** None (read-only; preparatory).
**Read scope:** (the 6 yamls + 2 `matches_1v1_clean.yaml` listed above).

---

### T02 — Draft `reports/specs/02_00_feature_input_contract.md`

**Objective:** Produce the cross-dataset Phase 02 input contract spec at `reports/specs/02_00_feature_input_contract.md`, following the `01_05_preregistration.md` pattern.

**Instructions:**
1. Create new file `reports/specs/02_00_feature_input_contract.md` with YAML frontmatter: `spec_id: 02_00`, `version: CROSS-02-00-v1`, `status: LOCKED`, `date: 2026-04-21`, `invariants_touched: [I2, I3, I5, I8]`, `supersedes: null`.
2. Write **§1 Scope and binding** — Which Phase 02 Pipeline Sections consume this spec. Per `docs/PHASES.md`, Phase 02 has 8 Pipeline Sections (02_01 through 02_08). This spec binds §2 column-grain commitments for all 8; §4 encoding protocol specifically binds 02_05 (Categorical Encoding) and 02_07 (Rating Systems & Domain Features) for the cross-game encoding rule. **I2 cross-branch binding note:** this spec prescribes a harmonized `player_id` join column in `matches_history_minimal` across three datasets whose I2 branch resolutions differ (sc2egset Branch iii region-scoped `toon_id`; aoestats Branch v structurally-forced `profile_id`; aoe2companion Branch i API-namespace `profileId`, per `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md:34`). Binding a shared join column atop three I2 branches is an I2-touching cross-dataset commitment; the harmonization happens inside the `matches_history_minimal` VIEW construction (not in this spec), and this spec merely names the harmonized column as the canonical Phase 02 join key on MHM. Raw I2-branch columns (`toon_id` / `profile_id` / `profileId`) are explicitly exposed in `player_history_all` and must be named per-dataset in §3 (next instruction).
3. Write **§2 Per-dataset canonical input VIEWs** — One sub-§ per dataset. Each sub-§ enumerates: (a) Primary VIEW for per-match features: `matches_history_minimal` (all three) with row count + column count + schema_version; (b) History VIEW for rolling-window features: `player_history_all` (all three) with row count + column count + schema_version; (c) aoestats-specific note: `canonical_slot` column present; aoestats-only; does not appear in sc2egset / aoe2companion. Populate from T01 tally.
4. Write **§3 Join keys and I3 temporal anchor — per-dataset mappings** — Declare separate mapping tables for the two VIEW classes (not a single SQL pattern; the column names differ between VIEWs and between datasets). **Sub-§3.1 `matches_history_minimal` (harmonized, cross-dataset canonical):** join key `player_id`; I3 temporal anchor `started_at` (TIMESTAMP); match key `match_id` (prefixed `<dataset_tag>::` — collision-safe cross-dataset); `dataset_tag` ∈ {sc2egset, aoestats, aoe2companion}. **Sub-§3.2 `player_history_all` (per-dataset raw; NOT harmonized at source):** table of per-dataset column mappings — sc2egset: `toon_id` (join) + `details_timeUTC` VARCHAR (anchor); aoestats: `profile_id` (join) + `started_timestamp` TIMESTAMPTZ (anchor); aoe2companion: `profileId` (join) + `started` TIMESTAMP (anchor). **Sub-§3.3 Rolling-window I3 guard:** every rolling-window query MUST apply `WHERE ph.<anchor_col> < target.started_at` (equality forbidden; the per-dataset anchor column comes from §3.2). Example SQL written in the spec MUST use placeholders (e.g., `ph.<anchor>`), not hard-code `started_at`, and the spec MUST explicitly caution executors that naive `SELECT * FROM player_history_all WHERE started_at < ...` will fail for 2 of 3 datasets. **Sub-§3.4 Cross-dataset player-history joins:** when UNION-ALL'ing player histories across datasets for cross-game analysis, composite key `(dataset_tag, player_id)` is required — bare `player_id` is per-dataset-scoped only; cross-dataset string-collision of raw IDs is structurally possible (sc2egset toon_id and aoec profileId occupy different namespaces but are both exposed as string/int at the application layer). The harmonization option is to wrap `player_history_all` in a Phase-02-owned canonicalizing VIEW per dataset that renames anchors + IDs to `started_at` + `player_id`; the spec should NAME this option but not prescribe it (Phase 02 picks at 02_01 kickoff).
5. Write **§4 Cross-game categorical encoding protocol (I8 compliance)** — Declare a GENERAL rule, then enumerate concrete instances. **General binding rule:** any column whose vocabulary is per-dataset (disjoint, non-interchangeable values across `dataset_tag` partitions) MUST be encoded within a `dataset_tag` partition. **Explicitly forbidden:** `GROUP BY <polymorphic_col>` or `OneHotEncoder(<polymorphic_col>)` across `dataset_tag` values; either pattern treats game-specific categoricals as shared vocabulary and violates I8. **Known instances of per-dataset polymorphic vocabulary (non-exhaustive):** (a) `faction`/`race`/`civ` — sc2egset ∈ {Prot, Terr, Zerg, Rand}, aoestats+aoe2companion ∈ {civ names, e.g., Britons, Franks, Persians, …}; note also the column-name asymmetry `race` (sc2egset) vs `civ` (aoe2 datasets); (b) `map` / `metadata_mapName` — sc2 map names (e.g., "Catalyst LE") vs aoe2 map names are empirically disjoint (94 distinct aoec maps, 77 distinct aoestats maps per `matches_1v1_clean.yaml`); (c) `leaderboard` — present in aoestats + aoe2companion, absent in sc2egset (asymmetric presence, not polymorphism, but same Phase 02 consequence: any join or encoder must branch on `dataset_tag`). **Acceptable patterns:** (α) per-game separate encoders with fit/transform called within a `dataset_tag` partition; (β) synthesized cross-game categorical (e.g., `faction_family := "sc2_race" if dataset_tag=sc2egset else "aoe2_civ"`) used as a grouping column; (γ) game-conditional target encoding. Reference: `.claude/scientific-invariants.md` I8. **Spec-maintenance note:** new cross-dataset polymorphic categoricals discovered during Phase 02 require a spec amendment (§7 change protocol).
6. Write **§5 Column-level classification summary** — For each canonical VIEW × dataset, reproduce the column-level classification (PRE_GAME / POST_GAME_HISTORICAL / CONTEXT / IDENTITY / TARGET) from the source yamls. This is the authoritative reference; Phase 02 consumers cite this §, not the scattered yamls. Use 3 tables (one per VIEW-type × dataset), each listing {column_name, type, classification, notes_if_any}.
7. Write **§6 Cross-reference table for Phase 02 Pipeline Sections** — For each of the 8 Pipeline Sections (02_01 … 02_08), name the expected input column set + transformation type. Source: `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` §1–§7. Example rows: `02_01 Pre-Game vs In-Game Boundary` ← all PRE_GAME columns from `matches_history_minimal`; `02_03 Temporal Features, Windows, Decay` ← `player_history_all` joined on `(player_id, started_at < T)`. Keep the table abstract — do NOT specify concrete feature names (those belong in 02_08 Feature Documentation & Catalog).
8. Write **§7 Spec change protocol** — Version bumps follow `01_05_preregistration.md` pattern: `CROSS-02-00-vN.M.K`. Any amendment requires `planner-science` + `reviewer-adversarial` gate; minor revisions that don't alter §2 column-grain commitments or §4 encoding rule are vN.M+1; any change to either is a major vN+1.
9. Write **§8 Referenced artifacts** — List `.claude/scientific-invariants.md`, `docs/PHASES.md`, `reports/specs/01_05_preregistration.md`, per-dataset yamls referenced in §2 and §5.

**Verification:**
- File exists at `reports/specs/02_00_feature_input_contract.md`.
- All 8 sections present.
- `grep "CROSS-02-00-v1"` across the repo returns exactly ONE match (this spec's frontmatter).
- §2 column counts match T01 yaml-derived counts for all three datasets.
- §4 explicitly states the cross-game encoding rule AND the I8 citation.
- §5 classification tags match source yamls (spot-check ≥1 column per VIEW-type × dataset).
- §6 enumerates all 8 Pipeline Sections.

**File scope:**
- `reports/specs/02_00_feature_input_contract.md` (Create)

**Read scope:**
- All yamls from T01 (6 files).
- `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md`
- `.claude/scientific-invariants.md`
- `docs/PHASES.md`
- `reports/specs/01_05_preregistration.md` (pattern reference)

---

### T03 — Backward-link the three `modeling_readiness_*.md` memos

**Objective:** Each of the three dataset-scoped `modeling_readiness_*.md` §5 paragraphs should cite the new spec as the formal Phase 02 input contract, so a Phase 02 executor reading the memo is redirected to the spec.

**Instructions:**
1. Edit `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md` §5 — append a sentence: "Phase 02 feature extractors bind to the cross-dataset `reports/specs/02_00_feature_input_contract.md §2` canonical input spec (version CROSS-02-00-v1, LOCKED 2026-04-21); this memo's scope ends at the Phase 01 output."
2. Same-shape edit to `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md` §5.
3. Same-shape edit to `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md` §5.

**Verification:**
- `grep -l "02_00_feature_input_contract.md" src/rts_predict/games/*/datasets/*/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_*.md` returns all 3 paths.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md` (Update)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md` (Update)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md` (Update)

**Read scope:**
- `reports/specs/02_00_feature_input_contract.md` (from T02)

---

### T04 — Link from `cross_dataset_phase01_rollup.md`

**Objective:** The cross-dataset Phase 01 rollup should reference the new spec as the Phase 02 Go/No-Go input binding across all three datasets.

**Instructions:**
1. Read `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` to locate the appropriate section for the reference (likely §4 or §5 "Phase 02 Go/No-Go" or equivalent; if absent, create such a subsection).
2. Add reference text: "**Phase 02 input binding:** `reports/specs/02_00_feature_input_contract.md` (LOCKED CROSS-02-00-v1, 2026-04-21) is the canonical input contract across all three datasets. Phase 02 feature-engineering execution reads this spec as the authoritative source for input VIEW names, row grain, join keys, I3 temporal anchor, cross-game categorical encoding protocol, and column-level classification. Amendments follow the §7 change protocol."

**Verification:**
- `grep "02_00_feature_input_contract.md" reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` returns ≥1 match.

**File scope:**
- `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` (Update)

**Read scope:**
- `reports/specs/02_00_feature_input_contract.md` (from T02)

---

### T05 — Refresh `cross_dataset_phase01_rollup.md` stale GO-NARROW text

**Objective:** `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md:15` still says aoestats "**GO-NARROW** (aggregate / UNION-ALL-symmetric features; per-slot deferred until F1+W4)" — text that became stale 2026-04-20 when canonical_slot landed via PR #185 (BACKLOG F1+W4). Since T04 adds a new backlink to this same file, it would be thesis-defensibility liability to leave contradictory text next to the new content. Refresh it in the same PR.

**Instructions:**
1. Edit `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` — locate the aoestats GO-NARROW line (around line 15 per 2026-04-21 inspection; verify exact line at execution time).
2. Change "**GO-NARROW** (aggregate / UNION-ALL-symmetric features; per-slot deferred until F1+W4)" to "**GO-FULL** (per-slot features invariant-safe after canonical_slot amendment landed 2026-04-20 per PR #185 / BACKLOG F1+W4; see `modeling_readiness_aoestats.md §1 + §6`)."
3. Verify no other rollup statements still reference "per-slot deferred" or "F1+W4 pending" for aoestats (if found, update or flag).

**Verification:**
- `grep "GO-NARROW" reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` returns zero aoestats hits.
- `grep "GO-FULL" reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` returns the updated aoestats line.

**File scope:**
- `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` (Update — combined with T04 edit; both edits land in the same file touch)

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md`

---

### T06 — Version bump + CHANGELOG

**Objective:** Version 3.38.1 → 3.39.0 (minor bump for docs, per `.claude/rules/git-workflow.md`), CHANGELOG entry populated.

**Instructions:**
1. Edit `pyproject.toml`: `version = "3.38.1"` → `version = "3.39.0"`.
2. Edit `CHANGELOG.md`: move `[Unreleased]` contents (empty) aside; add new `[3.39.0] — 2026-04-21 (PR #TBD: docs/phase02-interface-contract)` block with:
   - `### Added`: "Cross-dataset Phase 02 feature-engineering input contract at `reports/specs/02_00_feature_input_contract.md` (version CROSS-02-00-v1, LOCKED). Closes sc2egset WARNING 1, aoestats NOTE 3, sc2egset NOTE 4 from the 2026-04-21 Phase 01 sign-off audits. Spec covers: per-dataset canonical input VIEWs + row grain; join keys + I3 temporal anchor; cross-game categorical encoding protocol (I8 compliance); column-level classification summary; Phase 02 Pipeline Section cross-reference."
   - `### Changed`: edits to 3 `modeling_readiness_*.md` memos + `cross_dataset_phase01_rollup.md` back-linking the new spec; `cross_dataset_phase01_rollup.md` aoestats GO-NARROW → GO-FULL refresh (stale since PR #185 canonical_slot landing 2026-04-20).
3. Reset `[Unreleased]` to empty with `### Added / Changed / Fixed / Removed` headers.

**Verification:**
- `grep '^version' pyproject.toml` returns `version = "3.39.0"`.
- `CHANGELOG.md` `[3.39.0]` block populated; `[Unreleased]` reset empty.

**File scope:**
- `pyproject.toml` (Update)
- `CHANGELOG.md` (Update)

**Read scope:** None.

---

## File Manifest

| File | Action |
|------|--------|
| `reports/specs/02_00_feature_input_contract.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md` | Update |
| `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` | Update |
| `pyproject.toml` | Update |
| `CHANGELOG.md` | Update |
| `planning/current_plan.md` | (this plan; tracked separately from git-diff manifest) |
| `planning/current_plan.critique.md` | (produced by reviewer-adversarial Mode A before execution) |

7 git-diff-scope files + 2 planning-meta files. Note: `cross_dataset_phase01_rollup.md` receives TWO edits (T04 new backlink + T05 GO-NARROW→GO-FULL refresh) — still one file in the manifest.

## Gate Condition

- `reports/specs/02_00_feature_input_contract.md` exists at `CROSS-02-00-v1` LOCKED with all 8 sections populated and column-counts verified against T01 yaml tally.
- All three `modeling_readiness_*.md` memos §5 carry the back-reference sentence with the exact spec path and version string.
- `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` cites the new spec as the Phase 02 input binding AND its aoestats status reads GO-FULL (not GO-NARROW; refreshed per T05).
- `pyproject.toml` `version = "3.39.0"`.
- `CHANGELOG.md` `[3.39.0]` populated; `[Unreleased]` reset.
- All three `PHASE_STATUS.yaml` files UNCHANGED (Phase 01 remains `complete`; this PR does not alter Phase 01 exit state, only formalizes the Phase 01→02 interface).
- `planning/current_plan.critique.md` filed by reviewer-adversarial Mode A before execution; user reviews and approves.
- `git diff --stat` on the final commit touches exactly the 7 files in the File Manifest (plus `planning/current_plan.md` + `planning/current_plan.critique.md` which are excluded from git-diff-scope gates).

## Out of scope

- **WP-2 (leakage audit protocol)** — separate sibling spec `reports/specs/02_01_leakage_audit_protocol.md` in a follow-up PR (`docs/phase02-leakage-audit-protocol`). Planner-science recommended this separation; adversarial critique may revisit.
- **WP-3 (sc2egset cross-region empirical quantification)** — separate Cat A PR with its own notebook + artifact; not coupled to this spec.
- **WP-4 (aoestats `old_rating` PRE-GAME closure)** — separate Cat D PR.
- **WP-5 (aoestats 43-day gap provenance)** — separate Cat C or A PR; direction (retract vs derive) decided at execution-time via grep over thesis+reports+planning.
- **Feature naming conventions** for Phase 02 — belongs in Pipeline Section 02_08 (Feature Documentation & Catalog), NOT in this input spec. Explicitly deferred.
- **Phase 02 architectural decisions** (which classifiers, which splits, HPO strategy, etc.) — that is the Phase 02 kickoff `planner-science` session, a separate deliverable.
- **Updates to `docs/PHASES.md` Phase 02 Pipeline Section enumeration** — not touched; this spec consumes the existing 8-section enumeration as authoritative.
- **Changes to any VIEW schema yaml** — the spec *describes* current schemas; it does not propose changes to them. Any schema change requires a separate feat PR that also amends this spec with a version bump.

## Open questions

- **Q1: Does the spec's §6 Phase 02 Pipeline Section cross-reference need to enumerate concrete feature examples (e.g., `rolling_win_rate_30d`), or stay abstract?** — Recommendation: stay abstract; concrete feature names belong in 02_08. Resolves now (T02 instruction 7 enforces abstract).
- **Q2: Should the `dataset_tag` column be formally added to every `matches_history_minimal` VIEW, or synthesized at UNION-ALL time?** — Resolves during T01. If already present in all 3 yamls: spec §3 names it as a canonical column. If absent: spec §3 prescribes it as synthesized during cross-dataset UNION; does NOT modify the VIEWs (that's a future schema-bump PR).
- **Q3: Is there an existing aoestats-only column (canonical_slot) that the spec should flag as "breaks the cross-dataset UNION contract"?** — Yes; spec §2 aoestats sub-§ notes that canonical_slot is aoestats-local; cross-dataset UNION queries MUST project the shared 9-col subset. This instruction is already baked into T02 step 3.

## Dispatch sequence

1. This plan written at `planning/current_plan.md`.
2. `reviewer-adversarial` Mode A invoked against this plan 2026-04-21 — `planning/current_plan.critique.md` filed with verdict REVISE (2 BLOCKERs on §3 column names, 2 WARNINGs on 01_05 staleness + §4 scope, 3 NOTEs on I2 / composite key / rollup GO-NARROW staleness). **Revision round applied 2026-04-21:** all 8 required revisions addressed in this plan (frontmatter I2 added; Problem Statement 01_05 "pattern to follow" language removed; Assumptions block split into 4 explicit per-dataset assumptions; T01 column-contrast + per-dataset anchor sub-step added; T02 §1 I2 cross-branch-binding note added; §3 rewritten with per-dataset sub-sections 3.1/3.2/3.3/3.4 including composite-key clause; §4 generalized with map/race-civ/leaderboard instances; new T05 added for rollup GO-NARROW→GO-FULL refresh; T01–T05 sequence renumbered to T01–T06). Symmetric 1-revision cap consumed; execution may proceed.
3. (Skipped for Cat E unless adversarial flagged issues): `/critic` skill. User indicated direct adversarial is sufficient.
4. Executor dispatched against this plan with T01–T06.
5. `reviewer` (standard) post-execution review (Category E default).
6. Pre-commit validation (ruff / mypy N/A; planning-drift passes since plan present).
7. Commit + PR + merge per standard workflow.
8. Post-merge purge of `planning/current_plan.md` + `planning/current_plan.critique.md` by the next plan overwriting them (next plan = WP-2 or Phase 02 kickoff, per user direction).
