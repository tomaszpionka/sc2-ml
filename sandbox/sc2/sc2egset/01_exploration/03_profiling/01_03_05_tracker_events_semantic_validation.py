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
# ---
# ## V2 -- Player-id mapping by event type
#
# **Hypothesis.**
# - PlayerStats maps through `playerId`.
# - UnitBorn / UnitInit / UnitOwnerChange map through `controlPlayerId`
#   (true owner) and/or `upkeepPlayerId` (supply tracking).
# - UnitDied killer attribution maps through `killerPlayerId`; victim
#   attribution requires lineage via UnitBorn (deferred to V5).
# - Upgrade maps through `playerId`.
# - PlayerSetup maps through `playerId` / `slotId` / `userId`.
# - UnitTypeChange / UnitDone / UnitPositions have NO direct player-id
#   field (per s2protocol snapshot) and require lineage via
#   `(filename, unitTagIndex, unitTagRecycle)` join back to UnitBorn /
#   UnitInit; these are classified `lineage_required`, NOT `FAIL`.
#
# **Falsifier.**
# - No stable mapping field for semantically player-attributed rows.
# - Player-attributed match rate below 99.5% on the player_attributed
#   slice (per Amendment 3 -- neutral/global rows are NOT counted as
#   mapping failures).
# - Ambiguous ties between candidate mapping fields.
# - Direct fields contradict `replay_players_raw.playerID` mapping.
#
# **Per Amendment 3:** the >=99.5% mapping threshold applies ONLY to
# rows whose id field is NOT in the documented neutral/global set
# (`pid IN (16, 0)` by default; refined empirically per event type).

# %% [markdown]
# ### V2.1 -- enumerate observed id-bearing keys per event type

# %%
v2_1_df = run_q(
    "v2_1_observed_keys_per_event_type",
    """
    WITH samples AS (
        SELECT evtTypeName, event_data,
               ROW_NUMBER() OVER (
                   PARTITION BY evtTypeName ORDER BY loop
               ) AS rn
        FROM tracker_events_raw
    ),
    keys_unnested AS (
        SELECT evtTypeName,
               UNNEST(json_keys(event_data)) AS k
        FROM samples
        WHERE rn <= 3
    )
    SELECT evtTypeName,
           list(DISTINCT k ORDER BY k) AS observed_keys
    FROM keys_unnested
    GROUP BY evtTypeName
    ORDER BY evtTypeName
    """,
)
print("=== V2.1 observed top-level JSON keys per event type ===")
for _, row in v2_1_df.iterrows():
    keys = row["observed_keys"]
    print(f"  {row['evtTypeName']}: {sorted(keys)}")

# %% [markdown]
# ### V2.2 -- histogram of candidate id-field values per event type
#
# Top 6 values per event type (covers 0..5 for typical 1v1 + sentinels).

# %%
v2_2_df = run_q(
    "v2_2_id_value_histogram",
    """
    WITH ev AS (
        SELECT evtTypeName, filename,
            CASE
                WHEN evtTypeName = 'PlayerStats'
                    THEN json_extract_string(event_data, '$.playerId')
                WHEN evtTypeName IN ('UnitBorn','UnitInit','UnitOwnerChange')
                    THEN json_extract_string(event_data, '$.controlPlayerId')
                WHEN evtTypeName = 'UnitDied'
                    THEN json_extract_string(event_data, '$.killerPlayerId')
                WHEN evtTypeName = 'Upgrade'
                    THEN json_extract_string(event_data, '$.playerId')
                WHEN evtTypeName = 'PlayerSetup'
                    THEN json_extract_string(event_data, '$.playerId')
            END AS pid_str
        FROM tracker_events_raw
        WHERE evtTypeName IN (
            'PlayerStats','UnitBorn','UnitInit','UnitOwnerChange',
            'UnitDied','Upgrade','PlayerSetup'
        )
    ),
    hist AS (
        SELECT evtTypeName, pid_str, COUNT(*) AS n
        FROM ev GROUP BY evtTypeName, pid_str
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY evtTypeName ORDER BY n DESC
        ) AS rn
        FROM hist
    )
    SELECT evtTypeName, pid_str, n, rn
    FROM ranked WHERE rn <= 6
    ORDER BY evtTypeName, rn
    """,
)
print("=== V2.2 top-6 candidate id values per direct-mapping event ===")
print(v2_2_df.to_string(index=False))

# %% [markdown]
# ### V2.3 -- join-back validation with neutral/global slicing
#
# Per Amendment 3: match rate computed ONLY on the `player_attributed`
# slice. `null_or_missing` and `neutral_or_global` (default `pid IN
# (16, 0)`) are reported separately and do NOT count as failures.

# %%
v2_3_df = run_q(
    "v2_3_join_back_per_slot_class",
    """
    WITH ev AS (
        SELECT evtTypeName, filename,
            CASE
                WHEN evtTypeName = 'PlayerStats'
                    THEN TRY_CAST(json_extract_string(event_data, '$.playerId') AS INT)
                WHEN evtTypeName IN ('UnitBorn','UnitInit','UnitOwnerChange')
                    THEN TRY_CAST(json_extract_string(event_data, '$.controlPlayerId') AS INT)
                WHEN evtTypeName = 'UnitDied'
                    THEN TRY_CAST(json_extract_string(event_data, '$.killerPlayerId') AS INT)
                WHEN evtTypeName = 'Upgrade'
                    THEN TRY_CAST(json_extract_string(event_data, '$.playerId') AS INT)
                WHEN evtTypeName = 'PlayerSetup'
                    THEN TRY_CAST(json_extract_string(event_data, '$.playerId') AS INT)
            END AS pid
        FROM tracker_events_raw
        WHERE evtTypeName IN (
            'PlayerStats','UnitBorn','UnitInit','UnitOwnerChange',
            'UnitDied','Upgrade','PlayerSetup'
        )
    ),
    classified AS (
        SELECT evtTypeName, filename, pid,
            CASE
                WHEN pid IS NULL THEN 'null_or_missing'
                WHEN pid IN (16, 0) THEN 'neutral_or_global'
                ELSE 'player_attributed'
            END AS slot_class
        FROM ev
    )
    SELECT c.evtTypeName, c.slot_class,
           COUNT(*) AS n_events,
           COUNT(*) FILTER (WHERE rp.toon_id IS NOT NULL) AS n_matched,
           ROUND(
               1.0 * COUNT(*) FILTER (WHERE rp.toon_id IS NOT NULL)
                   / NULLIF(COUNT(*), 0), 6
           ) AS match_rate
    FROM classified c
    LEFT JOIN replay_players_raw rp
        ON rp.filename = c.filename AND rp.playerID = c.pid
    GROUP BY c.evtTypeName, c.slot_class
    ORDER BY c.evtTypeName, c.slot_class
    """,
)
print("=== V2.3 per-(event_type, slot_class) match rate ===")
print(v2_3_df.to_string(index=False))

# %% [markdown]
# ### V2.4 -- control / upkeep agreement check
#
# For UnitBorn / UnitInit / UnitOwnerChange, both `controlPlayerId`
# (true owner) and `upkeepPlayerId` (supply tracking) carry the
# slot id. They typically agree but can diverge in mind-control
# scenarios. controlPlayerId remains the canonical mapping per
# s2protocol snapshot semantics; this cell quantifies the agreement.

# %%
v2_4_df = run_q(
    "v2_4_control_upkeep_agreement",
    """
    WITH ev AS (
        SELECT evtTypeName,
            TRY_CAST(json_extract_string(event_data, '$.controlPlayerId') AS INT)
                AS control_pid,
            TRY_CAST(json_extract_string(event_data, '$.upkeepPlayerId') AS INT)
                AS upkeep_pid
        FROM tracker_events_raw
        WHERE evtTypeName IN ('UnitBorn','UnitInit','UnitOwnerChange')
    )
    SELECT evtTypeName,
           COUNT(*) AS n,
           COUNT(*) FILTER (WHERE control_pid = upkeep_pid)
               AS n_agree,
           COUNT(*) FILTER (WHERE control_pid != upkeep_pid)
               AS n_disagree,
           COUNT(*) FILTER (
               WHERE control_pid IS NULL OR upkeep_pid IS NULL
           ) AS n_either_null,
           ROUND(
               1.0 * COUNT(*) FILTER (WHERE control_pid = upkeep_pid)
                   / NULLIF(COUNT(*), 0), 6
           ) AS agreement_rate
    FROM ev
    GROUP BY evtTypeName
    ORDER BY evtTypeName
    """,
)
print("=== V2.4 control vs upkeep agreement per event ===")
print(v2_4_df.to_string(index=False))

# %% [markdown]
# ### V2 verdict assembly
#
# Per-event-type mapping verdict. The 7 direct-mapping events get
# `match_rate_player_attributed` from V2.3; the 3 lineage-required
# events (UnitTypeChange / UnitDone / UnitPositions) get
# `lineage_required` per Amendment-3-aware classification.

# %%
DIRECT_MAPPING_FIELD = {
    "PlayerStats": "playerId",
    "UnitBorn": "controlPlayerId",
    "UnitInit": "controlPlayerId",
    "UnitOwnerChange": "controlPlayerId",
    "UnitDied": "killerPlayerId",
    "Upgrade": "playerId",
    "PlayerSetup": "playerId",
}
LINEAGE_REQUIRED = {
    "UnitTypeChange": (
        "No direct player-id field per s2protocol snapshot; "
        "requires lineage via (filename, unitTagIndex, unitTagRecycle) "
        "join back to UnitBorn / UnitInit. Deferred to V5."
    ),
    "UnitDone": (
        "No direct player-id field; lineage via "
        "(filename, unitTagIndex, unitTagRecycle) -> UnitInit. "
        "Deferred to V5."
    ),
    "UnitPositions": (
        "No direct player-id field; uses packed m_items array keyed "
        "by m_firstUnitIndex. Lineage required; coordinate semantics "
        "handled in V6."
    ),
}

# %% [markdown]
# ### V2 verdict computation

# %%
mappings = []
for event_type, field in DIRECT_MAPPING_FIELD.items():
    rows = v2_3_df[v2_3_df["evtTypeName"] == event_type]
    pa = rows[rows["slot_class"] == "player_attributed"]
    ng = rows[rows["slot_class"] == "neutral_or_global"]
    nm = rows[rows["slot_class"] == "null_or_missing"]
    pa_match = float(pa["match_rate"].iloc[0]) if not pa.empty else None
    pa_n = int(pa["n_events"].iloc[0]) if not pa.empty else 0
    ng_n = int(ng["n_events"].iloc[0]) if not ng.empty else 0
    nm_n = int(nm["n_events"].iloc[0]) if not nm.empty else 0
    if pa_match is None:
        confidence = "no_player_attributed_rows"
    elif pa_match >= 0.995:
        confidence = "high"
    elif pa_match >= 0.95:
        confidence = "medium"
    else:
        confidence = "low"
    mappings.append({
        "event_type": event_type,
        "chosen_id_field": field,
        "match_rate_player_attributed": pa_match,
        "n_player_attributed": pa_n,
        "n_neutral_or_global": ng_n,
        "n_null_or_missing": nm_n,
        "confidence": confidence,
        "verdict": (
            "high_confidence_direct_mapping" if confidence == "high"
            else "medium_confidence_direct_mapping" if confidence == "medium"
            else "low_confidence_direct_mapping" if confidence == "low"
            else "no_player_attributed_rows"
        ),
    })
for event_type, reason in LINEAGE_REQUIRED.items():
    mappings.append({
        "event_type": event_type,
        "chosen_id_field": None,
        "match_rate_player_attributed": None,
        "n_player_attributed": None,
        "n_neutral_or_global": None,
        "n_null_or_missing": None,
        "confidence": "n/a",
        "verdict": "lineage_required",
        "rationale": reason,
    })

high_conf = [m for m in mappings if m["verdict"] == "high_confidence_direct_mapping"]
med_conf = [m for m in mappings if m["verdict"] == "medium_confidence_direct_mapping"]
low_or_amb = [m for m in mappings if m["verdict"] in (
    "low_confidence_direct_mapping", "no_player_attributed_rows"
)]
lineage = [m for m in mappings if m["verdict"] == "lineage_required"]

# Determine V2 result.
if low_or_amb:
    v2_result = "FAIL"
    v2_caveat = (
        f"{len(low_or_amb)} direct-mapping event types fell below the "
        f"99.5% / 95% confidence thresholds: "
        f"{[m['event_type'] for m in low_or_amb]}"
    )
elif med_conf:
    v2_result = "PASS_WITH_CAVEAT"
    v2_caveat = (
        f"{len(med_conf)} event types at MEDIUM confidence "
        f"(95% <= match_rate < 99.5%): {[m['event_type'] for m in med_conf]}"
    )
else:
    v2_result = "PASS"
    v2_caveat = (
        f"All {len(high_conf)} direct-mapping event types HIGH confidence; "
        f"{len(lineage)} event types correctly classified lineage_required."
    )

# %% [markdown]
# ### V2 verdict block

# %%
neutral_handling_summary = {
    m["event_type"]: {
        "neutral_or_global_count": m["n_neutral_or_global"],
        "null_or_missing_count": m["n_null_or_missing"],
    }
    for m in mappings
    if m["event_type"] in DIRECT_MAPPING_FIELD
}
control_upkeep_summary = {
    row["evtTypeName"]: {
        "n": int(row["n"]),
        "agreement_rate": float(row["agreement_rate"]),
    }
    for _, row in v2_4_df.iterrows()
}

verdicts["V2"] = {
    "hypothesis": (
        "PlayerStats->playerId; UnitBorn/Init/OwnerChange->controlPlayerId "
        "(+upkeepPlayerId); UnitDied->killerPlayerId (killer attribution; "
        "victim is lineage_required); Upgrade->playerId; PlayerSetup->playerId. "
        "UnitTypeChange/UnitDone/UnitPositions have NO direct player-id "
        "field and require lineage."
    ),
    "falsifier": (
        "no stable mapping field for player-attributed rows; player-attributed "
        "match rate < 99.5% on the player_attributed slice (Amendment 3); "
        "ambiguous ties; direct fields contradict replay_players_raw"
    ),
    "result": v2_result,
    "player_attributed_threshold": 0.995,
    "mappings": mappings,
    "neutral_handling": neutral_handling_summary,
    "control_vs_upkeep_agreement": control_upkeep_summary,
    "ambiguous_event_types": [m["event_type"] for m in low_or_amb],
    "lineage_required_event_types": [m["event_type"] for m in lineage],
    "high_confidence_event_types": [m["event_type"] for m in high_conf],
    "medium_confidence_event_types": [m["event_type"] for m in med_conf],
    "notes": v2_caveat,
}

print("=== V2 verdict ===")
print(f"  result: {verdicts['V2']['result']}")
print(f"  high-confidence direct mappings: "
      f"{verdicts['V2']['high_confidence_event_types']}")
print(f"  medium-confidence direct mappings: "
      f"{verdicts['V2']['medium_confidence_event_types']}")
print(f"  lineage_required: "
      f"{verdicts['V2']['lineage_required_event_types']}")
print(f"  ambiguous/low/fail: "
      f"{verdicts['V2']['ambiguous_event_types']}")
print(f"  notes: {verdicts['V2']['notes']}")

