---
# Layer 1 — fixed frontmatter (mechanically validated)
plan_id:            # e.g. 2026-04-11_aoe2companion_phase01_ingest
created:            # ISO-8601
planner_model:      # e.g. claude-opus-4-6
scope:              # one of: code | science | chore | research
dataset:            # sc2egset | aoe2companion | aoestats | null  (null only if scope=chore)
phase:              # NN matching docs/PHASES.md, or null
pipeline_section:   # name from docs/PHASES.md, or null
invariants_touched: # list of invariant IDs from .claude/scientific-invariants.md, or []
source_artifacts:   # list of paths: notebooks, SQL files, prior plans, docs consulted
review_gates:       # list of DAG node ids after which a reviewer MUST run
critique_required:  # bool — true for scope=science|research, optional for code, false for chore
---

# Plan: <short title>

## Problem statement
<What is being solved and why now. 1–3 paragraphs of prose. No solution yet.>

## Assumptions & unknowns
<Required for scope=science|research. Optional for code. Omit for chore.>
- Assumption:
- Unknown:

## Proposed DAG
<THE strict section. Executors consume this. One node per atomic action.>

```yaml
nodes:
  - id: n01
    agent:        # executor | reviewer | planner-science
    summary:      # one line
    inputs:       # files, tables, prior node outputs
    outputs:      # files, artifacts, DB objects
    depends_on:   # [] or list of node ids
    reviewer:     # node id of the reviewer that gates this, or null
    halts_on:     # conditions that must stop execution and return to planner
```

## Out of scope
<Explicit non-goals. Prevents executor scope creep.>

## Open questions
<Things the planner could not resolve. Each should name who/what resolves it.>