"""图距离贪心 AI：沿棋盘真实连边做 BFS，得到到目标区的最小步数。"""

from __future__ import annotations

import random
from typing import Optional, Sequence

from backend.game.env import GameEnv

from ..base import (
    Agent,
    bfs_distances,
    build_adjacency,
    get_targets,
    tuple_point,
)


class GraphBFSAgent(Agent):
    slug = "graph_bfs"
    display_name = "图距离 BFS"

    def choose(self, env: GameEnv) -> Optional[list]:
        obs = env.observe()
        legal = obs.legal_paths
        if not legal:
            return None

        state = env.state_dict()
        targets = get_targets(state).get(obs.current_player, set())
        if not targets:
            return legal[0]

        adj = build_adjacency(state)
        dist = bfs_distances(adj, targets)

        def gain(path: Sequence[Sequence[int]]) -> float:
            start = tuple_point(path[0])
            end = tuple_point(path[-1])
            before = dist.get(start)
            after = dist.get(end)
            if before is None or after is None:
                return 0.0
            return float(before - after)

        best_score = max((gain(p), -len(p)) for p in legal)
        tied = [p for p in legal if (gain(p), -len(p)) == best_score]
        return random.choice(tied)
