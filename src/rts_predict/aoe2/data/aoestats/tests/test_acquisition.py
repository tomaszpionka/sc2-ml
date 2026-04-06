"""Tests for src/rts_predict/aoe2/data/aoestats/acquisition.py."""

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rts_predict.aoe2.config import AOESTATS_RAW_MATCHES_DIR, AOESTATS_RAW_PLAYERS_DIR
from rts_predict.aoe2.data.aoestats.acquisition import (
    _compute_md5,
    download_file,
    filter_download_targets,
    is_already_downloaded,
    load_manifest,
    resolve_target_paths,
    run_download,
)


class TestLoadManifest:
    """Tests for load_manifest()."""

    def test_loads_valid_manifest(self, aoestats_manifest_file: Path) -> None:
        """Valid JSON with db_dumps array is loaded correctly."""
        entries = load_manifest(aoestats_manifest_file)
        assert isinstance(entries, list)
        assert len(entries) == 3

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """FileNotFoundError when manifest does not exist."""
        with pytest.raises(FileNotFoundError):
            load_manifest(tmp_path / "nonexistent.json")

    def test_raises_on_missing_db_dumps_key(self, tmp_path: Path) -> None:
        """KeyError when JSON lacks 'db_dumps' key."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text(json.dumps({"other": []}))
        with pytest.raises(KeyError):
            load_manifest(bad_file)


class TestFilterDownloadTargets:
    """Tests for filter_download_targets()."""

    def test_removes_zero_match_entries(
        self, aoestats_manifest_entries: list[dict]
    ) -> None:
        """3 fixture entries (2 non-zero, 1 zero) -> 2 targets."""
        targets = filter_download_targets(aoestats_manifest_entries)
        assert len(targets) == 2

    def test_empty_input_returns_empty(self) -> None:
        """Empty list in -> empty list out."""
        assert filter_download_targets([]) == []

    def test_all_zero_returns_empty(self) -> None:
        """All entries have num_matches == 0 -> empty list."""
        entries = [
            {
                "start_date": "2023-01-01",
                "end_date": "2023-01-07",
                "num_matches": 0,
                "num_players": 0,
                "matches_url": "/x/matches.parquet",
                "players_url": "/x/players.parquet",
                "match_checksum": "abc",
                "player_checksum": "def",
            }
        ]
        assert filter_download_targets(entries) == []


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


class TestComputeMd5:
    """Tests for _compute_md5()."""

    def test_known_hash(self, tmp_path: Path) -> None:
        """MD5 of known content matches expected digest."""
        target = tmp_path / "test.bin"
        target.write_bytes(b"hello world")
        assert _compute_md5(target) == "5eb63bbbe01eeed093cb22bb8f5acdc3"

    def test_empty_file(self, tmp_path: Path) -> None:
        """MD5 of empty file is the known empty-input digest."""
        target = tmp_path / "empty.bin"
        target.write_bytes(b"")
        assert _compute_md5(target) == "d41d8cd98f00b204e9800998ecf8427e"


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


class TestDownloadFile:
    """Tests for download_file() with mocked HTTP."""

    def test_downloads_and_verifies_md5(self, tmp_path: Path) -> None:
        """Successful download creates file that passes MD5 check."""
        content = b"hello parquet data"
        expected_checksum = hashlib.md5(content).hexdigest()
        target = tmp_path / "file.parquet"

        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.side_effect = [content, b""]

        with patch("urllib.request.urlopen", return_value=mock_response):
            download_file("https://aoestats.io/file.parquet", target, expected_checksum)

        assert target.exists()
        assert hashlib.md5(target.read_bytes()).hexdigest() == expected_checksum

    def test_raises_on_checksum_mismatch(self, tmp_path: Path) -> None:
        """ValueError raised when MD5 does not match expected_checksum."""
        content = b"hello parquet data"
        target = tmp_path / "file.parquet"

        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.side_effect = [content, b""]

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(ValueError, match="MD5 mismatch"):
                download_file("https://aoestats.io/file.parquet", target, "wrongchecksum")

        assert not target.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Parent directories are created automatically."""
        content = b"data"
        expected_checksum = hashlib.md5(content).hexdigest()
        target = tmp_path / "a" / "b" / "file.parquet"

        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.side_effect = [content, b""]

        with patch("urllib.request.urlopen", return_value=mock_response):
            download_file("https://aoestats.io/file.parquet", target, expected_checksum)

        assert target.exists()


