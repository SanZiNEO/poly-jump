"""两格跳（空一格跳）生成。

规则：
    起点 p
    p+v     空
    p+2v    有子（被跳）
    p+3v    空
    p+4v    空
    -> 可到 p+4v
"""

from __future__ import annotations

from typing import List, Sequence

from ..board import Board
from ..directions import Vector, add_vec, scale_vec
from .types import Path, Point


class TwoStepHopGenerator:
    def __init__(self, directions: Sequence[Vector]):
        self.directions = list(directions)

    def moves_from(self, board: Board, pos: Point) -> List[Path]:
        paths: List[Path] = []
        pos = tuple(pos)
        for v in self.directions:
            q1 = add_vec(pos, v)
            q2 = add_vec(pos, scale_vec(v, 2))
            q3 = add_vec(pos, scale_vec(v, 3))
            q4 = add_vec(pos, scale_vec(v, 4))

            if not all(
                board.is_inside(p)
                for p in (q1, q2, q3, q4)
            ):
                continue
            if not (board.is_empty(q1) and not board.is_empty(q2) and board.is_empty(q3) and board.is_empty(q4)):
                continue
            paths.append([pos, q4])
        return paths
