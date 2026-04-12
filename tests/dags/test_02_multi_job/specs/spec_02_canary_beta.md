---
task_id: "T02"
task_name: "Create beta canary file"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01_beta"
file_scope:
  - "canary/beta.txt"
read_scope: []
category: "C"
---

# Spec: Create beta canary file

## Objective

Create a canary file to verify multi-job DAG execution and the /dag skill.
This task belongs to job J02_beta (simulating a second dataset).

## Instructions

1. Create directory `canary/` at the repo root if it does not exist.
2. Create file `canary/beta.txt` with exactly this content (no trailing newline):
   ```
   MULTIJOB_BETA_e7a2_J02
   ```
3. Do NOT create any other files.

## Verification

- File `canary/beta.txt` exists
- Content is exactly `MULTIJOB_BETA_e7a2_J02`
