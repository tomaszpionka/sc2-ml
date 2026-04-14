# Architecture

This document describes the package structure of `rts-outcome-prediction` and
the conventions for extending it.

For project terminology (Phase, Pipeline Section, Step, Spec, PR, Category,
Session), see [`docs/TAXONOMY.md`](docs/TAXONOMY.md) — the single source of
truth for vocabulary used throughout this repository.

## Package layout

```
rts-outcome-prediction/
├── src/rts_predict/
│   ├── __init__.py          # Docstring only — no __version__
│   ├── games/
│   │   ├── sc2/             # StarCraft II — complete game package
│   │   └── aoe2/            # Age of Empires II — placeholder, mirrors sc2/ when populated
│   └── common/              # Shared evaluation code — see common/CONTRACT.md
├── sandbox/                 # Jupyter notebook exploration — see sandbox/README.md
│   ├── sc2/sc2egset/        # SC2EGSet notebooks (all dataset-scoped Phases)
│   └── aoe2/                # AoE2 placeholders
├── tests/                   # Mirrored test tree — see .claude/rules/python-code.md
├── thesis/                  # Thesis chapters and figures
├── reports/                 # Cross-cutting research log
└── docs/                    # Methodology manuals and agent documentation
```

Each game package is self-contained: it has its own CLI, config, data pipeline,
reports, models directory, and tests. The top-level `rts_predict` package provides
the namespace; it contains no game-specific logic and no version attribute.
Phase work code execution happens in `sandbox/<game>/<dataset>/` notebooks — not in
`src/` modules or ad-hoc scripts. See `sandbox/README.md` for the full contract.

## Game package contract

Every game package (`games/sc2/`, `games/aoe2/`, ...) must contain:

| Item | Purpose | Required? |
|------|---------|-----------|
| `__init__.py` | Docstring identifying the game. NO `__version__`. | Yes |
| `cli.py` | CLI entry point registered in `pyproject.toml` | Yes |
| `config.py` | `GAME_DIR`, `ROOT_DIR`, `DATASETS_REPORTS`, DB paths, constants | Yes |
| `datasets/<dataset>/reports/STEP_STATUS.yaml` | Machine-readable step progress (dataset-scoped) | Per dataset |
| `datasets/<dataset>/reports/PIPELINE_SECTION_STATUS.yaml` | Machine-readable pipeline section progress (dataset-scoped) | Per dataset |
| `datasets/<dataset>/reports/PHASE_STATUS.yaml` | Machine-readable phase progress (dataset-scoped) | Per dataset |
| `datasets/<dataset>/data/raw/` | Raw source data (gitignored contents, README tracked) | Yes |
| `datasets/<dataset>/data/db/` | DuckDB database file (gitignored, `.gitkeep` tracked) | Yes |
| `datasets/<dataset>/data/tmp/` | DuckDB spill-to-disk directory (gitignored, `.gitkeep` tracked) | Yes |
| — | Tests live in mirrored `tests/rts_predict/` tree, not inside game packages | — |
| `ROADMAP.md` | Game-level navigation (lists datasets, points to docs/PHASES.md) | Yes |
| `datasets/<dataset>/reports/ROADMAP.md` | Dataset-level execution plan (all Phases — see docs/PHASES.md) | Per dataset |
| `datasets/<dataset>/reports/` | Named documentation files (`ROADMAP.md`, `INVARIANTS.md`, etc.) | Per dataset |
| `datasets/<dataset>/reports/artifacts/` | Machine-generated step outputs (`XX_XX_*`, any extension) | Per dataset |
| `models/` | Serialised model artifacts (gitignored) | When modelling begins |
| `logs/` | Pipeline logs (gitignored) | When pipeline exists |
| — | CLI tests live in `tests/rts_predict/games/<game>/test_cli.py` | — |

> **Test location:** All tests live under the root `tests/` directory in a tree
> that exactly mirrors `src/rts_predict/`. See `.claude/rules/python-code.md` for
> the convention and the mirror-drift guardrail that enforces it.

## Adding a new game

1. Create `src/rts_predict/games/<game>/` mirroring the `games/sc2/` structure above
2. Create `datasets/<dataset>/reports/PHASE_STATUS.yaml` per dataset (see schema in docs/PHASES.md)
3. Create `ROADMAP.md` (game-level placeholder)
4. Create `datasets/<dataset>/reports/ROADMAP.md` per dataset
5. Register the CLI entry point in `pyproject.toml`
6. Update `.gitignore` patterns (already use `datasets/*/data/` wildcards)
7. Do NOT create shared abstractions until the second game's implementation
   reveals genuine code overlap (see `common/CONTRACT.md`)

## Source-of-Truth Hierarchy

The repository uses a strict precedence order for resolving contradictions
between files. When two files disagree, the higher-precedence file wins and
the lower-precedence file is edited to match, never the reverse.

1. **`.claude/scientific-invariants.md`** — universal, game-agnostic
   methodology constraints. Highest precedence. Cannot be overridden by any
   other file. Numberless (refers to concepts, not to numbered phases).

2. **`docs/ml_experiment_lifecycle/*.md`** and **`docs/thesis/THESIS_WRITING_MANUAL.md`**
   — thesis methodology reference. Describes lifecycle concepts with academic
   citations. Does not own phase numbering; owns the vocabulary of methodology
   and the definitions of lifecycle concepts.

3. **`docs/TAXONOMY.md`** — project terminology. Single source of truth for
   what Phase, Pipeline Section, Step, Spec, PR, Category, and Session mean
   in this repository. See the taxonomy file itself for definitions.

