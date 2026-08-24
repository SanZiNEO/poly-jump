"""AI 选择器基础测试。"""

from __future__ import annotations

from backend.game.ai import GreedyAI, RandomAI
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
