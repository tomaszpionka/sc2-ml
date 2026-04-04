"""Phase 1 — Corpus Inventory and Parse Quality.

Each public function maps to one roadmap step (1.1–1.7).  The orchestrator
``run_phase_1_exploration`` runs them in sequence and returns a summary dict.

Every report artifact embeds the literal SQL that produced each result
(Scientific Invariant #8).
"""

import json
import logging
import random
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from sc2ml.config import RANDOM_SEED

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

REPORTS_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent / "reports"

# ── Domain constants (Scientific Invariant #6) ──────────────────────────────
# Source: Blizzard s2client-proto protocol.md — "22.4 gameloops per second"
# Faster speed multiplier: 1.4x on top of 16 engine loops/second
LOOPS_PER_REAL_SECOND: float = 22.4
LOOPS_PER_GAME_SECOND: float = 16.0

# ── Step 1.7 constants ──────────────────────────────────────────────────────
_EXPECTED_PLAYERSTATS_INTERVAL: int = 160  # assumption to verify
_INTERVAL_TOLERANCE_PCT: float = 0.20      # 20% deviation threshold per roadmap

# ── SQL constants ───────────────────────────────────────────────────────────

# Step 1.1
_CORPUS_DIMENSIONS_QUERY = """\
SELECT
    COUNT(*) AS total_replays,
    COUNT(DISTINCT split_part(filename, '/', -3)) AS total_tournaments,
    MIN((details->>'$.timeUTC')::TIMESTAMP) AS date_min,
    MAX((details->>'$.timeUTC')::TIMESTAMP) AS date_max,
    SUM(CASE WHEN (details->>'$.timeUTC') IS NULL THEN 1 ELSE 0 END) AS null_match_time
FROM raw
"""

_REPLAYS_WITH_EVENTS_QUERY = """\
WITH raw_ids AS (
    SELECT regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM raw
),
tracker_ids AS (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM tracker_events_raw
)
SELECT
    SUM(CASE WHEN t.replay_id IS NOT NULL THEN 1 ELSE 0 END) AS has_events,
    SUM(CASE WHEN t.replay_id IS NULL THEN 1 ELSE 0 END) AS missing_events
FROM raw_ids r
LEFT JOIN tracker_ids t ON r.replay_id = t.replay_id
"""

_PLAYER_COUNT_DISTRIBUTION_QUERY = """\
SELECT player_count, COUNT(*) AS replay_count
FROM (
    SELECT match_id, COUNT(*) AS player_count
    FROM match_player_map
    GROUP BY match_id
)
GROUP BY player_count
ORDER BY player_count
"""

_PLAYER_COUNT_ANOMALIES_QUERY = """\
SELECT
    m.match_id,
    COUNT(*) AS player_count,
    regexp_extract(m.match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
    split_part(m.match_id, '/', -3) AS tournament_dir
FROM match_player_map m
GROUP BY m.match_id
HAVING COUNT(*) != 2
ORDER BY player_count DESC, m.match_id
"""

_RESULT_DISTINCT_VALUES_QUERY = """\
SELECT
    entry.value->>'$.result' AS result_value,
    COUNT(*) AS slot_count
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1
ORDER BY slot_count DESC
"""

_RESULT_NULL_COUNT_QUERY = """\
WITH extracted AS (
    SELECT entry.value->>'$.result' AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
)
SELECT
    SUM(CASE WHEN result_val IS NULL THEN 1 ELSE 0 END) AS null_results,
    SUM(CASE WHEN result_val IS NOT NULL
              AND result_val != 'Win'
              AND result_val != 'Loss' THEN 1 ELSE 0 END) AS non_standard_results
FROM extracted
"""

_RESULT_ANOMALOUS_REPLAYS_QUERY = """\
WITH replay_results AS (
    SELECT
        filename,
        SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_count,
        SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_count
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    GROUP BY filename
)
SELECT
    SUM(CASE WHEN win_count = 0 THEN 1 ELSE 0 END) AS no_winner_replays,
    SUM(CASE WHEN win_count >= 2 THEN 1 ELSE 0 END) AS multiple_winner_replays
FROM replay_results
"""

_DUPLICATE_REPLAY_ID_QUERY = """\
SELECT
    COUNT(*) AS total_rows,
    COUNT(
        DISTINCT regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1)
    ) AS distinct_replay_ids
FROM raw
"""

_DUPLICATE_REPLAY_LIST_QUERY = """\
SELECT replay_id, COUNT(*) AS occurrence_count, LIST(tournament_dir) AS tournaments
FROM (
    SELECT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        split_part(filename, '/', -3) AS tournament_dir
    FROM raw
)
GROUP BY replay_id
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC
"""

