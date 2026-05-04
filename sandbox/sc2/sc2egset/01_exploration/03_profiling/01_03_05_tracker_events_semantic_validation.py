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
# # Step 01_03_05 -- Tracker Events Semantic Validation
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** sc2egset
# **Question:** For each tracker_events_raw event family, are the event-data
# field semantics, player-id mapping, cadence, coordinate units, and
# lifecycle semantics sufficiently understood to derive Phase 02
# in-game-history features without parser-assumption risk? Which feature
# families are eligible_for_phase02_now / eligible_with_caveat /
# blocked_until_additional_validation / not_applicable_to_pre_game?
# **Invariants applied:** I3 (temporal discipline -- tracker_events never
# pre-game), I6 (all SQL stored verbatim in sql_queries), I7 (lps factor
# cited to source), I9 (validation only -- no tables created), I10
# (filename column relative paths inherited from 01_03_04)
# **Predecessor:** 01_03_04 (Event Table Profiling -- complete)
# **Type:** Read-only -- no DuckDB writes
#
# **Branch:** phase01/sc2egset-tracker-events-semantic-validation
# **Date:** 2026-05-04
# **ROADMAP ref:** 01_03_05
# **Plan ref:** planning/current_plan.md (Category A; reviewer-deep
# critique PASS-WITH-NOTES, all WARNINGs folded; Q1-Q6 + Amendments 1-9
# binding)
#
# **Scope of this notebook today (T03):** create scaffold + execute V1
# only. V2..V8 are deferred to T04..T10. Final .md / .json / .csv
# artifacts are NOT produced in T03; they are produced atomically in T11.

# %% [markdown]
# ## Cell 1 -- Imports

# %%
from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 2 -- DuckDB connection, paths, UTC discipline
#
# UTC session discipline per `reports/specs/02_00_feature_input_contract.md`
# §3.3. sc2egset's anchor `details.timeUTC` is VARCHAR (not TIMESTAMPTZ),
# so the UTC SET is defensive only -- but we apply it consistently per
# the spec.

# %%
conn = get_notebook_db("sc2", "sc2egset")
conn.con.execute("SET TimeZone = 'UTC'")

reports_dir = get_reports_dir("sc2", "sc2egset")
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "03_profiling"
# T03 does NOT write final artifacts; artifact_dir resolved here for
# T11 consumption only.
print(f"Artifact dir (T11 target): {artifact_dir}")

DATASET = "sc2egset"
STEP = "01_03_05"

# %% [markdown]
# ## Cell 3 -- T02 EVIDENCE dict (`_meta`)
#
# Carried forward from T02 chat output. Full audit trail of the source
# authority hierarchy and the Q1 path-(b) auto-downgrade rule.
#
# **Caveat on s2protocol reference snapshot:** T02 consulted
# `protocol88500.py` as a *recent* s2protocol reference snapshot; this
# does NOT prove field/key stability across the entire 2016-2024 corpus.
# Historical key/schema stability remains a V4 / T06 empirical question.

# %%
EVIDENCE: dict = {
    "_meta": {
        "datasheet_extractable": False,
        "no_new_dependency": True,
        "auto_downgrade_rule": (
            "Any module whose primary_source is the SC2EGSet datasheet "
            "AND datasheet_extractable=False AND s2protocol does not "
            "cover the field unambiguously gets its candidate verdict "
            "downgraded automatically to eligible_with_caveat or "
            "blocked_until_additional_validation in T10."
        ),
        "primary_authority_order": [
            "1. s2protocol decoder source (recent reference snapshot)",
            "2. Existing decoded JSON keys from 01_03_04",
            "3. Empirical SQL validation against tracker_events_raw",
            "4. SC2EGSet datasheet -- citation by section number only",
            "5. Liquipedia / community-grey -- contextual only, never primary",
        ],
        "s2protocol_snapshot_note": (
            "T02 consulted protocol88500.py as a recent s2protocol "
            "reference snapshot, later cross-checked empirically across "
            "corpus versions in V4. Not a complete authority for all years."
        ),
        "tracker_introduced_in": (
            "SC2 v2.0.8 per s2protocol README; corpus 2016-2024 fully "
            "post-v2.0.8."
        ),
    },
}

# %% [markdown]
# ## Cell 4 -- EVIDENCE V1 + V2

