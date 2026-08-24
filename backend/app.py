"""PolyJump FastAPI 入口。

启动：uvicorn backend.app:app
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .game.ai import GreedyAI, ProgressAI, RandomAI
from .game.config import PolyJumpConfig
from .game.direction_registry import get_available_sets
from .game.game_state import GameState
from .game.serializers import history_to_dict, path_to_lists, state_to_dict

app = FastAPI(title="PolyJump", version="0.1.0")

GAMES: Dict[str, GameState] = {}


class NewGameRequest(BaseModel):
    config: PolyJumpConfig


class MoveRequest(BaseModel):
    path: List[List[int]]


def _get_state(game_id: str) -> GameState:
    state = GAMES.get(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail="game not found")
    return state


@app.get("/api/config")
def get_config():
    return PolyJumpConfig().model_dump()


@app.get("/api/direction-sets")
def get_direction_sets():
    return get_available_sets()


@app.post("/api/game/new", status_code=201)
def new_game(req: NewGameRequest):
    try:
        state = GameState(req.config)
    except NotImplementedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    GAMES[state.id] = state
    return {"game_id": state.id, "state": state_to_dict(state)}


@app.get("/api/game/{game_id}")
def get_game(game_id: str):
    state = _get_state(game_id)
    return state_to_dict(state)


@app.get("/api/game/{game_id}/history")
def get_game_history(game_id: str):
    state = _get_state(game_id)
    return history_to_dict(state)


@app.get("/api/game/{game_id}/legal-moves")
def legal_moves(game_id: str, piece: Optional[str] = None):
    state = _get_state(game_id)
    if piece:
        try:
            key = tuple(int(x) for x in piece.split(","))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="piece 格式应为 x,y,z") from exc
        paths = state.legal_moves_for(key)
    else:
        paths = state.legal_moves()

    return {
        "player": state.current_player,
        "current_pos": list(state.board.pieces_for_player(state.current_player)),
        "paths": [path_to_lists(p) for p in paths],
    }


@app.post("/api/game/{game_id}/move")
def move(game_id: str, req: MoveRequest):
    state = _get_state(game_id)
    if not state.perform_move(req.path):
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "illegal move", "state": state_to_dict(state)},
        )
    return {"ok": True, "state": state_to_dict(state)}


@app.post("/api/game/{game_id}/ai-move")
def ai_move(game_id: str, ai_type: str = "progress"):
    state = _get_state(game_id)
    paths = state.legal_moves()
    if ai_type == "progress":
        selected = ProgressAI().select_move(state.board, state.current_player, paths)
    elif ai_type == "greedy":
        selected = GreedyAI().select_move(state.board, state.current_player, paths)
    else:
        selected = RandomAI().select_move(paths)
    if selected is None:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "no legal moves", "state": state_to_dict(state)},
        )

    if not state.perform_move(selected):
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "illegal AI move", "state": state_to_dict(state)},
        )
    return {"ok": True, "move": path_to_lists(selected), "state": state_to_dict(state)}


# 前端静态文件；API 路由已先注册，此处挂载兜底。
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
