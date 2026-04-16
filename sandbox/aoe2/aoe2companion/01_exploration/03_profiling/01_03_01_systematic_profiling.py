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
# # Step 01_03_01 -- Systematic Data Profiling: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** aoe2companion
# **Question:** What is the complete statistical profile of every column
#   in matches_raw? Are there dead fields, constant columns, near-constant
#   columns, or primary key violations?
# **Invariants applied:**
#   - #3 (temporal discipline -- every column labelled with I3 classification)
#   - #6 (reproducibility -- all SQL queries written verbatim to artifacts)
#   - #7 (no magic numbers -- thresholds from Manual 3.3 and census data)
#   - #9 (step scope -- consolidates 01_02 findings into structured profile)
# **Predecessor:** 01_02_07 (Multivariate EDA)
# **Step scope:** Systematic profiling. No DuckDB writes. No new tables.
# **Outputs:** JSON profile, completeness heatmap, QQ plot, ECDF plot, MD report
# Commit: 06fee1f
# Date: 2026-04-16
# ROADMAP ref: 01_03_01

# %% [markdown]
# ## 0. Imports and DB connection

# %%
import json
import math
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as scipy_stats

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()
matplotlib.use("Agg")

# %%
db = get_notebook_db("aoe2", "aoe2companion")
con = db.con
print("Connected via get_notebook_db: aoe2 / aoe2companion")

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
census_artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
profiling_dir = reports_dir / "artifacts" / "01_exploration" / "03_profiling"
profiling_dir.mkdir(parents=True, exist_ok=True)
plots_dir = profiling_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

census_json_path = census_artifacts_dir / "01_02_04_univariate_census.json"
with open(census_json_path) as f:
    census = json.load(f)
print(f"Census loaded: {len(census)} top-level keys")

