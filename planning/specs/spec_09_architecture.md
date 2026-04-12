---
task_id: "T09"
task_name: "Update ARCHITECTURE.md + docs/INDEX.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "ARCHITECTURE.md"
  - "docs/INDEX.md"
read_scope: []
category: "C"
---

# Spec: Update ARCHITECTURE.md + docs/INDEX.md

## Objective

Update cross-cutting files tables to describe the new per-dataset research
log structure.

## Instructions

1. ARCHITECTURE.md cross-cutting files table: research log entry →
   "Index + CROSS entries at `reports/research_log.md`; per-dataset
   findings at `<game>/reports/<dataset>/research_log.md`"
2. docs/INDEX.md: same update to research log entry.

## Verification

- Both files describe the new structure (index + per-dataset)