# %% [markdown]
# ## V2 result summary
#
# - **7 direct-mapping event types:** PlayerStats, UnitBorn, UnitInit,
#   UnitOwnerChange, UnitDied, Upgrade, PlayerSetup. Mapping field
#   chosen per s2protocol snapshot semantics (controlPlayerId for
#   ownership; killerPlayerId for UnitDied attribution; playerId for
#   the rest).
# - **3 lineage_required event types:** UnitTypeChange, UnitDone,
#   UnitPositions. No direct player-id field per s2protocol snapshot;
#   classified `lineage_required` (NOT `FAIL`) per Amendment 3
#   semantics + plan T07 deferral to V5.
# - **Amendment 3 enforced:** match-rate threshold (>=99.5%) applied
#   ONLY to the `player_attributed` slice. Neutral/global (pid IN
#   (16, 0)) and null/missing rows reported separately, NOT counted as
#   failures.

# %% [markdown]
# ---
# ## V3 -- PlayerStats field semantics (strict cumulative classification per Q3)
#
# **Hypothesis.**
# - PlayerStats records periodic per-player economic / military
#   snapshots.
# - The stream is suitable for in-game snapshot features if cadence,
#   mapping, and field completeness pass.
# - Cumulative interpretation is NOT assumed -- the s2protocol decoder
#   does not document cumulative semantics for the `*Lost` / `*Killed`
#   / `*FriendlyFire` / `*Used` / `*Current` keys. Per Q3 strict rule,
#   monotonic empirics ALONE do NOT promote a field to `safe_delta`.
#
# **Falsifier.**
# - PlayerStats cadence not stable per `(filename, playerId)`;
# - missing PlayerStats for a material number of replays;
# - field key-set differs materially from the s2protocol snapshot;
# - field values cannot be classified as snapshot / delta / ambiguous;
# - any field required for a candidate feature family has unverified
#   semantics.
#
# **Classification vocabulary (per T05 step 4).**
# - `safe_snapshot` -- per-tick observable, bounded oscillation,
#   decreases present (compatible with instantaneous state);
# - `safe_delta` -- monotonic non-decreasing AND s2protocol confirms
#   cumulative interpretation (Q3 strict requires source confirmation,
#   NOT empirical monotonicity alone);
# - `unsafe_or_ambiguous` -- neither pattern, OR monotonic-only with
#   no source authority.

# %% [markdown]
# ### V3.1 -- enumerate observed PlayerStats stats keys

# %%
v3_1_df = run_q(
    "v3_1_enumerate_stats_keys",
    """
    WITH s AS (
        SELECT json_extract(event_data, '$.stats') AS stats
        FROM tracker_events_raw
        WHERE evtTypeName = 'PlayerStats'
        LIMIT 100000
    ),
    keys_unnested AS (
        SELECT UNNEST(json_keys(stats)) AS k FROM s
    )
    SELECT k, COUNT(*) AS n
    FROM keys_unnested
    GROUP BY k
    ORDER BY k
    """,
)
print("=== V3.1 observed PlayerStats stats keys ===")
print(v3_1_df.to_string(index=False))
observed_keys = sorted(v3_1_df["k"].astype(str).tolist())
print(f"\nObserved key count: {len(observed_keys)}")

# %% [markdown]
# ### V3.1 -- cross-reference observed vs s2protocol snapshot
#
# **Empirical convention discovered.** The s2protocol snapshot uses the
# C++ struct member prefix `m_` (e.g., `m_scoreValueMineralsCurrent`).
# The SC2EGSet JSON decoder STRIPS this prefix when serializing event
# payloads, so the observed JSON keys are `scoreValueMineralsCurrent`
# (no leading `m_`). The set comparison normalizes both sides by
# stripping `m_` from the snapshot keys.

# %%
expected_keys_raw = sorted(
    EVIDENCE["V3_player_stats_fields"]["stats_keys_from_snapshot"]
)
expected_keys = sorted(k.removeprefix("m_") for k in expected_keys_raw)
observed_set = set(observed_keys)
expected_set = set(expected_keys)
missing_from_observed = sorted(expected_set - observed_set)
extra_in_observed = sorted(observed_set - expected_set)
matched_set = sorted(observed_set & expected_set)
print(f"observed_count: {len(observed_keys)}")
print(f"expected_count (m_-stripped): {len(expected_keys)}")
print(f"matched_count: {len(matched_set)}")
print(f"missing_from_observed ({len(missing_from_observed)}): "
      f"{missing_from_observed}")
print(f"extra_in_observed   ({len(extra_in_observed)}): "
      f"{extra_in_observed}")
# Per T05: do not fail if snapshot has keys absent historically; record
# for V4 if needed.
EVIDENCE["V3_player_stats_fields"]["decoded_json_strips_m_prefix"] = True

# %% [markdown]
# ### V3.2 -- cadence audit partitioned by (filename, playerId)
#
# Top gaps in the per-player tracker series. Per-player partitioning
# eliminates the cross-player co-fire seen in `research_log.md` lines
# ~991-994. Any `gap=0` rows that remain are NOT cross-player co-fire
# (the partition handles that) -- they are duplicate PlayerStats rows
# for the same `(filename, playerId, loop)`. The dedicated cell below
# verifies this empirically: the count of `(extra rows beyond the
# first per duplicate group)` should match the `gap=0` row count.

# %%
v3_2_gap_df = run_q(
    "v3_2_cadence_gap_distribution",
    """
    WITH ps AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.playerId') AS INT)
                   AS pid,
               loop,
               loop - LAG(loop) OVER (
                   PARTITION BY
                       filename,
                       TRY_CAST(json_extract_string(event_data, '$.playerId')
                                AS INT)
                   ORDER BY loop
               ) AS gap
        FROM tracker_events_raw
        WHERE evtTypeName = 'PlayerStats'
    )
    SELECT gap, COUNT(*) AS n
    FROM ps
    WHERE gap IS NOT NULL
    GROUP BY gap
    ORDER BY n DESC
    LIMIT 10
    """,
)
print("=== V3.2 top-10 gap distribution per (filename, playerId) ===")
print(v3_2_gap_df.to_string(index=False))

# %% [markdown]
# ### V3.2 -- per-replay coverage and per-player presence

# %%
v3_2_coverage_df = run_q(
    "v3_2_per_replay_player_coverage",
    """
    WITH ps_player AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.playerId') AS INT)
                   AS pid
        FROM tracker_events_raw
        WHERE evtTypeName = 'PlayerStats'
        GROUP BY filename, pid
    ),
    per_replay AS (
        SELECT filename, COUNT(DISTINCT pid) AS n_distinct_players
        FROM ps_player
        GROUP BY filename
    )
    SELECT n_distinct_players, COUNT(*) AS n_replays
    FROM per_replay
    GROUP BY n_distinct_players
    ORDER BY n_distinct_players
    """,
)
print("=== V3.2 distinct PlayerStats playerIds per replay ===")
print(v3_2_coverage_df.to_string(index=False))

# %% [markdown]
# ### V3.2 -- verdict assembly

# %%
total_gap_rows = int(v3_2_gap_df["n"].sum())
dominant_gap_row = v3_2_gap_df.iloc[0]
dominant_gap = int(dominant_gap_row["gap"])
dominant_gap_n = int(dominant_gap_row["n"])
dominant_gap_frac = (
    dominant_gap_n / total_gap_rows if total_gap_rows else 0.0
)
top_10_gaps = [
    {"gap": int(r["gap"]), "n": int(r["n"])}
    for _, r in v3_2_gap_df.iterrows()
]
n_replays_with_both_players = int(
    v3_2_coverage_df[v3_2_coverage_df["n_distinct_players"] == 2]
    ["n_replays"].sum()
)
n_replays_total_in_v32 = int(v3_2_coverage_df["n_replays"].sum())
n_replay_player_pairs_no_ps = 0
for _, r in v3_2_coverage_df.iterrows():
    if int(r["n_distinct_players"]) < 2:
        n_replay_player_pairs_no_ps += int(r["n_replays"]) * (
            2 - int(r["n_distinct_players"])
        )
cadence_pass_160 = (dominant_gap == 160) and (dominant_gap_frac >= 0.95)
print(
    f"dominant_gap={dominant_gap}, frac={dominant_gap_frac:.4f}, "
    f"replays_with_both_players={n_replays_with_both_players}/"
    f"{n_replays_total_in_v32}, missing_replay_player_pairs="
    f"{n_replay_player_pairs_no_ps}, cadence_pass={cadence_pass_160}"
)

# %% [markdown]
# ### V3.2 -- explain gap=0: duplicate-row vs cross-player co-fire
#
# The partition on `(filename, playerId)` already excludes cross-player
# co-fire from the gap series. A non-zero `gap=0` count therefore
# implies same-player duplicate PlayerStats rows: multiple rows with
# identical `(filename, playerId, loop)`. The query below counts those
# duplicates; the sum of `n - 1` per duplicate group must equal the
# `gap=0` row count from V3.2.

# %%
v3_2_dup_df = run_q(
    "v3_2_same_player_duplicate_groups",
    """
    WITH ps AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.playerId') AS INT)
                   AS pid,
               loop,
               COUNT(*) AS n_at_same_key
        FROM tracker_events_raw
        WHERE evtTypeName = 'PlayerStats'
        GROUP BY filename, pid, loop
    )
    SELECT
        COUNT(*) FILTER (WHERE n_at_same_key > 1) AS n_duplicate_groups,
        COALESCE(SUM(n_at_same_key - 1) FILTER (WHERE n_at_same_key > 1), 0)
            AS n_extra_rows_beyond_first
    FROM ps
    """,
)
n_duplicate_groups = int(v3_2_dup_df["n_duplicate_groups"].iloc[0])
n_extra_rows = int(v3_2_dup_df["n_extra_rows_beyond_first"].iloc[0])
gap_zero_row = v3_2_gap_df[v3_2_gap_df["gap"] == 0]
gap_zero_n = int(gap_zero_row["n"].iloc[0]) if not gap_zero_row.empty else 0
gap_zero_explained_by_duplicates = (n_extra_rows == gap_zero_n)
print(f"duplicate_groups={n_duplicate_groups}, "
      f"extra_rows_beyond_first={n_extra_rows}, "
      f"gap_zero_n={gap_zero_n}, "
      f"explained_by_duplicates={gap_zero_explained_by_duplicates}")

# %% [markdown]
# ### V3.3 -- field classification (per-(filename, playerId) monotonicity)
#
# Single SQL pass extracts every observed key as a DOUBLE column,
# computes LAG within (filename, playerId) ordered by loop, then
# aggregates: null count, min, max, n_with_prev, n_decreases. Per-field
# null fractions and decrease fractions are computed in Python.

# %%
def _build_field_stats_sql(keys: list[str]) -> str:
    """Build a single-pass SQL that aggregates monotonicity stats per key."""
    extracts = ",\n        ".join(
        f"TRY_CAST(json_extract_string(event_data, '$.stats.{k}') "
        f"AS DOUBLE) AS \"{k}\""
        for k in keys
    )
    lags = ",\n        ".join(
        f'"{k}", LAG("{k}") OVER w AS "prev_{k}"' for k in keys
    )
    aggs = ",\n  ".join(
        f'SUM(CASE WHEN "{k}" IS NULL THEN 1 ELSE 0 END) AS "n_null_{k}", '
        f'MIN("{k}") AS "min_{k}", MAX("{k}") AS "max_{k}", '
        f'SUM(CASE WHEN "prev_{k}" IS NOT NULL THEN 1 ELSE 0 END) '
        f'AS "n_wp_{k}", '
        f'SUM(CASE WHEN "prev_{k}" IS NOT NULL AND "{k}" < "prev_{k}" '
        f'THEN 1 ELSE 0 END) AS "n_dec_{k}"'
        for k in keys
    )
    return (
        "WITH ps AS (\n"
        "  SELECT filename,\n"
        "    TRY_CAST(json_extract_string(event_data, '$.playerId') AS INT)\n"
        "      AS pid,\n"
        "    loop,\n"
        f"    {extracts}\n"
        "  FROM tracker_events_raw\n"
        "  WHERE evtTypeName = 'PlayerStats'\n"
        "),\n"
        "with_lag AS (\n"
        f"  SELECT filename, pid, loop,\n        {lags}\n"
        "  FROM ps\n"
        "  WINDOW w AS (PARTITION BY filename, pid ORDER BY loop)\n"
        ")\n"
        f"SELECT COUNT(*) AS n_total_rows,\n  {aggs}\nFROM with_lag"
    )


# %%
v3_3_sql = _build_field_stats_sql(observed_keys)
sql_queries["v3_3_field_stats"] = v3_3_sql
print(f"V3.3 SQL length: {len(v3_3_sql)} chars; "
      f"keys: {len(observed_keys)}")
v3_3_df = conn.con.execute(v3_3_sql).df()
n_total_rows = int(v3_3_df["n_total_rows"].iloc[0])
print(f"V3.3 scanned n_total_rows = {n_total_rows}")

# %% [markdown]
# ### V3.3 -- per-field summary stats

# %%
import pandas as pd

field_stats: list[dict] = []
for k in observed_keys:
    n_null = int(v3_3_df[f"n_null_{k}"].iloc[0])
    minv = v3_3_df[f"min_{k}"].iloc[0]
    maxv = v3_3_df[f"max_{k}"].iloc[0]
    n_wp = int(v3_3_df[f"n_wp_{k}"].iloc[0])
    n_dec = int(v3_3_df[f"n_dec_{k}"].iloc[0])
    null_frac = n_null / n_total_rows if n_total_rows else None
    dec_frac = n_dec / n_wp if n_wp else None
    field_stats.append({
        "key": k,
        "n_null": n_null,
        "null_fraction": null_frac,
        "min": float(minv) if minv is not None else None,
        "max": float(maxv) if maxv is not None else None,
        "n_with_prev": n_wp,
        "n_decreases": n_dec,
        "frac_decreases": dec_frac,
    })
fs_df = pd.DataFrame(field_stats)
print("=== V3.3 per-field summary statistics ===")
print(
    fs_df[["key", "null_fraction", "min", "max", "frac_decreases"]]
    .to_string(index=False)
)

# %% [markdown]
# ### V3.3 -- apply Q3 strict classification rule
#
# Per Q3 + T02 EVIDENCE: s2protocol does NOT document cumulative
# semantics for any `*Lost` / `*Killed` / `*FriendlyFire` / `*Used` /
# `*Current` field. Therefore monotonic empirics ALONE cannot promote a
# field to `safe_delta`. Monotonic-only fields default to
# `unsafe_or_ambiguous`. The empty `SOURCE_CONFIRMS_CUMULATIVE` set
# encodes this explicitly.

# %%
SOURCE_CONFIRMS_CUMULATIVE: set[str] = set()
classified: list[dict] = []
for fs in field_stats:
    k = fs["key"]
    dec_frac = fs["frac_decreases"]
    if dec_frac is None or fs["n_with_prev"] == 0:
        cls, reason = "unsafe_or_ambiguous", "insufficient_consecutive_pairs"
    elif fs["min"] is not None and fs["min"] == fs["max"]:
        cls = "unsafe_or_ambiguous"
        reason = (
            f"constant value {fs['min']}; cannot distinguish snapshot "
            "vs cumulative"
        )
    elif dec_frac > 0:
        cls = "safe_snapshot"
        reason = f"bounded oscillation; frac_decreases={dec_frac:.6f}"
    elif k in SOURCE_CONFIRMS_CUMULATIVE:
        cls = "safe_delta"
        reason = "monotonic non-decreasing AND s2protocol cumulative-confirmed"
    else:
        cls = "unsafe_or_ambiguous"
        reason = (
            f"monotonic non-decreasing (frac_decreases={dec_frac:.6f}) "
            "but s2protocol silent on cumulative semantics (Q3 strict)"
        )
    classified.append({
        **fs,
        "classification": cls,
        "classification_reason": reason,
        "source_confirmed_cumulative": k in SOURCE_CONFIRMS_CUMULATIVE,
    })

