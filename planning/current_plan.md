---
category: "C"
branch: "chore/token-economy-indexing"
date: "2026-04-12"
prerequisite: "Research log split (PR #111) and DAG extraction plan (PR #112) merged"
---

# Category C Plan: Token Economy, Directory Indexing & Template Enforcement

## Scope

Three workstreams in one PR:

**A. Token economy** — trim inlined content in CLAUDE.md, ARCHITECTURE.md,
and executor.md by replacing duplicated sections with pointers to their
authoritative sources. Preserves dispatch rules and spec-first protocol.

**B. Directory indexing** — add README.md to 8 directories that agents
currently cannot navigate efficiently.

**C. Template enforcement** — add `check_planning_drift.py` pre-commit hook
that validates planning artifacts (plan frontmatter, spec sections, DAG
schema, cross-file spec_file resolution).

---

## Problem Statement

1. CLAUDE.md (140 lines) contains ~35 lines of content duplicated from
   planning/README.md, ARCHITECTURE.md, and agent definitions. Each
   session loads all of it regardless of task type.
2. ARCHITECTURE.md (206 lines) has a Progress Tracking section that
   re-explains the status derivation chain already documented in tier 7.
3. executor.md (143 lines) has a 21-line Data layout section and 24-line
   Notebook workflow section that duplicate sandbox/README.md and config.py.
4. 8 directories lack README.md files, forcing agents to explore blindly.
5. No structural validation exists for planning artifacts — specs with
   missing sections or DAGs with broken spec_file refs reach commit without
   being caught.

---

## Execution Steps

### T01 — Trim CLAUDE.md

**Objective:** Remove redundant inline content while preserving dispatch
rules and operational sections.

**Instructions:**
1. Plan/Execute Workflow section (lines 40-91):
   - KEEP line 40 (`## Plan / Execute Workflow`) — section header.
   - KEEP lines 42-44 (`All non-trivial work...`) — context sentence.
   - DELETE lines 46-54 (Planning session + Materialization paragraphs).
     Replace with:
     ```
     See `planning/README.md` for the full planning and materialization protocol.
     Key rule: execution MUST NOT begin until DAG + specs exist on disk.
     ```
   - KEEP lines 56-78 (Execution paragraph + Dispatch rules) — untouched.
     These are empirically validated and must stay in CLAUDE.md.
   - KEEP lines 80-88 (Category table) — agents need this every session.
   - KEEP lines 89-91 (Category A/F content requirements) — these specify
     what goes INSIDE plan sections (function signatures, SQL, test cases)
     which is not covered by the output contract (which specifies which
     sections to include, not their content).
2. Key File Locations section: Delete line 99 (PIPELINE_SECTION_STATUS.yaml).
   Add as the last bullet: `- Directory map: \`docs/INDEX.md\``
3. Lines 110-113 (Parallel Executor Orchestration): Delete entirely — pure
   pointer content already in AGENT_MANUAL.md.
4. Lines 126-131 (Project Status): Keep the `processing.py` caution (still
   exists at `src/rts_predict/sc2/data/processing.py`). Keep AoE2 warning.
5. Lines 133-140 (Progress Tracking): Replace with:
   ```
   ## Progress Tracking
   See `ARCHITECTURE.md` for the full tracking protocol.
   Key: read active STEP_STATUS.yaml + PHASE_STATUS.yaml at session start.
   ```

**Verification:**
- CLAUDE.md under 125 lines (current: 140, ~16 lines net removed)
- Dispatch rules (lines 61-78) intact
- Critical Rules (lines 6-15) intact
- Key File Locations includes `docs/INDEX.md` pointer as last bullet
- No broken pointers

**File scope:** `CLAUDE.md`
**Read scope:** none

---

### T02 — Trim ARCHITECTURE.md

**Objective:** Deduplicate progress tracking and trim thesis/version sections.

**Instructions:**
1. Find the Progress Tracking section that re-explains the ROADMAP →
   STEP_STATUS → PIPELINE_SECTION_STATUS → PHASE_STATUS derivation chain.
   Replace with pointer to Source-of-Truth tier 7a-7c.
2. Thesis writing workflow section: Replace with 2-line pointer to
   `.claude/rules/thesis-writing.md`.
3. Version management section: Replace with 1-line pointer to
   `.claude/rules/git-workflow.md`.

**Verification:**
- ARCHITECTURE.md under 190 lines
- All pointers resolve to existing files

**File scope:** `ARCHITECTURE.md`
**Read scope:** none

