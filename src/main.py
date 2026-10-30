from pathlib import Path
from typing import List, Literal, Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from algos.minimax_strategy import MinimaxStrategy
from board_adapter import api_move, state_from_api_rows
from connect_four import COLUMNS, PLAYER_ONE, PLAYER_TWO, ROWS, GameState
from strategies import create_strategy

import logging

# logging
LOG = "logging_data.log"
logging.basicConfig(filename=LOG, filemode="w", level=logging.DEBUG)


target_ip = "http://172.17.0.1"

#########################
# 6 0  0  0  0  0  0  0 #
# 5 0  0  0  0  0  0  0 #
# 4 0  0  0  0  0  0  0 #
# 3 h  0  0  r  0  0  0 #
# 2 h  r  r  h  r  0  r #
# 1 h  h  h  r  h  r  r #
# # 1  2  3  4  5  6  7 #

# h = Human Player | r = Robot Player | 0 = empty space

# Feld={ "Column1": {"Row1":"h", "Row2":"0", "Row3":"0", "Row4":"0", "Row5":"0", "Row6":"0"},
# "Column2": {"Row1":"0", "Row2":"0", "Row3":"0", "Row4":"0", "Row5":"0", "Row6":"0"},
# "Column3": {"Row1":"0", "Row2":"0", "Row3":"0", "Row4":"0", "Row5":"0", "Row6":"0"},
# "Column4": {"Row1":"0", "Row2":"0", "Row3":"0", "Row4":"0", "Row5":"0", "Row6":"0"},
# "Column5": {"Row1":"0", "Row2":"0", "Row3":"0", "Row4":"0", "Row5":"0", "Row6":"0"},
# "Column6": {"Row1":"h", "Row2":"h", "Row3":"h", "Row4":"0", "Row5":"0", "Row6":"0"},
# "Column7": {"Row1":"r", "Row2":"r", "Row3":"0", "Row4":"0", "Row5":"0", "Row6":"0"}
# }

ROWS = 6
COLUMNS = 7


class Column(BaseModel):
    Row1: str
    Row2: str
    Row3: str
    Row4: str
    Row5: str
    Row6: str


class Board(BaseModel):
    Column1: Column
    Column2: Column
    Column3: Column
    Column4: Column
    Column5: Column
    Column6: Column
    Column7: Column
    Difficulty: int


app = FastAPI()
WEB_INDEX = Path(__file__).resolve().parent.parent / "web" / "index.html"


class WebMoveRequest(BaseModel):
    board: List[List[int]]
    current_player: int = PLAYER_TWO
    column: int = Field(ge=0, lt=COLUMNS)
    algorithm: Literal["random", "minimax"] = "minimax"
    difficulty: int = Field(default=4, ge=1, le=8)


class WebMoveResponse(BaseModel):
    board: List[List[int]]
    current_player: Optional[int]
    winner: Optional[int]
    draw: bool
    message: str


@app.get("/play")
async def web_game():
    return FileResponse(WEB_INDEX)


@app.post("/web/move", response_model=WebMoveResponse)
async def web_move(request: WebMoveRequest):
    try:
        state = GameState(
            tuple(tuple(row) for row in request.board),
            request.current_player,
        )
        if state.current_player != PLAYER_TWO:
            raise ValueError("the human player is not expected to move")
        state = state.drop_piece(request.column)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    winner = state.winner()
    if winner is None and not state.is_draw():
        strategy = create_strategy(request.algorithm, request.difficulty)
        state = state.drop_piece(strategy.choose_move(state))
        winner = state.winner()

    draw = state.is_draw()
    if winner == PLAYER_TWO:
        message = "Du gewinnst."
    elif winner == PLAYER_ONE:
        message = "Die KI gewinnt."
    elif draw:
        message = "Unentschieden."
    else:
        message = "Du bist am Zug."

    return WebMoveResponse(
        board=[list(row) for row in state.board],
        current_player=None if state.is_terminal() else state.current_player,
        winner=winner,
        draw=draw,
        message=message,
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}


# NOT USED
@app.get("/findNextMove")
async def calculateMove():
    return {"col": 5, "row": 3}

@app.post("/updateBoard")
async def updateBoard(newBoard: Board):
    rows = [
        [
            getattr(getattr(newBoard, f"Column{column}"), f"Row{row}")
            for column in range(1, 8)
        ]
        for row in range(1, 7)
    ]
    state = state_from_api_rows(rows, PLAYER_ONE)
    logging.info(str(state))

    winner = state.winner()
    if winner == PLAYER_TWO:
        requests.post(target_ip + ':8096/end', json={"winner": "HUMAN"})
        return {}
    if winner == PLAYER_ONE:
        requests.post(target_ip + ':8096/end', json={"winner": "ROBOT"})
        return {}
    if not state.legal_moves():
        requests.post(target_ip + ':8096/end', json={"winner": "DRAW"})
        return {}

    move_col = MinimaxStrategy(newBoard.Difficulty).choose_move(state)
    move_col, move_row = api_move(state, move_col)
    requests.post(target_ip + ':8096/move', json={"col": move_col, "row": move_row})

    next_state = state.drop_piece(move_col)
    if next_state.winner() == PLAYER_ONE:
        requests.post(target_ip + ':8096/end', json={"winner": "ROBOT"})
    elif next_state.is_draw():
        requests.post(target_ip + ':8096/end', json={"winner": "DRAW"})
    return {}


if __name__ == "__main__":
    uvicorn.run("main:app", port=8093, host="0.0.0.0", log_level="info")

# PORT Bildverarbeitung: 8090
# PORT Spielalgorithmus: 8093
# PORT Hardwaresteuerung: 8096
