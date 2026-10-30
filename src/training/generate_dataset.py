"""Generate supervised Connect Four examples from Minimax games."""

import json
import random
from pathlib import Path
from typing import Dict, List, Literal, Optional

from algos.minimax_strategy import MinimaxStrategy
from connect_four import GameState

Distribution = Literal["uniform", "bell"]


def encode_state(state: GameState) -> List[int]:
    """Encode the board from the current player's perspective."""
    return [
        cell
        for row in state.encode_for_player(state.current_player)
        for cell in row
    ]


def choose_depth(
    minimum: int,
    maximum: int,
    distribution: Distribution,
    rng: random.Random,
) -> int:
    if minimum < 1 or maximum < minimum:
        raise ValueError("depth range must satisfy 1 <= minimum <= maximum")
    if distribution not in ("uniform", "bell"):
        raise ValueError("distribution must be 'uniform' or 'bell'")
    if distribution == "uniform":
        return rng.randint(minimum, maximum)

    mean = (minimum + maximum) / 2
    standard_deviation = max((maximum - minimum) / 6, 0.1)
    return max(minimum, min(maximum, round(rng.gauss(mean, standard_deviation))))


def generate_games(
    game_count: int,
    min_depth: int = 3,
    max_depth: Optional[int] = None,
    distribution: Distribution = "uniform",
    random_first_move: bool = True,
    seed: Optional[int] = None,
) -> List[Dict]:
    if game_count < 1:
        raise ValueError("game_count must be at least 1")
    if max_depth is None:
        max_depth = min_depth

    rng = random.Random(seed)
    examples: List[Dict] = []
    for _ in range(game_count):
        state = GameState.initial()
        depth = choose_depth(min_depth, max_depth, distribution, rng)
        if random_first_move:
            state = state.drop_piece(rng.choice(state.legal_moves()))
        strategy = MinimaxStrategy(depth=depth)
        game_examples = []

        while not state.is_terminal():
            move = strategy.choose_move(state)
            game_examples.append(
                {
                    "board": encode_state(state),
                    "legal_moves": list(state.legal_moves()),
                    "move": move,
                    "player": state.current_player,
                    "depth": depth,
                }
            )
            state = state.drop_piece(move)

        result = state.winner() or 0
        for example in game_examples:
            example["result"] = result
            examples.append(example)
    return examples


def write_jsonl(examples: List[Dict], output: Path) -> None:
    """Write legacy JSONL output; new runs should use ``write_dataset``."""
    with output.open("w", encoding="utf-8") as file:
        for example in examples:
            file.write(json.dumps(example) + "\n")


def write_dataset(examples: List[Dict], output: Path) -> None:
    """Write the complete dataset as a JSON array."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(examples, indent=2) + "\n", encoding="utf-8")
