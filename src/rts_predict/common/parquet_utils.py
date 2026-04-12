from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


def discover_parquet_schema(file_path: Path) -> dict:
    """Discover the schema of a single Parquet file.

    Reads only the schema metadata (no row data) via
    ``pyarrow.parquet.read_schema()``.

    Args:
        file_path: Path to the Parquet file.

    Returns:
        Dict with keys:
            - ``columns``: list of dicts, each with ``name`` (str),
              ``arrow_type`` (str), and ``nullable`` (bool).
            - ``total_columns``: int — number of columns in the schema.
    """
    schema = pq.read_schema(file_path)
    columns = []
    for i in range(len(schema)):
        field = schema.field(i)
        columns.append({
            "name": field.name,
            "arrow_type": str(field.type),
            "nullable": field.nullable,
        })
    return {
        "columns": columns,
        "total_columns": len(columns),
    }


def _schemas_match(schema_a: dict, schema_b: dict) -> tuple[bool, list[str]]:
    """Compare two per-file schema dicts for structural equality.

    Args:
        schema_a: Schema dict from ``discover_parquet_schema()``.
        schema_b: Schema dict from ``discover_parquet_schema()``.

    Returns:
        Tuple of (all_same: bool, variant_columns: list[str]).
        ``variant_columns`` lists column names that differ in type or
        presence between the two schemas.
    """
    cols_a = {c["name"]: c for c in schema_a["columns"]}
    cols_b = {c["name"]: c for c in schema_b["columns"]}
    all_names = set(cols_a) | set(cols_b)
    variant: list[str] = []
    for name in sorted(all_names):
        if name not in cols_a or name not in cols_b:
            variant.append(name)
        elif cols_a[name]["arrow_type"] != cols_b[name]["arrow_type"]:
            variant.append(name)
    return (len(variant) == 0, variant)


def discover_parquet_schemas(file_paths: list[Path]) -> dict:
    """Discover and compare schemas across multiple Parquet files.

    Calls ``discover_parquet_schema()`` on each file and checks whether all
    files share the same schema.  Files that fail to read are logged as
    warnings and skipped.

    Args:
        file_paths: List of Parquet file paths to inspect.

    Returns:
        Dict with keys:
            - ``schemas``: list of per-file schema dicts (same structure as
              ``discover_parquet_schema()`` output), in the same order as
              ``file_paths`` (failed files are omitted).
            - ``all_files_same_schema``: bool — ``True`` when every file has
              an identical set of columns and types.
            - ``variant_columns``: list[str] — column names that differ
              across at least two files.  Empty when
              ``all_files_same_schema`` is ``True``.
            - ``files_checked``: int — number of files successfully read.
    """
    schemas: list[dict] = []
    for path in file_paths:
        try:
            schemas.append(discover_parquet_schema(path))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping %s: %s", path, exc)

    if len(schemas) <= 1:
        return {
            "schemas": schemas,
            "all_files_same_schema": True,
            "variant_columns": [],
            "files_checked": len(schemas),
        }

    variant_set: set[str] = set()
    reference = schemas[0]
    for other in schemas[1:]:
        _, diff = _schemas_match(reference, other)
        variant_set.update(diff)

    all_same = len(variant_set) == 0
    return {
        "schemas": schemas,
        "all_files_same_schema": all_same,
        "variant_columns": sorted(variant_set),
        "files_checked": len(schemas),
    }


def discover_csv_schema(file_path: Path, sample_rows: int = 50) -> dict:
    """Discover the schema of a CSV file by sampling the first N rows.

    Reads the header plus up to ``sample_rows`` rows via
    ``pd.read_csv(nrows=sample_rows)`` and infers column types from the
    resulting DataFrame.

    Args:
        file_path: Path to the CSV file.
        sample_rows: Maximum number of data rows to read for type inference.
            Defaults to 50.

    Returns:
        Dict with keys:
            - ``columns``: list of dicts, each with ``name`` (str),
              ``inferred_type`` (str, pandas dtype name), and
              ``nullable`` (bool — ``True`` when the sampled column
              contains at least one NaN value).
            - ``total_columns``: int — number of columns.
            - ``sample_rows_read``: int — actual number of rows read
              (may be less than ``sample_rows`` for small files).
    """
    df = pd.read_csv(file_path, nrows=sample_rows)
    columns = []
    for col in df.columns:
        columns.append({
            "name": col,
            "inferred_type": str(df[col].dtype),
            "nullable": bool(df[col].isna().any()),
        })
    return {
        "columns": columns,
        "total_columns": len(columns),
        "sample_rows_read": len(df),
    }
