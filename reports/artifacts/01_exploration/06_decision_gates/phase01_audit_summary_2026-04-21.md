---
audit_date: 2026-04-21
auditor: reviewer-adversarial (Sonnet)
datasets: [sc2egset, aoestats, aoe2companion]
verdict_tier: READY_WITH_CAVEATS (all 3)
consolidation_date: 2026-04-21
supersedes: null
---

# Phase 01 Audit Summary — 2026-04-21

## §1 Scope and Method

On 2026-04-21 three reviewer-adversarial Sonnet agent dispatches were run, one per dataset, as the formal Phase 01 sign-off sweep. Each dispatch applied the following lens scope:

- Phase 01 completeness (all STEP_STATUS entries resolved)
- Decision gate quality (modeling-readiness and risk-register completeness)
- Phase 02 input readiness (canonical VIEW availability, column grain, temporal anchor)
- Invariant compliance (I1–I10 cross-check)
- Temporal leakage (Phase 01 leakage-audit artifact pass/fail status)
- Research-log consistency (dates, artifact references, staleness)
- Cross-dataset schema readiness (I8 comparability, cross-game encoding protocol)

**Overall verdicts:** READY_WITH_CAVEATS for all three datasets. Zero BLOCKERs across the sweep. Findings decomposed into WARNINGs (non-blocking gaps with scheduled remediation) and NOTEs (documentation staleness or minor provenance gaps).

The 2026-04-21 sign-off agent outputs existed only in chat transcripts and the interim registry `thesis/reviews_and_others/pass2_status.md` prior to this artifact. This summary is the durable on-disk referent for findings cited by WP-2, WP-3, WP-4, and WP-5.

---

## §2 sc2egset Findings

**Verdict:** READY_WITH_CAVEATS

**WARNINGs (3):**

- **sc2egset WARNING 1 — No explicit Phase-02-facing join/table-grain specification.** The Phase 01 gate artifacts and modeling-readiness doc did not enumerate the input VIEW names, row grain, join keys, and I3 temporal anchor that Phase 02 feature engineering must consume. Without a formal specification, Phase 02 implementers risk consuming stale or wrong VIEWs. Severity: MEDIUM (Phase 02 blocker if unaddressed before kickoff). Closed by: WP-1 PR #198 (`reports/specs/02_00_feature_input_contract.md`, CROSS-02-00-v1, LOCKED 2026-04-21).

- **sc2egset WARNING 2 — No mandated Phase 02 pre-training leakage-audit protocol.** The Phase 01 leakage audit (`leakage_audit_sc2egset.json`) confirms zero future-leakage at the VIEW/schema level but cannot verify Phase 02 rolling-window feature code. No gate exists requiring a leakage audit after Phase 02 feature materialization. Without such a gate, Phase 02 feature extractors could use `<=` instead of strict `<` cutoff filters, fit normalization statistics on the full dataset, or perform target encoding without fold-aware masking — all invisible at schema level. Severity: MEDIUM (Phase 02 correctness risk). Closed by: WP-2 (this PR, `reports/specs/02_01_leakage_audit_protocol.md`, CROSS-02-01-v1, LOCKED 2026-04-21).

- **sc2egset WARNING 3 — ~12% cross-region history fragmentation unquantified.** sc2egset players appearing in multiple Battle.net regions (EU, NA, KR) produce fragmented `toon_id` histories: the same physical player has multiple identifiers, causing their pre-game rolling history to undercount matches played in other regions. The ~12% figure is an estimate from Phase 01 identity-resolution analysis; no artifact quantifies the exact fragmentation rate or its downstream impact on rolling-window feature quality. Severity: MEDIUM (feature quality risk in 02_07 Rating Systems). Scheduled closure: WP-3 (dedicated quantification step in Phase 02 kickoff).

**NOTEs (2):**

- **sc2egset NOTE 1 — Cross-game faction encoding protocol undefined.** No spec existed for encoding the StarCraft II race (Terran / Protoss / Zerg) in a way compatible with AoE2 civilization encoding (50 civilizations). Phase 02 cross-game comparison requires harmonized encoding. Closed by: WP-1 PR #198 (`reports/specs/02_00_feature_input_contract.md` §4, CROSS-02-00-v1).

