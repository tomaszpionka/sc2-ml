"""Tests for src/rts_predict/common/json_utils.py."""

import json
from pathlib import Path

from rts_predict.common.json_utils import (
    _propose_duckdb_type,
    build_column_list,
    build_schema_table,
    classify_value,
    discover_json_schema,
    get_json_keypaths,
)


class TestProposeDuckdbType:
    """Tests for _propose_duckdb_type()."""

    def test_bool_only(self) -> None:
        """Single bool type maps to BOOLEAN."""
        assert _propose_duckdb_type({"bool"}) == "BOOLEAN"

    def test_int_only(self) -> None:
        """Single int type maps to BIGINT."""
        assert _propose_duckdb_type({"int"}) == "BIGINT"

    def test_float_only(self) -> None:
        """Single float type maps to DOUBLE."""
        assert _propose_duckdb_type({"float"}) == "DOUBLE"

    def test_str_only(self) -> None:
        """Single str type maps to VARCHAR."""
        assert _propose_duckdb_type({"str"}) == "VARCHAR"

    def test_nonetype_only(self) -> None:
        """All-None edge case maps to VARCHAR."""
        assert _propose_duckdb_type({"NoneType"}) == "VARCHAR"

    def test_int_and_none(self) -> None:
        """Nullable numeric: int + NoneType -> BIGINT."""
        assert _propose_duckdb_type({"int", "NoneType"}) == "BIGINT"

    def test_str_and_none(self) -> None:
        """Nullable string: str + NoneType -> VARCHAR."""
        assert _propose_duckdb_type({"str", "NoneType"}) == "VARCHAR"

    def test_mixed_scalars(self) -> None:
        """Mixed scalar types fall back to VARCHAR."""
        assert _propose_duckdb_type({"int", "str"}) == "VARCHAR"

    def test_dict_present(self) -> None:
        """dict type forces JSON."""
        assert _propose_duckdb_type({"dict", "int"}) == "JSON"

    def test_list_present(self) -> None:
        """list type forces JSON."""
        assert _propose_duckdb_type({"list"}) == "JSON"

    def test_dict_only(self) -> None:
        """Pure nested dict -> JSON."""
        assert _propose_duckdb_type({"dict"}) == "JSON"

    def test_empty_set(self) -> None:
        """Edge case: no observations maps to VARCHAR."""
        assert _propose_duckdb_type(set()) == "VARCHAR"


class TestDiscoverJsonSchema:
    """Tests for discover_json_schema()."""

    def test_empty_paths_list(self) -> None:
        """Empty input returns empty list."""
        assert discover_json_schema([]) == []

    def test_single_file_all_scalars(self, tmp_path: Path) -> None:
        """Single file with all scalar types produces correct profiles."""
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"a": 1, "b": "x", "c": True, "d": 1.5}))
        result = discover_json_schema([f])
        assert len(result) == 4
        by_key = {p.key: p for p in result}
        assert by_key["a"].proposed_duckdb_type == "BIGINT"
        assert by_key["b"].proposed_duckdb_type == "VARCHAR"
        assert by_key["c"].proposed_duckdb_type == "BOOLEAN"
        assert by_key["d"].proposed_duckdb_type == "DOUBLE"
        for p in result:
            assert p.is_scalar is True
            assert p.nullable is False
            assert p.frequency == 1
            assert p.total_samples == 1

    def test_single_file_nested(self, tmp_path: Path) -> None:
        """Nested dict and list produce JSON type and is_scalar=False."""
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"a": {"nested": 1}, "b": [1, 2]}))
        result = discover_json_schema([f])
        assert len(result) == 2
        by_key = {p.key: p for p in result}
        assert by_key["a"].is_scalar is False
        assert by_key["a"].proposed_duckdb_type == "JSON"
        assert by_key["b"].is_scalar is False
        assert by_key["b"].proposed_duckdb_type == "JSON"

    def test_multiple_files_same_keys(self, tmp_path: Path) -> None:
        """Keys present in all files have frequency == total_samples and nullable=False."""
        f1 = tmp_path / "f1.json"
        f2 = tmp_path / "f2.json"
        f1.write_text(json.dumps({"a": 1}))
        f2.write_text(json.dumps({"a": 2}))
        result = discover_json_schema([f1, f2])
        assert len(result) == 1
        assert result[0].frequency == 2
        assert result[0].total_samples == 2
        assert result[0].nullable is False

    def test_multiple_files_disjoint_keys(self, tmp_path: Path) -> None:
        """Keys present in only some files are marked nullable."""
        f1 = tmp_path / "f1.json"
        f2 = tmp_path / "f2.json"
        f1.write_text(json.dumps({"a": 1}))
        f2.write_text(json.dumps({"b": "x"}))
        result = discover_json_schema([f1, f2])
        assert len(result) == 2
        by_key = {p.key: p for p in result}
        assert by_key["a"].frequency == 1
        assert by_key["a"].nullable is True
        assert by_key["b"].frequency == 1
        assert by_key["b"].nullable is True

    def test_mixed_types_same_key(self, tmp_path: Path) -> None:
        """Key with int and str values across files produces VARCHAR."""
        f1 = tmp_path / "f1.json"
        f2 = tmp_path / "f2.json"
        f1.write_text(json.dumps({"a": 1}))
        f2.write_text(json.dumps({"a": "x"}))
        result = discover_json_schema([f1, f2])
        assert len(result) == 1
        assert result[0].observed_types == {"int", "str"}
        assert result[0].proposed_duckdb_type == "VARCHAR"

    def test_empty_json_object(self, tmp_path: Path) -> None:
        """File with empty dict has no keys, returns empty list."""
        f = tmp_path / "empty.json"
        f.write_text(json.dumps({}))
        result = discover_json_schema([f])
        assert result == []

    def test_non_object_root_skipped(self, tmp_path: Path) -> None:
        """Non-dict root (array) is skipped, returns empty list."""
        f = tmp_path / "array.json"
        f.write_text(json.dumps([1, 2, 3]))
        result = discover_json_schema([f])
        assert result == []

    def test_invalid_json_skipped(self, tmp_path: Path) -> None:
        """Parse error causes file to be skipped."""
        f = tmp_path / "bad.json"
        f.write_text("not json {{")
        result = discover_json_schema([f])
        assert result == []

    def test_max_sample_values(self, tmp_path: Path) -> None:
        """Sample values are capped at max_sample_values."""
        files = []
        for i in range(4):
            f = tmp_path / f"f{i}.json"
            f.write_text(json.dumps({"a": i + 1}))
            files.append(f)
        result = discover_json_schema(files, max_sample_values=2)
        assert len(result[0].sample_values) == 2

    def test_sorted_by_key(self, tmp_path: Path) -> None:
        """Keys are returned in alphabetical order."""
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"z": 1, "a": 2, "m": 3}))
        result = discover_json_schema([f])
        assert [p.key for p in result] == ["a", "m", "z"]

    def test_sample_values_non_scalar_stored_as_type_string(
        self, tmp_path: Path
    ) -> None:
        """Non-scalar sample values are stored as '<type>' strings."""
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"a": {"x": 1}}))
        result = discover_json_schema([f])
        assert result[0].sample_values == ["<dict>"]


