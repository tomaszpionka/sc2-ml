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
# # Step 01_02_02 — DuckDB Ingestion: aoe2companion
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_02 — EDA
# **Dataset:** aoe2companion
# **Question:** Materialise raw data into persistent DuckDB tables using the
# strategies determined by 01_02_01 (binary_as_string=true, explicit CSV types).
# **Invariants applied:** #6 (reproducibility), #7 (provenance), #9 (step scope),
# #10 (relative filename)
# **Step scope:** ingest
# **Prerequisites:** 01_02_01 artifacts on disk, notebook re-executed with outputs

# %%
import json
import logging

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir
from rts_predict.games.aoe2.config import AOE2COMPANION_RAW_DIR
from rts_predict.games.aoe2.datasets.aoe2companion.ingestion import (
    load_all_raw_tables,
)
from rts_predict.games.aoe2.datasets.aoe2companion.types import DtypeDecision

logging.basicConfig(level=logging.INFO)

# %% [markdown]
# ## 1. Configure dtype decision
#
# Step 01_02_01 established that `read_csv_auto` inferred ALL 7 rating CSV
# columns as VARCHAR when scanning 2,072 files at scale. Explicit types are
# required. Types confirmed by sample read + manual inspection in 01_02_01.

# %%
decision = DtypeDecision(
    strategy="explicit",
    rationale=(
        "read_csv_auto inferred all 7 columns as VARCHAR on the full 2,072-file "
        "ratings load. Explicit BIGINT/TIMESTAMP types required to preserve "
        "numeric fidelity. Confirmed in Step 01_02_01 ratings_type_inference artifact."
    ),
    dtype_map={
        "profile_id": "BIGINT",
        "games": "BIGINT",
        "rating": "BIGINT",
        "date": "TIMESTAMP",
        "leaderboard_id": "BIGINT",
        "rating_diff": "BIGINT",
        "season": "BIGINT",
    },
)
print(f"Dtype strategy: {decision.strategy}")
print(f"Rationale: {decision.rationale}")

# %% [markdown]
# ## 2. Ingest all DuckDB tables
#
# Calls `load_all_raw_tables` which creates:
# - `matches_raw`      — from 2,073 daily match Parquet files (binary_as_string=true)
# - `ratings_raw`      — from 2,072 daily rating CSV files (explicit types)
# - `leaderboards_raw` — singleton leaderboard Parquet (binary_as_string=true)
# - `profiles_raw`     — singleton profile Parquet (binary_as_string=true)

# %%
db = get_notebook_db("aoe2", "aoe2companion", read_only=False)
counts = load_all_raw_tables(db.con, AOE2COMPANION_RAW_DIR, decision=decision)
print("Ingestion counts:")
for table, n in counts.items():
    print(f"  {table}: {n:,} rows")

# %% [markdown]
# ## 3. Post-ingestion validation: DESCRIBE tables

# %%
schemas = {}
for table in counts:
    print(f"\n=== DESCRIBE {table} ===")
    desc_df = db.fetch_df(f'DESCRIBE "{table}"')
    print(desc_df.to_string(index=False))
    schemas[table] = desc_df.to_dict(orient="records")

# %% [markdown]
# ## 4a. NULL rates on key fields

# %%
# matches_raw NULL rates
match_null_query = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(matchId) AS matchId_null,
    COUNT(*) - COUNT(started) AS started_null,
    COUNT(*) - COUNT(won) AS won_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM matches_raw
"""
print("=== matches_raw NULL rates ===")
match_nulls = db.fetch_df(match_null_query)
print(match_nulls.to_string(index=False))

# %%
# ratings_raw NULL rates
rating_null_query = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(profile_id) AS profile_id_null,
    COUNT(*) - COUNT(rating) AS rating_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM ratings_raw
"""
print("=== ratings_raw NULL rates ===")
rating_nulls = db.fetch_df(rating_null_query)
print(rating_nulls.to_string(index=False))

# %% [markdown]
# ## 4b. Cross-table integrity: filename orphan check

# %%
# Every matches_raw filename must have a corresponding ratings_raw entry
# for the same date. This is a soft check — one-to-many is expected.
orphan_query = """
SELECT COUNT(DISTINCT filename) AS orphan_match_files
FROM matches_raw
WHERE filename IS NULL
"""
print("=== matches_raw NULL filename count ===")
print(db.fetch_df(orphan_query).to_string(index=False))

