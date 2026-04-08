# Phase 1 Step 1.9 Extension — Event `event_data` JSON Schema Exploration

**Category:** A (Phase work)
**Phase/Step:** SC2 Phase 1 / Steps 1.9D, 1.9E, 1.9F
**Branch:** `feat/sc2-phase1-step1.9` (current)
**Depends on:** Steps 1.9A–C complete, Step 1.6 complete

---

## Context

Steps 1.9A–C inventoried JSON fields in ToonPlayerDescMap and top-level replay
columns (header, initData, details, metadata). However, the two most voluminous
tables in the SC2EGSet staging schema store all in-game data in an opaque
`event_data VARCHAR` column:

| Table | Rows | Status |
|---|---|---|
| `tracker_events_raw` | ~62M | event type counts done (Step 1.6); `event_data` internals never profiled |
| `game_events_raw` | ~609M | not profiled at all |

This gap violates:
- Manual 01 §1 — schema discovery must cover all columns
- Manual 01 §3.1 — column-level profiling for every variable
- Manual 01 §6.1 — data dictionary must document all fields (Deliverable 1 of Step 1.16)
- Scientific Invariants 6 (reproducibility) and 7 (no magic numbers)

Phase 4 (in-game feature extraction) will need to parse these JSON fields.
Without an empirical field inventory now, Phase 4 extraction logic would rest on
assumptions rather than observed data properties.

---

## Pre-flight checks

- [ ] Currently on branch `feat/sc2-phase1-step1.9`
- [ ] Steps 1.9A–C artifacts exist in `src/rts_predict/sc2/reports/sc2egset/`
- [ ] Step 1.6 event-type count artifacts exist

---

## Step 1.9D — Tracker `event_data` field inventory (per event type)

**File to modify:** `src/rts_predict/sc2/data/exploration.py`

### Functions to add

```python
def build_event_data_field_inventory_query(
    table_name: str,
    sample_size: int = 100_000,
) -> str:
    """Return SQL that enumerates distinct JSON keys in event_data per event type.

    Uses SAMPLE for large tables. Suitable for both tracker_events_raw and
    game_events_raw.

    Args:
        table_name: DuckDB table name (e.g., 'tracker_events_raw')
        sample_size: Number of rows to sample. Use 0 for no sampling.

    Returns:
        SQL string returning columns: event_type, json_key
    """
    ...


def build_event_data_key_constancy_query(
    table_name: str,
    event_type: str,
    sample_size: int = 10_000,
) -> str:
    """Return SQL that measures key-set variant distribution for one event type.

    Builds a list of JSON keys per row, groups by that list, and counts variants.

    Args:
        table_name: DuckDB table name
        event_type: Value of the event_type column to filter to
        sample_size: Number of rows per event type to sample

    Returns:
        SQL string returning columns: key_list, n_events, pct
    """
    ...


def build_nested_field_inventory_query(
    table_name: str,
    event_type: str,
    nested_key: str,
    sample_size: int = 100_000,
) -> str:
    """Return SQL enumerating keys of a nested JSON object within event_data.

    Used for PlayerStats.stats sub-object and Cmd.abil / Cmd.data sub-objects.

    Args:
        table_name: DuckDB table name
        event_type: Filter to this event type
        nested_key: Top-level key whose value is the nested object (e.g., 'stats')
        sample_size: Number of rows to sample

    Returns:
        SQL string returning columns: nested_key_name
    """
    ...
```

### Sub-steps

**1.9D-i** — Enumerate all distinct JSON keys in `tracker_events_raw.event_data`,
per event type (sample 100 000 rows). Verify no new keys appear when re-sampling.

**1.9D-ii** — For each of the 10 tracker event types, run the key-constancy query
(sample 10 000 rows per type). Record variant counts.

**1.9D-iii** — For `PlayerStats` specifically, enumerate the nested `stats.*`
sub-object keys (these are the ~37 `scoreValue*` fields used by Phase 4).

### Artifacts

| File | Columns |
|---|---|
| `01_09D_tracker_event_data_field_inventory.csv` | event_type, json_key, is_nested |
| `01_09D_tracker_event_data_key_constancy.csv` | event_type, key_list, n_events, pct |
| `01_09D_playerstats_stats_field_inventory.csv` | stats_key |

### Gate condition

- **Continue:** Each event type has a dominant key-set variant covering >99% of events.
- **Halt:** Any event type has >5 key-set variants each covering >5% — structural
  heterogeneity would require per-variant extraction logic; escalate to user.

### Test cases

- Verify PlayerStats stats sub-object contains all `scoreValue*` fields observed
  in the sample JSON (unit test against the known sample file).
- Verify every event type from Step 1.6 appears in the output CSV.

---

## Step 1.9E — Game `event_data` field inventory (per event type)

