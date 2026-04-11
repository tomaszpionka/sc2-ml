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
source .venv/bin/activate && poetry install
source .venv/bin/activate && poetry run sc2 --help
source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict
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

## Prior Work

Superseded drafts and pre-restart artifacts were removed in v2.0.0 (archive
cleanup). Historical context is preserved in git history and `CHANGELOG.md`.

## Project Status

Phase progress is tracked per dataset in `PHASE_STATUS.yaml` files — see
`docs/PHASES.md` for the canonical phase list and `ARCHITECTURE.md` for
the full source-of-truth hierarchy.
