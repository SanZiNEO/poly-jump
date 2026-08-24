"""A-ext：外接金字塔 + 方向可配置（类似 A 模型）。

全整数点（包含奇偶），玩家数 2/3/4/6。
"""

from __future__ import annotations

from ..config import PolyJumpConfig
from ..directions import resolve_direction_set
from .external_pyramid import ExternalPyramidGeometry


class GeometryAExt(ExternalPyramidGeometry):
    parity = None

    def __init__(self, config: PolyJumpConfig):
        super().__init__(config)
        self.directions = resolve_direction_set(
            config.direction_set, config.custom_vectors
        )
