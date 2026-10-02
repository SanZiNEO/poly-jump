"""LLM 状态渲染的回归测试。

对应缺陷记录：`docs/15-llm-state-render-issue.md`

核心约束：`Opponent progress` 必须统计"对手棋子进入**对手自己**目标区"的数量，
**不能**统计"对手棋子占用我方目标区"的数量 —— 后者会被模型误读成双方进度对比，
实测导致模型前 55 个回合局势判断错误。
"""

from __future__ import annotations

import re

from ai_research.llm.agent import render_state
from ai_research.runner import make_a_config
from backend.game.env import GameEnv


def make_env() -> GameEnv:
    """小棋盘，跑得快。"""
    env = GameEnv(make_a_config(2, (5, 5, 5), [6, 12, 8], 0))
    env.reset()
    return env


def parse(text: str, pattern: str) -> int:
    match = re.search(pattern, text)
    assert match, f"状态块缺少字段 {pattern!r}：\n{text}"
    return int(match.group(1))


def test_start_progress_is_zero_for_both_sides():
    """开局双方进度都必须是 0 —— 旧实现在这里会显示「对手 4/4」。"""
    text = render_state(make_env(), 1)
    assert parse(text, r"Your progress: (\d+)/") == 0
    assert parse(text, r"Opponent progress: (\d+)/") == 0


def test_enemy_occupying_my_target_is_a_separate_labeled_line():
    """开局时对手棋子全摆在我方目标区里，这个信息要单独一行、标签明确。"""
    text = render_state(make_env(), 1)
    assert "Enemy pieces currently occupying YOUR target region: 4" in text
    # 关键：不能把「4」伪装成对手进度
    assert "Opponent progress: 4/" not in text


def test_progress_matches_recount_after_moves():
    """走若干步后，两个进度值都要与从 state_dict 重新统计的结果一致。"""
    env = make_env()
    for _ in range(3):
        obs = env.observe()
        if obs.done:
            break
        env.execute_action(obs.legal_actions[0]["id"])

    state = env.state_dict()
    pieces: dict[int, set] = {}
    for pos, owner in state["pieces"].items():
        pieces.setdefault(int(owner), set()).add(tuple(int(v) for v in pos.split(",")))
    targets = {
        int(key): {tuple(int(v) for v in p) for p in value}
        for key, value in state["targets"].items()
    }

    for player in (1, 2):
        text = render_state(env, player)
        expected_mine = len(pieces.get(player, set()) & targets[player])
        expected_opp = len(pieces.get(3 - player, set()) & targets[3 - player])
        assert parse(text, r"Your progress: (\d+)/") == expected_mine
        assert parse(text, r"Opponent progress: (\d+)/") == expected_opp
