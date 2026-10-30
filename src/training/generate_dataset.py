"""Generate supervised Connect Four examples from Minimax games."""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Literal, Optional, Sequence, Union

from algos.minimax_strategy import MinimaxStrategy
from connect_four import GameState

Distribution = Literal["uniform", "bell"]


def encode_state(state: GameState) -> List[int]:
    """Encode the board from the current player's perspective."""
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
) -> Iterator[Dict]:
    if game_count < 1:
        raise ValueError("game_count must be at least 1")
    if max_depth is None:
        max_depth = min_depth

    rng = random.Random(seed)
    for game_index in range(game_count):
        state = GameState.initial()
        depth = choose_depth(min_depth, max_depth, distribution, rng)
        if random_first_move:
            state = state.drop_piece(rng.choice(state.legal_moves()))
        strategy = MinimaxStrategy(depth=depth)
        game_examples = []

        while not state.is_terminal():
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
) -> List[Dict]:
    """Generate all examples in memory; use ``generate_and_save_run`` for large runs."""
    return list(
        iter_game_examples(
            game_count,
            min_depth,
            max_depth,
            distribution,
            random_first_move,
            seed,
        )
    )


def write_jsonl(examples: List[Dict], output: Path) -> None:
    """Write legacy JSONL output; new runs should use ``write_dataset``."""
    with output.open("w", encoding="utf-8") as file:
        for example in examples:
            file.write(json.dumps(example) + "\n")


def write_dataset(examples: List[Dict], output: Path) -> None:
    """Write the complete dataset as a JSON array."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(examples, indent=2) + "\n", encoding="utf-8")


def write_dataset_stream(
    examples: Iterator[Dict],
    output: Path,
    batch_size: int = 100,
) -> int:
    """Write a JSON array incrementally and flush every ``batch_size`` examples."""
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
    """Save one generation run and its exact configuration."""
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
    """Generate one run directly to disk without retaining all examples."""
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
    }
    run_directory = generate_and_save_run(config, args.output_root, args.timestamp)
    print(f"Saved dataset to {run_directory}")
    return run_directory


if __name__ == "__main__":
    main()
