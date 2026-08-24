"""吃子模式处理：NONE / CAPTURE / MIXED。

MIXED：被跳棋子不被移除，而是放回它自己的初始基地；
如果基地该位置被占，则放到基地内最近空格；
如果基地已满，则放到基地边缘最近的空格。
"""

from __future__ import annotations

from typing import List, Tuple

from ..board import Board
from ..config import CaptureConfig, CaptureMode

Point = Tuple[int, int, int]


def _dist(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


class CaptureHandler:
    def __init__(self, config: CaptureConfig):
        self.config = config

    def handle_jump(
        self,
        board: Board,
        src: Point,
        dst: Point,
        mover: int,
        captured_owner: int,
        captured_pos: Point,
    ) -> None:
        if captured_owner == mover and self.config.capture_opponent_only:
            return

        if self.config.mode == CaptureMode.CAPTURE:
            board.remove_piece(captured_pos)
        elif self.config.mode == CaptureMode.MIXED:
            board.remove_piece(captured_pos)
            slot = self._find_home_slot(board, captured_owner, captured_pos)
            if slot is not None and board.is_empty(slot):
                board.set_piece(slot, captured_owner)

    def _find_home_slot(self, board: Board, owner: int, captured_pos: Point) -> Point | None:
        """找到该玩家基地内最近空格；基地满则找基地边缘最近空格。"""
        base = list(board.player_bases.get(owner, set()))
        if not base:
            return None

        empties_in_base = [p for p in base if board.is_empty(p)]
        if empties_in_base:
            return min(empties_in_base, key=lambda p: _dist(p, captured_pos))

        # 基地已满：找所有合法空格中距离基地边缘最近的一个
        candidates = [p for p in board.points if board.is_empty(p)]
        if not candidates:
            return None
        return min(candidates, key=lambda p: min(_dist(p, b) for b in base))
