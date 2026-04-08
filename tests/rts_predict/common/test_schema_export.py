"""Tests for rts_predict.common.schema_export.export_schemas.

The export utility's load-bearing claim is comment preservation across re-runs.
Any regression in that contract invalidates the YAML schemas as a source of truth.
"""
from pathlib import Path

import duckdb
import pytest
import yaml

from rts_predict.common.schema_export import export_schemas


class TestExportSchemasFileCount:
    """export_schemas writes exactly N+1 files for a DB with N tables."""

    def test_export_schemas_writes_one_yaml_per_table(
        self, two_table_db: Path, tmp_path: Path
    ) -> None:
        """A DB with N tables produces N+1 files (N tables + _index.yaml)."""
        out_dir = tmp_path / "schemas"
        written = export_schemas(two_table_db, out_dir)

        # two_table_db has 2 tables → 2 YAMLs + 1 _index.yaml = 3 files
        assert len(written) == 3
        names = {p.name for p in written}
        assert "events.yaml" in names
        assert "players.yaml" in names
        assert "_index.yaml" in names


class TestExportSchemasYamlStructure:
    """Per-table YAML files have all required top-level and column-level fields."""

    def test_export_schemas_yaml_contains_required_fields(
        self, two_table_db: Path, tmp_path: Path
    ) -> None:
        """Each per-table YAML has table, database, generated_at, row_count, columns, notes."""
        out_dir = tmp_path / "schemas"
        export_schemas(two_table_db, out_dir)

        for yaml_path in out_dir.glob("*.yaml"):
            if yaml_path.name == "_index.yaml":
                continue
            data = yaml.safe_load(yaml_path.read_text())
            assert isinstance(data, dict), f"{yaml_path.name} is not a dict"
            for key in ("table", "database", "generated_at", "row_count", "columns", "notes"):
                assert key in data, f"Missing key '{key}' in {yaml_path.name}"

    def test_export_schemas_columns_have_required_fields(
        self, two_table_db: Path, tmp_path: Path
    ) -> None:
        """Each column dict has name, type, nullable, primary_key, comment."""
        out_dir = tmp_path / "schemas"
        export_schemas(two_table_db, out_dir)

        required_col_keys = {"name", "type", "nullable", "primary_key", "comment"}
        for yaml_path in out_dir.glob("*.yaml"):
            if yaml_path.name == "_index.yaml":
                continue
            data = yaml.safe_load(yaml_path.read_text())
            for col in data["columns"]:
                assert isinstance(col, dict), f"Column is not a dict in {yaml_path.name}"
                missing = required_col_keys - set(col.keys())
                assert not missing, (
                    f"Missing column keys {missing} in {yaml_path.name}: {col}"
                )


