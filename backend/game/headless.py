"""PolyJump 纯后端无前端运行入口。

用法：
    python -m backend.game.headless --config configs/a_2p_6dir.json
    python -m backend.game.headless --config configs/a_2p_6dir.json --actions 10

这是游戏的可编程后端接口：通过配置文件启动规则引擎，
不依赖前端；外部程序可以按自己的方式接入。
"""

from __future__ import annotations

import argparse
import sys

from .ai import GraphHeuristicAI
from .config_loader import load_config
from .game_state import GameState
from .serializers import path_to_lists, state_to_dict


def _print_state_summary(state: GameState) -> None:
    board = state.board
    print("== PolyJump Game ==")
    print(f"geometry: {state.config.geometry}")
    print(f"players: {state.config.players}")
    print(f"points: {len(board.points)}")
    print(f"pieces: {len(board.pieces)}")
    print(f"current_player: {state.current_player}")
    print(f"bases: {len(board.player_bases)}")
    print(f"targets: {len(board.player_targets)}")
    print("====================")


def main() -> int:
    parser = argparse.ArgumentParser(description="PolyJump headless runner")
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="JSON 配置文件路径",
    )
    parser.add_argument(
        "--actions",
        "-n",
        type=int,
        default=0,
        help="自动执行多少个 action；0 表示只加载并打印初始局面",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="随机种子（可选）",
    )
    args = parser.parse_args()

    if args.seed is not None:
        import random
        random.seed(args.seed)

    try:
        config = load_config(args.config)
        state = GameState(config)
    except Exception as exc:  # noqa: BLE001 - CLI 错误直接展示
        print(f"配置/初始化失败: {exc}", file=sys.stderr)
        return 1

    _print_state_summary(state)

    ai = GraphHeuristicAI()
    for action_index in range(args.actions):
        if state.winner is not None:
            break
        legal_actions = state.legal_actions()
        if not legal_actions:
            print("当前玩家无合法走法，已跳过/终止")
            break

        action = ai.select_action(state.board, state.current_player, legal_actions)
        ok = state.perform_action(action)
        if not ok:
            print(f"非法 action，终止: {action}")
            return 1

        last_action = state.action_history[-1]
        print(
            f"[action {action_index + 1}] player={last_action['player']} "
            f"action={path_to_lists(action)}"
        )

    print("== Final ==")
    print(f"winner: {state.winner}")
    print(f"actions: {len(state.action_history)}")
    print("state keys:", list(state_to_dict(state).keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
