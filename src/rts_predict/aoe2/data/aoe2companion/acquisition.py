"""Download raw data files from the aoe2companion CDN.

Reads the on-disk manifest (api_dump_list.json), filters to download targets
(match parquets, leaderboard parquet, profile parquet, rating CSVs), and
streams each file to its target raw/ subdirectory. Idempotent: skips files
whose on-disk size is at least as large as the manifest size field.

Size check policy:
- match / rating entries: reject if actual_size < expected_size (truncation guard).
  Accept if actual_size >= expected_size (CDN may serve slightly updated files).
- leaderboard / profile entries: no size check — these are live CDN files that
  are updated regularly; the manifest size becomes stale within hours.
"""

import json
import logging
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from rts_predict.aoe2.config import (
    AOE2COMPANION_MANIFEST,
    AOE2COMPANION_RAW_DIR,
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

# HTTP headers to bypass Cloudflare User-Agent blocking
_HTTP_HEADERS: dict[str, str] = {"User-Agent": "Mozilla/5.0"}

# Progress logging interval (every N files)
LOG_INTERVAL: int = 100

# Stream download buffer size (bytes)
_DOWNLOAD_CHUNK_SIZE: int = 8192

# Download log filename
_DOWNLOAD_LOG_FILENAME: str = "_download_manifest.json"


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
    with open(manifest_path, "r", encoding="utf-8") as f:
        entries: list[dict] = json.load(f)
    logger.info("Loaded aoe2companion manifest: %d entries", len(entries))
    return entries


def _classify_entry(key: str) -> str | None:
    """Classify a manifest entry key into a download category.

    Args:
        key: The 'key' field from a manifest entry (e.g., 'match-2020-08-01.parquet').

    Returns:
        One of 'match', 'leaderboard', 'profile', 'rating', or None if the
        entry should be skipped.
    """
    if _MATCH_PARQUET_PATTERN.match(key):
        return "match"
    if key == _LEADERBOARD_PARQUET_KEY:
        return "leaderboard"
    if key == _PROFILE_PARQUET_KEY:
        return "profile"
    if _RATING_CSV_PATTERN.match(key):
        return "rating"
    return None


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
    targets: list[dict] = []
    skipped = 0
    category_counts: dict[str, int] = {}

    for entry in entries:
        category = _classify_entry(entry["key"])
        if category is None:
            skipped += 1
            continue
        augmented = dict(entry)
        augmented["_category"] = category
        targets.append(augmented)
        category_counts[category] = category_counts.get(category, 0) + 1

    logger.info(
        "aoe2companion filter: %d targets (%s), %d skipped",
        len(targets),
        ", ".join(f"{k}={v}" for k, v in sorted(category_counts.items())),
        skipped,
    )
    return targets


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
    category = entry["_category"]
    key = entry["key"]
    if category == "match":
        return AOE2COMPANION_RAW_MATCHES_DIR / key
    if category == "leaderboard":
        return AOE2COMPANION_RAW_LEADERBOARDS_DIR / key
    if category == "profile":
        return AOE2COMPANION_RAW_PROFILES_DIR / key
    if category == "rating":
        return AOE2COMPANION_RAW_RATINGS_DIR / key
    raise ValueError(f"Unrecognised _category: {category!r}")


def is_already_downloaded(target_path: Path, expected_size: int | None) -> bool:
    """Check whether a file is already downloaded and acceptable.

    Idempotency check. The eTag is a multipart upload hash and is NOT
    suitable as an MD5 check, so size is used instead.

    Args:
        target_path: Path where the file should exist.
        expected_size: Expected minimum file size in bytes from the manifest,
            or None for live files (leaderboard/profile) where any non-empty
            file is accepted.

    Returns:
        True if the file exists and its on-disk size >= expected_size
        (or any non-zero size when expected_size is None).
    """
    if not target_path.exists():
        return False
    actual = target_path.stat().st_size
    if expected_size is None:
        return actual > 0
    return actual >= expected_size


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

    actual_size = tmp_path.stat().st_size
    if expected_size is not None and actual_size < expected_size:
        tmp_path.unlink()
        raise ValueError(
            f"Truncated download for {url}: expected >={expected_size}, got {actual_size}"
        )
    if expected_size is not None and actual_size > expected_size:
        logger.warning(
            "CDN served updated file for %s: manifest=%d, actual=%d (+%d bytes)",
            url,
            expected_size,
            actual_size,
            actual_size - expected_size,
        )

    shutil.move(str(tmp_path), target_path)


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
    return {
        "key": entry["key"],
        "url": entry["url"],
        "target_path": str(target_path),
        "size": entry["size"],
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }


def _write_download_log(log_entries: list[dict]) -> Path:
    """Write the download manifest log to disk.

    Args:
        log_entries: List of log entry dicts from _build_download_log_entry.

    Returns:
        Path to the written log file.
    """
    log_path = AOE2COMPANION_RAW_DIR / _DOWNLOAD_LOG_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entries, f, indent=2)
    logger.info("Download log written to %s (%d entries)", log_path, len(log_entries))
    return log_path


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
    entries = load_manifest(AOE2COMPANION_MANIFEST)
    targets = filter_download_targets(entries)
    logger.info("aoe2companion: %d download targets identified", len(targets))

    downloaded = 0
    skipped = 0
    failed = 0
    log_entries: list[dict] = []

    # leaderboard/profile are live CDN files — manifest size becomes stale quickly
    _LIVE_CATEGORIES: frozenset[str] = frozenset({"leaderboard", "profile"})

    for idx, entry in enumerate(targets):
        target_path = resolve_target_path(entry)
        size_hint: int | None = (
            None if entry["_category"] in _LIVE_CATEGORIES else entry["size"]
        )

        if is_already_downloaded(target_path, size_hint):
            skipped += 1
            log_entries.append(_build_download_log_entry(entry, target_path, "skipped"))
        elif dry_run:
            logger.debug("[DRY RUN] Would download: %s", entry["key"])
            log_entries.append(_build_download_log_entry(entry, target_path, "dry_run"))
        else:
            try:
                download_file(entry["url"], target_path, size_hint)
                downloaded += 1
                log_entries.append(
                    _build_download_log_entry(entry, target_path, "downloaded")
                )
            except (urllib.error.URLError, ValueError, OSError) as exc:
                failed += 1
                logger.warning("Failed to download %s: %s", entry["key"], exc)
                log_entries.append(
                    _build_download_log_entry(entry, target_path, "failed", str(exc))
                )

        if (idx + 1) % log_interval == 0:
            logger.info(
                "Progress: %d/%d (downloaded=%d, skipped=%d, failed=%d)",
                idx + 1,
                len(targets),
                downloaded,
                skipped,
                failed,
            )

    log_path = _write_download_log(log_entries)
    logger.info(
        "aoe2companion download complete: total=%d, downloaded=%d, skipped=%d, failed=%d",
        len(targets),
        downloaded,
        skipped,
        failed,
    )
    return {
        "total_targets": len(targets),
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
        "dry_run": dry_run,
        "log_path": str(log_path),
    }
