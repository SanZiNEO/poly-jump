"""积分制接口测试。"""

from __future__ import annotations

from backend.game.config import PolyJumpConfig, ScoringConfig
from backend.game.scoring import ScoringEngine


def make_engine(scoring: ScoringConfig | None = None) -> ScoringEngine:
    cfg = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
        scoring=scoring or ScoringConfig(enabled=True),
    )
    return ScoringEngine(cfg)


def test_chain_jump_scores_by_extra_jumps():
    engine = make_engine()
    # 普通跳不长分
    result = engine.assess_move(1, [[0, 0, 0], [1, 0, 0]])
    assert result["chain_temp"] == 0

    # 连跳两次：路径长度 3，临时分 +2
    result = engine.assess_move(1, [[0, 0, 0], [2, 0, 0], [4, 0, 0]])
    assert result["chain_temp"] == 2


def test_chain_scoring_cap_limits_scored_jumps():
    cfg = PolyJumpConfig(
        board_size=(9, 9, 9),
        players=2,
        direction_set=[6],
        scoring=ScoringConfig(enabled=True, chain_jump_points=1, chain_max_scoring=5),
    )
    engine = ScoringEngine(cfg)
    # 实际连跳 10 次，但计分上限 5
    path = [[0, 0, 0]] + [[i * 2, 0, 0] for i in range(1, 11)]
    result = engine.assess_move(1, path)
    assert result["chain_temp"] == 5


def test_target_zone_points():
    engine = make_engine()
    result = engine.assess_move(1, [[0, 0, 0], [1, 0, 0]], reached_target=True)
    assert result["target_points"] == 1


def test_capture_points():
    engine = make_engine()
    result = engine.assess_move(1, [[0, 0, 0], [2, 0, 0]], capture_count=3)
    assert result["capture_points"] == 6  # capture_points=2


def test_finalize_winner_keeps_temp_loser_loses():
    engine = make_engine()
    scores = {1: 1, 2: 0}
    temp = {1: 2, 2: 1}
    board = type("B", (), {})()
    # 用真实 Board 会更好，但 finalize 这里只需要 pieces_for_player
    class DummyBoard:
        def pieces_for_player(self, player):
            return [1, 2] if player == 1 else []

    result = engine.finalize(1, 2, DummyBoard(), scores, temp)
    # 胜者保留临时分 + 目标胜利奖励
    assert result[1] == 1 + 2 + 10
    # 败者扣临时分
    assert result[2] == 0 - 1
