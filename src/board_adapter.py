"""Conversion between the API board format and the shared game state."""

from typing import Sequence, Tuple

from connect_four import COLUMNS, EMPTY, PLAYER_ONE, PLAYER_TWO, ROWS, GameState

API_TO_PIECE = {
    "0": EMPTY,
    "h": PLAYER_TWO,
    "r": PLAYER_ONE,
}


def state_from_api_rows(rows: Sequence[Sequence[str]], current_player: int) -> GameState:
    if len(rows) != ROWS or any(len(row) != COLUMNS for row in rows):
        raise ValueError("API board must have 6 rows and 7 columns")
    try:
        board = tuple(
            tuple(API_TO_PIECE[cell] for cell in row)
            for row in rows
        )
    except KeyError as error:
        raise ValueError(f"unknown API board value: {error.args[0]}") from error
    return GameState(board, current_player)


def next_row(state: GameState, column: int) -> int:
    if column not in state.legal_moves():
        raise ValueError("column is not available")
    return next(row for row in range(ROWS) if state.board[row][column] == EMPTY)


def api_move(state: GameState, column: int) -> Tuple[int, int]:
    """Return a zero-based (column, row) pair for the hardware adapter."""
    return column, next_row(state, column)
