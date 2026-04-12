# Category C Plan: DAG Token Economy — Review Gates, Model Hints, Spec Consolidation

**Category:** C (chore)
**Branch:** `chore/dag-token-economy`
**Date:** 2026-04-12
**Status:** Draft

---

## Scope

Four related efficiency improvements to the DAG infrastructure:

1. **Review gates optional** — intermediate task group review gates disabled
   by default; one final review at DAG end.
2. **Model hints per task** — `model` field on DAG tasks lets the orchestrator
   dispatch trivial specs to Haiku, keeping Sonnet for judgment work.
3. **Self-contained specs** — ban cross-spec references ("same as spec_03");
   specs must inline full instructions.
4. **Spec consolidation** — combine tasks that share read_scope into fewer,
   larger specs. Parameterized dataset tables for multi-dataset work.

## Problem Statement

The current DAG infrastructure burns tokens in four ways:

**Review gates:** Every task group gets a reviewer dispatch. A 5-job DAG
with 2 TGs each = 10 intermediate reviews + 1 final. The intermediates
check the same things the final review covers on the full diff, just on
smaller slices. Only cascade risk boundaries justify an intermediate gate.

**Model uniformity:** All executor tasks dispatch at the same model tier
(inherited from parent session). Trivial tasks (verbatim text insertion,
literal string replacement) run on Sonnet when Haiku would suffice. The
Agent tool already supports `model: "haiku"` — we just need a field in the
DAG for the orchestrator to read.

**Cross-spec references:** Specs like "Same pattern as spec_03. Target
paths: ..." force the executor subagent to read a second spec file,
doubling context and risking inconsistent interpretation. Each spec should
be the executor's sole input.

**Spec proliferation:** One task = one spec = one executor dispatch. Each
dispatch pays ~5-10K tokens in overhead (agent prompt + spec read +
read_scope files). When N tasks share the same read_scope (e.g., 3 datasets
all needing the same invariants + template), combining them into one spec
eliminates N-1 redundant context loads.

### Token impact example (current rerun DAG)

| Approach | Specs | Dispatches | Overhead tokens (est.) |
|----------|-------|------------|----------------------|
| Current (1:1) | 10 | 10 | ~80K |
| Consolidated | 4 | 4 | ~30K |
| Savings | -6 | -6 | ~50K (~60%) |

## Assumptions & Unknowns

- The Agent tool's `model` parameter overrides agent definition frontmatter.
  Confirmed: `Agent(subagent_type="executor", model="haiku")` works.
- No new agent definitions needed — one `executor` agent, model varies.
- Haiku-safe criteria must be conservative: if any doubt, stay on Sonnet.
- The `/materialize_plan` command generates specs from the plan. It needs
  to respect both self-contained and consolidation rules.
- Parameterized specs (one spec with a dataset table) are a convention, not
  a schema change — the executor iterates the table in the spec.
- Consolidation trades parallelism for token savings. When tasks have
  non-overlapping file_scope and can run in parallel, the planner must
  weigh: is the parallelism speedup worth the extra dispatch overhead?
  For most document-heavy tasks, no.

## Spec Consolidation Rules

When to combine specs into one:

1. **Same read_scope** — if two tasks read the same invariants/templates,
   combine to avoid redundant reads.
2. **Same logical pattern** — if N tasks do the same thing to N datasets,
   use one parameterized spec with a dataset table instead of N copies.
3. **Same task group** — tasks in the same TG are sequential anyway.
   Combining them into one spec eliminates dispatch overhead with zero
   parallelism loss.
4. **Trivial follow-on** — if task B is trivial and depends on task A's
   output, combine into one spec (the executor does A then B).

When NOT to combine:

1. **Different models** — a haiku task and a sonnet task should not share
   a spec (the combined spec runs at the higher model tier).
2. **Risk isolation** — if task A is risky and task B is safe, keep them
   separate so a failure in A doesn't block retrying B.
3. **File scope >15 files** — very large specs become hard for the executor
   to track. Split at natural boundaries.

### Parameterized spec pattern

