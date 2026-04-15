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
# # Step 01_02_04 -- Metadata STRUCT Extraction & Replay-Level EDA
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA (Tukey-style)
# **Dataset:** sc2egset
# **Question:** What scalar fields are embedded in the metadata STRUCTs,
# what are their value distributions, and what is the full column-level
# profile (NULLs, constants, cardinality) across all raw tables?
# **Invariants applied:** #6 (reproducibility — SQL inlined in artifact),
# #7 (no magic numbers), #9 (step scope: univariate profiling only)
# **Step scope:** query, profile, visualize
# **Type:** Read-only — no DuckDB writes, no new tables, no schema changes

# %%
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from rts_predict.common.eda_census import profile_table
from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.sc2.config import DB_FILE

matplotlib.use("Agg")
logger = setup_notebook_logging()
logger.info("DB_FILE: %s", DB_FILE)

# %%
con = duckdb.connect(str(DB_FILE), read_only=True)
print(f"Connected (read-only): {DB_FILE}")

# %% [markdown]
# ### Database memory footprint

# %%
import os
db_size_bytes = os.path.getsize(str(DB_FILE))
db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
print(f"DuckDB file size: {db_size_bytes:,} bytes ({db_size_mb} MB)")

# %%
# Set up artifact directories
artifacts_dir = (
    get_reports_dir("sc2", "sc2egset")
    / "artifacts" / "01_exploration" / "02_eda"
)
plots_dir = artifacts_dir / "plots"
artifacts_dir.mkdir(parents=True, exist_ok=True)
plots_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifacts dir: {artifacts_dir}")
print(f"Plots dir: {plots_dir}")

# %% [markdown]
# ## Section A: STRUCT Field Extraction
#
# Flatten the four STRUCT columns (`details`, `header`, `initData`,
# `metadata`) from `replays_meta_raw` into scalar fields.

# %%
STRUCT_FLAT_SQL = """\
SELECT
    details.gameSpeed AS game_speed,
    details.isBlizzardMap AS is_blizzard_map,
    details.timeUTC AS time_utc,
    header.elapsedGameLoops AS elapsed_game_loops,
    header."version" AS game_version_header,
    metadata.baseBuild AS base_build,
    metadata.dataBuild AS data_build,
    metadata.gameVersion AS game_version_meta,
    metadata.mapName AS map_name,
    initData.gameDescription.maxPlayers AS max_players,
    initData.gameDescription.gameSpeed AS game_speed_init,
    initData.gameDescription.isBlizzardMap AS is_blizzard_map_init,
    initData.gameDescription.mapSizeX AS map_size_x,
    initData.gameDescription.mapSizeY AS map_size_y,
    gameEventsErr,
    messageEventsErr,
    trackerEvtsErr,
    filename
FROM replays_meta_raw
"""
struct_flat = con.execute(STRUCT_FLAT_SQL).df()
print(f"struct_flat shape: {struct_flat.shape}")
print(struct_flat.head())

# %% [markdown]
# ## Section B: Full NULL Census
#
# All 25 `replay_players_raw` columns + `replays_meta_raw.filename`.

# %%
NULL_CENSUS_SQL = """\
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(filename) AS filename_null,
    COUNT(*) - COUNT(toon_id) AS toon_id_null,
    COUNT(*) - COUNT(nickname) AS nickname_null,
    COUNT(*) - COUNT(playerID) AS playerID_null,
    COUNT(*) - COUNT(userID) AS userID_null,
    COUNT(*) - COUNT(isInClan) AS isInClan_null,
    COUNT(*) - COUNT(clanTag) AS clanTag_null,
    COUNT(*) - COUNT(MMR) AS MMR_null,
    COUNT(*) - COUNT(race) AS race_null,
    COUNT(*) - COUNT(selectedRace) AS selectedRace_null,
    COUNT(*) - COUNT(handicap) AS handicap_null,
    COUNT(*) - COUNT(region) AS region_null,
    COUNT(*) - COUNT(realm) AS realm_null,
    COUNT(*) - COUNT(highestLeague) AS highestLeague_null,
    COUNT(*) - COUNT(result) AS result_null,
    COUNT(*) - COUNT(APM) AS APM_null,
    COUNT(*) - COUNT(SQ) AS SQ_null,
    COUNT(*) - COUNT(supplyCappedPercent) AS supplyCappedPercent_null,
    COUNT(*) - COUNT(startDir) AS startDir_null,
    COUNT(*) - COUNT(startLocX) AS startLocX_null,
    COUNT(*) - COUNT(startLocY) AS startLocY_null,
    COUNT(*) - COUNT(color_a) AS color_a_null,
    COUNT(*) - COUNT(color_b) AS color_b_null,
    COUNT(*) - COUNT(color_g) AS color_g_null,
    COUNT(*) - COUNT(color_r) AS color_r_null
FROM replay_players_raw
"""
null_raw = con.execute(NULL_CENSUS_SQL).df()
total_rows = int(null_raw["total_rows"].iloc[0])
print(f"Total rows in replay_players_raw: {total_rows}")

# %%
# Reshape into tidy (column, null_count, null_pct) table
null_cols = [c for c in null_raw.columns if c.endswith("_null")]
null_records = []
for col in null_cols:
    col_name = col.replace("_null", "")
    null_count = int(null_raw[col].iloc[0])
    null_pct = round(100.0 * null_count / total_rows, 2)
    null_records.append(
        {"column": col_name, "null_count": null_count, "null_pct": null_pct}
    )

null_census_df = pd.DataFrame(null_records)
null_census_df = null_census_df.sort_values("null_count", ascending=False)
print("=== replay_players_raw NULL census ===")
print(null_census_df.to_string(index=False))

# %%
# Check replays_meta_raw.filename NULLs
META_FILENAME_NULL_SQL = """\
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct
FROM replays_meta_raw
"""
meta_fn_null = con.execute(META_FILENAME_NULL_SQL).df()
print("=== replays_meta_raw.filename NULL census ===")
print(meta_fn_null.to_string(index=False))

# %% [markdown]
# ### struct_flat NULL census

# %%
STRUCT_FLAT_NULL_CENSUS_SQL = """\
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(time_utc) AS time_utc_null,
    COUNT(*) - COUNT(elapsed_game_loops) AS elapsed_game_loops_null,
    COUNT(*) - COUNT(game_version_header) AS game_version_header_null,
    COUNT(*) - COUNT(base_build) AS base_build_null,
    COUNT(*) - COUNT(data_build) AS data_build_null,
    COUNT(*) - COUNT(game_version_meta) AS game_version_meta_null,
    COUNT(*) - COUNT(map_name) AS map_name_null,
    COUNT(*) - COUNT(max_players) AS max_players_null,
    COUNT(*) - COUNT(game_speed) AS game_speed_null,
    COUNT(*) - COUNT(game_speed_init) AS game_speed_init_null,
    COUNT(*) - COUNT(is_blizzard_map) AS is_blizzard_map_null,
    COUNT(*) - COUNT(is_blizzard_map_init) AS is_blizzard_map_init_null,
    COUNT(*) - COUNT(map_size_x) AS map_size_x_null,
    COUNT(*) - COUNT(map_size_y) AS map_size_y_null,
    COUNT(*) - COUNT(gameEventsErr) AS gameEventsErr_null,
    COUNT(*) - COUNT(messageEventsErr) AS messageEventsErr_null,
    COUNT(*) - COUNT(trackerEvtsErr) AS trackerEvtsErr_null
FROM struct_flat
"""
sf_null_raw = con.execute(STRUCT_FLAT_NULL_CENSUS_SQL).df()
sf_total_rows = int(sf_null_raw["total_rows"].iloc[0])
print(f"Total rows in struct_flat: {sf_total_rows}")

