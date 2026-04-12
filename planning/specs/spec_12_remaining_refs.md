---
task_id: "T12"
task_name: "Update AGENT_MANUAL.md + README.md + ROADMAPs"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "docs/agents/AGENT_MANUAL.md"
  - "README.md"
  - "src/rts_predict/sc2/reports/sc2egset/ROADMAP.md"
  - "src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md"
  - "src/rts_predict/aoe2/reports/aoestats/ROADMAP.md"
  - "src/rts_predict/aoe2/reports/ROADMAP.md"
read_scope: []
category: "C"
---

# Spec: Update AGENT_MANUAL.md + README.md + ROADMAPs

## Objective

Update remaining references across documentation and dataset ROADMAPs.

## Instructions

1. `docs/agents/AGENT_MANUAL.md`: update research_log references to
   per-dataset pattern.
2. `README.md`: update key document pointer to describe new structure.
3. 3 dataset ROADMAPs (`sc2egset/ROADMAP.md`, `aoe2companion/ROADMAP.md`,
   `aoestats/ROADMAP.md`): add `research_log.md` to their contents/sibling
   files listing (it's now a sibling file in the same directory).
4. `src/rts_predict/aoe2/reports/ROADMAP.md` (game-level): change
   "recorded in `reports/research_log.md`" → "recorded in the dataset's
   `research_log.md`" (this file directs dataset-specific decision gate
   findings, not CROSS entries).

## Verification

- All 6 files reference per-dataset logs
- Game-level AoE2 ROADMAP no longer directs dataset findings to root