---

### T03 — Trim executor.md

**Objective:** Replace data layout and notebook workflow bulk with pointers.
Do NOT touch the Read first / Spec-first protocol section.

**Instructions:**
1. Line 40 (venv activation rule in Constraints): Delete — duplicates
   CLAUDE.md line 10 which is auto-loaded into every session. Note: if
   SDK behavior changes and subagents no longer inherit CLAUDE.md, this
   rule would need to be restored. Acceptable risk for now.
2. Notebook workflow (lines 82-105): Line 82 is the section header
   (`## Notebook workflow (sandbox/)`). Line 84 is the sandbox/README.md
   pointer. Keep lines 82-86 (header + sandbox pointer + artifact path
   rule). Replace lines 87-105 with:
   ```
   See `sandbox/README.md` for cell caps, jupytext sync, nbconvert, and
   DuckDB access rules.
   ```
3. Data layout (lines 124-142): Replace with:
   ```
   ## Data layout
   Paths defined in `src/rts_predict/<game>/config.py`. See `ARCHITECTURE.md`
   game package contract for the full directory structure.
   ```

**Verification:**
- executor.md under 105 lines
- Read first / Spec-first protocol (lines 108-122) untouched
- No broken pointers

**File scope:** `.claude/agents/executor.md`
**Read scope:** none

---

### T04 — Delete phase derivative files + drift hook

**Objective:** Eliminate drift between `docs/PHASES.md` (canonical, 264 lines,
Tier 3) and its derivatives in `docs/ml_experiment_phases/`. The derivatives
are subsets of canonical content with silent structural drift that the hook
only partially detects.

**Instructions:**
1. Delete `docs/ml_experiment_phases/PHASES.md` — derivative subset of
   `docs/PHASES.md`, adds no unique content.
2. Delete `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` — derivative copy
   of Pipeline Section tables already in `docs/PHASES.md` lines 66-237.
3. Keep `docs/ml_experiment_phases/STEPS.md` — contains unique content (Step
   contract, schema, numbering convention) not found in `docs/PHASES.md`.
4. Delete `scripts/hooks/check_phases_drift.py` — no longer needed (nothing
   to drift against).
5. Remove the `phases-drift` hook entry from `.pre-commit-config.yaml`.
6. Add a 3-line README to `docs/ml_experiment_phases/`:
   ```
   # ML Experiment Phases — Supplementary Reference
   Phase and Pipeline Section definitions live in `docs/PHASES.md` (Tier 3).
   This directory contains only `STEPS.md` (Step contract and schema).
   ```

**Verification:**
- `docs/ml_experiment_phases/PHASES.md` does not exist
- `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` does not exist
- `docs/ml_experiment_phases/STEPS.md` exists (untouched)
- `scripts/hooks/check_phases_drift.py` does not exist
- `pre-commit run --all-files` passes (no missing hook)
- `docs/PHASES.md` unchanged (zero edits to the canonical source)

**File scope:** `docs/ml_experiment_phases/PHASES.md` (delete),
`docs/ml_experiment_phases/PIPELINE_SECTIONS.md` (delete),
`scripts/hooks/check_phases_drift.py` (delete),
`.pre-commit-config.yaml` (update),
`docs/ml_experiment_phases/README.md` (create)
**Read scope:** none

---

### T05 — Create docs/templates/README.md + .claude/README.md

**Objective:** Add routing READMEs to the two highest-impact undocumented
directories.

**Instructions:**
1. `docs/templates/README.md`: Map each template to its consumer (table
   format). Group by: Authoring templates, Status tracking templates,
   Operational templates. 15-30 lines.
2. `.claude/README.md`: Map agents, rules, commands, scientific-invariants,
   ml-protocol, settings.json to their load triggers (table format).

**Verification:** Both files exist, contain routing tables.
**File scope:** `docs/templates/README.md`, `.claude/README.md`
**Read scope:** none

---

### T06 — Create thesis/README.md + scripts/README.md

**Objective:** Add routing READMEs for thesis and scripts directories.

**Instructions:**
1. `thesis/README.md`: Key files table (THESIS_STRUCTURE.md,
   WRITING_STATUS.md, chapters/, figures/, tables/, references.bib).
   Mention Category F workflow.
2. `scripts/README.md`: Map hooks/, sc2egset/, debug/,
   check_mirror_drift.py, session_audit.py.

**Verification:** Both files exist with routing tables.
**File scope:** `thesis/README.md`, `scripts/README.md`
**Read scope:** none

