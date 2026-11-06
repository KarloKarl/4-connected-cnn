import json
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

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
    model_config = ConfigDict(
        json_schema_extra={
            "description": (
                "Eine Spalte mit sechs Feldern. Row1 ist die unterste "
                "Spielfeldzeile, Row6 die oberste."
            ),
            "example": {
                "Row1": "h",
                "Row2": "r",
                "Row3": "0",
                "Row4": "0",
                "Row5": "0",
                "Row6": "0",
            },
        }
    )

    Row1: Literal["0", "h", "r"] = Field(
        description="0 = leer, h = Human-Stein, r = Roboter-Stein.",
        examples=["0"],
    )
    Row2: Literal["0", "h", "r"] = Field(
        description="0 = leer, h = Human-Stein, r = Roboter-Stein.",
        examples=["0"],
    )
    Row3: Literal["0", "h", "r"] = Field(
        description="0 = leer, h = Human-Stein, r = Roboter-Stein.",
        examples=["0"],
    )
    Row4: Literal["0", "h", "r"] = Field(
        description="0 = leer, h = Human-Stein, r = Roboter-Stein.",
        examples=["0"],
    )
    Row5: Literal["0", "h", "r"] = Field(
        description="0 = leer, h = Human-Stein, r = Roboter-Stein.",
        examples=["0"],
    )
    Row6: Literal["0", "h", "r"] = Field(
        description="0 = leer, h = Human-Stein, r = Roboter-Stein.",
        examples=["0"],
    )

class Board(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": (
                "Hardware-Brett: sieben Spalten mit je sechs Feldern. "
                "Column1/Row1 ist links unten; Column7/Row6 ist rechts oben. "
                "Jeder Zellwert muss exakt 0, h oder r sein."
            ),
            "example": {
                "Column1": {"Row1": "h", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
                "Column2": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
                "Column3": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
                "Column4": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
                "Column5": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
                "Column6": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
                "Column7": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
                "Difficulty": 4,
            },
        }
    )

    Column1: Column = Field(description="Linke Spalte, nullbasierter Hardware-Spalte 0.")
    Column2: Column = Field(description="Spalte 2, nullbasierter Hardware-Spalte 1.")
    Column3: Column = Field(description="Spalte 3, nullbasierter Hardware-Spalte 2.")
    Column4: Column = Field(description="Mittlere Spalte, nullbasierter Hardware-Spalte 3.")
    Column5: Column = Field(description="Spalte 5, nullbasierter Hardware-Spalte 4.")
    Column6: Column = Field(description="Spalte 6, nullbasierter Hardware-Spalte 5.")
    Column7: Column = Field(description="Rechte Spalte, nullbasierter Hardware-Spalte 6.")
    Difficulty: int = Field(
        ge=1,
        le=6,
        description="Minimax-Suchtiefe des Roboters.",
        examples=[4],
    )

app = FastAPI(
    title="Connect Four API",
    description=(
        "REST API für das Connect-Four-Spiel, die Trainingsdatengenerierung "
        "und die bestehende Hardware-Schnittstelle."
    ),
    version="1.0.0",
    contact={"name": "Connect Four Project"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {
            "name": "Web",
            "description": "Webapp-Auslieferung und interaktive Spielzüge.",
        },
        {
            "name": "Training",
            "description": "Trainingsläufe starten, überwachen und analysieren.",
        },
        {
            "name": "Hardware",
            "description": "Kompatibilitätsendpunkte für die Hardwaresteuerung.",
        },
        {
            "name": "System",
            "description": "Basis- und Legacy-Endpunkte.",
        },
    ],
)
WEB_INDEX = Path(__file__).resolve().parent.parent / "web" / "index.html"
WEB_ASSETS = Path(__file__).resolve().parent.parent / "web"
TRAINING_ROOT = WEB_ASSETS.parent / "data" / "training"
TRAINING_EXECUTOR = ThreadPoolExecutor(max_workers=1)
TRAINING_JOBS: Dict[str, Future] = {}
app.mount("/web/assets", StaticFiles(directory=WEB_ASSETS), name="web-assets")


class WebMoveRequest(BaseModel):
    board: List[List[int]] = Field(
        description="6x7-Brett; 0 = leer, 1 und -1 = Spieler.",
        min_length=ROWS,
        max_length=ROWS,
        examples=[[[0] * COLUMNS for _ in range(ROWS)]],
    )
    current_player: int = Field(
        default=PLAYER_TWO,
        description="Spieler am Zug. Für die Webapp muss der Mensch -1 sein.",
        examples=[-1],
    )
    column: int = Field(
        ge=0,
        lt=COLUMNS,
        description="Spalte des menschlichen Zugs, nullbasiert.",
        examples=[3],
    )
    algorithm: Literal["random", "minimax"] = Field(
        default="minimax",
        description="Strategie für den automatischen Gegenzug.",
    )
    difficulty: int = Field(
        default=4,
        ge=1,
        le=6,
        description="Minimax-Suchtiefe.",
    )


