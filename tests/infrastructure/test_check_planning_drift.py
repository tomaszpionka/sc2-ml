"""Tests for scripts/hooks/check_planning_drift.py.

All tests use tmp_path to create synthetic planning artifact trees.
No dependency on the real repo structure.
"""
from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path
from types import ModuleType

import pytest

# ---------------------------------------------------------------------------
# Module loading helper
# ---------------------------------------------------------------------------


def _load_module(script_path: Path) -> ModuleType:
    """Load check_planning_drift.py as a module without side effects.

    Args:
        script_path: Absolute path to the script.

    Returns:
        Loaded module object.
    """
    spec = importlib.util.spec_from_file_location("check_planning_drift", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="module")
def mod() -> ModuleType:
    """Load check_planning_drift module once per test module."""
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "hooks" / "check_planning_drift.py"
    return _load_module(script)


# ---------------------------------------------------------------------------
# Helpers to build synthetic file content
# ---------------------------------------------------------------------------

_VALID_PLAN_YAML_FM = textwrap.dedent("""\
    ---
    category: C
    branch: chore/example
    date: 2026-04-12
    planner_model: claude-opus-4-6
    ---

    # Plan: Example

    ## Scope

    A bounded unit of work.

    ## Execution Steps

    ### T01 — Do something

    **Objective:** Achieve a goal.

    **Instructions:**
    1. Do the thing.

    **Verification:**
    - pytest passes

    **File scope:**
    - path/to/file.py

    ## File Manifest

    | File | Action |
    |------|--------|
    | `path/to/file.py` | Create |

    ## Suggested Execution Graph

    ```yaml
    dag_id: example
    ```
""")

_VALID_PLAN_AF_FM = textwrap.dedent("""\
    ---
    category: A
    branch: feat/sc2-phase01
    date: 2026-04-12
    planner_model: claude-opus-4-6
    ---

    # Plan: Phase Work

    ## Scope

    Phase 01 ingestion.

    ## Problem Statement

    Data is not ingested yet.

    ## Assumptions & Unknowns

    - **Assumption:** Data exists.

    ## Literature Context

    Paper X says Y.

    ## Execution Steps

    ### T01 — Ingest

    **Objective:** Ingest data.
    **Instructions:**
    1. Run the ingestor.
    **Verification:**
    - pytest passes
    **File scope:**
    - src/ingestion.py

    ## File Manifest

    | File | Action |
    |------|--------|
    | `src/ingestion.py` | Create |

    ## Gate Condition

    - All tests pass.

    ## Open Questions

    - How large is the data? Resolves by: experiment.

    ## Suggested Execution Graph

    ```yaml
    dag_id: example_a
    ```
""")

_VALID_SPEC = textwrap.dedent("""\
    ---
    task_id: "T01"
    task_name: "Do something"
    agent: "executor"
    dag_ref: "planning/dags/DAG.yaml"
    group_id: "TG01"
    file_scope:
      - "path/to/file.py"
    category: "C"
    ---

    # Spec: Do something

    ## Objective

    Achieve a goal.

    ## Instructions

    1. Do the thing.

    ## Verification

    - pytest passes
""")

_VALID_DAG = textwrap.dedent("""\
    dag_id: "dag_example"
    plan_ref: "planning/current_plan.md"
    category: "C"
    branch: "chore/example"
    base_ref: "master"

    jobs:
      - job_id: "J01"
        name: "Example job"
        task_groups:
          - group_id: "TG01"
            name: "Example group"
            depends_on: []
            tasks:
              - task_id: "T01"
                name: "Do something"
                spec_file: "planning/specs/spec_01_example.md"
                file_scope:
                  - "path/to/file.py"
                depends_on: []
""")

_LEGACY_PLAN = textwrap.dedent("""\
    # Plan: Legacy Example

    **Category:** C
    **Branch:** `chore/legacy`
    **Date:** 2026-01-01

    ## Scope

    Legacy plan using bold metadata.
""")


# ---------------------------------------------------------------------------
# Tests: validate_current_plan
# ---------------------------------------------------------------------------


