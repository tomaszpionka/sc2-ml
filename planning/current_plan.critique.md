# Adversarial Critique — Plan: DuckDB Ingestion 01_02_01

**Plan:** planning/current_plan.md
**Phase:** 01 / Pipeline Section 01_02, Step 01_02_01
**Date:** 2026-04-13
**Verdict:** REVISE

---

## Findings

### 1. [WARNING] `step_scope: "content"` is incorrect — should be `"query"`

The plan sets `step_scope: "content"` for all 3 datasets (plan lines
363, 437, 524). The research log entry template at
`docs/templates/research_log_entry_template.yaml` defines the scopes:

- `content`: "file headers, schemas, sample rows (01_01_02)"
- `query`: "DuckDB queries on ingested data (01_01_03+)"

Step 01_02_01 creates DuckDB tables, runs `DESCRIBE`, executes
`SELECT COUNT(*)`, and verifies NULL patterns — all of which are DuckDB
queries on ingested data. The plan's own Design Decision #8 (line
780-782) justifies the choice by saying "the primary activity is loading
raw files," but the template's scope taxonomy is based on the
*observation level*, not the activity type. The step reads file content
AND queries DuckDB — the highest-scope observation determines the scope,
which is `query`.

The plan even uses the phrase "Post-ingestion verification" with explicit
SQL in the method sections. This is query-scope work.

**Resolution needed:** Change `step_scope` from `"content"` to `"query"`
in all 3 dataset parameterizations and in the T02 instruction at line
629.

### 2. [NOTE] `union_by_name` auto-promotion claim cites "documentation" but behavior is undocumented

The plan cites "DuckDB 1.5.1 documentation" for `union_by_name`
auto-promotion behavior (int64↔double→DOUBLE, etc.). The official docs
do not specify this — the behavior is real (empirically confirmed) but
undocumented. The plan already includes a smoke test to verify
empirically, which is the correct approach. The smoke test IS the
research — if it fails, iterate.

### 3. [NOTE] Existing `ingestion.py` naming convention conflict is acknowledged

Existing `ingestion.py` modules use `raw_<entity>` prefix naming (e.g.,
`raw_matches`, `raw_ratings`) while this step uses `<entity>_raw` suffix
(e.g., `matches_raw`, `ratings_raw`). Verified on disk:

- `aoe2companion/ingestion.py`: uses `raw_matches`, `raw_ratings`,
  `raw_leaderboard`, `raw_profiles`
- `aoestats/ingestion.py`: uses `raw_matches`, `raw_players`

The plan acknowledges this (lines 107-111) and correctly states these
modules are not used in this step. No action required, but the naming
divergence means reconciliation must happen before any module references
these tables by name.

### 4. [NOTE] DuckDB caret range `^1.5.1` allows undocumented behavior drift

