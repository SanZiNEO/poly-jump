"""GameEnv 干净接口测试。"""

from __future__ import annotations

import pytest

from backend.game.config import PolyJumpConfig
from backend.game.env import GameEnv


def make_env() -> GameEnv:
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    return GameEnv(cfg)


def test_env_reset_and_legal_moves():
    env = make_env()
    result = env.reset()

    assert result.winner is None
    assert result.done is False
    assert len(result.legal_paths) > 0
    assert len(result.legal_actions) == len(result.legal_paths)


def test_env_step_by_path():
    env = make_env()
    env.reset()
    first = env.legal_moves()[0]

    result = env.step(first)
    assert result.current_player == 2
    assert result.last_move is not None
    assert len(result.legal_paths) >= 0


def test_env_step_by_action_id():
    env = make_env()
    env.reset()

    action_space = env.action_space()
    result = env.step(action_space[0]["id"])
    assert result.last_move is not None


def test_env_invalid_action_id_raises():
    env = make_env()
    env.reset()
    with pytest.raises(ValueError):
        env.step(999999)
