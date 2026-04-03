# SC2-ML: RTS Game Result Prediction

Master's thesis: "A comparative analysis of methods for predicting game results in
real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

Predicts professional match outcomes from replay data using classical ML, graph
embeddings, and Graph Neural Networks. SC2 is the primary dataset; AoE2 integration
is planned after SC2 work is complete.

## Quick Start
```bash
poetry install
poetry run sc2ml --help
poetry run pytest tests/ src/ -v --cov=sc2ml
```

## Key Documents

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | AI assistant instructions and project rules — read first |
| `.claude/scientific-invariants.md` | Thesis methodology constraints — non-negotiable |
| `reports/SC2ML_THESIS_ROADMAP.md` | **Authoritative phase-by-phase execution plan** |
| `reports/research_log.md` | Reverse-chronological thesis narrative |
| `CHANGELOG.md` | Code version history |
| `.claude/` | Coding, workflow, and ML experiment standards |

## Prior Drafts (reference only — not authoritative)

| Document | Status |
|----------|--------|
| `reports/archive/ROADMAP_v1.md` | Superseded — caused premature jump to modelling before data exploration |
| `reports/archive/methodology_v1.md` | Superseded — assumed feature decisions not yet validated by exploration |
| `reports/archive/sanity_validation.md` | Evidence log of known issues pre-restart |

## Project State

The SC2 pipeline has a working ingestion layer and draft feature/model code, but data
exploration (Phases 1–6 of `SC2ML_THESIS_ROADMAP.md`) has not been completed.
All feature and model code is a draft to be audited and revised as exploration findings
arrive. Do not treat existing module outputs as validated results.
