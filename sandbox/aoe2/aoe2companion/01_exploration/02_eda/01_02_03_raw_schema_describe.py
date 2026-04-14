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
# # Step 01_02_03 -- Raw Schema DESCRIBE: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** aoe2companion
# **Question:** What are the column names and types for every raw data source in
# aoe2companion? Since step 01_02_02 has not been executed there is no persistent
# DuckDB yet; this notebook uses in-memory DuckDB + direct file reads with
# `LIMIT 0` to obtain schema-only results without loading row data.
# **Invariants applied:** #6 (reproducibility — SQL inlined in artifact), #9 (step scope: query)
# **Step scope:** query
# **Type:** Read-only — no DuckDB writes, no new tables, no schema changes

# %%
import json

import duckdb

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import (
    AOE2COMPANION_RAW_MATCHES_DIR,
    AOE2COMPANION_RAW_LEADERBOARDS_DIR,
    AOE2COMPANION_RAW_PROFILES_DIR,
    AOE2COMPANION_RAW_RATINGS_DIR,
)

logger = setup_notebook_logging()
logger.info("Matches dir: %s", AOE2COMPANION_RAW_MATCHES_DIR)
logger.info("Ratings dir: %s", AOE2COMPANION_RAW_RATINGS_DIR)
logger.info("Leaderboards dir: %s", AOE2COMPANION_RAW_LEADERBOARDS_DIR)
logger.info("Profiles dir: %s", AOE2COMPANION_RAW_PROFILES_DIR)

# %% [markdown]
# ## 1. Connect to in-memory DuckDB

# %%
con = duckdb.connect(":memory:")
print("Connected to in-memory DuckDB")

# %% [markdown]
# ## 2. DESCRIBE all raw sources
#
# Sources covered:
# - `matches`: glob `*.parquet` with `binary_as_string=True, union_by_name=True, filename=True`
# - `ratings`: glob `*.csv` with explicit dtypes + `union_by_name=True, filename=True`
# - `leaderboards`: single file `leaderboard.parquet` with `binary_as_string=True, filename=True`
# - `profiles`: single file `profile.parquet` with `binary_as_string=True, filename=True`
#
# `LIMIT 0` makes each query schema-only — no row data is loaded into memory.

# %%
schemas: dict[str, list[dict]] = {}

# --- matches ---
matches_glob = str(AOE2COMPANION_RAW_MATCHES_DIR / "*.parquet")
df_matches = con.execute("""
    DESCRIBE SELECT * FROM read_parquet(?, binary_as_string=true, union_by_name=true, filename=true) LIMIT 0
""", [matches_glob]).df()
schemas["matches"] = df_matches.to_dict(orient="records")
print(f"\n=== DESCRIBE matches ({len(df_matches)} columns) ===")
print(df_matches.to_string(index=False))

# %%
# --- ratings ---
ratings_glob = str(AOE2COMPANION_RAW_RATINGS_DIR / "*.csv")
df_ratings = con.execute("""
    DESCRIBE SELECT * FROM read_csv(
        ?,
        union_by_name=true,
        filename=true,
        dtypes={
            'profile_id': 'BIGINT',
            'games': 'BIGINT',
            'rating': 'BIGINT',
            'date': 'TIMESTAMP',
            'leaderboard_id': 'BIGINT',
            'rating_diff': 'BIGINT',
            'season': 'BIGINT'
        }
    ) LIMIT 0
""", [ratings_glob]).df()
schemas["ratings"] = df_ratings.to_dict(orient="records")
print(f"\n=== DESCRIBE ratings ({len(df_ratings)} columns) ===")
print(df_ratings.to_string(index=False))

# %%
# --- leaderboards ---
leaderboard_file = str(AOE2COMPANION_RAW_LEADERBOARDS_DIR / "leaderboard.parquet")
df_leaderboards = con.execute("""
    DESCRIBE SELECT * FROM read_parquet(?, binary_as_string=true, filename=true) LIMIT 0
""", [leaderboard_file]).df()
schemas["leaderboards"] = df_leaderboards.to_dict(orient="records")
print(f"\n=== DESCRIBE leaderboards ({len(df_leaderboards)} columns) ===")
print(df_leaderboards.to_string(index=False))

# %%
# --- profiles ---
profile_file = str(AOE2COMPANION_RAW_PROFILES_DIR / "profile.parquet")
df_profiles = con.execute("""
    DESCRIBE SELECT * FROM read_parquet(?, binary_as_string=true, filename=true) LIMIT 0
""", [profile_file]).df()
schemas["profiles"] = df_profiles.to_dict(orient="records")
print(f"\n=== DESCRIBE profiles ({len(df_profiles)} columns) ===")
print(df_profiles.to_string(index=False))

# %% [markdown]
# ## 3. Write artifact

# %%
artifacts_dir = (
    get_reports_dir("aoe2", "aoe2companion")
    / "artifacts" / "01_exploration" / "02_eda"
)
artifacts_dir.mkdir(parents=True, exist_ok=True)

artifact_data = {
    "step": "01_02_03",
    "dataset": "aoe2companion",
    "schemas": schemas,
}

artifact_path = artifacts_dir / "01_02_03_raw_schema_describe.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2, default=str))
logger.info("Artifact written: %s", artifact_path)

print(f"\nArtifact written: {artifact_path}")
for source, cols in schemas.items():
    print(f"  {source}: {len(cols)} columns")

# %%
con.close()
