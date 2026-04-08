# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
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
# # Phase 0 / Step 0.9 — Post-Rebuild Verification
#
# | Field | Value |
# |-------|-------|
# | Phase | 0 |
# | Step | 0.9 |
# | Dataset | sc2egset |
# | Game | sc2 |
# | Date | 2026-04-08 |
# | Report artifacts | `src/rts_predict/sc2/reports/sc2egset/artifacts/00_99_post_rebuild_verification.md` |  # noqa: E501
# | Scientific question | Does the rebuilt DuckDB contain all Phase 0 raw tables with the |
# |                     | expected schemas and row counts? |
# | ROADMAP reference | `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` Step 0.9 |

# %%
from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir

client = get_notebook_db("sc2", "sc2egset")
con = client.con
artifacts_dir = get_reports_dir("sc2", "sc2egset") / "artifacts"
artifacts_dir.mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ## V1 — Tables present in main schema

# %%
V1_QUERY = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_name
"""
df_v1 = con.execute(V1_QUERY).df()
print(df_v1)

# %% [markdown]
# ## V2 — Schema of raw_map_alias_files

# %%
V2_QUERY = "PRAGMA table_info('raw_map_alias_files')"
df_v2 = con.execute(V2_QUERY).df()
print(df_v2)

# %% [markdown]
# ## V3 — Row count in raw_map_alias_files

# %%
V3_QUERY = "SELECT COUNT(*) AS n_rows FROM raw_map_alias_files"
row_v3 = con.execute(V3_QUERY).fetchone()
assert row_v3 is not None
n_rows = row_v3[0]
print(f"n_rows = {n_rows}")

# %% [markdown]
# ## V4 — Distinct SHA1 versions

# %%
V4_QUERY = "SELECT COUNT(DISTINCT byte_sha1) AS n_versions FROM raw_map_alias_files"
row_v4 = con.execute(V4_QUERY).fetchone()
assert row_v4 is not None
n_versions = row_v4[0]
print(f"n_versions = {n_versions}")

# %% [markdown]
# ## V5 — Distinct tournament directories

# %%
V5_QUERY = "SELECT COUNT(DISTINCT tournament_dir) AS n_dirs FROM raw_map_alias_files"
row_v5 = con.execute(V5_QUERY).fetchone()
assert row_v5 is not None
n_dirs = row_v5[0]
print(f"n_dirs = {n_dirs}")

# %% [markdown]
# ## V6 — File size statistics (bytes)

# %%
V6_QUERY = """
SELECT
    MIN(n_bytes)    AS min_bytes,
    MAX(n_bytes)    AS max_bytes,
    AVG(n_bytes)    AS avg_bytes,
    MEDIAN(n_bytes) AS median_bytes
FROM raw_map_alias_files
"""
df_v6 = con.execute(V6_QUERY).df()
print(df_v6)

# %% [markdown]
# ## V7 — Version distribution (how many tournament dirs share each SHA1)

# %%
V7_QUERY = """
SELECT byte_sha1, COUNT(*) AS n_dirs
FROM raw_map_alias_files
GROUP BY byte_sha1
ORDER BY n_dirs DESC
"""
df_v7 = con.execute(V7_QUERY).df()
print(df_v7)

# %% [markdown]
# ## V8 — Sample rows (first 5)

# %%
V8_QUERY = """
SELECT
    tournament_dir,
    byte_sha1,
    n_bytes,
    LENGTH(raw_json) AS json_len
