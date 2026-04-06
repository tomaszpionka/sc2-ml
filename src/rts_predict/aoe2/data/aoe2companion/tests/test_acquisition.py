"""Tests for src/rts_predict/aoe2/data/aoe2companion/acquisition.py."""

import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rts_predict.aoe2.config import (
    AOE2COMPANION_RAW_LEADERBOARDS_DIR,
    AOE2COMPANION_RAW_MATCHES_DIR,
    AOE2COMPANION_RAW_PROFILES_DIR,
    AOE2COMPANION_RAW_RATINGS_DIR,
)
from rts_predict.aoe2.data.aoe2companion.acquisition import (
    _classify_entry,
    download_file,
    filter_download_targets,
    is_already_downloaded,
    load_manifest,
    resolve_target_path,
)


class TestLoadManifest:
    """Tests for load_manifest()."""

    def test_loads_valid_manifest(self, aoe2companion_manifest_file: Path) -> None:
        """Valid JSON array is loaded and returned as list of dicts."""
        entries = load_manifest(aoe2companion_manifest_file)
        assert isinstance(entries, list)
        assert len(entries) == 9
        assert all("key" in e for e in entries)

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """FileNotFoundError when manifest path does not exist."""
        with pytest.raises(FileNotFoundError):
            load_manifest(tmp_path / "nonexistent.json")

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """JSONDecodeError when file contains invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")
        with pytest.raises(json.JSONDecodeError):
            load_manifest(bad_file)


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
        assert _classify_entry(key) == expected


class TestFilterDownloadTargets:
    """Tests for filter_download_targets()."""

    def test_keeps_only_download_targets(
        self, aoe2companion_manifest_entries: list[dict]
    ) -> None:
        """9 fixture entries -> 4 targets (1 match, 1 leaderboard, 1 profile, 1 rating)."""
        targets = filter_download_targets(aoe2companion_manifest_entries)
        assert len(targets) == 4
        assert all("_category" in t for t in targets)

    def test_empty_input_returns_empty(self) -> None:
        """Empty list in -> empty list out."""
        assert filter_download_targets([]) == []

    def test_categories_are_correct(
        self, aoe2companion_manifest_entries: list[dict]
    ) -> None:
        """Each returned entry has the expected _category value."""
        targets = filter_download_targets(aoe2companion_manifest_entries)
        categories = {t["_category"] for t in targets}
        assert categories == {"match", "leaderboard", "profile", "rating"}


class TestResolveTargetPath:
    """Tests for resolve_target_path()."""

    def test_match_goes_to_matches_dir(self) -> None:
        """Match parquet entry resolves to AOE2COMPANION_RAW_MATCHES_DIR."""
        entry = {"key": "match-2024-01-01.parquet", "_category": "match"}
        expected = AOE2COMPANION_RAW_MATCHES_DIR / "match-2024-01-01.parquet"
        assert resolve_target_path(entry) == expected

    def test_leaderboard_goes_to_leaderboards_dir(self) -> None:
        """Leaderboard parquet resolves to AOE2COMPANION_RAW_LEADERBOARDS_DIR."""
        entry = {"key": "leaderboard.parquet", "_category": "leaderboard"}
        expected = AOE2COMPANION_RAW_LEADERBOARDS_DIR / "leaderboard.parquet"
        assert resolve_target_path(entry) == expected

    def test_profile_goes_to_profiles_dir(self) -> None:
        """Profile parquet resolves to AOE2COMPANION_RAW_PROFILES_DIR."""
        entry = {"key": "profile.parquet", "_category": "profile"}
        assert resolve_target_path(entry) == AOE2COMPANION_RAW_PROFILES_DIR / "profile.parquet"

    def test_rating_goes_to_ratings_dir(self) -> None:
        """Rating CSV resolves to AOE2COMPANION_RAW_RATINGS_DIR."""
        entry = {"key": "rating-2024-01-01.csv", "_category": "rating"}
        assert resolve_target_path(entry) == AOE2COMPANION_RAW_RATINGS_DIR / "rating-2024-01-01.csv"

    def test_unknown_category_raises(self) -> None:
        """ValueError on unrecognised _category."""
        entry = {"key": "unknown.bin", "_category": "unknown"}
        with pytest.raises(ValueError, match="Unrecognised"):
            resolve_target_path(entry)


class TestIsAlreadyDownloaded:
    """Tests for is_already_downloaded()."""

    def test_returns_true_when_size_matches(self, tmp_path: Path) -> None:
        """File exists with exact manifest size -> True."""
        target = tmp_path / "test.parquet"
        target.write_bytes(b"x" * 100)
        assert is_already_downloaded(target, 100) is True

    def test_returns_true_when_file_larger_than_expected(self, tmp_path: Path) -> None:
        """File on disk is larger than manifest size (CDN update) -> True."""
        target = tmp_path / "test.parquet"
        target.write_bytes(b"x" * 110)
        assert is_already_downloaded(target, 100) is True

    def test_returns_false_when_file_smaller_than_expected(self, tmp_path: Path) -> None:
        """File exists but is smaller than manifest size (truncated) -> False."""
        target = tmp_path / "test.parquet"
        target.write_bytes(b"x" * 100)
        assert is_already_downloaded(target, 200) is False

    def test_returns_false_when_file_missing(self, tmp_path: Path) -> None:
        """File does not exist -> False."""
        assert is_already_downloaded(tmp_path / "missing.parquet", 100) is False

    def test_none_expected_size_accepts_nonempty_file(self, tmp_path: Path) -> None:
        """expected_size=None (live file): any non-empty file is accepted."""
        target = tmp_path / "leaderboard.parquet"
        target.write_bytes(b"x" * 50)
        assert is_already_downloaded(target, None) is True

    def test_none_expected_size_rejects_empty_file(self, tmp_path: Path) -> None:
        """expected_size=None: empty file is rejected."""
        target = tmp_path / "leaderboard.parquet"
        target.write_bytes(b"")
        assert is_already_downloaded(target, None) is False

    def test_none_expected_size_rejects_missing_file(self, tmp_path: Path) -> None:
        """expected_size=None: missing file is rejected."""
        assert is_already_downloaded(tmp_path / "missing.parquet", None) is False


class TestDownloadFile:
    """Tests for download_file() with mocked HTTP."""

    def test_downloads_and_saves_file(self, tmp_path: Path) -> None:
        """Successful download creates file with correct content."""
        content = b"hello parquet"
        target = tmp_path / "file.parquet"
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.side_effect = [content, b""]

        with patch("urllib.request.urlopen", return_value=mock_response):
            download_file("https://example.com/file.parquet", target, len(content))

        assert target.exists()
        assert target.read_bytes() == content

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Parent directories are created if they do not exist."""
        content = b"data"
        target = tmp_path / "a" / "b" / "file.parquet"
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.side_effect = [content, b""]

        with patch("urllib.request.urlopen", return_value=mock_response):
            download_file("https://example.com/file.parquet", target, len(content))

        assert target.exists()

    def test_raises_on_truncated_download(self, tmp_path: Path) -> None:
        """ValueError raised when downloaded size < expected_size (truncation)."""
        content = b"x" * 100
        target = tmp_path / "file.parquet"
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.side_effect = [content, b""]

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(ValueError, match="Truncated"):
                download_file("https://example.com/file.parquet", target, 200)

        assert not target.exists()

    def test_accepts_oversized_download(self, tmp_path: Path) -> None:
        """No error when CDN serves more bytes than manifest recorded."""
        content = b"x" * 110
        target = tmp_path / "file.parquet"
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.side_effect = [content, b""]

        with patch("urllib.request.urlopen", return_value=mock_response):
            download_file("https://example.com/file.parquet", target, 100)

        assert target.exists()
        assert len(target.read_bytes()) == 110

    def test_cleans_up_temp_file_on_network_failure(self, tmp_path: Path) -> None:
        """Temporary file is removed if download raises an exception."""
        target = tmp_path / "file.parquet"

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("network error"),
        ):
            with pytest.raises(urllib.error.URLError):
                download_file("https://example.com/file.parquet", target)

        assert not target.exists()
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0


