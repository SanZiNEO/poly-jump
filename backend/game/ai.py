"""可选小 AI：RandomAI 和 GreedyAI。

不包含训练逻辑，只作为游戏内的小棋手。
"""

from __future__ import annotations

import random
from typing import List, Optional, Sequence

from .board import Board


def _manhattan(a: Sequence[int], b: Sequence[int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


class RandomAI:
    def select_move(self, legal_paths: List[Sequence[Sequence[int]]]) -> Optional[list]:
        if not legal_paths:
            return None
        return random.choice(list(legal_paths))


class GreedyAI:
    """贪心 AI：选择让棋子更接近目标区的走法。"""

    def select_move(
        self,
        board: Board,
        player: int,
        legal_paths: List[Sequence[Sequence[int]]],
    ) -> Optional[list]:
        if not legal_paths:
            return None

        target = board.player_targets.get(player, set())
        if not target:
            return random.choice(list(legal_paths))

        def gain(path: Sequence[Sequence[int]]) -> int:
            start = path[0]
            end = path[-1]
            before = min(_manhattan(start, t) for t in target)
            after = min(_manhattan(end, t) for t in target)
            return before - after

        return max(legal_paths, key=gain)
