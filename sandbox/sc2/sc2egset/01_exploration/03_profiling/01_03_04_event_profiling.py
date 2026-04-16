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
# # Step 01_03_04 -- Event Table Profiling
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** sc2egset
# **Question:** What are the event type distributions, per-replay densities,
# PlayerStats periodicity, UnitBorn unit-type diversity, and event_data JSON
# schemas for the three event views (tracker_events_raw, game_events_raw,
# message_events_raw)?
# **Invariants applied:** #3 (all event views IN_GAME_ONLY), #6 (all SQL
# stored verbatim), #9 (profiling only -- no cleaning, no tables created)
# **Predecessor:** 01_03_03 (Table Utility Assessment -- complete)
# **Type:** Read-only -- no DuckDB writes
#
# **Branch:** feat/sc2egset-01-03-04-event-profiling
# **Date:** 2026-04-15
# **ROADMAP ref:** 01_03_04

# %% [markdown]
# ## Cell 1 -- Imports

# %%
import json

import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 2 -- DuckDB connection and output directories

# %%
conn = get_notebook_db("sc2", "sc2egset")
reports_dir = get_reports_dir("sc2", "sc2egset")

artifact_dir = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
)
artifact_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifact dir: {artifact_dir}")

# Load prior utility artifact for constants (I7, I9)
utility_json_path = artifact_dir / "01_03_03_table_utility.json"
with open(utility_json_path) as f:
    utility = json.load(f)

TRACKER_TOTAL = utility["table_verdicts"]["tracker_events_raw"]["row_count"]
GAME_TOTAL = utility["table_verdicts"]["game_events_raw"]["row_count"]
MESSAGE_TOTAL = utility["table_verdicts"]["message_events_raw"]["row_count"]
TOTAL_REPLAYS = 22390  # From 01_01_01 file inventory

print(f"tracker_events_raw row count (from 01_03_03): {TRACKER_TOTAL}")
print(f"game_events_raw row count (from 01_03_03):    {GAME_TOTAL}")
print(f"message_events_raw row count (from 01_03_03): {MESSAGE_TOTAL}")

sql_queries: dict = {}

# %% [markdown]
# ---
# ## T01 -- Tracker Events Deep Profile (62M rows)

# %% [markdown]
# ### Cell 3 -- Tracker: event type distribution

# %%
sql_queries["tracker_type_distribution"] = """
SELECT evtTypeName, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM tracker_events_raw
GROUP BY evtTypeName ORDER BY cnt DESC
"""

tracker_type_df = conn.con.execute(
    sql_queries["tracker_type_distribution"]
).df()
print("=== Tracker event type distribution ===")
print(tracker_type_df.to_string(index=False))
print(f"\nTotal types: {len(tracker_type_df)}")
print(f"Total events: {tracker_type_df['cnt'].sum():,}")

# Gate check: exact total
assert tracker_type_df["cnt"].sum() == 62_003_411, (
    f"Tracker total mismatch: {tracker_type_df['cnt'].sum()} != 62,003,411"
)

# %% [markdown]
# ### Cell 4 -- Tracker: per-replay event density

# %%
sql_queries["tracker_per_replay_density"] = """
SELECT filename, COUNT(*) AS n_events
FROM tracker_events_raw GROUP BY filename
"""

tracker_density_df = conn.con.execute(
    sql_queries["tracker_per_replay_density"]
).df()

tracker_density_stats = {
    "n_replays": len(tracker_density_df),
    "mean": round(float(tracker_density_df["n_events"].mean()), 1),
    "median": float(tracker_density_df["n_events"].median()),
    "p05": float(tracker_density_df["n_events"].quantile(0.05)),
    "p25": float(tracker_density_df["n_events"].quantile(0.25)),
    "p75": float(tracker_density_df["n_events"].quantile(0.75)),
    "p95": float(tracker_density_df["n_events"].quantile(0.95)),
    "min": int(tracker_density_df["n_events"].min()),
    "max": int(tracker_density_df["n_events"].max()),
}

print("=== Tracker per-replay density ===")
for k, v in tracker_density_stats.items():
    print(f"  {k}: {v}")

# %% [markdown]
# ### Cell 5 -- Tracker: per-replay by type (coverage per event type)

