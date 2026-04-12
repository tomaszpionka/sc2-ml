# Research Log — Specification

## Purpose

`docs/research/RESEARCH_LOG.md` (this file) is a **specification document**.
It describes the structure, location, and rules governing the research log
system.
It is NOT the log itself.

---

## Log Structure

The research log is split across multiple files:

### Root index log

```
reports/research_log.md
```

The root log is **index-only**. It contains:

- Links to each per-dataset log.
- Entries tagged `CROSS` — those that span multiple datasets or are
  game-agnostic (e.g., cross-dataset methodology decisions, infrastructure
  chores).

Dataset-specific entries MUST NOT be written to the root log.

### Per-dataset logs

```
src/rts_predict/games/<game>/datasets/<dataset>/reports/research_log.md
```

Each dataset has its own log. Examples:

```
src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md
src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
```

All dataset-specific entries (sc2egset, aoe2companion, aoestats) are written
to the matching per-dataset log, never to the root log.

---

## Ordering

Entries in every log are ordered **reverse chronological** (newest entry at the
top). This allows readers to see the most recent state of the research
immediately without scrolling.

---

## Entry Structure

### Schema

The authoritative schema for a single entry is defined in:

```
docs/templates/research_log_entry_template.yaml
```

### Human-Readable Rendering

A human-readable rendering of the entry template is provided at:

```
docs/research/RESEARCH_LOG_ENTRY.md
```

Use this file as a quick reference when composing a new entry by hand. The YAML
template is the authoritative source; the Markdown rendering is a convenience
for authors.

### Entry Fields (summary)

| Field | Required | Notes |
|---|---|---|
| Entry title | Always | See title format below |
| Category | Always | A, C, or F |
| Dataset | Always | See dataset tags below |
| Artifacts produced | Category A with outputs | Repo-relative paths |
| What | Always | Concrete description of work done |
| Why | Always | Motivating question; reference to Invariant or Manual |
| How (reproducibility) | Category A (mandatory) | Literal SQL or Python |
| Findings | Category A (mandatory) | Bullet list, numbers with units |
| What this means | When findings warrant it | Interpretation |
| Decisions taken | Always | One-sentence rationale each |
| Decisions deferred | Category A (mandatory) | What and at which phase/step |
| Acknowledged trade-offs | When a methodology decision is recorded | — |
| Thesis mapping | Always | Target section in THESIS_STRUCTURE.md |
| Open questions / follow-ups | Category A (mandatory) | Anything surprising |

Per **Invariant #6**: a finding without its derivation (the "How" section)
cannot be cited in the thesis. The "How (reproducibility)" field is mandatory
for all Category A entries.

---

## Hierarchy Linking

Each entry title embeds a Phase/Step reference using the format:

```
## YYYY-MM-DD — [Phase XX / Step XX_YY_ZZ] Short descriptive title
```

- `XX` is the two-digit Phase number (see `docs/PHASES.md`).
- `XX_YY_ZZ` is the Step number where `XX` = Phase, `YY` = Pipeline Section,
  `ZZ` = Step within section.
- The Pipeline Section is **implicit** in the Step number (the first two
  components, `XX_YY`). There is no separate Pipeline Section tag in the title.

For entries that do not belong to a specific Phase/Step — for example, a
cross-dataset decision or a housekeeping chore — use one of the alternate tags:

| Tag | When to use |
|---|---|
| `[CROSS]` | Spans multiple datasets or is game-agnostic |
| `[CHORE]` | Infrastructure, tooling, or Category C work |

Example titles:

```
## 2026-03-15 — [Phase 01 / Step 01_02_01] ELO distribution analysis — sc2egset
## 2026-03-10 — [CROSS] Decided on temporal split strategy across all datasets
## 2026-03-05 — [CHORE] Migrated research log to reverse-chronological order
```

---

## Dataset Tagging

Every entry must declare its dataset scope. Allowed values:

| Tag | Scope |
|---|---|
| `sc2egset` | StarCraft II SC2EGSet dataset only |
| `aoe2companion` | Age of Empires II aoe2companion dataset only |
| `aoestats` | Age of Empires II aoestats dataset only |
| `CROSS` | Spans multiple datasets or is game-agnostic |

The dataset appears in the entry header field:

```markdown
**Dataset:** sc2egset
```

---

## When an Entry Is Required

| Category | Requirement |
|---|---|
| A — Phase work (science) | Mandatory for every completed step |
| C — Chore | Recommended when methodology decisions are made |
| F — Thesis writing | Recommended when a writing decision affects interpretation |

Completion of a research log entry is a **prerequisite** for marking a Step as
complete in `STEP_STATUS.yaml`. Do not set a step to `DONE` without a
corresponding log entry.

### Entry destination

| Entry dataset tag | Write to |
|---|---|
| `sc2egset` | `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` |
| `aoe2companion` | `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` |
| `aoestats` | `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` |
| `CROSS` | `reports/research_log.md` (root index log) |

Dataset-specific entries (any tag other than `CROSS`) MUST go into the
per-dataset log. The root log at `reports/research_log.md` is reserved
for CROSS entries and index links only.

---

## Cross-References

### Artifacts and ROADMAPs

Artifact paths listed in an entry's "Artifacts produced" field must match the
paths declared in the corresponding ROADMAP step definition's `outputs` field.
If they do not match, the ROADMAP or the log entry must be corrected before the
step is marked complete.

### STEP_STATUS.yaml

A research log entry for a step is required before that step can be marked
`DONE` in:

```
src/rts_predict/games/<game>/datasets/<dataset>/reports/STEP_STATUS.yaml
```

### Scientific Invariants

See `.claude/scientific-invariants.md` for the full set of invariants,
especially Invariant #6 (reproducibility mandate for Category A findings).

### Phase and Pipeline Section definitions

See `docs/PHASES.md` for the canonical phase list and step numbering scheme.
See `docs/TAXONOMY.md` for definitions of Phase, Pipeline Section, and Step.
