"""Tests for src/rts_predict/common/inventory.py."""

from pathlib import Path

import pytest

from rts_predict.common.inventory import inventory_directory


class TestInventoryDirectory:
    """Tests for inventory_directory()."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Zero files handled correctly."""
        empty = tmp_path / "empty"
        empty.mkdir()
        result = inventory_directory(empty)
        assert result.total_files == 0
        assert result.total_bytes == 0
        assert result.subdirs == []
        assert result.files_at_root == []

    def test_nonexistent_directory_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError raised when directory does not exist."""
        with pytest.raises(FileNotFoundError):
            inventory_directory(tmp_path / "nope")

    def test_file_not_directory_raises(self, tmp_path: Path) -> None:
        """NotADirectoryError raised when path is a file, not a directory."""
        f = tmp_path / "file.txt"
        f.write_text("x")
        with pytest.raises(NotADirectoryError):
            inventory_directory(f)

    def test_files_at_root_only(self, tmp_path: Path) -> None:
        """Files directly in root are counted correctly."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "a.json").write_text("x" * 10)
        (root / "b.json").write_text("x" * 20)
        result = inventory_directory(root)
        assert result.total_files == 2
        assert result.total_bytes == 30
        assert result.subdirs == []
        assert len(result.files_at_root) == 2

    def test_single_subdir(self, tmp_path: Path) -> None:
        """Single subdirectory is summarised correctly."""
        root = tmp_path / "root"
        root.mkdir()
        sub = root / "sub"
        sub.mkdir()
        (sub / "a.json").write_text("x" * 5)
        (sub / "b.txt").write_text("x" * 3)
        result = inventory_directory(root)
        assert result.total_files == 2
        assert len(result.subdirs) == 1
        assert result.subdirs[0].name == "sub"
        assert result.subdirs[0].file_count == 2
        assert result.subdirs[0].extensions == {".json": 1, ".txt": 1}

    def test_multiple_subdirs_sorted(self, tmp_path: Path) -> None:
        """Subdirectories are returned in alphabetical order."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "beta").mkdir()
        (root / "alpha").mkdir()
        (root / "beta" / "a.json").write_text("x")
        (root / "alpha" / "b.json").write_text("x")
        result = inventory_directory(root)
        assert result.subdirs[0].name == "alpha"
        assert result.subdirs[1].name == "beta"

    def test_glob_filter(self, tmp_path: Path) -> None:
        """Glob pattern filters files correctly."""
        root = tmp_path / "root"
        root.mkdir()
        sub = root / "sub"
        sub.mkdir()
        (sub / "a.json").write_text("x")
        (sub / "b.txt").write_text("x")
        result = inventory_directory(root, file_glob="*.json")
        assert result.total_files == 1
        assert result.subdirs[0].file_count == 1

    def test_empty_subdirs_excluded(self, tmp_path: Path) -> None:
        """Subdirectories with no matching files are excluded from results."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "empty_sub").mkdir()
        full_sub = root / "full_sub"
        full_sub.mkdir()
        (full_sub / "a.json").write_text("x")
        result = inventory_directory(root)
        assert len(result.subdirs) == 1
        assert result.subdirs[0].name == "full_sub"

    def test_include_file_lists_false(self, tmp_path: Path) -> None:
        """With include_file_lists=False, file lists are empty but counts correct."""
        root = tmp_path / "root"
        root.mkdir()
        sub = root / "sub"
        sub.mkdir()
        (sub / "a.json").write_text("x")
        result = inventory_directory(root, include_file_lists=False)
        assert result.subdirs[0].file_count == 1
        assert result.subdirs[0].files == []
        assert result.files_at_root == []

    def test_mixed_root_and_subdirs(self, tmp_path: Path) -> None:
        """Files at root and in subdirs are both counted."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "top.json").write_text("x")
        sub = root / "sub"
        sub.mkdir()
        (sub / "nested.json").write_text("x")
        result = inventory_directory(root)
        assert result.total_files == 2
        assert len(result.files_at_root) == 1
        assert len(result.subdirs) == 1
