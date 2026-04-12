---
task_id: "T01"
task_name: "Update .gitignore + settings.json"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - ".gitignore"
  - ".claude/settings.json"
read_scope: []
category: "B"
---

# Spec: Update .gitignore + settings.json

## Objective

Update data-path patterns in `.gitignore` and deny rules in `.claude/settings.json`
to match the new `games/<game>/datasets/<dataset>/` structure BEFORE any files move.
This prevents 214GB of raw data from becoming untracked during the restructure.

## Instructions

1. **`.gitignore`** — add new patterns alongside old ones (do NOT delete old patterns yet):
   ```gitignore
   # New structure: datasets/*/data/{raw,staging,db,tmp}
   **/datasets/*/data/raw/**/*
   !**/datasets/*/data/raw/*/
   !**/datasets/*/data/raw/.gitkeep
   !**/datasets/*/data/raw/**/.gitkeep
   !**/datasets/*/data/raw/README.md
   **/datasets/*/data/staging/*
   !**/datasets/*/data/staging/README.md
   !**/datasets/*/data/staging/*/
   **/datasets/*/data/staging/*/*
   !**/datasets/*/data/staging/*/.gitkeep
   **/datasets/*/data/db/*
   !**/datasets/*/data/db/.gitkeep
   !**/datasets/*/data/db/schemas/
   !**/datasets/*/data/db/schemas/*.yaml
   **/datasets/*/data/tmp/*
   !**/datasets/*/data/tmp/.gitkeep
   **/datasets/*/api/*
   !**/datasets/*/api/.gitkeep
   ```
   Also add alongside existing `src/rts_predict/*/logs/`:
   ```gitignore
   src/rts_predict/games/*/logs/
   ```
   Also add alongside existing `**/data/samples/raw/*`:
   ```gitignore
   **/datasets/*/data/samples/raw/*
   ```

2. **`.claude/settings.json`** — add new deny rules alongside the existing old ones:
   ```json
   "Write(src/**/datasets/*/data/raw/**)",
   "Edit(src/**/datasets/*/data/raw/**)"
   ```
   Keep old rules temporarily (belt + suspenders until T10 removes them).

## Verification

- `git status` shows no new untracked data files after the update
- Old patterns still match old paths (coexistence — both old and new patterns present)
- New patterns present in `.gitignore`
- New deny rules present in `.claude/settings.json`
