---
category: E
branch: docs/phase02-leakage-audit-protocol
date: 2026-04-21
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: null
invariants_touched: [I3, I9]
source_artifacts:
  - reports/specs/02_00_feature_input_contract.md
  - reports/specs/01_05_preregistration.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/leakage_audit_sc2egset.json
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_leakage_audit.json
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md
  - docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md
  - .claude/scientific-invariants.md
  - thesis/reviews_and_others/pass2_status.md
critique_required: true
research_log_ref: null
---

# Plan: WP-2 — Mandatory Pre-Training Leakage Audit Protocol Spec (REVISED 2026-04-21 post Mode A)

## Scope

Create a sibling methodology spec to WP-1's `02_00_feature_input_contract.md` that formalizes a mandatory pre-training temporal leakage audit for Phase 02. Closes the sc2egset Phase 01 sign-off finding (WARNING 2 per 2026-04-21 reviewer-adversarial agent `af5c57132779f1103` output, consolidated into a new on-disk artifact by T02 below): "no mandated Phase 02 pre-training leakage-audit protocol at the Phase 01 gate." The spec binds Pipeline Section 02_01 (Pre-Game vs In-Game Boundary) as a hard gate.

Scope: one new Phase 01 audit summary artifact (creating durable on-disk traceability for the 2026-04-21 adversarial sweep; satisfies I9 for WP-2 + downstream WP-3/WP-4/WP-5) + one new spec + 3 ROADMAP placeholder amendments + version bump + CHANGELOG. **Not** a Phase 02 architecture exercise and **not** a rewrite of WP-1's input contract spec.

**Post-Mode-A revision summary (2026-04-21):** Mode A adversarial critique surfaced 2 BLOCKERs + 2 WARNINGs + 2 NOTEs. Revisions applied: (1) Assumption 2 corrected to acknowledge aoestats Phase 01 audit is MD (not JSON); T01 updated with format-asymmetry handling + Q7.x ↔ JSON field equivalences. (2) NEW T02 added to create Phase 01 audit summary artifact — establishes I9 traceability before the spec cites "WARNING 2"; existing T02–T04 renumbered to T03–T05. (3) T03 verification grep scoped to frontmatter. (4) Spec §5 gate-enforcement language clarified to convention-based v1 with tooling-enforcement as §7 future-amendment target. (5) NOTE 6 applied: spec §2.2 acknowledges lineage-resolution implementation-dependency limitation. (NOTE 5 spec_id/version field collapse deferred to a future spec-versioning-convention chore that standardizes both WP-1 and WP-2 frontmatter.) Symmetric 1-revision cap consumed.

## Problem Statement

Phase 01 produced per-dataset leakage audits that confirmed zero future-leakage at the VIEW level. These audits are structurally correct for Phase 01 but **cannot verify Phase 02 rolling-window feature code** — Phase 01 audits the schema that Phase 02 consumes, not the features Phase 02 computes.

Consequences if unaddressed before Phase 02 kickoff:

- Phase 02 feature extractors may compute rolling-window win-rate / match-count / Elo features using `WHERE ph.<anchor> <= target.started_at` (equality-inclusive) instead of strict `<` required by I3. No gate catches this.
- Normalization statistics (mean, std, min, max) fit on the full dataset rather than training folds introduces future-into-past leakage invisible at schema level.
- Target encoding (K-fold target-encoded categoricals) fit without fold-aware masking leaks the target into training features.
- Examiner asks: "How do you verify Phase 02 feature code is leakage-free?" The Phase 01 audits are the current answer; they are structurally inadequate.