class TestRunDownload:
    """Tests for run_download() orchestrator with mocked internals."""

    def test_dry_run_downloads_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoe2companion_manifest_file: Path
    ) -> None:
        """dry_run=True: no HTTP calls, all targets logged as 'dry_run'."""
        import rts_predict.aoe2.data.aoe2companion.acquisition as mod

        monkeypatch.setattr(mod, "AOE2COMPANION_MANIFEST", aoe2companion_manifest_file)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_MATCHES_DIR", tmp_path / "matches")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_LEADERBOARDS_DIR", tmp_path / "leaderboards")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_PROFILES_DIR", tmp_path / "profiles")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_RATINGS_DIR", tmp_path / "ratings")

        result = mod.run_download(dry_run=True)

        assert result["downloaded"] == 0
        assert result["dry_run"] is True
        assert result["total_targets"] == 4

    def test_skips_already_downloaded_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoe2companion_manifest_file: Path
    ) -> None:
        """Files already on disk with matching size are skipped."""
        import rts_predict.aoe2.data.aoe2companion.acquisition as mod

        matches_dir = tmp_path / "matches"
        matches_dir.mkdir()
        (matches_dir / "match-2024-01-01.parquet").write_bytes(b"x" * 500000)

        monkeypatch.setattr(mod, "AOE2COMPANION_MANIFEST", aoe2companion_manifest_file)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_MATCHES_DIR", matches_dir)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_LEADERBOARDS_DIR", tmp_path / "leaderboards")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_PROFILES_DIR", tmp_path / "profiles")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_RATINGS_DIR", tmp_path / "ratings")

        result = mod.run_download(dry_run=True)

        assert result["skipped"] == 1

    def test_download_log_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoe2companion_manifest_file: Path
    ) -> None:
        """Download manifest JSON is written after run_download completes."""
        import rts_predict.aoe2.data.aoe2companion.acquisition as mod

        monkeypatch.setattr(mod, "AOE2COMPANION_MANIFEST", aoe2companion_manifest_file)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_MATCHES_DIR", tmp_path / "matches")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_LEADERBOARDS_DIR", tmp_path / "leaderboards")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_PROFILES_DIR", tmp_path / "profiles")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_RATINGS_DIR", tmp_path / "ratings")

        result = mod.run_download(dry_run=True)

        log_file = tmp_path / "_download_manifest.json"
        assert log_file.exists()
        entries = json.loads(log_file.read_text())
        assert isinstance(entries, list)
        assert len(entries) == 4
        required_keys = {"key", "url", "target_path", "size", "status", "timestamp"}
        for entry in entries:
            assert required_keys.issubset(entry.keys())
        assert result["log_path"] == str(log_file)

    def test_handles_download_failure_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoe2companion_manifest_file: Path
    ) -> None:
        """Network failure for one file does not abort the entire run."""
        import rts_predict.aoe2.data.aoe2companion.acquisition as mod

        monkeypatch.setattr(mod, "AOE2COMPANION_MANIFEST", aoe2companion_manifest_file)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_MATCHES_DIR", tmp_path / "matches")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_LEADERBOARDS_DIR", tmp_path / "leaderboards")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_PROFILES_DIR", tmp_path / "profiles")
        monkeypatch.setattr(mod, "AOE2COMPANION_RAW_RATINGS_DIR", tmp_path / "ratings")

        call_count = 0

        def mock_download(url: str, target_path: Path, expected_size: int | None = None) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.URLError("network error")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"x" * (expected_size or 0))

        monkeypatch.setattr(mod, "download_file", mock_download)

        result = mod.run_download(dry_run=False)

        assert result["failed"] == 1
        assert result["downloaded"] == 3
        assert result["total_targets"] == 4
