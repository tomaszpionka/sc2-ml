# Phase 01 Pre-Ingestion Discovery — Steps 01_01_00 through 01_01_03

**Category:** A (Phase work)
**Branch:** `feat/phase-01-raw-audit`
**Phase:** 01 — Data Exploration, Pipeline Section 01_01 (Data Acquisition & Source Inventory)
**Manual:** `01_DATA_EXPLORATION_MANUAL.md`, Section 1

---

## Motivation

Before any DuckDB ingestion can be designed correctly, we need to discover from scratch: (a) what files exist on disk, how many there are, and how they are organized; (b) for JSON datasets, what keys exist, which are scalar vs nested, and whether schemas are consistent across files; (c) for Parquet/CSV datasets, what columns and types exist and whether schemas are stable across files.

We assume nothing. We have raw files on disk. Any READMEs, manifests, or prior documentation that exists in the repository is reference material that may or may not be accurate — it is NOT authoritative. The discovery steps below produce the authoritative inventory and schema descriptions.

These steps are purely observational — they read raw files, count them, and report schemas. No DuckDB modification, no ingestion.

---

## Step-to-dataset applicability

| Step | sc2egset | aoe2companion | aoestats |
|------|----------|---------------|----------|
| 01_01_00 (overview acquisition) | No | No | Yes |
| 01_01_01 (file inventory) | Yes | Yes | Yes |
| 01_01_02 (JSON schema discovery) | Yes (replay JSONs) | No | Yes (overview.json) |
| 01_01_03 (Parquet/CSV schema audit) | No | Yes (Parquet + CSV) | Yes (Parquet) |

---

## Step 01_01_00 — Overview JSON Acquisition (aoestats only)

**Question:** Can we download the aoestats overview reference data so it is available for schema discovery?

The existing acquisition module handles weekly Parquet dumps but has no function for this file.

### Code changes

**`src/rts_predict/aoe2/config.py`:** Add `AOESTATS_RAW_OVERVIEW_DIR` constant

**`src/rts_predict/aoe2/data/aoestats/acquisition.py`:** Add function:

```python
def download_overview(
    url: str = "https://aoestats.io/api/overview/?format=json",
    target_dir: Path | None = None,
    filename: str = "overview.json",
) -> Path:
    """Download the aoestats overview JSON. Idempotent: skip if exists."""
```

### Tests
- Idempotent (pre-existing file not re-downloaded)
- Creates parent dirs
- Network error propagates cleanly

### Gate
- Function exists, passes tests
- Config constant exists

---

## Step 01_01_01 — Raw File Inventory Audit (all 3 datasets)

**Question:** What files exist on disk, how many are there, and how are they organized?

We walk each raw directory and count everything. We do NOT compare against any expected counts — we are producing the counts for the first time.

### sc2egset
- Walk `src/rts_predict/sc2/data/sc2egset/raw/`
- Count: total subdirectories, `.SC2Replay.json` files per subdirectory, other file types
- For each subdirectory: name, file count, total size
- Flag subdirectories with 0 replay files
- Report totals, min/max/median files per subdirectory

### aoe2companion
- Walk `src/rts_predict/aoe2/data/aoe2companion/raw/`
- Count files in each subdirectory
- For daily-file subdirectories: extract dates from filenames, report date range and gaps
- Report file extensions found in each subdirectory, total count and size per subdirectory

