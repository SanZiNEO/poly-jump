"""简单胜负判定。"""

from __future__ import annotations

from typing import Optional

from ..board import Board
from ..config import PolyJumpConfig


def check_winner(board: Board, config: PolyJumpConfig) -> Optional[int]:
    """返回获胜玩家编号；没有胜者返回 None。

    中国跳棋默认：某玩家全部棋子都在其目标区且目标区填满即胜利。
    CAPTURE 模式：吃光所有其他玩家棋子者获胜。
    MIXED 模式：仍然按中国跳棋目标区胜利。
    """
    if config.capture.mode.value == "CAPTURE":
        return _check_capture_winner(board, config)

    if not config.goal.first_to_finish_wins:
        return None

    return _check_target_winner(board, config)


def _check_target_winner(board: Board, config: PolyJumpConfig) -> Optional[int]:
    for player in range(1, config.players + 1):
        target = board.player_targets.get(player, set())
        if not target:
            continue
        pieces = board.pieces_for_player(player)
        if not pieces:
            continue

        if config.goal.must_fill_all_cells:
            if all(board.get_piece(cell) == player for cell in target):
                return player
        else:
            if all(p in target for p in pieces):
                return player

    return None


def _check_capture_winner(board: Board, config: PolyJumpConfig) -> Optional[int]:
    """CAPTURE 模式：最后一个仍有棋子的玩家获胜。"""
    for player in range(1, config.players + 1):
        if not board.pieces_for_player(player):
            continue
        opponents_have_pieces = any(
            other != player and board.pieces_for_player(other)
            for other in range(1, config.players + 1)
        )
        if not opponents_have_pieces:
            return player
    return None
