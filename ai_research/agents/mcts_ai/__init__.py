"""MCTS 搜索 AI（full action 模式）。

以“一条完整路径 action”为搜索动作，使用随机 rollout 作为默认策略，
适合作为 PolyJump 的第一个搜索 baseline。

注意：搜索通过 GameEnv.clone() 模拟未来局面，不修改真实对局。
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence

from backend.game.env import GameEnv

from ..base import Agent

DEFAULT_SIMULATIONS = 20
DEFAULT_MAX_DEPTH = 60
EXPLORATION = 1.414


class _Node:
    __slots__ = ("env", "player", "actions", "visited", "value", "children", "untried", "action")

    def __init__(self, env: GameEnv, action: Optional[list] = None):
        self.env = env
        self.player = env.observe().current_player
        self.actions: List[list] = [
            list(p) for p in env.observe().legal_paths
        ]
        self.visited = 0
        self.value = 0.0
        self.children: List["_Node"] = []
        self.untried: List[list] = list(self.actions)
        self.action = action

    def is_terminal(self) -> bool:
        return self.env.observe().done or not self.actions

    def select_child(self) -> "_Node":
        log_n = math.log(max(1, self.visited))
        return max(
            self.children,
            key=lambda c: (
                (c.value / max(1, c.visited))
                + EXPLORATION * math.sqrt(log_n / max(1, c.visited))
            ),
        )

    def expand(self) -> Optional["_Node"]:
        if not self.untried:
            return None
        action = self.untried.pop()
        child_env = self.env.clone()
        if not child_env.execute_action(action):
            return None
        child = _Node(child_env, action=action)
        self.children.append(child)
        return child


class MCTSAgent(Agent):
    slug = "mcts"
    display_name = "MCTS"

    def __init__(
        self,
        simulations: int = DEFAULT_SIMULATIONS,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ):
        self.simulations = simulations
        self.max_depth = max_depth

    def choose(self, env: GameEnv) -> Optional[list]:
        root = _Node(env.clone())
        if root.is_terminal():
            return None

        root_player = root.player

        for _ in range(self.simulations):
            node = root
            path = [node]

            # Selection
            while not node.is_terminal() and not node.untried and node.children:
                node = node.select_child()
                path.append(node)

            # Expansion
            if not node.is_terminal() and node.untried:
                expanded = node.expand()
                if expanded is not None:
                    node = expanded
                    path.append(node)

            # Simulation
            reward = self._rollout(node.env, root_player)

            # Backpropagation
            for n in path:
                n.visited += 1
                n.value += reward

        # 选择访问次数最多的子节点
        if not root.children:
            return random.choice(root.actions) if root.actions else None
        best = max(root.children, key=lambda c: c.visited)
        return best.action

    def _rollout(self, env: GameEnv, root_player: int) -> float:
        sim = env.clone()
        for _ in range(self.max_depth):
            obs = sim.observe()
            if obs.done:
                break
            legal = obs.legal_paths
            if not legal:
                break
            sim.execute_action(random.choice(legal))

        obs = sim.observe()
        if obs.winner is None:
            return 0.5
        return 1.0 if obs.winner == root_player else 0.0


__all__ = ["MCTSAgent"]
