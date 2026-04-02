# Project Architecture

## Package Layout (`src/sc2ml/`)

- `cli.py` — pipeline orchestrator, configurable model selection (`CLASSIC`, `NODE2VEC`, `GNN`)
- `config.py` — path constants, ML hyperparameters, reproducibility settings
- `data/ingestion.py` — replay JSON parsing, DuckDB loading, map translations
- `data/processing.py` — SQL view creation (`flat_players`, `matches_flat`), data validation
- `features/engineering.py` — feature engineering (45+ features, Bayesian smoothing), temporal train/test split
- `features/elo.py` — custom ELO rating with dynamic K-factor (K=64 new, K=32 veteran)
- `models/classical.py` — classical ML training/evaluation (LR, RF, GB, XGB, LGBM)
- `models/tuning.py` — RandomizedSearchCV for Random Forest
- `gnn/model.py` — SC2EdgeClassifier (GATv2Conv-based edge classifier)
- `gnn/pipeline.py` — graph construction from player features (node + edge features)
- `gnn/trainer.py` — GNN training loop with early stopping
- `gnn/visualizer.py` — t-SNE visualization of learned GNN embeddings
- `gnn/embedder.py` — Node2Vec embeddings via NetworkX/Gensim

## Directories

- `models/` — serialized model artifacts (`.joblib`, `.pt`)
- `reports/` — research log and visualization outputs
- `reports/archive/` — legacy pipeline execution logs (`01_run.md` through `09_run.md`)
- `logs/` — pipeline log file (`sc2_pipeline.log`)
- `tests/` — pytest test suite (root level)
- `src/sc2ml/data/tests/` — data subpackage tests

## External Data Paths (from `config.py`)

- `~/duckdb_work/test_sc2.duckdb` — main DuckDB database
- `~/duckdb_work/tmp/` — DuckDB temp directory
- `~/Downloads/SC2_Replays/` — raw SC2Replay JSON files

## Data Pipeline (5 Stages)

1. **Ingestion** — `slim_down_sc2_with_manifest()` strips heavy replay events; `move_data_to_duck_db()` loads JSON into DuckDB `raw` table; `load_map_translations()` populates map name lookup
2. **SQL Processing** — `create_ml_views()` creates `flat_players` (one row per player per match) and `matches_flat` (paired players per match with features)
3. **ELO Computation** — `add_elo_features()` computes pre-match ELO with dynamic K-factor
4. **Feature Engineering** — `perform_feature_engineering()` builds historical rolling features (Bayesian-smoothed win rates, cumulative stats, race-specific rates). Drops post-match leakage columns.
5. **Model Training** (3 paths):
   - `CLASSIC` — tabular ML models with temporal split
   - `NODE2VEC` — graph embeddings appended to tabular features, then classical models
   - `GNN` — end-to-end GATv2-based edge classification

## Known Design Decisions

- `matches_flat` produces 2 rows per match (p1/p2 and p2/p1 perspective) — intentional data augmentation; raw row count is ~2x actual unique matches
- ELO system processes each unique `match_id` only once via `processed_matches` set, despite the paired rows
- Feature engineering's cumulative operations assume chronological sorting — **never shuffle the dataframe before feature engineering**
- The GNN uses **edge classification** (predicting match outcome from player node embeddings + edge features), not node classification — a less common PyG pattern
- DuckDB configured for 24GB RAM, 4 threads (tuned for high-memory machine)
- `processing_manifest.json` (2MB) tracks which replay files have been processed; committed to git
