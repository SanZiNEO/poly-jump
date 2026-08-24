"""PolyJump 配置类与校验。

设计依据 docs/05-configuration.md、docs/06-architecture.md。
本项目第一版先完整实现 A 模型 + 2 人局；B 模型和多于 2 人的基地分配
留接口并标注 TODO，不阻塞最小可玩版本。
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class HopMode(str, Enum):
    FREE_STOP = "FREE_STOP"
    FORCE_ALL = "FORCE_ALL"


class CaptureMode(str, Enum):
    NONE = "NONE"
    CAPTURE = "CAPTURE"
    MIXED = "MIXED"


class MovementConfig(BaseModel):
    allow_step: bool = True
    allow_jump: bool = True
    allow_chain: bool = True
    hop_mode: HopMode = HopMode.FREE_STOP
    two_step_hop: bool = False
    max_chain_length: int = 0  # 0 = 不限制


class CaptureConfig(BaseModel):
    mode: CaptureMode = CaptureMode.NONE
    capture_opponent_only: bool = True
    mixed_swap: bool = False


class GoalConfig(BaseModel):
    objective: str = "FILL_TARGET"
    target_region: str = "OPPOSITE_CORNER"
    must_fill_all_cells: bool = True
    allow_pass_through_enemy: bool = True
    allow_stay_in_enemy: bool = False
    first_to_finish_wins: bool = True


class InitialLayoutConfig(BaseModel):
    shape: str = "TETRA_PYRAMID"
    layers: int = 4
    custom_layout: List[List[int]] = Field(default_factory=list)


class RenderConfig(BaseModel):
    show_points: bool = True
    show_routes: bool = True
    route_colors: dict = Field(default_factory=dict)
    point_size: float = 1.0
    line_opacity: float = 0.3


class PolyJumpConfig(BaseModel):
    game_name: str = "PolyJump"
    geometry: Literal["A", "B"] = "A"
    board_size: Tuple[int, int, int] = (9, 9, 9)
    players: int = 2
    direction_set: Union[int, List[int]] = Field(default_factory=lambda: [6, 12, 8])
    custom_vectors: List[Tuple[int, int, int]] = Field(default_factory=list)
    movement: MovementConfig = Field(default_factory=MovementConfig)
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    goal: GoalConfig = Field(default_factory=GoalConfig)
    initial_layout: InitialLayoutConfig = Field(default_factory=InitialLayoutConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)

    @field_validator("board_size")
    @classmethod
    def _validate_board_size(cls, value: Tuple[int, int, int]) -> Tuple[int, int, int]:
        if any(v <= 0 for v in value):
            raise ValueError("board_size 每个维度必须为正整数")
        return value

    @field_validator("players")
    @classmethod
    def _validate_players(cls, value: int) -> int:
        if value not in (2, 3, 4, 6, 8):
            raise ValueError("players 只支持 2 / 3 / 4 / 6 / 8")
        return value

    @field_validator("direction_set", mode="before")
    @classmethod
    def _normalize_direction_set(cls, value: Union[int, List[int]]) -> List[int]:
        if isinstance(value, int):
            return [value]
        return value

    @field_validator("direction_set")
    @classmethod
    def _validate_direction_set(cls, value: List[int]) -> List[int]:
        allowed = {6, 8, 12, 14, 18, 20, 26}
        if any(v not in allowed for v in value):
            raise ValueError("direction_set 只支持 6/8/12/14/18/20/26")
        return value

    @model_validator(mode="after")
    def _validate_geometry(self) -> "PolyJumpConfig":
        if self.geometry == "B":
            # B 模型在第一版中仅保留接口/TODO。
            # 配置层面仍允许创建，但 Board 初始化时会明确报“未实现”。
            if any(v % 2 == 0 for v in self.board_size):
                raise ValueError("B 模型边长必须为奇数")
        return self

    def resolved_direction_set(self) -> List[int]:
        if isinstance(self.direction_set, int):
            return [self.direction_set]
        return list(self.direction_set)
