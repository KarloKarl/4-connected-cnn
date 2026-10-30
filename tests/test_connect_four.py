import unittest

from connect_four import COLUMNS, EMPTY, PLAYER_ONE, PLAYER_TWO, GameState


class GameStateTests(unittest.TestCase):
    def test_initial_state_has_all_legal_columns(self):
        state = GameState.initial()

        self.assertEqual(state.legal_moves(), tuple(range(COLUMNS)))
        self.assertFalse(state.is_terminal())

    def test_drop_piece_uses_gravity_and_alternates_player(self):
        state = GameState.initial().drop_piece(2).drop_piece(2)

        self.assertEqual(state.board[0][2], PLAYER_ONE)
        self.assertEqual(state.board[1][2], PLAYER_TWO)
        self.assertEqual(state.current_player, PLAYER_ONE)

    def test_horizontal_win(self):
        state = GameState.initial()
        for column in (0, 0, 1, 1, 2, 2, 3):
            state = state.drop_piece(column)

        self.assertEqual(state.winner(), PLAYER_ONE)
        self.assertTrue(state.is_terminal())

    def test_diagonal_win(self):
        state = GameState.initial()
        for column in (0, 1, 1, 2, 2, 3, 2, 3, 3, 4, 3):
            state = state.drop_piece(column)

        self.assertEqual(state.winner(), PLAYER_ONE)

    def test_full_column_is_not_legal(self):
        state = GameState.initial()
        for _ in range(3):
            state = state.drop_piece(0).drop_piece(0)

        self.assertNotIn(0, state.legal_moves())
        with self.assertRaises(ValueError):
            state.drop_piece(0)

    def test_empty_encoding_is_preserved(self):
        state = GameState.initial().drop_piece(0)

        encoded = state.encode_for_player(PLAYER_TWO)

        self.assertEqual(encoded[0][0], PLAYER_TWO)
        self.assertEqual(encoded[0][1], EMPTY)


if __name__ == "__main__":
    unittest.main()
