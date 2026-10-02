"""DeepSeek 工具调用冒烟测试：用真实 PolyJump 局面跑一个回合。

验证：
- 思考模式（reasoning_effort=max）下的 function calling 是否可用
- 工具定义 → 模型调用 → 结果回传 → 模型最终决策 的完整链路
- PolyJump 状态序列化格式模型能不能读懂

用法（项目根目录）：
    .poly_jump\\Scripts\\python.exe tools/deepseek_game_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402

from backend.game.env import GameEnv  # noqa: E402
from ai_research.runner import make_a_config  # noqa: E402
from ai_research.llm.agent import render_state  # noqa: E402

BASE_URL = "https://api.deepseek.com"
LOG_DIR = ROOT / "ai_research" / "logs"
MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """你在玩 PolyJump，一种 3D 跳棋。你的目标：把你全部棋子搬进对方目标区（目标区全部格子被你的棋子占满即获胜）。

规则：
- 每回合你只能移动一枚自己的棋子。
- 棋子可以走到相邻格（单步），也可以跳过相邻的棋子落到其后的空格（跳），连跳可以一直进行到无法继续。
- 落点必须在棋盘内且为空。

你的回合流程：
1. 用 get_moves 查询某枚棋子的全部合法落点（可以查多枚）。
2. 用 move 执行其中一步。

坐标是三维整数 (x, y, z)。"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_moves",
            "description": "查询指定棋子的全部合法落点（含连跳）。返回落点列表，每个落点对应唯一路径。",
            "parameters": {
                "type": "object",
                "properties": {
                    "piece": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "棋子坐标 [x, y, z]",
                    }
                },
                "required": ["piece"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move",
            "description": "把指定棋子移动到某个落点。落点必须来自 get_moves 的结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "piece": {"type": "array", "items": {"type": "integer"}},
                    "to": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["piece", "to"],
            },
        },
    },
]


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("未配置 DEEPSEEK_API_KEY")
        return 1

    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    env = GameEnv(make_a_config(2, (9, 9, 9), [6, 12, 8], 0))
    env.reset()
    legal = env.observe().legal_actions

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": render_state(env, 1) + "\n\n现在轮到你走。先查询你想移动的棋子，再执行 move。"},
    ]

    print("=" * 70)
    print(render_state(env, 1))
    print("=" * 70)

    transcript = []
    usage_total = {"prompt": 0, "completion": 0, "reasoning": 0, "cache_hit": 0, "cache_miss": 0}
    t_start = time.time()
    chosen = None

    for rnd in range(1, MAX_TOOL_ROUNDS + 1):
        t0 = time.time()
        resp = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=TOOLS,
            reasoning_effort="max",
        )
        dt = time.time() - t0
        msg = resp.choices[0].message
        u = resp.usage
        usage_total["prompt"] += u.prompt_tokens
        usage_total["completion"] += u.completion_tokens
        usage_total["reasoning"] += (u.completion_tokens_details.reasoning_tokens or 0)
        usage_total["cache_hit"] += (u.prompt_cache_hit_tokens or 0)
        usage_total["cache_miss"] += (u.prompt_cache_miss_tokens or 0)

        reasoning = getattr(msg, "reasoning_content", None) or ""
        print(f"\n--- round {rnd} | {dt:.1f}s | finish={resp.choices[0].finish_reason} "
              f"| in={u.prompt_tokens} out={u.completion_tokens} (think={u.completion_tokens_details.reasoning_tokens})")
        if reasoning:
            print(f"[思考] {reasoning[:400]}")
        if msg.content:
            print(f"[文本] {msg.content}")

        messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls} if msg.tool_calls
                        else {"role": "assistant", "content": msg.content})
        transcript.append({"round": rnd, "reasoning": reasoning, "content": msg.content,
                           "tool_calls": [tc.model_dump() for tc in (msg.tool_calls or [])],
                           "usage": u.model_dump(), "latency": dt})

        if not msg.tool_calls:
            print("[!] 模型没有调用工具，直接输出了文本")
            break

        done = False
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            print(f"[调用] {name}({json.dumps(args, ensure_ascii=False)})")

            if name == "get_moves":
                piece = tuple(args.get("piece", []))
                moves = [a for a in legal if tuple(a["path"][0]) == piece]
                dests = sorted({tuple(a["path"][-1]) for a in moves})
                result = ("落点: " + " ".join(f"({x},{y},{z})" for x, y, z in dests)) if dests else "该棋子没有合法落点"
            elif name == "move":
                piece = tuple(args.get("piece", []))
                to = tuple(args.get("to", []))
                match = [a for a in legal if tuple(a["path"][0]) == piece and tuple(a["path"][-1]) == to]
                if match:
                    chosen = match[0]
                    result = f"执行成功：{piece} -> {to}"
                    done = True
                else:
                    result = f"非法：棋子 {piece} 不能走到 {to}"
            else:
                result = f"未知工具 {name}"

            print(f"[结果] {result}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            transcript[-1]["tool_results"] = transcript[-1].get("tool_results", []) + [result]

        if done:
            break

    print("\n" + "=" * 70)
    print(f"总耗时 {time.time() - t_start:.1f}s")
    print("累计用量:", json.dumps(usage_total, ensure_ascii=False))
    if chosen:
        print(f"最终选择: {chosen['path'][0]} -> {chosen['path'][-1]}  (step_count={chosen['step_count']})")
        env.execute_action(chosen["id"])
        print("已应用到环境，新状态：")
        print(render_state(env, 1))
    else:
        print("未产出合法动作")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / f"game_smoke_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"transcript": transcript, "usage_total": usage_total,
                               "chosen": chosen}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完整记录: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
