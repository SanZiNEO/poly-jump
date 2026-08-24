"""通用规则扩展测试：两格跳、吃子模式。"""

from __future__ import annotations

from backend.game.board import Board
from backend.game.config import (
    CaptureConfig,
    CaptureMode,
    MovementConfig,
    PolyJumpConfig,
)
from backend.game.game_state import GameState
from backend.game.moves import MoveGenerator
from backend.game.rules.capture import CaptureHandler
from backend.game.rules.winner import check_winner


def test_two_step_hop():
    cfg = PolyJumpConfig(
        board_size=(7, 7, 7),
        players=2,
        direction_set=[6],
        movement=MovementConfig(
            allow_step=False,
            allow_jump=False,
            allow_chain=False,
            two_step_hop=True,
        ),
    )
    board = Board(cfg, setup=False)
    board.set_piece((0, 0, 0), 1)
    board.set_piece((2, 0, 0), 2)

    moves = MoveGenerator(cfg).legal_moves(board, 1)

    # p(0)->空(1)->子(2)->空(3)->空(4)
    assert [(0, 0, 0), (4, 0, 0)] in moves


def test_capture_win_when_all_opponents_gone():
    cfg = PolyJumpConfig(
        board_size=(5, 5, 5),
        players=2,
        direction_set=[6],
        capture=CaptureConfig(mode=CaptureMode.CAPTURE),
    )
    board = Board(cfg, setup=False)
    board.set_piece((0, 0, 0), 1)

    assert check_winner(board, cfg) == 1


def test_mixed_capture_returns_piece_to_own_base():
    cfg = PolyJumpConfig(
        board_size=(5, 5, 5),
        players=2,
        direction_set=[6],
        capture=CaptureConfig(mode=CaptureMode.MIXED),
    )
    board = Board(cfg, setup=False)
    board.points = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]
    board.player_bases = {2: [(2, 0, 0)]}
    board.set_piece((1, 0, 0), 2)

    handler = CaptureHandler(cfg.capture)
    handler.handle_jump(
        board,
        src=(0, 0, 0),
        dst=(2, 0, 0),
        mover=1,
        captured_owner=2,
        captured_pos=(1, 0, 0),
    )

    assert board.get_piece((1, 0, 0)) is None
    assert board.get_piece((2, 0, 0)) == 2


def test_no_move_auto_skip_to_next_player():
    cfg = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
        movement=MovementConfig(
            allow_step=True,
            allow_jump=False,
            allow_chain=False,
        ),
    )
    state = GameState(cfg)
    state.board.pieces = {}
    state.board.set_piece((0, 0, 0), 2)
    state.current_player = 1

    state._advance_turn()

    assert state.current_player == 2
