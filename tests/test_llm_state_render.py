"""LLM 状态渲染测试：多人局 + 「自上次自己行动以来的变动」窗口。

对应设计见 `ai_research/llm/agent.py::render_state` 与 `prompts/v2.md`。

两条核心约束：

1. 状态块必须列出**每个对手**的棋子与各自进度（多人局里"谁快赢了"是决策信息）；
2. 窗口必须按**玩家身份**切（`history[自己上次行动之后:]`），不能按回合数算 ——
   有玩家无棋可走被跳过时，按数字算会错位。
"""

from __future__ import annotations

import re

import pytest

from ai_research.llm.agent import render_state, trim_conversation
from ai_research.runner import make_a_config
from backend.game.env import GameEnv


def make_env(players: int = 3, size: int = 5) -> GameEnv:
    env = GameEnv(make_a_config(players, (size, size, size), [6, 12, 8], 0))
    env.reset()
    return env


def step(env: GameEnv, n: int = 1) -> None:
    for _ in range(n):
        obs = env.observe()
        if obs.done:
            return
        env.execute_action(obs.legal_actions[0]["id"])


def test_own_progress_line():
    text = render_state(make_env(players=3), 1)
    assert "Your progress: 0/4 pieces in target." in text


def test_every_opponent_is_listed_with_its_own_progress():
    text = render_state(make_env(players=4), 2)
    opponents = text.split("Other players:")[1].split("Moves since")[0]
    for other in (1, 3, 4):
        assert re.search(rf"P{other}: \d+/\d+ in target \| pieces", opponents)
    assert "P2:" not in opponents, "自己不应该出现在对手列表里"


def test_first_mover_sees_no_moves():
    text = render_state(make_env(players=3), 1)
    assert "you are first to act" in text


def test_round_label_is_the_upcoming_round():
    """显示的是「即将进行的轮次」，不是「上一个动作所在的轮次」。"""
    env = make_env(players=3)
    assert "Round 1." in render_state(env, 1)

    step(env, 3)                                   # 三人各行动一次
    actor = env.observe().current_player
    assert actor == 1
    assert "Round 2." in render_state(env, actor)


@pytest.mark.parametrize("players", [2, 3, 4])
def test_window_size_equals_players_minus_one(players: int):
    """每人至少行动两次后，轮到谁谁就该看到 P-1 步。"""
    env = make_env(players=players)
    step(env, players * 2)
    actor = env.observe().current_player
    text = render_state(env, actor)
    assert f"Moves since your last turn ({players - 1}):" in text


def test_opponents_are_unlabelled_by_default():
    opponents = render_state(make_env(players=3), 1).split("Other players:")[1].split("Moves since")[0]
    assert "[" not in opponents


def test_opponents_can_be_labelled_by_type():
    text = render_state(
        make_env(players=3),
        1,
        opponents={1: "LLM (gpt-5)", 2: "Euclidean-distance greedy", 3: "graph-distance greedy"},
    )
    opponents = text.split("Other players:")[1].split("Moves since")[0]
    assert "P2 [Euclidean-distance greedy]:" in opponents
    assert "P3 [graph-distance greedy]:" in opponents
    assert "P1 [" not in opponents, "本 agent 自己的身份不该出现"


def test_window_lists_other_players_only():
    """窗口里只该有别人的操作，不该有自己的。"""
    env = make_env(players=3)
    step(env, 5)                       # P1 P2 P3 P1 P2 -> 轮到 P3
    actor = env.observe().current_player
    assert actor == 3
    window = render_state(env, actor).split("Moves since your last turn")[1]
    assert "P1:" in window and "P2:" in window
    assert "P3:" not in window


def conversation() -> list:
    """三个回合的对话。"""
    msgs = [{"role": "system", "content": "S"}]
    for i in (1, 2, 3):
        msgs += [
            {"role": "user", "content": f"u{i}"},
            {"role": "assistant", "content": f"a{i}"},
            {"role": "tool", "content": f"t{i}"},
        ]
    return msgs


def contents(messages: list) -> list:
    return [m["content"] for m in messages]


def test_trim_conversation_unlimited():
    msgs = conversation()
    assert trim_conversation(msgs, -1) is msgs


def test_trim_conversation_zero_means_per_turn():
    """keep_turns=0 = 每回合独立：只剩 system，连自己上一回合都不带。"""
    assert contents(trim_conversation(conversation(), 0)) == ["S"]


def test_trim_conversation_keeps_last_n_turns():
    assert contents(trim_conversation(conversation(), 1)) == ["S", "u3", "a3", "t3"]
    assert contents(trim_conversation(conversation(), 2)) == ["S", "u2", "a2", "t2", "u3", "a3", "t3"]


def test_trim_conversation_never_splits_a_turn():
    """截断必须整回合切，否则会出现「有 tool_calls 却没有 tool 结果」的非法对话。"""
    for keep in (0, 1, 2):
        trimmed = trim_conversation(conversation(), keep)
        assert trimmed[0]["role"] == "system"
        for message in trimmed[1:]:
            assert message["role"] in ("user", "assistant", "tool")


def test_window_matches_action_history():
    """窗口内容必须与 action_history 的尾部逐条对应。"""
    env = make_env(players=3)
    step(env, 8)
    state = env.state_dict()
    history = state["actions"]
    actor = env.observe().current_player
    last_own = max(i for i, a in enumerate(history) if a["player"] == actor)
    expected = history[last_own + 1:]

    text = render_state(env, actor)
    window = text.split("Moves since your last turn")[1]
    for action in expected:
        start = tuple(action["path"][0])
        end = tuple(action["path"][-1])
        assert f"P{action['player']}: ({start[0]},{start[1]},{start[2]})" in window
        assert f"({end[0]},{end[1]},{end[2]})" in window
