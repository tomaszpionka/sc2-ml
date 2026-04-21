---
spec_id: CROSS-02-01-v1
version: CROSS-02-01-v1
status: LOCKED
date: 2026-04-21
invariants_touched: [I3]
supersedes: null
datasets_bound: [sc2egset, aoestats, aoe2companion]
sibling_specs: [CROSS-02-00-v1]
closes_finding: "sc2egset WARNING 2 per reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §2"
---

# Cross-Dataset Phase 02 Pre-Training Leakage Audit Protocol

## CROSS-02-01-v1 (LOCKED 2026-04-21)

This document is the authoritative cross-dataset pre-training leakage audit protocol for Phase 02 feature engineering. It formalizes the mandatory audit gate for Pipeline Section 02_01 (Pre-Game vs In-Game Boundary) and prescribes the audit artifact schema, execution timing, and gate condition across three datasets: sc2egset, aoestats, and aoe2companion.

This spec is the verification-side sibling to `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v1, LOCKED 2026-04-21). WP-1 names what Phase 02 reads; WP-2 (this spec) names what Phase 02 must verify before training.

Amendments follow the §7 change protocol.

---

## §1 Scope and Binding

### Closed Finding

This spec closes sc2egset WARNING 2 from the 2026-04-21 reviewer-adversarial Phase 01 sign-off audits. The finding is: "No mandated Phase 02 pre-training leakage-audit protocol at the Phase 01 gate." The durable on-disk referent for that finding is `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §2`.

The sibling input contract `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v1) specifies which VIEWs Phase 02 reads, their column grain, join keys, and I3 temporal anchor. This spec presupposes CROSS-02-00-v1 compliance: the audit defined here verifies the feature-computation code built on top of those inputs, not the inputs themselves.

### Pipeline Section Binding

This spec binds **Pipeline Section 02_01 (Pre-Game vs In-Game Boundary)** as a hard exit gate: no step in 02_01 may exit (i.e., no 02_01 exit PR may be merged) without the audit artifact prescribed in §3 committed to the repository, passing all §5 gate conditions.

The protocol is **reused** (not re-gated) by:

- **02_03 (Temporal Features, Windows, Decay, Cold Starts)** — whenever 02_03 materializes new rolling-window features, re-run the protocol and produce a new audit artifact. 02_03 has its own Pipeline Section exit gate; this protocol is reused inside that gate.
- **02_06 (Feature Selection)** — whenever 02_06 materializes new feature-selection outputs, re-run the protocol and produce a new audit artifact. Same principle as 02_03.

---

## §2 What Is Audited

### §2.1 Cutoff-Time Structural Check

Every Phase 02 feature-generating SQL expression or Python code block that reads `player_history_all` MUST apply a strict temporal filter: `WHERE ph.<anchor_col> < target.started_at` (per CROSS-02-00-v1 §3.3). The equality form `<=` is forbidden because it would include the target match's own history row in the feature computation, violating Invariant I3.

The audit asserts three sub-conditions for each feature-generating expression:

(a) A temporal filter is present (not absent or commented out).

(b) The filter operator is strict `<` (not `<=`, `>=`, `=`, or absent).

(c) The anchor column is the per-dataset canonical column per CROSS-02-00-v1 §3.2: `details_timeUTC` (sc2egset), `started_timestamp` (aoestats), `started` (aoe2companion). Using the cross-dataset alias `started_at` in a context where the per-dataset column name differs is a violation.

### §2.2 POST-GAME Token Absence

Every materialized feature column's source lineage must not include columns classified as POST_GAME_HISTORICAL, IN_GAME_HISTORICAL, or TARGET per CROSS-02-00-v1 §5. Including such columns in a pre-game feature would leak information available only after match completion into the pre-game prediction context.

Audit approach: source-column lineage resolution via SQL AST walk (for SQL views) or Python docstring trace (for notebook code).

