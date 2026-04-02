# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/).

## [Unreleased]

### Changed
- Translated all Polish comments and log strings to English across all 13 Python modules
- Added type hints to all function signatures (parameters and return types) in all modules
- Extracted 60+ magic numbers into named constants in `config.py` (ELO K-factors, Bayesian
  smoothing params, GNN architecture, Node2Vec walk config, t-SNE params, classical model
  hyperparameters, tuning settings, patch analysis threshold)
- Moved hardcoded model checkpoint path and visualization output path to `config.py`

### Added
- `pyproject.toml` with Poetry dependency management
- Project-specific `.gitignore` entries for model artifacts, logs, and scratch files
- `config.py`: `RANDOM_SEED`, `MODELS_DIR`, `GNN_CHECKPOINT_PATH`, `GNN_VIZ_OUTPUT_PATH`,
  `ELO_K_NEW/VETERAN/THRESHOLD`, `VETERAN_MIN_GAMES`, `BAYESIAN_C/PRIOR_WR`,
  `GNN_HIDDEN_DIM`, `GNN_HEADS_CONV1/CONV2`, `GNN_DROPOUT`, `GNN_LEARNING_RATE/WEIGHT_DECAY/
  PATIENCE/LOG_EVERY`, `NODE2VEC_*`, `NODE_FALLBACK_*`, `TSNE_*`, `VIZ_DPI`,
  `RF_*`, `HGB_*`, `LR_MAX_ITER`, `TUNING_N_ITER/CV_FOLDS`, `PATCH_MIN_MATCHES`
- `tests/` directory with initial test suite (data validation, feature engineering,
  graph construction, model reproducibility)
- Rich CLAUDE.md guidelines for Claude Code collaboration
- CHANGELOG.md for structured version tracking
- Research log (`reports/research_log.md`) for thesis documentation trail

### Removed
- Dead commented-out legacy `main()` function block from `main.py` (~100 lines)

### Fixed
- Test fixture now drops non-numeric columns (e.g. `data_build`) before passing to sklearn

## [0.1.0] — 2026-03-30 (Baseline)

### Added
- SC2 data ingestion pipeline with manifest tracking (`data_ingestion.py`)
- DuckDB-based data processing with SQL views (`data_processing.py`)
- Feature engineering with 45+ features and Bayesian smoothing (`ml_pipeline.py`)
- Custom ELO rating system with dynamic K-factor (`elo_system.py`)
- Classical ML baselines: Logistic Regression, Random Forest, Gradient Boosting, XGBoost, LightGBM (`model_training.py`)
- Random Forest hyperparameter tuning via RandomizedSearchCV (`hyperparameter_tuning.py`)
- GATv2-based Graph Neural Network for edge classification (`gnn_model.py`, `gnn_pipeline.py`, `gnn_trainer.py`)
- Node2Vec embedding pipeline (`node2vec_embedder.py`)
- t-SNE visualization of GNN embeddings (`gnn_visualizer.py`)
- Pipeline orchestrator with configurable model selection (`main.py`)
- Execution reports documenting 9 pipeline runs (`reports/`)
