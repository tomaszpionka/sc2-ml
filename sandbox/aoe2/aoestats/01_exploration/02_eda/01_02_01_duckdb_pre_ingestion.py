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
# # Step 01_02_01 -- DuckDB Pre-Ingestion: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** aoestats
# **Question:** What does the raw data look like before we commit to an
# ingestion strategy? Are there variant column types across weekly files,
# type promotions, or NULL patterns we need to handle?
# **Invariants applied:** #6 (reproducibility), #9 (step scope)
# **Step scope:** query

# %%

import duckdb
import json

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOESTATS_RAW_DIR
from rts_predict.games.aoe2.datasets.aoestats.pre_ingestion import (
    run_variant_census,
    run_smoke_test,
)

logger = setup_notebook_logging()
logger.info("Source: %s", AOESTATS_RAW_DIR)

# %% [markdown]
# ## 1. Pre-ingestion variant census (pyarrow)

# %%
census = run_variant_census(AOESTATS_RAW_DIR)
print(f"Matches variant columns: {list(census['matches']['variant_columns'].keys())}")
print(f"Players variant columns: {list(census['players']['variant_columns'].keys())}")

for subdir in ("matches", "players"):
    print(f"\n{subdir}:")
    for col, types in census[subdir]["variant_columns"].items():
        print(f"  {col}: {types}")

# %% [markdown]
# ## 2. Smoke test

# %%
con = duckdb.connect(":memory:")
smoke = run_smoke_test(con, AOESTATS_RAW_DIR)
print(f"Smoke matches: {smoke['matches']['row_count']} rows, {smoke['matches']['column_count']} cols")
print(f"Smoke players: {smoke['players']['row_count']} rows, {smoke['players']['column_count']} cols")

# %% [markdown]
# ## 3. DESCRIBE -- column names, types, nullability

# %%
for table_name in smoke:
    print(f"\n{'='*60}")
    print(f"  DESCRIBE {table_name}")
    print(f"{'='*60}")
    files = smoke[table_name]["files_sampled"]
    full_paths = [str(AOESTATS_RAW_DIR / table_name / f) for f in files]
    file_list = ", ".join(f"'{p}'" for p in full_paths)
    con.sql(
        f"DESCRIBE SELECT * FROM read_parquet([{file_list}], "
        f"union_by_name=true, filename=true)"
    ).show()

# %% [markdown]
# ## 4. Row preview -- SELECT * LIMIT 10

# %%
for table_name in smoke:
    print(f"\n{'='*60}")
    print(f"  {table_name}: {smoke[table_name]['row_count']} rows, {smoke[table_name]['column_count']} cols")
    print(f"{'='*60}")
    files = smoke[table_name]["files_sampled"]
    full_paths = [str(AOESTATS_RAW_DIR / table_name / f) for f in files]
    file_list = ", ".join(f"'{p}'" for p in full_paths)
    con.sql(
        f"SELECT * FROM read_parquet([{file_list}], "
        f"union_by_name=true, filename=true) LIMIT 10"
    ).show()

# %% [markdown]
# ## 5. Variant columns -- types and NULL counts per week (matches)

# %%
con.sql("""
    SELECT
        filename.split('matches/')[2][:10] AS file_week,
        COUNT(*) AS rows,
        COUNT(raw_match_type) AS raw_match_type_nn,
        COUNT(started_timestamp) AS started_timestamp_nn,
        COUNT(duration) AS duration_nn,
        COUNT(irl_duration) AS irl_duration_nn,
        typeof(duration) AS duration_type,
        typeof(irl_duration) AS irl_duration_type
    FROM read_parquet(
        '{glob}',
        union_by_name=true, filename=true
    )
    GROUP BY file_week
    ORDER BY file_week
""".format(glob=str(AOESTATS_RAW_DIR / "matches" / "*.parquet"))).show()

# %% [markdown]
# ## 6. Variant columns -- types and NULL counts per week (players)

# %%
con.sql("""
    SELECT
        filename.split('players/')[2][:10] AS file_week,
        COUNT(*) AS rows,
        COUNT(profile_id) AS profile_id_nn,
        COUNT(feudal_age_uptime) AS feudal_nn,
        COUNT(castle_age_uptime) AS castle_nn,
        COUNT(imperial_age_uptime) AS imperial_nn,
        COUNT(opening) AS opening_nn,
        typeof(profile_id) AS profile_id_type,
        typeof(feudal_age_uptime) AS feudal_type
    FROM read_parquet(
        '{glob}',
        union_by_name=true, filename=true
    )
    GROUP BY file_week
    ORDER BY file_week
""".format(glob=str(AOESTATS_RAW_DIR / "players" / "*.parquet"))).show()

