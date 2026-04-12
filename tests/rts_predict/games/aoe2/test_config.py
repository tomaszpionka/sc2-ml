"""Tests for AoE2 game-level configuration constants."""
from pathlib import Path

import rts_predict.games.aoe2.config as cfg


def test_path_constants_are_paths() -> None:
    for attr in ("GAME_DIR", "ROOT_DIR", "DATA_DIR", "REPORTS_DIR",
                 "AOE2COMPANION_DIR", "AOE2COMPANION_RAW_DIR",
                 "AOESTATS_DIR", "AOESTATS_RAW_DIR"):
        if hasattr(cfg, attr):
            assert isinstance(getattr(cfg, attr), Path), f"{attr} must be a Path"


def test_root_dir_is_path() -> None:
    assert isinstance(cfg.ROOT_DIR, Path)


def test_datasets_registry() -> None:
    assert "aoe2companion" in cfg.DATASETS
    assert "aoestats" in cfg.DATASETS
    assert cfg.DEFAULT_DATASET in cfg.DATASETS


def test_random_seed() -> None:
    assert cfg.RANDOM_SEED == 42
