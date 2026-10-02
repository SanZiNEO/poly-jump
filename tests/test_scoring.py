"""`WeightedScoring` 规则测试（框架默认积分规则）。"""

from __future__ import annotations

from backend.game.board import Board
from backend.game.config import (
    CaptureConfig,
    CaptureMode,
    PolyJumpConfig,
    ScoringConfig,
)
from backend.game.scoring import ActionContext, FinishContext, ScoreDelta, WeightedScoring


def make_parts(scoring: ScoringConfig | None = None, capture_mode: CaptureMode = CaptureMode.NONE):
    """返回 (策略, 配置, 棋盘)。"""
    config = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
        scoring=scoring or ScoringConfig(enabled=True),
        capture=CaptureConfig(mode=capture_mode),
    )
    return WeightedScoring(config), config, Board(config)


def ctx(config, board, path, *, captured=0, entered_target=False, player=1) -> ActionContext:
    return ActionContext(
        player=player,
        path=[list(p) for p in path],
        captured=captured,
        entered_target=entered_target,
        board=board,
        config=config,
        round=1,
    )


def test_chain_jump_scores_by_extra_jumps():
    policy, config, board = make_parts()
    # 普通跳不长分
    assert policy.on_action(ctx(config, board, [[0, 0, 0], [1, 0, 0]])).temp_scores.get(1, 0) == 0
    # 连跳两次：路径长度 3，临时分 +2
    assert policy.on_action(ctx(config, board, [[0, 0, 0], [2, 0, 0], [4, 0, 0]])).temp_scores[1] == 2


def test_chain_scoring_cap_limits_scored_jumps():
    policy, config, board = make_parts(
        ScoringConfig(enabled=True, chain_jump_points=1, chain_max_scoring=5)
    )
    # 实际连跳 10 次，但计分上限 5
    path = [[0, 0, 0]] + [[i * 2, 0, 0] for i in range(1, 11)]
    assert policy.on_action(ctx(config, board, path)).temp_scores[1] == 5


def test_target_zone_points():
    policy, config, board = make_parts()
    delta = policy.on_action(ctx(config, board, [[0, 0, 0], [1, 0, 0]], entered_target=True))
    assert delta.scores[1] == 1


def test_capture_points():
    policy, config, board = make_parts()
    delta = policy.on_action(ctx(config, board, [[0, 0, 0], [2, 0, 0]], captured=3))
    assert delta.scores[1] == 6  # capture_points=2


def test_disabled_scoring_produces_no_action_delta():
    policy, config, board = make_parts(ScoringConfig(enabled=False))
    delta = policy.on_action(
        ctx(config, board, [[0, 0, 0], [2, 0, 0], [4, 0, 0]], captured=5, entered_target=True)
    )
    assert delta == ScoreDelta()


def test_finish_winner_keeps_temp_loser_loses():
    policy, config, board = make_parts()
    result = policy.on_finish(
        FinishContext(
            winner=1,
            players=2,
            board=board,
            scores={1: 1, 2: 0},
            temp_scores={1: 2, 2: 1},
            config=config,
        )
    )
    # 胜者保留临时分 + 目标胜利奖励
    assert result[1] == 1 + 2 + 10
    # 败者扣临时分
    assert result[2] == 0 - 1


def test_finish_capture_mode_scores_survivors():
    policy, config, board = make_parts(
        ScoringConfig(enabled=True, survivor_piece_points=3),
        capture_mode=CaptureMode.CAPTURE,
    )
    survivors = len(board.pieces_for_player(1))
    assert survivors > 0

    result = policy.on_finish(
        FinishContext(
            winner=1,
            players=2,
            board=board,
            scores={1: 0, 2: 0},
            temp_scores={1: 0, 2: 0},
            config=config,
        )
    )
    assert result[1] == survivors * 3
