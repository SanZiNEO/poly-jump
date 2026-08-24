"""A 模型几何与金字塔初始布局测试。"""

from __future__ import annotations

from backend.game.config import InitialLayoutConfig, PolyJumpConfig
from backend.game.geometry.model_a import GeometryA


def make_geometry(size=(9, 9, 9), layers=4) -> GeometryA:
    return GeometryA(
        PolyJumpConfig(
            board_size=size,
            players=2,
            initial_layout=InitialLayoutConfig(layers=layers),
        )
    )


def test_pyramid_layer_counts():
    geometry = make_geometry(layers=4)
    bases, _ = geometry.player_assignments()
    home1 = bases[1]

    counts = [len([p for p in home1 if sum(p) == layer]) for layer in range(4)]
    assert counts == [1, 3, 6, 10]


def test_pyramid_apex_at_corner():
    geometry = make_geometry()
    bases, _ = geometry.player_assignments()
    home1 = bases[1]
    assert (0, 0, 0) in home1

    home2 = bases[2]
    assert (8, 8, 8) in home2


def test_pyramid_outward_layers():
    geometry = make_geometry()
    bases, _ = geometry.player_assignments()
    home1 = bases[1]

    # 第一层应该沿 x/y/z 三个轴各外扩一格
    assert (1, 0, 0) in home1
    assert (0, 1, 0) in home1
    assert (0, 0, 1) in home1


def test_a_three_four_player_targets_empty():
    for players, base_indices in [(3, [0, 4, 5]), (4, [0, 4, 5, 6])]:
        geometry = make_geometry()
        geometry.config.players = players
        bases, targets = geometry.player_assignments()

        base_positions = {p for base in bases.values() for p in base}
        target_positions = {p for target in targets.values() for p in target}
        assert base_positions.isdisjoint(target_positions)


def test_a_six_eight_player_assignments():
    for players in (6, 8):
        geometry = make_geometry()
        geometry.config.players = players
        bases, targets = geometry.player_assignments()

        assert len(bases) == players
        assert len(targets) == players
        all_base = [p for base in bases.values() for p in base]
        assert len(all_base) == len(set(all_base))
