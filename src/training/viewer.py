"""Load and group persisted training runs for the browser viewer."""

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence


def load_json(path: Path):
    """Load and decode one UTF-8 JSON file.

    Args:
        path: JSON file to read.

    Returns:
        The decoded JSON value.
    """
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def group_examples(examples: Sequence[Dict]) -> List[List[Dict]]:
    """Group examples by metadata or infer boundaries for legacy runs.

    Args:
        examples: Dataset examples with optional ``game`` and ``step`` fields.

    Returns:
        A list of games, each containing its ordered examples.
    """
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
    """Convert a player-relative board to absolute piece values.

    Args:
        example: Training example containing ``board`` and optional ``player``.

    Returns:
        A flattened board using the shared player values.
    """
    player = int(example.get("player", 1))
    return [int(cell) * player for cell in example["board"]]


def load_run(run_directory: Path) -> Dict:
    """Load a run and calculate data used by the browser viewer.

    Args:
        run_directory: Directory containing ``config.json`` and ``data.json``.

    Returns:
        Configuration, grouped games and difficulty distributions.
    """
    config = load_json(run_directory / "config.json")
    examples = load_json(run_directory / "data.json")
    games = group_examples(examples)
    difficulty_counts = Counter(
        str(example["depth"]) for example in examples if "depth" in example
    )
    player_difficulty_counts = {
        str(player): dict(
            sorted(
                (
                    (str(depth), count)
                    for depth, count in Counter(
                        example["depth"]
                        for example in examples
                        if "depth" in example and int(example.get("player", 0)) == player
                    ).items()
                ),
                key=lambda item: int(item[0]),
            )
        )
        for player in (-1, 1)
    }
    return {
        "config": config,
        "games": games,
        "difficulty_distribution": dict(
            sorted(difficulty_counts.items(), key=lambda item: int(item[0]))
        ),
        "difficulty_distribution_by_player": player_difficulty_counts,
    }
