"""Notebook helpers — DuckDB connection factory for sandbox notebooks.

Zero game-domain content. Provides a read-only DuckDB connection
pre-configured for the specified dataset. See ``_current_plan.md`` B.4.1
and A.2 Risk 2 for design rationale.

Risk 2 mitigation: connections are read-only by default to prevent
single-writer lock conflicts between notebook sessions and the CLI.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from types import ModuleType

from rts_predict.common.db import DatasetConfig, DuckDBClient

logger = logging.getLogger(__name__)

# ── Supported game identifiers ─────────────────────────────────────────────────
_SUPPORTED_GAMES: frozenset[str] = frozenset({"sc2", "aoe2"})

# ── Config module path template ────────────────────────────────────────────────
_CONFIG_MODULE_TEMPLATE: str = "rts_predict.{game}.config"


def _load_game_config(game: str) -> ModuleType:
    """Import and return the game config module by game identifier.

    Args:
        game: Game identifier ("sc2" or "aoe2").

    Returns:
        The imported config module.

    Raises:
        ValueError: If game is not in the supported set.
    """
    if game not in _SUPPORTED_GAMES:
        raise ValueError(f"Unknown game {game!r}. Supported games: {sorted(_SUPPORTED_GAMES)}")
    module_path = _CONFIG_MODULE_TEMPLATE.format(game=game)
    logger.debug("Loading config module: %s", module_path)
    return importlib.import_module(module_path)


def _resolve_dataset_config(config_module: ModuleType, game: str, dataset: str) -> DatasetConfig:
    """Resolve a DatasetConfig from the config module's DATASETS registry.

    Args:
        config_module: The imported game config module.
        game: Game identifier (used in error messages).
        dataset: Dataset identifier (e.g. "sc2egset").

    Returns:
        The DatasetConfig for the requested dataset.

    Raises:
        ValueError: If dataset is not found in the module's DATASETS registry.
    """
    datasets: dict[str, DatasetConfig] = getattr(config_module, "DATASETS", {})
    if dataset not in datasets:
        raise ValueError(
            f"Unknown dataset {dataset!r} for game {game!r}. "
            f"Available datasets: {sorted(datasets.keys())}"
        )
    return datasets[dataset]


def get_notebook_db(
    game: str,
    dataset: str,
    *,
    read_only: bool = True,
) -> DuckDBClient:
    """Return a DuckDBClient for use in a Jupyter notebook.

    Resolves the dataset config from the game package's config module
    and returns an open connection. The connection is read-only by default
    to avoid single-writer lock conflicts with the CLI (see _current_plan.md
    A.2 Risk 2).

    WARNING: If read_only=False, the caller must close the connection before
    invoking any CLI commands that write to the same database.

    Args:
        game: Game identifier ("sc2" or "aoe2").
        dataset: Dataset identifier (e.g. "sc2egset", "aoe2companion").
        read_only: Open in read-only mode. Default True.

    Returns:
        An open DuckDBClient. Caller must close it (use as context manager
        or call .close() explicitly).

    Raises:
        ValueError: If game or dataset is not recognized.
    """
    config_module = _load_game_config(game)
    dataset_config = _resolve_dataset_config(config_module, game, dataset)
    logger.debug(
        "Opening notebook DB connection: game=%s dataset=%s read_only=%s",
        game,
        dataset,
        read_only,
    )
    client = DuckDBClient(dataset_config, read_only=read_only)
    client.__enter__()
    return client


def get_reports_dir(game: str, dataset: str) -> Path:
    """Return the absolute path to the dataset's reports directory.

    Resolves the path from the game config module. For SC2, returns
    DATASET_REPORTS_DIR. For AoE2, derives the path from REPORTS_DIR
    and the dataset name (matching the aoe2/config.py naming pattern).

    Args:
        game: Game identifier ("sc2" or "aoe2").
        dataset: Dataset identifier (e.g. "sc2egset").

    Returns:
        Absolute Path to the reports directory.

    Raises:
        ValueError: If game or dataset is not recognized.
    """
    config_module = _load_game_config(game)
    # Validate the dataset exists in the DATASETS registry
    _resolve_dataset_config(config_module, game, dataset)

    reports_dir: Path = getattr(config_module, "REPORTS_DIR")
    resolved: Path = reports_dir / dataset
    logger.debug("Resolved reports dir: %s", resolved)
    return resolved
