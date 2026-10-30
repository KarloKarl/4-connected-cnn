from random import choice

from connect_four import GameState


class RandomStrategy:
    """Choose uniformly from the legal columns of a game state."""

    def choose_move(self, state: GameState) -> int:
        legal_moves = state.legal_moves()
        if not legal_moves:
            raise ValueError("cannot choose a move on a terminal board")
        return choice(legal_moves)