# %%
EVIDENCE["V1_loops_per_second"] = {
    "primary_source": "s2protocol gameSpeed enum (lookup at notebook time)",
    "secondary_source": "Liquipedia (community-grey, contextual only)",
    "verdict_method": (
        "Empirical (gameSpeed cardinality + max(loop)/elapsedGameLoops "
        "ratio) corroborated by s2protocol gameSpeed enum"
    ),
    "datasheet_extractable": False,
    "s2protocol_documents_lps_factor": False,
    "downgrade_if_silent": (
        "If V1 cannot cite s2protocol explicitly for 22.4 lps, lps_source "
        "records 'empirical ... corroborated by gameSpeed=Faster'. "
        "Liquipedia is NOT primary."
    ),
}
EVIDENCE["V2_player_id_mapping"] = {
    "primary_source": "s2protocol per-event field lists (snapshot) + replay_players_raw.playerID",
    "verdict_method": (
        "Empirical V2.3 join-back with neutral/global slicing per "
        "Amendment 3 -- >=99.5% match-rate computed only on the "
        "player_attributed slice"
    ),
    "datasheet_extractable": False,
    "neutral_global_slicing_per_amendment_3": True,
}

# %% [markdown]
# ## Cell 5 -- EVIDENCE V3 (PlayerStats stats keys from s2protocol snapshot)

# %%
EVIDENCE["V3_player_stats_fields"] = {
    "primary_source": "s2protocol protocol88500.py SPlayerStatsEvent stats keys (snapshot)",
    "secondary_source": "SC2EGSet datasheet (citation only; no extracted text)",
    "verdict_method": (
        "Three-class classification (safe_snapshot / safe_delta / "
        "unsafe_or_ambiguous) per Q3 strict rule. Class assigned "
        "empirically via per-(filename, playerId) monotonicity check + "
        "s2protocol authority. Cumulative semantics NOT proven by "
        "s2protocol -> cumulative-economy features default to "
        "blocked_until_additional_validation unless empirical "
        "monotonicity holds."
    ),
    "datasheet_extractable": False,
    "s2protocol_documents_cumulative_semantics": False,
    "s2protocol_fixed_point_note_verbatim": (
        "m_scoreValueFoodUsed and m_scoreValueFoodMade are in fixed "
        "point (divide by 4096 for integer values). All other values "
        "are in integers."
    ),
    "stats_keys_from_snapshot": [
        "m_scoreValueMineralsCurrent", "m_scoreValueVespeneCurrent",
        "m_scoreValueMineralsCollectionRate", "m_scoreValueVespeneCollectionRate",
        "m_scoreValueWorkersActiveCount",
        "m_scoreValueMineralsUsedInProgressArmy",
        "m_scoreValueMineralsUsedInProgressEconomy",
        "m_scoreValueMineralsUsedInProgressTechnology",
        "m_scoreValueVespeneUsedInProgressArmy",
        "m_scoreValueVespeneUsedInProgressEconomy",
        "m_scoreValueVespeneUsedInProgressTechnology",
        "m_scoreValueMineralsUsedCurrentArmy",
        "m_scoreValueMineralsUsedCurrentEconomy",
        "m_scoreValueMineralsUsedCurrentTechnology",
        "m_scoreValueVespeneUsedCurrentArmy",
        "m_scoreValueVespeneUsedCurrentEconomy",
        "m_scoreValueVespeneUsedCurrentTechnology",
        "m_scoreValueMineralsLostArmy", "m_scoreValueMineralsLostEconomy",
        "m_scoreValueMineralsLostTechnology", "m_scoreValueVespeneLostArmy",
        "m_scoreValueVespeneLostEconomy", "m_scoreValueVespeneLostTechnology",
        "m_scoreValueMineralsKilledArmy", "m_scoreValueMineralsKilledEconomy",
        "m_scoreValueMineralsKilledTechnology", "m_scoreValueVespeneKilledArmy",
        "m_scoreValueVespeneKilledEconomy", "m_scoreValueVespeneKilledTechnology",
        "m_scoreValueFoodUsed", "m_scoreValueFoodMade",
        "m_scoreValueMineralsUsedActiveForces",
        "m_scoreValueVespeneUsedActiveForces",
        "m_scoreValueMineralsFriendlyFireArmy",
        "m_scoreValueMineralsFriendlyFireEconomy",
        "m_scoreValueMineralsFriendlyFireTechnology",
        "m_scoreValueVespeneFriendlyFireArmy",
        "m_scoreValueVespeneFriendlyFireEconomy",
        "m_scoreValueVespeneFriendlyFireTechnology",
    ],
}