```yaml
# In the spec:
datasets:
  - id: sc2egset
    game: sc2
    notebook: sandbox/sc2/sc2egset/.../01_01_01_file_inventory.ipynb
    research_log: src/.../sc2egset/reports/research_log.md
    artifacts_dir: src/.../sc2egset/reports/artifacts/.../
  - id: aoe2companion
    game: aoe2
    notebook: sandbox/aoe2/aoe2companion/.../01_01_01_file_inventory.ipynb
    research_log: src/.../aoe2companion/reports/research_log.md
    artifacts_dir: src/.../aoe2companion/reports/artifacts/.../
  - id: aoestats
    game: aoe2
    notebook: sandbox/aoe2/aoestats/.../01_01_01_file_inventory.ipynb
    research_log: src/.../aoestats/reports/research_log.md
    artifacts_dir: src/.../aoestats/reports/artifacts/.../

# Instructions written ONCE, executor iterates the table.
```

---

## Execution Steps

### T01 — Update DAG template (model field + optional review gate)

**Objective:** Add `model` field, make `review_gate` optional, add spec
consolidation guidance.

**Instructions:**
1. Read `docs/templates/dag_template.yaml`.
2. Add `model` field to the task schema (after `agent`):
   ```yaml
   model: "sonnet"         # OPTIONAL — omit to inherit from parent session.
     # "haiku"  — ONLY when ALL of these hold:
     #   1. All content is provided verbatim in the spec (no synthesis)
     #   2. No judgment calls (no "decide if X is interpretive")
     #   3. No negative constraints ("don't use words like...")
     #   4. No artifact reading + prose writing
     #   5. No code changes
     # "sonnet" — DEFAULT for most executor tasks
     # "opus"   — when task requires:
     #   1. Multi-file reasoning across >5 files
     #   2. Novel methodology decisions
     #   3. Complex constraint satisfaction (thesis chapters)
   ```
3. Make `review_gate` optional with a comment:
   ```yaml
   # -- Review gate (OPTIONAL — omit for most task groups) --
   # Add a review_gate only when a bad result from this group would
   # cascade into downstream groups and the final review would catch
   # it too late (after wasted execution). Most groups do not need one.
   # When omitted, only the DAG-level final_review runs.
   #
   # review_gate:
   #   agent: "reviewer"
   #   scope: "diff"
   #   on_blocker: "halt"
   ```
4. Add a comment block about spec consolidation:
   ```yaml
   # -- Spec consolidation guidance --
   # Combine tasks into fewer specs when they share read_scope or
   # operate on the same logical pattern (e.g., 3 datasets).
   # One executor with a bigger spec is cheaper than three executors
   # that each re-read the same files. Use parameterized dataset
   # tables for multi-dataset work. See plan_template.md for rules.
   ```
5. Keep the `final_review` section unchanged.

**File scope:** `docs/templates/dag_template.yaml`

---

### T02 — Update plan template (all four improvements)

**Objective:** Update the plan template with review gate, model, spec
self-containment, and consolidation guidance.

**Instructions:**
1. Read `docs/templates/plan_template.md`.
2. In the Suggested Execution Graph YAML block:
   - Remove `review_gate` blocks from example task groups.
   - Add `model` field to example tasks.
   - Add comment: `# review_gate: omitted — see dag_template.yaml`
3. Add a "Spec Design Rules" section:
   ```markdown
   ## Spec Design Rules

   1. **Self-contained.** Every spec must inline its full instructions.
      Never use "Same as spec_XX" or "Same pattern as spec_XX." If the
      plan's Execution Steps for a task reference another task, the
      materializer inlines the full instructions with substituted paths.

   2. **Consolidate by read_scope.** Tasks that share the same read_scope
      (invariants, templates) should be combined into one spec to avoid
      redundant context loads. Each dispatch pays ~5-10K tokens in overhead.

   3. **Parameterize by dataset.** When N tasks do the same thing to N
      datasets, write one spec with a dataset table. The executor iterates
      the table. Instructions appear once.

   4. **Don't mix model tiers.** A haiku task and a sonnet task need
      separate specs. The combined spec runs at the higher tier.

   5. **Cap at ~15 files.** Very large specs become hard to track. Split
      at natural boundaries.
   ```

