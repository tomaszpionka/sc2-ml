---
task_id: "T04"
task_name: "Rewrite root research_log.md as index"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "reports/research_log.md"
read_scope: []
category: "C"
---

# Spec: Rewrite root research_log.md as index

## Objective

Transform root log into index + CROSS entries only.

## Instructions

1. Replace content of `reports/research_log.md` with:
   - Header: thesis title, explanation of per-dataset structure
   - Dataset log table with links to 3 per-dataset logs and last entry dates
   - CROSS entries section header
2. Keep Entry 1 ([CROSS] AoE2 Dataset Strategy Decision) verbatim including
   the retraction.
3. Replace Entry 2 with a trimmed CROSS summary: "Step 01_01_01 file
   inventory completed across all 3 datasets. Per-dataset findings migrated
   to each dataset's research_log.md. Cross-dataset observation: all three
   raw directories are non-empty and structurally sound." Link to the 3
   per-dataset entries. Remove the full dataset-specific findings.
4. Keep the Phase migration note.

## Verification

- Root log has links to 3 dataset logs
- Entry 1 [CROSS] retained with retraction
- Entry 2 replaced with trimmed CROSS summary (not full findings)
- No dataset-specific findings remain in root
