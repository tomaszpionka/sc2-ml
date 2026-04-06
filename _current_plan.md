# Current Plan: AoE2 Acquisition Modules

**Category:** A (Phase work)
**Phase/Step:** AoE2 Phase 0, Step 0.0 — Data acquisition infrastructure
**Branch:** `feat/aoe2-phase0-acquisition`
**Estimated steps:** 9
**Complexity:** Medium (two parallel modules with shared patterns, CLI wiring, comprehensive tests)

---

## Context

The AoE2 pipeline has `current_phase: null` -- no work has been done yet. These
acquisition modules are the first AoE2 code to implement. They download raw data
from two sources (aoe2companion CDN, aoestats.io) using on-disk manifest files
that already exist at:

- `src/rts_predict/aoe2/data/aoe2companion/api/api_dump_list.json` (6,224 entries)
- `src/rts_predict/aoe2/data/aoestats/api/db_dump_list.json` (188 entries)

All target directory constants already exist in `src/rts_predict/aoe2/config.py`.
No new dependencies are added (`urllib.request` from stdlib is used instead of
`requests`, which is not in pyproject.toml).

**Design constraint:** The `aoe2companion/` and `aoestats/` directories under
`data/` are currently pure data directories (no `__init__.py`). They must be
converted to Python packages to host the acquisition modules. This means adding
`__init__.py` to each, plus a `tests/` subdirectory inside each. However, this
creates a mixed code/data directory. An alternative: place acquisition modules
directly in `data/` as `data/aoe2companion_acquisition.py` and
`data/aoestats_acquisition.py`. The task specifies the paths
`data/aoe2companion/acquisition.py` and `data/aoestats/acquisition.py`, so we
follow that layout and make the directories into Python packages.

---

## Pre-flight checks

Before starting, verify:
- [ ] `git status` is clean (no uncommitted changes on master)
- [ ] `git checkout -b feat/aoe2-phase0-acquisition`
- [ ] All tests pass: `poetry run pytest tests/ src/ -v`

---

## Step 1 — Make data source directories importable Python packages

Create `__init__.py` files so the acquisition modules are importable.

**Files to create:**

```
src/rts_predict/aoe2/data/aoe2companion/__init__.py
src/rts_predict/aoe2/data/aoestats/__init__.py
```

**Contents for `aoe2companion/__init__.py`:**

```python
"""aoe2companion data source — acquisition and ingestion modules."""
```

**Contents for `aoestats/__init__.py`:**

```python
"""aoestats data source — acquisition and ingestion modules."""
```

**Verification:** `python -c "import rts_predict.aoe2.data.aoe2companion"` succeeds.

---

## Step 2 — Implement `aoe2companion/acquisition.py`

**File:** `src/rts_predict/aoe2/data/aoe2companion/acquisition.py`

### Module-level constants

```python
"""Download raw data files from the aoe2companion CDN.

Reads the on-disk manifest (api_dump_list.json), filters to download targets
(match parquets, leaderboard parquet, profile parquet, rating CSVs), and
streams each file to its target raw/ subdirectory. Idempotent: skips files
whose on-disk size matches the manifest size field.
"""

import json
import logging
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from rts_predict.aoe2.config import (
    AOE2COMPANION_DIR,
    AOE2COMPANION_MANIFEST,
    AOE2COMPANION_RAW_LEADERBOARDS_DIR,
    AOE2COMPANION_RAW_MATCHES_DIR,
    AOE2COMPANION_RAW_PROFILES_DIR,
    AOE2COMPANION_RAW_RATINGS_DIR,
)

logger = logging.getLogger(__name__)

# Download targets identified by key pattern
_MATCH_PARQUET_PATTERN: re.Pattern[str] = re.compile(r"^match-\d{4}-\d{2}-\d{2}\.parquet$")
_LEADERBOARD_PARQUET_KEY: str = "leaderboard.parquet"
_PROFILE_PARQUET_KEY: str = "profile.parquet"
_RATING_CSV_PATTERN: re.Pattern[str] = re.compile(r"^rating-\d{4}-\d{2}-\d{2}\.csv$")

# Progress logging interval (every N files)
LOG_INTERVAL: int = 100

# Stream download buffer size (bytes)
_DOWNLOAD_CHUNK_SIZE: int = 8192

# Download log filename
_DOWNLOAD_LOG_FILENAME: str = "_download_manifest.json"
```

### Function signatures and docstrings

```python
def load_manifest(manifest_path: Path) -> list[dict]:
    """Load and return all entries from the aoe2companion API dump manifest.

    Args:
        manifest_path: Path to api_dump_list.json.

    Returns:
        List of manifest entry dicts, each with keys:
        key, lastModified, eTag, size, storageClass, url.

    Raises:
        FileNotFoundError: If manifest_path does not exist.
        json.JSONDecodeError: If manifest is not valid JSON.
    """
```

Implementation notes: `json.load()` on the file. The file is a JSON array of
objects. Return as-is.

```python
def _classify_entry(key: str) -> str | None:
    """Classify a manifest entry key into a download category.

    Args:
        key: The 'key' field from a manifest entry (e.g., 'match-2020-08-01.parquet').

    Returns:
        One of 'match', 'leaderboard', 'profile', 'rating', or None if the
        entry should be skipped.
    """
```

