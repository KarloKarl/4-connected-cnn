import asyncio
import unittest

from fastapi import HTTPException

from connect_four import PLAYER_ONE, PLAYER_TWO
from main import TrainingRunRequest, WebMoveRequest, start_training_run, web_move


class WebApiTests(unittest.TestCase):
    def test_training_run_name_accepts_bounded_text(self):
        request = TrainingRunRequest(name="  Mein Lauf  ")

        self.assertEqual(request.name, "  Mein Lauf  ")
        self.assertLessEqual(len(request.name), 80)

    def test_training_run_rejects_invalid_depth_range(self):
        with self.assertRaises(HTTPException) as context:
            asyncio.run(start_training_run(
                TrainingRunRequest(game_count=1, min_depth=5, max_depth=3),
            ))
        self.assertEqual(context.exception.status_code, 422)

    def test_move_returns_human_and_ai_turns(self):
        request = WebMoveRequest(
            board=[[0] * 7 for _ in range(6)],
            column=3,
            algorithm="minimax",
            difficulty=1,
        )

        result = asyncio.run(web_move(request))

        self.assertEqual(result.board[0][3], PLAYER_TWO)
        self.assertEqual(
            sum(cell == PLAYER_ONE for row in result.board for cell in row),
            1,
        )
        self.assertEqual(result.current_player, PLAYER_TWO)

    def test_full_column_is_rejected(self):
        board = [[0] * 7 for _ in range(6)]
        for row in range(6):
            board[row][0] = PLAYER_ONE if row % 2 == 0 else PLAYER_TWO

        with self.assertRaises(HTTPException) as context:
            asyncio.run(web_move(WebMoveRequest(board=board, column=0)))
        self.assertEqual(context.exception.status_code, 400)

    def test_finished_game_rejects_follow_up_moves(self):
        board = [
            [PLAYER_TWO, PLAYER_TWO, PLAYER_TWO, PLAYER_TWO, 0, 0, 0],
            [0] * 7,
            [0] * 7,
            [0] * 7,
            [0] * 7,
            [0] * 7,
        ]

        with self.assertRaises(HTTPException) as context:
            asyncio.run(web_move(WebMoveRequest(board=board, column=4)))
        self.assertEqual(context.exception.status_code, 400)

    def test_web_difficulty_is_limited_to_interactive_range(self):
        with self.assertRaises(ValueError):
            WebMoveRequest(board=[[0] * 7 for _ in range(6)], column=0, difficulty=7)


if __name__ == "__main__":
    unittest.main()
