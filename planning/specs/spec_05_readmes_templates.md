---
task_id: "T05"
task_name: "Create docs/templates + .claude READMEs"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "docs/templates/README.md"
  - ".claude/README.md"
read_scope: []
category: "C"
---

# Spec: Create docs/templates + .claude READMEs

## Objective

Add routing READMEs to the two highest-impact undocumented directories.

## Instructions

1. `docs/templates/README.md`: Map each template to its consumer (table
   format). Group by: Authoring templates, Status tracking templates,
   Operational templates. 15-30 lines.
2. `.claude/README.md`: Map agents, rules, commands, scientific-invariants,
   ml-protocol, settings.json to their load triggers (table format).

## Verification

- Both files exist, contain routing tables
- No prose explanations — routing documents only