# %%
# Reshape into tidy (column, null_count, null_pct) table
sf_null_cols = [c for c in sf_null_raw.columns if c.endswith("_null")]
sf_null_records = []
for col in sf_null_cols:
    col_name = col.replace("_null", "")
    null_count = int(sf_null_raw[col].iloc[0])
    null_pct = round(100.0 * null_count / sf_total_rows, 2)
    sf_null_records.append(
        {"column": col_name, "null_count": null_count, "null_pct": null_pct}
    )

sf_null_census_df = pd.DataFrame(sf_null_records)
sf_null_census_df = sf_null_census_df.sort_values("null_count", ascending=False)
print("=== struct_flat NULL census ===")
print(sf_null_census_df.to_string(index=False))

# %% [markdown]
# ### struct_flat completeness note

# %%
_sf_all_zero_nulls = (sf_null_census_df["null_count"] == 0).all()
if _sf_all_zero_nulls:
    sf_completeness_note = "All 17 columns 0% NULL. No missingness co-occurrence."
    print("All 17 struct_flat columns have 0 NULLs. No missingness co-occurrence to analyze.")
else:
    # Build co-occurrence matrix for columns that have NULLs
    _null_cols_list = sf_null_census_df[sf_null_census_df["null_count"] > 0]["column"].tolist()
    _cooc_data = {}
    for col_a in _null_cols_list:
        _cooc_data[col_a] = {}
        for col_b in _null_cols_list:
            sql = f"""
            SELECT COUNT(*) AS both_null
            FROM struct_flat
            WHERE {col_a} IS NULL AND {col_b} IS NULL
            """
            both_null = con.execute(sql).fetchone()[0]
            _cooc_data[col_a][col_b] = both_null
    sf_completeness_note = {"type": "co_occurrence", "matrix": _cooc_data}
    _cooc_df = pd.DataFrame(_cooc_data)
    print("=== struct_flat NULL co-occurrence matrix ===")
    print(_cooc_df.to_string())

# %% [markdown]
# ## Section C: Target Variable (`result`)

# %%
RESULT_DIST_SQL = """\
SELECT result, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY result
ORDER BY cnt DESC
"""
result_dist = con.execute(RESULT_DIST_SQL).df()
print("=== result value distribution ===")
print(result_dist.to_string(index=False))

# %%
# Isolate results for non-2-player replays (known 11 from 01_02_02)
NON_2P_RESULT_SQL = """\
SELECT rp.result, COUNT(*) AS cnt
FROM replay_players_raw rp
JOIN replays_meta_raw rm ON rp.filename = rm.filename
WHERE rm.initData.gameDescription.maxPlayers != 2
   OR rm.filename IN (
       SELECT filename FROM replay_players_raw
       GROUP BY filename HAVING COUNT(*) != 2
   )
GROUP BY rp.result
ORDER BY cnt DESC
"""
non_2p_results = con.execute(NON_2P_RESULT_SQL).df()
print("=== result values for non-2-player replays ===")
print(non_2p_results.to_string(index=False))
print(
    "\nNote: OR-condition captures a superset -- any replay where "
    "either maxPlayers != 2 or actual player-row count differs from 2."
)

# %%
# Corrective query: Undecided/Tie replay context
# The OR-condition non-2-player query above returns only Win/Loss.
# This query uses LEFT JOIN so Undecided/Tie rows are included even if
# filename is absent from replays_meta_raw.
# Note: Joins on filename per sql-data.md rule 15 deviation -- unavoidable at this
# pipeline stage (replay_id not yet derived). Migrates to replay_id in 01_04.
UNDECIDED_TIE_CONTEXT_SQL = """\
SELECT
    rp.result,
    rp.filename,
    rm.initData.gameDescription.maxPlayers AS max_players,
    player_counts.player_row_count
FROM replay_players_raw rp
LEFT JOIN replays_meta_raw rm ON rp.filename = rm.filename
JOIN (
    SELECT filename, COUNT(*) AS player_row_count
    FROM replay_players_raw
    GROUP BY filename
) player_counts ON rp.filename = player_counts.filename
WHERE rp.result IN ('Undecided', 'Tie')
ORDER BY rp.result, rp.filename
"""
undecided_tie_context = con.execute(UNDECIDED_TIE_CONTEXT_SQL).df()
print(f"=== Undecided/Tie replay context ({len(undecided_tie_context)} rows) ===")
print(undecided_tie_context.to_string(index=False))

# %% [markdown]
# ## Section D: Categorical Field Profiles
#
# Distinct value counts for categorical fields using loop-based cells.

# %%
# replay_players_raw categorical fields
RP_CAT_COLS = ["race", "selectedRace", "highestLeague", "region", "realm"]
rp_cat_results = {}

for col in RP_CAT_COLS:
    sql = f"""
    SELECT {col}, COUNT(*) AS cnt,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
    FROM replay_players_raw
    GROUP BY {col}
    ORDER BY cnt DESC
    """
    df = con.execute(sql).df()
    rp_cat_results[col] = df
    print(f"\n=== {col} ===")
    print(df.to_string(index=False))

# %% [markdown]
# ### isInClan distribution

# %%
IS_IN_CLAN_SQL = """\
SELECT
    isInClan,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY isInClan
ORDER BY cnt DESC
"""
is_in_clan_df = con.execute(IS_IN_CLAN_SQL).df()
print("=== isInClan distribution ===")
print(is_in_clan_df.to_string(index=False))

# %% [markdown]
# ### clanTag top-20

# %%
CLAN_TAG_TOP20_SQL = """\
SELECT
    clanTag,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_of_total,
    ROUND(100.0 * COUNT(*) / (
        SELECT COUNT(*) FROM replay_players_raw
        WHERE clanTag != ''
    ), 2) AS pct_of_non_empty
FROM replay_players_raw
WHERE clanTag != ''
GROUP BY clanTag
ORDER BY cnt DESC
LIMIT 20
"""
clan_tag_top20_df = con.execute(CLAN_TAG_TOP20_SQL).df()
print("=== clanTag top-20 (non-empty) ===")
print(clan_tag_top20_df.to_string(index=False))

# %%
# replays_meta_raw STRUCT categorical fields
META_CAT_COLS = [
    "game_speed", "game_speed_init", "map_name",
    "game_version_meta", "base_build", "data_build",
]

