"""欧氏距离贪心 AI：用三维空间直线距离衡量与目标区的距离。"""

from __future__ import annotations

from ..base import HeuristicAgent, Point, euclidean


class EuclideanAgent(HeuristicAgent):
    slug = "euclidean"
    display_name = "欧氏距离"

    def heuristic_distance(self, a: Point, b: Point) -> float:
        return euclidean(a, b)
