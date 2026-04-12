---
task_id: "T01"
task_name: "Create alpha canary file"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01_alpha"
file_scope:
  - "canary/alpha.txt"
read_scope: []
category: "C"
---

# Spec: Create alpha canary file

## Objective

Create a canary file to verify multi-job DAG execution and the /dag skill.
This task belongs to job J01_alpha (simulating a first dataset).

## Instructions

1. Create directory `canary/` at the repo root if it does not exist.
2. Create file `canary/alpha.txt` with exactly this content (no trailing newline):
   ```
   MULTIJOB_ALPHA_c4f8_J01
   ```
3. Do NOT create any other files.

## Verification

- File `canary/alpha.txt` exists
- Content is exactly `MULTIJOB_ALPHA_c4f8_J01`