Implementation notes:
- Match against `_MATCH_PARQUET_PATTERN` -> "match"
- Exact match `_LEADERBOARD_PARQUET_KEY` -> "leaderboard"
- Exact match `_PROFILE_PARQUET_KEY` -> "profile"
- Match against `_RATING_CSV_PATTERN` -> "rating"
- Everything else -> `None` (skip)

This function must reject: `match-*.csv`, `leaderboard.csv`, `profile.csv`,
`test-*.parquet`, `test2-*.parquet`, and any other non-target entries.

```python
def filter_download_targets(entries: list[dict]) -> list[dict]:
    """Filter manifest entries to only those that should be downloaded.

    Applies skip rules: only match parquets, leaderboard parquet, profile
    parquet, and rating CSVs are download targets. All other entries
    (CSV duplicates, test files) are excluded.

    Args:
        entries: Raw manifest entries from load_manifest().

    Returns:
        Filtered list of entries, each augmented with a '_category' key
        ('match', 'leaderboard', 'profile', or 'rating').
    """
```

Implementation notes: iterate entries, call `_classify_entry(entry["key"])`,
keep only non-None results. Add `_category` key to each kept entry (shallow
copy the dict before mutating). Log the count per category and total skipped.

```python
def resolve_target_path(entry: dict) -> Path:
    """Map a manifest entry to its target file path on disk.

    Args:
        entry: A filtered manifest entry (must have '_category' key from
            filter_download_targets).

    Returns:
        Absolute path where the file should be saved.

    Raises:
        ValueError: If entry has an unrecognised _category.
    """
```

Implementation notes: dispatch on `entry["_category"]`:
- "match" -> `AOE2COMPANION_RAW_MATCHES_DIR / entry["key"]`
- "leaderboard" -> `AOE2COMPANION_RAW_LEADERBOARDS_DIR / entry["key"]`
- "profile" -> `AOE2COMPANION_RAW_PROFILES_DIR / entry["key"]`
- "rating" -> `AOE2COMPANION_RAW_RATINGS_DIR / entry["key"]`

```python
def is_already_downloaded(target_path: Path, expected_size: int) -> bool:
    """Check whether a file is already downloaded with the correct size.

    Idempotency check: the file exists AND its on-disk size matches the
    manifest's size field. The eTag is a multipart upload hash and is
    NOT suitable as an MD5 check.

    Args:
        target_path: Path where the file should exist.
        expected_size: Expected file size in bytes from the manifest.

    Returns:
        True if the file exists and its size matches expected_size.
    """
```

Implementation notes: `target_path.exists() and target_path.stat().st_size == expected_size`.

```python
def download_file(
    url: str,
    target_path: Path,
    expected_size: int | None = None,
) -> None:
    """Stream-download a single file from the CDN.

    Creates parent directories if they do not exist. After download,
    verifies the on-disk size matches expected_size (if provided).

    Args:
        url: Full CDN URL to download.
        target_path: Local path to write the file to.
        expected_size: Expected file size in bytes. If provided and the
            downloaded file size does not match, the file is deleted and
            a ValueError is raised.

    Raises:
        urllib.error.URLError: On network errors.
        ValueError: If downloaded size does not match expected_size.
    """
```

Implementation notes:
- `target_path.parent.mkdir(parents=True, exist_ok=True)`
- Use `urllib.request.urlopen(url)` as context manager
- Stream to a temporary file in the same directory (write to
  `target_path.with_suffix(target_path.suffix + ".tmp")`) then rename on
  success. This prevents partial files on interruption.
- Read in `_DOWNLOAD_CHUNK_SIZE` chunks, write to disk.
- After closing, check size: `target_path.stat().st_size != expected_size` ->
  delete and raise `ValueError`.
- Use `shutil.move(tmp_path, target_path)` for the atomic rename (works
  cross-filesystem on macOS).

```python
def _build_download_log_entry(
    entry: dict,
    target_path: Path,
    status: str,
    error: str | None = None,
) -> dict:
    """Build a single entry for the download manifest log.

    Args:
        entry: Original manifest entry dict.
        target_path: Where the file was (or would be) saved.
        status: One of 'downloaded', 'skipped', 'failed', 'dry_run'.
        error: Error message if status is 'failed'.

    Returns:
        Dict with keys: key, url, target_path, size, status, timestamp, error.
    """
```

Implementation notes: return a dict with:
- `key`: `entry["key"]`
- `url`: `entry["url"]`
- `target_path`: `str(target_path)`
- `size`: `entry["size"]`
- `status`: the status argument
- `timestamp`: `datetime.now(timezone.utc).isoformat()`
- `error`: the error argument (None if no error)

```python
def _write_download_log(log_entries: list[dict]) -> Path:
    """Write the download manifest log to disk.

    Args:
        log_entries: List of log entry dicts from _build_download_log_entry.

    Returns:
        Path to the written log file.
    """
```

Implementation notes: write to `AOE2COMPANION_DIR / _DOWNLOAD_LOG_FILENAME`
as indented JSON. Return the path.

```python
def run_download(
    dry_run: bool = False,
    log_interval: int = LOG_INTERVAL,
) -> dict:
    """Orchestrate the full aoe2companion download.

    Loads the manifest, filters to download targets, checks idempotency
    for each file, and downloads missing/changed files. Writes a download
    log on completion.

    Args:
        dry_run: If True, list what would be downloaded without making
            any HTTP requests. Files are still classified and logged.
        log_interval: Log progress every N files processed.

    Returns:
        Summary dict with keys: total_targets, downloaded, skipped,
        failed, dry_run (bool), log_path (str).
    """
```

