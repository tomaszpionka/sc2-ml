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
│   ├── sc2/                 # StarCraft II — complete game package
│   ├── aoe2/                # Age of Empires II — placeholder, mirrors sc2/ when populated
│   └── common/              # Shared evaluation code — see common/CONTRACT.md
├── sandbox/                 # Jupyter notebook exploration — see sandbox/README.md
│   ├── sc2/sc2egset/        # SC2EGSet notebooks (Phases 0–2)
│   └── aoe2/                # AoE2 placeholders
├── tests/                   # Mirrored test tree — see .claude/rules/python-code.md
├── thesis/                  # Thesis chapters and figures
├── reports/                 # Cross-cutting research log and archives
└── docs/                    # Methodology manuals and agent documentation
```

Each game package is self-contained: it has its own CLI, config, data pipeline,
reports, models directory, and tests. The top-level `rts_predict` package provides
the namespace; it contains no game-specific logic and no version attribute.
Phase work code execution happens in `sandbox/<game>/<dataset>/` notebooks — not in
`src/` modules or ad-hoc scripts. See `sandbox/README.md` for the full contract.

## Game package contract

Every game package (`sc2/`, `aoe2/`, ...) must contain:

| Item | Purpose | Required? |
|------|---------|-----------|
| `__init__.py` | Docstring identifying the game. NO `__version__`. | Yes |
| `cli.py` | CLI entry point registered in `pyproject.toml` | Yes |
| `config.py` | `GAME_DIR`, `ROOT_DIR`, `REPORTS_DIR`, DB paths, constants | Yes |
| `PHASE_STATUS.yaml` | Machine-readable phase progress | Yes |
| `data/` | Ingestion, processing, exploration, audit modules | Yes |
| `data/<dataset>/raw/` | Raw source data (gitignored contents, README tracked) | Yes |
| `data/<dataset>/staging/` | Intermediate artifacts by type (gitignored, README tracked) | When extraction exists |
| `data/<dataset>/db/` | DuckDB database file (gitignored, `.gitkeep` tracked) | Yes |
| `data/<dataset>/tmp/` | DuckDB spill-to-disk directory (gitignored, `.gitkeep` tracked) | Yes |
| — | Tests live in mirrored `tests/rts_predict/` tree, not inside game packages | — |
| `reports/` | Phase artifacts (tracked in git) | Yes |
| `reports/ROADMAP.md` | Game-level execution plan (Phases 3+) | Yes |
| `reports/<dataset>/ROADMAP.md` | Dataset-level execution plan (Phases 0–2) | Per dataset |
| `reports/<dataset>/` | Named documentation files (`ROADMAP.md`, `INVARIANTS.md`, etc.) | Per dataset |
| `reports/<dataset>/artifacts/` | Machine-generated step outputs (`XX_XX_*`, any extension) | Per dataset |
| `models/` | Serialised model artifacts (gitignored) | When modelling begins |
| `logs/` | Pipeline logs (gitignored) | When pipeline exists |
| — | CLI tests live in `tests/rts_predict/<game>/test_cli.py` | — |

> **Test location:** All tests live under the root `tests/` directory in a tree
> that exactly mirrors `src/rts_predict/`. See `.claude/rules/python-code.md` for
> the convention and the mirror-drift guardrail that enforces it.

## Adding a new game

1. Create `src/rts_predict/<game>/` mirroring the `sc2/` structure above
2. Create `PHASE_STATUS.yaml` with `current_phase: null`
3. Create `reports/ROADMAP.md` (game-level placeholder)
4. Create `reports/<dataset>/ROADMAP.md` per dataset
5. Register the CLI entry point in `pyproject.toml`
6. Update `.gitignore` patterns (already use `rts_predict/*/` wildcards)
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

4. **`src/rts_predict/<game>/reports/ROADMAP.md`** — game-level roadmap.
   Owns the canonical per-game Phase numbering. Each Phase must map to at
   least one manual in tier (2). If a manual in tier (2) and a game-level
   ROADMAP disagree, the ROADMAP is revised to match the manual — not the
   reverse.

5. **`src/rts_predict/<game>/reports/<dataset>/ROADMAP.md`** — dataset-level
   roadmap. Owns Pipeline Section and Step numbering within the dataset's
   in-scope Phases. Cannot invent Phases; can only decompose Phases into
   Pipeline Sections and Steps per `docs/TAXONOMY.md`.

6. **`src/rts_predict/<game>/PHASE_STATUS.yaml`** — machine-readable phase
   status. Strictly derived from tiers (4) and (5). Never authoritative;
   never diverges. If it diverges from the ROADMAPs, it is wrong and gets
   regenerated.

7. **Operational files** — `CLAUDE.md`, `.claude/ml-protocol.md`,
   `.claude/agents/*.md`, and any other file that instructs Claude agents
   how to work. These reference phase numbers and terminology only via
   pointers into tiers (3), (4), and (5). They never inline-encode a numbered
   Phase list and never redefine terminology.

**The rule.** Higher-precedence tiers are sources; lower-precedence tiers
are derivations. A change in a high-precedence file propagates downward
through edits to the lower-precedence files. A change in a lower-precedence
file that contradicts a higher-precedence file is a bug and gets reverted
or rewritten, not ratified.

**Out of scope for this hierarchy.** Per-dataset empirical findings (e.g.,
`src/rts_predict/<game>/reports/<dataset>/INVARIANTS.md`) are not listed
above because the convention governing them has not yet been formalised.
They will be added to this hierarchy in a future PR alongside the convention
section.

## Cross-cutting files (not game-specific)

| File | Location | Purpose |
|------|----------|---------|
| Project taxonomy | `docs/TAXONOMY.md` | Single source of truth for terminology (Phase, Pipeline Section, Step, Spec, PR, Category, Session) |
| Methodology manuals | `docs/INDEX.md` → `docs/ml_experiment_lifecycle/` | ML experiment lifecycle reference (01–06) |
| Research log | `reports/research_log.md` | Unified chronological narrative, tagged `[SC2]`/`[AoE2]`/`[CROSS]` |
| Thesis | `thesis/` | Chapters, figures, tables, bibliography |
| Review queue | `thesis/chapters/REVIEW_QUEUE.md` | Pass 1→2 handoff for thesis writing |
| Scientific invariants | `.claude/scientific-invariants.md` | Methodology constraints (apply to all games) |
| Thesis writing | `.claude/rules/thesis-writing.md` | Writing workflow + Chat handoff (loads on thesis/ touch) |
| Sandbox notebooks | `sandbox/<game>/<dataset>/` | Phase work execution (jupytext `.py` + `.ipynb` pairs); see `sandbox/README.md` |

## Progress tracking

Phase progress per game is tracked in `PHASE_STATUS.yaml` files. Claude Code reads
these at session start to determine the current phase without parsing full roadmaps.

Thesis section progress is tracked in `thesis/WRITING_STATUS.md` (per-section status)
and `thesis/chapters/REVIEW_QUEUE.md` (Pass 2 review queue).

The changelog (`CHANGELOG.md`) tracks code changes per version. The research log
(`reports/research_log.md`) tracks analytical findings per phase.

## Version management

- Single version source: `pyproject.toml`
- No `__version__` in any `__init__.py` (neither top-level nor game packages)
- Version is bumped at PR creation time (see `.claude/git-workflow.md`)
- Bumped atomically in two places: `pyproject.toml` and `CHANGELOG.md`

## Thesis writing workflow (two-pass)

See `.claude/rules/thesis-writing.md` for full details. Summary:

- **Pass 1 (Claude Code):** Draft section, run critical review checklist,
  plant `[REVIEW: ...]` flags, update `REVIEW_QUEUE.md`
- **Pass 2 (Claude Chat):** External validation against literature, resolve
  flags, check methodology alignment with field norms

The handoff protocol is defined in `.claude/rules/thesis-writing.md`.
