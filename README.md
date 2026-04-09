# RTS Outcome Prediction

Master's thesis: "A comparative analysis of methods for predicting game results in
real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

**Institution:** Polish-Japanese Academy of Information Technology (PJAIT), Warsaw
**Degree:** Master of Science in Computer Science, Data Science specialisation

Predicts professional match outcomes from replay data using classical ML, graph
embeddings, and Graph Neural Networks. SC2 is the primary dataset; AoE2 integration
is planned after SC2 work is complete.

## Quick Start
```bash
poetry install
poetry run sc2 --help
poetry run pytest tests/ -v --cov=rts_predict
```

## Key Documents

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | AI assistant instructions and project rules — read first |
| `.claude/scientific-invariants.md` | Thesis methodology constraints — non-negotiable |
| `docs/PHASES.md` | **Canonical phase list — 7 Phases of the ML experiment lifecycle** |
| `reports/research_log.md` | Reverse-chronological thesis narrative |
| `CHANGELOG.md` | Code version history |
| `.claude/` | Coding, workflow, and ML experiment standards |
| `docs/thesis/PJAIT_THESIS_REQUIREMENTS.md` | Institutional requirements — formatting, defense, grading |
| `.claude/thesis-formatting-rules.yaml` | Machine-readable PJAIT formatting thresholds |

## Prior Drafts (reference only — not authoritative)

| Document | Status |
|----------|--------|
| `src/rts_predict/sc2/reports/archive/ROADMAP_v1.md` | Superseded — caused premature jump to modelling before data exploration |
| `src/rts_predict/sc2/reports/archive/methodology_v1.md` | Superseded — assumed feature decisions not yet validated by exploration |
| `src/rts_predict/sc2/reports/archive/sanity_validation.md` | Evidence log of known issues pre-restart |

## Project State

The SC2 pipeline has a working ingestion layer and draft feature/model code, but data
exploration (Phase 01 — see `docs/PHASES.md` and `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md`) has not been completed.
All feature and model code is a draft to be audited and revised as exploration findings
arrive. Do not treat existing module outputs as validated results.
