---
task_id: "T04"
task_name: "Migrate old logs — stage, prepend, cleanup"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope: []
read_scope: []
category: "C"
---

# Spec: Test 04

## Objective

just log to stdout

## Instructions

1. Print "Hello world, this is me: <INSERT task_name HERE>!".

## Verification

- The message is in the main sessions terminal visible to user