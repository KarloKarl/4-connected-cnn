"""Strategy factory used by the interactive demo and API integrations."""

from algos.heuristics import HeuristicName
from algos.minimax_strategy import MinimaxStrategy
from algos.random_strategy import RandomStrategy


def create_strategy(name: str, difficulty: int, heuristic: HeuristicName = "current"):
    """Create a configured random or minimax strategy by public name.

    Args:
        name: ``random`` or ``minimax``.
        difficulty: Minimax search depth.
        heuristic: Heuristic used by Minimax.

    Returns:
        A configured strategy instance.

    Raises:
        ValueError: If the algorithm name, depth or heuristic is invalid.
    """
    factories = {
        "random": RandomStrategy,
        "minimax": lambda: MinimaxStrategy(depth=difficulty, heuristic=heuristic),
    }
    try:
        return factories[name]()
    except KeyError as error:
        available = ", ".join(sorted(factories))
        raise ValueError(f"unknown algorithm '{name}'; choose one of: {available}") from error