class WebMoveResponse(BaseModel):
    board: List[List[int]] = Field(description="Aktualisiertes 6x7-Brett.")
    current_player: Optional[int] = Field(
        description="Spieler am Zug; null bei beendetem Spiel."
    )
    winner: Optional[int] = Field(description="Gewinner oder null.")
    draw: bool = Field(description="True bei einem Unentschieden.")
    message: str = Field(description="Benutzerfreundliche Statusmeldung.")


class TrainingStartResponse(BaseModel):
    id: str = Field(description="Eindeutige ID des Trainingslaufs.")
    status: str = Field(description="Initialer Status des Laufs.", examples=["running"])
    config: Dict[str, Any] = Field(description="Gespeicherte Laufkonfiguration.")


class TrainingStatusResponse(BaseModel):
    id: str = Field(description="ID des Trainingslaufs.")
    status: str = Field(description="running, completed, failed oder unknown.")
    error: Optional[str] = Field(default=None, description="Fehlertext bei status=failed.")


class TrainingRunSummary(BaseModel):
    id: str = Field(description="ID des Trainingslaufs.")
    name: str = Field(description="Anzeigename des Trainingslaufs.")
    config: Dict[str, Any] = Field(description="Vollständige Laufkonfiguration.")
    game_count: int = Field(description="Anzahl der Partien.")
    example_count: int = Field(description="Anzahl gespeicherter Trainingsbeispiele.")
    difficulty_distribution: Dict[str, int] = Field(
        description="Anzahl der Züge pro Minimax-Tiefe."
    )
    difficulty_distribution_by_player: Dict[str, Dict[str, int]] = Field(
        description="Tiefenverteilung getrennt nach Spieler."
    )


class TrainingGameSummary(BaseModel):
    index: int = Field(description="Nullbasierter Index der Partie.")
    step_count: int = Field(description="Anzahl der Züge der Partie.")
    result: int = Field(description="Spielergebnis: -1, 0 oder 1.")
    depth: Optional[int] = Field(description="Tiefe des ersten gespeicherten Zugs.")


class TrainingGameResponse(BaseModel):
    config: Dict[str, Any] = Field(description="Laufkonfiguration.")
    difficulty_distribution: Dict[str, int] = Field(description="Gesamtverteilung der Tiefen.")
    difficulty_distribution_by_player: Dict[str, Dict[str, int]] = Field(
        description="Tiefenverteilung nach Spieler."
    )
    game_index: int = Field(description="Index der angeforderten Partie.")
    steps: List[Dict[str, Any]] = Field(description="Züge inklusive dekodierter Bretter.")


class RootResponse(BaseModel):
    message: str


class LegacyMoveResponse(BaseModel):
    col: int = Field(description="Beispielspalte.")
    row: int = Field(description="Beispielzeile.")


class EmptyResponse(BaseModel):
    """Empty JSON object returned by legacy hardware operations."""

    pass


class HardwareMove(BaseModel):
    col: int = Field(
        ge=0,
        lt=COLUMNS,
        description="Vom Roboter gewählte Spalte, nullbasiert (0-6).",
        examples=[3],
    )
    row: int = Field(
        ge=0,
        lt=ROWS,
        description="Zielzeile des Robotersteins, nullbasiert (0-5).",
        examples=[0],
    )


class HardwareUpdateResponse(BaseModel):
    status: Literal["move", "game_over"] = Field(
        description="move = Roboterzug wurde gesendet; game_over = Partie beendet.",
        examples=["move"],
    )
    winner: Optional[Literal["HUMAN", "ROBOT", "DRAW"]] = Field(
        default=None,
        description="Endstatus der Partie. Bei laufender Partie null.",
        examples=["ROBOT"],
    )
    move: Optional[HardwareMove] = Field(
        default=None,
        description="Roboterzug, sofern ein Zug ausgeführt wurde.",
    )
    message: str = Field(
        description="Zusammenfassung der Verarbeitung.",
        examples=["Roboterzug an die Hardwaresteuerung gesendet."],
    )


