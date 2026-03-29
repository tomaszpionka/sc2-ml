# import logging
# import pandas as pd
# import numpy as np

# logger = logging.getLogger(__name__)

# def perform_feature_engineering(df):
#     logger.info("Rozpoczynam Feature Engineering...")
    
#     # 1. Sortowanie chronologiczne
#     df = df.sort_values('match_time').reset_index(drop=True)
    
#     # 2. Dystans między graczami
#     df['spawn_distance'] = np.sqrt(
#         (df['p1_startLocX'] - df['p2_startLocX'])**2 + 
#         (df['p1_startLocY'] - df['p2_startLocY'])**2
#     )
    
#     # 3. Target w postaci binarnej
#     df['target'] = (df['p1_result'] == 'Win').astype(int)
    
#     # 4. Statystyki kroczące (Historical Win Rate dla P1)
#     # Obliczamy średnią wygranych gracza P1 tylko z meczów poprzedzających obecny
#     df['p1_historical_winrate'] = df.groupby('p1_id')['target'].transform(
#         lambda x: x.expanding().mean().shift(1)
#     )
#     # Dla pierwszego meczu gracza ustalamy domyślny win-rate na poziomie 0.5 (50%)
#     df['p1_historical_winrate'] = df['p1_historical_winrate'].fillna(0.5)
    
#     # 5. One-Hot Encoding dla zmiennych kategorycznych (rasy)
#     # Tworzy kolumny typu p1_race_Prot, p2_race_Zerg itd.
#     df = pd.get_dummies(df, columns=['p1_race', 'p2_race'], drop_first=False)
    
#     # 6. Czyszczenie niepotrzebnych kolumn
#     cols_to_drop = [
#         'match_id', 'p1_id', 'p2_id', 'p1_result', 
#         'p1_startLocX', 'p1_startLocY', 'p2_startLocX', 'p2_startLocY'
#     ]
#     features_df = df.drop(columns=cols_to_drop)
    
#     # Konwersja boolean (z get_dummies) na int
#     for col in features_df.select_dtypes(include=['bool']).columns:
#         features_df[col] = features_df[col].astype(int)
        
#     logger.info(f"Feature Engineering zakończony. Kształt danych: {features_df.shape}")
#     return features_df

# def temporal_train_test_split(df, test_size=0.2):
#     logger.info(f"Chronologiczny podział zbioru (test_size={test_size})...")
    
#     split_index = int(len(df) * (1 - test_size))
    
#     train_df = df.iloc[:split_index]
#     test_df = df.iloc[split_index:]
    
#     X_train = train_df.drop(columns=['target', 'match_time'])
#     y_train = train_df['target']
    
#     X_test = test_df.drop(columns=['target', 'match_time'])
#     y_test = test_df['target']
    
#     logger.info(f"Trening: X={X_train.shape}, y={y_train.shape}")
#     logger.info(f"Test: X={X_test.shape}, y={y_test.shape}")
    
#     return X_train, X_test, y_train, y_test

