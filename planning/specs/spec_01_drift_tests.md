---
task_id: "T01"
task_name: "Planning drift hook: main() integration tests + bug fixes"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "scripts/hooks/check_planning_drift.py"
  - "tests/infrastructure/test_check_planning_drift.py"
read_scope: []
category: "C"
---

# Spec: Planning drift hook — main() integration tests + bug fixes

## Objective

Add integration tests for `main()` and fix the absolute-path bug in orphan
detection. Verify the legacy heuristic does not misfire on plans with
YAML frontmatter.

## Instructions

1. Read `scripts/hooks/check_planning_drift.py` and
   `tests/infrastructure/test_check_planning_drift.py`.

2. Add `test_main_integration_clean` to the test file:
   - Build a synthetic repo tree (`tmp_path`) with valid `planning/current_plan.md`
     (YAML frontmatter + all required `##` sections), a valid
     `planning/dags/DAG.yaml` (one task referencing one spec), and a valid
     `planning/specs/spec_01_foo.md` (frontmatter + Objective + Instructions +
     Verification sections).
   - Call `main(repo_root=tmp_path)` and assert return code is 0.

3. Add `test_main_integration_errors`:
   - Same tree but the spec file is missing `## Objective`.
   - Call `main(repo_root=tmp_path)` and assert return code is 1.

4. Fix `check_orphaned_specs()` in `check_planning_drift.py`:
   - Before building the `referenced` set, normalize any absolute `spec_file`
     paths to relative using `Path(sf).relative_to(root)` if
     `Path(sf).is_absolute()`.
   - Add `test_absolute_spec_file_path`: DAG with an absolute `spec_file`
     value pointing to an existing spec. Assert no orphan error is raised.

5. Add `test_legacy_heuristic_false_positive`:
   - Plan with proper `---` YAML frontmatter AND `**NOTE:**` bold text in the
     first 10 lines.
   - Assert `_parse_frontmatter()` returns `is_legacy_bold_metadata=False`
     (frontmatter presence takes precedence over bold-pattern match).

6. Run `source .venv/bin/activate && poetry run pytest tests/infrastructure/test_check_planning_drift.py -v`
   to verify all tests pass.

## Verification

1. All existing + new tests pass.
2. `ruff check` and `mypy` clean on both files.
