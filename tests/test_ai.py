"""纯距离 AI 基础测试。"""

from __future__ import annotations

from backend.game.ai import (
    ChebyshevDistanceAI,
    EuclideanDistanceAI,
    GraphDistanceAI,
)
from backend.game.board import Board
from backend.game.config import PolyJumpConfig


def make_board() -> Board:
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    board = Board(cfg, setup=False)
    # 手动设置：玩家1棋子从(0,0,0)出发，目标区在(5,0,0)
    board.player_targets = {1: {(5, 0, 0)}}
    board.set_piece((0, 0, 0), 1)
    return board


def sample_paths():
    return [
        [(0, 0, 0), (1, 0, 0)],   # 向目标区前进
        [(0, 0, 0), (0, 1, 0)],   # 偏离目标区
    ]


def test_euclidean_ai_picks_closer_to_target():
    board = make_board()
    chosen = EuclideanDistanceAI().select_move(board, 1, sample_paths())
    assert chosen == [(0, 0, 0), (1, 0, 0)]


def test_chebyshev_ai_picks_closer_to_target():
    board = make_board()
    chosen = ChebyshevDistanceAI().select_move(board, 1, sample_paths())
    assert chosen == [(0, 0, 0), (1, 0, 0)]


def test_graph_distance_ai_picks_forward():
    board = make_board()
    chosen = GraphDistanceAI().select_move(board, 1, sample_paths())
    assert chosen == [(0, 0, 0), (1, 0, 0)]


def test_graph_distance_map():
    board = make_board()
    directions = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    dist = GraphDistanceAI._distance_map(board, {(5, 0, 0)}, directions)
    assert dist.get((0, 0, 0)) == 5
    assert dist.get((5, 0, 0)) == 0
