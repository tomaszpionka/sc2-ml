# Parallel Dataset Architecture: Multi-Job DAGs

**Date:** 2026-04-12
**Status:** Design note (not yet planned)
**Triggered by:** Discussion about parallel planning across 3 datasets

---

## 1. The Problem

The current infrastructure assumes one plan, one DAG, one execution stream.
For Phase 02+ where all 3 datasets (sc2egset, aoe2companion, aoestats) need
the same phase work done in parallel, we need a way to orchestrate this
without multiplying entities (3 plans, 3 DAGs, 3 branches).

---

## 2. Solution: One DAG, Multiple Jobs (Occam's Razor)

The DAG template already supports multiple jobs — we've just never used it.
Jobs are independent top-level units within a DAG. Three jobs = three
independent execution streams within one DAG.

### Example DAG

```yaml
dag_id: "dag_phase02_all_datasets"
plan_ref: "planning/current_plan.md"
category: "A"
branch: "feat/phase02"

jobs:
  - job_id: "J01_sc2"
    name: "Phase 02 — sc2egset"
    task_groups:
      - group_id: "TG01_sc2"
        name: "Schema discovery"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T01"
            name: "SC2 schema discovery"
            spec_file: "planning/specs/spec_01_sc2_schema.md"
            agent: "executor"
            file_scope:
              - "src/rts_predict/sc2/..."
            parallel_safe: true
            depends_on: []

  - job_id: "J02_aoe2c"
    name: "Phase 02 — aoe2companion"
    task_groups:
      - group_id: "TG01_aoe2c"
        name: "Schema discovery"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T04"
            name: "AoE2c schema discovery"
            spec_file: "planning/specs/spec_04_aoe2c_schema.md"
            agent: "executor"
            file_scope:
              - "src/rts_predict/aoe2/data/aoe2companion/..."
            parallel_safe: true
            depends_on: []

  - job_id: "J03_aoestats"
    name: "Phase 02 — aoestats"
    task_groups:
      - group_id: "TG01_aoestats"
        name: "Schema discovery"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T07"
            name: "AoE2 stats schema discovery"
            spec_file: "planning/specs/spec_07_aoestats_schema.md"
            agent: "executor"
            file_scope:
              - "src/rts_predict/aoe2/data/aoestats/..."
            parallel_safe: true
            depends_on: []

final_review:
  agent: "reviewer-adversarial"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```

### Why this works

- **Jobs are independent.** No `depends_on` between jobs = orchestrator can
  dispatch J01, J02, J03 in parallel (or sequentially, its call).
- **File scopes don't overlap.** SC2 tasks write to `src/rts_predict/sc2/`,
  AoE2 to `src/rts_predict/aoe2/`. Parallel-safe by directory isolation.
- **One plan, one DAG, one branch, one PR.** No entity multiplication.
- **Final reviewer-adversarial sees everything.** Cross-game consistency
  (Invariant #8) is checkable because all 3 datasets' changes are in one diff.
- **Cross-dataset dependencies are expressible.** If aoestats needs SC2
  findings first, add `depends_on: ["J01_sc2"]` on J03. If not, leave
  them independent.

---

## 3. Spec Naming Convention

Specs stay flat with the dataset in the slug:

```
planning/specs/spec_01_sc2_schema.md
planning/specs/spec_02_sc2_features.md
planning/specs/spec_03_sc2_validation.md
planning/specs/spec_04_aoe2c_schema.md
planning/specs/spec_05_aoe2c_features.md
planning/specs/spec_06_aoe2c_validation.md
planning/specs/spec_07_aoestats_schema.md
...
```

Global unique task IDs (T01-TNN), dataset context in the filename. No
subdirectories, no cardinality prefixes. The DAG's job structure carries
the grouping.

**Why not `spec_01_01.md` (plan cardinality)?** Collides visually with the
existing numbering convention (Phase_PipelineSection_Step uses the same
`NN_NN` pattern). The slug is unambiguous.

**Why not per-dataset subdirectories?** Unnecessary complexity when the slug
carries the context and task IDs are globally unique within the DAG.

---

## 4. Planning Workflow

### Level 1: Main session orchestrates planning (interactive, pre-DAG)

1. Main session dispatches 3 planner-science agents in parallel
2. Each planner returns plan text → main session writes ONE unified plan
3. Main session dispatches 3 reviewer-adversarial agents for critique
4. User reviews plan + critiques
5. Materialize → one DAG + all specs

### Level 2: DAG orchestrates execution (mechanical, post-materialization)

1. "Execute the DAG" → orchestrator reads DAG, sees 3 jobs
2. Dispatches jobs (parallel if independent, sequential if dependent)
3. Within each job: standard task group → review gate → next group flow
4. Final review: reviewer-adversarial sees all 3 datasets' changes

### Why planning stays outside the DAG

Planner agents are read-only (no Write/Edit tools). They return output to
the main session, which writes the plan file. This is an interactive step
(user reviews, approves, revises) — not something a DAG should automate.

The DAG handles execution. The main session handles planning. Two levels
of orchestration, each doing what it's good at.

---

## 5. Tool Constraints Reference

| Agent | Can Write? | DAG task role |
|-------|-----------|---------------|
| executor | Yes | Standard task execution |
| writer-thesis | Yes (except reports/) | Thesis chapter drafting |
| planner-science | No (read-only) | Returns output to orchestrator |
| planner | No (read-only) | Returns output to orchestrator |
| reviewer-adversarial | No (disallowed) | Returns review to orchestrator |
| reviewer-deep | No (disallowed) | Returns review to orchestrator |
| reviewer | No (no Write in tools) | Returns review to orchestrator |

Read-only agents can be `agent:` values in DAG tasks, but the orchestrator
must handle their output (write to file, act on verdict). The agent field
in the DAG template is not restricted to executors.

---

## 6. What Needs Building (when ready)

| Change | Scope |
|--------|-------|
| DAG template `agent` comment update | Done (2026-04-12, this branch) |
| Orchestrator multi-job dispatch logic | Document in CLAUDE.md execution rules |
| Plan template multi-dataset example | Add to plan template (Execution Steps per job) |
| `/materialize_plan` multi-job support | Verify it handles multiple jobs correctly |
| Smoke test with multi-job canary DAG | Before first real multi-dataset plan |

---

*Design note drafted 2026-04-12 from parallel dataset architecture discussion.*
