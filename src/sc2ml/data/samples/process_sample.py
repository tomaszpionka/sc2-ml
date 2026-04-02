"""Strip heavy event arrays from sample SC2Replay JSON files.

Mirrors the trimming logic in sc2ml.data.ingestion.slim_down_sc2_with_manifest(),
but operates on local sample files without the manifest system.
"""

import json
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent
RAW_DIR = SAMPLES_DIR / "raw"
PROCESSED_DIR = SAMPLES_DIR / "processed"

KEYS_TO_REMOVE = {"messageEvents", "gameEvents", "trackerEvents"}


def main() -> None:
    PROCESSED_DIR.mkdir(exist_ok=True)

    for raw_file in RAW_DIR.glob("*.SC2Replay.json"):
        with open(raw_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for key in KEYS_TO_REMOVE:
            data.pop(key, None)

        out_path = PROCESSED_DIR / raw_file.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))

        raw_kb = raw_file.stat().st_size / 1024
        out_kb = out_path.stat().st_size / 1024
        print(
            f"{raw_file.name}: {raw_kb:.0f} KB -> {out_kb:.0f} KB "
            f"({100 * (1 - out_kb / raw_kb):.1f}% reduction)"
        )


if __name__ == "__main__":
    main()
