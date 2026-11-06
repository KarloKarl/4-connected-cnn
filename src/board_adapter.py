"""Conversion between the API board format and the shared game state."""

from typing import Sequence, Tuple

from connect_four import COLUMNS, EMPTY, PLAYER_ONE, PLAYER_TWO, ROWS, GameState

API_TO_PIECE = {
    "0": EMPTY,
    "h": PLAYER_TWO,
    "r": PLAYER_ONE,
}


def state_from_api_rows(rows: Sequence[Sequence[str]], current_player: int) -> GameState:
    """Convert the hardware's ``h``/``r``/``0`` board into ``GameState``.

    Args:
        rows: Six rows with seven cells each.
        current_player: Internal player value, ``1`` or ``-1``.

    Returns:
        The equivalent immutable game state.

    Raises:
        ValueError: If dimensions, cell values or the player are invalid.
    """
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
    """Return the zero-based landing row for a legal column.

    Args:
        state: Current game state.
        column: Zero-based target column.

    Returns:
        The first empty row in the selected column.

    Raises:
        ValueError: If the column is full or outside the board.
    """
    if column not in state.legal_moves():
        raise ValueError("column is not available")
    return next(row for row in range(ROWS) if state.board[row][column] == EMPTY)


def api_move(state: GameState, column: int) -> Tuple[int, int]:
    """Return a zero-based ``(column, row)`` pair for the hardware adapter.

    Args:
        state: Current game state.
        column: Zero-based target column.

    Returns:
        The target column and landing row.

    Raises:
        ValueError: If the target column is not legal.
    """
    return column, next_row(state, column)
