"""DuckDB view orchestration — minimal safe subset for Phase 01.

Only ``_RAW_ENRICHED_VIEW_QUERY`` and ``create_raw_enriched_view`` are retained
here. They depend only on the ``raw`` table (filename column) which is always
present after ingestion, and add no schema assumptions beyond that.

All other functions (``get_matches_dataframe``, ``assign_series_ids``) that
assume the ``matches_flat`` view schema have been quarantined in
``_legacy/processing.py`` pending Phase 01 schema validation.
"""

import logging

import duckdb

logger = logging.getLogger(__name__)

# ── SQL query constants ───────────────────────────────────────────────────────

_RAW_ENRICHED_VIEW_QUERY = """
    CREATE OR REPLACE VIEW raw_enriched AS
    SELECT
        *,
        split_part(filename, '/', -3) AS tournament_dir,
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM raw
"""


def create_raw_enriched_view(con: duckdb.DuckDBPyConnection) -> None:
    """Create the raw_enriched view with tournament_dir and replay_id columns.

    Args:
        con: Open DuckDB connection pointing to a database containing the
            ``raw`` table produced by ingestion.
    """
    con.execute(_RAW_ENRICHED_VIEW_QUERY)
    logger.info("Created raw_enriched view.")
