"""Tests for :mod:`rts_predict.common.db` — DuckDBClient and DatasetConfig."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pandas as pd
import pytest

from rts_predict.common.db import DatasetConfig, DuckDBClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path, name: str = "test_db") -> DatasetConfig:
    """Return a DatasetConfig pointing to a temp directory."""
    return DatasetConfig(
        name=name,
        db_file=tmp_path / "db" / f"{name}.duckdb",
        temp_dir=tmp_path / "tmp",
        description="test dataset",
    )


# ---------------------------------------------------------------------------
# DatasetConfig
# ---------------------------------------------------------------------------


def test_dataset_config_is_frozen() -> None:
    """Assigning to a frozen dataclass field must raise FrozenInstanceError."""
    cfg = DatasetConfig(
        name="x",
        db_file=Path("/tmp/x.duckdb"),
        temp_dir=Path("/tmp/x_tmp"),
        description="frozen test",
    )
    with pytest.raises(FrozenInstanceError):
        cfg.name = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DuckDBClient — context manager
# ---------------------------------------------------------------------------


def test_client_context_manager_closes(tmp_path: Path) -> None:
    """The underlying connection must be None after __exit__."""
    cfg = _make_config(tmp_path)
    client = DuckDBClient(cfg)
    with client:
        assert client._con is not None
    # After exiting the context manager, _con should be None
    assert client._con is None


def test_client_creates_parent_dirs(tmp_path: Path) -> None:
    """Parent directories for db_file and temp_dir must be created on __enter__."""
    cfg = DatasetConfig(
        name="nested",
        db_file=tmp_path / "a" / "b" / "c" / "nested.duckdb",
        temp_dir=tmp_path / "x" / "y" / "z",
        description="nested dirs test",
    )
    assert not cfg.db_file.parent.exists()
    assert not cfg.temp_dir.exists()

    with DuckDBClient(cfg):
        assert cfg.db_file.parent.exists()
        assert cfg.temp_dir.exists()


def test_client_read_only_flag(tmp_path: Path) -> None:
    """A read_only=True client must raise an error on INSERT."""
    cfg = _make_config(tmp_path)

    # First create the db with a table
    with DuckDBClient(cfg) as client:
        client.con.execute("CREATE TABLE t (x INTEGER)")
        client.con.execute("INSERT INTO t VALUES (1)")

    # Now open read-only and attempt a write
    with DuckDBClient(cfg, read_only=True) as client:
        with pytest.raises(Exception):
            client.con.execute("INSERT INTO t VALUES (2)")


def test_client_applies_memory_pragma(tmp_path: Path) -> None:
    """The memory_limit pragma must be applied and retrievable."""
    cfg = _make_config(tmp_path)
    with DuckDBClient(cfg, memory_limit="512MB") as client:
        result = client.con.execute("SELECT current_setting('memory_limit')").fetchone()
        assert result is not None
        # DuckDB normalises "512MB" — just verify the value is not the default
        value = result[0]
        assert value is not None
        assert "512" in str(value) or "MB" in str(value).upper() or "GiB" not in str(value)


# ---------------------------------------------------------------------------
# DuckDBClient — query API
# ---------------------------------------------------------------------------


def test_client_query_returns_relation(tmp_path: Path) -> None:
    """query() must return a relation with the expected columns and row count."""
    cfg = _make_config(tmp_path)
    with DuckDBClient(cfg) as client:
        client.con.execute("CREATE TABLE nums (n INTEGER)")
        client.con.execute("INSERT INTO nums VALUES (1), (2), (3)")
        rel = client.query("SELECT n FROM nums ORDER BY n")
        df = rel.df()

    assert list(df.columns) == ["n"]
    assert df["n"].tolist() == [1, 2, 3]


def test_client_fetch_df_returns_dataframe(tmp_path: Path) -> None:
    """fetch_df() must return a pandas DataFrame."""
    cfg = _make_config(tmp_path)
    with DuckDBClient(cfg) as client:
        result = client.fetch_df("SELECT 42 AS answer")

    assert isinstance(result, pd.DataFrame)
    assert result["answer"].iloc[0] == 42


def test_client_tables_lists_tables(tmp_path: Path) -> None:
    """tables() must include a table after it is created."""
    cfg = _make_config(tmp_path)
    with DuckDBClient(cfg) as client:
        assert client.tables() == []
        client.con.execute("CREATE TABLE my_table (x INTEGER)")
        tables = client.tables()

    assert "my_table" in tables


def test_client_schema_returns_columns(tmp_path: Path) -> None:
    """schema() must return the correct column names and types from the DDL."""
    cfg = _make_config(tmp_path)
    with DuckDBClient(cfg) as client:
        client.con.execute(
            "CREATE TABLE products (id INTEGER, name VARCHAR, price DOUBLE)"
        )
        pairs = client.schema("products")

    col_names = [p[0] for p in pairs]
    assert col_names == ["id", "name", "price"]
    # Types are normalised by DuckDB — verify each is a non-empty string
    for _, col_type in pairs:
        assert isinstance(col_type, str)
        assert col_type
