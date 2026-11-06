import tempfile
import unittest
from pathlib import Path

import json

from training.generate_dataset import (
    depth_target,
    generate_and_save_run,
    generate_games,
    main,
    save_run,
    write_dataset,
    write_dataset_stream,
    write_jsonl,
)


class DatasetGeneratorTests(unittest.TestCase):
    def test_depth_target_rewards_faster_wins_and_delayed_losses(self):
        self.assertGreater(depth_target(1, 1, 2, 0.1), depth_target(1, 1, 6, 0.1))
        self.assertGreater(depth_target(-1, 1, 6, 0.1), depth_target(-1, 1, 2, 0.1))
        self.assertEqual(depth_target(0, 1, 6, 0.1), 0.0)

    def test_depth_target_is_stored_in_examples_when_enabled(self):
        examples = generate_games(
            game_count=1,
            min_depth=1,
            max_depth=1,
            random_first_move=False,
            seed=1,
            depth_heuristic=True,
            depth_penalty=0.01,
        )

        self.assertTrue(examples)
        self.assertTrue(all("target" in example for example in examples))
        self.assertTrue(all(-1 <= example["target"] <= 1 for example in examples))
    def test_examples_contain_legal_teacher_moves(self):
        examples = generate_games(game_count=1, min_depth=1, max_depth=2, seed=1)

        self.assertTrue(examples)
        for example in examples:
            self.assertEqual(len(example["board"]), 42)
            self.assertIn(example["move"], example["legal_moves"])
            self.assertIn(example["result"], (-1, 0, 1))
            self.assertIn(example["depth"], (1, 2))

    def test_depth_is_sampled_per_move(self):
        examples = generate_games(
            game_count=1,
            min_depth=1,
            max_depth=2,
            random_first_move=False,
            seed=1,
        )

        self.assertGreater(len({example["depth"] for example in examples}), 1)

    def test_tree_learning_persists_visited_search_nodes(self):
        examples = generate_games(
            game_count=1,
            min_depth=1,
            max_depth=1,
            random_first_move=False,
            seed=1,
            tree_learning=True,
        )

        self.assertTrue(examples[0]["tree_nodes"])
        self.assertEqual(
            examples[0]["tree_node_count"],
            len(examples[0]["tree_nodes"]),
        )
        self.assertIn("value", examples[0]["tree_nodes"][0])
        self.assertIn("exact", examples[0]["tree_nodes"][0])

    def test_asymmetric_depths_follow_the_current_player(self):
        examples = generate_games(
            game_count=1,
            min_depth=1,
            max_depth=1,
            random_first_move=False,
            player_configs={
                1: {"min_depth": 2, "max_depth": 2, "distribution": "uniform"},
                -1: {"min_depth": 4, "max_depth": 4, "distribution": "uniform"},
            },
            seed=1,
        )

        self.assertTrue(examples)
        for example in examples:
            expected_depth = 2 if example["player"] == 1 else 4
            self.assertEqual(example["depth"], expected_depth)

    def test_writes_json_lines(self):
        examples = generate_games(game_count=1, min_depth=1, seed=1)[:1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dataset.jsonl"
            write_jsonl(examples, output)

            self.assertEqual(len(output.read_text(encoding="utf-8").splitlines()), 1)

    def test_random_opening_is_optional(self):
        random_opening = generate_games(1, min_depth=1, random_first_move=True, seed=2)
        normal_opening = generate_games(1, min_depth=1, random_first_move=False, seed=2)

        self.assertEqual(sum(value != 0 for value in random_opening[0]["board"]), 1)
        self.assertEqual(sum(value != 0 for value in normal_opening[0]["board"]), 0)

    def test_writes_json_dataset(self):
        examples = generate_games(1, min_depth=1, seed=1)[:1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "data.json"
            write_dataset(examples, output)

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), examples)

    def test_saves_data_and_configuration_in_timestamp_directory(self):
        examples = generate_games(1, min_depth=1, seed=1)[:1]
        with tempfile.TemporaryDirectory() as directory:
            run_directory = save_run(
                examples,
                {"game_count": 1, "min_depth": 1, "max_depth": 1},
                Path(directory),
                timestamp="20261030_164500",
            )

            self.assertEqual(run_directory.name, "20261030_164500")
            self.assertTrue((run_directory / "data.json").is_file())
            config = json.loads((run_directory / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["example_count"], 1)
            self.assertIn("created_at", config)

    def test_cli_saves_requested_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            run_directory = main(
                [
                    "--games", "1",
                    "--min-depth", "1",
                    "--max-depth", "2",
                    "--distribution", "bell",
                    "--no-random-first-move",
                    "--seed", "7",
                    "--batch-size", "2",
                    "--heuristic", "ws22_window",
                    "--tree-learning",
                    "--depth-heuristic",
                    "--depth-penalty", "0.02",
                    "--output-root", directory,
                    "--timestamp", "cli-test",
                ]
            )
            config = json.loads((run_directory / "config.json").read_text(encoding="utf-8"))

            self.assertFalse(config["random_first_move"])
            self.assertEqual(config["distribution"], "bell")
            self.assertEqual(config["seed"], 7)
            self.assertEqual(config["batch_size"], 2)
            self.assertEqual(config["heuristic"], "ws22_window")
            self.assertTrue(config["tree_learning"])
            self.assertTrue(config["depth_heuristic"])
            self.assertEqual(config["depth_penalty"], 0.02)

    def test_stream_writer_creates_valid_json_in_batches(self):
        examples = iter({"index": index} for index in range(5))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "data.json"
            count = write_dataset_stream(examples, output, batch_size=2)

            self.assertEqual(count, 5)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))[4]["index"], 4)

    def test_streaming_run_persists_completed_status(self):
        with tempfile.TemporaryDirectory() as directory:
            run_directory = generate_and_save_run(
                {
                    "game_count": 1,
                    "min_depth": 1,
                    "max_depth": 1,
                    "distribution": "uniform",
                    "random_first_move": True,
                    "seed": 1,
                    "batch_size": 1,
                },
                Path(directory),
                "streaming-test",
            )
            config = json.loads((run_directory / "config.json").read_text(encoding="utf-8"))

            self.assertEqual(config["status"], "completed")
            self.assertGreater(config["example_count"], 0)

    def test_streaming_run_persists_asymmetric_player_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            run_directory = generate_and_save_run(
                {
                    "name": "Asymmetrischer Test",
                    "difficulty_mode": "asymmetric",
                    "game_count": 1,
                    "min_depth": 1,
                    "max_depth": 1,
                    "distribution": "uniform",
                    "player_one_min_depth": 2,
                    "player_one_max_depth": 2,
                    "player_one_distribution": "bell",
                    "player_minus_one_min_depth": 4,
                    "player_minus_one_max_depth": 4,
                    "player_minus_one_distribution": "uniform",
                    "random_first_move": False,
                    "seed": 1,
                    "batch_size": 10,
                },
                Path(directory),
                "asymmetric-test",
            )
            config = json.loads((run_directory / "config.json").read_text(encoding="utf-8"))

            self.assertEqual(config["difficulty_mode"], "asymmetric")
            self.assertEqual(config["player_one_distribution"], "bell")
            self.assertEqual(config["player_minus_one_min_depth"], 4)


if __name__ == "__main__":
    unittest.main()