FROM raw_map_alias_files
LIMIT 5
"""
df_v8 = con.execute(V8_QUERY).df()
print(df_v8)

# %% [markdown]
# ## V9 — Replay table row count

# %%
V9_QUERY = "SELECT COUNT(*) AS n_replays FROM raw"
row_v9 = con.execute(V9_QUERY).fetchone()
assert row_v9 is not None
n_replays = row_v9[0]
print(f"n_replays = {n_replays}")

# %% [markdown]
# ## V10 — Distinct tournament dirs in raw table

# %%
V10_QUERY = """
SELECT COUNT(DISTINCT split_part(filename, '/', -3)) AS n_dirs
FROM raw
"""
row_v10 = con.execute(V10_QUERY).fetchone()
assert row_v10 is not None
n_dirs_raw = row_v10[0]
print(f"n_dirs_raw = {n_dirs_raw}")

# %% [markdown]
# ## V11 — tracker_events_raw row count and schema

# %%
V11_QUERY = "SELECT COUNT(*) AS n_tracker_events FROM tracker_events_raw"
row_v11 = con.execute(V11_QUERY).fetchone()
assert row_v11 is not None
n_tracker_events = row_v11[0]
print(f"n_tracker_events = {n_tracker_events}")

V11_SCHEMA_QUERY = "PRAGMA table_info('tracker_events_raw')"
df_v11_schema = con.execute(V11_SCHEMA_QUERY).df()
print(df_v11_schema)

# %% [markdown]
# ## V12 — game_events_raw row count and schema

# %%
V12_QUERY = "SELECT COUNT(*) AS n_game_events FROM game_events_raw"
row_v12 = con.execute(V12_QUERY).fetchone()
assert row_v12 is not None
n_game_events = row_v12[0]
print(f"n_game_events = {n_game_events}")

V12_SCHEMA_QUERY = "PRAGMA table_info('game_events_raw')"
df_v12_schema = con.execute(V12_SCHEMA_QUERY).df()
print(df_v12_schema)

# %% [markdown]
# ## V13 — match_player_map row count and schema

# %%
V13_QUERY = "SELECT COUNT(*) AS n_match_player_map FROM match_player_map"
row_v13 = con.execute(V13_QUERY).fetchone()
assert row_v13 is not None
n_match_player_map = row_v13[0]
print(f"n_match_player_map = {n_match_player_map}")

V13_SCHEMA_QUERY = "PRAGMA table_info('match_player_map')"
df_v13_schema = con.execute(V13_SCHEMA_QUERY).df()
print(df_v13_schema)

# %% [markdown]
# ## V14 — player_stats row count and schema

# %%
V14_QUERY = "SELECT COUNT(*) AS n_player_stats FROM player_stats"
row_v14 = con.execute(V14_QUERY).fetchone()
assert row_v14 is not None
n_player_stats = row_v14[0]
print(f"n_player_stats = {n_player_stats}")

V14_SCHEMA_QUERY = "PRAGMA table_info('player_stats')"
df_v14_schema = con.execute(V14_SCHEMA_QUERY).df()
print(df_v14_schema)

# %% [markdown]
# ## Write report artifact

# %%
EXPECTED_RAW_ROW_COUNT = 22_390

one_file_per_dir_invariant = n_rows == n_dirs

report_lines = [
    "# Phase 0 / Step 0.9 — Post-Rebuild Verification Report",
    "",
    "**Date:** 2026-04-08  ",
    "**Branch:** feat/phase0-map-alias-ingestion",
    "",
    "---",
    "",
    "## 1. Summary",
    "",
    "Phase 0 was rebuilt after replacing the silent-merge `map_translation` table"
    " with the row-per-file `raw_map_alias_files` table and removing ML view"
    " construction from `init_database`. The database now contains six raw tables"
    " only: `raw`, `raw_map_alias_files`, `tracker_events_raw`, `game_events_raw`,"
    " `match_player_map`, and `player_stats`.",
    "",
    f"- `raw` row count: {n_replays} (expected {EXPECTED_RAW_ROW_COUNT})",
    f"- `raw_map_alias_files` row count: {n_rows}",
    f"- `tracker_events_raw` row count: {n_tracker_events}",
    f"- `game_events_raw` row count: {n_game_events}",
    f"- `match_player_map` row count: {n_match_player_map}",
    f"- `player_stats` row count: {n_player_stats}",
    f"- Distinct tournament dirs (alias table): {n_dirs}",
    f"- Distinct tournament dirs (raw table): {n_dirs_raw}",
    f"- Distinct SHA1 versions: {n_versions}",
    f"- One-file-per-dir invariant (V3 == V5): {one_file_per_dir_invariant}",
    f"- raw row count matches expected: {n_replays == EXPECTED_RAW_ROW_COUNT}",
    "",
    "---",
    "",
    "## 2. Schema (PRAGMA table_info)",
    "",
    "### raw_map_alias_files",
    "",
    "```",
    df_v2.to_string(index=False),
    "```",
    "",
    "### tracker_events_raw",
    "",
    "```",
    df_v11_schema.to_string(index=False),
    "```",
    "",
    "### game_events_raw",
    "",
    "```",
    df_v12_schema.to_string(index=False),
    "```",
    "",
    "### match_player_map",
    "",
    "```",
    df_v13_schema.to_string(index=False),
    "```",
    "",
    "### player_stats",
    "",
    "```",
    df_v14_schema.to_string(index=False),
    "```",
    "",
    "---",
    "",
    "## 3. Row Counts",
    "",
    "| Table | Row count |",
    "|-------|-----------|",
    f"| `raw` (V9) | {n_replays} |",
    f"| `raw_map_alias_files` (V3) | {n_rows} |",
    f"| `tracker_events_raw` (V11) | {n_tracker_events} |",
    f"| `game_events_raw` (V12) | {n_game_events} |",
    f"| `match_player_map` (V13) | {n_match_player_map} |",
    f"| `player_stats` (V14) | {n_player_stats} |",
    "",
    "**raw_map_alias_files file-size statistics:**",
    "",
    "```",
    df_v6.to_string(index=False),
    "```",
    "",
    "**Distinct SHA1 versions (V4):** " + str(n_versions),
    "**Distinct alias tournament dirs (V5):** " + str(n_dirs),
    "",
    "---",
    "",
    "## 4. Version Distribution",
    "",
    "```",
    df_v7.to_string(index=False),
    "```",
    "",
    "---",
    "",
    "## 5. One-File-Per-Dir Invariant",
    "",
    f"V3 (n_rows) = {n_rows}, V5 (n_dirs) = {n_dirs}",
    f"Invariant holds: **{one_file_per_dir_invariant}**",
    "",
    "---",
    "",
    "## 6. Replay Table Parity",
    "",
    f"V9 (n_replays) = {n_replays}, expected = {EXPECTED_RAW_ROW_COUNT}",
    f"Match: **{n_replays == EXPECTED_RAW_ROW_COUNT}**",
    "",
    "---",
    "",
    "## 7. Tournament Dir Cross-Check",
    "",
    f"V5 (alias n_dirs) = {n_dirs}, V10 (raw n_dirs) = {n_dirs_raw}",
    f"Match: **{n_dirs == n_dirs_raw}**",
    "",
    "---",
    "",
    "## 8. Sample Rows",
    "",
    "```",
    df_v8.to_string(index=False),
    "```",
    "",
    "---",
    "",
    "## 9. Appendix — SQL for Each Cell",
    "",
    f"**V1:**\n```sql\n{V1_QUERY.strip()}\n```",
    "",
    f"**V2:**\n```sql\n{V2_QUERY.strip()}\n```",
    "",
    f"**V3:**\n```sql\n{V3_QUERY.strip()}\n```",
    "",
    f"**V4:**\n```sql\n{V4_QUERY.strip()}\n```",
    "",
    f"**V5:**\n```sql\n{V5_QUERY.strip()}\n```",
    "",
    f"**V6:**\n```sql\n{V6_QUERY.strip()}\n```",
    "",
    f"**V7:**\n```sql\n{V7_QUERY.strip()}\n```",
    "",
    f"**V8:**\n```sql\n{V8_QUERY.strip()}\n```",
    "",
    f"**V9:**\n```sql\n{V9_QUERY.strip()}\n```",
    "",
    f"**V10:**\n```sql\n{V10_QUERY.strip()}\n```",
    "",
    f"**V11:**\n```sql\n{V11_QUERY.strip()}\n```",
    "",
    f"**V12:**\n```sql\n{V12_QUERY.strip()}\n```",
    "",
    f"**V13:**\n```sql\n{V13_QUERY.strip()}\n```",
    "",
    f"**V14:**\n```sql\n{V14_QUERY.strip()}\n```",
]

report_path = artifacts_dir / "00_99_post_rebuild_verification.md"
report_path.write_text("\n".join(report_lines), encoding="utf-8")
print(f"Report written to: {report_path}")

client.close()

# %% [markdown]
# ## Final invariant assertions

# %%
assert n_rows > 0, f"raw_map_alias_files is empty (n_rows={n_rows})"
assert n_versions >= 1, f"No distinct SHA1 versions found (n_versions={n_versions})"
assert n_dirs > 0, f"No distinct tournament dirs found (n_dirs={n_dirs})"
assert n_tracker_events > 0, f"tracker_events_raw is empty (n_tracker_events={n_tracker_events})"
assert n_game_events > 0, f"game_events_raw is empty (n_game_events={n_game_events})"
assert n_match_player_map > 0, f"match_player_map is empty (n_match_player_map={n_match_player_map})"
assert n_player_stats > 0, f"player_stats is empty (n_player_stats={n_player_stats})"
print("All invariant assertions passed.")
