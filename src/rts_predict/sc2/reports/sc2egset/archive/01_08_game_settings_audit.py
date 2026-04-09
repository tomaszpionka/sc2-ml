# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
# ---

# %% [markdown]
# # Phase 1 / Step 1.8 — Game Settings and Replay Field Completeness Audit
#
# | Field | Value |
# |-------|-------|
# | Phase | 1 |
# | Step | 1.8 |
# | Dataset | sc2egset |
# | Game | sc2 |
# | Date | 2026-04-08 |
# | Report artifacts | `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_game_settings_audit.md`, `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_error_flags_audit.csv` |
# | Scientific question | Are game settings (speed, handicap, mode flags, version) consistent and valid across all 22,390 tournament replays, and do any require cleaning rules in Phase 6? |
# | ROADMAP reference | `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` Step 1.8 |

# %%
import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir

con = get_notebook_db("sc2", "sc2egset")

# %% [markdown]
# ## Sub-step A — Game Speed Verification (CRITICAL)
#
# **Expectation:** 100% of replays at "Faster" speed. Any non-Faster replay would
# require a cleaning rule in Phase 6.

# %%
# Query A1 — initData game speed
QUERY_A1 = """
SELECT
    initData->'$.gameDescription'->>'$.gameSpeed' AS init_game_speed,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 2 DESC
"""
df_a1 = con.fetch_df(QUERY_A1)
df_a1

# %% [markdown]
# **Result:** All 22,390 replays are at "Faster" speed from `initData`.

# %%
# Query A2 — details game speed (cross-check)
QUERY_A2 = """
SELECT
    details->>'$.gameSpeed' AS details_game_speed,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 2 DESC
"""
df_a2 = con.fetch_df(QUERY_A2)
df_a2

# %% [markdown]
# **Result:** All 22,390 replays are at "Faster" speed from `details` as well.

# %%
# Query A3 — Consistency between initData and details game speed fields
QUERY_A3 = """
SELECT
    initData->'$.gameDescription'->>'$.gameSpeed' AS init_speed,
    details->>'$.gameSpeed' AS details_speed,
    COUNT(*) AS n
FROM raw
GROUP BY 1, 2
HAVING init_speed != details_speed
"""
df_a3 = con.fetch_df(QUERY_A3)
df_a3

# %% [markdown]
# **Verdict: PASS** — 0 rows returned (no mismatches). Both `initData` and `details`
# agree on "Faster" for all 22,390 replays. No cleaning rule needed for game speed.

# %% [markdown]
# ## Sub-step B — Handicap Check (CRITICAL)
#
# **Expectation:** 100% of player slots at handicap = 100. Any player at a
# non-standard handicap would invalidate the economic balance of the game.

# %%
# Query B1 — Handicap distribution across all ToonPlayerDescMap entries
QUERY_B1 = """
SELECT
    (entry.value->>'$.handicap')::INTEGER AS handicap,
    COUNT(*) AS n_player_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1
ORDER BY 1
"""
df_b1 = con.fetch_df(QUERY_B1)
df_b1

# %% [markdown]
# **Result:** 44,815 player slots at handicap = 100; 2 slots at handicap = 0.
#
# **Investigation:** The 2 handicap-0 slots are phantom/anonymous entries with
# empty toon keys (`""`), zero APM, zero MMR, and `color.a = 0`. They appear in:
#
# | replay_id | tournament_dir |
# |-----------|----------------|
# | `63a9f9bf14012cd277787af4ab9d9e96` | 2017_IEM_XI_World_Championship_Katowice |
# | `0eba71d4cdcf5a159a818a4c83bbb9d2` | 2019_HomeStory_Cup_XIX |
#
# **Verdict: NEAR-PASS** — 44,815/44,817 real player slots (99.996%) are at
# handicap = 100. The 2 exceptional slots are phantom entries that will be excluded
# naturally during player identity resolution (Phase 2) via the empty-nickname filter.
# No separate Phase 6 cleaning rule needed.

# %% [markdown]
# ## Sub-step C — Error Flags Audit (CRITICAL)
#
# The fields `gameEventsErr`, `messageEventsErr`, and `trackerEvtsErr` are **not**
# stored in the DuckDB `raw` table — they were read from ZIP archives during the
# original Pattern B audit. The result is the archived CSV artifact below.