class TestCommentPreservation:
    """Comment preservation is the load-bearing contract of export_schemas."""

    def test_export_schemas_preserves_column_comments_across_runs(
        self, two_table_db: Path, tmp_path: Path
    ) -> None:
        """Hand-written comment survives a re-export of the same schema.

        Arrange: export once → hand-edit a comment → export again.
        Assert: the hand-edited comment is still present after the second run.
        """
        out_dir = tmp_path / "schemas"
        export_schemas(two_table_db, out_dir)

        # Hand-edit the players.yaml comment for the 'name' column.
        players_yaml = out_dir / "players.yaml"
        data = yaml.safe_load(players_yaml.read_text())
        for col in data["columns"]:
            if col["name"] == "name":
                col["comment"] = "Human-written: player display name."
        players_yaml.write_text(
            yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )

        # Second export — preserve_comments=True (default).
        export_schemas(two_table_db, out_dir)

        result = yaml.safe_load(players_yaml.read_text())
        for col in result["columns"]:
            if col["name"] == "name":
                assert col["comment"] == "Human-written: player display name.", (
                    "Column comment was overwritten during re-export."
                )

    def test_export_schemas_preserves_table_notes_across_runs(
        self, two_table_db: Path, tmp_path: Path
    ) -> None:
        """Hand-written table-level notes survive a re-export."""
        out_dir = tmp_path / "schemas"
        export_schemas(two_table_db, out_dir)

        events_yaml = out_dir / "events.yaml"
        data = yaml.safe_load(events_yaml.read_text())
        data["notes"] = "Hand-written notes: one row per scoring event per player."
        events_yaml.write_text(
            yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )

        export_schemas(two_table_db, out_dir)

        result = yaml.safe_load(events_yaml.read_text())
        assert result["notes"] == "Hand-written notes: one row per scoring event per player.", (
            "Table notes were overwritten during re-export."
        )

    def test_export_schemas_drops_comment_for_renamed_column_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When a column is renamed, its old comment is dropped and logged at WARNING.

        Simulates a schema change by creating a DB with column 'score', exporting,
        writing a comment for 'score', then creating a NEW DB where 'score' is
        renamed to 'points'. The second export on the new DB should warn about
        the dropped comment.
        """
        import logging

        # First DB: has column 'score'
        db_v1 = tmp_path / "v1.duckdb"
        con = duckdb.connect(str(db_v1))
        con.execute("CREATE TABLE results (player_id INTEGER, score INTEGER)")
        con.close()

        out_dir = tmp_path / "schemas"
        export_schemas(db_v1, out_dir)

        # Hand-write a comment for 'score'.
        results_yaml = out_dir / "results.yaml"
        data = yaml.safe_load(results_yaml.read_text())
        for col in data["columns"]:
            if col["name"] == "score":
                col["comment"] = "Points earned, will be renamed to 'points'."
        results_yaml.write_text(
            yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )

        # Second DB: 'score' renamed to 'points' — simulates a schema migration.
        db_v2 = tmp_path / "v2.duckdb"
        con = duckdb.connect(str(db_v2))
        con.execute("CREATE TABLE results (player_id INTEGER, points INTEGER)")
        con.close()

        with caplog.at_level(logging.WARNING, logger="rts_predict.common.schema_export"):
            export_schemas(db_v2, out_dir)

        assert any(
            "score" in record.message and "renamed or dropped" in record.message
            for record in caplog.records
        ), "Expected WARNING about dropped 'score' comment, got: " + str(caplog.records)


class TestEdgeCases:
    """Edge case handling for empty databases and index file correctness."""

    def test_export_schemas_raises_on_empty_database(self, tmp_path: Path) -> None:
        """An empty DB is a hard failure, not a silent zero-file write."""
        empty_db = tmp_path / "empty.duckdb"
        con = duckdb.connect(str(empty_db))
        con.close()  # No tables created.

        out_dir = tmp_path / "schemas"
        with pytest.raises(ValueError, match="zero tables"):
            export_schemas(empty_db, out_dir)

    def test_export_schemas_raises_on_missing_db(self, tmp_path: Path) -> None:
        """FileNotFoundError when db_path does not exist."""
        missing = tmp_path / "does_not_exist.duckdb"
        with pytest.raises(FileNotFoundError):
            export_schemas(missing, tmp_path / "out")

    def test_export_schemas_index_yaml_lists_all_tables(
        self, two_table_db: Path, tmp_path: Path
    ) -> None:
        """The _index.yaml summary contains every table that has a per-table file."""
        out_dir = tmp_path / "schemas"
        export_schemas(two_table_db, out_dir)

        index = yaml.safe_load((out_dir / "_index.yaml").read_text())
        assert isinstance(index, dict)
        assert "tables" in index
        table_names = {entry["table"] for entry in index["tables"]}
        assert "players" in table_names
        assert "events" in table_names
        assert index["n_tables"] == 2

    def test_export_schemas_index_has_pk_true_for_pk_table(
        self, two_table_db: Path, tmp_path: Path
    ) -> None:
        """The _index.yaml correctly marks has_pk=True for the players table."""
        out_dir = tmp_path / "schemas"
        export_schemas(two_table_db, out_dir)

        index = yaml.safe_load((out_dir / "_index.yaml").read_text())
        by_table = {entry["table"]: entry for entry in index["tables"]}
        assert by_table["players"]["has_pk"] is True
        assert by_table["events"]["has_pk"] is False