import collections
class_counts = collections.Counter(c["classification"] for c in classified)
print("=== V3.3 classification counts ===")
print(dict(class_counts))

# %% [markdown]
# ### V3.3 -- fixed-point handling note
#
# Per s2protocol README, `m_scoreValueFoodUsed` and `m_scoreValueFoodMade`
# are stored in fixed point (divide by 4096 for integer values).
# Whether the SC2EGSet decoded JSON is pre-scaled is NOT confirmed by
# this notebook. T05 records the convention verbatim and does NOT apply
# any divide-by-4096 transformation. Phase 02 must resolve scaling
# discipline before any feature uses these fields.

# %%
FIXED_POINT_KEYS_SNAPSHOT = ["m_scoreValueFoodUsed", "m_scoreValueFoodMade"]
FIXED_POINT_KEYS_OBSERVED = [
    k.removeprefix("m_") for k in FIXED_POINT_KEYS_SNAPSHOT
]
fixed_point_handling = {
    "policy": (
        "T05 records fixed-point convention from s2protocol README "
        "verbatim; does NOT divide by 4096; classification proceeds on "
        "raw decoded values; Phase 02 must resolve scaling discipline."
    ),
    "verbatim_note": (
        EVIDENCE["V3_player_stats_fields"]
        ["s2protocol_fixed_point_note_verbatim"]
    ),
    "fields_in_snapshot": FIXED_POINT_KEYS_SNAPSHOT,
    "fields_in_observed_form": FIXED_POINT_KEYS_OBSERVED,
    "observed_in_sc2egset": [
        k for k in FIXED_POINT_KEYS_OBSERVED if k in observed_keys
    ],
}
print("=== V3.3 fixed-point handling ===")
for fk, fv in fixed_point_handling.items():
    print(f"  {fk}: {fv}")

# %% [markdown]
# ### V3 verdict assembly
#
# `cumulative_economy_blocked` is True iff at least one
# `*Lost` / `*Killed` / `*FriendlyFire` field is NOT classified
# `safe_delta`. Per the empty `SOURCE_CONFIRMS_CUMULATIVE` set, this is
# True by construction in T05.

# %%
safe_snapshot_fields = sorted(
    c["key"] for c in classified if c["classification"] == "safe_snapshot"
)
safe_delta_fields = sorted(
    c["key"] for c in classified if c["classification"] == "safe_delta"
)
unsafe_fields = sorted(
    c["key"] for c in classified
    if c["classification"] == "unsafe_or_ambiguous"
)
all_classified = (len(classified) == len(observed_keys))
cum_kw = ("Lost", "Killed", "FriendlyFire")
cumulative_economy_blocked = any(
    c["classification"] != "safe_delta"
    for c in classified
    if any(w in c["key"] for w in cum_kw)
)

if not cadence_pass_160:
    v3_result = "FAIL"
    v3_caveat = (
        f"cadence audit: dominant_gap={dominant_gap} "
        f"(frac={dominant_gap_frac:.4f}); expected 160 with frac>=0.95"
    )
elif missing_from_observed or extra_in_observed:
    v3_result = "PASS_WITH_CAVEAT"
    v3_caveat = (
        f"key set drift vs s2protocol snapshot: "
        f"missing={len(missing_from_observed)}, "
        f"extra={len(extra_in_observed)}; cumulative-economy fields "
        f"blocked per Q3 strict"
    )
else:
    v3_result = "PASS_WITH_CAVEAT"
    v3_caveat = (
        "snapshot cadence and key-set match; "
        f"{len(safe_snapshot_fields)} safe_snapshot fields enable "
        "in-game snapshot features; cumulative-economy features "
        "blocked because s2protocol silent on cumulative semantics "
        "(Q3 strict)"
    )

# %% [markdown]
# ### V3 verdict block

# %%
verdicts["V3"] = {
    "hypothesis": (
        "PlayerStats records periodic per-player economic / military "
        "snapshots; suitable for in-game snapshot features if cadence, "
        "mapping, and field completeness pass; cumulative interpretation "
        "NOT assumed (Q3 strict)."
    ),
    "falsifier": (
        "cadence not stable per (filename, playerId); missing PlayerStats "
        "for material number of replays; key-set drift; values cannot be "
        "classified; candidate feature family field semantics unverified"
    ),
    "result": v3_result,
    "all_observed_keys_classified": all_classified,
    "cadence_summary": {
        "dominant_gap_loops": dominant_gap,
        "dominant_gap_fraction": dominant_gap_frac,
        "top_10_gaps": top_10_gaps,
        "replays_with_both_players": n_replays_with_both_players,
        "replays_total_with_playerstats": n_replays_total_in_v32,
        "missing_replay_player_pairs": n_replay_player_pairs_no_ps,
        "expected_dominant_gap_loops": 160,
        "expected_dominant_gap_seconds_at_22_4_lps": 160 / 22.4,
        "cadence_pass_160": cadence_pass_160,
        "gap_zero_n": gap_zero_n,
        "gap_zero_cause": (
            "same-player duplicate PlayerStats tick rows; partition by "
            "(filename, playerId) is correct"
        ),
        "gap_zero_explained_by_duplicates": gap_zero_explained_by_duplicates,
        "duplicate_groups": n_duplicate_groups,
        "duplicate_extra_rows_beyond_first": n_extra_rows,
    },
    "key_set_comparison": {
        "observed_count": len(observed_keys),
        "expected_count": len(expected_keys),
        "matched_count": len(matched_set),
        "missing_from_observed": missing_from_observed,
        "extra_in_observed": extra_in_observed,
    },
    "field_classification": classified,
    "safe_snapshot_fields": safe_snapshot_fields,
    "safe_delta_fields": safe_delta_fields,
    "unsafe_or_ambiguous_fields": unsafe_fields,
    "cumulative_economy_blocked": cumulative_economy_blocked,
    "fixed_point_handling": fixed_point_handling,
    "notes": v3_caveat,
}
print("=== V3 verdict ===")
print(f"  result: {verdicts['V3']['result']}")
print(f"  safe_snapshot fields: {len(safe_snapshot_fields)}")
print(f"  safe_delta fields:    {len(safe_delta_fields)}")
print(f"  unsafe_or_ambiguous:  {len(unsafe_fields)}")
print(f"  cumulative_economy_blocked: {cumulative_economy_blocked}")
print(f"  notes: {verdicts['V3']['notes']}")

# %% [markdown]
# ### V3 classification consistency assertions
#
# Per T05 hygiene check section B: assert that the classification is
# total, mutually exclusive, and that `safe_delta` remains 0 (since
# `SOURCE_CONFIRMS_CUMULATIVE` is empty by design under Q3 strict).

# %%
assert len(classified) == len(observed_keys), (
    f"classified count {len(classified)} != observed {len(observed_keys)}"
)
class_buckets = {c["key"]: c["classification"] for c in classified}
assert len(class_buckets) == len(classified), "duplicate keys in classified"
assert set(class_buckets.values()) <= {
    "safe_snapshot", "safe_delta", "unsafe_or_ambiguous"
}, "unexpected classification value"
ss = set(safe_snapshot_fields)
sd = set(safe_delta_fields)
ua = set(unsafe_fields)
assert (ss | sd | ua) == set(observed_keys), (
    f"union of class lists != observed keys; "
    f"diff={(ss | sd | ua) ^ set(observed_keys)}"
)
assert (ss & sd) == set(), f"safe_snapshot ∩ safe_delta = {ss & sd}"
assert (ss & ua) == set(), f"safe_snapshot ∩ unsafe = {ss & ua}"
assert (sd & ua) == set(), f"safe_delta ∩ unsafe = {sd & ua}"
assert len(safe_delta_fields) == 0, (
    "safe_delta MUST be empty under Q3 strict: SOURCE_CONFIRMS_CUMULATIVE "
    "is empty by design"
)
print("=== V3 classification consistency: OK ===")
print(f"  total: {len(classified)}; "
      f"safe_snapshot: {len(safe_snapshot_fields)}; "
      f"safe_delta: {len(safe_delta_fields)}; "
      f"unsafe_or_ambiguous: {len(unsafe_fields)}")

# %% [markdown]
# ## V3 result summary
#
# - **Cadence:** dominant gap is 160 loops per `(filename, playerId)`,
#   matching the SC2 tracker spec (~7.14s at 22.4 lps). The residual
#   `gap=0` rows are NOT cross-player co-fire (partition handles that)
#   -- they are same-player duplicate PlayerStats rows for the same
#   `(filename, playerId, loop)`. Row count exactly matches the
#   `n - 1` sum over duplicate groups, so this is a row-multiplicity
#   caveat at ingestion, not a cadence partition error.
# - **Key set:** observed PlayerStats stats keys match the s2protocol
#   `protocol88500.py` snapshot after stripping the `m_` prefix (the
#   SC2EGSet decoder strips that C++ struct member prefix when
#   serializing JSON).
# - **`safe_snapshot` (26 fields)** -- usable as a raw observed snapshot
#   at a cutoff loop, with scaling and semantic caveats where flagged
#   below. NOT a cumulative total. Includes:
#     - all `*Current` / `*UsedCurrent*` / `*UsedInProgress*` /
#       `*UsedActiveForces` / `*CollectionRate` /
#       `WorkersActiveCount` / `FoodUsed` / `FoodMade`
#       (oscillation observed, as expected for instantaneous state);
#     - 5 of 6 `*Lost*` fields (`scoreValueMineralsLostArmy/Economy/
#       Technology`, `scoreValueVespeneLostArmy`,
#       `scoreValueVespeneLostTechnology`) -- small empirical decrease
#       fractions and negative minima (e.g., min=-2033) suggest these
#       are not pure cumulative tallies; treated as raw snapshots with
#       a "negative-min caveat" for Phase 02.
# - **`unsafe_or_ambiguous` (13 fields)** -- monotonic non-decreasing
#   AND s2protocol silent on cumulative semantics, OR constant-zero:
#     - all 6 `*Killed*` fields (Mineral and Vespene, Army/Economy/
#       Technology) -- strictly monotonic, no source confirmation;
#     - all 6 `*FriendlyFire*` fields -- mostly constant zero in 1v1
#       Random Map, no source confirmation;
#     - 1 of 6 `*Lost*` fields (`scoreValueVespeneLostEconomy`) --
#       zero decreases observed AND no source confirmation.
# - **`safe_delta` (0 fields)** -- empty by construction. Under Q3
#   strict, `SOURCE_CONFIRMS_CUMULATIVE` is empty: monotonic empirics
#   alone CANNOT promote a field to `safe_delta` without s2protocol
#   confirmation, which is absent for every PlayerStats stats key.
# - **Cumulative-economy feature families are blocked** until additional
#   validation (Q3 strict + Amendment 1 aggregation in T10);
#   snapshot feature families remain candidates pending V4..V7.
# - **`safe_snapshot` does NOT mean cumulative total.** It means
#   "usable as a raw observed snapshot at a cutoff loop, subject to the
#   scaling caveat (FoodUsed/FoodMade) and the negative-minimum caveat
#   (Lost fields)." Cumulative-style features remain blocked.
# - **V3 verdict:** `PASS_WITH_CAVEAT` -- snapshot cadence and key-set
#   pass; cumulative-economy feature families blocked per Q3 strict.

# %% [markdown]
# ---
# ## V4 -- Event coverage and JSON key-set stability across years / patches
#
# **Hypothesis.** All 10 tracker event families observed in 01_03_04
# have stable enough presence and JSON key structure across the
# 2016-2024 corpus to support feature-family eligibility decisions.
#
# **Falsifier.**
# - any event family used by a planned feature is missing or materially
#   unstable across major year / `gameVersion` cohorts;
# - key-set changes materially across cohorts (>=2 keys differ between
#   two cohorts each holding >5% of the corpus) and cannot be handled
#   by source-specific null/caveat logic;
# - rare-event under-sampling prevents a defensible decision.
#
# **Carry-forward (T02).** `protocol88500.py` is a *recent* s2protocol
# reference snapshot; V4 must empirically check observed corpus
# stability across the 2016-2024 SC2EGSet window. Do NOT claim that
# protocol88500 alone proves full historical stability.
#
# **Per Amendment 6.** Rare event families MUST NOT be declared
# absent/unstable solely because Pass A 1% Bernoulli sampling
# under-represents them. Pass B stratified resample (up to 10K rows per
# `(evtTypeName, cohort)`) confirms or refutes Pass A findings; truly
# rare families get `coverage_too_sparse_for_stability_decision`.

# %% [markdown]
# ### V4.1 -- per-year replay coverage and event count (full table)
#
# Joins `tracker_events_raw` x `replays_meta_raw` on `filename` and
# extracts the year from `details.timeUTC` via `TRY_CAST`. Full-table
# scan -- no sampling here.

# %%
v4_1_year_totals_df = run_q(
    "v4_1_year_replay_totals",
    """
    SELECT EXTRACT(YEAR FROM TRY_CAST(details.timeUTC AS TIMESTAMP)) AS year,
           COUNT(*) AS n_replays_in_year
    FROM replays_meta_raw
    GROUP BY year
    ORDER BY year
    """,
)
print("=== V4.1 replays per year ===")
print(v4_1_year_totals_df.to_string(index=False))
years_observed = sorted(
    int(y) for y in v4_1_year_totals_df["year"].dropna().tolist()
)
print(f"\nObserved years: {years_observed}")

# %%
v4_1_df = run_q(
    "v4_1_per_year_coverage",
    """
    WITH years AS (
        SELECT DISTINCT
               EXTRACT(YEAR FROM TRY_CAST(details.timeUTC AS TIMESTAMP)) AS year
        FROM replays_meta_raw
        WHERE TRY_CAST(details.timeUTC AS TIMESTAMP) IS NOT NULL
    ),
    event_types AS (
        SELECT DISTINCT evtTypeName FROM tracker_events_raw
    ),
    grid AS (
        SELECT y.year, et.evtTypeName
        FROM years y CROSS JOIN event_types et
    ),
    counts AS (
        SELECT EXTRACT(YEAR FROM TRY_CAST(rm.details.timeUTC AS TIMESTAMP))
                   AS year,
               te.evtTypeName,
               COUNT(DISTINCT te.filename) AS n_replays,
               COUNT(*) AS n_events
        FROM tracker_events_raw te
        JOIN replays_meta_raw rm USING (filename)
        GROUP BY year, te.evtTypeName
    )
    SELECT g.year, g.evtTypeName,
           COALESCE(c.n_replays, 0) AS n_replays,
           COALESCE(c.n_events, 0) AS n_events
    FROM grid g
    LEFT JOIN counts c USING (year, evtTypeName)
    ORDER BY g.year, g.evtTypeName
    """,
)
v4_1_with_pct = v4_1_df.merge(
    v4_1_year_totals_df, on="year", how="left"
)
v4_1_with_pct["coverage_pct"] = (
    v4_1_with_pct["n_replays"] / v4_1_with_pct["n_replays_in_year"]
)
print("=== V4.1 per-(year, evtTypeName) coverage (zero rows included) ===")
print(v4_1_with_pct.to_string(index=False))

# %% [markdown]
# ### V4.1 -- coverage stability per event type (across years)

