import tempfile
import unittest
from pathlib import Path

from training.generate_dataset import generate_games, write_jsonl


class DatasetGeneratorTests(unittest.TestCase):
    def test_examples_contain_legal_teacher_moves(self):
        examples = generate_games(game_count=1, depth=1)

        self.assertTrue(examples)
        for example in examples:
            self.assertEqual(len(example["board"]), 42)
            self.assertIn(example["move"], example["legal_moves"])
            self.assertIn(example["result"], (-1, 0, 1))

    def test_writes_json_lines(self):
        examples = generate_games(game_count=1, depth=1)[:1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dataset.jsonl"
            write_jsonl(examples, output)

            self.assertEqual(len(output.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
