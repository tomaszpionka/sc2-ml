# AoE2 Integration (Upcoming)

- AoE2 data pipeline does not exist yet
- Package location: `src/rts_predict/aoe2/` (placeholder exists, will be populated when SC2 pipeline is complete)
- Phase progress tracked in `src/rts_predict/aoe2/PHASE_STATUS.yaml`
- Architecture goal: shared abstractions where possible (feature engineering patterns, model evaluation framework) with game-specific modules
- AoE2 has different mechanics (civilizations vs races, different economy model, different replay format) — feature engineering needs adaptation, not copy-paste
- Comparative analysis framework needed: same model architectures on both games with consistent metrics
