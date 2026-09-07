"""跨几何模型初步发现实验。

目标：用固定种子、重复对局和路径指标，验证：
- 同一 AI 在不同几何模型（A/B/C/D）上的路径选择存在差异；
- B/C 模型中 MCTS 更容易出现长链（detour 较高）；
- A/D 模型中 MCTS 更容易选择较短路径。

这只是一个“站得住脚的初步发现”，不是深度学术研究。
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from statistics import mean, pstdev

from backend.game.config import (
    CaptureConfig,
    GoalConfig,
    HopMode,
    InitialLayoutConfig,
    MovementConfig,
    PolyJumpConfig,
    ScoringConfig,
)
from backend.game.env import GameEnv
from .agents.chebyshev_ai import ChebyshevAgent
from .agents.euclidean_ai import EuclideanAgent
from .agents.graph_bfs_ai import GraphBFSAgent
from .agents.mcts_ai import MCTSAgent
from .agents.random_ai import RandomAgent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

AGENTS = {
    "random": lambda: RandomAgent(),
    "euclidean": lambda: EuclideanAgent(),
    "chebyshev": lambda: ChebyshevAgent(),
    "graph_bfs": lambda: GraphBFSAgent(),
    "mcts": lambda sims: MCTSAgent(simulations=sims, max_depth=30),
}

AGENT_ORDER = ["random", "euclidean", "chebyshev", "graph_bfs", "mcts"]


def make_config(geometry: str) -> PolyJumpConfig:
    movement = MovementConfig(
        allow_single_move=True,
        allow_jump=True,
        allow_chain=True,
        hop_mode=HopMode.FREE_STOP,
    )
    capture = CaptureConfig(mode="NONE")
    goal = GoalConfig(
        objective="FILL_TARGET",
        target_region="OPPOSITE_CORNER",
        must_fill_all_cells=True,
        allow_pass_through_enemy=True,
        allow_stay_in_enemy=False,
        first_to_finish_wins=True,
    )
    scoring = ScoringConfig(enabled=False)

    if geometry == "A":
        return PolyJumpConfig(
            geometry="A",
            board_size=(9, 9, 9),
            players=2,
            direction_set=[6, 12, 8],
            movement=movement,
            capture=capture,
            goal=goal,
            scoring=scoring,
        )
    if geometry == "B":
        return PolyJumpConfig(
            geometry="B",
            b_radius=6,
            players=2,
            movement=movement,
            capture=capture,
            goal=goal,
            scoring=scoring,
        )
    if geometry == "C":
        return PolyJumpConfig(
            geometry="C",
            c_radius=6,
            players=2,
            movement=movement,
            capture=capture,
            goal=goal,
            scoring=scoring,
        )
    return PolyJumpConfig(
        geometry="D",
        ep_side=5,
        players=2,
        movement=movement,
        capture=capture,
        goal=goal,
        scoring=scoring,
    )


def make_agent(slug: str, mcts_sims: int):
    if slug == "mcts":
        return AGENTS["mcts"](mcts_sims)
    return AGENTS[slug]()


def play_once(
    cfg: PolyJumpConfig,
    agent_slug: str,
    agent_side: int,
    max_actions: int,
    mcts_sims: int,
    seed: int,
) -> dict:
    random.seed(seed)
    env = GameEnv(cfg)
    env.reset()
    agent = make_agent(agent_slug, mcts_sims)
    opponent = RandomAgent()

    while True:
        obs = env.observe()
        if obs.done or obs.action_count >= max_actions:
            break
        if obs.current_player == agent_side:
            action = agent.choose(env)
        else:
            action = opponent.choose(env)
        if action is None:
            legal = env.legal_actions()
            if not legal:
                break
            action = legal[0]
        env.execute_action(action)

    return env.state_dict()


def collect_agent_metrics(state: dict, agent_side: int) -> dict:
    actions = 0
    steps = 0
    path = 0.0
    straight = 0.0
    for act in state.get("actions", []):
        if act["player"] != agent_side:
            continue
        actions += 1
        steps += act.get("step_count", 0)
        path += act.get("path_distance", 0.0)
        straight += act.get("straight_distance", 0.0)
    return {
        "actions": actions,
        "steps": steps,
        "path": path,
        "straight": straight,
        "detour": path / straight if straight else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PolyJump 跨模型初步发现")
    parser.add_argument("--games", type=int, default=2)
    parser.add_argument("--max-actions", type=int, default=6)
    parser.add_argument("--mcts-simulations", type=int, default=5)
    parser.add_argument("--seeds", type=int, default=2000)
    args = parser.parse_args()

    models = ["A", "B", "C", "D"]
    results = {}

    for model in models:
        cfg = make_config(model)
        for agent_slug in AGENT_ORDER:
            samples = []
            for game_idx in range(args.games):
                for side in (1, 2):
                    seed = args.seeds + game_idx * 10 + side
                    state = play_once(
                        cfg,
                        agent_slug,
                        side,
                        args.max_actions,
                        args.mcts_simulations,
                        seed,
                    )
                    metrics = collect_agent_metrics(state, side)
                    samples.append(metrics)

            steps_values = [s["steps"] for s in samples]
            path_values = [s["path"] for s in samples]
            straight_values = [s["straight"] for s in samples]
            detour_values = [s["detour"] for s in samples]
            results[(model, agent_slug)] = {
                "games": len(samples),
                "mean_steps": mean(steps_values),
                "std_steps": pstdev(steps_values) if len(steps_values) > 1 else 0.0,
                "mean_path": mean(path_values),
                "std_path": pstdev(path_values) if len(path_values) > 1 else 0.0,
                "mean_straight": mean(straight_values),
                "mean_detour": mean(detour_values),
                "std_detour": pstdev(detour_values) if len(detour_values) > 1 else 0.0,
            }

    print("# PolyJump 跨几何初步发现")
    print()
    print("| 模型 | agent | 局数 | 平均 steps | 平均 path | 平均 straight | 平均 detour | detour std |")
    print("|---|---|---|---|---|---|---|---|")
    for model in models:
        for slug in AGENT_ORDER:
            r = results[(model, slug)]
            print(
                f"| {model} | {slug} | {r['games']} "
                f"| {r['mean_steps']:.2f} | {r['mean_path']:.2f} "
                f"| {r['mean_straight']:.2f} | {r['mean_detour']:.2f} "
                f"| {r['std_detour']:.2f} |"
            )

    print()
    print("## 关键观察")
    mcts_detour = {model: results[(model, "mcts")]["mean_detour"] for model in models}
    heur_detour = {
        model: sum(results[(model, a)]["mean_detour"] for a in ("euclidean", "chebyshev", "graph_bfs")) / 3
        for model in models
    }
    for model in models:
        diff = mcts_detour[model] - heur_detour[model]
        print(f"- {model}: MCTS detour={mcts_detour[model]:.2f}, 启发式平均={heur_detour[model]:.2f}, 差值={diff:+.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
