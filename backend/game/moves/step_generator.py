"""普通一步移动生成。"""

from __future__ import annotations

from typing import List, Sequence

from ..board import Board
from ..directions import Vector, add_vec
from .types import Path, Point


class StepGenerator:
    def __init__(self, directions: Sequence[Vector]):
        self.directions = list(directions)

    def moves_from(self, board: Board, pos: Point) -> List[Path]:
        paths: List[Path] = []
        for v in self.directions:
            dest = add_vec(pos, v)
            if board.is_inside(dest) and board.is_empty(dest):
                paths.append([tuple(pos), tuple(dest)])
        return paths