class TestRunDownload:
    """Tests for run_download() orchestrator."""

    def test_deferred_without_force(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without force=True, returns immediately with deferred=True."""
        result = run_download(dry_run=False, force=False)
        assert result["deferred"] is True
        assert result["downloaded"] == 0

    def test_dry_run_proceeds_without_force(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoestats_manifest_file: Path
    ) -> None:
        """dry_run=True works even without force (shows what would happen)."""
        import rts_predict.aoe2.data.aoestats.acquisition as mod

        monkeypatch.setattr(mod, "AOESTATS_MANIFEST", aoestats_manifest_file)
        monkeypatch.setattr(mod, "AOESTATS_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOESTATS_RAW_MATCHES_DIR", tmp_path / "matches")
        monkeypatch.setattr(mod, "AOESTATS_RAW_PLAYERS_DIR", tmp_path / "players")

        result = mod.run_download(dry_run=True, force=False)

        assert result["dry_run"] is True
        assert result["deferred"] is False
        assert result["downloaded"] == 0

    def test_force_enables_download(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoestats_manifest_file: Path
    ) -> None:
        """force=True allows actual downloads to proceed."""
        import rts_predict.aoe2.data.aoestats.acquisition as mod

        monkeypatch.setattr(mod, "AOESTATS_MANIFEST", aoestats_manifest_file)
        monkeypatch.setattr(mod, "AOESTATS_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOESTATS_RAW_MATCHES_DIR", tmp_path / "matches")
        monkeypatch.setattr(mod, "AOESTATS_RAW_PLAYERS_DIR", tmp_path / "players")

        def mock_download(url: str, target_path: Path, expected_checksum: str) -> None:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"data")

        monkeypatch.setattr(mod, "download_file", mock_download)

        result = mod.run_download(dry_run=False, force=True)

        assert result["forced"] is True
        assert result["deferred"] is False
        assert result["downloaded"] > 0

    def test_skips_already_downloaded_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoestats_manifest_file: Path
    ) -> None:
        """Files with matching MD5 are skipped."""
        import rts_predict.aoe2.data.aoestats.acquisition as mod

        matches_dir = tmp_path / "matches"
        matches_dir.mkdir()
        players_dir = tmp_path / "players"
        players_dir.mkdir()

        # Pre-create week 1 files (checksums from fixture — contents don't need to match)
        content = b"preexisting data"
        matches_file = matches_dir / "2023-01-01_2023-01-07_matches.parquet"
        players_file = players_dir / "2023-01-01_2023-01-07_players.parquet"
        matches_file.write_bytes(content)
        players_file.write_bytes(content)

        monkeypatch.setattr(mod, "AOESTATS_MANIFEST", aoestats_manifest_file)
        monkeypatch.setattr(mod, "AOESTATS_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOESTATS_RAW_MATCHES_DIR", matches_dir)
        monkeypatch.setattr(mod, "AOESTATS_RAW_PLAYERS_DIR", players_dir)

        # Mock is_already_downloaded to return True for the pre-created files
        original_is_downloaded = mod.is_already_downloaded

        def mock_is_downloaded(file_path: Path, expected_checksum: str) -> bool:
            if file_path in (matches_file, players_file):
                return True
            return original_is_downloaded(file_path, expected_checksum)

        monkeypatch.setattr(mod, "is_already_downloaded", mock_is_downloaded)

        result = mod.run_download(dry_run=True, force=False)

        assert result["skipped"] == 2

    def test_download_log_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoestats_manifest_file: Path
    ) -> None:
        """Download manifest JSON is written after completion."""
        import rts_predict.aoe2.data.aoestats.acquisition as mod

        monkeypatch.setattr(mod, "AOESTATS_MANIFEST", aoestats_manifest_file)
        monkeypatch.setattr(mod, "AOESTATS_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOESTATS_RAW_MATCHES_DIR", tmp_path / "matches")
        monkeypatch.setattr(mod, "AOESTATS_RAW_PLAYERS_DIR", tmp_path / "players")

        result = mod.run_download(dry_run=True, force=False)

        log_file = tmp_path / "_download_manifest.json"
        assert log_file.exists()
        entries = json.loads(log_file.read_text())
        assert isinstance(entries, list)
        assert result["log_path"] == str(log_file)

    def test_processes_both_matches_and_players(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aoestats_manifest_file: Path
    ) -> None:
        """Each non-zero entry produces two download attempts (matches + players)."""
        import rts_predict.aoe2.data.aoestats.acquisition as mod

        monkeypatch.setattr(mod, "AOESTATS_MANIFEST", aoestats_manifest_file)
        monkeypatch.setattr(mod, "AOESTATS_RAW_DIR", tmp_path)
        monkeypatch.setattr(mod, "AOESTATS_RAW_MATCHES_DIR", tmp_path / "matches")
        monkeypatch.setattr(mod, "AOESTATS_RAW_PLAYERS_DIR", tmp_path / "players")

        result = mod.run_download(dry_run=True, force=False)

        # 2 non-zero entries -> 4 files total
        assert result["total_targets"] == 2
        assert result["total_files"] == 4
