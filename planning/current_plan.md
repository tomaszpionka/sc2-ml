# Category C Plan: Research Log Decentralization

**Category:** C (chore)
**Branch:** `chore/research-log-split`
**Date:** 2026-04-12

---

## Scope

Split the unified `reports/research_log.md` into per-dataset logs at
`src/rts_predict/<game>/reports/<dataset>/research_log.md`. The root log
becomes an index with pointers + CROSS-game entries only. Migrate existing
2 entries. Update all ~25 files that reference `reports/research_log.md`.

**Source:** `research_log_decentralization.md` (design proposal)

---

## Problem Statement

The research log is the only reporting artifact that doesn't follow the
per-dataset pattern (ROADMAP, PHASE_STATUS, STEP_STATUS, artifacts/ are
all per-dataset). With 3 datasets x 7 phases, the unified log will grow to
hundreds of entries. Executors working on SC2 scan through AoE2 entries;
parallel executors on different datasets conflict on the same file.

---

## Execution Steps

### T01 — Create sc2egset research_log.md

**Objective:** Create per-dataset research log for sc2egset with migrated
Entry 2 content.

**Instructions:**
1. Read `reports/research_log.md` for Entry 2 content
2. Read `docs/templates/research_log_template.yaml` for schema
3. Create `src/rts_predict/sc2/reports/sc2egset/research_log.md`
4. Header: thesis title, "SC2 / sc2egset findings. Reverse chronological."
5. Migrate Entry 2's SC2-specific content: 22,390 files, ~214.1 GB,
   70 tournaments, two-level layout, the corrected `_data/` scanning,
   open questions about root files and no-extension files
6. Keep full entry schema (Category, Artifacts, What, Why, How, Findings,
   Decisions, Thesis mapping, Open questions) — filter to SC2 content only
7. Artifacts pointer: reference sc2egset's own artifact paths

**Verification:**
- File exists at expected path
- Contains SC2 findings from Entry 2
- Follows research_log_entry_template.yaml schema
- Does NOT contain aoe2companion or aoestats findings

**File scope:** `src/rts_predict/sc2/reports/sc2egset/research_log.md`
**Read scope:** `reports/research_log.md`, `docs/templates/research_log_entry_template.yaml`

---

### T02 — Create aoe2companion research_log.md

**Objective:** Create per-dataset research log for aoe2companion with
migrated Entry 2 content.

**Instructions:**
1. Read `reports/research_log.md` for Entry 2 content
2. Create `src/rts_predict/aoe2/reports/aoe2companion/research_log.md`
3. Header: thesis title, "AoE2 / aoe2companion findings. Reverse chronological."
4. Migrate Entry 2's aoe2companion content: 4,154 files, ~9.2 GB,
   daily matches (no gaps), daily ratings (1 gap: 2025-07-10 to 2025-07-12),
   leaderboards + profiles snapshots
5. Full entry schema, filtered to aoe2companion content only
6. Artifacts pointer: reference aoe2companion's own artifact paths

**Verification:**
- File exists, contains aoe2companion findings, follows schema
- Does NOT contain sc2egset or aoestats findings

**File scope:** `src/rts_predict/aoe2/reports/aoe2companion/research_log.md`
**Read scope:** `reports/research_log.md`

---

### T03 — Create aoestats research_log.md

**Objective:** Create per-dataset research log for aoestats with migrated
Entry 2 content.

**Instructions:**
1. Read `reports/research_log.md` for Entry 2 content
2. Create `src/rts_predict/aoe2/reports/aoestats/research_log.md`
3. Header: thesis title, "AoE2 / aoestats findings. Reverse chronological."
4. Migrate Entry 2's aoestats content: 349 files, ~3.7 GB, weekly data,
   3 gaps (43-day, 8-day, 8-day), paired matches/players mismatch (172 vs 171),
   known download failure
5. Full entry schema, filtered to aoestats content only
6. Artifacts pointer: reference aoestats's own artifact paths

**Verification:**
- File exists, contains aoestats findings, follows schema
- Does NOT contain sc2egset or aoe2companion findings