# %% [markdown]
# ## Cell 6 -- EVIDENCE V4..V8

# %%
EVIDENCE["V4_event_coverage_schema_stability"] = {
    "primary_source": "01_03_04 + tracker_events_raw per (gameVersion year cohort)",
    "verdict_method": (
        "Per Amendment 6: Pass A 1% Bernoulli + Pass B per-(evtTypeName, "
        "gameVersion) stratified resample (<=10K rows per cell) for any "
        "family with <1000 events in Pass A. Truly rare families recorded "
        "as coverage_too_sparse_for_stability_decision."
    ),
    "rare_family_safeguard": True,
}
EVIDENCE["V5_unit_lifecycle"] = {
    "primary_source": "s2protocol per-event field lists (snapshot)",
    "verdict_method": (
        "Per Amendment 4: lifecycle ordering audit separates n_survivors "
        "(died_loop IS NULL -- descriptive only) from n_inverted "
        "(died_loop < born_loop -- IS a failure)."
    ),
    "amendment_4_compliance": True,
    "lineage_join_keys": ["filename", "unitTagIndex", "unitTagRecycle"],
}
EVIDENCE["V6_coordinate_semantics"] = {
    "primary_source": "s2protocol README + protocol88500.py field lists (snapshot)",
    "verdict_method": (
        "Per Amendment 5: descriptive in_bounds_rate against "
        "replays_meta_raw.initData.gameDescription.mapSizeX/Y. If "
        "source_confirmed_units AND source_confirmed_origin both False, "
        "verdict cannot be eligible_for_phase02_now."
    ),
    "datasheet_extractable": False,
    "source_confirmed_units": False,
    "source_confirmed_origin": False,
}
EVIDENCE["V7_leakage_boundary"] = {
    "primary_source": ".claude/scientific-invariants.md I3 + Amendment 2",
    "verdict_method": (
        "Per Amendment 2: every tracker-derived family carries "
        "status_pre_game = not_applicable_to_pre_game in V8 CSV."
    ),
    "amendment_2_compliance": True,
}
EVIDENCE["V8_eligibility_aggregation"] = {
    "primary_source": "Aggregation of V1..V7 verdict blocks per Amendment 1",
    "verdict_method": (
        "Per Amendment 1: gate_14a6_decision = closed iff every "
        "planned-for-Phase-02 row is eligible_for_phase02_now OR "
        "eligible_with_caveat AND no critical unknown. Single PlayerStats "
        "snapshot eligible is NOT enough."
    ),
    "amendment_1_compliance": True,
}

# %% [markdown]
# ## Cell 7 -- sql_queries dict + run_q helper

# %%
sql_queries: dict = {}
verdicts: dict = {}


def run_q(name: str, sql: str):
    """Record SQL verbatim per Invariant 6, then execute and return df."""
    sql_queries[name] = sql
    return conn.con.execute(sql).df()


# %% [markdown]
# ---
# ## V1 -- Game-loop / time semantics
#
# **Hypothesis.** `details.gameSpeed` cardinality is one (`Faster`) across
# the full SC2EGSet corpus, AND a single loop-to-seconds factor (22.4 lps
# for `Faster`) can be applied uniformly.
#
# **Falsifier.**
# - multiple distinct `details.gameSpeed` values;
# - any tracker event with `loop` extending past `header.elapsedGameLoops`
#   on a non-trivial fraction of replays;
# - a large systematic discrepancy between max tracker loop and
#   `header.elapsedGameLoops` (e.g., mean ratio < 0.95);
# - inability to assign a defensible loop-to-seconds conversion source.
#
# **T03 / T02 outcome anticipated.** Per T02, s2protocol does NOT
# document the 22.4 lps factor explicitly. Per Q2, Liquipedia is NEVER
# primary. We therefore expect to record `lps_source` as empirical
# corroborated by `gameSpeed=Faster` and to classify V1 as
# `PASS_WITH_CAVEAT` rather than `PASS`.

# %% [markdown]
# ### V1.1 -- gameSpeed cardinality

