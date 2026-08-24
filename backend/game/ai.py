"""可选小 AI：RandomAI、GreedyAI、ProgressAI。

不包含训练逻辑，只作为游戏内的小棋手。
"""

from __future__ import annotations

import random
from typing import List, Optional, Sequence

from .board import Board
from .directions import resolve_direction_set
from .moves.segment import (
    is_jump_segment,
    is_two_step_segment,
    jump_mid,
    two_step_mid,
)


def _manhattan(a: Sequence[int], b: Sequence[int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


class RandomAI:
    def select_move(self, legal_paths: List[Sequence[Sequence[int]]]) -> Optional[list]:
        if not legal_paths:
            return None
        return random.choice(list(legal_paths))


class GreedyAI:
    """简单贪心 AI：选择让单个棋子更接近目标区的走法。"""

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


class ProgressAI:
    """带连跳奖励和回跳惩罚的简单 AI。

    评分：
        + 向目标区前进
        + 连跳长度奖励
        + 吃子奖励
        - 倒跳惩罚
    """

    def __init__(
        self,
        chain_bonus: float = 1.5,
        capture_bonus: float = 3.0,
        backward_penalty: float = 2.0,
    ):
        self.chain_bonus = chain_bonus
        self.capture_bonus = capture_bonus
        self.backward_penalty = backward_penalty

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

        directions = resolve_direction_set(
            board.config.direction_set, board.config.custom_vectors
        )

        def score(path: Sequence[Sequence[int]]) -> float:
            start = path[0]
            end = path[-1]
            before = min(_manhattan(start, t) for t in target)
            after = min(_manhattan(end, t) for t in target)
            progress = before - after

            chain = max(0, len(path) - 2) * self.chain_bonus
            captures = self._count_captures(board, path, directions, player)
            capture_gain = captures * self.capture_bonus

            if progress < 0:
                # 倒跳：重罚
                return progress + chain + capture_gain - abs(progress) * self.backward_penalty

            return progress + chain + capture_gain

        return max(legal_paths, key=score)

    @staticmethod
    def _count_captures(
        board: Board,
        path: Sequence[Sequence[int]],
        directions,
        player: int,
    ) -> int:
        count = 0
        for i in range(len(path) - 1):
            src = path[i]
            dst = path[i + 1]
            if is_jump_segment(src, dst, directions):
                mid = jump_mid(src, dst)
            elif is_two_step_segment(src, dst, directions):
                mid = two_step_mid(src, dst)
            else:
                continue
            owner = board.get_piece(mid)
            if owner is not None and owner != player:
                count += 1
        return count
