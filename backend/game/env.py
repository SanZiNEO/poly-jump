"""干净的游戏环境接口。

只暴露：
- reset()
- legal_actions()
- action_space()
- execute_action(action)
- observe()
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
from .path_metrics import summarize_actions
from .serializers import state_to_dict


@dataclass
class ActionResult:
    game_id: str
    current_player: int
    winner: Optional[int]
    last_action: Optional[dict]
    legal_paths: List[list]
    legal_actions: List[dict]
    done: bool
    scores: dict
    temp_scores: dict
    round: int
    action_count: int
    total_steps: int
    total_straight_distance: float
    total_path_distance: float


class GameEnv:
    def __init__(self, config: PolyJumpConfig):
        self.config = config
        self.state = GameState(config)

    def reset(self) -> ActionResult:
        self.state = GameState(self.config)
        return self.observe()

    def legal_actions(self) -> List[list]:
        return [list(p) for p in self.state.legal_actions()]

    def action_space(self) -> List[dict]:
        return action_index(self.state.legal_actions())

    def execute_action(self, action) -> ActionResult:
        """提交 action，可以是 path，也可以是 action id。"""
        if isinstance(action, int):
            paths = self.state.legal_actions()
            if action < 0 or action >= len(paths):
                raise ValueError(f"action id 越界: {action}")
            chosen = paths[action]
        else:
            chosen = action

        if not self.state.perform_action(chosen):
            raise ValueError("非法 action")

        return self.observe()

    def observe(self) -> ActionResult:
        paths = self.state.legal_actions()
        summary = summarize_actions(self.state.action_history)
        return ActionResult(
            game_id=self.state.id,
            current_player=self.state.current_player,
            winner=self.state.winner,
            last_action=self.state.action_history[-1] if self.state.action_history else None,
            legal_paths=[[list(p) for p in path] for path in paths],
            legal_actions=action_index(paths),
            done=self.state.winner is not None,
            scores=dict(self.state.scores),
            temp_scores=dict(self.state.temp_scores),
            round=self.state.round,
            action_count=self.state.action_count,
            total_steps=int(summary["total_steps"]),
            total_straight_distance=float(summary["total_straight_distance"]),
            total_path_distance=float(summary["total_path_distance"]),
        )

    def state_dict(self) -> dict:
        return state_to_dict(self.state)
