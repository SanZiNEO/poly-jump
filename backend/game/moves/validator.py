"""提交路径的权威校验。"""

from __future__ import annotations

from typing import Sequence

from ..board import Board
from ..config import PolyJumpConfig
from .generator import MoveGenerator
from .types import Path, Point


class MoveValidator:
    def __init__(self, config: PolyJumpConfig):
        self.generator = MoveGenerator(config)

    def is_legal(
        self,
        board: Board,
        player: int,
        path: Sequence[Sequence[int]],
    ) -> bool:
        path_t: Path = [tuple(p) for p in path]
        return path_t in self.generator.legal_moves(board, player)
