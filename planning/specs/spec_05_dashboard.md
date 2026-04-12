---
task_id: "T05"
task_name: "Write scripts/session_audit.py"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope: []
read_scope: []
category: "C"
---

# Spec: Test 05

## Objective

just log to stdout

## Instructions

1. Print "Hello world, this is me: <INSERT task_name HERE>!".

## Verification

- The message is in the main sessions terminal visible to user