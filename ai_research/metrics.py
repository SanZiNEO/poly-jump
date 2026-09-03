"""对局指标计算与汇总。

第一阶段指标聚焦“效率”：
- 胜率
- 平均步数 / 回合数
- 目标区进入/离开/穿过统计（针对“AI 进目标区又出来”）
- 终局时已进入目标区的棋子数
- 平均路径长度
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Set, Tuple

from backend.game.env import GameEnv
from .agents.base import Point, get_targets, tuple_point

AgentSlug = str


def analyze_state(
    state: dict,
    targets_by_player: Dict[int, Set[Point]],
) -> dict:
    """分析一局终局/中途状态，返回该局的指标。"""
    history = state.get("history", [])
    players_meta: Dict[int, dict] = {}

    for player in range(1, int(state.get("config", {}).get("players", 2)) + 1):
        target = targets_by_player.get(player, set())
        entered = 0
        left = 0
        through = 0
        path_lengths: List[int] = []
        for move in history:
            if move.get("player") != player:
                continue
            path = move.get("path", [])
            if len(path) < 2:
                continue
            start = tuple_point(path[0])
            end = tuple_point(path[-1])
            path_lengths.append(len(path))
            if start not in target and end in target:
                entered += 1
            elif start in target and end not in target:
                left += 1
            elif start not in target and end not in target and any(
                tuple_point(p) in target for p in path[1:-1]
            ):
                through += 1

        final_inside = 0
        for pos_key, owner in state.get("pieces", {}).items():
            if owner != player:
                continue
            pos = tuple_point([int(v) for v in pos_key.split(",")])
            if pos in target:
                final_inside += 1

        players_meta[player] = {
            "entered": entered,
            "left": left,
            "through": through,
            "final_inside": final_inside,
            "avg_path_length": round(
                sum(path_lengths) / len(path_lengths), 2
            ) if path_lengths else 0.0,
        }

    return {
        "winner": state.get("winner"),
        "moves": len(history),
        "players": players_meta,
    }


def analyze_match(
    env: GameEnv,
    targets_by_player: Dict[int, Set[Point]],
) -> dict:
    """从 GameEnv 当前状态生成一局完整指标。"""
    state = env.state_dict()
    result = analyze_state(state, targets_by_player)
    result["game_id"] = state.get("game_id")
    result["current_player"] = state.get("current_player")
    result["round"] = state.get("round")
    result["step_count"] = state.get("step_count")
    result["history"] = state.get("history", [])
    return result


def aggregate_matches(
    matches: List[dict],
    player_agent: Dict[int, AgentSlug] | None = None,
) -> dict:
    """汇总多局指标。

    matches 是 analyze_match 的结果，另外每个 match 可以带
    `player_agent` 字段 {1: agent_slug, 2: agent_slug}。
    """
    per_agent: Dict[str, dict] = defaultdict(lambda: {
        "games": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "entered": 0,
        "left": 0,
        "through": 0,
        "final_inside_total": 0,
        "path_lengths": [],
        "moves_when_win": [],
        "moves_all": [],
    })
    per_pair: Dict[Tuple[str, str], dict] = defaultdict(lambda: {
        "a_wins": 0,
        "b_wins": 0,
        "draws": 0,
        "moves": [],
    })

    for match in matches:
        agents = match.get("player_agent", {})
        winner = match.get("winner")
        moves = match.get("moves", 0)
        for p, slug in agents.items():
            meta = per_agent[slug]
            meta["games"] += 1
            meta["moves_all"].append(moves)
            if winner == p:
                meta["wins"] += 1
                meta["moves_when_win"].append(moves)
            elif winner is None:
                meta["draws"] += 1
            else:
                meta["losses"] += 1

            pm = match.get("players", {}).get(p, {})
            meta["entered"] += pm.get("entered", 0)
            meta["left"] += pm.get("left", 0)
            meta["through"] += pm.get("through", 0)
            meta["final_inside_total"] += pm.get("final_inside", 0)
            meta["path_lengths"].append(pm.get("avg_path_length", 0.0))

        if len(agents) == 2:
            pair = tuple(sorted(agents.items()))  # [(1,slug),(2,slug)]
            a_slug = pair[0][1]
            b_slug = pair[1][1]
            key = (a_slug, b_slug)
            pp = per_pair[key]
            pp["moves"].append(moves)
            if winner is None:
                pp["draws"] += 1
            else:
                # agents dict value is player -> slug
                if agents.get(winner) == a_slug:
                    pp["a_wins"] += 1
                else:
                    pp["b_wins"] += 1

    summary = {"agents": {}, "pairs": {}}
    for slug, m in per_agent.items():
        games = m["games"]
        wins = m["wins"]
        summary["agents"][slug] = {
            "games": games,
            "wins": wins,
            "losses": m["losses"],
            "draws": m["draws"],
            "win_rate": round(wins / games, 4) if games else 0.0,
            "avg_moves": round(sum(m["moves_all"]) / games, 2) if games else 0.0,
            "avg_moves_when_win": (
                round(sum(m["moves_when_win"]) / len(m["moves_when_win"]), 2)
                if m["moves_when_win"] else 0.0
            ),
            "avg_final_inside": round(m["final_inside_total"] / games, 2) if games else 0.0,
            "avg_left_per_game": round(m["left"] / games, 2) if games else 0.0,
            "avg_through_per_game": round(m["through"] / games, 2) if games else 0.0,
            "total_entered": m["entered"],
            "total_left": m["left"],
            "total_through": m["through"],
            "avg_path_length": round(sum(m["path_lengths"]) / games, 2) if games else 0.0,
        }

    for (a, b), pp in per_pair.items():
        summary["pairs"][f"{a} vs {b}"] = {
            "a": a,
            "b": b,
            "a_wins": pp["a_wins"],
            "b_wins": pp["b_wins"],
            "draws": pp["draws"],
            "avg_moves": round(sum(pp["moves"]) / len(pp["moves"]), 2) if pp["moves"] else 0.0,
        }

    return summary