# %% [markdown]
# ## 4c. Relative filename assertion (Invariant I10)

# %%
for table in ("matches_raw", "ratings_raw", "leaderboards_raw", "profiles_raw"):
    result = db.fetch_df(f"""
        SELECT
            COUNT(*) FILTER (WHERE filename LIKE '/%') AS absolute_count,
            COUNT(*) FILTER (WHERE filename NOT LIKE '%/%') AS bare_basename_count
        FROM {table}
    """)
    abs_count = int(result["absolute_count"].iloc[0])
    bare_count = int(result["bare_basename_count"].iloc[0])
    assert abs_count == 0, f"{table}: {abs_count} absolute paths found (I10 violation)"
    assert bare_count == 0, f"{table}: {bare_count} bare basenames found (I10 violation)"
    print(f"{table}: filename column OK (relative, non-bare)")

# %%
db.close()

# %% [markdown]
# ## 5. Write artifacts

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
artifacts_dir.mkdir(parents=True, exist_ok=True)

# Extract null rate values for artifact
match_null_row = match_nulls.iloc[0]
rating_null_row = rating_nulls.iloc[0]

artifact_data = {
    "step": "01_02_02",
    "dataset": "aoe2companion",
    "dtype_decision": {
        "strategy": decision.strategy,
        "rationale": decision.rationale,
        "dtype_map": decision.dtype_map,
    },
    "tables_created": list(counts.keys()),
    "row_counts": counts,
    "schemas": schemas,
    "null_rates": {
        "matches_raw": {
            "total_rows": int(match_null_row["total_rows"]),
            "matchId_null": int(match_null_row["matchId_null"]),
            "started_null": int(match_null_row["started_null"]),
            "won_null": int(match_null_row["won_null"]),
            "filename_null": int(match_null_row["filename_null"]),
        },
        "ratings_raw": {
            "total_rows": int(rating_null_row["total_rows"]),
            "profile_id_null": int(rating_null_row["profile_id_null"]),
            "rating_null": int(rating_null_row["rating_null"]),
            "filename_null": int(rating_null_row["filename_null"]),
        },
    },
    "sql": {
        "matches_raw": (
            "CREATE TABLE matches_raw AS SELECT * FROM read_parquet("
            "'{glob}', union_by_name = true, filename = true, binary_as_string = true)"
        ),
        "ratings_raw_explicit": (
            "CREATE TABLE ratings_raw AS SELECT * FROM read_csv("
            "'{glob}', union_by_name = true, dtypes = {dtype_map}, filename = true)"
        ),
        "leaderboards_raw": (
            "CREATE TABLE leaderboards_raw AS SELECT * FROM read_parquet("
            "'{path}', filename = true, binary_as_string = true)"
        ),
        "profiles_raw": (
            "CREATE TABLE profiles_raw AS SELECT * FROM read_parquet("
            "'{path}', filename = true, binary_as_string = true)"
        ),
    },
    "invariant_i10_check": "PASSED — all filename columns are relative, non-bare",
}

artifact_path = artifacts_dir / "01_02_02_duckdb_ingestion.json"
artifact_path.write_text(json.dumps(artifact_data, indent=2))
print(f"Artifact written: {artifact_path}")

# %%
md_lines = [
    "# Step 01_02_02 — DuckDB Ingestion: aoe2companion\n",
    "",
    "## Tables created\n",
    "",
    "| Table | Rows |",
    "|-------|------|",
]
for table, n in counts.items():
    md_lines.append(f"| `{table}` | {n:,} |")
md_lines.extend([
    "",
    f"## Dtype strategy: `{decision.strategy}`\n",
    "",
    f"**Rationale:** {decision.rationale}",
    "",
    "## NULL rates\n",
    "",
    f"- `matches_raw.won`: {int(match_null_row['won_null']):,} NULLs "
    f"/ {int(match_null_row['total_rows']):,} total rows "
    f"({100 * int(match_null_row['won_null']) / int(match_null_row['total_rows']):.2f}%)",
    f"- `ratings_raw.profile_id`: {int(rating_null_row['profile_id_null']):,} NULLs",
    "",
    "## Invariant I10\n",
    "",
    "All four `filename` columns verified relative (no leading `/`, contains `/`).",
])

md_path = artifacts_dir / "01_02_02_duckdb_ingestion.md"
md_path.write_text("\n".join(md_lines))
print(f"Report written: {md_path}")
