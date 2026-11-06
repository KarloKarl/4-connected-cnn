"""Heuristic evaluations used by the minimax strategy."""

from typing import Callable, Dict, Literal

from connect_four import COLUMNS, EMPTY, ROWS, GameState

HeuristicName = Literal["current", "ws22_minimax", "ws22_window"]
Heuristic = Callable[[GameState, int], float]


def _windows(state: GameState):
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
    """Evaluate the current symmetric heuristic."""
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
    """Reproduce the heuristic from WS22/Spielalgorithmus/Minimax.py."""
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
    """Reproduce the heuristic from WS22/Spielalgorithmus/4GewinntSpielBrett.py."""
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
    try:
        return HEURISTICS[name]  # type: ignore[index]
    except KeyError as error:
        available = ", ".join(HEURISTICS)
        raise ValueError(f"unknown heuristic '{name}'; choose one of: {available}") from error
