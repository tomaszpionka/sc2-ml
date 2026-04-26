# Adversarial critique: thesis audit cleanup PR plan

**Plan under review:** `planning/current_plan.md` (Category F, branch `thesis/audit-methodology-lineage-cleanup`, 20 tasks)
**Reviewer:** reviewer-adversarial
**Date:** 2026-04-26

## Verdict
**ACCEPTABLE-WITH-REVISIONS** — the plan's *order* is sound (lineage audit → AoE2 provenance → ROADMAP/notebook → log → cross-dataset → spec → thesis → review) and the guardrails are explicit, but five concrete BLOCKERs must be resolved before T03 begins, plus the scope is borderline-too-large for one PR and several conditional manifest entries are weaker than the planner contract requires. None of the BLOCKERs invalidates the strategy; all are correctable in the plan text.

## BLOCKER findings

### BLOCKER-1 — `internalLeaderboardId = 18` is already on-disk classified as `qp_rm_1v1` (quickplay), yet the plan treats Q2 as an open empirical question and the existing thesis prose calls the combined population "Ladder rankingowy 1v1 (rm_1v1 + qp_rm_1v1)"

**Tasks affected:** T05 (sub-step 4.2), T11 (Chapter 4), T12 (Chapter 1), Q2 in Open Questions, plus all four chapter rewrites that depend on the answer.

**The attack:**
The plan's Q2 says "Is `aoe2companion` `internalLeaderboardId = 18` ranked ladder, quickplay, or a distinct ladder-like population… resolves at T05 sub-step 4.2 with `@lookup` external verification." This frames the answer as unresolved. But the repo already contains decisive on-disk evidence that ID 18 = `qp_rm_1v1` (quickplay), not ranked ladder:

- `sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py:23` — comment literally reads "internalLeaderboardId=6 (rm_1v1) and =18 (qp_rm_1v1)".
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md:872` — leaderboard_raw top values include "6/rm_1v1 (54M), … 18/qp_rm_1v1 (7M)".
- `thesis/chapters/04_data_and_methodology.md:177, 187, 255` — the thesis already labels the population "Ladder rankingowy 1v1 (rm_1v1 + qp_rm_1v1)", inheriting `qp_rm_1v1`'s "ranked ladder" label without justification.
- `src/.../aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md:29` — calls R01 "Retain 1v1 ranked ladder only" while the underlying filter retains `qp_rm_1v1`.

This is precisely the same-class contradiction Guardrail G12 is meant to catch: the labelling ("ranked ladder") and the empirical scope (a leaderboard ID externally documented as the *quickplay* random-map queue) directly conflict on master. The plan's Q2 framing inadvertently understates the seriousness — the thesis is *currently* labelling quickplay records as ranked ladder. T05 must not just "verify whether ID 18 is ranked or quickplay"; it must also (a) audit how that conflict propagated into the on-disk artifact `data_quality_report_aoe2companion.md` (which is generated — see BLOCKER-3), and (b) trace which downstream artifacts and thesis sections inherited the mis-label.

**Proposed fix:**
1. Update Q2 wording from "Is ID 18 ranked ladder, quickplay, or distinct?" to "*Confirm* the on-disk classification of ID 18 = `qp_rm_1v1` against external aoe2companion / aoe2.net documentation, and trace the propagation of the mis-label `1v1 ranked ladder` from the data quality report into Chapter 4 §4.1.3 and §4.2.3."
2. Add a fallback to T05 4.2 step 5: "If external documentation is ambiguous (e.g., the aoe2companion REST API does not enumerate `internalLeaderboardId` semantics), treat ID 18 as `quickplay/matchmaking` (the conservative weakening) and weaken thesis terminology accordingly. Do NOT default to 'ranked ladder' on ambiguity."
3. The §6 Stage 4.3 terminology ladder must explicitly map: ID 18 alone → "third-party 1v1 Random Map quickplay/matchmaking records (per `qp_rm_1v1` label found in stratification artifact 01_05_03)" unless the external verification overturns the on-disk evidence.

---

### BLOCKER-2 — `reports/specs/02_00_feature_input_contract.md` is at LOCKED v3 and `02_01_leakage_audit_protocol.md` is at LOCKED v1; both specs have a §7 amendment protocol that the plan does not reference

**Tasks affected:** T15 (instructions 2 and 6), T16 sub-blocks 14A.2 and 14A.3.

**The attack:**
- `reports/specs/02_00_feature_input_contract.md:13` — "CROSS-02-00-v3 (LOCKED 2026-04-21)".
- `reports/specs/02_00_feature_input_contract.md:456` — "## §7 Spec Change Protocol" prescribing major (vN+1) and minor (vN.M+1) bumps, an amendment-log entry, and a frontmatter version bump in the same commit.
- `reports/specs/02_01_leakage_audit_protocol.md:15` — "CROSS-02-01-v1 (LOCKED 2026-04-21)" with `155: Any amendment requires sign-off from both planner-science and reviewer-adversarial. Any change to §2 audit dimensions or §5 gate condition constitutes a major version increment (vN+1)."

