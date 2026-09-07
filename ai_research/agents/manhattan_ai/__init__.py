"""曼哈顿距离贪心 AI：用 |dx|+|dy|+|dz| 衡量与目标区的距离。"""

from __future__ import annotations

from ..base import HeuristicAgent, Point, manhattan


class ManhattanAgent(HeuristicAgent):
    slug = "manhattan"
    display_name = "曼哈顿距离"

    def heuristic_distance(self, a: Point, b: Point) -> float:
        return float(manhattan(a, b))
