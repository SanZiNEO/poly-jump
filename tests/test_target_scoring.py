"""目标区积分：只奖励从外部进入目标区，不奖励目标区内移动。"""

from __future__ import annotations

from backend.game.config import PolyJumpConfig, ScoringConfig
from backend.game.game_state import GameState


def make_state() -> GameState:
    cfg = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
        scoring=ScoringConfig(enabled=True, target_zone_points=20),
    )
    state = GameState(cfg)
    state.board.pieces = {}
    state.board.player_targets = {1: {(1, 0, 0), (2, 0, 0)}, 2: set()}
    state.board.player_bases = {1: set(), 2: set()}
    return state


def test_enter_target_from_outside_scores():
    state = make_state()
    state.board.set_piece((0, 0, 0), 1)
    state.current_player = 1

    actions = state.legal_actions()
    target_action = [a for a in actions if a[-1] == (1, 0, 0)]
    assert target_action
    assert state.perform_action(target_action[0])

    assert state.scores[1] == 20


def test_action_inside_target_does_not_score_again():
    state = make_state()
    state.board.set_piece((1, 0, 0), 1)
    state.current_player = 1

    actions = state.legal_actions()
    inside_action = [a for a in actions if a[-1] == (2, 0, 0)]
    assert inside_action
    assert state.perform_action(inside_action[0])

    assert state.scores[1] == 0