**File scope:** `src/rts_predict/aoe2/reports/aoestats/research_log.md`
**Read scope:** `reports/research_log.md`

---

### T04 — Rewrite root research_log.md as index

**Objective:** Transform root log into index + CROSS entries only.

**Instructions:**
1. Replace content of `reports/research_log.md` with:
   - Header: thesis title, explanation of per-dataset structure
   - Dataset log table with links to 3 per-dataset logs and last entry dates
   - CROSS entries section header
2. Keep Entry 1 ([CROSS] AoE2 Dataset Strategy Decision) verbatim including
   the retraction
3. Replace Entry 2 with a trimmed CROSS summary: "Step 01_01_01 file
   inventory completed across all 3 datasets. Per-dataset findings migrated
   to each dataset's research_log.md. Cross-dataset observation: all three
   raw directories are non-empty and structurally sound." Link to the 3
   per-dataset entries. Remove the full dataset-specific findings.
4. Keep the Phase migration note

**Verification:**
- Root log has links to 3 dataset logs
- Entry 1 [CROSS] retained with retraction
- Entry 2 removed
- No dataset-specific findings remain in root

**File scope:** `reports/research_log.md`
**Read scope:** none (T01-T03 must complete first)

---

### T05 — Update CLAUDE.md + executor.md

**Objective:** Update orchestrator and executor research_log references.

**Instructions:**
1. CLAUDE.md: change "update `reports/research_log.md`" → "update the
   active dataset's `research_log.md`"
2. executor.md Category A rule (~line 70): change "Update `reports/research_log.md`
   after each step" → "Update the active dataset's `research_log.md` after each step"
3. executor.md notebook workflow (~line 102): change "Update `reports/research_log.md`
   with a new entry" → "Update the active dataset's `research_log.md` with a new entry"
