"""DeepSeek API 冒烟测试：验证鉴权 / 模型 / 思考模式 / 用量统计。

用法（项目根目录）：
    .poly_jump\\Scripts\\python.exe tools/deepseek_smoke.py
    .poly_jump\\Scripts\\python.exe tools/deepseek_smoke.py --effort none
    .poly_jump\\Scripts\\python.exe tools/deepseek_smoke.py --model deepseek-v4-pro

密钥从环境变量 DEEPSEEK_API_KEY 读取（根目录 .env 会被自动加载），不会打印。
原始响应落到 ai_research/logs/（已 gitignore）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402

BASE_URL = "https://api.deepseek.com"
LOG_DIR = ROOT / "ai_research" / "logs"


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek API 冒烟测试")
    parser.add_argument("--model", default="deepseek-flash")
    parser.add_argument("--effort", default="max", choices=["none", "low", "high", "max"])
    parser.add_argument("--prompt", default="用一句话说明什么是 3D 跳棋。")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("未配置 DEEPSEEK_API_KEY，请检查根目录 .env")
        return 1

    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    t0 = time.time()
    resp = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": args.prompt},
        ],
        reasoning_effort=args.effort,
    )
    elapsed = time.time() - t0

    choice = resp.choices[0]
    msg = choice.message
    usage = resp.usage
    reasoning = getattr(msg, "reasoning_content", None)

    print(f"model      : {resp.model}")
    print(f"effort     : {args.effort}")
    print(f"finish     : {choice.finish_reason}")
    print(f"latency    : {elapsed:.2f} s")
    print(f"content    : {msg.content}")
    if reasoning:
        head = reasoning[:300] + ("..." if len(reasoning) > 300 else "")
        print(f"reasoning  : {head}")
    print(f"usage      : {json.dumps(usage.model_dump(), ensure_ascii=False)}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / f"smoke_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(resp.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"raw saved  : {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