**Implementation-dependency limitation:** for cascading VIEWs without AST-walk tooling and for Python code without docstring conventions, audit rigor depends on manual review. Phase 02 planner-science must either (a) author a lineage-resolution script, OR (b) restrict Phase 02 feature materialization patterns to a set where manual review is feasible and complete.

### §2.3 Normalization Fit-Scope

Any scaling or normalization statistic (mean, standard deviation, min, max, quantile) or K-fold target-encoding statistic MUST be fit on training folds only. Fitting on the full dataset before train/test split introduces future-into-past leakage that is invisible at the schema level.

Audit assertions:

- For scikit-learn `Pipeline` steps: assert that `fit` (or `fit_transform`) is called with training-fold data only, not with the full dataset prior to splitting.
- For K-fold target encoding: assert fold-mask discipline — the target statistic for fold k must be computed from all folds except k.
- For manual encoding code: assert fold-mask discipline via code review (no global `df.mean()` or `df.std()` calls before the train/test split).

### §2.4 Reference-Window Assertion (Reused from Phase 01)

The temporal window used for feature computation must be consistent with the training window of the model. The reference window defined in Phase 01 PSI and cohort analysis (`ref_start`, `ref_end`) must match the feature-computation window applied in Phase 02.

The audit asserts that training-fold start and end timestamps match the feature-computation window timestamps as established in the Phase 01 leakage-audit artifacts:

- sc2egset: `ref_start = 2022-08-29`, `ref_end = 2022-12-31` (per `leakage_audit_sc2egset.json`).
- aoestats: `ref_start = 2022-08-29`, `ref_end = 2022-10-27` (per `01_05_06_temporal_leakage_audit_v1.md §Q7.3`).
- aoe2companion: `ref_start = 2022-08-29`, `ref_end = 2022-12-31` (per `01_05_08_leakage_audit.json` check_3).

---

## §3 Audit Artifact Schema

Phase 02 audit runs MUST produce a JSON artifact at `reports/artifacts/02_<step>/leakage_audit_<dataset>.json` where `<step>` is the Pipeline Section step identifier (e.g., `02_01_01`) and `<dataset>` is the dataset name.

Required JSON fields:

| Field | Type | Pass Condition |
|---|---|---|
| `spec_version` | string | `"CROSS-02-01-v1"` |
| `dataset` | string | one of `{"sc2egset", "aoestats", "aoe2companion"}` |
| `phase_02_step` | string | e.g., `"02_01_01"` |
| `audit_date` | string | ISO date, e.g., `"2026-04-21"` |
| `future_leak_count` | integer | `0` required for PASS |
| `post_game_token_violations` | integer | `0` required for PASS |
| `normalization_fit_scope` | string | `"training_fold_only"` required for PASS |
| `target_encoding_fold_awareness` | string | `"K_fold_masked"` or `"N/A_no_target_encoding"` required for PASS |
| `cutoff_time_filter_structural_check` | string | `"pass"` required for PASS |
| `reference_window_assertion` | string | `"pass"` required for PASS |
| `features_audited` | list of strings | all Phase 02 feature columns materialized in the step |
| `verdict` | string | `"PASS"` required for 02_01 exit |

A sibling Markdown report (`.md`, same base name as the JSON) MUST also be produced. The Markdown report narrates the audit — describing the queries and checks performed — with SQL verbatim per Invariant I6. The JSON carries the machine-readable verdict; the Markdown carries the human-readable audit trail.

Both the JSON and the Markdown artifacts MUST be committed to the repository before 02_01 exit.

---

## §4 Execution Timing

The audit MUST run AFTER every Phase 02 feature materialization step and BEFORE any training or model evaluation step that consumes those features.

"Materialization" is defined as any step that persists a new feature column to DuckDB (as a VIEW or materialized table) or to Parquet file format that is consumed by the training pipeline.

