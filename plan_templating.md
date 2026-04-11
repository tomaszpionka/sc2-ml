# Plan Templating: Adversarial Review & Recommendations

**Date:** 2026-04-11
**Reviewer:** reviewer-adversarial (Opus)
**Targets:** `docs/templates/plan_template.md`, `plan_critique_template.md`, `planner_output_contract.md`
**Context:** These were drafted by ChatGPT without knowledge of the existing DAG/spec/materialization infrastructure

---

## Executive Summary

The plan template is **unsound** — a plan conforming to it will fail `/materialize_plan` because the DAG schema, section names, and spec_file fields are all wrong. The critique template is **adequate but incomplete** — it needs citations, full invariant enumeration, and temporal discipline assessment. The planner output contract **contradicts the taxonomy** and cites a non-existent document.

All three need revision before they can gate plan production.

---

## 1. Compatibility Audit

### 1.1 [BLOCKER] Plan template DAG format is structurally incompatible

`plan_template.md` lines 29-38 define a flat `nodes:` list:
```yaml
nodes:
  - id: n01
    summary:
    inputs:
    outputs:
```

The real DAG (`dag_template.yaml` lines 47-94) uses a three-level hierarchy:
```yaml
jobs:
  - job_id: "J01"
    task_groups:
      - group_id: "TG01"
        tasks:
          - task_id: "T01"
            spec_file: "planning/specs/spec_01.md"
            file_scope: [...]
```

**Every field name differs:**

| plan_template.md | dag_template.yaml | Match? |
|------------------|-------------------|--------|
| `nodes` | `jobs[].task_groups[].tasks` | NO |
| `id: n01` | `task_id: "T01"` + `group_id` + `job_id` | NO |
| `summary` | `name` | NO |
| `inputs` | `read_scope` | NO |
| `outputs` | `file_scope` | NO |
| `reviewer` (per-node) | `review_gate` (per-task-group) | NO |
| `halts_on` | `on_blocker` (inside review_gate) | NO |
| (absent) | `spec_file` | MISSING |
| (absent) | `parallel_safe` | MISSING |
| (absent) | `plan_ref`, `dag_id`, `category`, `branch` | MISSING |

**Impact:** `/materialize_plan` will STOP because it cannot find `task_id`, `spec_file`, or `file_scope`.

### 1.2 [BLOCKER] Plan template missing 3 required sections

`/materialize_plan` expects:
1. `## Execution Steps` — content extracted into spec files
2. `## Suggested Execution Graph` — the DAG YAML
3. `## File Manifest` — all files touched

The template has `## Proposed DAG` (wrong name, wrong schema) and none of the other two.

### 1.3 [BLOCKER] Missing `spec_file` path requirement

Both planner agents mandate `spec_file` paths in the Suggested Execution Graph (planner.md:35, planner-science.md:50). The template has no `spec_file` field.

### 1.4 [BLOCKER] Contract forbids "task" — but the taxonomy defines it

`planner_output_contract.md` line 35:
> no "stage", "milestone", **"task"**, "phase 0"

But `docs/TAXONOMY.md` lines 248-264 **define** "Task" as an official operational term. The `tasks:` key is required YAML in every DAG. This is self-contradictory — a planner following this contract cannot produce a valid DAG.

The actual forbidden terms per TAXONOMY.md lines 268-288: Stage, Experiment (as formal unit), Milestone, Workstream, Track, Initiative, Epic, Component (as work unit), Section (unqualified).

### 1.5 [WARNING] Contract cites non-existent document

`planner_output_contract.md` line 4:
> see project instructions section 4.1

No "section 4.1" exists in CLAUDE.md or any project file. ChatGPT hallucination.

### 1.6 [WARNING] Contract scoped only to planner-science

Line 3: "You are the planner-science agent." But the `planner` agent (Sonnet, used for Category B/C) also produces plans that go through materialization. Either make the contract agent-agnostic or create a parallel contract.

### 1.7 [WARNING] Critique file not in planning lifecycle

`planner_output_contract.md` specifies output at `planning/current_plan.critique.md`, but `planning/README.md` does not list this file in its contents table (lines 10-19) or purge protocol (lines 49-59). After merge, stale critiques would persist.

### 1.8 [WARNING] Scope system misaligned with Category system

Template defines `scope: code | science | chore | research`.
Existing system uses `category: A | B | C | D | E | F`.

Ambiguities:
- Category B (Refactor) → `code` or `chore`?
- Category D (Bug fix) → `code`?
- Category E (Docs) → not mapped
- Category F (Thesis) → `research`? `science`?

The real plan at `planning/current_plan.md` uses `Category: C (chore)` — the Category letter, not the scope system.

---

## 2. Terminology Violations

| Term | Used in | Status per TAXONOMY.md |
|------|---------|----------------------|
| `node` | plan_template.md (6 uses) | **NOT DEFINED** — use Task/Task Group/Job |
| `task` (forbidden) | planner_output_contract.md:35 | **DEFINED AND REQUIRED** — line 248 |
| `phase 0` (forbidden) | planner_output_contract.md:35 | Correct to forbid (Phases start at 01) but cite PHASES.md not TAXONOMY.md |

