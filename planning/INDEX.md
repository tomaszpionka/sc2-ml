# Planning Index

## Active plan
- [Current Plan](current_plan.md) — the authoritative Spec for this PR

## Execution schedule
- [DAG](dags/DAG.yaml) — machine-readable execution graph
- [DAG format docs](dags/README.md)

## Task specs
- [Parallel execution guide](specs/README.md)

- [spec_01](specs/spec_01_drift_tests.md) — planning drift hook: main() tests + absolute path fix
- [spec_02](specs/spec_02_aoe2_readme.md) — aoe2 README: per-dataset report/artifact paths
- [spec_03](specs/spec_03_strategy_ab.md) — Strategy A/B: TAXONOMY.md + pointers
- [spec_04](specs/spec_04_changelog.md) — CHANGELOG for follow-up fixes

## Agent routing

| Role | Read | Skip |
|------|------|------|
| Executor (dispatched to spec_NN) | `specs/spec_NN.md` | `current_plan.md`, `DAG.yaml` |
| Reviewer (post-group gate) | `dags/DAG.yaml`, diff | `current_plan.md`, `specs/` |
| Adversarial reviewer (final gate) | `current_plan.md`, `dags/DAG.yaml` | `specs/` |
| Parent orchestrator | `dags/DAG.yaml` | `specs/` (reads only to dispatch) |
