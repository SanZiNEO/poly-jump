"""AI 研究代理基类与公共工具。

设计目标：AI 只通过 GameEnv 公开接口获取信息，不直接操作 Board，
从而验证 PolyJump 平台是否足以作为外部 AI 的研究环境。
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from backend.game.env import GameEnv

Point = Tuple[int, int, int]


def tuple_point(p: Sequence[int]) -> Point:
    return (int(p[0]), int(p[1]), int(p[2]))


def get_targets(state: dict) -> Dict[int, Set[Point]]:
    """从 state_dict 中解析各玩家目标区。"""
    result: Dict[int, Set[Point]] = {}
    for player, points in state.get("targets", {}).items():
        result[int(player)] = {tuple_point(p) for p in points}
    return result


def build_adjacency(state: dict) -> Dict[Point, Set[Point]]:
    """用 state_dict 中的 routes 构建无向图邻接表。"""
    adj: Dict[Point, Set[Point]] = {}
    for route in state.get("routes", []):
        a = tuple_point(route["from"])
        b = tuple_point(route["to"])
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    # 保证所有合法点都在映射里（孤立点至少给自己一个空集合）
    for p in state.get("points", []):
        adj.setdefault(tuple_point(p), set())
    return adj


def bfs_distances(
    adj: Dict[Point, Set[Point]], targets: Iterable[Point]
) -> Dict[Point, int]:
    """从目标区出发的 BFS 距离。目标内距离为 0。"""
    dist: Dict[Point, int] = {}
    q: deque = deque()
    for t in targets:
        if t in adj and t not in dist:
            dist[t] = 0
            q.append(t)
    while q:
        p = q.popleft()
        d = dist[p]
        for n in adj.get(p, set()):
            if n not in dist:
                dist[n] = d + 1
                q.append(n)
    return dist


def manhattan(a: Point, b: Point) -> int:
    return sum(abs(x - y) for x, y in zip(a, b))


def euclidean(a: Point, b: Point) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def chebyshev(a: Point, b: Point) -> int:
    return max(abs(x - y) for x, y in zip(a, b))


class Agent:
    """所有研究用 AI 的接口。

    子类只需实现 choose(env)，返回一条合法 path（list of list）。
    """

    slug = "base"
    display_name = "Base Agent"

    def choose(self, env: GameEnv) -> Optional[list]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(slug={self.slug!r})"


class DistanceAgent(Agent):
    """按某种度量距离目标区的“贪心前进” AI。

    评分：before_distance - after_distance，越大越接近目标区。
    同分时优先短路径。
    """

    def distance(self, a: Point, b: Point) -> float:
        raise NotImplementedError

    def choose(self, env: GameEnv) -> Optional[list]:
        obs = env.observe()
        legal = obs.legal_paths
        if not legal:
            return None

        state = env.state_dict()
        targets = get_targets(state).get(obs.current_player, set())
        if not targets:
            # 没有目标区时退化为随机/第一合法步
            return legal[0]

        def gain(path: Sequence[Sequence[int]]) -> float:
            start = tuple_point(path[0])
            end = tuple_point(path[-1])
            before = min(self.distance(start, t) for t in targets)
            after = min(self.distance(end, t) for t in targets)
            return float(before - after)

        return max(legal, key=lambda p: (gain(p), -len(p)))