Implementation notes (orchestration flow):
1. `entries = load_manifest(AOE2COMPANION_MANIFEST)`
2. `targets = filter_download_targets(entries)`
3. Log: `f"aoe2companion: {len(targets)} download targets identified"`
4. Initialise counters: `downloaded = 0, skipped = 0, failed = 0`
5. Initialise `log_entries: list[dict] = []`
6. For each `entry` in `targets`:
   a. `target_path = resolve_target_path(entry)`
   b. If `is_already_downloaded(target_path, entry["size"])`:
      - increment `skipped`, append log entry with status "skipped", continue
   c. If `dry_run`:
      - log at DEBUG: `f"[DRY RUN] Would download: {entry['key']}"`
      - append log entry with status "dry_run", continue
   d. Try `download_file(entry["url"], target_path, entry["size"])`:
      - increment `downloaded`, append log entry with status "downloaded"
   e. Except `(urllib.error.URLError, ValueError, OSError) as exc`:
      - increment `failed`, log warning with error
      - append log entry with status "failed" and error string
   f. If `(downloaded + skipped + failed) % log_interval == 0`:
      - log progress: `f"Progress: {downloaded + skipped + failed}/{len(targets)}"`
7. `log_path = _write_download_log(log_entries)`
8. Log summary: total, downloaded, skipped, failed
9. Return summary dict

---

## Step 3 — Implement `aoestats/acquisition.py`

**File:** `src/rts_predict/aoe2/data/aoestats/acquisition.py`

### Module-level constants

```python
"""Download raw data files from aoestats.io.

Reads the on-disk manifest (db_dump_list.json), filters out zero-match
weeks, and downloads matches.parquet and players.parquet for each week.
Idempotent: skips files whose on-disk MD5 matches the manifest checksum.

Status: DEFERRED. The CLI subcommand requires --force to execute.
Code is fully implemented and tested, but automatic execution is gated
until aoe2companion Phase 0 profiling is complete.
"""

import hashlib
import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from rts_predict.aoe2.config import (
    AOESTATS_DIR,
    AOESTATS_MANIFEST,
    AOESTATS_RAW_MATCHES_DIR,
    AOESTATS_RAW_PLAYERS_DIR,
)

logger = logging.getLogger(__name__)

# Base URL for aoestats file downloads (manifest provides relative paths)
_AOESTATS_BASE_URL: str = "https://aoestats.io"

# Progress logging interval (every N entries processed)
LOG_INTERVAL: int = 20

# Stream download buffer size (bytes)
_DOWNLOAD_CHUNK_SIZE: int = 8192

# MD5 read buffer size (bytes)
_MD5_CHUNK_SIZE: int = 8192

# Download log filename
_DOWNLOAD_LOG_FILENAME: str = "_download_manifest.json"

# Deferred-status warning message
_DEFERRED_WARNING: str = (
    "aoestats acquisition is deferred -- use --force to proceed. "
    "Reason: aoe2companion Phase 0 profiling must complete first."
)
```

### Function signatures and docstrings

```python
def load_manifest(manifest_path: Path) -> list[dict]:
    """Load and return the db_dumps array from the aoestats manifest.

    Args:
        manifest_path: Path to db_dump_list.json.

    Returns:
        List of weekly dump entry dicts, each with keys: start_date,
        end_date, num_matches, num_players, matches_url, players_url,
        match_checksum, player_checksum.

    Raises:
        FileNotFoundError: If manifest_path does not exist.
        json.JSONDecodeError: If manifest is not valid JSON.
        KeyError: If manifest does not contain 'db_dumps' key.
    """
```

Implementation notes: `json.load()` on the file, return `data["db_dumps"]`.

```python
def filter_download_targets(entries: list[dict]) -> list[dict]:
    """Filter manifest entries, removing weeks with zero matches.

    Args:
        entries: Raw manifest entries from load_manifest().

    Returns:
        Filtered list containing only entries where num_matches > 0.
    """
```

Implementation notes: `[e for e in entries if e["num_matches"] > 0]`. Log the
count of filtered-out entries.

```python
def resolve_target_paths(entry: dict) -> tuple[Path, Path]:
    """Map a manifest entry to its target file paths on disk.

    Files are named {start_date}_{end_date}_matches.parquet and
    {start_date}_{end_date}_players.parquet to prevent overwrites
    across weeks.

    Args:
        entry: A manifest entry dict with start_date and end_date keys.

    Returns:
        Tuple of (matches_path, players_path).
    """
```

Implementation notes:
- `matches_name = f"{entry['start_date']}_{entry['end_date']}_matches.parquet"`
- `players_name = f"{entry['start_date']}_{entry['end_date']}_players.parquet"`
- Return `(AOESTATS_RAW_MATCHES_DIR / matches_name, AOESTATS_RAW_PLAYERS_DIR / players_name)`

```python
def _compute_md5(file_path: Path) -> str:
    """Compute the MD5 hex digest of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Lowercase hex MD5 digest string.
    """
```

Implementation notes: read file in `_MD5_CHUNK_SIZE` chunks, update
`hashlib.md5()`, return `.hexdigest()`.

```python
def is_already_downloaded(file_path: Path, expected_checksum: str) -> bool:
    """Check whether a file is already downloaded with the correct MD5.

    Args:
        file_path: Path where the file should exist.
        expected_checksum: Expected MD5 hex digest from the manifest.

    Returns:
        True if the file exists and its MD5 matches expected_checksum.
    """
```

