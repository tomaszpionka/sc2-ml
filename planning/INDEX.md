# Planning Index

## Active plan
- [Current Plan](current_plan.md) — the authoritative Spec for this PR

## Execution schedule
- [DAG](dags/DAG.yaml) — machine-readable execution graph
- [DAG format docs](dags/README.md)

## Task specs
- [Parallel execution guide](specs/README.md)

### TG01 — Safety + file moves
- [spec_01](specs/spec_01_gitignore.md) — Update .gitignore + settings.json (MUST be first)
- [spec_02](specs/spec_02_mv_sc2.md) — git mv SC2 tracked files
- [spec_03](specs/spec_03_mv_aoe2.md) — git mv AoE2 tracked files
- [spec_04](specs/spec_04_mv_data.md) — Filesystem mv raw data + verify
- [spec_05](specs/spec_05_tests.md) — Restructure test mirror

### TG02 — Code updates (depends on TG01)
- [spec_06](specs/spec_06_config.md) — Rewrite config.py path constants
- [spec_07](specs/spec_07_imports.md) — Update imports + pyproject + notebooks + scripts

### TG03 — Documentation + cleanup + CHANGELOG (depends on TG02)
- [spec_08](specs/spec_08_claude_agents.md) — Update CLAUDE.md + agent defs + rules
- [spec_09](specs/spec_09_docs.md) — Update docs + templates + reports
- [spec_10](specs/spec_10_cleanup.md) — Clean up .gitignore + final verification
- [spec_11](specs/spec_11_changelog.md) — Update CHANGELOG

## Agent routing

| Role | Read | Skip |
|------|------|------|
| Executor (dispatched to spec_NN) | `specs/spec_NN.md` | `current_plan.md`, `DAG.yaml` |
| Reviewer (post-group gate) | `dags/DAG.yaml`, diff | `current_plan.md`, `specs/` |
| Reviewer-deep (final gate) | `current_plan.md`, `dags/DAG.yaml`, all specs | — |
| Parent orchestrator | `dags/DAG.yaml` | `specs/` (reads only to dispatch) |
