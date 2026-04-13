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
# # Step 01_02_02 -- DuckDB Ingestion: sc2egset
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** sc2egset
# **Question:** Materialise raw data into persistent DuckDB tables using the
# three-stream strategy determined by 01_02_01.
# **Invariants applied:** #6 (reproducibility), #7 (provenance), #9 (step scope), #10 (relative filenames)
# **Step scope:** ingest
# **Prerequisites:** 01_02_01 artifacts on disk, notebook re-executed with outputs

# %%
import json
import logging
from pathlib import Path

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir
from rts_predict.games.sc2.config import REPLAYS_SOURCE_DIR
from rts_predict.games.sc2.datasets.sc2egset.ingestion import (
    load_all_raw_tables,
)

logging.basicConfig(level=logging.INFO)

# %% [markdown]
# ## 1. Ingest all DuckDB tables
#
# Calls `load_all_raw_tables` which creates:
# - `replays_meta_raw` -- one row per replay, STRUCT columns, ToonPlayerDescMap as VARCHAR
# - `replay_players_raw` -- normalised one row per (replay, player)
# - `map_aliases_raw` -- foreign-to-english map names with tournament provenance
#
# All filename columns store paths relative to `raw_dir` (Invariant I10).

# %%
db = get_notebook_db("sc2", "sc2egset", read_only=False)
# Reduce threads for the 209 GB read_json_auto CTAS to limit memory pressure.
# DuckDB default is 4 threads; 2 halves the peak concurrent file-buffer RSS.
# Restored to default after ingestion completes.
db.con.execute("SET threads = 2")
counts = load_all_raw_tables(db.con, REPLAYS_SOURCE_DIR)
db.con.execute("SET threads = 4")
print("Ingestion counts:")
for table, n in counts.items():
    print(f"  {table}: {n:,} rows")

# %% [markdown]
# ## 2. Post-ingestion validation: DESCRIBE tables

# %%
describe_results = {}
for table in counts:
    print(f"\n=== DESCRIBE {table} ===")
    desc_df = db.fetch_df(f'DESCRIBE "{table}"')
    print(desc_df.to_string(index=False))
    describe_results[table] = desc_df.to_dict(orient="records")

# %% [markdown]
# ## 3. NULL rates on key fields

# %%
# replays_meta_raw: check NULL rates for metadata STRUCT columns
null_check_query = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(details) AS details_null,
    COUNT(*) - COUNT(header) AS header_null,
    COUNT(*) - COUNT(initData) AS initData_null,
    COUNT(*) - COUNT(metadata) AS metadata_null,
    COUNT(*) - COUNT(ToonPlayerDescMap) AS tpdm_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM replays_meta_raw
"""
print("=== replays_meta_raw NULL rates ===")
null_df = db.fetch_df(null_check_query)
print(null_df.to_string(index=False))

# %%
# replay_players_raw: check NULL rates for key player fields
player_null_query = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(toon_id) AS toon_id_null,
    COUNT(*) - COUNT(nickname) AS nickname_null,
    COUNT(*) - COUNT(MMR) AS MMR_null,
    COUNT(*) - COUNT(race) AS race_null,
    COUNT(*) - COUNT(result) AS result_null,
    COUNT(*) - COUNT(APM) AS APM_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM replay_players_raw
"""
print("=== replay_players_raw NULL rates ===")
player_null_df = db.fetch_df(player_null_query)
print(player_null_df.to_string(index=False))

# %%
# map_aliases_raw: check NULL rates
alias_null_query = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(tournament) AS tournament_null,
    COUNT(*) - COUNT(foreign_name) AS foreign_name_null,
    COUNT(*) - COUNT(english_name) AS english_name_null,
    COUNT(DISTINCT tournament) AS distinct_tournaments
FROM map_aliases_raw
"""
print("=== map_aliases_raw NULL rates ===")
alias_null_df = db.fetch_df(alias_null_query)
print(alias_null_df.to_string(index=False))

# %% [markdown]
# ## 4. ToonPlayerDescMap VARCHAR verification

# %%
# Verify ToonPlayerDescMap is stored as VARCHAR (JSON text blob)
tpdm_type_query = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'replays_meta_raw' AND column_name = 'ToonPlayerDescMap'
"""
print("=== ToonPlayerDescMap type ===")
tpdm_type_df = db.fetch_df(tpdm_type_query)
print(tpdm_type_df.to_string(index=False))

