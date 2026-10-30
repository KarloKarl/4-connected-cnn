"""Load and group persisted training runs for the browser viewer."""

import json
from pathlib import Path
from typing import Dict, List, Sequence


def load_json(path: Path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def group_examples(examples: Sequence[Dict]) -> List[List[Dict]]:
    """Group examples by explicit metadata or infer boundaries for old runs."""
    if not examples:
        return []

    if all("game" in example and "step" in example for example in examples):
        games: Dict[int, List[Dict]] = {}
        for example in examples:
            games.setdefault(int(example["game"]), []).append(example)
        return [games[index] for index in sorted(games)]

    games: List[List[Dict]] = []
    current: List[Dict] = []
    for example in examples:
        occupied = sum(cell != 0 for cell in example["board"])
        if current and occupied <= 1:
            games.append(current)
            current = []
        current.append(example)
    if current:
        games.append(current)
    return games


def load_run(run_directory: Path) -> Dict:
    config = load_json(run_directory / "config.json")
    examples = load_json(run_directory / "data.json")
    return {"config": config, "games": group_examples(examples)}