# %% [markdown]
# Stability classification (per "don't overfail rare families"):
# - "presence" = year has >=1 replay containing the event family.
# - present-year spread is computed over years with presence ONLY (not
#   over zero rows -- absence is a separate dimension).
# - high-prevalence family (max present-year cov >= 0.9): stable iff
#   *absolute* spread <= 5%;
# - sparse family (max present-year cov < 0.9): stable iff *relative*
#   spread <= 30%;
# - sparse + absent in some years (e.g., UnitOwnerChange absent in 2016):
#   `coverage_stable_by_year=True` IF spread is within the family's
#   threshold AND presence covers >= 70% of observed years; a
#   `coverage_caveat` is recorded and a `feature_eligibility_caveat`
#   propagates the sparse/absent fact to V8.
# - absent in majority of years: `too_sparse_to_decide`.
# `stability_basis` records which rule applied so the verdict is auditable.

# %%
event_types_observed = sorted(v4_1_df["evtTypeName"].unique().tolist())
years_total_set = set(int(y) for y in v4_1_year_totals_df["year"].dropna())
year_coverage_summary: dict = {}
for et in event_types_observed:
    rows = v4_1_with_pct[v4_1_with_pct["evtTypeName"] == et]
    rows_present = rows[rows["n_replays"] > 0]
    years_present = sorted(
        int(y) for y in rows_present["year"].dropna().tolist()
    )
    years_absent = sorted(years_total_set - set(years_present))
    present_pcts = rows_present["coverage_pct"].tolist()
    if not present_pcts:
        year_coverage_summary[et] = {
            "years_present": [], "years_absent": sorted(years_total_set),
            "min_year_coverage": None, "max_year_coverage": None,
            "coverage_spread": None, "coverage_relative_spread": None,
            "stability_basis": "no_presence_in_any_year",
            "coverage_stable_by_year": "too_sparse_to_decide",
            "coverage_caveat": "no presence in any observed year",
            "feature_eligibility_caveat":
                "sparse_event_family_not_broadly_available",
        }
        continue
    minp = float(min(present_pcts)); maxp = float(max(present_pcts))
    spread = maxp - minp
    rel_spread = spread / maxp if maxp > 0 else 0.0
    if maxp >= 0.9:
        spread_basis = "absolute_spread<=0.05 (high-prevalence)"
        spread_stable = (spread <= 0.05)
    else:
        spread_basis = "relative_spread<=0.30 (sparse-family)"
        spread_stable = (rel_spread <= 0.30)
    if not years_absent:
        cls = spread_stable
        basis = spread_basis
        cov_caveat = None
        feat_caveat = None
    elif len(years_present) >= 0.7 * len(years_total_set):
        cls = True if spread_stable else False
        basis = (
            f"{spread_basis} + sparse-family caveat: absent in "
            f"{years_absent}"
        )
        cov_caveat = (
            f"sparse / absent in years {years_absent} but present in "
            f"{len(years_present)} of {len(years_total_set)} years; "
            f"present-year spread within family threshold"
        )
        feat_caveat = "sparse_event_family_not_broadly_available"
    else:
        cls = "too_sparse_to_decide"
        basis = "absent_in_majority_of_years"
        cov_caveat = (
            f"absent in {len(years_absent)} of {len(years_total_set)} "
            f"years -> insufficient year coverage to decide stability"
        )
        feat_caveat = "sparse_event_family_not_broadly_available"
    year_coverage_summary[et] = {
        "years_present": years_present,
        "years_absent": years_absent,
        "min_year_coverage": minp,
        "max_year_coverage": maxp,
        "coverage_spread": spread,
        "coverage_relative_spread": rel_spread,
        "stability_basis": basis,
        "coverage_stable_by_year": cls,
        "coverage_caveat": cov_caveat,
        "feature_eligibility_caveat": feat_caveat,
    }
print("=== V4.1 per-event year coverage summary ===")
for et in event_types_observed:
    s = year_coverage_summary[et]
    print(
        f"  {et}: present={len(s['years_present'])}, "
        f"absent={s['years_absent']}, "
        f"min={s['min_year_coverage']:.4f}, "
        f"max={s['max_year_coverage']:.4f}, "
        f"abs_spread={s['coverage_spread']:.4f}, "
        f"rel_spread={s['coverage_relative_spread']:.4f}, "
        f"stable={s['coverage_stable_by_year']}"
    )
    if s["coverage_caveat"]:
        print(f"    caveat: {s['coverage_caveat']}")

# %% [markdown]
# ### V4.2 -- gameVersion cardinality + cohort strategy
#
# If `gameVersion` cardinality > 20, group by major.minor prefix
# (e.g., `5.0`, `4.10`, `4.11`); otherwise use raw gameVersion.
# Grouping rule is recorded explicitly so it can be reproduced.

# %%
v4_2_gv_df = run_q(
    "v4_2_gameversion_cardinality",
    """
    SELECT metadata.gameVersion AS game_version,
           COUNT(*) AS n_replays
    FROM replays_meta_raw
    GROUP BY game_version
    ORDER BY n_replays DESC
    """,
)
N_DISTINCT_GAMEVERSION = len(v4_2_gv_df)
USE_GROUPED_COHORT = N_DISTINCT_GAMEVERSION > 20
COHORT_REGEX = r'^([0-9]+\.[0-9]+)'
if USE_GROUPED_COHORT:
    COHORT_LABEL = "major_minor"
    COHORT_RULE = (
        f"regexp_extract(metadata.gameVersion, '{COHORT_REGEX}', 1)"
    )
else:
    COHORT_LABEL = "raw_gameVersion"
    COHORT_RULE = "metadata.gameVersion"
print(
    f"Distinct gameVersion: {N_DISTINCT_GAMEVERSION}; "
    f"grouped={USE_GROUPED_COHORT}; cohort_label={COHORT_LABEL}; "
    f"cohort_rule='{COHORT_RULE}'"
)


def cohort_expr(prefix: str = "") -> str:
    """Build the cohort SQL expression with optional table-alias prefix."""
    base = f"{prefix}metadata.gameVersion"
    if USE_GROUPED_COHORT:
        return f"regexp_extract({base}, '{COHORT_REGEX}', 1)"
    return base


# %% [markdown]
# ### V4.2 -- per-cohort replay totals + non-trivial cohort selection
#
# Non-trivial cohort = cohort holding > 5% of replays. Falsifier
# threshold (`>=2 keys differ between two cohorts`) only applies to
# non-trivial cohorts.

# %%
v4_2_cohort_totals_df = run_q(
    "v4_2_cohort_replay_totals",
    f"""
    SELECT {cohort_expr()} AS cohort,
           COUNT(*) AS n_replays
    FROM replays_meta_raw
    GROUP BY cohort
    ORDER BY n_replays DESC
    """,
)
total_replays = int(v4_2_cohort_totals_df["n_replays"].sum())
v4_2_cohort_totals_df["pct"] = (
    v4_2_cohort_totals_df["n_replays"] / total_replays
)
v4_2_cohort_totals_df["non_trivial"] = v4_2_cohort_totals_df["pct"] > 0.05
print(f"=== V4.2 cohort replay totals ({COHORT_LABEL}) ===")
print(v4_2_cohort_totals_df.to_string(index=False))
NON_TRIVIAL_COHORTS = sorted(
    v4_2_cohort_totals_df.loc[
        v4_2_cohort_totals_df["non_trivial"], "cohort"
    ].astype(str).tolist()
)
print(f"\nNon-trivial cohorts (>5% of {total_replays}): "
      f"{NON_TRIVIAL_COHORTS}")

# %% [markdown]
# ### V4.2 -- Pass A: 1% Bernoulli key-sets per (evtTypeName, cohort)
#
# `TABLESAMPLE BERNOULLI(1) REPEATABLE(42)` for reproducibility.
# Key-set extracted via `UNNEST(json_keys(event_data))`.

# %%
v4_2_pass_a_df = run_q(
    "v4_2_pass_a_keysets",
    f"""
    WITH samp AS (
        SELECT te.evtTypeName, te.event_data, te.filename
        FROM tracker_events_raw te
        TABLESAMPLE BERNOULLI(1%) REPEATABLE(42)
    ),
    joined AS (
        SELECT s.evtTypeName, s.event_data,
               {cohort_expr('rm.')} AS cohort
        FROM samp s JOIN replays_meta_raw rm USING (filename)
    ),
    ec AS (
        SELECT evtTypeName, cohort, COUNT(*) AS n_events
        FROM joined GROUP BY 1, 2
    ),
    un AS (
        SELECT evtTypeName, cohort, UNNEST(json_keys(event_data)) AS k
        FROM joined
    ),
    ks AS (
        SELECT evtTypeName, cohort, list(DISTINCT k ORDER BY k) AS keys
        FROM un GROUP BY evtTypeName, cohort
    )
    SELECT ks.evtTypeName, ks.cohort, ks.keys, ec.n_events
    FROM ks JOIN ec USING (evtTypeName, cohort)
    ORDER BY ks.evtTypeName, ks.cohort
    """,
)
print(f"Pass A rows: {len(v4_2_pass_a_df)}")
print(v4_2_pass_a_df[["evtTypeName", "cohort", "n_events"]]
      .to_string(index=False))

# %% [markdown]
# ### V4.2 -- identify Pass A under-sampled cells
#
# A `(evtTypeName, cohort)` cell is under-sampled if Pass A has
# < 1000 events AND the cohort is non-trivial. These cells need
# Pass B confirmation before any "unstable" verdict.

# %%
under = v4_2_pass_a_df[
    (v4_2_pass_a_df["n_events"] < 1000) &
    (v4_2_pass_a_df["cohort"].astype(str).isin(NON_TRIVIAL_COHORTS))
]
print(f"Under-sampled (Pass A) cells: {len(under)}")
if len(under):
    print(under[["evtTypeName", "cohort", "n_events"]]
          .to_string(index=False))
under_event_types = sorted(under["evtTypeName"].unique().tolist())
under_cohorts = sorted(under["cohort"].astype(str).unique().tolist())
print(f"\nUnder-sampled event types: {under_event_types}")
print(f"Under-sampled cohorts:    {under_cohorts}")

# %% [markdown]
# ### V4.2 -- Pass B: stratified resample for under-sampled cells
#
# Per Amendment 6 + plan T06.3: for every under-sampled
# `(evtTypeName, cohort)` cell, draw up to 10K rows by
# `ROW_NUMBER() OVER (PARTITION BY evtTypeName, cohort ORDER BY loop)`.
# This gives a sample large enough that key-set findings cannot be
# dismissed as under-coverage.

# %%
if under_event_types and under_cohorts:
    et_list = ", ".join(f"'{e}'" for e in under_event_types)
    coh_list = ", ".join(f"'{c}'" for c in under_cohorts)
    v4_2_pass_b_df = run_q(
        "v4_2_pass_b_keysets",
        f"""
        WITH ranked AS (
            SELECT te.evtTypeName, te.event_data, te.loop,
                   {cohort_expr('rm.')} AS cohort,
                   ROW_NUMBER() OVER (
                       PARTITION BY te.evtTypeName, {cohort_expr('rm.')}
                       ORDER BY te.loop
                   ) AS rn
            FROM tracker_events_raw te
            JOIN replays_meta_raw rm USING (filename)
            WHERE te.evtTypeName IN ({et_list})
        ),
        sampled AS (
            SELECT evtTypeName, event_data, cohort
            FROM ranked
            WHERE rn <= 10000 AND cohort IN ({coh_list})
        ),
        ec AS (
            SELECT evtTypeName, cohort, COUNT(*) AS n_events
            FROM sampled GROUP BY 1, 2
        ),
        un AS (
            SELECT evtTypeName, cohort,
                   UNNEST(json_keys(event_data)) AS k
            FROM sampled
        ),
        ks AS (
            SELECT evtTypeName, cohort,
                   list(DISTINCT k ORDER BY k) AS keys
            FROM un GROUP BY evtTypeName, cohort
        )
        SELECT ks.evtTypeName, ks.cohort, ks.keys, ec.n_events
        FROM ks JOIN ec USING (evtTypeName, cohort)
        ORDER BY ks.evtTypeName, ks.cohort
        """,
    )
    print(f"Pass B rows: {len(v4_2_pass_b_df)}")
    print(v4_2_pass_b_df[["evtTypeName", "cohort", "n_events"]]
          .to_string(index=False))
else:
    v4_2_pass_b_df = pd.DataFrame(
        columns=["evtTypeName", "cohort", "keys", "n_events"]
    )
    sql_queries["v4_2_pass_b_keysets"] = (
        "-- skipped: no under-sampled cells in Pass A"
    )
    print("No under-sampled cells; Pass B skipped.")

# %% [markdown]
# ### V4.2 -- combine Pass A + Pass B into authoritative key-sets
#
# For each `(evtTypeName, cohort)`, pick the larger sample. Record
# `sample_strategy` per cell (pass_a_only / pass_b_stratified /
# too_sparse).

# %%
authoritative: dict = {}
pass_a_lookup = {
    (r["evtTypeName"], str(r["cohort"])): {
        "keys": list(r["keys"]), "n_events": int(r["n_events"]),
    }
    for _, r in v4_2_pass_a_df.iterrows()
}
pass_b_lookup = {
    (r["evtTypeName"], str(r["cohort"])): {
        "keys": list(r["keys"]), "n_events": int(r["n_events"]),
    }
    for _, r in v4_2_pass_b_df.iterrows()
}
all_cells = set(pass_a_lookup) | set(pass_b_lookup)
for cell in all_cells:
    a = pass_a_lookup.get(cell)
    b = pass_b_lookup.get(cell)
    if b is not None and (a is None or b["n_events"] > a["n_events"]):
        authoritative[cell] = {**b, "sample_strategy": "pass_b_stratified"}
    elif a is not None and a["n_events"] >= 1000:
        authoritative[cell] = {**a, "sample_strategy": "pass_a_only"}
    elif a is not None:
        authoritative[cell] = {**a, "sample_strategy": "too_sparse"}
    else:
        authoritative[cell] = {**b, "sample_strategy": "pass_b_stratified"}
print(f"Authoritative cells: {len(authoritative)}")

# %% [markdown]
# ### V4.2 -- per-event-type stability check
#
# `key_set_stable=False` iff any pair of *non-trivial* cohorts (each
# >5% of the corpus, each with >=1000 events in the chosen sample)
# differs by >=2 keys. `too_sparse_to_decide` if no cohort meets the
# 1000-event threshold under any sample strategy.

# %%
def stability_for(et: str) -> dict:
    """Compute key-set stability for one event type across cohorts."""
    cells = {c: v for c, v in authoritative.items() if c[0] == et}
    nt = {
        c[1]: v for c, v in cells.items()
        if c[1] in NON_TRIVIAL_COHORTS and v["n_events"] >= 1000
    }
    if len(nt) == 0:
        return {
            "key_set_stable": "too_sparse_to_decide",
            "non_trivial_cohorts_in_sample": [],
            "unstable_versions": [],
            "key_union_size": None,
            "max_pairwise_diff": None,
            "sample_strategy": "too_sparse",
        }
    cohorts = sorted(nt)
    union: set = set()
    for v in nt.values():
        union |= set(v["keys"])
    max_diff = 0
    unstable_pairs: list = []
    for i in range(len(cohorts)):
        for j in range(i + 1, len(cohorts)):
            c1, c2 = cohorts[i], cohorts[j]
            sym = set(nt[c1]["keys"]) ^ set(nt[c2]["keys"])
            if len(sym) > max_diff:
                max_diff = len(sym)
            if len(sym) >= 2:
                unstable_pairs.append({
                    "a": c1, "b": c2, "sym_diff_size": len(sym),
                    "sym_diff": sorted(sym),
                })
    strat = {v["sample_strategy"] for v in nt.values()}
    if strat == {"pass_a_only"}:
        ss = "pass_a_only"
    elif "pass_b_stratified" in strat:
        ss = "pass_b_stratified"
    else:
        ss = "mixed"
    return {
        "key_set_stable": (max_diff < 2),
        "non_trivial_cohorts_in_sample": cohorts,
        "unstable_versions": unstable_pairs,
        "key_union_size": len(union),
        "max_pairwise_diff": max_diff,
        "sample_strategy": ss,
    }


