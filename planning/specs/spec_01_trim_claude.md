---
task_id: "T01"
task_name: "Trim CLAUDE.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "CLAUDE.md"
read_scope: []
category: "C"
---

# Spec: Trim CLAUDE.md

## Objective

Remove redundant inline content while preserving dispatch rules and
operational sections.

## Instructions

1. Plan/Execute Workflow section (lines 40-91):
   - KEEP line 40 (`## Plan / Execute Workflow`) — section header.
   - KEEP lines 42-44 (`All non-trivial work...`) — context sentence.
   - DELETE lines 46-54 (Planning session + Materialization paragraphs).
     Replace with:
     ```
     See `planning/README.md` for the full planning and materialization protocol.
     Key rule: execution MUST NOT begin until DAG + specs exist on disk.
     ```
   - KEEP lines 56-78 (Execution paragraph + Dispatch rules) — untouched.
     These are empirically validated and must stay in CLAUDE.md.
   - KEEP lines 80-88 (Category table) — agents need this every session.
   - KEEP lines 89-91 (Category A/F content requirements) — these specify
     what goes INSIDE plan sections (function signatures, SQL, test cases)
     which is not covered by the output contract.
2. Key File Locations section: Delete line 99 (PIPELINE_SECTION_STATUS.yaml).
   Add as the last bullet: `- Directory map: \`docs/INDEX.md\``
3. Lines 110-113 (Parallel Executor Orchestration): Delete entirely — pure
   pointer content already in AGENT_MANUAL.md.
4. Lines 126-131 (Project Status): Keep the `processing.py` caution (still
   exists at `src/rts_predict/sc2/data/processing.py`). Keep AoE2 warning.
5. Lines 133-140 (Progress Tracking): Replace with:
   ```
   ## Progress Tracking
   See `ARCHITECTURE.md` for the full tracking protocol.
   Key: read active STEP_STATUS.yaml + PHASE_STATUS.yaml at session start.
   ```

## Verification

- CLAUDE.md under 125 lines (current: 140, ~16 lines net removed)
- Dispatch rules (lines 61-78) intact
- Critical Rules (lines 6-15) intact
- Key File Locations includes `docs/INDEX.md` pointer as last bullet
- No broken pointers
