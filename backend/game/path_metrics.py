"""路径度量（Path Metrics）。

术语约定（全项目统一）：

- action：一次玩家操作，对应一条合法路径 / 一条历史记录。
- step：一条 action 路径中的一次移动，即 path[i] -> path[i+1]。
- step_count：一条 action 中包含多少个 step。
- straight_distance：action 起点到终点的直线距离（欧氏距离）。
- path_distance：沿 action 实际路径累计移动的总距离。
- step_distances：每个 step 的移动距离明细。

这里只提供计算工具，不修改游戏规则。外部 AI / 训练代码可以自行决定
使用哪些字段。
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence

Point = Sequence[int]


def step_count(path: Sequence[Point]) -> int:
    """返回一条 action 路径中的 step 数量。"""
    return max(0, len(path) - 1)


def step_distances(path: Sequence[Point]) -> List[float]:
    """返回每个 step 的实际位移长度。"""
    return [
        math.dist(tuple(path[i]), tuple(path[i + 1]))
        for i in range(len(path) - 1)
    ]


def straight_distance(path: Sequence[Point]) -> float:
    """返回 action 起点到终点的直线距离。"""
    if len(path) < 2:
        return 0.0
    return math.dist(tuple(path[0]), tuple(path[-1]))


def path_distance(path: Sequence[Point]) -> float:
    """返回沿 action 实际路径累计移动的总距离。"""
    return float(sum(step_distances(path)))


def path_metrics(path: Sequence[Point]) -> Dict[str, object]:
    """返回一个 action 的完整路径度量。"""
    return {
        "step_count": step_count(path),
        "straight_distance": round(straight_distance(path), 6),
        "path_distance": round(path_distance(path), 6),
        "step_distances": [round(d, 6) for d in step_distances(path)],
    }


def summarize_actions(history: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """从历史记录汇总 action / step / 距离统计。

    历史中的每个 action 应包含 path_metrics 写入的字段。
    """
    total_steps = 0
    total_straight_distance = 0.0
    total_path_distance = 0.0
    players: Dict[str, Dict[str, float]] = {}

    for action in history:
        player = str(action.get("player", ""))
        player_metrics = players.setdefault(
            player,
            {
                "action_count": 0,
                "step_count": 0,
                "straight_distance": 0.0,
                "path_distance": 0.0,
            },
        )
        player_metrics["action_count"] += 1
        steps = int(action.get("step_count", 0))
        straight = float(action.get("straight_distance", 0.0))
        path = float(action.get("path_distance", 0.0))
        player_metrics["step_count"] += steps
        player_metrics["straight_distance"] += straight
        player_metrics["path_distance"] += path
        total_steps += steps
        total_straight_distance += straight
        total_path_distance += path

    return {
        "action_count": len(history),
        "total_steps": total_steps,
        "total_straight_distance": round(total_straight_distance, 6),
        "total_path_distance": round(total_path_distance, 6),
        "players": {
            pid: {
                "action_count": int(metrics["action_count"]),
                "step_count": int(metrics["step_count"]),
                "straight_distance": round(float(metrics["straight_distance"]), 6),
                "path_distance": round(float(metrics["path_distance"]), 6),
            }
            for pid, metrics in sorted(players.items())
        },
    }


__all__ = [
    "step_count",
    "step_distances",
    "straight_distance",
    "path_distance",
    "path_metrics",
    "summarize_actions",
]
