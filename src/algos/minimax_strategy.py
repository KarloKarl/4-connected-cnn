"""Alpha-beta strategy operating on the shared Connect Four state."""

import math
from typing import Dict, List, Optional, Tuple

from algos.heuristics import HeuristicName, get_heuristic
from connect_four import GameState

SearchNode = Dict[str, object]


class MinimaxStrategy:
    """Choose moves with alpha-beta minimax and a configurable heuristic."""

    def __init__(self, depth: int = 4, heuristic: HeuristicName = "current") -> None:
        """Create a strategy with a positive search depth and heuristic name.

        Args:
            depth: Maximum search depth; must be at least one.
            heuristic: Registered heuristic used at leaf nodes.

        Raises:
            ValueError: If the depth or heuristic is invalid.
        """
        if depth < 1:
            raise ValueError("depth must be at least 1")
        self.depth = depth
        self.heuristic = heuristic
        self._heuristic = get_heuristic(heuristic)

    def choose_move(self, state: GameState) -> int:
        """Return the best legal move for the current player.

        Args:
            state: Position from which to choose.

        Returns:
            A zero-based legal column index.

        Raises:
            ValueError: If the position has no legal moves.
            RuntimeError: If search returns no move for a non-terminal state.
        """
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

    def choose_move_with_trace(self, state: GameState) -> Tuple[int, List[SearchNode]]:
        """Return the best move and the nodes visited during its search.

        Args:
            state: Position from which to choose.

        Returns:
            A legal zero-based column and one trace entry per visited search
            state. Each entry contains a player-relative board, legal moves,
            returned search value, remaining depth and whether the value is
            exact. Values at alpha-beta cutoffs are marked as non-exact
            bounds.

        Raises:
            ValueError: If the position has no legal moves.
            RuntimeError: If search returns no move for a non-terminal state.
        """
        if not state.legal_moves():
            raise ValueError("cannot choose a move on a terminal board")

        trace: List[SearchNode] = []
        move, _ = self._search(
            state,
            self.depth,
            -math.inf,
            math.inf,
            state.current_player,
            trace,
        )
        if move is None:
            raise RuntimeError("minimax returned no move for a non-terminal board")
        return move, trace

    def _search(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: int,
        trace: Optional[List[SearchNode]] = None,
    ) -> Tuple[Optional[int], float]:
        """Search the game tree and return the best move and its score.

        Args:
            state: Position at the current search node.
            depth: Remaining search depth.
            alpha: Best guaranteed maximizing score.
            beta: Best guaranteed minimizing score.
            maximizing_player: Player whose score is optimized.

        Returns:
            The selected column and its score.
        """
        winner = state.winner()
        if winner is not None:
            if winner == maximizing_player:
                value = 100000.0 + depth
            else:
                value = -100000.0 - depth
            self._record_node(trace, state, depth, maximizing_player, value, True)
            return None, value
        if state.is_draw():
            self._record_node(trace, state, depth, maximizing_player, 0.0, True)
            return None, 0.0
        if depth == 0:
            value = self._evaluate(state, maximizing_player)
            self._record_node(trace, state, depth, maximizing_player, value, True)
            return None, value

        maximizing = state.current_player == maximizing_player
        best_move = state.legal_moves()[0]
        exact = True
        if maximizing:
            value = -math.inf
            for move in state.legal_moves():
                child_value = self._search(
                    state.drop_piece(move),
                    depth - 1,
                    alpha,
                    beta,
                    maximizing_player,
                    trace,
                )[1]
                if child_value > value:
                    value, best_move = child_value, move
                alpha = max(alpha, value)
                if alpha >= beta:
                    exact = False
                    break
        else:
            value = math.inf
            for move in state.legal_moves():
                child_value = self._search(
                    state.drop_piece(move),
                    depth - 1,
                    alpha,
                    beta,
                    maximizing_player,
                    trace,
                )[1]
                if child_value < value:
                    value, best_move = child_value, move
                beta = min(beta, value)
                if alpha >= beta:
                    exact = False
                    break
        self._record_node(trace, state, depth, maximizing_player, value, exact)
        return best_move, value

    @staticmethod
    def _record_node(
        trace: Optional[List[SearchNode]],
        state: GameState,
        depth: int,
        player: int,
        value: float,
        exact: bool,
    ) -> None:
        """Append one player-relative search result when tracing is enabled."""
        if trace is None:
            return
        trace.append({
            "board": [
                cell
                for row in state.encode_for_player(player)
                for cell in row
            ],
            "legal_moves": list(state.legal_moves()),
            "player": player,
            "remaining_depth": depth,
            "value": value,
            "exact": exact,
        })

    def _evaluate(self, state: GameState, player: int) -> float:
        """Evaluate a leaf position with the configured heuristic.

        Args:
            state: Leaf position.
            player: Perspective used for the score.

        Returns:
            The configured heuristic score.
        """
        return self._heuristic(state, player)
