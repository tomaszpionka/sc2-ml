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
# # Step 01_02_01 -- DuckDB Pre-Ingestion: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** aoe2companion
# **Question:** What does the raw data look like before we commit to an
# ingestion strategy? Are there binary column issues, schema evolution,
# type inference traps, or NULL patterns we need to handle?
# **Invariants applied:** #6 (reproducibility), #9 (step scope)
# **Step scope:** query

# %%
import logging

import duckdb

from rts_predict.common.notebook_utils import setup_notebook_logging
from rts_predict.games.aoe2.config import AOE2COMPANION_RAW_DIR
from rts_predict.games.aoe2.datasets.aoe2companion.pre_ingestion import (
    inspect_binary_columns,
    run_smoke_test,
)

setup_notebook_logging()
logger = logging.getLogger(__name__)

# %% [markdown]
# ## 1. Pyarrow binary column inspection

# %%
binary_info = inspect_binary_columns(AOE2COMPANION_RAW_DIR)
for subdir, info in binary_info.items():
    print(f"{subdir}: {info['binary_column_count']} binary columns")
    for col in info["binary_columns"]:
        print(f"  {col['name']}: {col['converted_type']}")

# %% [markdown]
# ## 2. Smoke test

# %%
con = duckdb.connect(":memory:")
smoke = run_smoke_test(con, AOE2COMPANION_RAW_DIR)
print(f"Smoke matches: {smoke['matches']['row_count']} rows, {smoke['matches']['column_count']} cols")
print(f"Smoke ratings: {smoke['ratings']['row_count']} rows, {smoke['ratings']['column_count']} cols")

# %% [markdown]
# ## 3. DESCRIBE -- column names, types, nullability

# %%
for table_name in smoke:
    print(f"\n{'='*60}")
    print(f"  DESCRIBE {table_name}")
    print(f"{'='*60}")
    files = smoke[table_name]["files_sampled"]
    full_paths = [str(AOE2COMPANION_RAW_DIR / table_name / f) for f in files]
    file_list = ", ".join(f"'{p}'" for p in full_paths)
    reader = "read_csv_auto" if files[0].endswith(".csv") else "read_parquet"
    opts = "binary_as_string=true, " if reader == "read_parquet" else ""
    con.sql(
        f"DESCRIBE SELECT * FROM {reader}([{file_list}], {opts}filename=true)"
    ).show()

# %% [markdown]
# ## 4. Row preview -- SELECT * LIMIT 10

# %%
for table_name in smoke:
    print(f"\n{'='*60}")
    print(f"  {table_name}: {smoke[table_name]['row_count']} rows, {smoke[table_name]['column_count']} cols")
    print(f"{'='*60}")
    files = smoke[table_name]["files_sampled"]
    full_paths = [str(AOE2COMPANION_RAW_DIR / table_name / f) for f in files]
    file_list = ", ".join(f"'{p}'" for p in full_paths)
    reader = "read_csv_auto" if files[0].endswith(".csv") else "read_parquet"
    opts = "binary_as_string=true, " if reader == "read_parquet" else ""
    con.sql(f"SELECT * FROM {reader}([{file_list}], {opts}filename=true) LIMIT 10").show()

# %% [markdown]
# ## 5. Schema evolution -- NULL counts per file date (matches)

# %%
con.sql("""
    SELECT
        filename.split('match-')[2][:10] AS file_date,
        COUNT(*) AS rows,
        COUNT(server) AS server_nn,
        COUNT(empireWarsMode) AS empireWarsMode_nn,
        COUNT(hideCivs) AS hideCivs_nn,
        COUNT(regicideMode) AS regicideMode_nn,
        COUNT(suddenDeathMode) AS suddenDeathMode_nn,
        COUNT(antiquityMode) AS antiquityMode_nn,
        COUNT(scenario) AS scenario_nn,
        COUNT(password) AS password_nn,
        COUNT(modDataset) AS modDataset_nn,
        COUNT(rating) AS rating_nn,
        COUNT(ratingDiff) AS ratingDiff_nn,
        COUNT(team) AS team_nn
    FROM read_parquet(
        '{glob}',
        binary_as_string=true, filename=true, union_by_name=true
    )
    GROUP BY file_date
    ORDER BY file_date
""".format(glob=str(AOE2COMPANION_RAW_DIR / "matches" / "*.parquet"))).show()

# %% [markdown]
# ## 6. Schema evolution -- NULL counts per file date (ratings)

# %%
con.sql("""
    SELECT
        filename.split('rating-')[2][:10] AS file_date,
        COUNT(*) AS rows,
        COUNT(profile_id) AS profile_id_nn,
        COUNT(games) AS games_nn,
        COUNT(rating) AS rating_nn,
        COUNT(date) AS date_nn,
        COUNT(leaderboard_id) AS leaderboard_id_nn,
        COUNT(rating_diff) AS rating_diff_nn,
        COUNT(season) AS season_nn
    FROM read_csv(
        '{glob}',
        filename=true, union_by_name=true
    )
    GROUP BY file_date
    ORDER BY file_date
""".format(glob=str(AOE2COMPANION_RAW_DIR / "ratings" / "*.csv"))).show()

