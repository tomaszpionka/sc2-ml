"""Dtype decision dataclass for aoe2companion rating CSV ingestion.

The DtypeDecision is the formal handoff from Step 0.3 (schema profiling) to
Steps 0.5 and 0.6 (smoke test and full ingestion). Serialising it to JSON
makes the dtype choice auditable and prevents executor improvisation.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DtypeDecision:
    """Records the dtype strategy for reading rating CSVs.

    Attributes:
        strategy: Either "auto_detect" or "explicit".
        rationale: One-sentence justification for the chosen strategy.
        dtype_map: Mapping of column name to DuckDB type string. Only
            populated when strategy is "explicit".
    """

    strategy: str
    rationale: str
    dtype_map: dict[str, str] = field(default_factory=dict)

    def to_json(self, path: Path) -> None:
        """Serialise the decision to a JSON file.

        Args:
            path: Target path for the JSON artifact.
        """
        payload: dict = {
            "strategy": self.strategy,
            "rationale": self.rationale,
        }
        if self.strategy == "explicit":
            payload["dtype_map"] = self.dtype_map
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2))

    @classmethod
    def from_json(cls, path: Path) -> "DtypeDecision":
        """Deserialise a DtypeDecision from a JSON file.

        Args:
            path: Path to the JSON artifact produced by to_json().

        Returns:
            A DtypeDecision instance with all fields populated.

        Raises:
            FileNotFoundError: If path does not exist.
            KeyError: If required keys are missing from the JSON.
        """
        payload = json.loads(path.read_text())
        return cls(
            strategy=payload["strategy"],
            rationale=payload["rationale"],
            dtype_map=payload.get("dtype_map", {}),
        )
