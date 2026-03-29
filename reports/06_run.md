2026-03-29 20:25:08 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-29 20:25:08 - data_processing - INFO - Tworzenie zaktualizowanych widoków ML w DuckDB (nowe cechy: czas, supply, clan, mapa)...
2026-03-29 20:25:08 - data_processing - INFO - Widok 'matches_flat' gotowy.
2026-03-29 20:25:08 - data_processing - INFO - Pobieranie danych do Pandas...
2026-03-29 20:25:08 - ml_pipeline - INFO - Rozpoczynam Zaawansowany Feature Engineering...
2026-03-29 20:25:08 - ml_pipeline - INFO - Feature Engineering zakończony. Zbudowano 30 cech.
2026-03-29 20:25:08 - SC2_Pipeline - INFO - Dane gotowe. Uruchamiam trenowanie i ewaluację modeli...
2026-03-29 20:25:08 - model_training - INFO - Trenowanie modelu: Logistic Regression...

=======================================================
Wyniki: Logistic Regression
-> Accuracy (Cały zbiór testowy, N=519): 0.5530
-> Accuracy (Tylko Weterani, N=423):   0.5697
=======================================================
2026-03-29 20:25:09 - model_training - INFO - Trenowanie modelu: Random Forest...

=======================================================
Wyniki: Random Forest
-> Accuracy (Cały zbiór testowy, N=519): 0.5645
-> Accuracy (Tylko Weterani, N=423):   0.5745
=======================================================
2026-03-29 20:25:10 - model_training - INFO - Trenowanie modelu: Gradient Boosting...

=======================================================
Wyniki: Gradient Boosting
-> Accuracy (Cały zbiór testowy, N=519): 0.5087
-> Accuracy (Tylko Weterani, N=423):   0.5154
=======================================================

--- Top 10 najważniejszych cech (Random Forest) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.117702
p1_hist_winrate_as_race_smooth    0.078372
        p1_hist_winrate_smooth    0.072776
                  diff_hist_sq    0.068667
p1_hist_winrate_vs_race_smooth    0.063205
               p2_hist_mean_sq    0.062116
                 diff_hist_apm    0.060918
               p1_hist_mean_sq    0.057961
              p2_hist_mean_apm    0.057766
                    game_loops    0.054922
2026-03-29 20:25:13 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.