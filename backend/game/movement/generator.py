"""ActionGenerator：按配置组合普通移动、单跳、连跳，返回合法 action 路径列表。"""

from __future__ import annotations

from typing import Iterable, List

from ..board import Board
from ..config import HopMode, PolyJumpConfig
from ..directions import resolve_direction_set
from .jump_generator import JumpGenerator
from .single_step_generator import SingleStepGenerator
from .two_hop_generator import TwoHopGenerator
from .types import Path, Point


class ActionGenerator:
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.directions = resolve_direction_set(
            config.direction_set, config.custom_vectors
        )
        self.single_step_generator = SingleStepGenerator(self.directions)
        self.jump_generator = JumpGenerator(
            self.directions,
            max_chain_steps=config.movement.max_chain_steps,
        )
        self.two_hop_generator = TwoHopGenerator(self.directions)

    def legal_actions(self, board: Board, player: int) -> List[Path]:
        paths: List[Path] = []
        for pos in board.pieces_for_player(player):
            paths.extend(self.legal_actions_from(board, pos))
        return self._deduplicate(paths)

    def legal_actions_for_piece(self, board: Board, player: int, pos: Point) -> List[Path]:
        if board.get_piece(pos) != player:
            return []
        return self.legal_actions_from(board, pos)

    def legal_actions_from(self, board: Board, pos: Point) -> List[Path]:
        paths: List[Path] = []
        pos = tuple(pos)

        if self.config.movement.allow_single_move:
            paths.extend(self.single_step_generator.actions_from(board, pos))

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

        if self.config.movement.two_hop:
            paths.extend(self.two_hop_generator.actions_from(board, pos))

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
