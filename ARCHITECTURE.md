# Architecture

This document describes the package structure of `rts-outcome-prediction` and
the conventions for extending it.

## Package layout

```
src/rts_predict/
├── __init__.py          # Docstring only — no __version__
├── sc2/                 # StarCraft II — complete game package
├── aoe2/                # Age of Empires II — placeholder, mirrors sc2/ when populated
└── common/              # Shared evaluation code — see common/CONTRACT.md
```

Each game package is self-contained: it has its own CLI, config, data pipeline,
reports, models directory, and tests. The top-level `rts_predict` package provides
the namespace; it contains no game-specific logic and no version attribute.

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
| `data/tests/` | Co-located unit tests for data modules | Yes |
| `reports/` | Phase artifacts (tracked in git) | Yes |
| `reports/<GAME>_THESIS_ROADMAP.md` | Authoritative execution plan | Yes |
| `models/` | Serialised model artifacts (gitignored) | When modelling begins |
| `logs/` | Pipeline logs (gitignored) | When pipeline exists |
| `tests/` | Package-root tests (CLI, validation) | Yes |

## Adding a new game

1. Create `src/rts_predict/<game>/` mirroring the `sc2/` structure above
2. Create `PHASE_STATUS.yaml` with `current_phase: null`
3. Create `<GAME>_THESIS_ROADMAP.md` in the reports directory
4. Register the CLI entry point in `pyproject.toml`
5. Update `.gitignore` patterns (already use `rts_predict/*/` wildcards)
6. Do NOT create shared abstractions until the second game's implementation
   reveals genuine code overlap (see `common/CONTRACT.md`)

## Cross-cutting files (not game-specific)

| File | Location | Purpose |
|------|----------|---------|
| Research log | `reports/research_log.md` | Unified chronological narrative, tagged `[SC2]`/`[AoE2]`/`[CROSS]` |
| Thesis | `thesis/` | Chapters, figures, tables, bibliography |
| Review queue | `thesis/chapters/REVIEW_QUEUE.md` | Pass 1→2 handoff for thesis writing |
| Scientific invariants | `.claude/scientific-invariants.md` | Methodology constraints (apply to all games) |
| Thesis writing | `.claude/rules/thesis-writing.md` | Writing workflow + Chat handoff (loads on thesis/ touch) |

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