---

### T07 — Create ml_experiment_lifecycle/README.md + game READMEs

**Objective:** Add routing READMEs for methodology manuals and game packages.

**Instructions:**
1. `docs/ml_experiment_lifecycle/README.md`: Note 6 manuals, one per Phase.
2. `src/rts_predict/sc2/README.md`: CLI, config, data, reports paths.
   Dataset table with ROADMAP link and status.
3. `src/rts_predict/aoe2/README.md`: Same pattern. Note operational status.

**Verification:** All 3 files exist with routing tables.
**File scope:** `docs/ml_experiment_lifecycle/README.md`,
`src/rts_predict/sc2/README.md`, `src/rts_predict/aoe2/README.md`
**Read scope:** none

---

### T08 — Create reports/README.md

**Objective:** Add routing README for reports directory reflecting the
per-dataset structure from the research log split.

**Instructions:**
1. `reports/README.md`: Describe root as index + CROSS entries only.
   Per-dataset reports at `src/rts_predict/<game>/reports/<dataset>/`.
   Link to research_log_template.yaml.

**Verification:** File exists. Describes the post-split structure.
**File scope:** `reports/README.md`
**Read scope:** none

---

### T09 — Update docs/INDEX.md with directory map

**Objective:** Make `docs/INDEX.md` the centralized routing hub — a single
read that tells any agent where to find anything in the project.

**Instructions:**
1. Read the current `docs/INDEX.md`.
2. Add a `## Directory Map` section with a table:

   | Directory | Index | Contents |
   |-----------|-------|----------|
   | `.claude/` | `.claude/README.md` | Agents, rules, commands, invariants |
   | `docs/templates/` | `docs/templates/README.md` | Template schemas |
   | `thesis/` | `thesis/README.md` | Chapters, writing workflow |
   | `scripts/` | `scripts/README.md` | Hooks, utilities, diagnostics |
   | `docs/ml_experiment_lifecycle/` | `...README.md` | Phase methodology manuals |
   | `src/rts_predict/sc2/` | `...README.md` | SC2 game package |
   | `src/rts_predict/aoe2/` | `...README.md` | AoE2 game package |
   | `reports/` | `reports/README.md` | Research log index + CROSS entries |
   | `planning/` | `planning/INDEX.md` | Active plan, DAG, specs |

3. Verify all README paths in the table resolve to files created by T05-T08.

**Verification:**
- `docs/INDEX.md` has `## Directory Map` section
- All 9 paths in the table resolve to existing files
- CLAUDE.md Key File Locations points here (added by T01)

**File scope:** `docs/INDEX.md`
**Read scope:** none

---

### T10 — Write check_planning_drift.py + tests

**Objective:** Create the pre-commit validation script for planning artifacts.

**Instructions:**
1. Create `scripts/hooks/check_planning_drift.py` (stdlib only, ~150 lines).
2. Validation logic when `planning/` files are staged:
   - `current_plan.md`: Parse YAML frontmatter (category, branch, date
     required). Check required sections (case-insensitive heading match):
     - Universal (all categories): `## Scope`, `## Execution Steps`,
       `## File Manifest`, `## Suggested Execution Graph`
     - Category A/F only: also `## Problem Statement`,
       `## Assumptions & unknowns`, `## Literature context`,
       `## Gate Condition`, `## Open questions`
     - Category B/D: `## Problem Statement` recommended but not enforced
     - Category C/E: `## Problem Statement` not enforced
     (Match section names from `docs/templates/plan_template.md`.)
     **Bootstrap tolerance:** If the plan has markdown-bold metadata instead
     of YAML frontmatter (legacy format), warn but do not block. Add a
     `# TODO: enforce strict YAML frontmatter after this PR` comment.
   - `specs/spec_*.md`: Parse YAML frontmatter (task_id, task_name, agent,
     dag_ref, group_id, file_scope, category). Check required sections:
     `## Objective`, `## Instructions`, `## Verification`. (`## Context`
     is optional — do not enforce, but document this in the script docstring.)
   - `dags/DAG.yaml`: Valid YAML. Required fields: dag_id, plan_ref,
     category, branch, base_ref. Every task has spec_file, file_scope,
     depends_on. All spec_file refs resolve to files on disk.
   - Cross-file: every spec_file in DAG has a matching spec; every spec on
     disk is referenced in the DAG (no orphans).
3. Follow `check_phases_drift.py` pattern: regex extraction, clear error
   messages, exit 1 on failure, stdlib only.
