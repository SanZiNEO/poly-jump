"""几何抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Sequence, Tuple

from ..directions import Vector

Point = Tuple[int, int, int]


class Geometry(ABC):
    """所有几何模型共用的接口。"""

    @abstractmethod
    def generate_points(self) -> List[Point]:
        """生成合法点集。"""

    @abstractmethod
    def generate_routes(self, directions: Sequence[Vector] | None = None) -> List[dict]:
        """生成用于前端渲染的路线列表。"""

    @abstractmethod
    def is_inside(self, pos: Point) -> bool:
        """判断点是否在棋盘内。"""

    @abstractmethod
    def player_assignments(
        self,
    ) -> Tuple[Dict[int, List[Point]], Dict[int, List[Point]]]:
        """返回 (player_bases, player_targets)。"""