The plan's T15 says only "Submit spec changes that affect methodology to `@reviewer-adversarial` per source §6 Stage 14 (no Cat-C demotion of methodology-affecting changes)." That captures the reviewer-adversarial signoff but **omits**: (i) the requirement to bump the version field (`v3 → v4` or `v3 → v3.1`), (ii) the requirement to add an amendment-log row in the same commit, (iii) the planner-science co-signoff, and (iv) the major-vs-minor classification rule (§7 says any change to §2 column-grain or §5 gate is a major bump). T16 14A.2 names "v1 enforcement mechanism" and "defer AST/pre-commit/CI tooling to v2 only if explicitly documented", which sounds like a v1→v2 bump but does not invoke the §7 amendment protocol procedurally.

If the executor follows T15/T16 as written, the spec frontmatter will go stale, the amendment log will be empty, and CROSS-02-00 will silently drift from LOCKED v3 to a state where its frontmatter says v3 but its body has been mutated. That is a Guardrail G3 / I9 violation by another name (artifact's stated state ≠ on-disk state).

**Proposed fix:**
Insert into T15 Instructions step 2 (and T16 14A.2/14A.3): "Apply the §7 Spec Change Protocol of the affected spec: classify the change as major (vN+1) or minor (vN.M+1) per the spec's own §7 rules; bump the `version` field in the frontmatter; add an amendment-log entry recording date, author, motivation, scope; obtain planner-science + reviewer-adversarial signoffs; commit the version bump and amendment-log row in the same commit as the body change." Add to T15 Verification: "spec version field has been bumped; amendment log has a new row dated within this PR."

---

### BLOCKER-3 — T16 14A.1 ("data dictionary temporal-classification audit") names `01_06_01_data_dictionary.py` work-output but the File Manifest does not list the upstream notebook, ROADMAP step, research_log entry, or STEP_STATUS row that 14A.1 must update if the dictionary is generated (which it is)

**Tasks affected:** T16 sub-block 14A.1; File Manifest.

**The attack:**
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py:114` — the data dictionary CSV is **generated** by this notebook.
- T16 14A.1 step 3 correctly says: "If the data dictionary is generated, update the upstream ROADMAP Step and notebook/generator and regenerate the CSV (apply T06/T07 discipline)."
- But the File Manifest only enumerates `sandbox/aoe2/aoe2companion/**` (conditional²) and `src/.../aoe2companion/reports/artifacts/**` (conditional²) and `src/.../aoe2companion/reports/research_log.md` (conditional³). The notebook, the artifact, and the log are conditional on T06's regeneration manifest declaring them stale. There is **no path** from "T16 14A.1 finds a temporal-classification contradiction in the data dictionary" to a binding manifest declaration; conditional² is keyed off T06, but T06 reads only T03/T04/T05 outputs — not T16's findings.

The planner contract Hard Rule reads: "no executor task may touch a file absent from the manifest." `sandbox/.../01_06_01_data_dictionary.py` is reachable only via the wildcard `sandbox/aoe2/aoe2companion/**`, and that wildcard fires only under conditional². If T16 14A.1 declares the dictionary generated but the manifest's footnote chain doesn't connect to T16 14A.1's findings, the executor faces a contract violation: it must either (a) refuse to touch the notebook (but then 14A.1 cannot be executed) or (b) touch it and violate the manifest contract.

**Proposed fix:**
Add an explicit conditional⁶ for "files touched in T16 14A.1 generated-vs-hand-maintained workflow." The set of files is enumerable a priori:
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` and `.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.csv`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` (Step 01_06_01 section)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` (Step 01_06_01 entry)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` (Step 01_06_01 row)

These should be enumerated explicitly in the manifest, conditional⁶ on T16 14A.1 finding a temporal-classification contradiction. Alternatively, the conditional² wildcard `sandbox/aoe2/aoe2companion/**` should be tightened by adding "include files touched by T16 14A.1 if the dictionary is found generated" to footnote ², which the current footnote does not say (it's keyed exclusively to T06's manifest declarations).

---

### BLOCKER-4 — `thesis/pass2_evidence/` already contains 5 files (`README.md`, `sec_4_1_crosswalk.md`, `sec_4_1_halt_log.md`, `sec_4_2_crosswalk.md`, `sec_4_2_halt_log.md`); the File Manifest neither lists nor accounts for them, and `claim_evidence_matrix.md` is declared Create even though the existing crosswalks fulfil most of its role

**Tasks affected:** T03 (claim_evidence_matrix first version), T11 (claim_evidence_matrix update), File Manifest.

**The attack:**
- `thesis/pass2_evidence/sec_4_1_crosswalk.md` already maps thesis §4.1 numbers to artifact paths in an 8-column schema: claim_text → artifact_path → anchor → prose_form → artifact_form → normalized_value → datatype → hedging_needed.
- `thesis/pass2_evidence/sec_4_2_crosswalk.md` does the same for §4.2, with 78 rows.
- `thesis/pass2_evidence/README.md:11` — the existing index says: "Each artifact must be cited from at least one thesis chapter or tracking file; uncited artifacts should be either cited or removed."

The plan declares `claim_evidence_matrix.md` as **Create** (File Manifest line 1274) and gives it a first-version slot in T03. But the existing sec_4_*_crosswalk.md files are *already* a claim-evidence matrix, restricted to Chapter 4 only. The plan does not state whether `claim_evidence_matrix.md` will:
- subsume / replace the existing crosswalks (in which case the manifest must list the existing crosswalks for Update or Delete);
- coexist with them (in which case the plan owes a section explaining the relationship and the README index update);
- only cover Chapters 1–3 (in which case naming is misleading).

The README also has a frozen-at-Pass-2-handoff convention — re-drafting requires `sec_<id>_vN_<type>.md`. The plan does not specify whether T11's "ensure every number traces" produces `sec_4_v2_crosswalk.md` or mutates the v1 files. This is a Guardrail G3 / discipline question that an executor cannot answer from the plan.

**Proposed fix:**
Add to T03 Instructions: "Examine the existing `thesis/pass2_evidence/{README.md, sec_4_1_crosswalk.md, sec_4_1_halt_log.md, sec_4_2_crosswalk.md, sec_4_2_halt_log.md}`. Decide whether `claim_evidence_matrix.md` (a) subsumes them (then list them as Update/Delete in the manifest), (b) is supplementary to them and covers Chapters 1–3 only (then name it accordingly and update the README index), or (c) replaces sec_4_*_crosswalk.md but versioned as sec_4_v2_*.md per the README's frozen-handoff convention. Record the decision in `dependency_lineage_audit.md`." Add corresponding rows to the File Manifest and to the read scope of T03.

---

### BLOCKER-5 — Adversarial-review dispatch count exceeds the project's symmetric 3-round cap on intra-PR adversarial cycles

**Tasks affected:** T02 (plan critique gate), T05 (provenance audit, "Submit the audit to @reviewer-adversarial"), T10 (risk register stress-test), T15 (spec adversarial review), T16 14A.2 (spec adversarial review), T19 (full gate).

**The attack:**
The project memory entry `feedback_adversarial_cap_execution.md` states: "3-round adversarial cap symmetric — cap applies to execution-side review too, not just plan-side; symmetric rigor." Counting from the start of execution: T05 (round 1 against the provenance audit), T10 (round 2 against the risk register), T15 (round 3 against the specs), T16 14A.2 (round 4 against the spec change), T19 (round 5 against the final PR). That is five intra-execution adversarial dispatches, not counting the pre-execution plan critique gate at T02 and the pre-execution adversarial review of the master plan that the plan itself requests.

Even if some dispatches are "lightweight stress-tests" rather than full adversarial reviews, the plan does not differentiate them. An executor reading T05/T10/T15/T16/T19 will dispatch full adversarial cycles each time, unless told otherwise. Each adversarial round costs Opus-tier compute and adds latency; more importantly, repeated dispatches against the same body of work (the four chapters) will produce overlapping findings, encourage churn, and make verdict reconciliation across rounds difficult.

**Proposed fix:**
Either (a) reclassify some dispatches as "@reviewer-deep mechanical-cum-methodology check" rather than "@reviewer-adversarial full critique"; (b) batch T05+T10+T15+T16 into a single mid-PR adversarial gate with a unified prompt; or (c) explicitly justify in the plan why the 3-round cap is exceeded for this PR (e.g., "this PR has 17 risks and cross-dataset scope; the cap is waived per user direction") and obtain user signoff. Recommendation: collapse T05's adversarial sub-step into T10 (stress-test the provenance audit and the risk register together), and collapse T16 14A.2's adversarial review into T15 (since both are spec-mutation cycles). Net adversarial cycles: T02 (plan), T10 (mid-PR audit gate covering provenance + risks), T15 (spec gate), T19 (final) = 4 rounds, still over the cap, but the cap-exceedance is now visible and justifiable.

---

## WARNING findings

### WARNING-1 — Scope realism: 20 tasks, 11 evidence files, conditional regeneration across three datasets, four chapter rewrites — this is borderline two-to-three PRs in disguise

**Tasks affected:** PR scope as a whole.

**The attack:**
- T03–T08 alone are six audit/regeneration tasks across three datasets. Each dataset has Phase 01 already complete (per PHASE_STATUS.yaml), so on-disk artifacts are extensive: `data/db/schemas/views/*.yaml`, `reports/artifacts/01_exploration/{01_acquisition,02_eda,03_profiling,04_cleaning,05_temporal_panel_eda,06_decision_gates}/**`. A single thesis-claim audit across all three datasets is non-trivial. The source plan §3 explicitly rejects two-PR branching, but rejection is not evidence the work fits.
- T11–T14 are four chapter rewrites in Polish, with literature verification for ~10 references and dataset-population terminology revision. Each chapter is in the 5–15k character range (per WRITING_STATUS.md).
- T15–T16 update specs that are LOCKED v3/v1 with their own change protocols.
- T19 runs three review gates (mechanical + deep + adversarial).

The plan does not estimate effort. A conservative reading: T03 alone is a multi-hour audit; T07 regeneration could trigger 30+ notebook executions if the manifest declares many Steps stale. The plan has no escape valve — no "if T07 regeneration scope exceeds N notebooks, escalate to user for scope split" clause.

**Recommendation:**
Document this as a methodology risk in the risk register (T10): "PR scope risk — 20 tasks across thesis, three datasets, four chapters, two LOCKED specs. If T03 dependency lineage audit declares more than ~10 Steps stale, escalate to user for a scope-split decision before T06 begins." This is not a BLOCKER because the plan's serial ordering means a scope explosion is detected at T03/T06 and can be triaged then; but the executor must be told to escalate, not silently push through.

### WARNING-2 — Notebook validation has no documented standard command; T19 step 2 punts on this

**Tasks affected:** T07 (artifact regeneration verification), T19 (full review gate step 2).

**The attack:**
- `pyproject.toml` declares `pytest`, `jupytext`, `nbconvert` as dev dependencies, but there is no `[tool.poetry.scripts]` or Makefile entry for "run-notebooks-and-validate".
- `sandbox/README.md` describes notebook conventions but cites no validation command. `sandbox/notebook_config.toml` exposes a `[execution] timeout_seconds = 600` knob, suggesting nbconvert-based execution is the intent, but the actual command (`jupyter nbconvert --to notebook --execute …` or `papermill …`) is not standardized in repo docs.
- T19 step 2: "Run available tests and notebook validation only if a standard command exists; do not invent commands."
- T07 Verification step: "git diff shows updated notebook pairs that match `notebook_regeneration_manifest.md` declarations" and "@reviewer (mechanical) approves each per-dataset block." But mechanical review of a regenerated notebook depends on knowing whether it executed cleanly; an unexecuted .ipynb (no outputs cells, or stale outputs) won't be caught by `git diff --stat`.

If T07 regenerates artifacts but cannot prove the notebook executed end-to-end (because T19 has no command), the entire regeneration is unaudited. This is not a BLOCKER because (a) Phase 01 is complete on all three datasets, so most likely T07 will declare zero notebooks stale; (b) jupytext's `.py:percent` ↔ `.ipynb` pairing means structural diffs are visible. But it is a concrete gap.

**Recommendation:**
Add to T07 Instructions step 1: "Notebook execution: use `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace <notebook.ipynb>` with a 600s timeout per `sandbox/notebook_config.toml`. If a notebook fails to execute end-to-end, halt and document in `notebook_regeneration_manifest.md`; do not commit an .ipynb whose execution log shows errors." Cite `sandbox/notebook_config.toml [execution] timeout_seconds = 600` as the source for the timeout. Update T19 step 2 from "do not invent commands" to "use the nbconvert command above."

### WARNING-3 — Branch-prefix deviation `thesis/...` is not in the conventional set `feat/ fix/ refactor/ docs/ test/ chore/` per `.claude/rules/git-workflow.md`; CHANGELOG/version-bump assumptions may key off the prefix

**Tasks affected:** T01 (branch creation), T20 (PR-body draft), repo-wide PR/CHANGELOG conventions.

**The attack:**
- `.claude/rules/git-workflow.md` enumerates branches as `feat/ fix/ refactor/ docs/ test/ chore/` and prescribes "Version: minor for feat/refactor/docs, patch for fix/test/chore." `thesis/` is not in either list, so version-bump rule is undefined.
- The plan records the deviation as Assumption B ("user-explicit override") and Q5 ("already user-approved"). That handles the policy question but not the operational consequence: if a CI hook, pre-commit script, or `gh pr create` template keys off the prefix, the deviation could trigger unexpected behavior.

The user-approval is genuinely sufficient for the policy question per project memory `feedback_no_branches_without_approval.md` (the user explicitly approved). But the *operational* check ("does any CI / pre-commit / template / changelog rule break?") is not in the plan.

**Recommendation:**
Add to T01 Instructions: "Verify that the `thesis/` prefix does not break: (a) `.github/workflows/*.yml` filters keyed on branch name; (b) `.pre-commit-config.yaml` rules; (c) `.github/pull_request_template.md` placeholder substitution; (d) `.claude/rules/git-workflow.md` version-bump classification (decide: minor or patch). Document the version-bump classification chosen in `audit_cleanup_summary.md`." This is a 5-minute check; recording it once removes the risk.

### WARNING-4 — Open Question Q3 ("aggregation semantics underlie aoestats records") risks empirical investigation during execution that should have been declared as a verification SQL in the plan

**Tasks affected:** T05 sub-step 4.1; planner contract.

**The attack:**
The planner contract `docs/templates/planner_output_contract.md` line 4: "Empirical investigation during planning is prohibited." Q3 is correctly framed as an Unknown ("resolves at T05 sub-step 4.1"), not as a fact discovered in the plan — that's contract-compliant. But Q3 specifies neither the verification SQL the executor will run nor the artifact paths the executor will read. T05 4.1 says "Identify population fields … Verify what `leaderboard='random_map'` means in aoestats. Determine whether records represent ranked 1v1 Random Map ladder, public Random Map ladder, broader ranked multiplayer, source-specific aggregation, or insufficient documentation."

That's a checklist, not an executable verification. The existing on-disk evidence (research_log.md:1077, "Jaccard index between true 1v1 and ranked 1v1 = 0.958755") and the cleaning logic (`leaderboard='random_map'` filter) are not mentioned as starting points. The executor will end up doing ad-hoc empirical work to "verify what `random_map` means" without a binding artifact to anchor against.

**Recommendation:**
Add to T05 4.1 Instructions: "Read `01_03_02_true_1v1_profile.md` (Jaccard 0.958755 finding) and `01_04_01_data_cleaning.md` (R02 rule) as the existing on-disk evidence. Verify against external aoestats source documentation (use `@lookup` for the aoestats README/repo) whether `leaderboard='random_map'` corresponds to the ranked random-map queue specifically, or to public/quickplay random-map records. If aoestats source documentation is silent, treat this as 'source-specific aggregation, scope semantically opaque' and weaken thesis terminology." This converts Q3 from a vague unknown into a bounded verification task.

### WARNING-5 — Conditional File Manifest with footnotes ¹–⁵ is contract-compliant but the wildcard `sandbox/<game>/<dataset>/**` rows are too coarse to satisfy "no executor task may touch a file absent from the manifest"

**Tasks affected:** File Manifest entries `sandbox/sc2/sc2egset/**`, `sandbox/aoe2/aoestats/**`, `sandbox/aoe2/aoe2companion/**`.

**The attack:**
The planner contract Hard Rule says "no executor task may touch a file absent from the manifest." `sandbox/sc2/sc2egset/**` matches every notebook under that directory (50+ files in real terms across `01_exploration/{01_acquisition,02_eda,03_profiling,04_cleaning,05_temporal_panel_eda,06_decision_gates}/`). This wildcard does technically satisfy the contract literally, but it concedes no boundary: an executor could regenerate any notebook under the directory and claim manifest compliance.

This is a tension within the planner contract itself — some plans must touch unknown-in-advance subsets of a tree. The plan's footnote ² (conditional on T06 declaring the Step's artifacts stale) provides the bound, but the bound lives in the footnote text, not in the manifest row.

**Recommendation:**
Tighten the manifest row to: "Update (conditional² — only files declared stale in `notebook_regeneration_manifest.md` after T06; manifest is the authoritative bound)." This is a wording change with no functional cost; it makes the bound explicit. Also add to T07 Verification: "every modified file under `sandbox/<game>/<dataset>/**` has a corresponding row in `notebook_regeneration_manifest.md`. Files modified outside the manifest are a Hard Rule violation."

## NOTE findings

### NOTE-1 — T06 says "If a notebook must be edited: mark current artifacts from that Step as stale; do not silently reuse" but does not specify *how* the stale marking is done physically

The marking could be a comment in the artifact, a YAML key in `STEP_STATUS.yaml`, a `STALE` filename suffix, or a column in `notebook_regeneration_manifest.md`. The plan implies the manifest is authoritative but never says so. **Suggestion:** "Stale marking lives in `notebook_regeneration_manifest.md` only; on-disk artifact filenames are not mutated; a downstream consumer of any artifact must consult the manifest before citing." Without this, an executor might rename `01_04_01_data_cleaning.md` → `01_04_01_data_cleaning_STALE.md`, breaking every downstream cross-reference in research logs and thesis prose.

### NOTE-2 — Stage 14A.5 ("SC2 cross-region fragmentation") is bound to risk register but does not specify the retention threshold below which the dual-feature-paths fallback must be used

T16 14A.5 says "Prefer sensitivity indicator or dual feature paths if strict filtering destroys sample size." "Destroys" is a magic word (Invariant I7 — no magic numbers): when does retention go from "acceptable" to "destroys"? Below 80%? Below 50%? Bound this empirically (e.g., to retention finding from `01_05_10` per the WP-3 work).

### NOTE-3 — T19 mechanical checks regex `rg "Phase 01|PR #TBD|BACKLOG.md|grep|post-F1|master"` will yield false-positive matches on the bare word "master"

`master` appears as a generic English/Polish noun in many contexts ("master plan", "master's thesis", "Master's degree"). The thesis title uses it: "A comparative analysis…" is described as a "master's thesis." T19 step 1 line 4 will produce noise. **Suggestion:** Tighten the regex to `\bmaster\b` (workflow-leakage usage typically reads "on master", "into master", or "merged to master") or specify "branch master" as the disallowed phrase. As-written, the executor will face noise to triage.

### NOTE-4 — Plan fidelity to source: the plan re-emits all 18 stages from `final_production_pr_plan.md` faithfully and respects the source's cardinal ordering (lineage → AoE2 → ROADMAP → log → comparability → spec → thesis → review)

I checked T01 ↔ Stage 0, T02 ↔ Stage 1, …, T20 ↔ Stage 18 — every source stage is present and the ordering is preserved. Cross-game comparability matrix (T09) precedes Chapter 4 (T11), which precedes Chapter 1 (T12), Chapter 2 (T13), Chapter 3 (T14). The dependency footnote chain T11 reads-from T09 and T11 sets the AoE2 terminology that T12/T13/T14 inherit. The ordering is sound.

## Strengths

1. **Lineage ordering is correctly enforced.** T03 (lineage audit) precedes T05 (provenance) precedes T06 (regeneration decision) precedes T07 (artifact regeneration) precedes T08 (log repair) precedes T11 (Chapter 4 rewrite) precedes T12/T13/T14 (Chapters 1/2/3). Read-scope footnotes consistently require T11 to read regenerated artifacts, T12 to read aoe2_ladder_provenance_audit.md, etc. The plan correctly forbids Chapter rewrite before artifact regeneration.

2. **Generated-artifact protection (G4) is reflected in T07 step 5 and T16 14A.1.** T07 instruction 5 says "Do not edit any artifact manually if it is generated; only regenerate via its upstream notebook." T16 14A.1 step 3 correctly prescribes upstream-ROADMAP-then-notebook discipline for the data dictionary.

3. **`tracker_events_raw` validation (T16 14A.6) is correctly gated on T15's decision to retain SC2 in-game telemetry features.** The cautions section is precise: "Do not assume final-tick `PlayerStats` minerals/vespene are cumulative totals." This rejects the unsafe assumption from the prior Pre-Phase-02 plan that the master plan §3 warned against.

4. **The "ranked ladder" terminology ladder (master plan §6 Stage 4.3) is faithfully transcribed and bound to T05 acceptance.** Four tiers from "publicly indexed 1v1 ranked Random Map ladder matches" (strong evidence) to "third-party AoE2 multiplayer match records filtered to 1v1 Random Map-like matches" (insufficient evidence) — this is the right shape.

5. **Two-PR branching is explicitly rejected in Out-of-scope, with the rationale traced to source §3.** Manual artifact edits and Cat-C demotion of methodology spec changes are likewise rejected. The unsafe items from the prior plan are enumerated in Out-of-scope. This is exactly what the source plan §3 demanded.

6. **Read-scope chains (footnotes ¹–⁵) are non-trivial and correct in shape.** T11 reads from T09 + T10 + T07 outputs; T12 reads from T05 + T09 + T11. The dependency graph is acyclic and order-preserving.

## Recommended pre-execution actions

These map to BLOCKERs above; each must be resolved (or explicitly converted to a documented non-executable constraint per T02 step 3) before T03 begins.

1. **Resolve BLOCKER-1:** Rewrite Q2 to acknowledge the on-disk `qp_rm_1v1` evidence; add fallback "default to quickplay/matchmaking on ambiguity, never default to ranked ladder"; bind T05 4.2 step 5 to that fallback. Trace propagation of the mis-label through `data_quality_report_aoe2companion.md` → thesis §4.1.3 / §4.2.3.
2. **Resolve BLOCKER-2:** Insert §7 spec-amendment-protocol invocation into T15 instructions and T16 14A.2/14A.3 instructions. Require version bump, amendment-log row, planner-science + reviewer-adversarial co-signoff in the same commit.
3. **Resolve BLOCKER-3:** Add a conditional⁶ footnote and explicit File Manifest rows for the 6 files that T16 14A.1 may touch if the data dictionary is found generated (which it is per `01_06_01_data_dictionary.py:114`).
4. **Resolve BLOCKER-4:** In T03 Instructions, decide whether `claim_evidence_matrix.md` subsumes / coexists with / replaces the existing `sec_4_1_crosswalk.md` and `sec_4_2_crosswalk.md`. Add the existing 5 `pass2_evidence/` files to the File Manifest (Read scope at minimum; Update if subsumed; Delete if replaced). Decide handling under the existing README's "frozen at Pass-2 handoff" convention.
5. **Resolve BLOCKER-5:** Collapse adversarial dispatches: merge T05's adversarial sub-step into T10; merge T16 14A.2's adversarial review into T15. Net adversarial cycles inside execution: T10 (mid-PR audit gate) + T15 (spec gate) + T19 (final). With T02 (pre-execution plan critique) the total is 4. Document this as cap-exceedance with user signoff, OR justify why some cycles count as @reviewer-deep, not @reviewer-adversarial.
6. **Address WARNING-1, WARNING-2:** Add scope-explosion escape valve to T03/T06 (escalate to user if >10 Steps declared stale); cite explicit nbconvert command and timeout in T07/T19.
7. **Address WARNING-3, WARNING-4:** Verify branch-prefix `thesis/` does not break CI/hooks/templates; document version-bump classification (minor for thesis ≈ docs?). Bind Q3's resolution to a specific verification SQL anchored on `01_03_02_true_1v1_profile.md` and `01_04_01_data_cleaning.md`.
8. **Address NOTE-2:** Bind T16 14A.5's "destroys sample size" threshold empirically to the WP-3 retention finding.
9. **Address NOTE-3:** Tighten T19 regex `master` to `\bbranch master\b` or equivalent; document the false-positive triage rule.

Verdict: ACCEPTABLE-WITH-REVISIONS; BLOCKERs: 5; WARNINGs: 5; NOTEs: 4