Implementation notes: `file_path.exists() and _compute_md5(file_path) == expected_checksum`.

```python
def download_file(
    url: str,
    target_path: Path,
    expected_checksum: str,
) -> None:
    """Stream-download a single file from aoestats.io and verify MD5.

    Creates parent directories if they do not exist. Downloads to a
    temporary file first, verifies the MD5, then renames to the final
    path. Deletes the temporary file on checksum mismatch.

    Args:
        url: Full URL to download (base URL + relative path).
        target_path: Local path to write the file to.
        expected_checksum: Expected MD5 hex digest.

    Raises:
        urllib.error.URLError: On network errors.
        ValueError: If downloaded file's MD5 does not match expected_checksum.
    """
```

Implementation notes:
- Same temp-file + rename pattern as aoe2companion.
- After download, compute MD5 of temp file.
- If mismatch: delete temp file, raise `ValueError` with details.
- If match: rename temp to final path.

```python
def _build_download_log_entry(
    entry: dict,
    file_type: str,
    target_path: Path,
    status: str,
    error: str | None = None,
) -> dict:
    """Build a single entry for the download manifest log.

    Args:
        entry: Original manifest entry dict.
        file_type: Either 'matches' or 'players'.
        target_path: Where the file was (or would be) saved.
        status: One of 'downloaded', 'skipped', 'failed', 'dry_run'.
        error: Error message if status is 'failed'.

    Returns:
        Dict with keys: start_date, end_date, file_type, url, target_path,
        checksum, status, timestamp, error.
    """
```

Implementation notes: return dict with the listed keys. URL is computed as
`_AOESTATS_BASE_URL + entry["matches_url"]` or `players_url` based on
`file_type`. Checksum is `entry["match_checksum"]` or `entry["player_checksum"]`.

```python
def _write_download_log(log_entries: list[dict]) -> Path:
    """Write the download manifest log to disk.

    Args:
        log_entries: List of log entry dicts.

    Returns:
        Path to the written log file.
    """
```

Implementation notes: write to `AOESTATS_DIR / _DOWNLOAD_LOG_FILENAME`.

```python
def run_download(
    dry_run: bool = False,
    force: bool = False,
    log_interval: int = LOG_INTERVAL,
) -> dict:
    """Orchestrate the full aoestats download.

    Loads the manifest, filters out zero-match weeks, checks idempotency
    for each file pair (matches + players), and downloads missing files.
    Writes a download log on completion.

    This source is DEFERRED: unless force=True, the function logs a
    warning and returns immediately without downloading anything.

    Args:
        dry_run: If True, list what would be downloaded without HTTP requests.
        force: If True, proceed despite deferred status. Required for
            actual downloads.
        log_interval: Log progress every N entries (each entry = 2 files).

    Returns:
        Summary dict with keys: total_targets, total_files, downloaded,
        skipped, failed, dry_run (bool), forced (bool), deferred (bool),
        log_path (str | None).
    """
```

Implementation notes (orchestration flow):
1. If not `force` and not `dry_run`:
   - `logger.warning(_DEFERRED_WARNING)`
   - Return summary with `deferred=True`, all counters zero, `log_path=None`
2. `entries = load_manifest(AOESTATS_MANIFEST)`
3. `targets = filter_download_targets(entries)`
4. Log: `f"aoestats: {len(targets)} weekly dumps, {len(targets) * 2} files"`
5. Initialise counters and log_entries list
6. For each `entry` in `targets`:
   a. `matches_path, players_path = resolve_target_paths(entry)`
   b. For each `(file_path, url_key, checksum_key, file_type)` in:
      - `(matches_path, "matches_url", "match_checksum", "matches")`
      - `(players_path, "players_url", "player_checksum", "players")`
   c. `full_url = _AOESTATS_BASE_URL + entry[url_key]`
   d. `checksum = entry[checksum_key]`
   e. If `is_already_downloaded(file_path, checksum)`:
      - increment skipped, log entry "skipped", continue
   f. If `dry_run`:
      - log entry "dry_run", continue
   g. Try `download_file(full_url, file_path, checksum)`:
      - increment downloaded, log entry "downloaded"
   h. Except `(urllib.error.URLError, ValueError, OSError) as exc`:
      - increment failed, log warning, log entry "failed"
   i. Log progress at `log_interval` boundaries (check entry index, not file index)
7. Write download log, log summary, return summary dict

---

## Step 4 — Wire CLI subcommand `download`

**File to modify:** `src/rts_predict/aoe2/cli.py`

### Changes to `build_parser()`

Add a `download` subcommand after the existing `db` subcommand setup:

```python
download_parser = subparsers.add_parser(
    "download",
    help="Download raw data from AoE2 sources",
)
download_parser.add_argument(
    "source",
    choices=["aoe2companion", "aoestats"],
    help="Data source to download from",
)
download_parser.add_argument(
    "--dry-run",
    action="store_true",
    default=False,
    help="List files to download without making HTTP requests",
)
download_parser.add_argument(
    "--force",
    action="store_true",
    default=False,
    help="Force download even for deferred sources (required for aoestats)",
)
download_parser.add_argument(
    "--log-interval",
    type=int,
    default=None,
    help="Log progress every N files (default: source-specific)",
)
```

