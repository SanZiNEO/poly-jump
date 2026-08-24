"""方向规则注册表。

从 configs/directions.json 加载基础方向集和自定义方向集。
后续添加新方向规则只需修改该 JSON，不需要改前端硬编码。
"""

from __future__ import annotations

import json
from functools import lru_cache
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
            }
        )

    return base + custom
