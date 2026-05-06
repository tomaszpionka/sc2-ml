---
category: C
branch: docs/phase02-contracts-lock-and-planning-cleanup
date: 2026-05-06
base_ref: master
base_commit: ef3fc627be1793c135711b8bc3715ecda7490cf7
planner_model: opus
dataset: null
phase: "02"
pipeline_section: "post-PR209 cleanup"
invariants_touched: []
source_artifacts:
  - planning/README.md
  - planning/current_plan.md
  - planning/current_plan.critique.md
  - planning/current_plan.critique_resolution.md
  - reports/specs/02_02_feature_engineering_plan.md
  - reports/specs/02_03_temporal_feature_audit_protocol.md
  - reports/specs/02_04_cross_spec_consistency_report.json
  - reports/specs/02_04_cross_spec_consistency_report.md
  - reports/research_log.md
  - CHANGELOG.md
  - pyproject.toml
  - .claude/rules/data-analysis-lineage.md
critique_required: true
research_log_ref: reports/research_log.md#2026-05-06-post-pr209-cleanup
---

# Plan: Post-merge cleanup, DRAFT → LOCKED activation, and planning purge for CROSS-02-02 / CROSS-02-03 (after PR #209)

## Scope

Documentation-only post-merge cleanup. PR #209 merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z); this plan executes the post-merge cleanup. Four narrowly-scoped tasks:

- **T01** — flip the front-matter `status: DRAFT` → `status: LOCKED` in `reports/specs/02_02_feature_engineering_plan.md` (CROSS-02-02-v1) and `reports/specs/02_03_temporal_feature_audit_protocol.md` (CROSS-02-03-v1), and update each spec's §1 / §14 / §15 / §16 lock-banner prose to reflect the LOCKED state. No body content edits beyond banner / lock-status prose.
- **T02** — execute the planning purge protocol from `planning/README.md` for the merged PR #209 artifacts, and amend `planning/README.md` §Contents lifecycle table to register `current_plan.critique_resolution.md` as a recognized ephemeral planning artifact.
- **T03** — append a short `[CROSS] 2026-05-06` hygiene-only entry to `reports/research_log.md` recording the post-merge T00b activation event: CROSS-02-02-v1 and CROSS-02-03-v1 transitioned from DRAFT (PR-local) to LOCKED (binding) by way of this cleanup PR; cite PR #209 merge commit `ef3fc627be1793c135711b8bc3715ecda7490cf7` and the new branch `docs/phase02-contracts-lock-and-planning-cleanup`. No follow-up CROSS entries created.
- **T04** — PR wrap-up via `.claude/rules/git-workflow.md` (version bump, CHANGELOG entry, commit, propose push + `gh pr create`).

This plan executes the post-merge cleanup. PR #209 merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z) and the on-disk DRAFT specs (CROSS-02-02-v1, CROSS-02-03-v1) plus the consistency verdict (PASS / 0 blockers, head_sha `e3cf8923`) provide the gate evidence the LOCKED transition prose cites.

## Problem statement

PR #209 (`phase02/feature-engineering-readiness`) merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z); this plan executes the post-merge cleanup. As of merge, the on-disk state is:

- `reports/specs/02_02_feature_engineering_plan.md` carries `status: DRAFT` and §1 / §14 / §16 explicitly state "DRAFT / PR-local until reviewed" pending the active Phase 02 readiness plan's reviewer-deep gate. The PR #209 reviewer-deep verdict (PASS-WITH-NOTES, 0 BLOCKERs) is the gate that the spec's own lock-condition prose cites.
- `reports/specs/02_03_temporal_feature_audit_protocol.md` carries the identical `status: DRAFT` front-matter plus §1 / §13 / §14.1 / §15 parallel lock-condition prose.
- `reports/specs/02_04_cross_spec_consistency_report.json` records `verdict: PASS`, `blockers: 0`, `head_sha: e3cf8923` — the cross-spec consistency gate is satisfied.
- `planning/current_plan.md`, `planning/current_plan.critique.md`, `planning/current_plan.critique_resolution.md`, and `planning/INDEX.md` still hold the merged PR #209 plan and its companions; per `planning/README.md` §Purge protocol, these must be purged on the first session after merge.
- `planning/README.md` §Contents lifecycle table does **not** list `current_plan.critique_resolution.md`. PR #209 introduced this file (T05A planning amendment companion) but did not register it in the lifecycle table; the purge protocol therefore touches an unlisted file asymmetrically. This is a small but real documentation-hygiene gap.