### New function `_handle_download(args: argparse.Namespace) -> None`

```python
def _handle_download(args: argparse.Namespace) -> None:
    """Dispatch the download command to the appropriate source module.

    Args:
        args: Parsed CLI arguments with source, dry_run, force, log_interval.
    """
```

Implementation notes:
- If `args.source == "aoe2companion"`:
  - `from rts_predict.aoe2.data.aoe2companion.acquisition import run_download`
  - Build kwargs: `dry_run=args.dry_run`
  - If `args.log_interval` is not None: add `log_interval=args.log_interval`
  - Call `result = run_download(**kwargs)`
- If `args.source == "aoestats"`:
  - `from rts_predict.aoe2.data.aoestats.acquisition import run_download`
  - Build kwargs: `dry_run=args.dry_run, force=args.force`
  - If `args.log_interval` is not None: add `log_interval=args.log_interval`
  - Call `result = run_download(**kwargs)`
- Log the returned summary dict at INFO level

### Update `main()` dispatch

Add to the command dispatch in `main()`:

```python
elif args.command == "download":
    _handle_download(args)
```

---

## Step 5 — Test fixtures

**File:** `src/rts_predict/aoe2/data/tests/conftest.py` (create)

Define shared pytest fixtures used by both test modules.

```python
"""Shared fixtures for AoE2 data acquisition tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def aoe2companion_manifest_entries() -> list[dict]:
    """Minimal aoe2companion manifest entries covering all categories + skips."""
    return [
        {
            "key": "match-2024-01-01.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"abc123\"-16",
            "size": 500000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/match-2024-01-01.parquet",
        },
        {
            "key": "leaderboard.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"def456\"-8",
            "size": 87000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/leaderboard.parquet",
        },
        {
            "key": "profile.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"ghi789\"-4",
            "size": 170000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/profile.parquet",
        },
        {
            "key": "rating-2024-01-01.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"jkl012\"",
            "size": 1000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/rating-2024-01-01.csv",
        },
        # --- entries that should be SKIPPED ---
        {
            "key": "match-2024-01-01.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"skip1\"",
            "size": 3000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/match-2024-01-01.csv",
        },
        {
            "key": "leaderboard.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"skip2\"",
            "size": 700000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/leaderboard.csv",
        },
        {
            "key": "profile.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"skip3\"",
            "size": 600000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/profile.csv",
        },
        {
            "key": "test-match-2022-09-09.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"skip4\"",
            "size": 5000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/test-match-2022-09-09.parquet",
        },
        {
            "key": "test2-match-2022-10-07.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": "\"skip5\"",
            "size": 5000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/test2-match-2022-10-07.parquet",
        },
    ]


@pytest.fixture()
def aoestats_manifest_entries() -> list[dict]:
    """Minimal aoestats manifest entries including a zero-match week."""
    return [
        {
            "start_date": "2023-01-01",
            "end_date": "2023-01-07",
            "num_matches": 150000,
            "num_players": 300000,
            "matches_url": "/media/db_dumps/date_range%3D2023-01-01_2023-01-07/matches.parquet",
            "players_url": "/media/db_dumps/date_range%3D2023-01-01_2023-01-07/players.parquet",
            "match_checksum": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
            "player_checksum": "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3",
        },
        {
            "start_date": "2023-01-08",
            "end_date": "2023-01-14",
            "num_matches": 120000,
            "num_players": 250000,
            "matches_url": "/media/db_dumps/date_range%3D2023-01-08_2023-01-14/matches.parquet",
            "players_url": "/media/db_dumps/date_range%3D2023-01-08_2023-01-14/players.parquet",
            "match_checksum": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d400",
            "player_checksum": "e5d4c3b2a1f6e5d4c3b2a1f6e5d4c300",
        },
        # --- zero-match week: should be SKIPPED ---
        {
            "start_date": "2023-01-15",
            "end_date": "2023-01-21",
            "num_matches": 0,
            "num_players": 0,
            "matches_url": "/media/db_dumps/date_range%3D2023-01-15_2023-01-21/matches.parquet",
            "players_url": "/media/db_dumps/date_range%3D2023-01-15_2023-01-21/players.parquet",
            "match_checksum": "0000000000000000000000000000000000",
            "player_checksum": "0000000000000000000000000000000000",
        },
    ]


@pytest.fixture()
def aoe2companion_manifest_file(
    tmp_path: Path, aoe2companion_manifest_entries: list[dict]
) -> Path:
    """Write fixture entries to a temporary manifest JSON file."""
    manifest_path = tmp_path / "api_dump_list.json"
    manifest_path.write_text(json.dumps(aoe2companion_manifest_entries))
    return manifest_path


@pytest.fixture()
def aoestats_manifest_file(
    tmp_path: Path, aoestats_manifest_entries: list[dict]
) -> Path:
    """Write fixture entries to a temporary aoestats manifest JSON file."""
    manifest_path = tmp_path / "db_dump_list.json"
    manifest_path.write_text(json.dumps({"db_dumps": aoestats_manifest_entries}))
    return manifest_path
```

---

## Step 6 — Tests for `aoe2companion/acquisition.py`

**File:** `src/rts_predict/aoe2/data/tests/test_aoe2companion_acquisition.py`

All tests use fixtures from conftest.py and mocks for HTTP. No real network calls.

### Test class: `TestLoadManifest`

