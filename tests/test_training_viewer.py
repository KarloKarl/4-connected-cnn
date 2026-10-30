import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import main
from training.viewer import decode_board_for_view, group_examples


class TrainingViewerTests(unittest.TestCase):
    def test_decodes_player_relative_board_for_viewer(self):
        example = {"board": [-1, 0, 1], "player": -1}

        self.assertEqual(decode_board_for_view(example), [1, 0, -1])

    def test_groups_legacy_examples_without_game_metadata(self):
        examples = [
            {"board": [0] * 42, "move": 3},
            {"board": [1, -1] + [0] * 40, "move": 3},
            {"board": [0] * 42, "move": 2},
        ]

        games = group_examples(examples)

        self.assertEqual([len(game) for game in games], [2, 1])

    def test_training_endpoints_return_config_and_steps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run-1"
            run.mkdir()
            (run / "config.json").write_text(
                json.dumps({"min_depth": 1, "example_count": 1}),
                encoding="utf-8",
            )
            (run / "data.json").write_text(
                json.dumps([{
                    "board": [-1] + [0] * 41,
                    "move": 3,
                    "player": -1,
                    "depth": 1,
                    "result": 0,
                    "game": 0,
                    "step": 0,
                }]),
                encoding="utf-8",
            )
            original_root = main.TRAINING_ROOT
            main.TRAINING_ROOT = root
            try:
                runs = asyncio.run(main.training_runs())
                games = asyncio.run(main.training_run_games("run-1"))
                detail = asyncio.run(main.training_game("run-1", 0))
            finally:
                main.TRAINING_ROOT = original_root

        self.assertEqual(runs[0]["config"]["min_depth"], 1)
        self.assertEqual(games[0]["step_count"], 1)
        self.assertEqual(detail["config"]["example_count"], 1)
        self.assertEqual(detail["steps"][0]["move"], 3)
        self.assertEqual(detail["steps"][0]["board"][0], 1)
        self.assertEqual(detail["difficulty_distribution"], {"1": 1})
        self.assertEqual(
            detail["difficulty_distribution_by_player"],
            {"-1": {"1": 1}, "1": {}},
        )


if __name__ == "__main__":
    unittest.main()
