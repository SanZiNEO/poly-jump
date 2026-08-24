"""B-ext：外接金字塔 + 12 向 + 同一子晶格。

使用偶子晶格，保证 12 向下全图连通。
每个面外部 5 个子（3×3 中的偶点 + 1 个尖点）。
"""

from __future__ import annotations

from ..config import PolyJumpConfig
from ..directions import DIRECTION_SETS
from .external_pyramid import ExternalPyramidGeometry


class GeometryBExt(ExternalPyramidGeometry):
    directions = DIRECTION_SETS[12]
    parity = 0

    def __init__(self, config: PolyJumpConfig):
        super().__init__(config)
