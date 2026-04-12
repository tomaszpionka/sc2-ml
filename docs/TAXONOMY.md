# Project Taxonomy

Single source of truth for terminology used across the `rts-outcome-prediction`
repository. Every other file that uses one of these terms does so by pointing
at this document. When a new term is added, edit this file only.

This file defines terminology only. It does not enumerate the canonical Phase
list — that lives in [`docs/PHASES.md`](PHASES.md). It does not catalogue where
each term is currently used — that is the job of the files that use them.

> **Usage note:** This file is reference documentation, not auto-loaded
> context. Agents should read it on demand when terminology is ambiguous,
> not at session start. For the Phase list itself, see `docs/PHASES.md`.

---

## The three-level work hierarchy

Work on the thesis pipeline is organised in three nested levels. The hierarchy
mirrors the structure of the methodology in `docs/ml_experiment_lifecycle/` so
that every unit of work has a traceable lineage back to a manual.

```
Phase             01              one manual's worth of lifecycle work
  Pipeline Section  01_01         one top-level section within that manual
    Step              01_01_01    one notebook + its artifacts
```

### Phase

A Phase is one unit of the ML experiment lifecycle, corresponding to one of
the numbered manuals in `docs/ml_experiment_lifecycle/` (plus the thesis
writing manual as the final Phase).

Phases are numbered `01`, `02`, …, `NN`. The number is two digits with a
leading zero so that Phases, Pipeline Sections, and Steps all share a
uniform numeric-prefix convention.

