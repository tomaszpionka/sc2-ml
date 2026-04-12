#!/usr/bin/env python3
"""Pre-commit hook: validate planning artifacts for structural completeness.

Validates three artifact types when planning/ files are staged:

1. ``planning/current_plan.md`` — YAML frontmatter fields + required sections.
   Bootstrap tolerance: legacy markdown-bold metadata warns but does not block.
   # TODO: enforce strict YAML frontmatter after this PR

2. ``planning/specs/spec_*.md`` — YAML frontmatter fields + required sections.
   Required sections: ## Objective, ## Instructions, ## Verification.
   Optional section: ## Context (not enforced; documented here for reference).

3. ``planning/dags/DAG.yaml`` — valid YAML, required fields, resolvable
   spec_file refs, and cross-file orphan detection.

Usage (typically invoked by pre-commit):
    python scripts/hooks/check_planning_drift.py

Exit codes:
    0 — all checks pass (warnings may have been printed)
    1 — one or more errors found
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml  # PyYAML — project dependency (pyyaml = "^6.0.3" in pyproject.toml)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANNING_DIR = REPO_ROOT / "planning"
SPECS_DIR = PLANNING_DIR / "specs"
DAGS_DIR = PLANNING_DIR / "dags"
CURRENT_PLAN = PLANNING_DIR / "current_plan.md"

# Required YAML frontmatter fields for current_plan.md
PLAN_FRONTMATTER_REQUIRED = {"category", "branch", "date"}

# Required sections for current_plan.md — universal (all categories)
PLAN_SECTIONS_UNIVERSAL = {
    "scope",
    "execution steps",
    "file manifest",
    "suggested execution graph",
}

# Additional required sections for category A and F
PLAN_SECTIONS_AF_EXTRA = {
    "problem statement",
    "assumptions & unknowns",
    "literature context",
    "gate condition",
    "open questions",
}

# Required YAML frontmatter fields for spec files
SPEC_FRONTMATTER_REQUIRED = {
    "task_id",
    "task_name",
    "agent",
    "dag_ref",
    "group_id",
    "file_scope",
    "category",
}

# Required sections for spec files
SPEC_SECTIONS_REQUIRED = {"objective", "instructions", "verification"}

# Required top-level fields for DAG.yaml
DAG_FIELDS_REQUIRED = {"dag_id", "plan_ref", "category", "branch", "base_ref"}

# Required per-task fields in DAG.yaml
DAG_TASK_FIELDS_REQUIRED = {"spec_file", "file_scope", "depends_on"}


# ---------------------------------------------------------------------------
# Frontmatter parsing (stdlib-only YAML block)
# ---------------------------------------------------------------------------

def _extract_yaml_frontmatter(text: str) -> tuple[dict[str, Any] | None, bool]:
    """Extract YAML frontmatter delimited by ``---`` lines.

    Args:
        text: Full file content.

    Returns:
        Tuple of (parsed_dict_or_None, is_legacy_bold_metadata).
        is_legacy_bold_metadata is True if the file uses **Key:** Value style
        instead of proper YAML frontmatter.
    """
    lines = text.splitlines()
    if not lines:
        return None, False

    # Detect legacy bold-metadata format: starts with markdown heading or bold key
    if not lines[0].strip().startswith("---"):
        # Check if it looks like legacy **Key:** Value format
        has_bold_meta = any(
            re.match(r"^\*\*\w", line) for line in lines[:10]
        )
        return None, has_bold_meta

    # Find closing ---
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        return None, False

    frontmatter_text = "\n".join(lines[1:end])
    try:
        parsed = yaml.safe_load(frontmatter_text)
        if isinstance(parsed, dict):
            return parsed, False
        return None, False
    except yaml.YAMLError:
        return None, False


def _extract_sections(text: str) -> set[str]:
    """Extract lowercase heading names from markdown (## level).

    Args:
        text: Full markdown file content.

    Returns:
        Set of lowercased heading text (without the ## prefix).
    """
    headings: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.+)", line)
        if m:
            headings.add(m.group(1).strip().lower())
    return headings


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_current_plan(path: Path, repo_root: Path | None = None) -> list[str]:
    """Validate planning/current_plan.md frontmatter and sections.

    Args:
        path: Path to current_plan.md.
        repo_root: Repository root used for relative-path display in error
            messages. Defaults to the module-level ``REPO_ROOT``.

    Returns:
        List of error strings (empty if valid; warnings are printed inline).
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    errors: list[str] = []
    text = path.read_text()
    frontmatter, is_legacy = _extract_yaml_frontmatter(text)

    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path

    if is_legacy:
        # Bootstrap tolerance: warn but do not block
        print(
            f"WARNING: {rel} uses legacy bold-metadata "
            "format instead of YAML frontmatter. "
            "Migrate to YAML frontmatter when convenient."
        )
        # Do not add to errors — legacy is allowed
    elif frontmatter is None:
        errors.append(f"{rel}: missing or unparseable YAML frontmatter")
    else:
        missing = PLAN_FRONTMATTER_REQUIRED - set(frontmatter.keys())
        if missing:
            errors.append(
                f"{rel}: frontmatter missing required fields: "
                + ", ".join(sorted(missing))
            )

    # Section checks — only if not legacy (legacy plans may lack sections)
    if not is_legacy:
        sections = _extract_sections(text)
        missing_sections = PLAN_SECTIONS_UNIVERSAL - sections
        if missing_sections:
            for s in sorted(missing_sections):
                errors.append(
                    f"{rel}: missing required section: '## {s.title()}'"
                )

        # Category A/F additional sections
        category = (frontmatter or {}).get("category", "")
        if str(category).upper() in ("A", "F"):
            missing_af = PLAN_SECTIONS_AF_EXTRA - sections
            for s in sorted(missing_af):
                errors.append(
                    f"{rel}: category {category} requires "
                    f"section: '## {s.title()}'"
                )

    return errors


def validate_spec_file(path: Path, repo_root: Path | None = None) -> list[str]:
    """Validate a spec file's frontmatter and required sections.

    Args:
        path: Path to a spec_*.md file.
        repo_root: Repository root used for relative-path display in error
            messages. Defaults to the module-level ``REPO_ROOT``.

    Returns:
        List of error strings.
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    errors: list[str] = []
    text = path.read_text()
    frontmatter, _ = _extract_yaml_frontmatter(text)

    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path

    if frontmatter is None:
        errors.append(f"{rel}: missing or unparseable YAML frontmatter")
    else:
        missing = SPEC_FRONTMATTER_REQUIRED - set(frontmatter.keys())
        if missing:
            errors.append(
                f"{rel}: frontmatter missing required fields: "
                + ", ".join(sorted(missing))
            )

    sections = _extract_sections(text)
    missing_sections = SPEC_SECTIONS_REQUIRED - sections
    for s in sorted(missing_sections):
        errors.append(f"{rel}: missing required section: '## {s.title()}'")

    return errors


def validate_dag(
    path: Path,
    repo_root: Path | None = None,
) -> tuple[list[str], list[str]]:
    """Validate a DAG.yaml file: schema, required fields, spec_file resolution.

    Args:
        path: Path to DAG.yaml.
        repo_root: Repository root used to resolve spec_file paths and for
            relative-path display. Defaults to the module-level ``REPO_ROOT``.

    Returns:
        Tuple of (errors, spec_files_referenced) where spec_files_referenced
        is a list of spec_file values found in all tasks.
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    errors: list[str] = []
    spec_files: list[str] = []

    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path

    try:
        dag = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        errors.append(f"{rel}: invalid YAML — {exc}")
        return errors, spec_files

    if not isinstance(dag, dict):
        errors.append(f"{rel}: expected a YAML mapping at the top level")
        return errors, spec_files

    # Required top-level fields
    missing = DAG_FIELDS_REQUIRED - set(dag.keys())
    if missing:
        errors.append(
            f"{rel}: missing required top-level fields: " + ", ".join(sorted(missing))
        )

    # Walk all tasks
    for job in dag.get("jobs", []):
        for group in job.get("task_groups", []):
            for task in group.get("tasks", []):
                task_id = task.get("task_id", "<unknown>")
                missing_task = DAG_TASK_FIELDS_REQUIRED - set(task.keys())
                if missing_task:
                    errors.append(
                        f"{rel}: task {task_id} missing fields: "
                        + ", ".join(sorted(missing_task))
                    )

                sf = task.get("spec_file")
                if sf:
                    spec_files.append(sf)
                    spec_path = root / sf
                    if not spec_path.exists():
                        errors.append(
                            f"{rel}: task {task_id} spec_file not found on disk: {sf}"
                        )

    return errors, spec_files


def check_orphaned_specs(
    dag_spec_files: list[str],
    specs_dir: Path | None = None,
    repo_root: Path | None = None,
) -> list[str]:
    """Check for spec files on disk that are not referenced in any DAG.

    Args:
        dag_spec_files: List of spec_file values collected from all DAG tasks.
        specs_dir: Directory to search for spec_*.md files. Defaults to
            ``SPECS_DIR`` (``planning/specs/`` relative to ``REPO_ROOT``).
        repo_root: Repository root used for relative-path display. Defaults
            to the module-level ``REPO_ROOT``.

    Returns:
        List of error strings for orphaned spec files.
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    search_dir = specs_dir if specs_dir is not None else SPECS_DIR
    errors: list[str] = []
    disk_specs = {
        str(p.relative_to(root))
        for p in search_dir.glob("spec_*.md")
    }
    referenced = set(dag_spec_files)
    orphans = disk_specs - referenced
    for orphan in sorted(orphans):
        errors.append(f"{orphan}: spec file on disk is not referenced in any DAG task")
    return errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run all planning drift checks and return exit code.

    Returns:
        0 if all checks pass, 1 if any errors were found.
    """
    all_errors: list[str] = []
    all_dag_spec_files: list[str] = []

    # 1. Validate current_plan.md (if it exists)
    if CURRENT_PLAN.exists():
        all_errors.extend(validate_current_plan(CURRENT_PLAN))

    # 2. Validate all spec files
    for spec_path in sorted(SPECS_DIR.glob("spec_*.md")):
        all_errors.extend(validate_spec_file(spec_path))

    # 3. Validate all DAG.yaml files + collect spec_file refs
    for dag_path in sorted(DAGS_DIR.glob("*.yaml")):
        dag_errors, spec_files = validate_dag(dag_path)
        all_errors.extend(dag_errors)
        all_dag_spec_files.extend(spec_files)

    # 4. Cross-file: check for orphaned specs
    all_errors.extend(check_orphaned_specs(all_dag_spec_files))

    if all_errors:
        print("PLANNING DRIFT DETECTED:")
        for err in all_errors:
            print(f"  {err}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
