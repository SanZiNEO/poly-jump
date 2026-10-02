"""LLM Agent 的工具定义与调度。

工具只有两个：
- get_moves(pieces)  查询若干棋子的全部合法落点
- move(piece, to)    执行一步

调度函数不依赖 LLM，纯函数：给定合法动作列表即可执行。
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Point = Tuple[int, int, int]


def _as_point(value: Any) -> Optional[Point]:
    """把 [x, y, z] 解析成 (x, y, z)，非法返回 None。"""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            return (int(value[0]), int(value[1]), int(value[2]))
        except (TypeError, ValueError):
            return None
    return None


def _fmt(points: Sequence[Point]) -> str:
    return " ".join(f"({x},{y},{z})" for x, y, z in points)


def _fmt_single(point: Point) -> str:
    return f"({point[0]},{point[1]},{point[2]})"


TOOL_SCHEMAS: List[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_board",
            "description": (
                "返回完整棋盘：你的全部棋子、你的目标区、每个对手的棋子与各自进度。"
                "增量模式下不会每回合提供棋盘，需要确认局面时调用它。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_moves",
            "description": (
                "查询若干枚棋子的全部合法落点（含单步、跳、连跳）。"
                "返回每枚棋子的落点列表；一个落点唯一对应一条路径。"
                "一次可以查询多枚棋子。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pieces": {
                        "type": "array",
                        "description": "要查询的棋子坐标列表，例如 [[0,0,0],[1,1,1]]",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 3,
                            "maxItems": 3,
                        },
                    }
                },
                "required": ["pieces"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move",
            "description": "把一枚棋子移动到某个落点。落点必须来自 get_moves 的结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "piece": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "棋子坐标 [x, y, z]",
                    },
                    "to": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "目标落点 [x, y, z]",
                    },
                },
                "required": ["piece", "to"],
            },
        },
    },
]


def parse_arguments(raw: str) -> Dict[str, Any]:
    """解析工具入参；模型偶尔产出非法 JSON，这里做一次容错。"""
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def destinations_by_piece(legal_actions: List[dict]) -> Dict[Point, List[Point]]:
    """按棋子分组落点。"""
    grouped: Dict[Point, List[Point]] = {}
    for action in legal_actions:
        path = action["path"]
        start = tuple(int(v) for v in path[0])
        end = tuple(int(v) for v in path[-1])
        grouped.setdefault(start, [])
        if end not in grouped[start]:
            grouped[start].append(end)
    return grouped


def execute_tool(
    name: str,
    args: Dict[str, Any],
    legal_actions: List[dict],
    board_provider: Optional[Callable[[], str]] = None,
) -> Tuple[str, Optional[dict]]:
    """执行一次工具调用。

    返回 (回给模型的文本, 选中的 action 或 None)。
    选中的 action 是 runner 的 action dict（含 id / path / step_count）。

    `board_provider` 供 `get_board` 使用：返回完整棋盘的文本。
    """
    if name == "get_board":
        if board_provider is None:
            return "完整棋盘不可用", None
        return board_provider(), None

    if name == "get_moves":
        raw_pieces = args.get("pieces")
        if isinstance(raw_pieces, (list, tuple)) and len(raw_pieces) == 3 and all(
            isinstance(v, (int, float)) for v in raw_pieces
        ):
            raw_pieces = [raw_pieces]  # 容错：模型传了单个坐标
        if not isinstance(raw_pieces, (list, tuple)):
            return "参数错误：pieces 必须是坐标列表", None

        grouped = destinations_by_piece(legal_actions)
        lines: List[str] = []
        for raw in raw_pieces[:32]:  # 单次最多 32 枚，防止刷查询
            point = _as_point(raw)
            if point is None:
                lines.append(f"{raw}: 坐标非法")
                continue
            dests = grouped.get(point)
            if dests is None:
                lines.append(f"{_fmt_single(point)}: 这不是你的棋子（或当前不可移动）")
            elif not dests:
                lines.append(f"{_fmt_single(point)}: 没有合法落点")
            else:
                lines.append(f"{_fmt_single(point)} -> {_fmt(dests)}")
        return "\n".join(lines) if lines else "没有查询到任何棋子", None

    if name == "move":
        piece = _as_point(args.get("piece"))
        to = _as_point(args.get("to"))
        if piece is None or to is None:
            return "参数错误：piece / to 必须是 [x, y, z]", None
        for action in legal_actions:
            path = action["path"]
            if tuple(int(v) for v in path[0]) == piece and tuple(int(v) for v in path[-1]) == to:
                return f"执行成功：{_fmt_single(piece)} -> {_fmt_single(to)}", action
        return f"非法：{_fmt_single(piece)} 不能走到 {_fmt_single(to)}", None

    return f"未知工具：{name}", None
