"""Shared fixtures for rts_predict.common tests."""
from collections.abc import Generator
from pathlib import Path

import duckdb
import pytest


@pytest.fixture()
def two_table_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a minimal DuckDB file with two tables for schema export tests.

    Tables:
        - ``players`` — (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL)
        - ``events``  — (player_id INTEGER, score INTEGER)

    The database is written to ``tmp_path / "test.duckdb"`` and opened
    read-write only during fixture setup; after yield the file is used
    read-only by the tests.

    Yields:
        Path to the DuckDB file.
    """
    db_path = tmp_path / "test.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        con.execute(
            "CREATE TABLE players (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL)"
        )
        con.execute("INSERT INTO players VALUES (1, 'Alice'), (2, 'Bob')")
        con.execute("CREATE TABLE events (player_id INTEGER, score INTEGER)")
        con.execute("INSERT INTO events VALUES (1, 100), (2, 200), (1, 150)")
    finally:
        con.close()
    yield db_path
