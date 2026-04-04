# Common Package Contract

This package contains code shared across all game-specific packages (SC2, AoE2).
The boundary rule is simple: if it's game-agnostic, it goes here. If it requires
knowledge of a specific game's mechanics, data format, or domain, it goes in the
game package.

## What belongs here

- **Evaluation metrics**: log-loss, AUC-ROC, Brier score, calibration curves,
  bootstrap confidence intervals. These are identical across games.
- **Split validation utilities**: temporal leakage checks, class balance verification,
  subgroup distribution comparison. Game-agnostic by design.
- **Report formatting**: markdown table generation, figure export helpers,
  research log entry templates.
- **Cross-game comparison protocol**: the implementation of Scientific Invariant #10
  (shared evaluation protocol, identical metrics, matched experimental conditions).
- **Base classes / interfaces**: abstract feature group, abstract data pipeline step,
  if these patterns emerge and prove useful. Do not create them speculatively.

## What does NOT belong here

- Data ingestion (game-specific file formats: SC2Replay.json vs AoE2 recorded games)
- Feature engineering (races vs civilizations, APM semantics, economy models differ)
- Cleaning rules (game-specific anomalies, duration thresholds, player ID schemes)
- CLI entry points (each game has its own CLI)
- Config (DB paths, replay directories, game constants)
- Rating systems implementation (shared in principle, but calibration and
  cold-start handling may differ per game — start in game packages, extract
  to common only if implementations converge)

## When to extract to common

Do NOT pre-emptively create abstractions. The rule is:
1. Build it in the first game package (SC2)
2. Build it again in the second game package (AoE2)
3. If the implementations are >80% identical, extract to common
4. If they diverge meaningfully, keep them separate with a comment explaining why

This avoids premature abstraction, which is worse than duplication in a
two-game thesis project.
