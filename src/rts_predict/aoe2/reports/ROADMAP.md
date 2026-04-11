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

## Dataset Strategy

**Decision (2026-04-11):** aoe2companion is the PRIMARY AoE2 dataset;
aoestats is SUPPLEMENTARY VALIDATION.

**Justification:**
1. aoe2companion has 9× more matches (277M vs 30.7M) and longer time span
   (2020–2026 vs 2022–2026) — better for temporal features and cold-start
   analysis (RQ4).
2. Daily granularity (vs weekly) enables denser rating computation.
3. THESIS_STRUCTURE.md §5.2 expects a single AoE2 result set.

**Implications:**
- aoe2companion runs full Phases 01–07.
- aoestats runs full Phase 01 for data quality understanding, then a
  lightweight Phase 02–05 pass for validation only (replicate the
  aoe2companion pipeline and compare results).
- Phase 06 uses aoe2companion data exclusively.
- If aoestats results contradict aoe2companion, report in thesis §6.5
  (Threats to Validity).
