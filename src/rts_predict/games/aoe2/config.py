"""AoE2 game package configuration — paths and constants."""
from pathlib import Path

from rts_predict.common.db import DatasetConfig

# ── Project paths ──────────────────────────────────────────────────────────────
GAME_DIR: Path = Path(__file__).resolve().parent                # games/aoe2/
ROOT_DIR: Path = GAME_DIR.parent.parent.parent.parent           # 4 levels to repo root
DATASETS_DIR: Path = GAME_DIR / "datasets"

# ── aoe2companion dataset ──────────────────────────────────────────────────────
AOE2COMPANION_DIR: Path = DATASETS_DIR / "aoe2companion"
AOE2COMPANION_DATA_DIR: Path = AOE2COMPANION_DIR / "data"
AOE2COMPANION_RAW_DIR: Path = AOE2COMPANION_DATA_DIR / "raw"
AOE2COMPANION_RAW_MATCHES_DIR: Path = AOE2COMPANION_RAW_DIR / "matches"
AOE2COMPANION_RAW_LEADERBOARDS_DIR: Path = AOE2COMPANION_RAW_DIR / "leaderboards"
AOE2COMPANION_RAW_PROFILES_DIR: Path = AOE2COMPANION_RAW_DIR / "profiles"
AOE2COMPANION_RAW_RATINGS_DIR: Path = AOE2COMPANION_RAW_DIR / "ratings"
AOE2COMPANION_DB_FILE: Path = AOE2COMPANION_DATA_DIR / "db" / "db.duckdb"
AOE2COMPANION_TMP_DIR: Path = AOE2COMPANION_DATA_DIR / "tmp"
AOE2COMPANION_TEMP_DIR: Path = AOE2COMPANION_TMP_DIR  # backward-compat alias
AOE2COMPANION_API_DIR: Path = AOE2COMPANION_DIR / "api"
AOE2COMPANION_MANIFEST: Path = AOE2COMPANION_API_DIR / "api_dump_list.json"
AOE2COMPANION_REPORTS_DIR: Path = AOE2COMPANION_DIR / "reports"
AOE2COMPANION_ARTIFACTS_DIR: Path = AOE2COMPANION_REPORTS_DIR / "artifacts"

# ── aoestats dataset ───────────────────────────────────────────────────────────
AOESTATS_DIR: Path = DATASETS_DIR / "aoestats"
AOESTATS_DATA_DIR: Path = AOESTATS_DIR / "data"
AOESTATS_RAW_DIR: Path = AOESTATS_DATA_DIR / "raw"
AOESTATS_RAW_MATCHES_DIR: Path = AOESTATS_RAW_DIR / "matches"
AOESTATS_RAW_PLAYERS_DIR: Path = AOESTATS_RAW_DIR / "players"
AOESTATS_RAW_OVERVIEW_DIR: Path = AOESTATS_RAW_DIR / "overview"
AOESTATS_DB_FILE: Path = AOESTATS_DATA_DIR / "db" / "db.duckdb"
AOESTATS_TMP_DIR: Path = AOESTATS_DATA_DIR / "tmp"
AOESTATS_TEMP_DIR: Path = AOESTATS_TMP_DIR  # backward-compat alias
AOESTATS_API_DIR: Path = AOESTATS_DIR / "api"
AOESTATS_MANIFEST: Path = AOESTATS_API_DIR / "db_dump_list.json"
AOESTATS_REPORTS_DIR: Path = AOESTATS_DIR / "reports"
AOESTATS_ARTIFACTS_DIR: Path = AOESTATS_REPORTS_DIR / "artifacts"

# -- Reproducibility --
RANDOM_SEED: int = 42

# -- Dataset registry --
DATASETS: dict[str, DatasetConfig] = {
    "aoe2companion": DatasetConfig(
        name="aoe2companion",
        db_file=AOE2COMPANION_DB_FILE,
        temp_dir=AOE2COMPANION_TMP_DIR,
        description="aoe2companion.com daily API dumps",
    ),
    "aoestats": DatasetConfig(
        name="aoestats",
        db_file=AOESTATS_DB_FILE,
        temp_dir=AOESTATS_TMP_DIR,
        description="aoestats.io weekly DB dumps",
    ),
}
DEFAULT_DATASET: str = "aoe2companion"

# ── Reports registry (used by notebook_utils.get_reports_dir) ─────────────────
DATASETS_REPORTS: dict[str, Path] = {
    "aoe2companion": AOE2COMPANION_REPORTS_DIR,
    "aoestats": AOESTATS_REPORTS_DIR,
}