# %% [markdown]
# ## 7. Ingestion readiness checks

# %% [markdown]
# ### 7a. CSV type validation -- can ratings columns actually be parsed as numeric/temporal?

# %%
import pandas as pd

# Stratified sample: early, middle, late
ratings_dir = AOE2COMPANION_RAW_DIR / "ratings"
csv_files = sorted(ratings_dir.glob("*.csv"))
sample_csvs = [csv_files[0], csv_files[len(csv_files) // 2], csv_files[-1]]

for fp in sample_csvs:
    df = pd.read_csv(fp, nrows=500)
    print(f"\n--- {fp.name} ({len(df)} rows) ---")
    for col in df.columns:
        numeric_ok = pd.to_numeric(df[col], errors="coerce").notna().sum()
        print(f"  {col}: {numeric_ok}/{len(df)} parseable as numeric")
    date_ok = pd.to_datetime(df["date"], errors="coerce").notna().sum()
    print(f"  date as datetime: {date_ok}/{len(df)} parseable")

# %% [markdown]
# ### 7b. Singleton tables -- DESCRIBE and preview (leaderboard, profiles)

# %%
con = duckdb.connect(":memory:")

for name, path in [
    ("leaderboard", AOE2COMPANION_RAW_DIR / "leaderboards" / "leaderboard.parquet"),
    ("profiles", AOE2COMPANION_RAW_DIR / "profiles" / "profile.parquet"),
]:
    print(f"\n{'='*60}")
    print(f"  DESCRIBE {name}")
    print(f"{'='*60}")
    con.sql(f"DESCRIBE SELECT * FROM read_parquet('{path}', binary_as_string=true)").show()
    print(f"\n  {name} -- first 5 rows:")
    con.sql(f"SELECT * FROM read_parquet('{path}', binary_as_string=true) LIMIT 5").show()

# %% [markdown]
# ### 7c. Join key (matchId, profileId) and prediction target (won) NULL rates

# %%
matches_glob = str(AOE2COMPANION_RAW_DIR / "matches" / "*.parquet")

con.sql("""
    SELECT
        COUNT(*) AS total,
        COUNT(matchId) AS matchId_nn,
        COUNT(*) - COUNT(matchId) AS matchId_null,
        COUNT(profileId) AS profileId_nn,
        COUNT(*) - COUNT(profileId) AS profileId_null,
        COUNT(won) AS won_nn,
        COUNT(*) - COUNT(won) AS won_null,
        ROUND(100.0 * (COUNT(*) - COUNT(won)) / COUNT(*), 2) AS won_null_pct
    FROM read_parquet('{glob}', binary_as_string=true, union_by_name=true)
""".format(glob=matches_glob)).show()

# %% [markdown]
# ### 7d. matchId uniqueness -- is each row a player-in-match?

# %%
con.sql("""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT matchId) AS distinct_matches,
        ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT matchId), 2) AS avg_rows_per_match
    FROM read_parquet('{glob}', binary_as_string=true, union_by_name=true)
""".format(glob=matches_glob)).show()

# %% [markdown]
# ### 7e. Ratings -- full corpus type check (does read_csv_auto fail on all files?)

# %%
ratings_glob = str(AOE2COMPANION_RAW_DIR / "ratings" / "*.csv")

print("read_csv_auto DESCRIBE on full corpus:")
try:
    con.sql("""
        DESCRIBE SELECT * FROM read_csv_auto('{glob}', filename=true)
    """.format(glob=ratings_glob)).show()
    print("read_csv_auto: SUCCEEDED on full corpus")
except Exception as e:
    print(f"read_csv_auto: FAILED -- {e}")

print("\nread_csv with explicit types DESCRIBE:")
con.sql("""
    DESCRIBE SELECT * FROM read_csv(
        '{glob}', filename=true, header=true,
        types={{'profile_id':'BIGINT','games':'BIGINT','rating':'BIGINT',
               'date':'TIMESTAMP','leaderboard_id':'BIGINT',
               'rating_diff':'BIGINT','season':'BIGINT'}}
    )
""".format(glob=ratings_glob)).show()

# %% [markdown]
# ## 8. Findings and ingestion strategy recommendation
#
# Summarize all findings from sections 1-7 here after execution.
# Key decisions to record:
#
# - **Binary columns:** binary_as_string=true confirmed? (based on section 1)
# - **Schema evolution:** which columns appear/disappear over time? (based on section 5)
# - **CSV types:** explicit types validated? (based on 7a, 7e)
# - **won NULLs:** acceptable rate? (based on 7c)
# - **Data structure:** player-in-match rows confirmed? (based on 7d)
# - **Proposed DDL** for matches_raw, ratings_raw, leaderboards_raw, profiles_raw

# %%
con.close()
