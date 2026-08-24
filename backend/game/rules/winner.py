"""简单胜负判定。"""

from __future__ import annotations

from typing import Optional

from ..board import Board
from ..config import PolyJumpConfig


def check_winner(board: Board, config: PolyJumpConfig) -> Optional[int]:
    """返回获胜玩家编号；没有胜者返回 None。

    第一版规则：某玩家全部棋子都在其目标区且目标区填满即胜利。
    """
    if not config.goal.first_to_finish_wins:
        return None

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
