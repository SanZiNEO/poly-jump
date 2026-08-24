"""A 模型：XYZ 正交网格（docs/03）。

- 原点在角上
- 全部整数格点合法
- 支持 6/8/12/14/18/20/26 向和自定义向量
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from ..config import PolyJumpConfig
from ..directions import Vector, resolve_direction_set
from .base import Geometry, Point
from .route_builder import RouteBuilder


class GeometryA(Geometry):
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.size = tuple(int(v) for v in config.board_size)

    @property
    def a(self) -> int:
        return self.size[0]

    @property
    def b(self) -> int:
        return self.size[1]

    @property
    def c(self) -> int:
        return self.size[2]

    def generate_points(self) -> List[Point]:
        points: List[Point] = []
        for z in range(self.c):
            for y in range(self.b):
                for x in range(self.a):
                    points.append((x, y, z))
        return points

    def is_inside(self, pos: Point) -> bool:
        x, y, z = pos
        return 0 <= x < self.a and 0 <= y < self.b and 0 <= z < self.c

    def generate_routes(
        self, directions: Sequence[Vector] | None = None
    ) -> List[dict]:
        if directions is None:
            directions = resolve_direction_set(
                self.config.direction_set, self.config.custom_vectors
            )
        return RouteBuilder(self).build(directions)

    def player_assignments(
        self,
    ) -> Tuple[Dict[int, List[Point]], Dict[int, List[Point]]]:
        # TODO: 第一版只支持 2 人对角局；3/4/6/8 人需按 docs/05 显式基地/目标区分配。
        if self.config.players != 2:
            raise NotImplementedError(
                "第一版仅支持 2 人局（A 模型对角金字塔）。"
                "3/4/6/8 人局留待后续实现。"
            )

        layers = self.config.initial_layout.layers
        if layers <= 0:
            raise ValueError("initial_layout.layers 必须为正整数")

        # 用户规则：A 模型层数上限 = max(2, floor(最短边 / 2))
        min_side = min(self.a, self.b, self.c)
        max_layers = max(2, min_side // 2)
        if layers > max_layers:
            raise ValueError(
                f"A 模型棋子层数上限为 {max_layers} 层（最短边 {min_side}），"
                f"当前配置 {layers} 层"
            )

        home1 = self._pyramid((0, 0, 0), layers, (1, 1, 1))
        home2 = self._pyramid((self.a - 1, self.b - 1, self.c - 1), layers, (-1, -1, -1))
        if not home1 or not home2:
            raise ValueError("金字塔布局生成失败：棋盘可能太小或层数过大")

        return {1: home1, 2: home2}, {1: home2, 2: home1}

    def _pyramid(
        self,
        corner: Point,
        layers: int,
        signs: Vector,
    ) -> List[Point]:
        """生成三角金字塔基地坐标。

        层 k = 所有满足 dx+dy+dz == k 的点，即从角点沿三条轴同时向外扩展。
        这样金字塔尖正好落在正方体角上，层数依次为 1,3,6,10...
        """
        sx, sy, sz = signs
        cells: List[Point] = []
        for layer in range(layers):
            for dx in range(layer + 1):
                for dy in range(layer + 1 - dx):
                    dz = layer - dx - dy
                    p = (corner[0] + sx * dx, corner[1] + sy * dy, corner[2] + sz * dz)
                    if self.is_inside(p):
                        cells.append(p)
        return cells
