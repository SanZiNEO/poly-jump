"""欧氏距离贪心 AI：用三维空间直线距离衡量与目标区的距离。"""

from __future__ import annotations

from ..base import DistanceAgent, Point, euclidean


class EuclideanAgent(DistanceAgent):
    slug = "euclidean"
    display_name = "欧氏距离"

    def distance(self, a: Point, b: Point) -> float:
        return euclidean(a, b)
