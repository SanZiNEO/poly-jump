"""跳跃与连跳生成。

只负责“从某个点出发的所有合法跳跃路径”，不包含普通移动。
"""

from __future__ import annotations

from typing import List, Sequence

from ..board import Board
from ..directions import Vector, add_vec, scale_vec
from .types import Path, Point


class JumpGenerator:
    def __init__(
        self,
        directions: Sequence[Vector],
        max_chain_length: int = 0,
    ):
        self.directions = list(directions)
        self.max_chain_length = max_chain_length

    def all_jump_paths(self, board: Board, pos: Point) -> List[Path]:
        return self._recurse(board, [tuple(pos)], depth=0)

    def has_any_jump(self, board: Board, pos: Point, exclude_path: Path) -> bool:
        for v in self.directions:
            mid = add_vec(pos, v)
            dest = add_vec(pos, scale_vec(v, 2))
            if (
                board.is_inside(mid)
                and not board.is_empty(mid)
                and board.is_inside(dest)
                and board.is_empty(dest)
                and dest not in exclude_path
            ):
                return True
        return False

    def _recurse(
        self,
        board: Board,
        path: Path,
        depth: int,
    ) -> List[Path]:
        results: List[Path] = []
        if self.max_chain_length and depth >= self.max_chain_length:
            return results

        current = path[-1]
        for v in self.directions:
            mid = add_vec(current, v)
            dest = add_vec(current, scale_vec(v, 2))
            if (
                board.is_inside(mid)
                and not board.is_empty(mid)
                and board.is_inside(dest)
                and board.is_empty(dest)
                and dest not in path
            ):
                new_path = path + [dest]
                results.append(new_path)
                results.extend(self._recurse(board, new_path, depth + 1))
        return results