_NEAR_DUPLICATE_QUERY = """\
WITH raw_entries AS (
    SELECT
        filename,
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time,
        metadata->>'$.mapName' AS map_name,
        CAST(entry.value->>'$.nickname' AS VARCHAR) AS nickname,
        CAST(entry.value->>'$.result' AS VARCHAR) AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
),
players_per_game AS (
    SELECT
        filename,
        ANY_VALUE(replay_id) AS replay_id,
        ANY_VALUE(match_time) AS match_time,
        ANY_VALUE(map_name) AS map_name,
        LIST(LOWER(nickname) ORDER BY LOWER(nickname)) AS player_names
    FROM raw_entries
    WHERE nickname IS NOT NULL
      AND (result_val = 'Win' OR result_val = 'Loss')
    GROUP BY filename
)
SELECT
    a.replay_id AS replay_id_a,
    b.replay_id AS replay_id_b,
    a.map_name,
    a.match_time AS time_a,
    b.match_time AS time_b,
    ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) AS time_diff_seconds,
    a.player_names
FROM players_per_game a
JOIN players_per_game b
    ON a.player_names = b.player_names
    AND a.map_name = b.map_name
    AND a.replay_id < b.replay_id
    AND ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) <= 60
ORDER BY time_diff_seconds
"""

# Step 1.2
_PARSE_QUALITY_BY_TOURNAMENT_QUERY = """\
WITH tournament_raw AS (
    SELECT
        split_part(filename, '/', -3) AS tournament_dir,
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time,
        filename
    FROM raw
),
tracker_ids AS (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM tracker_events_raw
),
player_counts AS (
    SELECT
        regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        COUNT(*) AS player_count
    FROM match_player_map
    GROUP BY 1
),
result_extracted AS (
    SELECT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        entry.value->>'$.result' AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
),
result_check AS (
    SELECT
        replay_id,
        SUM(CASE WHEN result_val = 'Win' THEN 1 ELSE 0 END) AS win_count,
        SUM(
            CASE WHEN result_val IS NULL
                      OR (result_val != 'Win' AND result_val != 'Loss')
                 THEN 1 ELSE 0 END
        ) AS bad_results
    FROM result_extracted
    GROUP BY 1
)
SELECT
    tr.tournament_dir,
    COUNT(*) AS total_replays,
    SUM(CASE WHEN t.replay_id IS NOT NULL THEN 1 ELSE 0 END) AS has_events,
    SUM(CASE WHEN t.replay_id IS NULL THEN 1 ELSE 0 END) AS missing_events,
    SUM(CASE WHEN tr.match_time IS NULL THEN 1 ELSE 0 END) AS null_timestamp,
    ROUND(100.0 * SUM(CASE WHEN t.replay_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS event_coverage_pct,
    SUM(CASE WHEN pc.player_count IS NULL OR pc.player_count != 2 THEN 1 ELSE 0 END)
        AS player_count_anomalies,
    SUM(CASE WHEN rc.win_count != 1 OR rc.bad_results > 0 THEN 1 ELSE 0 END)
        AS result_anomalies
FROM tournament_raw tr
LEFT JOIN tracker_ids t ON tr.replay_id = t.replay_id
LEFT JOIN player_counts pc ON pc.replay_id = tr.replay_id
LEFT JOIN result_check rc ON rc.replay_id = tr.replay_id
GROUP BY tr.tournament_dir
ORDER BY event_coverage_pct ASC
"""

# Step 1.3
_DURATION_PERCENTILES_QUERY = """\
SELECT
    COUNT(*) AS n,
    ROUND(AVG(real_time_minutes), 2) AS mean,
    ROUND(MEDIAN(real_time_minutes), 2) AS median,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.01), 2) AS p01,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.05), 2) AS p05,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.10), 2) AS p10,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.25), 2) AS p25,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.75), 2) AS p75,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.90), 2) AS p90,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.95), 2) AS p95,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.99), 2) AS p99
FROM (
    SELECT (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS real_time_minutes
    FROM raw
    WHERE (header->>'$.elapsedGameLoops') IS NOT NULL
)
"""

