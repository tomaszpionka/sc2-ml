# Project Taxonomy

Single source of truth for terminology used across the `rts-outcome-prediction`
repository. Every other file that uses one of these terms does so by pointing
at this document. When a new term is added, edit this file only.

This file defines terminology only. It does not define phase numbering for any
specific game — that lives in `src/rts_predict/<game>/reports/ROADMAP.md`. It
does not catalogue where each term is currently used — that is the job of the
files that use them.

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

**Per-game specialisation.** The canonical Phase list for a specific game is
a translation of `docs/ml_experiment_lifecycle/` into a concrete plan for
that game. The list is owned by `src/rts_predict/<game>/reports/ROADMAP.md`.
If the game-level list and `docs/ml_experiment_lifecycle/` disagree, the
game-level list is revised to match `docs/`, not the reverse.

**Phase scope.** Some Phases are scoped to a single dataset (e.g., data
acquisition, exploration); others span datasets within a game (e.g.,
feature engineering, splitting); others span games (e.g., cross-domain
transfer, thesis writing). The scope of each Phase is declared in the
game-level ROADMAP.

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

**Pipeline Section scope.** Pipeline Sections inherit the scope of their
parent Phase. A Pipeline Section within a dataset-scoped Phase is
dataset-scoped; within a game-scoped Phase, game-scoped.

**Ownership.** Pipeline Sections within a dataset-scoped Phase are owned by
the dataset-level ROADMAP at
`src/rts_predict/<game>/reports/<dataset>/ROADMAP.md`. Pipeline Sections
within a game-scoped Phase are owned by the game-level ROADMAP.

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
- One entry in `reports/research_log.md` summarising the Step's findings.

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
`src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/`.
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
`_current_plan.md` at the repo root.

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
across two Sessions: a planning Session that authors `_current_plan.md`,
and an execution Session that carries out the plan. The split is
deliberate — it forces an explicit approval checkpoint.

---

## Terms explicitly not used

To prevent taxonomy drift, the following words are avoided as load-bearing
terminology. In casual prose any of these words may appear as ordinary
English; they just don't name formal units of work.

- **Stage** — not used. Historically overloaded in the repo. If Stage-like
  coordination is needed, use Phase.
- **Task** — not used as a formal unit.
- **Job** — not used. Reserved for batch-processing connotations that don't
  apply here.
- **Experiment** — not used as a formal unit. It appears in prose referring
  to ML experiments in the Phase 5 sense; that usage is unrelated to work
  organisation.
- **Milestone** — not used. Phase gates (defined in the game-level ROADMAP)
  replace this concept.
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
