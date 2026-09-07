"""A 模型边构建：从点集和方向列表生成前端渲染用边。"""

from __future__ import annotations

from typing import List, Sequence

from ..directions import Vector, add_vec, vector_type
from .base import Point


class EdgeBuilder:
    def __init__(self, geometry):
        self.geometry = geometry

    def build(self, directions: Sequence[Vector]) -> List[dict]:
        points = self.geometry.generate_points()
        seen = set()
        edges: List[dict] = []
        for p in points:
            for v in directions:
                q = add_vec(p, v)
                if not self.geometry.is_inside(q):
                    continue
                key = (p, q) if p < q else (q, p)
                if key in seen:
                    continue
                seen.add(key)
                edges.append(
                    {
                        "from": list(p),
                        "to": list(q),
                        "type": vector_type(v),
                    }
                )
        return edges