# %%
sql_queries["tracker_per_replay_by_type"] = """
SELECT evtTypeName,
       COUNT(DISTINCT filename) AS n_replays,
       ROUND(100.0 * COUNT(DISTINCT filename) / 22390, 2)
         AS replay_coverage_pct,
       COUNT(*) AS total_events,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT filename), 1)
         AS mean_per_replay
FROM tracker_events_raw GROUP BY evtTypeName ORDER BY total_events DESC
"""

tracker_coverage_df = conn.con.execute(
    sql_queries["tracker_per_replay_by_type"]
).df()
print("=== Tracker event type coverage ===")
print(tracker_coverage_df.to_string(index=False))

# %% [markdown]
# ### Cell 6 -- Tracker: temporal distribution (1000-loop buckets)

# %%
sql_queries["tracker_temporal_distribution"] = """
SELECT (loop / 1000) * 1000 AS loop_bucket, COUNT(*) AS cnt
FROM tracker_events_raw GROUP BY loop_bucket ORDER BY loop_bucket
"""

tracker_temporal_df = conn.con.execute(
    sql_queries["tracker_temporal_distribution"]
).df()
print("=== Tracker temporal distribution (loop buckets) ===")
print(f"Number of buckets: {len(tracker_temporal_df)}")
print(f"Min bucket: {tracker_temporal_df['loop_bucket'].min()}")
print(f"Max bucket: {tracker_temporal_df['loop_bucket'].max()}")
print("\nTop 10 by count:")
print(
    tracker_temporal_df.nlargest(10, "cnt").to_string(index=False)
)

# %% [markdown]
# ### Cell 7 -- Tracker: event_data JSON key sampling (top 5 types)

# %%
top5_tracker_types = tracker_type_df["evtTypeName"].head(5).tolist()
tracker_event_data_keys: dict = {}

for etype in top5_tracker_types:
    sql_key = f"tracker_event_data_sample_{etype}"
    sql_queries[sql_key] = (
        f"SELECT event_data FROM tracker_events_raw "
        f"WHERE evtTypeName = '{etype}' LIMIT 5"
    )
    sample_df = conn.con.execute(sql_queries[sql_key]).df()

    all_keys: set = set()
    for row in sample_df["event_data"]:
        if row and row.strip():
            parsed = json.loads(row)
            if isinstance(parsed, dict):
                all_keys.update(parsed.keys())

    tracker_event_data_keys[etype] = sorted(all_keys)
    print(f"\n{etype} keys ({len(all_keys)}): {sorted(all_keys)}")

# %% [markdown]
# ### Cell 8 -- Tracker: PlayerStats periodicity

# %%
sql_queries["playerstats_periodicity"] = """
WITH ps AS (
    SELECT filename, loop,
           loop - LAG(loop) OVER (
               PARTITION BY filename ORDER BY loop
           ) AS gap
    FROM tracker_events_raw
    WHERE evtTypeName = 'PlayerStats'
)
SELECT gap, COUNT(*) AS cnt
FROM ps WHERE gap IS NOT NULL
GROUP BY gap ORDER BY cnt DESC
"""

periodicity_df = conn.con.execute(
    sql_queries["playerstats_periodicity"]
).df()
print("=== PlayerStats gap distribution ===")
print(periodicity_df.head(20).to_string(index=False))

periodicity_stats = {
    "n_distinct_gaps": len(periodicity_df),
    "total_gap_observations": int(periodicity_df["cnt"].sum()),
    "mode_gap": int(periodicity_df.iloc[0]["gap"]),
    "mode_count": int(periodicity_df.iloc[0]["cnt"]),
    "mode_pct": round(
        100.0 * periodicity_df.iloc[0]["cnt"]
        / periodicity_df["cnt"].sum(), 4
    ),
    "all_gaps": [
        {"gap": int(r["gap"]), "count": int(r["cnt"])}
        for _, r in periodicity_df.iterrows()
    ],
}

print(f"\nDistinct gaps: {periodicity_stats['n_distinct_gaps']}")
print(f"Mode gap: {periodicity_stats['mode_gap']} loops "
      f"({periodicity_stats['mode_pct']}% of observations)")

# Gate check: non-empty
assert len(periodicity_df) > 0, "PlayerStats periodicity is empty"

# %% [markdown]
# ### Cell 9 -- Tracker: UnitBorn unit-type diversity

# %%
sql_queries["unitborn_unit_types"] = """
SELECT json_extract_string(event_data, '$.unitTypeName') AS unit_type,
       COUNT(*) AS cnt
FROM tracker_events_raw
WHERE evtTypeName = 'UnitBorn'
GROUP BY unit_type ORDER BY cnt DESC LIMIT 50
"""

