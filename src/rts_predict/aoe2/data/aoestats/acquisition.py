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
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from rts_predict.aoe2.config import (
    AOESTATS_MANIFEST,
    AOESTATS_RAW_DIR,
    AOESTATS_RAW_MATCHES_DIR,
    AOESTATS_RAW_OVERVIEW_DIR,
    AOESTATS_RAW_PLAYERS_DIR,
)

logger = logging.getLogger(__name__)

# Base URL for aoestats file downloads (manifest provides relative paths)
_AOESTATS_BASE_URL: str = "https://aoestats.io"

# HTTP headers to bypass Cloudflare User-Agent blocking
_HTTP_HEADERS: dict[str, str] = {"User-Agent": "Mozilla/5.0"}

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


def download_overview(
    url: str = "https://aoestats.io/api/overview/?format=json",
    target_dir: Path | None = None,
    filename: str = "overview.json",
) -> Path:
    """Download the aoestats overview JSON reference file.

    Idempotent: if the target file already exists, returns its path
    without making an HTTP request.

    The overview JSON provides lookup tables (civilizations, maps,
    game modes, etc.) used during schema discovery and ingestion.

    Args:
        url: URL to fetch the overview JSON from.
        target_dir: Directory to write the file into. Defaults to
            AOESTATS_RAW_OVERVIEW_DIR.
        filename: Name of the output file. Default "overview.json".

    Returns:
        Absolute path to the downloaded (or already existing) file.

    Raises:
        urllib.error.URLError: On network errors.
        OSError: On filesystem errors.
    """
    resolved_dir = target_dir if target_dir is not None else AOESTATS_RAW_OVERVIEW_DIR
    target_path = resolved_dir / filename

    if target_path.exists():
        logger.info("Overview file already exists, skipping download: %s", target_path)
        return target_path

    resolved_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(".json.tmp")

    try:
        req = urllib.request.Request(url, headers=_HTTP_HEADERS)
        with urllib.request.urlopen(req) as response:
            content = response.read()
        tmp_path.write_bytes(content)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    shutil.move(str(tmp_path), target_path)
    logger.info("Downloaded overview to %s (%d bytes)", target_path, target_path.stat().st_size)
    return target_path


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
    with open(manifest_path, "r", encoding="utf-8") as f:
        data: dict = json.load(f)
    entries: list[dict] = data["db_dumps"]
    logger.info("Loaded aoestats manifest: %d entries", len(entries))
    return entries


def filter_download_targets(entries: list[dict]) -> list[dict]:
    """Filter manifest entries, removing weeks with zero matches.

    Args:
        entries: Raw manifest entries from load_manifest().

    Returns:
        Filtered list containing only entries where num_matches > 0.
    """
    targets = [e for e in entries if e["num_matches"] > 0]
    skipped = len(entries) - len(targets)
    logger.info(
        "aoestats filter: %d targets, %d zero-match entries skipped",
        len(targets),
        skipped,
    )
    return targets


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
    start = entry["start_date"]
    end = entry["end_date"]
    matches_name = f"{start}_{end}_matches.parquet"
    players_name = f"{start}_{end}_players.parquet"
    return (AOESTATS_RAW_MATCHES_DIR / matches_name, AOESTATS_RAW_PLAYERS_DIR / players_name)


