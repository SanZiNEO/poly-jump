"""B 模型：FCC / 菱形十二面体点阵。

第一版只保留接口。TODO：按 docs/04 实现：
- 奇数边长、几何中心坐标
- FCC 子晶格合法点集
- 12 向路线
- 外部四棱锥基地/目标区
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from ..config import PolyJumpConfig
from ..directions import Vector
from .base import Geometry, Point


class GeometryB(Geometry):
    def __init__(self, config: PolyJumpConfig):
        self.config = config

    def generate_points(self) -> List[Point]:
        raise NotImplementedError("B 模型第一版未实现，仅保留接口")

    def is_inside(self, pos: Point) -> bool:
        raise NotImplementedError("B 模型第一版未实现，仅保留接口")

    def generate_routes(
        self, directions: Sequence[Vector] | None = None
    ) -> List[dict]:
        raise NotImplementedError("B 模型第一版未实现，仅保留接口")

    def player_assignments(
        self,
    ) -> Tuple[Dict[int, List[Point]], Dict[int, List[Point]]]:
        raise NotImplementedError("B 模型第一版未实现，仅保留接口")