# %%
# Load and display the archived error flags audit CSV
reports_dir = get_reports_dir("sc2", "sc2egset")
error_flags_csv = reports_dir / "artifacts" / "01_08_error_flags_audit.csv"
df_c = pd.read_csv(error_flags_csv)
print(f"Rows in error flags CSV: {len(df_c)}")
df_c

# %% [markdown]
# **Result:** The CSV contains only the header row — zero replays with any error flag.
#
# | metric | value |
# |--------|-------|
# | Total replays scanned | 22,390 |
# | gameEventsErr = true | 0 |
# | messageEventsErr = true | 0 |
# | trackerEvtsErr = true | 0 |
#
# **Verdict: PASS** — Zero replays have any parse error flag set.
# No Phase 6 exclusion rule needed for error flags.
# (Original scan was performed via `zipfile`/`json` over 70 ZIP archives;
# see `01_08_game_settings_audit.md` Sub-step C for the full Python scan code.)

# %% [markdown]
# ## Sub-step D — Victory/Defeat and Game Mode Settings (CRITICAL)
#
# **Expectation:** All replays should have `noVictoryOrDefeat=false`,
# `competitive=false`, `cooperative=false`, `practice=false`.

# %%
# Query D1 — Game mode flag distribution
QUERY_D1 = """
SELECT
    initData->'$.gameDescription'->'$.gameOptions'->>'$.noVictoryOrDefeat' AS no_victory,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.competitive'       AS competitive,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.cooperative'       AS cooperative,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.practice'          AS practice,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1, 2, 3, 4
ORDER BY 5 DESC
"""
df_d1 = con.fetch_df(QUERY_D1)
df_d1

# %% [markdown]
# **Result:** 22,387 replays have the expected flag combination (all false).
# 3 replays have `competitive=true`.
#
# **Investigation:** The 3 outliers (all from `2017_IEM_XI_World_Championship_Katowice`)
# also have `amm=true` and `battleNet=true`, indicating they are Battle.net ladder
# replays accidentally bundled with the tournament dataset, not actual IEM matches.
#
# **Verdict: NEAR-PASS** — 22,387/22,390 replays (99.987%) have the expected flags.
#
# **Phase 6 Cleaning Rule C-D1:** Exclude the 3 replays with `competitive=true`
# (`amm=true`, `battleNet=true`) from the modelling corpus.

# %% [markdown]
# ## Sub-step E — Random Race Detection (IMPORTANT)
#
# **Expectation:** Most players should have `selectedRace` matching `assigned_race`.
# Empty `selectedRace` indicates Random selection.

# %%
# Query E1 — Selected race vs assigned race cross-tabulation
QUERY_E1 = """
SELECT
    (entry.value->>'$.selectedRace') AS selected_race,
    (entry.value->>'$.race')         AS assigned_race,
    COUNT(*)                          AS n_player_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 3 DESC
"""
df_e1 = con.fetch_df(QUERY_E1)
df_e1

# %% [markdown]
# **Observations:**
# 1. **Non-random locked races** (selectedRace matches assigned_race for Prot/Zerg/Terr):
#    43,694 player slots — standard competitive play.
# 2. **Random race (empty `selectedRace`):** 1,110 slots selected Random. The
#    `assigned_race` (resolved at game start) is the correct race to use for
#    feature engineering; `selectedRace` must NOT be used as a feature (null for Random).
# 3. **Explicit `Rand` in `selectedRace`:** 10 slots with `selectedRace=Rand`.
# 4. **BW race codes (BWTe, BWPr, BWZe):** 3 anomalous slots, likely Katowice legacy.
#
# **Verdict: INFORMATIONAL** — Random race occurs in ~2.5% of slots.
# Feature engineering must use `assigned_race` not `selectedRace`.
#
# **Phase 6 Cleaning Rule C-E1:** Flag replays with BW race codes for manual review.

# %% [markdown]
# ## Sub-step G — Map and Lobby Metadata Profiling (MINOR)

# %%
# Query G1 — maxPlayers distribution
QUERY_G1 = """
SELECT
    (initData->'$.gameDescription'->>'$.maxPlayers')::INTEGER AS max_players,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 1
"""
df_g1 = con.fetch_df(QUERY_G1)
df_g1

# %% [markdown]
# **Observation:** 409 replays have `maxPlayers > 2`. This is a map-slot count, not
# a player count — 4-player maps used for 1v1 are common in SC2 (diagonal positions).
# Does not indicate team games.

