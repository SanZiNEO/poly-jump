"""PolyJump 配置类与校验。

设计依据 docs/05-configuration.md、docs/06-architecture.md。
A 模型：全整数 XYZ 立方格。
B 模型：纯 12 向 FCC / L1 球偶子晶格，b_radius 为偶数。
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


class ScoringConfig(BaseModel):
    enabled: bool = False
    first_finish_reward: int = 10
    chain_jump_points: int = 1
    chain_temp: bool = True
    capture_points: int = 2
    target_zone_points: int = 1
    survivor_piece_points: int = 1


class PolyJumpConfig(BaseModel):
    game_name: str = "PolyJump"
    geometry: Literal["A", "B", "C", "D", "B_EXT", "C_EXT", "A_EXT"] = "A"
    board_size: Tuple[int, int, int] = (9, 9, 9)
    b_radius: int = 6
    c_radius: int = 6
    ep_side: int = 5
    players: int = 2
    direction_set: Union[int, List[int]] = Field(default_factory=lambda: [6, 12, 8])
    custom_vectors: List[Tuple[int, int, int]] = Field(default_factory=list)
    movement: MovementConfig = Field(default_factory=MovementConfig)
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    goal: GoalConfig = Field(default_factory=GoalConfig)
    initial_layout: InitialLayoutConfig = Field(default_factory=InitialLayoutConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)

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
            if self.b_radius <= 0 or self.b_radius % 2 != 0:
                raise ValueError("B 模型 b_radius 必须为正偶数")
            if self.players not in (2, 3, 4, 6):
                raise ValueError("B 模型支持 2 / 3 / 4 / 6 人")
            # B 模型标准移动固定为 12 向
            self.direction_set = [12]
        elif self.geometry == "C":
            if self.c_radius <= 0 or self.c_radius % 2 != 0:
                raise ValueError("C 模型 c_radius 必须为正偶数")
            if self.players not in (2, 3, 4, 6):
                raise ValueError("C 模型支持 2 / 3 / 4 / 6 人")
            # C 模型固定为 12 + 8 = 20 向
            self.direction_set = [20]
        elif self.geometry == "D":
            if self.players not in (2, 3, 4, 6):
                raise ValueError("D 模型支持 2 / 3 / 4 / 6 人")
            self.direction_set = [14]
        elif self.geometry == "B_EXT":
            if self.players not in (2, 3, 4, 6):
                raise ValueError("B-ext 模型支持 2 / 3 / 4 / 6 人")
            self.direction_set = [12]
        elif self.geometry == "C_EXT":
            if self.players not in (2, 3, 4, 6):
                raise ValueError("C-ext 模型支持 2 / 3 / 4 / 6 人")
            self.direction_set = [20]
        elif self.geometry == "A_EXT":
            if self.players not in (2, 3, 4, 6):
                raise ValueError("A-ext 模型支持 2 / 3 / 4 / 6 人")
            # 方向不固定，沿用 direction_set
        if self.geometry in ("A_EXT", "B_EXT", "C_EXT", "D"):
            if self.ep_side % 2 == 0 or self.ep_side < 3:
                raise ValueError("外接金字塔中心边长 ep_side 必须为奇数且 >= 3")
        return self

    def resolved_direction_set(self) -> List[int]:
        if isinstance(self.direction_set, int):
            return [self.direction_set]
        return list(self.direction_set)
