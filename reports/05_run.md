2026-03-29 20:02:10 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-29 20:02:10 - data_processing - INFO - Tworzenie zaktualizowanych widoków ML w DuckDB (z APM i SQ)...
2026-03-29 20:02:10 - data_processing - INFO - Widok 'matches_flat' gotowy.
2026-03-29 20:02:10 - data_processing - INFO - Pobieranie danych do Pandas...
2026-03-29 20:02:10 - ml_pipeline - INFO - Rozpoczynam Zaawansowany Feature Engineering...
2026-03-29 20:02:10 - ml_pipeline - INFO - Feature Engineering zakończony. Zbudowano 22 cech.
2026-03-29 20:02:10 - SC2_Pipeline - INFO - Dane gotowe. Uruchamiam trenowanie i ewaluację modeli...
2026-03-29 20:02:10 - model_training - INFO - Trenowanie modelu: Logistic Regression...

=======================================================
Wyniki: Logistic Regression
-> Accuracy (Cały zbiór testowy, N=519): 0.5453
-> Accuracy (Tylko Weterani, N=423):   0.5650
=======================================================
2026-03-29 20:02:10 - model_training - INFO - Trenowanie modelu: Random Forest...

=======================================================
Wyniki: Random Forest
-> Accuracy (Cały zbiór testowy, N=519): 0.5491
-> Accuracy (Tylko Weterani, N=423):   0.5485
=======================================================
2026-03-29 20:02:12 - model_training - INFO - Trenowanie modelu: Gradient Boosting...

=======================================================
Wyniki: Gradient Boosting
-> Accuracy (Cały zbiór testowy, N=519): 0.5241
-> Accuracy (Tylko Weterani, N=423):   0.5201
=======================================================

--- Top 10 najważniejszych cech (Random Forest) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.132719
p1_hist_winrate_as_race_smooth    0.085888
        p1_hist_winrate_smooth    0.082078
                  diff_hist_sq    0.079468
                 diff_hist_apm    0.076749
p1_hist_winrate_vs_race_smooth    0.075635
               p2_hist_mean_sq    0.072440
              p2_hist_mean_apm    0.072153
               p1_hist_mean_sq    0.070924
              p1_hist_mean_apm    0.069094
2026-03-29 20:02:15 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.