"""Tests for scripts/check_mirror_drift.py.

All tests use tmp_path to create synthetic directory trees.
No dependency on the real repo structure.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_module(script_path: Path):  # type: ignore[return]
    """Load a script as a module without adding it to sys.modules permanently."""
    spec = importlib.util.spec_from_file_location("check_mirror_drift", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture()
def mod(tmp_path: Path) -> object:
    """Load the check_mirror_drift module (using the real script path)."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    script = repo_root / "scripts" / "check_mirror_drift.py"
    return _load_module(script)


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Create a minimal synthetic repo structure."""
    # src/rts_predict/sc2/ingestion.py
    src = tmp_path / "src" / "rts_predict" / "sc2"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "ingestion.py").write_text("")

    # tests/rts_predict/sc2/test_ingestion.py
    tests = tmp_path / "tests" / "rts_predict" / "sc2"
    tests.mkdir(parents=True)
    (tests / "test_ingestion.py").write_text("")

    # pyproject.toml with empty exemptions
    (tmp_path / "pyproject.toml").write_text(
        "[tool.mirror_drift]\nexempt_sources = []\n"
    )
    return tmp_path


def test_source_to_test_path_basic(mod: object, tmp_path: Path) -> None:
    """Verifies the mapping for a standard module."""
    repo_root = tmp_path
    source = repo_root / "src" / "rts_predict" / "sc2" / "ingestion.py"
    result = mod.source_to_test_path(source, repo_root)  # type: ignore[attr-defined]
    expected = repo_root / "tests" / "rts_predict" / "sc2" / "test_ingestion.py"
    assert result == expected


def test_test_to_source_path_basic(mod: object, tmp_path: Path) -> None:
    """Verifies the reverse mapping."""
    repo_root = tmp_path
    test_file = repo_root / "tests" / "rts_predict" / "sc2" / "test_ingestion.py"
    result = mod.test_to_source_path(test_file, repo_root)  # type: ignore[attr-defined]
    expected = repo_root / "src" / "rts_predict" / "sc2" / "ingestion.py"
    assert result == expected


def test_forward_check_missing_test(mod: object, fake_repo: Path) -> None:
    """Creates a source file without a test; verifies forward check catches it."""
    # Add a new source file with no corresponding test
    new_src = fake_repo / "src" / "rts_predict" / "sc2" / "processing.py"
    new_src.write_text("")

    errors = mod.check_forward(fake_repo, set())  # type: ignore[attr-defined]
    assert any("processing.py" in e for e in errors), f"Expected processing.py error, got: {errors}"


def test_forward_check_exempt_source(mod: object, fake_repo: Path) -> None:
    """Creates an exempt source file without a test; verifies no error."""
    new_src = fake_repo / "src" / "rts_predict" / "sc2" / "config.py"
    new_src.write_text("")

    exemptions = {"src/rts_predict/sc2/config.py"}
    errors = mod.check_forward(fake_repo, exemptions)  # type: ignore[attr-defined]
    assert not any("config.py" in e for e in errors), f"config.py should be exempt, got: {errors}"


def test_reverse_check_orphaned_test(mod: object, fake_repo: Path) -> None:
    """Creates a test file without a source; verifies reverse check catches it."""
    # Add a test with no corresponding source
    orphan = fake_repo / "tests" / "rts_predict" / "sc2" / "test_orphan.py"
    orphan.write_text("")

    errors = mod.check_reverse(fake_repo)  # type: ignore[attr-defined]
    assert any("orphan" in e for e in errors), f"Expected orphan error, got: {errors}"


def test_forward_check_clean(mod: object, fake_repo: Path) -> None:
    """A fully mirrored tree passes forward check."""
    errors = mod.check_forward(fake_repo, set())  # type: ignore[attr-defined]
    assert errors == [], f"Expected no errors, got: {errors}"


def test_conftest_excluded(mod: object, fake_repo: Path) -> None:
    """conftest.py files in src are not collected by find_source_files (they would
    only appear in tests/), but conftest.py in tests/ is not a test_*.py file so
    it is not collected by find_mirrored_test_files either."""
    # Add a conftest.py in src (unusual but possible)
    conftest_src = fake_repo / "src" / "rts_predict" / "sc2" / "conftest.py"
    conftest_src.write_text("")

    # find_source_files collects all .py excluding __init__.py, including conftest.py
    # But conftest.py does NOT map to test_conftest.py as a test file typically
    # The plan says conftest files in tests/ are not test_*.py so check_reverse skips them
    # For forward check, conftest.py in src would trigger a missing test unless exempt.
    # Add it to exemptions for this test.
    exemptions = {"src/rts_predict/sc2/conftest.py"}
    errors = mod.check_forward(fake_repo, exemptions)  # type: ignore[attr-defined]
    assert not any("conftest.py" in e.split("/")[-1] for e in errors), (
        f"conftest should be exempt, got: {errors}"
    )

    # conftest in tests/ (not test_*.py) must not appear in find_mirrored_test_files
    conftest_tests = fake_repo / "tests" / "rts_predict" / "sc2" / "conftest.py"
    conftest_tests.write_text("")
    test_files = mod.find_mirrored_test_files(fake_repo)  # type: ignore[attr-defined]
    assert not any(p.name == "conftest.py" for p in test_files), (
        f"conftest.py should not appear in mirrored test files: {test_files}"
    )


def test_init_excluded(mod: object, fake_repo: Path) -> None:
    """__init__.py files are not collected by find_source_files."""
    # __init__.py already exists in fake_repo/src/rts_predict/sc2/
    source_files = mod.find_source_files(fake_repo)  # type: ignore[attr-defined]
    assert not any("__init__" in str(p) for p in source_files), (
        f"__init__.py should be excluded, got: {source_files}"
    )
