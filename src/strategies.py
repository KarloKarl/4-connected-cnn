"""Strategy factory used by the interactive demo and API integrations."""

from typing import Callable, Dict

from algos.minimax_strategy import MinimaxStrategy
from algos.random_strategy import RandomStrategy

Strategy = Callable


def create_strategy(name: str, difficulty: int) -> Strategy:
    """Create a configured strategy by its public command-line name."""
    factories: Dict[str, Strategy] = {
        "random": RandomStrategy,
        "minimax": lambda: MinimaxStrategy(depth=difficulty),
    }
    try:
        return factories[name]()
    except KeyError as error:
        available = ", ".join(sorted(factories))
        raise ValueError(f"unknown algorithm '{name}'; choose one of: {available}") from error
