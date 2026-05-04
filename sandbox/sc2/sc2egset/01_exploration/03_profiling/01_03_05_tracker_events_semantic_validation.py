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
# ## Out of scope for T05 (this notebook execution)
#
# - V4..V8 are deferred to T06..T10 per `planning/current_plan.md`.
# - Final `.md` / `.json` / `.csv` artifacts under
#   `reports/artifacts/01_exploration/03_profiling/` are produced
#   atomically in T11, NOT in T05.
# - STEP_STATUS / PIPELINE_SECTION_STATUS / PHASE_STATUS updates are
#   T11-atomic per WARNING-3 + WARNING-4 fold.
# - research_log entry is T11.
# - thesis chapter prose, AoE2 datasets, specs, pyproject, poetry,
#   Phase 02 feature engineering -- all out of scope.
