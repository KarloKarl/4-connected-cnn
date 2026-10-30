import json
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from algos.minimax_strategy import MinimaxStrategy
from board_adapter import api_move, state_from_api_rows
from connect_four import COLUMNS, PLAYER_ONE, PLAYER_TWO, ROWS, GameState
from strategies import create_strategy
from training.viewer import decode_board_for_view, load_json, load_run
from training.generate_dataset import generate_and_save_run

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
WEB_ASSETS = Path(__file__).resolve().parent.parent / "web"
TRAINING_ROOT = WEB_ASSETS.parent / "data" / "training"
TRAINING_EXECUTOR = ThreadPoolExecutor(max_workers=1)
TRAINING_JOBS: Dict[str, Future] = {}
app.mount("/web/assets", StaticFiles(directory=WEB_ASSETS), name="web-assets")


class WebMoveRequest(BaseModel):
    board: List[List[int]]
    current_player: int = PLAYER_TWO
    column: int = Field(ge=0, lt=COLUMNS)
    algorithm: Literal["random", "minimax"] = "minimax"
    difficulty: int = Field(default=4, ge=1, le=6)


class WebMoveResponse(BaseModel):
    board: List[List[int]]
    current_player: Optional[int]
    winner: Optional[int]
    draw: bool
    message: str


class TrainingRunRequest(BaseModel):
    name: str = Field(default="Trainingslauf", min_length=1, max_length=80)
    difficulty_mode: Literal["symmetric", "asymmetric"] = "symmetric"
    game_count: int = Field(default=10, ge=1, le=10000)
    min_depth: int = Field(default=1, ge=1, le=8)
    max_depth: int = Field(default=5, ge=1, le=8)
    distribution: Literal["uniform", "bell"] = "uniform"
    random_first_move: bool = True
    seed: Optional[int] = None
    batch_size: int = Field(default=100, ge=1, le=10000)
    player_one_min_depth: int = Field(default=1, ge=1, le=8)
    player_one_max_depth: int = Field(default=5, ge=1, le=8)
    player_one_distribution: Literal["uniform", "bell"] = "uniform"
    player_minus_one_min_depth: int = Field(default=1, ge=1, le=8)
    player_minus_one_max_depth: int = Field(default=5, ge=1, le=8)
    player_minus_one_distribution: Literal["uniform", "bell"] = "uniform"


@app.get("/play")
async def web_game():
    return FileResponse(WEB_INDEX)


def training_run_directory(run_id: str) -> Path:
    """Resolve a run ID without allowing access outside the training root."""
    if not run_id or Path(run_id).name != run_id:
        raise HTTPException(status_code=404, detail="training run not found")
    directory = TRAINING_ROOT / run_id
    if not directory.is_dir():
        raise HTTPException(status_code=404, detail="training run not found")
    return directory


def training_job_status(run_id: str, future: Future) -> Dict:
    if not future.done():
        return {"id": run_id, "status": "running"}
    error = future.exception()
    if error is not None:
        return {"id": run_id, "status": "failed", "error": str(error)}
    return {"id": run_id, "status": "completed"}


def generate_training_run(
    run_id: str,
    config: Dict[str, object],
) -> Path:
    try:
        return generate_and_save_run(config, TRAINING_ROOT, run_id)
    except Exception as error:
        logging.exception("Training run %s failed", run_id)
        raise RuntimeError(f"Trainingslauf fehlgeschlagen: {error}") from error


@app.post("/web/training/runs", status_code=202)
async def start_training_run(request: TrainingRunRequest) -> Dict:
    if request.max_depth < request.min_depth:
        raise HTTPException(
            status_code=422,
            detail="max_depth muss mindestens min_depth entsprechen",
        )
    if request.difficulty_mode == "asymmetric":
        if request.player_one_max_depth < request.player_one_min_depth:
            raise HTTPException(status_code=422, detail="Spieler 1: Max. Tiefe muss mindestens Min. Tiefe entsprechen")
        if request.player_minus_one_max_depth < request.player_minus_one_min_depth:
            raise HTTPException(status_code=422, detail="Spieler -1: Max. Tiefe muss mindestens Min. Tiefe entsprechen")
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name darf nicht leer sein")
    if any(not future.done() for future in TRAINING_JOBS.values()):
        raise HTTPException(
            status_code=409,
            detail="Es läuft bereits ein Trainingslauf",
        )
    run_id = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    config = request.dict()
    config["name"] = name
    future = TRAINING_EXECUTOR.submit(generate_training_run, run_id, config)
    TRAINING_JOBS[run_id] = future
    return {"id": run_id, "status": "running", "config": config}


@app.get("/web/training/runs/{run_id}/status")
async def training_run_status(run_id: str) -> Dict:
    future = TRAINING_JOBS.get(run_id)
    if future is None:
        try:
            config = load_json(training_run_directory(run_id) / "config.json")
        except (HTTPException, OSError, ValueError, json.JSONDecodeError):
            raise HTTPException(status_code=404, detail="training run not found")
        return {"id": run_id, "status": config.get("status", "unknown")}
    return training_job_status(run_id, future)


@app.get("/web/training/runs")
async def training_runs() -> List[Dict]:
    if not TRAINING_ROOT.is_dir():
        return []
    runs = []
    for directory in sorted(TRAINING_ROOT.iterdir(), reverse=True):
        if not directory.is_dir():
            continue
        try:
            config = load_json(directory / "config.json")
            run = load_run(directory)
            games = run["games"]
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        runs.append({
            "id": directory.name,
            "name": config.get("name", directory.name),
            "config": config,
            "game_count": len(games),
            "example_count": config.get("example_count", 0),
            "difficulty_distribution": run["difficulty_distribution"],
        })
    return runs


@app.get("/web/training/runs/{run_id}/games")
async def training_run_games(run_id: str) -> List[Dict]:
    run = load_run(training_run_directory(run_id))
    return [
        {
            "index": index,
            "step_count": len(game),
            "result": game[0].get("result", 0) if game else 0,
            "depth": game[0].get("depth"),
        }
        for index, game in enumerate(run["games"])
    ]


@app.get("/web/training/runs/{run_id}/games/{game_index}")
async def training_game(run_id: str, game_index: int) -> Dict:
    run = load_run(training_run_directory(run_id))
    games = run["games"]
    if game_index < 0 or game_index >= len(games):
        raise HTTPException(status_code=404, detail="training game not found")
    steps = [
        {
            **example,
            "board": decode_board_for_view(example),
        }
        for example in games[game_index]
    ]
    return {
        "config": run["config"],
        "difficulty_distribution": run["difficulty_distribution"],
        "game_index": game_index,
        "steps": steps,
    }


@app.post("/web/move", response_model=WebMoveResponse)
async def web_move(request: WebMoveRequest):
    try:
        state = GameState(
            tuple(tuple(row) for row in request.board),
            request.current_player,
        )
        if state.current_player != PLAYER_TWO:
            raise ValueError("the human player is not expected to move")
        if state.is_terminal():
            raise ValueError("the game is already over")
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
