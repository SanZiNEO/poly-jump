"""GameEnv 干净接口测试。"""

from __future__ import annotations

import pytest

from backend.game.config import PolyJumpConfig
from backend.game.env import GameEnv


def make_env() -> GameEnv:
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    return GameEnv(cfg)


def test_env_reset_and_legal_actions():
    env = make_env()
    result = env.reset()

    assert result.winner is None
    assert result.done is False
    assert len(result.legal_paths) > 0
    assert len(result.legal_actions) == len(result.legal_paths)


def test_env_execute_action_by_path():
    env = make_env()
    env.reset()
    first = env.legal_actions()[0]

    result = env.execute_action(first)
    assert result.current_player == 2
    assert result.last_action is not None
    assert len(result.legal_paths) >= 0


def test_env_execute_action_by_action_id():
    env = make_env()
    env.reset()

    action_space = env.action_space()
    result = env.execute_action(action_space[0]["id"])
    assert result.last_action is not None


def test_env_invalid_action_id_raises():
    env = make_env()
    env.reset()
    with pytest.raises(ValueError):
        env.execute_action(999999)


def test_env_clone_is_independent():
    env = make_env()
    env.reset()

    clone = env.clone()
    assert clone.state.action_count == env.state.action_count

    clone.execute_action(clone.legal_actions()[0])
    assert clone.state.action_count == env.state.action_count + 1
    assert env.state.action_count == 0
