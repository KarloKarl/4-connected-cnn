import unittest

from board_adapter import api_move, state_from_api_rows
from connect_four import PLAYER_ONE, PLAYER_TWO


class BoardAdapterTests(unittest.TestCase):
    def test_converts_api_rows_and_finds_next_row(self):
        rows = [["0"] * 7 for _ in range(6)]
        rows[0][3] = "h"
        state = state_from_api_rows(rows, PLAYER_ONE)

        self.assertEqual(state.board[0][3], PLAYER_TWO)
        self.assertEqual(api_move(state, 3), (3, 1))

    def test_rejects_unknown_board_values(self):
        rows = [["0"] * 7 for _ in range(6)]
        rows[0][0] = "invalid"

        with self.assertRaises(ValueError):
            state_from_api_rows(rows, PLAYER_ONE)


if __name__ == "__main__":
    unittest.main()