def _compute_md5(file_path: Path) -> str:
    """Compute the MD5 hex digest of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Lowercase hex MD5 digest string.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(_MD5_CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def is_already_downloaded(file_path: Path, expected_checksum: str) -> bool:
    """Check whether a file is already downloaded with the correct MD5.

    Args:
        file_path: Path where the file should exist.
        expected_checksum: Expected MD5 hex digest from the manifest.

    Returns:
        True if the file exists and its MD5 matches expected_checksum.
    """
    return file_path.exists() and _compute_md5(file_path) == expected_checksum


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
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")

    try:
        req = urllib.request.Request(url, headers=_HTTP_HEADERS)
        with urllib.request.urlopen(req) as response:
            with open(tmp_path, "wb") as out_file:
                while True:
                    chunk = response.read(_DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    out_file.write(chunk)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    actual_checksum = _compute_md5(tmp_path)
    if actual_checksum != expected_checksum:
        tmp_path.unlink()
        raise ValueError(
            f"MD5 mismatch for {url}: expected {expected_checksum}, got {actual_checksum}"
        )

    shutil.move(str(tmp_path), target_path)


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
    if file_type == "matches":
        url = _AOESTATS_BASE_URL + entry["matches_url"]
        checksum = entry["match_checksum"]
    else:
        url = _AOESTATS_BASE_URL + entry["players_url"]
        checksum = entry["player_checksum"]

    return {
        "start_date": entry["start_date"],
        "end_date": entry["end_date"],
        "file_type": file_type,
        "url": url,
        "target_path": str(target_path),
        "checksum": checksum,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }


def _write_download_log(log_entries: list[dict]) -> Path:
    """Write the download manifest log to disk.

    Args:
        log_entries: List of log entry dicts.

    Returns:
        Path to the written log file.
    """
    log_path = AOESTATS_RAW_DIR / _DOWNLOAD_LOG_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entries, f, indent=2)
    logger.info("Download log written to %s (%d entries)", log_path, len(log_entries))
    return log_path


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
    if not force and not dry_run:
        logger.warning(_DEFERRED_WARNING)
        return {
            "total_targets": 0,
            "total_files": 0,
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
            "dry_run": dry_run,
            "forced": False,
            "deferred": True,
            "log_path": None,
        }

    entries = load_manifest(AOESTATS_MANIFEST)
    targets = filter_download_targets(entries)
    logger.info(
        "aoestats: %d weekly dumps, %d files", len(targets), len(targets) * 2
    )

    downloaded = 0
    skipped = 0
    failed = 0
    log_entries: list[dict] = []

    file_specs = [
        ("matches_url", "match_checksum", "matches"),
        ("players_url", "player_checksum", "players"),
    ]

    for idx, entry in enumerate(targets):
        matches_path, players_path = resolve_target_paths(entry)
        paths_by_type = {"matches": matches_path, "players": players_path}

        for url_key, checksum_key, file_type in file_specs:
            file_path = paths_by_type[file_type]
            full_url = _AOESTATS_BASE_URL + entry[url_key]
            checksum = entry[checksum_key]

            if is_already_downloaded(file_path, checksum):
                skipped += 1
                log_entries.append(
                    _build_download_log_entry(entry, file_type, file_path, "skipped")
                )
            elif dry_run:
                logger.debug("[DRY RUN] Would download: %s", file_path.name)
                log_entries.append(
                    _build_download_log_entry(entry, file_type, file_path, "dry_run")
                )
            else:
                try:
                    download_file(full_url, file_path, checksum)
                    downloaded += 1
                    log_entries.append(
                        _build_download_log_entry(
                            entry, file_type, file_path, "downloaded"
                        )
                    )
                except (urllib.error.URLError, ValueError, OSError) as exc:
                    failed += 1
                    logger.warning("Failed to download %s: %s", file_path.name, exc)
                    log_entries.append(
                        _build_download_log_entry(
                            entry, file_type, file_path, "failed", str(exc)
                        )
                    )

        if (idx + 1) % log_interval == 0:
            logger.info(
                "Progress: %d/%d entries (downloaded=%d, skipped=%d, failed=%d)",
                idx + 1,
                len(targets),
                downloaded,
                skipped,
                failed,
            )

    log_path = _write_download_log(log_entries)
    logger.info(
        "aoestats download complete: targets=%d, downloaded=%d, skipped=%d, failed=%d",
        len(targets),
        downloaded,
        skipped,
        failed,
    )
    return {
        "total_targets": len(targets),
        "total_files": len(targets) * 2,
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
        "dry_run": dry_run,
        "forced": force,
        "deferred": False,
        "log_path": str(log_path),
    }