---

## 3. Structural Recommendations

### 3.1 Add Citations section to critique template

Currently no way to back scientific claims with references. When the defensibility check says "rolling windows may leak," there's no place to cite Arlot & Celisse 2010.

**Add after `## Alternatives considered and rejected`:**
```markdown
## Citations

<Every scientific claim in the sections above must be traceable to a published
source. If no citation exists, the claim is opinion and must be labelled as such.
Format: [AuthorYear] Author, Title, Venue/Year — supports: <which section/claim>>

- [Author Year] ...
```

### 3.2 Enumerate all 8 invariants explicitly in critique template

The `## Invariants check` shows a partial example starting at #6. A planner might skip invariants. List all 8:

```markdown
- **#1 (per-player split)** — yes/no/n-a — ...
- **#2 (canonical nickname)** — yes/no/n-a — ...
- **#3 (temporal < T)** — yes/no/n-a — ...
- **#4 (prediction target)** — yes/no/n-a — ...
- **#5 (symmetric treatment)** — yes/no/n-a — ...
- **#6 (SQL with findings)** — yes/no/n-a — ...
- **#7 (no magic numbers)** — yes/no/n-a — ...
- **#8 (cross-game protocol)** — yes/no/n-a — ...
```

### 3.3 Add temporal discipline section to critique template (scope=science only)

Given that temporal leakage is the single most fatal thesis flaw (Invariant #3), one line in the invariants checklist is insufficient for science plans. Add:

```markdown
## Temporal discipline assessment
<Required for scope=science. For each proposed feature computation or data
split, state: what time boundary is used, what data could leak, why the
proposed approach is safe. If unsure, flag as open question.>
```

### 3.4 Add revision tracking

Plans go through revision cycles. Add to plan template frontmatter:
```yaml
revision: 1           # increment on each revision
prior_revision_sha:   # git SHA of the prior version (if revised)
```

### 3.5 Add Gate Condition section to plan template

Required by planner-science for Category A. The existing real plan has it.

### 3.6 Add Literature context section (scope=science|research)

```markdown
## Literature context
<Required for scope=science|research. What published work informs this plan?
Feeds into thesis related-work chapter and critique defensibility section.>
```

---

## 4. Missing Items

| What | Priority | Notes |
|------|----------|-------|
| `## Suggested Execution Graph` (correct schema) | BLOCKER | Replaces `## Proposed DAG` |
| `## Execution Steps` | BLOCKER | Source for spec extraction |
| `spec_file` in DAG tasks | BLOCKER | Required by materialization |
| Correct terminology (Task not node) | BLOCKER | Per TAXONOMY.md |
| `## File Manifest` | High | Required by materialization |
| `## Gate Condition` | High | Required for Category A |
| `## Citations` in critique | High | Thesis defence preparation |
| All 8 invariants enumerated | High | Prevents skipping |
| Temporal discipline section | Medium | Science plans only |
| Literature context section | Medium | Science/research plans |
| Revision tracking | Medium | Plan iteration history |
| Critique in purge protocol | Low | planning/README.md update |
| Research log entry link | Low | Category A completeness |

---

## 5. Priority Ranking

### Tier 1: Must fix (plans will fail materialization)

1. Replace flat `nodes:` with `jobs > task_groups > tasks` schema
2. Add `## Suggested Execution Graph` and `## Execution Steps` sections
3. Add `spec_file` as required field per task
4. Fix "node" → Task/Task Group/Job terminology
5. Remove false "task" prohibition from contract
6. Remove phantom "section 4.1" reference

### Tier 2: Must fix (plans will be weak at defence)

7. Add Citations section to critique template
8. Enumerate all 8 invariants in critique
9. Align scope system with Category system (or document mapping)
10. Add Gate Condition section to plan template
11. Add File Manifest section
12. Make contract agent-agnostic
13. Add revision tracking

### Tier 3: Should fix for completeness

14. Add critique file to planning/README.md lifecycle
15. Link to research log entry template
16. Add Literature context section
17. Add temporal discipline assessment to critique
18. Group frontmatter fields by concern

---

## 6. Recommended Next Steps

1. **Do not use these templates as-is.** Plans produced from them will fail materialization.
2. **Rewrite plan_template.md** using the real plan (`planning/current_plan.md`) as the reference, not the ChatGPT draft. The real plan already works with the pipeline.
3. **Fix the contract** — remove the "task" prohibition, fix the phantom reference, make it agent-agnostic.
4. **Enhance the critique template** — add Citations, enumerate all invariants, add temporal discipline for science plans.
5. **Add to planning/README.md** — include `current_plan.critique.md` in lifecycle and purge protocol.
6. **Scope this as a Category C chore** — it touches templates, agent definitions, and lifecycle docs. Estimate: 1 PR, ~6 tasks.

---

*Generated by reviewer-adversarial (Opus) from adversarial review of 3 draft templates against 8 infrastructure files.*