class TestValidateCurrentPlan:
    """Tests for validate_current_plan()."""

    def test_valid_plan_no_errors(self, mod: ModuleType, tmp_path: Path) -> None:
        """A fully valid plan with YAML frontmatter returns no errors."""
        plan = tmp_path / "current_plan.md"
        plan.write_text(_VALID_PLAN_YAML_FM)
        errors = mod.validate_current_plan(plan, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_valid_plan_category_a(self, mod: ModuleType, tmp_path: Path) -> None:
        """A valid category A plan with all extra sections returns no errors."""
        plan = tmp_path / "current_plan.md"
        plan.write_text(_VALID_PLAN_AF_FM)
        errors = mod.validate_current_plan(plan, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_missing_frontmatter_fields(self, mod: ModuleType, tmp_path: Path) -> None:
        """A plan missing required frontmatter fields returns errors."""
        content = textwrap.dedent("""\
            ---
            category: C
            ---

            ## Scope
            ## Execution Steps
            ## File Manifest
            ## Suggested Execution Graph
        """)
        plan = tmp_path / "current_plan.md"
        plan.write_text(content)
        errors = mod.validate_current_plan(plan, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("branch" in e for e in errors), f"Expected 'branch' error: {errors}"
        assert any("date" in e for e in errors), f"Expected 'date' error: {errors}"

    def test_missing_universal_section(self, mod: ModuleType, tmp_path: Path) -> None:
        """A plan missing a universal section returns a section error."""
        content = textwrap.dedent("""\
            ---
            category: C
            branch: chore/test
            date: 2026-04-12
            ---

            ## Scope

            Bounded work.

            ## Execution Steps

            Steps here.

            ## Suggested Execution Graph

            ```yaml
            dag_id: x
            ```
        """)
        # Missing "## File Manifest"
        plan = tmp_path / "current_plan.md"
        plan.write_text(content)
        errors = mod.validate_current_plan(plan, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("file manifest" in e.lower() for e in errors), (
            f"Expected 'File Manifest' section error: {errors}"
        )

    def test_missing_af_section(self, mod: ModuleType, tmp_path: Path) -> None:
        """A category A plan missing 'Gate Condition' returns an error."""
        content = textwrap.dedent("""\
            ---
            category: A
            branch: feat/sc2-phase01
            date: 2026-04-12
            ---

            ## Scope
            ## Problem Statement
            ## Assumptions & Unknowns
            ## Literature Context
            ## Execution Steps
            ## File Manifest
            ## Open Questions
            ## Suggested Execution Graph
        """)
        # Missing "## Gate Condition"
        plan = tmp_path / "current_plan.md"
        plan.write_text(content)
        errors = mod.validate_current_plan(plan, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("gate condition" in e.lower() for e in errors), (
            f"Expected 'Gate Condition' error: {errors}"
        )

    def test_legacy_bold_metadata_warns_not_blocks(
        self, mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Legacy bold-metadata plan prints a warning but returns no errors."""
        plan = tmp_path / "current_plan.md"
        plan.write_text(_LEGACY_PLAN)
        errors = mod.validate_current_plan(plan, repo_root=tmp_path)  # type: ignore[attr-defined]
        captured = capsys.readouterr()
        assert errors == [], f"Legacy plan should not produce errors, got: {errors}"
        assert "WARNING" in captured.out, (
            f"Expected WARNING in output, got: {captured.out!r}"
        )

    def test_no_frontmatter_not_legacy(self, mod: ModuleType, tmp_path: Path) -> None:
        """A plan with no frontmatter and no bold metadata returns an error."""
        content = textwrap.dedent("""\
            # Plain plan

            Some text without frontmatter or bold metadata.

            ## Scope

            Something.
        """)
        plan = tmp_path / "current_plan.md"
        plan.write_text(content)
        errors = mod.validate_current_plan(plan, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("frontmatter" in e.lower() for e in errors), (
            f"Expected frontmatter error: {errors}"
        )


# ---------------------------------------------------------------------------
# Tests: validate_spec_file
# ---------------------------------------------------------------------------


class TestValidateSpecFile:
    """Tests for validate_spec_file()."""

    def test_valid_spec_no_errors(self, mod: ModuleType, tmp_path: Path) -> None:
        """A fully valid spec returns no errors."""
        spec = tmp_path / "spec_01_example.md"
        spec.write_text(_VALID_SPEC)
        errors = mod.validate_spec_file(spec, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_missing_frontmatter_fields(self, mod: ModuleType, tmp_path: Path) -> None:
        """A spec missing required frontmatter fields returns errors."""
        content = textwrap.dedent("""\
            ---
            task_id: "T01"
            task_name: "Do something"
            ---

            ## Objective
            ## Instructions
            ## Verification
        """)
        spec = tmp_path / "spec_01_example.md"
        spec.write_text(content)
        errors = mod.validate_spec_file(spec, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("agent" in e for e in errors), f"Expected 'agent' error: {errors}"
        assert any("dag_ref" in e for e in errors), f"Expected 'dag_ref' error: {errors}"

    def test_missing_objective_section(self, mod: ModuleType, tmp_path: Path) -> None:
        """A spec missing ## Objective returns an error."""
        content = textwrap.dedent("""\
            ---
            task_id: "T01"
            task_name: "Do something"
            agent: "executor"
            dag_ref: "planning/dags/DAG.yaml"
            group_id: "TG01"
            file_scope:
              - "path/to/file.py"
            category: "C"
            ---

            ## Instructions

            1. Do the thing.

            ## Verification

            - pytest passes
        """)
        spec = tmp_path / "spec_01_example.md"
        spec.write_text(content)
        errors = mod.validate_spec_file(spec, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("objective" in e.lower() for e in errors), (
            f"Expected 'Objective' section error: {errors}"
        )

    def test_missing_verification_section(self, mod: ModuleType, tmp_path: Path) -> None:
        """A spec missing ## Verification returns an error."""
        content = textwrap.dedent("""\
            ---
            task_id: "T01"
            task_name: "Do something"
            agent: "executor"
            dag_ref: "planning/dags/DAG.yaml"
            group_id: "TG01"
            file_scope:
              - "path/to/file.py"
            category: "C"
            ---

            ## Objective

            Do the thing.

            ## Instructions

            1. Step one.
        """)
        spec = tmp_path / "spec_01_example.md"
        spec.write_text(content)
        errors = mod.validate_spec_file(spec, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("verification" in e.lower() for e in errors), (
            f"Expected 'Verification' section error: {errors}"
        )

    def test_context_section_not_required(self, mod: ModuleType, tmp_path: Path) -> None:
        """A valid spec without ## Context produces no errors (Context is optional)."""
        spec = tmp_path / "spec_01_example.md"
        spec.write_text(_VALID_SPEC)
        errors = mod.validate_spec_file(spec, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert errors == [], f"Context is optional; expected no errors: {errors}"

    def test_no_frontmatter_returns_error(self, mod: ModuleType, tmp_path: Path) -> None:
        """A spec with no frontmatter returns an error."""
        content = textwrap.dedent("""\
            # Spec: No frontmatter

            ## Objective
            ## Instructions
            ## Verification
        """)
        spec = tmp_path / "spec_01_example.md"
        spec.write_text(content)
        errors = mod.validate_spec_file(spec, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("frontmatter" in e.lower() for e in errors), (
            f"Expected frontmatter error: {errors}"
        )


# ---------------------------------------------------------------------------
# Tests: validate_dag
# ---------------------------------------------------------------------------


class TestValidateDAG:
    """Tests for validate_dag()."""

    def test_valid_dag_no_errors(self, mod: ModuleType, tmp_path: Path) -> None:
        """A valid DAG with resolvable spec_file refs returns no errors."""
        # Create the spec file that the DAG references
        specs_dir = tmp_path / "planning" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec_01_example.md").write_text(_VALID_SPEC)

        dag_dir = tmp_path / "planning" / "dags"
        dag_dir.mkdir(parents=True)
        dag = dag_dir / "DAG.yaml"
        dag.write_text(_VALID_DAG)

        errors, spec_files = mod.validate_dag(dag, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert errors == [], f"Expected no errors, got: {errors}"
        assert "planning/specs/spec_01_example.md" in spec_files

    def test_invalid_yaml_returns_error(self, mod: ModuleType, tmp_path: Path) -> None:
        """Invalid YAML content returns a parse error."""
        dag_dir = tmp_path / "planning" / "dags"
        dag_dir.mkdir(parents=True)
        dag = dag_dir / "DAG.yaml"
        dag.write_text("key: [unclosed\n")

        errors, _ = mod.validate_dag(dag, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("invalid YAML" in e or "YAML" in e for e in errors), (
            f"Expected YAML parse error: {errors}"
        )

    def test_missing_top_level_fields(self, mod: ModuleType, tmp_path: Path) -> None:
        """A DAG missing required top-level fields returns errors."""
        content = textwrap.dedent("""\
            dag_id: "dag_example"
            plan_ref: "planning/current_plan.md"
            jobs: []
        """)
        dag_dir = tmp_path / "planning" / "dags"
        dag_dir.mkdir(parents=True)
        dag = dag_dir / "DAG.yaml"
        dag.write_text(content)

        errors, _ = mod.validate_dag(dag, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("category" in e for e in errors), f"Expected 'category' error: {errors}"
        assert any("branch" in e for e in errors), f"Expected 'branch' error: {errors}"
        assert any("base_ref" in e for e in errors), f"Expected 'base_ref' error: {errors}"

    def test_broken_spec_file_ref(self, mod: ModuleType, tmp_path: Path) -> None:
        """A DAG whose spec_file does not exist on disk returns an error."""
        dag_dir = tmp_path / "planning" / "dags"
        dag_dir.mkdir(parents=True)
        dag = dag_dir / "DAG.yaml"
        dag.write_text(_VALID_DAG)
        # Do NOT create the spec file — should trigger the "not found on disk" error

        errors, _ = mod.validate_dag(dag, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("spec_file not found" in e for e in errors), (
            f"Expected 'spec_file not found' error: {errors}"
        )

    def test_task_missing_required_fields(self, mod: ModuleType, tmp_path: Path) -> None:
        """A task missing required fields returns a per-task error."""
        content = textwrap.dedent("""\
            dag_id: "dag_example"
            plan_ref: "planning/current_plan.md"
            category: "C"
            branch: "chore/example"
            base_ref: "master"

            jobs:
              - job_id: "J01"
                name: "Example"
                task_groups:
                  - group_id: "TG01"
                    name: "Group"
                    depends_on: []
                    tasks:
                      - task_id: "T01"
                        name: "Incomplete task"
                        # missing spec_file, file_scope, depends_on
        """)
        dag_dir = tmp_path / "planning" / "dags"
        dag_dir.mkdir(parents=True)
        dag = dag_dir / "DAG.yaml"
        dag.write_text(content)

        errors, _ = mod.validate_dag(dag, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert any("T01" in e for e in errors), f"Expected T01 error: {errors}"

    def test_spec_files_collected(self, mod: ModuleType, tmp_path: Path) -> None:
        """validate_dag returns the list of spec_file values from all tasks."""
        specs_dir = tmp_path / "planning" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec_01_example.md").write_text(_VALID_SPEC)

        dag_dir = tmp_path / "planning" / "dags"
        dag_dir.mkdir(parents=True)
        dag = dag_dir / "DAG.yaml"
        dag.write_text(_VALID_DAG)

        _, spec_files = mod.validate_dag(dag, repo_root=tmp_path)  # type: ignore[attr-defined]
        assert spec_files == ["planning/specs/spec_01_example.md"]


# ---------------------------------------------------------------------------
# Tests: check_orphaned_specs
# ---------------------------------------------------------------------------


class TestCheckOrphanedSpecs:
    """Tests for check_orphaned_specs()."""

    def test_no_orphans_when_all_referenced(
        self, mod: ModuleType, tmp_path: Path
    ) -> None:
        """No errors when every on-disk spec is referenced in the DAG."""
        specs_dir = tmp_path / "planning" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec_01_example.md").write_text(_VALID_SPEC)

        dag_refs = ["planning/specs/spec_01_example.md"]
        errors = mod.check_orphaned_specs(  # type: ignore[attr-defined]
            dag_refs, specs_dir=specs_dir, repo_root=tmp_path
        )
        assert errors == [], f"Expected no orphan errors, got: {errors}"

    def test_orphaned_spec_detected(self, mod: ModuleType, tmp_path: Path) -> None:
        """An on-disk spec not referenced in any DAG is reported as orphaned."""
        specs_dir = tmp_path / "planning" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec_01_example.md").write_text(_VALID_SPEC)
        (specs_dir / "spec_02_orphan.md").write_text(_VALID_SPEC)

        dag_refs = ["planning/specs/spec_01_example.md"]
        errors = mod.check_orphaned_specs(  # type: ignore[attr-defined]
            dag_refs, specs_dir=specs_dir, repo_root=tmp_path
        )
        assert any("spec_02_orphan.md" in e for e in errors), (
            f"Expected orphan error for spec_02: {errors}"
        )

    def test_empty_specs_dir_no_errors(self, mod: ModuleType, tmp_path: Path) -> None:
        """An empty specs directory with no DAG refs produces no errors."""
        specs_dir = tmp_path / "planning" / "specs"
        specs_dir.mkdir(parents=True)

        errors = mod.check_orphaned_specs(  # type: ignore[attr-defined]
            [], specs_dir=specs_dir, repo_root=tmp_path
        )
        assert errors == [], f"Expected no errors for empty dirs: {errors}"

    def test_readme_not_treated_as_spec(self, mod: ModuleType, tmp_path: Path) -> None:
        """README.md in specs dir is not flagged as orphaned (only spec_*.md matched)."""
        specs_dir = tmp_path / "planning" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "README.md").write_text("# Specs README")

        errors = mod.check_orphaned_specs(  # type: ignore[attr-defined]
            [], specs_dir=specs_dir, repo_root=tmp_path
        )
        assert errors == [], f"README.md should not be flagged: {errors}"
