"""路径度量（action / step）测试。"""

from __future__ import annotations

import math

import pytest

from backend.game.config import PolyJumpConfig
from backend.game.env import GameEnv
from backend.game.game_state import GameState
from backend.game.path_metrics import path_metrics, summarize_actions
from backend.game.serializers import state_to_dict


def test_path_metrics_single_step():
    path = [(0, 0, 0), (1, 0, 0)]
    metrics = path_metrics(path)

    assert metrics["step_count"] == 1
    assert metrics["straight_distance"] == pytest.approx(1.0)
    assert metrics["path_distance"] == pytest.approx(1.0)
    assert metrics["step_distances"] == [pytest.approx(1.0)]


def test_path_metrics_chain():
    path = [(0, 0, 0), (2, 0, 0), (0, 2, 0)]
    metrics = path_metrics(path)

    assert metrics["step_count"] == 2
    assert metrics["straight_distance"] == pytest.approx(2.0)
    assert metrics["path_distance"] == pytest.approx(2.0 + math.sqrt(8))
    assert len(metrics["step_distances"]) == 2


def test_action_space_includes_path_metrics():
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    env = GameEnv(cfg)
    env.reset()
    actions = env.observe().legal_actions

    assert len(actions) > 0
    for action in actions:
        assert "step_count" in action
        assert "straight_distance" in action
        assert "path_distance" in action
        assert "step_distances" in action
        assert action["step_count"] == len(action["path"]) - 1


def test_move_history_includes_path_metrics():
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    state = GameState(cfg)
    moves = state.legal_moves()

    assert state.perform_move(moves[0])
    entry = state.move_history[0]
    assert entry["step_count"] == len(entry["path"]) - 1
    assert "straight_distance" in entry
    assert "path_distance" in entry
    assert len(entry["step_distances"]) == entry["step_count"]


def test_state_dict_path_stats_and_action_count():
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    state = GameState(cfg)
    moves = state.legal_moves()
    state.perform_move(moves[0])

    data = state_to_dict(state)
    assert data["action_count"] == 1
    stats = data["path_stats"]
    assert stats["action_count"] == 1
    assert stats["total_steps"] >= 1
    assert stats["players"]["1"]["action_count"] == 1


def test_step_result_exposes_path_summary():
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    env = GameEnv(cfg)
    env.reset()
    result = env.step(env.legal_moves()[0])

    assert result.action_count == 1
    assert result.total_steps >= 1
    assert result.total_straight_distance >= 0
    assert result.total_path_distance >= 0


def test_summarize_actions_aggregates():
    actions = [
        {
            "player": 1,
            "step_count": 2,
            "straight_distance": 1.0,
            "path_distance": 3.0,
        },
        {
            "player": 2,
            "step_count": 3,
            "straight_distance": 2.0,
            "path_distance": 4.0,
        },
        {
            "player": 1,
            "step_count": 1,
            "straight_distance": 0.5,
            "path_distance": 0.5,
        },
    ]
    summary = summarize_actions(actions)

    assert summary["action_count"] == 3
    assert summary["total_steps"] == 6
    assert summary["total_straight_distance"] == pytest.approx(3.5)
    assert summary["total_path_distance"] == pytest.approx(7.5)
    assert summary["players"]["1"]["action_count"] == 2
    assert summary["players"]["1"]["step_count"] == 3
    assert summary["players"]["2"]["action_count"] == 1
    assert summary["players"]["2"]["step_count"] == 3
