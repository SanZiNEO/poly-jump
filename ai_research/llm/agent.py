"""LLM Agent：把 DeepSeek 接成 PolyJump 的一个玩家。

两个核心设计：

**一、完整对话（不做无状态）**
每个 agent 在一局内维护一条连续的 `messages`，每回合把新的状态块和工具往返
追加进去 —— 模型因此有完整的记忆，而不是每回合从零看一张快照。
`context_turns > 0` 时只保留最近若干回合（在 user 消息边界处截断），
防止长对局撑爆上下文。

**二、多人局支持**
状态块会列出**每个对手**的棋子与各自进度，并给出「自你上次行动以来，
其他玩家做了什么」—— 多人局里只看棋盘快照无法判断谁在威胁谁。

一回合的流程：
    渲染状态 -> 模型 get_moves（可查多枚）-> 回传结果 -> 模型 move -> 执行

所有 API 调用（含思考原文、工具调用、用量、费用、延迟）逐条写入
`<log_dir>/<game_id>_p<player>.jsonl`，一局一个文件。
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from backend.game.env import GameEnv

from ..agents.base import Agent, BudgetExceeded
from .client import Budget, DeepSeekClient
from .tools import TOOL_SCHEMAS, execute_tool, parse_arguments

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system.md"


def _board_facts(env: GameEnv, player: int):
    """把 state_dict 解析成渲染需要的结构。"""
    state = env.state_dict()
    players = int(state["config"]["players"])
    pieces: Dict[int, List[tuple]] = {}
    for pos_key, owner in state["pieces"].items():
        pieces.setdefault(int(owner), []).append(tuple(int(v) for v in pos_key.split(",")))
    targets = {
        p: {tuple(int(v) for v in c) for c in state["targets"][str(p)]}
        for p in range(1, players + 1)
    }
    return state, players, pieces, targets


def _fmt(points) -> str:
    return " ".join(f"({x},{y},{z})" for x, y, z in points)


def render_board(env: GameEnv, player: int, opponents: Optional[Dict[int, str]] = None) -> str:
    """完整棋盘：自己的棋子与目标区 + 每个对手的棋子与进度。

    也作为 `get_board` 工具的返回内容（增量模式下模型主动查询时用）。
    """
    _, players, pieces, targets = _board_facts(env, player)
    mine = sorted(pieces.get(player, []))
    my_target = targets[player]
    my_inside = sum(1 for p in mine if p in my_target)

    lines = [
        f"Your pieces ({len(mine)}): {_fmt(mine)}",
        f"Your target region ({len(my_target)} cells): {_fmt(sorted(my_target))}",
        f"Your progress: {my_inside}/{len(my_target)} pieces in target.",
        "",
        "Other players:",
    ]
    for other in range(1, players + 1):
        if other == player:
            continue
        theirs = sorted(pieces.get(other, []))
        inside = sum(1 for p in theirs if p in targets[other])
        label = f" [{opponents[other]}]" if opponents and other in opponents else ""
        lines.append(
            f"  P{other}{label}: {inside}/{len(targets[other])} in target | "
            f"pieces ({len(theirs)}): {_fmt(theirs)}"
        )
    return "\n".join(lines)


def render_progress(env: GameEnv, player: int) -> str:
    """只给各方进度（增量模式）—— 谁快赢了是每回合都必须知道的信息。"""
    _, players, pieces, targets = _board_facts(env, player)

    def inside(owner: int) -> int:
        return sum(1 for p in pieces.get(owner, []) if p in targets[owner])

    parts = [f"you {inside(player)}/{len(targets[player])}"]
    for other in range(1, players + 1):
        if other != player:
            parts.append(f"P{other} {inside(other)}/{len(targets[other])}")
    return "Progress: " + " | ".join(parts) + " pieces in target."


def render_window(env: GameEnv, player: int) -> str:
    """自你上次行动以来，其他玩家做了什么。

    按**玩家身份**切（`history[自己上次行动之后:]`），不按回合数算 ——
    有玩家无棋可走被跳过时，按数字算会错位。
    """
    state, _, _, targets = _board_facts(env, player)
    history = state.get("actions", [])
    last_own = max((i for i, a in enumerate(history) if a.get("player") == player), default=-1)
    recent = history[last_own + 1:]

    if not recent:
        return "Moves since your last turn: none — you are first to act this game."

    lines = [f"Moves since your last turn ({len(recent)}):"]
    for action in recent:
        path = action.get("path") or []
        if len(path) < 2:
            continue
        mover = int(action["player"])
        start = tuple(int(v) for v in path[0])
        end = tuple(int(v) for v in path[-1])
        steps = len(path) - 1
        tags = []
        if start not in targets.get(mover, set()) and end in targets.get(mover, set()):
            tags.append("entered target")
        if steps > 1:
            tags.append("chain")
        suffix = f"  [{', '.join(tags)}]" if tags else ""
        lines.append(
            f"  P{mover}: ({start[0]},{start[1]},{start[2]}) -> ({end[0]},{end[1]},{end[2]})  "
            f"{steps} step{'s' if steps != 1 else ''}{suffix}"
        )
    return "\n".join(lines)


def render_state(
    env: GameEnv,
    player: int,
    opponents: Optional[Dict[int, str]] = None,
    include_board: bool = True,
) -> str:
    """组装状态块。

    `include_board=False` 走**增量模式**：只给各方进度与变动窗口，
    完整棋盘要靠模型主动调用 `get_board` 工具获取。

    `opponents` 可选：`{玩家号: 描述}`，传入时在每个对手后面标注它是谁。
    **不含本 agent 自己的身份** —— 渲染时本来就会跳过自己。
    """
    state, players, _, targets = _board_facts(env, player)
    round_no = int(state["action_count"]) // players + 1

    lines = [
        f"You are P{player} of {players} players. Round {round_no}.",
        f"Goal: fill ALL {len(targets[player])} cells of your target region with your pieces.",
    ]
    if include_board:
        lines.append(render_board(env, player, opponents))
    else:
        lines.append(render_progress(env, player))
        lines.append("")
        lines.append("(Full board not shown. Call get_board if you need the current position.)")
    lines.append("")
    lines.append(render_window(env, player))
    return "\n".join(lines)


def should_include_board(board_mode: str, messages: List[dict]) -> bool:
    """本回合是否给完整棋盘。

    `full` 模式永远给；`delta` 模式只在**对话还没有任何回合**时给 ——
    无记忆（每回合清空）时因此自然退化为每回合都给。
    """
    if board_mode == "full":
        return True
    return not any(m.get("role") == "user" for m in messages)


def trim_conversation(messages: List[dict], keep_turns: int) -> List[dict]:
    """只保留最近 `keep_turns` 个回合的对话。

    - `keep_turns < 0`：不限，原样返回（完整对话）
    - `keep_turns = 0`：只留 system 消息（每回合独立）
    - `keep_turns > 0`：system + 最近 N 个回合

    必须在 **user 消息边界**整段截断 —— 在回合中间切会出现
    「有 tool_calls 却没有对应 tool 结果」的非法对话，API 会直接报错。
    """
    if keep_turns < 0:
        return messages
    starts = [i for i, m in enumerate(messages) if m.get("role") == "user"]
    if len(starts) <= keep_turns:
        return messages
    if keep_turns == 0:
        return messages[:1]
    return messages[:1] + messages[starts[-keep_turns]:]


class LLMAgent(Agent):
    """把 LLM 当成一个 PolyJump 玩家（完整对话 + 多人局）。

    `context_turns` 控制对话记忆：

    | 值 | 含义 |
    |---|---|
    | `-1`（默认） | 完整对话，不截断 |
    | `0` | 每回合独立（只带 system 提示词） |
    | `N > 0` | 保留最近 N 个回合 |

    裁剪发生在**回合开始时**，且在 user 消息边界整段截断。

    `board_mode` 控制棋盘信息的供给方式：

    | 值 | 含义 |
    |---|---|
    | `"delta"`（默认） | 只在**本对话的第一次**给完整棋盘，之后只给进度与变动窗口；模型需要时自己调 `get_board` |
    | `"full"` | 每回合都给完整棋盘 |

    两个开关互相独立，可自由组合；注意 `delta + context_turns=0` 会退化为每回合都给完整棋盘
    （因为每回合都没有历史可依据）。
    """

    def __init__(
        self,
        model: str = "deepseek-flash",
        *,
        effort: str = "max",
        max_rounds: int = 3,
        context_turns: int = -1,
        board_mode: str = "delta",
        opponents: Optional[Dict[int, str]] = None,
        budget: Optional[Budget] = None,
        log_dir: Optional[Path] = None,
    ):
        self.model = model
        self.effort = effort
        self.max_rounds = max_rounds
        self.context_turns = context_turns
        if board_mode not in ("full", "delta"):
            raise ValueError("board_mode 只支持 full / delta")
        self.board_mode = board_mode
        self.opponents = dict(opponents) if opponents else None
        self.budget = budget or Budget()
        self.log_dir = Path(log_dir) if log_dir else None
        self.slug = f"llm:{model}"
        self.display_name = f"LLM·{model}"
        self._client = DeepSeekClient(model=model, budget=self.budget)
        self._prompt = PROMPT_PATH.read_text(encoding="utf-8").format(max_rounds=max_rounds)
        self._messages: List[dict] = []
        self._game_id: Optional[str] = None
        self._turn = 0

    # ------------------------------------------------------------------ 记录
    def _log_path(self, env: GameEnv, player: int) -> Optional[Path]:
        if self.log_dir is None:
            return None
        game_id = env.state_dict().get("game_id", "unknown")
        return self.log_dir / f"{game_id}_p{player}.jsonl"

    @staticmethod
    def _append(path: Optional[Path], payload: dict) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ 对话
    def _ensure_conversation(self, game_id: Optional[str]) -> None:
        """换局则重开对话；开局第一条永远是 system。"""
        if game_id != self._game_id:
            self._messages = []
            self._game_id = game_id
        if not self._messages:
            self._messages.append({"role": "system", "content": self._prompt})

    def _trim_context(self) -> None:
        """按 `context_turns` 裁剪对话（在回合开始时调用）。"""
        self._messages = trim_conversation(self._messages, self.context_turns)

    # ------------------------------------------------------------------ 主流程
    def choose(self, env: GameEnv) -> Optional[list]:
        obs = env.observe()
        player = obs.current_player
        legal = obs.legal_actions
        log_path = self._log_path(env, player)

        self._ensure_conversation(env.state_dict().get("game_id"))
        self._trim_context()
        # 增量模式：只在「本对话还没有任何回合」时给完整棋盘；
        # 无记忆时每回合都算第一次，自然退化为每回合都给。
        include_board = should_include_board(self.board_mode, self._messages)
        state_block = render_state(env, player, self.opponents, include_board)

        self._turn += 1
        turn = self._turn
        self._messages.append(
            {"role": "user", "content": state_block + "\n\n现在轮到你走。先查询棋子，再用 move 执行。"}
        )

        chosen: Optional[dict] = None
        turn_started = time.time()
        calls: List[dict] = []

        for rnd in range(1, self.max_rounds + 1):
            last_round = rnd == self.max_rounds
            try:
                resp = self._client.chat(self._messages, tools=TOOL_SCHEMAS, effort=self.effort)
            except BudgetExceeded:
                self._append(log_path, {
                    "kind": "budget_exceeded", "turn": turn, "player": player,
                    "round": rnd, "state_block": state_block,
                    "budget": self.budget.summary(),
                })
                raise

            call_record = {
                "kind": "call",
                "game_id": self._game_id,
                "turn": turn,
                "player": player,
                "round": rnd,
                "last_round": last_round,
                "model": self.model,
                "effort": self.effort,
                "state_block": state_block,
                "board_included": include_board,
                "reasoning": resp.reasoning,
                "content": resp.content,
                "finish_reason": resp.finish_reason,
                "latency_s": round(resp.latency_s, 3),
                "context_messages": len(self._messages),
                "context_chars": sum(len(str(m.get("content") or "")) for m in self._messages),
                "usage": {
                    "prompt_tokens": resp.prompt_tokens,
                    "completion_tokens": resp.completion_tokens,
                    "reasoning_tokens": resp.reasoning_tokens,
                    "cache_hit_tokens": resp.cache_hit_tokens,
                    "cache_miss_tokens": resp.cache_miss_tokens,
                },
                "cost_cny": round(resp.cost_cny, 6),
                "cumulative_cost_cny": round(self.budget.spent_cny, 6),
                "peak": resp.peak,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_calls": [],
            }

            assistant_msg: dict = {"role": "assistant", "content": resp.content or ""}
            if resp.tool_calls:
                assistant_msg["tool_calls"] = [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                    for tc in resp.tool_calls
                ]
            self._messages.append(assistant_msg)

            if not resp.tool_calls:
                call_record["note"] = "模型未调用工具"
                calls.append(call_record)
                self._append(log_path, call_record)
                self._messages.append({
                    "role": "user",
                    "content": "请调用工具：先 get_moves 查询，再用 move 执行一步。",
                })
                continue

            for tc in resp.tool_calls:
                args = parse_arguments(tc["arguments"])
                text, action = execute_tool(
                    tc["name"], args, legal,
                    board_provider=lambda: render_board(env, player, self.opponents),
                )
                call_record["tool_calls"].append({
                    "name": tc["name"], "arguments": args, "result": text,
                })
                self._messages.append({"role": "tool", "tool_call_id": tc["id"], "content": text})
                if action is not None:
                    chosen = action

            calls.append(call_record)
            self._append(log_path, call_record)

            if chosen is not None:
                break

            if last_round:
                break
            self._messages.append({
                "role": "user",
                "content": "还没看到你的 move。请在下一步用 move 执行一个合法走法。",
            })

        self._append(log_path, {
            "kind": "turn_summary",
            "game_id": self._game_id,
            "turn": turn,
            "player": player,
            "state_block": state_block,
            "chosen_path": chosen["path"] if chosen else None,
            "chosen_step_count": chosen["step_count"] if chosen else None,
            "rounds": len(calls),
            "turn_latency_s": round(time.time() - turn_started, 3),
            "turn_cost_cny": round(sum(c["cost_cny"] for c in calls), 6),
            "cumulative_cost_cny": round(self.budget.spent_cny, 6),
            "context_messages": len(self._messages),
        })

        if chosen is None:
            return None
        return [[int(v) for v in point] for point in chosen["path"]]
