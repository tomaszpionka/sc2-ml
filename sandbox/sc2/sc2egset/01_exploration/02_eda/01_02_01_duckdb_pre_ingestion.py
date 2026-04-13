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
# ## 1b. Filename uniqueness across tournaments
#
# The replay files are named `<hash>.SC2Replay.json`. If the same hash appears
# in multiple `*_data` directories, using just the basename as a provenance key
# would be ambiguous. Check whether basenames are unique across all tournaments
# before committing to a filename-only join key.

# %%
all_replays = sorted(REPLAYS_SOURCE_DIR.glob("*/*_data/*.SC2Replay.json"))
print(f"Total replay files: {len(all_replays):,}")

basenames = [f.name for f in all_replays]
unique_basenames = set(basenames)
print(f"Unique basenames:   {len(unique_basenames):,}")
print(f"Duplicates:         {len(basenames) - len(unique_basenames):,}")

if len(basenames) != len(unique_basenames):
    from collections import Counter
    dupes = [name for name, count in Counter(basenames).items() if count > 1]
    print(f"\nDuplicate basenames ({len(dupes)}):")
    for name in dupes[:10]:
        locations = [f.parent.parent.name for f in all_replays if f.name == name]
        print(f"  {name} -> {locations}")
    if len(dupes) > 10:
        print(f"  ... and {len(dupes) - 10} more")
else:
    print("\nAll basenames are unique — safe to use filename as join key.")

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
# ## 6b. Event array struct analysis
#
# The batch DESCRIBE (section 6) shows gameEvents, trackerEvents, messageEvents
# as STRUCT[] — arrays of structs. But each event type within an array has a
# different set of fields. DuckDB's read_json_auto unions all event structs
# into one wide STRUCT with NULLs for missing fields, which is why the batch
# DESCRIBE shows a single massive STRUCT type per array.
#
# This section examines the actual event struct heterogeneity by reading
# the raw JSON directly — how many distinct event struct shapes exist within
# each array, and what are the common vs rare fields?

# %%
from collections import Counter
from rts_predict.common.json_utils import classify_value

EVENT_KEYS = ["gameEvents", "trackerEvents", "messageEvents"]

