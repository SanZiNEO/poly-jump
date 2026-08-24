"""方向规则注册表。

从 configs/directions.json 加载基础方向集和自定义方向集。
后续添加新方向规则只需修改该 JSON，不需要改前端硬编码。
"""

from __future__ import annotations

import json
from functools import lru_cache
from itertools import permutations, product
from pathlib import Path
from typing import Dict, List, Tuple

Vector = Tuple[int, int, int]

_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent / "configs" / "directions.json"
)


@lru_cache(maxsize=1)
def _load_raw() -> dict:
    with _REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def expand_family(vector: List[int]) -> List[Vector]:
    """把一个自定义向量展开为完整方向族。

    例如 [2,1,0] 会生成：
    - 三个坐标轴的所有不同排列
    - 每个非零分量的正负号组合
    所以得到 6 种排列 × 4 种符号 = 24 个方向。
    """
    base = tuple(vector)
    results = set()
    for perm in set(permutations(base)):
        axes = []
        for c in perm:
            axes.append((0,) if c == 0 else (c, -c))
        for signs in product(*axes):
            results.add(tuple(signs))
    return sorted(results)


def load_base_sets() -> Dict[int, List[Vector]]:
    raw = _load_raw()
    result: Dict[int, List[Vector]] = {}
    for key, value in raw.get("base_sets", {}).items():
        result[int(key)] = [tuple(v) for v in value["vectors"]]
    return result


def load_custom_sets() -> List[dict]:
    raw = _load_raw()
    result = []
    for item in raw.get("custom_sets", []):
        result.append(
            {
                "id": item["id"],
                "name": item["name"],
                "vector": list(item["vector"]),
                "vectors": [list(v) for v in expand_family(item["vector"])],
            }
        )
    return result


def get_available_sets() -> List[dict]:
    """返回给前端的完整方向规则列表。"""
    base = []
    for key, vectors in sorted(load_base_sets().items()):
        base.append(
            {
                "id": str(key),
                "type": "base",
                "name": f"{key} 向",
                "vectors": [list(v) for v in vectors],
            }
        )

    custom = []
    for item in load_custom_sets():
        custom.append(
            {
                "id": f"custom:{item['id']}",
                "type": "custom",
                "name": item["name"],
                "vector": item["vector"],
                "vectors": item["vectors"],
            }
        )

    return base + custom