# %%
required_keys = [
    "matches_raw_total_rows",
    "matches_raw_null_census",
    "matches_raw_numeric_stats",
    "categorical_profiles",
    "boolean_census",
    "field_classification",
    "won_distribution",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"
print(f"All {len(required_keys)} required census keys present")

# %%
# Build I3 classification for all columns.
# Source: census field_classification (01_02_04) with 01_02_06 overrides.
# 01_02_06 confirmed: ratingDiff=POST-GAME, rating=AMBIGUOUS.
# duration_min is derived (finished - started); finished=post_game per census.
I3_CLASSIFICATION = {}
for entry in census["field_classification"]["fields"]:
    I3_CLASSIFICATION[entry["column"]] = entry["temporal_class"].upper()

# Override with 01_02_06 findings (authoritative)
I3_CLASSIFICATION["ratingDiff"] = "POST_GAME"
# W1 fix: rating classified as AMBIGUOUS per 01_02_06 Q2.
# 01_02_06 heading uses "RESULT PENDING"; the plot index and statistical test
# sections use "AMBIGUOUS", which also matches the census field_classification
# "ambiguous_pre_or_post". Treated as AMBIGUOUS here; resolution requires Phase
# 02 row-level verification with ratings_raw (deferred to 01_04).
I3_CLASSIFICATION["rating"] = "AMBIGUOUS"  # 01_02_06 Q2: classified "RESULT PENDING" (unresolved temporal class).
                                             # 42.46% NULL; resolution deferred to 01_04.
# duration_min is a derived column (not in raw table); note for later
I3_DURATION_MIN = "POST_GAME"  # finished is POST_GAME

print(f"I3 classifications for {len(I3_CLASSIFICATION)} columns")
for col, cls in sorted(I3_CLASSIFICATION.items()):
    print(f"  {col}: {cls}")

# %%
sql_queries = {}

total_rows = census["matches_raw_total_rows"]  # 277,099,059

# I7: BERNOULLI sample fraction for QQ/ECDF distribution visualization.
# 277M rows * 0.02% = ~55,400 rows per sample.
# For QQ normality assessment: Cleveland (1993) recommends N > 1,000 for reliable
# normal probability plots. N=55,400 is 55x that minimum. The SE of the median
# quantile estimate is ~ sigma / (2 * sqrt(N) * f(median)) which is negligible
# at N=55K. Source: Wilk & Gnanadesikan (1968), JSTOR.
SAMPLE_PCT_VIZ = 0.02  # I7: yields ~55K rows at 277M scale; Cleveland (1993) min 1K; Wilk & Gnanadesikov (1968) SE criterion
TARGET_SAMPLE_ROWS = int(total_rows * SAMPLE_PCT_VIZ / 100)
print(f"Total rows: {total_rows:,}")
print(f"BERNOULLI sample pct: {SAMPLE_PCT_VIZ}%")
print(f"Expected sample rows: ~{TARGET_SAMPLE_ROWS:,}")

# I7: near-constant thresholds from Manual 3.3
NEAR_CONSTANT_UNIQUENESS_RATIO = 0.001  # Manual 3.3

# %% [markdown]
# ## 1. Column-Level Profiling (Section 3.1)

# %%
# Reuse census null_census data (exact counts from 01_02_04, full-table scan)
null_census = {
    entry["column_name"]: entry
    for entry in census["matches_raw_null_census"]
}
print(f"Null census columns: {len(null_census)}")

# %%
numeric_cols = [s["column_name"] for s in census["matches_raw_numeric_stats"]]
print(f"Numeric columns from census: {numeric_cols}")

# Build zero-count query
zero_parts = []
for col in numeric_cols:
    zero_parts.append(f"SUM(CASE WHEN {col} = 0 THEN 1 ELSE 0 END) AS {col}_zero_count")
zero_sql = "SELECT\n    " + (",\n    ".join(zero_parts)) + "\nFROM matches_raw"
sql_queries["zero_count_numeric"] = zero_sql
print(f"Executing zero count query for {len(numeric_cols)} numeric columns...")
zero_result = con.execute(zero_sql).fetchdf().iloc[0]
zero_counts = {col: int(zero_result[f"{col}_zero_count"]) for col in numeric_cols}
for col, zc in zero_counts.items():
    pct = zc * 100.0 / total_rows
    print(f"  {col}: {zc:,} zeros ({pct:.2f}%)")

# %%
# DuckDB >= 1.0.0 native SKEWNESS/KURTOSIS; KURTOSIS() returns excess kurtosis (kurtosis - 3). Exact values over full 277M rows.
skew_kurt_sql = """
SELECT
    SKEWNESS(rating) AS rating_skew,       KURTOSIS(rating) AS rating_kurt,
    SKEWNESS(ratingDiff) AS ratingDiff_skew, KURTOSIS(ratingDiff) AS ratingDiff_kurt,
    SKEWNESS(population) AS population_skew, KURTOSIS(population) AS population_kurt,
    SKEWNESS(slot) AS slot_skew,            KURTOSIS(slot) AS slot_kurt,
    SKEWNESS(color) AS color_skew,          KURTOSIS(color) AS color_kurt,
    SKEWNESS(team) AS team_skew,            KURTOSIS(team) AS team_kurt,
    SKEWNESS(speedFactor) AS speedFactor_skew, KURTOSIS(speedFactor) AS speedFactor_kurt,
    SKEWNESS(treatyLength) AS treatyLength_skew, KURTOSIS(treatyLength) AS treatyLength_kurt,
    SKEWNESS(internalLeaderboardId) AS internalLeaderboardId_skew,
    KURTOSIS(internalLeaderboardId) AS internalLeaderboardId_kurt,
    SKEWNESS(EXTRACT(EPOCH FROM (finished - started)) / 60.0)
        FILTER (WHERE finished > started) AS duration_min_skew,
    KURTOSIS(EXTRACT(EPOCH FROM (finished - started)) / 60.0)
        FILTER (WHERE finished > started) AS duration_min_kurt
FROM matches_raw
"""
sql_queries["skewness_kurtosis"] = skew_kurt_sql
print("Computing exact skewness/kurtosis via DuckDB native aggregation...")
sk_result = con.execute(skew_kurt_sql).fetchdf().iloc[0]

# Build skewness_kurtosis dict for all 10 columns
skew_kurt_cols = [
    "rating", "ratingDiff", "population", "slot", "color", "team",
    "speedFactor", "treatyLength", "internalLeaderboardId", "duration_min",
]
skewness_kurtosis = {}
for col in skew_kurt_cols:
    sk_val = sk_result[f"{col}_skew"]
    ku_val = sk_result[f"{col}_kurt"]
    sk_float = round(float(sk_val), 4) if sk_val is not None and not np.isnan(sk_val) else None
    ku_float = round(float(ku_val), 4) if ku_val is not None and not np.isnan(ku_val) else None
    skewness_kurtosis[col] = {
        "skewness": sk_float,
        "kurtosis": ku_float,  # excess kurtosis (DuckDB convention)
    }
    print(f"  {col}: skew={sk_float}, kurtosis(excess)={ku_float}")

print(f"\nExact skewness/kurtosis computed for {len(skewness_kurtosis)} columns "
      f"(full table, {total_rows:,} rows, per-column NULL exclusion)")

# %%
# I7: IQR fences from census p25/p75 (Tukey 1.5*IQR criterion)
numeric_stats_lookup = {
    s["column_name"]: s for s in census["matches_raw_numeric_stats"]
}

# Pre-compute fences for all columns with IQR > 0
iqr_fences = {}
iqr_outlier_counts = {}
for col in numeric_cols:
    stats = numeric_stats_lookup[col]
    p25 = stats["p25"]
    p75 = stats["p75"]
    iqr = p75 - p25
    if iqr == 0:
        # Near-constant: IQR=0 means any value != p25 is "outlier" by IQR rule
        # but this is misleading for near-constant columns; report as N/A
        iqr_outlier_counts[col] = {
            "iqr": 0.0, "lower_fence": p25, "upper_fence": p75,
            "outlier_count": None,
            "note": "IQR=0 (near-constant); IQR outlier detection not meaningful"
        }
        print(f"  {col}: IQR=0 (near-constant), outlier count N/A")
    else:
        lower_fence = p25 - 1.5 * iqr
        upper_fence = p75 + 1.5 * iqr
        iqr_fences[col] = (lower_fence, upper_fence, iqr)

# W4 fix: consolidated single-scan query for all columns with IQR > 0
if iqr_fences:
    filter_parts = []
    for col, (lower, upper, _) in iqr_fences.items():
        filter_parts.append(
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL "
            f"AND ({col} < {lower} OR {col} > {upper})) AS {col}_iqr_outliers"
        )
    iqr_sql = "SELECT\n    " + (",\n    ".join(filter_parts)) + "\nFROM matches_raw"
    sql_queries["iqr_outlier_all"] = iqr_sql
    print(f"Executing consolidated IQR outlier query for {len(iqr_fences)} columns...")
    iqr_result = con.execute(iqr_sql).fetchdf().iloc[0]

    for col, (lower, upper, iqr) in iqr_fences.items():
        outlier_count = int(iqr_result[f"{col}_iqr_outliers"])
        non_null = total_rows - null_census[col]["null_count"]
        outlier_pct = outlier_count * 100.0 / non_null if non_null > 0 else 0.0
        iqr_outlier_counts[col] = {
            "iqr": float(iqr), "lower_fence": float(lower),
            "upper_fence": float(upper),
            "outlier_count": outlier_count,
            "outlier_pct": round(outlier_pct, 4),
        }
        print(f"  {col}: IQR={iqr:.2f}, fences=[{lower:.2f}, {upper:.2f}], "
              f"outliers={outlier_count:,} ({outlier_pct:.2f}%)")

# %%
# Categorical columns: leaderboard, civ, map, gameMode, gameVariant, speed,
# difficulty, startingAge, endingAge, mapSize, resources, victory,
# civilizationSet, revealMap, server, privacy, status, country,
# scenario, modDataset, colorHex
CATEGORICAL_COLS = [
    "leaderboard", "civ", "map", "gameMode", "gameVariant", "speed",
    "difficulty", "startingAge", "endingAge", "mapSize", "resources",
    "victory", "civilizationSet", "revealMap", "server", "privacy",
    "status", "country", "scenario", "modDataset", "colorHex",
]

topk_profiles = {}
K = 5
for col in CATEGORICAL_COLS:
    topk_sql = f"""
SELECT {col} AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / {total_rows}, 2) AS pct
FROM matches_raw
WHERE {col} IS NOT NULL
GROUP BY {col}
ORDER BY cnt DESC
LIMIT {K}
"""
    sql_queries[f"topk_{col}"] = topk_sql
    df_topk = con.execute(topk_sql).fetchdf()
    topk_profiles[col] = df_topk.to_dict(orient="records")

print(f"Top-{K} profiles computed for {len(CATEGORICAL_COLS)} categorical columns")
for col in CATEGORICAL_COLS[:3]:
    print(f"  {col}: {[r['value'] for r in topk_profiles[col]]}")

# %%
column_profiles = []
for entry in census["matches_raw_null_census"]:
    col = entry["column_name"]
    profile = {
        "column": col,
        "i3_classification": I3_CLASSIFICATION.get(col, "UNKNOWN"),
        "null_count": entry["null_count"],
        "null_pct": entry["null_pct"],
        "cardinality": entry["approx_cardinality"],
        "uniqueness_ratio": round(
            entry["approx_cardinality"] / total_rows, 8
        ),
    }
    # Zero count (numeric only)
    if col in zero_counts:
        profile["zero_count"] = zero_counts[col]
        profile["zero_pct"] = round(zero_counts[col] * 100.0 / total_rows, 4)
    # Descriptive stats (numeric only)
    if col in numeric_stats_lookup:
        ns = numeric_stats_lookup[col]
        profile["mean"] = ns["mean_val"]
        profile["std"] = ns["stddev_val"]
        profile["min"] = ns["min_val"]
        profile["p05"] = ns["p05"]
        profile["p25"] = ns["p25"]
        profile["p50"] = ns["median_val"]
        profile["p75"] = ns["p75"]
        profile["p95"] = ns["p95"]
        profile["max"] = ns["max_val"]
    # Skewness/kurtosis (numeric + duration_min)
    if col in skewness_kurtosis:
        profile["skewness"] = skewness_kurtosis[col]["skewness"]
        profile["kurtosis"] = skewness_kurtosis[col]["kurtosis"]
    # IQR outlier count
    if col in iqr_outlier_counts:
        profile["iqr_outlier"] = iqr_outlier_counts[col]
    # Top-k (categorical)
    if col in topk_profiles:
        profile["top_k"] = topk_profiles[col]
    column_profiles.append(profile)

print(f"Column profiles assembled: {len(column_profiles)} columns")

# Verify all 9 census numeric columns + duration_min have skewness/kurtosis
numeric_with_sk = [p["column"] for p in column_profiles if "skewness" in p]
print(f"Columns with skewness/kurtosis: {len(numeric_with_sk)} "
      f"({', '.join(numeric_with_sk)})")

# %% [markdown]
# ## 2. Dataset-Level Profiling (Section 3.2)

# %%
# Primary key = (matchId, profileId) -- each player-match row should be unique
dup_sql = """
SELECT matchId, profileId, COUNT(*) AS cnt
FROM matches_raw
GROUP BY matchId, profileId
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 20
"""
sql_queries["duplicate_detection"] = dup_sql
print("Checking primary key (matchId, profileId) integrity...")
df_dups = con.execute(dup_sql).fetchdf()
n_dup_groups = len(df_dups)
if n_dup_groups > 0:
    total_dup_rows_sql = """
SELECT SUM(cnt) AS total_dup_rows, COUNT(*) AS dup_groups
FROM (
    SELECT matchId, profileId, COUNT(*) AS cnt
    FROM matches_raw
    GROUP BY matchId, profileId
    HAVING COUNT(*) > 1
)
"""
    sql_queries["duplicate_totals"] = total_dup_rows_sql
    dup_totals = con.execute(total_dup_rows_sql).fetchdf().iloc[0]
    dup_info = {
        "has_duplicates": True,
        "dup_groups": int(dup_totals["dup_groups"]),
        "total_dup_rows": int(dup_totals["total_dup_rows"]),
        "sample_dups": df_dups.to_dict(orient="records"),
    }
    print(f"  DUPLICATES FOUND: {dup_info['dup_groups']:,} groups, "
          f"{dup_info['total_dup_rows']:,} total rows")
else:
    dup_info = {"has_duplicates": False, "dup_groups": 0, "total_dup_rows": 0}
    print("  No duplicates found -- primary key is clean")

# %%
won_dist = census["won_distribution"]
class_balance = {
    "target_column": "won",
    "distribution": won_dist,
    "note": census.get("exact_won_null_note", {}).get("resolution", ""),
}
for entry in won_dist:
    print(f"  won={entry['won']}: {entry['cnt']:,} ({entry['pct']}%)")

# %%
completeness_data = []
for entry in census["matches_raw_null_census"]:
    completeness_data.append({
        "column": entry["column_name"],
        "null_pct": entry["null_pct"],
        "completeness_pct": round(100.0 - entry["null_pct"], 2),
    })
# Sort by null_pct descending for heatmap ordering
completeness_data.sort(key=lambda x: x["null_pct"], reverse=True)
print(f"Completeness data: {len(completeness_data)} columns")
print(f"Most incomplete: {completeness_data[0]['column']} ({completeness_data[0]['null_pct']}% null)")
print(f"Most complete: {completeness_data[-1]['column']} ({completeness_data[-1]['null_pct']}% null)")

# %%
# DuckDB 1.5.1: pragma_storage_info does not expose compressed_size/uncompressed_size.
# Use pragma_database_size for block-level footprint (whole DB file, not per-table).
footprint_sql = """
SELECT
    total_blocks * block_size AS total_bytes,
    used_blocks * block_size AS used_bytes
FROM pragma_database_size()
"""
sql_queries["memory_footprint"] = footprint_sql
footprint_result = con.execute(footprint_sql).fetchdf().iloc[0]
memory_footprint = {
    "total_bytes": int(footprint_result["total_bytes"]),
    "used_bytes": int(footprint_result["used_bytes"]),
    "total_gb": round(int(footprint_result["total_bytes"]) / (1024**3), 2),
    "used_gb": round(int(footprint_result["used_bytes"]) / (1024**3), 2),
    "total_rows": total_rows,
    "note": (
        "DuckDB 1.5.1: pragma_database_size() whole-DB block counts. "
        "total_bytes=allocated blocks*block_size; used_bytes=used blocks*block_size. "
        "Per-table footprint not available via pragma_storage_info in this DuckDB version."
    ),
}
print(f"Memory footprint: {memory_footprint['total_gb']:.2f} GB total allocated, "
      f"{memory_footprint['used_gb']:.2f} GB used (whole DB)")

# %%
dataset_profile = {
    "total_rows": total_rows,
    "total_columns": len(column_profiles),
    "duplicate_detection": dup_info,
    "class_balance": class_balance,
    "completeness_data": completeness_data,
    "memory_footprint": memory_footprint,
}
print(f"Dataset profile: {total_rows:,} rows, {len(column_profiles)} columns")

# %% [markdown]
# ## 3. Critical Detection (Section 3.3)

# %%
dead_fields = []
constant_columns = []
near_constant_columns = []

for p in column_profiles:
    col = p["column"]
    # Dead fields: 100% null
    if p["null_pct"] == 100.0:
        dead_fields.append({"column": col, "null_pct": 100.0})

    # Constant columns: cardinality == 1
    if p["cardinality"] == 1:
        constant_columns.append({
            "column": col, "cardinality": 1,
            "null_pct": p["null_pct"],
        })

    # Near-constant: uniqueness_ratio < 0.001 OR IQR == 0 for numeric
    is_near_constant = False
    reasons = []
    if p["uniqueness_ratio"] < NEAR_CONSTANT_UNIQUENESS_RATIO:
        is_near_constant = True
        reasons.append(f"uniqueness_ratio={p['uniqueness_ratio']:.8f} < {NEAR_CONSTANT_UNIQUENESS_RATIO}")
    if "iqr_outlier" in p and p["iqr_outlier"].get("iqr") == 0:
        is_near_constant = True
        reasons.append("IQR=0")
    if is_near_constant and p["cardinality"] > 1:
        near_constant_columns.append({
            "column": col,
            "cardinality": p["cardinality"],
            "uniqueness_ratio": p["uniqueness_ratio"],
            "iqr": p.get("iqr_outlier", {}).get("iqr"),
            "reasons": reasons,
            "i3_classification": p["i3_classification"],
        })

critical_findings = {
    "dead_fields": dead_fields,
    "dead_fields_count": len(dead_fields),
    "constant_columns": constant_columns,
    "constant_columns_count": len(constant_columns),
    "near_constant_columns": near_constant_columns,
    "near_constant_columns_count": len(near_constant_columns),
    "thresholds": {
        "near_constant_uniqueness_ratio": NEAR_CONSTANT_UNIQUENESS_RATIO,
        "iqr_zero_flagged": True,
        "source": "Manual 3.3 + census percentiles (I7)",
    },
}

print(f"Dead fields: {len(dead_fields)}")
for d in dead_fields:
    print(f"  {d['column']}")
print(f"Constant columns: {len(constant_columns)}")
for c in constant_columns:
    print(f"  {c['column']} (null_pct={c['null_pct']}%)")
print(f"Near-constant columns: {len(near_constant_columns)}")
for nc in near_constant_columns:
    print(f"  {nc['column']}: {', '.join(nc['reasons'])}")

# %% [markdown]
# ## 3b. Near-constant Stratification (R11)
#
# Stratify the near-constant columns into "genuinely uninformative" vs
# "low cardinality categorical" using a hybrid approach: IQR + top_k +
# boolean_census + cardinality fallback.

# %%
# Build dominant-value percentage lookup from boolean_census
boolean_dominant_pct = {}
for entry in census["boolean_census"]:
    col = entry["column_name"]
    non_null = entry["true_count"] + entry["false_count"]
    if non_null > 0:
        dominant = max(entry["true_count"], entry["false_count"])
        boolean_dominant_pct[col] = dominant * 100.0 / non_null

# won from won_distribution (exclude NULLs)
won_non_null = sum(
    e["cnt"] for e in census["won_distribution"] if e["won"] is not None
)
won_dominant = max(
    e["cnt"] for e in census["won_distribution"] if e["won"] is not None
)
boolean_dominant_pct["won"] = won_dominant * 100.0 / won_non_null

print(f"Boolean dominant_pct lookup: {len(boolean_dominant_pct)} columns")
for col, pct in sorted(boolean_dominant_pct.items()):
    print(f"  {col}: {pct:.2f}%")

# %%
# I7: 95% dominant-value threshold follows scikit-learn VarianceThreshold
# and caret nearZeroVar conventions (default frequency ratio 95/5).
# At 277M rows, dominant value must account for >263M rows to trigger.
DOMINANT_VALUE_THRESHOLD = 95.0

genuinely_uninformative = []
low_cardinality_categorical = []

for nc in near_constant_columns:
    col = nc["column"]

    # Rule 0: TARGET is never uninformative
    if nc["i3_classification"] == "TARGET":
        low_cardinality_categorical.append(col)
        continue

    # Rule 1: IQR available and IQR == 0
    if nc.get("iqr") is not None and nc["iqr"] == 0:
        genuinely_uninformative.append(col)
        continue

    # Rule 2: top_k available -- check top-1 percentage
    col_profile = next(
        (p for p in column_profiles if p["column"] == col), None
    )
    if col_profile and "top_k" in col_profile and col_profile["top_k"]:
        top1_pct = col_profile["top_k"][0]["pct"]
        if top1_pct > DOMINANT_VALUE_THRESHOLD:
            genuinely_uninformative.append(col)
        else:
            low_cardinality_categorical.append(col)
        continue

    # Rule 3: boolean_census available
    if col in boolean_dominant_pct:
        if boolean_dominant_pct[col] > DOMINANT_VALUE_THRESHOLD:
            genuinely_uninformative.append(col)
        else:
            low_cardinality_categorical.append(col)
        continue

    # Rule 4: cardinality heuristic fallback (only filename expected here)
    if nc["i3_classification"] == "IDENTIFIER":
        low_cardinality_categorical.append(col)
    elif nc["cardinality"] == 1:
        genuinely_uninformative.append(col)
    else:
        low_cardinality_categorical.append(col)

assert (
    len(genuinely_uninformative) + len(low_cardinality_categorical)
    == len(near_constant_columns)
), (
    f"Stratification mismatch: {len(genuinely_uninformative)} + "
    f"{len(low_cardinality_categorical)} != {len(near_constant_columns)}"
)

print(f"\nNear-constant stratification:")
print(f"  Genuinely uninformative ({len(genuinely_uninformative)}): "
      f"{genuinely_uninformative}")
print(f"  Low-cardinality categorical ({len(low_cardinality_categorical)}): "
      f"{low_cardinality_categorical}")

# Verify key classifications
assert "won" in low_cardinality_categorical, "TARGET column 'won' must be low_cardinality_categorical"

# %%
critical_findings["near_constant_stratification"] = {
    "genuinely_uninformative": genuinely_uninformative,
    "genuinely_uninformative_count": len(genuinely_uninformative),
    "low_cardinality_categorical": low_cardinality_categorical,
    "low_cardinality_categorical_count": len(low_cardinality_categorical),
    "stratification_criteria": {
        "genuinely_uninformative": (
            "IQR=0 (numeric) OR dominant value > 95% of non-null rows "
            "(from top_k or boolean_census)"
        ),
        "low_cardinality_categorical": (
            "Flagged by uniqueness_ratio < 0.001 only due to large table "
            "size; dominant value <= 95% indicates meaningful variation"
        ),
        "threshold_justification": (
            "I7: 95% dominant-value threshold follows scikit-learn "
            "VarianceThreshold and caret nearZeroVar conventions "
            "(default frequency ratio 95/5)."
        ),
    },
    "data_sources": {
        "iqr": "column_profiles (9 numeric columns)",
        "top_k": "column_profiles (21 categorical columns)",
        "boolean_census": "01_02_04 census (18 BOOLEAN columns)",
        "won_distribution": "01_02_04 census (target column)",
        "cardinality_heuristic": "column_profiles cardinality + I3 class (filename only)",
    },
    # [Critique fix: WARNING I8]
    "cross_notebook_asymmetry_note": (
        "The aoestats notebook applies NEAR_CONSTANT_CARDINALITY_CAP=5 in "
        "near-constant detection, resulting in 3 flagged columns vs 50 here. "
        "The difference is due to the much larger row count (277M vs 30M) "
        "making the uniqueness_ratio threshold more aggressive. The "
        "stratification resolves this by separating genuinely uninformative "
        "columns from low-cardinality categoricals."
    ),
}
print("Near-constant stratification added to critical_findings")

# %% [markdown]
# ## 4. Leaderboard-Stratified Rating Profile

# %%
LEADERBOARD_1V1_FILTER = "leaderboard IN ('rm_1v1', 'qp_rm_1v1')"

rating_strat_sql = f"""
SELECT
    'full_table' AS scope,
    COUNT(*) AS n_rows,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) AS rating_null,
    ROUND(SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS rating_null_pct,
    ROUND(AVG(rating), 2) AS rating_mean,
    ROUND(STDDEV(rating), 2) AS rating_std,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating) AS rating_median,
    SUM(CASE WHEN ratingDiff IS NULL THEN 1 ELSE 0 END) AS ratingdiff_null,
    ROUND(AVG(ratingDiff), 4) AS ratingdiff_mean
FROM matches_raw

UNION ALL

SELECT
    '1v1_ranked' AS scope,
    COUNT(*) AS n_rows,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) AS rating_null,
    ROUND(SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS rating_null_pct,
    ROUND(AVG(rating), 2) AS rating_mean,
    ROUND(STDDEV(rating), 2) AS rating_std,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating) AS rating_median,
    SUM(CASE WHEN ratingDiff IS NULL THEN 1 ELSE 0 END) AS ratingdiff_null,
    ROUND(AVG(ratingDiff), 4) AS ratingdiff_mean
FROM matches_raw
WHERE {LEADERBOARD_1V1_FILTER}
"""
sql_queries["rating_stratified"] = rating_strat_sql
df_rating_strat = con.execute(rating_strat_sql).fetchdf()
rating_stratified = df_rating_strat.to_dict(orient="records")
print("Rating stratification:")
for row in rating_stratified:
    print(f"  {row['scope']}: n={row['n_rows']:,}, "
          f"rating_null={row['rating_null_pct']}%, "
          f"rating_mean={row['rating_mean']}, "
          f"ratingdiff_mean={row['ratingdiff_mean']}")

# %% [markdown]
# ## 5. Completeness Heatmap (Artifact 2)

# %%
# Sort columns by null_pct descending
comp_df = pd.DataFrame(completeness_data)
# Only show columns with non-zero null_pct (otherwise heatmap is trivially green)
comp_nonzero = comp_df[comp_df["null_pct"] > 0].copy()
comp_nonzero = comp_nonzero.sort_values("null_pct", ascending=True)

fig, ax = plt.subplots(figsize=(8, max(6, len(comp_nonzero) * 0.35)))
y_pos = range(len(comp_nonzero))
ax.barh(list(y_pos), comp_nonzero["null_pct"].values, color=plt.cm.RdYlGn_r(
    comp_nonzero["null_pct"].values / 100.0))
ax.set_yticks(list(y_pos))
ax.set_yticklabels(comp_nonzero["column"].values, fontsize=8)
ax.set_xlabel("NULL %")
ax.set_title(
    f"Completeness Profile -- aoe2companion matches_raw\n"
    f"({total_rows:,} rows, {len(comp_nonzero)} columns with NULLs "
    f"of {len(comp_df)} total)"
)

# Annotate bars with percentages
for i, (pct, col) in enumerate(zip(comp_nonzero["null_pct"].values, comp_nonzero["column"].values)):
    ax.text(pct + 0.5, i, f"{pct:.1f}%", va="center", fontsize=7)

fig.tight_layout()
heatmap_path = plots_dir / "01_03_01_completeness_heatmap.png"
fig.savefig(heatmap_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {heatmap_path}")

# %% [markdown]
# ## 5b. Temporal Coverage (Section 3.2)

# %%
temporal_coverage_sql = """
SELECT
    MIN(started) AS min_started,
    MAX(started) AS max_started,
    COUNT(DISTINCT DATE_TRUNC('month', started)) AS distinct_months
FROM matches_raw
WHERE started IS NOT NULL
"""
sql_queries["temporal_coverage"] = temporal_coverage_sql
print("Querying temporal coverage...")
tc_result = con.execute(temporal_coverage_sql).fetchdf().iloc[0]
tc_min = str(tc_result["min_started"])
tc_max = str(tc_result["max_started"])
tc_distinct_months = int(tc_result["distinct_months"])
print(f"  Min started: {tc_min}")
print(f"  Max started: {tc_max}")
print(f"  Distinct months: {tc_distinct_months}")

# %%
temporal_gaps_sql = """
WITH monthly AS (
    SELECT DISTINCT DATE_TRUNC('month', started) AS month
    FROM matches_raw
    WHERE started IS NOT NULL
),
expected AS (
    SELECT UNNEST(GENERATE_SERIES(
        (SELECT MIN(month) FROM monthly),
        (SELECT MAX(month) FROM monthly),
        INTERVAL '1 MONTH'
    )) AS month
)
SELECT e.month
FROM expected e
LEFT JOIN monthly m ON e.month = m.month
WHERE m.month IS NULL
ORDER BY e.month
"""
sql_queries["temporal_gaps"] = temporal_gaps_sql
print("Querying temporal gaps...")
gaps_df = con.execute(temporal_gaps_sql).fetchdf()
temporal_gaps = [str(g) for g in gaps_df["month"].tolist()]
print(f"  Missing months: {len(temporal_gaps)}")
for g in temporal_gaps:
    print(f"    {g}")

# %%
temporal_coverage = {
    "min_started": tc_min,
    "max_started": tc_max,
    "distinct_months": tc_distinct_months,
    "missing_months": temporal_gaps,
    "missing_months_count": len(temporal_gaps),
}
print(f"Temporal coverage assembled: {tc_min} to {tc_max}, "
      f"{tc_distinct_months} distinct months, {len(temporal_gaps)} gaps")

# %% [markdown]
# ## 6. QQ Plots (Artifact 3)

# %%
# Shared sample for QQ and ECDF (T08+T09)
# Use a fresh sample with broad NULL tolerance (per-column dropna in plotting)
qq_ecdf_sql = f"""
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI({SAMPLE_PCT_VIZ:.6f} PERCENT)
) sub
WHERE finished > started
"""
sql_queries["qq_ecdf_sample"] = qq_ecdf_sql
print("Fetching BERNOULLI sample for QQ/ECDF...")
df_viz = con.execute(qq_ecdf_sql).fetchdf()
n_viz = len(df_viz)
print(f"QQ/ECDF sample rows: {n_viz:,}")
# I7: 5000 minimum for reliable distributional visualization.
# SE of sample quantile at N=5000 is negligible for practical normality assessment.
# Cleveland (1993) recommends N > 1,000 for normal probability plots;
# 5000 provides ~5x safety margin. At N=5000, SE(median) ~ sigma/(2*sqrt(N)*f(median))
# is < 1% of sigma for any symmetric unimodal distribution.
assert n_viz >= 5000, (
    f"QQ/ECDF sample too small: n={n_viz}. "
    f"Expected ~{TARGET_SAMPLE_ROWS:,} rows from BERNOULLI {SAMPLE_PCT_VIZ}%."
)

# %%
# W3 fix: Spearman sample assertion (5000 minimum for SE(rho) ~ 1/sqrt(5000) ~ 0.014)
n_spearman = n_viz
assert n_spearman >= 5000, f"Spearman sample too small: n={n_spearman}"
# 5000: SE(rho) ~ 1/sqrt(5000) ~ 0.014 at N=5000; acceptable for correlation matrix
print(f"Sample size assertion passed: n={n_spearman:,} >= 5000")

# %%
qq_columns = ["rating", "ratingDiff", "duration_min", "population", "speedFactor"]
qq_i3_labels = {
    "rating": "AMBIGUOUS",
    "ratingDiff": "POST_GAME",
    "duration_min": "POST_GAME",
    "population": "PRE_GAME",
    "speedFactor": "PRE_GAME",
}

n_cols = len(qq_columns)
fig, axes = plt.subplots(1, n_cols, figsize=(4 * n_cols, 4))
if n_cols == 1:
    axes = [axes]

for ax, col in zip(axes, qq_columns):
    data = df_viz[col].dropna().values
    if len(data) < 10:
        ax.text(0.5, 0.5, f"Insufficient data\n(n={len(data)})",
                transform=ax.transAxes, ha="center", va="center")
        ax.set_title(f"{col}\n[{qq_i3_labels[col]}]", fontsize=9)
        continue
    scipy_stats.probplot(data, dist="norm", plot=ax)
    ax.set_title(f"{col}\n[{qq_i3_labels[col]}]", fontsize=9)
    ax.get_lines()[0].set_markersize(1)
    ax.get_lines()[0].set_alpha(0.3)

fig.suptitle(
    f"QQ Plots (Normal Reference) -- aoe2companion matches_raw\n"
    f"BERNOULLI {SAMPLE_PCT_VIZ}% sample (N={n_viz:,})",
    fontsize=11, y=1.02
)
fig.tight_layout()
qq_path = plots_dir / "01_03_01_qq_plot.png"
fig.savefig(qq_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {qq_path}")

# %% [markdown]
# ## 7. ECDF Plots (Artifact 4)

# %%
ecdf_columns = ["rating", "ratingDiff", "duration_min"]
ecdf_i3_labels = {
    "rating": "AMBIGUOUS",
    "ratingDiff": "POST_GAME",
    "duration_min": "POST_GAME",
}

fig, axes = plt.subplots(1, len(ecdf_columns), figsize=(5 * len(ecdf_columns), 4))

for ax, col in zip(axes, ecdf_columns):
    data = df_viz[col].dropna().values
    if len(data) < 10:
        ax.text(0.5, 0.5, f"Insufficient data\n(n={len(data)})",
                transform=ax.transAxes, ha="center", va="center")
        ax.set_title(f"ECDF: {col}\n[{ecdf_i3_labels[col]}]", fontsize=9)
        continue
    sorted_data = np.sort(data)
    ecdf_y = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax.step(sorted_data, ecdf_y, where="post", linewidth=1, color="steelblue")
    ax.set_xlabel(col)
    ax.set_ylabel("ECDF")
    ax.set_title(f"ECDF: {col}\n[{ecdf_i3_labels[col]}]", fontsize=9)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)

    # Annotate percentiles from census
    # census uses median_val for p50 (not p50 key)
    if col in numeric_stats_lookup:
        ns = numeric_stats_lookup[col]
        pctls = [
            (ns["p05"], "p05"),
            (ns["median_val"], "p50"),
            (ns["p95"], "p95"),
        ]
        for pctl, label in pctls:
            if pctl is not None:
                ax.axvline(pctl, color="red", linestyle=":", linewidth=0.5, alpha=0.5)
                ax.text(pctl, 0.02, label, fontsize=6, color="red", rotation=90)

fig.suptitle(
    f"ECDFs -- aoe2companion matches_raw\n"
    f"BERNOULLI {SAMPLE_PCT_VIZ}% sample (N={n_viz:,})",
    fontsize=11, y=1.02
)
fig.tight_layout()
ecdf_path = plots_dir / "01_03_01_ecdf_key_columns.png"
fig.savefig(ecdf_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {ecdf_path}")

# %% [markdown]
# ## 8. JSON Profile Assembly (Artifact 1)

# %%
profile_json = {
    "step": "01_03_01",
    "dataset": "aoe2companion",
    "table": "matches_raw",
    "total_rows": total_rows,
    "total_columns": len(column_profiles),
    "column_profiles": column_profiles,
    "dataset_profile": dataset_profile,
    "critical_findings": critical_findings,
    "temporal_coverage": temporal_coverage,
    "cross_table_notes": {
        "profiles_raw_dead_columns": [
            "sharedHistory", "twitchChannel", "youtubeChannel",
            "youtubeChannelName", "discordId", "discordName",
            "discordInvitation",
        ],
        "source": "01_02_04 univariate census",
        "note": (
            "profiles_raw contains 7 columns that are 100% NULL. "
            "Not re-profiled in 01_03_01 (matches_raw scope only)."
        ),
    },
    "rating_stratified": rating_stratified,
    "sample_info": {
        "bernoulli_pct_viz": SAMPLE_PCT_VIZ,
        "skewness_kurtosis_method": "DuckDB native SKEWNESS()/KURTOSIS() -- exact, full table",
        "skewness_kurtosis_columns": len(skewness_kurtosis),
        "kurtosis_convention": "excess kurtosis (kurtosis - 3); DuckDB KURTOSIS() default",
        "qq_ecdf_sample_rows": n_viz,
    },
    "sql_queries": sql_queries,
}

json_path = profiling_dir / "01_03_01_systematic_profile.json"
with open(json_path, "w") as f:
    json.dump(profile_json, f, indent=2, default=str)
print(f"Saved: {json_path} ({json_path.stat().st_size:,} bytes)")

# %% [markdown]
# ## 9. Markdown Report (Artifact 5)

# %%
md_lines = [
    "# Step 01_03_01 -- Systematic Data Profiling: aoe2companion",
    "",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_03 -- Systematic Data Profiling",
    "**Dataset:** aoe2companion",
    "**Predecessor:** 01_02_07 (Multivariate EDA)",
    "**Invariants applied:** #3, #6, #7, #9",
    f"**Table:** matches_raw ({total_rows:,} rows, {len(column_profiles)} columns)",
    "",
    "## I3 Temporal Classification Table",
    "",
    "| Column | I3 Classification | Null % | Cardinality | Uniqueness Ratio | Notes |",
    "|--------|-------------------|--------|-------------|------------------|-------|",
]

for p in column_profiles:
    col = p["column"]
    cls = p["i3_classification"]
    null_pct = p["null_pct"]
    card = p["cardinality"]
    uniq = p["uniqueness_ratio"]
    notes = ""
    # Flag critical findings
    if any(d["column"] == col for d in dead_fields):
        notes = "DEAD FIELD"
    elif any(c["column"] == col for c in constant_columns):
        notes = "CONSTANT"
    elif any(nc["column"] == col for nc in near_constant_columns):
        reasons = [nc for nc in near_constant_columns if nc["column"] == col]
        if reasons:
            notes = f"NEAR-CONSTANT ({', '.join(reasons[0]['reasons'])})"
    md_lines.append(
        f"| {col} | {cls} | {null_pct} | {card:,} | {uniq:.8f} | {notes} |"
    )

md_lines.extend([
    "",
    "## Dataset-Level Summary",
    "",
    f"- **Total rows:** {total_rows:,}",
    f"- **Total columns:** {len(column_profiles)}",
    f"- **Duplicates (matchId, profileId):** {dup_info['dup_groups']:,} groups"
    f" ({dup_info['total_dup_rows']:,} rows)",
    f"- **Memory footprint:** {memory_footprint['total_gb']:.2f} GB total allocated"
    f" / {memory_footprint['used_gb']:.2f} GB used (whole DB, DuckDB 1.5.1 pragma_database_size)",
    "",
    "### Class Balance (won)",
    "",
    "| won | Count | Pct |",
    "|-----|-------|-----|",
])
for entry in won_dist:
    md_lines.append(f"| {entry['won']} | {entry['cnt']:,} | {entry['pct']}% |")

md_lines.extend([
    "",
    "## Critical Findings",
    "",
    f"- **Dead fields ({len(dead_fields)}):** "
    + (", ".join(d["column"] for d in dead_fields) if dead_fields else "None"),
    f"- **Constant columns ({len(constant_columns)}):** "
    + (", ".join(c["column"] for c in constant_columns) if constant_columns else "None"),
    f"- **Near-constant columns ({len(near_constant_columns)}):** "
    + (", ".join(nc["column"] for nc in near_constant_columns) if near_constant_columns else "None"),
    "",
    f"### Near-constant threshold: uniqueness_ratio < {NEAR_CONSTANT_UNIQUENESS_RATIO} OR IQR == 0 (Manual 3.3, I7)",
    "",
])

# Near-constant detail table
if near_constant_columns:
    md_lines.extend([
        "| Column | Cardinality | Uniqueness Ratio | IQR | Reasons | I3 |",
        "|--------|-------------|------------------|-----|---------|-----|",
    ])
    for nc in near_constant_columns:
        md_lines.append(
            f"| {nc['column']} | {nc['cardinality']} | {nc['uniqueness_ratio']:.8f} "
            f"| {nc['iqr']} | {', '.join(nc['reasons'])} | {nc['i3_classification']} |"
        )
    md_lines.append("")

# Near-constant stratification subsection
md_lines.extend([
    "### Near-constant Stratification",
    "",
    f"Of {len(near_constant_columns)} near-constant columns, "
    f"**{len(genuinely_uninformative)}** are genuinely uninformative and "
    f"**{len(low_cardinality_categorical)}** are low-cardinality categoricals "
    f"with meaningful variation.",
    "",
    f"**Genuinely uninformative ({len(genuinely_uninformative)}):** "
    + (", ".join(genuinely_uninformative) if genuinely_uninformative else "None"),
    "",
    f"**Low-cardinality categorical ({len(low_cardinality_categorical)}):** "
    + (", ".join(low_cardinality_categorical) if low_cardinality_categorical else "None"),
    "",
    f"**Threshold justification (I7):** 95% dominant-value threshold follows "
    f"scikit-learn VarianceThreshold and caret nearZeroVar conventions "
    f"(default frequency ratio 95/5). At {total_rows:,} rows, the dominant "
    f"value must account for >{int(total_rows * 0.95):,} rows to trigger.",
    "",
    f"**Cross-notebook asymmetry note (I8):** The aoestats notebook applies "
    f"NEAR_CONSTANT_CARDINALITY_CAP=5 in near-constant detection, resulting "
    f"in 3 flagged columns vs {len(near_constant_columns)} here. The "
    f"difference is due to the much larger row count (277M vs 30M) making "
    f"the uniqueness_ratio threshold more aggressive. The stratification "
    f"resolves this by separating genuinely uninformative columns from "
    f"low-cardinality categoricals.",
    "",
])

# Temporal coverage section
md_lines.extend([
    "## Temporal Coverage",
    "",
    f"- **Earliest match:** {temporal_coverage['min_started']}",
    f"- **Latest match:** {temporal_coverage['max_started']}",
    f"- **Distinct months:** {temporal_coverage['distinct_months']}",
    f"- **Missing months:** {temporal_coverage['missing_months_count']}",
])
if temporal_coverage["missing_months"]:
    for gap in temporal_coverage["missing_months"]:
        md_lines.append(f"  - {gap}")
md_lines.append("")

# Cross-table notes section
md_lines.extend([
    "## Cross-Table Notes",
    "",
    "**profiles_raw dead columns (01_02_04 census):** "
    "sharedHistory, twitchChannel, youtubeChannel, youtubeChannelName, "
    "discordId, discordName, discordInvitation (all 100% NULL). "
    "Not re-profiled in 01_03_01 (matches_raw scope only).",
    "",
])

md_lines.extend([
    "## Rating Stratification",
    "",
    "| Scope | N Rows | Rating NULL % | Rating Mean | Rating Std | Rating Median | RatingDiff Mean |",
    "|-------|--------|---------------|-------------|------------|---------------|-----------------|",
])
for row in rating_stratified:
    md_lines.append(
        f"| {row['scope']} | {row['n_rows']:,} | {row['rating_null_pct']}% "
        f"| {row['rating_mean']} | {row['rating_std']} | {row['rating_median']} "
        f"| {row['ratingdiff_mean']} |"
    )

md_lines.extend([
    "",
    "## Skewness/Kurtosis (Exact, Full Table)",
    "",
    "Computed via DuckDB native `SKEWNESS()` and `KURTOSIS()` aggregate functions",
    "over all non-NULL rows per column (no sampling, no listwise deletion).",
    "Kurtosis values are **excess kurtosis** (kurtosis - 3); normal = 0.",
    "",
    "| Column | Skewness | Kurtosis (excess) | I3 |",
    "|--------|----------|-------------------|-----|",
])
for col in skew_kurt_cols:
    sk_data = skewness_kurtosis[col]
    i3 = I3_CLASSIFICATION.get(col, I3_DURATION_MIN if col == "duration_min" else "UNKNOWN")
    md_lines.append(
        f"| {col} | {sk_data['skewness']} | {sk_data['kurtosis']} | {i3} |"
    )

md_lines.extend([
    "",
    "## Artifact Index",
    "",
    "| # | Artifact | Filename | Description |",
    "|---|----------|----------|-------------|",
    "| 1 | Systematic Profile JSON | `01_03_01_systematic_profile.json` | Machine-readable profile with all metrics |",
    "| 2 | Completeness Heatmap | `plots/01_03_01_completeness_heatmap.png` | NULL rate per column, color-coded |",
    "| 3 | QQ Plots | `plots/01_03_01_qq_plot.png` | Normal reference QQ for 5 numeric columns |",
    "| 4 | ECDF Plots | `plots/01_03_01_ecdf_key_columns.png` | Empirical CDFs for rating, ratingDiff, duration_min |",
    "| 5 | This Report | `01_03_01_systematic_profile.md` | Human-readable summary |",
    "",
    "## SQL Queries (Invariant #6)",
    "",
])

for name, query in sql_queries.items():
    md_lines.extend([f"### {name}", "", "```sql", query.strip(), "```", ""])

md_lines.extend([
    "## Data Sources",
    "",
    f"- `matches_raw` ({total_rows:,} rows) -- DuckDB table from 01_02_02",
    "- Census JSON: `01_02_04_univariate_census.json`",
    "- Bivariate findings: `01_02_06_bivariate_eda.md` (I3 classifications)",
    "- Multivariate findings: `01_02_07_multivariate_analysis.md`",
    f"- Skewness/kurtosis: DuckDB native SKEWNESS()/KURTOSIS() -- exact, full table, "
    f"{len(skewness_kurtosis)} columns",
    f"- BERNOULLI sample: {SAMPLE_PCT_VIZ}% ({n_viz:,} rows for QQ/ECDF visualization)",
    "",
])

md_text = "\n".join(md_lines)
md_path = profiling_dir / "01_03_01_systematic_profile.md"
with open(md_path, "w") as f:
    f.write(md_text)
print(f"Saved: {md_path} ({md_path.stat().st_size:,} bytes)")

# %% [markdown]
# ## 10. Gate Verification

# %%
expected_artifacts = [
    profiling_dir / "01_03_01_systematic_profile.json",
    plots_dir / "01_03_01_completeness_heatmap.png",
    plots_dir / "01_03_01_qq_plot.png",
    plots_dir / "01_03_01_ecdf_key_columns.png",
    profiling_dir / "01_03_01_systematic_profile.md",
]

for artifact in expected_artifacts:
    assert artifact.exists(), f"Missing artifact: {artifact}"
    assert artifact.stat().st_size > 0, f"Empty artifact: {artifact}"
    print(f"  OK: {artifact.name} ({artifact.stat().st_size:,} bytes)")

# Verify JSON schema
with open(expected_artifacts[0]) as f:
    profile_check = json.load(f)
assert "critical_findings" in profile_check, "JSON missing critical_findings key"
assert "column_profiles" in profile_check, "JSON missing column_profiles key"
assert len(profile_check["column_profiles"]) == len(column_profiles), (
    f"JSON column_profiles count mismatch: {len(profile_check['column_profiles'])} "
    f"vs expected {len(column_profiles)}"
)
print(f"  OK: JSON has critical_findings and {len(profile_check['column_profiles'])} column_profiles")

# Verify JSON sample_info documents skewness/kurtosis method
assert "skewness_kurtosis_method" in profile_check["sample_info"], (
    "JSON sample_info missing skewness_kurtosis_method"
)
assert "exact" in profile_check["sample_info"]["skewness_kurtosis_method"].lower(), (
    "JSON sample_info should document exact skewness/kurtosis computation"
)
print("  OK: JSON documents exact skewness/kurtosis method")

# Verify MD contains I3 classification table
md_check = expected_artifacts[4].read_text()
assert "I3 Temporal Classification Table" in md_check, "MD missing I3 classification table"
assert "Critical Findings" in md_check, "MD missing Critical Findings section"
assert "Skewness/Kurtosis (Exact, Full Table)" in md_check, (
    "MD missing Skewness/Kurtosis section"
)
for qname in sql_queries:
    assert qname in md_check, f"SQL query '{qname}' missing from markdown"
print("  OK: MD contains I3 table, Critical Findings, Skewness/Kurtosis, and all SQL queries")

# Verify every column has i3_classification
for cp in profile_check["column_profiles"]:
    assert "i3_classification" in cp, f"Column {cp['column']} missing i3_classification"
print(f"  OK: All {len(profile_check['column_profiles'])} columns have i3_classification")

# Verify all 9 census numeric columns have skewness/kurtosis in profile
numeric_cols_in_profile = [
    cp["column"] for cp in profile_check["column_profiles"]
    if "skewness" in cp
]
expected_numeric = [
    "rating", "ratingDiff", "population", "slot", "color", "team",
    "speedFactor", "treatyLength", "internalLeaderboardId",
]
for nc in expected_numeric:
    assert nc in numeric_cols_in_profile, (
        f"Numeric column {nc} missing skewness/kurtosis in profile"
    )
print(f"  OK: All {len(expected_numeric)} census numeric columns have skewness/kurtosis")

# Verify temporal_coverage in JSON (R10)
assert "temporal_coverage" in profile_check, "JSON missing temporal_coverage key"
tc_check = profile_check["temporal_coverage"]
assert tc_check["min_started"], "temporal_coverage.min_started is empty"
assert tc_check["max_started"], "temporal_coverage.max_started is empty"
assert tc_check["distinct_months"] > 0, "temporal_coverage.distinct_months must be > 0"
print(f"  OK: temporal_coverage present ({tc_check['min_started']} to {tc_check['max_started']})")

# Verify near_constant_stratification in JSON (R11)
assert "near_constant_stratification" in profile_check["critical_findings"], (
    "JSON missing near_constant_stratification in critical_findings"
)
ncs_check = profile_check["critical_findings"]["near_constant_stratification"]
assert (
    ncs_check["genuinely_uninformative_count"] + ncs_check["low_cardinality_categorical_count"]
    == len(near_constant_columns)
), "near_constant_stratification counts do not sum to total near-constant columns"
assert "won" in ncs_check["low_cardinality_categorical"], (
    "TARGET column 'won' must be in low_cardinality_categorical"
)
assert "threshold_justification" in ncs_check["stratification_criteria"], (
    "JSON missing threshold_justification (I7)"
)
assert "cross_notebook_asymmetry_note" in ncs_check, (
    "JSON missing cross_notebook_asymmetry_note (I8)"
)
print(f"  OK: near_constant_stratification present "
      f"({ncs_check['genuinely_uninformative_count']} uninformative + "
      f"{ncs_check['low_cardinality_categorical_count']} categorical = "
      f"{len(near_constant_columns)} total)")

# Verify cross_table_notes in JSON (R12)
assert "cross_table_notes" in profile_check, "JSON missing cross_table_notes key"
ctn_check = profile_check["cross_table_notes"]
assert len(ctn_check["profiles_raw_dead_columns"]) == 7, (
    f"Expected 7 dead columns in cross_table_notes, got "
    f"{len(ctn_check['profiles_raw_dead_columns'])}"
)
print(f"  OK: cross_table_notes present ({len(ctn_check['profiles_raw_dead_columns'])} dead columns)")

# Verify MD contains new sections
assert "Temporal Coverage" in md_check, "MD missing Temporal Coverage section"
assert "Near-constant Stratification" in md_check, "MD missing Near-constant Stratification section"
assert "Cross-Table Notes" in md_check, "MD missing Cross-Table Notes section"
print("  OK: MD contains Temporal Coverage, Near-constant Stratification, Cross-Table Notes")

print("\nAll gate checks passed.")

# %%
db.close()
print("DuckDB connection closed.")
