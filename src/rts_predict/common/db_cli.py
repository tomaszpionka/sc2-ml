"""Shared argparse helpers for the ``db`` CLI subcommand group.

Both the SC2 and AoE2 CLIs call :func:`add_db_subparser` and
:func:`handle_db_command`; neither game package duplicates this wiring.
"""

from __future__ import annotations

import argparse
import io
import logging

import pandas as pd
from tabulate import tabulate  # type: ignore[import-untyped]

from rts_predict.common.db import DatasetConfig, DuckDBClient

logger = logging.getLogger(__name__)

_FORMAT_CHOICES: list[str] = ["table", "csv", "json"]
_DEFAULT_FORMAT: str = "table"


def add_db_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    datasets: dict[str, DatasetConfig],
    default_dataset: str,
) -> None:
    """Register a ``db`` sub-parser onto an existing subparsers action.

    The ``db`` sub-parser exposes three sub-sub-commands:

    * ``query <sql> [--format csv|json|table]``
    * ``tables``
    * ``schema <table>``

    Args:
        subparsers: The ``_SubParsersAction`` returned by
            ``parser.add_subparsers()``.
        datasets: Mapping of dataset name → :class:`DatasetConfig` for
            ``--dataset`` choices.
        default_dataset: The dataset name selected when ``--dataset`` is
            omitted.
    """
    db_parser = subparsers.add_parser("db", help="Ad-hoc DuckDB operations.")
    db_parser.add_argument(
        "--dataset",
        choices=list(datasets.keys()),
        default=default_dataset,
        help=(
            f"Dataset to connect to (default: {default_dataset!r}). "
            f"Available: {', '.join(datasets.keys())}."
        ),
    )

    db_sub = db_parser.add_subparsers(dest="db_command", metavar="DB_COMMAND")
    db_sub.required = True

    # -- query --
    query_parser = db_sub.add_parser("query", help="Execute a SQL query.")
    query_parser.add_argument("sql", help="SQL statement to run (read-only).")
    query_parser.add_argument(
        "--format",
        dest="output_format",
        choices=_FORMAT_CHOICES,
        default=_DEFAULT_FORMAT,
        help="Output format (default: table).",
    )

    # -- tables --
    db_sub.add_parser("tables", help="List all tables in the database.")

    # -- schema --
    schema_parser = db_sub.add_parser(
        "schema", help="Show column names and types for a table."
    )
    schema_parser.add_argument("table", help="Table name to inspect.")


def handle_db_command(
    args: argparse.Namespace,
    datasets: dict[str, DatasetConfig],
) -> None:
    """Dispatch a parsed ``db`` sub-command to the appropriate handler.

    Args:
        args: Parsed namespace produced by the ``db`` sub-parser.
        datasets: Same mapping that was passed to :func:`add_db_subparser`.
    """
    dataset = datasets[args.dataset]
    logger.debug("db command: %s, dataset: %s", args.db_command, dataset.name)

    with DuckDBClient(dataset, read_only=True) as client:
        if args.db_command == "tables":
            _handle_tables(client)
        elif args.db_command == "schema":
            _handle_schema(client, args.table)
        elif args.db_command == "query":
            fmt = getattr(args, "output_format", _DEFAULT_FORMAT)
            _handle_query(client, args.sql, fmt)


# ── Private helpers ────────────────────────────────────────────────────────────


def _handle_tables(client: DuckDBClient) -> None:
    """Print the list of tables in the connected database.

    Args:
        client: An open :class:`DuckDBClient` instance.
    """
    names = client.tables()
    if not names:
        print("(no tables)")
        return
    df = pd.DataFrame({"table": names})
    print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))


def _handle_schema(client: DuckDBClient, table_name: str) -> None:
    """Print column name / type pairs for *table_name*.

    Args:
        client: An open :class:`DuckDBClient` instance.
        table_name: Name of the table to describe.
    """
    pairs = client.schema(table_name)
    if not pairs:
        print(f"(table {table_name!r} has no columns or does not exist)")
        return
    df = pd.DataFrame(pairs, columns=["column", "type"])
    print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))


def _handle_query(client: DuckDBClient, sql: str, fmt: str) -> None:
    """Execute *sql* and print the result in *fmt* format.

    Args:
        client: An open :class:`DuckDBClient` instance.
        sql: SQL statement to execute (read-only connection).
        fmt: One of ``"table"``, ``"csv"``, or ``"json"``.
    """
    df = client.fetch_df(sql)
    _format_output(df, fmt)


def _format_output(df: pd.DataFrame, fmt: str) -> None:
    """Format *df* and print it to stdout.

    Args:
        df: ``pandas.DataFrame`` to render.
        fmt: One of ``"table"``, ``"csv"``, or ``"json"``.

    Raises:
        ValueError: If *fmt* is not a recognised format string.
    """
    if fmt == "table":
        print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))
    elif fmt == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        print(buf.getvalue(), end="")
    elif fmt == "json":
        print(df.to_json(orient="records", indent=2))
    else:
        raise ValueError(f"Unknown output format: {fmt!r}")