4. Add tests: `tests/infrastructure/test_check_planning_drift.py` — test
   valid/invalid plan frontmatter, missing spec sections, broken DAG refs,
   legacy (non-YAML) plan frontmatter warns but passes.

**Verification:**
- Script catches missing sections in plans
- Script catches broken spec_file refs in DAGs
- Script catches orphaned spec files
- Tests pass

**File scope:** `scripts/hooks/check_planning_drift.py`,
`tests/infrastructure/test_check_planning_drift.py`
**Read scope:** `scripts/hooks/check_phases_drift.py` (pattern reference)

---

### T11 — Wire pre-commit hook + test

**Objective:** Add the planning-drift hook to `.pre-commit-config.yaml`.

**Instructions:**
1. Add to `.pre-commit-config.yaml`:
   ```yaml
   - repo: local
     hooks:
       - id: planning-drift
         name: planning artifact validation
         language: system
         entry: python scripts/hooks/check_planning_drift.py
         files: ^planning/
         pass_filenames: false
   ```
2. Test: stage a spec with missing `## Objective` section, verify the hook
   blocks the commit. Restore the spec after testing.

**Verification:** `pre-commit run planning-drift` passes on valid planning
artifacts. Blocks on invalid ones.
**File scope:** `.pre-commit-config.yaml`
**Read scope:** none

---

### T12 — CHANGELOG

**Objective:** Document all three workstreams.

**Instructions:**
1. Under `[Unreleased]`, add:
   - Changed: CLAUDE.md trimmed (~16 lines removed, dispatch rules preserved)
   - Changed: ARCHITECTURE.md trimmed (~18 lines, pointers replace duplication)
   - Changed: executor.md trimmed (~40 lines, data layout + notebook workflow
     replaced with pointers)
   - Added: 8 directory README.md files (routing documents)
   - Added: `docs/INDEX.md` directory map — centralized routing hub
   - Added: `scripts/hooks/check_planning_drift.py` pre-commit hook for
     planning artifact validation
   - Added: `tests/infrastructure/test_check_planning_drift.py`
   - Removed: `docs/ml_experiment_phases/PHASES.md` (derivative of canonical
     `docs/PHASES.md`)
   - Removed: `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` (derivative)
   - Removed: `scripts/hooks/check_phases_drift.py` (no longer needed)

**Verification:** CHANGELOG has entries under `[Unreleased]`.
**File scope:** `CHANGELOG.md`
**Read scope:** none

---

## File Manifest

| File | Action |
|------|--------|
| `CLAUDE.md` | Trim |
| `ARCHITECTURE.md` | Trim |
| `.claude/agents/executor.md` | Trim |
| `docs/ml_experiment_phases/PHASES.md` | Delete |
| `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` | Delete |
| `scripts/hooks/check_phases_drift.py` | Delete |
| `docs/ml_experiment_phases/README.md` | Create |
| `docs/templates/README.md` | Create |
| `.claude/README.md` | Create |
| `thesis/README.md` | Create |
| `scripts/README.md` | Create |
| `docs/ml_experiment_lifecycle/README.md` | Create |
| `src/rts_predict/sc2/README.md` | Create |
| `src/rts_predict/aoe2/README.md` | Create |
| `reports/README.md` | Create |
| `docs/INDEX.md` | Update |
| `scripts/hooks/check_planning_drift.py` | Create |
| `tests/infrastructure/test_check_planning_drift.py` | Create |
| `.pre-commit-config.yaml` | Update |
| `CHANGELOG.md` | Update |

---

## Gate Condition

- CLAUDE.md under 125 lines; dispatch rules (current lines 61-78) intact
- ARCHITECTURE.md under 190 lines
- executor.md under 105 lines; Read first / Spec-first protocol untouched
- 8 routing README.md files exist
- `docs/INDEX.md` has `## Directory Map` with paths resolving to all 8 READMEs
- CLAUDE.md Key File Locations includes `docs/INDEX.md` pointer
- `pre-commit run planning-drift` passes on valid planning artifacts
- `pre-commit run planning-drift` blocks on: missing plan sections, missing
  spec frontmatter, broken DAG spec_file refs, orphaned specs
- `check_planning_drift.py` tests pass
- `processing.py` caution retained in CLAUDE.md (file still exists)
- `docs/ml_experiment_phases/PHASES.md` does not exist (deleted derivative)
- `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` does not exist (deleted)
- `docs/ml_experiment_phases/STEPS.md` exists (unique content, kept)
- `scripts/hooks/check_phases_drift.py` does not exist (deleted)
- `pre-commit run --all-files` passes (no missing hook reference)

