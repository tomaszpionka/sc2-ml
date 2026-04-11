# Dataset ROADMAP Reference

This document specifies the structure and conventions for dataset-level
`ROADMAP.md` files. It is not itself a ROADMAP — it is the specification for
how ROADMAPs are written.

## Purpose

A dataset ROADMAP is a dataset-level execution plan that decomposes the seven
canonical phases (01 through 07) into Pipeline Sections and Steps for one
specific `<game>/<dataset>` combination. It records planned and completed work,
links each Step to its notebook and artifacts, and surfaces the gate conditions
that guard phase transitions.

ROADMAPs do not define phases or pipeline sections — they implement the ones
defined in `docs/PHASES.md`. A ROADMAP must not invent, rename, or omit any
Phase or Pipeline Section listed there.

## Location convention

Every dataset ROADMAP lives at:

```
src/rts_predict/<game>/reports/<dataset>/ROADMAP.md
```

Examples:

- `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md`
- `src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md`
- `src/rts_predict/aoe2/reports/aoestats/ROADMAP.md`

## Schema

The overall document structure of a ROADMAP is governed by:

```
docs/templates/dataset_roadmap_template.yaml
```

That template specifies the required sections, their order, and the constraints
on each section's content. Every new or revised ROADMAP must conform to it.

## Step definitions

Each Step entry inside a ROADMAP is a fenced YAML block that conforms to:

```
docs/templates/step_template.yaml
```

A Step is the atomic leaf unit of work: one notebook, its artifacts, one
research log entry. The step number follows the `NN_NN_NN` scheme
(Phase\_Section\_Step, zero-padded). Do not populate a Step block until the
preceding phase gate has been met; use the placeholder Phase structure
(described below) until then.

## Relationship to docs/PHASES.md

`docs/PHASES.md` is the single source of truth for:

- The canonical list of Phases (01-07) and their names
- The canonical list of Pipeline Sections within each Phase, including their
  `NN_NN` identifiers and names
- Phase gate conditions

A ROADMAP references these definitions and adds the dataset-specific details:
concrete Step numbers, notebook paths, artifact paths, and gate evidence. If
`docs/PHASES.md` changes (e.g., a Pipeline Section is added or renamed), every
active ROADMAP must be updated to match before the next Step in the affected
section begins.

## Role field

When a game has more than one dataset, each ROADMAP header carries a `role`
field indicating whether the dataset is `PRIMARY` or
`SUPPLEMENTARY VALIDATION`.

This field must be set to `TO BE DETERMINED` until the Phase 01 Decision Gate
(`01_06`) has been passed and the evidence from that gate supports a concrete
role assignment. Setting the role before gate evidence exists is not permitted.

If a game has only one dataset, the `role` field is omitted entirely.

## Required sections

A ROADMAP must contain the following top-level sections in this order:

### 1. Header

Metadata block including `game`, `dataset`, `role` (if applicable), and
`canonical_references` pointing to `docs/PHASES.md`, `docs/INDEX.md`, and
`docs/templates/step_template.yaml`. See
`docs/templates/dataset_roadmap_template.yaml` for the full field list.

### 2. How to use this document

Prose block explaining that the ROADMAP decomposes Phases into Pipeline
Sections and Steps, that canonical Phase and Pipeline Section definitions live
in `docs/PHASES.md`, and describing the `NN_NN_NN` numbering scheme.

### 3. Source data

Dataset provenance: citation, row counts, known issues, temporal coverage, and
any warnings about snapshot tables or schema drift. Values recorded before
Phase 01 completes carry a provenance caveat noting that they are preliminary
estimates.

### 4. Phase sections (01 through 07)

One `## Phase NN` section per phase. Phases use one of three structures:

**Active phase** — Pipeline Sections are listed as a bullet list with their
`NN_NN` identifiers and names. Step definitions follow as fenced YAML blocks
conforming to `docs/templates/step_template.yaml`.

```
## Phase NN -- Phase Name

Pipeline Sections:
- `NN_NN` -- Pipeline Section Name
- ...

### NN_NN -- Pipeline Section Name

```yaml
step_number:
  value: "NN_NN_NN"
...
` ``
```

**Placeholder phase** — Used for phases whose preceding gate has not yet been
met. No Pipeline Section detail is given.

```
## Phase NN -- Phase Name (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase NN-1 gate is met.
```

**Gate marker (Phase 07 only)** — Phase 07 contains no Pipeline Sections. It
is recorded as:

```
## Phase 07 -- Thesis Writing Wrap-up (gate marker)

Per `docs/PHASES.md`, Phase 07 is a gate marker with no Pipeline Sections.
```

## Summary of template references

| Purpose | Template file |
|---|---|
| Overall ROADMAP document structure | `docs/templates/dataset_roadmap_template.yaml` |
| Individual Step definition schema | `docs/templates/step_template.yaml` |
| Phase block schema | `docs/templates/phase_template.yaml` |
| Pipeline Section block schema | `docs/templates/pipeline_section_template.yaml` |
| Canonical Phase and Pipeline Section list | `docs/PHASES.md` |
| Taxonomy definitions | `docs/TAXONOMY.md` |
