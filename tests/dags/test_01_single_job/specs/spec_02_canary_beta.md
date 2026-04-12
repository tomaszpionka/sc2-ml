---
task_id: "T02"
task_name: "Canary beta"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "canary/02.txt"
read_scope: []
category: "C"
---

# Spec: Canary beta

## Objective

Create a canary file to verify that the executor reads and follows spec
content rather than the dispatch prompt.

## Instructions

1. Create directory `canary/` at the repo root if it does not exist.
2. Create file `canary/02.txt` with exactly this content (no trailing newline):
   ```
   SPEC_02_CANARY_BETA_9d1e
   ```
3. Do NOT create any other files.

## Verification

- File `canary/02.txt` exists
- Content is exactly `SPEC_02_CANARY_BETA_9d1e`