_DURATION_PERCENTILES_BY_YEAR_QUERY = """\
SELECT
    EXTRACT(YEAR FROM match_time) AS year,
    COUNT(*) AS n,
    ROUND(AVG(rtm), 2) AS mean,
    ROUND(MEDIAN(rtm), 2) AS median,
    ROUND(QUANTILE_CONT(rtm, 0.01), 2) AS p01,
    ROUND(QUANTILE_CONT(rtm, 0.05), 2) AS p05,
    ROUND(QUANTILE_CONT(rtm, 0.10), 2) AS p10,
    ROUND(QUANTILE_CONT(rtm, 0.25), 2) AS p25,
    ROUND(QUANTILE_CONT(rtm, 0.75), 2) AS p75,
    ROUND(QUANTILE_CONT(rtm, 0.90), 2) AS p90,
    ROUND(QUANTILE_CONT(rtm, 0.95), 2) AS p95,
    ROUND(QUANTILE_CONT(rtm, 0.99), 2) AS p99
FROM (
    SELECT
        (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS rtm,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time
    FROM raw
    WHERE (header->>'$.elapsedGameLoops') IS NOT NULL
)
GROUP BY 1
ORDER BY 1
"""

_DURATION_HISTOGRAM_QUERY = """\
SELECT
    FLOOR(real_time_minutes)::INTEGER AS bin_minute,
    COUNT(*) AS count
FROM (
    SELECT (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS real_time_minutes
    FROM raw
    WHERE (header->>'$.elapsedGameLoops') IS NOT NULL
)
WHERE real_time_minutes >= 0 AND real_time_minutes < 60
GROUP BY 1
ORDER BY 1
"""

_DURATION_SHORT_TAIL_HISTOGRAM_QUERY = """\
SELECT
    FLOOR(real_time_minutes * 2) / 2.0 AS bin_30s,
    COUNT(*) AS count
FROM (
    SELECT (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS real_time_minutes
    FROM raw
    WHERE (header->>'$.elapsedGameLoops') IS NOT NULL
)
WHERE real_time_minutes >= 0 AND real_time_minutes < 10
GROUP BY 1
ORDER BY 1
"""

# Step 1.4
_APM_BY_YEAR_QUERY = """\
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
"""

_MMR_BY_YEAR_QUERY = """\
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) AS mmr_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
"""

_MMR_BY_LEAGUE_QUERY = """\
SELECT
    entry.value->>'$.highestLeague' AS league,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0 THEN 1 ELSE 0 END) AS mmr_nonzero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0
          THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_nonzero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY total_slots DESC
"""

# Step 1.5
_PATCH_LANDSCAPE_QUERY = """\
SELECT
    metadata->>'$.gameVersion' AS game_version,
    metadata->>'$.dataBuild' AS data_build,
    COUNT(*) AS replay_count,
    MIN((details->>'$.timeUTC')::TIMESTAMP) AS date_min,
    MAX((details->>'$.timeUTC')::TIMESTAMP) AS date_max,
    EXTRACT(YEAR FROM MIN((details->>'$.timeUTC')::TIMESTAMP))::INTEGER AS year_min,
    EXTRACT(YEAR FROM MAX((details->>'$.timeUTC')::TIMESTAMP))::INTEGER AS year_max
FROM raw
GROUP BY 1, 2
ORDER BY date_min
"""

# Step 1.6
_EVENT_TYPE_INVENTORY_QUERY = """\
WITH per_replay AS (
    SELECT match_id, event_type, COUNT(*) AS event_count
    FROM tracker_events_raw
    GROUP BY match_id, event_type
)
SELECT
    event_type,
    SUM(event_count) AS total_rows,
    COUNT(*) AS replays_with_type,
    ROUND(AVG(event_count), 1) AS avg_per_replay,
    MEDIAN(event_count)::INTEGER AS median_per_replay
FROM per_replay
GROUP BY event_type
ORDER BY total_rows DESC
"""

_EVENT_COUNT_DISTRIBUTION_QUERY = """\
WITH per_replay AS (
    SELECT match_id, event_type, COUNT(*) AS event_count
    FROM tracker_events_raw
    GROUP BY match_id, event_type
)
SELECT
    event_type,
    MIN(event_count) AS min_count,
    QUANTILE_CONT(event_count, 0.05)::INTEGER AS p05,
    QUANTILE_CONT(event_count, 0.25)::INTEGER AS p25,
    MEDIAN(event_count)::INTEGER AS median_count,
    QUANTILE_CONT(event_count, 0.75)::INTEGER AS p75,
    QUANTILE_CONT(event_count, 0.95)::INTEGER AS p95,
    MAX(event_count) AS max_count
FROM per_replay
GROUP BY event_type
ORDER BY event_type
"""

_ZERO_PLAYERSTATS_REPLAYS_QUERY = """\
WITH all_replay_ids AS (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM tracker_events_raw
),
ps_replay_ids AS (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM tracker_events_raw
    WHERE event_type = 'PlayerStats'
)
SELECT
    COUNT(*) AS total_replays_with_events,
    SUM(CASE WHEN ps.replay_id IS NULL THEN 1 ELSE 0 END) AS zero_playerstats_replays
FROM all_replay_ids a
LEFT JOIN ps_replay_ids ps ON a.replay_id = ps.replay_id
"""

