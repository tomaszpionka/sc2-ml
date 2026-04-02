# ML Experiment Protocol

## Data Leakage Rules (Critical for Thesis Quality)

- Never use current-match stats (APM, SQ, supply_capped_pct, game_loops) as features — only pre-match historical aggregates
- GNN node features should ideally be recomputed from training edges only
- Any new feature must respect this principle — validate before integrating

## Experiment Protocol

1. **Hypothesis first** — before modifying any model or feature, document what you're changing and why it should help
2. **Run and log** — after every experiment, log results in `reports/` following the `XX_run.md` naming convention
3. **Compare baselines** — always compare against established results (~63-65% accuracy for classical models)
4. **Temporal splits only** — no random shuffling; use `GLOBAL_TEST_SIZE` from `main.py` for consistency
5. **Fixed seeds** — random seed 42 is the convention; all experiments must be reproducible
6. **Validate inputs/outputs** — at each pipeline stage, check data shapes, nulls, distributions, and edge cases before proceeding
7. **Report both metrics** — include "all test" and "veterans only" (3+ historical matches) accuracy figures

## Documentation Artifacts

### CHANGELOG.md (code versioning)
- [Keep a Changelog](https://keepachangelog.com/) format
- Each merged branch gets its own semver section (e.g. `[0.7.0] — 2026-04-02 (PR #8: feat/classical-eval)`)
- `[Unreleased]` tracks only the current working branch's uncommitted/unmerged changes
- On merge, move `[Unreleased]` content into a new versioned section and bump `__version__` in `__init__.py`
- Concise one-liners grouped by: `Added`, `Changed`, `Fixed`, `Removed`
- Updated every session that changes code

### reports/research_log.md (thesis material)
- Reverse chronological, date-stamped entries
- Each entry uses structured fields: **Objective**, **Approach**, **Issues encountered**, **Resolution/Outcome**, **Thesis notes**
- References execution reports (`reports/archive/XX_run.md`) and specific commits where relevant
- Directly usable as source material when writing thesis chapters
- Updated every session involving experimentation, methodology decisions, issues, or breakthroughs

### reports/archive/XX_run.md (pipeline execution output)
- Legacy pipeline execution results and metrics (ChatGPT/Gemini era)
- Archived for reference — reports 07-09 contain primary baseline metrics (~64.5% accuracy)
- Referenced from research log entries, not replaced by them
