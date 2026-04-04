Before reading this file, read `.claude/scientific-invariants.md`.
The invariants there take precedence over any implementation convenience
described here.

# ML Experiment Protocol

## Data Leakage Rules (Critical for Thesis Quality)

**The fundamental rule:** For any game G played at time T, only information
strictly from games played before T may be used to predict G's outcome.
This applies to ALL features without exception.

**Why this matters for this thesis:** The prediction task is a sliding window —
predict game M+1 for a player given their results in games 1..M within a
tournament, plus their entire cross-tournament history before that tournament.
Any feature computed from game M+1 itself (its duration, its in-game stats,
its result) is contamination that makes results unreproducible in real inference.

**The three leakage failure modes to test explicitly:**
1. Rolling aggregates computed using the target game's own value
2. Head-to-head win rates that include the target game
3. Within-tournament features that include the target game's position

## Experiment Protocol

1. **Hypothesis first** — before modifying any model or feature, document what you're changing and why it should help
2. **Run and log** — after every experiment, log results in the game-specific reports directory (e.g. `src/rts_predict/sc2/reports/`) following the `XX_run.md` naming convention
3. **Compare baselines** — always compare against established results (~63-65% accuracy for classical models)
4. **Temporal splits only** — no random shuffling. The correct split strategy is
per-player leave-last-tournament-out (see reports/ROADMAP.md Phase 8). The
legacy create_temporal_split() and GLOBAL_TEST_SIZE are superseded and must
not be used for any thesis experiment.
5. **Fixed seeds** — random seed 42 is the convention; all experiments must be reproducible
6. **Validate inputs/outputs** — at each pipeline stage, check data shapes, nulls, distributions, and edge cases before proceeding
7. **Report both metrics** — include "all test" and "veterans only" (3+ historical matches) accuracy figures

## Documentation Artifacts

### CHANGELOG.md (code versioning)
- [Keep a Changelog](https://keepachangelog.com/) format
- Each merged branch gets its own semver section (e.g. `[0.7.0] — 2026-04-02 (PR #8: feat/classical-eval)`)
- `[Unreleased]` tracks only the current working branch's uncommitted/unmerged changes
- On merge, move `[Unreleased]` content into a new versioned section and bump the version in `pyproject.toml`
- Concise one-liners grouped by: `Added`, `Changed`, `Fixed`, `Removed`
- Updated every session that changes code

### reports/research_log.md (thesis material)
- Reverse chronological, date-stamped entries
- Each entry uses structured fields: **Objective**, **Approach**, **Issues encountered**, **Resolution/Outcome**, **Thesis notes**
- References execution reports (`reports/archive/XX_run.md`) and specific commits where relevant
- Directly usable as source material when writing thesis chapters
- Updated every session involving experimentation, methodology decisions, issues, or breakthroughs

### src/rts_predict/sc2/reports/archive/XX_run.md (pipeline execution output)
- Legacy pipeline execution results and metrics (ChatGPT/Gemini era)
- Archived for reference — reports 07-09 contain primary baseline metrics (~64.5% accuracy)
- Referenced from research log entries, not replaced by them
