"""几何模型包：A 完整实现，B 接口/TODO。"""

from __future__ import annotations

from ..config import PolyJumpConfig
from .base import Geometry
from .model_a import GeometryA
from .model_a_ext import GeometryAExt
from .model_b import GeometryB
from .model_b_ext import GeometryBExt
from .model_c import GeometryC
from .model_c_ext import GeometryCExt
from .model_d import GeometryD


def create_geometry(config: PolyJumpConfig) -> Geometry:
    geometry = config.geometry
    if geometry == "A":
        return GeometryA(config)
    if geometry == "A_EXT":
        return GeometryAExt(config)
    if geometry == "B":
        return GeometryB(config)
    if geometry == "B_EXT":
        return GeometryBExt(config)
    if geometry == "C":
        return GeometryC(config)
    if geometry == "C_EXT":
        return GeometryCExt(config)
    if geometry == "D":
        return GeometryD(config)
    raise ValueError(f"未知 geometry: {config.geometry}")


__all__ = [
    "Geometry",
    "GeometryA",
    "GeometryAExt",
    "GeometryB",
    "GeometryBExt",
    "GeometryC",
    "GeometryCExt",
    "GeometryD",
    "create_geometry",
]
