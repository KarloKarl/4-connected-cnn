"""Interactive terminal demonstrator for Connect Four strategies."""

import argparse
from typing import Callable, Optional

from connect_four import COLUMNS, PLAYER_ONE, PLAYER_TWO, GameState
from strategies import create_strategy


def render(state: GameState) -> str:
    symbols = {0: ".", PLAYER_ONE: "A", PLAYER_TWO: "H"}
    lines = ["  " + " ".join(str(column + 1) for column in range(COLUMNS))]
    for row in range(5, -1, -1):
        lines.append("| " + " ".join(symbols[state.board[row][column]] for column in range(COLUMNS)))
    return "\n".join(lines)


def play(
    algorithm: str,
    difficulty: int,
    human_first: bool = True,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> Optional[int]:
    """Run one human-vs-AI game and return the winner."""
    strategy = create_strategy(algorithm, difficulty)
    state = GameState.initial()
    if not human_first:
        state = GameState(state.board, PLAYER_ONE)

    output_fn(f"Algorithmus: {algorithm} | Schwierigkeit: {difficulty}")
    output_fn(render(state))

    while not state.is_terminal():
        if state.current_player == PLAYER_TWO:
            while True:
                try:
                    column = int(input_fn("Dein Zug (Spalte 1-7): ")) - 1
                except ValueError:
                    output_fn("Bitte eine Zahl von 1 bis 7 eingeben.")
                    continue
                if column in state.legal_moves():
                    break
                output_fn("Diese Spalte ist nicht verfügbar.")
        else:
            column = strategy.choose_move(state)
            output_fn(f"KI spielt Spalte {column + 1}.")

        state = state.drop_piece(column)
        output_fn(render(state))

    winner = state.winner()
    output_fn({PLAYER_ONE: "Die KI gewinnt.", PLAYER_TWO: "Du gewinnst.", None: "Unentschieden."}[winner])
    return winner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--algorithm",
        choices=("random", "minimax"),
        default="minimax",
        help="Gegneralgorithmus (Standard: minimax)",
    )
    parser.add_argument(
        "--difficulty",
        type=int,
        choices=range(1, 9),
        default=4,
        metavar="1-8",
        help="Minimax-Suchtiefe; bei random ohne Einfluss (Standard: 4)",
    )
    parser.add_argument(
        "--ai-first",
        action="store_true",
        help="Die KI beginnt statt des Menschen.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    play(args.algorithm, args.difficulty, human_first=not args.ai_first)


if __name__ == "__main__":
    main()
