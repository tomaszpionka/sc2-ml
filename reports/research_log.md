# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

This log contains CROSS-dataset entries only. Dataset-specific findings
live in per-dataset logs — one per game/dataset combination.

| Dataset | Log | Last entry |
|---------|-----|------------|
| sc2 / sc2egset | [sc2egset research log](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md) | 2026-04-09 |
| aoe2 / aoe2companion | [aoe2companion research log](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md) | 2026-04-09 |
| aoe2 / aoestats | [aoestats research log](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md) | 2026-04-09 |

> **Phase migration note (2026-04-09):** This log was reset as part of the
> Phase 01-07 migration. Prior entries were removed in v2.0.0 (archive
> cleanup); historical context is preserved in git history.
> All new entries use the Phase XX / Step XX_YY_ZZ format per docs/PHASES.md.

---

## CROSS-Dataset Entries

---

## 2026-04-11 — [CROSS] AoE2 Dataset Strategy Decision

**Category:** C (chore — decision record)

### What
Formalized the AoE2 dataset strategy: aoe2companion is PRIMARY,
aoestats is SUPPLEMENTARY VALIDATION.

### Why
Both datasets had identical ROADMAP structures implying equal treatment.
Without formalization, Phase 01 work proceeds on both at equal priority,
potentially wasting 50% of AoE2 effort.

### Decisions taken
- aoe2companion (277M matches, daily, 2020–2026) runs full Phases 01–07.
- aoestats (30.7M matches, weekly, 2022–2026) runs full Phase 01, then
  lightweight Phase 02–05 replication for validation.
- Phase 06 uses aoe2companion exclusively.
- Contradictions between datasets are reported in thesis §6.5.

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1 Datasets

### Retraction (2026-04-11)

The PRIMARY / SUPPLEMENTARY VALIDATION role assignments and the aoestats Phase
06 exclusion are retracted. These commitments were made before Phase 01 EDA and
rely on unverified row counts and structural observations (file granularity)
rather than schema completeness, null rates, or feature availability — evidence
that Phase 01 Steps 01_02 through 01_06 are designed to produce. Per
docs/PHASES.md, whether generalisation holds between datasets is a Phase 01/02
finding, not a prior assumption. Both datasets now run full Phases 01-07
independently. Role assignment is deferred to Pipeline Section 01_06 (Decision
Gates).

---

## 2026-04-12 — [CROSS / Phase 01 / Step 01_01_01] File Inventory Summary

**Category:** A (phase work — rerun)
**Datasets:** sc2egset, aoe2companion, aoestats

Step 01_01_01 file inventory rerun completed for all 3 datasets.
Context leaks stripped, research log entries rewritten from artifacts.
ROADMAP source data sections, raw/README.md, and reports/README.md
repopulated strictly from 01_01_01 artifacts per Invariant #9.
Per-dataset findings in each dataset's research_log.md.

Per-dataset entries:
- [sc2egset](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md)
- [aoe2companion](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md)
- [aoestats](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md)
