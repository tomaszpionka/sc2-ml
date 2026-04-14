"""Notebook helpers — DuckDB connection factory for sandbox notebooks.

Zero game-domain content. Provides a read-only DuckDB connection
pre-configured for the specified dataset. See ``planning/current_plan.md`` B.4.1
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
_CONFIG_MODULE_TEMPLATE: str = "rts_predict.games.{game}.config"


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


def _validate_dataset_known(config_module: ModuleType, game: str, dataset: str) -> None:
    """Raise ValueError if dataset is not in the module's DATASETS registry.

    This is a validation-only wrapper around _resolve_dataset_config for
    callers that need the validation but not the resolved DatasetConfig.
    """
    _resolve_dataset_config(config_module, game, dataset)


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


def setup_notebook_logging(name: str = "notebook") -> logging.Logger:
    """Configure the root logger and return a named logger for notebook use.

    Sets level=INFO and formats lines as ``HH:MM:SS LEVEL name: message``.
    Safe to call multiple times — ``logging.basicConfig`` is a no-op when
    handlers are already configured, so re-running a cell is harmless.

    Call once in the imports cell of every notebook::

        from rts_predict.common.notebook_utils import setup_notebook_logging
        logger = setup_notebook_logging()

    Args:
        name: Logger name. Defaults to ``"notebook"`` which is sufficient
            for all sandbox notebooks. Pass a custom name only if log output
            needs to be filtered by notebook identity.

    Returns:
        A configured :class:`logging.Logger` instance ready to use.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger(name)


def get_notebook_db(
    game: str,
    dataset: str,
    *,
    read_only: bool = True,
) -> DuckDBClient:
    """Return a DuckDBClient for use in a Jupyter notebook.

    Resolves the dataset config from the game package's config module
    and returns an open connection. The connection is read-only by default
    to avoid single-writer lock conflicts with the CLI (see planning/current_plan.md
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
    client.open()
    return client


def get_reports_dir(game: str, dataset: str) -> Path:
    """Return the absolute path to the dataset's ``reports/`` directory.

    Each game config module exports a ``DATASETS_REPORTS`` dict that maps
    dataset name to its canonical ``reports/`` path. The returned path always
    ends in ``…/<dataset>/reports`` regardless of game.

    Args:
        game: Game identifier ("sc2" or "aoe2").
        dataset: Dataset identifier (e.g. "sc2egset", "aoe2companion").

    Returns:
        Absolute Path to the dataset's ``reports/`` directory.

    Raises:
        ValueError: If game or dataset is not recognized, or if the
            game's config module does not export DATASETS_REPORTS.
    """
    config_module = _load_game_config(game)
    _validate_dataset_known(config_module, game, dataset)
    datasets_reports = getattr(config_module, "DATASETS_REPORTS", None)
    if datasets_reports is None:
        raise ValueError(
            f"Config module for game {game!r} does not export DATASETS_REPORTS"
        )
    resolved: Path = datasets_reports[dataset]
    logger.debug("Resolved reports dir: %s", resolved)
    return resolved