unitborn_df = conn.con.execute(
    sql_queries["unitborn_unit_types"]
).df()
print("=== UnitBorn unit types (top 50) ===")
print(unitborn_df.to_string(index=False))
print(f"\nDistinct unit types shown: {len(unitborn_df)}")

# Gate check: at least 20 distinct unit types
assert len(unitborn_df) >= 20, (
    f"UnitBorn diversity too low: {len(unitborn_df)} < 20"
)

# Also get full count of distinct unit types
sql_queries["unitborn_distinct_count"] = """
SELECT COUNT(DISTINCT
    json_extract_string(event_data, '$.unitTypeName')
) AS n_distinct
FROM tracker_events_raw
WHERE evtTypeName = 'UnitBorn'
"""

unitborn_distinct = conn.con.execute(
    sql_queries["unitborn_distinct_count"]
).fetchone()[0]
print(f"Total distinct unit types: {unitborn_distinct}")

# %% [markdown]
# ---
# ## T02 -- Game Events Moderate Profile (608M rows)

# %% [markdown]
# ### Cell 10 -- Game: event type distribution

# %%
sql_queries["game_type_distribution"] = """
SELECT evtTypeName, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM game_events_raw GROUP BY evtTypeName ORDER BY cnt DESC
"""

game_type_df = conn.con.execute(
    sql_queries["game_type_distribution"]
).df()
print("=== Game event type distribution ===")
print(game_type_df.to_string(index=False))
print(f"\nTotal types: {len(game_type_df)}")
print(f"Total events: {game_type_df['cnt'].sum():,}")

# Gate check: exact total
assert game_type_df["cnt"].sum() == 608_618_823, (
    f"Game total mismatch: {game_type_df['cnt'].sum()} != 608,618,823"
)

# %% [markdown]
# ### Cell 11 -- Game: CameraUpdate dominance analysis

# %%
camera_row = game_type_df[
    game_type_df["evtTypeName"] == "CameraUpdate"
]
non_camera_df = game_type_df[
    game_type_df["evtTypeName"] != "CameraUpdate"
]

camera_pct = float(camera_row["pct"].iloc[0]) if len(camera_row) else 0
non_camera_total = int(non_camera_df["cnt"].sum())

print(f"CameraUpdate: {camera_pct}% of all game events")
print(f"Non-CameraUpdate events: {non_camera_total:,}")
print(f"\nNon-CameraUpdate breakdown:")
print(non_camera_df.to_string(index=False))

# %% [markdown]
# ### Cell 12 -- Game: per-replay density (10% BERNOULLI sample)

# %%
sql_queries["game_per_replay_density_sample"] = """
SELECT filename, COUNT(*) AS n_events
FROM game_events_raw TABLESAMPLE BERNOULLI(10)
GROUP BY filename
"""

try:
    game_density_df = conn.con.execute(
        sql_queries["game_per_replay_density_sample"]
    ).df()
    sample_method = "TABLESAMPLE BERNOULLI(10)"
except Exception as e:
    # Fallback: CTE-based filename sample
    print(f"TABLESAMPLE failed ({e}), using CTE-based sample")
    sql_queries["game_per_replay_density_fallback"] = """
    WITH sample_files AS (
        SELECT DISTINCT filename FROM game_events_raw
        USING SAMPLE 10 PERCENT (bernoulli)
    )
    SELECT g.filename, COUNT(*) AS n_events
    FROM game_events_raw g
    INNER JOIN sample_files s ON g.filename = s.filename
    GROUP BY g.filename
    """
    game_density_df = conn.con.execute(
        sql_queries["game_per_replay_density_fallback"]
    ).df()
    sample_method = "CTE-based 10% filename sample"

game_density_stats = {
    "sample_method": sample_method,
    "n_replays_sampled": len(game_density_df),
    "mean": round(float(game_density_df["n_events"].mean()), 1),
    "median": float(game_density_df["n_events"].median()),
    "p05": float(game_density_df["n_events"].quantile(0.05)),
    "p25": float(game_density_df["n_events"].quantile(0.25)),
    "p75": float(game_density_df["n_events"].quantile(0.75)),
    "p95": float(game_density_df["n_events"].quantile(0.95)),
    "min": int(game_density_df["n_events"].min()),
    "max": int(game_density_df["n_events"].max()),
}

print(f"=== Game per-replay density ({sample_method}) ===")
for k, v in game_density_stats.items():
    print(f"  {k}: {v}")