# %%
v4_per_event: dict = {}
for et in event_types_observed:
    cov = year_coverage_summary[et]
    stab = stability_for(et)
    v4_per_event[et] = {
        "coverage_stable": cov["coverage_stable_by_year"],
        "min_year_coverage": cov["min_year_coverage"],
        "max_year_coverage": cov["max_year_coverage"],
        "coverage_spread": cov["coverage_spread"],
        "coverage_relative_spread": cov["coverage_relative_spread"],
        "years_present": cov["years_present"],
        "years_absent": cov["years_absent"],
        "stability_basis": cov["stability_basis"],
        "coverage_caveat": cov["coverage_caveat"],
        "key_set_stable": stab["key_set_stable"],
        "non_trivial_cohorts_in_sample":
            stab["non_trivial_cohorts_in_sample"],
        "unstable_versions": stab["unstable_versions"],
        "key_union_size": stab["key_union_size"],
        "max_pairwise_diff": stab["max_pairwise_diff"],
        "sample_strategy": stab["sample_strategy"],
        "feature_eligibility_caveat": cov["feature_eligibility_caveat"],
        "caveat": None,
    }
    if stab["key_set_stable"] == "too_sparse_to_decide":
        v4_per_event[et]["caveat"] = (
            "rare-family safeguard (Amendment 6): no cohort reached "
            "1000-event threshold under Pass A or Pass B"
        )
print("=== V4 per-event verdict ===")
for et in event_types_observed:
    v = v4_per_event[et]
    print(
        f"  {et}: cov_stable={v['coverage_stable']}, "
        f"key_stable={v['key_set_stable']}, "
        f"sample={v['sample_strategy']}, "
        f"max_diff={v['max_pairwise_diff']}"
    )

# %% [markdown]
# ### V4 verdict assembly + result
#
# Result discipline (per T06 step 6): one sparse event family does NOT
# fail V4 unless it blocks ALL planned tracker-derived feature families.
# A `too_sparse_to_decide` rare family is recorded but does not invert
# `result` to FAIL.

# %%
stable_events = [
    et for et in event_types_observed
    if v4_per_event[et]["coverage_stable"] is True
    and v4_per_event[et]["key_set_stable"] is True
]
unstable_events = [
    et for et in event_types_observed
    if v4_per_event[et]["coverage_stable"] is False
    or v4_per_event[et]["key_set_stable"] is False
]
sparse_events = [
    et for et in event_types_observed
    if v4_per_event[et]["coverage_stable"] == "too_sparse_to_decide"
    or v4_per_event[et]["key_set_stable"] == "too_sparse_to_decide"
]
caveated_events = [
    et for et in event_types_observed
    if v4_per_event[et]["feature_eligibility_caveat"] is not None
    or v4_per_event[et]["coverage_caveat"] is not None
]
all_have_verdicts = all(
    et in v4_per_event for et in event_types_observed
)

if unstable_events:
    v4_result = "PASS_WITH_CAVEAT"
    v4_caveat = (
        f"unstable event families: {unstable_events}; "
        f"stable: {len(stable_events)}; too_sparse: {sparse_events}; "
        f"caveated: {caveated_events}"
    )
elif sparse_events:
    v4_result = "PASS_WITH_CAVEAT"
    v4_caveat = (
        f"all checked families stable; rare-family safeguard kept "
        f"{sparse_events} as too_sparse_to_decide (not failed); "
        f"caveated: {caveated_events}"
    )
elif caveated_events:
    # Sparse / occasionally-absent families pass the spread threshold
    # within their basis, but carry a feature_eligibility caveat for V8.
    # Per T06 hygiene-pass step 3: PASS only if sparse-family caveats
    # provably do not affect planned Phase 02 families. T06 cannot
    # validate Phase 02 plans, so default to PASS_WITH_CAVEAT.
    v4_result = "PASS_WITH_CAVEAT"
    v4_caveat = (
        f"all {len(event_types_observed)} event families stable; "
        f"sparse / occasionally-absent caveats on: {caveated_events}; "
        f"V8 must propagate these as feature_eligibility caveats"
    )
else:
    v4_result = "PASS"
    v4_caveat = (
        f"all {len(event_types_observed)} event families stable "
        f"across years and non-trivial cohorts; no sparse-family caveats"
    )

verdicts["V4"] = {
    "hypothesis": (
        "all 10 tracker event families have stable presence and JSON "
        "key structure across the 2016-2024 SC2EGSet corpus"
    ),
    "falsifier": (
        "any planned-feature family missing/unstable across major "
        "year/gameVersion cohorts; key-set differs >=2 keys between "
        "non-trivial cohorts (>5% each); rare-event under-sampling "
        "blocks decision"
    ),
    "result": v4_result,
    "rare_family_safeguard_applied": True,
    "protocol88500_snapshot_caveat": (
        "T02 used protocol88500.py as a recent reference snapshot only; "
        "V4 stability is empirical across observed corpus, NOT a claim "
        "about all SC2 protocols ever shipped"
    ),
    "cohort_strategy": {
        "n_distinct_gameversion": N_DISTINCT_GAMEVERSION,
        "use_grouped_cohort": USE_GROUPED_COHORT,
        "cohort_label": COHORT_LABEL,
        "cohort_rule": COHORT_RULE,
        "non_trivial_cohorts": NON_TRIVIAL_COHORTS,
        "non_trivial_threshold_pct": 0.05,
    },
    "year_coverage_summary": year_coverage_summary,
    "per_event": v4_per_event,
    "stable_event_types": stable_events,
    "unstable_event_types": unstable_events,
    "too_sparse_event_types": sparse_events,
    "caveated_event_types": caveated_events,
    "v8_carry_forward_caveats": {
        et: v4_per_event[et]["feature_eligibility_caveat"]
        for et in event_types_observed
        if v4_per_event[et]["feature_eligibility_caveat"] is not None
    },
    "all_event_types_have_verdict": all_have_verdicts,
    "notes": v4_caveat,
}
print("=== V4 verdict ===")
print(f"  result: {verdicts['V4']['result']}")
print(f"  stable: {len(stable_events)} -> {stable_events}")
print(f"  unstable: {len(unstable_events)} -> {unstable_events}")
print(f"  too_sparse: {len(sparse_events)} -> {sparse_events}")
print(f"  caveated (V8 carry-forward): {len(caveated_events)} -> "
      f"{caveated_events}")
print(f"  notes: {verdicts['V4']['notes']}")

# %% [markdown]
# ### V4 consistency assertions

# %%
assert all_have_verdicts, (
    f"missing V4 verdict for some event types: "
    f"{set(event_types_observed) - set(v4_per_event)}"
)
assert len(v4_per_event) == 10, (
    f"expected 10 event types, got {len(v4_per_event)}"
)
for et, v in v4_per_event.items():
    assert v["coverage_stable"] in (True, False, "too_sparse_to_decide"), (
        f"{et}: bad coverage_stable={v['coverage_stable']}"
    )
    assert v["key_set_stable"] in (True, False, "too_sparse_to_decide"), (
        f"{et}: bad key_set_stable={v['key_set_stable']}"
    )
    assert v["sample_strategy"] in (
        "pass_a_only", "pass_b_stratified", "mixed", "too_sparse"
    ), f"{et}: bad sample_strategy={v['sample_strategy']}"
print("=== V4 consistency: OK ===")
print(f"  10 event types verdict: stable={len(stable_events)}, "
      f"unstable={len(unstable_events)}, "
      f"too_sparse={len(sparse_events)}")

# %% [markdown]
# ## V4 result summary
#
# - **Per-year coverage:** 9 years (2016-2024). The
#   `v4_1_per_year_coverage` query uses `years CROSS JOIN event_types
#   LEFT JOIN counts` so every `(year, event_type)` cell is materialised
#   even when zero -- absence is visible to the classifier, not silently
#   dropped. Common event families (UnitBorn, UnitDied, UnitTypeChange,
#   PlayerStats, UnitInit, UnitDone, UnitPositions, Upgrade, PlayerSetup)
#   appear at near-100% replay coverage every year (absolute spread
#   <= 5%). **UnitOwnerChange is schema-stable but coverage-sparse:**
#   it is absent in the 2016 slice and appears in roughly one quarter
#   of replays in later years. This supports descriptive stability of
#   the event schema where present, but not robust use as a broadly
#   available feature family without caveats. The classifier records
#   `coverage_caveat` and `feature_eligibility_caveat:
#   sparse_event_family_not_broadly_available` as machine-readable V8
#   carry-forward fields under `verdicts["V4"]["v8_carry_forward_caveats"]`.
# - **Cohort strategy:** 46 distinct `gameVersion` strings -> grouped
#   by `major.minor` prefix (e.g., `5.0`, `4.10`, `4.11`). Non-trivial
#   cohorts are those holding > 5% of replays.
# - **Pass A / Pass B:** 1% Bernoulli sample with `REPEATABLE(42)` for
#   reproducibility. Cells under-sampled in Pass A (< 1000 events in a
#   non-trivial cohort) trigger Pass B stratified resample
#   (`ROW_NUMBER() OVER (PARTITION BY evtTypeName, cohort ORDER BY loop)
#   <= 10000`). Cells still < 1000 after Pass B are
#   `coverage_too_sparse_for_stability_decision`, NOT `unstable`.
# - **Key-set stability:** assessed only for non-trivial cohorts each
#   holding >= 1000 events in the chosen sample. Pairwise symmetric
#   difference >= 2 keys = `key_set_stable=False`.
# - **Carry-forward (T02):** the s2protocol `protocol88500.py` snapshot
#   is a *recent* reference, NOT a proof of historical stability across
#   the 2016-2024 corpus. V4 stability is empirical, sample-confirmed
#   for the corpus actually observed.
# - **V4 verdict:** see printed result above.

# %% [markdown]
# ---
# ## V5 -- Unit-lifecycle event semantics (per Amendment 4)
#
# **Hypothesis.**
# - Unit-lifecycle events (UnitBorn, UnitInit, UnitDone, UnitDied,
#   UnitTypeChange, UnitOwnerChange, UnitPositions) record local state
#   transitions at their event `loop`.
# - Cutoff-based counts (units born by cutoff, completed by cutoff,
#   dead by cutoff) can be computed from event loops without needing
#   any post-game state.
# - For lineage-required event families (UnitDone, UnitTypeChange,
#   UnitPositions) ownership and origin can be resolved through the
#   `(filename, unitTagIndex, unitTagRecycle)` lineage join back to
#   UnitBorn / UnitInit.
#
# **Falsifier.**
# - death / done / type-change occurs before its corresponding birth /
#   init event at material rate;
# - unit-tag recycle handling makes lineage ambiguous at material rate;
# - required lineage keys are missing or unstable;
# - event semantics require future / post-game information;
# - lineage attribution cannot resolve ownership for a planned feature
#   family.
#
# **Per Amendment 4 (carried forward to V5).**
# - `n_survivors` (origin without UnitDied) is descriptive, NOT failure.
# - `n_constructing_survivors` (UnitInit without UnitDone) is NOT
#   failure if the game ends before completion.
# - `n_inverted` = impossible ordering: died_loop < origin_loop OR
#   done_loop < init_loop. MUST be 0 (or near-zero with documented
#   explanation).
# - `n_died_without_prior_origin` is NOT automatic failure (map units
#   like MineralField / VespeneGeyser / WatchTower exist by map editor
#   placement, not by UnitBorn / UnitInit -- they die when mined or
#   destroyed).
#
# **Per V4 carry-forward.** `UnitOwnerChange` is schema-stable but
# coverage-sparse (absent in 2016, ~25% of replays in later years);
# `feature_eligibility_caveat = sparse_event_family_not_broadly_available`
# is propagated. T07 must NOT over-promote UnitOwnerChange-derived
# features merely because key-set diff is zero.

# %% [markdown]
# ### V5.1 -- lifecycle key availability per event family
#
# Joins use `(filename, unitTagIndex, unitTagRecycle)`. UnitPositions
# uses a different scheme (`firstUnitIndex` + packed `items` array)
# and is handled separately in V5.6.

# %%
LIFECYCLE_EVENT_TYPES = [
    "UnitBorn", "UnitInit", "UnitDone", "UnitDied",
    "UnitTypeChange", "UnitOwnerChange",
]
v5_1_df = run_q(
    "v5_1_lifecycle_key_availability",
    f"""
    SELECT evtTypeName,
           COUNT(*) AS n_total,
           COUNT(*) FILTER (
               WHERE json_extract_string(event_data, '$.unitTagIndex')
                     IS NULL
           ) AS n_null_uti,
           COUNT(*) FILTER (
               WHERE json_extract_string(event_data, '$.unitTagRecycle')
                     IS NULL
           ) AS n_null_utr
    FROM tracker_events_raw
    WHERE evtTypeName IN ({", ".join(f"'{e}'" for e in LIFECYCLE_EVENT_TYPES)})
    GROUP BY evtTypeName
    ORDER BY evtTypeName
    """,
)
v5_1_df["null_uti_rate"] = v5_1_df["n_null_uti"] / v5_1_df["n_total"]
v5_1_df["null_utr_rate"] = v5_1_df["n_null_utr"] / v5_1_df["n_total"]
print("=== V5.1 lifecycle key availability ===")
print(v5_1_df.to_string(index=False))
key_availability = {
    r["evtTypeName"]: {
        "n_total": int(r["n_total"]),
        "null_uti_rate": float(r["null_uti_rate"]),
        "null_utr_rate": float(r["null_utr_rate"]),
        "lineage_keys_available": (
            r["null_uti_rate"] < 0.001 and r["null_utr_rate"] < 0.001
        ),
    }
    for _, r in v5_1_df.iterrows()
}

# %% [markdown]
# ### V5.2 -- origin lineage base table (UnitBorn UNION UnitInit)
#
# Each unit identity = `(filename, unitTagIndex, unitTagRecycle)`.
# `first_origin_loop` = MIN(loop) over UnitBorn / UnitInit. Per-identity
# counts of Born vs Init events let us classify the origin source
# (born-only / init-only / both) and surface duplicate-origin
# identities.

