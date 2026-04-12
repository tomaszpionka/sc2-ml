# Planning Index

## Active plan
- [Current Plan](current_plan.md) — the authoritative Spec for this PR

## Execution schedule
- [DAG](dags/DAG.yaml) — machine-readable execution graph
- [DAG format docs](dags/README.md)

## Task specs
- [Parallel execution guide](specs/README.md)

- [spec_01](specs/spec_01_trim_claude.md) — trim CLAUDE.md (~16 lines)
- [spec_02](specs/spec_02_trim_architecture.md) — trim ARCHITECTURE.md (~18 lines)
- [spec_03](specs/spec_03_trim_executor.md) — trim executor.md (~40 lines)
- [spec_04](specs/spec_04_phase_consolidation.md) — delete phase derivatives + drift hook
- [spec_05](specs/spec_05_readmes_templates.md) — create docs/templates + .claude READMEs
- [spec_06](specs/spec_06_readmes_thesis_scripts.md) — create thesis + scripts READMEs
- [spec_07](specs/spec_07_readmes_lifecycle_games.md) — create lifecycle + game READMEs
- [spec_08](specs/spec_08_readme_reports.md) — create reports/README.md
- [spec_09](specs/spec_09_index.md) — update docs/INDEX.md directory map
- [spec_10](specs/spec_10_planning_drift.md) — write check_planning_drift.py + tests
- [spec_11](specs/spec_11_precommit.md) — wire pre-commit hook
- [spec_12](specs/spec_12_changelog.md) — CHANGELOG

## Agent routing

| Role | Read | Skip |
|------|------|------|
| Executor (dispatched to spec_NN) | `specs/spec_NN.md` | `current_plan.md`, `DAG.yaml` |
| Reviewer (post-group gate) | `dags/DAG.yaml`, diff | `current_plan.md`, `specs/` |
| Adversarial reviewer (final gate) | `current_plan.md`, `dags/DAG.yaml` | `specs/` |
| Parent orchestrator | `dags/DAG.yaml` | `specs/` (reads only to dispatch) |
