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
# # Step 01_02_03 -- Raw Schema DESCRIBE: sc2egset
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** sc2egset
# **Question:** What are the column names and types for every `*_raw` object in
# the sc2egset DuckDB? This establishes a baseline schema snapshot used by
# downstream feature engineering steps.
# **Invariants applied:** #6 (reproducibility — SQL inlined in artifact), #9 (step scope: query)
# **Step scope:** query
# **Type:** Read-only — no DuckDB writes, no new tables, no schema changes

# %%
import json

import duckdb

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.sc2.config import DB_FILE

logger = setup_notebook_logging()
logger.info("DB_FILE: %s", DB_FILE)

# %% [markdown]
# ## 1. Connect to DuckDB (read-only)

# %%
con = duckdb.connect(str(DB_FILE), read_only=True)
print(f"Connected (read-only): {DB_FILE}")

# %% [markdown]
# ## 2. DESCRIBE all *_raw objects
#
# Objects covered:
# - Tables: `replays_meta_raw`, `replay_players_raw`, `map_aliases_raw`
# - Views: `game_events_raw`, `tracker_events_raw`, `message_events_raw`

# %%
RAW_OBJECTS = [
    "replays_meta_raw",
    "replay_players_raw",
    "map_aliases_raw",
    "game_events_raw",
    "tracker_events_raw",
    "message_events_raw",
]

schemas: dict[str, list[dict]] = {}

for obj in RAW_OBJECTS:
    df = con.execute(f"DESCRIBE {obj}").df()
    schemas[obj] = df.to_dict(orient="records")
    print(f"\n=== DESCRIBE {obj} ({len(df)} columns) ===")
    print(df.to_string(index=False))

# %% [markdown]
# ## 3. Write artifact

# %%
artifacts_dir = (
    get_reports_dir("sc2", "sc2egset")
    / "artifacts" / "01_exploration" / "02_eda"
)
artifacts_dir.mkdir(parents=True, exist_ok=True)

artifact_data = {
    "step": "01_02_03",
    "dataset": "sc2egset",
    "schemas": schemas,
}

artifact_path = artifacts_dir / "01_02_03_raw_schema_describe.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2, default=str))
logger.info("Artifact written: %s", artifact_path)

print(f"\nArtifact written: {artifact_path}")
for obj, cols in schemas.items():
    print(f"  {obj}: {len(cols)} columns")

# %%
con.close()