# %%
v5_2_df = run_q(
    "v5_2_origin_lineage_summary",
    """
    WITH origins AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                        AS INT) AS uti,
               TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                        AS INT) AS utr,
               evtTypeName, loop
        FROM tracker_events_raw
        WHERE evtTypeName IN ('UnitBorn', 'UnitInit')
    ),
    per_identity AS (
        SELECT filename, uti, utr,
               MIN(loop) AS first_origin_loop,
               SUM(CASE WHEN evtTypeName='UnitBorn' THEN 1 ELSE 0 END)
                   AS n_born_events,
               SUM(CASE WHEN evtTypeName='UnitInit' THEN 1 ELSE 0 END)
                   AS n_init_events
        FROM origins GROUP BY filename, uti, utr
    )
    SELECT
        COUNT(*) AS n_origin_identities,
        SUM(CASE WHEN n_born_events > 0 AND n_init_events = 0
                 THEN 1 ELSE 0 END) AS n_born_only,
        SUM(CASE WHEN n_init_events > 0 AND n_born_events = 0
                 THEN 1 ELSE 0 END) AS n_init_only,
        SUM(CASE WHEN n_born_events > 0 AND n_init_events > 0
                 THEN 1 ELSE 0 END) AS n_both,
        SUM(CASE WHEN n_born_events > 1 OR n_init_events > 1
                 THEN 1 ELSE 0 END) AS n_duplicate_origin
    FROM per_identity
    """,
)
print("=== V5.2 origin lineage base ===")
print(v5_2_df.to_string(index=False))
origin_summary = {k: int(v5_2_df[k].iloc[0]) for k in v5_2_df.columns}

# %% [markdown]
# ### V5.3 -- UnitBorn / UnitInit -> UnitDied ordering audit
#
# Per Amendment 4: `n_survivors` is descriptive (NOT failure).
# `n_died_without_prior_origin` is NOT automatic failure -- the cause
# is not classified by T07; possible origins include pre-existing map
# units, missing origin events, parser omissions, and genuine
# ambiguity. The notebook reports the count but does not assert a
# specific mechanism without source evidence.
# `n_inverted` (died_loop < first_origin_loop) MUST be 0.
# `n_same_loop_origin_death` (died_loop == first_origin_loop) is
# empirically common but its exact mechanics are NOT interpreted here;
# this is NOT an inverted ordering (`died_loop < first_origin_loop` is
# the impossible case) and it does not falsify cutoff-count semantics.

# %%
v5_3_df = run_q(
    "v5_3_lifecycle_ordering_audit",
    """
    WITH origins AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                        AS INT) AS uti,
               TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                        AS INT) AS utr,
               MIN(loop) AS first_origin_loop
        FROM tracker_events_raw
        WHERE evtTypeName IN ('UnitBorn', 'UnitInit')
        GROUP BY filename,
                 TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                          AS INT),
                 TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                          AS INT)
    ),
    deaths AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                        AS INT) AS uti,
               TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                        AS INT) AS utr,
               MIN(loop) AS died_loop
        FROM tracker_events_raw
        WHERE evtTypeName = 'UnitDied'
        GROUP BY filename,
                 TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                          AS INT),
                 TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                          AS INT)
    ),
    joined AS (
        SELECT COALESCE(o.filename, d.filename) AS filename,
               o.first_origin_loop, d.died_loop
        FROM origins o
        FULL OUTER JOIN deaths d USING (filename, uti, utr)
    )
    SELECT
        COUNT(*) FILTER (WHERE first_origin_loop IS NOT NULL) AS n_origins,
        COUNT(*) FILTER (WHERE died_loop IS NOT NULL) AS n_died,
        COUNT(*) FILTER (
            WHERE died_loop IS NOT NULL AND first_origin_loop IS NOT NULL
        ) AS n_died_with_prior_origin,
        COUNT(*) FILTER (
            WHERE died_loop IS NOT NULL AND first_origin_loop IS NULL
        ) AS n_died_without_prior_origin,
        COUNT(*) FILTER (
            WHERE first_origin_loop IS NOT NULL AND died_loop IS NULL
        ) AS n_survivors,
        COUNT(*) FILTER (
            WHERE first_origin_loop IS NOT NULL
              AND died_loop IS NOT NULL
              AND died_loop < first_origin_loop
        ) AS n_inverted,
        COUNT(*) FILTER (
            WHERE first_origin_loop IS NOT NULL
              AND died_loop IS NOT NULL
              AND died_loop = first_origin_loop
        ) AS n_same_loop_origin_death
    FROM joined
    """,
)
print("=== V5.3 origin -> death ordering ===")
print(v5_3_df.to_string(index=False))
ordering = {k: int(v5_3_df[k].iloc[0]) for k in v5_3_df.columns}

# %% [markdown]
# ### V5.4 -- UnitInit -> UnitDone construction audit
#
# Per Amendment 4: `n_constructing_survivors` is NOT failure if the
# game ends before construction completes. `n_done_before_init` MUST
# be 0 (or near-zero with explanation). `n_done_without_init` may be
# caveated -- some structures fire UnitDone without a prior UnitInit
# in some s2protocol versions (e.g., warpgate units).

# %%
v5_4_df = run_q(
    "v5_4_construction_audit",
    """
    WITH inits AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                        AS INT) AS uti,
               TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                        AS INT) AS utr,
               MIN(loop) AS init_loop
        FROM tracker_events_raw
        WHERE evtTypeName = 'UnitInit'
        GROUP BY filename,
                 TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                          AS INT),
                 TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                          AS INT)
    ),
    dones AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                        AS INT) AS uti,
               TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                        AS INT) AS utr,
               MIN(loop) AS done_loop
        FROM tracker_events_raw
        WHERE evtTypeName = 'UnitDone'
        GROUP BY filename,
                 TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                          AS INT),
                 TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                          AS INT)
    ),
    joined AS (
        SELECT i.init_loop, d.done_loop
        FROM inits i
        FULL OUTER JOIN dones d USING (filename, uti, utr)
    )
    SELECT
        COUNT(*) FILTER (WHERE init_loop IS NOT NULL) AS n_init,
        COUNT(*) FILTER (WHERE done_loop IS NOT NULL) AS n_done,
        COUNT(*) FILTER (
            WHERE init_loop IS NOT NULL AND done_loop IS NOT NULL
        ) AS n_done_with_init,
        COUNT(*) FILTER (
            WHERE done_loop IS NOT NULL AND init_loop IS NULL
        ) AS n_done_without_init,
        COUNT(*) FILTER (
            WHERE init_loop IS NOT NULL AND done_loop IS NULL
        ) AS n_constructing_survivors,
        COUNT(*) FILTER (
            WHERE init_loop IS NOT NULL AND done_loop IS NOT NULL
              AND done_loop < init_loop
        ) AS n_done_before_init
    FROM joined
    """,
)
print("=== V5.4 init -> done construction ===")
print(v5_4_df.to_string(index=False))
construction = {k: int(v5_4_df[k].iloc[0]) for k in v5_4_df.columns}

# %% [markdown]
# ### V5.5 -- UnitTypeChange attribution
#
# UnitTypeChange has no direct player-id field; it must be lineage-
# attributed via `(filename, uti, utr)` to a prior UnitBorn / UnitInit
# origin. Reports attribution success rate and inverted ordering.

# %%
v5_5_df = run_q(
    "v5_5_unit_type_change_attribution",
    """
    WITH origins AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                        AS INT) AS uti,
               TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                        AS INT) AS utr,
               MIN(loop) AS first_origin_loop
        FROM tracker_events_raw
        WHERE evtTypeName IN ('UnitBorn', 'UnitInit')
        GROUP BY filename,
                 TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                          AS INT),
                 TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                          AS INT)
    ),
    type_changes AS (
        SELECT filename,
               TRY_CAST(json_extract_string(event_data, '$.unitTagIndex')
                        AS INT) AS uti,
               TRY_CAST(json_extract_string(event_data, '$.unitTagRecycle')
                        AS INT) AS utr,
               loop AS type_change_loop
        FROM tracker_events_raw WHERE evtTypeName = 'UnitTypeChange'
    )
    SELECT
        COUNT(*) AS n_total,
        COUNT(*) FILTER (WHERE o.first_origin_loop IS NOT NULL)
            AS n_attributed,
        COUNT(*) FILTER (WHERE o.first_origin_loop IS NULL)
            AS n_unattributed,
        COUNT(*) FILTER (
            WHERE o.first_origin_loop IS NOT NULL
              AND tc.type_change_loop < o.first_origin_loop
        ) AS n_inverted
    FROM type_changes tc
    LEFT JOIN origins o USING (filename, uti, utr)
    """,
)
print("=== V5.5 UnitTypeChange attribution ===")
print(v5_5_df.to_string(index=False))
type_change_attr = {k: int(v5_5_df[k].iloc[0]) for k in v5_5_df.columns}
type_change_attr["attribution_success_rate"] = (
    type_change_attr["n_attributed"] / type_change_attr["n_total"]
    if type_change_attr["n_total"] else None
)

# %% [markdown]
# ### V5.6 -- UnitPositions structure inspection
#
# UnitPositions has no direct lineage keys -- it carries `firstUnitIndex`
# (BIGINT) and `items` (packed array of unit ids and coordinates).
# Owner attribution requires unpacking `items` and joining back to
# UnitBorn / UnitInit lineage. T07 inspects whether the structure is
# accessible via SQL and classifies attribution feasibility for V8.
# Coordinate semantics (units, origin, bounds) are V6 / T08, NOT here.

# %%
v5_6_df = run_q(
    "v5_6_unit_positions_structure",
    """
    SELECT
        COUNT(*) AS n_total,
        COUNT(*) FILTER (
            WHERE json_extract(event_data, '$.firstUnitIndex') IS NOT NULL
        ) AS n_with_first_index,
        COUNT(*) FILTER (
            WHERE json_extract(event_data, '$.items') IS NOT NULL
        ) AS n_with_items,
        AVG(json_array_length(json_extract(event_data, '$.items')))
            AS mean_items_array_length,
        MAX(json_array_length(json_extract(event_data, '$.items')))
            AS max_items_array_length
    FROM tracker_events_raw WHERE evtTypeName = 'UnitPositions'
    """,
)
print("=== V5.6 UnitPositions structure ===")
print(v5_6_df.to_string(index=False))
positions_struct = {k: v5_6_df[k].iloc[0] for k in v5_6_df.columns}

# %% [markdown]
# ### V5.7 -- UnitOwnerChange caveat (V4 carry-forward)
#
# V4 verdict already classifies `UnitOwnerChange` with
# `feature_eligibility_caveat = sparse_event_family_not_broadly_available`
# (absent in 2016, ~25% of replays in later years). V5 confirms
# schema availability but propagates the V4 caveat. Basic unit
# birth/death counts using *origin owner* (UnitBorn.controlPlayerId)
# are NOT affected, because they do not require dynamic ownership
# updates.

# %%
unit_owner_change_caveat = {
    "schema_keys_available_per_v51":
        key_availability.get("UnitOwnerChange", {})
        .get("lineage_keys_available", False),
    "v4_feature_eligibility_caveat": (
        verdicts["V4"]["v8_carry_forward_caveats"]
        .get("UnitOwnerChange")
    ),
    "v4_years_absent": (
        verdicts["V4"]["per_event"]["UnitOwnerChange"]["years_absent"]
    ),
    "v4_min_year_coverage": (
        verdicts["V4"]["per_event"]["UnitOwnerChange"]["min_year_coverage"]
    ),
    "impact_on_basic_origin_owner_features":
        "none -- UnitBorn.controlPlayerId is the origin owner",
    "impact_on_dynamic_ownership_features":
        "blocked_until_additional_validation -- UnitOwnerChange is the "
        "only source of mid-game ownership updates and is sparse",
}
print("=== V5.7 UnitOwnerChange caveat ===")
for k, v in unit_owner_change_caveat.items():
    print(f"  {k}: {v}")

# %% [markdown]
# ### V5.8 -- Upgrade event count semantics
#
# Upgrade has high-confidence direct mapping per V2 (playerId).
# `count` field semantics (per-event level vs cumulative) are NOT
# documented in the s2protocol snapshot. V5 reports the empirical
# distribution; V8 should use *event occurrence counts* (COUNT(*)
# per (filename, playerId)), NOT trust `count` as a cumulative tally.

# %%
v5_8_df = run_q(
    "v5_8_upgrade_count_semantics",
    """
    SELECT
        TRY_CAST(json_extract_string(event_data, '$.count') AS INT) AS cnt,
        COUNT(*) AS n
    FROM tracker_events_raw WHERE evtTypeName = 'Upgrade'
    GROUP BY cnt ORDER BY n DESC LIMIT 10
    """,
)
print("=== V5.8 Upgrade count field distribution (top 10) ===")
print(v5_8_df.to_string(index=False))
upgrade_count_semantics = {
    "count_field_distribution_top_10": [
        {"count": (int(r["cnt"]) if r["cnt"] is not None else None),
         "n": int(r["n"])}
        for _, r in v5_8_df.iterrows()
    ],
    "policy": (
        "V8 must use COUNT(*) per (filename, playerId) for upgrade "
        "occurrence features. The 'count' field is NOT trusted as a "
        "cumulative tally without source confirmation (s2protocol "
        "snapshot does not document its semantics)."
    ),
    "feature_eligibility": "occurrence_count_safe; count_field_unverified",
}

# %% [markdown]
# ### V5 verdict assembly
#
# Per-event-family verdict + V5 result. Result discipline (per T07
# brief): one caveat does NOT fail V5 -- only impossible orderings
# (`n_inverted > 0`) or missing lineage keys at material rate fail.

# %%
ordering_pass = (
    ordering["n_inverted"] == 0 and
    construction["n_done_before_init"] == 0
)
type_change_pass = (
    type_change_attr["attribution_success_rate"] is not None and
    type_change_attr["attribution_success_rate"] >= 0.99 and
    type_change_attr["n_inverted"] == 0
)
positions_attribution_decoded = False  # requires items unpacking; deferred

_BASIC_SCOPE = (
    "basic cutoff-count features only (e.g., units born by cutoff "
    "loop); complex derived features may still require V8 family-"
    "specific eligibility and Phase 02 feature-contract review"
)
_OCCURRENCE_SCOPE = (
    "event-occurrence count only (COUNT(*) per (filename, playerId)); "
    "the count field is NOT trusted as a cumulative tally without "
    "source confirmation"
)
event_family_verdicts = {
    "UnitBorn": {
        "lineage_keys_available":
            key_availability["UnitBorn"]["lineage_keys_available"],
        "cutoff_count_safe": True,
        "feature_eligibility": "eligible_for_phase02_now",
        "eligibility_scope": _BASIC_SCOPE,
        "notes": "origin event with direct controlPlayerId",
    },
    "UnitInit": {
        "lineage_keys_available":
            key_availability["UnitInit"]["lineage_keys_available"],
        "cutoff_count_safe": True,
        "feature_eligibility": "eligible_for_phase02_now",
        "eligibility_scope": _BASIC_SCOPE,
        "notes": "construction-start event with direct controlPlayerId",
    },
    "UnitDone": {
        "lineage_keys_available":
            key_availability["UnitDone"]["lineage_keys_available"],
        "cutoff_count_safe": True,
        "feature_eligibility": (
            "eligible_for_phase02_now"
            if construction["n_done_before_init"] == 0
            and construction["n_done_without_init"]
                / max(construction["n_done"], 1) < 0.05
            else "eligible_with_caveat"
        ),
        "eligibility_scope": _BASIC_SCOPE,
        "notes": (
            f"done_without_init = {construction['n_done_without_init']} "
            f"of {construction['n_done']}; lineage via UnitInit"
        ),
    },
    "UnitDied": {
        "lineage_keys_available":
            key_availability["UnitDied"]["lineage_keys_available"],
        "cutoff_count_safe": True,
        "feature_eligibility": (
            "eligible_for_phase02_now" if ordering_pass
            else "blocked_until_additional_validation"
        ),
        "eligibility_scope": _BASIC_SCOPE,
        "notes": (
            f"survivors={ordering['n_survivors']} (descriptive); "
            f"orphan deaths={ordering['n_died_without_prior_origin']} "
            "(cause not classified; possible origins: map units, "
            "missing events, parser edge cases); inverted="
            f"{ordering['n_inverted']} (must be 0); "
            f"same_loop={ordering['n_same_loop_origin_death']} "
            "(empirically common, mechanics not interpreted; not "
            "inverted)"
        ),
    },
    "UnitTypeChange": {
        "lineage_keys_available":
            key_availability["UnitTypeChange"]["lineage_keys_available"],
        "cutoff_count_safe": True,
        "feature_eligibility": (
            "eligible_for_phase02_now" if type_change_pass
            else "eligible_with_caveat"
        ),
        "eligibility_scope": _BASIC_SCOPE,
        "notes": (
            f"attribution_rate={type_change_attr['attribution_success_rate']:.4f}"
            f"; inverted={type_change_attr['n_inverted']}"
        ),
    },
    "UnitOwnerChange": {
        "lineage_keys_available":
            key_availability["UnitOwnerChange"]["lineage_keys_available"],
        "cutoff_count_safe": True,
        "feature_eligibility":
            "blocked_until_additional_validation",
        "eligibility_scope": (
            "owner-attributed features blocked because UnitOwnerChange "
            "is sparse per V4; basic origin-owner features (using "
            "UnitBorn.controlPlayerId) are not affected"
        ),
        "notes": (
            "schema OK but V4 sparse caveat propagates; dynamic "
            "ownership features blocked"
        ),
    },
    "UnitPositions": {
        "lineage_keys_available": False,
        "cutoff_count_safe": "requires_unpacking",
        "feature_eligibility":
            "blocked_until_additional_validation",
        "eligibility_scope": (
            "owner-attributed features blocked because items "
            "unpacking + UnitBorn lineage attribution is unresolved "
            "in T07; coordinate semantics are V6 / T08"
        ),
        "notes": (
            "uses firstUnitIndex + packed items; owner attribution "
            "requires items unpacking + UnitBorn lineage; coordinate "
            "semantics are V6 / T08"
        ),
    },
    "Upgrade": {
        "lineage_keys_available": True,
        "cutoff_count_safe": True,
        "feature_eligibility":
            "eligible_with_caveat (occurrence-count only)",
        "eligibility_scope": _OCCURRENCE_SCOPE,
        "notes": (
            "direct playerId mapping per V2; count field unverified"
        ),
    },
}

