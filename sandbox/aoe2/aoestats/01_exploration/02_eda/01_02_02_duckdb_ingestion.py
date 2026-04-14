# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_02_02 -- DuckDB Ingestion: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** aoestats
# **Question:** Materialise raw data into persistent DuckDB tables using the
# strategies determined by 01_02_01 (union_by_name for variant columns).
# **Invariants applied:** #6 (reproducibility), #7 (provenance), #9 (step scope)
# **Step scope:** ingest
# **Prerequisites:** 01_02_01 artifacts on disk, notebook re-executed with outputs

# %%
import json

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOESTATS_RAW_DIR
from rts_predict.games.aoe2.datasets.aoestats.ingestion import (
    load_all_raw_tables,
)

logger = setup_notebook_logging()
logger.info("Source: %s", AOESTATS_RAW_DIR)

# %% [markdown]
# ## 1. Ingest all DuckDB tables
#
# Calls `load_all_raw_tables` which creates:
# - `matches_raw` -- from 172 weekly match Parquet files (union_by_name)
# - `players_raw` -- from 171 weekly player Parquet files (union_by_name)
# - `overviews_raw` -- singleton overview.json

# %%
db = get_notebook_db("aoe2", "aoestats", read_only=False)
counts = load_all_raw_tables(db.con, AOESTATS_RAW_DIR)
print("Ingestion counts:")
for table, n in counts.items():
    print(f"  {table}: {n:,} rows")

# %% [markdown]
# ## 2. Post-ingestion validation: DESCRIBE tables

# %%
for table in counts:
    print(f"\n=== DESCRIBE {table} ===")
    desc_df = db.fetch_df(f'DESCRIBE "{table}"')
    print(desc_df.to_string(index=False))

# %% [markdown]
# ## 3. NULL rates on key fields

# %%
# matches_raw NULL rates
match_null_query = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    COUNT(*) - COUNT(map) AS map_null,
    COUNT(*) - COUNT(started_timestamp) AS started_timestamp_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM matches_raw
"""
print("=== matches_raw NULL rates ===")
print(db.fetch_df(match_null_query).to_string(index=False))

# %%
# players_raw NULL rates
player_null_query = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    COUNT(*) - COUNT(profile_id) AS profile_id_null,
    COUNT(*) - COUNT(winner) AS winner_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM players_raw
"""
print("=== players_raw NULL rates ===")
print(db.fetch_df(player_null_query).to_string(index=False))

# %%
# overviews_raw row count
print(f"overviews_raw: {counts.get('overviews_raw', 'N/A'):,} rows")

# %%
db.close()

# %% [markdown]
# ## 4. Write artifacts

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
artifacts_dir.mkdir(parents=True, exist_ok=True)

artifact_data = {
    "step": "01_02_02",
    "dataset": "aoestats",
    "tables_created": {
        table: {"row_count": n} for table, n in counts.items()
    },
}

artifact_path = artifacts_dir / "01_02_02_duckdb_ingestion.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2))
logger.info("Artifact written: %s", artifact_path)

# %%
md_lines = [
    "# Step 01_02_02 -- DuckDB Ingestion: aoestats\n",
    "",
    "## Tables created\n",
    "",
    "| Table | Rows |",
    "|-------|------|",
]
for table, n in counts.items():
    md_lines.append(f"| {table} | {n:,} |")
md_lines.extend([
    "",
    "## Ingestion strategy\n",
    "",
    "- `matches_raw` and `players_raw`: `union_by_name = true` to handle",
    "  variant columns across weekly files.",
    "- `overviews_raw`: `read_json_auto` on singleton overview.json.",
    "- All tables include `filename` provenance column.",
    "",
    "## SQL used\n",
    "",
    "See `src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py` for all",
    "SQL constants.",
])

md_path = artifacts_dir / "01_02_02_duckdb_ingestion.md"
md_path.write_text("\n".join(md_lines))
logger.info("Report written: %s", md_path)
