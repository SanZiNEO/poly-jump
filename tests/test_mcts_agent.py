"""MCTS baseline agent 基础测试。"""

from __future__ import annotations

from backend.game.config import PolyJumpConfig
from backend.game.env import GameEnv
from ai_research.agents.mcts_ai import MCTSAgent


def test_mcts_agent_returns_legal_action():
    cfg = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
    )
    env = GameEnv(cfg)
    env.reset()
    legal = [[list(q) for q in p] for p in env.legal_actions()]

    agent = MCTSAgent(simulations=5, max_depth=20)
    chosen = agent.choose(env)

    assert chosen is not None
    assert chosen in legal
