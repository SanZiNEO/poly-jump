"""积分策略接口。

设计原则：**内核产事实，策略定价**。

- `ActionContext` / `FinishContext` 是对局事实的只读快照，不含任何价值判断；
- `ScoringPolicy` 决定这些事实值多少分；
- 框架自带两个实现：
  - `NullScoring`：不计分（所有变化恒为 0）—— `scoring.policy = "none"`（默认）
  - `WeightedScoring`：按 `config.scoring` 的权重计分 —— `scoring.policy = "weighted"`

外部程序可以自带策略，无需改动内核：

    from backend.game.env import GameEnv
    from backend.game.scoring import ActionContext, ScoreDelta

    class EnterTargetScoring:
        \"\"\"只给"进入目标区"计分的自定义策略。\"\"\"

        def on_action(self, ctx: ActionContext) -> ScoreDelta:
            if ctx.entered_target:
                return ScoreDelta(scores={ctx.player: 3})
            return ScoreDelta()

        def on_finish(self, ctx) -> dict:
            return dict(ctx.scores)

    env = GameEnv(config, scoring=EnterTargetScoring())

策略通过 `GameEnv` / `GameState` 的构造参数注入，**不进入 `PolyJumpConfig`** ——
配置需要可 JSON 序列化，装不下策略对象。

`GameState.clone()`（搜索/模拟用）**按引用共享策略**，不深拷贝，
因此自定义策略不必可拷贝，也不会在 MCTS 里被复制成千上万次。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, runtime_checkable

from .board import Board
from .config import CaptureMode, PolyJumpConfig


@dataclass(frozen=True)
class ActionContext:
    """一次 action 的事实快照（内核产生，不含价值判断）。"""

    player: int
    path: List[list]
    captured: int
    """本次 action 吃掉的棋子数。"""
    entered_target: bool
    """是否有棋子**从目标区外进入**目标区。

    内核统一定义：起点在目标区外、终点在目标区内才算；
    目标区内部移动、或只是穿过目标区都不算。策略直接读这个布尔值，
    不必各自重复推导（推导口径不一致会让不同策略对同一局面给出矛盾结论）。
    """
    board: Board
    """结算后的棋盘。自定义策略依赖局面信息时读它。"""
    config: PolyJumpConfig
    round: int


@dataclass(frozen=True)
class FinishContext:
    """对局结束的事实快照。"""

    winner: Optional[int]
    players: int
    board: Board
    scores: Dict[int, int]
    """结算前的正式分。"""
    temp_scores: Dict[int, int]
    """结算前的临时分（连跳累计）。"""
    config: PolyJumpConfig


@dataclass(frozen=True)
class ScoreDelta:
    """一次 action 产生的分数变化（缺省的键视为 0）。"""

    scores: Dict[int, int] = field(default_factory=dict)
    temp_scores: Dict[int, int] = field(default_factory=dict)


@runtime_checkable
class ScoringPolicy(Protocol):
    """积分策略接口。"""

    def on_action(self, ctx: ActionContext) -> ScoreDelta:
        """一次 action 结算后，返回各玩家的分数变化。"""
        ...

    def on_finish(self, ctx: FinishContext) -> Dict[int, int]:
        """对局结束时结算，返回**最终正式分**（整份，不是增量）。"""
        ...


def build_policy(config: PolyJumpConfig) -> ScoringPolicy:
    """按 `config.scoring.policy` 选择内置策略。

    仅在调用方没有显式注入策略时使用；注入的策略优先级更高。
    """
    if config.scoring.policy == "weighted":
        return WeightedScoring(config)
    return NullScoring()


class NullScoring:
    """不计分：所有变化恒为 0。"""

    def on_action(self, ctx: ActionContext) -> ScoreDelta:
        return ScoreDelta()

    def on_finish(self, ctx: FinishContext) -> Dict[int, int]:
        return dict(ctx.scores)


class WeightedScoring:
    """按 `config.scoring` 的权重计分（由 `policy = "weighted"` 选用）。

    事件与分值：

    | 事件 | 分值 | 配置项 |
    |---|---|---|
    | 连跳（路径超过 2 个点时，多出的每段） | 临时分 | `chain_jump_points` / `chain_temp` / `chain_max_scoring` |
    | 吃子 | 正式分 | `capture_points` |
    | 进入目标区 | 正式分 | `target_zone_points` |
    | 对局结束 | 正式分 | 吃子模式按存活棋子数 `survivor_piece_points`；否则 `first_finish_reward` |
    | 结算时的临时分 | 胜者保留、败者扣除 | `chain_temp` |

    这个策略没有开关：选用它就全程计分。不想计分请用 `NullScoring`。
    """

    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.scoring = config.scoring

    def on_action(self, ctx: ActionContext) -> ScoreDelta:
        chain_jumps = max(0, len(ctx.path) - 1) if len(ctx.path) > 2 else 0
        # 只限制计分的连跳次数，不限制连跳本身长度
        if self.scoring.chain_max_scoring > 0:
            chain_jumps = min(chain_jumps, self.scoring.chain_max_scoring)

        temp = chain_jumps * self.scoring.chain_jump_points if self.scoring.chain_temp else 0
        scores = ctx.captured * self.scoring.capture_points
        if ctx.entered_target:
            scores += self.scoring.target_zone_points

        return ScoreDelta(
            scores={ctx.player: scores} if scores else {},
            temp_scores={ctx.player: temp} if temp else {},
        )

    def on_finish(self, ctx: FinishContext) -> Dict[int, int]:
        if ctx.winner is None:
            return dict(ctx.scores)

        final = dict(ctx.scores)

        if ctx.config.capture.mode == CaptureMode.CAPTURE:
            # 西洋棋胜利：按存活棋子数加分
            survivor = len(ctx.board.pieces_for_player(ctx.winner))
            final[ctx.winner] = final.get(ctx.winner, 0) + survivor * self.scoring.survivor_piece_points
        else:
            # 中国跳棋/混合模式：先完成目标区获胜，给固定奖励
            final[ctx.winner] = final.get(ctx.winner, 0) + self.scoring.first_finish_reward

        # 临时分：胜者保留；败者临时分按比例扣除（当前简单实现为全扣）
        if self.scoring.chain_temp:
            for player in range(1, ctx.players + 1):
                temp = ctx.temp_scores.get(player, 0)
                if player == ctx.winner:
                    final[player] = final.get(player, 0) + temp
                else:
                    final[player] = final.get(player, 0) - temp

        return final