The two DRAFT specs cannot become binding until the lock-condition prose is updated and the front-matter status flipped — which is what T01 does.

## Assumptions

1. PR #209 merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z); this plan executes the post-merge cleanup. The reviewer-deep gate the DRAFT specs cite has therefore already cleared (PASS-WITH-NOTES, 0 BLOCKERs) on master.
2. CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1 remain LOCKED and binding; nothing in T01–T04 amends them or re-versions them. They are not superseded by CROSS-02-02-v1 or CROSS-02-03-v1.
3. The cross-spec consistency verdict (`02_04_cross_spec_consistency_report.json`, verdict PASS, 0 blockers, head_sha `e3cf8923`) is the binding readiness evidence for the DRAFT → LOCKED transition; the validator script is **not** re-run as part of T01–T04.
4. No dataset-scoped ROADMAPs, STEP_STATUS, PIPELINE_SECTION_STATUS, or PHASE_STATUS files are edited. All Phase status remains untouched.
5. Per-dataset research logs (sc2egset, aoestats, aoe2companion) are not edited. T03 is a CROSS-only entry.
6. No notebooks, no generated dataset artifacts, no raw data, no thesis chapters, no `thesis/pass2_evidence/` deletions, no `thesis/reviews_and_others/` deletions, no file moves, no validator regeneration.
7. The branch is `docs/phase02-contracts-lock-and-planning-cleanup`, created off master after PR #209 was merged; `base_ref` is `master`, `base_commit` is the merge SHA `ef3fc627be1793c135711b8bc3715ecda7490cf7`.
8. Version bump is **minor** (3.45.0 → 3.46.0): the change set includes a docs amendment to `planning/README.md` (lifecycle table extension) plus spec lock-state activation, both of which qualify as docs-with-content under `.claude/rules/git-workflow.md` step 2 ("minor for feat/refactor/docs").

## Literature / methodology context

This is documentation-hygiene work; no literature contrast is required. The work is governed by:

- `.claude/scientific-invariants.md` — invariants are not modified; T01 only flips a status flag and amends lock-condition prose for two specs whose invariants_touched list (I3, I5, I6, I7, I8, I9, I10) was already validated by the PR #209 reviewer-deep pass.
- `docs/PHASES.md` — phase boundaries unchanged.
- `planning/README.md` — purge protocol governs T02; T02 also extends this document's own §Contents lifecycle table.
- `.claude/rules/git-workflow.md` — governs T04.
- `.claude/rules/data-analysis-lineage.md` — governs the non-batching rule, artifact discipline, and stop conditions; this plan does not generate any artifacts and does not touch any notebooks, so the rule's notebook / feature-engineering / temporal leakage clauses do not bind. The agent-and-model routing clauses do bind: T01 and T03 are mechanically specified docs edits (`@executor` on Sonnet sufficient); T02 is mechanical but touches a markdown table and a planning protocol (`@executor` on Sonnet sufficient with explicit instructions); T04 is the standard PR wrap-up flow (`@executor` on Sonnet sufficient).

## Execution Steps

### T01 — Lock CROSS-02-02-v1 and CROSS-02-03-v1

**Goal.** Transition CROSS-02-02-v1 and CROSS-02-03-v1 from DRAFT (PR-local) to LOCKED (binding) on master, by way of this cleanup PR. PR #209 merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z); this plan executes the post-merge cleanup, which is the gate-clearing event the DRAFT specs cite. After T01, both specs are authoritative and may be consumed by future Phase 02 ROADMAP entries, notebooks, and generated artifacts.

