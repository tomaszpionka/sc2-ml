"""Tests for DtypeDecision dataclass (aoe2companion rating CSV ingestion)."""
import json
from pathlib import Path

import pytest

from rts_predict.games.aoe2.datasets.aoe2companion.types import DtypeDecision


def test_auto_detect_round_trip(tmp_path: Path) -> None:
    decision = DtypeDecision(strategy="auto_detect", rationale="schema is clean")
    out = tmp_path / "decision.json"
    decision.to_json(out)
    loaded = DtypeDecision.from_json(out)
    assert loaded.strategy == "auto_detect"
    assert loaded.rationale == "schema is clean"
    assert loaded.dtype_map == {}


def test_explicit_round_trip(tmp_path: Path) -> None:
    decision = DtypeDecision(
        strategy="explicit",
        rationale="nullable ints",
        dtype_map={"rating": "INTEGER", "num_games": "INTEGER"},
    )
    out = tmp_path / "decision.json"
    decision.to_json(out)
    loaded = DtypeDecision.from_json(out)
    assert loaded.strategy == "explicit"
    assert loaded.dtype_map == {"rating": "INTEGER", "num_games": "INTEGER"}


def test_auto_detect_json_excludes_dtype_map(tmp_path: Path) -> None:
    decision = DtypeDecision(strategy="auto_detect", rationale="clean")
    out = tmp_path / "decision.json"
    decision.to_json(out)
    payload = json.loads(out.read_text())
    assert "dtype_map" not in payload


def test_explicit_json_includes_dtype_map(tmp_path: Path) -> None:
    decision = DtypeDecision(
        strategy="explicit", rationale="mixed nulls", dtype_map={"col": "VARCHAR"}
    )
    out = tmp_path / "decision.json"
    decision.to_json(out)
    payload = json.loads(out.read_text())
    assert "dtype_map" in payload


def test_from_json_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        DtypeDecision.from_json(tmp_path / "nonexistent.json")