```python
class TestLoadManifest:
    """Tests for load_manifest()."""

    def test_loads_valid_manifest(
        self, aoe2companion_manifest_file: Path
    ) -> None:
        """Valid JSON array is loaded and returned as list of dicts."""
        # Assert: returns list, length matches fixture, each entry has 'key'

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """FileNotFoundError when manifest path does not exist."""

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """JSONDecodeError when file contains invalid JSON."""
        # Write "not json" to a file, call load_manifest, assert raises
```

### Test class: `TestClassifyEntry`

```python
class TestClassifyEntry:
    """Tests for _classify_entry()."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("match-2024-01-01.parquet", "match"),
            ("match-2020-08-01.parquet", "match"),
            ("leaderboard.parquet", "leaderboard"),
            ("profile.parquet", "profile"),
            ("rating-2024-01-01.csv", "rating"),
            ("rating-2025-06-27.csv", "rating"),
            # Skip cases
            ("match-2024-01-01.csv", None),
            ("leaderboard.csv", None),
            ("profile.csv", None),
            ("test-match-2022-09-09.parquet", None),
            ("test2-match-2022-10-07.parquet", None),
            ("random-file.txt", None),
        ],
    )
    def test_classifies_correctly(self, key: str, expected: str | None) -> None:
        """Each key pattern maps to the correct category or None."""
```

### Test class: `TestFilterDownloadTargets`

```python
class TestFilterDownloadTargets:
    """Tests for filter_download_targets()."""

    def test_keeps_only_download_targets(
        self, aoe2companion_manifest_entries: list[dict]
    ) -> None:
        """9 fixture entries -> 4 targets (1 match, 1 leaderboard, 1 profile, 1 rating)."""
        # Assert: len == 4, all have '_category' key

    def test_empty_input_returns_empty(self) -> None:
        """Empty list in -> empty list out."""

    def test_categories_are_correct(
        self, aoe2companion_manifest_entries: list[dict]
    ) -> None:
        """Each returned entry has the expected _category value."""
        # Assert set of categories == {"match", "leaderboard", "profile", "rating"}
```

### Test class: `TestResolveTargetPath`

```python
class TestResolveTargetPath:
    """Tests for resolve_target_path()."""

    def test_match_goes_to_matches_dir(self) -> None:
        """Match parquet entry resolves to AOE2COMPANION_RAW_MATCHES_DIR."""
        entry = {"key": "match-2024-01-01.parquet", "_category": "match"}
        # Assert path == AOE2COMPANION_RAW_MATCHES_DIR / "match-2024-01-01.parquet"

    def test_leaderboard_goes_to_leaderboards_dir(self) -> None:
        """Leaderboard parquet resolves to AOE2COMPANION_RAW_LEADERBOARDS_DIR."""

    def test_profile_goes_to_profiles_dir(self) -> None:
        """Profile parquet resolves to AOE2COMPANION_RAW_PROFILES_DIR."""

    def test_rating_goes_to_ratings_dir(self) -> None:
        """Rating CSV resolves to AOE2COMPANION_RAW_RATINGS_DIR."""

    def test_unknown_category_raises(self) -> None:
        """ValueError on unrecognised _category."""
        entry = {"key": "unknown.bin", "_category": "unknown"}
        # pytest.raises(ValueError)
```

### Test class: `TestIsAlreadyDownloaded`

```python
class TestIsAlreadyDownloaded:
    """Tests for is_already_downloaded()."""

    def test_returns_true_when_size_matches(self, tmp_path: Path) -> None:
        """File exists with correct size -> True."""
        target = tmp_path / "test.parquet"
        target.write_bytes(b"x" * 100)
        # Assert is_already_downloaded(target, 100) is True

    def test_returns_false_when_size_differs(self, tmp_path: Path) -> None:
        """File exists but size differs -> False."""
        target = tmp_path / "test.parquet"
        target.write_bytes(b"x" * 100)
        # Assert is_already_downloaded(target, 200) is False

    def test_returns_false_when_file_missing(self, tmp_path: Path) -> None:
        """File does not exist -> False."""
        # Assert is_already_downloaded(tmp_path / "missing.parquet", 100) is False
```

### Test class: `TestDownloadFile`

```python
class TestDownloadFile:
    """Tests for download_file() with mocked HTTP."""

    def test_downloads_and_saves_file(self, tmp_path: Path) -> None:
        """Successful download creates file with correct content."""
        # Mock urllib.request.urlopen to return BytesIO with known content
        # Assert file exists at target_path with correct size

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Parent directories are created if they do not exist."""
        # Target: tmp_path / "a" / "b" / "file.parquet"
        # Mock download, assert file exists

    def test_raises_on_size_mismatch(self, tmp_path: Path) -> None:
        """ValueError raised when downloaded size != expected_size."""
        # Mock urlopen to return 100 bytes, expected_size=200
        # Assert raises ValueError, assert file does NOT exist (cleaned up)

    def test_cleans_up_temp_file_on_failure(self, tmp_path: Path) -> None:
        """Temporary file is removed if download fails mid-stream."""
        # Mock urlopen to raise partway through
        # Assert no .tmp file remains
```

### Test class: `TestRunDownload`

