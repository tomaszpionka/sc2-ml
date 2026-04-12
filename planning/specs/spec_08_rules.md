---
task_id: "T08"
task_name: "Update reviewer.md + git-workflow.md + thesis-writing.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - ".claude/agents/reviewer.md"
  - ".claude/rules/git-workflow.md"
  - ".claude/rules/thesis-writing.md"
read_scope: []
category: "C"
---

# Spec: Update reviewer.md + git-workflow.md + thesis-writing.md

## Objective

Lightweight updates to remaining agent/rule files.

## Instructions

1. reviewer.md: "verify entry exists" → "verify entry exists in active
   dataset's `research_log.md`"
2. git-workflow.md: end-of-session checklist → "active dataset's
   research_log.md updated (mandatory for Category A)"
3. thesis-writing.md: "read relevant entry in `reports/research_log.md`"
   → "read relevant entry in the active dataset's `research_log.md`"

## Verification

- No bare `reports/research_log.md` as dataset-specific destination in
  any of the 3 files