4. **`docs/PHASES.md`** — canonical Phase list. Enumerates the 7 Phases and
   their Pipeline Sections. Derived from the methodology manuals in tier (2).
   All downstream files that reference Phase numbers point here. See also
   `docs/templates/step_template.yaml` for the Step definition schema used
   in dataset ROADMAPs.

5. **`src/rts_predict/games/<game>/ROADMAP.md`** — game-level roadmap.
   Navigation document listing datasets and pointing to docs/PHASES.md.
   Does not own phase numbering (that is tier 4, docs/PHASES.md). Does
   not define Steps.

6. **`src/rts_predict/games/<game>/datasets/<dataset>/reports/ROADMAP.md`** — dataset-level
   roadmap. Owns Pipeline Section and Step numbering within the dataset's
   in-scope Phases. Cannot invent Phases; can only decompose Phases into
   Pipeline Sections and Steps per `docs/TAXONOMY.md`.

7. **Machine-readable status files** — three files per dataset, forming a derivation chain:

   - **7a. `STEP_STATUS.yaml`** — derived from the dataset ROADMAP (tier 6). Authoritative
     at the step level. Each entry has a `pipeline_section` upward link.
   - **7b. `PIPELINE_SECTION_STATUS.yaml`** — derived from STEP_STATUS.yaml (tier 7a).
     Lists only pipeline sections for active phases (added incrementally as phases activate).
   - **7c. `PHASE_STATUS.yaml`** — derived from PIPELINE_SECTION_STATUS.yaml (tier 7b).
     Lists all 7 phases including not_started ones.

   None of these files are authoritative. If any disagrees with its upstream source,
   it is wrong and gets regenerated. Full chain: ROADMAP → STEP_STATUS →
   PIPELINE_SECTION_STATUS → PHASE_STATUS.

8. **`*_raw` schema YAML files** — per-dataset DuckDB layer documentation at
   `src/rts_predict/games/<game>/datasets/<dataset>/data/db/schemas/raw/<table>.yaml`.
   Column names, types, and nullability are sourced verbatim from the `01_02_03`
   `DESCRIBE` artifact (see `.claude/rules/sql-data.md § Schema Source of Truth`).
   These are the authoritative schema reference for `*_raw` tables and views — never
   infer schema from notebooks, JSON artifacts, or prior documentation when a YAML exists.
   Template: `docs/templates/duckdb_schema_template.yaml`.

9. **Operational files** — `CLAUDE.md`, `.claude/ml-protocol.md`,
   `.claude/agents/*.md`, and any other file that instructs Claude agents
   how to work. These reference phase numbers and terminology only via
   pointers into tiers (3), (4), (5), and (6). They never inline-encode a numbered
   Phase list and never redefine terminology.

   **9b. Planning artifacts** — `planning/current_plan.md` (the active Spec),
   `planning/dags/DAG.yaml` (the active execution schedule),
   `planning/specs/spec_*.md` (task-level instructions). Within this sub-tier,
   precedence is: plan (authoritative) > DAG (derived execution order) >
   specs (derived task-level extracts). If any derived artifact diverges from
   the plan, the plan wins and the DAG is regenerated. Planning artifacts are
   ephemeral: committed on the feature branch for PR auditability, then purged
   after merge (see `planning/README.md`). Permanent documentation files
   (`planning/INDEX.md`, `planning/README.md`, `planning/*/README.md`) are
   tier 9 operational files, not ephemeral planning artifacts.

**The rule.** Higher-precedence tiers are sources; lower-precedence tiers
are derivations. A change in a high-precedence file propagates downward
through edits to the lower-precedence files. A change in a lower-precedence
file that contradicts a higher-precedence file is a bug and gets reverted
or rewritten, not ratified.

**Out of scope for this hierarchy.** Per-dataset empirical findings (e.g.,
`src/rts_predict/games/<game>/datasets/<dataset>/reports/INVARIANTS.md`) are not listed
above because the convention governing them has not yet been formalised.
They will be added to this hierarchy in a future PR alongside the convention
section.

## Cross-cutting files (not game-specific)

| File | Location | Purpose |
|------|----------|---------|
| Project taxonomy | `docs/TAXONOMY.md` | Single source of truth for all project terminology (see file for full list) |
| Methodology manuals | `docs/INDEX.md` → `docs/ml_experiment_lifecycle/` | ML experiment lifecycle reference (01–06) |
| Research log | `reports/research_log.md` (index + `[CROSS]` entries); `src/rts_predict/games/<game>/datasets/<dataset>/reports/research_log.md` (per-dataset findings) | Chronological narrative: index holds cross-cutting entries, per-dataset files hold game/dataset-specific findings |
| Thesis | `thesis/` | Chapters, figures, tables, bibliography |
| Review queue | `thesis/chapters/REVIEW_QUEUE.md` | Pass 1→2 handoff for thesis writing |
| Scientific invariants | `.claude/scientific-invariants.md` | Methodology constraints (apply to all games) |
| Thesis writing | `.claude/rules/thesis-writing.md` | Writing workflow + Chat handoff (loads on thesis/ touch) |
| Sandbox notebooks | `sandbox/<game>/<dataset>/` | Phase work execution (jupytext `.py` + `.ipynb` pairs); see `sandbox/README.md` |

## Progress tracking

Progress is tracked via the three-tier derivation chain described in
Source-of-Truth tier 7a-7c above (STEP_STATUS.yaml → PIPELINE_SECTION_STATUS.yaml
→ PHASE_STATUS.yaml). See that section for the full derivation chain and
authoritative definitions.

## Version management

See `.claude/rules/git-workflow.md` for version bump rules and changelog protocol.

## Thesis writing workflow

See `.claude/rules/thesis-writing.md` for the full two-pass workflow, critical
review checklist, and Chat handoff protocol.