4. executor.md: add rule: "If a finding has cross-game implications
   (Invariant #8), also add a [CROSS] entry to `reports/research_log.md`"

**Verification:** No bare `reports/research_log.md` as destination for
dataset-specific entries in either file (CROSS context references are fine)
**File scope:** `CLAUDE.md`, `.claude/agents/executor.md`
**Read scope:** none

---

### T06 — Update reviewer-deep.md + reviewer-adversarial.md

**Objective:** Reviewers read the active dataset's log + root CROSS log.

**Instructions:**
1. reviewer-deep.md Required Reading item 7: "Read `reports/research_log.md`
   recent entries" → "Read the active dataset's `research_log.md` and
   `reports/research_log.md` (CROSS entries) — check for contradictions
   with prior findings in both"
2. reviewer-adversarial.md: same pattern for its research_log reference

**Verification:** Both files reference dataset log + root CROSS log
**File scope:** `.claude/agents/reviewer-deep.md`, `.claude/agents/reviewer-adversarial.md`
**Read scope:** none

---

### T07 — Update planner-science.md + ml-protocol.md

**Objective:** Planner checks root CROSS log + sibling dataset logs for
cross-dataset coordination.

**Instructions:**
1. planner-science.md: "check `reports/research_log.md` for sibling
   decisions" → "check `reports/research_log.md` (CROSS entries) for
   cross-game decisions, and sibling dataset research logs if coordinating
   across datasets"
2. ml-protocol.md: update any research_log references to per-dataset pattern

**Verification:** Both files reference the new structure
**File scope:** `.claude/agents/planner-science.md`, `.claude/ml-protocol.md`
**Read scope:** none

---

### T08 — Update reviewer.md + git-workflow.md + thesis-writing.md

**Objective:** Lightweight updates to remaining agent/rule files.

**Instructions:**
1. reviewer.md: "verify entry exists" → "verify entry exists in active
   dataset's `research_log.md`"
2. git-workflow.md: end-of-session checklist → "active dataset's
   research_log.md updated (mandatory for Category A)"
3. thesis-writing.md: "read relevant entry in `reports/research_log.md`"
   → "read relevant entry in the active dataset's `research_log.md`"

**Verification:** No bare `reports/research_log.md` as dataset-specific
destination in any of the 3 files
**File scope:** `.claude/agents/reviewer.md`, `.claude/rules/git-workflow.md`,
`.claude/rules/thesis-writing.md`
**Read scope:** none

---

### T09 — Update ARCHITECTURE.md + docs/INDEX.md

**Objective:** Update cross-cutting files tables.

**Instructions:**
1. ARCHITECTURE.md cross-cutting files table: research log entry →
   "Index + CROSS entries at `reports/research_log.md`; per-dataset
   findings at `<game>/reports/<dataset>/research_log.md`"
2. docs/INDEX.md: same update to research log entry

**Verification:** Both files describe the new structure
**File scope:** `ARCHITECTURE.md`, `docs/INDEX.md`
**Read scope:** none

---

### T10 — Update TAXONOMY.md + PHASES.md + STEPS.md

**Objective:** Update phase/step references to per-dataset logs.

**Instructions:**
1. docs/TAXONOMY.md: "one entry in `reports/research_log.md`" → "one entry
   in the dataset's `research_log.md`"
2. docs/PHASES.md: Phase 07 exit gate → "per-dataset `research_log.md`
   entries are current and thesis-citable"; cross-dataset coordination →
   "tracked in `reports/research_log.md` CROSS entries"
3. docs/ml_experiment_phases/PHASES.md: same as docs/PHASES.md
4. docs/ml_experiment_phases/STEPS.md: step output → "dataset's
   `research_log.md`"

**Verification:** All 4 files reference per-dataset logs for findings;
CROSS coordination references root
**File scope:** `docs/TAXONOMY.md`, `docs/PHASES.md`,
`docs/ml_experiment_phases/PHASES.md`, `docs/ml_experiment_phases/STEPS.md`
**Read scope:** none

---

### T11 — Update templates + research docs

**Objective:** Update research log templates and specification docs.

**Instructions:**
1. `docs/templates/research_log_template.yaml`: add note that per-dataset
   logs follow this schema; root log is index-only with CROSS entries
2. `docs/templates/step_template.yaml`: research_log_entry pointer →
   dataset's log
3. `docs/templates/research_log_entry_template.yaml`: note that entries
   live in per-dataset logs
4. `docs/templates/plan_template.md`: `research_log_ref` → clarify points
   to dataset's log
5. `docs/research/RESEARCH_LOG.md`: update to describe new structure
6. `docs/research/RESEARCH_LOG_ENTRY.md`: update to reference per-dataset logs

**Verification:** All 6 files describe per-dataset structure
**File scope:** `docs/templates/research_log_template.yaml`,
`docs/templates/step_template.yaml`,
`docs/templates/research_log_entry_template.yaml`,
`docs/templates/plan_template.md`, `docs/research/RESEARCH_LOG.md`,
`docs/research/RESEARCH_LOG_ENTRY.md`
**Read scope:** none

---

### T12 — Update AGENT_MANUAL.md + README.md + ROADMAPs

**Objective:** Update remaining references.

**Instructions:**
1. `docs/agents/AGENT_MANUAL.md`: update research_log references to
   per-dataset pattern
2. `README.md`: update key document pointer to describe new structure
3. 3 dataset ROADMAPs: add `research_log.md` to their contents/sibling
   files listing (it's now a sibling file in the same directory)
4. `src/rts_predict/aoe2/reports/ROADMAP.md` (game-level): change
   "recorded in `reports/research_log.md`" → "recorded in the dataset's
   `research_log.md`" (this file directs dataset-specific decision gate
   findings, not CROSS entries)

**Verification:** All 6 files reference per-dataset logs
**File scope:** `docs/agents/AGENT_MANUAL.md`, `README.md`,
`src/rts_predict/sc2/reports/sc2egset/ROADMAP.md`,
`src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md`,
`src/rts_predict/aoe2/reports/aoestats/ROADMAP.md`,
`src/rts_predict/aoe2/reports/ROADMAP.md`
**Read scope:** none

---

### T13 — CHANGELOG

**Objective:** Document the research log decentralization.

**Instructions:**
1. Under `[Unreleased]`, add:
   - Added: 3 per-dataset `research_log.md` files (sc2egset, aoe2companion,
     aoestats) with migrated Step 01_01_01 findings
   - Changed: `reports/research_log.md` rewritten as index + CROSS entries
   - Changed: ~25 files updated to reference per-dataset logs instead of
     unified log

**Verification:** CHANGELOG has entries under `[Unreleased]`
**File scope:** `CHANGELOG.md`
**Read scope:** none

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/sc2/reports/sc2egset/research_log.md` | Create |
| `src/rts_predict/aoe2/reports/aoe2companion/research_log.md` | Create |
| `src/rts_predict/aoe2/reports/aoestats/research_log.md` | Create |
| `reports/research_log.md` | Rewrite |
| `CLAUDE.md` | Update |
| `.claude/agents/executor.md` | Update |
| `.claude/agents/reviewer-deep.md` | Update |
| `.claude/agents/reviewer-adversarial.md` | Update |
| `.claude/agents/planner-science.md` | Update |
| `.claude/agents/reviewer.md` | Update |
| `.claude/rules/git-workflow.md` | Update |
| `.claude/rules/thesis-writing.md` | Update |
| `.claude/ml-protocol.md` | Update |
| `ARCHITECTURE.md` | Update |
| `docs/INDEX.md` | Update |
| `docs/TAXONOMY.md` | Update |
| `docs/PHASES.md` | Update |
| `docs/ml_experiment_phases/PHASES.md` | Update |
| `docs/ml_experiment_phases/STEPS.md` | Update |
| `docs/templates/research_log_template.yaml` | Update |
| `docs/templates/step_template.yaml` | Update |
| `docs/templates/research_log_entry_template.yaml` | Update |
| `docs/templates/plan_template.md` | Update |
| `docs/research/RESEARCH_LOG.md` | Update |
| `docs/research/RESEARCH_LOG_ENTRY.md` | Update |
| `docs/agents/AGENT_MANUAL.md` | Update |
| `README.md` | Update |
| `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` | Update |
| `src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md` | Update |
| `src/rts_predict/aoe2/reports/aoestats/ROADMAP.md` | Update |
| `src/rts_predict/aoe2/reports/ROADMAP.md` | Update |
| `CHANGELOG.md` | Update |

---

## Gate Condition

- 3 per-dataset `research_log.md` files exist with migrated Entry 2 content
- Root `reports/research_log.md` is an index with CROSS entries only
- Entry 1 [CROSS] retained in root with retraction
- Entry 2's cross-dataset summary retained as trimmed CROSS entry in root
- Full Entry 2 dataset-specific findings removed from root
- Each per-dataset log follows `research_log_entry_template.yaml` schema
- Machine-testable reference check:
  ```
  grep -rn "reports/research_log" --include="*.md" --include="*.yaml" \
    | grep -v CHANGELOG.md \
    | grep -v planning/current_plan.md \
    | grep -v "CROSS" \
    | grep -v "index" \
    | grep -v "research_log_decentralization"
  ```
  Allowed matches: only lines that reference the root log in CROSS context
  (e.g., "add a [CROSS] entry to `reports/research_log.md`") or describe the
  new structure. Any line that says "update `reports/research_log.md`" for
  dataset-specific findings is a failure.

---

## Out of Scope

- Programmatic enforcement of research log location (future pre-commit hook)
- Cross-game implication automation (manual for now — executor adds CROSS
  entry when relevant)
- Revision tracking for research log entries (git log suffices)

---

## Open questions

None.

---

## Suggested Execution Graph

```yaml
dag_id: "dag_research_log_split"
plan_ref: "planning/current_plan.md"
category: "C"
branch: "chore/research-log-split"
base_ref: "master"
default_isolation: "shared_branch"

jobs:
  - job_id: "J01"
    name: "Research log decentralization"

    task_groups:
      - group_id: "TG01"
        name: "Create per-dataset logs + rewrite root"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T01"
            name: "Create sc2egset research_log.md"
            spec_file: "planning/specs/spec_01_sc2_research_log.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "src/rts_predict/sc2/reports/sc2egset/research_log.md"
            read_scope:
              - "reports/research_log.md"
              - "docs/templates/research_log_template.yaml"
            depends_on: []
          - task_id: "T02"
            name: "Create aoe2companion research_log.md"
            spec_file: "planning/specs/spec_02_aoe2c_research_log.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "src/rts_predict/aoe2/reports/aoe2companion/research_log.md"
            read_scope:
              - "reports/research_log.md"
            depends_on: []
          - task_id: "T03"
            name: "Create aoestats research_log.md"
            spec_file: "planning/specs/spec_03_aoestats_research_log.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "src/rts_predict/aoe2/reports/aoestats/research_log.md"
            read_scope:
              - "reports/research_log.md"
            depends_on: []
          - task_id: "T04"
            name: "Rewrite root research_log.md as index"
            spec_file: "planning/specs/spec_04_root_index.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "reports/research_log.md"
            depends_on: ["T01", "T02", "T03"]

      - group_id: "TG02"
        name: "Update agent definitions + rules"
        depends_on: ["TG01"]
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T05"
            name: "Update CLAUDE.md + executor.md"
            spec_file: "planning/specs/spec_05_orchestrator_agents.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "CLAUDE.md"
              - ".claude/agents/executor.md"
            depends_on: []
          - task_id: "T06"
            name: "Update reviewer-deep.md + reviewer-adversarial.md"
            spec_file: "planning/specs/spec_06_reviewer_agents.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - ".claude/agents/reviewer-deep.md"
              - ".claude/agents/reviewer-adversarial.md"
            depends_on: []
          - task_id: "T07"
            name: "Update planner-science.md + ml-protocol.md"
            spec_file: "planning/specs/spec_07_planner_agents.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - ".claude/agents/planner-science.md"
              - ".claude/ml-protocol.md"
            depends_on: []
          - task_id: "T08"
            name: "Update reviewer.md + git-workflow.md + thesis-writing.md"
            spec_file: "planning/specs/spec_08_rules.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - ".claude/agents/reviewer.md"
              - ".claude/rules/git-workflow.md"
              - ".claude/rules/thesis-writing.md"
            depends_on: []

      - group_id: "TG03"
        name: "Update documentation + templates"
        depends_on: ["TG01"]
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T09"
            name: "Update ARCHITECTURE.md + docs/INDEX.md"
            spec_file: "planning/specs/spec_09_architecture.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "ARCHITECTURE.md"
              - "docs/INDEX.md"
            depends_on: []
          - task_id: "T10"
            name: "Update TAXONOMY.md + PHASES.md + STEPS.md"
            spec_file: "planning/specs/spec_10_phase_docs.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "docs/TAXONOMY.md"
              - "docs/PHASES.md"
              - "docs/ml_experiment_phases/PHASES.md"
              - "docs/ml_experiment_phases/STEPS.md"
            depends_on: []
          - task_id: "T11"
            name: "Update templates + research docs"
            spec_file: "planning/specs/spec_11_templates.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "docs/templates/research_log_template.yaml"
              - "docs/templates/step_template.yaml"
              - "docs/templates/research_log_entry_template.yaml"
              - "docs/templates/plan_template.md"
              - "docs/research/RESEARCH_LOG.md"
              - "docs/research/RESEARCH_LOG_ENTRY.md"
            depends_on: []
          - task_id: "T12"
            name: "Update AGENT_MANUAL.md + README.md + ROADMAPs"
            spec_file: "planning/specs/spec_12_remaining_refs.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "docs/agents/AGENT_MANUAL.md"
              - "README.md"
              - "src/rts_predict/sc2/reports/sc2egset/ROADMAP.md"
              - "src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md"
              - "src/rts_predict/aoe2/reports/aoestats/ROADMAP.md"
              - "src/rts_predict/aoe2/reports/ROADMAP.md"
            depends_on: []

      - group_id: "TG04"
        name: "CHANGELOG"
        depends_on: ["TG02", "TG03"]
        review_gate:
          agent: "reviewer"
          scope: "cumulative"
          on_blocker: "halt"
        tasks:
          - task_id: "T13"
            name: "Update CHANGELOG"
            spec_file: "planning/specs/spec_13_changelog.md"
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
