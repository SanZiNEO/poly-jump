"""执行一条合法路径，更新棋盘。"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from ..board import Board
from ..config import PolyJumpConfig
from ..directions import resolve_direction_set
from ..moves.segment import (
    is_jump_segment,
    is_two_step_segment,
    jump_mid,
    two_step_mid,
)
from .capture import CaptureHandler

Point = Tuple[int, int, int]
Path = List[Point]


class MoveApplier:
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.directions = resolve_direction_set(
            config.direction_set, config.custom_vectors
        )
        self.capture_handler = CaptureHandler(config.capture)

    def apply(
        self,
        board: Board,
        path: Sequence[Sequence[int]],
        player: int,
    ) -> None:
        path_t: Path = [tuple(p) for p in path]
        if len(path_t) < 2:
            raise ValueError("路径长度必须 >= 2")

        start = path_t[0]
        if board.get_piece(start) != player:
            raise ValueError("路径起点不是当前玩家棋子")

        board.remove_piece(start)
        for i in range(len(path_t) - 1):
            src = path_t[i]
            dst = path_t[i + 1]

            # 先把棋子从本段起点移到落点；混合吃子会稍后回填被跳子。
            if board.get_piece(src) == player:
                board.remove_piece(src)
            board.set_piece(dst, player)

            captured_pos = self._captured_pos(src, dst)
            if captured_pos is None:
                continue

            captured_owner = board.get_piece(captured_pos)
            if captured_owner is not None:
                self.capture_handler.handle_jump(
                    board, src, dst, player, captured_owner, captured_pos
                )

    def _captured_pos(self, src: Point, dst: Point) -> Point | None:
        """返回标准跳/两格跳中被跳棋子位置；不是跳跃段返回 None。"""
        if is_jump_segment(src, dst, self.directions):
            return jump_mid(src, dst)
        if is_two_step_segment(src, dst, self.directions):
            return two_step_mid(src, dst)
        return None
