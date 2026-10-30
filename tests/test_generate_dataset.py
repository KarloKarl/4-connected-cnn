import tempfile
import unittest
from pathlib import Path

import json

from training.generate_dataset import generate_games, save_run, write_dataset, write_jsonl


class DatasetGeneratorTests(unittest.TestCase):
    def test_examples_contain_legal_teacher_moves(self):
        examples = generate_games(game_count=1, min_depth=1, max_depth=2, seed=1)

        self.assertTrue(examples)
        for example in examples:
            self.assertEqual(len(example["board"]), 42)
            self.assertIn(example["move"], example["legal_moves"])
            self.assertIn(example["result"], (-1, 0, 1))
            self.assertIn(example["depth"], (1, 2))

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


if __name__ == "__main__":
    unittest.main()