meta_cat_results = {}
for col in META_CAT_COLS:
    if col == "map_name":
        sql = f"""
        SELECT {col}, COUNT(*) AS cnt
        FROM struct_flat
        GROUP BY {col}
        ORDER BY cnt DESC
        LIMIT 20
        """
    else:
        sql = f"""
        SELECT {col}, COUNT(*) AS cnt,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
        FROM struct_flat
        GROUP BY {col}
        ORDER BY cnt DESC
        """
    # struct_flat is a pandas df, so register it for SQL access
    df = con.execute(sql).df()
    meta_cat_results[col] = df
    print(f"\n=== {col} ===")
    if col == "map_name":
        print(f"(top 20 of {con.execute(f'SELECT COUNT(DISTINCT {col}) FROM struct_flat').fetchone()[0]} distinct)")
    print(df.to_string(index=False))

# %%
# Game speed assertion -- MUST pass before Section E
speed_counts = con.execute(
    "SELECT game_speed, COUNT(*) AS cnt FROM struct_flat GROUP BY game_speed ORDER BY cnt DESC"
).df()
print(speed_counts)
assert set(speed_counts["game_speed"].dropna()) == {"Faster"}, (
    f"Expected only 'Faster' game speed; found: {speed_counts['game_speed'].unique()}"
)
print("All replays confirmed Faster speed -- duration conversion is safe.")

