"""棋谱历史记录测试。"""

from __future__ import annotations

from backend.game.config import PolyJumpConfig
from backend.game.game_state import GameState
from backend.game.serializers import history_to_dict


def test_history_records_initial_and_snapshots():
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    state = GameState(cfg)

    assert len(state.initial_pieces) == 40
    assert state.snapshots == []

    moves = state.legal_moves()
    assert state.perform_move(moves[0])

    assert len(state.move_history) == 1
    assert len(state.snapshots) == 1

    history = history_to_dict(state)
    assert history["winner"] is None
    assert len(history["snapshots"]) == 1
    assert len(history["initial_pieces"]) == 40
