2026-03-29 19:56:00 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-29 19:56:00 - data_processing - INFO - Tworzenie zaktualizowanych widoków ML w DuckDB (z APM i SQ)...
2026-03-29 19:56:00 - data_processing - INFO - Widok 'matches_flat' gotowy.
2026-03-29 19:56:00 - data_processing - INFO - Pobieranie danych do Pandas...
2026-03-29 19:56:00 - ml_pipeline - INFO - Rozpoczynam Zaawansowany Feature Engineering...
2026-03-29 19:56:00 - ml_pipeline - INFO - Feature Engineering zakończony. Zbudowano 22 cech.
2026-03-29 19:56:00 - SC2_Pipeline - INFO - Dane gotowe. Uruchamiam trenowanie i ewaluację modeli...
2026-03-29 19:56:00 - model_training - INFO - Trenowanie modelu: Logistic Regression...
2026-03-29 19:56:01 - model_training - INFO - Logistic Regression - Accuracy na zbiorze testowym: 0.5453

========================================
Raport Klasyfikacji: Logistic Regression
========================================
              precision    recall  f1-score   support

           0       0.54      0.55      0.55       259
           1       0.55      0.54      0.54       260

    accuracy                           0.55       519
   macro avg       0.55      0.55      0.55       519
weighted avg       0.55      0.55      0.55       519

2026-03-29 19:56:01 - model_training - INFO - Trenowanie modelu: Random Forest...
2026-03-29 19:56:02 - model_training - INFO - Random Forest - Accuracy na zbiorze testowym: 0.5491

========================================
Raport Klasyfikacji: Random Forest
========================================
              precision    recall  f1-score   support

           0       0.55      0.53      0.54       259
           1       0.55      0.57      0.56       260

    accuracy                           0.55       519
   macro avg       0.55      0.55      0.55       519
weighted avg       0.55      0.55      0.55       519

2026-03-29 19:56:02 - model_training - INFO - Trenowanie modelu: Gradient Boosting...
2026-03-29 19:56:03 - model_training - INFO - Gradient Boosting - Accuracy na zbiorze testowym: 0.5241

========================================
Raport Klasyfikacji: Gradient Boosting
========================================
              precision    recall  f1-score   support

           0       0.52      0.53      0.53       259
           1       0.53      0.52      0.52       260

    accuracy                           0.52       519
   macro avg       0.52      0.52      0.52       519
weighted avg       0.52      0.52      0.52       519


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
2026-03-29 19:56:03 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.