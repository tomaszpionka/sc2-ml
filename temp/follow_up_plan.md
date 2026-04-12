# Category C Plan: Token Economy & Directory Indexing

**Category:** C (chore)
**Branch:** `chore/token-economy-indexing`
**Date:** 2026-04-11

---

## Scope

Two workstreams in one PR:

**A. Token economy** — trim inlined content in CLAUDE.md, ARCHITECTURE.md,
executor.md, and specs/README.md by replacing duplicated sections with pointers
to their authoritative sources. Net savings: ~2,130 tokens.

**B. Directory indexing** — add README.md or INDEX.md to 10 directories that
agents currently cannot navigate efficiently, plus clean up zero-byte untracked
stubs and the root `_current_plan.md` relic.

---

## Workstream A: Token Economy

### A.1 CLAUDE.md — trim from ~119 lines to ~92 lines (~605 tokens saved)

**A.1.1 — Replace Plan/Execute Workflow section (lines 39-57) with pointer**

Current: 16-line inline of the three-phase lifecycle with DAG details.
Replace with:

```markdown
## Plan / Execute Workflow

All non-trivial work uses the plan → materialize → execute lifecycle.
See `planning/README.md` for the full protocol. `planning/current_plan.md`
is the handoff artifact.

**Key rule:** Execution MUST NOT begin until DAG + specs exist on disk.
```

Keep the Category table (lines 49-56 in the new version) — agents need it
every session.

**A.1.2 — Delete Category A/F plan requirements (lines 58-60)**

"Category A plan must include: phase/step ref..." and "Category F: section
paths..." belong in `.claude/agents/planner-science.md` and
`.claude/agents/planner.md` where they already exist as the DAG requirement.
Delete from CLAUDE.md.

**A.1.3 — Delete PIPELINE_SECTION_STATUS.yaml from Key File Locations (line 68)**

No agent reads this at session start. The derivation chain is in
ARCHITECTURE.md. Keep only STEP_STATUS.yaml and PHASE_STATUS.yaml.

**A.1.4 — Fix stale Project Status section (lines 97-100)**

Remove the `processing.py` → `create_temporal_split()` caution — the function
no longer exists. Replace with:

```markdown
## Project Status

AoE2 placeholder exists at `src/rts_predict/aoe2/` — do not add implementation
code until instructed.
```

**A.1.5 — Trim Progress Tracking section (lines 102-109)**

Replace 7 lines with:

```markdown
## Progress Tracking

See `ARCHITECTURE.md § Progress tracking` for the full protocol.
Key: read active STEP_STATUS.yaml + PHASE_STATUS.yaml at session start.
```

**A.1.6 — Delete Parallel Executor Orchestration section (lines 79-81)**

Pure pointer content. The executor agent definition and AGENT_MANUAL.md already
cover this. Remove the section entirely.

---

### A.2 ARCHITECTURE.md — trim ~18 lines (~350 tokens saved)

**A.2.1 — Deduplicate Progress Tracking section (lines 166-186)**

The derivation chain (ROADMAP → STEP_STATUS → PIPELINE_SECTION_STATUS →
PHASE_STATUS) is described both in the Source-of-Truth Hierarchy (tier 7) and
in the Progress Tracking section. Replace the Progress Tracking re-explanation
with a pointer to tier 7:

```markdown
## Progress tracking

See Source-of-Truth tiers 7a-7c above for the status derivation chain.

Claude Code reads the active dataset's PHASE_STATUS.yaml at session start to
determine the current phase without parsing full roadmaps.

Thesis section progress is tracked in `thesis/WRITING_STATUS.md` (per-section
status) and `thesis/chapters/REVIEW_QUEUE.md` (Pass 2 review queue).

The changelog (`CHANGELOG.md`) tracks code changes per version. The research
log (`reports/research_log.md`) tracks analytical findings per phase.
```

**A.2.2 — Trim Thesis writing workflow section (lines 195-204)**

Replace with:

```markdown
## Thesis writing workflow

Two-pass: Claude Code drafts (Pass 1), Claude Chat validates (Pass 2).
See `.claude/rules/thesis-writing.md` for the full protocol (auto-loads on
thesis/ touch).
```

**A.2.3 — Trim Version management section (lines 188-193)**

Replace with:

```markdown
## Version management

Single source: `pyproject.toml`. Bump protocol in `.claude/rules/git-workflow.md`.
```

---

### A.3 executor.md — trim ~34 lines (~675 tokens saved)