**Files touched.**
- `reports/specs/02_02_feature_engineering_plan.md` — front-matter + §1 (lock-condition banner) + §14 (state transition) + §16 (status table / governance closing) only. No edits to §2–§13, §15, or appendices.
- `reports/specs/02_03_temporal_feature_audit_protocol.md` — front-matter + §1 (lock-condition banner) + §13 (state transition) + §14.1 (consumption-readiness clause) + §15 (status table / governance closing) only. No edits to §2–§12, §14 (excluding §14.1), or appendices.

**Instructions (mechanical).**

1. In `reports/specs/02_02_feature_engineering_plan.md`:
   1. Update front-matter: `status: DRAFT` → `status: LOCKED`; `date: 2026-05-05` → `date: 2026-05-06`. Leave `spec_id`, `version`, `invariants_touched`, `datasets_bound`, `sibling_specs`, `supersedes` unchanged.
   2. In §1.1 / §1 lock-condition banner: replace the "DRAFT / PR-local until reviewed" sentence with a "LOCKED on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` (PR #209 merged 2026-05-05T21:00:02Z; cleanup PR `docs/phase02-contracts-lock-and-planning-cleanup` 2026-05-06)" sentence. Cite the cross-spec consistency verdict (`02_04_cross_spec_consistency_report.json` PASS, 0 blockers, head_sha `e3cf8923`) as the readiness gate.
   3. In §14 (state transition / change protocol section): record the DRAFT → LOCKED transition with the same SHA / date / cleanup-PR attribution; preserve all prior change-protocol prose.
   4. In §16 (status table / governance closing section): update the status row from DRAFT to LOCKED; preserve all other rows.
   5. No edits to §2 / §3 / §4 / §5 / §6 / §7 / §8 / §9 / §10 / §11 / §12 / §13 / §15 prose.

2. In `reports/specs/02_03_temporal_feature_audit_protocol.md`:
   1. Update front-matter: `status: DRAFT` → `status: LOCKED`; `date: 2026-05-05` → `date: 2026-05-06`. Leave `spec_id`, `version`, `invariants_touched`, `datasets_bound`, `sibling_specs`, `supersedes` unchanged.
   2. In §1.1 / §1 lock-condition banner: same DRAFT → LOCKED prose replacement as for CROSS-02-02 above.
   3. In §13 (state transition / change protocol section): same as CROSS-02-02 §14 above.
   4. In §14.1 (consumption-readiness clause): update from "may not be consumed until LOCKED" to "is now LOCKED and may be consumed by Phase 02 ROADMAP entries, notebooks, and generated artifacts as of this cleanup PR" — preserving the rest of §14's prose unchanged.
   5. In §15 (status table / governance closing section): update the status row from DRAFT to LOCKED; preserve all other rows.
   6. No edits to §2 / §3 / §4 / §5 / §6 / §7 / §8 / §9 / §10 / §11 / §12 / §14 (excluding §14.1) prose.

**Deliverables.** Two specs LOCKED on master via this cleanup PR.

**Gate.** Both specs carry `status: LOCKED` in front-matter; both lock-banner sections cite the PR #209 merge SHA, the merge timestamp, and this cleanup PR branch; both governance/status closing sections show LOCKED. No other prose in either spec is modified.

**Agent routing.** `@executor` on Sonnet (mechanical specified edits to two files, no methodological reasoning required).

**Allowed files.**
- `reports/specs/02_02_feature_engineering_plan.md`
- `reports/specs/02_03_temporal_feature_audit_protocol.md`

**Forbidden files.** Everything else (especially: status YAMLs, ROADMAPs, per-dataset research_logs, notebooks, generated artifacts, raw data, thesis chapters, the validator script, `02_04_cross_spec_consistency_report.{json,md}`).

**Stop condition.** Halt before commit if:
- the front-matter `status` field cannot be flipped without unintended diff,
- the lock-condition banner edits change body content beyond the banner,
- the §14 / §13 / §14.1 / §15 / §16 edits change body content beyond status rows / state-transition lines,
- any edit accidentally touches `02_04_cross_spec_consistency_report.{json,md}`,
- any edit accidentally touches a sibling LOCKED spec (CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1).

### T02 — Planning purge + README amendment

**Goal.** Execute the `planning/README.md` §Purge protocol for the merged PR #209 artifacts, and amend `planning/README.md` §Contents lifecycle table to register `current_plan.critique_resolution.md` as a recognized ephemeral planning artifact (so the asymmetric purge of an unlisted file is corrected before the next Cat A/F PR).