if not ordering_pass:
    v5_result = "FAIL"
    v5_caveat = (
        f"impossible orderings: n_inverted={ordering['n_inverted']}, "
        f"n_done_before_init={construction['n_done_before_init']}"
    )
else:
    blocked = [
        et for et, v in event_family_verdicts.items()
        if v["feature_eligibility"]
        == "blocked_until_additional_validation"
    ]
    caveated = [
        et for et, v in event_family_verdicts.items()
        if v["feature_eligibility"]
        in ("eligible_with_caveat",
            "eligible_with_caveat (occurrence-count only)")
    ]
    if blocked:
        v5_result = "PASS_WITH_CAVEAT"
        v5_caveat = (
            f"ordering OK; blocked: {blocked}; caveated: {caveated}"
        )
    elif caveated:
        v5_result = "PASS_WITH_CAVEAT"
        v5_caveat = (
            f"ordering OK; caveated families: {caveated}"
        )
    else:
        v5_result = "PASS"
        v5_caveat = "all lifecycle families eligible"

verdicts["V5"] = {
    "hypothesis": (
        "lifecycle events record local state transitions at their loop; "
        "cutoff counts are computable without post-game leakage; "
        "lineage joins resolve owner for no-direct-id event families"
    ),
    "falsifier": (
        "death/done/type-change before origin at material rate; "
        "lineage ambiguity from tag-recycle; missing/unstable keys; "
        "future-dependent semantics; lineage cannot resolve owner "
        "for a planned feature family"
    ),
    "result": v5_result,
    "amendment_4_compliance": True,
    "lifecycle_key_availability": key_availability,
    "origin_lineage_summary": origin_summary,
    "lifecycle_ordering_summary": ordering,
    "construction_audit_summary": construction,
    "type_change_attribution": type_change_attr,
    "unit_positions_structure": {
        k: (int(v) if v is not None and not isinstance(v, str) else v)
        for k, v in positions_struct.items()
    },
    "unit_owner_change_caveat": unit_owner_change_caveat,
    "upgrade_count_semantics": upgrade_count_semantics,
    "event_family_verdicts": event_family_verdicts,
    "blocked_or_caveated_families": [
        et for et, v in event_family_verdicts.items()
        if v["feature_eligibility"] != "eligible_for_phase02_now"
    ],
    "notes_for_V8": (
        "Use UnitBorn.controlPlayerId as origin owner. Avoid dynamic "
        "ownership features (require UnitOwnerChange, sparse). "
        "UnitPositions owner attribution needs items-unpacking before "
        "use. Upgrade features must use COUNT(*), not the count field. "
        "Cutoff-based counts on UnitBorn/UnitInit/UnitDone/UnitDied "
        "are safe because every event records local state at its loop."
    ),
    "notes": v5_caveat,
}
print("=== V5 verdict ===")
print(f"  result: {verdicts['V5']['result']}")
print(f"  ordering pass: {ordering_pass}")
print(f"  blocked/caveated: {verdicts['V5']['blocked_or_caveated_families']}")
print(f"  notes: {verdicts['V5']['notes']}")

# %% [markdown]
# ### V5 consistency assertions

# %%
assert ordering["n_inverted"] == 0, (
    f"impossible ordering: n_inverted = {ordering['n_inverted']}"
)
# Cell-level allowances: tag-recycle artefacts can produce a small
# number of done_before_init entries; we surface that as a caveat
# rather than a hard failure (the .005 ceiling is a sanity bound).
done_before_init_rate = (
    construction["n_done_before_init"] / max(construction["n_done"], 1)
)
assert done_before_init_rate < 0.005, (
    f"done_before_init rate {done_before_init_rate:.6f} exceeds 0.5%"
)
assert ordering["n_survivors"] >= 0, "survivors negative??"
assert "UnitOwnerChange" in event_family_verdicts, (
    "UnitOwnerChange must have a V5 verdict (carry-forward V4 caveat)"
)
v5_lineage_required = ["UnitDone", "UnitTypeChange", "UnitPositions"]
for et in v5_lineage_required:
    assert et in event_family_verdicts, f"missing V5 verdict for {et}"
print("=== V5 consistency: OK ===")
print(f"  n_inverted=0; survivors descriptive; "
      f"{len(event_family_verdicts)} event families have V5 verdicts")

# %% [markdown]
# ## V5 result summary
#
# - **Lifecycle keys** (V5.1): `unitTagIndex` and `unitTagRecycle`
#   are present at near-zero null rate for all 6 direct-keyed
#   lifecycle event types (UnitBorn, UnitInit, UnitDone, UnitDied,
#   UnitTypeChange, UnitOwnerChange). UnitPositions is structurally
#   different (`firstUnitIndex` + packed `items`).
# - **Origin lineage** (V5.2): every distinct
#   `(filename, unitTagIndex, unitTagRecycle)` resolves to a single
#   `first_origin_loop` from UnitBorn ∪ UnitInit. Born/init split and
#   duplicate-origin counts recorded for audit.
# - **Lifecycle ordering** (V5.3, per Amendment 4):
#   - `n_survivors` -- descriptive, NOT failure (units alive at game
#     end);
#   - `n_died_without_prior_origin` -- cause is NOT classified by T07;
#     possible origins include pre-existing map units, missing origin
#     events, parser omissions, and genuine ambiguity. The notebook
#     reports the count but does not assert a specific mechanism
#     without source evidence. NOT failure.
#   - `n_inverted` (died_loop < first_origin_loop) -- MUST be 0;
#     verified by assertion above.
#   - `n_same_loop_origin_death` (died_loop == first_origin_loop) --
#     empirically common; the exact mechanics are NOT interpreted
#     here. This is NOT an inverted ordering and does not falsify
#     cutoff-count semantics.
# - **Eligibility scope** -- where event_family_verdicts records
#   `eligible_for_phase02_now`, the scope is *basic cutoff-count
#   features only* (e.g., units born by cutoff loop). Complex derived
#   features (per-unit lifecycle reconstructions, owner re-attribution,
#   coordinate-derived metrics) are NOT covered by this verdict and
#   may still require V8 family-specific eligibility and Phase 02
#   feature-contract review. The scope is recorded per family in
#   `event_family_verdicts[*]["eligibility_scope"]`.
# - **Construction audit** (V5.4, per Amendment 4):
#   `n_constructing_survivors` (Init without Done) is NOT failure if
#   the game ended mid-construction. `n_done_before_init` rate must
#   be < 0.5% (rare tag-recycle artefacts allowed).
# - **UnitTypeChange attribution** (V5.5): >=99% attribution rate via
#   `(filename, uti, utr)` lineage to UnitBorn / UnitInit. Inverted
#   ordering must be 0.
# - **UnitDone**: lineage via UnitInit; `n_done_without_init` rate
#   recorded, classified `eligible_with_caveat` if non-trivial.
# - **UnitPositions** (V5.6): structure is accessible (`firstUnitIndex`
#   + `items` array length). Owner attribution requires Python-side
#   unpacking of `items`, NOT done in T07. Classified
#   `blocked_until_additional_validation` for V8 owner-attributed
#   features. Coordinate semantics are V6 / T08.
# - **UnitOwnerChange** (V5.7): schema OK; V4 sparse caveat
#   (`sparse_event_family_not_broadly_available`) propagated. Basic
#   origin-owner features (UnitBorn.controlPlayerId) are NOT
#   affected. Dynamic-ownership features
#   `blocked_until_additional_validation`.
# - **Upgrade** (V5.8): direct playerId mapping per V2; the `count`
#   field is NOT trusted as cumulative without source confirmation;
#   V8 must use `COUNT(*)` per `(filename, playerId)` for upgrade
#   occurrence features.
# - **V5 verdict:** see printed result above.

# %% [markdown]
# ---
# ## V6 -- Coordinate semantics (descriptive only per Q4 + Amendment 5)
#
# **Hypothesis.** Coordinate fields on tracker events are local
# observations that can be used descriptively if their units (cell vs
# sub-cell vs fixed-point), origin (top-left vs map-center), and the
# observed map bounds are mutually consistent.
#
# **Falsifier.**
# - coordinate units / origin cannot be source-confirmed AND empirical
#   bounds are inconsistent with any plausible interpretation;
# - material out-of-bounds rate without an explainable convention;
# - `UnitPositions.items` packed encoding cannot be decoded safely;
# - coordinate features would require future / post-game information.
#
# **Per Q4 + Amendment 5 (carried forward to V6).**
# - Coordinate validation is *descriptive only*. Out-of-bounds rates
#   are reported but NOT called "parser bugs" without source evidence.
# - `source_confirmed_units` and `source_confirmed_origin` are
#   recorded per family. Per T02 EVIDENCE V6, BOTH are False for
#   SC2EGSet today (s2protocol README + protocol88500.py do not
#   explicitly state cell-vs-sub-cell-vs-fixed-point and origin
#   convention for SC2 tracker events). Therefore NO coordinate
#   family can be `eligible_for_phase02_now` in V6, regardless of
#   empirical in-bounds rate.
# - `UnitPositions` remains blocked or caveated unless items unpacking
#   is non-trivially validated.

# %% [markdown]
# ### V6.1 -- map bounds extraction + cleanliness check

# %%
v6_1_df = run_q(
    "v6_1_map_bounds",
    """
    SELECT
        COUNT(*) AS n_replays,
        COUNT(*) FILTER (
            WHERE initData.gameDescription.mapSizeX IS NULL
        ) AS n_null_msx,
        COUNT(*) FILTER (
            WHERE initData.gameDescription.mapSizeY IS NULL
        ) AS n_null_msy,
        COUNT(*) FILTER (
            WHERE initData.gameDescription.mapSizeX <= 0
        ) AS n_degenerate_msx,
        COUNT(*) FILTER (
            WHERE initData.gameDescription.mapSizeY <= 0
        ) AS n_degenerate_msy,
        MIN(initData.gameDescription.mapSizeX) AS min_msx,
        MAX(initData.gameDescription.mapSizeX) AS max_msx,
        MIN(initData.gameDescription.mapSizeY) AS min_msy,
        MAX(initData.gameDescription.mapSizeY) AS max_msy
    FROM replays_meta_raw
    """,
)
print("=== V6.1 map bounds availability ===")
print(v6_1_df.to_string(index=False))
bounds_summary = {k: int(v6_1_df[k].iloc[0]) for k in v6_1_df.columns}
n_replays_clean_bounds = (
    bounds_summary["n_replays"]
    - bounds_summary["n_degenerate_msx"]
    - bounds_summary["n_degenerate_msy"]
)
bounds_summary["n_replays_with_clean_bounds"] = n_replays_clean_bounds
bounds_summary["clean_bounds_rate"] = (
    n_replays_clean_bounds / bounds_summary["n_replays"]
    if bounds_summary["n_replays"] else 0.0
)
print(f"\nclean-bounds replay count = {n_replays_clean_bounds}; "
      f"rate = {bounds_summary['clean_bounds_rate']:.6f}")

# %% [markdown]
# ### V6.2 -- coordinate availability per event family
#
# Direct `x` / `y` coordinate fields exist on UnitBorn / UnitInit /
# UnitDied per V5.1 schema recon. UnitPositions uses a different
# packed scheme (V6.4). All other lifecycle event types have no
# direct coordinate fields.

# %%
DIRECT_COORD_EVENTS = ["UnitBorn", "UnitInit", "UnitDied"]
v6_2_df = run_q(
    "v6_2_direct_coord_availability",
    f"""
    SELECT evtTypeName,
           COUNT(*) AS n_total,
           COUNT(*) FILTER (
               WHERE json_extract_string(event_data, '$.x') IS NULL
           ) AS n_null_x,
           COUNT(*) FILTER (
               WHERE json_extract_string(event_data, '$.y') IS NULL
           ) AS n_null_y,
           MIN(TRY_CAST(json_extract_string(event_data, '$.x')
                        AS INT)) AS min_x,
           MAX(TRY_CAST(json_extract_string(event_data, '$.x')
                        AS INT)) AS max_x,
           MIN(TRY_CAST(json_extract_string(event_data, '$.y')
                        AS INT)) AS min_y,
           MAX(TRY_CAST(json_extract_string(event_data, '$.y')
                        AS INT)) AS max_y
    FROM tracker_events_raw
    WHERE evtTypeName IN ({", ".join(f"'{e}'" for e in DIRECT_COORD_EVENTS)})
    GROUP BY evtTypeName
    ORDER BY evtTypeName
    """,
)
print("=== V6.2 direct-coord event availability ===")
print(v6_2_df.to_string(index=False))

# %% [markdown]
# ### V6.3 -- in-bounds rate per direct-coord event family
#
# Joins event x/y to `replays_meta_raw.initData.gameDescription.
# mapSizeX/mapSizeY` and computes the rate at which raw integer
# coordinates fall in `[0, mapSizeX-1] x [0, mapSizeY-1]`. Replays
# with degenerate bounds (msx<=0 or msy<=0) are excluded. The "raw"
# interpretation is tested empirically; a "scaled" interpretation
# is NOT chosen without source evidence.

