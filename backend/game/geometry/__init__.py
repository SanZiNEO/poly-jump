"""几何模型包：A 完整实现，B 接口/TODO。"""

from __future__ import annotations

from ..config import PolyJumpConfig
from .base import Geometry
from .model_a import GeometryA
from .model_b import GeometryB
from .model_c import GeometryC


def create_geometry(config: PolyJumpConfig) -> Geometry:
    if config.geometry == "A":
        return GeometryA(config)
    if config.geometry == "B":
        return GeometryB(config)
    if config.geometry == "C":
        return GeometryC(config)
    raise ValueError(f"未知 geometry: {config.geometry}")


__all__ = [
    "Geometry",
    "GeometryA",
    "GeometryB",
    "GeometryC",
    "create_geometry",
]
