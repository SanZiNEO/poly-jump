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

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "v2.md"


def render_state(env: GameEnv, player: int) -> str:
    """紧凑状态块（支持任意人数）。

    四块内容：

    1. 自己的棋子与目标区
    2. **每个对手**的棋子与各自进度（多人局里"谁快赢了"是决策信息）
    3. 各方进度汇总
    4. **自你上次行动以来其他玩家的操作** —— 只看棋盘快照无法判断谁做了什么

    第 4 块的窗口按「玩家身份」切（`history[自己上次行动之后:]`），
    不按回合数算 —— 有玩家无棋可走被跳过时，按数字算会错位。
    """
    state = env.state_dict()
    players = int(state["config"]["players"])

    pieces: Dict[int, List[tuple]] = {}
    for pos_key, owner in state["pieces"].items():
        pieces.setdefault(int(owner), []).append(tuple(int(v) for v in pos_key.split(",")))

    def target_cells(owner: int) -> set:
        return {tuple(int(v) for v in p) for p in state["targets"][str(owner)]}

    targets = {p: target_cells(p) for p in range(1, players + 1)}
    mine = sorted(pieces.get(player, []))
    my_target = targets[player]
    my_inside = sum(1 for p in mine if p in my_target)

    def fmt(points) -> str:
        return " ".join(f"({x},{y},{z})" for x, y, z in points)

    def fmt_point(point) -> str:
        return f"({point[0]},{point[1]},{point[2]})"

    lines = [
        f"You are P{player} of {players} players. "
        # state["round"] 是「上一个动作」所在轮次；这里要显示「即将进行的」轮次
        f"Round {int(state['action_count']) // players + 1}.",
        f"Goal: fill ALL {len(my_target)} cells of your target region with your pieces.",
        f"Your pieces ({len(mine)}): {fmt(mine)}",
        f"Your target region ({len(my_target)} cells): {fmt(sorted(my_target))}",
        f"Your progress: {my_inside}/{len(my_target)} pieces in target.",
        "",
        "Other players:",
    ]
    for other in range(1, players + 1):
        if other == player:
            continue
        theirs = sorted(pieces.get(other, []))
        inside = sum(1 for p in theirs if p in targets[other])
        lines.append(
            f"  P{other}: {inside}/{len(targets[other])} in target | "
            f"pieces ({len(theirs)}): {fmt(theirs)}"
        )

    history = state.get("actions", [])
    last_own = max((i for i, a in enumerate(history) if a.get("player") == player), default=-1)
    recent = history[last_own + 1:]

    lines.append("")
    if not recent:
        lines.append("Moves since your last turn: none — you are first to act this game.")
    else:
        lines.append(f"Moves since your last turn ({len(recent)}):")
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
                f"  P{mover}: {fmt_point(start)} -> {fmt_point(end)}  "
                f"{steps} step{'s' if steps != 1 else ''}{suffix}"
            )

    return "\n".join(lines)


class LLMAgent(Agent):
    """把 LLM 当成一个 PolyJump 玩家（完整对话 + 多人局）。"""

    def __init__(
        self,
        model: str = "deepseek-flash",
        *,
        effort: str = "max",
        max_rounds: int = 3,
        context_turns: int = 0,
        budget: Optional[Budget] = None,
        log_dir: Optional[Path] = None,
    ):
        self.model = model
        self.effort = effort
        self.max_rounds = max_rounds
        self.context_turns = context_turns
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
        """只保留最近 `context_turns` 个回合（0 = 不限）。

        在 user 消息边界处整段截断 —— 不能在回合中间切，
        否则会出现「有 tool_calls 却没有对应 tool 结果」的非法对话。
        """
        if self.context_turns <= 0:
            return
        starts = [i for i, m in enumerate(self._messages) if m.get("role") == "user"]
        if len(starts) <= self.context_turns:
            return
        self._messages = self._messages[:1] + self._messages[starts[-self.context_turns]:]

    # ------------------------------------------------------------------ 主流程
    def choose(self, env: GameEnv) -> Optional[list]:
        obs = env.observe()
        player = obs.current_player
        legal = obs.legal_actions
        state_block = render_state(env, player)
        log_path = self._log_path(env, player)

        self._ensure_conversation(env.state_dict().get("game_id"))
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
                text, action = execute_tool(tc["name"], args, legal)
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

        self._trim_context()

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
