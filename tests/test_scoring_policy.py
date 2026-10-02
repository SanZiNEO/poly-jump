"""积分策略接口测试：注入、替换、克隆与重置语义。"""

from __future__ import annotations

import random

import pytest

from backend.game.config import InitialLayoutConfig, PolyJumpConfig, ScoringConfig
from backend.game.env import GameEnv
from backend.game.game_state import GameState
from backend.game.scoring import (
    ActionContext,
    FinishContext,
    NullScoring,
    ScoreDelta,
    ScoringPolicy,
    WeightedScoring,
)


class TargetOnlyScoring:
    """自定义策略：只给「从目标区外进入目标区」计分，并记录每次调用的上下文。"""

    def __init__(self, points: int = 3):
        self.points = points
        self.contexts: list[ActionContext] = []

    @property
    def calls(self) -> int:
        return len(self.contexts)

    def on_action(self, ctx: ActionContext) -> ScoreDelta:
        self.contexts.append(ctx)
        if ctx.entered_target:
            return ScoreDelta(scores={ctx.player: self.points})
        return ScoreDelta()

    def on_finish(self, ctx: FinishContext) -> dict:
        return dict(ctx.scores)


def make_config() -> PolyJumpConfig:
    """小棋盘 + 关掉内置计分，便于验证「分数完全由注入的策略决定」。"""
    return PolyJumpConfig(
        board_size=(5, 5, 5),
        players=2,
        direction_set=[6],
        initial_layout=InitialLayoutConfig(layers=2),
        scoring=ScoringConfig(enabled=False),
    )


def play(env: GameEnv, steps: int, seed: int = 7):
    random.seed(seed)
    obs = env.reset()
    for _ in range(steps):
        if obs.done:
            break
        obs = env.execute_action(random.choice(obs.legal_actions)["id"])
    return obs


def test_protocol_is_runtime_checkable():
    assert isinstance(WeightedScoring(make_config()), ScoringPolicy)
    assert isinstance(NullScoring(), ScoringPolicy)
    assert isinstance(TargetOnlyScoring(), ScoringPolicy)
    assert not isinstance(object(), ScoringPolicy)


def test_invalid_policy_rejected_at_construction():
    with pytest.raises(TypeError, match="ScoringPolicy"):
        GameState(make_config(), scoring=object())


def test_default_policy_is_weighted_scoring():
    assert isinstance(GameState(make_config()).scoring, WeightedScoring)


def test_null_scoring_leaves_every_score_at_zero():
    env = GameEnv(make_config(), scoring=NullScoring())
    play(env, 40)
    assert set(env.state.scores.values()) == {0}
    assert set(env.state.temp_scores.values()) == {0}


def test_custom_policy_drives_the_env():
    """分数完全由注入的策略决定，与 config 里的内置权重无关。"""
    policy = TargetOnlyScoring(points=3)
    env = GameEnv(make_config(), scoring=policy)
    env.reset()

    # 造一个「棋子一步即可进入目标区」的局面
    board = env.state.board
    board.pieces = {}
    board.player_targets = {1: {(1, 0, 0)}, 2: set()}
    board.player_bases = {1: set(), 2: set()}
    board.set_piece((0, 0, 0), 1)
    env.state.current_player = 1

    entering = [a for a in env.state.legal_actions() if a[-1] == (1, 0, 0)]
    assert entering, "测试前提：应存在一步进入目标区的走法"

    env.execute_action(entering[0])

    assert env.state.scores[1] == 3
    assert env.state.temp_scores[1] == 0, "自定义策略没有临时分，不该凭空产生"
    assert any(c.entered_target for c in policy.contexts)


def test_policy_receives_every_action_with_facts():
    """策略必须被每一次 action 调用，并拿到对应的事实快照。"""
    policy = TargetOnlyScoring()
    env = GameEnv(make_config(), scoring=policy)
    play(env, 30)

    assert policy.calls == env.state.action_count
    assert all(c.player in (1, 2) for c in policy.contexts)
    assert all(c.config is env.config for c in policy.contexts)
    assert all(c.board is env.state.board for c in policy.contexts)
    assert all(len(c.path) >= 2 for c in policy.contexts)


def test_policy_is_shared_across_clone():
    """clone（搜索/模拟）按引用共享策略，不做深拷贝。"""
    policy = TargetOnlyScoring()
    env = GameEnv(make_config(), scoring=policy)
    env.reset()

    cloned = env.clone()
    assert cloned.scoring is policy
    assert cloned.state.scoring is policy


def test_policy_survives_reset():
    policy = TargetOnlyScoring()
    env = GameEnv(make_config(), scoring=policy)
    env.reset()
    env.reset()
    assert env.state.scoring is policy


def test_clone_scores_independently_of_original():
    """克隆体自己计分，不影响原状态。"""
    policy = TargetOnlyScoring(points=5)
    env = GameEnv(make_config(), scoring=policy)
    env.reset()

    twin = env.clone()
    play(twin, 40, seed=11)

    assert env.state.scores[1] == 0, "克隆体计分不应影响原状态"