---

## Out of Scope

- `_current_plan.md` root relic (already deleted)
- `planning/specs/README.md` ephemeral purge (already clean — 39 lines)
- Zero-byte stubs in `docs/` (resolved during research log split)
- Programmatic enforcement of research log location (separate future hook)
- Token economy for `docs/agents/AGENT_MANUAL.md` (large file, separate chore)
- Strict YAML frontmatter enforcement in `check_planning_drift.py` (currently
  warns on legacy format; enforce after all plans use the new template)

---

## Suggested Execution Graph

```yaml
dag_id: "dag_token_economy_indexing"
plan_ref: "planning/current_plan.md"
category: "C"
branch: "chore/token-economy-indexing"
base_ref: "master"
default_isolation: "shared_branch"

jobs:
  - job_id: "J01"
    name: "Token economy, directory indexing, template enforcement"

    task_groups:
      - group_id: "TG01"
        name: "Token economy + phase consolidation"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T01"
            name: "Trim CLAUDE.md"
            spec_file: "planning/specs/spec_01_trim_claude.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "CLAUDE.md"
            depends_on: []
          - task_id: "T02"
            name: "Trim ARCHITECTURE.md"
            spec_file: "planning/specs/spec_02_trim_architecture.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "ARCHITECTURE.md"
            depends_on: []
          - task_id: "T03"
            name: "Trim executor.md"
            spec_file: "planning/specs/spec_03_trim_executor.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - ".claude/agents/executor.md"
            depends_on: []
          - task_id: "T04"
            name: "Delete phase derivatives + drift hook"
            spec_file: "planning/specs/spec_04_phase_consolidation.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "docs/ml_experiment_phases/PHASES.md"
              - "docs/ml_experiment_phases/PIPELINE_SECTIONS.md"
              - "docs/ml_experiment_phases/README.md"
              - "scripts/hooks/check_phases_drift.py"
              - ".pre-commit-config.yaml"
            depends_on: []

      - group_id: "TG02"
        name: "Directory indexing"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T05"
            name: "Create docs/templates + .claude READMEs"
            spec_file: "planning/specs/spec_05_readmes_templates.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "docs/templates/README.md"
              - ".claude/README.md"
            depends_on: []
          - task_id: "T06"
            name: "Create thesis + scripts READMEs"
            spec_file: "planning/specs/spec_06_readmes_thesis_scripts.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "thesis/README.md"
              - "scripts/README.md"
            depends_on: []
          - task_id: "T07"
            name: "Create lifecycle + game READMEs"
            spec_file: "planning/specs/spec_07_readmes_lifecycle_games.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "docs/ml_experiment_lifecycle/README.md"
              - "src/rts_predict/sc2/README.md"
              - "src/rts_predict/aoe2/README.md"
            depends_on: []
          - task_id: "T08"
            name: "Create reports/README.md"
            spec_file: "planning/specs/spec_08_readme_reports.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "reports/README.md"
            depends_on: []
          - task_id: "T09"
            name: "Update docs/INDEX.md with directory map"
            spec_file: "planning/specs/spec_09_index.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "docs/INDEX.md"
            depends_on: ["T05", "T06", "T07", "T08"]

      - group_id: "TG03"
        name: "Template enforcement"
        depends_on: ["TG01"]
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T10"
            name: "Write check_planning_drift.py + tests"
            spec_file: "planning/specs/spec_10_planning_drift.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "scripts/hooks/check_planning_drift.py"
              - "tests/infrastructure/test_check_planning_drift.py"
            read_scope:
              - "scripts/hooks/check_phases_drift.py"
            depends_on: []
          - task_id: "T11"
            name: "Wire pre-commit hook"
            spec_file: "planning/specs/spec_11_precommit.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - ".pre-commit-config.yaml"
            depends_on: ["T10"]

      - group_id: "TG04"
        name: "CHANGELOG"
        depends_on: ["TG01", "TG02", "TG03"]
        review_gate:
          agent: "reviewer"
          scope: "cumulative"
          on_blocker: "halt"
        tasks:
          - task_id: "T12"
            name: "Update CHANGELOG"
            spec_file: "planning/specs/spec_12_changelog.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "CHANGELOG.md"
            depends_on: []

final_review:
  agent: "reviewer-deep"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```
