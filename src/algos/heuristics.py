"""Heuristic evaluations used by the minimax strategy.

The current heuristic evaluates a position from one player's perspective. It
adds a small center-column bonus and scores every horizontal, vertical, and
diagonal four-cell window. Terminal wins and losses are handled separately by
``MinimaxStrategy`` with much larger values.

The two ``ws22_*`` functions preserve the historical scoring profiles from
``WS22/Spielalgorithmus`` for reproducible dataset generation and comparison.
"""

from typing import Callable, Dict, Iterator, List, Literal

from connect_four import COLUMNS, EMPTY, ROWS, GameState

HeuristicName = Literal["current", "ws22_minimax", "ws22_window"]
Heuristic = Callable[[GameState, int], float]


def _windows(state: GameState) -> Iterator[List[int]]:
    """Yield every horizontal, vertical, and diagonal four-cell window.

    Args:
        state: Position whose board is scanned.

    Yields:
        Lists containing four consecutive cell values.
    """
    board = state.board
    for row in range(ROWS):
        for column in range(COLUMNS - 3):
            yield [board[row][column + offset] for offset in range(4)]
    for row in range(ROWS - 3):
        for column in range(COLUMNS):
            yield [board[row + offset][column] for offset in range(4)]
    for row in range(ROWS - 3):
        for column in range(COLUMNS - 3):
            yield [board[row + offset][column + offset] for offset in range(4)]
    for row in range(ROWS - 3):
        for column in range(COLUMNS - 3):
            yield [board[row + 3 - offset][column + offset] for offset in range(4)]


def current_heuristic(state: GameState, player: int) -> float:
    """Return the current symmetric score for ``player``.

    The score is positive when the position favors ``player`` and negative
    when it favors the opponent. A center stone contributes ``+3`` and an
    opponent center stone ``-3``. Window scores are ``+100/-100`` for a
    completed four, ``+5/-6`` for an open three, and ``+2/-2`` for an open
    two. This function evaluates patterns only; it does not test whether an
    empty cell is immediately playable.
    Args:
        state: Position to evaluate.
        player: Player whose perspective defines positive scores.

    Returns:
        A positive or negative heuristic score.

    Raises:
        ValueError: If ``player`` is not ``1`` or ``-1``.
    """
    opponent = -player
    score = 0.0
    center = [state.board[row][COLUMNS // 2] for row in range(ROWS)]
    score += center.count(player) * 3
    score -= center.count(opponent) * 3

    for window in _windows(state):
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(EMPTY)
        if player_count == 4:
            score += 100
        elif opponent_count == 4:
            score -= 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif opponent_count == 3 and empty_count == 1:
            score -= 6
        elif player_count == 2 and empty_count == 2:
            score += 2
        elif opponent_count == 2 and empty_count == 2:
            score -= 2
    return score


def ws22_minimax_heuristic(state: GameState, player: int) -> float:
    """Return the historical ``Minimax.py`` scoring profile from WS22.

    Args:
        state: Position to evaluate.
        player: Player whose perspective defines positive scores.

    Returns:
        The historical WS22 heuristic score.
    """
    opponent = -player
    center = [state.board[row][COLUMNS // 2] for row in range(ROWS)]
    score = center.count(player) * 2.5
    for window in _windows(state):
        if window.count(player) == 4:
            score += 15
        elif window.count(player) == 3 and window.count(EMPTY) == 1:
            score += 3
        elif window.count(player) == 2 and window.count(EMPTY) == 2:
            score += 1
        elif window.count(opponent) == 3 and window.count(EMPTY) == 1:
            score -= 2
    return score


def ws22_window_heuristic(state: GameState, player: int) -> float:
    """Return the historical ``4GewinntSpielBrett.py`` scoring profile.

    Args:
        state: Position to evaluate.
        player: Player whose perspective defines positive scores.

    Returns:
        The historical window-based heuristic score.
    """
    opponent = -player
    center = [state.board[row][COLUMNS // 2] for row in range(ROWS)]
    score = center.count(player) * 3
    for window in _windows(state):
        if window.count(player) == 4:
            score += 100
        elif window.count(player) == 3 and window.count(EMPTY) == 1:
            score += 5
        elif window.count(player) == 2 and window.count(EMPTY) == 2:
            score += 2
        elif window.count(opponent) == 3 and window.count(EMPTY) == 1:
            score -= 4
    return score


HEURISTICS: Dict[HeuristicName, Heuristic] = {
    "current": current_heuristic,
    "ws22_minimax": ws22_minimax_heuristic,
    "ws22_window": ws22_window_heuristic,
}


def get_heuristic(name: str) -> Heuristic:
    """Return a registered heuristic by name.

    Args:
        name: One of ``current``, ``ws22_minimax`` or ``ws22_window``.

    Returns:
        The selected heuristic callable.

    Raises:
        ValueError: If ``name`` is not registered.
    """
    try:
        return HEURISTICS[name]  # type: ignore[index]
    except KeyError as error:
        available = ", ".join(HEURISTICS)
        raise ValueError(f"unknown heuristic '{name}'; choose one of: {available}") from error
