"""Generic DuckDB schema export utility.

Produces one YAML file per table (or view) in a DuckDB database, plus an
``_index.yaml`` summary file.  Human-written ``comment`` (per-column) and
``notes`` (per-table) fields are preserved across re-runs when the corresponding
column or table still exists in the database.

Typical usage
-------------
    from pathlib import Path
    from rts_predict.common.schema_export import export_schemas

    written = export_schemas(
        db_path=Path("path/to/db.duckdb"),
        out_dir=Path("path/to/schemas/"),
    )
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import yaml

logger = logging.getLogger(__name__)

# ── SQL constants ─────────────────────────────────────────────────────────────

_LIST_TABLES_QUERY = (
    "SELECT table_name FROM information_schema.tables"
    " WHERE table_schema = 'main'"
    " ORDER BY table_name"
)

_TABLE_INFO_QUERY = "PRAGMA table_info('{table}')"
_ROW_COUNT_QUERY = "SELECT COUNT(*) FROM \"{table}\""

# Keys that are always re-derived from the live database (never preserved).
_GENERATED_KEYS: frozenset[str] = frozenset(
    {"table", "database", "generated_at", "row_count"}
)

# Required top-level keys in each per-table YAML, in canonical order.
_TABLE_YAML_KEYS: list[str] = [
    "table",
    "database",
    "generated_at",
    "row_count",
    "columns",
    "notes",
]

# Required keys in each column dict, in canonical order.
_COLUMN_KEYS: list[str] = ["name", "type", "nullable", "primary_key", "comment"]


# ── Internal helpers ──────────────────────────────────────────────────────────


def _now_utc() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_existing_comments(yaml_path: Path) -> tuple[dict[str, str], str]:
    """Parse an existing per-table YAML and extract human-written fields.

    Args:
        yaml_path: Path to an existing per-table YAML file.

    Returns:
        A tuple of:
        - column_comments: mapping of column name → comment string.
        - table_notes: the table-level ``notes`` string (empty string if absent).
    """
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}, ""

    column_comments: dict[str, str] = {}
    for col in raw.get("columns", []):
        if isinstance(col, dict) and "name" in col:
            column_comments[col["name"]] = col.get("comment", "")

    table_notes: str = raw.get("notes", "") or ""
    return column_comments, table_notes


def _warn_dropped_comments(
    old_comments: dict[str, str],
    new_columns: list[str],
    table: str,
) -> None:
    """Log a WARNING for every column whose comment will be dropped.

    A comment is dropped when its column no longer exists in the live schema.

    Args:
        old_comments: Column name → comment from the previous YAML.
        new_columns: Column names present in the live schema.
        table: Table name, used in the log message.
    """
    new_set = set(new_columns)
    for col_name, comment in old_comments.items():
        if col_name not in new_set and comment:
            logger.warning(
                "Column '%s.%s' was renamed or dropped — comment lost: %r",
                table,
                col_name,
                comment,
            )


def _build_column_dict(
    row: tuple[Any, ...],
    comment: str,
) -> dict[str, Any]:
    """Convert a PRAGMA table_info row to a canonical column dict.

    Args:
        row: A row from ``PRAGMA table_info``:
             (cid, name, type, notnull, dflt_value, pk).
        comment: Human-written comment string (may be empty).

    Returns:
        Ordered dict with keys: name, type, nullable, primary_key, comment.
    """
    _cid, name, col_type, notnull, _dflt, pk = row
    return {
        "name": name,
        "type": col_type,
        "nullable": not bool(notnull),
        "primary_key": bool(pk),
        "comment": comment,
    }


def _build_table_yaml(
    table: str,
    db_path: Path,
    columns: list[dict[str, Any]],
    row_count: int,
    notes: str,
    generated_at: str,
) -> dict[str, Any]:
    """Assemble the canonical dict for a per-table YAML.

    Args:
        table: Table name.
        db_path: Path to the source DuckDB file (stored as a string in the YAML).
        columns: List of column dicts built by :func:`_build_column_dict`.
        row_count: Advisory row count at generation time.
        notes: Table-level notes string.
        generated_at: UTC timestamp string.

    Returns:
        Ordered dict matching the canonical YAML structure.
    """
    return {
        "table": table,
        "database": str(db_path),
        "generated_at": generated_at,
        "row_count": row_count,
        "columns": columns,
        "notes": notes,
    }


def _build_index_entry(
    table: str,
    row_count: int,
    columns: list[dict[str, Any]],
    notes: str,
) -> dict[str, Any]:
    """Build one entry for the ``_index.yaml`` table list.

    Args:
        table: Table name.
        row_count: Advisory row count.
        columns: Column dicts (used to derive ``n_columns`` and ``has_pk``).
        notes: Table-level notes string.

    Returns:
        Dict with keys: table, row_count, n_columns, has_pk, notes_first_line.
    """
    has_pk = any(col["primary_key"] for col in columns)
    notes_first_line = (notes.splitlines()[0] if notes else "")
    return {
        "table": table,
        "row_count": row_count,
        "n_columns": len(columns),
        "has_pk": has_pk,
        "notes_first_line": notes_first_line,
    }


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write ``data`` to ``path`` using ``yaml.safe_dump``.

    Args:
        path: Target file path (parent directory must exist).
        data: Data to serialise.
    """
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


