"""Shared Connect Four state and rules."""

from dataclasses import dataclass
from typing import Optional, Tuple

ROWS = 6
COLUMNS = 7
EMPTY = 0
PLAYER_ONE = 1
PLAYER_TWO = -1

Board = Tuple[Tuple[int, ...], ...]


@dataclass(frozen=True)
class GameState:
    """Immutable Connect Four position with rows stored bottom first."""

    board: Board
    current_player: int = PLAYER_ONE

    def __post_init__(self) -> None:
        """Validate board dimensions, values and active player.

        Raises:
            ValueError: If the state is malformed.
        """
        if len(self.board) != ROWS or any(len(row) != COLUMNS for row in self.board):
            raise ValueError("board must have 6 rows and 7 columns")
        if self.current_player not in (PLAYER_ONE, PLAYER_TWO):
            raise ValueError("current_player must be PLAYER_ONE or PLAYER_TWO")
        if any(cell not in (EMPTY, PLAYER_ONE, PLAYER_TWO) for row in self.board for cell in row):
            raise ValueError("board contains an invalid piece")

    @classmethod
    def initial(cls) -> "GameState":
        """Create an empty board with player one to move.

        Returns:
            A new initial game state.
        """
        return cls(tuple(tuple(EMPTY for _ in range(COLUMNS)) for _ in range(ROWS)))

    def legal_moves(self) -> Tuple[int, ...]:
        """Return zero-based columns that still have room for a piece.

        Returns:
            A tuple of legal column indices.
        """
        return tuple(
            column
            for column in range(COLUMNS)
            if self.board[ROWS - 1][column] == EMPTY
        )

    def drop_piece(self, column: int) -> "GameState":
        """Return a new state after dropping the current player's piece.

        Args:
            column: Zero-based target column.

        Returns:
            A new immutable state with the next player active.

        Raises:
            ValueError: If the column is outside the board or full.
        """
        if column not in range(COLUMNS):
            raise ValueError("column must be between 0 and 6")
        if column not in self.legal_moves():
            raise ValueError("column is full")

        rows = [list(row) for row in self.board]
        row = next(row for row in range(ROWS) if rows[row][column] == EMPTY)
        rows[row][column] = self.current_player
        return GameState(
            tuple(tuple(row_values) for row_values in rows),
            -self.current_player,
        )

    def winner(self) -> Optional[int]:
        """Return the winning player, or ``None`` if there is no winner.

        Returns:
            ``1``, ``-1`` or ``None``.
        """
        for row in range(ROWS):
            for column in range(COLUMNS):
                piece = self.board[row][column]
                if piece == EMPTY:
                    continue
                for row_step, column_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    if all(
                        self._piece_at(row + row_step * offset, column + column_step * offset)
                        == piece
                        for offset in range(4)
                    ):
                        return piece
        return None

    def is_draw(self) -> bool:
        """Return whether the board is full without a winner.

        Returns:
            ``True`` only for a full, non-winning board.
        """
        return self.winner() is None and not self.legal_moves()

    def is_terminal(self) -> bool:
        """Return whether the position is a win or a draw.

        Returns:
            ``True`` when no further move should be played.
        """
        return self.winner() is not None or self.is_draw()

    def encode_for_player(self, player: int) -> Board:
        """Return a player-relative encoding suitable for model input.

        Args:
            player: Perspective, either ``1`` or ``-1``.

        Returns:
            Board values with the selected player's stones positive.

        Raises:
            ValueError: If ``player`` is invalid.
        """
        if player not in (PLAYER_ONE, PLAYER_TWO):
            raise ValueError("player must be PLAYER_ONE or PLAYER_TWO")
        return tuple(
            tuple(cell * player for cell in row)
            for row in self.board
        )

    def _piece_at(self, row: int, column: int) -> int:
        if not (0 <= row < ROWS and 0 <= column < COLUMNS):
            return EMPTY
        return self.board[row][column]