`pyproject.toml` pins DuckDB as `^1.5.1` (>=1.5.1, <2.0.0). Since
`union_by_name` auto-promotion is undocumented (Finding #2), a future
`poetry update` could install a version where this behavior changes.
The smoke test is the safety net, but the plan does not acknowledge
this version sensitivity.

### 5. [WARNING] `overviews_raw` omits `filename=true`, contradicting Design Decision #9

Design Decision #9 (lines 786-788) states: "Every raw-layer DuckDB
table includes a `filename` column from `read_parquet(filename=true)`
or equivalent — including singletons."

But the aoestats `overviews_raw` ingestion SQL at line 572-573 is:

```sql
CREATE TABLE overviews_raw AS SELECT * FROM read_json_auto(
  'raw/overview/overview.json')
```

This does not include `filename=true`. `read_json_auto` does support a
`filename` parameter. No exceptions to the provenance column rule —
singletons included.

**Resolution needed:** Add `filename=true` to the `overviews_raw`
`read_json_auto` call.

### 6. [WARNING] T02 executor model should be opus, not sonnet

The DAG assigns T02 (notebooks + ingestion + docs) to `model: "sonnet"`
(plan line 849). T02 is a parameterized task covering 3 datasets with
significantly different complexity — sc2egset involves investigating
209 GiB of nested JSON with 7,350 keypaths, pyarrow census work, and
producing a design artifact. This requires opus-level reasoning.

**Resolution needed:** Change T02 `model` from `"sonnet"` to `"opus"`
in the suggested execution graph.

### 7. [NOTE] `started_timestamp` expected type is ambiguous in gate condition

The aoestats gate condition (line 319) says `started_timestamp:
TIMESTAMP`. But 01_01_02 shows this column as `timestamp[us, tz=UTC]`
in most files. DuckDB could map this to `TIMESTAMP` (without timezone)
or `TIMESTAMPTZ` (with timezone). The smoke test will reveal the actual
type, but the gate condition should specify which is expected, or use
`TIMESTAMP*` to accept either. An unintended gate failure is low risk
but possible.

### 8. [NOTE] File manifest contradicts sc2egset investigation-only scope

The plan says sc2egset uses "temporary in-memory DB" (line 201) and the
gate condition at line 705 says "(no DuckDB tables)." But the file
manifest at line 684 lists `sc2egset/data/db/db.duckdb` with action
"Create + populate." These contradict each other.

If sc2egset investigation uses only in-memory DB, no `db.duckdb` file
should be created. Remove from file manifest or clarify that this file
is NOT expected after this step.

---

## Verified Claims (no issues found)

| Claim | Verified against | Result |
|-------|-----------------|--------|
| DuckDB 1.5.1 pinned in pyproject.toml | `pyproject.toml` | `duckdb = "^1.5.1"`, installed 1.5.1 |
| All 3 DuckDB databases deleted (clean slate) | Disk | `data/db/` dirs exist but are empty |
| 01_01_01 and 01_01_02 artifacts exist (all 3 datasets) | Disk | All 12 files present |
| sc2egset: 22,390 replay files | `01_01_01_file_inventory.json` | `total_replay_files: 22390` |
| sc2egset: 11 root keys, 7,350 keypaths | `01_01_02_schema_discovery.json` | `total_columns: 11`, keypaths 7350 |
| aoe2companion: 2,073 Parquet + 2,072 CSV | `01_01_01_file_inventory.json` | Confirmed |
| aoe2companion columns: matches 54, ratings 7, leaderboards 18, profiles 13 | `01_01_02_schema_discovery.json` | Confirmed |
| aoestats: 172 matches + 171 players files | `01_01_01_file_inventory.json` | Confirmed |
| aoestats columns: matches 17, players 13, overview 8 | `01_01_02_schema_discovery.json` | Confirmed |
| aoestats: 7 variant columns (2 matches + 5 players) | `01_01_02_schema_discovery.json` | Confirmed |
| 70 map_foreign_to_english_mapping.json files | Disk | Exactly 70 at depth 2 |
| `binary_as_string` defaults to `false` | DuckDB docs | Confirmed |
| `read_parquet` has no `types=` parameter | DuckDB docs | Only `schema=` (MAP type) |
| `get_notebook_db` exists with `read_only` param | `notebook_utils.py:80` | Confirmed |
| `jupytext.toml` at `sandbox/jupytext.toml` | Disk | Exists, `formats = "ipynb,py:percent"` |
| `01_eda/` subdirs do not exist yet | Disk | Only `01_acquisition/` exists |
| No existing `pre_ingestion.py` files | Disk | None found |
| `union_by_name` auto-promotion works in 1.5.1 | Empirical test | int64↔double→DOUBLE confirmed |
| `union_by_name` fills NULLs for absent columns | Empirical test | Confirmed |

## Invariant Compliance

| # | Invariant | Status | Notes |
|---|-----------|--------|-------|
| 6 | Reproducibility | RESPECTED | All code in notebooks, paired with outputs. Smoke test + full SQL documented. |
| 7 | No magic numbers | RESPECTED | File counts/column counts traced to 01_01_01/01_01_02. Sample selection from per-directory size data. |
| 9 | Pipeline discipline | AT RISK | `step_scope: "content"` too narrow for query-level work (Finding #1). Conclusions otherwise correctly scoped. |

## Required Revisions

1. **(WARNING #1)** Change `step_scope` from `"content"` to `"query"` in
   all 3 dataset parameterizations and T02 instructions.
2. **(WARNING #5)** Add `filename=true` to `overviews_raw`
   `read_json_auto` call — no exceptions to provenance column rule.
3. **(WARNING #6)** Change T02 executor model from `"sonnet"` to
   `"opus"`.

## Notes (no action required)

4. `union_by_name` auto-promotion is undocumented but empirically
   confirmed. Smoke test is the research — iterate if it fails.
5. Naming convention divergence (`raw_` prefix vs `_raw` suffix) is
   acknowledged; reconciliation tracked for future step.
6. DuckDB caret range permits behavior drift for undocumented features.
   Smoke test mitigates.
7. `started_timestamp` gate condition should specify TIMESTAMP vs
   TIMESTAMPTZ.
8. File manifest lists sc2egset `db.duckdb` as "Create + populate" but
   investigation is in-memory only.
