"""单局状态管理。"""

from __future__ import annotations

import copy
import uuid
from typing import List, Optional, Sequence

from .board import Board
from .config import PolyJumpConfig
from .movement import ActionGenerator, ActionValidator
from .path_metrics import path_metrics
from .rules import ActionApplier, check_winner
from .scoring import (
    ActionContext,
    FinishContext,
    ScoringPolicy,
    build_policy,
)


class GameState:
    def __init__(self, config: PolyJumpConfig, scoring: Optional[ScoringPolicy] = None):
        if scoring is not None and not isinstance(scoring, ScoringPolicy):
            raise TypeError("scoring 必须实现 ScoringPolicy（on_action / on_finish）")
        self.id: str = uuid.uuid4().hex
        self.config = config
        self.scoring: ScoringPolicy = scoring or build_policy(config)
        self.board: Board = Board(config)
        self.current_player: int = 1
        self.winner: Optional[int] = None
        self.action_history: List[dict] = []
        self.initial_pieces: dict = dict(self.board.pieces)
        self.snapshots: List[dict] = []
        self.scores: dict = {i: 0 for i in range(1, config.players + 1)}
        self.temp_scores: dict = {i: 0 for i in range(1, config.players + 1)}

    @property
    def action_count(self) -> int:
        """已经发生的 action（玩家操作）数量。"""
        return len(self.action_history)

    @property
    def round(self) -> int:
        if not self.action_history:
            return 0
        return (len(self.action_history) - 1) // self.config.players + 1

    def legal_actions(self):
        return ActionGenerator(self.config).legal_actions(self.board, self.current_player)

    def legal_actions_for(self, pos) -> list:
        return ActionGenerator(self.config).legal_actions_for_piece(
            self.board, self.current_player, tuple(pos)
        )

    def is_legal(self, path: Sequence[Sequence[int]]) -> bool:
        return ActionValidator(self.config).is_legal(
            self.board, self.current_player, path
        )

    def perform_action(self, path: Sequence[Sequence[int]]) -> bool:
        """校验并应用一次 action；成功返回 True。"""
        if self.winner is not None:
            return False

        path_t = [tuple(p) for p in path]
        if not self.is_legal(path_t):
            return False

        player = self.current_player
        capture_count = ActionApplier(self.config).apply(self.board, path_t, player)

        # 积分：把事实交给策略定价（策略由构造参数注入，默认按配置权重）
        target_set = self.board.player_targets.get(player, set())
        # 只有“从目标区外进入目标区”才算一次；目标区内移动/穿过不算
        entered_target = (
            tuple(path_t[0]) not in target_set
            and tuple(path_t[-1]) in target_set
        )
        score_delta = self.scoring.on_action(
            ActionContext(
                player=player,
                path=[list(p) for p in path_t],
                captured=capture_count,
                entered_target=entered_target,
                board=self.board,
                config=self.config,
                round=self.action_count // self.config.players + 1,
            )
        )
        for who, value in score_delta.scores.items():
            self.scores[who] = self.scores.get(who, 0) + value
        for who, value in score_delta.temp_scores.items():
            self.temp_scores[who] = self.temp_scores.get(who, 0) + value

        self.winner = check_winner(self.board, self.config)
        if self.winner is not None:
            self.scores = self.scoring.on_finish(
                FinishContext(
                    winner=self.winner,
                    players=self.config.players,
                    board=self.board,
                    scores=self.scores,
                    temp_scores=self.temp_scores,
                    config=self.config,
                )
            )

        metrics = path_metrics(path_t)
        self.action_history.append(
            {
                "player": player,
                "path": [list(p) for p in path_t],
                "score_delta": {
                    "scores": dict(score_delta.scores),
                    "temp_scores": dict(score_delta.temp_scores),
                },
                "scores": dict(self.scores),
                "temp_scores": dict(self.temp_scores),
                "step_count": metrics["step_count"],
                "straight_distance": metrics["straight_distance"],
                "path_distance": metrics["path_distance"],
                "step_distances": metrics["step_distances"],
            }
        )
        self.snapshots.append(dict(self.board.pieces))
        if self.winner is None:
            self._advance_turn()
        return True

    def __deepcopy__(self, memo):
        """深拷贝状态，但**按引用共享**积分策略。

        搜索（MCTS 等）会高频调用 `clone()`：策略既不该被复制成千上万次，
        也不该要求外部自定义的策略可深拷贝。
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        for key, value in self.__dict__.items():
            setattr(new, key, value if key == "scoring" else copy.deepcopy(value, memo))
        return new

    def clone(self) -> "GameState":
        """深拷贝当前状态，用于搜索/模拟。"""
        return copy.deepcopy(self)

    def _advance_turn(self) -> None:
        # 无棋可走自动跳过：轮询到下一个有合法走法的玩家
        for _ in range(self.config.players):
            self.current_player = self.current_player % self.config.players + 1
            if self.legal_actions():
                return
