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
# # Step 01_01_02 — Schema Discovery: sc2egset
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** sc2egset
# **Question:** What is the internal structure of the SC2EGSet JSON files, and is this structure consistent across all 70 directories?
# **Invariants applied:** #6 (reproducibility), #7 (no magic numbers), #9 (pipeline discipline)
# **ROADMAP reference:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` Step 01_01_02
#
# Reads 1 file per directory (first alphabetically) for root schema via
# `discover_json_schema()` and 3 files per directory for full keypath
# enumeration via `get_json_keypaths()`. No DuckDB type proposals.

# %% [markdown]
# ## Cell 1 — Imports, config, paths

# %%
import json
from pathlib import Path

from rts_predict.common.json_utils import classify_value, discover_json_schema, get_json_keypaths
from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.sc2.config import REPLAYS_SOURCE_DIR

logger = setup_notebook_logging()

RAW_DIR: Path = REPLAYS_SOURCE_DIR
ARTIFACTS_DIR: Path = (
    get_reports_dir("sc2", "sc2egset")
    / "artifacts"
    / "01_exploration"
    / "01_acquisition"
)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
PRIOR_ARTIFACT: Path = ARTIFACTS_DIR / "01_01_01_file_inventory.json"

logger.info("RAW_DIR: %s", RAW_DIR)
logger.info("ARTIFACTS_DIR: %s", ARTIFACTS_DIR)

# %% [markdown]
# ## Cell 2 — Load 01_01_01 artifact to get directory list

# %%
with PRIOR_ARTIFACT.open() as fh:
    inventory = json.load(fh)

top_level_dirs = [d["name"] for d in inventory["top_level_dirs"]]
print(f"Loaded {len(top_level_dirs)} top-level directories from prior artifact")
print(f"First 3 dirs: {top_level_dirs[:3]}")

# %% [markdown]
# ## Cell 3 — Sampling / file selection (deterministic)
#
# Root schema: 1 file per directory (first alphabetically) → 70 files total.
# Keypath enumeration: 3 files per directory (first 3 alphabetically) → up to 210 files total.

# %%
root_schema_files: list[Path] = []
keypath_files: list[Path] = []

for dir_name in sorted(top_level_dirs):
    data_dir = RAW_DIR / dir_name / (dir_name + "_data")
    if not data_dir.exists():
        logger.warning("Missing _data/ subdir for: %s", dir_name)
        continue
    json_files = sorted(f for f in data_dir.iterdir() if f.suffix == ".json")
    if not json_files:
        logger.warning("No JSON files in: %s", data_dir)
        continue
    root_schema_files.append(json_files[0])
    keypath_files.extend(json_files[:3])

print(f"root_schema_files selected: {len(root_schema_files)}")
print(f"keypath_files selected: {len(keypath_files)}")

# %% [markdown]
# ## Cell 4 — Schema discovery
#
# Root-level key catalog via `discover_json_schema()`.
# Full keypath enumeration via `get_json_keypaths()` on the keypath sample.

# %%
print(f"Running discover_json_schema() on {len(root_schema_files)} files...")
key_profiles = discover_json_schema(root_schema_files, max_sample_values=3)
print(f"Root-level keys discovered: {len(key_profiles)}")

# %%
print(f"Running get_json_keypaths() on {len(keypath_files)} files...")
all_keypaths: set[str] = set()
keypath_parse_errors = 0
for fp in keypath_files:
    try:
        paths = get_json_keypaths(fp)
        all_keypaths.update(paths)
    except Exception as exc:
        keypath_parse_errors += 1
        logger.warning("Keypath parse error for %s: %s", fp, exc)

sorted_keypaths = sorted(all_keypaths)
print(f"Unique keypaths discovered: {len(sorted_keypaths)} (parse errors: {keypath_parse_errors})")

# %% [markdown]
# ## Cell 4b — Event array deep structure
#
# The three event arrays (`messageEvents`, `gameEvents`, `trackerEvents`)
# contain arrays of heterogeneous structs. Different event types carry
# different fields. This cell examines:
# - Unique event types (by `evtTypeName` / `id`)
# - Per-type struct shapes (which keys are present)
# - Nested sub-structures (dicts, arrays of dicts) inside events
#
# This is critical for ingestion strategy: do we need per-event-type
# tables, or can a single wide table with NULLs work?

# %%
from collections import Counter

EVENT_KEYS = ["messageEvents", "gameEvents", "trackerEvents"]

