"""游戏内 AI：启发式选择接近目标区的走法。

不读取计分配置，只以“把棋子送进目标区”为唯一目标。
由基准评测筛选出的三种启发式 AI：
- EuclideanHeuristicAI：欧氏距离启发式
- ChebyshevHeuristicAI：切比雪夫距离启发式
- GraphHeuristicAI：真实图距离 BFS 启发式
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, List, Optional, Sequence

from .board import Board
from .directions import resolve_direction_set


class _HeuristicAI:
    """按启发式度量选择让棋子更接近目标区的走法。"""

    def _heuristic_distance(self, a: Sequence[int], b: Sequence[int]) -> float:
        raise NotImplementedError

    def select_action(
        self,
        board: Board,
        player: int,
        legal_paths: List[Sequence[Sequence[int]]],
    ) -> Optional[list]:
        if not legal_paths:
            return None

        target = board.player_targets.get(player, set())
        if not target:
            return legal_paths[0]

        def score(path: Sequence[Sequence[int]]) -> float:
            start = path[0]
            end = path[-1]
            before = min(self._heuristic_distance(start, t) for t in target)
            after = min(self._heuristic_distance(end, t) for t in target)
            return float(before - after)

        # 同分优先短路径；仍同分取 max 第一个（确定性）
        return max(legal_paths, key=lambda p: (score(p), -len(p)))


class EuclideanHeuristicAI(_HeuristicAI):
    """欧氏距离启发式 AI。"""

    def _heuristic_distance(self, a: Sequence[int], b: Sequence[int]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class ChebyshevHeuristicAI(_HeuristicAI):
    """切比雪夫距离启发式 AI。"""

    def _heuristic_distance(self, a: Sequence[int], b: Sequence[int]) -> float:
        return float(max(abs(x - y) for x, y in zip(a, b)))


class GraphHeuristicAI:
    """真实图距离 BFS 启发式 AI：只沿棋盘实际连边计算到目标区的最少边数。"""

    def select_action(
        self,
        board: Board,
        player: int,
        legal_paths: List[Sequence[Sequence[int]]],
    ) -> Optional[list]:
        if not legal_paths:
            return None

        target = board.player_targets.get(player, set())
        if not target:
            return legal_paths[0]

        directions = resolve_direction_set(
            board.config.direction_set, board.config.custom_vectors
        )
        dist = self._graph_distance_map(board, target, directions)

        def score(path: Sequence[Sequence[int]]) -> float:
            start = path[0]
            end = path[-1]
            before = dist.get(tuple(start))
            after = dist.get(tuple(end))
            if before is None or after is None:
                return 0.0
            return float(before - after)

        return max(legal_paths, key=lambda p: (score(p), -len(p)))

    @staticmethod
    def _graph_distance_map(
        board: Board,
        targets: set,
        directions,
    ) -> Dict[tuple, int]:
        points = set(board.points)
        dist: Dict[tuple, int] = {}
        q: deque = deque()

        for t in targets:
            key = tuple(t)
            if key in points:
                dist[key] = 0
                q.append(key)

        while q:
            p = q.popleft()
            d = dist[p]
            for v in directions:
                n = (p[0] + v[0], p[1] + v[1], p[2] + v[2])
                if n in points and n not in dist:
                    dist[n] = d + 1
                    q.append(n)

        return dist


__all__ = [
    "EuclideanHeuristicAI",
    "ChebyshevHeuristicAI",
    "GraphHeuristicAI",
]
