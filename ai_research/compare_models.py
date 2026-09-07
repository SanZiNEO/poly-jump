"""跨模型小规模对比脚本。

对比 A/B/C/D 四个默认尺寸模型上，random / graph_bfs / MCTS 的行为差异。

指标：
- actions：action 数
- steps：step 数
- path_distance：实际路径距离
- straight_distance：起终点直线距离
- detour：path_distance / straight_distance
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from itertools import combinations

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backend.game.config import (
    CaptureConfig,
    GoalConfig,
    HopMode,
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

AGENTS = {
    "random": lambda: RandomAgent(),
    "euclidean": lambda: EuclideanAgent(),
    "chebyshev": lambda: ChebyshevAgent(),
    "graph_bfs": lambda: GraphBFSAgent(),
    "mcts": lambda sims: MCTSAgent(simulations=sims, max_depth=30),
}


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
    if geometry == "D":
        return PolyJumpConfig(
            geometry="D",
            ep_side=5,
            players=2,
            movement=movement,
            capture=capture,
            goal=goal,
            scoring=scoring,
        )
    raise ValueError(f"未知 geometry: {geometry}")


def play(
    cfg: PolyJumpConfig,
    a_slug: str,
    b_slug: str,
    side: tuple[int, int],
    max_actions: int,
    mcts_sims: int,
) -> dict:
    env = GameEnv(cfg)
    env.reset()
    agents = {
        "random": AGENTS["random"](),
        "euclidean": AGENTS["euclidean"](),
        "chebyshev": AGENTS["chebyshev"](),
        "graph_bfs": AGENTS["graph_bfs"](),
        "mcts": AGENTS["mcts"](mcts_sims),
    }

    while True:
        obs = env.observe()
        if obs.done or obs.action_count >= max_actions:
            break
        slug = a_slug if obs.current_player == side[0] else b_slug
        action = agents[slug].choose(env)
        if action is None:
            legal = env.legal_actions()
            if not legal:
                break
            action = legal[0]
        env.execute_action(action)

    return env.state_dict()


def aggregate(state: dict, slug_by_player: dict[int, str]) -> tuple[dict, dict]:
    stats: dict[str, dict] = {
        slug: {"actions": 0, "steps": 0, "path": 0.0, "straight": 0.0}
        for slug in slug_by_player.values()
    }
    for act in state.get("actions", []):
        player = act["player"]
        slug = slug_by_player.get(player)
        if slug is None:
            continue
        stats[slug]["actions"] += 1
        stats[slug]["steps"] += act.get("step_count", 0)
        stats[slug]["path"] += act.get("path_distance", 0.0)
        stats[slug]["straight"] += act.get("straight_distance", 0.0)
    return state.get("winner"), stats


def main() -> int:
    parser = argparse.ArgumentParser(description="PolyJump 跨模型小对比")
    parser.add_argument("--max-actions", type=int, default=12)
    parser.add_argument("--mcts-simulations", type=int, default=5)
    parser.add_argument("--models", default="A,B,C,D")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    slugs = ["random", "euclidean", "chebyshev", "graph_bfs", "mcts"]
    total = defaultdict(
        lambda: {"games": 0, "actions": 0, "steps": 0, "path": 0.0, "straight": 0.0}
    )

    for model in models:
        cfg = make_config(model)
        for a_slug, b_slug in combinations(slugs, 2):
            for side in [(1, 2), (2, 1)]:
                state = play(cfg, a_slug, b_slug, side, args.max_actions, args.mcts_simulations)
                slug_by_player = {
                    1: a_slug if side[0] == 1 else b_slug,
                    2: a_slug if side[0] == 2 else b_slug,
                }
                _, stats = aggregate(state, slug_by_player)
                for slug, s in stats.items():
                    t = total[(model, slug)]
                    t["games"] += 1
                    t["actions"] += s["actions"]
                    t["steps"] += s["steps"]
                    t["path"] += s["path"]
                    t["straight"] += s["straight"]

    print("# PolyJump 跨模型小对比")
    print()
    print("| 模型 | agent | 局数 | 平均 actions | 平均 steps | 平均 path | 平均 straight | detour |")
    print("|---|---|---|---|---|---|---|---|")
    for model in models:
        for slug in slugs:
            t = total[(model, slug)]
            games = max(1, t["games"])
            avg_actions = t["actions"] / games
            avg_steps = t["steps"] / games
            avg_path = t["path"] / games
            avg_straight = t["straight"] / games
            detour = t["path"] / t["straight"] if t["straight"] else 0.0
            print(
                f"| {model} | {slug} | {t['games']} "
                f"| {avg_actions:.2f} | {avg_steps:.2f} "
                f"| {avg_path:.2f} | {avg_straight:.2f} | {detour:.2f} |"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
