"""Game-agnostic DuckDB client and dataset configuration.

Zero imports from any game package — import direction is strictly
``common`` <- ``sc2`` / ``aoe2``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

# ── Module-level resource defaults ────────────────────────────────────────────
_DEFAULT_MEMORY_LIMIT: str = "24GB"
_DEFAULT_THREADS: int = 4
_DEFAULT_MAX_TEMP_DIR_SIZE: str = "150GB"


@dataclass(frozen=True)
class DatasetConfig:
    """Immutable descriptor for a single dataset stored in DuckDB.

    Args:
        name: Short identifier (e.g. ``"sc2egset"``).
        db_file: Absolute path to the ``.duckdb`` file.
        temp_dir: Directory DuckDB may use for spill-to-disk scratch files.
        description: Human-readable one-liner for help text / log messages.
    """

    name: str
    db_file: Path
    temp_dir: Path
    description: str


class DuckDBClient:
    """Context manager wrapping a DuckDB connection with resource pragmas.

    Example::

        cfg = DatasetConfig(name="my_db", db_file=Path("my.duckdb"),
                            temp_dir=Path("/tmp/duckdb"), description="demo")
        with DuckDBClient(cfg, read_only=True) as client:
            df = client.fetch_df("SELECT 1 AS x")

    Args:
        dataset: Dataset descriptor — provides ``db_file`` and ``temp_dir``.
        memory_limit: DuckDB ``memory_limit`` pragma value.
        threads: DuckDB ``threads`` pragma value.
        max_temp_dir_size: DuckDB ``max_temp_directory_size`` pragma value.
        read_only: Open the connection in read-only mode when ``True``.
    """

    def __init__(
        self,
        dataset: DatasetConfig,
        *,
        memory_limit: str = _DEFAULT_MEMORY_LIMIT,
        threads: int = _DEFAULT_THREADS,
        max_temp_dir_size: str = _DEFAULT_MAX_TEMP_DIR_SIZE,
        read_only: bool = False,
    ) -> None:
        self._dataset = dataset
        self._memory_limit = memory_limit
        self._threads = threads
        self._max_temp_dir_size = max_temp_dir_size
        self._read_only = read_only
        self._con: duckdb.DuckDBPyConnection | None = None

    # ── Context manager protocol ───────────────────────────────────────────

    def open(self) -> "DuckDBClient":
        """Open the DuckDB connection explicitly.

        Equivalent to entering the context manager block. Use this when
        the client is constructed outside a ``with`` block (e.g. from
        ``get_notebook_db``).

        Returns:
            Self, so callers can chain or assign.

        Raises:
            RuntimeError: If the connection is already open.
        """
        if self._con is not None:
            raise RuntimeError(
                f"DuckDBClient.open() called on an already-open connection: {self._dataset.db_file}"
            )
        self._dataset.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._dataset.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(
            "Opening DuckDB connection: %s (read_only=%s)",
            self._dataset.db_file,
            self._read_only,
        )
        self._con = duckdb.connect(str(self._dataset.db_file), read_only=self._read_only)
        self._apply_pragmas()
        return self

    def __enter__(self) -> "DuckDBClient":
        """Open the DuckDB connection and apply resource pragmas.

        Returns:
            The ``DuckDBClient`` instance (``self``).
        """
        return self.open()

    def __exit__(self, *exc: object) -> None:
        """Close the DuckDB connection.

        Args:
            *exc: Exception info forwarded from the ``with`` block (ignored).
        """
        self.close()

    def close(self) -> None:
        """Close the DuckDB connection explicitly.

        Safe to call multiple times. Use this when the client is obtained
        outside a ``with`` block (e.g. from ``get_notebook_db``).
        """
        if self._con is not None:
            self._con.close()
            logger.debug("DuckDB connection closed: %s", self._dataset.db_file)
            self._con = None

    # ── Public API ─────────────────────────────────────────────────────────

    @property
    def con(self) -> duckdb.DuckDBPyConnection:
        """The underlying DuckDB connection.

        Raises:
            RuntimeError: If accessed outside the ``with`` block.
        """
        if self._con is None:
            raise RuntimeError("DuckDBClient.con accessed outside the context manager block.")
        return self._con

    def query(self, sql: str, params: list[object] | None = None) -> duckdb.DuckDBPyRelation:
        """Execute *sql* and return a lazy DuckDB relation.

        Args:
            sql: SQL statement to execute.
            params: Optional positional parameters for ``?`` placeholders.

        Returns:
            A ``DuckDBPyRelation`` that can be consumed with ``.df()`` etc.
        """
        if params:
            return self.con.execute(sql, params)  # type: ignore[return-value]
        return self.con.sql(sql)

    def fetch_df(self, sql: str, params: list[object] | None = None) -> pd.DataFrame:
        """Execute *sql* and return results as a ``pandas.DataFrame``.

        Args:
            sql: SQL statement to execute.
            params: Optional positional parameters for ``?`` placeholders.

        Returns:
            Query results as a ``pandas.DataFrame``.
        """
        rel = self.query(sql, params)
        return rel.df()

    def tables(self) -> list[str]:
        """Return a sorted list of table names in the connected database.

        Returns:
            Sorted list of table name strings.
        """
        df = self.fetch_df("SHOW TABLES")
        if df.empty:
            return []
        return sorted(df["name"].tolist())

    def schema(self, table_name: str) -> list[tuple[str, str]]:
        """Return column name / type pairs for *table_name*.

        Args:
            table_name: Name of an existing table.

        Returns:
            List of ``(column_name, column_type)`` tuples in definition order.
        """
        df = self.fetch_df(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = ? ORDER BY ordinal_position",
            [table_name],
        )
        return list(zip(df["column_name"].tolist(), df["data_type"].tolist()))

    def row_counts(self) -> dict[str, int]:
        """Return a mapping of ``{table_name: row_count}`` for all tables.

        Returns:
            Dictionary mapping each table name to its row count.
        """
        result: dict[str, int] = {}
        for table in self.tables():
            df = self.fetch_df(f'SELECT COUNT(*) AS n FROM "{table}"')  # noqa: S608
            result[table] = int(df["n"].iloc[0])
        return result

    # ── Private helpers ────────────────────────────────────────────────────

    def _apply_pragmas(self) -> None:
        """Apply DuckDB resource-limit pragmas after connecting."""
        assert self._con is not None
        self._con.execute(f"SET memory_limit = '{self._memory_limit}'")
        self._con.execute(f"SET threads = {self._threads}")
        self._con.execute(f"SET max_temp_directory_size = '{self._max_temp_dir_size}'")
        try:
            self._con.execute(f"SET temp_directory = '{self._dataset.temp_dir}'")
        except duckdb.NotImplementedException:
            # DuckDB raises this when the temp directory has already been used
            # in the current process (e.g. a previous kernel cell spilled to disk).
            # The existing temp dir remains in effect — this is safe to ignore.
            logger.warning(
                "Could not set temp_directory to '%s': already in use. "
                "DuckDB will continue using its current temp directory.",
                self._dataset.temp_dir,
            )
        logger.debug(
            "DuckDB pragmas applied — memory_limit=%s, threads=%d, "
            "max_temp_directory_size=%s, temp_directory=%s",
            self._memory_limit,
            self._threads,
            self._max_temp_dir_size,
            self._dataset.temp_dir,
        )
