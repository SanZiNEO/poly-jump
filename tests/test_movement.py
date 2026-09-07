"""基础移动规则单元测试：普通移动、单跳、连跳。"""

from __future__ import annotations

import pytest

from backend.game.board import Board
from backend.game.config import (
    CaptureConfig,
    HopMode,
    MovementConfig,
    PolyJumpConfig,
)
from backend.game.movement import ActionGenerator


def make_config(
    directions=(6,),
    hop_mode: HopMode = HopMode.FREE_STOP,
    allow_single_move: bool = True,
    allow_jump: bool = True,
    allow_chain: bool = True,
) -> PolyJumpConfig:
    return PolyJumpConfig(
        board_size=(7, 7, 7),
        players=2,
        direction_set=list(directions),
        movement=MovementConfig(
            allow_single_move=allow_single_move,
            allow_jump=allow_jump,
            allow_chain=allow_chain,
            hop_mode=hop_mode,
        ),
        capture=CaptureConfig(mode="NONE"),
    )


def make_empty_board(config: PolyJumpConfig) -> Board:
    return Board(config, setup=False)


def test_single_move():
    config = make_config()
    board = make_empty_board(config)
    board.set_piece((0, 0, 0), 1)

    actions = ActionGenerator(config).legal_actions(board, 1)

    assert [(0, 0, 0), (1, 0, 0)] in actions
    assert [(0, 0, 0), (0, 1, 0)] in actions
    assert [(0, 0, 0), (0, 0, 1)] in actions


def test_single_jump():
    config = make_config()
    board = make_empty_board(config)
    board.set_piece((0, 0, 0), 1)
    board.set_piece((1, 0, 0), 2)

    actions = ActionGenerator(config).legal_actions(board, 1)

    assert [(0, 0, 0), (2, 0, 0)] in actions


def test_jump_requires_occupied_mid_and_empty_landing():
    config = make_config()
    board = make_empty_board(config)
    board.set_piece((0, 0, 0), 1)
    board.set_piece((1, 0, 0), 2)
    board.set_piece((2, 0, 0), 2)

    actions = ActionGenerator(config).legal_actions(board, 1)

    assert [(0, 0, 0), (2, 0, 0)] not in actions


def test_chain_jump_free_stop_includes_intermediate():
    config = make_config(hop_mode=HopMode.FREE_STOP)
    board = make_empty_board(config)
    board.set_piece((0, 0, 0), 1)
    board.set_piece((1, 0, 0), 2)
    board.set_piece((3, 0, 0), 2)

    actions = ActionGenerator(config).legal_actions(board, 1)

    assert [(0, 0, 0), (2, 0, 0)] in actions
    assert [(0, 0, 0), (2, 0, 0), (4, 0, 0)] in actions


def test_chain_jump_force_all_only_terminal():
    config = make_config(hop_mode=HopMode.FORCE_ALL)
    board = make_empty_board(config)
    board.set_piece((0, 0, 0), 1)
    board.set_piece((1, 0, 0), 2)
    board.set_piece((3, 0, 0), 2)

    actions = ActionGenerator(config).legal_actions(board, 1)

    assert [(0, 0, 0), (2, 0, 0)] not in actions
    assert [(0, 0, 0), (2, 0, 0), (4, 0, 0)] in actions


def test_disabled_jump_only_single_move_actions():
    config = make_config(allow_jump=False)
    board = make_empty_board(config)
    board.set_piece((0, 0, 0), 1)
    board.set_piece((1, 0, 0), 2)

    actions = ActionGenerator(config).legal_actions(board, 1)

    assert [(0, 0, 0), (2, 0, 0)] not in actions
    assert [(0, 0, 0), (1, 0, 0)] not in actions  # 被占，不能走