print("\nNote: BERNOULLI samples rows, so per-replay counts are "
      "deflated (~10% of true per-replay totals)")

# %% [markdown]
# ### Cell 13 -- Game: event_data sampling (Cmd and SelectionDelta)

# %%
game_sample_types = ["Cmd", "SelectionDelta"]
game_event_data_keys: dict = {}

for etype in game_sample_types:
    sql_key = f"game_event_data_sample_{etype}"
    sql_queries[sql_key] = (
        f"SELECT event_data FROM game_events_raw "
        f"WHERE evtTypeName = '{etype}' LIMIT 5"
    )
    sample_df = conn.con.execute(sql_queries[sql_key]).df()

    all_keys: set = set()
    for row in sample_df["event_data"]:
        if row and row.strip():
            parsed = json.loads(row)
            if isinstance(parsed, dict):
                all_keys.update(parsed.keys())

    game_event_data_keys[etype] = sorted(all_keys)
    print(f"\n{etype} keys ({len(all_keys)}): {sorted(all_keys)}")

# %% [markdown]
# ---
# ## T03 -- Message Events Light Profile (52K rows)

# %% [markdown]
# ### Cell 14 -- Message: event type distribution

# %%
sql_queries["message_type_distribution"] = """
SELECT evtTypeName, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM message_events_raw GROUP BY evtTypeName ORDER BY cnt DESC
"""

message_type_df = conn.con.execute(
    sql_queries["message_type_distribution"]
).df()
print("=== Message event type distribution ===")
print(message_type_df.to_string(index=False))
print(f"\nTotal types: {len(message_type_df)}")
print(f"Total events: {message_type_df['cnt'].sum():,}")

# Gate check: exact total
assert message_type_df["cnt"].sum() == 52_167, (
    f"Message total mismatch: {message_type_df['cnt'].sum()} != 52,167"
)

# %% [markdown]
# ### Cell 15 -- Message: replay coverage

# %%
sql_queries["message_replay_coverage"] = """
SELECT COUNT(DISTINCT filename) AS n_replays
FROM message_events_raw
"""

message_coverage = conn.con.execute(
    sql_queries["message_replay_coverage"]
).fetchone()[0]
print(f"Replays with message events: {message_coverage}")
print(f"Coverage: {100.0 * message_coverage / TOTAL_REPLAYS:.2f}%")
print(f"Replays without messages: {TOTAL_REPLAYS - message_coverage}")

# %% [markdown]
# ### Cell 16 -- Message: event_data sampling

# %%
sql_queries["message_event_data_sample"] = """
SELECT evtTypeName, event_data
FROM message_events_raw LIMIT 10
"""

message_sample_df = conn.con.execute(
    sql_queries["message_event_data_sample"]
).df()
print("=== Message event_data sample (10 rows) ===")
print(message_sample_df.to_string(index=False))

message_event_data_keys: dict = {}
for etype in message_type_df["evtTypeName"].tolist():
    sql_key = f"message_event_data_sample_{etype}"
    sql_queries[sql_key] = (
        f"SELECT event_data FROM message_events_raw "
        f"WHERE evtTypeName = '{etype}' LIMIT 5"
    )
    sample_df = conn.con.execute(sql_queries[sql_key]).df()

    all_keys: set = set()
    for row in sample_df["event_data"]:
        if row and row.strip():
            parsed = json.loads(row)
            if isinstance(parsed, dict):
                all_keys.update(parsed.keys())

    message_event_data_keys[etype] = sorted(all_keys)
    print(f"\n{etype} keys ({len(all_keys)}): {sorted(all_keys)}")

# %% [markdown]
# ---
# ## T04 -- Artifact Generation

# %% [markdown]
# ### Cell 17 -- Build JSON artifact

