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
    """判断 [src, dst] 是否为一个标准跳跃段：dst-src == 2 * v。"""
    diff = sub_vec(dst, src)
    if any(d % 2 != 0 for d in diff):
        return False
    half = (diff[0] // 2, diff[1] // 2, diff[2] // 2)
    return half in directions


def jump_mid(src: Point, dst: Point) -> Point:
    """返回标准跳跃段中被跳位置的坐标。"""
    return (
        (src[0] + dst[0]) // 2,
        (src[1] + dst[1]) // 2,
        (src[2] + dst[2]) // 2,
    )


def is_two_step_segment(
    src: Point,
    dst: Point,
    directions: Sequence[Vector],
) -> bool:
    """判断 [src, dst] 是否为一个两格跳段：dst-src == 4 * v。"""
    diff = sub_vec(dst, src)
    if any(d % 4 != 0 for d in diff):
        return False
    quarter = (diff[0] // 4, diff[1] // 4, diff[2] // 4)
    return quarter in directions


def two_step_mid(src: Point, dst: Point) -> Point:
    """返回两格跳段中被跳位置的坐标。"""
    return (
        src[0] + (dst[0] - src[0]) // 2,
        src[1] + (dst[1] - src[1]) // 2,
        src[2] + (dst[2] - src[2]) // 2,
    )
