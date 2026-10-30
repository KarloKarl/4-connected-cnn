import asyncio
import unittest

from fastapi import HTTPException

from connect_four import PLAYER_ONE, PLAYER_TWO
from main import WebMoveRequest, web_move


class WebApiTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
