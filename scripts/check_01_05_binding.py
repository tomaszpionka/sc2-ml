#!/usr/bin/env python3
"""Pre-commit / CI binding checker for 01_05 Temporal & Panel EDA notebooks.

Scans Python files under sandbox/*/01_exploration/05_temporal_panel_eda/ and
verifies that each file's docstring contains a spec-binding line of the form:

    # spec: reports/specs/01_05_preregistration.md@<git-SHA>

and that the cited SHA resolves in git history (git cat-file -e <SHA>).

Usage
-----
    python scripts/check_01_05_binding.py --check   # staged files only (pre-commit)
    python scripts/check_01_05_binding.py --all     # all matching files (CI)

Exit codes
----------
0  All files pass (or no matching files found).
1  One or more files are missing or have an invalid spec-binding line.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SPEC_PATTERN = re.compile(
    r"#\s*spec:\s*reports/specs/01_05_preregistration\.md@([0-9a-f]{7,40})"
)
GLOB = "sandbox/*/01_exploration/05_temporal_panel_eda/*.py"
SCAN_LINES = 40


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def staged_matching_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
        cwd=root,
    )
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        p = root / line
        if p.match(GLOB) and p.suffix == ".py":
            paths.append(p)
    return paths


def all_matching_files(root: Path) -> list[Path]:
    return list(root.glob(GLOB))


def sha_exists(sha: str, root: Path) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", sha],
        capture_output=True,
        cwd=root,
    )
    return result.returncode == 0


def check_file(path: Path, root: Path) -> str | None:
    """Return error message or None if file passes."""
    lines = path.read_text(encoding="utf-8").splitlines()[:SCAN_LINES]
    for line in lines:
        m = SPEC_PATTERN.search(line)
        if m:
            sha = m.group(1)
            if sha_exists(sha, root):
                return None
            return (
                f"{path.relative_to(root)}: spec-binding SHA '{sha}' not found in "
                f"git history. Did you copy a SHA from a future commit?"
            )
    return (
        f"{path.relative_to(root)}: missing spec-binding line in first {SCAN_LINES} lines.\n"
        f"  Expected: # spec: reports/specs/01_05_preregistration.md@<git-SHA>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Check staged files only (pre-commit mode).",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Check all matching files (CI mode).",
    )
    args = parser.parse_args()

    root = repo_root()
    files = staged_matching_files(root) if args.check else all_matching_files(root)

    if not files:
        # No matching files — Phase 01_05 has not started yet; no-op.
        return 0

    errors: list[str] = []
    for f in sorted(files):
        err = check_file(f, root)
        if err:
            errors.append(err)

    if errors:
        print("check-01-05-binding FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"check-01-05-binding OK ({len(files)} file(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
