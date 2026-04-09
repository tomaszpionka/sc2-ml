"""Filesystem inventory utilities for raw data discovery.

Walks a directory tree, counts files, measures sizes, and groups results
by immediate subdirectory. Used by Phase 01 pre-ingestion notebooks to
produce authoritative file inventories from scratch.

No game-domain imports. This module is game-agnostic.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileEntry:
    """A single file observed during inventory.

    Attributes:
        path: Absolute path to the file.
        size_bytes: File size in bytes from os.stat().
        extension: File suffix including the dot (e.g. ".json"), or
            empty string if no extension.
    """

    path: Path
    size_bytes: int
    extension: str


@dataclass(frozen=True)
class SubdirSummary:
    """Aggregated statistics for one immediate subdirectory.

    Attributes:
        name: Subdirectory name (not full path, just the dir name).
        file_count: Number of files matching the glob in this subdirectory.
        total_bytes: Sum of file sizes in bytes.
        extensions: Mapping of extension string to count of files with
            that extension. Extensions include the dot (e.g. {".json": 42}).
        files: List of FileEntry objects for every matched file.
    """

    name: str
    file_count: int
    total_bytes: int
    extensions: dict[str, int]
    files: list[FileEntry] = field(default_factory=list)


@dataclass(frozen=True)
class InventoryResult:
    """Complete inventory of a directory tree.

    Attributes:
        root: The root directory that was inventoried.
        total_files: Total number of files matching the glob across all
            subdirectories and the root itself.
        total_bytes: Sum of all matched file sizes in bytes.
        subdirs: List of SubdirSummary, one per immediate subdirectory
            that contained at least one matching file. Sorted alphabetically
            by name.
        files_at_root: List of FileEntry for files matching the glob that
            sit directly in root (not in any subdirectory).
    """

    root: Path
    total_files: int
    total_bytes: int
    subdirs: list[SubdirSummary]
    files_at_root: list[FileEntry]


def inventory_directory(
    root: Path,
    file_glob: str = "*",
    *,
    include_file_lists: bool = True,
) -> InventoryResult:
    """Walk a directory tree and produce a file inventory.

    Iterates over immediate subdirectories of ``root``. For each, collects
    all files matching ``file_glob`` (non-recursive within the subdir --
    only direct children). Also collects files matching the glob that sit
    directly in ``root`` itself.

    Does NOT recurse deeper than one level below root. This matches the
    typical raw data layout where root/ has subdirectories like
    tournament_name/ or matches/ and files sit directly in those.

    Args:
        root: Directory to inventory. Must exist.
        file_glob: Glob pattern for file matching within each subdirectory.
            Default "*" matches all files. Use "*.json" or
            "*.SC2Replay.json" to filter.
        include_file_lists: If True, populate the ``files`` field on each
            SubdirSummary and the ``files_at_root`` field on the result.
            If False, these lists are empty (saves memory for large dirs).

    Returns:
        InventoryResult with per-subdirectory summaries and root-level files.

    Raises:
        FileNotFoundError: If root does not exist.
        NotADirectoryError: If root exists but is not a directory.
    """
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    # Collect files at root level
    root_matched = [p for p in sorted(root.glob(file_glob)) if p.is_file()]
    files_at_root = [
        FileEntry(path=f, size_bytes=f.stat().st_size, extension=f.suffix)
        for f in root_matched
    ]

    subdirs: list[SubdirSummary] = []
    for subdir in sorted(root.iterdir()):
        if not subdir.is_dir():
            continue

        matched_files = [p for p in sorted(subdir.glob(file_glob)) if p.is_file()]
        if not matched_files:
            continue

        ext_counter = Counter(f.suffix for f in matched_files)
        file_entries = [
            FileEntry(path=f, size_bytes=f.stat().st_size, extension=f.suffix)
            for f in matched_files
        ]
        total_bytes = sum(e.size_bytes for e in file_entries)

        subdirs.append(
            SubdirSummary(
                name=subdir.name,
                file_count=len(file_entries),
                total_bytes=total_bytes,
                extensions=dict(ext_counter),
                files=file_entries if include_file_lists else [],
            )
        )

    root_bytes = sum(e.size_bytes for e in files_at_root)
    subdir_bytes = sum(s.total_bytes for s in subdirs)
    subdir_files = sum(s.file_count for s in subdirs)

    total_files = len(files_at_root) + subdir_files
    total_bytes = root_bytes + subdir_bytes

    return InventoryResult(
        root=root,
        total_files=total_files,
        total_bytes=total_bytes,
        subdirs=subdirs,
        files_at_root=files_at_root if include_file_lists else [],
    )
