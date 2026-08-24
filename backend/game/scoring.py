"""积分制接口。

目前定义积分规则配置和基础计算框架。
具体连跳临时分、失败扣分比例、吃子分值等都可以在 configuration 中后续调整。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .config import CaptureMode, PolyJumpConfig
from .board import Board


class ScoringEngine:
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.scoring = config.scoring

    def assess_move(
        self,
        player: int,
        path: List[List[int]],
        capture_count: int = 0,
        reached_target: bool = False,
    ) -> dict:
        """评估一步产生的分数变化。

        返回：
        - chain_temp：连跳临时分（每多一次连跳 +1）
        - capture_points：吃子分
        - target_points：进入目标区分
        """
        chain_jumps = max(0, len(path) - 1) if len(path) > 2 else 0
        chain_temp = 0
        if self.scoring.enabled and self.scoring.chain_temp:
            chain_temp = chain_jumps * self.scoring.chain_jump_points

        capture_points = 0
        if self.scoring.enabled:
            capture_points = capture_count * self.scoring.capture_points

        target_points = 0
        if self.scoring.enabled and reached_target:
            target_points = self.scoring.target_zone_points

        return {
            "chain_temp": chain_temp,
            "capture_points": capture_points,
            "target_points": target_points,
        }

    def finalize(
        self,
        winner: Optional[int],
        players: int,
        board: Board,
        scores: Dict[int, int],
        temp_scores: Dict[int, int],
    ) -> Dict[int, int]:
        """对局结束时结算最终积分。"""
        if winner is None:
            return dict(scores)

        final = dict(scores)

        if self.config.capture.mode == CaptureMode.CAPTURE:
            # 西洋棋胜利：按存活棋子数加分
            survivor = len(board.pieces_for_player(winner))
            final[winner] = final.get(winner, 0) + survivor * self.scoring.survivor_piece_points
        else:
            # 中国跳棋/混合模式：先完成目标区获胜，给固定奖励
            final[winner] = final.get(winner, 0) + self.scoring.first_finish_reward

        # 临时分：胜者保留；败者临时分按比例扣除（当前简单实现为全扣）
        if self.scoring.chain_temp:
            for player in range(1, players + 1):
                temp = temp_scores.get(player, 0)
                if player == winner:
                    final[player] = final.get(player, 0) + temp
                else:
                    final[player] = final.get(player, 0) - temp

        return final