**Files touched.**
- `planning/current_plan.md` — replaced wholesale with `<!-- No active plan -->`.
- `planning/current_plan.critique.md` — deleted.
- `planning/current_plan.critique_resolution.md` — deleted.
- `planning/INDEX.md` — reset to template state per `planning/README.md` §Purge protocol step 3.
- `planning/README.md` — §Contents lifecycle table amendment (Option A, default).

**Instructions (mechanical).**

1. Replace `planning/current_plan.md` with exactly `<!-- No active plan -->` (single-line HTML comment, no trailing newline beyond what the editor adds). Per `planning/README.md` §Purge protocol step 1.
2. Delete `planning/current_plan.critique.md`. Per §Purge protocol step 2.
3. Delete `planning/current_plan.critique_resolution.md`. The file is an ephemeral critique-resolution companion and is purged symmetrically with `current_plan.critique.md`; the README amendment in step 5 below formalizes its lifecycle.
4. Reset `planning/INDEX.md` to its template state. Per §Purge protocol step 3. The current INDEX.md content is the active-plan pointer for PR #209; replace with the template (active plan = none, agent routing table preserved).
5. Amend `planning/README.md` **§Contents lifecycle table**.
   - **Option A (default):** add one row after the existing `current_plan.critique.md` row:
     ```
     | `current_plan.critique_resolution.md` | Ephemeral | Resolution log accompanying critique (Cat A/F when critique present) |
     ```
     Justification: the file is an ephemeral critique-resolution companion and is purged symmetrically with `current_plan.critique.md`.
   - **Option B (fallback):** allowed only if the lifecycle table structure prevents a clean row insertion (e.g., column-width or markdown-rendering constraints). In that fallback, register the file in the §Lifecycle prose body (step 1 of the lifecycle list) using the same purpose description as Option A, and add a one-line note in §Purge protocol covering the deletion.
6. No other edits to `planning/README.md` (no changes to §Lifecycle other than the Option-B fallback case, no changes to §Purge protocol other than the Option-B fallback case, no changes to §Source-of-truth).

**Commit message.** Per `planning/README.md` §Purge protocol prescription: `chore(planning): purge artifacts from merged PR #209`. The README amendment goes in the same commit (it is a co-located doc-hygiene fix to the same protocol whose execution it accompanies).

**Deliverables.** Planning directory in clean post-merge state with `current_plan.critique_resolution.md` formally recognized in the lifecycle table going forward.

**Gate.** `planning/current_plan.md` contains exactly `<!-- No active plan -->`; `planning/current_plan.critique.md` and `planning/current_plan.critique_resolution.md` no longer exist; `planning/INDEX.md` matches its template state; `planning/README.md` §Contents lifecycle table contains the new row (Option A) or §Lifecycle and §Purge protocol have been minimally extended (Option B).

**Agent routing.** `@executor` on Sonnet (mechanical specified edits and deletions, no methodological reasoning required).

**Allowed files.**
- `planning/current_plan.md`
- `planning/current_plan.critique.md`
- `planning/current_plan.critique_resolution.md`
- `planning/INDEX.md`
- `planning/README.md`

**Forbidden files.** Everything else.

**Stop condition.** Halt before commit if:
- the README §Contents lifecycle table cannot be cleanly amended via Option A AND Option B fallback also fails,
- the §Purge protocol step 3 INDEX.md template is ambiguous (re-confirm what "template state" means by reading the current INDEX.md and stripping only the active-plan reference, preserving the agent routing table),
- any deletion accidentally targets `BACKLOG.md` (which is permanent / append/claim and must not be deleted).

### T03 — Root research_log CROSS hygiene entry

**Goal.** Append one short `[CROSS] 2026-05-06` entry to the top `reports/research_log.md` recording the post-merge T00b activation event: CROSS-02-02-v1 and CROSS-02-03-v1 transitioned from DRAFT (PR-local) to LOCKED (binding) by way of the cleanup PR `docs/phase02-contracts-lock-and-planning-cleanup`, citing PR #209 merge commit `ef3fc627be1793c135711b8bc3715ecda7490cf7` and the cross-spec consistency verdict (PASS, 0 blockers, head_sha `e3cf8923`). This is a hygiene entry; no follow-up CROSS entries are added.

