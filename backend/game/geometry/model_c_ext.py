"""C-ext：外接金字塔 + 20 向 + 全整数点。

可以跨奇偶子晶格。
每个面外部 10 个子（3×3 + 1×1）。
"""

from __future__ import annotations

from ..config import PolyJumpConfig
from ..directions import DIRECTION_SETS
from .external_pyramid import ExternalPyramidGeometry


class GeometryCExt(ExternalPyramidGeometry):
    directions = DIRECTION_SETS[20]
    parity = None

    def __init__(self, config: PolyJumpConfig):
        super().__init__(config)
