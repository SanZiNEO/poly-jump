"""B 模型（纯 12 向 L1 偶子晶格）基础测试。"""

from __future__ import annotations

import pytest

from backend.game.config import PolyJumpConfig
from backend.game.geometry.model_b import GeometryB


def make_b_config(radius=6, players=6) -> PolyJumpConfig:
    return PolyJumpConfig(
        geometry="B",
        b_radius=radius,
        players=players,
        direction_set=[12],
    )


def test_b_point_count_r6():
    geometry = GeometryB(make_b_config(radius=6, players=2))
    points = geometry.generate_points()
    assert len(points) == 231


def test_b_parity_and_l1_ball():
    geometry = GeometryB(make_b_config(radius=6, players=2))
    points = set(geometry.generate_points())

    assert (6, 0, 0) in points
    assert (0, 0, 0) in points
    # 奇点不在偶子晶格中
    assert (1, 0, 0) not in points
    # L1 距离超过半径的点不在棋盘内
    assert (7, 0, 0) not in points
    assert (6, 1, 0) not in points


def test_b_radius_even_required():
    with pytest.raises(ValueError):
        PolyJumpConfig(geometry="B", b_radius=5, players=2)


def test_b_six_player_bases():
    geometry = GeometryB(make_b_config(radius=6, players=6))
    bases, targets = geometry.player_assignments()

    assert len(bases) == 6
    for player in range(1, 7):
        assert len(bases[player]) == 14
        assert len(targets[player]) == 14

    # 六个基地互不重叠
    all_positions = [pos for base in bases.values() for pos in base]
    assert len(all_positions) == len(set(all_positions))


def test_b_three_player_uses_empty_opposite_tips():
    geometry = GeometryB(make_b_config(radius=6, players=3))
    bases, targets = geometry.player_assignments()

    base_positions = {pos for base in bases.values() for pos in base}
    target_positions = {pos for target in targets.values() for pos in target}

    assert len(bases) == 3
    # 3 人局目标区为空白对侧尖端，不与任何玩家基地重叠
    assert base_positions.isdisjoint(target_positions)
