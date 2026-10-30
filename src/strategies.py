"""Strategy factory used by the interactive demo and API integrations."""

from algos.minimax_strategy import MinimaxStrategy
from algos.random_strategy import RandomStrategy


def create_strategy(name: str, difficulty: int):
    """Create a configured strategy by its public command-line name."""
    factories = {
        "random": RandomStrategy,
        "minimax": lambda: MinimaxStrategy(depth=difficulty),
    }
    try:
        return factories[name]()
    except KeyError as error:
        available = ", ".join(sorted(factories))
        raise ValueError(f"unknown algorithm '{name}'; choose one of: {available}") from error
