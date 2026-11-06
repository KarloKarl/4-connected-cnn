"""Alpha-beta strategy operating on the shared Connect Four state."""

import math
from typing import Optional, Tuple

from algos.heuristics import HeuristicName, get_heuristic
from connect_four import GameState


class MinimaxStrategy:
    def __init__(self, depth: int = 4, heuristic: HeuristicName = "current") -> None:
        if depth < 1:
            raise ValueError("depth must be at least 1")
        self.depth = depth
        self.heuristic = heuristic
        self._heuristic = get_heuristic(heuristic)

    def choose_move(self, state: GameState) -> int:
        legal_moves = state.legal_moves()
        if not legal_moves:
            raise ValueError("cannot choose a move on a terminal board")

        move, _ = self._search(
            state,
            self.depth,
            -math.inf,
            math.inf,
            state.current_player,
        )
        if move is None:
            raise RuntimeError("minimax returned no move for a non-terminal board")
        return move

    def _search(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: int,
    ) -> Tuple[Optional[int], float]:
        winner = state.winner()
        if winner is not None:
            if winner == maximizing_player:
                return None, 100000.0 + depth
            return None, -100000.0 - depth
        if state.is_draw():
            return None, 0.0
        if depth == 0:
            return None, self._evaluate(state, maximizing_player)

        maximizing = state.current_player == maximizing_player
        best_move = state.legal_moves()[0]
        if maximizing:
            value = -math.inf
            for move in state.legal_moves():
                child_value = self._search(
                    state.drop_piece(move), depth - 1, alpha, beta, maximizing_player
                )[1]
                if child_value > value:
                    value, best_move = child_value, move
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = math.inf
            for move in state.legal_moves():
                child_value = self._search(
                    state.drop_piece(move), depth - 1, alpha, beta, maximizing_player
                )[1]
                if child_value < value:
                    value, best_move = child_value, move
                beta = min(beta, value)
                if alpha >= beta:
                    break
        return best_move, value

    def _evaluate(self, state: GameState, player: int) -> float:
        return self._heuristic(state, player)