The audit must cover ALL feature columns materialized in the Pipeline Section being audited. Partial audits (covering only a subset of columns) do not satisfy the gate condition.

---

## §5 Gate Condition (v1 enforcement: convention-based)

Pipeline Section 02_01 exit requires all three of the following conditions:

(a) Every feature column materialized in 02_01 appears in `features_audited` in the audit artifact.

(b) `verdict = "PASS"` in the audit artifact JSON.

(c) Both the JSON artifact and the sibling Markdown report are present at the prescribed path (`reports/artifacts/02_01_*/leakage_audit_<dataset>.json` and `.md`).

A missing audit artifact OR `verdict != "PASS"` blocks 02_01 exit.

**v1 ENFORCEMENT MECHANISM: convention-based — no CI check, pre-commit hook, or gate script in the current toolchain reads the JSON and fails commits on `verdict != PASS`. Enforcement is (i) the reviewer-adversarial mandatory review gate before any 02_01 exit PR is merged, and (ii) this spec's convention. See §7 for the tooling-enforcement follow-up target.**

---

## §6 Scope Reuse by 02_03 and 02_06

When Pipeline Section 02_03 (Temporal Features, Windows, Decay, Cold Starts) materializes new rolling-window features, the audit protocol defined in this spec MUST be re-run and a new audit artifact produced (same JSON schema, new `phase_02_step` value, e.g., `"02_03_01"`). This is not a re-gate of 02_01; it is a reuse of the protocol within 02_03's own exit requirements.

The same reuse rule applies to Pipeline Section 02_06 (Feature Selection) whenever 02_06 materializes new feature-selection outputs.

Protocol reuse means: the same §2 audit dimensions, the same §3 artifact schema, and the same §5 pass conditions apply. The dataset-specific anchor column and reference-window values (§2.1, §2.4) are carried forward unchanged.

---

## §7 Spec Change Protocol

Version bumps follow the WP-1 pattern: `CROSS-02-01-vN.M.K` where N is major (breaking §2 audit dimensions or §5 gate condition), M is minor (additive changes to §2 or §3 schema), and K is patch (prose corrections, §6 clarifications, §8 reference updates).

Any amendment requires sign-off from both `planner-science` and `reviewer-adversarial`. Any change to §2 audit dimensions or §5 gate condition constitutes a major version increment (vN+1).

**Future-amendment target (top-priority for v2):** v2 should add CI/pre-commit tooling enforcement of the §5 gate condition — specifically, a script that reads the audit artifact JSON and fails the commit (or PR merge) if `verdict != "PASS"` or if the artifact is absent. This tooling enforcement is scheduled as a follow-up chore after initial Phase 02 execution validates the audit schema. It is the top-priority amendment for CROSS-02-01-v2 and is noted here so that the Phase 02 planner-science session may scope it explicitly.

---

## §8 Referenced Artifacts

- `.claude/scientific-invariants.md` Invariant I3 — temporal discipline; the strict `<` cutoff requirement this audit enforces.
- `docs/PHASES.md` §Phase 02 — canonical Pipeline Section numbering (02_01 through 02_08) and step definitions.
- `reports/specs/02_00_feature_input_contract.md` (CROSS-02-00-v1, LOCKED 2026-04-21) — sibling input contract; defines VIEWs, column grain, join keys, temporal anchor, and column-level classification this audit presupposes.
- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §2` — on-disk referent for sc2egset WARNING 2, the closed finding that motivated this spec.
- `docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md §2` — cutoff-time mechanism this audit verifies.
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/leakage_audit_sc2egset.json` — Phase 01 sc2egset leakage audit; template for §3 JSON field inheritance and §2.4 reference-window values.
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.md` — Phase 01 aoestats leakage audit (Markdown format; Q7.1–Q7.4 structure; §2.4 reference-window values).
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_leakage_audit.json` — Phase 01 aoe2companion leakage audit; template for §3 JSON field inheritance and §2.4 reference-window values.
