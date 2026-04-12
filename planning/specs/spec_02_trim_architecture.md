---
task_id: "T02"
task_name: "Trim ARCHITECTURE.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "ARCHITECTURE.md"
read_scope: []
category: "C"
---

# Spec: Trim ARCHITECTURE.md

## Objective

Deduplicate progress tracking and trim thesis/version management sections.

## Instructions

1. Find the Progress Tracking section (~lines 166-188) that re-explains
   the ROADMAP → STEP_STATUS → PIPELINE_SECTION_STATUS → PHASE_STATUS
   derivation chain. Replace with pointer to Source-of-Truth tier 7a-7c.
2. Thesis writing workflow section (~lines 197-206): Replace with 2-line
   pointer to `.claude/rules/thesis-writing.md`.
3. Version management section (~lines 190-195): Replace with 1-line pointer
   to `.claude/rules/git-workflow.md`.

## Verification

- ARCHITECTURE.md under 190 lines
- All pointers resolve to existing files
