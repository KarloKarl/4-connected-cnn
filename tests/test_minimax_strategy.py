import unittest

from algos.minimax_strategy import MinimaxStrategy
from connect_four import GameState


class MinimaxStrategyTests(unittest.TestCase):
    def test_takes_immediate_win(self):
        state = GameState.initial()
        for column in (0, 0, 1, 1, 2, 2):
            state = state.drop_piece(column)

        self.assertEqual(MinimaxStrategy(depth=2).choose_move(state), 3)

    def test_blocks_immediate_loss(self):
        state = GameState.initial()
        for column in (6, 0, 6, 1, 5, 2):
            state = state.drop_piece(column)

        self.assertEqual(MinimaxStrategy(depth=2).choose_move(state), 3)

    def test_rejects_invalid_depth(self):
        with self.assertRaises(ValueError):
            MinimaxStrategy(depth=0)


if __name__ == "__main__":
    unittest.main()
