from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from rts_predict.common.parquet_utils import (
    discover_csv_schema,
    discover_parquet_schema,
    discover_parquet_schemas,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def parquet_file_a(tmp_path: Path) -> Path:
    """Parquet file with 4 columns and 5 rows, mixed types including nullable."""
    table = pa.table(
        {
            "id": pa.array([1, 2, 3, 4, 5], type=pa.int32()),
            "name": pa.array(["alice", "bob", "carol", None, "eve"], type=pa.string()),
            "score": pa.array([1.1, 2.2, 3.3, 4.4, 5.5], type=pa.float64()),
            "active": pa.array([True, False, True, True, False], type=pa.bool_()),
        }
    )
    path = tmp_path / "schema_a.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture()
def parquet_file_b(tmp_path: Path) -> Path:
    """Parquet file with different schema (extra column, different type)."""
    table = pa.table(
        {
            "id": pa.array([10, 20], type=pa.int64()),  # different int type
            "name": pa.array(["x", "y"], type=pa.string()),
            "extra": pa.array([99, 100], type=pa.int32()),  # new column
        }
    )
    path = tmp_path / "schema_b.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture()
def csv_file(tmp_path: Path) -> Path:
    """CSV file with 3 columns and 10 rows including a nullable column."""
    df = pd.DataFrame(
        {
            "player_id": list(range(10)),
            "rating": [1500.0, 1600.5, None, 1700.0, 1800.0,
                       1900.0, 2000.0, 2100.0, 2200.0, 2300.0],
            "league": ["bronze", "silver", "gold", "platinum", "diamond",
                       "master", "grandmaster", "bronze", "silver", "gold"],
        }
    )
    path = tmp_path / "players.csv"
    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# discover_parquet_schema tests
# ---------------------------------------------------------------------------


def test_discover_parquet_schema_returns_column_names(parquet_file_a: Path) -> None:
    result = discover_parquet_schema(parquet_file_a)
    names = [c["name"] for c in result["columns"]]
    assert names == ["id", "name", "score", "active"]


def test_discover_parquet_schema_returns_arrow_types(parquet_file_a: Path) -> None:
    result = discover_parquet_schema(parquet_file_a)
    type_map = {c["name"]: c["arrow_type"] for c in result["columns"]}
    assert type_map["id"] == "int32"
    assert type_map["score"] == "double"
    assert type_map["active"] == "bool"


def test_discover_parquet_schema_total_columns(parquet_file_a: Path) -> None:
    result = discover_parquet_schema(parquet_file_a)
    assert result["total_columns"] == 4


def test_discover_parquet_schema_nullable_field(parquet_file_a: Path) -> None:
    """Arrow marks all fields nullable by default unless explicitly set otherwise."""
    result = discover_parquet_schema(parquet_file_a)
    col_map = {c["name"]: c for c in result["columns"]}
    # name column was written with a None — Arrow schema reflects nullable=True
    assert col_map["name"]["nullable"] is True


def test_discover_parquet_schema_no_duckdb_keys(parquet_file_a: Path) -> None:
    result = discover_parquet_schema(parquet_file_a)
    for col in result["columns"]:
        assert "duckdb_type" not in col
        assert "proposed_duckdb_type" not in col


# ---------------------------------------------------------------------------
# discover_parquet_schemas tests
# ---------------------------------------------------------------------------


def test_discover_parquet_schemas_same_file_twice(parquet_file_a: Path) -> None:
    result = discover_parquet_schemas([parquet_file_a, parquet_file_a])
    assert result["all_files_same_schema"] is True
    assert result["variant_columns"] == []
    assert result["files_checked"] == 2
    assert len(result["schemas"]) == 2


def test_discover_parquet_schemas_mismatching_schemas(
    parquet_file_a: Path, parquet_file_b: Path
) -> None:
    result = discover_parquet_schemas([parquet_file_a, parquet_file_b])
    assert result["all_files_same_schema"] is False
    assert len(result["variant_columns"]) > 0
    # "id" type differs (int32 vs int64), "score", "active" are absent in B,
    # "extra" is absent in A — all should be variant
    variant_set = set(result["variant_columns"])
    assert "extra" in variant_set or "score" in variant_set or "id" in variant_set


def test_discover_parquet_schemas_variant_columns_populated(
    parquet_file_a: Path, parquet_file_b: Path
) -> None:
    result = discover_parquet_schemas([parquet_file_a, parquet_file_b])
    assert isinstance(result["variant_columns"], list)
    assert len(result["variant_columns"]) >= 1


def test_discover_parquet_schemas_single_file(parquet_file_a: Path) -> None:
    result = discover_parquet_schemas([parquet_file_a])
    assert result["all_files_same_schema"] is True
    assert result["variant_columns"] == []
    assert result["files_checked"] == 1


def test_discover_parquet_schemas_empty_list() -> None:
    result = discover_parquet_schemas([])
    assert result["all_files_same_schema"] is True
    assert result["variant_columns"] == []
    assert result["files_checked"] == 0
    assert result["schemas"] == []


def test_discover_parquet_schemas_skips_bad_file(
    tmp_path: Path, parquet_file_a: Path
) -> None:
    bad_file = tmp_path / "bad.parquet"
    bad_file.write_text("not a parquet file")
    result = discover_parquet_schemas([bad_file, parquet_file_a])
    # Bad file is skipped; only parquet_file_a is read
    assert result["files_checked"] == 1


# ---------------------------------------------------------------------------
# discover_csv_schema tests
# ---------------------------------------------------------------------------


def test_discover_csv_schema_column_names(csv_file: Path) -> None:
    result = discover_csv_schema(csv_file)
    names = [c["name"] for c in result["columns"]]
    assert names == ["player_id", "rating", "league"]


def test_discover_csv_schema_inferred_types(csv_file: Path) -> None:
    result = discover_csv_schema(csv_file)
    type_map = {c["name"]: c["inferred_type"] for c in result["columns"]}
    assert "int" in type_map["player_id"]
    assert "float" in type_map["rating"]
    # pandas >= 2 may report "object" or "str" for string columns
    assert type_map["league"] in ("object", "str")


def test_discover_csv_schema_total_columns(csv_file: Path) -> None:
    result = discover_csv_schema(csv_file)
    assert result["total_columns"] == 3


def test_discover_csv_schema_nullable_column(csv_file: Path) -> None:
    result = discover_csv_schema(csv_file)
    col_map = {c["name"]: c for c in result["columns"]}
    assert col_map["rating"]["nullable"] is True
    assert col_map["player_id"]["nullable"] is False


def test_discover_csv_schema_sample_rows_respected(tmp_path: Path) -> None:
    """When file has more rows than sample_rows, only sample_rows are read."""
    df = pd.DataFrame({"x": range(200)})
    path = tmp_path / "large.csv"
    df.to_csv(path, index=False)

    result_50 = discover_csv_schema(path, sample_rows=50)
    assert result_50["sample_rows_read"] == 50

    result_10 = discover_csv_schema(path, sample_rows=10)
    assert result_10["sample_rows_read"] == 10


def test_discover_csv_schema_small_file_reads_all(tmp_path: Path) -> None:
    """When file has fewer rows than sample_rows, all rows are returned."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    path = tmp_path / "small.csv"
    df.to_csv(path, index=False)

    result = discover_csv_schema(path, sample_rows=50)
    assert result["sample_rows_read"] == 3


def test_discover_csv_schema_no_duckdb_keys(csv_file: Path) -> None:
    result = discover_csv_schema(csv_file)
    for col in result["columns"]:
        assert "duckdb_type" not in col
        assert "proposed_duckdb_type" not in col