# %%
# Visualizations: bar charts for categorical fields
# result bar chart
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(result_dist["result"].astype(str), result_dist["cnt"])
ax.set_title("Result Value Distribution")
ax.set_xlabel("result")
ax.set_ylabel("Count")
for i, (val, cnt) in enumerate(zip(result_dist["result"], result_dist["cnt"])):
    ax.text(i, cnt, str(cnt), ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_result_bar.png", dpi=150)
plt.show()
plt.close()

# %%
# race bar chart
race_df = rp_cat_results["race"]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(race_df["race"].astype(str), race_df["cnt"])
ax.set_title("Race Distribution")
ax.set_xlabel("race")
ax.set_ylabel("Count")
for i, (val, cnt) in enumerate(zip(race_df["race"], race_df["cnt"])):
    ax.text(i, cnt, str(cnt), ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_race_bar.png", dpi=150)
plt.show()
plt.close()

# %%
# selectedRace bar chart
sr_df = rp_cat_results["selectedRace"]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(sr_df["selectedRace"].astype(str), sr_df["cnt"])
ax.set_title("Selected Race Distribution")
ax.set_xlabel("selectedRace")
ax.set_ylabel("Count")
for i, (val, cnt) in enumerate(zip(sr_df["selectedRace"], sr_df["cnt"])):
    ax.text(i, cnt, str(cnt), ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_selectedrace_bar.png", dpi=150)
plt.show()
plt.close()

# %%
# highestLeague bar chart
hl_df = rp_cat_results["highestLeague"]
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(hl_df["highestLeague"].astype(str), hl_df["cnt"])
ax.set_title("Highest League Distribution")
ax.set_xlabel("highestLeague")
ax.set_ylabel("Count")
ax.tick_params(axis="x", rotation=45)
for i, (val, cnt) in enumerate(zip(hl_df["highestLeague"], hl_df["cnt"])):
    ax.text(i, cnt, str(cnt), ha="center", va="bottom", fontsize=8)
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_highestleague_bar.png", dpi=150)
plt.show()
plt.close()

# %%
# region bar chart
reg_df = rp_cat_results["region"]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(reg_df["region"].astype(str), reg_df["cnt"])
ax.set_title("Region Distribution")
ax.set_xlabel("region")
ax.set_ylabel("Count")
for i, (val, cnt) in enumerate(zip(reg_df["region"], reg_df["cnt"])):
    ax.text(i, cnt, str(cnt), ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_region_bar.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ## Section E: Numeric Descriptive Statistics
#
# **Prerequisite:** Section D game speed assertion passed.
# The game-loop-to-seconds conversion uses `/ 22.4` (22.4 game loops/second:
# standard Faster speed = 16 base loops/second x 1.4 Faster multiplier).
#
# **In-game field distinction:** APM, SQ, and supplyCappedPercent are
# in-game-only fields (computed from replay actions, available only
# post-game). Their presence in the EDA does not imply pre-game
# availability. This distinction will be formally enforced at the feature
# engineering stage (Phase 03).

# %%
# Descriptive stats for replay_players_raw numeric columns
RP_NUM_COLS = ["MMR", "APM", "SQ", "supplyCappedPercent", "handicap"]
rp_num_stats = {}

for col in RP_NUM_COLS:
    sql = f"""
    SELECT
        MIN({col}) AS min_val,
        MAX({col}) AS max_val,
        ROUND(AVG({col}), 2) AS mean_val,
        ROUND(MEDIAN({col}), 2) AS median_val,
        ROUND(STDDEV({col}), 2) AS stddev_val,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {col}) AS p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col}) AS p25,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col}) AS p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {col}) AS p95
    FROM replay_players_raw
    WHERE {col} IS NOT NULL
    """
    df = con.execute(sql).df()
    rp_num_stats[col] = df
    print(f"\n=== {col} ===")
    print(df.to_string(index=False))

# %% [markdown]
# ### SQ stats excluding INT32_MIN sentinel

# %%
SQ_NO_SENTINEL_SQL = """\
SELECT
    MIN(SQ) AS min_val,
    MAX(SQ) AS max_val,
    ROUND(AVG(SQ), 2) AS mean_val,
    ROUND(MEDIAN(SQ), 2) AS median_val,
    ROUND(STDDEV(SQ), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) AS p95,
    COUNT(*) AS n_rows
FROM replay_players_raw
WHERE SQ IS NOT NULL AND SQ != -2147483648
"""
sq_no_sentinel = con.execute(SQ_NO_SENTINEL_SQL).df()
print("=== SQ stats (sentinel excluded) ===")
print(sq_no_sentinel.to_string(index=False))
print(
    "\nThe main SQ descriptive statistics (Section E) are contaminated by 2 rows "
    "containing the INT32_MIN sentinel value (-2147483648). The stats above "
    "exclude those rows. The sentinel causes the main SQ mean and stddev to be "
    "misleading. Refer to the sentinel-excluded stats above for the clean SQ "
    "distribution's actual median and range."
)

# %%
# Positional columns: cardinality and ranges
POS_COLS = ["startDir", "startLocX", "startLocY"]

for col in POS_COLS:
    sql = f"""
    SELECT
        COUNT(DISTINCT {col}) AS cardinality,
        MIN({col}) AS min_val,
        MAX({col}) AS max_val
    FROM replay_players_raw
    WHERE {col} IS NOT NULL
    """
    df = con.execute(sql).df()
    print(f"\n=== {col} ===")
    print(df.to_string(index=False))

# %%
# Duration stats from replays_meta_raw (elapsed_game_loops)
DURATION_STATS_SQL = """\
SELECT
    MIN(elapsed_game_loops) AS min_val,
    MAX(elapsed_game_loops) AS max_val,
    ROUND(AVG(elapsed_game_loops), 2) AS mean_val,
    ROUND(MEDIAN(elapsed_game_loops), 2) AS median_val,
    ROUND(STDDEV(elapsed_game_loops), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p95,
    ROUND(MIN(elapsed_game_loops) / 22.4, 2) AS min_seconds,
    ROUND(MAX(elapsed_game_loops) / 22.4, 2) AS max_seconds,
    ROUND(AVG(elapsed_game_loops) / 22.4, 2) AS mean_seconds,
    ROUND(MEDIAN(elapsed_game_loops) / 22.4, 2) AS median_seconds
FROM struct_flat
WHERE elapsed_game_loops IS NOT NULL
"""
duration_stats = con.execute(DURATION_STATS_SQL).df()
print("=== elapsed_game_loops (+ seconds conversion at 22.4 loops/sec) ===")
print(duration_stats.to_string(index=False))

# %%
# Map dimensions
MAP_DIM_SQL = """\
SELECT
    map_size_x, map_size_y, COUNT(*) AS cnt
FROM struct_flat
GROUP BY map_size_x, map_size_y
ORDER BY cnt DESC
"""
map_dims = con.execute(MAP_DIM_SQL).df()
print("=== Map dimensions (map_size_x, map_size_y) ===")
print(map_dims.to_string(index=False))

# %%
# Verification: MMR data before plot
mmr_data = con.execute(
    "SELECT MMR FROM replay_players_raw WHERE MMR IS NOT NULL"
).df()
print(f"=== MMR data for plot ({len(mmr_data)} rows) ===")
print(mmr_data.describe().to_string())

# %%
# Histogram: MMR
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(mmr_data["MMR"], bins=50, edgecolor="black", alpha=0.7)
axes[0].set_title("MMR Distribution (histogram)")
axes[0].set_xlabel("MMR")
axes[0].set_ylabel("Frequency")
axes[1].boxplot(mmr_data["MMR"], vert=True)
axes[1].set_title("MMR Distribution (boxplot)")
axes[1].set_ylabel("MMR")
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_mmr_histogram.png", dpi=150)
plt.show()
plt.close()

# %%
# Verification: APM data before plot
apm_data = con.execute(
    "SELECT APM FROM replay_players_raw WHERE APM IS NOT NULL"
).df()
print(f"=== APM data for plot ({len(apm_data)} rows) ===")
print(apm_data.describe().to_string())

# %%
# Histogram: APM
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(apm_data["APM"], bins=50, edgecolor="black", alpha=0.7)
axes[0].set_title("APM Distribution (histogram)")
axes[0].set_xlabel("APM")
axes[0].set_ylabel("Frequency")
axes[1].boxplot(apm_data["APM"], vert=True)
axes[1].set_title("APM Distribution (boxplot)")
axes[1].set_ylabel("APM")
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_apm_histogram.png", dpi=150)
plt.show()
plt.close()

# %%
# Verification: SQ data before plot
sq_data = con.execute(
    "SELECT SQ FROM replay_players_raw WHERE SQ IS NOT NULL"
).df()
print(f"=== SQ data for plot ({len(sq_data)} rows) ===")
print(sq_data.describe().to_string())

# %%
# Histogram: SQ
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(sq_data["SQ"], bins=50, edgecolor="black", alpha=0.7)
axes[0].set_title("SQ Distribution (histogram)")
axes[0].set_xlabel("SQ")
axes[0].set_ylabel("Frequency")
axes[1].boxplot(sq_data["SQ"], vert=True)
axes[1].set_title("SQ Distribution (boxplot)")
axes[1].set_ylabel("SQ")
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_sq_histogram.png", dpi=150)
plt.show()
plt.close()

# %%
# Verification: supplyCappedPercent data before plot
sc_data = con.execute(
    "SELECT supplyCappedPercent FROM replay_players_raw WHERE supplyCappedPercent IS NOT NULL"
).df()
print(f"=== supplyCappedPercent data for plot ({len(sc_data)} rows) ===")
print(sc_data.describe().to_string())

# %%
# Histogram: supplyCappedPercent
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(sc_data["supplyCappedPercent"], bins=50, edgecolor="black", alpha=0.7)
axes[0].set_title("supplyCappedPercent Distribution (histogram)")
axes[0].set_xlabel("supplyCappedPercent")
axes[0].set_ylabel("Frequency")
axes[1].boxplot(sc_data["supplyCappedPercent"], vert=True)
axes[1].set_title("supplyCappedPercent Distribution (boxplot)")
axes[1].set_ylabel("supplyCappedPercent")
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_supplycapped_histogram.png", dpi=150)
plt.show()
plt.close()

# %%
# Verification: Duration data before plot
dur_data = con.execute(
    "SELECT elapsed_game_loops / 22.4 / 60.0 AS duration_min FROM struct_flat WHERE elapsed_game_loops IS NOT NULL"
).df()
print(f"=== Duration data for plot ({len(dur_data)} rows) ===")
print(dur_data.describe().to_string())

# %%
# Histogram: Duration in minutes
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(dur_data["duration_min"], bins=60, edgecolor="black", alpha=0.7)
ax.set_title("Game Duration Distribution (minutes)")
ax.set_xlabel("Duration (minutes)")
ax.set_ylabel("Frequency")
ax.axvline(dur_data["duration_min"].median(), color="red", ls="--", label=f"Median: {dur_data['duration_min'].median():.1f} min")
ax.legend()
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_duration_histogram.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ## Section E1: Skewness and Kurtosis (EDA Manual 3.1)

# %%
SKEW_KURT_COLS = [
    "MMR", "APM", "SQ", "supplyCappedPercent", "handicap",
    "startDir", "startLocX", "startLocY",
    "color_a", "color_b", "color_g", "color_r",
    "playerID", "userID",
]
skew_kurt_results = {}

for col in SKEW_KURT_COLS:
    sql = f"""
    SELECT
        ROUND(SKEWNESS({col}), 4) AS skewness,
        ROUND(KURTOSIS({col}), 4) AS kurtosis
    FROM replay_players_raw
    WHERE {col} IS NOT NULL
    """
    row = con.execute(sql).fetchone()
    skew_kurt_results[col] = {"skewness": row[0], "kurtosis": row[1]}

# elapsed_game_loops from struct_flat
_sk_row = con.execute("""
    SELECT
        ROUND(SKEWNESS(elapsed_game_loops), 4) AS skewness,
        ROUND(KURTOSIS(elapsed_game_loops), 4) AS kurtosis
    FROM struct_flat
    WHERE elapsed_game_loops IS NOT NULL
""").fetchone()
skew_kurt_results["elapsed_game_loops"] = {"skewness": _sk_row[0], "kurtosis": _sk_row[1]}

skew_kurt_df = pd.DataFrame(
    [{"column": k, **v} for k, v in skew_kurt_results.items()]
)
print("=== Skewness and Kurtosis ===")
print(skew_kurt_df.to_string(index=False))

# %% [markdown]
# ## Section E2: Zero Counts (EDA Manual 3.1)
#
# Count exact-zero values for each numeric column in `replay_players_raw`
# and the INT32_MIN sentinel for SQ (value = -2147483648).
# Also count exact-zero `elapsed_game_loops` in `replays_meta_raw`.

# %%
ZERO_COUNT_SQL = """\
SELECT
    COUNT(*) FILTER (WHERE MMR = 0) AS MMR_zero,
    COUNT(*) FILTER (WHERE APM = 0) AS APM_zero,
    COUNT(*) FILTER (WHERE SQ = 0) AS SQ_zero,
    COUNT(*) FILTER (WHERE SQ = -2147483648) AS SQ_sentinel,
    COUNT(*) FILTER (WHERE supplyCappedPercent = 0) AS supplyCappedPercent_zero,
    COUNT(*) FILTER (WHERE handicap = 0) AS handicap_zero,
    COUNT(*) FILTER (WHERE startDir = 0) AS startDir_zero,
    COUNT(*) FILTER (WHERE startLocX = 0) AS startLocX_zero,
    COUNT(*) FILTER (WHERE startLocY = 0) AS startLocY_zero,
    COUNT(*) FILTER (WHERE color_a = 0) AS color_a_zero,
    COUNT(*) FILTER (WHERE color_b = 0) AS color_b_zero,
    COUNT(*) FILTER (WHERE color_g = 0) AS color_g_zero,
    COUNT(*) FILTER (WHERE color_r = 0) AS color_r_zero,
    COUNT(*) FILTER (WHERE playerID = 0) AS playerID_zero,
    COUNT(*) FILTER (WHERE userID = 0) AS userID_zero
FROM replay_players_raw
"""
zero_counts = con.execute(ZERO_COUNT_SQL).df()
print("=== Zero counts (replay_players_raw) ===")
print(zero_counts.to_string(index=False))

# %%
DURATION_ZERO_COUNT_SQL = """\
SELECT
    COUNT(*) FILTER (WHERE elapsed_game_loops = 0) AS elapsed_game_loops_zero
FROM struct_flat
"""
duration_zero_counts = con.execute(DURATION_ZERO_COUNT_SQL).df()
print("=== Zero counts (elapsed_game_loops) ===")
print(duration_zero_counts.to_string(index=False))

# %% [markdown]
# ### MMR zero-spike interpretation

# %%
MMR_ZERO_BY_RESULT_SQL = """\
SELECT
    result,
    COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero_cnt,
    COUNT(*) AS total_cnt,
    ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 2)
        AS mmr_zero_pct
FROM replay_players_raw
GROUP BY result
ORDER BY total_cnt DESC
"""
mmr_zero_by_result = con.execute(MMR_ZERO_BY_RESULT_SQL).df()
print("=== MMR=0 by result ===")
print(mmr_zero_by_result.to_string(index=False))

# %%
MMR_ZERO_BY_LEAGUE_SQL = """\
SELECT
    highestLeague,
    COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero_cnt,
    COUNT(*) AS total_cnt,
    ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 2)
        AS mmr_zero_pct
FROM replay_players_raw
GROUP BY highestLeague
ORDER BY total_cnt DESC
"""
mmr_zero_by_league = con.execute(MMR_ZERO_BY_LEAGUE_SQL).df()
print("=== MMR=0 by highestLeague ===")
print(mmr_zero_by_league.to_string(index=False))
# Interpretation: if MMR=0 rate is uniform across all result categories,
# that supports the "not reported" hypothesis over a "loss-correlated sentinel" hypothesis.
_mmr_zero_pcts = mmr_zero_by_result["mmr_zero_pct"].dropna()
_mmr_zero_spread = round(float(_mmr_zero_pcts.max() - _mmr_zero_pcts.min()), 2)
print(
    f"\nMMR=0 rate spread across result categories: {_mmr_zero_spread} percentage points. "
    + (
        "Small spread supports 'sentinel = not reported' hypothesis."
        if _mmr_zero_spread < 5.0
        else "Large spread suggests possible correlation with outcome."
    )
)

# %%
DUPLICATE_CHECK_SQL = """\
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT filename || '|' || toon_id) AS distinct_player_rows,
    COUNT(*) - COUNT(DISTINCT filename || '|' || toon_id) AS duplicate_rows
FROM replay_players_raw
"""
duplicate_check = con.execute(DUPLICATE_CHECK_SQL).df()
print("=== Duplicate check (replay_players_raw) ===")
print(duplicate_check.to_string(index=False))

# %% [markdown]
# ## Section F: Temporal Range
#
# Use string-based MIN/MAX -- ISO 8601 strings sort lexicographically.
# No STRPTIME: the format `2016-07-29T04:50:12.5655603Z` contains
# 7-digit fractional seconds (.NET precision) that `%f` (6-digit) cannot handle.

# %%
TEMPORAL_RANGE_SQL = """\
SELECT
    MIN(details.timeUTC) AS earliest,
    MAX(details.timeUTC) AS latest,
    COUNT(DISTINCT SUBSTR(details.timeUTC, 1, 7)) AS distinct_months
FROM replays_meta_raw
"""
temporal_range = con.execute(TEMPORAL_RANGE_SQL).df()
print("=== Temporal range ===")
print(temporal_range.to_string(index=False))

# %%
# Time-series: replay counts by month
MONTHLY_COUNTS_SQL = """\
SELECT
    SUBSTR(details.timeUTC, 1, 7) AS month,
    COUNT(*) AS cnt
FROM replays_meta_raw
GROUP BY month
ORDER BY month
"""
monthly = con.execute(MONTHLY_COUNTS_SQL).df()
print("=== Monthly replay counts ===")
print(monthly.to_string(index=False))

# %%
fig, ax = plt.subplots(figsize=(14, 5))
ax.bar(range(len(monthly)), monthly["cnt"], tick_label=monthly["month"])
ax.set_title("Replays Over Time (by month)")
ax.set_xlabel("Month")
ax.set_ylabel("Replay Count")
ax.tick_params(axis="x", rotation=90, labelsize=7)
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_replays_over_time.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ## Section G: Error Column Census

# %%
ERROR_CENSUS_SQL = """\
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE gameEventsErr = TRUE) AS game_err,
    COUNT(*) FILTER (WHERE messageEventsErr = TRUE) AS msg_err,
    COUNT(*) FILTER (WHERE trackerEvtsErr = TRUE) AS tracker_err
FROM replays_meta_raw
"""
error_census = con.execute(ERROR_CENSUS_SQL).df()
print("=== Error column census ===")
print(error_census.to_string(index=False))

# %% [markdown]
# ## Section H: Dead/Constant/Near-Constant Field Detection
#
# Cardinality and uniqueness ratio (`COUNT(DISTINCT col) / COUNT(*)`)
# for all columns. Flag cardinality = 1 (constant) or uniqueness
# ratio < 0.001 (near-constant). Denominator is `COUNT(*)` (all rows,
# including NULLs) by design.

# %%
# replay_players_raw cardinality
RP_ALL_COLS = [
    "filename", "toon_id", "nickname", "playerID", "userID",
    "isInClan", "clanTag", "MMR", "race", "selectedRace",
    "handicap", "region", "realm", "highestLeague", "result",
    "APM", "SQ", "supplyCappedPercent", "startDir",
    "startLocX", "startLocY", "color_a", "color_b", "color_g", "color_r",
]

rp_card_records = []
for col in RP_ALL_COLS:
    sql = f"""
    SELECT
        COUNT(DISTINCT {col}) AS cardinality,
        COUNT(*) AS total_rows,
        ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio
    FROM replay_players_raw
    """
    row = con.execute(sql).fetchone()
    rp_card_records.append({
        "table": "replay_players_raw",
        "column": col,
        "cardinality": row[0],
        "total_rows": row[1],
        "uniqueness_ratio": row[2],
    })

rp_card_df = pd.DataFrame(rp_card_records)
print("=== replay_players_raw cardinality ===")
print(rp_card_df.to_string(index=False))

# %%
# struct_flat (replays_meta_raw) cardinality
SF_COLS = [
    "game_speed", "is_blizzard_map", "time_utc",
    "elapsed_game_loops", "game_version_header",
    "base_build", "data_build", "game_version_meta",
    "map_name", "max_players", "game_speed_init",
    "is_blizzard_map_init", "map_size_x", "map_size_y",
    "gameEventsErr", "messageEventsErr", "trackerEvtsErr", "filename",
]

sf_card_records = []
for col in SF_COLS:
    sql = f"""
    SELECT
        COUNT(DISTINCT {col}) AS cardinality,
        COUNT(*) AS total_rows,
        ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio
    FROM struct_flat
    """
    row = con.execute(sql).fetchone()
    sf_card_records.append({
        "table": "replays_meta_raw (struct_flat)",
        "column": col,
        "cardinality": row[0],
        "total_rows": row[1],
        "uniqueness_ratio": row[2],
    })

sf_card_df = pd.DataFrame(sf_card_records)
print("=== struct_flat (replays_meta_raw) cardinality ===")
print(sf_card_df.to_string(index=False))

# %%
# Combine and flag dead/constant/near-constant
all_card_df = pd.concat([rp_card_df, sf_card_df], ignore_index=True)

flagged = all_card_df[
    (all_card_df["cardinality"] == 1)
    | (all_card_df["uniqueness_ratio"] < 0.001)
].copy()
flagged["flag"] = "near-constant"
flagged.loc[flagged["cardinality"] == 1, "flag"] = "constant"
print("=== Flagged dead/constant/near-constant columns ===")
if len(flagged) > 0:
    print(flagged.to_string(index=False))
else:
    print("(none)")

# %% [markdown]
# **Threshold sensitivity note:** The uniqueness_ratio < 0.001 threshold
# is appropriate for this dataset (N=44,817 rows). For larger datasets
# (N > 1M), the same threshold would flag more columns as near-constant
# because uniqueness_ratio = cardinality / N decreases with N even for
# columns with stable cardinality. Re-evaluate the threshold for each
# dataset based on its row count and the cardinality distribution.

# %%
# Field classification: pre-game / in-game / identifier / target / constant
# Covers all 25 replay_players_raw columns and all struct_flat-extracted fields.
# Purpose: downstream steps use this dict to select features without parsing prose.
FIELD_CLASSIFICATION = {
    "replay_players_raw": {
        "identifier": ["filename", "toon_id", "nickname", "playerID", "userID"],
        "pre_game": [
            "MMR", "race", "selectedRace", "handicap", "region", "realm",
            "highestLeague", "isInClan", "clanTag", "startDir", "startLocX",
            "startLocY", "color_a", "color_b", "color_g", "color_r",
        ],
        "in_game": ["APM", "SQ", "supplyCappedPercent"],
        "target": ["result"],
    },
    "replays_meta_raw_struct_flat": {
        "identifier": ["filename"],
        "pre_game": [
            "time_utc", "game_version_header", "base_build", "data_build",
            "game_version_meta", "map_name", "max_players", "map_size_x",
            "map_size_y", "is_blizzard_map", "is_blizzard_map_init",
        ],
        "in_game": ["elapsed_game_loops"],
        "constant": [
            "game_speed", "game_speed_init", "gameEventsErr",
            "messageEventsErr", "trackerEvtsErr",
        ],
    },
    "classification_notes": {
        "pre_game": (
            "Available before match start. Usable as prediction features "
            "without temporal leakage."
        ),
        "in_game": (
            "Computed from replay actions; available only post-game. Using these "
            "as features requires in-game prediction framing (Phase 02 decision)."
        ),
        "identifier": "Player/replay identity columns. Not features.",
        "target": "Prediction target. Never a feature.",
        "constant": "Single-value columns. No predictive information.",
    },
}
# Sanity check: replay_players_raw total column count must be 25
_rp_total = sum(
    len(v)
    for k, v in FIELD_CLASSIFICATION["replay_players_raw"].items()
)
assert _rp_total == 25, (
    f"replay_players_raw column count mismatch: expected 25, got {_rp_total}"
)
print(f"FIELD_CLASSIFICATION replay_players_raw column count: {_rp_total} (OK)")

# %% [markdown]
# ## Section 9: Write JSON and Markdown Artifacts

# %%
# Build JSON artifact
findings = {
    "step": "01_02_04",
    "dataset": "sc2egset",
    "db_memory_footprint_bytes": db_size_bytes,
    "null_census": {
        "replay_players_raw": {
            "total_rows": total_rows,
            "columns": null_census_df.to_dict(orient="records"),
        },
        "replays_meta_raw_filename": meta_fn_null.to_dict(orient="records")[0],
        "struct_flat": {
            "total_rows": sf_total_rows,
            "columns": sf_null_census_df.to_dict(orient="records"),
        },
    },
    "result_distribution": result_dist.to_dict(orient="records"),
    "non_2p_results": non_2p_results.to_dict(orient="records"),
    "categorical_profiles": {},
    "numeric_stats": {},
    "temporal_range": temporal_range.to_dict(orient="records")[0],
    "monthly_counts": monthly.to_dict(orient="records"),
    "error_census": error_census.to_dict(orient="records")[0],
    "cardinality": all_card_df.to_dict(orient="records"),
    "flagged_columns": flagged.to_dict(orient="records") if len(flagged) > 0 else [],
    "struct_flat_shape": list(struct_flat.shape),
    "game_speed_assertion": "PASSED -- all Faster",
    "duration_stats": {},
    "map_dimensions": map_dims.to_dict(orient="records"),
    "plots": [],
}
sql_queries: dict = {}

# %%
# Add categorical profiles to findings
for col, df in rp_cat_results.items():
    findings["categorical_profiles"][col] = df.to_dict(orient="records")
for col, df in meta_cat_results.items():
    findings["categorical_profiles"][col] = df.to_dict(orient="records")

# Add numeric stats
for col, df in rp_num_stats.items():
    findings["numeric_stats"][col] = df.to_dict(orient="records")[0]

# Add duration stats
findings["duration_stats"] = duration_stats.to_dict(orient="records")[0]

# Add zero counts
findings["zero_counts"] = {
    "replay_players_raw": zero_counts.to_dict(orient="records")[0],
    "replays_meta_raw": duration_zero_counts.to_dict(orient="records")[0],
}

# Add duplicate check
findings["duplicate_check"] = duplicate_check.to_dict(orient="records")[0]

# Add field classification
findings["field_classification"] = FIELD_CLASSIFICATION

# Add Undecided/Tie context
findings["undecided_tie_context"] = undecided_tie_context.to_dict(orient="records")

# Add new pass-2 analytics
findings["skew_kurtosis"] = skew_kurt_results
findings["numeric_stats_SQ_no_sentinel"] = sq_no_sentinel.to_dict(orient="records")[0]
findings["mmr_zero_interpretation"] = {
    "by_result": mmr_zero_by_result.to_dict(orient="records"),
    "by_highestLeague": mmr_zero_by_league.to_dict(orient="records"),
}
findings["struct_flat_completeness_note"] = sf_completeness_note
findings["isInClan_distribution"] = is_in_clan_df.to_dict(orient="records")
findings["clanTag_top20"] = clan_tag_top20_df.to_dict(orient="records")

# %%
# Collect plot filenames
plot_files = sorted(plots_dir.glob("01_02_04_*.png"))
findings["plots"] = [f.name for f in plot_files]
print(f"Plot files: {findings['plots']}")

# %% [markdown]
# ## Systematic Column Profile (Top-5 / Bottom-5)
#
# EDA Manual Section 3.1: top-5 / bottom-5 for every column.
# Performance note: game_events_raw (608M rows) may take several minutes
# per column for GROUP BY on high-cardinality columns (loop, evtTypeName).
# event_data is excluded from top_n/bottom_n (JSON strings — GROUP BY
# on 608M opaque payloads is semantically useless and OOM-risk).
# Elapsed time printed per column; gate: elapsed < 600s per column.
# Invariant #6: all SQL captured in sql_queries for artifact emission.

# %%
for _tbl in [
    "replay_players_raw",
    "replays_meta_raw",
    "game_events_raw",
    "tracker_events_raw",
    "message_events_raw",
    "map_aliases_raw",
]:
    _skip = {"event_data"} if _tbl == "game_events_raw" else None
    _specs = [
        {"name": r["column_name"], "dtype": r["column_type"]}
        for _, r in con.execute(f"DESCRIBE {_tbl}").df().iterrows()
    ]
    _census = profile_table(con, _tbl, _specs, skip_topn_columns=_skip)
    findings[f"{_tbl}_census"] = _census["profiles"]
    for _col, _sqls in _census["sql_registry"].items():
        sql_queries[f"census.{_tbl}.{_col}.null"] = _sqls["sql_null"]
        sql_queries[f"census.{_tbl}.{_col}.top_n"] = _sqls["sql_top_n"]
        sql_queries[f"census.{_tbl}.{_col}.bottom_n"] = _sqls["sql_bottom_n"]
    print(f"census complete: {_tbl} ({len(_census['profiles'])} columns)")

# %%
# Write JSON
findings["sql_queries"] = sql_queries
json_path = artifacts_dir / "01_02_04_univariate_census.json"
json_path.write_text(json.dumps(findings, indent=2, default=str))
print(f"JSON artifact written: {json_path}")

# %%
# Build markdown artifact with all SQL verbatim (Invariant #6)
md_lines = [
    "# Step 01_02_04 -- Metadata STRUCT Extraction & Replay-Level EDA",
    "",
    "**Dataset:** sc2egset",
    f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
    "",
    "---",
    "",
    "## Section A: STRUCT Field Extraction",
    "",
    "```sql",
    STRUCT_FLAT_SQL.strip(),
    "```",
    "",
    f"Result shape: {struct_flat.shape}",
    "",
    "## Database Memory Footprint",
    "",
    f"DuckDB file size: {db_size_bytes:,} bytes ({db_size_mb} MB)",
    "",
]

# %%
md_lines += [
    "## Section B: Full NULL Census",
    "",
    "### replay_players_raw",
    "",
    "```sql",
    NULL_CENSUS_SQL.strip(),
    "```",
    "",
    null_census_df.to_markdown(index=False),
    "",
    "### replays_meta_raw.filename",
    "",
    "```sql",
    META_FILENAME_NULL_SQL.strip(),
    "```",
    "",
    meta_fn_null.to_markdown(index=False),
    "",
    "### struct_flat NULL census",
    "",
    "```sql",
    STRUCT_FLAT_NULL_CENSUS_SQL.strip(),
    "```",
    "",
    sf_null_census_df.to_markdown(index=False),
    "",
    "### struct_flat completeness note",
    "",
    (
        "All 17 struct_flat columns have 0 NULLs. No missingness co-occurrence to analyze."
        if _sf_all_zero_nulls
        else "struct_flat has columns with NULLs -- see co-occurrence matrix in JSON artifact."
    ),
    "",
]

# %%
md_lines += [
    "## Section C: Target Variable",
    "",
    "```sql",
    RESULT_DIST_SQL.strip(),
    "```",
    "",
    result_dist.to_markdown(index=False),
    "",
    "### Non-2-player replay results",
    "",
    "```sql",
    NON_2P_RESULT_SQL.strip(),
    "```",
    "",
    non_2p_results.to_markdown(index=False),
    "",
    "### Undecided/Tie replay context (corrective query)",
    "",
    "```sql",
    UNDECIDED_TIE_CONTEXT_SQL.strip(),
    "```",
    "",
    undecided_tie_context.to_markdown(index=False),
    "",
    (
        f"Finding: All {len(undecided_tie_context)} rows "
        f"({'Undecided' if (undecided_tie_context['result'] == 'Undecided').all() else 'Undecided and Tie'}) "
        f"came from replays with player_row_count="
        f"{undecided_tie_context['player_row_count'].unique().tolist()} "
        f"and max_players={undecided_tie_context['max_players'].unique().tolist()}."
    ),
    "",
    (
        "Note: The OR-condition non-2-player query above returned only Win/Loss. "
        "Undecided/Tie rows are present in standard 2-player replays per this corrective query."
    ),
    "",
]

# %%
md_lines += [
    "## Section D: Categorical Field Profiles",
    "",
]
for col in RP_CAT_COLS:
    cat_sql = f"""\
SELECT {col}, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY {col}
ORDER BY cnt DESC"""
    md_lines += [
        f"### {col}",
        "",
        "```sql",
        cat_sql,
        "```",
        "",
        rp_cat_results[col].to_markdown(index=False),
        "",
    ]

# %%
md_lines += [
    "### isInClan distribution",
    "",
    "```sql",
    IS_IN_CLAN_SQL.strip(),
    "```",
    "",
    is_in_clan_df.to_markdown(index=False),
    "",
    "### clanTag top-20",
    "",
    "```sql",
    CLAN_TAG_TOP20_SQL.strip(),
    "```",
    "",
    clan_tag_top20_df.to_markdown(index=False),
    "",
]

# %%
for col in META_CAT_COLS:
    if col == "map_name":
        cat_sql = f"""\
SELECT {col}, COUNT(*) AS cnt
FROM struct_flat
GROUP BY {col}
ORDER BY cnt DESC
LIMIT 20"""
    else:
        cat_sql = f"""\
SELECT {col}, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM struct_flat
GROUP BY {col}
ORDER BY cnt DESC"""
    md_lines += [
        f"### {col}",
        "",
        "```sql",
        cat_sql,
        "```",
        "",
        meta_cat_results[col].to_markdown(index=False),
        "",
    ]

# %%
md_lines += [
    "### Game Speed Assertion",
    "",
    "```python",
    'assert set(speed_counts["game_speed"].dropna()) == {"Faster"}',
    "```",
    "",
    "**PASSED** -- all replays confirmed Faster speed.",
    "",
]

# %%
md_lines += [
    "## Section E: Numeric Descriptive Statistics",
    "",
    (
        "Note: APM, SQ, and supplyCappedPercent are in-game-only fields. "
        "See `field_classification` in the JSON artifact for the full "
        "pre-game/in-game/identifier/target/constant taxonomy."
    ),
    "",
]
for col in RP_NUM_COLS:
    num_sql = f"""\
SELECT
    MIN({col}) AS min_val, MAX({col}) AS max_val,
    ROUND(AVG({col}), 2) AS mean_val,
    ROUND(MEDIAN({col}), 2) AS median_val,
    ROUND(STDDEV({col}), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {col}) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col}) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col}) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {col}) AS p95
FROM replay_players_raw
WHERE {col} IS NOT NULL"""
    md_lines += [
        f"### {col}",
        "",
        "```sql",
        num_sql,
        "```",
        "",
        rp_num_stats[col].to_markdown(index=False),
        "",
    ]

# %%
md_lines += [
    "### elapsed_game_loops (duration)",
    "",
    "```sql",
    DURATION_STATS_SQL.strip(),
    "```",
    "",
    duration_stats.to_markdown(index=False),
    "",
    "### Map Dimensions",
    "",
    "```sql",
    MAP_DIM_SQL.strip(),
    "```",
    "",
    map_dims.to_markdown(index=False),
    "",
    "### SQ stats excluding INT32_MIN sentinel",
    "",
    "```sql",
    SQ_NO_SENTINEL_SQL.strip(),
    "```",
    "",
    sq_no_sentinel.to_markdown(index=False),
    "",
    (
        "The main SQ descriptive statistics (Section E) are contaminated by 2 rows "
        "containing the INT32_MIN sentinel value (-2147483648). The stats above "
        "exclude those rows. The sentinel causes the main SQ mean and stddev to be "
        "misleading. Refer to the sentinel-excluded stats above for the clean SQ "
        "distribution's actual median and range."
    ),
    "",
]

# %%
md_lines += [
    "## Section E1: Skewness and Kurtosis (EDA Manual 3.1)",
    "",
    "SQL template (one query per column):",
    "",
    "```sql",
    "SELECT",
    "    ROUND(SKEWNESS({col}), 4) AS skewness,",
    "    ROUND(KURTOSIS({col}), 4) AS kurtosis",
    "FROM {table}",
    "WHERE {col} IS NOT NULL",
    "```",
    "",
    skew_kurt_df.to_markdown(index=False),
    "",
]

# %%
md_lines += [
    "## Section E2: Zero Counts (EDA Manual 3.1)",
    "",
    "### replay_players_raw zero counts",
    "",
    "```sql",
    ZERO_COUNT_SQL.strip(),
    "```",
    "",
    zero_counts.to_markdown(index=False),
    "",
    "### elapsed_game_loops zero count",
    "",
    "```sql",
    DURATION_ZERO_COUNT_SQL.strip(),
    "```",
    "",
    duration_zero_counts.to_markdown(index=False),
    "",
    "### MMR zero-spike interpretation",
    "",
    "```sql",
    MMR_ZERO_BY_RESULT_SQL.strip(),
    "```",
    "",
    mmr_zero_by_result.to_markdown(index=False),
    "",
    "```sql",
    MMR_ZERO_BY_LEAGUE_SQL.strip(),
    "```",
    "",
    mmr_zero_by_league.to_markdown(index=False),
    "",
    (
        "Interpretation: If MMR=0 rate is uniform across all result categories (~83%), "
        "that supports the 'sentinel = not reported' hypothesis rather than a "
        "loss-correlated sentinel."
    ),
    "",
    "## Section E3: Duplicate Detection",
    "",
    "```sql",
    DUPLICATE_CHECK_SQL.strip(),
    "```",
    "",
    duplicate_check.to_markdown(index=False),
    "",
]

# %%
md_lines += [
    "## Section F: Temporal Range",
    "",
    "```sql",
    TEMPORAL_RANGE_SQL.strip(),
    "```",
    "",
    temporal_range.to_markdown(index=False),
    "",
    "### Monthly Replay Counts",
    "",
    "```sql",
    MONTHLY_COUNTS_SQL.strip(),
    "```",
    "",
    monthly.to_markdown(index=False),
    "",
]

# %%
md_lines += [
    "## Section G: Error Column Census",
    "",
    "```sql",
    ERROR_CENSUS_SQL.strip(),
    "```",
    "",
    error_census.to_markdown(index=False),
    "",
]

# %%
md_lines += [
    "## Section H: Dead/Constant/Near-Constant Field Detection",
    "",
    "Cardinality query (per column):",
    "",
    "```sql",
    "SELECT '{col}' AS column_name,",
    "       COUNT(DISTINCT {col}) AS cardinality,",
    "       COUNT(*) AS total_rows,",
    "       ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6)"
    " AS uniqueness_ratio",
    "FROM {table}",
    "```",
    "",
    "### Full Cardinality Table",
    "",
    all_card_df.to_markdown(index=False),
    "",
    "### Flagged Columns",
    "",
    "### Interpretation Note",
    "",
    (
        "The uniqueness_ratio < 0.001 threshold (EDA Manual Section 3.3) flags all "
        "low-cardinality columns mechanically. This includes:"
    ),
    "",
    (
        "- **Expected categoricals** (race, selectedRace, highestLeague, region, realm, "
        "result, isInClan, color_*, startDir): These are inherently low-cardinality "
        "fields in any game dataset. Flagging them is a consequence of the threshold "
        "definition, not a data quality concern. Their value distributions are profiled "
        "in Section D."
    ),
    "",
    (
        "- **Genuinely constant/degenerate** (game_speed, game_speed_init, "
        "gameEventsErr, messageEventsErr, trackerEvtsErr): cardinality=1 fields "
        "that carry zero information and should be excluded from feature engineering."
    ),
    "",
    (
        "- **Low-cardinality numerics** (playerID, userID, handicap): "
        "playerID ranges 1-16 (slot index within replay, not a player identifier); "
        "userID is similarly replay-scoped; handicap is 100 for all but 1 row. "
        "These warrant investigation in cleaning (01_04) but are not data quality "
        "defects per se."
    ),
    "",
    (
        "Downstream steps should use the `field_classification` in the JSON artifact "
        "rather than the near-constant flag to decide feature eligibility."
    ),
    "",
    (
        "**Threshold sensitivity note:** The uniqueness_ratio < 0.001 threshold "
        "is appropriate for this dataset (N=44,817 rows). For larger datasets "
        "(N > 1M), the same threshold would flag more columns as near-constant "
        "because uniqueness_ratio = cardinality / N decreases with N even for "
        "columns with stable cardinality. Re-evaluate the threshold for each "
        "dataset based on its row count and the cardinality distribution."
    ),
    "",
]
if len(flagged) > 0:
    md_lines.append(flagged.to_markdown(index=False))
else:
    md_lines.append("(none)")
md_lines.append("")

# %%
# Write markdown
md_path = artifacts_dir / "01_02_04_univariate_census.md"
md_path.write_text("\n".join(md_lines))
print(f"Markdown artifact written: {md_path}")

# %%
con.close()
print("Done. All artifacts written.")