### aoestats
- Walk `src/rts_predict/aoe2/data/aoestats/raw/`
- Count files in each subdirectory
- For weekly-file subdirectories: extract date ranges from filenames, report coverage and gaps
- Check whether paired directories have matching file counts and date ranges (discover this, don't assume)
- Report total count and size per subdirectory

### New library code

**`src/rts_predict/common/inventory.py`** (new):

```python
@dataclass
class SubdirSummary:
    name: str
    file_count: int
    total_bytes: int
    extensions: dict[str, int]

@dataclass
class InventoryResult:
    root: Path
    total_files: int
    total_bytes: int
    subdirs: list[SubdirSummary]
    files_at_root: list[Path]

def inventory_directory(
    root: Path,
    file_glob: str = "*",
    group_by_subdir: bool = True,
) -> InventoryResult:
```

### Tests
- Empty directory: zero counts
- Directory with subdirs: correct per-subdir counts
- Files at root level captured
- Nonexistent directory: `FileNotFoundError`

### Notebooks

| Dataset | Path |
|---------|------|
| sc2egset | `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py` |
| aoe2companion | `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py` |
| aoestats | `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py` |

### Artifacts (per dataset)
- `01_01/01_01_01_file_inventory.json`
- `01_01/01_01_01_file_inventory.md`

### Gate
- Notebook executes without error
- Artifacts exist on disk
- The `.md` contains: total file count, total size, per-subdirectory breakdown
- **No assertion about what counts should be — the counts ARE the finding**

---

## Step 01_01_02 — JSON Schema Discovery (sc2egset + aoestats only)

**Question:** What keys exist in the JSON files, what are their types, and are schemas consistent across files?

We open JSON files, inspect their structure, and report what we find. We do NOT start with a list of expected keys — we discover the key set.

### sc2egset
- Sample 1 JSON per tournament subdirectory (deterministic: seed 42)
- For each root key across all samples: name, frequency, observed Python types, scalar vs nested
- Per-key summary table
- Key-presence matrix: rows = subdirectories, columns = root keys, values = present/absent
- Propose DuckDB column type per key
- Flag any keys that appear in some files but not others

### aoestats (overview.json only)
- Single-file analysis
- Record all root-level keys, types
- For list-valued keys: list length and element schema
- Discover what lookups this file provides

### Type mapping logic
- All `bool` → `BOOLEAN`
- All `int` → `BIGINT`
- All `float` → `DOUBLE`
- All `str` → `VARCHAR`
- Any `dict` or `list` → `JSON`
- Mixed scalar → `VARCHAR`
- Key in < 100% of samples → nullable

### New library code

**`src/rts_predict/common/json_utils.py`** (extend):

```python
@dataclass
class KeyProfile:
    key: str
    frequency: int
    total_samples: int
    observed_types: set[str]
    is_scalar: bool
    proposed_duckdb_type: str
    sample_values: list[Any]

def discover_json_schema(
    paths: list[Path],
    max_sample_values: int = 3,
) -> list[KeyProfile]:
```

### Tests
- Scalar-only file: all marked scalar
- Nested-only file: all marked non-scalar, type = JSON
- Identical key sets across files: frequency = 1.0
- Disjoint key sets: mixed frequencies
- Mixed types for same key: proposed type = VARCHAR
- Empty JSON: returns empty list

### Notebooks

| Dataset | Path |
|---------|------|
| sc2egset | `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_02_json_schema_discovery.py` |
| aoestats | `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_02_json_schema_discovery.py` |

### Artifacts (per dataset)
- `01_01/01_01_02_schema_discovery.json`
- `01_01/01_01_02_schema_discovery.md`
- sc2egset adds: `01_01/01_01_02_key_presence_matrix.csv`

### Gate
- Notebook executes without error
- Artifacts exist on disk
- Every root key found has a proposed DuckDB type
- Schema inconsistencies documented (or explicitly stated none found)
- **No assertion about what keys should exist — the discovered key set IS the finding**

---

## Step 01_01_03 — Parquet/CSV Schema Audit (aoe2companion + aoestats only)

**Question:** What columns and types exist in the Parquet/CSV files, and are schemas stable across files?

We read file metadata (not row data) and compare schemas. We do NOT start with expected columns or known drift — we discover schemas and any differences.

### aoe2companion
- For each subdirectory:
  - Read schema from first and last file using `pyarrow.parquet.read_schema()`
  - For CSV: `DuckDB DESCRIBE` on first and last file
  - Record column names, types, nullable flags
  - Compare first vs last: report columns added, removed, or type-changed
- If subdirectory has only 1 file, report schema without drift comparison

### aoestats
- For each subdirectory:
  - Read schema from earliest and latest file (by filename date)
  - Compare and report differences
  - Also sample midpoint file to check for gradual drift
- Report ALL schema differences found

### Notebooks

| Dataset | Path |
|---------|------|
| aoe2companion | `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_03_schema_audit.py` |
| aoestats | `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_03_schema_audit.py` |

### Artifacts (per dataset)
- `01_01/01_01_03_schema_audit.json`
- `01_01/01_01_03_schema_audit.md`
- If drift found: `01_01/01_01_03_schema_drift.csv` (one row per differing column)

### Gate
- Notebook executes without error
- Artifacts exist on disk
- Every column in every file category documented
- Drift CSV produced if and only if differences found
- **No assertion about what columns should exist — discovered schemas ARE the findings**

---

## Execution Dependencies

```
01_01_00 (aoestats)  ── independent, library code only

01_01_01 (sc2egset)  ─┐
01_01_01 (aoe2comp)  ─┤── all independent, parallel
01_01_01 (aoestats)  ─┘

01_01_02 (sc2egset)  ── depends on 01_01_01 (sc2egset)
01_01_02 (aoestats)  ── depends on 01_01_00 + 01_01_01 (aoestats)

01_01_03 (aoe2comp)  ── depends on 01_01_01 (aoe2comp)
01_01_03 (aoestats)  ── depends on 01_01_01 (aoestats)
```

---

## PR Structure

**PR 1:** Library code — `common/inventory.py` (new), `common/json_utils.py` (extend), `aoe2/config.py` (overview constant), `aoe2/data/aoestats/acquisition.py` (download_overview) + all tests
**PR 2:** Step 01_01_01 notebooks (all 3 datasets) + artifacts
**PR 3:** Step 01_01_02 notebooks (sc2egset + aoestats) + artifacts
**PR 4:** Step 01_01_03 notebooks (aoe2companion + aoestats) + artifacts

---

## Out of Scope

- Full Phase 01 planning (only Pipeline Section 01_01, Steps 00-03)
- Actual DuckDB ingestion (depends on schema discovery output)
- Ingestion/audit code rewrite (informed by discovery, done later)
- Interpreting findings against prior documentation (post-discovery activity)
- Any reference to expected counts, known schemas, or archived findings
