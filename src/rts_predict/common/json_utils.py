import json
from pathlib import Path


def get_json_keypaths(path: str | Path) -> list[str]:
    with open(path) as f:
        data = json.load(f)

    paths: set[str] = set()

    def traverse(node, prefix: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                full = f"{prefix}.{key}" if prefix else key
                traverse(value, full)
        elif isinstance(node, list):
            paths.add(f"{prefix}[]")
            for item in node:
                traverse(item, f"{prefix}[]")
        else:
            paths.add(prefix)

    traverse(data, "")
    return sorted(paths)


if __name__ == "__main__":
    _sample = (
        "/Users/tomaszpionka/Projects/rts-outcome-prediction"
        "/src/rts_predict/sc2/data/samples/raw"
        "/0e0b1a550447f0b0a616e48224b31bd9.SC2Replay.json"
    )
    keypaths = get_json_keypaths(_sample)
    for path in keypaths:
        print(path)
