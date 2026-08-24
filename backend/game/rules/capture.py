"""吃子模式处理：NONE / CAPTURE / MIXED。"""

from __future__ import annotations

from typing import Tuple

from ..board import Board
from ..config import CaptureConfig, CaptureMode

Point = Tuple[int, int, int]


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
    ) -> None:
        if captured_owner == mover and self.config.capture_opponent_only:
            return

        mid = (
            (src[0] + dst[0]) // 2,
            (src[1] + dst[1]) // 2,
            (src[2] + dst[2]) // 2,
        )

        if self.config.mode == CaptureMode.CAPTURE:
            board.remove_piece(mid)
        elif self.config.mode == CaptureMode.MIXED:
            board.remove_piece(mid)
            board.set_piece(src, captured_owner)
        # NONE: 不做任何吃子/位移
