"""Load and group persisted training runs for the browser viewer."""

import json
from collections import Counter
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


def decode_board_for_view(example: Dict) -> List[int]:
    """Convert the player-relative training board to absolute piece values."""
    player = int(example.get("player", 1))
    return [int(cell) * player for cell in example["board"]]


def load_run(run_directory: Path) -> Dict:
    config = load_json(run_directory / "config.json")
    examples = load_json(run_directory / "data.json")
    games = group_examples(examples)
    difficulty_counts = Counter(
        str(example["depth"]) for example in examples if "depth" in example
    )
    game_difficulty_counts = Counter(
        str(game[0]["depth"]) for game in games if game and "depth" in game[0]
    )
    return {
        "config": config,
        "games": games,
        "difficulty_distribution": dict(
            sorted(difficulty_counts.items(), key=lambda item: int(item[0]))
        ),
        "game_difficulty_distribution": dict(
            sorted(game_difficulty_counts.items(), key=lambda item: int(item[0]))
        ),
    }
