"""PolyJump PettingZoo AEC 包装测试。"""

from __future__ import annotations

import random

import pytest

pytest.importorskip("pettingzoo")

from backend.game.config import PolyJumpConfig  # noqa: E402
from ai_research.pettingzoo_env import PolyJumpAECEnv, MAX_ACTIONS  # noqa: E402


def make_config() -> PolyJumpConfig:
    return PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
    )


def test_full_action_mode_legal_and_step():
    env = PolyJumpAECEnv(make_config(), action_mode="full_action")
    env.reset()

    agent = env.agent_selection
    legal = env.legal_actions(agent)
    assert len(legal) > 0

    obs = env.observe(agent)
    assert obs is not None
    assert len(obs) > 0

    env.step(0)
    assert env.terminations[agent] is False or env.terminations[agent] is True


def test_primitive_mode_returns_single_step_actions():
    env = PolyJumpAECEnv(make_config(), action_mode="primitive")
    env.reset()

    agent = env.agent_selection
    legal = env.legal_actions(agent)
    assert len(legal) > 0

    for action in legal:
        assert len(action) == 2


@pytest.mark.parametrize("mode", ["full_action", "primitive"])
def test_aec_agent_iter_last_and_action_mask(mode):
    env = PolyJumpAECEnv(make_config(), action_mode=mode)
    env.reset()

    steps = 0
    for agent in env.agent_iter():
        obs, reward, termination, truncation, info = env.last()
        assert obs is not None

        if termination or truncation:
            env.step(None)
            continue

        legal = env.legal_actions(agent)
        if not legal:
            env.step(None)
            continue

        mask = info.get("action_mask")
        assert mask is not None
        assert len(mask) == MAX_ACTIONS
        assert sum(mask) == len(legal)

        env.step(random.randrange(len(legal)))
        steps += 1
        if steps >= 10:
            break


def test_observation_includes_agent_target_mask():
    """观测必须包含「本 agent 的目标区掩码」，否则策略不知道该往哪走。"""
    env = PolyJumpAECEnv(make_config(), action_mode="full_action")
    env.reset()
    state = env.env.state_dict()
    n = len(state["points"])

    for agent in env.possible_agents:
        obs = env.observe(agent)
        assert obs.shape == env.observation_space(agent).shape

        player = int(agent.split("_")[1])
        target = {tuple(int(v) for v in p) for p in state["targets"][str(player)]}
        mask = obs[4 * n:5 * n].tolist()
        expected = [1.0 if tuple(p) in target else 0.0 for p in state["points"]]
        assert mask == expected
        assert int(sum(mask)) == len(target)


def test_target_mask_is_agent_relative():
    """掩码按 agent 视角生成：两人局的目标区互不相交。"""
    env = PolyJumpAECEnv(make_config(), action_mode="full_action")
    env.reset()
    n = len(env.env.state_dict()["points"])

    mask1 = env.observe("player_1")[4 * n:5 * n].tolist()
    mask2 = env.observe("player_2")[4 * n:5 * n].tolist()

    assert mask1 != mask2
    inside1 = {i for i, v in enumerate(mask1) if v}
    inside2 = {i for i, v in enumerate(mask2) if v}
    assert inside1 and inside2
    assert not (inside1 & inside2)
