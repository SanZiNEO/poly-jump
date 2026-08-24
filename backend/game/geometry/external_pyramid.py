"""外接金字塔坐标体系（可配置奇数中心边长）。

中心正方体边长 = ep_side（奇数）。
每个面外部金字塔由奇数层组成：
    ep_side=5：3×3 + 1×1 = 10 子/面
    ep_side=7：5×5 + 3×3 + 1×1 = 35 子/面
    ep_side=9：7×7 + 5×5 + 3×3 + 1×1 = 84 子/面
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..config import PolyJumpConfig
from ..directions import Vector, add_vec
from .base import Geometry, Point

TIPS: List[Tuple[int, int]] = [
    (0, 1), (0, -1),
    (1, 1), (1, -1),
    (2, 1), (2, -1),
]

PLAYER_TIPS: dict[int, List[int]] = {
    2: [0, 1],
    3: [0, 2, 4],
    4: [0, 1, 2, 3],
    6: [0, 1, 2, 3, 4, 5],
}


def generate_external_points(
    k: int,
    parity: Optional[int] = None,
) -> List[Point]:
    """生成外接金字塔完整点集。

    k = (ep_side - 1) / 2。
    parity=None 保留全部整数点；parity=0/1 只保留对应子晶格。
    """
    pts: List[Point] = []

    for x in range(-k, k + 1):
        for y in range(-k, k + 1):
            for z in range(-k, k + 1):
                p = (x, y, z)
                if parity is None or sum(p) % 2 == parity:
                    pts.append(p)

    for axis in range(3):
        for sign in (1, -1):
            pts.extend(face_pyramid_points(axis, sign, parity, k))

    return pts


def face_pyramid_points(
    axis: int,
    sign: int,
    parity: Optional[int],
    k: int,
) -> List[Point]:
    """生成一个面上的外接金字塔。

    层大小为 ep_side-2, ep_side-4, ..., 1。
    """
    other = [i for i in range(3) if i != axis]
    pts: List[Point] = []

    for layer in range(1, k + 1):
        side = 2 * k + 1 - 2 * layer  # 奇数：3,5,7... 反向到1
        half = side // 2
        main = sign * (k + layer)

        for a in range(-half, half + 1):
            for b in range(-half, half + 1):
                p = [0, 0, 0]
                p[axis] = main
                p[other[0]] = a
                p[other[1]] = b
                point = tuple(p)
                if parity is None or sum(point) % 2 == parity:
                    pts.append(point)

    return pts


class ExternalPyramidGeometry(Geometry):
    """外接金字塔几何基类。

    子类设置：
    - directions：移动方向列表
    - parity：None（全点）或 0/1（偶/奇子晶格）
    """

    directions: List[Vector] = []
    parity: Optional[int] = None

    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.ep_side = int(config.ep_side)
        if self.ep_side % 2 == 0 or self.ep_side < 3:
            raise ValueError("外接金字塔中心边长必须为奇数且 >= 3")
        self.k = (self.ep_side - 1) // 2

    def generate_points(self) -> List[Point]:
        return generate_external_points(self.k, self.parity)

    def is_inside(self, pos: Point) -> bool:
        return tuple(pos) in set(self.generate_points())

    def generate_routes(
        self, directions: Optional[List[Vector]] = None
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
                routes.append({"from": list(p), "to": list(q), "type": _type(v)})
        return routes

    def player_assignments(
        self,
    ) -> Tuple[dict[int, List[Point]], dict[int, List[Point]]]:
        players = self.config.players
        if players not in PLAYER_TIPS:
            raise NotImplementedError(
                f"外接金字塔模型支持 2 / 3 / 4 / 6 人，当前 {players} 人"
            )

        bases: dict[int, List[Point]] = {}
        targets: dict[int, List[Point]] = {}
        for player_idx, tip_index in enumerate(PLAYER_TIPS[players], start=1):
            axis, sign = TIPS[tip_index]
            bases[player_idx] = face_pyramid_points(axis, sign, self.parity, self.k)
            opposite_index = tip_index ^ 1
            o_axis, o_sign = TIPS[opposite_index]
            targets[player_idx] = face_pyramid_points(o_axis, o_sign, self.parity, self.k)

        return bases, targets


def _type(v: Vector) -> str:
    nz = sum(1 for c in v if c != 0)
    if nz == 1:
        return "axis6"
    if nz == 2:
        return "face12"
    if nz == 3:
        return "body8"
    return "custom"
