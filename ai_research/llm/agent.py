"""LLM Agent：把 DeepSeek 接成 PolyJump 的一个玩家（方案 A：工具查询式）。

一回合的流程：
    渲染紧凑状态 -> 模型调用 get_moves（可多枚）-> 回传结果 -> 模型调用 move -> 执行

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

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "v1.md"


def render_state(env: GameEnv, player: int) -> str:
    """紧凑状态块：己方棋子、对方棋子、目标区、双方各自进度。

    注意：`Your progress` 与 `Opponent progress` 必须都是"棋子进入**自己**目标区"的数量，
    否则会被误读成双方进度对比（见 docs/15-llm-state-render-issue.md）。
    敌方棋子占用我方目标区的数量单独一行，标签必须明确。
    """
    sd = env.state_dict()
    opponent = 3 - player
    pieces: Dict[int, List[tuple]] = {}
    for pos_key, owner in sd["pieces"].items():
        pieces.setdefault(int(owner), []).append(tuple(int(v) for v in pos_key.split(",")))
    mine = sorted(pieces.get(player, []))
    theirs = sorted(pieces.get(opponent, []))

    def target_cells(owner: int) -> set:
        return {tuple(int(v) for v in p) for p in sd["targets"][str(owner)]}

    my_target = target_cells(player)
    opp_target = target_cells(opponent)
    my_inside = sum(1 for p in mine if p in my_target)
    opp_inside = sum(1 for p in theirs if p in opp_target)
    blocking = sum(1 for p in theirs if p in my_target)

    def fmt(points) -> str:
        return " ".join(f"({x},{y},{z})" for x, y, z in points)

    return (
        f"You are P{player}. Goal: fill ALL {len(my_target)} cells of your target region.\n"
        f"Your pieces ({len(mine)}): {fmt(mine)}\n"
        f"Opponent pieces ({len(theirs)}): {fmt(theirs)}\n"
        f"Your target region ({len(my_target)} cells): {fmt(sorted(my_target))}\n"
        f"Your progress: {my_inside}/{len(my_target)} of your pieces are in your target region.\n"
        f"Opponent progress: {opp_inside}/{len(opp_target)} of their pieces are in their target region "
        f"(their target is your starting corner).\n"
        f"Enemy pieces currently occupying YOUR target region: {blocking}.\n"
        f"Round {sd['round']}."
    )


class LLMAgent(Agent):
    """把 LLM 当成一个 PolyJump 玩家。"""

    def __init__(
        self,
        model: str = "deepseek-flash",
        *,
        effort: str = "max",
        max_rounds: int = 3,
        budget: Optional[Budget] = None,
        log_dir: Optional[Path] = None,
    ):
        self.model = model
        self.effort = effort
        self.max_rounds = max_rounds
        self.budget = budget or Budget()
        self.log_dir = Path(log_dir) if log_dir else None
        self.slug = f"llm:{model}"
        self.display_name = f"LLM·{model}"
        self._client = DeepSeekClient(model=model, budget=self.budget)
        self._prompt = PROMPT_PATH.read_text(encoding="utf-8").format(max_rounds=max_rounds)
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

    # ------------------------------------------------------------------ 主流程
    def choose(self, env: GameEnv) -> Optional[list]:
        obs = env.observe()
        player = obs.current_player
        legal = obs.legal_actions
        state_block = render_state(env, player)
        log_path = self._log_path(env, player)

        self._turn += 1
        turn = self._turn
        messages: List[dict] = [
            {"role": "system", "content": self._prompt},
            {"role": "user", "content": state_block + "\n\n现在轮到你走。先查询棋子，再用 move 执行。"},
        ]

        chosen: Optional[dict] = None
        turn_started = time.time()
        calls: List[dict] = []

        for rnd in range(1, self.max_rounds + 1):
            last_round = rnd == self.max_rounds
            try:
                resp = self._client.chat(messages, tools=TOOL_SCHEMAS, effort=self.effort)
            except BudgetExceeded:
                self._append(log_path, {
                    "kind": "budget_exceeded", "turn": turn, "player": player,
                    "round": rnd, "state_block": state_block,
                    "budget": self.budget.summary(),
                })
                raise

            call_record = {
                "kind": "call",
                "game_id": env.state_dict().get("game_id"),
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
            messages.append(assistant_msg)

            if not resp.tool_calls:
                # 模型没调工具，只说话：追加提醒，继续下一轮
                call_record["note"] = "模型未调用工具"
                calls.append(call_record)
                self._append(log_path, call_record)
                messages.append({
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
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": text})
                if action is not None:
                    chosen = action

            calls.append(call_record)
            self._append(log_path, call_record)

            if chosen is not None:
                break

            if last_round:
                break
            messages.append({
                "role": "user",
                "content": "还没看到你的 move。请在下一步用 move 执行一个合法走法。",
            })

        self._append(log_path, {
            "kind": "turn_summary",
            "game_id": env.state_dict().get("game_id"),
            "turn": turn,
            "player": player,
            "state_block": state_block,
            "chosen_path": chosen["path"] if chosen else None,
            "chosen_step_count": chosen["step_count"] if chosen else None,
            "rounds": len(calls),
            "turn_latency_s": round(time.time() - turn_started, 3),
            "turn_cost_cny": round(sum(c["cost_cny"] for c in calls), 6),
            "cumulative_cost_cny": round(self.budget.spent_cny, 6),
        })

        if chosen is None:
            return None
        return [[int(v) for v in point] for point in chosen["path"]]
