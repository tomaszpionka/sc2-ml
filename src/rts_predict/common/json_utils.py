from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KeyProfile:
    """Profile of a single root-level JSON key observed across multiple files.

    Attributes:
        key: The key name (root-level only, no nested paths).
        frequency: Number of files where this key was present.
        total_samples: Total number of files sampled.
        observed_types: Set of Python type names observed for this key's
            value (e.g. {"int", "str"}). Type names come from
            ``type(value).__name__``.
        is_scalar: True if ALL observed values are scalar (bool, int,
            float, str, NoneType). False if any value is dict or list.
        proposed_duckdb_type: Suggested DuckDB column type. See
            ``_propose_duckdb_type`` for mapping rules.
        nullable: True if the key was absent in at least one sample
            (frequency < total_samples).
        sample_values: Up to ``max_sample_values`` example values observed
            for this key. For non-scalar values, stores the Python type
            name string instead of the value itself.
    """

    key: str
    frequency: int
    total_samples: int
    observed_types: set[str]
    is_scalar: bool
    proposed_duckdb_type: str
    nullable: bool
    sample_values: list[Any] = field(default_factory=list)


# Type mapping: Python type name -> DuckDB type (used when all observations
# are the same type). This mapping is applied per-key across all sampled files.
_PYTHON_TO_DUCKDB: dict[str, str] = {
    "bool": "BOOLEAN",
    "int": "BIGINT",
    "float": "DOUBLE",
    "str": "VARCHAR",
    "NoneType": "VARCHAR",
}

_SCALAR_TYPE_NAMES: frozenset[str] = frozenset({
    "bool", "int", "float", "str", "NoneType",
})


def _propose_duckdb_type(observed_types: set[str]) -> str:
    """Propose a DuckDB column type from observed Python types.

    Rules (applied in order):
    1. If observed_types contains "dict" or "list" -> "JSON"
    2. If observed_types has exactly one scalar type -> lookup from
       _PYTHON_TO_DUCKDB
    3. If observed_types has "NoneType" plus exactly one other scalar
       type -> use the non-None type's mapping
    4. If observed_types has multiple non-None scalar types -> "VARCHAR"
       (mixed scalars fall back to string)

    Args:
        observed_types: Set of Python type name strings.

    Returns:
        DuckDB type string.
    """
    if "dict" in observed_types or "list" in observed_types:
        return "JSON"
    non_none = observed_types - {"NoneType"}
    if len(non_none) == 0:
        return "VARCHAR"
    if len(non_none) == 1:
        single = next(iter(non_none))
        return _PYTHON_TO_DUCKDB.get(single, "JSON")
    if all(t in _SCALAR_TYPE_NAMES for t in non_none):
        return "VARCHAR"
    return "JSON"


def discover_json_schema(
    paths: list[Path],
    *,
    max_sample_values: int = 3,
) -> list[KeyProfile]:
    """Discover root-level JSON schema across multiple files.

    Opens each file, reads the root-level keys, records value types,
    and produces a KeyProfile per unique key. Only inspects root-level
    keys -- nested structures are recorded as type "dict" or "list"
    without further traversal.

    Args:
        paths: List of JSON file paths to sample. Each file must contain
            a root-level JSON object (dict). Files that fail to parse or
            contain a non-object root are logged as warnings and skipped.
        max_sample_values: Maximum number of example values to collect
            per key. For non-scalar values, the type name string is
            stored instead of the value.

    Returns:
        List of KeyProfile, sorted alphabetically by key name.
        Empty list if paths is empty or all files failed to parse.
    """
    total_samples = 0
    key_data: dict[str, dict[str, Any]] = {}

    for path in paths:
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping %s: %s", path, exc)
            continue

        if not isinstance(result, dict):
            logger.warning(
                "Skipping %s: root is %s, not dict", path, type(result).__name__
            )
            continue

        total_samples += 1

        for key, value in result.items():
            type_name = type(value).__name__
            if key not in key_data:
                key_data[key] = {"types": set(), "count": 0, "samples": []}
            key_data[key]["types"].add(type_name)
            key_data[key]["count"] += 1
            if len(key_data[key]["samples"]) < max_sample_values:
                if type_name in _SCALAR_TYPE_NAMES:
                    key_data[key]["samples"].append(value)
                else:
                    key_data[key]["samples"].append(f"<{type_name}>")

    if total_samples == 0:
        return []

    profiles: list[KeyProfile] = []
    for key in sorted(key_data):
        entry = key_data[key]
        is_scalar = entry["types"].issubset(_SCALAR_TYPE_NAMES)
        proposed_duckdb_type = _propose_duckdb_type(entry["types"])
        nullable = entry["count"] < total_samples
        profiles.append(
            KeyProfile(
                key=key,
                frequency=entry["count"],
                total_samples=total_samples,
                observed_types=entry["types"],
                is_scalar=is_scalar,
                proposed_duckdb_type=proposed_duckdb_type,
                nullable=nullable,
                sample_values=entry["samples"],
            )
        )

    return profiles


def get_json_keypaths(path: str | Path) -> list[str]:
    with open(path) as f:
        data = json.load(f)

    paths: set[str] = set()

    def traverse(node: Any, prefix: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                full = f"{prefix}.{key}" if prefix else key
                traverse(value, full)
        elif isinstance(node, list):
            paths.add(f"{prefix}[]")
            for item in node:
                traverse(item, f"{prefix}[]")
        else:
            paths.add(prefix)

    traverse(data, "")
    return sorted(paths)


def classify_value(v: object) -> str:
    """Return a short type tag for a JSON value, distinguishing nested structures.

    Scalars return their type name ("null", "bool", "int", "float", "str").
    Dicts return "struct(N keys)" with the key count.
    Lists return "list(<inner_type>)" by inspecting the first element,
    or "list(empty)" if the list is empty.

    Args:
        v: A Python value deserialized from JSON.

    Returns:
        Human-readable type tag string.
    """
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, dict):
        return f"struct({len(v)} keys)"
    if isinstance(v, list):
        if not v:
            return "list(empty)"
        inner = classify_value(v[0])
        return f"list({inner})"
    return type(v).__name__


def build_column_list(
    schema_dict: dict[str, Any],
    col_type_key: str = "arrow_type",
) -> list[dict[str, Any]]:
    """Extract a normalized column list from a schema discovery dict.

    Args:
        schema_dict: Dict with a "columns" key containing column metadata.
            Each column dict should have "name" and a type key.
        col_type_key: Key to use for the physical type. Falls back to
            "inferred_type" if the primary key is absent.

    Returns:
        List of dicts with keys: name, physical_type, nullable.
    """
    return [
        {
            "name": c["name"],
            "physical_type": c.get(col_type_key, c.get("inferred_type", "")),
            "nullable": c.get("nullable", False),
        }
        for c in schema_dict.get("columns", [])
    ]


def build_schema_table(
    columns: list[dict[str, Any]],
    type_key: str = "physical_type",
) -> list[str]:
    """Build a Markdown table of column names, types, and nullability.

    Args:
        columns: List of column dicts (as returned by :func:`build_column_list`).
        type_key: Key to read the type from each column dict.

    Returns:
        List of Markdown lines (header + separator + one row per column).
    """
    lines = [
        "| Column | Type | Nullable |",
        "|--------|------|----------|",
    ]
    for c in columns:
        lines.append(
            f"| `{c['name']}` | {c.get(type_key, '')} | {c.get('nullable', '')} |"
        )
    return lines
