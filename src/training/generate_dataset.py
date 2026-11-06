"""Generate supervised Connect Four examples from Minimax games."""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Literal, Optional, Sequence, Union

from algos.minimax_strategy import MinimaxStrategy
from algos.heuristics import HeuristicName
from connect_four import GameState

Distribution = Literal["uniform", "bell"]
PlayerConfig = Dict[str, Union[str, int]]


def encode_state(state: GameState) -> List[int]:
    """Encode the board from the current player's perspective.

    Args:
        state: Position to encode.

    Returns:
        A flattened list of 42 player-relative cell values.
    """
    return [
        cell
        for row in state.encode_for_player(state.current_player)
        for cell in row
    ]


def choose_depth(
    minimum: int,
    maximum: int,
    distribution: Distribution,
    rng: random.Random,
) -> int:
    """Sample a Minimax depth from a uniform or bell-shaped distribution.

    Args:
        minimum: Inclusive lower depth bound.
        maximum: Inclusive upper depth bound.
        distribution: ``uniform`` or truncated Gaussian-like ``bell``.
        rng: Random generator used for reproducible sampling.

    Returns:
        A depth within the requested bounds.

    Raises:
        ValueError: If bounds or distribution are invalid.
    """
    if minimum < 1 or maximum < minimum:
        raise ValueError("depth range must satisfy 1 <= minimum <= maximum")
    if distribution not in ("uniform", "bell"):
        raise ValueError("distribution must be 'uniform' or 'bell'")
    if distribution == "uniform":
        return rng.randint(minimum, maximum)

    mean = (minimum + maximum) / 2
    standard_deviation = max((maximum - minimum) / 6, 0.1)
    return max(minimum, min(maximum, round(rng.gauss(mean, standard_deviation))))


def iter_game_examples(
    game_count: int,
    min_depth: int = 3,
    max_depth: Optional[int] = None,
    distribution: Distribution = "uniform",
    random_first_move: bool = True,
    seed: Optional[int] = None,
    player_configs: Optional[Dict[int, PlayerConfig]] = None,
    heuristic: HeuristicName = "current",
) -> Iterator[Dict]:
    """Yield one supervised example for every move in generated games.

    Args:
        game_count: Number of games to simulate.
        min_depth: Default minimum Minimax depth.
        max_depth: Default maximum Minimax depth.
        distribution: Default depth distribution.
        random_first_move: Whether to randomize each opening move.
        seed: Optional seed for deterministic generation.
        player_configs: Optional per-player depth configuration.
        heuristic: Default heuristic name.

    Returns:
        An iterator yielding one dictionary per generated move.

    Yields:
        Dictionaries containing board, legal moves, move, player and result.

    Raises:
        ValueError: If the game count or depth configuration is invalid.
    """
    if game_count < 1:
        raise ValueError("game_count must be at least 1")
    if max_depth is None:
        max_depth = min_depth

    rng = random.Random(seed)
    for game_index in range(game_count):
        state = GameState.initial()
        if random_first_move:
            state = state.drop_piece(rng.choice(state.legal_moves()))
        game_examples = []

        while not state.is_terminal():
            settings = (player_configs or {}).get(
                state.current_player,
                {
                    "min_depth": min_depth,
                    "max_depth": max_depth,
                    "distribution": distribution,
                },
            )
            depth = choose_depth(
                int(settings["min_depth"]),
                int(settings["max_depth"]),
                str(settings["distribution"]),  # type: ignore[arg-type]
                rng,
            )
            strategy = MinimaxStrategy(depth=depth, heuristic=str(settings.get("heuristic", heuristic)))
            move = strategy.choose_move(state)
            game_examples.append(
                {
                    "board": encode_state(state),
                    "legal_moves": list(state.legal_moves()),
                    "move": move,
                    "player": state.current_player,
                    "depth": depth,
                }
            )
            state = state.drop_piece(move)

        result = state.winner() or 0
        for step, example in enumerate(game_examples):
            example["game"] = game_index
            example["step"] = step
            example["result"] = result
            yield example


def generate_games(
    game_count: int,
    min_depth: int = 3,
    max_depth: Optional[int] = None,
    distribution: Distribution = "uniform",
    random_first_move: bool = True,
    seed: Optional[int] = None,
    player_configs: Optional[Dict[int, PlayerConfig]] = None,
    heuristic: HeuristicName = "current",
) -> List[Dict]:
    """Generate all examples in memory.

    Use ``generate_and_save_run`` for larger datasets to avoid retaining all
    examples in memory.

    Args:
        game_count: Number of games to simulate.
        min_depth: Default minimum Minimax depth.
        max_depth: Default maximum Minimax depth.
        distribution: Default depth distribution.
        random_first_move: Whether to randomize openings.
        seed: Optional generation seed.
        player_configs: Optional per-player configuration.
        heuristic: Default heuristic name.

    Returns:
        All generated examples.
    """
    return list(
        iter_game_examples(
            game_count,
            min_depth,
            max_depth,
            distribution,
            random_first_move,
            seed,
            player_configs,
            heuristic,
        )
    )


def write_jsonl(examples: List[Dict], output: Path) -> None:
    """Write legacy JSONL output.

    Args:
        examples: Examples to serialize.
        output: Destination file.
    """
    with output.open("w", encoding="utf-8") as file:
        for example in examples:
            file.write(json.dumps(example) + "\n")