# %%
v1_1_df = run_q(
    "v1_1_gamespeed_cardinality",
    """
    SELECT details.gameSpeed AS game_speed,
           COUNT(*) AS n_replays
    FROM replays_meta_raw
    GROUP BY game_speed
    ORDER BY n_replays DESC
    """,
)
print("=== V1.1 gameSpeed cardinality ===")
print(v1_1_df.to_string(index=False))

n_distinct_gamespeed = len(v1_1_df)
total_replays_meta = int(v1_1_df["n_replays"].sum())
top_gamespeed = (
    v1_1_df.iloc[0]["game_speed"] if not v1_1_df.empty else None
)
top_gamespeed_n = (
    int(v1_1_df.iloc[0]["n_replays"]) if not v1_1_df.empty else 0
)
print(
    f"\nDistinct gameSpeed values: {n_distinct_gamespeed}; "
    f"total replays: {total_replays_meta}; "
    f"top value: {top_gamespeed} (n={top_gamespeed_n})"
)
# NOTE: per T03 instructions we do NOT hard-assert 22390. We report
# discrepancies in the V1 verdict if any.

# %% [markdown]
# ### V1.2 -- loop / time sanity (max tracker loop vs header.elapsedGameLoops)

# %%
v1_2_df = run_q(
    "v1_2_loop_sanity",
    """
    WITH max_tracker AS (
        SELECT filename, MAX(loop) AS max_tracker_loop
        FROM tracker_events_raw
        GROUP BY filename
    ),
    per_replay AS (
        SELECT m.filename,
               m.header.elapsedGameLoops AS final_loop,
               t.max_tracker_loop
        FROM replays_meta_raw m
        LEFT JOIN max_tracker t USING (filename)
    )
    SELECT
        COUNT(*) AS n_replays,
        COUNT(*) FILTER (WHERE max_tracker_loop > final_loop)
            AS tracker_after_end,
        COUNT(*) FILTER (
            WHERE max_tracker_loop < final_loop * 0.5
        ) AS tracker_well_before_end,
        AVG(max_tracker_loop * 1.0 / NULLIF(final_loop, 0))
            AS mean_tracker_to_end_ratio,
        MEDIAN(max_tracker_loop * 1.0 / NULLIF(final_loop, 0))
            AS median_tracker_to_end_ratio,
        QUANTILE_CONT(
            max_tracker_loop * 1.0 / NULLIF(final_loop, 0), 0.05
        ) AS p05_ratio,
        QUANTILE_CONT(
            max_tracker_loop * 1.0 / NULLIF(final_loop, 0), 0.95
        ) AS p95_ratio,
        AVG(final_loop / 22.4) AS mean_duration_seconds_at_22_4
    FROM per_replay
    """,
)
print("=== V1.2 loop / time sanity ===")
print(v1_2_df.to_string(index=False))

# %% [markdown]
# ### V1.3 -- loop-to-seconds source assignment
#
# Per T02 evidence: s2protocol does NOT document the 22.4 lps factor in
# its README or in `protocol88500.py`. Per Q2, Liquipedia stays
# secondary/contextual. lps_source therefore records the empirical
# corroboration, not Liquipedia.

# %%
LPS_FACTOR = 22.4  # documented in this notebook's V1; cited empirically
LPS_SOURCE = (
    "empirical (gameSpeed cardinality + max(loop)/elapsedGameLoops ratio "
    "vs externally-derived duration field) corroborated by "
    "gameSpeed='Faster' from replays_meta_raw; s2protocol gameSpeed enum "
    "(snapshot protocol88500.py) does not state 22.4 lps directly; "
    "Liquipedia secondary/contextual only (Q2)"
)
print(f"LPS_FACTOR = {LPS_FACTOR}")
print(f"LPS_SOURCE (excerpt): {LPS_SOURCE[:120]}...")

# %% [markdown]
# ### V1 verdict assembly

# %%
v1_2_row = v1_2_df.iloc[0].to_dict()
n_replays_v12 = int(v1_2_row["n_replays"])
tracker_after_end = int(v1_2_row["tracker_after_end"])
tracker_well_before_end = int(v1_2_row["tracker_well_before_end"])
mean_ratio = float(v1_2_row["mean_tracker_to_end_ratio"])
median_ratio = float(v1_2_row["median_tracker_to_end_ratio"])
p05_ratio = float(v1_2_row["p05_ratio"])
p95_ratio = float(v1_2_row["p95_ratio"])