# %%
artifact = {
    "step": "01_03_04",
    "dataset": "sc2egset",
    "tracker_events": {
        "total_rows": int(tracker_type_df["cnt"].sum()),
        "type_distribution": [
            {
                "evtTypeName": row["evtTypeName"],
                "count": int(row["cnt"]),
                "pct": float(row["pct"]),
            }
            for _, row in tracker_type_df.iterrows()
        ],
        "n_event_types": len(tracker_type_df),
        "per_replay_density": tracker_density_stats,
        "per_replay_by_type": [
            {
                "evtTypeName": row["evtTypeName"],
                "n_replays": int(row["n_replays"]),
                "replay_coverage_pct": float(
                    row["replay_coverage_pct"]
                ),
                "total_events": int(row["total_events"]),
                "mean_per_replay": float(row["mean_per_replay"]),
            }
            for _, row in tracker_coverage_df.iterrows()
        ],
        "temporal_distribution": {
            "n_buckets": len(tracker_temporal_df),
            "min_bucket": int(tracker_temporal_df["loop_bucket"].min()),
            "max_bucket": int(tracker_temporal_df["loop_bucket"].max()),
        },
        "playerstats_periodicity": periodicity_stats,
        "unitborn_unit_types": {
            "distinct_count": int(unitborn_distinct),
            "top_50": [
                {
                    "unit_type": row["unit_type"],
                    "count": int(row["cnt"]),
                }
                for _, row in unitborn_df.iterrows()
            ],
        },
        "event_data_keys": tracker_event_data_keys,
    },
    "game_events": {
        "total_rows": int(game_type_df["cnt"].sum()),
        "type_distribution": [
            {
                "evtTypeName": row["evtTypeName"],
                "count": int(row["cnt"]),
                "pct": float(row["pct"]),
            }
            for _, row in game_type_df.iterrows()
        ],
        "n_event_types": len(game_type_df),
        "camera_update_analysis": {
            "camera_pct": camera_pct,
            "non_camera_total": non_camera_total,
        },
        "per_replay_density_sample": game_density_stats,
        "event_data_keys": game_event_data_keys,
    },
    "message_events": {
        "total_rows": int(message_type_df["cnt"].sum()),
        "type_distribution": [
            {
                "evtTypeName": row["evtTypeName"],
                "count": int(row["cnt"]),
                "pct": float(row["pct"]),
            }
            for _, row in message_type_df.iterrows()
        ],
        "n_event_types": len(message_type_df),
        "replay_coverage": {
            "n_replays_with_messages": message_coverage,
            "total_replays": TOTAL_REPLAYS,
            "coverage_pct": round(
                100.0 * message_coverage / TOTAL_REPLAYS, 2
            ),
        },
        "event_data_keys": message_event_data_keys,
    },
    "sql_queries": sql_queries,
}

json_path = artifact_dir / "01_03_04_event_profiling.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2, default=str)
print(f"JSON artifact written: {json_path}")

# %% [markdown]
# ### Cell 18 -- Build MD artifact

# %%
md_lines = [
    "# Step 01_03_04 -- Event Table Profiling",
    "",
    "**Dataset:** sc2egset",
    "**Date:** 2026-04-15",
    "**Predecessor:** 01_03_03 (Table Utility Assessment)",
    "**Invariants:** I3, I6, I9",
    "",
    "---",
    "",
    "## Tracker Events (62,003,411 rows)",
    "",
    "### Event type distribution",
    "",
    "| Event Type | Count | % |",
    "|-----------|------:|---:|",
]

for _, row in tracker_type_df.iterrows():
    md_lines.append(
        f"| {row['evtTypeName']} | {int(row['cnt']):,} "
        f"| {row['pct']:.4f} |"
    )

md_lines.extend([
    "",
    "### Per-replay density",
    "",
    "| Statistic | Value |",
    "|-----------|------:|",
])
for k, v in tracker_density_stats.items():
    md_lines.append(f"| {k} | {v} |")

md_lines.extend([
    "",
    "### Event type coverage per replay",
    "",
    "| Event Type | Replays | Coverage % | Total Events "
    "| Mean/Replay |",
    "|-----------|--------:|-----------:|-------------:"
    "|-----------:|",
])
for _, row in tracker_coverage_df.iterrows():
    md_lines.append(
        f"| {row['evtTypeName']} | {int(row['n_replays']):,} "
        f"| {row['replay_coverage_pct']:.2f} "
        f"| {int(row['total_events']):,} "
        f"| {row['mean_per_replay']:.1f} |"
    )

md_lines.extend([
    "",
    "### PlayerStats periodicity",
    "",
    f"- Mode gap: {periodicity_stats['mode_gap']} loops "
    f"({periodicity_stats['mode_pct']}% of observations)",
    f"- Distinct gap values: {periodicity_stats['n_distinct_gaps']}",
    f"- Total gap observations: "
    f"{periodicity_stats['total_gap_observations']:,}",
    "",
])