def write_dataset(examples: List[Dict], output: Path) -> None:
    """Write the complete dataset as a JSON array.

    Args:
        examples: Examples to serialize.
        output: Destination file.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(examples, indent=2) + "\n", encoding="utf-8")


def write_dataset_stream(
    examples: Iterator[Dict],
    output: Path,
    batch_size: int = 100,
) -> int:
    """Write a JSON array incrementally and return the example count.

    Args:
        examples: Iterator of examples.
        output: Destination file.
        batch_size: Number of serialized examples per flush.

    Returns:
        Number of written examples.

    Raises:
        ValueError: If ``batch_size`` is less than one.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    count = 0
    pending: List[str] = []
    with output.open("w", encoding="utf-8") as file:
        file.write("[\n")
        for example in examples:
            prefix = "" if count == 0 else ",\n"
            pending.append(prefix + json.dumps(example))
            count += 1
            if len(pending) >= batch_size:
                file.write("".join(pending))
                file.flush()
                pending.clear()
        if pending:
            file.write("".join(pending))
        file.write("\n]\n")
        file.flush()
    return count


def save_run(
    examples: List[Dict],
    config: Dict[str, Union[str, int, bool]],
    output_root: Path = Path("data/training"),
    timestamp: Optional[str] = None,
) -> Path:
    """Save examples and their exact configuration in a timestamped run.

    Args:
        examples: Examples to persist.
        config: Generation configuration.
        output_root: Parent directory for the run.
        timestamp: Optional run-directory name.

    Returns:
        The created run directory.

    Raises:
        FileExistsError: If the target run directory already exists.
    """
    run_name = timestamp or datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_directory = output_root / run_name
    if run_directory.exists():
        raise FileExistsError(f"dataset directory already exists: {run_directory}")

    run_directory.mkdir(parents=True)
    write_dataset(examples, run_directory / "data.json")
    stored_config = dict(config)
    stored_config["created_at"] = datetime.now().astimezone().isoformat()
    stored_config["example_count"] = len(examples)
    (run_directory / "config.json").write_text(
        json.dumps(stored_config, indent=2) + "\n",
        encoding="utf-8",
    )
    return run_directory


def generate_and_save_run(
    config: Dict[str, Union[str, int, bool]],
    output_root: Path = Path("data/training"),
    timestamp: Optional[str] = None,
) -> Path:
    """Generate one run directly to disk with incremental JSON output.

    Args:
        config: Generation configuration.
        output_root: Parent directory for the run.
        timestamp: Optional run-directory name.

    Returns:
        The completed run directory.

    Raises:
        FileExistsError: If the target run directory already exists.
        ValueError: If the configuration is invalid.
    """
    batch_size = int(config.get("batch_size", 100))
    run_name = timestamp or datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_directory = output_root / run_name
    if run_directory.exists():
        raise FileExistsError(f"dataset directory already exists: {run_directory}")
    run_directory.mkdir(parents=True)

    stored_config = dict(config)
    stored_config.update({
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "running",
        "example_count": 0,
    })
    config_path = run_directory / "config.json"
    config_path.write_text(json.dumps(stored_config, indent=2) + "\n", encoding="utf-8")

    examples = iter_game_examples(
        game_count=int(config["game_count"]),
        min_depth=int(config["min_depth"]),
        max_depth=int(config["max_depth"]),
        distribution=config["distribution"],  # type: ignore[arg-type]
        random_first_move=bool(config["random_first_move"]),
        seed=config.get("seed"),  # type: ignore[arg-type]
        heuristic=str(config.get("heuristic", "current")),  # type: ignore[arg-type]
        player_configs=(
            {
                1: {
                    "min_depth": int(config["player_one_min_depth"]),
                    "max_depth": int(config["player_one_max_depth"]),
                    "distribution": str(config["player_one_distribution"]),
                },
                -1: {
                    "min_depth": int(config["player_minus_one_min_depth"]),
                    "max_depth": int(config["player_minus_one_max_depth"]),
                    "distribution": str(config["player_minus_one_distribution"]),
                },
            }
            if str(config.get("difficulty_mode", "symmetric")) == "asymmetric"
            else None
        ),
    )
    count = write_dataset_stream(examples, run_directory / "data.json", batch_size)
    stored_config.update({"status": "completed", "example_count": count})
    config_path.write_text(json.dumps(stored_config, indent=2) + "\n", encoding="utf-8")
    return run_directory


def main(arguments: Optional[Sequence[str]] = None) -> Path:
    """Generate and persist one dataset run from command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--min-depth", type=int, default=1)
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--distribution", choices=("uniform", "bell"), default="uniform")
    parser.add_argument(
        "--random-first-move",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="randomize each game's opening move (default: enabled)",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument(
        "--heuristic",
        choices=("current", "ws22_minimax", "ws22_window"),
        default="current",
    )
    parser.add_argument("--output-root", type=Path, default=Path("data/training"))
    parser.add_argument("--timestamp", default=None, help="override the output directory name")
    args = parser.parse_args(arguments)

    config = {
        "game_count": args.games,
        "min_depth": args.min_depth,
        "max_depth": args.max_depth,
        "distribution": args.distribution,
        "random_first_move": args.random_first_move,
        "seed": args.seed,
        "batch_size": args.batch_size,
        "heuristic": args.heuristic,
    }
    run_directory = generate_and_save_run(config, args.output_root, args.timestamp)
    print(f"Saved dataset to {run_directory}")
    return run_directory


if __name__ == "__main__":
    main()
