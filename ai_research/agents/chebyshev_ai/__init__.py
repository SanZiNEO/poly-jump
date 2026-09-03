"""切比雪夫距离贪心 AI：用 max(|dx|,|dy|,|dz|) 衡量与目标区的距离。"""

from __future__ import annotations

from ..base import DistanceAgent, Point, chebyshev


class ChebyshevAgent(DistanceAgent):
    slug = "chebyshev"
    display_name = "切比雪夫距离"

    def distance(self, a: Point, b: Point) -> float:
        return float(chebyshev(a, b))
