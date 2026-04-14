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
#     display_name: .venv
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
from pathlib import Path

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging
from rts_predict.games.sc2.config import REPLAYS_SOURCE_DIR
from rts_predict.games.sc2.datasets.sc2egset.ingestion import (
    load_all_raw_tables,
)

logger = setup_notebook_logging()
logger.info("Source: %s", REPLAYS_SOURCE_DIR)

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
db.con.execute("SET threads = 8")
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
# ## 5. Extract events to Parquet
#
# Extracts gameEvents, trackerEvents, messageEvents from all 22,390
# SC2Replay.json files to zstd-compressed Parquet under:
#   IN_GAME_PARQUET_DIR/gameEvents/batch_*.parquet
#   IN_GAME_PARQUET_DIR/trackerEvents/batch_*.parquet
#   IN_GAME_PARQUET_DIR/messageEvents/batch_*.parquet
#
# Single-pass: each file is read once; events routed to all three
# accumulators in the same batch loop (I/O: 3× reduction vs sequential).
# Columns: filename (relative to raw_dir, I10), loop, evtTypeName, event_data.

# %%
from rts_predict.games.sc2.config import IN_GAME_PARQUET_DIR
from rts_predict.games.sc2.datasets.sc2egset.ingestion import (
    extract_events_to_parquet,
)
event_counts = extract_events_to_parquet(
    REPLAYS_SOURCE_DIR,
    IN_GAME_PARQUET_DIR,
    batch_size=100,
)
print("Event extraction counts:")
for et, n in event_counts.items():
    print(f"  {et}: {n:,} rows")

# %% [markdown]
# ## 6. Register event Parquets as DuckDB views
#
# Creates three views over the per-type Parquet subdirectories.
# Views not tables: the Parquet files are authoritative; no data is duplicated.
# Views persist in the DuckDB file so downstream steps can SQL over events.

# %%
from rts_predict.games.sc2.datasets.sc2egset.ingestion import load_event_views

view_counts = load_event_views(db.con, IN_GAME_PARQUET_DIR)
print("Event view row counts:")
for view_name, n in view_counts.items():
    print(f"  {view_name}: {n:,} rows")

# %% [markdown]
# ## 7. Event view health checks
#
# NULL rates, filename coverage, and event type distribution for all three
# event views. SQL inlined for reproducibility (Invariant I6).

# %%
# NULL rates per event view
event_null_query_template = """
SELECT
    COUNT(*)                       AS total_rows,
    COUNT(*) - COUNT(filename)     AS filename_null,
    COUNT(*) - COUNT(loop)         AS loop_null,
    COUNT(*) - COUNT(evtTypeName)  AS evtTypeName_null,
    COUNT(*) - COUNT(event_data)   AS event_data_null
FROM {view_name}
"""
event_null_results: dict = {}
for view_name in view_counts:
    if view_counts[view_name] == 0:
        print(f"=== {view_name}: no rows — skipping NULL check ===")
        continue
    q = event_null_query_template.format(view_name=view_name)
    df = db.fetch_df(q)
    print(f"=== {view_name} NULL rates ===")
    print(df.to_string(index=False))
    event_null_results[view_name] = df.to_dict(orient="records")[0]

# %%
# Filename coverage: distinct replay files contributing to each event view
# vs total files in replays_meta_raw (orphan detection)
event_coverage_query_template = """
SELECT
    COUNT(DISTINCT e.filename)  AS event_files,
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT e.filename)
        - COUNT(DISTINCT CASE WHEN rm.filename IS NOT NULL
                              THEN e.filename END) AS orphan_event_files
FROM {view_name} e
LEFT JOIN replays_meta_raw rm ON e.filename = rm.filename
"""
event_coverage_results: dict = {}
for view_name in view_counts:
    if view_counts[view_name] == 0:
        continue
    q = event_coverage_query_template.format(view_name=view_name)
    df = db.fetch_df(q)
    print(f"=== {view_name} filename coverage ===")
    print(df.to_string(index=False))
    event_coverage_results[view_name] = df.to_dict(orient="records")[0]

# %%
# Top-10 evtTypeName distribution per event view
event_type_query_template = """
SELECT evtTypeName, COUNT(*) AS event_count
FROM {view_name}
GROUP BY evtTypeName
ORDER BY event_count DESC
LIMIT 10
"""
event_type_dist: dict = {}
for view_name in view_counts:
    if view_counts[view_name] == 0:
        continue
    q = event_type_query_template.format(view_name=view_name)
    df = db.fetch_df(q)
    print(f"=== {view_name} top-10 evtTypeName ===")
    print(df.to_string(index=False))
    event_type_dist[view_name] = df.to_dict(orient="records")

# %% [markdown]
# ## 8. Write artifacts

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
    "event_extraction_counts": event_counts,
    "event_views_created": view_counts,
    "event_views_health": {
        view_name: {
            "null_rates": event_null_results.get(view_name, {}),
            "filename_coverage": event_coverage_results.get(view_name, {}),
            "top10_evt_types": event_type_dist.get(view_name, []),
        }
        for view_name in view_counts
    },
}

artifact_path = artifacts_dir / "01_02_02_duckdb_ingestion.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2, default=str))
logger.info("Artifact written: %s", artifact_path)

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
    "- **game_events_raw / tracker_events_raw / message_events_raw**: DuckDB",
    "  views over per-type Parquet subdirectories. Single-pass extraction;",
    "  columns: filename (relative, I10), loop, evtTypeName, event_data.",
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

# %%
# Event extraction counts + view registration
md_lines.extend([
    "",
    "## Event extraction\n",
    "",
    "| Event type | Rows extracted | DuckDB view |",
    "|------------|---------------|-------------|",
])
_et_to_view = {"gameEvents": "game_events_raw", "trackerEvents": "tracker_events_raw",
               "messageEvents": "message_events_raw"}
for et, n in event_counts.items():
    md_lines.append(f"| {et} | {n:,} | {_et_to_view[et]} |")

# %%
# Event view health checks (Invariant I6)
for view_name in view_counts:
    if view_name not in event_null_results:
        continue
    md_lines.extend([
        "",
        f"## {view_name} health checks\n",
        "",
        "### NULL rates\n",
        "",
        "```sql",
        event_null_query_template.format(view_name=view_name).strip(),
        "```\n",
        "",
        db.fetch_df(event_null_query_template.format(view_name=view_name)).to_markdown(
            index=False
        ),
        "",
        "### Filename coverage\n",
        "",
        "```sql",
        event_coverage_query_template.format(view_name=view_name).strip(),
        "```\n",
        "",
        db.fetch_df(
            event_coverage_query_template.format(view_name=view_name)
        ).to_markdown(index=False),
        "",
        "### Top-10 evtTypeName\n",
        "",
        "```sql",
        event_type_query_template.format(view_name=view_name).strip(),
        "```\n",
        "",
        db.fetch_df(
            event_type_query_template.format(view_name=view_name)
        ).to_markdown(index=False),
    ])

md_path = artifacts_dir / "01_02_02_duckdb_ingestion.md"
md_path.write_text("\n".join(md_lines))
logger.info("Report written: %s", md_path)

# %%
db.close()
