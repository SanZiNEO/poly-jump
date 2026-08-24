"""C 模型（L1 球全整数点 + 20 向）基础测试。"""

from __future__ import annotations

import pytest

from backend.game.config import PolyJumpConfig
from backend.game.geometry.model_c import GeometryC


def make_c_config(radius=6, players=6) -> PolyJumpConfig:
    return PolyJumpConfig(
        geometry="C",
        c_radius=radius,
        players=players,
        direction_set=[20],
    )


def test_c_point_count_r6():
    geometry = GeometryC(make_c_config(radius=6, players=2))
    points = geometry.generate_points()
    assert len(points) == 377


def test_c_full_integer_points_inside_l1():
    geometry = GeometryC(make_c_config(radius=6, players=2))
    points = set(geometry.generate_points())

    assert (6, 0, 0) in points
    assert (1, 0, 0) in points  # C 模型包含奇点
    assert (6, 1, 0) not in points
    assert (3, 3, 0) in points  # 3+3=6 在 L1 内


def test_c_direction_fixed_20():
    cfg = make_c_config()
    assert cfg.direction_set == [20]


def test_c_radius_even_required():
    with pytest.raises(ValueError):
        PolyJumpConfig(geometry="C", c_radius=5, players=2)


def test_c_six_player_bases():
    geometry = GeometryC(make_c_config(radius=6, players=6))
    bases, targets = geometry.player_assignments()

    assert len(bases) == 6
    for player in range(1, 7):
        # R=6 时每层全点数为 1,5,13，共 19 子
        assert len(bases[player]) == 19
        assert len(targets[player]) == 19

    all_positions = [pos for base in bases.values() for pos in base]
    assert len(all_positions) == len(set(all_positions))
