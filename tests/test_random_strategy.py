import unittest

from algos.random_strategy import RandomStrategy
from connect_four import COLUMNS, PLAYER_ONE, PLAYER_TWO, ROWS, GameState


class RandomStrategyTests(unittest.TestCase):
    def test_choose_move_returns_a_legal_column(self):
        state = GameState.initial().drop_piece(0)

        move = RandomStrategy().choose_move(state)

        self.assertIn(move, state.legal_moves())

    def test_choose_move_rejects_a_terminal_board(self):
        board = tuple(
            tuple(PLAYER_ONE if (row + column) % 2 == 0 else PLAYER_TWO
                  for column in range(COLUMNS))
            for row in range(ROWS)
        )
        state = GameState(board)

        with self.assertRaises(ValueError):
            RandomStrategy().choose_move(state)


if __name__ == "__main__":
    unittest.main()
