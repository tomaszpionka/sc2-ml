---
task_id: "T03"
task_name: "Update hooks README"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "scripts/hooks/README.md"
read_scope: []
category: "C"
---

file_scope: []
read_scope: []
category: "C"
---

# Spec: Test 03

## Objective

just log to stdout

## Instructions

1. Print "Hello world, this is me: <INSERT task_name HERE>!".

## Verification

- The message is in the main sessions terminal visible to user