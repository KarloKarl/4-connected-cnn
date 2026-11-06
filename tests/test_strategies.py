import unittest

from strategies import create_strategy
from algos.minimax_strategy import MinimaxStrategy
from algos.random_strategy import RandomStrategy


class StrategyFactoryTests(unittest.TestCase):
    def test_creates_supported_algorithms(self):
        self.assertIsInstance(create_strategy("random", 4), RandomStrategy)
        self.assertIsInstance(create_strategy("minimax", 3), MinimaxStrategy)
        self.assertEqual(
            create_strategy("minimax", 3, "ws22_minimax").heuristic,
            "ws22_minimax",
        )

    def test_rejects_unknown_algorithm(self):
        with self.assertRaises(ValueError):
            create_strategy("unknown", 4)
