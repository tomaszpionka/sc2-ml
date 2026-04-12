---
task_id: "T06"
task_name: "Create thesis + scripts READMEs"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "thesis/README.md"
  - "scripts/README.md"
read_scope: []
category: "C"
---

# Spec: Create thesis + scripts READMEs

## Objective

Add routing READMEs for thesis and scripts directories.

## Instructions

1. `thesis/README.md`: Key files table (THESIS_STRUCTURE.md,
   WRITING_STATUS.md, chapters/, figures/, tables/, references.bib).
   Mention Category F workflow.
2. `scripts/README.md`: Map hooks/, sc2egset/, debug/,
   check_mirror_drift.py, session_audit.py.

## Verification

- Both files exist with routing tables
