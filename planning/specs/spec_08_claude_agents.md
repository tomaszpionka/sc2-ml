---
task_id: "T08"
task_name: "Update CLAUDE.md + agent defs + rules"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "CLAUDE.md"
  - ".claude/"
read_scope: []
category: "B"
---

# Spec: Update CLAUDE.md + agent defs + rules

## Objective

Update all path references in the Claude Code configuration layer — CLAUDE.md,
agent definitions, and rule files — to reflect the new `games/<game>/datasets/<dataset>/`
structure.

## Instructions

1. **`CLAUDE.md`**:
   - Key File Locations section: update any `<game>/reports/<dataset>/` paths to
     `games/<game>/datasets/<dataset>/reports/`
   - Project Status section: update `processing.py` reference if it mentions old path
   - Any other `rts_predict/sc2` or `rts_predict/aoe2` path references

2. **`.claude/agents/planner-science.md`**: Update data layout section (6 refs).
   Search for old paths: `grep -n "rts_predict/sc2\|rts_predict/aoe2" .claude/agents/planner-science.md`

3. **`.claude/agents/reviewer.md`**: Update report artifact path (1 ref).

4. **`.claude/dev-constraints.md`**: Update data paths (4 refs).

5. **`.claude/ml-protocol.md`**: Update reports path (1 ref).

6. **`.claude/rules/python-code.md`**: Update import example and test tree example (2 refs).

7. **`.claude/scientific-invariants.md`**: Update INVARIANTS.md paths (2 refs).

## Verification

```bash
grep -rn "rts_predict/sc2\|rts_predict/aoe2" .claude/ CLAUDE.md
```
Returns zero matches (only `rts_predict/games/` references remain).

## Context

- Run grep first to find all occurrences before editing, to avoid missing any.
- This task is in TG03 and can run in parallel with T09 (docs update).
- Do not change any non-path content in these files.
