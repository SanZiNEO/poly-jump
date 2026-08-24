"""MoveGenerator：按配置组合普通移动、单跳、连跳，返回合法路径列表。"""

from __future__ import annotations

from typing import Iterable, List

from ..board import Board
from ..config import HopMode, PolyJumpConfig
from ..directions import resolve_direction_set
from .jump_generator import JumpGenerator
from .step_generator import StepGenerator
from .types import Path, Point


class MoveGenerator:
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.directions = resolve_direction_set(
            config.direction_set, config.custom_vectors
        )
        self.step_generator = StepGenerator(self.directions)
        self.jump_generator = JumpGenerator(
            self.directions,
            max_chain_length=config.movement.max_chain_length,
        )

    def legal_moves(self, board: Board, player: int) -> List[Path]:
        paths: List[Path] = []
        for pos in board.pieces_for_player(player):
            paths.extend(self.legal_moves_from(board, pos))
        return self._deduplicate(paths)

    def legal_moves_from(self, board: Board, pos: Point) -> List[Path]:
        paths: List[Path] = []
        pos = tuple(pos)

        if self.config.movement.allow_step:
            paths.extend(self.step_generator.moves_from(board, pos))

        if self.config.movement.allow_jump:
            jump_paths = self.jump_generator.all_jump_paths(board, pos)
            if self.config.movement.hop_mode == HopMode.FREE_STOP:
                paths.extend(jump_paths)
            else:
                paths.extend(
                    path
                    for path in jump_paths
                    if not self.jump_generator.has_any_jump(board, path[-1], path)
                )

        return self._deduplicate(paths)

    @staticmethod
    def _deduplicate(paths: Iterable[Path]) -> List[Path]:
        seen = set()
        out: List[Path] = []
        for path in paths:
            key = tuple(path)
            if key not in seen:
                seen.add(key)
                out.append(path)
        return out