```python
class TestRunDownload:
    """Tests for run_download() orchestrator with mocked internals."""

    def test_dry_run_downloads_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """dry_run=True: no HTTP calls, all targets logged as 'dry_run'."""
        # Monkeypatch AOE2COMPANION_MANIFEST to fixture file
        # Monkeypatch AOE2COMPANION_DIR to tmp_path (for log output)
        # Monkeypatch the raw dir constants to tmp_path subdirs
        # Assert: result["downloaded"] == 0, result["dry_run"] is True
        # Assert: download log file exists

    def test_skips_already_downloaded_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Files already on disk with matching size are skipped."""
        # Pre-create files with correct sizes in tmp_path
        # Assert: result["skipped"] == number of pre-created files

    def test_download_log_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Download manifest JSON is written after run_download completes."""
        # Run with dry_run=True
        # Assert _download_manifest.json exists and is valid JSON
        # Assert each log entry has required keys

    def test_handles_download_failure_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Network failure for one file does not abort the entire run."""
        # Mock download_file to raise URLError for one specific URL
        # Assert: result["failed"] == 1, other files still processed
```

---

## Step 7 — Tests for `aoestats/acquisition.py`

**File:** `src/rts_predict/aoe2/data/tests/test_aoestats_acquisition.py`

### Test class: `TestLoadManifest`

```python
class TestLoadManifest:
    """Tests for load_manifest()."""

    def test_loads_valid_manifest(self, aoestats_manifest_file: Path) -> None:
        """Valid JSON with db_dumps array is loaded correctly."""
        # Assert: returns list, length == 3 (fixture has 3 entries)

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """FileNotFoundError when manifest does not exist."""

    def test_raises_on_missing_db_dumps_key(self, tmp_path: Path) -> None:
        """KeyError when JSON lacks 'db_dumps' key."""
        # Write {"other": []} to file, assert raises KeyError
```

### Test class: `TestFilterDownloadTargets`

```python
class TestFilterDownloadTargets:
    """Tests for filter_download_targets()."""

    def test_removes_zero_match_entries(
        self, aoestats_manifest_entries: list[dict]
    ) -> None:
        """3 fixture entries (2 non-zero, 1 zero) -> 2 targets."""

    def test_empty_input_returns_empty(self) -> None:
        """Empty list in -> empty list out."""

    def test_all_zero_returns_empty(self) -> None:
        """All entries have num_matches == 0 -> empty list."""
```

### Test class: `TestResolveTargetPaths`

```python
class TestResolveTargetPaths:
    """Tests for resolve_target_paths()."""

    def test_correct_filenames(self) -> None:
        """File names follow {start_date}_{end_date}_{type}.parquet pattern."""
        entry = {"start_date": "2023-01-01", "end_date": "2023-01-07"}
        matches_path, players_path = resolve_target_paths(entry)
        assert matches_path.name == "2023-01-01_2023-01-07_matches.parquet"
        assert players_path.name == "2023-01-01_2023-01-07_players.parquet"

    def test_correct_directories(self) -> None:
        """Matches go to AOESTATS_RAW_MATCHES_DIR, players to AOESTATS_RAW_PLAYERS_DIR."""
        entry = {"start_date": "2023-01-01", "end_date": "2023-01-07"}
        matches_path, players_path = resolve_target_paths(entry)
        assert matches_path.parent == AOESTATS_RAW_MATCHES_DIR
        assert players_path.parent == AOESTATS_RAW_PLAYERS_DIR
```

### Test class: `TestComputeMd5`

```python
class TestComputeMd5:
    """Tests for _compute_md5()."""

    def test_known_hash(self, tmp_path: Path) -> None:
        """MD5 of known content matches expected digest."""
        target = tmp_path / "test.bin"
        target.write_bytes(b"hello world")
        # hashlib.md5(b"hello world").hexdigest() == "5eb63bbbe01eeed093cb22bb8f5acdc3"
        assert _compute_md5(target) == "5eb63bbbe01eeed093cb22bb8f5acdc3"

    def test_empty_file(self, tmp_path: Path) -> None:
        """MD5 of empty file is the known empty-input digest."""
        target = tmp_path / "empty.bin"
        target.write_bytes(b"")
        # hashlib.md5(b"").hexdigest() == "d41d8cd98f00b204e9800998ecf8427e"
        assert _compute_md5(target) == "d41d8cd98f00b204e9800998ecf8427e"
```

### Test class: `TestIsAlreadyDownloaded`

```python
class TestIsAlreadyDownloaded:
    """Tests for is_already_downloaded()."""

    def test_returns_true_when_checksum_matches(self, tmp_path: Path) -> None:
        """File exists with correct MD5 -> True."""
        target = tmp_path / "test.parquet"
        content = b"hello world"
        target.write_bytes(content)
        checksum = hashlib.md5(content).hexdigest()
        assert is_already_downloaded(target, checksum) is True

    def test_returns_false_when_checksum_differs(self, tmp_path: Path) -> None:
        """File exists but MD5 differs -> False."""
        target = tmp_path / "test.parquet"
        target.write_bytes(b"hello world")
        assert is_already_downloaded(target, "0000000000000000") is False

    def test_returns_false_when_file_missing(self, tmp_path: Path) -> None:
        """File does not exist -> False."""
        assert is_already_downloaded(tmp_path / "missing.parquet", "abc") is False
```

### Test class: `TestDownloadFile`

