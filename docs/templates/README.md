# docs/templates — Routing Index

## Authoring Templates

| Template | Consumer |
|---|---|
| `plan_template.md` | Planner agent — fills `planning/current_plan.md` |
| `plan_critique_template.md` | Reviewer agent — fills critique doc during planning review |
| `planner_output_contract.md` | Planner agent — governs required sections in `current_plan.md` |
| `spec_template.md` | Materializer agent — fills `planning/specs/spec_NN_<name>.md` |
| `dag_template.yaml` | Materializer agent — fills `planning/dags/DAG.yaml` |
| `phase_template.yaml` | Planner agent — fills per-phase narrative doc under `docs/` |
| `pipeline_section_template.yaml` | Executor agent — fills pipeline section docs |
| `notebook_template.yaml` | Executor agent — fills notebook front-matter in `sandbox/` |
| `research_log_entry_template.yaml` | Executor agent — fills one entry appended to `reports/research_log.md` |
| `research_log_template.yaml` | Executor agent — bootstraps a new `reports/research_log.md` |
| `raw_data_readme_template.yaml` | Executor agent — fills `data/raw/README.yaml` per dataset |

## Status Tracking Templates

| Template | Consumer |
|---|---|
| `phase_status_template.yaml` | Executor agent — bootstraps `reports/<dataset>/PHASE_STATUS.yaml` |
| `step_status_template.yaml` | Executor agent — bootstraps `reports/<dataset>/STEP_STATUS.yaml` |
| `pipeline_section_status_template.yaml` | Executor agent — bootstraps `reports/<dataset>/PIPELINE_SECTION_STATUS.yaml` |
| `dag_status_template.yaml` | Orchestrator — tracks gate state in `planning/dags/DAG_STATUS.yaml` |

## Operational Templates

| Template | Consumer |
|---|---|
| `dataset_roadmap_template.yaml` | Planner agent — fills `src/rts_predict/<game>/reports/<dataset>/ROADMAP.md` |
| `step_template.yaml` | Planner agent — documents individual pipeline steps |