_EVENT_DENSITY_BY_YEAR_QUERY = """\
WITH replay_year AS (
    SELECT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year
    FROM raw
),
per_replay AS (
    SELECT
        regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        event_type,
        COUNT(*) AS event_count
    FROM tracker_events_raw
    GROUP BY 1, event_type
)
SELECT
    ry.year,
    pr.event_type,
    ROUND(AVG(pr.event_count), 1) AS avg_per_replay,
    MEDIAN(pr.event_count)::INTEGER AS median_per_replay
FROM per_replay pr
JOIN replay_year ry ON pr.replay_id = ry.replay_id
GROUP BY ry.year, pr.event_type
ORDER BY ry.year, pr.event_type
"""

_EVENT_DENSITY_BY_TOURNAMENT_QUERY = """\
WITH replay_tournament AS (
    SELECT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        split_part(filename, '/', -3) AS tournament_dir
    FROM raw
),
per_replay AS (
    SELECT
        regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
        event_type,
        COUNT(*) AS event_count
    FROM tracker_events_raw
    GROUP BY 1, event_type
),
per_tournament AS (
    SELECT
        rt.tournament_dir,
        pr.event_type,
        ROUND(AVG(pr.event_count), 1) AS avg_per_replay,
        MEDIAN(pr.event_count)::INTEGER AS median_per_replay
    FROM per_replay pr
    JOIN replay_tournament rt ON pr.replay_id = rt.replay_id
    GROUP BY rt.tournament_dir, pr.event_type
),
corpus_stats AS (
    SELECT
        event_type,
        AVG(avg_per_replay) AS corpus_mean,
        STDDEV(avg_per_replay) AS corpus_std
    FROM per_tournament
    GROUP BY event_type
)
SELECT
    pt.*,
    CASE WHEN cs.corpus_std > 0
         AND ABS(pt.avg_per_replay - cs.corpus_mean) > 2.0 * cs.corpus_std
         THEN true ELSE false END AS is_outlier
FROM per_tournament pt
JOIN corpus_stats cs ON pt.event_type = cs.event_type
ORDER BY pt.event_type, pt.tournament_dir
"""

# Step 1.7
_RANKED_GAMES_PER_YEAR_QUERY = """\
SELECT replay_id, year, rn
FROM (
    SELECT
        ry.replay_id,
        ry.year,
        ROW_NUMBER() OVER (PARTITION BY ry.year ORDER BY ry.replay_id) AS rn
    FROM (
        SELECT
            regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
            EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP)::INTEGER AS year
        FROM raw
        WHERE (details->>'$.timeUTC') IS NOT NULL
    ) ry
    WHERE EXISTS (
        SELECT 1 FROM tracker_events_raw t
        WHERE t.event_type = 'PlayerStats'
          AND regexp_extract(t.match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) = ry.replay_id
    )
)
ORDER BY year, rn
"""

_PLAYERSTATS_GAMELOOPS_FOR_SAMPLE_QUERY = """\
SELECT
    regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id,
    player_id,
    game_loop
FROM tracker_events_raw
WHERE event_type = 'PlayerStats'
  AND regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) = ANY(?)
ORDER BY replay_id, player_id, game_loop
"""


# ── Plot helpers ────────────────────────────────────────────────────────────