```python
class TestDownloadFile:
    """Tests for download_file() with mocked HTTP."""

    def test_downloads_and_verifies_md5(self, tmp_path: Path) -> None:
        """Successful download creates file that passes MD5 check."""
        # Mock urllib.request.urlopen, provide known content
        # Compute expected MD5 of that content
        # Assert file exists and MD5 matches

    def test_raises_on_checksum_mismatch(self, tmp_path: Path) -> None:
        """ValueError raised when MD5 does not match expected_checksum."""
        # Mock download with known content, pass wrong checksum
        # Assert raises ValueError, assert file does NOT exist

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Parent directories are created automatically."""
```

### Test class: `TestRunDownload`

```python
class TestRunDownload:
    """Tests for run_download() orchestrator."""

    def test_deferred_without_force(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without force=True, returns immediately with deferred=True."""
        # Monkeypatch config paths to tmp_path
        result = run_download(dry_run=False, force=False)
        assert result["deferred"] is True
        assert result["downloaded"] == 0

    def test_dry_run_proceeds_without_force(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """dry_run=True works even without force (shows what would happen)."""
        # Monkeypatch manifest path and dir constants
        # Assert: result["dry_run"] is True, result["deferred"] is False

    def test_force_enables_download(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """force=True allows actual downloads to proceed."""
        # Mock download_file, monkeypatch config
        # Assert: result["forced"] is True, result["downloaded"] > 0

    def test_skips_already_downloaded_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Files with matching MD5 are skipped."""
        # Pre-create files with correct checksums
        # Assert: result["skipped"] == expected count

    def test_download_log_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Download manifest JSON is written after completion."""
        # dry_run with force, check _download_manifest.json exists

    def test_processes_both_matches_and_players(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Each non-zero entry produces two download attempts (matches + players)."""
        # 2 non-zero entries in fixture -> 4 file attempts
        # Assert result["total_files"] == 4
```

---

## Step 8 — Test for CLI wiring

**File:** `src/rts_predict/aoe2/data/tests/test_aoe2companion_acquisition.py`
(append to the same file, or a separate `src/rts_predict/aoe2/tests/test_cli.py`
if one exists)

### Test class: `TestCLIDownload`

```python
class TestCLIDownload:
    """Tests for CLI download subcommand parsing."""

    def test_download_subcommand_exists(self) -> None:
        """'download' is a recognised subcommand."""
        from rts_predict.aoe2.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["download", "aoe2companion", "--dry-run"])
        assert args.command == "download"
        assert args.source == "aoe2companion"
        assert args.dry_run is True

    def test_aoestats_force_flag(self) -> None:
        """--force flag is parsed for aoestats source."""
        from rts_predict.aoe2.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["download", "aoestats", "--force"])
        assert args.source == "aoestats"
        assert args.force is True

    def test_invalid_source_rejected(self) -> None:
        """Unrecognised source name causes parser error."""
        from rts_predict.aoe2.cli import build_parser
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["download", "invalid_source"])
```

Place these CLI tests in `src/rts_predict/aoe2/tests/test_cli.py` (create if
it does not exist, add CLI test class).

---

## Step 9 — Verification and gate

### Run full test suite

```bash
poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing
poetry run ruff check src/ tests/
poetry run mypy src/rts_predict/
```

### Verify CLI works

```bash
poetry run aoe2 download aoe2companion --dry-run
poetry run aoe2 download aoestats  # Should print deferred warning
poetry run aoe2 download aoestats --dry-run  # Should list targets
```

### Gate condition

All of the following must be true:

1. `src/rts_predict/aoe2/data/aoe2companion/__init__.py` exists
2. `src/rts_predict/aoe2/data/aoestats/__init__.py` exists
3. `src/rts_predict/aoe2/data/aoe2companion/acquisition.py` exists with all 8 functions
4. `src/rts_predict/aoe2/data/aoestats/acquisition.py` exists with all 8 functions
5. `src/rts_predict/aoe2/cli.py` has `download` subcommand with `source`, `--dry-run`, `--force`, `--log-interval` args
6. `poetry run aoe2 download aoe2companion --dry-run` runs without error and lists 4,147 targets
7. `poetry run aoe2 download aoestats` prints deferred warning and exits with zero downloads
8. `poetry run aoe2 download aoestats --dry-run` lists 172 non-zero weekly entries (344 files)
9. All tests pass: `poetry run pytest tests/ src/ -v`
10. `poetry run ruff check src/ tests/` reports zero errors
11. `poetry run mypy src/rts_predict/` reports zero errors
12. Both modules write `_download_manifest.json` logs to their respective `AOE2COMPANION_DIR` / `AOESTATS_DIR` directories
13. No real HTTP requests are made in any test (all network calls are mocked)

---

## Files created/modified (complete list)

| Action | File |
|--------|------|
| Create | `src/rts_predict/aoe2/data/aoe2companion/__init__.py` |
| Create | `src/rts_predict/aoe2/data/aoestats/__init__.py` |
| Create | `src/rts_predict/aoe2/data/aoe2companion/acquisition.py` |
| Create | `src/rts_predict/aoe2/data/aoestats/acquisition.py` |
| Create | `src/rts_predict/aoe2/data/tests/conftest.py` |
| Create | `src/rts_predict/aoe2/data/tests/test_aoe2companion_acquisition.py` |
| Create | `src/rts_predict/aoe2/data/tests/test_aoestats_acquisition.py` |
| Create | `src/rts_predict/aoe2/tests/test_cli.py` (or append to existing) |
| Modify | `src/rts_predict/aoe2/cli.py` |

**No changes to `config.py`** -- all required path constants already exist.
**No new dependencies** -- uses `urllib.request` from stdlib.