A Phase is named after its primary concern (e.g., "Phase 01 — Data
Exploration"). The name and number together are the canonical identifier.

**Canonical list.** The canonical Phase list is owned by
[`docs/PHASES.md`](PHASES.md). It is derived mechanically from
`docs/ml_experiment_lifecycle/` under the rule "one Phase per manual" (plus
the thesis writing wrap-up marker). See PHASES.md for the list itself, the
Pipeline Section decomposition of each Phase, and the derivation rule.

**Phase scope.** Every Phase is dataset-scoped. Each dataset's ROADMAP at
`src/rts_predict/<game>/reports/<dataset>/ROADMAP.md` implements all Phases
defined in `docs/PHASES.md` as its own execution plan. Two datasets under
the same game are independent — they do not share ROADMAPs, Pipeline Sections,
or Steps. Cross-dataset and cross-game coordination (e.g., the Phase 06
cross-domain transfer experiments, or Phase 07 thesis writing) is tracked
outside the ROADMAP system — in `reports/research_log.md` and `thesis/`
respectively. See `docs/PHASES.md` for the full scope rule.

### Pipeline Section

A Pipeline Section is one top-level section within a Phase's source manual.
Pipeline Sections decompose a Phase into coherent sub-topics that can be
worked on independently. A Pipeline Section is the unit at which a Phase
can be reviewed for completeness — a Phase is complete when every Pipeline
Section it contains has been executed and its exit gates met.

Pipeline Sections are numbered `{PHASE}_{PIPELINE_SECTION}` with zero-padded two-digit
components. Example: `01_01` means Phase 01, Pipeline Section 01. The section
numbering is sequential within its Phase and does not need to match the
`§` numbering of the source manual — it reflects execution order within
this project, not the manual's table of contents.

**Pipeline Section scope.** Every Pipeline Section is dataset-scoped, inherited
from its parent Phase (see `docs/PHASES.md`).

**Ownership.** The canonical Pipeline Section list for each Phase is defined
in [`docs/PHASES.md`](PHASES.md). Dataset ROADMAPs at
`src/rts_predict/<game>/reports/<dataset>/ROADMAP.md` implement those Pipeline
Sections by decomposing each into executable Steps. A dataset ROADMAP does
not invent, rename, or omit Pipeline Sections; it only adds Steps underneath
them.

### Step

A Step is the atomic leaf unit of work. One Step produces exactly one
sandbox notebook and the artifacts that notebook emits.

Steps are numbered `{PHASE}_{PIPELINE_SECTION}_{STEP}` with zero-padded two-digit
components. Example: `01_01_01`. The step number is sequential within its
Pipeline Section and indicates execution order where dependencies exist —
Step `01_01_02` may depend on `01_01_01`'s artifacts, but `01_02_01` does
not depend on `01_01_99`.

**Step contract.** Every Step produces:

- One sandbox notebook pair at the canonical path (see *Directory layout*).
- One or more artifacts under the matching `reports/<dataset>/artifacts/` subpath.
- One entry in the dataset's `research_log.md` summarising the Step's findings.

**Step schema.** A Step's definition in a dataset ROADMAP is a fenced YAML
block matching the schema in [`docs/templates/step_template.yaml`](templates/step_template.yaml).
The ROADMAP file is markdown; Step definitions are machine-parseable YAML
inside it. Required fields must be populated; optional fields are omitted
entirely rather than left empty.

A Step that produces no artifact is not a Step — it's either a Chore or a
Refactor (see *Categories* below).

**Ownership.** Steps live under the Pipeline Section that contains them.
A Step defined under a dataset-scoped Pipeline Section is scoped to that
dataset.

---

## Directory layout

The Phase / Pipeline Section / Step hierarchy is reflected in two mirrored
directory trees: one for sandbox notebooks, one for report artifacts. The
directory names use a `{NN}_{slug}` convention so directories are both
sortable by number and human-readable by slug.

### Sandbox notebooks

```
sandbox/<game>/<dataset>/
  01_exploration/
    01_acquisition/
      01_01_01_<slug>.py              jupytext source (reviewable)
      01_01_01_<slug>.ipynb           paired notebook (carries outputs)
      01_01_02_<slug>.py
      01_01_02_<slug>.ipynb
    02_profiling/
      01_02_01_<slug>.py
      01_02_01_<slug>.ipynb
  02_cleaning/
    ...
```

### Report artifacts

```
src/rts_predict/<game>/reports/<dataset>/artifacts/
  01_exploration/
    01_acquisition/
      01_01_01_<descriptive_name>.csv
      01_01_01_<descriptive_name>.md
      01_01_02_<descriptive_name>.json
```

The slug component of a Phase or Pipeline Section directory is chosen once
when the Phase or Section is first created, and does not change. The slug
component of a Step's file name is per-Step and is descriptive of the Step's
specific output. Tool references, code, and cross-links use the numeric
prefix (`01_01_01`) — the slug exists only for human browse-ability.

### Mirroring rule

The sandbox and artifacts trees have the same Phase and Pipeline Section
directory structure. When a notebook at
`sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_source_inventory.py`
runs, its artifacts land under
`src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/`.
The mirror is enforced by the notebook helpers in `rts_predict.common`, not
by convention alone.

---

## Operational terms

These terms describe how work is organised into reviewable units. They are
orthogonal to the Phase / Pipeline Section / Step hierarchy — one Spec may
execute part of a Step, one Step, or multiple Steps.

### Spec

A single executable plan scoped to one pull request. A Spec is authored by
a planner agent, reviewed and approved by the user, then executed by the
executor agent. The canonical location for the active Spec is
`planning/current_plan.md` at the repo root.

### PR

A git pull request. One PR corresponds to exactly one Spec. Branch naming
follows the Category convention.

### Category

Work classification. Drives branch prefix and agent routing.

| Letter | Name | Branch prefix |
|--------|------|---------------|
| A | Phase work (data science) | `feat/` |
| B | Refactor | `refactor/` |
| C | Chore | `chore/` |
| D | Bug fix | `fix/` |
| E | Documentation only | `docs/` |
| F | Thesis writing | `docs/thesis-` |

### Session

One conversation with Claude (chat or code). A Spec is typically split
across two Sessions: a planning Session that authors `planning/current_plan.md`,
and an execution Session that carries out the plan. The split is
deliberate — it forces an explicit approval checkpoint.

### DAG

A Directed Acyclic Graph representing the execution schedule for a single
Spec. One DAG corresponds to exactly one Spec and one PR. The DAG is a
derived artifact: it is generated from `planning/current_plan.md` after
user approval. The canonical location for the active DAG is
`planning/dags/DAG.yaml`.

A DAG contains Jobs. Jobs contain Task Groups. Task Groups contain Tasks.
The graph edges represent execution dependencies: a Task Group that
depends on another cannot begin until the dependency completes (and its
review gate passes, if one is configured).

**Relationship to the science hierarchy:** A DAG may execute part of a
Step, one Step, or multiple Steps. The DAG's `step_refs` field links to
the science hierarchy for traceability, but the DAG does not own or
redefine Step numbering.

### Job

A named logical unit within a DAG. Jobs are independent top-level
containers. In most cases a DAG has exactly one Job. Multiple Jobs exist
when a single Spec spans truly independent workstreams (e.g., SC2 and
AoE2 parallel execution within the same PR).

Jobs are identified by `J01`, `J02`, etc. This prefix is distinct from
the Step numbering convention (`NN_NN_NN`) to prevent confusion.

### Task Group

An ordered group of Tasks within a Job. Task Groups execute sequentially
when they have dependencies (`depends_on`), or in parallel when they do
not. A review gate MAY run after a Task Group completes, if configured.
Review gates are optional and omitted by default. The DAG-level
final_review is the standard quality gate.

Task Groups are identified by `TG01`, `TG02`, etc.

Commits happen per task group regardless of whether a review gate is
configured: the parent session commits all changes from a Task Group as
a single commit. This produces an auditable PR with one commit per
Task Group.

**Relationship to Pipeline Section:** A Task Group is NOT a synonym for
Pipeline Section. A Pipeline Section is a science hierarchy unit that may
span multiple Task Groups across multiple DAGs. A Task Group is a single
dispatch batch within one DAG.

### Task

A single agent invocation within a Task Group. One Task corresponds to
one spec file (`planning/specs/spec_NN_<slug>.md`) and one agent
dispatch. Tasks within a Task Group MAY run in parallel if their
`file_scope` declarations do not overlap.

Tasks are identified by `T01`, `T02`, etc.

A Task MAY include a `model` field: specifies which model tier the
orchestrator uses when dispatching this task's agent. When omitted, the
task inherits the parent session's model.

**Relationship to Step:** A Task is NOT a synonym for Step. A Step is the
atomic leaf unit of the science hierarchy; it produces one notebook and
its artifacts. A Task is an operational dispatch unit; it may implement
part of a Step (e.g., just the library code), or a non-science operation
(e.g., updating a research log). Multiple Tasks across one or more Task
Groups may be needed to complete a single Step.

### Parallel execution strategies

When a Task Group contains multiple Tasks that run in parallel, the
orchestrator chooses one of two strategies based on whether their
`file_scope` declarations overlap.

- **Strategy A (shared branch):** All parallel executors work on the same
  branch. Executors do NOT run `git add` or `git commit` — the parent
  orchestrator stages and commits after each task group completes and its
  review gate passes. Use when file scopes do not overlap. DAG field:
  `default_isolation: "shared_branch"`.

- **Strategy B (worktree isolation):** Each executor runs in a temporary
  git worktree on its own branch via `isolation: "worktree"`. Changes are
  merged back by the orchestrator after each executor completes. Use when
  file scopes overlap or when executors need independent git state. DAG
  field: task-level `isolation: "worktree"`.

The strategy is declared in the DAG. Executors do not choose their own
strategy — they follow the isolation mode they are dispatched with.
See `docs/templates/dag_template.yaml` for the DAG fields.

---

## Terms explicitly not used

To prevent taxonomy drift, the following words are avoided as load-bearing
terminology. In casual prose any of these words may appear as ordinary
English; they just don't name formal units of work.

- **Stage** — not used. Historically overloaded in the repo. If Stage-like
  coordination is needed, use Phase.
- **Experiment** — not used as a formal unit. It appears in prose referring
  to ML experiments in the Phase 5 sense; that usage is unrelated to work
  organisation.
- **Milestone** — not used. Use "Phase gate" instead. The canonical gate
  definitions live in `docs/PHASES.md` (for Phase 07, which is itself a gate
  marker) and in each dataset ROADMAP (for exit criteria of Phases 01–06).
- **Workstream**, **Track**, **Initiative**, **Epic** — not used.
- **Component** — not used as a work unit name. It may appear in prose for
  software components (e.g., "the ingestion component").
- **Section** (unqualified) — ambiguous. Use "Pipeline Section" for the
  Level-2 work unit and "thesis section" or "manual section" for prose
  references to sections of written documents.

---

## How to add a new term

1. Edit this file. Do not edit any other file to introduce the new term.
2. Add the term under the appropriate section with: definition, scope,
   owner, and relationship to existing terms.
3. If the new term overlaps with an existing one, resolve the overlap
   explicitly before merging — either rename the new term, redefine the
   old one, or withdraw the proposal.
4. Add a `CHANGELOG.md` entry under `[Unreleased]`.

Files that reference this document (`ARCHITECTURE.md`, `CLAUDE.md`,
`.claude/agents/*.md`, `.claude/scientific-invariants.md`) do so by pointer
only. They do not restate definitions. A new term therefore requires
exactly one file edit: this one.
