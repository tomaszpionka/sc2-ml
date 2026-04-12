"""Tests for SC2 game-level configuration constants."""
from pathlib import Path

import rts_predict.games.sc2.config as cfg


def test_path_constants_are_paths() -> None:
    for attr in ("GAME_DIR", "ROOT_DIR", "DATASETS_DIR", "DATASET_DIR",
                 "DATA_DIR", "REPORTS_DIR", "DB_FILE", "REPLAYS_SOURCE_DIR"):
        if hasattr(cfg, attr):
            assert isinstance(getattr(cfg, attr), Path), f"{attr} must be a Path"


def test_root_dir_is_path() -> None:
    assert isinstance(cfg.ROOT_DIR, Path)


def test_datasets_registry() -> None:
    assert "sc2egset" in cfg.DATASETS
    assert cfg.DEFAULT_DATASET in cfg.DATASETS


def test_random_seed() -> None:
    assert cfg.RANDOM_SEED == 42
