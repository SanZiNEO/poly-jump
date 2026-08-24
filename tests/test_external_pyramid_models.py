"""外接金字塔模型（D / B-ext / C-ext）测试。"""

from __future__ import annotations

import pytest

from backend.game.config import PolyJumpConfig
from backend.game.geometry.external_pyramid import generate_external_points
from backend.game.geometry.model_a_ext import GeometryAExt
from backend.game.geometry.model_b_ext import GeometryBExt
from backend.game.geometry.model_c_ext import GeometryCExt
from backend.game.geometry.model_d import GeometryD


def make_config(geometry: str, players: int = 6) -> PolyJumpConfig:
    return PolyJumpConfig(geometry=geometry, players=players)


def test_external_pyramid_point_counts():
    full = generate_external_points(2, None)
    even = generate_external_points(2, 0)
    assert len(full) == 185
    assert len(even) == 93


def test_d_model():
    geometry = GeometryD(make_config("D"))
    points = geometry.generate_points()
    assert len(points) == 185

    bases, targets = geometry.player_assignments()
    assert len(bases) == 6
    for player in range(1, 7):
        assert len(bases[player]) == 10
        assert len(targets[player]) == 10


def test_b_ext_even_sublattice():
    geometry = GeometryBExt(make_config("B_EXT"))
    points = geometry.generate_points()
    assert len(points) == 93

    bases, targets = geometry.player_assignments()
    assert len(bases) == 6
    for player in range(1, 7):
        assert len(bases[player]) == 5
        assert len(targets[player]) == 5


def test_c_ext_model():
    geometry = GeometryCExt(make_config("C_EXT"))
    points = geometry.generate_points()
    assert len(points) == 185

    bases, targets = geometry.player_assignments()
    assert len(bases) == 6
    for player in range(1, 7):
        assert len(bases[player]) == 10
        assert len(targets[player]) == 10


def test_ext_direction_fixed():
    assert PolyJumpConfig(geometry="D", players=2).direction_set == [14]
    assert PolyJumpConfig(geometry="B_EXT", players=2).direction_set == [12]
    assert PolyJumpConfig(geometry="C_EXT", players=2).direction_set == [20]


def test_ext_players_limited():
    with pytest.raises(ValueError):
        PolyJumpConfig(geometry="D", players=8)
    with pytest.raises(ValueError):
        PolyJumpConfig(geometry="B_EXT", players=8)
    with pytest.raises(ValueError):
        PolyJumpConfig(geometry="C_EXT", players=8)
    with pytest.raises(ValueError):
        PolyJumpConfig(geometry="A_EXT", players=8)


def test_a_ext_model():
    cfg = PolyJumpConfig(geometry="A_EXT", players=6, direction_set=[6])
    geometry = GeometryAExt(cfg)
    points = geometry.generate_points()
    assert len(points) == 185

    bases, targets = geometry.player_assignments()
    assert len(bases) == 6
    for player in range(1, 7):
        assert len(bases[player]) == 10
        assert len(targets[player]) == 10

    # A-ext 方向可配置
    assert cfg.direction_set == [6]


def test_ep_side_7_point_count():
    cfg = PolyJumpConfig(geometry="D", players=6, ep_side=7)
    geometry = GeometryD(cfg)
    # 7×7×7 中心 343 + 6 面 × (25+9+1=35) = 553
    assert len(geometry.generate_points()) == 553

    bases, _ = geometry.player_assignments()
    assert len(bases[1]) == 35
