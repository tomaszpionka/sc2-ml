# Sandbox

This directory is a sandbox. Working documents live here. For the authoritative
plan, see `_current_plan.md`.

## Purpose

Exploration workspace for SC2 and AoE2 phase work. Each notebook is an
executable artifact — query, output, narrative, and interpretation in one
place. Notebooks complement the `src/rts_predict/` modules; they do not replace
them. See `_current_plan.md` sections A.1–A.3 for full rationale.

## Directory structure

```
sandbox/
  sc2/
    sc2egset/       # SC2EGSet dataset notebooks, Phases 0–2
  aoe2/
    aoe2companion/  # Placeholder — populated when AoE2 Phase 1 begins
    aoestats/       # Placeholder — populated when AoE2 Phase 1 begins
```

## Naming convention

```
{PHASE:02d}_{STEP}_{descriptive_name}.ipynb
```

Examples:
- `01_01_corpus_summary.ipynb` — Phase 1, Step 1.1
- `01_08_game_settings_audit.ipynb` — Phase 1, Step 1.8
- `01_90_ad_hoc_investigation.ipynb` — ad-hoc (no ROADMAP step); use 90+

Each `.ipynb` is paired with a `.py:percent` file (jupytext). Both files are
committed. See `jupytext.toml` at the repo root.

## Hard rules

1. **No inline definitions.** No `def`, `class`, or lambda assignments in any
   cell. All non-trivial Python lives in `src/rts_predict/` and is imported.
2. **Cell size cap.** Cells are capped at `[cells] max_lines` from
   `sandbox/notebook_config.toml` (default 50 lines). A cell approaching the
   cap is a signal to extract logic to `src/`.
3. **Read-only DuckDB.** Use `get_notebook_db()` from
   `rts_predict.common.notebook_utils`. Connections are read-only by default.
4. **Both files committed.** Always stage both `.ipynb` and `.py` of a pair.
   The jupytext pre-commit hook (`.pre-commit-config.yaml`) enforces that
   the two files have matching content, but does NOT enforce that both
   are staged. Staging both is the author's responsibility.

## Configuration pointers

- `jupytext.toml` — pairing format and metadata filter (repo root)
- `sandbox/notebook_config.toml` — cell line cap and execution timeout

## Report artifacts

Notebooks write report artifacts (CSV, MD, PNG) to
`src/rts_predict/<game>/reports/<dataset>/artifacts/` — always the `artifacts/`
subdirectory, never the dataset report root directly. Use
`get_reports_dir("sc2", "sc2egset") / "artifacts"` from
`rts_predict.common.notebook_utils`. Notebooks themselves are not cited as
findings sources — only the report artifacts are.
