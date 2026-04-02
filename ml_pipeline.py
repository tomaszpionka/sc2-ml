import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def perform_feature_engineering(df):
    logger.info(
        "Rozpoczynam Zaawansowany Feature Engineering (z poprawką na Data Leakage)..."
    )

    # 1. Sortowanie chronologiczne
    df = df.sort_values("match_time").reset_index(drop=True)

    # Target
    df["target"] = (df["p1_result"] == "Win").astype(int)

    # Dystans między bazami i rozmiar mapy (Legalne cechy pre-match)
    df["spawn_distance"] = np.sqrt(
        (df["p1_startLocX"] - df["p2_startLocX"]) ** 2
        + (df["p1_startLocY"] - df["p2_startLocY"]) ** 2
    )
    df["map_area"] = df["map_size_x"] * df["map_size_y"]

    # --- PARAMETRY BAYESIAN SMOOTHING ---
    C = 5.0
    PRIOR_WR = 0.5

    # --- GLOBALNE STATYSTYKI DATASETU ---
    global_mean_apm = df["p1_apm"].mean()
    global_mean_sq = df["p1_sq"].mean()
    global_mean_supply = df["p1_supply_capped_pct"].mean()
    global_mean_loops = df["game_loops"].mean()

    def get_historical_sum(groupby_cols, value_col):
        return df.groupby(groupby_cols)[value_col].cumsum() - df[value_col]

    def get_historical_count(groupby_cols):
        return df.groupby(groupby_cols).cumcount()

    df["p1_total_games_played"] = get_historical_count("p1_name")
    df["p2_total_games_played"] = get_historical_count("p2_name")

    # =========================================================================
    # CECHY HISTORYCZNE: APM, SQ, Supply Block, Czas Gry
    # =========================================================================
    for player_prefix in ["p1", "p2"]:
        games_played = df[f"{player_prefix}_total_games_played"]

        # APM & SQ
        hist_apm_sum = get_historical_sum(
            f"{player_prefix}_name", f"{player_prefix}_apm"
        )
        hist_sq_sum = get_historical_sum(f"{player_prefix}_name", f"{player_prefix}_sq")

        df[f"{player_prefix}_hist_mean_apm"] = np.where(
            games_played > 0, hist_apm_sum / games_played, global_mean_apm
        )
        df[f"{player_prefix}_hist_mean_sq"] = np.where(
            games_played > 0, hist_sq_sum / games_played, global_mean_sq
        )

        # Supply Block (Jak bardzo gracz "zapomina" w przeszłości)
        hist_supply_sum = get_historical_sum(
            f"{player_prefix}_name", f"{player_prefix}_supply_capped_pct"
        )
        df[f"{player_prefix}_hist_mean_supply_block"] = np.where(
            games_played > 0, hist_supply_sum / games_played, global_mean_supply
        )

        # Preferencje długości gry (Czy gracz to "Rusznikarz" czy "Żółw")
        hist_loops_sum = get_historical_sum(f"{player_prefix}_name", "game_loops")
        df[f"{player_prefix}_hist_mean_game_length"] = np.where(
            games_played > 0, hist_loops_sum / games_played, global_mean_loops
        )

    # RÓŻNICE (Silne cechy dla modeli drzewiastych)
    df["diff_hist_apm"] = df["p1_hist_mean_apm"] - df["p2_hist_mean_apm"]
    df["diff_hist_sq"] = df["p1_hist_mean_sq"] - df["p2_hist_mean_sq"]
    df["diff_hist_supply_block"] = (
        df["p1_hist_mean_supply_block"] - df["p2_hist_mean_supply_block"]
    )
    df["diff_hist_game_length"] = (
        df["p1_hist_mean_game_length"] - df["p2_hist_mean_game_length"]
    )
    df["diff_experience"] = df["p1_total_games_played"] - df["p2_total_games_played"]

    # =========================================================================
    # BAYESIAN WIN RATES
    # =========================================================================
    p1_prior_wins = get_historical_sum("p1_name", "target")
    df["p2_target_perspective"] = 1 - df["target"]
    p2_prior_wins_real = (
        df.groupby("p2_name")["p2_target_perspective"].cumsum()
        - df["p2_target_perspective"]
    )

    df["p1_hist_winrate_smooth"] = (p1_prior_wins + C * PRIOR_WR) / (
        df["p1_total_games_played"] + C
    )
    df["p2_hist_winrate_smooth"] = (p2_prior_wins_real + C * PRIOR_WR) / (
        df["p2_total_games_played"] + C
    )

    games_p1_as_race = get_historical_count(["p1_name", "p1_race"])
    wins_p1_as_race = get_historical_sum(["p1_name", "p1_race"], "target")
    df["p1_hist_winrate_as_race_smooth"] = (wins_p1_as_race + C * PRIOR_WR) / (
        games_p1_as_race + C
    )

    games_p1_vs_race = get_historical_count(["p1_name", "p2_race"])
    wins_p1_vs_race = get_historical_sum(["p1_name", "p2_race"], "target")
    df["p1_hist_winrate_vs_race_smooth"] = (wins_p1_vs_race + C * PRIOR_WR) / (
        games_p1_vs_race + C
    )

    # =========================================================================
    # CZYSZCZENIE DANYCH (ZABEZPIECZENIE PRZED WYCIEKIEM)
    # =========================================================================
    df = pd.get_dummies(df, columns=["p1_race", "p2_race"], drop_first=False)

    # UWAGA: Wyrzucamy wszystko, co dotyczy BIEŻĄCEGO meczu i nie jest znane w lobby.
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
        # "data_build",
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
        f"Feature Engineering zakończony. Zbudowano {features_df.shape[1]} czystych cech (zawiera ID i nazwy dla GNN)."
    )
    return features_df


def temporal_train_test_split(df, test_size=0.2):
    split_index = int(len(df) * (1 - test_size))
    train_df, test_df = df.iloc[:split_index], df.iloc[split_index:]

    # Tutaj ostatecznie odcinamy tekstowe zmienne przed wpuszczeniem do XGBoost / RF
    cols_to_drop_for_ml = ["target", "match_time", "match_id", "p1_name", "p2_name"]

    # Bezpieczne usuwanie (tylko tych kolumn, które faktycznie istnieją w DF)
    drop_cols = [c for c in cols_to_drop_for_ml if c in train_df.columns]

    X_train = train_df.drop(columns=drop_cols)
    y_train = train_df["target"]

    X_test = test_df.drop(columns=drop_cols)
    y_test = test_df["target"]

    return X_train, X_test, y_train, y_test