**File to modify:** `src/rts_predict/sc2/data/exploration.py`
(reuse functions added in 1.9D, parameterised with `table_name`)

### Sub-steps

**1.9E-i** — Enumerate all distinct JSON keys in `game_events_raw.event_data`,
per event type (sample 200 000 rows; mandatory due to 609M row count).

**1.9E-ii** — Enumerate nested sub-object keys for high-value event types:
- `Cmd` → `abil` sub-object, `data` sub-object
- `SelectionDelta` → `delta` sub-object

**1.9E-iii** — Run key-constancy query for the 5 analytically relevant types:
`Cmd`, `SelectionDelta`, `ControlGroupUpdate`, `CmdUpdateTargetPoint`,
`CmdUpdateTargetUnit`. (CameraUpdate omitted — trivial position-only structure.)

### Artifacts

| File | Columns |
|---|---|
| `01_09E_game_event_data_field_inventory.csv` | event_type, json_key, is_nested |
| `01_09E_game_event_data_key_constancy.csv` | event_type, key_list, n_events, pct |

### Gate condition

- **Continue:** 5 high-value event types each have a dominant key-set variant
  covering >95% of events.
- **Halt:** `Cmd` shows >10 key-set variants each covering >2% — escalate.

### Test cases

- Every event type from the game_events_raw type inventory is represented.
- `Cmd` event type contains at minimum: `abil`, `cmdFlags`, `data`, `evtTypeName`,
  `id`, `loop`, `userid` (based on sample observation).

---

## Step 1.9F — Consolidated event schema + Parquet↔DuckDB reconciliation

**File to modify:** `src/rts_predict/sc2/data/exploration.py`

### Functions to add

```python
def verify_parquet_duckdb_schema_consistency(
    staging_dir: Path,
    db_path: Path,
    table_name: str,
    batch_prefix: str,
    n_batches: int = 5,
) -> dict[str, Any]:
    """Compare a random sample of Parquet batch schemas with the DuckDB table.

    Checks column names, column types, and column order for n_batches randomly
    selected Parquet files from staging_dir matching batch_prefix*.parquet.

    Args:
        staging_dir: Directory containing batch Parquet files
        db_path: Path to db.duckdb
        table_name: DuckDB table name (e.g., 'tracker_events_raw')
        batch_prefix: Filename prefix (e.g., 'tracker_events_batch_')
        n_batches: Number of random batches to check

    Returns:
        Dict with keys: parquet_schema, duckdb_schema, mismatches, n_batches_checked
    """
    ...


def compile_event_schema_document(
    tracker_inventory: pd.DataFrame,
    game_inventory: pd.DataFrame,
    tracker_constancy: pd.DataFrame,
    game_constancy: pd.DataFrame,
) -> str:
    """Compile a markdown event_data schema reference from 1.9D/1.9E findings.

    For each event type documents: JSON key list, inferred data type, null/missing
    rate estimate, and intended Phase 4 usage.

    Returns:
        Markdown string — written to 01_09F_event_schema_reference.md
    """
    ...
```

### Sub-steps

**1.9F-i** — Parquet↔DuckDB schema reconciliation: check 5 random batches from
each of `tracker_events_batch_*` and `game_events_batch_*`. Verify column names,
types, and order match the corresponding DuckDB table.

**1.9F-ii** — Compile consolidated event schema reference markdown. For each of
the 10 tracker event types and 5 high-value game event types document: JSON key
list, inferred types, sample-based null rate estimate, Phase 4 role.

### Artifacts

| File | Description |
|---|---|
| `01_09F_parquet_duckdb_schema_reconciliation.md` | Comparison results for both table types |
| `01_09F_event_schema_reference.md` | Consolidated schema doc — authoritative input for Phase 4 |

### Gate condition

- **Continue:** Parquet and DuckDB schemas match for all checked batches AND
  event schema reference covers all 10 tracker event types and all 5 high-value
  game event types → proceed to Step 1.10.
- **Halt:** Any Parquet batch has columns absent from DuckDB (or vice versa) →
  halt and investigate data loss in ingestion pipeline.

### Test cases

- `test_verify_schema_empty_dir` — empty staging directory returns zero batches checked.
- `test_verify_schema_mismatch` — synthetic Parquet with an extra column triggers
  mismatch detection.
- `test_compile_event_schema_covers_all_types` — all event types appear in output.

---

## Downstream impact

Step 1.16 (Deliverable 1: data dictionary) must incorporate findings from 1.9D–F.
The event schema reference from 1.9F is the authoritative input for Phase 4
feature extraction — without it, Phase 4 would rediscover the schema empirically,
violating the principle that Phase 1 exploration precedes Phase 4 engineering.

The ROADMAP.md should be updated to insert Steps 1.9D, 1.9E, 1.9F between the
existing Step 1.9C entry and the Step 1.10 entry.
