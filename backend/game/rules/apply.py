"""执行一条合法路径，更新棋盘。"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from ..board import Board
from ..config import PolyJumpConfig
from ..directions import resolve_direction_set
from ..moves.segment import is_jump_segment
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

            # 先把棋子从本段起点移到落点；混合吃子会在 src 空出后回填被跳子。
            if board.get_piece(src) == player:
                board.remove_piece(src)
            board.set_piece(dst, player)

            if not is_jump_segment(src, dst, self.directions):
                continue

            mid = (
                (src[0] + dst[0]) // 2,
                (src[1] + dst[1]) // 2,
                (src[2] + dst[2]) // 2,
            )
            captured_owner = board.get_piece(mid)
            if captured_owner is not None:
                self.capture_handler.handle_jump(
                    board, src, dst, player, captured_owner
                )