# ── Public API ────────────────────────────────────────────────────────────────


def export_schemas(
    db_path: Path,
    out_dir: Path,
    *,
    preserve_comments: bool = True,
) -> list[Path]:
    """Dump every table in ``db_path`` to YAML files under ``out_dir``.

    Produces one YAML file per table plus an ``_index.yaml`` summary file.
    The schema (column names, types, nullability, primary key) is always
    re-derived from the live database — never preserved from disk. Only
    the human-written ``comment`` (per-column) and ``notes`` (per-table) string
    fields are preserved across re-runs, and only when the column or table
    they are attached to still exists.

    Args:
        db_path: Path to a DuckDB database file. Opened read-only.
        out_dir: Target directory for the YAML files. Created if missing.
        preserve_comments: If True (default), read existing per-table YAMLs
            in ``out_dir`` (if present) and preserve any human-written ``comment``
            fields per column and ``notes`` field per table when re-emitting.
            If False, any existing files are overwritten without preservation.

    Returns:
        List of paths to the YAML files written, in deterministic order:
        per-table files alphabetically, then ``_index.yaml`` last.

    Raises:
        FileNotFoundError: If ``db_path`` does not exist.
        ValueError: If ``db_path`` exists but contains zero tables in the ``main``
            schema. An empty database is a hard failure — schema export against
            an empty DB is meaningless and almost certainly a bug.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    logger.info("export_schemas: db_path=%s, out_dir=%s", db_path, out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables: list[str] = [
            row[0] for row in con.execute(_LIST_TABLES_QUERY).fetchall()
        ]
    finally:
        con.close()

    if not tables:
        raise ValueError(
            f"Database '{db_path}' contains zero tables in the 'main' schema. "
            "An empty database is not a valid export target."
        )

    generated_at = _now_utc()
    written_paths: list[Path] = []
    index_entries: list[dict[str, Any]] = []

    for table in tables:
        yaml_path = out_dir / f"{table}.yaml"

        # Load previous comments/notes before connecting for schema read.
        old_comments: dict[str, str] = {}
        old_notes: str = ""
        if preserve_comments and yaml_path.exists():
            old_comments, old_notes = _load_existing_comments(yaml_path)

        # Open a fresh read-only connection per table to keep resource scope tight.
        con = duckdb.connect(str(db_path), read_only=True)
        try:
            pragma_rows = con.execute(
                _TABLE_INFO_QUERY.format(table=table)
            ).fetchall()
            row_count: int = con.execute(
                _ROW_COUNT_QUERY.format(table=table)
            ).fetchone()[0]  # type: ignore[index]
        finally:
            con.close()

        column_names = [row[1] for row in pragma_rows]
        if preserve_comments and old_comments:
            _warn_dropped_comments(old_comments, column_names, table)

        columns = [
            _build_column_dict(row, old_comments.get(row[1], ""))
            for row in pragma_rows
        ]

        table_notes = old_notes if preserve_comments else ""

        table_data = _build_table_yaml(
            table=table,
            db_path=db_path,
            columns=columns,
            row_count=row_count,
            notes=table_notes,
            generated_at=generated_at,
        )
        _write_yaml(yaml_path, table_data)
        written_paths.append(yaml_path)
        logger.info("Wrote schema: %s", yaml_path)

        index_entries.append(_build_index_entry(table, row_count, columns, table_notes))

    # Write _index.yaml last.
    index_path = out_dir / "_index.yaml"
    index_data: dict[str, Any] = {
        "database": str(db_path),
        "generated_at": generated_at,
        "n_tables": len(tables),
        "advisory_note": "row_count values are accurate at generation time only.",
        "tables": index_entries,
    }
    _write_yaml(index_path, index_data)
    written_paths.append(index_path)
    logger.info("Wrote index: %s", index_path)

    logger.info("export_schemas: wrote %d files to %s", len(written_paths), out_dir)
    return written_paths
