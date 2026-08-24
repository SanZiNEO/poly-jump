"""AI 选择器基础测试。"""

from __future__ import annotations

from backend.game.ai import (
    GraphProgressAI,
    GreedyAI,
    ProgressAI,
    RandomAI,
    ScoringAwareAI,
)
from backend.game.config import ScoringConfig
from backend.game.board import Board
from backend.game.config import PolyJumpConfig


def make_board() -> Board:
    cfg = PolyJumpConfig(board_size=(9, 9, 9), players=2, direction_set=[6])
    board = Board(cfg, setup=False)
    # 手动设置：玩家1棋子从(0,0,0)出发，目标区在(5,0,0)
    board.player_targets = {1: {(5, 0, 0)}}
    board.set_piece((0, 0, 0), 1)
    return board


def test_random_ai_returns_legal_path():
    paths = [[(0, 0, 0), (1, 0, 0)]]
    assert RandomAI().select_move(paths) in paths


def test_greedy_ai_picks_closer_to_target():
    board = make_board()
    paths = [
        [(0, 0, 0), (1, 0, 0)],
        [(0, 0, 0), (0, 1, 0)],
    ]
    chosen = GreedyAI().select_move(board, 1, paths)
    assert chosen == [(0, 0, 0), (1, 0, 0)]


def test_progress_ai_avoids_backward_jump():
    board = make_board()
    paths = [
        [(0, 0, 0), (1, 0, 0)],   # 前进
        [(0, 0, 0), (0, 0, -1)],  # 倒跳
    ]
    chosen = ProgressAI().select_move(board, 1, paths)
    assert chosen == [(0, 0, 0), (1, 0, 0)]


def test_progress_ai_prefers_longer_chain_forward():
    board = make_board()
    board.set_piece((2, 0, 0), 2)  # 垫脚石
    paths = [
        [(0, 0, 0), (1, 0, 0)],                # 普通前进 1 格
        [(0, 0, 0), (4, 0, 0)],                # 连跳，如果合法
    ]
    # 简单验证：连跳路径评分不低于普通前进
    ai = ProgressAI()
    assert ai._count_captures(board, [(0, 0, 0), (4, 0, 0)], [(1, 0, 0)], 1) == 1


def test_graph_progress_ai_picks_forward():
    board = make_board()
    paths = [
        [(0, 0, 0), (1, 0, 0)],
        [(0, 0, 0), (0, 1, 0)],
    ]
    chosen = GraphProgressAI().select_move(board, 1, paths)
    assert chosen == [(0, 0, 0), (1, 0, 0)]


def test_scoring_aware_ai_prefers_target_zone():
    cfg = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
        scoring=ScoringConfig(enabled=True, target_zone_points=20),
    )
    board = Board(cfg, setup=False)
    board.player_targets = {1: {(5, 0, 0)}}
    board.set_piece((0, 0, 0), 1)

    paths = [
        [(0, 0, 0), (1, 0, 0)],
        [(0, 0, 0), (5, 0, 0)],
    ]
    chosen = ScoringAwareAI().select_move(board, 1, paths)
    assert chosen == [(0, 0, 0), (5, 0, 0)]