**Files touched.** `reports/research_log.md` — exactly one new CROSS entry appended at the top of the CROSS section, dated `2026-05-06`.

**Instructions (mechanical).**

1. Append a new `[CROSS] 2026-05-06` entry at the top of the CROSS section in `reports/research_log.md` with the following structure:
   - **Purpose.** Record post-merge T00b activation: DRAFT → LOCKED transition for CROSS-02-02-v1 and CROSS-02-03-v1.
   - **T00b summary.** PR #209 (`phase02/feature-engineering-readiness`) merged on master at `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z). Cleanup PR `docs/phase02-contracts-lock-and-planning-cleanup` (2026-05-06): T01 flipped both specs to `status: LOCKED`; T02 ran the planning purge and amended `planning/README.md` §Contents lifecycle table. Cross-spec consistency verdict: PASS, 0 blockers, head_sha `e3cf8923` (`reports/specs/02_04_cross_spec_consistency_report.json`).
   - **Follow-up candidates.** None at this time. Future Phase 02 ROADMAP entries that consume CROSS-02-02-v1 / CROSS-02-03-v1 are out of scope for this PR and are scheduled in subsequent dataset-scoped plans.
   - **Out-of-scope confirmations.** No dataset ROADMAPs edited; no notebooks; no generated artifacts; no raw data; no status YAMLs; no thesis chapters; no `thesis/pass2_evidence/` deletions; no `thesis/reviews_and_others/` deletions; no file moves; no validator regeneration; no edits to `02_00`, `02_01`, or `scripts/validate_phase02_readiness_contracts.py`; no edits to per-dataset research logs.
2. Do not modify any prior CROSS entries. Do not modify the index table at the top of `reports/research_log.md` unless it tracks the "CROSS" last-entry date — in which case bump that single cell to `2026-05-06 (T00b activation)`.

**Deliverables.** One new CROSS hygiene entry on master; no other research_log changes.

**Gate.** The new `[CROSS] 2026-05-06` entry exists at the top of the CROSS section; the four sub-bullets (Purpose, T00b summary, Follow-up candidates, Out-of-scope confirmations) match the contents above; PR #209 merge SHA `ef3fc627be1793c135711b8bc3715ecda7490cf7` is cited; the cleanup branch `docs/phase02-contracts-lock-and-planning-cleanup` is cited; the cross-spec consistency verdict is cited. No prior entries modified. Per-dataset research logs untouched.

**Agent routing.** `@executor` on Sonnet (mechanical specified docs edit).

**Allowed files.** `reports/research_log.md`.

**Forbidden files.** Everything else (especially: per-dataset `src/rts_predict/games/<game>/datasets/<dataset>/reports/research_log.md`).

**Stop condition.** Halt before commit if:
- the CROSS section header cannot be located unambiguously,
- the index table at the top tracks CROSS last-entry date in a format that would require re-rendering more than the single date cell,
- any per-dataset research_log appears in the diff.

### T04 — PR wrap-up via git-workflow

**Goal.** Bump version 3.45.0 → 3.46.0, move CHANGELOG `[Unreleased]` to a new `[3.46.0]` stanza, commit the release bump, and propose the push + `gh pr create` commands per `.claude/rules/git-workflow.md`.

**Files touched.**
- `pyproject.toml` — `version = "3.45.0"` → `version = "3.46.0"`. (Single source per project rules; no `__init__.py` version edits.)
- `CHANGELOG.md` — `[Unreleased]` stanza moved to `[3.46.0] — 2026-05-06 (PR #<TBD>: docs/phase02-contracts-lock-and-planning-cleanup)`; `[Unreleased]` left empty with the four standard subsection headers (Added / Changed / Fixed / Removed).

**Instructions (mechanical).**

