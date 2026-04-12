# Planning Index

## Active plan
- [Current Plan](current_plan.md) — the authoritative Spec for this PR

## Execution schedule
- [DAG](dags/DAG.yaml) — machine-readable execution graph
- [DAG format docs](dags/README.md)

## Task specs
- [Parallel execution guide](specs/README.md)

- [spec_01](specs/spec_01_sc2_research_log.md) — create sc2egset per-dataset research log
- [spec_02](specs/spec_02_aoe2c_research_log.md) — create aoe2companion per-dataset research log
- [spec_03](specs/spec_03_aoestats_research_log.md) — create aoestats per-dataset research log
- [spec_04](specs/spec_04_root_index.md) — rewrite root research_log.md as index + CROSS
- [spec_05](specs/spec_05_orchestrator_agents.md) — update CLAUDE.md + executor.md
- [spec_06](specs/spec_06_reviewer_agents.md) — update reviewer-deep + reviewer-adversarial
- [spec_07](specs/spec_07_planner_agents.md) — update planner-science + ml-protocol
- [spec_08](specs/spec_08_rules.md) — update reviewer + git-workflow + thesis-writing
- [spec_09](specs/spec_09_architecture.md) — update ARCHITECTURE.md + INDEX.md
- [spec_10](specs/spec_10_phase_docs.md) — update TAXONOMY + PHASES + STEPS
- [spec_11](specs/spec_11_templates.md) — update templates + research docs
- [spec_12](specs/spec_12_remaining_refs.md) — update AGENT_MANUAL + README + ROADMAPs
- [spec_13](specs/spec_13_changelog.md) — CHANGELOG update

## Agent routing

| Role | Read | Skip |
|------|------|------|
| Executor (dispatched to spec_NN) | `specs/spec_NN.md` | `current_plan.md`, `DAG.yaml` |
| Reviewer (post-group gate) | `dags/DAG.yaml`, diff | `current_plan.md`, `specs/` |
| Adversarial reviewer (final gate) | `current_plan.md`, `dags/DAG.yaml` | `specs/` |
| Parent orchestrator | `dags/DAG.yaml` | `specs/` (reads only to dispatch) |
