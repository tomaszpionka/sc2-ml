# Category A Plan: Rerun Phase 01 Step 01_01_01 (File Inventory)

**Category:** A (Phase work)
**Branch:** `feat/rerun-01-01-01`
**Phase/Step:** Phase 01, Pipeline Section 01_01 (Acquisition), Step 01_01_01
**Datasets:** sc2egset, aoe2companion, aoestats
**Date:** 2026-04-12
**Status:** Draft — waiting for token economy PR to free `current_plan.md`

---

## Scope

Rerun the 01_01_01 file inventory step for all 3 datasets to eliminate
context leak in the research log entries. The existing entries contain
interpretive claims beyond file-level scope ("daily and complete," "single
snapshots," "structurally sound"). These conclusions require content-level
knowledge that Step 01_01_01 cannot produce — it only sees the file tree.

## Problem Statement

The research log entries for Step 01_01_01 were written with implicit
knowledge about what the data represents. A file inventory should report:
- Directory tree structure (names, nesting)
- File counts per directory
- File extensions and types
- File sizes
- Date ranges extracted from filenames (pattern-based, not content-based)
- Gaps in date sequences

It should NOT report:
- What the files contain (that's 01_01_02 Schema Discovery)
- Whether data is "daily" or "weekly" (that's a content-level conclusion)
- Whether a directory is a "snapshot" (requires schema knowledge)
- Whether the data is "structurally sound" (requires content analysis)

## Context: Pipeline Section 01_01 breakdown

```
01_01_01: File Inventory
  Input:  raw/ directory
  Output: file tree, counts, types, sizes, filename-derived dates, gaps
  Scope:  filesystem-level only — do not open files

01_01_02: Schema Discovery
  Input:  raw/ files (open and read headers/schemas)
  Output: column names, types, sample rows, format details
  Scope:  file-content-level — do not analyze data semantics

01_01_03+: DuckDB Ingestion (future pipeline section or step)
  Input:  schema knowledge from 01_01_02
  Output: DuckDB tables, ingestion scripts, DDL
  Scope:  load files into queryable format

01_01_04+: Content Analysis (future)
  Input:  DuckDB tables
  Output: match/game/player counts, distributions, data quality reports
  Scope:  query-level — this is where "how many games" gets answered
```

Each step's research log entry reports ONLY what that step's artifacts
contain. No forward-referencing, no interpretive conclusions beyond scope.

## Execution Steps

### T01 — Rerun sc2egset 01_01_01

**Objective:** Clear the existing research log entry for sc2egset, rerun the
file inventory notebook, and write a clean entry from artifacts only.

**Instructions:**
1. Read `src/rts_predict/sc2/reports/sc2egset/research_log.md` — identify
   the 01_01_01 entry and delete it.
2. Read the notebook at `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`.
3. Verify the notebook calls `inventory_directory()` and writes artifacts to:
   - `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
   - `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`
4. Run fresh-kernel execution:
   `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`
5. Sync jupytext:
   `source .venv/bin/activate && poetry run jupytext --sync sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`
6. Read the produced artifacts (JSON + MD).
7. Write a new research log entry based STRICTLY on the artifacts:
   - Report: directory tree, file counts per directory, extensions, sizes,
     filename-derived date ranges, gaps
   - Do NOT interpret directory names as data semantics
   - Do NOT use words like "daily," "weekly," "snapshot," "structurally sound"
     unless they appear literally in the artifact output
   - `matches/` is a directory name — not a claim about data content
8. Verify `.ipynb` and `.py` pair are synced.

**Verification:**
- Artifacts exist and are current (timestamp matches notebook execution)
- Research log entry contains only file-level observations
- `grep -iE "daily|weekly|snapshot|structurally sound" research_log.md`
  returns zero matches outside of directory name contexts
- `.ipynb` and `.py` pair synced

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`
- `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py`
- `src/rts_predict/sc2/reports/sc2egset/research_log.md`
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/`
**Read scope:**
- `reports/research_log.md` (root CROSS log — do not modify)
- `.claude/scientific-invariants.md`
- `docs/templates/research_log_entry_template.yaml`

---

### T02 — Rerun aoe2companion 01_01_01

**Objective:** Same as T01 for aoe2companion.

**Instructions:** Same pattern as T01. Target paths:
- Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`
- Artifacts: `src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/`
- Research log: `src/rts_predict/aoe2/reports/aoe2companion/research_log.md`

Same strict scoping rules: filesystem-level observations only.

**Verification:** Same as T01 adapted to aoe2companion paths.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`
- `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py`
- `src/rts_predict/aoe2/reports/aoe2companion/research_log.md`
- `src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/`
**Read scope:**
- `.claude/scientific-invariants.md`
- `docs/templates/research_log_entry_template.yaml`

---

### T03 — Rerun aoestats 01_01_01

**Objective:** Same as T01 for aoestats.

**Instructions:** Same pattern. Target paths:
- Notebook: `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`
- Artifacts: `src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/`
- Research log: `src/rts_predict/aoe2/reports/aoestats/research_log.md`

**Verification:** Same as T01 adapted to aoestats paths.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`
- `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`
- `src/rts_predict/aoe2/reports/aoestats/research_log.md`
- `src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/`
**Read scope:**
- `.claude/scientific-invariants.md`
- `docs/templates/research_log_entry_template.yaml`

---

### T04 — Update root CROSS log

**Objective:** Replace the interpretive CROSS summary with a factual one.

**Instructions:**
1. Read `reports/research_log.md`.
2. Find the CROSS summary for 01_01_01 (if one exists from the research
   log split).
3. Replace with factual content only:
   "Step 01_01_01 file inventory completed for all 3 datasets. Per-dataset
   findings in each dataset's research_log.md. Artifacts produced at
   standard paths."
4. Do NOT include any cross-dataset comparisons or interpretive claims.
   Those belong in future steps that have the schema/content knowledge to
   make them.

**Verification:**
- Root CROSS log has a factual 01_01_01 summary
- No interpretive claims about data characteristics

**File scope:** `reports/research_log.md`
**Read scope:** none (T01-T03 must complete first)

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb` | Rerun |
| `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py` | Sync |
| `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb` | Rerun |
| `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py` | Sync |
| `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb` | Rerun |
| `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py` | Sync |
| `src/rts_predict/sc2/reports/sc2egset/research_log.md` | Rewrite entry |
| `src/rts_predict/aoe2/reports/aoe2companion/research_log.md` | Rewrite entry |
| `src/rts_predict/aoe2/reports/aoestats/research_log.md` | Rewrite entry |
| `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/` | Regenerate |
| `src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/` | Regenerate |
| `src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/` | Regenerate |
| `reports/research_log.md` | Update CROSS summary |

---

## Gate Condition

- 3 notebooks executed fresh-kernel without error
- 6 artifact files exist (JSON + MD per dataset) with current timestamps
- 3 per-dataset research log entries contain ONLY file-level observations
- Machine check: `grep -iE "daily|weekly|snapshot|structurally sound|complete\b"` on
  each dataset's research_log entry returns zero matches (excluding directory
  name literals like "`matches/`")
- Root CROSS log has factual summary (no interpretive claims)
- STEP_STATUS.yaml still shows 01_01_01 as complete for all 3 datasets
- `.ipynb` / `.py` pairs synced for all 3 notebooks

---

## Suggested Execution Graph

```yaml
dag_id: "dag_rerun_01_01_01"
plan_ref: "planning/current_plan.md"
category: "A"
branch: "feat/rerun-01-01-01"
base_ref: "master"
default_isolation: "shared_branch"

jobs:
  - job_id: "J01_sc2"
    name: "01_01_01 — sc2egset"
    task_groups:
      - group_id: "TG01_sc2"
        name: "Rerun sc2 file inventory"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T01"
            name: "Clear + rerun + log sc2egset"
            spec_file: "planning/specs/spec_01_sc2_rerun.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb"
              - "sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py"
              - "src/rts_predict/sc2/reports/sc2egset/research_log.md"
              - "src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/"
            read_scope:
              - ".claude/scientific-invariants.md"
              - "docs/templates/research_log_entry_template.yaml"
            depends_on: []

  - job_id: "J02_aoe2c"
    name: "01_01_01 — aoe2companion"
    task_groups:
      - group_id: "TG01_aoe2c"
        name: "Rerun aoe2companion file inventory"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T02"
            name: "Clear + rerun + log aoe2companion"
            spec_file: "planning/specs/spec_02_aoe2c_rerun.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb"
              - "sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py"
              - "src/rts_predict/aoe2/reports/aoe2companion/research_log.md"
              - "src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/"
            read_scope:
              - ".claude/scientific-invariants.md"
              - "docs/templates/research_log_entry_template.yaml"
            depends_on: []

  - job_id: "J03_aoestats"
    name: "01_01_01 — aoestats"
    task_groups:
      - group_id: "TG01_aoestats"
        name: "Rerun aoestats file inventory"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T03"
            name: "Clear + rerun + log aoestats"
            spec_file: "planning/specs/spec_03_aoestats_rerun.md"
            agent: "executor"
            parallel_safe: true
            file_scope:
              - "sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb"
              - "sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py"
              - "src/rts_predict/aoe2/reports/aoestats/research_log.md"
              - "src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/"
            read_scope:
              - ".claude/scientific-invariants.md"
              - "docs/templates/research_log_entry_template.yaml"
            depends_on: []

final_review:
  agent: "reviewer-adversarial"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```

---

## Open questions

- Should the notebooks be checked for content-level leaks in their markdown
  cells (e.g., conclusions that interpret directory names)? Currently the plan
  only scopes the research log entries, not the notebook prose.
- The `inventory_directory()` function — does it report anything beyond
  filesystem metadata? If it inspects file headers, that's a scope violation
  for 01_01_01.

---

*Draft plan — waiting for token economy PR to merge before writing to
current_plan.md. This will be the first real Category A multi-job DAG.*
