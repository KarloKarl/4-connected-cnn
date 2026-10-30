"""Generate supervised Connect Four examples from a reference strategy."""

import json
from pathlib import Path
from typing import Dict, List

from algos.minimax_strategy import MinimaxStrategy
from connect_four import GameState


def encode_state(state: GameState) -> List[int]:
    """Encode the board from the current player's perspective."""
    return [
        cell
        for row in state.encode_for_player(state.current_player)
        for cell in row
    ]


def generate_games(game_count: int, depth: int = 3) -> List[Dict]:
    if game_count < 1:
        raise ValueError("game_count must be at least 1")

    strategy = MinimaxStrategy(depth=depth)
    examples: List[Dict] = []
    for _ in range(game_count):
        state = GameState.initial()
        game_examples = []

        while not state.is_terminal():
            move = strategy.choose_move(state)
            game_examples.append(
                {
                    "board": encode_state(state),
                    "legal_moves": list(state.legal_moves()),
                    "move": move,
                    "player": state.current_player,
                }
            )
            state = state.drop_piece(move)

        result = state.winner() or 0
        for example in game_examples:
            example["result"] = result
            examples.append(example)
    return examples


def write_jsonl(examples: List[Dict], output: Path) -> None:
    with output.open("w", encoding="utf-8") as file:
        for example in examples:
            file.write(json.dumps(example) + "\n")