# iter 2

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def perform_feature_engineering(df):
    logger.info("Rozpoczynam Zaawansowany Feature Engineering...")
    
    # 1. Sortowanie chronologiczne to absolutna podstawa
    df = df.sort_values('match_time').reset_index(drop=True)
    
    # Target
    df['target'] = (df['p1_result'] == 'Win').astype(int)
    
    # Dystans między bazami
    df['spawn_distance'] = np.sqrt(
        (df['p1_startLocX'] - df['p2_startLocX'])**2 + 
        (df['p1_startLocY'] - df['p2_startLocY'])**2
    )

    # --- PARAMETRY BAYESIAN SMOOTHING ---
    C = 5.0          # Waga wygładzania (odpowiada 5 "wirtualnym" rozegranym meczom)
    PRIOR_WR = 0.5   # Zakładamy bazowy winrate 50%
    
    # --- GLOBALNE STATYSTYKI DATASETU DO UZUPEŁNIANIA BRAKÓW ---
    global_mean_apm = df['p1_apm'].mean()
    global_mean_sq = df['p1_sq'].mean()

    # =========================================================================
    # FUNKCJA POMOCNICZA: Szybkie liczenie statystyk historycznych (bez bieżącego meczu)
    # =========================================================================
    def get_historical_sum(groupby_cols, value_col):
        # Skumulowana suma MINUS wartość z obecnego wiersza
        return df.groupby(groupby_cols)[value_col].cumsum() - df[value_col]
        
    def get_historical_count(groupby_cols):
        # cumcount iteruje od 0, więc dokładnie odpowiada liczbie meczów PRZED bieżącym
        return df.groupby(groupby_cols).cumcount()

    # =========================================================================
    # CECHY: DOŚWIADCZENIE (Liczba gier przed tym meczem)
    # =========================================================================
    df['p1_total_games_played'] = get_historical_count('p1_id')
    df['p2_total_games_played'] = get_historical_count('p2_id')

    # =========================================================================
    # CECHY: HISTORYCZNE UMIEJĘTNOŚCI MECHANICZNE (APM & SQ)
    # =========================================================================
    for player_prefix in ['p1', 'p2']:
        hist_apm_sum = get_historical_sum(f'{player_prefix}_id', f'{player_prefix}_apm')
        hist_sq_sum = get_historical_sum(f'{player_prefix}_id', f'{player_prefix}_sq')
        games_played = df[f'{player_prefix}_total_games_played']
        
        # Jeśli gracz nie grał, dajemy mu globalną średnią
        df[f'{player_prefix}_hist_mean_apm'] = np.where(
            games_played > 0, hist_apm_sum / games_played, global_mean_apm
        )
        df[f'{player_prefix}_hist_mean_sq'] = np.where(
            games_played > 0, hist_sq_sum / games_played, global_mean_sq
        )

    # Różnice w mechanice (bardzo silne cechy!)
    df['diff_hist_apm'] = df['p1_hist_mean_apm'] - df['p2_hist_mean_apm']
    df['diff_hist_sq'] = df['p1_hist_mean_sq'] - df['p2_hist_mean_sq']
    df['diff_experience'] = df['p1_total_games_played'] - df['p2_total_games_played']

    # =========================================================================
    # CECHY: BAYESIAN WIN RATES (Ogólny, Rasy, Przeciwko Rasie)
    # =========================================================================
    
    # 1. Ogólny historyczny Win Rate
    p1_prior_wins = get_historical_sum('p1_id', 'target')
    p2_prior_wins = get_historical_sum('p2_id', 'target') # Target dla P2 jest taki sam jak dla P1 (bo P2 w swoich rzędach to P1) - ale w naszym widoku "target" to wynik P1.
    
    # UWAGA: p2_prior_wins musimy liczyć z perspektywy P2. 
    # W `matches_flat` każdy mecz pojawia się 2 razy. Kiedy P2 jest "głównym graczem" (w swoim wierszu), jego wygrane się liczą normalnie.
    # Użyjemy prostej sztuczki:
    df['p2_target_perspective'] = (1 - df['target']) 
    p2_prior_wins_real = df.groupby('p2_id')['p2_target_perspective'].cumsum() - df['p2_target_perspective']

    df['p1_hist_winrate_smooth'] = (p1_prior_wins + C * PRIOR_WR) / (df['p1_total_games_played'] + C)
    df['p2_hist_winrate_smooth'] = (p2_prior_wins_real + C * PRIOR_WR) / (df['p2_total_games_played'] + C)

    # 2. Win Rate konkretną rasą (Biegłość w rasie)
    games_p1_as_race = get_historical_count(['p1_id', 'p1_race'])
    wins_p1_as_race = get_historical_sum(['p1_id', 'p1_race'], 'target')
    df['p1_hist_winrate_as_race_smooth'] = (wins_p1_as_race + C * PRIOR_WR) / (games_p1_as_race + C)

    # 3. Win Rate przeciwko konkretnej rasie (Matchup specific skill)
    games_p1_vs_race = get_historical_count(['p1_id', 'p2_race'])
    wins_p1_vs_race = get_historical_sum(['p1_id', 'p2_race'], 'target')
    df['p1_hist_winrate_vs_race_smooth'] = (wins_p1_vs_race + C * PRIOR_WR) / (games_p1_vs_race + C)

    # =========================================================================
    # CZYSZCZENIE I ONE-HOT ENCODING
    # =========================================================================
    
    df = pd.get_dummies(df, columns=['p1_race', 'p2_race'], drop_first=False)
    
    cols_to_drop = [
        'match_id', 'p1_id', 'p2_id', 'p1_result', 
        'p1_startLocX', 'p1_startLocY', 'p2_startLocX', 'p2_startLocY',
        'p1_apm', 'p2_apm', 'p1_sq', 'p2_sq', 'p2_target_perspective'
    ]
    features_df = df.drop(columns=cols_to_drop)
    
    for col in features_df.select_dtypes(include=['bool']).columns:
        features_df[col] = features_df[col].astype(int)
        
    logger.info(f"Feature Engineering zakończony. Zbudowano {features_df.shape[1]} cech.")
    return features_df

def temporal_train_test_split(df, test_size=0.2):
    split_index = int(len(df) * (1 - test_size))
    train_df, test_df = df.iloc[:split_index], df.iloc[split_index:]
    
    X_train = train_df.drop(columns=['target', 'match_time'])
    y_train = train_df['target']
    
    X_test = test_df.drop(columns=['target', 'match_time'])
    y_test = test_df['target']
    
    return X_train, X_test, y_train, y_test
