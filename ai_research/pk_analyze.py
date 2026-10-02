"""本地 AI PK 离线分析：判优 + 排名。

读取 runner 输出的 `runs/<out>/<时间戳>/matches/*.json`，按
`docs/14-local-ai-pk.md` 的固定规则判定胜负并排名：

1. 正常终局：winner。
2. 达到 action 上限未终局：
   - 目标区棋子数（final_inside）多者胜；
   - 相同 → 累计 path_distance 短者胜；
   - 仍相同 → 平局。
3. 计分：胜 1 分、平 0.5 分、负 0 分。

用法：
    .poly_jump\\Scripts\\python.exe -m ai_research.pk_analyze ai_research/runs/pk_a_fast ai_research/runs/pk_b_fast
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _side(mapping: dict | None, key):
    """兼容 JSON 序列化后 int key 变 str 的情况。"""
    if not mapping:
        return None
    if key in mapping:
        return mapping[key]
    return mapping.get(str(key))


def decide(match: dict) -> tuple[str, str] | None:
    """按 PK 规则返回 (胜者 slug, 败者 slug)；平局返回 None。"""
    agents = match.get("player_agent") or {}
    winner = match.get("winner")
    slugs = {int(k): v for k, v in agents.items()}

    if winner is not None:
        winner = int(winner)
        loser = 2 if winner == 1 else 1
        return slugs.get(winner), slugs.get(loser)

    players = match.get("players") or {}
    p1 = _side(players, 1) or {}
    p2 = _side(players, 2) or {}
    fi1, fi2 = p1.get("final_inside", 0), p2.get("final_inside", 0)
    if fi1 != fi2:
        return (slugs.get(1), slugs.get(2)) if fi1 > fi2 else (slugs.get(2), slugs.get(1))
    pd1, pd2 = p1.get("path_distance", 0.0), p2.get("path_distance", 0.0)
    if pd1 != pd2:
        return (slugs.get(1), slugs.get(2)) if pd1 < pd2 else (slugs.get(2), slugs.get(1))
    return None


def wilson(points: float, games: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% 置信区间。"""
    if games == 0:
        return 0.0, 0.0
    p = points / games
    denom = 1.0 + z * z / games
    center = (p + z * z / (2 * games)) / denom
    half = z * math.sqrt(p * (1 - p) / games + z * z / (4 * games * games)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def config_label(run_dir: Path) -> str:
    """从 experiment.json 生成配置标签，如 A-9x9x9 / B-R8。"""
    exp_path = run_dir / "experiment.json"
    if not exp_path.exists():
        return run_dir.name
    with exp_path.open(encoding="utf-8") as f:
        cfg = json.load(f).get("config", {})
    if cfg.get("geometry") == "A":
        size = cfg.get("board_size") or [9, 9, 9]
        return "A-" + "x".join(str(v) for v in size)
    if cfg.get("geometry") == "B":
        return f"B-R{cfg.get('b_radius')}"
    return cfg.get("geometry", run_dir.name)


def load_groups(roots: list[Path]) -> dict[str, list[dict]]:
    """按配置分组加载全部对局记录。"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for root in roots:
        for matches_dir in sorted(root.glob("*/matches")):
            label = config_label(matches_dir.parent)
            for path in sorted(matches_dir.glob("*.json")):
                with path.open(encoding="utf-8") as f:
                    match = json.load(f)
                match["_config"] = label
                match["_file"] = str(path)
                groups[label].append(match)
    return groups


def summarize(matches: list[dict]) -> dict:
    """统计每个 agent 与每个配对的战绩。"""
    per_agent = defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0, "draws": 0,
                                     "points": 0.0, "tiebreak_wins": 0, "unfinished": 0})
    per_pair = defaultdict(lambda: {"games": 0, "a_wins": 0, "b_wins": 0, "draws": 0})
    for match in matches:
        agents = match.get("player_agent") or {}
        slugs = sorted({str(v) for v in agents.values()})
        result = decide(match)
        unfinished = match.get("winner") is None
        for slug in slugs:
            meta = per_agent[slug]
            meta["games"] += 1
            if unfinished:
                meta["unfinished"] += 1
        if result is None:
            for slug in slugs:
                per_agent[slug]["draws"] += 1
                per_agent[slug]["points"] += 0.5
            pair_key = tuple(slugs)
            per_pair[pair_key]["games"] += 1
            per_pair[pair_key]["draws"] += 1
            continue
        winner, loser = result
        per_agent[winner]["wins"] += 1
        per_agent[winner]["points"] += 1.0
        per_agent[loser]["losses"] += 1
        if unfinished:
            per_agent[winner]["tiebreak_wins"] += 1
        pair_key = tuple(sorted([winner, loser]))
        pp = per_pair[pair_key]
        pp["games"] += 1
        pp.setdefault("a", pair_key[0])
        pp.setdefault("b", pair_key[1])
        if winner == pair_key[0]:
            pp["a_wins"] += 1
        else:
            pp["b_wins"] += 1
    return {"agents": per_agent, "pairs": per_pair}


def format_table(per_agent: dict, title: str) -> list[str]:
    rows = sorted(per_agent.items(), key=lambda kv: (-kv[1]["points"] / max(1, kv[1]["games"]),
                                                     -kv[1]["points"]))
    lines = [f"### {title}", "",
             "| # | agent | 场次 | 胜 | 平 | 负 | 胜率 | Wilson 95% | 未终局 | 判优胜 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, (slug, m) in enumerate(rows, 1):
        wr = m["points"] / m["games"] if m["games"] else 0.0
        lo, hi = wilson(m["points"], m["games"])
        lines.append(f"| {i} | {slug} | {m['games']} | {m['wins']} | {m['draws']} | {m['losses']} "
                     f"| {wr:.1%} | [{lo:.1%}, {hi:.1%}] | {m['unfinished']} | {m['tiebreak_wins']} |")
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="本地 AI PK 离线分析")
    parser.add_argument("roots", nargs="+", type=Path, help="runs 下的实验根目录")
    parser.add_argument("--out", type=Path, default=None, help="把 Markdown 报告写到文件")
    args = parser.parse_args()

    groups = load_groups(args.roots)
    if not groups:
        print("没有找到对局记录，请检查目录。")
        return 1

    lines: list[str] = ["# 本地 AI PK 结果", ""]
    combined: dict[str, dict] = defaultdict(lambda: {"games": 0, "points": 0.0})
    for label, matches in sorted(groups.items()):
        stats = summarize(matches)
        lines += format_table(stats["agents"], f"{label}（{len(matches)} 局）")
        lines += ["<details><summary>配对明细</summary>", "",
                  "| 配对 | 局数 | 胜 A | 胜 B | 平 |", "|---|---|---|---|---|"]
        for (a, b), pp in sorted(stats["pairs"].items()):
            lines.append(f"| {a} vs {b} | {pp['games']} | {pp.get('a_wins', 0)} "
                         f"| {pp.get('b_wins', 0)} | {pp['draws']} |")
        lines += ["", "</details>", ""]
        for slug, m in stats["agents"].items():
            combined[slug]["games"] += m["games"]
            combined[slug]["points"] += m["points"]

    if len(groups) > 1:
        lines += ["### 合并（两配置等权胜率）", "",
                  "| agent | 各配置胜率 | 合并胜率 | 总场次 |", "|---|---|---|---|"]
        rows = []
        for slug, m in combined.items():
            rates = []
            for label, matches in sorted(groups.items()):
                stats = summarize(matches)
                if slug in stats["agents"]:
                    s = stats["agents"][slug]
                    rates.append(s["points"] / s["games"] if s["games"] else 0.0)
            rows.append((slug, rates, sum(rates) / len(rates) if rates else 0.0, m["games"]))
        for slug, rates, mean_rate, games in sorted(rows, key=lambda r: -r[2]):
            rate_text = " / ".join(f"{r:.1%}" for r in rates)
            lines.append(f"| {slug} | {rate_text} | {mean_rate:.1%} | {games} |")
        lines.append("")

    report = "\n".join(lines)
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"\n报告已写入：{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
