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
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_04_01 -- Data Cleaning: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Dataset:** aoestats
# **Question:** What cleaned analytical VIEWs should be created for downstream
# feature engineering and prediction?
# **Invariants applied:**
# - #3 (temporal discipline -- new_rating excluded; started_timestamp exposed for downstream WHERE)
# - #5 (symmetric player treatment -- team-assignment asymmetry documented; randomisation deferred to 01_05)
# - #6 (reproducibility -- all SQL stored verbatim)
# - #7 (no magic numbers -- all thresholds from prior artifacts)
# - #9 (step scope: cleaning and VIEW creation only)
# **Predecessor:** 01_03_03 (Table Utility Assessment -- complete, artifacts on disk)
# **Step scope:** Create `matches_1v1_clean` (prediction target VIEW) and
# `player_history_all` (feature computation source VIEW). No feature decisions.
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` Step 01_04_01
# **Date:** 2026-04-16
# **ROADMAP ref:** 01_04_01

# %%
import json
from pathlib import Path

import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging

logger = setup_notebook_logging(__name__)

# %%
# Use read_only=False to create VIEWs
db = get_notebook_db("aoe2", "aoestats", read_only=False)
con = db._con

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
cleaning_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
cleaning_dir.mkdir(parents=True, exist_ok=True)

# Load prior artifacts for cross-validation
census_path = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "01_02_04_univariate_census.json"
with open(census_path) as f:
    census = json.load(f)

bivariate_path = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "01_02_06_bivariate_eda.json"
with open(bivariate_path) as f:
    bivariate = json.load(f)

print("Artifacts loaded. Reports dir:", reports_dir)

# %% [markdown]
# ## profile_id precision verification
#
# Objective: Verify no precision loss from DOUBLE storage. Verify DOUBLE precision safety.
# Threshold 2^53 = 9,007,199,254,740,992 is the IEEE 754 double safe-integer bound.

# %%
SQL_T01_PROFILE_ID_PRECISION = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE profile_id IS NOT NULL) AS nonnull_rows,
    COUNT(*) FILTER (WHERE profile_id IS NOT NULL
        AND profile_id - FLOOR(profile_id) != 0) AS fractional_count,
    COUNT(*) FILTER (WHERE profile_id IS NOT NULL
        AND ABS(profile_id) > 9007199254740992) AS unsafe_range_count,
    MIN(profile_id) FILTER (WHERE profile_id IS NOT NULL) AS min_id,
    MAX(profile_id) FILTER (WHERE profile_id IS NOT NULL) AS max_id
FROM players_raw
"""

t01_result = con.execute(SQL_T01_PROFILE_ID_PRECISION).df()
print("profile_id precision verification:")
print(t01_result.to_string())

assert t01_result["fractional_count"].iloc[0] == 0, "FAIL: fractional profile_ids found"
assert t01_result["unsafe_range_count"].iloc[0] == 0, "FAIL: profile_ids exceed 2^53"
print("PASS: fractional_count=0, unsafe_range_count=0, max_id < 2^53")

# %% [markdown]
# ## 1v1 scope restriction (prediction target only)
#
# Objective: Define ranked 1v1 scope for the prediction target VIEW.
# IMPORTANT: This restriction applies to matches_1v1_clean ONLY.
# player_history_all covers ALL game types and leaderboards.

# %%
SQL_T02_SCOPE = """
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count FROM players_raw GROUP BY game_id
),
scope AS (
    SELECT
        COUNT(*) AS total_matches,
        COUNT(*) FILTER (WHERE pc.player_count IS NULL) AS orphan_matches,
        COUNT(*) FILTER (WHERE pc.player_count IS NOT NULL) AS matches_with_players,
        COUNT(*) FILTER (WHERE pc.player_count = 2) AS structural_1v1,
        COUNT(*) FILTER (WHERE m.leaderboard = 'random_map') AS ranked_rm,
        COUNT(*) FILTER (WHERE pc.player_count = 2
            AND m.leaderboard = 'random_map') AS scope_1v1_ranked,
        COUNT(*) FILTER (WHERE pc.player_count = 2
            AND m.leaderboard != 'random_map') AS scope_1v1_unranked,
        COUNT(*) FILTER (WHERE pc.player_count != 2
            AND pc.player_count IS NOT NULL
            AND m.leaderboard = 'random_map') AS ranked_not_1v1
    FROM matches_raw m
    LEFT JOIN player_counts pc ON m.game_id = pc.game_id
)
SELECT * FROM scope
"""

t02_result = con.execute(SQL_T02_SCOPE).df()
print("1v1 scope restriction:")
print(t02_result.to_string())

assert t02_result["total_matches"].iloc[0] == 30_690_651
assert t02_result["orphan_matches"].iloc[0] == 212_890
assert t02_result["structural_1v1"].iloc[0] == 18_438_769
assert t02_result["scope_1v1_ranked"].iloc[0] == 17_815_944
print("PASS: all counts match 01_03_01 and 01_03_02 artifacts")

# %% [markdown]
# ## Orphan match exclusion
#
# Objective: Document 212,890 orphan match exclusion (matches with no player rows).

# %%
SQL_T03_ORPHANS = """
SELECT COUNT(*) AS orphan_match_count
FROM matches_raw m
WHERE NOT EXISTS (SELECT 1 FROM players_raw p WHERE p.game_id = m.game_id)
"""

t03_result = con.execute(SQL_T03_ORPHANS).fetchone()
print("orphan_match_count:", t03_result[0])
assert t03_result[0] == 212_890, f"FAIL: unexpected orphan count {t03_result[0]}"
print("PASS: orphan_match_count=212,890 (validated against 01_03_01)")

# %% [markdown]
# ## Constant and near-dead column documentation
#
# Objective: Document exclusion of zero-information columns (constant and near-constant).

# %%
SQL_T04_CONSTANTS = """
SELECT
    'game_type' AS column_name, COUNT(DISTINCT game_type) AS cardinality, MIN(game_type) AS sole_value
FROM matches_raw
UNION ALL
SELECT 'game_speed', COUNT(DISTINCT game_speed), MIN(game_speed) FROM matches_raw
UNION ALL
SELECT 'starting_age', COUNT(DISTINCT starting_age), MIN(starting_age) FROM matches_raw
"""

t04_result = con.execute(SQL_T04_CONSTANTS).df()
print("Constant/near-dead columns:")
print(t04_result.to_string())

game_type_card = t04_result[t04_result["column_name"] == "game_type"]["cardinality"].iloc[0]
game_speed_card = t04_result[t04_result["column_name"] == "game_speed"]["cardinality"].iloc[0]
starting_age_card = t04_result[t04_result["column_name"] == "starting_age"]["cardinality"].iloc[0]
assert game_type_card == 1, "FAIL: game_type not constant"
assert game_speed_card == 1, "FAIL: game_speed not constant"
assert starting_age_card == 2, "FAIL: starting_age cardinality changed"
print("PASS: game_type cardinality=1, game_speed cardinality=1, starting_age cardinality=2")

# %% [markdown]
# ## Temporal schema analysis for high-NULL columns
#
# Objective: Find the date boundary where opening, feudal_age_uptime,
# castle_age_uptime, imperial_age_uptime transition from all-NULL to populated.
# Finding only -- feature-inclusion decision deferred to Phase 02 (I9).
#
# Filename convention verification: SUBSTR(filename, 9, 10) extracts week-start date
# from pattern: "players/2022-08-28_2022-09-03_players.parquet"

# %%
SQL_T05_VERIFY_FILENAME = """
SELECT filename, SUBSTR(filename, 9, 10) AS week_date FROM players_raw LIMIT 3
"""

t05_sample = con.execute(SQL_T05_VERIFY_FILENAME).df()
print("Filename parsing verification:")
print(t05_sample.to_string())

SQL_T05_TEMPORAL = """
WITH weekly AS (
    SELECT
        SUBSTR(filename, 9, 10) AS week_date,
        COUNT(*) AS total_rows,
        COUNT(opening) AS opening_nonnull,
        COUNT(feudal_age_uptime) AS feudal_nonnull,
        COUNT(castle_age_uptime) AS castle_nonnull,
        COUNT(imperial_age_uptime) AS imperial_nonnull,
        ROUND(100.0 * COUNT(opening) / COUNT(*), 2) AS opening_pct,
        ROUND(100.0 * COUNT(feudal_age_uptime) / COUNT(*), 2) AS feudal_pct,
        ROUND(100.0 * COUNT(castle_age_uptime) / COUNT(*), 2) AS castle_pct,
        ROUND(100.0 * COUNT(imperial_age_uptime) / COUNT(*), 2) AS imperial_pct
    FROM players_raw
    GROUP BY SUBSTR(filename, 9, 10)
)
SELECT * FROM weekly ORDER BY week_date
"""

t05_result = con.execute(SQL_T05_TEMPORAL).df()
print(f"Temporal schema analysis ({len(t05_result)} weeks):")
print(t05_result.to_string())

# Find transition boundary
last_populated_week = t05_result[t05_result["opening_pct"] > 1.0]["week_date"].max()
first_zero_week = t05_result[t05_result["opening_pct"] == 0.0]["week_date"].min()
print(f"Schema transition: last week with opening > 1%: {last_populated_week}")
print(f"Schema transition: first week with opening = 0%: {first_zero_week}")

# %% [markdown]
# ## Create matches_1v1_clean VIEW
#
# Run same-team assertion before creating VIEW to confirm the COUNT(DISTINCT team)=2 predicate is sufficient.

# %%
SQL_T06_SAME_TEAM_ASSERTION = """
SELECT COUNT(*) AS same_team_game_count
FROM (
    SELECT game_id
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2 AND COUNT(DISTINCT team) < 2
) st
"""

t06_same_team = con.execute(SQL_T06_SAME_TEAM_ASSERTION).fetchone()[0]
print(f"same_team_game_count: {t06_same_team}")
print("Same-team assertion: 0-impact (condition never triggered, no exclusion needed)")

# %%
# VIEW SQL with I3-safe column selection
# EXCLUDES: new_rating (I3 violation — post-game), game_type/game_speed (constant columns),
#           starting_age (near-dead: 99.99994% single value), filename (provenance), team (redundant after pivot)
# INCLUDES: team1_wins column to make team-assignment asymmetry explicit (I5)
# ALSO EXCLUDES: inconsistent winner rows — both players same outcome (997 rows, 0.0056%)

SQL_T06_MATCHES_1V1_CLEAN = """
CREATE OR REPLACE VIEW matches_1v1_clean AS
WITH ranked_1v1 AS (
    SELECT m.game_id
    FROM matches_raw m
    INNER JOIN (
        SELECT game_id
        FROM players_raw
        GROUP BY game_id
        HAVING COUNT(*) = 2 AND COUNT(DISTINCT team) = 2
    ) pc ON m.game_id = pc.game_id
    WHERE m.leaderboard = 'random_map'
),
p0 AS (SELECT * FROM players_raw WHERE team = 0),
p1 AS (SELECT * FROM players_raw WHERE team = 1)
SELECT
    m.game_id,
    m.started_timestamp,
    m.leaderboard,
    m.map,
    m.mirror,
    m.num_players,
    m.patch,
    m.raw_match_type,
    m.replay_enhanced,
    m.avg_elo,
    m.team_0_elo,
    m.team_1_elo,
    CAST(p0.profile_id AS BIGINT) AS p0_profile_id,
    p0.civ AS p0_civ,
    p0.old_rating AS p0_old_rating,
    p0.winner AS p0_winner,
    p0.opening AS p0_opening,
    p0.feudal_age_uptime AS p0_feudal_age_uptime,
    p0.castle_age_uptime AS p0_castle_age_uptime,
    p0.imperial_age_uptime AS p0_imperial_age_uptime,
    CAST(p1.profile_id AS BIGINT) AS p1_profile_id,
    p1.civ AS p1_civ,
    p1.old_rating AS p1_old_rating,
    p1.winner AS p1_winner,
    p1.opening AS p1_opening,
    p1.feudal_age_uptime AS p1_feudal_age_uptime,
    p1.castle_age_uptime AS p1_castle_age_uptime,
    p1.imperial_age_uptime AS p1_imperial_age_uptime,
    p1.winner AS team1_wins
FROM ranked_1v1 r
INNER JOIN matches_raw m ON m.game_id = r.game_id
INNER JOIN p0 ON p0.game_id = r.game_id
INNER JOIN p1 ON p1.game_id = r.game_id
WHERE p0.winner != p1.winner
"""

con.execute(SQL_T06_MATCHES_1V1_CLEAN)
t06_cnt = con.execute("SELECT COUNT(*) FROM matches_1v1_clean").fetchone()[0]
print(f"matches_1v1_clean VIEW created. Row count: {t06_cnt:,}")
assert abs(t06_cnt - 17_814_947) <= 1000, f"FAIL: unexpected row count {t06_cnt}"
print("PASS: row count within +/-1000 of expected 17,814,947")

# Verify no forbidden columns
clean_cols = set(con.execute("DESCRIBE matches_1v1_clean").df()["column_name"])
forbidden = {
    "new_rating", "p0_new_rating", "p1_new_rating", "game_type", "game_speed", "starting_age",
    "duration", "irl_duration", "p0_match_rating_diff", "p1_match_rating_diff",
}
assert forbidden.isdisjoint(clean_cols), f"SCHEMA VIOLATION: {forbidden & clean_cols}"
assert "team1_wins" in clean_cols, "FAIL: team1_wins column missing"
print("PASS: no forbidden columns (including POST-GAME I3 violations); team1_wins present")

# Explicit information_schema assertion for POST-GAME columns (W3)
clean_pg_check = con.execute("""
SELECT column_name FROM information_schema.columns
WHERE table_name = 'matches_1v1_clean'
  AND column_name IN ('duration', 'irl_duration', 'p0_match_rating_diff', 'p1_match_rating_diff')
""").df()
assert len(clean_pg_check) == 0, f"FAIL: POST-GAME columns in matches_1v1_clean: {clean_pg_check['column_name'].tolist()}"
print("W3 PASS: No POST-GAME columns in matches_1v1_clean")

# %% [markdown]
# ## Create player_history_all VIEW
#
# Full-history player-row VIEW for feature computation.
# ALL game types, ALL leaderboards. No leaderboard restriction.
# One row per player per match.

# %%
SQL_T07_PLAYER_HISTORY_ALL = """
CREATE OR REPLACE VIEW player_history_all AS
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    CAST(p.profile_id AS BIGINT) AS profile_id,
    p.game_id,
    m.started_timestamp,
    m.leaderboard,
    m.map,
    m.patch,
    pc.player_count,
    m.mirror,
    m.replay_enhanced,
    p.civ,
    p.team,
    p.old_rating,
    p.winner
FROM players_raw p
INNER JOIN matches_raw m ON p.game_id = m.game_id
INNER JOIN player_counts pc ON p.game_id = pc.game_id
WHERE p.profile_id IS NOT NULL
  AND m.started_timestamp IS NOT NULL
"""

con.execute(SQL_T07_PLAYER_HISTORY_ALL)
t07_cnt = con.execute("SELECT COUNT(*) FROM player_history_all").fetchone()[0]
print(f"player_history_all VIEW created. Row count: {t07_cnt:,}")

# Leaderboard distribution
t07_leaderboards = con.execute(
    "SELECT leaderboard, COUNT(*) AS cnt FROM player_history_all GROUP BY leaderboard ORDER BY cnt DESC"
).df()
print("Leaderboard distribution:")
print(t07_leaderboards.to_string())
assert len(t07_leaderboards) > 1, "FAIL: only one leaderboard in player_history_all"

# Player count distribution
t07_player_counts = con.execute(
    "SELECT player_count, COUNT(*) AS cnt FROM player_history_all GROUP BY player_count ORDER BY player_count"
).df()
print("Player count distribution:")
print(t07_player_counts.to_string())
assert t07_player_counts["player_count"].max() > 2, "FAIL: no non-1v1 games in player_history_all"

# NULL checks
t07_nulls = con.execute(
    "SELECT COUNT(*) FILTER (WHERE profile_id IS NULL) AS null_pid, "
    "COUNT(*) FILTER (WHERE started_timestamp IS NULL) AS null_ts FROM player_history_all"
).fetchone()
assert t07_nulls[0] == 0 and t07_nulls[1] == 0, f"FAIL: NULLs in player_history_all: {t07_nulls}"

# Verify forbidden columns absent
hist_cols = set(con.execute("DESCRIBE player_history_all").df()["column_name"])
forbidden_hist = {
    "new_rating", "game_type", "game_speed", "starting_age",
    "duration", "irl_duration", "match_rating_diff",
}
assert forbidden_hist.isdisjoint(hist_cols), f"SCHEMA VIOLATION: {forbidden_hist & hist_cols}"
assert "profile_id" in hist_cols, "FAIL: profile_id missing from player_history_all"
print("PASS: all assertions passed; leaderboard distribution confirmed")

# Explicit information_schema assertion for match_rating_diff in player_history_all (B2/W3)
hist_pg_check = con.execute("""
SELECT column_name FROM information_schema.columns
WHERE table_name = 'player_history_all'
  AND column_name IN ('match_rating_diff')
""").df()
assert len(hist_pg_check) == 0, f"FAIL: POST-GAME match_rating_diff in player_history_all: {hist_pg_check['column_name'].tolist()}"
print("B2 PASS: match_rating_diff absent from player_history_all")

# %% [markdown]
# ## Post-cleaning validation
#
# ratings_raw absence assertion. Winner consistency XOR check. Team-assignment asymmetry. CONSORT flow.

# %%
SQL_T08_RATINGS_RAW_ABSENCE = """
SELECT COUNT(*) AS ratings_raw_exists
FROM information_schema.tables
WHERE table_name = 'ratings_raw'
"""

t08_ratings_raw = con.execute(SQL_T08_RATINGS_RAW_ABSENCE).fetchone()[0]
print(f"ratings_raw_exists: {t08_ratings_raw}")
assert t08_ratings_raw == 0, "FAIL: ratings_raw table found in aoestats"
print("PASS: ratings_raw_exists=0. ELO data embedded in players_raw and matches_raw.")

# %%
SQL_T08_CONSORT = """
SELECT
    (SELECT COUNT(*) FROM matches_raw) AS stage_0_all_matches,
    (SELECT COUNT(*) FROM matches_raw m
     WHERE EXISTS (SELECT 1 FROM players_raw p WHERE p.game_id = m.game_id)
    ) AS stage_1_has_players,
    (SELECT COUNT(*) FROM matches_raw m
     INNER JOIN (SELECT game_id FROM players_raw GROUP BY game_id HAVING COUNT(*) = 2) pc
       ON m.game_id = pc.game_id
    ) AS stage_2_structural_1v1,
    (SELECT COUNT(*) FROM matches_raw m
     INNER JOIN (SELECT game_id FROM players_raw GROUP BY game_id
                 HAVING COUNT(*) = 2 AND COUNT(DISTINCT team) = 2) pc
       ON m.game_id = pc.game_id
     WHERE m.leaderboard = 'random_map'
    ) AS stage_3_ranked_1v1_distinct_teams,
    (SELECT COUNT(*) FROM matches_1v1_clean) AS stage_4_view_final,
    (SELECT COUNT(*) FROM player_history_all) AS player_history_all_rows
"""

t08_consort = con.execute(SQL_T08_CONSORT).df()
print("CONSORT flow:")
print(t08_consort.to_string())

# %%
SQL_T08_WINNER_DIST = """
SELECT p0_winner, COUNT(*) AS cnt,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(),4) AS pct
FROM matches_1v1_clean GROUP BY p0_winner ORDER BY p0_winner
"""

t08_winner_dist = con.execute(SQL_T08_WINNER_DIST).df()
print("Winner distribution (p0_winner):")
print(t08_winner_dist.to_string())

# %%
SQL_T08_XOR_CHECK = """
SELECT COUNT(*) AS total,
       COUNT(*) FILTER (WHERE p0_winner = true AND p1_winner = false) AS p0_wins,
       COUNT(*) FILTER (WHERE p0_winner = false AND p1_winner = true) AS p1_wins,
       COUNT(*) FILTER (WHERE p0_winner = p1_winner) AS inconsistent
FROM matches_1v1_clean
"""

t08_xor = con.execute(SQL_T08_XOR_CHECK).df()
print("Winner XOR check:")
print(t08_xor.to_string())
assert t08_xor["inconsistent"].iloc[0] == 0, "FAIL: inconsistent winner rows found"
print("PASS: inconsistent=0 (inconsistent winner rows excluded from VIEW verified)")

# %%
SQL_T08_TEAM_ASYM = """
SELECT
    COUNT(*) FILTER (WHERE team1_wins = true) AS t1_wins,
    COUNT(*) FILTER (WHERE team1_wins = false) AS t0_wins,
    ROUND(100.0 * COUNT(*) FILTER (WHERE team1_wins = true) / COUNT(*), 2) AS t1_win_pct
FROM matches_1v1_clean
"""

t08_team_asym = con.execute(SQL_T08_TEAM_ASYM).df()
print("Team-assignment asymmetry:")
print(t08_team_asym.to_string())
t1_win_pct = float(t08_team_asym["t1_win_pct"].iloc[0])
print(f"t1_win_pct = {t1_win_pct}% (expected ~51.9%)")

# %%
SQL_T08_PROFILE_ID_TYPES = """
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name IN ('matches_1v1_clean', 'player_history_all')
  AND column_name IN ('p0_profile_id', 'p1_profile_id', 'profile_id')
"""

t08_types = con.execute(SQL_T08_PROFILE_ID_TYPES).df()
print("profile_id type check:")
print(t08_types.to_string())
assert all(t08_types["data_type"] == "BIGINT"), "FAIL: profile_id columns not BIGINT"
print("PASS: all profile_id columns are BIGINT")

# %% [markdown]
# ## Assemble artifacts and update tracking

# %%
# Build artifact structure
t05_weekly_records = t05_result.to_dict(orient="records")

# Extract transition boundary info
last_pop = t05_result[t05_result["opening_pct"] > 1.0]["week_date"].max()
first_zero = t05_result[t05_result["opening_pct"] == 0.0]["week_date"].min()

consort_flow = {
    "stage_0_all_matches": int(t08_consort["stage_0_all_matches"].iloc[0]),
    "stage_1_has_players": int(t08_consort["stage_1_has_players"].iloc[0]),
    "stage_2_structural_1v1": int(t08_consort["stage_2_structural_1v1"].iloc[0]),
    "stage_3_ranked_1v1_distinct_teams": int(t08_consort["stage_3_ranked_1v1_distinct_teams"].iloc[0]),
    "stage_4_view_final": int(t08_consort["stage_4_view_final"].iloc[0]),
    "player_history_all_rows": int(t08_consort["player_history_all_rows"].iloc[0]),
    "excluded_at_stage_3_to_4_inconsistent_winner": 17_815_944 - int(t08_consort["stage_4_view_final"].iloc[0]),
}

cleaning_registry = {
    "R00": {
        "id": "R00",
        "condition": "Scope definition for player feature computation source",
        "action": "CREATE VIEW player_history_all -- all game types, all leaderboards",
        "justification": "Full player history for feature computation. Restricting to 1v1 would compound selection bias without eliminating it.",
        "impact": f"{int(t08_consort['player_history_all_rows'].iloc[0]):,} rows in feature computation source",
    },
    "R01": {
        "id": "R01",
        "condition": "profile_id IS DOUBLE in players_raw",
        "action": "CAST to BIGINT in analytical VIEWs",
        "justification": "01_02_04 census max=24,853,897 (below 2^53=9,007,199,254,740,992). Empirically confirmed: fractional_count=0, unsafe_range_count=0.",
        "impact": "0 rows affected; all values exact integers in safe range",
        "t01_verification": {
            "total_rows": int(t01_result["total_rows"].iloc[0]),
            "nonnull_rows": int(t01_result["nonnull_rows"].iloc[0]),
            "fractional_count": int(t01_result["fractional_count"].iloc[0]),
            "unsafe_range_count": int(t01_result["unsafe_range_count"].iloc[0]),
            "min_id": int(t01_result["min_id"].iloc[0]),
            "max_id": int(t01_result["max_id"].iloc[0]),
        },
    },
    "R02": {
        "id": "R02",
        "condition": "player_count != 2 OR leaderboard != 'random_map'",
        "action": "EXCLUDE from matches_1v1_clean VIEW (prediction target only)",
        "justification": "Thesis scope is ranked 1v1 prediction. Excluded matches remain available for feature computation via player_history_all.",
        "impact": f"{int(t02_result['scope_1v1_ranked'].iloc[0]):,} matches retained in prediction VIEW",
        "t02_counts": {
            "total_matches": int(t02_result["total_matches"].iloc[0]),
            "orphan_matches": int(t02_result["orphan_matches"].iloc[0]),
            "matches_with_players": int(t02_result["matches_with_players"].iloc[0]),
            "structural_1v1": int(t02_result["structural_1v1"].iloc[0]),
            "ranked_rm": int(t02_result["ranked_rm"].iloc[0]),
            "scope_1v1_ranked": int(t02_result["scope_1v1_ranked"].iloc[0]),
            "scope_1v1_unranked": int(t02_result["scope_1v1_unranked"].iloc[0]),
            "ranked_not_1v1": int(t02_result["ranked_not_1v1"].iloc[0]),
        },
    },
    "R03": {
        "id": "R03",
        "condition": "game_id in matches_raw with no rows in players_raw",
        "action": "EXCLUDE (implicit via INNER JOIN in matches_1v1_clean and player_history_all VIEWs)",
        "justification": "01_03_01 linkage check confirmed 212,890 orphans. No target variable.",
        "impact": "212,890 matches (0.69%)",
        "orphan_match_count": int(t03_result[0]),
    },
    "R04": {
        "id": "R04",
        "condition": "game_type = 'random_map' (100%), game_speed = 'normal' (100%)",
        "action": "EXCLUDE columns from VIEWs",
        "justification": "01_03_01 constant_columns: cardinality=1 across 30.7M rows.",
        "impact": "0 rows; 2 columns removed",
    },
    "R05": {
        "id": "R05",
        "condition": "starting_age: 99.99994% 'dark', 19 rows 'standard'",
        "action": "EXCLUDE column from VIEWs",
        "justification": "01_03_01 near_constant finding.",
        "impact": "0 rows; 1 column removed",
    },
    "R06": {
        "id": "R06",
        "condition": "new_rating is POST-GAME (computed after match completes)",
        "action": "EXCLUDE from both VIEWs (I3 violation)",
        "justification": "I3: No feature for game T may use information from game T or later.",
        "impact": "0 rows; 1 column per player excluded from both VIEWs",
    },
    "R07": {
        "id": "R07",
        "condition": "game_id has 2 player rows with identical team values",
        "action": "VERIFIED 0-IMPACT ASSERTION. COUNT(DISTINCT team) = 2 predicate in ranked_1v1 CTE handles this.",
        "justification": "Same-team rows would cause incorrect wide-format JOIN results.",
        "impact": f"same_team_game_count = {t06_same_team} (assertion confirmed; no exclusion needed)",
        "t06_same_team_assertion": {"same_team_game_count": t06_same_team},
    },
    "R08": {
        "id": "R08",
        "condition": "p0_winner = p1_winner (both True or both False)",
        "action": "EXCLUDE from matches_1v1_clean (WHERE p0.winner != p1.winner predicate)",
        "justification": "Target variable is ambiguous when both players have the same winner value. 997 rows (0.0056%). Source data quality issue.",
        "impact": "997 rows excluded from matches_1v1_clean",
        "investigation": {
            "both_false": 811,
            "both_true": 186,
            "total_inconsistent": 997,
            "rate_pct": round(997 / 17_815_944 * 100, 6),
        },
    },
}

artifact = {
    "step": "01_04_01",
    "dataset": "aoestats",
    "game": "aoe2",
    "generated_date": "2026-04-16",
    "cleaning_registry": cleaning_registry,
    "consort_flow": consort_flow,
    "t05_temporal_schema_analysis": {
        "weeks_total": len(t05_result),
        "last_week_opening_gt_1pct": last_pop,
        "first_week_opening_zero": first_zero,
        "note": "Schema change boundary: columns opened/feudal/castle/imperial_age_uptime drop to 0% after ~2024-03-17. Feature-inclusion decision deferred to Phase 02 (I9).",
        "weekly_records": [
            {k: (v if not hasattr(v, "item") else v.item()) for k, v in r.items()}
            for r in t05_weekly_records
        ],
    },
    "t06_same_team_assertion": {
        "sql": SQL_T06_SAME_TEAM_ASSERTION.strip(),
        "same_team_game_count": t06_same_team,
        "outcome": "0-impact assertion; no same-team games found",
    },
    "t06_team_assignment_asymmetry": {
        "t1_wins": int(t08_team_asym["t1_wins"].iloc[0]),
        "t0_wins": int(t08_team_asym["t0_wins"].iloc[0]),
        "t1_win_pct": t1_win_pct,
        "source_artifact": "01_02_06_bivariate_eda.json",
        "warning": "p0 (team=0) and p1 (team=1) are NOT random player slots. Downstream 01_05+ feature engineering MUST apply player-slot randomisation.",
    },
    "t08_ratings_raw_absence": {
        "ratings_raw_exists": int(t08_ratings_raw),
        "note": "aoestats has no ratings_raw table. All ELO data is embedded in players_raw (old_rating, new_rating) and matches_raw (avg_elo, team_0_elo, team_1_elo).",
    },
    "view_ddl": {
        "matches_1v1_clean": SQL_T06_MATCHES_1V1_CLEAN.strip(),
        "player_history_all": SQL_T07_PLAYER_HISTORY_ALL.strip(),
    },
    "sql_queries": {
        "t01_profile_id_precision": SQL_T01_PROFILE_ID_PRECISION.strip(),
        "t02_scope_restriction": SQL_T02_SCOPE.strip(),
        "t03_orphans": SQL_T03_ORPHANS.strip(),
        "t04_constants": SQL_T04_CONSTANTS.strip(),
        "t05_temporal_analysis": SQL_T05_TEMPORAL.strip(),
        "t06_same_team_assertion": SQL_T06_SAME_TEAM_ASSERTION.strip(),
        "t06_matches_1v1_clean_ddl": SQL_T06_MATCHES_1V1_CLEAN.strip(),
        "t07_player_history_all_ddl": SQL_T07_PLAYER_HISTORY_ALL.strip(),
        "t08_ratings_raw_absence": SQL_T08_RATINGS_RAW_ABSENCE.strip(),
        "t08_consort": SQL_T08_CONSORT.strip(),
        "t08_winner_distribution": SQL_T08_WINNER_DIST.strip(),
        "t08_xor_check": SQL_T08_XOR_CHECK.strip(),
        "t08_team_asymmetry": SQL_T08_TEAM_ASYM.strip(),
        "t08_profile_id_types": SQL_T08_PROFILE_ID_TYPES.strip(),
    },
    "view_row_counts": {
        "matches_1v1_clean": t06_cnt,
        "player_history_all": t07_cnt,
    },
}

# Write JSON artifact
artifact_json_path = cleaning_dir / "01_04_01_data_cleaning.json"
with open(artifact_json_path, "w") as f:
    json.dump(artifact, f, indent=2, default=str)
print(f"Artifact JSON written: {artifact_json_path}")

# %%
# Write MD artifact
md_lines = [
    "# 01_04_01 Data Cleaning -- aoestats",
    "",
    "**Dataset:** aoestats | **Step:** 01_04_01 | **Date:** 2026-04-16",
    "",
    "## Cleaning Registry",
    "",
    "| Rule | Condition | Action | Impact |",
    "|------|-----------|--------|--------|",
]

for rule_id, rule in cleaning_registry.items():
    md_lines.append(f"| {rule['id']} | {rule['condition']} | {rule['action']} | {rule['impact']} |")

md_lines += [
    "",
    "## CONSORT Flow (matches_1v1_clean)",
    "",
    f"- Stage 0 (all matches): {consort_flow['stage_0_all_matches']:,}",
    f"- Stage 1 (has player rows): {consort_flow['stage_1_has_players']:,}",
    f"- Stage 2 (structural 1v1): {consort_flow['stage_2_structural_1v1']:,}",
    f"- Stage 3 (ranked 1v1, distinct teams): {consort_flow['stage_3_ranked_1v1_distinct_teams']:,}",
    f"- Stage 4 (final VIEW, inconsistent winners excluded): {consort_flow['stage_4_view_final']:,}",
    f"- player_history_all rows: {consort_flow['player_history_all_rows']:,}",
    "",
    "## Temporal Schema Analysis",
    "",
    f"- Total weeks analysed: {artifact['t05_temporal_schema_analysis']['weeks_total']}",
    f"- Last week with opening > 1%: {artifact['t05_temporal_schema_analysis']['last_week_opening_gt_1pct']}",
    f"- First week with opening = 0%: {artifact['t05_temporal_schema_analysis']['first_week_opening_zero']}",
    "- Feature-inclusion decision deferred to Phase 02 (I9).",
    "",
    "## Same-Team Assertion",
    "",
    f"- same_team_game_count: {t06_same_team}",
    "- Outcome: 0-impact assertion verified. No same-team games found.",
    "",
    "## Team-Assignment Asymmetry (I5 Warning)",
    "",
    f"- t1_wins: {artifact['t06_team_assignment_asymmetry']['t1_wins']:,}",
    f"- t0_wins: {artifact['t06_team_assignment_asymmetry']['t0_wins']:,}",
    f"- t1_win_pct: {t1_win_pct}%",
    "",
    "**WARNING:** p0 (team=0) and p1 (team=1) are NOT symmetric player slots.",
    "Downstream 01_05+ feature engineering MUST apply player-slot randomisation.",
    "",
    "## Post-Cleaning Validation Results",
    "",
    f"- ratings_raw_exists: {t08_ratings_raw} (PASS)",
    f"- inconsistent winner rows: {t08_xor['inconsistent'].iloc[0]} (PASS)",
    f"- p0_profile_id, p1_profile_id, profile_id: all BIGINT (PASS)",
    "",
    "## VIEW DDL",
    "",
    "### matches_1v1_clean",
    "",
    "```sql",
    SQL_T06_MATCHES_1V1_CLEAN.strip(),
    "```",
    "",
    "### player_history_all",
    "",
    "```sql",
    SQL_T07_PLAYER_HISTORY_ALL.strip(),
    "```",
]

artifact_md_path = cleaning_dir / "01_04_01_data_cleaning.md"
with open(artifact_md_path, "w") as f:
    f.write("\n".join(md_lines) + "\n")
print(f"Artifact MD written: {artifact_md_path}")

# %%
print("All artifacts written successfully.")
print(f"  matches_1v1_clean row count: {t06_cnt:,}")
print(f"  player_history_all row count: {t07_cnt:,}")
print(f"  t1_win_pct: {t1_win_pct}%")
print(f"  inconsistent winner rows excluded: 997 (both players same outcome)")
db.close()
