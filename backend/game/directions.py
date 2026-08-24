"""移动方向常量与解析。

方向定义来自 configs/directions.json（通过 direction_registry 加载），
不写死在业务代码中。
"""

from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, List, Tuple

from .direction_registry import load_base_sets

Vector = Tuple[int, int, int]

_BASE_SETS = load_base_sets()

AXIS6: List[Vector] = _BASE_SETS[6]
FACE12: List[Vector] = _BASE_SETS[12]
BODY8: List[Vector] = _BASE_SETS[8]

# 组合方向：由基础方向集自动组合
DIRECTION_SETS: Dict[int, List[Vector]] = {
    6: AXIS6,
    8: BODY8,
    12: FACE12,
    14: AXIS6 + BODY8,
    18: AXIS6 + FACE12,
    20: FACE12 + BODY8,
    26: AXIS6 + FACE12 + BODY8,
}


def add_vec(p: Vector, v: Vector) -> Vector:
    return (p[0] + v[0], p[1] + v[1], p[2] + v[2])


def sub_vec(a: Vector, b: Vector) -> Vector:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale_vec(v: Vector, k: int) -> Vector:
    return (v[0] * k, v[1] * k, v[2] * k)


def expand_vector(v: Vector) -> List[Vector]:
    """把自定义向量展开成所有正负组合。"""
    axes: List[Tuple[int, ...]] = []
    for c in v:
        axes.append((0,) if c == 0 else (c, -c))
    return [tuple(comb) for comb in product(*axes)]


def resolve_direction_set(
    direction_set: int | List[int],
    custom_vectors: Iterable[Vector] = (),
) -> List[Vector]:
    """把配置里的编号和自定义向量解析为去重后的方向向量列表。"""
    if isinstance(direction_set, int):
        direction_set = [direction_set]

    result: List[Vector] = []
    for ds in direction_set:
        result.extend(DIRECTION_SETS.get(ds, []))
    for cv in custom_vectors:
        result.extend(expand_vector(tuple(cv)))

    seen = set()
    out: List[Vector] = []
    for v in result:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def vector_type(v: Vector) -> str:
    """返回方向类型，用于前端路线着色。"""
    nz = sum(1 for c in v if c != 0)
    max_abs = max(abs(c) for c in v)
    if max_abs == 1 and nz == 1:
        return "axis6"
    if max_abs == 1 and nz == 2:
        return "face12"
    if max_abs == 1 and nz == 3:
        return "body8"
    return "custom"
