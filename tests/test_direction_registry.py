"""方向注册表与自定义向量全方向族测试。"""

from __future__ import annotations

from backend.game.direction_registry import expand_family, load_custom_sets


def test_expand_family_2_1_0_full_orientation():
    vectors = expand_family([2, 1, 0])
    # 6 种排列 × 4 种符号 = 24 个方向
    assert len(vectors) == 24
    assert (2, 1, 0) in vectors
    assert (2, -1, 0) in vectors
    assert (1, 2, 0) in vectors
    assert (2, 0, 1) in vectors


def test_expand_family_2_2_1_full_orientation():
    vectors = expand_family([2, 2, 1])
    assert len(vectors) == 24
    assert (2, 2, 1) in vectors
    assert (2, 2, -1) in vectors
    assert (2, 1, 2) in vectors
    assert (1, 2, 2) in vectors


def test_custom_sets_expose_full_vectors():
    custom = load_custom_sets()
    for item in custom:
        assert item["id"] in ("2:1:0", "2:2:1")
        assert len(item["vectors"]) == 24
