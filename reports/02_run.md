2026-03-29 18:52:02 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-29 18:52:02 - data_processing - INFO - Tworzenie zaktualizowanych widoków ML w DuckDB (z APM i SQ)...
2026-03-29 18:52:02 - data_processing - INFO - Widok 'matches_flat' gotowy.
2026-03-29 18:52:02 - data_processing - INFO - Pobieranie danych do Pandas...
2026-03-29 18:52:02 - ml_pipeline - INFO - Rozpoczynam Zaawansowany Feature Engineering...
2026-03-29 18:52:02 - ml_pipeline - INFO - Feature Engineering zakończony. Zbudowano 22 cech.
2026-03-29 18:52:02 - SC2_Pipeline - INFO - Dane gotowe. Uruchamiam trenowanie i ewaluację modeli...
2026-03-29 18:52:02 - model_training - INFO - Trenowanie modelu: Logistic Regression...
/home/tomasz/projects/sc2-ml/.venv/lib/python3.12/site-packages/sklearn/linear_model/_logistic.py:406: ConvergenceWarning: lbfgs failed to converge after 1000 iteration(s) (status=1):
STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT

Increase the number of iterations to improve the convergence (max_iter=1000).
You might also want to scale the data as shown in:
    https://scikit-learn.org/stable/modules/preprocessing.html
Please also refer to the documentation for alternative solver options:
    https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression
  n_iter_i = _check_optimize_result(
2026-03-29 18:52:07 - model_training - INFO - Logistic Regression - Accuracy na zbiorze testowym: 0.5857

========================================
Raport Klasyfikacji: Logistic Regression
========================================
              precision    recall  f1-score   support

           0       0.59      0.58      0.58       259
           1       0.59      0.59      0.59       260

    accuracy                           0.59       519
   macro avg       0.59      0.59      0.59       519
weighted avg       0.59      0.59      0.59       519

2026-03-29 18:52:07 - model_training - INFO - Trenowanie modelu: Random Forest...
2026-03-29 18:52:07 - model_training - INFO - Random Forest - Accuracy na zbiorze testowym: 0.5568

========================================
Raport Klasyfikacji: Random Forest
========================================
              precision    recall  f1-score   support

           0       0.56      0.55      0.55       259
           1       0.56      0.56      0.56       260

    accuracy                           0.56       519
   macro avg       0.56      0.56      0.56       519
weighted avg       0.56      0.56      0.56       519


--- Top 10 najważniejszych cech (Random Forest) ---
                       Feature  Importance
        p2_hist_winrate_smooth    0.116822
                  diff_hist_sq    0.081143
        p1_hist_winrate_smooth    0.078887
p1_hist_winrate_as_race_smooth    0.078009
              p2_hist_mean_apm    0.075425
                 diff_hist_apm    0.075297
               p1_hist_mean_sq    0.075122
              p1_hist_mean_apm    0.074505
               p2_hist_mean_sq    0.073729
p1_hist_winrate_vs_race_smooth    0.066678
2026-03-29 18:52:08 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.