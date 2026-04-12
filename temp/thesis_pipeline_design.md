# Thesis Pipeline Design: Multi-Agent DAG Architecture

**Date:** 2026-04-12
**Status:** Design note — prerequisite: sections marked DRAFTABLE

---

## Agent Capabilities for Thesis Work

| Agent | Model | Write | Web | Role in thesis pipeline |
|-------|-------|-------|-----|------------------------|
| planner-science | Opus | No | Yes | Literature research, section scoping, spec writing |
| writer-thesis | Opus | Yes* | **Yes (add)** | Section drafting with citation lookup |
| reviewer-adversarial | Opus | No | Yes | Draft review, claim-evidence audit |
| reviewer-deep | Opus | No | Yes | Cross-chapter consistency, final review |

*writer-thesis: Write/Edit allowed except reports/**

### Recommended change: Add WebSearch to writer-thesis

```yaml
# .claude/agents/writer-thesis.md frontmatter
tools: Read, Grep, Glob, Write, Edit, WebFetch, WebSearch
disallowedTools: Write(reports/**), Edit(reports/**)
```

**Why:** A writer that can't look up references during drafting leaves
[NEEDS CITATION] flags everywhere, creating unnecessary review round-trips.
WebSearch enables in-flow citation checking without self-review.

### Self-review: NO

The project proved (PR #110 plan critique split) that external review
catches what self-review misses. writer-thesis drafts; reviewer-adversarial
reviews. The Critical Review Checklist in thesis-writing.md is a self-CHECK
(structural), not a self-REVIEW (adversarial).

---

## Pipeline Architecture

### Phase 1: Planning Session (pre-DAG)

```
User: "Plan thesis chapters 1-3 drafting"
    |
    v
planner-science (Opus, WebSearch)
    |
    ├── Researches literature per section
    ├── Identifies key papers, citations
    ├── Scopes each section (what to cover, what to skip)
    ├── Notes feeding artifacts from research_log
    └── Produces plan with per-section specs containing:
        - Section scope from THESIS_STRUCTURE.md
        - Key references to cite (author, year, finding)
        - Research log entries that feed the section
        - "Must cite" list
        - "Do NOT claim" constraints
        - Expected length (character count targets)
    |
    v
reviewer-adversarial (optional critique for Category F)
    |
    v
User approves → /materialize_plan → specs + DAG
```

### Phase 2: Execution DAG (multi-job, parallel chapters)

```yaml
dag_id: "dag_thesis_chapters_1_3"
category: "F"
branch: "docs/thesis-ch1-3"

jobs:
  - job_id: "J01_ch1"
    name: "Chapter 1 — Introduction"
    task_groups:
      - group_id: "TG01_ch1"
        name: "Draft Chapter 1 sections"
        review_gate:
          agent: "reviewer-adversarial"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          # Sequential within chapter (same file)
          - task_id: "T01"
            name: "Draft §1.1 Background and motivation"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_01_s1_1_background.md"
            file_scope: ["thesis/chapters/01_introduction.md"]
            parallel_safe: false
            depends_on: []
          - task_id: "T02"
            name: "Draft §1.2 Problem statement"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_02_s1_2_problem.md"
            file_scope: ["thesis/chapters/01_introduction.md"]
            parallel_safe: false
            depends_on: ["T01"]
          - task_id: "T03"
            name: "Draft §1.3 Research questions"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_03_s1_3_questions.md"
            file_scope: ["thesis/chapters/01_introduction.md"]
            parallel_safe: false
            depends_on: ["T02"]
          - task_id: "T04"
            name: "Draft §1.4 Scope and limitations"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_04_s1_4_scope.md"
            file_scope: ["thesis/chapters/01_introduction.md"]
            parallel_safe: false
            depends_on: ["T03"]

  - job_id: "J02_ch2"
    name: "Chapter 2 — Theoretical Background"
    # Parallel with J01 — different file
    task_groups:
      - group_id: "TG01_ch2"
        name: "Draft Chapter 2 sections"
        review_gate:
          agent: "reviewer-adversarial"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T05"
            name: "Draft §2.1 RTS game characteristics"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_05_s2_1_rts.md"
            file_scope: ["thesis/chapters/02_theoretical_background.md"]
            parallel_safe: false
            depends_on: []
          - task_id: "T06"
            name: "Draft §2.2 StarCraft II (literature part)"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_06_s2_2_sc2.md"
            file_scope: ["thesis/chapters/02_theoretical_background.md"]
            parallel_safe: false
            depends_on: ["T05"]
          - task_id: "T07"
            name: "Draft §2.4 ML methods for classification"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_07_s2_4_ml.md"
            file_scope: ["thesis/chapters/02_theoretical_background.md"]
            parallel_safe: false
            depends_on: ["T06"]
          - task_id: "T08"
            name: "Draft §2.5 Player skill rating systems"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_08_s2_5_ratings.md"
            file_scope: ["thesis/chapters/02_theoretical_background.md"]
            parallel_safe: false
            depends_on: ["T07"]
          - task_id: "T09"
            name: "Draft §2.6 Evaluation metrics"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_09_s2_6_eval.md"
            file_scope: ["thesis/chapters/02_theoretical_background.md"]
            parallel_safe: false
            depends_on: ["T08"]

  - job_id: "J03_ch3"
    name: "Chapter 3 — Related Work"
    # Parallel with J01+J02 — different file
    task_groups:
      - group_id: "TG01_ch3"
        name: "Draft Chapter 3 sections"
        review_gate:
          agent: "reviewer-adversarial"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T10"
            name: "Draft §3.1 Traditional sports prediction"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_10_s3_1_sports.md"
            file_scope: ["thesis/chapters/03_related_work.md"]
            parallel_safe: false
            depends_on: []
          - task_id: "T11"
            name: "Draft §3.2 StarCraft prediction literature"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_11_s3_2_sc2_lit.md"
            file_scope: ["thesis/chapters/03_related_work.md"]
            parallel_safe: false
            depends_on: ["T10"]
          - task_id: "T12"
            name: "Draft §3.3 MOBA and other esports"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_12_s3_3_moba.md"
            file_scope: ["thesis/chapters/03_related_work.md"]
            parallel_safe: false
            depends_on: ["T11"]
          - task_id: "T13"
            name: "Draft §3.5 Research gap"
            agent: "writer-thesis"
            spec_file: "planning/specs/spec_13_s3_5_gap.md"
            file_scope: ["thesis/chapters/03_related_work.md"]
            parallel_safe: false
            depends_on: ["T12"]

final_review:
  agent: "reviewer-adversarial"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"
```

### Phase 3: Pass 2 — Claude Chat (post-DAG)

Per thesis-writing.md, user brings drafts + artifacts to Claude Chat for:
- Literature validation (are citations real? correct year/findings?)
- Methodology alignment (does the framing match the actual experiments?)
- Flag resolution ([REVIEW:], [NEEDS CITATION], etc.)
- Academic register check

---

## Why This Works Without Agent Chaining

The key insight: **specs carry the research context.**

```
Planning session:
  planner-science researches → findings go into SPEC content
                                                    |
                                                    v
Execution DAG:                                  SPEC FILE
  writer-thesis reads spec ←────────────── (key refs, scope,
       |                                    constraints, "must cite")
       ├── Drafts section
       ├── Uses WebSearch for additional citations
       └── Writes to thesis/chapters/*.md
                    |
                    v
  reviewer-adversarial reads draft + spec
       ├── Checks claim-evidence alignment
       ├── Checks citation completeness (WebSearch)
       └── Flags issues
```

No agent-to-agent messaging needed. No orchestrator file writing.
The spec is the contract — same as for code execution.

---

## Spec Template for Thesis Sections

```markdown
---
task_id: "T05"
task_name: "Draft §2.1 RTS game characteristics"
agent: "writer-thesis"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01_ch2"
file_scope:
  - "thesis/chapters/02_theoretical_background.md"
read_scope:
  - "thesis/THESIS_STRUCTURE.md"
  - "thesis/references.bib"
category: "F"
---

# Spec: Draft §2.1 RTS game characteristics

## Objective

Draft the theoretical background section on RTS game characteristics.
Target: ~3000 characters. Academic register, third person.

## Key References (from planner-science research)

- [Ontanon2013] Ontañón et al., "A Survey of Real-Time Strategy Game AI
  Research and Competition in StarCraft", 2013 — foundational RTS taxonomy
- [Robertson2014] Robertson & Watson, "A Review of Real-Time Strategy Game
  AI", 2014 — game state complexity analysis
- [Stanescu2016] Stanescu et al., "Evaluating Real-Time Strategy Game
  States Using Convolutional Neural Networks", 2016 — state representation

Use WebSearch to verify these and find 2-3 additional recent references.

## Scope

Cover:
- What defines an RTS game (real-time decisions, resource management,
  fog of war, asymmetric information)
- How RTS differs from turn-based strategy and MOBA
- Why prediction is hard (state space size, imperfect information)

Do NOT cover:
- Specific SC2 or AoE2 mechanics (those are §2.2 and §2.3)
- ML methods (that's §2.4)

## Constraints

- Every claim must cite a source. Use [AuthorYear] keys matching
  thesis/references.bib. Add new entries to references.bib if needed.
- Do NOT claim "RTS games are the most complex" without comparative
  evidence. Use "among the most complex" with citation.
- Insert [REVIEW: ...] flags for any claim you're unsure about.

## Verification

- Section is ~3000 characters
- Every factual claim has a citation
- No [NEEDS CITATION] flags left (WebSearch should resolve them)
- [REVIEW: ...] flags are present for genuinely uncertain claims
- Academic register maintained
```

---

## Prerequisite Chain

1. **Mark sections DRAFTABLE** (Category E) — `temp/plan_thesis_draftable.md`
2. **Add WebSearch to writer-thesis** — 1-line agent definition edit
3. **Planning session: scope Chapters 1-3** (Category F) — planner-science
   researches literature, produces plan with per-section specs
4. **Execution: /dag** — writer-thesis agents draft, reviewer-adversarial reviews
5. **Pass 2: Claude Chat** — external validation per thesis-writing.md

Steps 1-2 are trivial (status update + config change).
Step 3 is the heavy lift (literature research).
Steps 4-5 are mechanical (DAG execution + human review).

---

*Design note drafted 2026-04-12. Builds on the DAG execution mechanics
validated by canary tests (PR #110) and the multi-job architecture
designed for parallel dataset work.*
