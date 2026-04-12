---
task_id: "T10"
task_name: "Clean up .gitignore + final verification"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - ".gitignore"
  - ".claude/settings.json"
read_scope: []
category: "B"
---

# Spec: Clean up .gitignore + final verification

## Objective

Remove old `.gitignore` data-path patterns and old settings.json deny rules now
that all data is at new paths and new patterns are confirmed working. Then run
comprehensive final verification across code, docs, and git state.

## Instructions

1. **`.gitignore`** — delete old data-path patterns (the `**/data/*/` style patterns
   added for the old structure). New `**/datasets/*/data/` patterns from T01 are
   already in place. Only remove patterns that are now superseded — verify each
   deletion won't expose data files first.

2. **`.claude/settings.json`** — remove old deny rules, keep only:
   ```json
   "Write(src/**/datasets/*/data/raw/**)",
   "Edit(src/**/datasets/*/data/raw/**)"
   ```

3. **Run comprehensive verification**:
   ```bash
   # No old import paths in Python code
   grep -rn "rts_predict\.sc2\|rts_predict\.aoe2" --include="*.py" . | grep -v .venv
   # No old paths in docs (excluding CHANGELOG and temp/)
   grep -rn "rts_predict/sc2\|rts_predict/aoe2" \
     --include="*.md" --include="*.yaml" . | grep -v CHANGELOG | grep -v temp/
   # Tests pass
   source .venv/bin/activate && poetry run pytest tests/ -v
   # Data is still gitignored
   git status | grep -E "raw/|staging/|\.parquet|\.json" | grep -v CHANGELOG \
     || echo "0 data files exposed"
   ```

## Verification

- Zero old-path matches in Python code
- Zero old-path matches in docs/yaml (excluding CHANGELOG and temp/)
- `pytest` passes
- Zero data files exposed in `git status`
- `.gitignore` contains only `**/datasets/*/data/` patterns (old patterns removed)
- `.claude/settings.json` deny rules reference only new paths

## Context

- This task depends on T08 and T09 completing first (all doc/config refs updated).
- Only remove .gitignore patterns AFTER confirming `git status` is clean with new patterns.
  Removing a pattern before data is at the new path would expose 214GB.
