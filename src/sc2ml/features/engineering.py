import logging
import pandas as pd
import numpy as np
from config import BAYESIAN_C, BAYESIAN_PRIOR_WR

logger = logging.getLogger(__name__)


def perform_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Build historical pre-match features and remove post-match leakage columns.

    All features are computed as cumulative historical aggregates — they represent
    what was known before the current match started. Current-match stats (APM, SQ,
    supply_capped_pct, game_loops) are dropped at the end to prevent leakage.
    """
    logger.info("Starting feature engineering (leakage-safe historical aggregates)...")

    df = df.sort_values("match_time").reset_index(drop=True)

    df["target"] = (df["p1_result"] == "Win").astype(int)

    # Pre-match map features (known before the game begins)
    df["spawn_distance"] = np.sqrt(
        (df["p1_startLocX"] - df["p2_startLocX"]) ** 2
        + (df["p1_startLocY"] - df["p2_startLocY"]) ** 2
    )
    df["map_area"] = df["map_size_x"] * df["map_size_y"]

    # Global dataset means used as fallbacks for players with no prior history
    global_mean_apm = df["p1_apm"].mean()
    global_mean_sq = df["p1_sq"].mean()
    global_mean_supply = df["p1_supply_capped_pct"].mean()
    global_mean_loops = df["game_loops"].mean()

    def get_historical_sum(groupby_cols: str | list[str], value_col: str) -> pd.Series:
        return df.groupby(groupby_cols)[value_col].cumsum() - df[value_col]

    def get_historical_count(groupby_cols: str | list[str]) -> pd.Series:
        return df.groupby(groupby_cols).cumcount()

    df["p1_total_games_played"] = get_historical_count("p1_name")
    df["p2_total_games_played"] = get_historical_count("p2_name")

    # Historical performance metrics: APM, SQ, supply block rate, preferred game length
    for player_prefix in ["p1", "p2"]:
        games_played = df[f"{player_prefix}_total_games_played"]

        hist_apm_sum = get_historical_sum(
            f"{player_prefix}_name", f"{player_prefix}_apm"
        )
        hist_sq_sum = get_historical_sum(
            f"{player_prefix}_name", f"{player_prefix}_sq"
        )

        df[f"{player_prefix}_hist_mean_apm"] = np.where(
            games_played > 0, hist_apm_sum / games_played, global_mean_apm
        )
        df[f"{player_prefix}_hist_mean_sq"] = np.where(
            games_played > 0, hist_sq_sum / games_played, global_mean_sq
        )

        # Supply block rate: how often the player hits the supply cap historically
        hist_supply_sum = get_historical_sum(
            f"{player_prefix}_name", f"{player_prefix}_supply_capped_pct"
        )
        df[f"{player_prefix}_hist_mean_supply_block"] = np.where(
            games_played > 0, hist_supply_sum / games_played, global_mean_supply
        )

        # Preferred game length: proxy for aggressive vs. macro playstyle
        hist_loops_sum = get_historical_sum(f"{player_prefix}_name", "game_loops")
        df[f"{player_prefix}_hist_mean_game_length"] = np.where(
            games_played > 0, hist_loops_sum / games_played, global_mean_loops
        )

    # Relative differences — strong signal for tree-based models
    df["diff_hist_apm"] = df["p1_hist_mean_apm"] - df["p2_hist_mean_apm"]
    df["diff_hist_sq"] = df["p1_hist_mean_sq"] - df["p2_hist_mean_sq"]
    df["diff_hist_supply_block"] = (
        df["p1_hist_mean_supply_block"] - df["p2_hist_mean_supply_block"]
    )
    df["diff_hist_game_length"] = (
        df["p1_hist_mean_game_length"] - df["p2_hist_mean_game_length"]
    )
    df["diff_experience"] = df["p1_total_games_played"] - df["p2_total_games_played"]

    # Bayesian-smoothed win rates (C and prior from config)
    p1_prior_wins = get_historical_sum("p1_name", "target")
    df["p2_target_perspective"] = 1 - df["target"]
    p2_prior_wins_real = (
        df.groupby("p2_name")["p2_target_perspective"].cumsum()
        - df["p2_target_perspective"]
    )

    df["p1_hist_winrate_smooth"] = (p1_prior_wins + BAYESIAN_C * BAYESIAN_PRIOR_WR) / (
        df["p1_total_games_played"] + BAYESIAN_C
    )
    df["p2_hist_winrate_smooth"] = (p2_prior_wins_real + BAYESIAN_C * BAYESIAN_PRIOR_WR) / (
        df["p2_total_games_played"] + BAYESIAN_C
    )

    # Race-specific win rates (as this race, vs this race)
    games_p1_as_race = get_historical_count(["p1_name", "p1_race"])
    wins_p1_as_race = get_historical_sum(["p1_name", "p1_race"], "target")
    df["p1_hist_winrate_as_race_smooth"] = (
        wins_p1_as_race + BAYESIAN_C * BAYESIAN_PRIOR_WR
    ) / (games_p1_as_race + BAYESIAN_C)

    games_p1_vs_race = get_historical_count(["p1_name", "p2_race"])
    wins_p1_vs_race = get_historical_sum(["p1_name", "p2_race"], "target")
    df["p1_hist_winrate_vs_race_smooth"] = (
        wins_p1_vs_race + BAYESIAN_C * BAYESIAN_PRIOR_WR
    ) / (games_p1_vs_race + BAYESIAN_C)

    # One-hot encode race columns
    df = pd.get_dummies(df, columns=["p1_race", "p2_race"], drop_first=False)

    # Drop all current-match stats that are not known before the match starts
    cols_to_drop = [
        "p1_result",
        "p1_startLocX",
        "p1_startLocY",
        "p2_startLocX",
        "p2_startLocY",
        "p1_apm",
        "p2_apm",
        "p1_sq",
        "p2_sq",
        "p1_supply_capped_pct",
        "p2_supply_capped_pct",
        "game_loops",
        # "data_build",  # kept for per-patch analysis
        "p2_target_perspective",
        "map_size_x",
        "map_size_y",
        "tournament_name",
        "map_name",
    ]
    features_df = df.drop(columns=cols_to_drop, errors="ignore")

    for col in features_df.select_dtypes(include=["bool"]).columns:
        features_df[col] = features_df[col].astype(int)

    logger.info(
        f"Feature engineering complete. Built {features_df.shape[1]} clean features "
        "(includes ID and name columns retained for GNN)."
    )
    return features_df


def temporal_train_test_split(
    df: pd.DataFrame, test_size: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split the dataset chronologically into train and test sets.

    Non-feature columns (target, match metadata, player names) are dropped from
    X before returning. The dataframe must already be sorted by match_time.
    """
    split_index = int(len(df) * (1 - test_size))
    train_df, test_df = df.iloc[:split_index], df.iloc[split_index:]

    # Remove columns that are not ML features or would cause leakage
    cols_to_drop_for_ml = ["target", "match_time", "match_id", "p1_name", "p2_name"]
    drop_cols = [c for c in cols_to_drop_for_ml if c in train_df.columns]

    X_train = train_df.drop(columns=drop_cols)
    y_train = train_df["target"]

    X_test = test_df.drop(columns=drop_cols)
    y_test = test_df["target"]

    return X_train, X_test, y_train, y_test
