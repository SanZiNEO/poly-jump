"""B 模型：纯 12 向 FCC / L1 球偶子晶格。

文档依据 docs/04-geometry-model-b.md。

点集定义：
    |x| + |y| + |z| <= R
    (x + y + z) % 2 == 0

初始布局：
    玩家从 6 个尖端之一开始
    每个玩家基地 = 从尖端向内 R/2 层
    每层点数为平方数：1, 4, 9, 16, ...
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from ..config import PolyJumpConfig
from ..directions import FACE12, Vector, add_vec
from .base import Geometry, Point

# (axis, sign) 对应六个尖端
TIPS: List[Tuple[int, int]] = [
    (0, 1),   # +x
    (0, -1),  # -x
    (1, 1),   # +y
    (1, -1),  # -y
    (2, 1),   # +z
    (2, -1),  # -z
]

# 各人数使用的尖端索引
PLAYER_TIPS: Dict[int, List[int]] = {
    2: [0, 1],
    3: [0, 2, 4],
    4: [0, 1, 2, 3],
    6: [0, 1, 2, 3, 4, 5],
}


class GeometryB(Geometry):
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.R = int(config.b_radius)

    def generate_points(self) -> List[Point]:
        pts: List[Point] = []
        R = self.R
        for x in range(-R, R + 1):
            for y in range(-R, R + 1):
                for z in range(-R, R + 1):
                    if abs(x) + abs(y) + abs(z) <= R and (x + y + z) % 2 == 0:
                        pts.append((x, y, z))
        return pts

    def is_inside(self, pos: Point) -> bool:
        x, y, z = pos
        return (
            abs(x) + abs(y) + abs(z) <= self.R
            and (x + y + z) % 2 == 0
        )

    def generate_routes(
        self, directions: Sequence[Vector] | None = None
    ) -> List[dict]:
        if directions is None:
            directions = FACE12

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
                routes.append(
                    {
                        "from": list(p),
                        "to": list(q),
                        "type": "face12",
                    }
                )
        return routes

    def player_assignments(
        self,
    ) -> Tuple[Dict[int, List[Point]], Dict[int, List[Point]]]:
        players = self.config.players
        if players not in PLAYER_TIPS:
            raise NotImplementedError(
                f"B 模型第一版支持 2 / 3 / 4 / 6 人，当前 {players} 人"
            )

        tip_indices = PLAYER_TIPS[players]
        bases: Dict[int, List[Point]] = {}
        targets: Dict[int, List[Point]] = {}

        for player_idx, tip_index in enumerate(tip_indices, start=1):
            axis, sign = TIPS[tip_index]
            bases[player_idx] = self._tip_base(axis, sign)

            opposite_index = tip_index ^ 1  # 0<->1, 2<->3, 4<->5
            opposite_axis, opposite_sign = TIPS[opposite_index]
            targets[player_idx] = self._tip_base(opposite_axis, opposite_sign)

        return bases, targets

    def _tip_base(self, axis: int, sign: int) -> List[Point]:
        """生成一个尖端基地：从尖端向内 R/2 层。

        第 s 层（s 从 0 开始）：
            主坐标 = sign * (R - s)
            其他两坐标满足 |a| + |b| <= s
            并且总坐标和为偶数。
        """
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
                    p = tuple(coords)
                    if sum(p) % 2 == 0:
                        pts.append(p)
        return pts