# %% [markdown]
# ## 4b. Cross-table integrity
#
# Verify that every file in `replay_players_raw` has a matching entry in
# `replays_meta_raw` (and vice versa). Orphan files in either direction
# indicate ingestion mismatches.

# %%
cross_table_query = """
SELECT
    COUNT(DISTINCT rp.filename) AS player_files,
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT rp.filename)
        - COUNT(DISTINCT CASE WHEN rm.filename IS NOT NULL
                              THEN rp.filename END) AS orphan_player_files
FROM replay_players_raw rp
LEFT JOIN replays_meta_raw rm ON rp.filename = rm.filename
"""
print("=== Cross-table integrity (players -> meta) ===")
cross_df = db.fetch_df(cross_table_query)
print(cross_df.to_string(index=False))

# %%
# Reverse direction: replays_meta_raw rows with no replay_players_raw entries
reverse_cross_query = """
SELECT
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT rm.filename)
        - COUNT(DISTINCT CASE WHEN rp.filename IS NOT NULL
                              THEN rm.filename END) AS orphan_meta_files
FROM replays_meta_raw rm
LEFT JOIN replay_players_raw rp ON rm.filename = rp.filename
"""
print("=== Cross-table integrity (meta -> players) ===")
reverse_cross_df = db.fetch_df(reverse_cross_query)
print(reverse_cross_df.to_string(index=False))

# %% [markdown]
# ## 4c. Player count per replay
#
# Distribution of how many players each replay file contains.
# Expected: mostly 2 (1v1 replays). Non-1v1 or parse anomalies will show here.

# %%
player_count_query = """
SELECT players_per_replay, COUNT(*) AS replay_count
FROM (
    SELECT filename, COUNT(*) AS players_per_replay
    FROM replay_players_raw
    GROUP BY filename
)
GROUP BY players_per_replay
ORDER BY players_per_replay
"""
print("=== Player count per replay distribution ===")
player_count_df = db.fetch_df(player_count_query)
print(player_count_df.to_string(index=False))

# %% [markdown]
# ## 4d. map_aliases_raw dedup check
#
# All 70 tournament mapping files are loaded for provenance tracing.
# This check profiles the uniqueness of the data.

# %%
dedup_query = """
SELECT
    COUNT(DISTINCT foreign_name) AS unique_foreign,
    COUNT(DISTINCT english_name) AS unique_english,
    COUNT(DISTINCT tournament) AS unique_tournaments,
    COUNT(*) AS total_rows
FROM map_aliases_raw
"""
print("=== map_aliases_raw dedup profile ===")
dedup_df = db.fetch_df(dedup_query)
print(dedup_df.to_string(index=False))

# %% [markdown]
# ## 5. Extract events to Parquet (optional -- SSD-dependent)
#
# This step extracts gameEvents, trackerEvents, messageEvents to
# zstd-compressed Parquet. If SSD space is insufficient, skip this step.
# NOTE: When implemented, `extract_events_to_parquet` must use
# `str(fpath.relative_to(raw_dir))` for the filename column (I10).

# %%
# Uncomment to run event extraction:
# from rts_predict.games.sc2.config import IN_GAME_PARQUET_DIR
# from rts_predict.games.sc2.datasets.sc2egset.ingestion import (
#     extract_events_to_parquet,
# )
# event_counts = extract_events_to_parquet(
#     REPLAYS_SOURCE_DIR,
#     IN_GAME_PARQUET_DIR,
#     batch_size=100,
# )
# print("Event extraction counts:")
# for et, n in event_counts.items():
#     print(f"  {et}: {n:,} rows")

# %% [markdown]
# ## 6. Write artifacts

# %%
reports_dir = get_reports_dir("sc2", "sc2egset")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
artifacts_dir.mkdir(parents=True, exist_ok=True)

