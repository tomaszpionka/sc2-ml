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
# # Step 01_02_01 -- DuckDB Pre-Ingestion Investigation: sc2egset
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** sc2egset
# **Question:** How does DuckDB read_json_auto handle SC2EGSet replay JSONs?
# What is the event array storage cost? What table split strategy is optimal?
# **Invariants applied:** #6 (reproducibility), #9 (step scope)
# **Step scope:** query
# **Type:** Investigation only -- no full ingestion of 22,390 files

# %%
import json
import logging
import statistics
from pathlib import Path

import duckdb

from rts_predict.common.notebook_utils import get_reports_dir
from rts_predict.games.sc2.config import REPLAYS_SOURCE_DIR
from rts_predict.games.sc2.datasets.sc2egset.pre_ingestion import (
    select_sample_files,
    probe_read_json_auto_single,
    measure_event_arrays,
    probe_batch_ingestion,
    census_mapping_files,
    probe_mapping_read_json_auto,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# %% [markdown]
# ## 1. Select sample files

# %%
inv_path = (
    get_reports_dir("sc2", "sc2egset")
    / "artifacts" / "01_exploration" / "01_acquisition"
    / "01_01_01_file_inventory.json"
)
with open(inv_path) as f:
    inventory = json.load(f)

samples = select_sample_files(inventory, REPLAYS_SOURCE_DIR)
print(f"Selected {len(samples)} sample files:")
for s in samples:
    mb = s.stat().st_size / 1024 / 1024
    print(f"  {s.parent.parent.name}/{s.name} ({mb:.1f} MB)")

# %% [markdown]
# ## 2. Test read_json_auto on each sample

# %%
con = duckdb.connect(":memory:")
con.execute("SET memory_limit = '24GB'")
con.execute("SET threads = 4")

rja_results = []
for s in samples:
    r = probe_read_json_auto_single(con, s)
    rja_results.append(r)
    print(f"{r['file']}: success={r['success']}, cols={r.get('column_count')}")
    print(f"  ToonPlayerDescMap: {r.get('ToonPlayerDescMap_type', 'N/A')[:80]}...")

# %% [markdown]
# ## 3. DESCRIBE -- single file read_json_auto output

# %%
con.sql(
    f"DESCRIBE SELECT * FROM read_json_auto('{samples[0]}', "
    f"maximum_object_size=536870912)"
).show()

# %% [markdown]
# ## 4. Row preview -- single file

# %%
con.sql(
    f"SELECT * FROM read_json_auto('{samples[0]}', "
    f"maximum_object_size=536870912) LIMIT 5"
).show()

# %% [markdown]
# ## 5. Event array storage assessment

# %%
ea_results = [measure_event_arrays(s) for s in samples]

for key in ("gameEvents", "trackerEvents", "messageEvents"):
    counts = [r[key]["element_count"] for r in ea_results]
    bytes_ = [r[key]["json_bytes"] for r in ea_results]
    total_est_gb = statistics.mean(bytes_) * 22390 / 1024**3
    print(f"{key}:")
    print(f"  elements: mean={statistics.mean(counts):.0f}, "
          f"median={statistics.median(counts):.0f}, "
          f"min={min(counts)}, max={max(counts)}")
    print(f"  est. total (22,390 files): {total_est_gb:.1f} GB")

# %% [markdown]
# ## 6. Batch ingestion probe

# %%
batch_dir = (
    REPLAYS_SOURCE_DIR / "2018_Cheeseadelphia_8"
    / "2018_Cheeseadelphia_8_data"
)
batch_result = probe_batch_ingestion(con, batch_dir)
print(f"Directory: {batch_result['directory']}")
print(f"Files: {batch_result['file_count']}")
print(f"Success: {batch_result['success']}")
print(f"Elapsed: {batch_result.get('elapsed_seconds', 'N/A')} seconds")
print(f"Rows: {batch_result.get('row_count', 'N/A')}")

# %% [markdown]
# ### DESCRIBE -- batch (union_by_name across tournament dir)

# %%
batch_glob = str(batch_dir / "*.SC2Replay.json")
con.sql(
    f"DESCRIBE SELECT * FROM read_json_auto('{batch_glob}', "
    f"union_by_name=true, filename=true, "
    f"maximum_object_size=536870912)"
).show()

# %% [markdown]
# ### Row preview -- batch

# %%
con.sql(
    f"SELECT * FROM read_json_auto('{batch_glob}', "
    f"union_by_name=true, filename=true, "
    f"maximum_object_size=536870912) LIMIT 5"
).show()

# %% [markdown]
# ## 7. Mapping file census

# %%
census = census_mapping_files(REPLAYS_SOURCE_DIR)
print(f"Files found: {census['total_files_found']}")
print(f"Combined size: {census['total_combined_bytes']:,} bytes")
print(f"Cross-file consistency: {census['cross_file_consistency']}")

# %%
first_mf = (
    REPLAYS_SOURCE_DIR / census["files"][0]["tournament"]
    / "map_foreign_to_english_mapping.json"
)
mapping_test = probe_mapping_read_json_auto(con, first_mf)
print(f"read_json_auto: success={mapping_test['success']}")
print(f"DuckDB type: {mapping_test.get('columns', [{}])[0].get('column_type')}")

# %% [markdown]
# ## 8. Ingestion readiness checks

# %% [markdown]
# ### 8a. Sub-field DESCRIBE for metadata structs
#
# The root-level DESCRIBE (section 3) shows `details`, `header`, `initData`,
# `metadata` as STRUCT. We need the sub-field types to write correct DDL.

# %%
con = duckdb.connect(":memory:")
con.execute("SET memory_limit = '24GB'")

# Use the batch glob (64 files) for richer union_by_name coverage
batch_glob = str(batch_dir / "*.SC2Replay.json")

for struct_col in ("details", "header", "initData", "metadata"):
    print(f"\n{'='*60}")
    print(f"  DESCRIBE {struct_col}.*")
    print(f"{'='*60}")
    try:
        con.sql(f"""
            DESCRIBE SELECT "{struct_col}".* FROM read_json_auto(
                '{batch_glob}', union_by_name=true,
                maximum_object_size=536870912
            )
        """).show()
    except Exception as e:
        print(f"  Cannot unnest {struct_col}: {e}")
        con.sql(f"""
            SELECT typeof("{struct_col}") AS type
            FROM read_json_auto('{batch_glob}',
                union_by_name=true, maximum_object_size=536870912)
            LIMIT 1
        """).show()

# %% [markdown]
# ### 8b. Storage estimate -- median vs mean (skew correction)

# %%
print("Storage estimates -- mean vs median (7-file sample):\n")
print(f"{'Array':<20} {'Mean (GB)':>10} {'Median (GB)':>12} {'Ratio':>8}")
print("-" * 55)
for key in ("gameEvents", "trackerEvents", "messageEvents"):
    bytes_ = [r[key]["json_bytes"] for r in ea_results]
    mean_gb = statistics.mean(bytes_) * 22390 / 1024**3
    median_gb = statistics.median(bytes_) * 22390 / 1024**3
    ratio = mean_gb / median_gb if median_gb > 0 else float("inf")
    print(f"{key:<20} {mean_gb:>10.1f} {median_gb:>12.1f} {ratio:>8.1f}x")

total_mean = sum(statistics.mean([r[k]["json_bytes"] for r in ea_results]) for k in ("gameEvents", "trackerEvents", "messageEvents")) * 22390 / 1024**3
total_median = sum(statistics.median([r[k]["json_bytes"] for r in ea_results]) for k in ("gameEvents", "trackerEvents", "messageEvents")) * 22390 / 1024**3
print(f"{'TOTAL':<20} {total_mean:>10.1f} {total_median:>12.1f} {total_mean/total_median:>8.1f}x")
print(f"\nNote: n=7, highly right-skewed. Median is the conservative estimate.")

# %% [markdown]
# ### 8c. ToonPlayerDescMap -- per-player fields catalog
#
# Enumerate the actual per-player fields inside ToonPlayerDescMap to assess
# whether these are prediction-relevant (race, MMR, APM, etc.)

# %%
with open(samples[0]) as f:
    sample_data = json.load(f)

tpdm = sample_data.get("ToonPlayerDescMap", {})
if tpdm:
    first_player_key = next(iter(tpdm))
    player_data = tpdm[first_player_key]
    print(f"ToonPlayerDescMap: {len(tpdm)} players in sample file")
    print(f"Per-player fields ({len(player_data)} total):")
    for k, v in sorted(player_data.items()):
        print(f"  {k}: {type(v).__name__} = {repr(v)[:80]}")

# %% [markdown]
# ## 9. Findings and ingestion strategy recommendation
#
# Summarize all findings from sections 1-8 here after execution.
# Key decisions to record:
#
# - **Table split strategy:** metadata-only vs include events?
# - **Event ingestion:** defer all, or ingest specific trackerEvent types?
# - **ToonPlayerDescMap:** unnest to per-player columns or keep as MAP?
# - **Mapping files:** single reference table (all 70 identical)?
# - **Sub-field types:** any surprises in nested struct fields?
# - **Proposed DDL** for each table

# %%
con.close()
