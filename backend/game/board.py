"""棋盘状态。"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from .config import PolyJumpConfig
from .geometry import Geometry, create_geometry
from .geometry.base import Point


class Board:
    def __init__(self, config: PolyJumpConfig, setup: bool = True):
        self.config = config
        self.geometry: Geometry = create_geometry(config)
        self.points: List[Point] = self.geometry.generate_points()
        self.pieces: Dict[Point, int] = {}
        self.player_bases: Dict[int, Set[Point]] = {}
        self.player_targets: Dict[int, Set[Point]] = {}

        if setup:
            bases, targets = self.geometry.player_assignments()
            self.player_bases = {k: set(v) for k, v in bases.items()}
            self.player_targets = {k: set(v) for k, v in targets.items()}
            self._setup_initial_layout()

    def _setup_initial_layout(self) -> None:
        for player, base in self.player_bases.items():
            for pos in base:
                if pos in self.pieces:
                    # 基地重叠在完整实现中应被配置校验拦截；这里先防御。
                    raise ValueError(f"初始基地重叠：{pos}")
                self.pieces[pos] = player

    def is_inside(self, pos: Point) -> bool:
        return self.geometry.is_inside(tuple(pos))

    def is_empty(self, pos: Point) -> bool:
        return tuple(pos) not in self.pieces

    def get_piece(self, pos: Point) -> Optional[int]:
        return self.pieces.get(tuple(pos))

    def set_piece(self, pos: Point, player: int) -> None:
        self.pieces[tuple(pos)] = player

    def remove_piece(self, pos: Point) -> None:
        self.pieces.pop(tuple(pos), None)

    def pieces_for_player(self, player: int) -> List[Point]:
        return [pos for pos, owner in self.pieces.items() if owner == player]