**A.3.1 — Remove venv activation rule (line 36)**

Duplicates CLAUDE.md line 10, which is auto-loaded into every session. Delete.

**A.3.2 — Replace Data layout section (lines 112-131) with pointer**

Replace 18 lines with:

```markdown
## Data layout

Paths are defined in `src/rts_predict/<game>/config.py`. See `ARCHITECTURE.md`
game package contract for the full directory structure.
```

**A.3.3 — Trim Notebook workflow section (lines 82-106)**

Keep lines 82-83 (pointer to sandbox/README.md and artifact path rule). Replace
lines 84-106 with:

```markdown
See `sandbox/README.md` for cell caps, jupytext sync, nbconvert, and DuckDB
access rules.
```

---

### A.4 specs/README.md — purge ephemeral content (~400 tokens saved)

**A.4.1 — Remove PR-specific file ownership map (lines 53-77)**

The "File ownership map" and "Recommended order for specs 01-03" sections are
from a historical PR. They should have been purged per `planning/README.md`
purge protocol. Delete them, leaving only the permanent parallel execution
guide content.

---

### A.5 Cleanup

**A.5.1 — Delete root `_current_plan.md`**

Untracked relic from the `planning/` migration. No file references this path.

**A.5.2 — Delete or explain zero-byte stubs**

- `docs/ml_experiment_phases/` — 3 zero-byte untracked files (PHASES.md,
  PIPELINE_SECTIONS.md, STEPS.md). Delete if abandoned; if planned, add a
  README explaining purpose. Check with user.
- `docs/research/` — 3 zero-byte untracked files (RESEARCH_LOG.md,
  RESEARCH_LOG_ENTRY.md, ROADMAP.md). Same treatment.

---

## Workstream B: Directory Indexing

Create README.md files for 10 directories, ordered by impact. Each README is
a lightweight routing document — typically 15-30 lines, not a full manual.

### B.1 `docs/templates/README.md` (highest impact)

Map each of the 14 templates to its consumer:

```markdown
# Templates

Canonical YAML schemas for project artifacts. Each template is the single
source of truth for the structure of its target file type.

## Authoring templates (used when writing ROADMAPs and research logs)

| Template | Target file | Consumer |
|----------|-------------|----------|
| `step_template.yaml` | Step definitions in dataset ROADMAPs | planner-science |
| `phase_template.yaml` | Phase blocks in dataset ROADMAPs | planner-science |
| `pipeline_section_template.yaml` | Pipeline Section blocks in dataset ROADMAPs | planner-science |
| `dataset_roadmap_template.yaml` | Dataset ROADMAP.md structure | planner-science |
| `research_log_template.yaml` | reports/research_log.md structure | executor |
| `research_log_entry_template.yaml` | Individual research log entries | executor |
| `notebook_template.yaml` | Sandbox notebook structure | executor |
| `raw_data_readme_template.yaml` | Raw data directory READMEs | executor |

## Status tracking templates (used when creating/updating status files)

| Template | Target file | Consumer |
|----------|-------------|----------|
| `step_status_template.yaml` | STEP_STATUS.yaml | executor |
| `pipeline_section_status_template.yaml` | PIPELINE_SECTION_STATUS.yaml | executor |
| `phase_status_template.yaml` | PHASE_STATUS.yaml | executor |

## Operational templates (DAG orchestration)

| Template | Target file | Consumer |
|----------|-------------|----------|
| `dag_template.yaml` | planning/dags/DAG.yaml | parent orchestrator |
| `dag_status_template.yaml` | planning/dags/DAG_STATUS.yaml | parent orchestrator |
| `spec_template.md` | planning/specs/spec_*.md | parent orchestrator |
```

### B.2 `.claude/README.md`