cross_integrity = cross_df.to_dict(orient="records")[0]
cross_integrity["orphan_meta_files"] = int(
    reverse_cross_df["orphan_meta_files"].iloc[0]
)

artifact_data = {
    "step": "01_02_02",
    "dataset": "sc2egset",
    "ingestion_strategy": "three-stream; see 01_02_01",
    "tables_created": {
        table: {
            "row_count": n,
            "schema": describe_results.get(table, []),
        }
        for table, n in counts.items()
    },
    "null_rates": {
        "replays_meta_raw": null_df.to_dict(orient="records")[0],
        "replay_players_raw": player_null_df.to_dict(orient="records")[0],
        "map_aliases_raw": alias_null_df.to_dict(orient="records")[0],
    },
    "cross_table_integrity": cross_integrity,
    "players_per_replay_distribution": player_count_df.to_dict(orient="records"),
    "map_aliases_dedup": dedup_df.to_dict(orient="records")[0],
    "tpdm_type": tpdm_type_df.to_dict(orient="records")[0],
}

artifact_path = artifacts_dir / "01_02_02_duckdb_ingestion.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2, default=str))
print(f"Artifact written: {artifact_path}")

# %%
md_lines = [
    "# Step 01_02_02 -- DuckDB Ingestion: sc2egset\n",
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
    "Three-stream extraction (see 01_02_01 design artifact):",
    "- **replays_meta_raw**: DuckDB table, one row per replay. Metadata as",
    "  STRUCT columns, ToonPlayerDescMap as VARCHAR (JSON text blob).",
    "  Event arrays excluded. filename stores relative path from raw_dir.",
    "- **replay_players_raw**: DuckDB table, normalised from ToonPlayerDescMap.",
    "  One row per (replay, player) with all player fields extracted.",
    "  filename stores relative path from raw_dir.",
    "- **map_aliases_raw**: DuckDB table, all tournament mapping files with",
    "  tournament provenance column. filename stores relative path from raw_dir.",
    "- **Events**: Parquet extraction (optional, SSD-dependent, deferred).",
])

# %%
# NULL rates section with inline SQL (Invariant I6)
md_lines.extend([
    "",
    "## NULL rates\n",
    "",
    "### replays_meta_raw\n",
    "",
    "```sql",
    null_check_query.strip(),
    "```\n",
    "",
    null_df.to_markdown(index=False),
    "",
    "### replay_players_raw\n",
    "",
    "```sql",
    player_null_query.strip(),
    "```\n",
    "",
    player_null_df.to_markdown(index=False),
    "",
    "### map_aliases_raw\n",
    "",
    "```sql",
    alias_null_query.strip(),
    "```\n",
    "",
    alias_null_df.to_markdown(index=False),
])

# %%
# ToonPlayerDescMap type + cross-table integrity (Invariant I6)
md_lines.extend([
    "",
    "## ToonPlayerDescMap type verification\n",
    "",
    "```sql",
    tpdm_type_query.strip(),
    "```\n",
    "",
    tpdm_type_df.to_markdown(index=False),
    "",
    "## Cross-table integrity\n",
    "",
    "### Players -> Meta\n",
    "",
    "```sql",
    cross_table_query.strip(),
    "```\n",
    "",
    cross_df.to_markdown(index=False),
    "",
    "### Meta -> Players (reverse)\n",
    "",
    "```sql",
    reverse_cross_query.strip(),
    "```\n",
    "",
    reverse_cross_df.to_markdown(index=False),
])

# %%
# Player count + map aliases dedup (Invariant I6)
md_lines.extend([
    "",
    "## Player count per replay\n",
    "",
    "```sql",
    player_count_query.strip(),
    "```\n",
    "",
    player_count_df.to_markdown(index=False),
    "",
    "## map_aliases_raw dedup profile\n",
    "",
    "```sql",
    dedup_query.strip(),
    "```\n",
    "",
    dedup_df.to_markdown(index=False),
])

md_path = artifacts_dir / "01_02_02_duckdb_ingestion.md"
md_path.write_text("\n".join(md_lines))
print(f"Report written: {md_path}")

# %%
db.close()
