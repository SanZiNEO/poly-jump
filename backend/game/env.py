"""干净的游戏环境接口。

只暴露：
- reset()
- legal_moves()
- action_space()
- step(action)
- state_dict()

外部 AI 程序可以直接调用，无需了解前端/API 细节。
不包含任何训练逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .actions import action_index
from .config import PolyJumpConfig
from .game_state import GameState
from .serializers import state_to_dict


@dataclass
class StepResult:
    game_id: str
    current_player: int
    winner: Optional[int]
    last_move: Optional[dict]
    legal_paths: List[list]
    legal_actions: List[dict]
    done: bool
    scores: dict
    temp_scores: dict
    round: int
    step_count: int


class GameEnv:
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.state = GameState(config)

    def reset(self) -> StepResult:
        self.state = GameState(self.config)
        return self.observe()

    def legal_moves(self) -> List[list]:
        return [list(p) for p in self.state.legal_moves()]

    def action_space(self) -> List[dict]:
        return action_index(self.state.legal_moves())

    def step(self, action) -> StepResult:
        """提交动作，可以是 path，也可以是 action id。"""
        if isinstance(action, int):
            paths = self.state.legal_moves()
            if action < 0 or action >= len(paths):
                raise ValueError(f"action id 越界: {action}")
            chosen = paths[action]
        else:
            chosen = action

        if not self.state.perform_move(chosen):
            raise ValueError("非法动作")

        return self.observe()

    def observe(self) -> StepResult:
        paths = self.state.legal_moves()
        return StepResult(
            game_id=self.state.id,
            current_player=self.state.current_player,
            winner=self.state.winner,
            last_move=self.state.move_history[-1] if self.state.move_history else None,
            legal_paths=[[list(p) for p in path] for path in paths],
            legal_actions=action_index(paths),
            done=self.state.winner is not None,
            scores=dict(self.state.scores),
            temp_scores=dict(self.state.temp_scores),
            round=self.state.round,
            step_count=self.state.step_count,
        )

    def state_dict(self) -> dict:
        return state_to_dict(self.state)
