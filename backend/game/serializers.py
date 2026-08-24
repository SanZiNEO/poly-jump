"""把 GameState / 棋盘数据转换为前端友好的 JSON 字典。"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple


def point_key(pos: Tuple[int, int, int]) -> str:
    return f"{pos[0]},{pos[1]},{pos[2]}"


def path_to_lists(path: Sequence[Sequence[int]]) -> List[List[int]]:
    return [list(p) for p in path]


def state_to_dict(state: Any) -> Dict[str, Any]:
    board = state.board
    return {
        "game_id": state.id,
        "config": state.config.model_dump(),
        "points": [list(p) for p in board.points],
        "routes": board.geometry.generate_routes(),
        "pieces": {
            point_key(pos): owner
            for pos, owner in board.pieces.items()
        },
        "current_player": state.current_player,
        "winner": state.winner,
        "bases": {
            str(player): [list(p) for p in base]
            for player, base in board.player_bases.items()
        },
        "targets": {
            str(player): [list(p) for p in target]
            for player, target in board.player_targets.items()
        },
        "history": list(state.move_history),
    }
