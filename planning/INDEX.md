# Planning Index

## Active plan
- [Current Plan](current_plan.md) — Phase 01 Step 01_02_01 DuckDB Ingestion

## Execution schedule
- [DAG](dags/DAG.yaml) — machine-readable execution graph
- [DAG format docs](dags/README.md)

## Task specs
- [Parallel execution guide](specs/README.md)

### J01 — DuckDB ingestion, all datasets

#### TG01 — ROADMAP step definitions
- [spec_01](specs/spec_01_roadmaps.md) — Add 01_02_01 step defs to all 3 ROADMAPs

#### TG02 — Notebooks + ingestion + docs (depends on TG01)
- [spec_02](specs/spec_02_ingestion.md) — DuckDB ingestion — all 3 datasets (parameterized)

## Agent routing

| Role | Read | Skip |
|------|------|------|
| Executor (dispatched to spec_NN) | `specs/spec_NN.md` | `current_plan.md`, `DAG.yaml` |
| Reviewer-adversarial (final gate) | `current_plan.md`, `dags/DAG.yaml`, all specs | — |
| Parent orchestrator | `dags/DAG.yaml` | `specs/` (reads only to dispatch) |