The `reports/specs/02_00_feature_input_contract.md` (WP-1, landed PR #198, version CROSS-02-00-v1 LOCKED) provides the input-side binding. This plan produces the verification-side sibling: `reports/specs/02_01_leakage_audit_protocol.md` (version CROSS-02-01-v1, LOCKED). Both specs together define the Phase 01 → Phase 02 contract: WP-1 names what Phase 02 reads; WP-2 names what Phase 02 must verify before training.

Additionally, WP-2 closes a traceability gap surfaced by Mode A: the 2026-04-21 reviewer-adversarial Phase 01 sign-off findings (3 dataset verdicts, 5 WARNINGs, 9 NOTEs) were generated as agent output + chat summaries but never committed as repo artifacts. T02 below produces a consolidated summary artifact so WP-2, WP-3, WP-4, WP-5 all cite a durable on-disk source (I9 compliance).

## Assumptions & unknowns

- **Assumption (WP-1 landed and stable):** `reports/specs/02_00_feature_input_contract.md` exists at `CROSS-02-00-v1` LOCKED per PR #198 merge. Verified via `git log master -- reports/specs/02_00_feature_input_contract.md`.
- **Assumption (Phase 01 leakage audit artifacts have HETEROGENEOUS formats):** sc2egset carries `leakage_audit_sc2egset.json` (JSON with `future_leak_count`, `post_game_token_violations`, `reference_window_assertion`); aoe2companion carries `01_05_08_leakage_audit.json` (same JSON schema); aoestats carries `01_05_06_temporal_leakage_audit_v1.md` (Markdown, NOT JSON; uses Q7.1–Q7.4 section headers). T01 handles this asymmetry with explicit field equivalences: Q7.1 → `future_leak_count`, Q7.2 → `post_game_token_violations`, Q7.3 → `reference_window_assertion` (Q7.4 is canonical_slot readiness, not a Phase 02 template field).
- **Assumption (Phase 02 Pipeline Section numbering is stable):** `docs/PHASES.md` §Phase 02 lists 8 Pipeline Sections (02_01 through 02_08). This plan binds the audit gate to 02_01 exit. No renumbering expected.
- **Assumption (pass2_status.md is the interim audit-finding registry):** `thesis/reviews_and_others/pass2_status.md` (updated PR #196) references the 2026-04-21 Phase 01 audits at high level but does not enumerate W-codes. T02 below creates the formal audit artifact; pass2_status.md back-references it after this PR merges (follow-up task, not in WP-2 scope).
- **Unknown:** Whether the audit should also cover Phase 02 Pipeline Sections 02_03 and 02_06. **Resolution:** spec §1 binds 02_01 as the mandatory hard gate; §6 documents that 02_03 and 02_06 REUSE the protocol if they materialize new features; not a second gate — a protocol reuse rule.
- **Unknown:** Whether Phase 02 planner-science will implement the audit as Python module + CLI, or as spec-only document with per-step manual execution. **Resolution:** this spec prescribes the PROTOCOL + ARTIFACT SCHEMA; the IMPLEMENTATION is a Phase 02 architecture decision, explicitly out of WP-2 scope. Spec §5 explicitly notes that v1 enforcement is convention-based + reviewer-gated (not automated tooling); §7 prescribes tooling enforcement as a future-amendment target.

## Literature context

Not applicable at thesis-citation level — internal methodology spec. References:

- `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` §2 (cutoff-time mechanism this audit verifies).
- `.claude/scientific-invariants.md` I3 (temporal), I9 (traceability — the new audit summary artifact satisfies I9 for the 2026-04-21 findings).
- `reports/specs/02_00_feature_input_contract.md` (WP-1 sibling spec; cited at §1 and §8).
- `reports/specs/01_05_preregistration.md` (frontmatter + versioning-discipline reference).
- Existing Phase 01 leakage audits (sc2egset + aoe2companion JSON; aoestats MD): template for the Phase 02 audit artifact schema.

## Execution Steps

### T01 — Inventory Phase 01 leakage-audit artifacts (HETEROGENEOUS formats)

**Objective:** Read the three Phase 01 leakage-audit artifacts and capture their schemas, handling the format asymmetry (2 JSON + 1 MD). Derive the Phase-02 baseline template fields.

**Instructions:**
1. Read `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/leakage_audit_sc2egset.json` — note JSON schema.
2. Read `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_leakage_audit.json` — note JSON schema.
3. Read `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.md` — note its Q7.1–Q7.4 section structure.
4. **Format-asymmetry handling:** Two JSON artifacts + one MD artifact. Define semantic equivalences explicitly: Q7.1 (aoestats MD) ↔ `future_leak_count` (sc2egset + aoe2companion JSON); Q7.2 ↔ `post_game_token_violations`; Q7.3 ↔ `reference_window_assertion`. Q7.4 is canonical_slot readiness — aoestats-specific; not part of the Phase 02 template baseline.
5. Tabulate the baseline template (intersection of 3 artifacts, using the Q7.x ↔ JSON-field mappings): 3 shared dimensions (`future_leak_count`, `post_game_token_violations`, `reference_window_assertion`) form the Phase-02-audit baseline.
6. Enumerate the Phase-02-specific audit dimensions the new spec must add: (a) cutoff-time structural check (strict `<` vs `<=`); (b) normalization fit-scope (training-fold only); (c) target-encoding fold-awareness (K-fold masked); (d) features-audited column list.

**Verification:**
- Executor notes a side-by-side field matrix across the 3 Phase 01 artifacts with Q7.x ↔ JSON-field mappings explicit.
- 4 Phase-02-specific audit dimensions enumerated in executor's notes.

**File scope:** None (read-only).
**Read scope:** (3 artifacts listed above).

---

### T02 — Create Phase 01 audit summary artifact (on-disk traceability)

**Objective:** Establish a durable on-disk referent for the 2026-04-21 reviewer-adversarial Phase 01 sign-off audits. The 3 agent outputs (sc2egset, aoestats, aoe2companion sign-off verdicts with WARNING/NOTE enumerations) live only in chat transcripts and pass2_status.md references today. This new artifact makes them traceable for WP-2 (closes WARNING 2) and downstream WP-3/WP-4/WP-5 which cite other findings.

**Instructions:**
1. Create new file `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md`.
2. Write the artifact with four sections:
   - **§1 Scope and method** — Summarize the adversarial Phase 01 sign-off sweep: date 2026-04-21, 3 reviewer-adversarial Sonnet agent dispatches (one per dataset), lens scope (Phase 01 completeness / decision gate quality / Phase 02 input readiness / invariant compliance / temporal leakage / research-log consistency / cross-dataset schema readiness). Verdicts across all 3: READY_WITH_CAVEATS; zero BLOCKERs.
   - **§2 sc2egset findings** — Enumerate verdict tier, findings list, remediation map. WARNINGs: W1 (no explicit Phase-02-facing join/table-grain specification — closed by WP-1 PR #198), W2 (no mandated Phase 02 pre-training leakage-audit protocol — closed by THIS PR, WP-2), W3 (~12% cross-region history fragmentation unquantified — scheduled WP-3). NOTEs: N1 (cross-game faction encoding protocol undefined — closed by WP-1 PR #198 as §4), N2 (`reports/research_log.md` index stale dates for sc2egset — closed by PR #197).
   - **§3 aoestats findings** — WARNINGs: W1 (`data_quality_report_aoestats.md:52` stale 9-col claim — closed by PR #197), W2 (`old_rating` PRE-GAME classification deferred empirical test — scheduled WP-4). NOTEs: N1 (`player_history_all` interface documentation gap — closed by WP-1 PR #198 as §3.2), N2 ("43-day post-patch gap" figure no artifact provenance — scheduled WP-5), N3 (Q7.4 FAILED sub-check not amended post-BACKLOG F6 — closed by PR #197).
   - **§4 aoe2companion findings** — NOTEs only (zero WARNINGs): N1 (LPM ICC value discrepancy 0.000485 vs 0.000491 — closed by PR #197), N2 (I8 cross-dataset ICC spec v1.0.2 AT RISK — closed by PR #197 AC-R06), N3 (`cross_dataset_phase01_rollup.md` path ambiguity — closed by PR #197), N4 (absolute paths in `01_05_05_icc.json` — closed by PR #197).
3. Include frontmatter: `audit_date: 2026-04-21`, `auditor: reviewer-adversarial (Sonnet)`, `datasets: [sc2egset, aoestats, aoe2companion]`, `verdict_tier: READY_WITH_CAVEATS (all 3)`, `consolidation_date: 2026-04-21`, `supersedes: null`.
4. Add a closing §5 "Finding closure status table" cross-referencing each finding → the PR that closed it (or WP that will close it).
5. Do NOT reproduce the full verbatim agent transcripts — this is a summary artifact, not a full audit log. Capture the structural findings with enough detail that future agents/examiners can understand the finding, its severity, and its closure path.

**Verification:**
- File exists at `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md`.
- All 3 datasets' findings enumerated (at minimum: 5 WARNINGs + 9 NOTEs + 3 verdicts).
- Each finding cross-referenced to its closing PR/WP.
- Frontmatter present with all prescribed fields.

**File scope:**
- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` (Create)

**Read scope:**
- `thesis/reviews_and_others/pass2_status.md` (interim finding registry).

---

### T03 — Draft `reports/specs/02_01_leakage_audit_protocol.md`

**Objective:** Produce the sibling methodology spec following the WP-1 spec pattern (versioned, LOCKED, YAML frontmatter, sectioned).

**Instructions:**
1. Create new file `reports/specs/02_01_leakage_audit_protocol.md` with YAML frontmatter: `spec_id: CROSS-02-01-v1`, `version: CROSS-02-01-v1`, `status: LOCKED`, `date: 2026-04-21`, `invariants_touched: [I3]`, `supersedes: null`, `datasets_bound: [sc2egset, aoestats, aoe2companion]`, `sibling_specs: [CROSS-02-00-v1]`, `closes_finding: "sc2egset WARNING 2 per reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §2"`.
2. Write **§1 Scope and binding** — Hard gate for Pipeline Section 02_01 (Pre-Game vs In-Game Boundary): no step in 02_01 may exit without the audit artifact committed. REUSED (not re-gated) by 02_03 (Temporal Features, Windows, Decay, Cold Starts) and 02_06 (Feature Selection) whenever they materialize new features — protocol re-run produces new audit artifact; gate scoped to 02_01 exit. Cite WP-1 sibling spec `CROSS-02-00-v1` as the input contract this audit presupposes. Cite `phase01_audit_summary_2026-04-21.md §2` (sc2egset WARNING 2) as the closed finding.
3. Write **§2 What is audited** — Four dimensions:
   - **§2.1 Cutoff-time structural check:** Every Phase 02 feature-generating SQL/Python expression that reads `player_history_all` MUST apply `WHERE ph.<anchor_col> < target.started_at` (per WP-1 §3.3; anchor column per-dataset per WP-1 §3.2). Equality (`<=`) is forbidden. Audit asserts: (a) filtered scope; (b) `<` operator; (c) per-dataset anchor column (not canonical `started_at`).
   - **§2.2 POST-GAME token absence:** Every materialized feature column's source lineage must not include POST_GAME_HISTORICAL, IN_GAME_HISTORICAL, or TARGET columns per WP-1 §5 classification. Audit: source-column lineage resolution via SQL AST walk (for SQL views) or Python docstring trace (for notebook code). **Implementation-dependency limitation:** lineage-resolution mechanism is implementer's choice; for cascading VIEWs without AST-walk tooling and for Python code without docstring conventions, audit rigor depends on manual review. Phase 02 planner-science must either (a) author a lineage-resolution script, OR (b) restrict Phase 02 feature materialization to a set of patterns where manual review is feasible.
   - **§2.3 Normalization fit-scope:** Any scaling / normalization (mean, std, min, max, quantile) or K-fold target-encoding statistic MUST be fit on training folds only. Audit: for scikit-learn `Pipeline` steps, assert `fit` called with training-fold data only; for manual encoding code, assert fold-mask discipline via code review.
   - **§2.4 Reference-window assertion (reused from Phase 01):** The temporal window used for feature computation must match the training window of the model. Audit asserts training-fold start/end timestamps match feature-computation window.
4. Write **§3 Audit artifact schema** — Phase 02 audit runs MUST produce `reports/artifacts/02_*/leakage_audit_<dataset>.json`. Fields: `spec_version` (CROSS-02-01-v1), `dataset` (∈ {sc2egset, aoestats, aoe2companion}), `phase_02_step` (e.g., `02_01_01`), `audit_date` (ISO), `future_leak_count` (int; 0 required for pass), `post_game_token_violations` (int; 0 required for pass), `normalization_fit_scope` (string; "training_fold_only" required for pass), `target_encoding_fold_awareness` (string; "K_fold_masked" required for pass or "N/A_no_target_encoding"), `cutoff_time_filter_structural_check` (string; "pass" required), `reference_window_assertion` (string; "pass" required), `features_audited` (list of column names), `verdict` (string; "PASS" required for 02_01 exit). Sibling Markdown report (`.md`, same base name) narrates the audit with SQL verbatim per I6.
5. Write **§4 Execution timing** — Audit runs AFTER every Phase 02 feature materialization, BEFORE any training. "Materialization" = any step that persists a new feature column to DuckDB or Parquet consumed by the training pipeline.
6. Write **§5 Gate condition (v1 enforcement: convention-based)** — Pipeline Section 02_01 exit requires: (a) every feature materialized in 02_01 appears in `features_audited`; (b) `verdict = "PASS"`; (c) artifact JSON + MD both present at the prescribed path. Missing audit OR verdict != PASS blocks 02_01 exit. **v1 ENFORCEMENT MECHANISM:** convention-based — no CI check, pre-commit hook, or gate script in the current toolchain reads the JSON and fails commits on `verdict != PASS`. Enforcement is (i) the reviewer-adversarial mandatory review gate before any 02_01 exit PR is merged, and (ii) this spec's convention. See §7 for the tooling-enforcement follow-up target.
7. Write **§6 Scope reuse by 02_03 and 02_06** — When 02_03 materializes new rolling-window features or 02_06 materializes new feature-selection outputs, re-run the protocol and produce a new audit artifact (same schema). Not a re-gate (02_03 and 02_06 have their own Pipeline Section exit gates; this protocol is reused inside them).
8. Write **§7 Spec change protocol** — Version bumps follow WP-1 pattern: `CROSS-02-01-vN.M.K`. Any amendment requires `planner-science` + `reviewer-adversarial` gate. Any change to §2 audit dimensions or §5 gate condition is a major vN+1. **Future-amendment target:** v2 should add CI/pre-commit tooling enforcement of §5 gate (reads JSON, fails commits on `verdict != PASS`); scheduled as a follow-up chore after initial Phase 02 execution validates the audit schema. Noted here as the top-priority §7 amendment.
9. Write **§8 Referenced artifacts** — List `.claude/scientific-invariants.md` I3, `docs/PHASES.md` §Phase 02, `reports/specs/02_00_feature_input_contract.md` (sibling), `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` (closes sc2egset WARNING 2 per §2), `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` §2, and the three Phase 01 leakage-audit artifacts (template references).

**Verification:**
- File exists at `reports/specs/02_01_leakage_audit_protocol.md`.
- All 8 sections present.
- `grep "^spec_id: CROSS-02-01-v1" reports/specs/02_01_leakage_audit_protocol.md` returns exactly ONE match (frontmatter-scoped).
- §3 audit artifact schema lists the required JSON fields verbatim.
- §5 gate condition explicitly states "verdict = PASS" required for 02_01 exit AND acknowledges v1 convention-based enforcement.
- §7 explicitly names tooling-enforcement as future-amendment target.
- §1 cites both CROSS-02-00-v1 (sibling) AND `phase01_audit_summary_2026-04-21.md §2` (closed finding).

**File scope:**
- `reports/specs/02_01_leakage_audit_protocol.md` (Create)

**Read scope:**
- 3 Phase 01 leakage-audit artifacts (from T01).
- `reports/specs/02_00_feature_input_contract.md` (WP-1 sibling).
- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` (from T02).
- `.claude/scientific-invariants.md`, `docs/PHASES.md`, `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md`.

---

### T04 — Amend three dataset ROADMAPs' Phase 02 placeholder sections

**Objective:** Each dataset ROADMAP has `## Phase 02 — Feature Engineering (placeholder)`. Add a one-paragraph mandatory-entry note citing the WP-2 spec as hard gate for Pipeline Section 02_01 exit.

**Instructions:**
1. Edit `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` — locate `## Phase 02 — Feature Engineering (placeholder)` (around line 1718); after existing two-line content, append: "\n\n**Mandatory entry requirement (added 2026-04-21 per WP-2):** Before any step in Pipeline Section 02_01 exits, a leakage-audit artifact must be produced per `reports/specs/02_01_leakage_audit_protocol.md` (CROSS-02-01-v1, LOCKED 2026-04-21). The audit verifies cutoff-time structural filters, POST-GAME token absence from feature lineage, normalization fit-scope, and reference-window assertion. `verdict = PASS` is required for 02_01 exit. v1 enforcement is convention-based (reviewer-adversarial gate); automated tooling enforcement is a §7 future-amendment target. Input contract: `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v1). Protocol is reused (not re-gated) by 02_03 and 02_06."
2. Same-shape edit to `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` (around line 1684).
3. Same-shape edit to `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` (around line 1412).

**Verification:**
- `grep -l "02_01_leakage_audit_protocol.md" src/rts_predict/games/*/datasets/*/reports/ROADMAP.md` returns all 3 paths.
- Each ROADMAP's Phase 02 placeholder now enumerates the mandatory-entry requirement.

**File scope:**
- sc2egset `ROADMAP.md` (Update)
- aoestats `ROADMAP.md` (Update)
- aoe2companion `ROADMAP.md` (Update)

**Read scope:**
- `reports/specs/02_01_leakage_audit_protocol.md` (from T03)

---

### T05 — Version bump + CHANGELOG

**Objective:** Version 3.39.0 → 3.40.0 (minor, docs). CHANGELOG entry.

**Instructions:**
1. Edit `pyproject.toml`: `version = "3.39.0"` → `version = "3.40.0"`.
2. Edit `CHANGELOG.md`: move `[Unreleased]` contents aside; add new `[3.40.0] — 2026-04-21 (PR #TBD: docs/phase02-leakage-audit-protocol)`:
   - `### Added`: Phase 01 audit summary artifact at `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` (on-disk traceability for 2026-04-21 reviewer-adversarial sign-off sweep; referenced by WP-2/WP-3/WP-4/WP-5). Cross-dataset Phase 02 pre-training leakage-audit protocol at `reports/specs/02_01_leakage_audit_protocol.md` (version CROSS-02-01-v1, LOCKED). Sibling spec to WP-1's `02_00_feature_input_contract.md` (CROSS-02-00-v1). Closes sc2egset WARNING 2 from 2026-04-21 Phase 01 audits (now traceable via audit summary artifact). Binds Pipeline Section 02_01 as hard gate; v1 enforcement convention-based (reviewer-adversarial); tooling-enforcement scheduled as §7 future amendment. Audits four dimensions: cutoff-time structural check, POST-GAME token absence, normalization fit-scope, reference-window assertion. Prescribes JSON + MD audit artifact schema. Reused (not re-gated) by 02_03 and 02_06.
   - `### Changed`: edits to 3 dataset ROADMAPs' Phase 02 placeholders appending mandatory-entry requirement citation.
3. Reset `[Unreleased]` to empty with `### Added / Changed / Fixed / Removed`.

**Verification:**
- `grep '^version' pyproject.toml` returns `version = "3.40.0"`.
- `CHANGELOG.md` `[3.40.0]` block populated; `[Unreleased]` reset empty.

**File scope:**
- `pyproject.toml` (Update)
- `CHANGELOG.md` (Update)

**Read scope:** None.

---

## File Manifest

| File | Action |
|------|--------|
| `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` | Create |
| `reports/specs/02_01_leakage_audit_protocol.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update |
| `pyproject.toml` | Update |
| `CHANGELOG.md` | Update |
| `planning/current_plan.md` | (this plan; tracked separately) |
| `planning/current_plan.critique.md` | (produced by reviewer-adversarial Mode A) |

6 git-diff-scope files (2 new + 4 modified) + 2 planning-meta files.

## Gate Condition

- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` exists with all 3 dataset sections + finding closure table.
- `reports/specs/02_01_leakage_audit_protocol.md` exists at `CROSS-02-01-v1` LOCKED with all 8 sections populated; §1 cites both CROSS-02-00-v1 sibling + phase01_audit_summary referent; §5 acknowledges v1 convention-based enforcement; §7 names tooling enforcement as future amendment.
- All 3 dataset ROADMAPs' Phase 02 placeholder sections cite the spec with mandatory-entry requirement.
- `pyproject.toml` `version = "3.40.0"`.
- `CHANGELOG.md` `[3.40.0]` populated; `[Unreleased]` reset.
- All three `PHASE_STATUS.yaml` UNCHANGED.
- `planning/current_plan.critique.md` filed by Mode A; revisions applied.
- `git diff --stat` on final commit touches exactly the 6 files in the File Manifest.

## Out of scope

- **Phase 02 audit implementation** (Python script, CLI, SQL macros) — Phase 02 planner-science decision.
- **CI/pre-commit tooling for gate enforcement** — scheduled as §7 future-amendment target post initial Phase 02 execution.
- **Spec-versioning-convention chore** (NOTE 5: `spec_id`/`version` collapse) — deferred to a separate chore that standardizes both WP-1 + WP-2 frontmatter.
- **WP-3 / WP-4 / WP-5** — separate PRs; each cites `phase01_audit_summary_2026-04-21.md` for its closed finding.
- **Phase 02 Pipeline Section decomposition** (steps 02_01_01, ...) — Phase 02 kickoff planner-science session.
- **Amendments to WP-1's spec** (`02_00_feature_input_contract.md`) — WP-2 is a sibling, not a revision.
- **Thesis prose updates** — none required.

## Open questions

- **Q1: Should §2.3 fit-scope audit distinguish sklearn Pipeline fits (automatic via CV) from manual fit scripts?** — Yes; §2.3 text notes both paths with different assertion mechanisms. Resolved in T03 step 3.
- **Q2: Should the audit schema reserve fields for future extensions (e.g., `privacy_leakage_count`)?** — No. Spec is LOCKED at v1; extensions follow §7 change protocol.
- **Q3: Should WP-2 propose an initial Python implementation stub?** — No. Explicitly out of scope per §Out of scope.

## Dispatch sequence

1. This plan written at `planning/current_plan.md` on branch `docs/phase02-leakage-audit-protocol`.
2. `reviewer-adversarial` Mode A invoked against prior version of this plan 2026-04-21 — verdict REVISE with 2 BLOCKERs + 2 WARNINGs + 2 NOTEs. **Revision round applied 2026-04-21:** Assumption 2 corrected (aoestats MD format); T02 added for Phase 01 audit summary artifact (I9 traceability; existing T02–T04 renumbered T03–T05); T03 verification grep scoped to frontmatter; §5 gate v1 enforcement language clarified; §7 tooling-enforcement future-amendment target added; NOTE 6 §2.2 implementation-dependency limitation acknowledged. Symmetric 1-revision cap consumed.
3. Executor dispatched with T01–T05.
4. `reviewer` (standard, Cat E default) post-execution review.
5. Pre-commit validation (ruff / mypy N/A; planning-drift passes).
6. Commit + PR + merge per standard workflow.
7. Post-merge: next plan (WP-3, WP-4, or WP-5) overwrites `planning/current_plan.md`.