class TrainingRunRequest(BaseModel):
    name: str = Field(default="Trainingslauf", min_length=1, max_length=80, description="Anzeigename.")
    difficulty_mode: Literal["symmetric", "asymmetric"] = Field(
        default="symmetric", description="Gemeinsame oder spielerspezifische Schwierigkeit."
    )
    game_count: int = Field(default=10, ge=1, le=10000, description="Anzahl der Partien.")
    min_depth: int = Field(default=1, ge=1, le=8, description="Minimale Minimax-Tiefe.")
    max_depth: int = Field(default=5, ge=1, le=8, description="Maximale Minimax-Tiefe.")
    distribution: Literal["uniform", "bell"] = Field(
        default="uniform", description="Verteilung der zufällig gezogenen Tiefen."
    )
    random_first_move: bool = Field(
        default=True, description="Partien mit einem zufälligen Eröffnungszug starten."
    )
    seed: Optional[int] = Field(default=None, description="Optionaler Zufalls-Seed.")
    batch_size: int = Field(default=100, ge=1, le=10000, description="Schreibbatchgröße.")
    heuristic: Literal["current", "ws22_minimax", "ws22_window"] = Field(
        default="current", description="Bewertungsfunktion des Minimax-Lehrers."
    )
    player_one_min_depth: int = Field(default=1, ge=1, le=8, description="Minimale Tiefe für Spieler 1.")
    player_one_max_depth: int = Field(default=5, ge=1, le=8, description="Maximale Tiefe für Spieler 1.")
    player_one_distribution: Literal["uniform", "bell"] = Field(
        default="uniform", description="Tiefenverteilung für Spieler 1."
    )
    player_minus_one_min_depth: int = Field(default=1, ge=1, le=8, description="Minimale Tiefe für Spieler -1.")
    player_minus_one_max_depth: int = Field(default=5, ge=1, le=8, description="Maximale Tiefe für Spieler -1.")
    player_minus_one_distribution: Literal["uniform", "bell"] = Field(
        default="uniform", description="Tiefenverteilung für Spieler -1."
    )


@app.get(
    "/play",
    tags=["Web"],
    summary="Webapp ausliefern",
    description="Liefert die browserbasierte Connect-Four-Oberfläche.",
    response_class=FileResponse,
)
async def web_game() -> FileResponse:
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


@app.post(
    "/web/training/runs",
    status_code=202,
    response_model=TrainingStartResponse,
    tags=["Training"],
    summary="Trainingslauf starten",
    description="Startet einen Trainingslauf asynchron. Es kann nur ein Lauf gleichzeitig aktiv sein.",
    responses={
        202: {"description": "Trainingslauf wurde gestartet."},
        409: {"description": "Es läuft bereits ein Trainingslauf."},
        422: {"description": "Ungültige Laufkonfiguration."},
    },
)
async def start_training_run(request: TrainingRunRequest) -> TrainingStartResponse:
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
    return TrainingStartResponse(id=run_id, status="running", config=config)


@app.get(
    "/web/training/runs/{run_id}/status",
    response_model=TrainingStatusResponse,
    tags=["Training"],
    summary="Trainingslaufstatus abrufen",
    description="Liefert den aktuellen Status eines Trainingslaufs.",
    responses={404: {"description": "Trainingslauf nicht gefunden."}},
)
async def training_run_status(run_id: str) -> Dict[str, Any]:
    future = TRAINING_JOBS.get(run_id)
    if future is None:
        try:
            config = load_json(training_run_directory(run_id) / "config.json")
        except (HTTPException, OSError, ValueError, json.JSONDecodeError):
            raise HTTPException(status_code=404, detail="training run not found")
        return {"id": run_id, "status": config.get("status", "unknown")}
    return training_job_status(run_id, future)


@app.get(
    "/web/training/runs",
    response_model=List[TrainingRunSummary],
    tags=["Training"],
    summary="Trainingsläufe auflisten",
    description="Listet gespeicherte Trainingsläufe inklusive Konfiguration und Verteilungen.",
)
async def training_runs() -> List[Dict[str, Any]]:
    if not TRAINING_ROOT.is_dir():
        return []
    runs: List[Dict[str, Any]] = []
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
            "difficulty_distribution_by_player": run["difficulty_distribution_by_player"],
        })
    return runs


@app.get(
    "/web/training/runs/{run_id}/games",
    response_model=List[TrainingGameSummary],
    tags=["Training"],
    summary="Partien eines Trainingslaufs auflisten",
    description="Liefert eine kompakte Übersicht der Partien eines Trainingslaufs.",
    responses={404: {"description": "Trainingslauf nicht gefunden."}},
)
async def training_run_games(run_id: str) -> List[Dict[str, Any]]:
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