# %% [markdown]
# ## 7. Ingestion readiness checks
#
# Targeted queries against the full file corpus to resolve open questions
# from the smoke test. Each query reads raw files directly (no persistent DB).

# %% [markdown]
# ### 7a. profile_id precision -- is DOUBLE safe or do we need BIGINT?

# %%
con.sql("""
    SELECT
        MIN(profile_id) AS min_id,
        MAX(profile_id) AS max_id,
        COUNT(*) FILTER (WHERE profile_id IS NULL) AS null_count,
        COUNT(*) FILTER (
            WHERE profile_id IS NOT NULL
              AND profile_id != CAST(CAST(profile_id AS BIGINT) AS DOUBLE)
        ) AS lossy_cast_count,
        COUNT(*) AS total
    FROM read_parquet(
        '{glob}', union_by_name=true
    )
""".format(glob=str(AOESTATS_RAW_DIR / "players" / "*.parquet"))).show()

# %% [markdown]
# ### 7b. duration / irl_duration value range -- any negatives or extremes?

# %%
con.sql("""
    SELECT
        MIN(duration) AS min_dur_ns,
        MAX(duration) AS max_dur_ns,
        MIN(duration / 1e9) AS min_dur_sec,
        MAX(duration / 1e9) AS max_dur_sec,
        COUNT(*) FILTER (WHERE duration < 0) AS negative_dur,
        COUNT(*) FILTER (WHERE duration IS NULL) AS null_dur,
        MIN(irl_duration) AS min_irl_ns,
        MAX(irl_duration) AS max_irl_ns,
        MIN(irl_duration / 1e9) AS min_irl_sec,
        MAX(irl_duration / 1e9) AS max_irl_sec,
        COUNT(*) FILTER (WHERE irl_duration < 0) AS negative_irl,
        COUNT(*) FILTER (WHERE irl_duration IS NULL) AS null_irl
    FROM read_parquet(
        '{glob}', union_by_name=true
    )
""".format(glob=str(AOESTATS_RAW_DIR / "matches" / "*.parquet"))).show()

# %% [markdown]
# ### 7c. Join key (game_id) and prediction target (winner) NULL rates

# %%
con.sql("""
    SELECT
        'matches' AS source,
        COUNT(*) AS total,
        COUNT(game_id) AS game_id_nn,
        COUNT(*) - COUNT(game_id) AS game_id_null
    FROM read_parquet('{matches_glob}', union_by_name=true)
    UNION ALL
    SELECT
        'players' AS source,
        COUNT(*) AS total,
        COUNT(game_id) AS game_id_nn,
        COUNT(*) - COUNT(game_id) AS game_id_null
    FROM read_parquet('{players_glob}', union_by_name=true)
""".format(
    matches_glob=str(AOESTATS_RAW_DIR / "matches" / "*.parquet"),
    players_glob=str(AOESTATS_RAW_DIR / "players" / "*.parquet"),
)).show()

# %%
con.sql("""
    SELECT
        COUNT(*) AS total_players,
        COUNT(winner) AS winner_nn,
        COUNT(*) - COUNT(winner) AS winner_null,
        ROUND(100.0 * (COUNT(*) - COUNT(winner)) / COUNT(*), 2) AS winner_null_pct
    FROM read_parquet('{glob}', union_by_name=true)
""".format(glob=str(AOESTATS_RAW_DIR / "players" / "*.parquet"))).show()

# %% [markdown]
# ### 7d. game_id uniqueness -- duplicates in matches?

# %%
con.sql("""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT game_id) AS distinct_game_ids,
        COUNT(*) - COUNT(DISTINCT game_id) AS duplicate_rows
    FROM read_parquet('{glob}', union_by_name=true)
""".format(glob=str(AOESTATS_RAW_DIR / "matches" / "*.parquet"))).show()

# %% [markdown]
# ### 7e. overview.json -- DESCRIBE and preview

