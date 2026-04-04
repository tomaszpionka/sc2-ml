2026-03-29 22:08:15 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-29 22:08:15 - data_ingestion - INFO - Loaded manifest: 22103 files tracked.
2026-03-29 22:08:18 - data_ingestion - INFO - Manifest updated and saved.
2026-03-29 22:08:18 - data_ingestion - INFO - New files processed: 0. Disk space saved: 0.0000 GB
2026-03-29 22:08:18 - data_ingestion - INFO - Setting up DuckDB optimizations (Anti-OOM configuration)...
2026-03-29 22:08:18 - data_ingestion - INFO - Scanning JSONs into DuckDB: /home/tomasz/Downloads/SC2_Replays/**/data/*.SC2Replay.json
2026-03-29 22:08:19 - data_ingestion - INFO - DuckDB Ingestion complete. Total replays in 'raw': 22103
2026-03-29 22:08:19 - data_ingestion - INFO - Szukam słowników tłumaczeń map...
2026-03-29 22:08:19 - data_ingestion - INFO - Załadowano 1488 unikalnych tłumaczeń map do bazy DuckDB.
2026-03-29 22:08:19 - data_processing - INFO - Tworzenie zaktualizowanych widoków ML w DuckDB (tłumaczenia map i unifikacja nicków)...
2026-03-29 22:08:19 - data_processing - INFO - Widok 'matches_flat' gotowy.
2026-03-29 22:08:19 - data_processing - INFO - Pobieranie danych do Pandas...
2026-03-29 22:08:21 - SC2_Pipeline - INFO - Aplikuję system relatywnego ELO...
2026-03-29 22:08:21 - elo_system - INFO - Generowanie autorskiego systemu ELO (Wariant B)...
2026-03-29 22:08:24 - elo_system - INFO - Mapowanie ELO z powrotem do głównego zbioru...
2026-03-29 22:08:27 - ml_pipeline - INFO - Rozpoczynam Zaawansowany Feature Engineering (z poprawką na Data Leakage)...
2026-03-29 22:08:27 - ml_pipeline - INFO - Feature Engineering zakończony. Zbudowano 45 czystych cech.
2026-03-29 22:08:27 - SC2_Pipeline - INFO - Oceniamy modele bazowe (teraz na wzbogaconych danych z ELO)...
2026-03-29 22:08:27 - model_training - INFO - Trenowanie modelu: Logistic Regression...

=======================================================
Wyniki: Logistic Regression
-> Accuracy (Cały zbiór testowy, N=8904): 0.6325
-> Accuracy (Tylko Weterani, N=8303):   0.6262
=======================================================
2026-03-29 22:08:28 - model_training - INFO - Trenowanie modelu: Random Forest...

=======================================================
Wyniki: Random Forest
-> Accuracy (Cały zbiór testowy, N=8904): 0.6420
-> Accuracy (Tylko Weterani, N=8303):   0.6351
=======================================================
2026-03-29 22:08:49 - model_training - INFO - Trenowanie modelu: Gradient Boosting...

=======================================================
Wyniki: Gradient Boosting
-> Accuracy (Cały zbiór testowy, N=8904): 0.6508
-> Accuracy (Tylko Weterani, N=8303):   0.6454
=======================================================

--- Top 10 najważniejszych cech (Random Forest) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.137404
               diff_experience    0.097905
p1_hist_winrate_as_race_smooth    0.085011
        p1_hist_winrate_smooth    0.081261
p1_hist_winrate_vs_race_smooth    0.078779
         p2_total_games_played    0.056982
                  diff_hist_sq    0.055103
         p1_total_games_played    0.041958
               p2_hist_mean_sq    0.034121
         diff_hist_game_length    0.034038
2026-03-29 22:08:51 - SC2_Pipeline - INFO - Rozpoczynam strojenie hiperparametrów Random Forest (Tuning)...
2026-03-29 22:08:51 - hyperparameter_tuning - INFO - Rozpoczynam strojenie hiperparametrów dla Random Forest (Wariant A)...
Fitting 5 folds for each of 50 candidates, totalling 250 fits
2026-03-29 22:30:41 - hyperparameter_tuning - INFO - Najlepsze parametry: {'max_depth': 12, 'max_features': 'sqrt', 'min_samples_leaf': 6, 'min_samples_split': 6, 'n_estimators': 471}
2026-03-29 22:30:41 - hyperparameter_tuning - INFO - Najlepsze CV Accuracy: 0.6283

=================================================================
OSTATECZNY WYNIK (Tuned Random Forest + Time-Aware ELO System)
Accuracy na zbiorze testowym: 0.6418
=================================================================

--- Top 10 Najważniejszych Cech (Po tuningu i wdrożeniu ELO) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.097801
               diff_experience    0.068837
p1_hist_winrate_as_race_smooth    0.060377
        p1_hist_winrate_smooth    0.058931
p1_hist_winrate_vs_race_smooth    0.055950
                  diff_hist_sq    0.049383
         p2_total_games_played    0.046109
         diff_hist_game_length    0.038804
         p1_total_games_played    0.038351
      p2_hist_mean_game_length    0.038191
2026-03-29 22:30:41 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.