2026-03-29 20:27:00 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-29 20:27:00 - data_processing - INFO - Tworzenie zaktualizowanych widoków ML w DuckDB (nowe cechy: czas, supply, clan, mapa)...
2026-03-29 20:27:00 - data_processing - INFO - Widok 'matches_flat' gotowy.
2026-03-29 20:27:00 - data_processing - INFO - Pobieranie danych do Pandas...
2026-03-29 20:27:00 - ml_pipeline - INFO - Rozpoczynam Zaawansowany Feature Engineering (z poprawką na Data Leakage)...
2026-03-29 20:27:00 - ml_pipeline - INFO - Feature Engineering zakończony. Zbudowano 31 czystych cech.
2026-03-29 20:27:00 - SC2_Pipeline - INFO - Dane gotowe. Uruchamiam trenowanie i ewaluację modeli...
2026-03-29 20:27:00 - model_training - INFO - Trenowanie modelu: Logistic Regression...

=======================================================
Wyniki: Logistic Regression
-> Accuracy (Cały zbiór testowy, N=519): 0.5337
-> Accuracy (Tylko Weterani, N=423):   0.5508
=======================================================
2026-03-29 20:27:01 - model_training - INFO - Trenowanie modelu: Random Forest...

=======================================================
Wyniki: Random Forest
-> Accuracy (Cały zbiór testowy, N=519): 0.5800
-> Accuracy (Tylko Weterani, N=423):   0.5863
=======================================================
2026-03-29 20:27:03 - model_training - INFO - Trenowanie modelu: Gradient Boosting...

=======================================================
Wyniki: Gradient Boosting
-> Accuracy (Cały zbiór testowy, N=519): 0.5279
-> Accuracy (Tylko Weterani, N=423):   0.5296
=======================================================

--- Top 10 najważniejszych cech (Random Forest) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.105329
        p1_hist_winrate_smooth    0.067323
p1_hist_winrate_as_race_smooth    0.064694
p1_hist_winrate_vs_race_smooth    0.060024
                  diff_hist_sq    0.058213
      p1_hist_mean_game_length    0.056558
      p2_hist_mean_game_length    0.055745
         diff_hist_game_length    0.054584
               p1_hist_mean_sq    0.050720
                 diff_hist_apm    0.049442
2026-03-29 20:27:12 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.