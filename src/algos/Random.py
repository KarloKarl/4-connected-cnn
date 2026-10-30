from random import choice

from connect_four import GameState


class RandomStrategy:
    """Choose uniformly from the legal columns of a game state."""

    def choose_move(self, state: GameState) -> int:
        legal_moves = state.legal_moves()
        if not legal_moves:
            raise ValueError("cannot choose a move on a terminal board")
        return choice(legal_moves)


class Random(RandomStrategy):
    """Compatibility wrapper for the former constructor-based API."""

    def __init__(self, curr_board, row_count, column_count, ai_piece, human_piece):
        self.board = curr_board
        self.rows = row_count
        self.columns = column_count
        self.ai_piece = ai_piece
        self.human_piece = human_piece

    def choose_column(self):
        if not isinstance(self.board, GameState):
            raise TypeError("Random.choose_column requires a GameState board")
        return self.choose_move(self.board)
