import unittest

from connect_four import PLAYER_ONE, PLAYER_TWO, GameState
from play import play, render


class PlayTests(unittest.TestCase):
    def test_render_contains_board_coordinates(self):
        self.assertIn("1 2 3 4 5 6 7", render(GameState.initial()))

    def test_game_can_be_played_with_scripted_human_moves(self):
        moves = iter(str(column) for _ in range(10) for column in range(1, 8))
        output = []

        winner = play("random", 1, input_fn=lambda _: next(moves), output_fn=output.append)

        self.assertIn(winner, (PLAYER_ONE, PLAYER_TWO, None))
        self.assertTrue(output)


if __name__ == "__main__":
    unittest.main()
