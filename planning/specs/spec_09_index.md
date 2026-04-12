---
task_id: "T09"
task_name: "Update docs/INDEX.md with directory map"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "docs/INDEX.md"
read_scope: []
category: "C"
---

# Spec: Update docs/INDEX.md with directory map

## Objective

Make `docs/INDEX.md` the centralized routing hub — a single read that tells
any agent where to find anything in the project.

## Instructions

1. Read the current `docs/INDEX.md`.
2. Add a `## Directory Map` section with a table:

   | Directory | Index | Contents |
   |-----------|-------|----------|
   | `.claude/` | `.claude/README.md` | Agents, rules, commands, invariants |
   | `docs/templates/` | `docs/templates/README.md` | Template schemas |
   | `thesis/` | `thesis/README.md` | Chapters, writing workflow |
   | `scripts/` | `scripts/README.md` | Hooks, utilities, diagnostics |
   | `docs/ml_experiment_lifecycle/` | `...README.md` | Phase methodology manuals |
   | `src/rts_predict/sc2/` | `...README.md` | SC2 game package |
   | `src/rts_predict/aoe2/` | `...README.md` | AoE2 game package |
   | `reports/` | `reports/README.md` | Research log index + CROSS entries |
   | `planning/` | `planning/INDEX.md` | Active plan, DAG, specs |

3. Verify all README paths in the table resolve to files created by T05-T08.

## Verification

- `docs/INDEX.md` has `## Directory Map` section
- All 9 paths in the table resolve to existing files
- CLAUDE.md Key File Locations points here (added by T01)