class TestClassifyValue:
    """Tests for classify_value()."""

    def test_none(self) -> None:
        assert classify_value(None) == "null"

    def test_bool(self) -> None:
        assert classify_value(True) == "bool"
        assert classify_value(False) == "bool"

    def test_int(self) -> None:
        assert classify_value(42) == "int"

    def test_float(self) -> None:
        assert classify_value(3.14) == "float"

    def test_str(self) -> None:
        assert classify_value("hello") == "str"

    def test_dict(self) -> None:
        assert classify_value({"a": 1, "b": 2}) == "struct(2 keys)"

    def test_empty_dict(self) -> None:
        assert classify_value({}) == "struct(0 keys)"

    def test_list_of_ints(self) -> None:
        assert classify_value([1, 2, 3]) == "list(int)"

    def test_list_of_dicts(self) -> None:
        assert classify_value([{"a": 1}]) == "list(struct(1 keys))"

    def test_empty_list(self) -> None:
        assert classify_value([]) == "list(empty)"

    def test_nested_list(self) -> None:
        assert classify_value([[1, 2]]) == "list(list(int))"

    def test_bool_before_int(self) -> None:
        """bool is a subclass of int in Python — must be checked first."""
        assert classify_value(True) == "bool"
        assert classify_value(1) == "int"


class TestBuildColumnList:
    """Tests for build_column_list()."""

    def test_basic(self) -> None:
        schema = {
            "columns": [
                {"name": "id", "arrow_type": "int64", "nullable": False},
                {"name": "name", "arrow_type": "string", "nullable": True},
            ]
        }
        result = build_column_list(schema)
        assert len(result) == 2
        assert result[0] == {"name": "id", "physical_type": "int64", "nullable": False}
        assert result[1] == {"name": "name", "physical_type": "string", "nullable": True}

    def test_custom_type_key(self) -> None:
        schema = {
            "columns": [
                {"name": "x", "inferred_type": "VARCHAR"},
            ]
        }
        result = build_column_list(schema, col_type_key="inferred_type")
        assert result[0]["physical_type"] == "VARCHAR"

    def test_fallback_to_inferred_type(self) -> None:
        schema = {
            "columns": [
                {"name": "x", "inferred_type": "BIGINT"},
            ]
        }
        result = build_column_list(schema)
        assert result[0]["physical_type"] == "BIGINT"

    def test_empty_columns(self) -> None:
        assert build_column_list({"columns": []}) == []

    def test_missing_columns_key(self) -> None:
        assert build_column_list({}) == []


class TestBuildSchemaTable:
    """Tests for build_schema_table()."""

    def test_basic(self) -> None:
        columns = [
            {"name": "id", "physical_type": "int64", "nullable": False},
            {"name": "val", "physical_type": "string", "nullable": True},
        ]
        lines = build_schema_table(columns)
        assert lines[0] == "| Column | Type | Nullable |"
        assert lines[1] == "|--------|------|----------|"
        assert lines[2] == "| `id` | int64 | False |"
        assert lines[3] == "| `val` | string | True |"

    def test_custom_type_key(self) -> None:
        columns = [{"name": "x", "arrow_type": "float64"}]
        lines = build_schema_table(columns, type_key="arrow_type")
        assert "float64" in lines[2]

    def test_empty_columns(self) -> None:
        lines = build_schema_table([])
        assert len(lines) == 2  # header + separator only


class TestGetJsonKeypaths:
    """Tests for the existing get_json_keypaths() function."""

    def test_flat_object(self, tmp_path: Path) -> None:
        """Flat JSON object returns top-level key paths."""
        f = tmp_path / "flat.json"
        f.write_text(json.dumps({"a": 1, "b": "x"}))
        result = get_json_keypaths(f)
        assert result == ["a", "b"]

    def test_nested_object(self, tmp_path: Path) -> None:
        """Nested dict produces dotted path."""
        f = tmp_path / "nested.json"
        f.write_text(json.dumps({"a": {"b": 1}}))
        result = get_json_keypaths(f)
        assert result == ["a.b"]

    def test_array(self, tmp_path: Path) -> None:
        """Array value produces bracket notation."""
        f = tmp_path / "array.json"
        f.write_text(json.dumps({"a": [1, 2]}))
        result = get_json_keypaths(f)
        assert "a[]" in result
