---
task_id: "T06"
task_name: "Delete static reports, update CHANGELOG"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope: []
read_scope: []
category: "C"
---

# Spec: Test 06

## Objective

just log to stdout

## Instructions

1. Print "Hello world, this is me: <INSERT task_name HERE>!".

## Verification

- The message is in the main sessions terminal visible to user