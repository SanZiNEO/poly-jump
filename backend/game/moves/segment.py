"""路径段的几何判定辅助。"""

from __future__ import annotations

from typing import Sequence, Tuple

from ..directions import Vector, sub_vec

Point = Tuple[int, int, int]


def is_jump_segment(
    src: Point,
    dst: Point,
    directions: Sequence[Vector],
) -> bool:
    """判断 [src, dst] 是否为一个跳跃段：dst-src == 2 * v。"""
    diff = sub_vec(dst, src)
    if any(d % 2 != 0 for d in diff):
        return False
    half = (diff[0] // 2, diff[1] // 2, diff[2] // 2)
    return half in directions


def jump_mid(src: Point, dst: Point) -> Point:
    """返回跳跃段中被跳位置的坐标。"""
    return (
        (src[0] + dst[0]) // 2,
        (src[1] + dst[1]) // 2,
        (src[2] + dst[2]) // 2,
    )
