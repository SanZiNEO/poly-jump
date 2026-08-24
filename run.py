"""PolyJump 一键启动脚本。

用法：
    python run.py

自动：
1. 启动 uvicorn 后端服务
2. 等待服务就绪
3. 打开浏览器访问游戏页面
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def main() -> int:
    print("正在启动 PolyJump 三维跳棋...")
    print(f"服务地址：{URL}")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=ROOT,
    )

    # 等待服务启动后再打开浏览器
    time.sleep(1.5)
    webbrowser.open(URL)

    print("按 Ctrl+C 停止服务")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("服务已停止。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
