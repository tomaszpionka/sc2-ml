"""Data ingestion, processing, and temporal splitting for the SC2 ML pipeline.

Submodules:
    ingestion   — Raw replay loading (JSON to DuckDB) and in-game event extraction
                  (replay to Parquet to DuckDB).
    processing  — DuckDB view creation, series grouping, and temporal train/val/test
                  splitting with tournament-level boundaries.
    cv          — Expanding-window temporal cross-validator with series-aware
                  fold boundaries for scikit-learn integration.
"""