1. Per `.claude/rules/git-workflow.md` step 1: skip pytest / coverage / ruff / mypy manual runs (no .py files in this PR's diff); pre-commit hooks remain the binding gate at commit time.
2. Per step 2: bump is **minor** (docs PR with content amendments).
3. Per step 3: edit `pyproject.toml` `version = "3.45.0"` → `version = "3.46.0"`.
4. Per step 4: in `CHANGELOG.md`, move `[Unreleased]` content into a new `[3.46.0] — 2026-05-06 (PR #<TBD>: docs/phase02-contracts-lock-and-planning-cleanup)` stanza. The `<TBD>` placeholder convention is explicit:
   - At version-bump commit time the CHANGELOG entry will read literally `## [3.46.0] — 2026-05-06 (PR #<TBD>: docs/phase02-contracts-lock-and-planning-cleanup)`.
   - After `gh pr create` issues a PR number, the executor substitutes `<TBD>` with the issued number in a tightly-scoped follow-up commit on the same branch (single-file edit to `CHANGELOG.md`, commit message `chore(release): substitute PR number in CHANGELOG for 3.46.0`).
   - This **matches the PR #209 precedent** at master commit `73416179` (the T06C CHANGELOG entry that originally carried `<TBD>`-style placeholder language and was post-substituted at PR creation).
5. The `[3.46.0]` stanza body must summarize:
   - **Changed.** CROSS-02-02-v1 and CROSS-02-03-v1 transitioned from DRAFT to LOCKED (T01); citation to PR #209 merge commit `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z).
   - **Changed.** `planning/README.md` §Contents lifecycle table extended to register `current_plan.critique_resolution.md` as ephemeral (T02).
   - **Removed.** `planning/current_plan.critique.md`, `planning/current_plan.critique_resolution.md` (T02 purge).
   - **Changed.** `planning/current_plan.md` reset to `<!-- No active plan -->`; `planning/INDEX.md` reset to template (T02 purge).
   - **Added.** `reports/research_log.md` — new `[CROSS] 2026-05-06` T00b activation entry (T03).
6. Per step 5: leave `[Unreleased]` with empty Added / Changed / Fixed / Removed subsection headers.
7. Per step 6: commit `chore(release): bump version to 3.46.0`.
8. Per step 7: propose to user the push command (`git push -u origin docs/phase02-contracts-lock-and-planning-cleanup`) and the `gh pr create --title "..." --body-file .github/tmp/pr.txt` invocation per the rule's PR Body Format. Write the PR body via the Write tool to `.github/tmp/pr.txt` (per project memory). After the user runs `gh pr create`, perform the `<TBD>` → issued PR number substitution commit described in step 4 above; then delete `.github/tmp/pr.txt` per project memory.

**PR title.** `docs(phase02): lock CROSS-02-02 / CROSS-02-03 and run planning purge`.

**PR body** (per `.claude/rules/git-workflow.md` PR Body Format):

> ## Summary
>
> - Lock CROSS-02-02-v1 (`reports/specs/02_02_feature_engineering_plan.md`) and CROSS-02-03-v1 (`reports/specs/02_03_temporal_feature_audit_protocol.md`) on master via this cleanup PR; PR #209 merge SHA `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z) is the reviewer-deep gate-clearing event the DRAFT specs cited; cross-spec consistency verdict PASS / 0 blockers / head_sha `e3cf8923` (`reports/specs/02_04_cross_spec_consistency_report.json`).
> - Execute `planning/README.md` §Purge protocol for the merged PR #209 artifacts and amend `planning/README.md` §Contents lifecycle table to register `current_plan.critique_resolution.md` as ephemeral.
> - Append a single `[CROSS] 2026-05-06` T00b activation entry to `reports/research_log.md`.
> - No dataset ROADMAPs, notebooks, generated artifacts, raw data, status YAMLs, thesis chapters, per-dataset research logs, or `02_04_cross_spec_consistency_report.{json,md}` are modified.
>
> ## Test plan
>
> - [x] Pre-commit hooks (ruff, mypy) pass at commit time (no .py changes expected to alter lint/type surface).
> - [x] Both specs flipped to `status: LOCKED` with PR #209 SHA citation; no body content edits beyond banner / lock-status prose.
> - [x] `planning/current_plan.md` is `<!-- No active plan -->`; critique + resolution files deleted; INDEX.md template; README.md lifecycle table extended.
> - [x] `reports/research_log.md` new `[CROSS] 2026-05-06` T00b entry only.
> - [x] `pyproject.toml` `version = "3.46.0"`; `CHANGELOG.md` `[Unreleased]` empty; `[3.46.0]` stanza present pre-substitution; post-`gh pr create`, `<TBD>` substituted in a follow-up commit on this branch.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

**Deliverables.** One commit `chore(release): bump version to 3.46.0` plus the propose-to-user push + PR creation command pair, plus the post-PR `<TBD>` substitution commit.

**Gate.** `pyproject.toml` shows `3.46.0`; `CHANGELOG.md` `[Unreleased]` empty; `[3.46.0]` stanza present and correctly attributed; PR opened with title and body matching above; `<TBD>` replaced with issued PR number on the same branch.

**Agent routing.** `@executor` on Sonnet (standard PR wrap-up flow per `.claude/rules/git-workflow.md`; no methodological reasoning required).

**Allowed files.** `pyproject.toml`, `CHANGELOG.md`, `.github/tmp/pr.txt`, `.github/tmp/commit.txt`.

**Forbidden files.** Everything else.

**Stop condition.** Halt before commit if:
- pre-commit hooks fail unexpectedly,
- `CHANGELOG.md` `[Unreleased]` was not empty pre-edit (it should be — this is the first version-bump after the PR #209 release),
- the `<TBD>` substitution follow-up commit would touch any file other than `CHANGELOG.md`.

## File Manifest

The PR's expected diff scope, by task:

- **T01:**
  - `reports/specs/02_02_feature_engineering_plan.md`
  - `reports/specs/02_03_temporal_feature_audit_protocol.md`
- **T02:**
  - `planning/current_plan.md` (content replaced)
  - `planning/current_plan.critique.md` (deleted)
  - `planning/current_plan.critique_resolution.md` (deleted)
  - `planning/INDEX.md` (reset)
  - `planning/README.md` (lifecycle table amended)
- **T03:**
  - `reports/research_log.md`
- **T04:**
  - `pyproject.toml`
  - `CHANGELOG.md`
  - `.github/tmp/pr.txt` (created during PR flow; deleted after)
  - `.github/tmp/commit.txt` (created during commit flow; deleted after)

Total expected committed-files set on this branch: 9 modified/deleted content files (not counting `.github/tmp/` which is created and removed in-session).

## Gate Condition

The plan is complete when, after merge:

- both Phase 02 cross-specs (CROSS-02-02-v1, CROSS-02-03-v1) are LOCKED on master and cite the PR #209 merge SHA `ef3fc627be1793c135711b8bc3715ecda7490cf7` (2026-05-05T21:00:02Z);
- the planning directory is clean (no orphan `current_plan.critique*.md` files; `current_plan.md` placeholder; INDEX.md template);
- `planning/README.md` §Contents lifecycle table includes `current_plan.critique_resolution.md`;
- `reports/research_log.md` has the single `[CROSS] 2026-05-06` T00b activation entry;
- version is 3.46.0; CHANGELOG `[3.46.0]` stanza published with substituted PR number;
- no dataset ROADMAPs, notebooks, generated artifacts, raw data, status YAMLs, thesis chapters, per-dataset research logs, or `02_04_cross_spec_consistency_report.{json,md}` were modified.

## Out of scope

Hard exclusions (reproduced verbatim from the user-supplied binding constraint list):

- No dataset ROADMAP edits.
- No notebooks.
- No generated artifacts.
- No raw data.
- No status YAMLs.
- No thesis chapters.
- No `thesis/pass2_evidence/` deletions.
- No `thesis/reviews_and_others/` deletions.
- No file moves.
- No validator/report regeneration.
- No edits to `02_00`, `02_01`, or `scripts/validate_phase02_readiness_contracts.py`.
- No edits to per-dataset research logs.

## Open questions

None. All five PR-#209-reviewer-deep documentation-hygiene WARNINGs are addressed in this plan as mechanical edits with explicit instructions.

---
**Plan-stage critique queue:** plan ready for implementation (reviewer-deep gate already cleared).
