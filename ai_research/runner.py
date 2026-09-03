"""PolyJump AI 基准评测运行器（纯后端）。

用法（在项目根目录）：
    .poly_jump\\Scripts\\python.exe -m ai_research.runner --games 10 --radius 6

输出：
    ai_research/runs/<时间戳>/
      experiment.json      实验配置快照
      matches/*.json       每局完整对局记录
      metrics.json         聚合指标
      curves.csv           基础性能表
      summary.md           人类可读总结
      learning_curves/     预留给学习曲线图
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Type

# Windows 控制台默认编码可能不是 UTF-8，这里强制统一，避免中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backend.game.config import (
    CaptureConfig,
    CaptureMode,
    GoalConfig,
    HopMode,
    InitialLayoutConfig,
    MovementConfig,
    PolyJumpConfig,
    ScoringConfig,
)
from backend.game.env import GameEnv

from .agents.base import Agent, get_targets
from .agents.random_ai import RandomAgent
from .agents.manhattan_ai import ManhattanAgent
from .agents.euclidean_ai import EuclideanAgent
from .agents.chebyshev_ai import ChebyshevAgent
from .agents.graph_bfs_ai import GraphBFSAgent
from .metrics import aggregate_matches, analyze_match

AGENT_REGISTRY: Dict[str, Type[Agent]] = {
    "random": RandomAgent,
    "manhattan": ManhattanAgent,
    "euclidean": EuclideanAgent,
    "chebyshev": ChebyshevAgent,
    "graph_bfs": GraphBFSAgent,
}

DEFAULT_AGENTS = ",".join(AGENT_REGISTRY.keys())
DEFAULT_OUT = Path(__file__).resolve().parent / "runs"


def make_b_config(radius: int = 6, players: int = 2) -> PolyJumpConfig:
    """B 模型基准：核心跳棋规则、无吃子、无计分。"""
    return PolyJumpConfig(
        game_name=f"PolyJump-B{players}-Benchmark",
        geometry="B",
        b_radius=radius,
        players=players,
        movement=MovementConfig(
            allow_step=True,
            allow_jump=True,
            allow_chain=True,
            hop_mode=HopMode.FREE_STOP,
            two_step_hop=False,
        ),
        capture=CaptureConfig(
            mode=CaptureMode.NONE,
            capture_opponent_only=True,
            mixed_swap=False,
            capture_in_base=False,
        ),
        goal=GoalConfig(
            objective="FILL_TARGET",
            target_region="OPPOSITE_CORNER",
            must_fill_all_cells=True,
            allow_pass_through_enemy=True,
            allow_stay_in_enemy=False,
            first_to_finish_wins=True,
        ),
        scoring=ScoringConfig(enabled=False),
    )


def make_a_config(
    players: int = 2,
    size: tuple = (9, 9, 9),
    direction_set: Optional[List[int]] = None,
    layers: int = 0,
) -> PolyJumpConfig:
    """A 模型基准：标准 XYZ 网格、核心跳棋规则、无吃子、无计分。"""
    if direction_set is None:
        direction_set = [6, 12, 8]
    if layers <= 0:
        layers = max(2, min(size) // 2)
    return PolyJumpConfig(
        game_name=f"PolyJump-A{players}-Benchmark",
        geometry="A",
        board_size=size,
        players=players,
        direction_set=direction_set,
        initial_layout=InitialLayoutConfig(
            shape="TETRA_PYRAMID",
            layers=layers,
        ),
        movement=MovementConfig(
            allow_step=True,
            allow_jump=True,
            allow_chain=True,
            hop_mode=HopMode.FREE_STOP,
            two_step_hop=False,
        ),
        capture=CaptureConfig(
            mode=CaptureMode.NONE,
            capture_opponent_only=True,
            mixed_swap=False,
            capture_in_base=False,
        ),
        goal=GoalConfig(
            objective="FILL_TARGET",
            target_region="OPPOSITE_CORNER",
            must_fill_all_cells=True,
            allow_pass_through_enemy=True,
            allow_stay_in_enemy=False,
            first_to_finish_wins=True,
        ),
        scoring=ScoringConfig(enabled=False),
    )


def build_config(args: argparse.Namespace) -> PolyJumpConfig:
    """根据 CLI 参数生成评测配置。"""
    if args.geometry == "A":
        size = tuple(int(v) for v in args.size.split(","))
        direction_set = None
        if args.direction_set:
            direction_set = [int(v.strip()) for v in args.direction_set.split(",") if v.strip()]
        return make_a_config(
            players=args.players,
            size=size,
            direction_set=direction_set,
            layers=args.layers,
        )
    if args.players == 8:
        print("B 模型不支持 8 人局，请改用 A 模型或 2/3/4/6 人")
        raise SystemExit(1)
    return make_b_config(args.radius, args.players)


def play_one_game(
    env: GameEnv,
    agents: Dict[int, Agent],
    max_steps: int,
) -> dict:
    """用 GameEnv 跑一局，返回本局 analyze_match 结果 + player_agent。"""
    while True:
        obs = env.observe()
        if obs.done:
            break
        if obs.step_count >= max_steps:
            break

        player = obs.current_player
        agent = agents[player]
        move = agent.choose(env)
        if move is None:
            legal = env.legal_moves()
            if not legal:
                break
            move = legal[0]
        env.step(move)

    state = env.state_dict()
    targets = get_targets(state)
    match = analyze_match(env, targets)
    match["player_agent"] = {p: a.slug for p, a in agents.items()}
    return match


def build_summary_markdown(summary: dict, agents_info: Dict[str, str]) -> str:
    lines = ["# PolyJump AI 基准评测结果", ""]
    lines.append("## 各 AI 指标")
    lines.append("")
    lines.append("| AI | 胜率 | 场次 | 平均步数 | 平均终局进目标子数 | 平均离开目标区次数 | 平均穿过目标区次数 | 平均路径长度 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for slug, row in summary["agents"].items():
        lines.append(
            f"| {agents_info.get(slug, slug)} | {row['win_rate']:.2%} | {row['games']} "
            f"| {row['avg_moves']} | {row['avg_final_inside']} "
            f"| {row['avg_left_per_game']} | {row['avg_through_per_game']} | {row['avg_path_length']} |"
        )
    lines.append("")
    if summary["pairs"]:
        lines.append("## 配对结果")
        lines.append("")
        lines.append("| 配对 | A 胜 | B 胜 | 平局 | 平均步数 |")
        lines.append("|---|---|---|---|---|")
        for pair, row in summary["pairs"].items():
            lines.append(
                f"| {pair} | {row['a_wins']} | {row['b_wins']} | {row['draws']} | {row['avg_moves']} |"
            )
        lines.append("")
    else:
        lines.append("## 配对结果")
        lines.append("")
        lines.append("（多人局不生成两两配对表，请看上方各 AI 汇总指标。）")
        lines.append("")
    lines.append("## 说明")
    lines.append("- 计分已关闭，只比“谁先把棋子搬到对方目标区”的效率。")
    lines.append("- `平均离开目标区次数` 越小越好；这正是“进目标区又出来”的问题指标。")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="PolyJump AI 基准评测")
    parser.add_argument("--geometry", default="B", choices=["A", "B"], help="几何模型")
    parser.add_argument("--agents", default=DEFAULT_AGENTS, help="逗号分隔的 agent slug")
    parser.add_argument("--games", type=int, default=10, help="每局组合各跑多少局")
    parser.add_argument("--radius", type=int, default=6, help="B 模型半径 R")
    parser.add_argument("--size", default="9,9,9", help="A 模型棋盘大小 x,y,z")
    parser.add_argument("--layers", type=int, default=0, help="A 模型起始层数；0=按最短边自动")
    parser.add_argument("--direction-set", default="", help="A 模型方向集，逗号分隔，如 6 或 6,12,8")
    parser.add_argument("--players", type=int, default=2, choices=[2, 3, 4, 6, 8], help="玩家人数")
    parser.add_argument("--max-steps", type=int, default=2000, help="单局最大步数")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出根目录")
    args = parser.parse_args()

    agent_slugs = [s.strip() for s in args.agents.split(",") if s.strip()]
    unknown = [s for s in agent_slugs if s not in AGENT_REGISTRY]
    if unknown:
        print(f"未知 agent: {unknown}，可选: {list(AGENT_REGISTRY)}")
        return 1
    if len(agent_slugs) < args.players:
        print(f"玩家人数 {args.players}，但只提供了 {len(agent_slugs)} 个 AI，需要至少 {args.players} 个")
        return 1

    random.seed(args.seed)
    config = build_config(args)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.out / timestamp
    matches_dir = run_dir / "matches"
    curves_dir = run_dir / "learning_curves"
    matches_dir.mkdir(parents=True, exist_ok=True)
    curves_dir.mkdir(parents=True, exist_ok=True)

    # 实验配置快照
    experiment = {
        "timestamp": timestamp,
        "seed": args.seed,
        "config": config.model_dump(),
        "agents": agent_slugs,
        "games_per_pair": args.games,
        "max_steps": args.max_steps,
    }
    with (run_dir / "experiment.json").open("w", encoding="utf-8") as f:
        json.dump(experiment, f, ensure_ascii=False, indent=2)

    matches: List[dict] = []
    agents_info = {slug: AGENT_REGISTRY[slug]().display_name for slug in agent_slugs}

    game_index = 0
    if args.geometry == "A":
        geom_desc = f"A 模型 {args.players} 人，size={args.size}"
    else:
        geom_desc = f"B 模型 {args.players} 人，R={args.radius}"
    if args.players == 2:
        total_pairs = len(agent_slugs) * (len(agent_slugs) - 1) // 2
        total_games = total_pairs * args.games
        print(f"开始评测：{geom_desc}，agent={agent_slugs}")
        print(f"共 {total_pairs} 个配对 × {args.games} 局 = {total_games} 局")

        for i, a_slug in enumerate(agent_slugs):
            for b_slug in agent_slugs[i + 1:]:
                for g in range(args.games):
                    if g % 2 == 0:
                        player_agent_slugs = {1: a_slug, 2: b_slug}
                    else:
                        player_agent_slugs = {1: b_slug, 2: a_slug}

                    env = GameEnv(config)
                    agents = {
                        p: AGENT_REGISTRY[slug]()
                        for p, slug in player_agent_slugs.items()
                    }
                    match = play_one_game(env, agents, args.max_steps)
                    match["player_agent"] = player_agent_slugs

                    game_index += 1
                    match_path = matches_dir / f"game_{game_index:04d}.json"
                    with match_path.open("w", encoding="utf-8") as f:
                        json.dump(match, f, ensure_ascii=False, indent=2)

                    matches.append(match)
                    print(
                        f"[{game_index}/{total_games}] {a_slug} vs {b_slug} "
                        f"(side {player_agent_slugs[1]}/{player_agent_slugs[2]}) "
                        f"winner={match.get('winner')} moves={match.get('moves')}"
                    )
    else:
        combos = list(combinations(agent_slugs, args.players))
        total_games = len(combos) * args.games
        print(f"开始评测：{geom_desc}，agent={agent_slugs}")
        print(f"共 {len(combos)} 个组合 × {args.games} 局 = {total_games} 局")

        for combo in combos:
            for g in range(args.games):
                # 轮转座位：不同局让每个 AI 坐到不同玩家位，减少先后手偏差
                player_agent_slugs = {
                    p + 1: combo[(g + p) % args.players]
                    for p in range(args.players)
                }

                env = GameEnv(config)
                agents = {
                    p: AGENT_REGISTRY[slug]()
                    for p, slug in player_agent_slugs.items()
                }
                match = play_one_game(env, agents, args.max_steps)
                match["player_agent"] = player_agent_slugs

                game_index += 1
                match_path = matches_dir / f"game_{game_index:04d}.json"
                with match_path.open("w", encoding="utf-8") as f:
                    json.dump(match, f, ensure_ascii=False, indent=2)

                matches.append(match)
                lineup = "/".join(player_agent_slugs.values())
                print(
                    f"[{game_index}/{total_games}] {lineup} "
                    f"winner={match.get('winner')} moves={match.get('moves')}"
                )

    summary = aggregate_matches(matches)

    with (run_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with (run_dir / "curves.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "agent", "win_rate", "games", "avg_moves", "avg_final_inside",
            "avg_left_per_game", "avg_through_per_game", "avg_path_length",
        ])
        for slug, row in summary["agents"].items():
            writer.writerow([
                slug, row["win_rate"], row["games"], row["avg_moves"],
                row["avg_final_inside"], row["avg_left_per_game"],
                row["avg_through_per_game"], row["avg_path_length"],
            ])

    summary_text = build_summary_markdown(summary, agents_info)
    with (run_dir / "summary.md").open("w", encoding="utf-8") as f:
        f.write(summary_text)

    print(f"\n完成！输出目录：{run_dir}")
    print(f"汇总写入：{run_dir / 'metrics.json'}")
    print(f"人类可读：{run_dir / 'summary.md'}")
    print("\n你可以打开 summary.md 查看对比结果。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