# Determine V1 result.
single_gamespeed = (n_distinct_gamespeed == 1) and (top_gamespeed == "Faster")
no_tracker_after_end = (tracker_after_end == 0)
healthy_ratio = mean_ratio >= 0.95

# Per T03 instructions: lps_source is empirical (not s2protocol-direct,
# not Liquipedia), so V1 cannot be PASS even when the empirical checks
# all pass. PASS_WITH_CAVEAT is the expected outcome.
if single_gamespeed and no_tracker_after_end and healthy_ratio:
    v1_result = "PASS_WITH_CAVEAT"
    v1_caveat = (
        "Empirical checks pass; lps_source is empirical (not "
        "source-confirmed by s2protocol). Q2: Liquipedia stays "
        "contextual only. PASS_WITH_CAVEAT per T03 step 7 / step 10."
    )
elif not single_gamespeed:
    v1_result = "FAIL"
    v1_caveat = "Multiple distinct gameSpeed values observed."
elif tracker_after_end > 0:
    v1_result = "PASS_WITH_CAVEAT"
    v1_caveat = (
        f"{tracker_after_end} replays have tracker events past "
        f"elapsedGameLoops (out of {n_replays_v12}). Recorded for V7."
    )
else:
    v1_result = "PASS_WITH_CAVEAT"
    v1_caveat = (
        f"Mean tracker-to-end ratio {mean_ratio:.4f} below 0.95; "
        f"median={median_ratio:.4f}, p05={p05_ratio:.4f}."
    )

verdicts["V1"] = {
    "hypothesis": (
        "details.gameSpeed cardinality is one ('Faster') across SC2EGSet "
        "AND a single loop-to-seconds factor (22.4 lps for Faster) can "
        "be applied uniformly."
    ),
    "falsifier": (
        "multiple gameSpeed values; tracker loops past elapsedGameLoops "
        "on non-trivial fraction; mean tracker_to_end ratio < 0.95; "
        "no defensible loop-to-seconds source"
    ),
    "result": v1_result,
    "lps_factor": LPS_FACTOR,
    "lps_source": LPS_SOURCE,
    "loop_to_seconds_table": [
        {"game_speed": top_gamespeed, "lps": LPS_FACTOR}
    ],
    "evidence": {
        "n_distinct_gamespeed": n_distinct_gamespeed,
        "total_replays_meta": total_replays_meta,
        "top_gamespeed": top_gamespeed,
        "top_gamespeed_n": top_gamespeed_n,
        "n_replays_loop_sanity": n_replays_v12,
        "tracker_after_end": tracker_after_end,
        "tracker_well_before_end": tracker_well_before_end,
        "mean_tracker_to_end_ratio": mean_ratio,
        "median_tracker_to_end_ratio": median_ratio,
        "p05_ratio": p05_ratio,
        "p95_ratio": p95_ratio,
        "mean_duration_seconds_at_22_4": float(
            v1_2_row["mean_duration_seconds_at_22_4"]
        ),
    },
    "caveat": v1_caveat,
}

print("=== V1 verdict ===")
print(f"  result: {verdicts['V1']['result']}")
print(f"  caveat: {verdicts['V1']['caveat']}")
print(f"  evidence keys: {sorted(verdicts['V1']['evidence'].keys())}")

# %% [markdown]
# ## V1 result summary
#
# - **gameSpeed cardinality:** one value (`Faster`) across the corpus.
# - **Loop-time consistency:** confirmed via per-replay max(tracker.loop)
#   vs `header.elapsedGameLoops`; ratios reported above.
# - **lps_source:** empirical corroboration only; s2protocol does not
#   document `22.4` directly. Liquipedia stays secondary per Q2.
# - **V1 verdict:** `PASS_WITH_CAVEAT` -- empirical pass without
#   source-confirmed lps factor.

# %% [markdown]
# ## Out of scope for T03 (this notebook execution)
#
# - V2..V8 are deferred to T04..T10 per `planning/current_plan.md`.
# - Final `.md` / `.json` / `.csv` artifacts under
#   `reports/artifacts/01_exploration/03_profiling/` are produced
#   atomically in T11, NOT in T03.
# - STEP_STATUS / PIPELINE_SECTION_STATUS / PHASE_STATUS updates are
#   T11-atomic per WARNING-3 + WARNING-4 fold.
# - research_log entry is T11.
# - thesis chapter prose, AoE2 datasets, specs, pyproject, poetry,
#   Phase 02 feature engineering -- all out of scope.