@app.get(
    "/web/training/runs/{run_id}/games/{game_index}",
    response_model=TrainingGameResponse,
    tags=["Training"],
    summary="Partie mit Zügen abrufen",
    description="Liefert alle Züge und dekodierten Brettzustände einer Partie.",
    responses={
        404: {"description": "Trainingslauf oder Partie nicht gefunden."},
    },
)
async def training_game(run_id: str, game_index: int) -> Dict[str, Any]:
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
        "difficulty_distribution_by_player": run["difficulty_distribution_by_player"],
        "game_index": game_index,
        "steps": steps,
    }


@app.post(
    "/web/move",
    response_model=WebMoveResponse,
    tags=["Web"],
    summary="Menschlichen Spielzug ausführen",
    description="Prüft den menschlichen Zug und berechnet anschließend den KI-Gegenzug.",
    responses={400: {"description": "Ungültiger Zug oder bereits beendetes Spiel."}},
)
async def web_move(request: WebMoveRequest) -> WebMoveResponse:
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

@app.get(
    "/",
    response_model=RootResponse,
    tags=["System"],
    summary="API-Status prüfen",
    description="Ein einfacher Erreichbarkeitscheck der API.",
)
async def root() -> Dict[str, str]:
    return {"message": "Hello World"}


# NOT USED
@app.get(
    "/findNextMove",
    response_model=LegacyMoveResponse,
    tags=["System"],
    summary="Legacy-Beispielzug abrufen",
    description="Historischer Kompatibilitätsendpunkt; wird von der aktuellen Webapp nicht verwendet.",
)
async def calculateMove() -> Dict[str, int]:
    return {"col": 5, "row": 3}

@app.post(
    "/updateBoard",
    response_model=HardwareUpdateResponse,
    tags=["Hardware"],
    summary="Hardware-Brett aktualisieren",
    description=(
        "Die Hardwaresteuerung sendet das vollständige 7x6-Brett an diesen "
        "Endpunkt. Die API erkennt Gewinn oder Unentschieden. Ist die Partie "
        "noch aktiv, berechnet sie den Roboterzug und sendet ihn als "
        "nullbasiertes (col, row)-Paar an die Hardwaresteuerung auf Port 8096. "
        "Bei einem Spielende wird stattdessen ein Endstatus gesendet."
    ),
    responses={
        200: {
            "description": (
                "Brett verarbeitet. Bei status=move enthält move den an Port "
                "8096 gesendeten Roboterzug; bei status=game_over enthält "
                "winner HUMAN, ROBOT oder DRAW."
            ),
        },
        422: {
            "description": (
                "Ungültiges Brett: Jede Zelle muss exakt 0, h oder r sein; "
                "Difficulty muss zwischen 1 und 6 liegen."
            ),
        },
    },
)
async def updateBoard(newBoard: Board) -> HardwareUpdateResponse:
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
        return HardwareUpdateResponse(
            status="game_over",
            winner="HUMAN",
            message="Partie durch den Menschen gewonnen.",
        )
    if winner == PLAYER_ONE:
        requests.post(target_ip + ':8096/end', json={"winner": "ROBOT"})
        return HardwareUpdateResponse(
            status="game_over",
            winner="ROBOT",
            message="Partie durch den Roboter gewonnen.",
        )
    if not state.legal_moves():
        requests.post(target_ip + ':8096/end', json={"winner": "DRAW"})
        return HardwareUpdateResponse(
            status="game_over",
            winner="DRAW",
            message="Partie endet unentschieden.",
        )

    move_col = MinimaxStrategy(newBoard.Difficulty).choose_move(state)
    move_col, move_row = api_move(state, move_col)
    requests.post(target_ip + ':8096/move', json={"col": move_col, "row": move_row})

    next_state = state.drop_piece(move_col)
    if next_state.winner() == PLAYER_ONE:
        requests.post(target_ip + ':8096/end', json={"winner": "ROBOT"})
        return HardwareUpdateResponse(
            status="game_over",
            winner="ROBOT",
            move=HardwareMove(col=move_col, row=move_row),
            message="Roboterzug ausgeführt; der Roboter gewinnt.",
        )
    elif next_state.is_draw():
        requests.post(target_ip + ':8096/end', json={"winner": "DRAW"})
        return HardwareUpdateResponse(
            status="game_over",
            winner="DRAW",
            move=HardwareMove(col=move_col, row=move_row),
            message="Roboterzug ausgeführt; Partie endet unentschieden.",
        )
    return HardwareUpdateResponse(
        status="move",
        move=HardwareMove(col=move_col, row=move_row),
        message="Roboterzug an die Hardwaresteuerung gesendet.",
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8093, host="0.0.0.0", log_level="info")

# PORT Bildverarbeitung: 8090
# PORT Spielalgorithmus: 8093
# PORT Hardwaresteuerung: 8096
