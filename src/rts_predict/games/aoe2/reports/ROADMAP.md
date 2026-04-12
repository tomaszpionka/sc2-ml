# AoE2 Game-Level Roadmap

This file is a navigation aid. It does not own phase planning or step
definitions. All phases are dataset-scoped; each dataset has its own
ROADMAP with fully defined Steps for the active Phase.

**Canonical phase structure:** [`docs/PHASES.md`](../../../docs/PHASES.md)
**Methodology manuals:** [`docs/INDEX.md`](../../../docs/INDEX.md)

---

## Datasets

| Dataset | ROADMAP | PHASE_STATUS |
|---------|---------|--------------|
| aoe2companion | [`reports/aoe2companion/ROADMAP.md`](aoe2companion/ROADMAP.md) | [`reports/aoe2companion/PHASE_STATUS.yaml`](aoe2companion/PHASE_STATUS.yaml) |
| aoestats | [`reports/aoestats/ROADMAP.md`](aoestats/ROADMAP.md) | [`reports/aoestats/PHASE_STATUS.yaml`](aoestats/PHASE_STATUS.yaml) |

---

## Dataset Strategy (provisional — to be confirmed by Phase 01 Decision Gates)

**Planning indicators (2026-04-11, based on file inventory only — not verified
Phase 01 findings):**

1. aoe2companion has more files (4,154 vs 349) and spans a longer date range
   (2020-2026 vs 2022-2026) based on file inventory.
2. aoe2companion files have daily granularity; aoestats files have weekly
   granularity.

**Status:** Role assignment (PRIMARY vs SUPPLEMENTARY VALIDATION) requires
Phase 01 Decision Gate (01_06) evidence: schema completeness, null rates,
player identity coverage, temporal density. Until then, both datasets run
full Phases 01-07 independently with no scope restrictions.

**Decision point:** Pipeline Section 01_06 (Decision Gates) for each dataset
will produce the comparative evidence needed to formalize roles. The decision
will be recorded in `reports/research_log.md` with full derivation per
Invariant 6.
