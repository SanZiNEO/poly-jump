"""D 模型：外接金字塔 + 14 向（6 + 8）全整数点。

每个面外部 10 个子（3×3 + 1×1）。
"""

from __future__ import annotations

from ..config import PolyJumpConfig
from ..directions import DIRECTION_SETS
from .external_pyramid import ExternalPyramidGeometry


class GeometryD(ExternalPyramidGeometry):
    directions = DIRECTION_SETS[14]
    parity = None

    def __init__(self, config: PolyJumpConfig):
        super().__init__(config)