- **sc2egset NOTE 2 — `reports/research_log.md` index stale dates for sc2egset.** The top-level cross-dataset research log had 5 rows for 3 datasets with stale last-entry dates. Closed by: PR #197 (chore/phase01-audit-cleanup, 2026-04-21; index deduplicated to 1 row per dataset with accurate dates).

---

## §3 aoestats Findings

**Verdict:** READY_WITH_CAVEATS

**WARNINGs (2):**

- **aoestats WARNING 1 — `data_quality_report_aoestats.md:52` stale 9-column claim.** The data quality report cited 9 columns in `matches_history_minimal` at line 52. Post-canonical_slot amendment (PR #185, 2026-04-20 / BACKLOG F1+W4), the aoestats VIEW has 10 columns (the cross-dataset 9-col contract plus the locally extended `canonical_slot`). The stale count is a consumer-facing schema confusion risk. Closed by: PR #197 (chore/phase01-audit-cleanup, 2026-04-21; count corrected to 10).

- **aoestats WARNING 2 — `old_rating` PRE-GAME classification deferred empirical test.** The `old_rating` column in `player_history_all` is classified PRE-GAME (available before match start) but no empirical test confirms that the rating system updates occur strictly after match end. If `old_rating` captures the state after match resolution, it leaks the target. The deferral is acknowledged in the Phase 01 gate artifacts but no Phase 02 test is mandated. Severity: MEDIUM (potential leakage if classification wrong). Scheduled closure: WP-4 (empirical test in Phase 02 setup).

**NOTEs (3):**

- **aoestats NOTE 1 — `player_history_all` interface documentation gap.** The VIEW `player_history_all` lacked explicit column documentation of the pre-game/in-game/post-game classification for its columns in the Phase 01 gate artifacts, creating ambiguity for Phase 02 consumers. Closed by: WP-1 PR #198 (`reports/specs/02_00_feature_input_contract.md` §3.2, CROSS-02-00-v1, which enumerates the per-dataset `player_history_all` columns with temporal classification).

- **aoestats NOTE 2 — "43-day post-patch gap" figure provenance.** The 43-day post-patch gap (2024-07-20 → 2024-09-01) referenced in aoestats temporal analysis was flagged at initial audit as lacking artifact provenance. Follow-up verification 2026-04-21 (WP-5) located the existing provenance: the figure is documented in `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md:29` (matches/ section) and `:38` (players/ section); the filename-scanning derivation logic resides in the paired sandbox notebook `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`. Together the `.md` (output) + `.py` (derivation) pair constitute the I9-compliant provenance. Severity: LOW (audit-time documentation gap; resolved by citation). Closure: WP-5 (2026-04-21) via citation-hardening.

- **aoestats NOTE 3 — Q7.4 FAILED sub-check not amended post-BACKLOG F6.** The Phase 01 leakage audit (`01_05_06_temporal_leakage_audit_v1.md`) showed Q7.4 FAILED at the time of initial write, reflecting the pre-backfill state. The BACKLOG F6 back-tagging fix (2026-04-19) and the PR #185 canonical_slot amendment (2026-04-20) resolved the underlying issue but the audit artifact lacked an AMENDMENT block documenting the post-fix state. Closed by: PR #197 (chore/phase01-audit-cleanup, 2026-04-21; AMENDMENT block added to Q7.4 section documenting post-fix canonical_slot status and retaining the historical FAILED line as a pre-backfill record).

---

## §4 aoe2companion Findings

**Verdict:** READY_WITH_CAVEATS

**WARNINGs:** Zero.

**NOTEs (4):**

- **aoe2companion Note 1 — LPM ICC value discrepancy 0.000485 vs 0.000491.** The research log at line 124 cited ICC value 0.000485 (5k bootstrap) but the canonical artifact `01_05_05_icc.json:18` carries 0.000491. Similarly, 0.002501 vs 0.002505 (10k). The discrepancy is a thesis-citation trap: if a thesis author reads the research log, they cite the wrong value. Closed by: PR #197 (chore/phase01-audit-cleanup, 2026-04-21; research log corrected to match artifact values).

- **aoe2companion Note 2 — I8 cross-dataset ICC spec v1.0.2 AT RISK.** The aoe2companion Phase 01 ICC procedure used spec v1.0.2 with a 5k LMM sample-size cap and omitted the GLMM sub-check, creating a procedural divergence from the cross-dataset I8 spec. The `cross_dataset_phase01_rollup.md §4 item 2` ANOVA-primary harmonization formally closes the AT RISK flag, but no risk-register entry documented the divergence. Closed by: PR #197 (chore/phase01-audit-cleanup, 2026-04-21; new risk-register entry AC-R06 [LOW] added to `risk_register_aoe2companion.md` documenting the divergence and its closure).

- **aoe2companion Note 3 — `cross_dataset_phase01_rollup.md` path ambiguity.** Citations of `cross_dataset_phase01_rollup.md` within aoe2companion artifacts and ROADMAP did not qualify whether the path is relative to the dataset or the repo root (the cross-dataset artifact lives at `<repo>/reports/...`, not at `<dataset>/reports/...`). Closed by: PR #197 (chore/phase01-audit-cleanup, 2026-04-21; path citations clarified with explicit `repo-root` qualifier).

- **aoe2companion Note 4 — Absolute paths in `01_05_05_icc.json`.** The `sample_files` block in the ICC artifact carried machine-local absolute paths (`/Users/tomaszpionka/...`) violating I10 (raw table filename convention — repo-root-relative paths, no absolute paths). Closed by: PR #197 (chore/phase01-audit-cleanup, 2026-04-21; paths relativized to `src/rts_predict/...` repo-root-relative format with `path_convention` marker).

---

## §5 Finding Closure Status Table

| Dataset | Finding ID | Severity | Description (short) | Closed by | Status |
|---|---|---|---|---|---|
| sc2egset | WARNING 1 | MEDIUM | No Phase-02 join/grain spec | WP-1 PR #198 | CLOSED |
| sc2egset | WARNING 2 | MEDIUM | No mandated Phase 02 leakage-audit protocol | WP-2 (this PR) | CLOSED |
| sc2egset | WARNING 3 | MEDIUM | ~12% cross-region history fragmentation unquantified | WP-3 (scheduled) | OPEN — SCHEDULED |
| sc2egset | NOTE 1 | LOW | Cross-game faction encoding undefined | WP-1 PR #198 §4 | CLOSED |
| sc2egset | NOTE 2 | LOW | Top-level research_log.md stale sc2egset dates | PR #197 | CLOSED |
| aoestats | WARNING 1 | MEDIUM | Stale 9-col claim in data quality report | PR #197 | CLOSED |
| aoestats | WARNING 2 | MEDIUM | `old_rating` PRE-GAME classification unverified | WP-4 PR #201 | CLOSED (FAIL verdict; leaderboard-partitioned consecutive-match test 01_04_06; 3-gate FAIL across agreement rate, max disagreement magnitude, stratification; INVARIANTS.md §3 line 76 updated with empirical evidence + 3 Cat D candidates) |
| aoestats | NOTE 1 | LOW | `player_history_all` interface docs gap | WP-1 PR #198 §3.2 | CLOSED |
| aoestats | NOTE 2 | LOW | "43-day post-patch gap" figure no artifact provenance | WP-5 (PR #TBD, 2026-04-21) | CLOSED (`01_01_01_file_inventory.md:29,38` reports the figure; paired `.py` notebook carries the filename-scanning derivation; together constitute I9-compliant provenance) |
| aoestats | NOTE 3 | LOW | Q7.4 FAILED sub-check not amended post-BACKLOG F6 | PR #197 | CLOSED |
| aoe2companion | NOTE 1 | LOW | LPM ICC value discrepancy (log vs artifact) | PR #197 | CLOSED |
| aoe2companion | NOTE 2 | LOW | I8 ICC spec v1.0.2 AT RISK no risk-register entry | PR #197 | CLOSED |
| aoe2companion | NOTE 3 | LOW | `cross_dataset_phase01_rollup.md` path ambiguity | PR #197 | CLOSED |
| aoe2companion | NOTE 4 | LOW | Absolute paths in `01_05_05_icc.json` | PR #197 | CLOSED |
