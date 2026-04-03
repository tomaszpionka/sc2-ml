"""PyArrow schemas for SC2 replay event Parquet files.

Also exports ``PLAYER_STATS_FIELD_MAP`` which drives both the DuckDB
``player_stats`` view construction and the Parquet schema validation
in the in-game extraction pipeline (Path B).
"""

import pyarrow as pa

# All 39 PlayerStats score fields mapped to snake_case column names.
# Source: trackerEvents where evtTypeName == "PlayerStats", nested under "stats".
PLAYER_STATS_FIELD_MAP: dict[str, str] = {
    "scoreValueFoodMade": "food_made",
    "scoreValueFoodUsed": "food_used",
    "scoreValueMineralsCollectionRate": "minerals_collection_rate",
    "scoreValueMineralsCurrent": "minerals_current",
    "scoreValueMineralsFriendlyFireArmy": "minerals_friendly_fire_army",
    "scoreValueMineralsFriendlyFireEconomy": "minerals_friendly_fire_economy",
    "scoreValueMineralsFriendlyFireTechnology": "minerals_friendly_fire_technology",
    "scoreValueMineralsKilledArmy": "minerals_killed_army",
    "scoreValueMineralsKilledEconomy": "minerals_killed_economy",
    "scoreValueMineralsKilledTechnology": "minerals_killed_technology",
    "scoreValueMineralsLostArmy": "minerals_lost_army",
    "scoreValueMineralsLostEconomy": "minerals_lost_economy",
    "scoreValueMineralsLostTechnology": "minerals_lost_technology",
    "scoreValueMineralsUsedActiveForces": "minerals_used_active_forces",
    "scoreValueMineralsUsedCurrentArmy": "minerals_used_current_army",
    "scoreValueMineralsUsedCurrentEconomy": "minerals_used_current_economy",
    "scoreValueMineralsUsedCurrentTechnology": "minerals_used_current_technology",
    "scoreValueMineralsUsedInProgressArmy": "minerals_used_in_progress_army",
    "scoreValueMineralsUsedInProgressEconomy": "minerals_used_in_progress_economy",
    "scoreValueMineralsUsedInProgressTechnology": "minerals_used_in_progress_technology",
    "scoreValueVespeneCollectionRate": "vespene_collection_rate",
    "scoreValueVespeneCurrent": "vespene_current",
    "scoreValueVespeneFriendlyFireArmy": "vespene_friendly_fire_army",
    "scoreValueVespeneFriendlyFireEconomy": "vespene_friendly_fire_economy",
    "scoreValueVespeneFriendlyFireTechnology": "vespene_friendly_fire_technology",
    "scoreValueVespeneKilledArmy": "vespene_killed_army",
    "scoreValueVespeneKilledEconomy": "vespene_killed_economy",
    "scoreValueVespeneKilledTechnology": "vespene_killed_technology",
    "scoreValueVespeneLostArmy": "vespene_lost_army",
    "scoreValueVespeneLostEconomy": "vespene_lost_economy",
    "scoreValueVespeneLostTechnology": "vespene_lost_technology",
    "scoreValueVespeneUsedActiveForces": "vespene_used_active_forces",
    "scoreValueVespeneUsedCurrentArmy": "vespene_used_current_army",
    "scoreValueVespeneUsedCurrentEconomy": "vespene_used_current_economy",
    "scoreValueVespeneUsedCurrentTechnology": "vespene_used_current_technology",
    "scoreValueVespeneUsedInProgressArmy": "vespene_used_in_progress_army",
    "scoreValueVespeneUsedInProgressEconomy": "vespene_used_in_progress_economy",
    "scoreValueVespeneUsedInProgressTechnology": "vespene_used_in_progress_technology",
    "scoreValueWorkersActiveCount": "workers_active_count",
}

TRACKER_SCHEMA = pa.schema(
    [
        pa.field("match_id", pa.string()),
        pa.field("event_type", pa.string()),
        pa.field("game_loop", pa.int32()),
        pa.field("player_id", pa.int8()),
        pa.field("event_data", pa.string()),
    ]
)

GAME_EVENT_SCHEMA = pa.schema(
    [
        pa.field("match_id", pa.string()),
        pa.field("event_type", pa.string()),
        pa.field("game_loop", pa.int32()),
        pa.field("user_id", pa.int32()),
        pa.field("player_id", pa.int8()),
        pa.field("event_data", pa.string()),
    ]
)

METADATA_SCHEMA = pa.schema(
    [
        pa.field("match_id", pa.string()),
        pa.field("player_id", pa.int8()),
        pa.field("user_id", pa.int32()),
        pa.field("nickname", pa.string()),
        pa.field("race", pa.string()),
        pa.field("total_game_loops", pa.int32()),
    ]
)