**File scope:** `docs/templates/plan_template.md`

---

### T03 — Update normative docs (TAXONOMY + DAG README + planning README)

**Objective:** Update definitions and format docs across 3 files.

**Instructions:**

**docs/TAXONOMY.md:**
1. Task Group: change "A review gate runs automatically after every Task
   Group completes." to "A review gate MAY run after a Task Group completes
   if configured. Review gates are optional and omitted by default. The
   DAG-level final_review is the standard quality gate."
2. Task: add `model` as an optional field.
3. Update review gate / commit strategy text.

**planning/dags/README.md:**
4. Change auto-injected language to optional.
5. Replace "Review gate defaults" section with opt-in guidance + final
   reviewer by category (adversarial for A/F, Sonnet for B/C/D/E).
6. Add "Model assignment" section with haiku/sonnet/opus criteria.
7. Add "Spec consolidation" section with when-to-combine rules.

**planning/README.md:**
8. Update step 3 (Execution): "Review gates after groups that configure
   one (optional)."

**File scope:**
- `docs/TAXONOMY.md`
- `planning/dags/README.md`
- `planning/README.md`

---

### T04 — Update commands (CLAUDE.md + /dag + /materialize_plan)

**Objective:** Update dispatch rules and materialization enforcement.

**Instructions:**

**CLAUDE.md:**
1. Review gate dispatch: conditional — "If the group has a review_gate
   configured, dispatch. If not, proceed to next group."
2. Final review dispatch: Cat A/F = reviewer-adversarial, Cat B/C/D/E =
   reviewer (Sonnet).

**.claude/commands/dag.md:**
3. Review gate step: conditional dispatch.
4. Add model dispatch: "Read the task's `model` field. If present, pass as
   `model` parameter to Agent tool. If absent, omit (inherits from parent)."
5. Summary output: review gates show "skipped" for unconfigured groups.

**.claude/commands/materialize_plan.md:**
6. Self-contained spec enforcement: "If the plan says 'Same as TXX', the
   materializer MUST inline the full instructions, substituting paths."
7. Model field: "If the DAG includes `model` on a task, include it in the
   spec's YAML frontmatter."
8. Consolidation: "When the plan marks tasks for consolidation (shared
   read_scope, parameterized dataset table), produce one combined spec."

**File scope:**
- `CLAUDE.md`
- `.claude/commands/dag.md`
- `.claude/commands/materialize_plan.md`

---

### T05 — Update spec template + agent manual + test DAGs

**Objective:** Update schema, agent docs, and reference test DAGs.

**Instructions:**

**docs/templates/spec_template.md:**
1. Add `model` as optional frontmatter field (after `agent`).
2. Add `datasets` as optional frontmatter field for parameterized specs.

**docs/agents/AGENT_MANUAL.md:**
3. Review gates: optional, not automatic.
4. Model assignment guidance in agent routing section.
5. Final reviewer by category.

**tests/dags/test_01_single_job/DAG.yaml:**
6. Remove `review_gate` from task groups.
7. Add `model` field to tasks.

**tests/dags/test_02_multi_job/DAG.yaml:**
8. Same. Add a parameterized task example if applicable.

**tests/dags/README.md:**
9. Update if it references review gate behavior.

**File scope:**
- `docs/templates/spec_template.md`
- `docs/agents/AGENT_MANUAL.md`
- `tests/dags/test_01_single_job/DAG.yaml`
- `tests/dags/test_02_multi_job/DAG.yaml`
- `tests/dags/README.md`

---

## File Manifest

| File | Action |
|------|--------|
| `docs/templates/dag_template.yaml` | Add `model`, optional `review_gate`, consolidation |
| `docs/templates/plan_template.md` | Spec design rules, remove default gates, add model |
| `docs/templates/spec_template.md` | Add `model` + `datasets` to frontmatter |
| `docs/TAXONOMY.md` | Update TG + Task definitions |
| `docs/agents/AGENT_MANUAL.md` | Update routing docs |
| `planning/dags/README.md` | Update format docs |
| `planning/README.md` | Update lifecycle docs |
| `CLAUDE.md` | Update dispatch rules |
| `.claude/commands/dag.md` | Conditional gates + model dispatch |
| `.claude/commands/materialize_plan.md` | Self-contained + consolidation enforcement |
| `tests/dags/test_01_single_job/DAG.yaml` | Remove gates, add model |
| `tests/dags/test_02_multi_job/DAG.yaml` | Remove gates, add model |
| `tests/dags/README.md` | Update |

