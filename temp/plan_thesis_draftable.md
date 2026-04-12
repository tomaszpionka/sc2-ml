---
category: "E"
branch: "docs/thesis-draftable-status"
date: "2026-04-12"
planner_model: "claude-opus-4-6"
---

# Category E Plan: Mark Literature-Based Thesis Sections DRAFTABLE

## Scope

Update `thesis/WRITING_STATUS.md` to flip 13 sections from SKELETON to
DRAFTABLE. These sections have zero data dependency — they are pure
literature, framing, or methodology review that can be drafted now.

Also mark 3 sections as DRAFTABLE with revision notes (literature part
now, data part after Phase 01+).

This is a prerequisite for a future Category F plan that dispatches
parallel writer-thesis agents per section.

## Problem Statement

All 30+ thesis sections are currently SKELETON or BLOCKED. 13 of them
have notes saying "can write anytime" or "Literature" — but their status
doesn't reflect this. Agents checking WRITING_STATUS.md see SKELETON and
skip them. Flipping to DRAFTABLE signals that drafting work can begin.

## Execution Steps

### T01 — Update WRITING_STATUS.md

**Objective:** Change status of 16 sections (13 full + 3 partial).

**Instructions:**
1. Chapter 1 — flip to DRAFTABLE:
   - §1.1 Background and motivation
   - §1.2 Problem statement
   - §1.3 Research questions — add note: "Draft now; finalize after experiments"
   - §1.4 Scope and limitations — add note: "Draft now; revise after AoE2 assessment"

2. Chapter 2 — flip to DRAFTABLE:
   - §2.1 RTS game characteristics
   - §2.2 StarCraft II — add note: "Literature part draftable; data-derived
     details added after Phase 01"
   - §2.4 ML methods for classification
   - §2.5 Player skill rating systems
   - §2.6 Evaluation metrics

3. Chapter 3 — flip to DRAFTABLE:
   - §3.1 Traditional sports prediction
   - §3.2 StarCraft prediction literature
   - §3.3 MOBA and other esports
   - §3.5 Research gap

4. Chapter 4 — flip to DRAFTABLE:
   - §4.4.4 Evaluation metrics

5. Chapter 6 — flip to DRAFTABLE:
   - §6.5 Threats to validity — add note: "Start listing known threats;
     expand after experiments"

6. Chapter 7 — flip to DRAFTABLE:
   - §7.3 Future work — add note: "Accumulate ideas; finalize last"

7. Update "Last updated" date at top of file.

**Verification:**
- 16 sections show DRAFTABLE status
- Notes preserved for sections needing future revision
- BLOCKED sections unchanged (§1.5, §2.3, §3.4, all Ch.4 data sections,
  all Ch.5, remaining Ch.6-7)

**File scope:** `thesis/WRITING_STATUS.md`
**Read scope:** none

### T02 — CHANGELOG

**Objective:** Document the status update.

**Instructions:**
1. Under `[Unreleased]`:
   - Changed: `thesis/WRITING_STATUS.md` — 16 sections moved from SKELETON
     to DRAFTABLE (literature-based, zero data dependency)

**File scope:** `CHANGELOG.md`
**Read scope:** none

## File Manifest

| File | Action |
|------|--------|
| `thesis/WRITING_STATUS.md` | Update |
| `CHANGELOG.md` | Update |

## Gate Condition

- 16 sections show DRAFTABLE in WRITING_STATUS.md
- BLOCKED sections unchanged
- No DRAFTABLE section has a data dependency that isn't noted

## Suggested Execution Graph

```yaml
dag_id: "dag_thesis_draftable"
plan_ref: "planning/current_plan.md"
category: "E"
branch: "docs/thesis-draftable-status"
base_ref: "master"
default_isolation: "shared_branch"

jobs:
  - job_id: "J01"
    name: "Thesis draftable status"

    task_groups:
      - group_id: "TG01"
        name: "Status update + CHANGELOG"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "cumulative"
          on_blocker: "halt"
        tasks:
          - task_id: "T01"
            name: "Update WRITING_STATUS.md"
            spec_file: "planning/specs/spec_01_writing_status.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "thesis/WRITING_STATUS.md"
            depends_on: []
          - task_id: "T02"
            name: "Update CHANGELOG"
            spec_file: "planning/specs/spec_02_changelog.md"
            agent: "executor"
            parallel_safe: false
            file_scope:
              - "CHANGELOG.md"
            depends_on: ["T01"]

final_review:
  agent: "reviewer"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```

---

## Future: Category F Multi-Agent Thesis Drafting DAG

Once these 16 sections are DRAFTABLE, the next step is a Category F plan
that dispatches parallel writer-thesis agents. Sketch:

```yaml
# FUTURE — not this plan
dag_id: "dag_thesis_chapters_1_3"
category: "F"

jobs:
  - job_id: "J01_ch1"
    name: "Chapter 1 — Introduction"
    task_groups:
      - group_id: "TG01_ch1"
        tasks:
          - task_id: "T01"
            name: "Draft §1.1 Background and motivation"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_01_s1_1.md"
            file_scope: ["thesis/chapters/01_introduction.md"]
          - task_id: "T02"
            name: "Draft §1.2 Problem statement"
            agent: "writer-thesis"
            # NOTE: parallel_safe FALSE — same file
            parallel_safe: false
            depends_on: ["T01"]

  - job_id: "J02_ch2"
    name: "Chapter 2 — Theoretical Background"
    task_groups:
      - group_id: "TG01_ch2"
        tasks:
          - task_id: "T05"
            name: "Draft §2.1 RTS game characteristics"
            agent: "writer-thesis"
          - task_id: "T06"
            name: "Draft §2.4 ML methods"
            agent: "writer-thesis"
          # These CAN be parallel — different sections, same chapter file
          # but writer-thesis appends, so sequential is safer

  - job_id: "J03_ch3"
    name: "Chapter 3 — Related Work"
    # Same pattern — one agent per section, sequential within chapter

final_review:
  agent: "reviewer-adversarial"  # Category F — full methodology review
```

**Design decisions for the future DAG:**
- One writer-thesis agent per section (not per chapter — sections are
  the atomic unit)
- Sequential within a chapter (all write to the same file)
- Parallel across chapters (different files)
- Each spec includes: the section description from THESIS_STRUCTURE.md,
  key references to read, the research_log entries that feed it, and
  explicit "do NOT claim X without Y evidence" constraints
- reviewer-adversarial final review checks: claim-evidence alignment,
  citation completeness, scope honesty, thesis register

**Prerequisite chain:**
1. This plan (E) — mark sections DRAFTABLE ← **now**
2. Literature collection — gather key papers, create references.bib entries
3. Category F plan — dispatch writer-thesis agents per section
4. Pass 2 — Claude Chat validates each draft (per thesis-writing.md workflow)
