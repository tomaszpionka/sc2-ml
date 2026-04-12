---
task_id: "T09"
task_name: "Update docs + templates + reports"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "docs/"
  - "reports/"
  - "thesis/"
  - "LATER.md"
read_scope: []
category: "B"
---

# Spec: Update docs + templates + reports

## Objective

Update all path references in documentation, templates, per-dataset files,
and top-level reports to reflect the new `games/<game>/datasets/<dataset>/`
structure. ~42 files, ~126 references total.

## Instructions

Run grep first to find all occurrences, then update:
```bash
grep -rn "rts_predict/sc2\|rts_predict/aoe2\|sc2/data\|aoe2/data\|sc2/reports\|aoe2/reports" \
  --include="*.md" --include="*.yaml" \
  docs/ reports/ thesis/ LATER.md
```

File-by-file targets:

1. **`docs/INDEX.md`** — directory map table (2 refs)
2. **`docs/TAXONOMY.md`** — artifact path example (1 ref)
3. **`docs/agents/AGENT_MANUAL.md`** — example command (1 ref)
4. **`docs/research/RESEARCH_LOG.md`** — (6 refs)
5. **`docs/research/RESEARCH_LOG_ENTRY.md`** — (4 refs)
6. **`docs/research/ROADMAP.md`** — (3 refs)
7. **`docs/templates/dag_template.yaml`** — (3 refs)
8. **`docs/templates/notebook_template.md`** — (1 ref)
9. **`docs/templates/plan_template.md`** — (1 ref)
10. **`docs/templates/raw_data_readme_template.md`** — (6 refs)
11. **`reports/research_log.md`** — dataset log links (6 refs)
12. **`reports/README.md`** — dataset log paths (2 refs)
13. **Per-dataset files** (now at new paths — update their internal self-references):
    - 3x `PHASE_STATUS.yaml` — `dataset_roadmap` self-reference
    - 3x `ROADMAP.md` — README reference
    - 3x `research_log.md` — artifact paths
    - 3x `data/raw/README.md` — heavily path-dependent (8+ refs each)
    - 3x `artifacts/01_exploration/01_acquisition/01_01_01_*.md` — absolute path in header
14. **Game READMEs** — rewrite paths table for new structure
15. **`thesis/THESIS_STRUCTURE.md`** — ROADMAP reference (1 ref)
16. **`LATER.md`** — update any remaining deferred items that reference old paths

## Verification

```bash
grep -rn "rts_predict/sc2\|rts_predict/aoe2" \
  --include="*.md" --include="*.yaml" \
  docs/ reports/ thesis/ LATER.md
```
Returns zero matches (excluding CHANGELOG).

## Context

- This task is in TG03 and can run in parallel with T08 (CLAUDE.md + agents update).
- Per-dataset files (PHASE_STATUS, ROADMAP, research_log, raw/README) were physically
  moved by T02/T03 (git mv). Their internal path references still point to old locations
  and need updating here.
- Do NOT delete old .gitignore patterns — that is T10's job.