# Use 3 sample files spanning the size distribution
event_probe_files = [samples[0], samples[len(samples) // 2], samples[-1]]

for event_key in EVENT_KEYS:
    print(f"\n{'='*70}")
    print(f"  {event_key} — struct heterogeneity analysis")
    print(f"{'='*70}")

    type_counter: Counter[str] = Counter()
    type_shapes: dict[str, set[str]] = {}
    type_field_types: dict[str, dict[str, set[str]]] = {}
    total_events = 0

    for fp in event_probe_files:
        with fp.open() as fh:
            data = json.load(fh)
        events = data.get(event_key, [])
        total_events += len(events)

        for evt in events:
            if not isinstance(evt, dict):
                continue
            evt_type = evt.get("evtTypeName", evt.get("id", "UNKNOWN"))
            if isinstance(evt_type, int):
                evt_type = f"id={evt_type}"
            type_counter[evt_type] += 1

            if evt_type not in type_shapes:
                type_shapes[evt_type] = set()
                type_field_types[evt_type] = {}
            type_shapes[evt_type].update(evt.keys())

            for k, v in evt.items():
                tag = classify_value(v)
                if k not in type_field_types[evt_type]:
                    type_field_types[evt_type][k] = set()
                type_field_types[evt_type][k].add(tag)

    print(f"  Total events across {len(event_probe_files)} files: {total_events:,}")
    print(f"  Unique event types: {len(type_counter)}")

    all_fields: set[str] = set()
    for shape in type_shapes.values():
        all_fields.update(shape)
    print(f"  Union of all fields (what DuckDB STRUCT[] becomes): {len(all_fields)} fields")
    print()

    for evt_type, count in type_counter.most_common():
        shape = sorted(type_shapes[evt_type])
        nested = [
            f for f in shape
            if any("struct" in t or "list" in t
                   for t in type_field_types[evt_type].get(f, set()))
        ]
        print(f"  [{count:>7,}x] {evt_type}  ({len(shape)} fields)")
        if nested:
            print(f"           nested: {nested}")
            for nf in nested:
                print(f"             {nf}: {type_field_types[evt_type][nf]}")
        print()

# %% [markdown]
# ### 6c. Event array — DuckDB STRUCT[] field explosion
#
# When DuckDB reads heterogeneous event structs with union_by_name, it creates
# one STRUCT type with ALL fields from ALL event types. This means each array
# element carries NULLs for every field not present in its event type.
#
# Show the actual DuckDB STRUCT[] column types to see how wide they become.

# %%
for event_key in EVENT_KEYS:
    print(f"\n{'='*60}")
    print(f"  typeof({event_key}) from batch load")
    print(f"{'='*60}")
    try:
        result = con.sql(f"""
            SELECT typeof("{event_key}") AS col_type
            FROM read_json_auto('{batch_glob}',
                union_by_name=true, maximum_object_size=536870912)
            LIMIT 1
        """).fetchone()
        type_str = result[0] if result else "N/A"
        # Print first 200 chars + total length to show the explosion
        print(f"  Length: {len(type_str)} chars")
        print(f"  Preview: {type_str[:300]}...")
    except Exception as e:
        print(f"  Error: {e}")

# %% [markdown]
# ### 6d. Alternative: UNNEST event arrays for per-event-type exploration
#
# Instead of loading the wide STRUCT[], unnest the arrays and group by
# evtTypeName to see the actual data shape per event type.

# %%
for event_key in EVENT_KEYS:
    print(f"\n{'='*60}")
    print(f"  UNNEST {event_key} — top event types with field counts")
    print(f"{'='*60}")
    try:
        con.sql(f"""
            WITH events AS (
                SELECT UNNEST("{event_key}") AS evt
                FROM read_json_auto('{batch_glob}',
                    union_by_name=true, maximum_object_size=536870912)
            )
            SELECT
                evt.evtTypeName AS event_type,
                COUNT(*) AS count
            FROM events
            GROUP BY evt.evtTypeName
            ORDER BY count DESC
        """).show()
    except Exception as e:
        print(f"  Error: {e}")

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
# ### 8d. Smoke test — extract_events_to_parquet on a single replay
#
# Validate that the Parquet extraction pipeline works end-to-end on one file
# before committing to the full 22,390-file run. Uses a temp raw directory
# with a single replay, then verifies the output with in-memory DuckDB.

# %%
import shutil
import tempfile

from rts_predict.games.sc2.config import DUCKDB_TEMP_DIR
from rts_predict.games.sc2.datasets.sc2egset.ingestion import extract_events_to_parquet

sample = samples[0]
smoke_output = DUCKDB_TEMP_DIR / "events_smoke_test"

# Build a temp raw dir matching the glob pattern: */*_data/*.SC2Replay.json
with tempfile.TemporaryDirectory() as tmp_raw:
    mirror = Path(tmp_raw) / sample.parent.parent.name / sample.parent.name
    mirror.mkdir(parents=True)
    shutil.copy2(sample, mirror / sample.name)

    counts = extract_events_to_parquet(Path(tmp_raw), smoke_output)

print("Extraction results:")
for event_type, count in counts.items():
    print(f"  {event_type}: {count:,} rows")

# %%
# Verify Parquet output with in-memory DuckDB
con_smoke = duckdb.connect(":memory:")

for event_type in ("gameEvents", "trackerEvents", "messageEvents"):
    pq_path = smoke_output / f"{event_type}.parquet"
    if not pq_path.exists():
        print(f"{event_type}: no Parquet file (0 events)")
        continue

    size_kb = pq_path.stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f"  {event_type}.parquet ({size_kb:.1f} KB)")
    print(f"{'='*60}")

    con_smoke.sql(f"DESCRIBE SELECT * FROM '{pq_path}'").show()

    row_count = con_smoke.sql(f"SELECT COUNT(*) FROM '{pq_path}'").fetchone()[0]
    print(f"  Rows: {row_count:,} (expected: {counts[event_type]:,})")
    assert row_count == counts[event_type], "Row count mismatch!"

    nulls = con_smoke.sql(f"""
        SELECT
            SUM(CASE WHEN filename IS NULL THEN 1 ELSE 0 END) AS null_filename,
            SUM(CASE WHEN loop IS NULL THEN 1 ELSE 0 END) AS null_loop,
            SUM(CASE WHEN "evtTypeName" IS NULL THEN 1 ELSE 0 END) AS null_evt_type
        FROM '{pq_path}'
    """).fetchone()
    print(f"  NULLs: filename={nulls[0]}, loop={nulls[1]}, evtTypeName={nulls[2]}")

    con_smoke.sql(f"""
        SELECT "evtTypeName", COUNT(*) AS n
        FROM '{pq_path}'
        GROUP BY "evtTypeName"
        ORDER BY n DESC
    """).show()

con_smoke.close()

# %%
# Compression ratio
raw_bytes = sample.stat().st_size
parquet_bytes = sum(
    (smoke_output / f"{et}.parquet").stat().st_size
    for et in ("gameEvents", "trackerEvents", "messageEvents")
    if (smoke_output / f"{et}.parquet").exists()
)
print(f"Raw JSON:      {raw_bytes / 1024:.1f} KB")
print(f"Parquet total: {parquet_bytes / 1024:.1f} KB")
print(f"Compression:   {raw_bytes / parquet_bytes:.1f}x")

shutil.rmtree(smoke_output)
print("\nSmoke test passed — output cleaned up.")

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
# - **Raw layer strategy:** `SELECT *` with `filename=true` for all `*_raw`
#   tables — no explicit DDL at this stage. DDL is deferred to staging tables
#   after exploration, analysis, and cleaning.

# %%
con.close()
