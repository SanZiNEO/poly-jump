"""单局状态管理。"""

from __future__ import annotations

import uuid
from typing import List, Optional, Sequence

from .board import Board
from .config import PolyJumpConfig
from .moves import MoveGenerator, MoveValidator
from .rules import MoveApplier, check_winner
from .scoring import ScoringEngine


class GameState:
    def __init__(self, config: PolyJumpConfig):
        self.id: str = uuid.uuid4().hex
        self.config = config
        self.board: Board = Board(config)
        self.current_player: int = 1
        self.winner: Optional[int] = None
        self.move_history: List[dict] = []
        self.initial_pieces: dict = dict(self.board.pieces)
        self.snapshots: List[dict] = []
        self.scores: dict = {i: 0 for i in range(1, config.players + 1)}
        self.temp_scores: dict = {i: 0 for i in range(1, config.players + 1)}

    def legal_moves(self):
        return MoveGenerator(self.config).legal_moves(self.board, self.current_player)

    def legal_moves_for(self, pos) -> list:
        return MoveGenerator(self.config).legal_moves_for_piece(
            self.board, self.current_player, tuple(pos)
        )

    def is_legal(self, path: Sequence[Sequence[int]]) -> bool:
        return MoveValidator(self.config).is_legal(
            self.board, self.current_player, path
        )

    def perform_move(self, path: Sequence[Sequence[int]]) -> bool:
        """校验并应用一步；成功返回 True。"""
        if self.winner is not None:
            return False

        path_t = [tuple(p) for p in path]
        if not self.is_legal(path_t):
            return False

        player = self.current_player
        capture_count = MoveApplier(self.config).apply(self.board, path_t, player)

        # 积分：连跳临时分 / 吃子分 / 进入目标区分
        engine = ScoringEngine(self.config)
        reached_target = path_t[-1] in self.board.player_targets.get(player, set())
        assessment = engine.assess_move(
            player, path_t, capture_count, reached_target
        )
        if self.config.scoring.enabled:
            self.temp_scores[player] += assessment["chain_temp"]
            self.scores[player] += (
                assessment["capture_points"] + assessment["target_points"]
            )

        self.winner = check_winner(self.board, self.config)
        if self.winner is not None:
            self.scores = engine.finalize(
                self.winner,
                self.config.players,
                self.board,
                self.scores,
                self.temp_scores,
            )

        self.move_history.append(
            {
                "player": player,
                "path": [list(p) for p in path_t],
                "scoring": assessment,
                "scores": dict(self.scores),
                "temp_scores": dict(self.temp_scores),
            }
        )
        self.snapshots.append(dict(self.board.pieces))
        if self.winner is None:
            self._advance_turn()
        return True

    def _advance_turn(self) -> None:
        # 无棋可走自动跳过：轮询到下一个有合法走法的玩家
        for _ in range(self.config.players):
            self.current_player = self.current_player % self.config.players + 1
            if self.legal_moves():
                return
