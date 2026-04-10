# Sandbox

This directory is a sandbox. Working documents live here. For the authoritative
plan, see `_current_plan.md`. For the canonical Phase list, see `docs/PHASES.md`.
For terminology, see `docs/TAXONOMY.md`.

## Purpose

Exploration workspace for SC2 and AoE2 phase work. Each notebook is an
executable artifact — query, output, narrative, and interpretation in one
place. Notebooks complement the `src/rts_predict/` modules; they do not replace
them. See `_current_plan.md` sections A.1–A.3 for full rationale.

## Directory structure

```
sandbox/
  sc2/
    sc2egset/                         # SC2EGSet dataset notebooks
      01_exploration/                 # Phase 01 — Data Exploration
        01_acquisition/               # Pipeline Section 01_01
          01_01_01_<slug>.py          # Step notebook (jupytext source)
          01_01_01_<slug>.ipynb       # Step notebook (paired, carries outputs)
        02_profiling/                 # Pipeline Section 01_02
          ...
      02_feature_engineering/         # Phase 02 (created when Phase 01 completes)
        ...
  aoe2/
    aoe2companion/                    # Placeholder — populated when Phase 01 begins
    aoestats/                         # Placeholder — populated when Phase 01 begins
```

## Naming convention

Notebooks follow the three-level numbering defined in `docs/TAXONOMY.md`:

```
{PHASE}_{PIPELINE_SECTION}_{STEP}_{descriptive_slug}.ipynb
```

All numeric components are two-digit, zero-padded. The slug is descriptive
and chosen per-Step.

Examples:
- `01_01_01_source_inventory.ipynb` — Phase 01, Pipeline Section 01_01 (Acquisition), Step 01
- `01_02_03_duration_distribution.ipynb` — Phase 01, Pipeline Section 01_02 (Profiling), Step 03
- `01_01_90_ad_hoc_investigation.ipynb` — ad-hoc (no ROADMAP step); use 90+

Each `.ipynb` is paired with a `.py:percent` file (jupytext). Both files are
committed. See `sandbox/jupytext.toml` for pairing configuration.

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

- `sandbox/jupytext.toml` — pairing format and metadata filter
- `sandbox/notebook_config.toml` — cell line cap and execution timeout
- `docs/templates/notebook_template.yaml` — notebook cell structure and front-matter schema

## Report artifacts

Notebooks write report artifacts (CSV, MD, PNG) to
`src/rts_predict/<game>/reports/<dataset>/artifacts/` — always the `artifacts/`
subdirectory, never the dataset report root directly. Use
`get_reports_dir("sc2", "sc2egset") / "artifacts"` from
`rts_predict.common.notebook_utils`. Notebooks themselves are not cited as
findings sources — only the report artifacts are.