## Gate Condition

- `model` field exists in `dag_template.yaml` with assignment criteria
- `review_gate` is optional in `dag_template.yaml`
- Spec design rules documented in plan template (5 rules)
- `/materialize_plan` enforces self-contained specs + consolidation
- Spec template has `model` and `datasets` in frontmatter
- TAXONOMY.md says review gates are "optional" not "automatic"
- CLAUDE.md dispatch rules handle missing review_gate + model field
- `/dag` command dispatches with model override when specified
- `grep -c "runs automatically after every" docs/TAXONOMY.md planning/dags/README.md`
  returns 0
- Test DAGs demonstrate new conventions
- Final review section unchanged and present in all templates

## Suggested Execution Graph

```yaml
dag_id: "dag_token_economy"
plan_ref: "planning/current_plan.md"
category: "C"
branch: "chore/dag-token-economy"
base_ref: "master"
default_isolation: "shared_branch"

jobs:
  - job_id: "J01"
    name: "DAG token economy improvements"
    task_groups:
      - group_id: "TG01"
        name: "Templates"
        depends_on: []
        tasks:
          - task_id: "T01"
            name: "DAG template — model + review gate + consolidation"
            spec_file: "planning/specs/spec_01_dag_template.md"
            agent: "executor"
            model: "sonnet"
            parallel_safe: true
            file_scope:
              - "docs/templates/dag_template.yaml"
            depends_on: []
          - task_id: "T02"
            name: "Plan template — spec design rules"
            spec_file: "planning/specs/spec_02_plan_template.md"
            agent: "executor"
            model: "sonnet"
            parallel_safe: true
            file_scope:
              - "docs/templates/plan_template.md"
            depends_on: []

      - group_id: "TG02"
        name: "Docs + commands + tests"
        depends_on: ["TG01"]
        tasks:
          - task_id: "T03"
            name: "TAXONOMY + DAG README + planning README"
            spec_file: "planning/specs/spec_03_normative_docs.md"
            agent: "executor"
            model: "sonnet"
            parallel_safe: false
            file_scope:
              - "docs/TAXONOMY.md"
              - "planning/dags/README.md"
              - "planning/README.md"
            depends_on: []
          - task_id: "T04"
            name: "CLAUDE.md + /dag + /materialize_plan"
            spec_file: "planning/specs/spec_04_commands.md"
            agent: "executor"
            model: "sonnet"
            parallel_safe: false
            file_scope:
              - "CLAUDE.md"
              - ".claude/commands/dag.md"
              - ".claude/commands/materialize_plan.md"
            depends_on: []
          - task_id: "T05"
            name: "Spec template + agent manual + test DAGs"
            spec_file: "planning/specs/spec_05_schema_tests.md"
            agent: "executor"
            model: "haiku"
            parallel_safe: true
            file_scope:
              - "docs/templates/spec_template.md"
              - "docs/agents/AGENT_MANUAL.md"
              - "tests/dags/test_01_single_job/DAG.yaml"
              - "tests/dags/test_02_multi_job/DAG.yaml"
              - "tests/dags/README.md"
            depends_on: []

final_review:
  agent: "reviewer"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```

## Dependency Graph

```
TG01: T01 (dag template) + T02 (plan template)  [parallel]
  |
TG02: T03 (normative docs) + T04 (commands) + T05 (schema+tests)  [parallel]
```

5 specs, 5 dispatches. The DAG itself demonstrates all four improvements:
no intermediate review gates, model hints (1 haiku, 4 sonnet), self-contained
specs, and consolidation (T03 = 3 doc files, T04 = 3 command files,
T05 = schema + agent manual + test DAGs).

---

*Draft plan — Cat C chore. Final reviewer is Sonnet per Cat B/C/D/E rules.*