md_lines.extend([
    "### UnitBorn unit-type diversity",
    "",
    f"- Total distinct unit types: {unitborn_distinct}",
    "",
    "Top 20 unit types by frequency:",
    "",
    "| Unit Type | Count |",
    "|-----------|------:|",
])
for _, row in unitborn_df.head(20).iterrows():
    md_lines.append(f"| {row['unit_type']} | {int(row['cnt']):,} |")

md_lines.extend([
    "",
    "### event_data JSON keys by type",
    "",
])
for etype, keys in tracker_event_data_keys.items():
    md_lines.append(f"- **{etype}:** {', '.join(keys)}")

md_lines.extend([
    "",
    "---",
    "",
    "## Game Events (608,618,823 rows)",
    "",
    "### Event type distribution",
    "",
    "| Event Type | Count | % |",
    "|-----------|------:|---:|",
])
for _, row in game_type_df.iterrows():
    md_lines.append(
        f"| {row['evtTypeName']} | {int(row['cnt']):,} "
        f"| {row['pct']:.4f} |"
    )

md_lines.extend([
    "",
    f"CameraUpdate dominance: {camera_pct:.4f}%",
    f"Non-CameraUpdate events: {non_camera_total:,}",
    "",
    "### Per-replay density (10% BERNOULLI sample)",
    "",
    f"- Sample method: {game_density_stats['sample_method']}",
    f"- Replays sampled: {game_density_stats['n_replays_sampled']}",
    f"- Mean events/replay (sampled): "
    f"{game_density_stats['mean']}",
    f"- Median events/replay (sampled): "
    f"{game_density_stats['median']}",
    "",
    "Note: BERNOULLI samples rows, so per-replay counts are deflated "
    "(~10% of true per-replay totals).",
    "",
    "### event_data JSON keys by type",
    "",
])
for etype, keys in game_event_data_keys.items():
    md_lines.append(f"- **{etype}:** {', '.join(keys)}")

md_lines.extend([
    "",
    "---",
    "",
    "## Message Events (52,167 rows)",
    "",
    "### Event type distribution",
    "",
    "| Event Type | Count | % |",
    "|-----------|------:|---:|",
])
for _, row in message_type_df.iterrows():
    md_lines.append(
        f"| {row['evtTypeName']} | {int(row['cnt']):,} "
        f"| {row['pct']:.4f} |"
    )

md_lines.extend([
    "",
    f"Replay coverage: {message_coverage} / {TOTAL_REPLAYS} "
    f"({100.0 * message_coverage / TOTAL_REPLAYS:.2f}%)",
    "",
    "### event_data JSON keys by type",
    "",
])
for etype, keys in message_event_data_keys.items():
    md_lines.append(f"- **{etype}:** {', '.join(keys)}")

md_lines.extend([
    "",
    "---",
    "",
    "## SQL Queries (I6)",
    "",
])
for qname, qtext in sql_queries.items():
    md_lines.append(f"### {qname}")
    md_lines.append("```sql")
    md_lines.append(qtext.strip())
    md_lines.append("```")
    md_lines.append("")

md_path = artifact_dir / "01_03_04_event_profiling.md"
with open(md_path, "w") as f:
    f.write("\n".join(md_lines) + "\n")
print(f"MD artifact written: {md_path}")

# %% [markdown]
# ### Cell 19 -- Gate checks summary

# %%
print("=== Gate Checks ===")
print(f"Tracker total: {artifact['tracker_events']['total_rows']:,} "
      f"(expected 62,003,411)")
print(f"Game total:    {artifact['game_events']['total_rows']:,} "
      f"(expected 608,618,823)")
print(f"Message total: {artifact['message_events']['total_rows']:,} "
      f"(expected 52,167)")
print(f"PlayerStats periodicity entries: "
      f"{len(periodicity_stats['all_gaps'])}")
print(f"UnitBorn distinct types: {unitborn_distinct}")
print(f"Tracker event_data keys sampled: "
      f"{len(tracker_event_data_keys)} types")
print(f"Game event_data keys sampled: "
      f"{len(game_event_data_keys)} types")
print(f"sql_queries count: {len(sql_queries)}")

assert artifact["tracker_events"]["total_rows"] == 62_003_411
assert artifact["game_events"]["total_rows"] == 608_618_823
assert artifact["message_events"]["total_rows"] == 52_167
assert len(periodicity_stats["all_gaps"]) > 0
assert unitborn_distinct >= 20
assert len(tracker_event_data_keys) >= 5
assert len(game_event_data_keys) >= 2
assert len(sql_queries) > 0

print("\nAll gate checks PASSED")
