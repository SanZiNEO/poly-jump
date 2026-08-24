"""基地内吃子规则测试。"""

from __future__ import annotations

from backend.game.board import Board
from backend.game.config import CaptureConfig, CaptureMode, PolyJumpConfig
from backend.game.rules.capture import CaptureHandler


def make_board(capture_in_base: bool) -> Board:
    cfg = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
        capture=CaptureConfig(
            mode=CaptureMode.CAPTURE,
            capture_in_base=capture_in_base,
        ),
    )
    board = Board(cfg, setup=False)
    board.player_bases = {2: {(1, 0, 0)}}
    board.set_piece((1, 0, 0), 2)
    return board


def test_capture_disabled_inside_opponent_base():
    board = make_board(capture_in_base=False)
    handler = CaptureHandler(board.config.capture)

    handler.handle_jump(
        board,
        src=(0, 0, 0),
        dst=(2, 0, 0),
        mover=1,
        captured_owner=2,
        captured_pos=(1, 0, 0),
    )

    # 基地内跳过：不移除
    assert board.get_piece((1, 0, 0)) == 2


def test_capture_enabled_inside_opponent_base():
    board = make_board(capture_in_base=True)
    handler = CaptureHandler(board.config.capture)

    handler.handle_jump(
        board,
        src=(0, 0, 0),
        dst=(2, 0, 0),
        mover=1,
        captured_owner=2,
        captured_pos=(1, 0, 0),
    )

    # 开关开启后：基地内也吃子移除
    assert board.get_piece((1, 0, 0)) is None