```markdown
# .claude/

Claude Code configuration and agent definitions.

| Path | Purpose | Loaded when |
|------|---------|-------------|
| `agents/*.md` | Sub-agent prompt files (8 agents) | Agent is spawned |
| `rules/*.md` | Auto-loaded rules by file-pattern match | Matching file touched |
| `commands/pr.md` | PR wrap-up slash command | /pr invoked |
| `scientific-invariants.md` | Methodology constraints | Session start (Category A/F) |
| `ml-protocol.md` | ML-specific constraints | .py file touched |
| `dev-constraints.md` | Coding constraints | .py file touched |
| `thesis-formatting-rules.yaml` | PJAIT formatting thresholds | thesis/ touched |
| `settings.json` | Claude Code hooks and config | Always (by runtime) |

See `docs/agents/AGENT_MANUAL.md` for the full agent architecture.
```

### B.3 `thesis/README.md`

```markdown
# Thesis

Master's thesis chapters, figures, tables, and writing workflow.

## Key files

| File | Purpose |
|------|---------|
| `THESIS_STRUCTURE.md` | Chapter/section hierarchy — defines scope |
| `WRITING_STATUS.md` | Per-section progress tracker (DRAFT/REVIEW/FINAL) |
| `chapters/` | Chapter drafts (numbered .md files) |
| `chapters/REVIEW_QUEUE.md` | Pass 1→2 handoff queue |
| `figures/` | Thesis figures (empty until Phase 05) |
| `tables/` | Thesis tables (empty until Phase 05) |
| `references.bib` | Bibliography |

## Writing workflow

Category F work. Two-pass: Claude Code drafts (Pass 1), Claude Chat validates
(Pass 2). See `.claude/rules/thesis-writing.md` for the full protocol.
```

### B.4 `scripts/README.md`

```markdown
# Scripts

Operational scripts. Not part of the `rts_predict` package.

| Path | Purpose |
|------|---------|
| `hooks/` | Claude Code PreToolUse hooks (NOT git hooks) — see hooks/README.md |
| `sc2egset/` | SC2EGSet dataset utilities — see sc2egset/README.md |
| `debug/` | Debug/diagnostic scripts (not production) |
| `check_mirror_drift.py` | Validates sandbox↔artifacts directory mirroring |
```

### B.5 `docs/ml_experiment_lifecycle/README.md`

```markdown
# ML Experiment Lifecycle Manuals

6 methodology reference manuals, one per Phase (01-06). These are the
authoritative source for Phase definitions — `docs/PHASES.md` is derived
from them.

Read order: by Phase number. Each manual is self-contained.
See `docs/INDEX.md` for the Phase-to-manual mapping table.
```

### B.6 `src/rts_predict/sc2/README.md`

```markdown
# SC2 Game Package

StarCraft II game implementation. See `ARCHITECTURE.md` game package contract
for the required structure.

| Path | Purpose |
|------|---------|
| `cli.py` | CLI entry point (`poetry run sc2`) |
| `config.py` | Paths, constants, DB locations |
| `data/` | Processing module and raw/staging/db data dirs |
| `reports/` | Phase artifacts, ROADMAPs, status files |

## Datasets

| Dataset | ROADMAP | Status |
|---------|---------|--------|
| sc2egset | `reports/sc2egset/ROADMAP.md` | Phase 01 in progress |
```

### B.7 `src/rts_predict/aoe2/README.md`

```markdown
# AoE2 Game Package

Age of Empires II game implementation. See `ARCHITECTURE.md` game package
contract for the required structure.

**Operational status:** Data acquisition pipeline is functional (cli.py,
config.py, data/ dirs populated). Feature engineering and model code are
not yet implemented — do not add until Phase 02 begins.

| Path | Purpose |
|------|---------|
| `cli.py` | CLI entry point (`poetry run aoe2`) |
| `config.py` | Paths, constants, DB locations |
| `data/` | Raw/staging/db data dirs (2 datasets) |
| `reports/` | Phase artifacts, ROADMAPs, status files |

## Datasets

| Dataset | ROADMAP | Status |
|---------|---------|--------|
| aoe2companion | `reports/aoe2companion/ROADMAP.md` | Phase 01 in progress |
| aoestats | `reports/aoestats/ROADMAP.md` | Phase 01 in progress |
```

### B.8 `reports/README.md`

```markdown
# Reports

Cross-cutting research documentation (not dataset-specific).

| File | Purpose |
|------|---------|
| `research_log.md` | Unified chronological narrative of all findings |
| `RESEARCH_LOG_TEMPLATE.md` | Human-readable entry template (YAML schema: `docs/templates/research_log_entry_template.yaml`) |

Dataset-specific reports live in `src/rts_predict/<game>/reports/<dataset>/`.
```

### B.9 `docs/ml_experiment_phases/` — resolve or delete

These are 3 zero-byte untracked files. Two options:
- **If planned:** Add a README explaining they will hold phase-specific
  documentation extracted from the lifecycle manuals. Not yet populated.
- **If abandoned:** Delete the directory. `docs/PHASES.md` already serves as
  the phase reference.

### B.10 `docs/research/` — resolve or delete

Same as B.9. Three zero-byte untracked files with no context. Resolve with
user input.

---

## File manifest

**Workstream A — Modified files (5):**
1. `CLAUDE.md` (trim ~27 lines)
2. `ARCHITECTURE.md` (trim ~18 lines)
3. `.claude/agents/executor.md` (trim ~34 lines)
4. `planning/specs/README.md` (purge ephemeral content)
5. `CHANGELOG.md`

**Workstream A — Deleted files (1-7):**
6. `_current_plan.md` (root relic)
7-12. Zero-byte stubs in `docs/ml_experiment_phases/` and `docs/research/`
      (pending user decision — delete or explain)

**Workstream B — New files (8-10):**
13. `docs/templates/README.md`
14. `.claude/README.md`
15. `thesis/README.md`
16. `scripts/README.md`
17. `docs/ml_experiment_lifecycle/README.md`
18. `src/rts_predict/sc2/README.md`
19. `src/rts_predict/aoe2/README.md`
20. `reports/README.md`
21-22. `docs/ml_experiment_phases/README.md` and `docs/research/README.md`
       (if kept, not deleted)

---

## Design decisions

1. **README.md files are routing documents, not manuals.** Each is 15-30 lines
   with a table mapping paths to purposes. No prose explanations of how things
   work — that lives in the authoritative source each entry points to.

2. **CLAUDE.md contains only what every session needs.** The test is: "does an
   agent need this on every message, regardless of task?" If no, it's a pointer
   or it's deleted.

3. **Pointers use `§ Section name` convention** when pointing to a specific
   section within a file (e.g., "See `ARCHITECTURE.md § Progress tracking`").
   This lets agents jump to the right section without reading the whole file.

4. **Zero-byte stubs require user decision.** The plan cannot unilaterally
   delete `docs/ml_experiment_phases/` or `docs/research/` because they may
   represent planned work. The executor will ask.

---

## Gate condition

- CLAUDE.md is ≤95 lines
- ARCHITECTURE.md is ≤190 lines
- executor.md is ≤100 lines
- All 10 priority directories have a README.md
- `_current_plan.md` does not exist at repo root
- `planning/specs/README.md` contains no PR-specific ephemeral content
- No zero-byte untracked files remain in `docs/` without an explaining README

---

## Suggested Execution Graph

```
J01: Token economy + directory indexing
  TG01: Token economy (A.1-A.5)
    depends_on: []
    review_gate:
      agent: "reviewer"
      base_ref: "auto"
      scope: "diff"
      on_blocker: "halt"
    tasks:
      T01: Trim CLAUDE.md (A.1.1-A.1.6)
        agent: executor
        file_scope: [CLAUDE.md]
        parallel_safe: true
      T02: Trim ARCHITECTURE.md (A.2.1-A.2.3)
        agent: executor
        file_scope: [ARCHITECTURE.md]
        parallel_safe: true
      T03: Trim executor.md (A.3.1-A.3.3)
        agent: executor
        file_scope: [.claude/agents/executor.md]
        parallel_safe: true
      T04: Purge specs/README.md + delete _current_plan.md (A.4-A.5)
        agent: executor
        file_scope: [planning/specs/README.md, _current_plan.md]
        parallel_safe: true

  TG02: Directory indexing (B.1-B.8)
    depends_on: ["TG01"]
    review_gate:
      agent: "reviewer"
      base_ref: "auto"
      scope: "diff"
      on_blocker: "halt"
    tasks:
      T05: Create docs/templates/README.md + .claude/README.md (B.1-B.2)
        agent: executor
        file_scope: [docs/templates/README.md, .claude/README.md]
        parallel_safe: true
      T06: Create thesis/README.md + scripts/README.md (B.3-B.4)
        agent: executor
        file_scope: [thesis/README.md, scripts/README.md]
        parallel_safe: true
      T07: Create ml_experiment_lifecycle/README.md + game READMEs (B.5-B.7)
        agent: executor
        file_scope:
          - docs/ml_experiment_lifecycle/README.md
          - src/rts_predict/sc2/README.md
          - src/rts_predict/aoe2/README.md
        parallel_safe: true
      T08: Create reports/README.md + resolve stubs (B.8-B.10)
        agent: executor
        file_scope:
          - reports/README.md
          - docs/ml_experiment_phases/
          - docs/research/
        parallel_safe: true

  TG03: CHANGELOG
    depends_on: ["TG02"]
    review_gate:
      agent: "reviewer"
      base_ref: "auto"
      scope: "cumulative"
      on_blocker: "halt"
    tasks:
      T09: CHANGELOG.md entry
        agent: executor
        file_scope: [CHANGELOG.md]
        parallel_safe: false

final_review:
  agent: "reviewer-deep"
  scope: "all"
  base_ref: "auto"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```

---

## Provenance

This plan addresses findings from two adversarial reviews run on 2026-04-11:
1. Token economy audit of CLAUDE.md, ARCHITECTURE.md, executor.md
2. Directory indexing completeness audit across the full repository

Both audits were triggered by the user after the DAG orchestration infrastructure
was merged (PR #107) to ensure the documentation layer is consistent, minimal,
and navigable.

---

## Compatibility Review (2026-04-12)

**Context:** On `chore/plan-template-rewrite`, dispatch rules were added to
CLAUDE.md and executor.md (pointer dispatch, spec-first protocol), plan and
critique templates were redesigned, and the planner output contract was
rewritten. This review checks the follow-up plan against those changes.

### CONFLICT: A.1.1 — Trim Plan/Execute Workflow in CLAUDE.md

The plan wants to replace the entire Plan/Execute Workflow section (lines
39-57) with a 3-line pointer to `planning/README.md`.

**Problem:** The template rewrite added Dispatch rules (lines 61-76) to this
section. These rules were empirically validated via a canary test — without
them, the orchestrator reads the plan and duplicates spec content in dispatch
prompts. The dispatch rules are:
- Executor dispatch: pointer prompt (spec_file path only, no content)
- Review gate dispatch: diff scope
- Final review dispatch: plan_ref + spec paths + base_ref from DAG metadata
- NEVER rule in Critical Rules: don't read specs/plan when dispatching executors

**These cannot be trimmed.** They're operational — every session needs them
during DAG execution. Moving them to `planning/README.md` would break the
guarantee, because the orchestrator is told NOT to read planning files during
execution (it would never see the rules it needs to follow).

**Fix:** A.1.1 must preserve the dispatch rules. It can still trim the
lifecycle description (planning session → materialization → execution) to a
pointer, but the dispatch rules and the Critical Rules NEVER line must stay
in CLAUDE.md.

### STRUCTURAL ISSUE: Suggested Execution Graph doesn't follow DAG schema

The plan's execution graph (lines 449-530) uses pseudo-YAML without:
- `spec_file` paths per task
- `parallel_safe` flags
- Proper `review_gate` structure (missing `base_ref`, `scope`, `on_blocker`)
- DAG metadata fields (`dag_id`, `plan_ref`, `base_ref`, `default_isolation`)

This would fail `/materialize_plan`. The graph must use the real
`dag_template.yaml` schema before materialization.

**Fix:** Rewrite the Suggested Execution Graph to match `dag_template.yaml`.
This also means adding `spec_file` references to the Execution Steps, with
the per-task structure from the new plan template (Objective / Instructions /
Verification / File scope / Read scope).

### Compatible sections

A.1.2 through A.5 and all B sections (directory indexing) are compatible
with the template rewrite changes:
- A.1.2 (delete A/F plan requirements) — now covered by output contract
- A.1.3 (delete PIPELINE_SECTION_STATUS) — unrelated to dispatch rules
- A.1.4 (fix stale Project Status) — unrelated
- A.1.5 (trim Progress Tracking) — unrelated
- A.1.6 (delete Parallel Executor Orchestration) — unrelated
- A.2-A.4 (ARCHITECTURE.md, executor.md, specs/README.md) — unrelated
- B.1-B.10 (directory indexing) — unrelated

### executor.md line numbers are stale

The plan references executor.md lines 36, 82-106, 112-131 for trimming.
The template rewrite merged "Spec-first protocol" and "Read first" into
one section, shifting line numbers. The plan's executor.md tasks (A.3.1-A.3.3)
need re-targeting against the post-rewrite file.

---

## Workstream C: Template Enforcement (2026-04-12 addition)

### The enforcement question

Should template enforcement use Claude hooks, pre-commit hooks, or custom
Python scripts?

### Answer: pre-commit hook calling a custom Python script

**Not Claude hooks.** Here's why, based on the existing infrastructure:

#### What Claude hooks do in this project

From `.claude/settings.json`, Claude hooks serve two purposes:
- **Audit logging** — `log-bash.sh`, `log-subagent.sh` (never block, exit 0)
- **Operational guards** — `guard-write-path.sh`, `guard-master-branch.sh`
  (block dangerous writes, exit 2)

They are NOT used for content validation. That's what pre-commit hooks do.

#### Why Claude hooks are wrong for template enforcement

1. **Single-file visibility.** A `PreToolUse: Write` hook sees ONE file per
   invocation. Template enforcement needs cross-file validation — DAG
   `spec_file` refs must resolve to spec files on disk. Pre-commit sees all
   staged files together.

2. **Blocks the executor mid-work.** If a Claude hook rejects a Write, the
   executor gets interrupted while following its spec. The executor's job is
   to write what the spec says — validation should happen at commit time, not
   during iterative editing. Executors work, pre-commit validates, reviewer
   confirms.

3. **Non-standard.** Pre-commit hooks run regardless of who commits — Claude,
   human, or CI. Claude hooks only run inside Claude Code sessions.

4. **Latency on every write.** A PreToolUse hook fires on every Write/Edit to
   any file. Filtering by path (`planning/*`) adds complexity and still slows
   down non-planning writes with the filter check.

#### Why pre-commit is right

The project already has the exact pattern:

| Existing hook | What it does | Pattern |
|---------------|-------------|---------|
| `check_phases_drift.py` | Compares phase tables across 2 files | Cross-file structural validation |
| `check_mirror_drift.py` | Ensures test files mirror source files | Cross-file structural validation |
| ruff | Validates Python style | Single-file validation |
| jupytext | Ensures .py/.ipynb sync | Cross-file sync validation |

Template enforcement is cross-file structural validation — same category as
phases-drift and mirror-drift. Same implementation pattern: stdlib-only Python,
~150 lines, exits 1 on drift, prints specific errors.

### What the validation script should check

New script: `scripts/hooks/check_planning_drift.py`

**When `planning/current_plan.md` is staged:**
- Parse YAML frontmatter → `category`, `branch`, `date` required
- Required sections present: `## Scope`, `## Execution Steps`,
  `## File Manifest`, `## Suggested Execution Graph`
- Category A/F: also `## Assumptions`, `## Literature context`
- `## Execution Steps` has `### TNN` headers
- `## Suggested Execution Graph` contains parseable YAML

**When `planning/specs/spec_*.md` are staged:**
- YAML frontmatter has: `task_id`, `task_name`, `agent`, `dag_ref`,
  `group_id`, `file_scope`, `category`
- Sections present: `## Objective`, `## Instructions`, `## Verification`

**When `planning/dags/DAG.yaml` is staged:**
- Valid YAML
- Required fields: `dag_id`, `plan_ref`, `category`, `branch`, `base_ref`
- Every task has: `task_id`, `spec_file`, `agent`, `file_scope`, `depends_on`
- All `spec_file` refs resolve to files on disk

**Cross-file (DAG + specs both staged):**
- Every `spec_file` in DAG has a matching spec on disk
- Every spec on disk is referenced in the DAG (no orphans)

### Pre-commit config addition

```yaml
- repo: local
  hooks:
    - id: planning-drift
      name: planning artifact validation
      language: system
      entry: python scripts/hooks/check_planning_drift.py
      files: ^planning/
      pass_filenames: false
```

Budget: <1 second (YAML parse + regex). No impact on non-planning commits.

### Enforcement layering

Three layers, each catching different classes of issues:

| Layer | When | What it catches | Tool |
|-------|------|----------------|------|
| Pre-commit hook | `git commit` | Structural: missing sections, bad YAML, broken refs | `check_planning_drift.py` |
| Reviewer (per-TG) | After each task group | Quality: unclear instructions, weak verification | reviewer agent |
| Reviewer-deep (final) | After all groups | Semantic: plan-vs-reality drift, scope violations | reviewer-deep agent |

The pre-commit hook catches what a regex can find. The reviewers catch what
only an LLM can evaluate. No overlap, no gaps.

---

## Execution Recommendation

1. **Do NOT execute this plan until the template rewrite merges.** The plan
   references CLAUDE.md and executor.md at line numbers that are now stale.

2. **Before execution, revise:**
   - A.1.1: preserve dispatch rules
   - Execution graph: rewrite to real DAG schema with spec_files
   - Add Workstream C (template enforcement pre-commit hook) as a new TG
   - Re-target executor.md line references

3. **The revised plan should be materialized fresh** using the new plan
   template (after T01 from the current plan creates it).

---

*Compatibility review conducted 2026-04-12 against chore/plan-template-rewrite
branch changes (dispatch rules, spec-first protocol, template redesign).*