# %%
# Query G2 — isBlizzardMap distribution
QUERY_G2 = """
SELECT
    initData->'$.gameDescription'->>'$.isBlizzardMap' AS is_blizzard,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 1
"""
df_g2 = con.fetch_df(QUERY_G2)
df_g2

# %% [markdown]
# **Observation:** 4,875 replays (21.8%) use non-Blizzard (community-made) maps.
# Expected for a tournament corpus spanning multiple eras.

# %%
# Query G3 — Fog of war setting
QUERY_G3 = """
SELECT
    (initData->'$.gameDescription'->'$.gameOptions'->>'$.fog')::INTEGER AS fog,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 1
"""
df_g3 = con.fetch_df(QUERY_G3)
df_g3

# %% [markdown]
# **Observation:** 100% fog = 0 (standard fog of war). PASS.

# %%
# Query G4 — Random races flag (lobby-level toggle)
QUERY_G4 = """
SELECT
    initData->'$.gameDescription'->'$.gameOptions'->>'$.randomRaces' AS random_races,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 1
"""
df_g4 = con.fetch_df(QUERY_G4)
df_g4

# %% [markdown]
# **Observation:** 100% have `randomRaces=false` (lobby-level toggle, distinct from
# individual player random selection). PASS.

# %%
# Query G5 — Observers count
QUERY_G5 = """
SELECT
    (initData->'$.gameDescription'->'$.gameOptions'->>'$.observers')::INTEGER AS observers,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 1
"""
df_g5 = con.fetch_df(QUERY_G5)
df_g5

# %% [markdown]
# **Observation:** 100% have 0 observers. PASS.

# %% [markdown]
# ## Sub-step H — Version Consistency Check (MINOR)
#
# **Expectation:** `header.version` and `metadata.gameVersion` should agree for all replays.

# %%
# Query H1 — Version mismatch detection
QUERY_H1 = """
SELECT
    header->>'$.version'       AS header_version,
    metadata->>'$.gameVersion' AS meta_version,
    COUNT(*)                    AS n
FROM raw
GROUP BY 1, 2
HAVING header_version != meta_version
"""
df_h1 = con.fetch_df(QUERY_H1)
df_h1

# %% [markdown]
# **Verdict: PASS** — 0 rows returned (no mismatches). `header.version` and
# `metadata.gameVersion` are consistent across all 22,390 replays.
# No cleaning rule needed.

# %% [markdown]
# ## Conclusion
#
# ### Summary of findings
#
# | Sub-step | Topic | Status | Cleaning rule needed |
# |----------|-------|--------|---------------------|
# | A | Game speed | PASS — 100% Faster | None |
# | B | Handicap | NEAR-PASS — 2/44,817 phantom slots | Exclude by empty nickname (Phase 2) |
# | C | Error flags | PASS — 0/22,390 replays flagged | None |
# | D | Game mode flags | NEAR-PASS — 3/22,390 competitive | Rule C-D1: exclude competitive=true |
# | E | Random race | INFORMATIONAL — 2.5% Random slots | Rule C-E1: use assigned_race; flag BW codes |
# | G | Map/lobby metadata | PASS (all sub-queries nominal) | None |
# | H | Version consistency | PASS — 0 mismatches | None |
#
# ### Phase 6 cleaning rules from this step
#
# | Rule ID | Condition | Action |
# |---------|-----------|--------|
# | C-D1 | `competitive = true` (3 replays, IEM Katowice 2017) | Exclude from modelling corpus |
# | C-E1 | Player slot has BW race code (BWTe, BWPr, BWZe) — 3 slots | Flag for manual review / exclude host replay |
#
# ### Feature engineering notes (Phase 7)
#
# - Use `assigned_race` (`ToonPlayerDescMap.race`) as the race feature, not `selectedRace`.
# - The `maxPlayers` field reflects map slot count, not player count.
#
# ### Artifacts produced
# - `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_game_settings_audit.md` — original Pattern B report (superseded; see SUPERSEDED.md)
# - `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_error_flags_audit.csv` — error flags scan result (header-only = zero errors)
#
# ### Follow-ups
# - Phase 2: Player identity resolution will naturally exclude phantom slots (empty nickname filter).
# - Phase 6: Implement cleaning rules C-D1 and C-E1.
# - Phase 7: Use `assigned_race` as race feature; do not use `selectedRace`.
#
# ### Thesis mapping
# - `thesis/THESIS_STRUCTURE.md` Chapter 4 (Data) — dataset quality and cleaning pipeline.

# %%
con.close()
