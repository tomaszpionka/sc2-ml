"""Tests for :mod:`rts_predict.common.db_cli` — shared argparse db helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from rts_predict.common.db import DatasetConfig
from rts_predict.common.db_cli import add_db_subparser, handle_db_command

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DS_A = DatasetConfig(
    name="dataset_a",
    db_file=Path("/tmp/a.duckdb"),
    temp_dir=Path("/tmp/a_tmp"),
    description="Dataset A",
)
_DS_B = DatasetConfig(
    name="dataset_b",
    db_file=Path("/tmp/b.duckdb"),
    temp_dir=Path("/tmp/b_tmp"),
    description="Dataset B",
)
_DATASETS: dict[str, DatasetConfig] = {"dataset_a": _DS_A, "dataset_b": _DS_B}
_DEFAULT = "dataset_a"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_db_subparser(subparsers, _DATASETS, _DEFAULT)
    return parser


# ---------------------------------------------------------------------------
# add_db_subparser
# ---------------------------------------------------------------------------


def test_add_db_subparser_registers_subcommands() -> None:
    """query, tables, and schema must appear in db sub-subparser choices."""
    parser = _build_parser()
    # Parse a known command to confirm the subparser was registered
    args = parser.parse_args(["db", "tables"])
    assert args.command == "db"
    assert args.db_command == "tables"

    args_q = parser.parse_args(["db", "query", "SELECT 1"])
    assert args_q.db_command == "query"

    args_s = parser.parse_args(["db", "schema", "my_table"])
    assert args_s.db_command == "schema"


# ---------------------------------------------------------------------------
# handle_db_command — query with format variants
# ---------------------------------------------------------------------------

_MOCK_DF = pd.DataFrame({"col": [1, 2]})

_DB_CLI = "rts_predict.common.db_cli"


@pytest.fixture()
def mock_client() -> MagicMock:
    """Return a DuckDBClient mock whose fetch_df returns _MOCK_DF."""
    m = MagicMock()
    m.__enter__ = MagicMock(return_value=m)
    m.__exit__ = MagicMock(return_value=False)
    m.fetch_df.return_value = _MOCK_DF
    m.tables.return_value = ["table_x", "table_y"]
    return m


def test_handle_db_query_table_format(
    mock_client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    """Table format output must include column header text."""
    parser = _build_parser()
    args = parser.parse_args(["db", "query", "SELECT 1", "--format", "table"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client):
        handle_db_command(args, _DATASETS)

    captured = capsys.readouterr()
    assert "col" in captured.out


def test_handle_db_query_csv_format(
    mock_client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    """CSV format output must include a comma-separated header line."""
    parser = _build_parser()
    args = parser.parse_args(["db", "query", "SELECT 1", "--format", "csv"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client):
        handle_db_command(args, _DATASETS)

    captured = capsys.readouterr()
    assert "col" in captured.out
    # CSV should have a comma or just the column name on its own line
    lines = captured.out.strip().splitlines()
    assert lines[0].strip() == "col"


def test_handle_db_query_json_format(
    mock_client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON format output must be valid JSON containing col values."""
    import json

    parser = _build_parser()
    args = parser.parse_args(["db", "query", "SELECT 1", "--format", "json"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client):
        handle_db_command(args, _DATASETS)

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["col"] == 1


def test_handle_db_tables_prints_list(
    mock_client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    """tables subcommand must print the table names returned by the client."""
    parser = _build_parser()
    args = parser.parse_args(["db", "tables"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client):
        handle_db_command(args, _DATASETS)

    captured = capsys.readouterr()
    assert "table_x" in captured.out
    assert "table_y" in captured.out


def test_handle_db_dataset_flag_selects_config(mock_client: MagicMock) -> None:
    """--dataset flag must cause the correct DatasetConfig to be passed to DuckDBClient."""
    parser = _build_parser()
    args = parser.parse_args(["db", "--dataset", "dataset_b", "tables"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client) as mock_cls:
        handle_db_command(args, _DATASETS)

    # First positional argument to DuckDBClient constructor must be _DS_B
    call_args = mock_cls.call_args
    assert call_args[0][0] is _DS_B


def test_handle_db_schema_prints_columns(
    mock_client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    """schema subcommand must print column/type pairs returned by the client."""
    mock_client.schema.return_value = [("id", "INTEGER"), ("name", "VARCHAR")]
    parser = _build_parser()
    args = parser.parse_args(["db", "schema", "my_table"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client):
        handle_db_command(args, _DATASETS)

    captured = capsys.readouterr()
    assert "id" in captured.out
    assert "name" in captured.out


def test_handle_db_tables_no_tables(
    mock_client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    """tables subcommand must print '(no tables)' when the database is empty."""
    mock_client.tables.return_value = []
    parser = _build_parser()
    args = parser.parse_args(["db", "tables"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client):
        handle_db_command(args, _DATASETS)

    captured = capsys.readouterr()
    assert "(no tables)" in captured.out


def test_format_output_unknown_format_raises() -> None:
    """_format_output must raise ValueError for an unrecognised format string."""
    from rts_predict.common.db_cli import _format_output

    df = pd.DataFrame({"x": [1]})
    with pytest.raises(ValueError, match="Unknown output format"):
        _format_output(df, "xml")


def test_handle_db_schema_no_columns(
    mock_client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    """schema subcommand must print '(no columns)' message when schema is empty."""
    mock_client.schema.return_value = []
    parser = _build_parser()
    args = parser.parse_args(["db", "schema", "ghost_table"])

    with patch(f"{_DB_CLI}.DuckDBClient", return_value=mock_client):
        handle_db_command(args, _DATASETS)

    captured = capsys.readouterr()
    assert "ghost_table" in captured.out
