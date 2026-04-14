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
# # Step 01_02_03 -- Raw Schema DESCRIBE: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** aoestats
# **Question:** What are the column names and types for every `*_raw` table in
# the aoestats DuckDB? This establishes a baseline schema snapshot used by
# downstream feature engineering steps.
# **Invariants applied:** #6 (reproducibility — SQL inlined in artifact), #9 (step scope: query)
# **Step scope:** query
# **Type:** Read-only — no DuckDB writes, no new tables, no schema changes

# %%
import json

import duckdb

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOESTATS_DB_FILE

logger = setup_notebook_logging()
logger.info("DB_FILE: %s", AOESTATS_DB_FILE)

# %% [markdown]
# ## 1. Connect to DuckDB (read-only)

# %%
con = duckdb.connect(str(AOESTATS_DB_FILE), read_only=True)
print(f"Connected (read-only): {AOESTATS_DB_FILE}")

# %% [markdown]
# ## 2. DESCRIBE all *_raw tables
#
# Tables covered:
# - `matches_raw`
# - `players_raw`
# - `overviews_raw`

# %%
RAW_TABLES = [
    "matches_raw",
    "players_raw",
    "overviews_raw",
]

schemas: dict[str, list[dict]] = {}

for table in RAW_TABLES:
    df = con.execute(f"DESCRIBE {table}").df()
    schemas[table] = df.to_dict(orient="records")
    print(f"\n=== DESCRIBE {table} ({len(df)} columns) ===")
    print(df.to_string(index=False))

# %% [markdown]
# ## 3. Write artifact

# %%
artifacts_dir = (
    get_reports_dir("aoe2", "aoestats")
    / "artifacts" / "01_exploration" / "02_eda"
)
artifacts_dir.mkdir(parents=True, exist_ok=True)

artifact_data = {
    "step": "01_02_03",
    "dataset": "aoestats",
    "schemas": schemas,
}

artifact_path = artifacts_dir / "01_02_03_raw_schema_describe.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2, default=str))
logger.info("Artifact written: %s", artifact_path)

print(f"\nArtifact written: {artifact_path}")
for table, cols in schemas.items():
    print(f"  {table}: {len(cols)} columns")

# %%
con.close()
