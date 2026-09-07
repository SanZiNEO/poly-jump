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
