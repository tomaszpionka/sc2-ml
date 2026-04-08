#!/usr/bin/env python3
"""Check that the tests/ tree mirrors src/rts_predict/ and vice versa.

Exit 0 if the mirror is intact. Exit 1 with a report of drift otherwise.

Usage:
    python scripts/check_mirror_drift.py
    python scripts/check_mirror_drift.py --verbose
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def load_exemptions(repo_root: Path) -> set[str]:
    """Load exempt source paths from pyproject.toml [tool.mirror_drift]."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    pyproject = repo_root / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)

    raw: list[str] = data.get("tool", {}).get("mirror_drift", {}).get("exempt_sources", [])
    return set(raw)


def source_to_test_path(source_path: Path, repo_root: Path) -> Path:
    """Map src/rts_predict/<path>/module.py -> tests/rts_predict/<path>/test_module.py."""
    relative = source_path.relative_to(repo_root / "src" / "rts_predict")
    test_relative = relative.parent / f"test_{relative.name}"
    return repo_root / "tests" / "rts_predict" / test_relative


def test_to_source_path(test_path: Path, repo_root: Path) -> Path:
    """Map tests/rts_predict/<path>/test_module.py -> src/rts_predict/<path>/module.py."""
    relative = test_path.relative_to(repo_root / "tests" / "rts_predict")
    # Strip the "test_" prefix from the filename
    stem = relative.name
    if stem.startswith("test_"):
        source_name = stem[len("test_"):]
    else:
        source_name = stem
    source_relative = relative.parent / source_name
    return repo_root / "src" / "rts_predict" / source_relative


def find_source_files(repo_root: Path) -> list[Path]:
    """Find all .py files under src/rts_predict/ excluding __init__.py."""
    src_root = repo_root / "src" / "rts_predict"
    return [
        p
        for p in src_root.rglob("*.py")
        if p.name != "__init__.py"
    ]


def find_mirrored_test_files(repo_root: Path) -> list[Path]:
    """Find all test_*.py files under tests/rts_predict/."""
    tests_root = repo_root / "tests" / "rts_predict"
    if not tests_root.exists():
        return []
    return list(tests_root.rglob("test_*.py"))


def check_forward(
    repo_root: Path, exemptions: set[str]
) -> list[str]:
    """Check that every source file has a corresponding test file.

    Returns list of error messages for missing test files.
    """
    errors: list[str] = []
    for source_path in find_source_files(repo_root):
        # Normalise to repo-relative string for exemption check
        rel = str(source_path.relative_to(repo_root))
        if rel in exemptions:
            continue
        expected_test = source_to_test_path(source_path, repo_root)
        if not expected_test.exists():
            errors.append(
                f"MISSING TEST: {rel} has no corresponding {expected_test.relative_to(repo_root)}"
            )
    return errors


def check_reverse(repo_root: Path) -> list[str]:
    """Check that every mirrored test file has a corresponding source file.

    Returns list of error messages for orphaned test files.
    """
    errors: list[str] = []
    for test_path in find_mirrored_test_files(repo_root):
        expected_source = test_to_source_path(test_path, repo_root)
        if not expected_source.exists():
            errors.append(
                f"ORPHANED TEST: {test_path.relative_to(repo_root)} has no corresponding "
                f"{expected_source.relative_to(repo_root)}"
            )
    return errors


def main() -> int:
    """Run both checks and report results. Returns 0 on success, 1 on drift."""
    parser = argparse.ArgumentParser(
        description="Check that tests/ mirrors src/rts_predict/."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show all checked files"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    exemptions = load_exemptions(repo_root)

    if args.verbose:
        print(f"Repo root: {repo_root}")
        print(f"Exemptions ({len(exemptions)}):")
        for e in sorted(exemptions):
            print(f"  {e}")
        print()

    forward_errors = check_forward(repo_root, exemptions)
    reverse_errors = check_reverse(repo_root)

    all_errors = forward_errors + reverse_errors

    if all_errors:
        print(f"Mirror drift detected ({len(all_errors)} issue(s)):")
        for err in sorted(all_errors):
            print(f"  {err}")
        return 1

    source_count = len(find_source_files(repo_root))
    test_count = len(find_mirrored_test_files(repo_root))
    exempt_count = len(exemptions)
    print(
        f"Mirror intact: {source_count} source files, "
        f"{test_count} test files, "
        f"{exempt_count} exemptions."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
