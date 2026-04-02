from pathlib import Path

# ── Project paths ──────────────────────────────────────────────────────────────
# Derived from file location: src/sc2ml/config.py → repo root
ROOT_PROJECTS_DIR: Path = Path(__file__).resolve().parent.parent.parent
DB_FILE: Path = Path("~/duckdb_work/test_sc2.duckdb").expanduser().resolve()
MANIFEST_PATH: Path = ROOT_PROJECTS_DIR / "processing_manifest.json"

# DuckDB configuration
DUCKDB_TEMP_DIR: Path = Path("~/duckdb_work/tmp").expanduser().resolve()

# Raw replay files location
REPLAYS_SOURCE_DIR: Path = Path("~/Downloads/SC2_Replays").expanduser().resolve()

# ── Model artifact paths ───────────────────────────────────────────────────────
MODELS_DIR: Path = ROOT_PROJECTS_DIR / "models"
GNN_CHECKPOINT_PATH: Path = MODELS_DIR / "best_gnn_checkpoint.pt"
GNN_VIZ_OUTPUT_PATH: Path = ROOT_PROJECTS_DIR / "reports" / "gnn_space_map.png"

# ── Reproducibility ────────────────────────────────────────────────────────────
RANDOM_SEED: int = 42

# ── ELO system ─────────────────────────────────────────────────────────────────
ELO_K_NEW: int = 64       # K-factor for players with fewer than ELO_K_THRESHOLD games
ELO_K_VETERAN: int = 32   # K-factor for veteran players
ELO_K_THRESHOLD: int = 10  # Games played threshold separating new vs. veteran players

# ── Feature engineering ────────────────────────────────────────────────────────
VETERAN_MIN_GAMES: int = 3   # Minimum historical games for the "veterans only" evaluation set
BAYESIAN_C: float = 5.0      # Bayesian smoothing confidence weight
BAYESIAN_PRIOR_WR: float = 0.5  # Prior win rate for Bayesian smoothing

# ── GNN architecture ───────────────────────────────────────────────────────────
GNN_HIDDEN_DIM: int = 64
GNN_HEADS_CONV1: int = 4
GNN_HEADS_CONV2: int = 1
GNN_DROPOUT: float = 0.4

# ── GNN training ───────────────────────────────────────────────────────────────
GNN_LEARNING_RATE: float = 0.001
GNN_WEIGHT_DECAY: float = 1e-3
GNN_PATIENCE: int = 30
GNN_LOG_EVERY: int = 10  # Log training progress every N epochs

# ── Node2Vec ───────────────────────────────────────────────────────────────────
NODE2VEC_EMBEDDING_DIM: int = 64
NODE2VEC_WALK_LENGTH: int = 20
NODE2VEC_NUM_WALKS: int = 10
NODE2VEC_WORKERS: int = 4
NODE2VEC_WINDOW: int = 10

# ── GNN node feature fallbacks (for players with no training history) ──────────
NODE_FALLBACK_APM: float = 150.0
NODE_FALLBACK_SQ: float = 50.0
NODE_FALLBACK_WINRATE: float = 0.5
NODE_FALLBACK_GAMES: float = 0.0

# ── t-SNE visualization ────────────────────────────────────────────────────────
TSNE_N_COMPONENTS: int = 2
TSNE_PERPLEXITY: int = 30
TSNE_N_ITER: int = 1000
VIZ_DPI: int = 300

# ── Classical models ───────────────────────────────────────────────────────────
RF_N_ESTIMATORS: int = 200
RF_MAX_DEPTH: int = 8
RF_MIN_SAMPLES_SPLIT: int = 5
HGB_MAX_ITER: int = 200
HGB_LEARNING_RATE: float = 0.05
LR_MAX_ITER: int = 1000

# ── Hyperparameter tuning ──────────────────────────────────────────────────────
TUNING_N_ITER: int = 50
TUNING_CV_FOLDS: int = 5

# ── Patch analysis ─────────────────────────────────────────────────────────────
PATCH_MIN_MATCHES: int = 100  # Minimum matches for a patch to be included in per-patch analysis
