2026-03-29 18:38:46 - SC2_Pipeline - INFO - Start SC2 ML Pipeline...
2026-03-29 18:38:46 - data_processing - INFO - Creating flattened ML views in DuckDB...
2026-03-29 18:38:46 - data_processing - INFO - View 'matches_flat' created successfully.
2026-03-29 18:38:46 - data_processing - INFO - Fetching data to Pandas DataFrame...
2026-03-29 18:38:46 - ml_pipeline - INFO - Rozpoczynam Feature Engineering...
2026-03-29 18:38:46 - ml_pipeline - INFO - Feature Engineering zakończony. Kształt danych: (2592, 10)
2026-03-29 18:38:46 - ml_pipeline - INFO - Chronologiczny podział zbioru (test_size=0.2)...
2026-03-29 18:38:46 - ml_pipeline - INFO - Trening: X=(2073, 8), y=(2073,)
2026-03-29 18:38:46 - ml_pipeline - INFO - Test: X=(519, 8), y=(519,)
2026-03-29 18:38:46 - SC2_Pipeline - INFO - Dane gotowe. Uruchamiam trenowanie i ewaluację modeli...
2026-03-29 18:38:46 - model_training - INFO - Trenowanie modelu: Logistic Regression...
2026-03-29 18:38:47 - model_training - INFO - Logistic Regression - Accuracy na zbiorze testowym: 0.5279

========================================
Raport Klasyfikacji: Logistic Regression
========================================
              precision    recall  f1-score   support

           0       0.55      0.29      0.38       259
           1       0.52      0.77      0.62       260

    accuracy                           0.53       519
   macro avg       0.54      0.53      0.50       519
weighted avg       0.54      0.53      0.50       519

2026-03-29 18:38:48 - model_training - INFO - Trenowanie modelu: Random Forest...
2026-03-29 18:38:48 - model_training - INFO - Random Forest - Accuracy na zbiorze testowym: 0.4798

========================================
Raport Klasyfikacji: Random Forest
========================================
              precision    recall  f1-score   support

           0       0.48      0.44      0.46       259
           1       0.48      0.52      0.50       260

    accuracy                           0.48       519
   macro avg       0.48      0.48      0.48       519
weighted avg       0.48      0.48      0.48       519


--- Top 10 najważniejszych cech (Random Forest) ---
              Feature  Importance
p1_historical_winrate    0.722270
       spawn_distance    0.198634
         p1_race_Zerg    0.016132
         p1_race_Prot    0.013456
         p2_race_Prot    0.013016
         p1_race_Terr    0.012824
         p2_race_Terr    0.012217
         p2_race_Zerg    0.011451
2026-03-29 18:38:48 - SC2_Pipeline - INFO - Połączenie z DuckDB zamknięte.