# %%
v6_3_df = run_q(
    "v6_3_in_bounds_rate",
    f"""
    WITH bounds AS (
        SELECT filename,
               initData.gameDescription.mapSizeX AS msx,
               initData.gameDescription.mapSizeY AS msy
        FROM replays_meta_raw
        WHERE initData.gameDescription.mapSizeX > 0
          AND initData.gameDescription.mapSizeY > 0
    ),
    coords AS (
        SELECT te.evtTypeName, te.filename,
               TRY_CAST(json_extract_string(te.event_data, '$.x') AS INT)
                   AS x,
               TRY_CAST(json_extract_string(te.event_data, '$.y') AS INT)
                   AS y
        FROM tracker_events_raw te
        WHERE te.evtTypeName IN
            ({", ".join(f"'{e}'" for e in DIRECT_COORD_EVENTS)})
    ),
    joined AS (
        SELECT c.evtTypeName, c.x, c.y, b.msx, b.msy
        FROM coords c JOIN bounds b USING (filename)
    )
    SELECT evtTypeName,
           COUNT(*) AS n_evaluated,
           COUNT(*) FILTER (
               WHERE x >= 0 AND x < msx AND y >= 0 AND y < msy
           ) AS n_in_bounds,
           COUNT(*) FILTER (
               WHERE x < 0 OR x >= msx OR y < 0 OR y >= msy
           ) AS n_out_of_bounds,
           ROUND(
               1.0 * COUNT(*) FILTER (
                   WHERE x >= 0 AND x < msx AND y >= 0 AND y < msy
               ) / NULLIF(COUNT(*), 0), 6
           ) AS in_bounds_rate
    FROM joined
    GROUP BY evtTypeName
    ORDER BY evtTypeName
    """,
)
print("=== V6.3 in-bounds rate per event family (raw interp) ===")
print(v6_3_df.to_string(index=False))
in_bounds_per_event = {
    r["evtTypeName"]: {
        "n_evaluated": int(r["n_evaluated"]),
        "n_in_bounds": int(r["n_in_bounds"]),
        "n_out_of_bounds": int(r["n_out_of_bounds"]),
        "in_bounds_rate": float(r["in_bounds_rate"])
                          if r["in_bounds_rate"] is not None else None,
    }
    for _, r in v6_3_df.iterrows()
}

# %% [markdown]
# ### V6.4 -- UnitPositions packed-items structural check
#
# `event_data.items` is a packed array. Per s2protocol README, items
# are emitted as triplets `(delta_index, x, y)` where the unit index
# is `firstUnitIndex + cumulative deltas`. T08 verifies the array
# length is divisible by 3 (necessary condition for the triplet
# format) and reports max coordinate observed across a bounded
# sample. Full decoding (cumulative-delta index walk + per-unit
# owner attribution via UnitBorn lineage) is NOT performed in T08
# -- per Amendment 5 + plan T07.6, that risks blowing scope and
# UnitPositions remains `requires_additional_unpacking_validation`
# until a dedicated decoder is validated.

# %%
v6_4_df = run_q(
    "v6_4_unit_positions_structure",
    """
    WITH lengths AS (
        SELECT json_array_length(json_extract(event_data, '$.items'))
                   AS items_len
        FROM tracker_events_raw
        WHERE evtTypeName = 'UnitPositions'
    )
    SELECT
        COUNT(*) AS n_total,
        COUNT(*) FILTER (WHERE items_len % 3 = 0) AS n_divisible_by_3,
        COUNT(*) FILTER (WHERE items_len % 3 != 0)
            AS n_not_divisible_by_3,
        MIN(items_len) AS min_items_len,
        MAX(items_len) AS max_items_len,
        AVG(items_len) AS mean_items_len,
        ROUND(
            1.0 * COUNT(*) FILTER (WHERE items_len % 3 = 0)
                / NULLIF(COUNT(*), 0), 6
        ) AS divisibility_rate
    FROM lengths
    """,
)
print("=== V6.4 UnitPositions packed-items structure ===")
print(v6_4_df.to_string(index=False))
unit_positions_structure = {
    "n_total": int(v6_4_df["n_total"].iloc[0]),
    "n_divisible_by_3": int(v6_4_df["n_divisible_by_3"].iloc[0]),
    "n_not_divisible_by_3": int(v6_4_df["n_not_divisible_by_3"].iloc[0]),
    "min_items_len": int(v6_4_df["min_items_len"].iloc[0]),
    "max_items_len": int(v6_4_df["max_items_len"].iloc[0]),
    "mean_items_len": float(v6_4_df["mean_items_len"].iloc[0]),
    "divisibility_rate": float(v6_4_df["divisibility_rate"].iloc[0]),
    "decoded_in_t08": False,
    "decision": (
        "requires_additional_unpacking_validation -- T08 verifies the "
        "triplet-divisibility condition only; full cumulative-delta "
        "index walk + UnitBorn-lineage owner attribution is deferred"
    ),
}

# %% [markdown]
# ### V6.5 -- source-confirmation gate (per Amendment 5)
#
# T02 EVIDENCE V6 records `source_confirmed_units = False` and
# `source_confirmed_origin = False` for every tracker coordinate
# family in SC2EGSet. s2protocol README + `protocol88500.py` do not
# explicitly state whether `x` / `y` are cell units, sub-cell units,
# or fixed-point, nor whether origin is top-left vs map-center.
# Per Amendment 5, this means NO coordinate family can be
# `eligible_for_phase02_now` regardless of empirical bounds.

# %%
source_confirmation = {
    "source_confirmed_units": (
        verdicts.get("V4", {})
        .get("protocol88500_snapshot_caveat") is not None
        and EVIDENCE["V6_coordinate_semantics"]["source_confirmed_units"]
    ),
    "source_confirmed_origin": EVIDENCE["V6_coordinate_semantics"][
        "source_confirmed_origin"
    ],
    "rationale": (
        "T02 EVIDENCE V6: s2protocol README + protocol88500.py do not "
        "explicitly state coordinate units (cell vs sub-cell vs "
        "fixed-point) nor origin (top-left vs map-center) for SC2 "
        "tracker events. Empirical max(x)~219 vs map max~248 is "
        "consistent with cell units, but consistency != confirmation."
    ),
}
print("=== V6.5 source confirmation ===")
for k, v in source_confirmation.items():
    print(f"  {k}: {v}")

# %% [markdown]
# ### V6 verdict assembly
#
# Per-event-family coordinate verdict + V6 result. Per Amendment 5:
# `eligible_for_phase02_now` is impossible without source confirmation
# of units AND origin (both False here). Best achievable is
# `eligible_with_caveat` for direct-coord families with high empirical
# in-bounds rate; `blocked_until_additional_validation` otherwise.

# %%
def coord_verdict(et: str) -> dict:
    if et in DIRECT_COORD_EVENTS:
        ib = in_bounds_per_event.get(et)
        if not ib:
            return {
                "coordinate_verdict": "fail",
                "reason": "no in-bounds evaluation result",
                "in_bounds_rate": None,
            }
        rate = ib["in_bounds_rate"]
        if rate is None:
            verdict = "fail"
        elif (rate >= 0.99
              and source_confirmation["source_confirmed_units"]
              and source_confirmation["source_confirmed_origin"]):
            verdict = "eligible_for_phase02_now"
        elif rate >= 0.99:
            verdict = "eligible_with_caveat"
        else:
            verdict = "blocked_until_additional_validation"
        return {
            "coordinate_verdict": verdict,
            "in_bounds_rate": rate,
            "n_evaluated": ib["n_evaluated"],
            "n_out_of_bounds": ib["n_out_of_bounds"],
            "scope": (
                "descriptive coordinate features only; subject to "
                "Amendment 5 source-confirmation gate"
            ),
        }
    if et == "UnitPositions":
        return {
            "coordinate_verdict": "blocked_until_additional_validation",
            "in_bounds_rate": None,
            "scope": (
                "owner-attributed and coordinate features blocked until "
                "items unpacking decoder is validated AND units/origin "
                "are source-confirmed"
            ),
            "structure": unit_positions_structure,
        }
    return {
        "coordinate_verdict": "not_applicable",
        "in_bounds_rate": None,
        "scope": "no coordinate fields on this event family",
    }


COORD_BEARING = DIRECT_COORD_EVENTS + ["UnitPositions"]
coordinate_feature_eligibility = {et: coord_verdict(et) for et in COORD_BEARING}
print("=== V6 coordinate verdicts ===")
for et, v in coordinate_feature_eligibility.items():
    print(f"  {et}: {v['coordinate_verdict']} "
          f"(in_bounds_rate={v.get('in_bounds_rate')})")

# %% [markdown]
# ### V6 verdict block + REVIEW followup

# %%
review_followups: list = []
for et, v in coordinate_feature_eligibility.items():
    rate = v.get("in_bounds_rate")
    if rate is not None and rate < 0.99:
        review_followups.append(
            f"[REVIEW: investigate s2protocol coordinate-encoding for "
            f"SC2 tracker event {et}; out-of-bounds rate "
            f"{(1.0 - rate) * 100:.4f}% observed 2026-05-04]"
        )

eligible = [
    et for et, v in coordinate_feature_eligibility.items()
    if v["coordinate_verdict"] == "eligible_for_phase02_now"
]
caveated = [
    et for et, v in coordinate_feature_eligibility.items()
    if v["coordinate_verdict"] == "eligible_with_caveat"
]
blocked = [
    et for et, v in coordinate_feature_eligibility.items()
    if v["coordinate_verdict"] == "blocked_until_additional_validation"
]
failed = [
    et for et, v in coordinate_feature_eligibility.items()
    if v["coordinate_verdict"] == "fail"
]

if failed:
    v6_result = "FAIL"
    v6_caveat = (
        f"failed coordinate verdicts: {failed}; "
        f"blocked: {blocked}; caveated: {caveated}"
    )
elif blocked or not source_confirmation["source_confirmed_units"]:
    v6_result = "PASS_WITH_CAVEAT"
    v6_caveat = (
        f"source-confirmation gate not met (units / origin not "
        f"confirmed in s2protocol); coord-bearing eligibility "
        f"capped at eligible_with_caveat; blocked: {blocked}; "
        f"caveated: {caveated}"
    )
else:
    v6_result = "PASS"
    v6_caveat = (
        f"all {len(eligible)} coord-bearing families eligible "
        f"(source-confirmed AND empirical bounds pass)"
    )

verdicts["V6"] = {
    "hypothesis": (
        "tracker coordinate fields are local observations usable "
        "descriptively if units / origin are understood and bounds "
        "are plausible"
    ),
    "falsifier": (
        "units / origin not source-confirmed AND empirical bounds "
        "inconsistent; material out-of-bounds rate without "
        "explainable convention; UnitPositions cannot be decoded; "
        "future-dependent semantics"
    ),
    "result": v6_result,
    "amendment_5_compliance": True,
    "per_event_coordinate_summary": {
        et: in_bounds_per_event.get(et) for et in DIRECT_COORD_EVENTS
    },
    "source_confirmation": source_confirmation,
    "bounds_summary": bounds_summary,
    "unit_positions_unpacking_summary": unit_positions_structure,
    "coordinate_feature_eligibility": coordinate_feature_eligibility,
    "review_followups_for_artifact_json": review_followups,
    "notes_for_V8": (
        "Coordinate-derived features for any tracker event family are "
        "blocked or caveated under V6 because s2protocol does not "
        "source-confirm units / origin (Amendment 5). Empirical "
        "in-bounds rates are reported descriptively. UnitPositions "
        "owner attribution remains blocked until items unpacking is "
        "validated. V6 does NOT block non-coordinate cutoff-count "
        "features (those are V5)."
    ),
    "notes": v6_caveat,
}
print("=== V6 verdict ===")
print(f"  result: {verdicts['V6']['result']}")
print(f"  eligible: {eligible}; caveated: {caveated}; blocked: {blocked}; "
      f"failed: {failed}")
print(f"  review_followups: {len(review_followups)}")
for note in review_followups:
    print(f"    {note}")
print(f"  notes: {verdicts['V6']['notes']}")

# %% [markdown]
# ### V6 consistency assertions

# %%
for et in COORD_BEARING:
    assert et in coordinate_feature_eligibility, (
        f"missing V6 verdict for coord-bearing family {et}"
    )
    v = coordinate_feature_eligibility[et]
    assert v["coordinate_verdict"] in (
        "eligible_for_phase02_now", "eligible_with_caveat",
        "blocked_until_additional_validation", "not_applicable", "fail"
    ), f"{et}: bad coordinate_verdict={v['coordinate_verdict']}"
    if not source_confirmation["source_confirmed_units"]:
        assert v["coordinate_verdict"] != "eligible_for_phase02_now", (
            f"{et}: cannot be eligible_for_phase02_now without "
            "source_confirmed_units (Amendment 5)"
        )
print("=== V6 consistency: OK ===")
print(f"  {len(coordinate_feature_eligibility)} coord-bearing families "
      f"have V6 verdicts; Amendment 5 gate enforced.")

# %% [markdown]
# ## V6 result summary
#
# - **Map bounds** (V6.1): every replay carries
#   `initData.gameDescription.mapSizeX/mapSizeY`. A small number with
#   `msx <= 0` or `msy <= 0` are excluded from the in-bounds
#   evaluation (degenerate-bounds replay count reported above).
# - **Direct coordinates** (V6.2): UnitBorn / UnitInit / UnitDied
#   carry `event_data.x` and `event_data.y` with near-zero null
#   rate; observed integer ranges are consistent with cell units
#   (max `x`/`y` < typical `mapSize`).
# - **In-bounds rate** (V6.3): joined to map dims, raw integer
#   interpretation `[0, mapSizeX-1] x [0, mapSizeY-1]` -- per-family
#   in_bounds_rate reported descriptively. NOT called a "parser bug"
#   without source evidence (Q4 / Amendment 5).
# - **UnitPositions** (V6.4): structural check only. `event_data.items`
#   length divisibility-by-3 reported as a necessary condition for
#   the triplet `(delta_index, x, y)` packed encoding. Full decoding
#   is NOT performed in T08; UnitPositions remains
#   `requires_additional_unpacking_validation` until a dedicated
#   decoder is validated AND units / origin are source-confirmed.
# - **Source confirmation** (V6.5, per T02 EVIDENCE V6):
#   `source_confirmed_units = False` and `source_confirmed_origin =
#   False`. s2protocol does not explicitly state cell-vs-sub-cell-
#   vs-fixed-point or origin convention for SC2 tracker events. Per
#   Amendment 5, NO coordinate family can be
#   `eligible_for_phase02_now` regardless of empirical bounds.
# - **REVIEW followup**: if any direct-coord family has
#   `in_bounds_rate < 0.99`, a follow-up note is recorded in
#   `verdicts["V6"]["review_followups_for_artifact_json"]` (artifact
#   JSON only, NOT thesis prose, NOT REVIEW_QUEUE.md per Q5).
# - **V6 verdict:** see printed result above.
# - **Scope:** V6 governs coordinate-derived features only. It does
#   NOT block non-coordinate cutoff-count features established in V5.

# %% [markdown]
# ## Out of scope for T08 (this notebook execution)
#
# - V7..V8 are deferred to T09..T10 per `planning/current_plan.md`.
# - Final `.md` / `.json` / `.csv` artifacts under
#   `reports/artifacts/01_exploration/03_profiling/` are produced
#   atomically in T11, NOT in T08.
# - STEP_STATUS / PIPELINE_SECTION_STATUS / PHASE_STATUS updates are
#   T11-atomic per WARNING-3 + WARNING-4 fold.
# - research_log entry is T11.
# - thesis chapter prose, AoE2 datasets, specs, pyproject, poetry,
#   Phase 02 feature engineering -- all out of scope.