# Sample 5 files across the size distribution
sample_indices = [0, len(root_schema_files) // 4, len(root_schema_files) // 2,
                  3 * len(root_schema_files) // 4, -1]
event_sample_files = [root_schema_files[i] for i in sample_indices]
print(f"Event deep-structure sample: {len(event_sample_files)} files")


# %%
event_deep_structure: dict[str, dict] = {}

for event_key in EVENT_KEYS:
    print(f"\n{'='*70}")
    print(f"  {event_key}")
    print(f"{'='*70}")

    type_counter: Counter[str] = Counter()
    type_shapes: dict[str, set[str]] = {}        # event_type -> union of all keys
    type_field_types: dict[str, dict[str, set[str]]] = {}  # event_type -> field -> {types}
    total_events = 0

    for fp in event_sample_files:
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

    print(f"  Total events across {len(event_sample_files)} files: {total_events:,}")
    print(f"  Unique event types: {len(type_counter)}")
    print()

    # Build serializable summary for artifact
    event_types_summary = []
    for evt_type, count in type_counter.most_common():
        shape = sorted(type_shapes[evt_type])
        field_types = {
            f: sorted(type_field_types[evt_type][f]) for f in shape
        }
        nested = [
            f for f in shape
            if any("struct" in t or "list" in t for t in type_field_types[evt_type].get(f, set()))
        ]
        event_types_summary.append({
            "event_type": evt_type,
            "count": count,
            "fields": shape,
            "field_count": len(shape),
            "field_types": field_types,
            "nested_fields": nested,
        })

        print(f"  [{count:>7,}x] {evt_type}  ({len(shape)} fields)")
        if nested:
            print(f"           nested: {nested}")
            for nf in nested:
                print(f"             {nf}: {type_field_types[evt_type][nf]}")
        print()

    event_deep_structure[event_key] = {
        "total_events_sampled": total_events,
        "files_sampled": len(event_sample_files),
        "unique_event_types": len(type_counter),
        "event_types": event_types_summary,
    }

# %% [markdown]
# ## Cell 5 — Schema consistency check
#
# Compare root-level key sets across all 70 directories.
# Directories are temporal strata (2016-2024), so variation would indicate
# era-dependent schema evolution.

# %%
per_dir_key_sets: dict[str, set[str]] = {}
for fp in root_schema_files:
    dir_name = fp.parent.parent.name
    try:
        with fp.open() as fh:
            obj = json.load(fh)
        per_dir_key_sets[dir_name] = set(obj.keys()) if isinstance(obj, dict) else set()
    except Exception as exc:
        logger.warning("Cannot read keys from %s: %s", fp, exc)

all_key_sets = list(per_dir_key_sets.values())
if all_key_sets:
    reference_keys = all_key_sets[0]
    variant_directories = [
        d for d, ks in per_dir_key_sets.items() if ks != reference_keys
    ]
    all_files_same_schema = len(variant_directories) == 0
else:
    all_files_same_schema = True
    variant_directories = []

print(f"Schema consistency: all_same={all_files_same_schema}, variant_directories_count={len(variant_directories)}")
if variant_directories:
    print(f"Variant directories: {variant_directories[:10]}")

# %% [markdown]
# ## Cell 5b — Mapping file schema discovery
#
# Each tournament directory contains a `map_foreign_to_english_mapping.json`.
# These were inventoried in 01_01_01 but never schema-checked. What is the
# internal structure? Is it consistent across all 70 tournaments?

# %%
mapping_files = sorted(RAW_DIR.glob("*/map_foreign_to_english_mapping.json"))
print(f"Mapping files found: {len(mapping_files)}")

mapping_schemas: list[dict] = []
mapping_errors: list[str] = []

for mf in mapping_files:
    tournament = mf.parent.name
    try:
        with mf.open() as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as e:
        mapping_errors.append(f"{tournament}: {e}")
        continue

    entry_count = len(data) if isinstance(data, dict) else None
    key_types = set(type(k).__name__ for k in data.keys()) if isinstance(data, dict) else set()
    val_types = set(type(v).__name__ for v in data.values()) if isinstance(data, dict) else set()
    is_flat = all(not isinstance(v, (dict, list)) for v in data.values()) if isinstance(data, dict) else False

    mapping_schemas.append({
        "tournament": tournament,
        "top_level_type": type(data).__name__,
        "entry_count": entry_count,
        "key_types": sorted(key_types),
        "value_types": sorted(val_types),
        "is_flat": is_flat,
    })

print(f"Successfully parsed: {len(mapping_schemas)}")
print(f"Parse errors: {len(mapping_errors)}")
if mapping_errors:
    for e in mapping_errors:
        print(f"  ERROR: {e}")

# %%
# Schema consistency across all mapping files
top_types = set(m["top_level_type"] for m in mapping_schemas)
all_flat = all(m["is_flat"] for m in mapping_schemas)
key_type_union = set()
val_type_union = set()
entry_counts = []

for m in mapping_schemas:
    key_type_union.update(m["key_types"])
    val_type_union.update(m["value_types"])
    if m["entry_count"] is not None:
        entry_counts.append(m["entry_count"])

print(f"Top-level types: {sorted(top_types)}")
print(f"All flat (no nesting): {all_flat}")
print(f"Key types across all files: {sorted(key_type_union)}")
print(f"Value types across all files: {sorted(val_type_union)}")
print(f"Entries per file: min={min(entry_counts)}, max={max(entry_counts)}, "
      f"mean={sum(entry_counts)/len(entry_counts):.1f}")

# Check if all files share the same structure
ref = mapping_schemas[0] if mapping_schemas else None
variant_mappings = [
    m for m in mapping_schemas
    if (m["top_level_type"] != ref["top_level_type"]
        or m["key_types"] != ref["key_types"]
        or m["value_types"] != ref["value_types"]
        or m["is_flat"] != ref["is_flat"])
] if ref else []

if variant_mappings:
    print(f"\nVariant files ({len(variant_mappings)}):")
    for m in variant_mappings:
        print(f"  {m['tournament']}: type={m['top_level_type']}, flat={m['is_flat']}, "
              f"keys={m['key_types']}, vals={m['value_types']}")
else:
    print(f"\nAll {len(mapping_schemas)} files share the same structure: "
          f"type={ref['top_level_type']}, flat={ref['is_flat']}, "
          f"keys={ref['key_types']}, vals={ref['value_types']}")

# %%
# Sample content from first and last mapping files (temporal span)
for mf in [mapping_files[0], mapping_files[-1]]:
    with mf.open() as fh:
        data = json.load(fh)
    print(f"\n{mf.parent.name} ({len(data)} entries):")
    for k, v in list(data.items())[:5]:
        print(f"  {k!r} -> {v!r}")
    if len(data) > 5:
        print(f"  ... ({len(data) - 5} more)")

# %% [markdown]
# ## Cell 6 — Write JSON artifact

# %%
columns_out = []
for kp in key_profiles:
    col_entry = {
        "name": kp.key,
        "physical_type": sorted(kp.observed_types)[0] if len(kp.observed_types) == 1 else sorted(kp.observed_types),
        "nullable": kp.nullable,
        "frequency": kp.frequency,
        "total_samples": kp.total_samples,
        "sample_values": kp.sample_values,
    }
    columns_out.append(col_entry)

artifact = {
    "step": "01_01_02",
    "dataset": "sc2egset",
    "sampling": {
        "strategy": "systematic_temporal_stratified",
        "total_files_in_dataset": inventory["total_replay_files"],
        "files_checked_root_schema": len(root_schema_files),
        "files_checked_keypaths": len(keypath_files),
        "method": (
            "1 file per directory (first alphabetically) for root schema; "
            "3 files per directory (first 3 alphabetically) for keypath enumeration. "
            "All 70 directories represented."
        ),
    },
    "file_types": [
        {
            "type": "json",
            "subdirectory": "TOURNAMENT_data",
            "files_in_subdirectory": inventory["total_replay_files"],
            "files_checked": len(root_schema_files),
            "schema": {
                "columns": columns_out,
                "total_columns": len(columns_out),
                "nesting_depth": max(p.count(".") + 1 for p in sorted_keypaths) if sorted_keypaths else 0,
                "keypaths": sorted_keypaths,
            },
            "consistency": {
                "all_files_same_schema": all_files_same_schema,
                "variant_directories": variant_directories if not all_files_same_schema else [],
            },
            "event_array_deep_structure": event_deep_structure,
        },
        {
            "type": "json",
            "subdirectory": "TOURNAMENT (root level)",
            "filename_pattern": "map_foreign_to_english_mapping.json",
            "files_found": len(mapping_schemas),
            "files_with_errors": len(mapping_errors),
            "schema": {
                "top_level_type": sorted(top_types),
                "all_flat": all_flat,
                "key_types": sorted(key_type_union),
                "value_types": sorted(val_type_union),
                "entry_counts": {
                    "min": min(entry_counts) if entry_counts else None,
                    "max": max(entry_counts) if entry_counts else None,
                    "mean": round(sum(entry_counts) / len(entry_counts), 1) if entry_counts else None,
                },
            },
            "consistency": {
                "all_same_schema": len(variant_mappings) == 0,
                "variant_files": [m["tournament"] for m in variant_mappings],
            },
            "per_file": mapping_schemas,
        },
    ],
}

out_json = ARTIFACTS_DIR / "01_01_02_schema_discovery.json"
with out_json.open("w") as fh:
    json.dump(artifact, fh, indent=2)
logger.info("Wrote JSON artifact: %s", out_json)

# %% [markdown]
# ## Cell 7 — Write Markdown artifact

# %%
md_lines = [
    "# Step 01_01_02 — Schema Discovery: sc2egset",
    "",
    "**Phase:** 01 — Data Exploration  ",
    "**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory  ",
    "**Dataset:** sc2egset  ",
    "**Invariants applied:** #6, #7, #9  ",
    "",
    "## Sampling methodology",
    "",
    "| Parameter | Value |",
    "|-----------|-------|",
    f"| Strategy | systematic temporal stratification (1 file/dir for root schema, 3 files/dir for keypaths) |",
    f"| Directories | {inventory['num_top_level_dirs']} |",
    f"| Files selected (root schema) | {len(root_schema_files)} |",
    f"| Files selected (keypaths) | {len(keypath_files)} |",
    f"| Total files in dataset | {inventory['total_replay_files']} |",
    "",
    "File selection is deterministic: first N files alphabetically per `_data/` directory.",
    "",
    "## Root-level key catalog (JSON schema)",
    "",
    "| Key | Observed types | Nullable | Frequency / Total |",
    "|-----|----------------|----------|-------------------|",
]

for kp in key_profiles:
    type_str = ", ".join(sorted(kp.observed_types))
    md_lines.append(
        f"| `{kp.key}` | {type_str} | {kp.nullable} | {kp.frequency} / {kp.total_samples} |"
    )

md_lines += [
    "",
    "## Full keypath tree",
    "",
    f"Total unique keypaths: {len(sorted_keypaths)}",
    "",
    "```",
]
md_lines.extend(sorted_keypaths[:200])
if len(sorted_keypaths) > 200:
    md_lines.append(f"... ({len(sorted_keypaths) - 200} more keypaths truncated)")
md_lines.append("```")

md_lines += [
    "",
    "## Schema consistency",
    "",
    f"**All 70 directories share the same root-level schema:** {all_files_same_schema}",
    "",
]
if not all_files_same_schema:
    md_lines.append(f"**Variant directories ({len(variant_directories)}):**")
    for vd in variant_directories:
        md_lines.append(f"- {vd}")
    md_lines.append("")

md_lines += [
    "## Event array deep structure",
    "",
    f"Sampled {len(event_sample_files)} files across the size distribution.",
    "",
]
for ek in EVENT_KEYS:
    ds = event_deep_structure[ek]
    md_lines += [
        f"### {ek}",
        "",
        f"- Total events sampled: {ds['total_events_sampled']:,}",
        f"- Unique event types: {ds['unique_event_types']}",
        "",
        "| Event type | Count | Fields | Nested fields |",
        "|------------|-------|--------|---------------|",
    ]
    for et in ds["event_types"]:
        nested_str = ", ".join(et["nested_fields"]) if et["nested_fields"] else "none"
        md_lines.append(
            f"| {et['event_type']} | {et['count']:,} | {et['field_count']} | {nested_str} |"
        )
    md_lines.append("")

md_lines += [
    "## Mapping file schema (`map_foreign_to_english_mapping.json`)",
    "",
    f"- Files found: {len(mapping_schemas)} / {len(mapping_files)}",
    f"- Parse errors: {len(mapping_errors)}",
    f"- Top-level type: {sorted(top_types)}",
    f"- All flat (no nesting): {all_flat}",
    f"- Key types: {sorted(key_type_union)}, Value types: {sorted(val_type_union)}",
    f"- Entries per file: min={min(entry_counts)}, max={max(entry_counts)}, "
    f"mean={sum(entry_counts)/len(entry_counts):.1f}",
    f"- Schema consistent across all files: {len(variant_mappings) == 0}",
    "",
]
if variant_mappings:
    md_lines.append(f"**Variant files ({len(variant_mappings)}):**")
    for m in variant_mappings:
        md_lines.append(f"- {m['tournament']}: type={m['top_level_type']}, "
                        f"flat={m['is_flat']}, keys={m['key_types']}, vals={m['value_types']}")
    md_lines.append("")

md_lines += [
    "## Notes",
    "",
    "- No DuckDB type proposals in this step (deferred to ingestion design).",
    "- Sample values in the JSON artifact are for type-inference validation only.",
    "- Step scope: `content` (file headers/schemas/sample root keys).",
    "- Event deep structure in JSON artifact has full per-field type breakdown.",
]

out_md = ARTIFACTS_DIR / "01_01_02_schema_discovery.md"
out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
logger.info("Wrote Markdown artifact: %s", out_md)