# %%
con.sql("""
    DESCRIBE SELECT * FROM read_json_auto('{path}')
""".format(path=str(AOESTATS_RAW_DIR / "overview" / "overview.json"))).show()

con.sql("""
    SELECT * FROM read_json_auto('{path}')
""".format(path=str(AOESTATS_RAW_DIR / "overview" / "overview.json"))).show()

# %% [markdown]
# ## 8. Findings and ingestion strategy recommendation
#
# Summarize all findings from sections 1-7 here after execution.
# Key decisions to record:
#
# - **profile_id:** BIGINT or DOUBLE? (based on 7a lossy_cast_count)
# - **duration/irl_duration:** keep as BIGINT nanoseconds or convert? (based on 7b range)
# - **game_id:** needs dedup at ingestion? (based on 7d)
# - **winner NULLs:** acceptable rate? (based on 7c)
# - **Proposed DDL** for matches_raw, players_raw, overviews_raw

# %% [markdown]
# ## Write artifact

# %%
artifacts_dir = (
    get_reports_dir("aoe2", "aoestats")
    / "artifacts" / "01_exploration" / "02_eda"
)
artifacts_dir.mkdir(parents=True, exist_ok=True)

winner_null_df = con.sql("""
    SELECT
        COUNT(*) AS total_players,
        COUNT(winner) AS winner_nn,
        ROUND(100.0 * (COUNT(*) - COUNT(winner)) / COUNT(*), 2) AS winner_null_pct
    FROM read_parquet('{glob}', union_by_name=true)
""".format(glob=str(AOESTATS_RAW_DIR / "players" / "*.parquet"))).fetchdf()

game_id_dedup_df = con.sql("""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT game_id) AS distinct_game_ids,
        COUNT(*) - COUNT(DISTINCT game_id) AS duplicate_rows
    FROM read_parquet('{glob}', union_by_name=true)
""".format(glob=str(AOESTATS_RAW_DIR / "matches" / "*.parquet"))).fetchdf()

artifact_data = {
    "step": "01_02_01",
    "dataset": "aoestats",
    "variant_column_census": {
        "matches": {"variant_columns": census["matches"]["variant_columns"]},
        "players": {"variant_columns": census["players"]["variant_columns"]},
    },
    "smoke_test": {
        "matches": {
            "row_count": smoke["matches"]["row_count"],
            "column_count": smoke["matches"]["column_count"],
        },
        "players": {
            "row_count": smoke["players"]["row_count"],
            "column_count": smoke["players"]["column_count"],
        },
    },
    "winner_null_rates": winner_null_df.to_dict(orient="records")[0],
    "game_id_dedup": game_id_dedup_df.to_dict(orient="records")[0],
}

artifact_path = artifacts_dir / "01_02_01_duckdb_pre_ingestion.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2, default=str))
logger.info("Artifact written: %s", artifact_path)

# %%
winner_row = winner_null_df.iloc[0]
dedup_row = game_id_dedup_df.iloc[0]

md_lines = [
    "# Step 01_02_01 -- DuckDB Pre-Ingestion: aoestats\n",
    "",
    "## Variant column census\n",
    "",
    f"- Matches variant columns: {list(census['matches']['variant_columns'].keys())}",
    f"- Players variant columns: {list(census['players']['variant_columns'].keys())}",
    "",
    "## Smoke test\n",
    "",
    f"- matches: {smoke['matches']['row_count']:,} rows, {smoke['matches']['column_count']} cols",
    f"- players: {smoke['players']['row_count']:,} rows, {smoke['players']['column_count']} cols",
    "",
    "## winner NULL rates\n",
    "",
    f"- Total players: {int(winner_row['total_players']):,}",
    f"- winner NULLs: {int(winner_row['total_players']) - int(winner_row['winner_nn']):,}"
    f" ({float(winner_row['winner_null_pct']):.2f}%)",
    "",
    "## game_id dedup\n",
    "",
    f"- Total rows: {int(dedup_row['total_rows']):,}",
    f"- Distinct game_ids: {int(dedup_row['distinct_game_ids']):,}",
    f"- Duplicate rows: {int(dedup_row['duplicate_rows']):,}",
]

md_path = artifacts_dir / "01_02_01_duckdb_pre_ingestion.md"
md_path.write_text("\n".join(md_lines))
logger.info("Report written: %s", md_path)

# %%
con.close()
