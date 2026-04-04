2026-03-30 00:26:12 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-30 00:26:12 - data_processing - INFO - Pobieranie danych do Pandas...
2026-03-30 00:26:12 - SC2_Pipeline - INFO - Aplikuję system relatywnego ELO...
2026-03-30 00:26:12 - elo_system - INFO - Generowanie autorskiego systemu ELO (Wariant B)...
2026-03-30 00:26:13 - elo_system - INFO - Mapowanie ELO z powrotem do głównego zbioru...
2026-03-30 00:26:13 - ml_pipeline - INFO - Rozpoczynam Zaawansowany Feature Engineering (z poprawką na Data Leakage)...
2026-03-30 00:26:13 - ml_pipeline - INFO - Feature Engineering zakończony. Zbudowano 45 czystych cech.
2026-03-30 00:26:13 - SC2_Pipeline - INFO - Oceniamy modele bazowe (teraz na wzbogaconych danych z ELO)...
2026-03-30 00:26:13 - model_training - INFO - Trenowanie modelu: Logistic Regression...

=======================================================
Wyniki: Logistic Regression
-> Accuracy (Cały zbiór testowy, N=8904): 0.6326
-> Accuracy (Tylko Weterani, N=8303):   0.6262
=======================================================
2026-03-30 00:26:13 - model_training - INFO - Trenowanie modelu: Random Forest...

=======================================================
Wyniki: Random Forest
-> Accuracy (Cały zbiór testowy, N=8904): 0.6398
-> Accuracy (Tylko Weterani, N=8303):   0.6330
=======================================================
2026-03-30 00:26:19 - model_training - INFO - Trenowanie modelu: Gradient Boosting...

=======================================================
Wyniki: Gradient Boosting
-> Accuracy (Cały zbiór testowy, N=8904): 0.6453
-> Accuracy (Tylko Weterani, N=8303):   0.6405
=======================================================

--- Top 10 najważniejszych cech (Random Forest) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.138345
               diff_experience    0.098828
        p1_hist_winrate_smooth    0.086147
p1_hist_winrate_as_race_smooth    0.081566
p1_hist_winrate_vs_race_smooth    0.081047
                  diff_hist_sq    0.057725
         p2_total_games_played    0.055878
         p1_total_games_played    0.040541
         diff_hist_game_length    0.032959
                 diff_hist_apm    0.032047
2026-03-30 00:26:20 - SC2_Pipeline - INFO - Rozpoczynam strojenie hiperparametrów Random Forest (Tuning)...
2026-03-30 00:26:20 - hyperparameter_tuning - INFO - Rozpoczynam strojenie hiperparametrów dla Random Forest (Wariant A)...
Fitting 5 folds for each of 50 candidates, totalling 250 fits
2026-03-30 00:30:01 - hyperparameter_tuning - INFO - Najlepsze parametry: {'max_depth': 12, 'max_features': 'sqrt', 'min_samples_leaf': 6, 'min_samples_split': 3, 'n_estimators': 269}
2026-03-30 00:30:01 - hyperparameter_tuning - INFO - Najlepsze CV Accuracy: 0.6292

=================================================================
OSTATECZNY WYNIK (Tuned Random Forest + Time-Aware ELO System)
Accuracy na zbiorze testowym: 0.6458
=================================================================

--- Top 10 Najważniejszych Cech (Po tuningu i wdrożeniu ELO) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.099145
               diff_experience    0.066802
        p1_hist_winrate_smooth    0.060901
p1_hist_winrate_as_race_smooth    0.059870
p1_hist_winrate_vs_race_smooth    0.055318
                  diff_hist_sq    0.049337
         p2_total_games_played    0.046449
         diff_hist_game_length    0.039134
         p1_total_games_played    0.038756
      p2_hist_mean_game_length    0.037969
2026-03-30 00:30:01 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.