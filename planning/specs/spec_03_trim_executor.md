---
task_id: "T03"
task_name: "Trim executor.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - ".claude/agents/executor.md"
read_scope: []
category: "C"
---

# Spec: Trim executor.md

## Objective

Replace data layout and notebook workflow bulk with pointers. Do NOT touch
the Read first / Spec-first protocol section.

## Instructions

1. Line 40 (venv activation rule in Constraints): Delete — duplicates
   CLAUDE.md line 10 which is auto-loaded into every session.
2. Notebook workflow (lines 82-105): Line 82 is the section header
   (`## Notebook workflow (sandbox/)`). Line 84 is the sandbox/README.md
   pointer. Keep lines 82-86 (header + sandbox pointer + artifact path
   rule). Replace lines 87-105 with:
   ```
   See `sandbox/README.md` for cell caps, jupytext sync, nbconvert, and
   DuckDB access rules.
   ```
3. Data layout (lines 124-142): Replace with:
   ```
   ## Data layout
   Paths defined in `src/rts_predict/<game>/config.py`. See `ARCHITECTURE.md`
   game package contract for the full directory structure.
   ```

## Verification

- executor.md under 105 lines
- Read first / Spec-first protocol (lines 108-122) untouched
- No broken pointers
