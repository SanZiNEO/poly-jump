"""C 模型：L1 球全整数点 + 20 向移动。

文档依据：
- L1 球 R=c_radius
- 所有整数点：(x,y,z) ∈ Z³，|x|+|y|+|z| <= R
- 固定 20 向：12 向（面对角）+ 8 向（体对角）
- 最多支持 6 人
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from ..config import PolyJumpConfig
from ..directions import DIRECTION_SETS, Vector, add_vec
from .base import Geometry, Point

TIPS: List[Tuple[int, int]] = [
    (0, 1), (0, -1),
    (1, 1), (1, -1),
    (2, 1), (2, -1),
]

PLAYER_TIPS: Dict[int, List[int]] = {
    2: [0, 1],
    3: [0, 2, 4],
    4: [0, 1, 2, 3],
    6: [0, 1, 2, 3, 4, 5],
}


class GeometryC(Geometry):
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.R = int(config.c_radius)
        self.directions = DIRECTION_SETS[20]

    def generate_points(self) -> List[Point]:
        pts: List[Point] = []
        R = self.R
        for x in range(-R, R + 1):
            for y in range(-R, R + 1):
                for z in range(-R, R + 1):
                    if abs(x) + abs(y) + abs(z) <= R:
                        pts.append((x, y, z))
        return pts

    def is_inside(self, pos: Point) -> bool:
        x, y, z = pos
        return abs(x) + abs(y) + abs(z) <= self.R

    def generate_routes(
        self, directions: Sequence[Vector] | None = None
    ) -> List[dict]:
        if directions is None:
            directions = self.directions

        points = set(self.generate_points())
        seen = set()
        routes: List[dict] = []
        for p in points:
            for v in directions:
                q = add_vec(p, v)
                if q not in points:
                    continue
                key = (p, q) if p < q else (q, p)
                if key in seen:
                    continue
                seen.add(key)
                nz = sum(1 for c in v if c != 0)
                routes.append(
                    {
                        "from": list(p),
                        "to": list(q),
                        "type": "body8" if nz == 3 else "face12",
                    }
                )
        return routes

    def player_assignments(
        self,
    ) -> Tuple[Dict[int, List[Point]], Dict[int, List[Point]]]:
        players = self.config.players
        if players not in PLAYER_TIPS:
            raise NotImplementedError(
                f"C 模型支持 2 / 3 / 4 / 6 人，当前 {players} 人"
            )

        tip_indices = PLAYER_TIPS[players]
        bases: Dict[int, List[Point]] = {}
        targets: Dict[int, List[Point]] = {}

        for player_idx, tip_index in enumerate(tip_indices, start=1):
            axis, sign = TIPS[tip_index]
            bases[player_idx] = self._tip_base(axis, sign)

            opposite_index = tip_index ^ 1
            opposite_axis, opposite_sign = TIPS[opposite_index]
            targets[player_idx] = self._tip_base(opposite_axis, opposite_sign)

        return bases, targets

    def _tip_base(self, axis: int, sign: int) -> List[Point]:
        R = self.R
        layers = R // 2
        other_axes = [i for i in range(3) if i != axis]
        pts: List[Point] = []

        for s in range(layers):
            main = sign * (R - s)
            for a in range(-s, s + 1):
                for b in range(-s, s + 1):
                    if abs(a) + abs(b) > s:
                        continue
                    coords = [0, 0, 0]
                    coords[axis] = main
                    coords[other_axes[0]] = a
                    coords[other_axes[1]] = b
                    pts.append(tuple(coords))
        return pts
