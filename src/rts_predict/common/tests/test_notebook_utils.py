"""Tests for :mod:`rts_predict.common.notebook_utils`.

Covers read-only default, write-access opt-in, unknown game/dataset errors,
reports-dir resolution, and connection lifecycle. Does not hit real DuckDB
files — all tests use tmp_path fixtures or mock the game config modules.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from rts_predict.common.db import DatasetConfig, DuckDBClient
from rts_predict.common.notebook_utils import (
    _load_game_config,
    _resolve_dataset_config,
    get_notebook_db,
    get_reports_dir,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_fake_config_module(
    tmp_path: Path,
    datasets: dict[str, DatasetConfig] | None = None,
    reports_dir: Path | None = None,
) -> ModuleType:
    """Return a minimal fake config module with DATASETS and REPORTS_DIR."""
    if datasets is None:
        db_file = tmp_path / "db" / "db.duckdb"
        temp_dir = tmp_path / "tmp"
        datasets = {
            "testset": DatasetConfig(
                name="testset",
                db_file=db_file,
                temp_dir=temp_dir,
                description="test dataset",
            )
        }
    if reports_dir is None:
        reports_dir = tmp_path / "reports"

    module = MagicMock(spec=ModuleType)
    module.DATASETS = datasets
    module.REPORTS_DIR = reports_dir
    return module


# ---------------------------------------------------------------------------
# _load_game_config
# ---------------------------------------------------------------------------


def test_load_game_config_unknown_game_raises() -> None:
    """_load_game_config must raise ValueError for an unknown game."""
    with pytest.raises(ValueError, match="Unknown game"):
        _load_game_config("aoe3")


def test_load_game_config_known_games_import() -> None:
    """_load_game_config must successfully import sc2 and aoe2 config modules."""
    sc2_config = _load_game_config("sc2")
    assert hasattr(sc2_config, "DATASETS")

    aoe2_config = _load_game_config("aoe2")
    assert hasattr(aoe2_config, "DATASETS")


# ---------------------------------------------------------------------------
# _resolve_dataset_config
# ---------------------------------------------------------------------------


def test_resolve_dataset_config_found(tmp_path: Path) -> None:
    """_resolve_dataset_config must return the DatasetConfig for a known dataset."""
    module = _make_fake_config_module(tmp_path)
    cfg = _resolve_dataset_config(module, "fakegame", "testset")
    assert cfg.name == "testset"


def test_resolve_dataset_config_unknown_dataset_raises(tmp_path: Path) -> None:
    """_resolve_dataset_config must raise ValueError for an unknown dataset."""
    module = _make_fake_config_module(tmp_path)
    with pytest.raises(ValueError, match="Unknown dataset"):
        _resolve_dataset_config(module, "fakegame", "nonexistent")


def test_resolve_dataset_config_error_message_includes_available(tmp_path: Path) -> None:
    """The ValueError message must list available datasets for debugging."""
    module = _make_fake_config_module(tmp_path)
    with pytest.raises(ValueError, match="testset"):
        _resolve_dataset_config(module, "fakegame", "nonexistent")


# ---------------------------------------------------------------------------
# get_notebook_db — unknown game/dataset
# ---------------------------------------------------------------------------


def test_get_notebook_db_unknown_game_raises() -> None:
    """get_notebook_db must raise ValueError for an unknown game."""
    with pytest.raises(ValueError, match="Unknown game"):
        get_notebook_db("warcraft3", "ladder2023")


def test_get_notebook_db_unknown_dataset_raises() -> None:
    """get_notebook_db must raise ValueError for an unknown dataset in a known game."""
    with pytest.raises(ValueError, match="Unknown dataset"):
        get_notebook_db("sc2", "nonexistent_dataset")


# ---------------------------------------------------------------------------
# get_notebook_db — read-only default
# ---------------------------------------------------------------------------


def test_get_notebook_db_returns_duckdb_client_read_only(tmp_path: Path) -> None:
    """get_notebook_db must return a DuckDBClient opened in read-only mode by default."""
    fake_module = _make_fake_config_module(tmp_path)

    with patch(
        "rts_predict.common.notebook_utils._load_game_config",
        return_value=fake_module,
    ):
        # Create the DB first in read-write mode so it exists
        db_file = tmp_path / "db" / "db.duckdb"
        (tmp_path / "db").mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(db_file))
        con.close()

        client = get_notebook_db("sc2", "testset")
        try:
            assert isinstance(client, DuckDBClient)
            # Read-only default: _read_only must be True
            assert client._read_only is True
            # Connection is open
            result = client.fetch_df("SELECT 1 AS x")
            assert result["x"].iloc[0] == 1
        finally:
            client.close()


def test_get_notebook_db_read_only_blocks_writes(tmp_path: Path) -> None:
    """get_notebook_db default (read-only) must raise on INSERT."""
    fake_module = _make_fake_config_module(tmp_path)

    with patch(
        "rts_predict.common.notebook_utils._load_game_config",
        return_value=fake_module,
    ):
        db_file = tmp_path / "db" / "db.duckdb"
        (tmp_path / "db").mkdir(parents=True, exist_ok=True)
        # Create the table before opening read-only
        con = duckdb.connect(str(db_file))
        con.execute("CREATE TABLE t (x INTEGER)")
        con.close()

        client = get_notebook_db("sc2", "testset")
        try:
            with pytest.raises((duckdb.InvalidInputException, duckdb.IOException)) as exc_info:
                client.con.execute("INSERT INTO t VALUES (1)")
            err = str(exc_info.value).lower()
            assert "read" in err or "readonly" in err
        finally:
            client.close()


# ---------------------------------------------------------------------------
# get_notebook_db — write-access opt-in
# ---------------------------------------------------------------------------


def test_get_notebook_db_write_access_opt_in(tmp_path: Path) -> None:
    """get_notebook_db with read_only=False must allow writes."""
    fake_module = _make_fake_config_module(tmp_path)

    with patch(
        "rts_predict.common.notebook_utils._load_game_config",
        return_value=fake_module,
    ):
        (tmp_path / "db").mkdir(parents=True, exist_ok=True)
        (tmp_path / "tmp").mkdir(parents=True, exist_ok=True)

        client = get_notebook_db("sc2", "testset", read_only=False)
        try:
            assert client._read_only is False
            client.con.execute("CREATE TABLE t (x INTEGER)")
            client.con.execute("INSERT INTO t VALUES (42)")
            result = client.fetch_df("SELECT x FROM t")
            assert result["x"].iloc[0] == 42
        finally:
            client.close()


# ---------------------------------------------------------------------------
# get_notebook_db — DuckDBClient.close()
# ---------------------------------------------------------------------------


def test_get_notebook_db_client_is_closeable(tmp_path: Path) -> None:
    """Client returned by get_notebook_db must support .close() for resource cleanup."""
    fake_module = _make_fake_config_module(tmp_path)

    with patch(
        "rts_predict.common.notebook_utils._load_game_config",
        return_value=fake_module,
    ):
        db_file = tmp_path / "db" / "db.duckdb"
        (tmp_path / "db").mkdir(parents=True, exist_ok=True)

        con = duckdb.connect(str(db_file))
        con.close()

        client = get_notebook_db("sc2", "testset")
        # Connection should be open
        assert client._con is not None
        client.close()
        # Connection should be closed after .close()
        assert client._con is None


def test_get_notebook_db_close_is_idempotent(tmp_path: Path) -> None:
    """DuckDBClient.close() must be safe to call multiple times (per docstring)."""
    fake_module = _make_fake_config_module(tmp_path)

    with patch(
        "rts_predict.common.notebook_utils._load_game_config",
        return_value=fake_module,
    ):
        db_file = tmp_path / "db" / "db.duckdb"
        (tmp_path / "db").mkdir(parents=True, exist_ok=True)

        con = duckdb.connect(str(db_file))
        con.close()

        client = get_notebook_db("sc2", "testset")
        client.close()
        # Second call must not raise
        client.close()
        assert client._con is None


# ---------------------------------------------------------------------------
# get_reports_dir
# ---------------------------------------------------------------------------


def test_get_reports_dir_unknown_game_raises() -> None:
    """get_reports_dir must raise ValueError for an unknown game."""
    with pytest.raises(ValueError, match="Unknown game"):
        get_reports_dir("warcraft3", "ladder2023")


def test_get_reports_dir_unknown_dataset_raises() -> None:
    """get_reports_dir must raise ValueError for an unknown dataset."""
    with pytest.raises(ValueError, match="Unknown dataset"):
        get_reports_dir("sc2", "nonexistent_dataset")


def test_get_reports_dir_missing_reports_dir_raises(tmp_path: Path) -> None:
    """get_reports_dir must raise ValueError if config module lacks REPORTS_DIR."""
    fake_module = _make_fake_config_module(tmp_path)
    # Remove REPORTS_DIR from the module so getattr returns None
    del fake_module.REPORTS_DIR

    with patch(
        "rts_predict.common.notebook_utils._load_game_config",
        return_value=fake_module,
    ):
        with pytest.raises(ValueError, match="does not export REPORTS_DIR"):
            get_reports_dir("sc2", "testset")


def test_get_reports_dir_returns_path(tmp_path: Path) -> None:
    """get_reports_dir must return REPORTS_DIR / dataset for a known pair."""
    reports_dir = tmp_path / "reports"
    fake_module = _make_fake_config_module(tmp_path, reports_dir=reports_dir)

    with patch(
        "rts_predict.common.notebook_utils._load_game_config",
        return_value=fake_module,
    ):
        result = get_reports_dir("sc2", "testset")

    assert result == reports_dir / "testset"
    assert isinstance(result, Path)


def test_get_reports_dir_sc2_egset_real() -> None:
    """get_reports_dir must return the correct path for sc2/sc2egset without mocking."""
    result = get_reports_dir("sc2", "sc2egset")
    # Must end with the expected suffix
    assert result.name == "sc2egset"
    assert result.is_absolute()


def test_get_reports_dir_aoe2_companion_real() -> None:
    """get_reports_dir must return the correct path for aoe2/aoe2companion."""
    result = get_reports_dir("aoe2", "aoe2companion")
    assert result.name == "aoe2companion"
    assert result.is_absolute()


def test_get_reports_dir_aoe2_aoestats_real() -> None:
    """get_reports_dir must return the correct path for aoe2/aoestats."""
    result = get_reports_dir("aoe2", "aoestats")
    assert result.name == "aoestats"
    assert result.is_absolute()