def _plot_duration_full(
    histogram_df: pd.DataFrame, stats: dict, output_path: Path
) -> None:
    """Render full-range duration histogram (0-60 min, 1-min bins)."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(histogram_df["bin_minute"], histogram_df["count"], width=0.8, color="#4C72B0")

    if "median" in stats:
        ax.axvline(
            stats["median"], color="red", linestyle="--", linewidth=1.5,
            label=f"Median: {stats['median']} min",
        )
    if "p95" in stats:
        ax.axvline(
            stats["p95"], color="orange", linestyle="--", linewidth=1.5,
            label=f"P95: {stats['p95']} min",
        )

    ax.set_xlabel("Duration (real-time minutes)")
    ax.set_ylabel("Number of replays")
    ax.set_title("Game Duration Distribution (Real-Time Minutes)")
    fig.text(
        0.5, 0.01, "Conversion: real_time_min = game_loops / 22.4 / 60",
        ha="center", fontsize=9, style="italic",
    )
    ax.legend()
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _plot_duration_short_tail(
    short_tail_df: pd.DataFrame, output_path: Path
) -> None:
    """Render zoomed short-tail histogram (<10 min, 30-sec bins) with SC2 landmarks."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(short_tail_df["bin_30s"], short_tail_df["count"], width=0.4, color="#55A868")

    landmarks = [
        (2.0, "Worker rush", "gray", "--"),
        (4.0, "Cheese/cannon rush", "orange", "--"),
        (7.0, "MSC minimum (Wu et al. 2017)", "red", "-"),
        (9.0, "SC2EGSet minimum (Bialecki et al. 2023)", "blue", "-"),
    ]
    for x, label, color, ls in landmarks:
        ax.axvline(x, color=color, linestyle=ls, linewidth=1.5, label=label)

    ax.set_xlabel("Duration (real-time minutes)")
    ax.set_ylabel("Number of replays")
    ax.set_title("Short Game Left-Tail (< 10 Real-Time Minutes)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


# ── Step 1.1 ────────────────────────────────────────────────────────────────


def run_corpus_summary(
    con: duckdb.DuckDBPyConnection, output_dir: Path | None = None
) -> dict:
    """Step 1.1 — Overall corpus counts and structural validation."""
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    result: dict = {}

    # Corpus dimensions
    dims = con.execute(_CORPUS_DIMENSIONS_QUERY).df()
    result["dimensions"] = dims.iloc[0].to_dict()

    # Event coverage
    events = con.execute(_REPLAYS_WITH_EVENTS_QUERY).df()
    result["event_coverage"] = events.iloc[0].to_dict()

    # Player count distribution
    pc_dist = con.execute(_PLAYER_COUNT_DISTRIBUTION_QUERY).df()
    result["player_count_distribution"] = pc_dist.to_dict(orient="records")

    # Player count anomalies
    pc_anomalies = con.execute(_PLAYER_COUNT_ANOMALIES_QUERY).df()
    result["player_count_anomalies"] = len(pc_anomalies)
    if len(pc_anomalies) > 0:
        pc_anomalies.to_csv(out / "01_player_count_anomalies.csv", index=False)
        logger.info(f"Wrote {len(pc_anomalies)} player count anomalies to CSV")

    # Result field audit
    result_distinct = con.execute(_RESULT_DISTINCT_VALUES_QUERY).df()
    result["result_distinct_values"] = result_distinct.to_dict(orient="records")

    result_nulls = con.execute(_RESULT_NULL_COUNT_QUERY).df()
    result["result_null_counts"] = result_nulls.iloc[0].to_dict()

    result_anomalous = con.execute(_RESULT_ANOMALOUS_REPLAYS_QUERY).df()
    result["result_anomalous"] = result_anomalous.iloc[0].to_dict()

    # Duplicate detection
    dup_counts = con.execute(_DUPLICATE_REPLAY_ID_QUERY).df()
    result["duplicate_counts"] = dup_counts.iloc[0].to_dict()

    dup_list = con.execute(_DUPLICATE_REPLAY_LIST_QUERY).df()
    result["duplicate_list"] = dup_list.to_dict(orient="records")

    near_dups = con.execute(_NEAR_DUPLICATE_QUERY).df()
    result["near_duplicates"] = near_dups.to_dict(orient="records")

    # Write corpus summary JSON
    summary_json = {
        k: _serialize_value(v) for k, v in result["dimensions"].items()
    }
    summary_json["has_events"] = _serialize_value(result["event_coverage"].get("has_events"))
    summary_json["missing_events"] = _serialize_value(
        result["event_coverage"].get("missing_events")
    )
    summary_json["player_count_anomalies"] = result["player_count_anomalies"]
    summary_json["exact_duplicates"] = len(dup_list)
    summary_json["near_duplicates"] = len(near_dups)
    (out / "01_corpus_summary.json").write_text(json.dumps(summary_json, indent=2, default=str))

    # Write result field audit MD
    _write_result_field_audit_md(out, result_distinct, result_nulls, result_anomalous)

    # Write duplicate detection MD
    _write_duplicate_detection_md(out, dup_counts, dup_list, near_dups)

    logger.info("Step 1.1 complete")
    return result


def _serialize_value(v: object) -> object:
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if hasattr(v, "item"):
        return v.item()
    return v


def _write_result_field_audit_md(
    out: Path,
    result_distinct: pd.DataFrame,
    result_nulls: pd.DataFrame,
    result_anomalous: pd.DataFrame,
) -> None:
    lines = [
        "# Result Field Audit",
        "",
        "## Distinct result values",
        "",
        "### Query",
        "```sql",
        _RESULT_DISTINCT_VALUES_QUERY.strip(),
        "```",
        "",
        "### Results",
        "",
        result_distinct.to_markdown(index=False),
        "",
        "## Null and non-standard results",
        "",
        "### Query",
        "```sql",
        _RESULT_NULL_COUNT_QUERY.strip(),
        "```",
        "",
        "### Results",
        "",
        result_nulls.to_markdown(index=False),
        "",
        "## Anomalous replays (no winner or multiple winners)",
        "",
        "### Query",
        "```sql",
        _RESULT_ANOMALOUS_REPLAYS_QUERY.strip(),
        "```",
        "",
        "### Results",
        "",
        result_anomalous.to_markdown(index=False),
        "",
    ]
    (out / "01_result_field_audit.md").write_text("\n".join(lines))


def _write_duplicate_detection_md(
    out: Path,
    dup_counts: pd.DataFrame,
    dup_list: pd.DataFrame,
    near_dups: pd.DataFrame,
) -> None:
    lines = [
        "# Duplicate Detection",
        "",
        "## Exact duplicate replay IDs",
        "",
        "### Query",
        "```sql",
        _DUPLICATE_REPLAY_ID_QUERY.strip(),
        "```",
        "",
        "### Results",
        "",
        dup_counts.to_markdown(index=False),
        "",
    ]
    if len(dup_list) > 0:
        lines.extend([
            "### Duplicate replay ID list",
            "",
            "```sql",
            _DUPLICATE_REPLAY_LIST_QUERY.strip(),
            "```",
            "",
            dup_list.to_markdown(index=False),
            "",
        ])
    lines.extend([
        "## Near-duplicates (same players, same map, <60s apart)",
        "",
        "### Query",
        "```sql",
        _NEAR_DUPLICATE_QUERY.strip(),
        "```",
        "",
    ])
    if len(near_dups) > 0:
        lines.append(near_dups.to_markdown(index=False))
    else:
        lines.append("No near-duplicates found.")
    lines.append("")
    (out / "01_duplicate_detection.md").write_text("\n".join(lines))


# ── Step 1.2 ────────────────────────────────────────────────────────────────


def run_parse_quality_by_tournament(
    con: duckdb.DuckDBPyConnection, output_dir: Path | None = None
) -> dict:
    """Step 1.2 — Per-tournament parse quality table."""
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    df = con.execute(_PARSE_QUALITY_BY_TOURNAMENT_QUERY).df()
    df.to_csv(out / "01_parse_quality_by_tournament.csv", index=False)

    # Identify flagged tournaments
    flagged = df[
        (df["event_coverage_pct"] < 80)
        | (df["player_count_anomalies"] > 0)
        | (df["result_anomalies"] > 0)
    ]

    # Write summary MD
    lines = [
        "# Parse Quality Summary",
        "",
        "## Query",
        "```sql",
        _PARSE_QUALITY_BY_TOURNAMENT_QUERY.strip(),
        "```",
        "",
        f"## Summary: {len(df)} tournaments total, {len(flagged)} flagged",
        "",
        "Flagging thresholds:",
        "- event_coverage_pct < 80%",
        "- player_count_anomalies > 0",
        "- result_anomalies > 0",
        "",
    ]
    if len(flagged) > 0:
        lines.extend([
            "## Flagged tournaments",
            "",
            flagged.to_markdown(index=False),
            "",
        ])
    (out / "01_parse_quality_summary.md").write_text("\n".join(lines))

    logger.info("Step 1.2 complete")
    return {"dataframe": df, "flagged": flagged.to_dict(orient="records")}


# ── Step 1.3 ────────────────────────────────────────────────────────────────


def run_duration_distribution(
    con: duckdb.DuckDBPyConnection, output_dir: Path | None = None
) -> dict:
    """Step 1.3 — Game duration distribution."""
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    percentiles = con.execute(_DURATION_PERCENTILES_QUERY).df()
    by_year = con.execute(_DURATION_PERCENTILES_BY_YEAR_QUERY).df()
    histogram = con.execute(_DURATION_HISTOGRAM_QUERY).df()
    short_tail = con.execute(_DURATION_SHORT_TAIL_HISTOGRAM_QUERY).df()

    # Write combined CSV with sections
    csv_path = out / "01_duration_distribution.csv"
    with open(csv_path, "w") as f:
        f.write("# Overall percentiles\n")
        percentiles.to_csv(f, index=False)
        f.write("\n# By-year percentiles\n")
        by_year.to_csv(f, index=False)
        f.write("\n# Full histogram (1-min bins, 0-60 min)\n")
        histogram.to_csv(f, index=False)
        f.write("\n# Short-tail histogram (30s bins, 0-10 min)\n")
        short_tail.to_csv(f, index=False)

    # Extract stats for plot annotations
    stats = percentiles.iloc[0].to_dict() if len(percentiles) > 0 else {}

    # Plots
    if len(histogram) > 0:
        _plot_duration_full(histogram, stats, out / "01_duration_distribution_full.png")
    if len(short_tail) > 0:
        _plot_duration_short_tail(short_tail, out / "01_duration_distribution_short_tail.png")

    logger.info("Step 1.3 complete")
    return {"percentiles": stats, "by_year": by_year.to_dict(orient="records")}


# ── Step 1.4 ────────────────────────────────────────────────────────────────


def run_apm_mmr_audit(
    con: duckdb.DuckDBPyConnection, output_dir: Path | None = None
) -> dict:
    """Step 1.4 — APM and MMR audit."""
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    apm_by_year = con.execute(_APM_BY_YEAR_QUERY).df()
    mmr_by_year = con.execute(_MMR_BY_YEAR_QUERY).df()
    mmr_by_league = con.execute(_MMR_BY_LEAGUE_QUERY).df()

    lines = [
        "# APM and MMR Audit",
        "",
        "## APM zero-rate by year",
        "",
        "### Query",
        "```sql",
        _APM_BY_YEAR_QUERY.strip(),
        "```",
        "",
        "### Results",
        "",
        apm_by_year.to_markdown(index=False),
        "",
        "## MMR zero-rate by year",
        "",
        "### Query",
        "```sql",
        _MMR_BY_YEAR_QUERY.strip(),
        "```",
        "",
        "### Results",
        "",
        mmr_by_year.to_markdown(index=False),
        "",
        "## MMR availability by league",
        "",
        "### Query",
        "```sql",
        _MMR_BY_LEAGUE_QUERY.strip(),
        "```",
        "",
        "### Results",
        "",
        mmr_by_league.to_markdown(index=False),
        "",
        "## Conclusions",
        "",
        "- **APM**: Usable from 2017 onward (Scientific Invariant #7).",
        "  2016 tournaments have systematic zero APM.",
        "- **MMR**: NOT usable as a direct feature.",
        "  Systematic missingness driven by tournament organiser, year,",
        "  and highestLeague availability.",
        "  Player skill must be derived from match history.",
        "",
    ]
    (out / "01_apm_mmr_audit.md").write_text("\n".join(lines))

    logger.info("Step 1.4 complete")
    return {
        "apm_by_year": apm_by_year.to_dict(orient="records"),
        "mmr_by_year": mmr_by_year.to_dict(orient="records"),
        "mmr_by_league": mmr_by_league.to_dict(orient="records"),
    }


# ── Step 1.5 ────────────────────────────────────────────────────────────────


def run_patch_landscape(
    con: duckdb.DuckDBPyConnection, output_dir: Path | None = None
) -> dict:
    """Step 1.5 — Game version and patch landscape."""
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    df = con.execute(_PATCH_LANDSCAPE_QUERY).df()
    df.to_csv(out / "01_patch_landscape.csv", index=False)

    logger.info("Step 1.5 complete")
    return {"dataframe": df, "patch_count": len(df)}


# ── Step 1.6 ────────────────────────────────────────────────────────────────


def run_event_type_inventory(
    con: duckdb.DuckDBPyConnection, output_dir: Path | None = None
) -> dict:
    """Step 1.6 — Tracker event type inventory (stratified)."""
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    # 1.6A — Corpus-wide
    inventory = con.execute(_EVENT_TYPE_INVENTORY_QUERY).df()
    inventory.to_csv(out / "01_event_type_inventory.csv", index=False)

    # 1.6B — Per-replay distribution + zero PlayerStats
    distribution = con.execute(_EVENT_COUNT_DISTRIBUTION_QUERY).df()
    zero_ps = con.execute(_ZERO_PLAYERSTATS_REPLAYS_QUERY).df()
    # Combine into one CSV
    csv_path = out / "01_event_count_distribution.csv"
    with open(csv_path, "w") as f:
        f.write("# Per-replay event count distribution\n")
        distribution.to_csv(f, index=False)
        f.write("\n# Zero-PlayerStats replays\n")
        zero_ps.to_csv(f, index=False)

    # 1.6C — By-year
    by_year = con.execute(_EVENT_DENSITY_BY_YEAR_QUERY).df()
    by_year.to_csv(out / "01_event_density_by_year.csv", index=False)

    # 1.6D — By-tournament with outlier flagging
    by_tournament = con.execute(_EVENT_DENSITY_BY_TOURNAMENT_QUERY).df()
    by_tournament.to_csv(out / "01_event_density_by_tournament.csv", index=False)

    outliers = by_tournament[by_tournament["is_outlier"] == True]  # noqa: E712

    logger.info("Step 1.6 complete")
    return {
        "inventory": inventory.to_dict(orient="records"),
        "zero_playerstats": zero_ps.iloc[0].to_dict() if len(zero_ps) > 0 else {},
        "outlier_tournaments": outliers.to_dict(orient="records"),
    }


# ── Step 1.7 ────────────────────────────────────────────────────────────────


def run_playerstats_sampling_check(
    con: duckdb.DuckDBPyConnection,
    output_dir: Path | None = None,
    games_per_year: int = 10,
) -> dict:
    """Step 1.7 — PlayerStats sampling regularity check."""
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    # Get ranked games per year
    ranked = con.execute(_RANKED_GAMES_PER_YEAR_QUERY).df()

    # Sample deterministically
    rng = random.Random(RANDOM_SEED)
    sampled_ids: list[str] = []
    for year, group in ranked.groupby("year"):
        ids = group["replay_id"].tolist()
        n = min(games_per_year, len(ids))
        sampled_ids.extend(rng.sample(ids, n))

    if not sampled_ids:
        logger.warning("No games with PlayerStats found for sampling check")
        return {"per_game": [], "by_year": [], "flagged_years": []}

    # Get PlayerStats game loops for sampled games
    ps_df = con.execute(_PLAYERSTATS_GAMELOOPS_FOR_SAMPLE_QUERY, [sampled_ids]).df()

    # Compute intervals per (replay_id, player_id)
    ps_df = ps_df.sort_values(["replay_id", "player_id", "game_loop"])
    ps_df["interval"] = ps_df.groupby(["replay_id", "player_id"])["game_loop"].diff()

    # Per-game stats (across all players in that game)
    per_game = (
        ps_df.dropna(subset=["interval"])
        .groupby("replay_id")["interval"]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
        .rename(columns={
            "mean": "mean_diff", "std": "std_diff",
            "min": "min_diff", "max": "max_diff",
        })
    )

    # Add year info
    year_map = ranked.set_index("replay_id")["year"].to_dict()
    per_game["year"] = per_game["replay_id"].map(year_map)

    # By-year aggregation
    by_year = (
        per_game.groupby("year")["mean_diff"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={
            "mean": "year_mean_diff", "std": "year_std_diff", "count": "games_sampled",
        })
    )

    # Flag years with >20% deviation from expected 160
    by_year["deviation_pct"] = (
        (by_year["year_mean_diff"] - _EXPECTED_PLAYERSTATS_INTERVAL).abs()
        / _EXPECTED_PLAYERSTATS_INTERVAL
    )
    by_year["flagged"] = by_year["deviation_pct"] > _INTERVAL_TOLERANCE_PCT
    flagged_years = by_year[by_year["flagged"]]["year"].tolist()

    # Write CSV
    csv_path = out / "01_playerstats_sampling_check.csv"
    with open(csv_path, "w") as f:
        f.write("# Per-game PlayerStats interval stats\n")
        per_game.to_csv(f, index=False)
        f.write("\n# By-year summary\n")
        by_year.to_csv(f, index=False)

    logger.info("Step 1.7 complete")
    return {
        "per_game": per_game.to_dict(orient="records"),
        "by_year": by_year.to_dict(orient="records"),
        "flagged_years": flagged_years,
    }


# ── Orchestrator ────────────────────────────────────────────────────────────


def run_phase_1_exploration(
    con: duckdb.DuckDBPyConnection,
    steps: list[str] | None = None,
) -> dict[str, dict]:
    """Run Phase 1 exploration steps in order."""
    all_steps = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7"]
    run_steps = steps if steps else all_steps
    results: dict[str, dict] = {}

    step_map = {
        "1.1": ("Corpus summary", run_corpus_summary),
        "1.2": ("Parse quality by tournament", run_parse_quality_by_tournament),
        "1.3": ("Duration distribution", run_duration_distribution),
        "1.4": ("APM/MMR audit", run_apm_mmr_audit),
        "1.5": ("Patch landscape", run_patch_landscape),
        "1.6": ("Event type inventory", run_event_type_inventory),
        "1.7": ("PlayerStats sampling check", run_playerstats_sampling_check),
    }

    for step_id in all_steps:
        if step_id in run_steps:
            label, func = step_map[step_id]
            logger.info(f"=== Step {step_id}: {label} ===")
            results[step_id] = func(con)

    logger.info(f"Phase 1 exploration complete. Steps run: {list(results.keys())}")
    return results
