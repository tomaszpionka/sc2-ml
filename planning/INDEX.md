# Planning Index

## Active plan
- [Current Plan](current_plan.md) — the authoritative Spec for this PR

## Execution schedule
- [DAG](dags/DAG.yaml) — machine-readable execution graph
- [DAG format docs](dags/README.md)

## Task specs
- [Parallel execution guide](specs/README.md)

<!-- Spec links are added here when the DAG is materialized.
     Reset to this template state after PR merge. -->

## Agent routing

| Role | Read | Skip |
|------|------|------|
| Executor (dispatched to spec_NN) | `specs/spec_NN.md` | `current_plan.md`, `DAG.yaml` |
| Reviewer (post-group gate) | `dags/DAG.yaml`, diff | `current_plan.md`, `specs/` |
| Adversarial reviewer (final gate) | `current_plan.md`, `dags/DAG.yaml` | `specs/` |
| Parent orchestrator | `dags/DAG.yaml` | `specs/` (reads only to dispatch) |
