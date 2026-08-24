"""合法动作的稳定索引表示。"""

from __future__ import annotations

from typing import List, Tuple

Path = Tuple[Tuple[int, int, int], ...]


def action_index(paths: List[list]) -> List[dict]:
    """把合法路径列表转成带稳定 id 的动作列表。

    AI 外部程序只需要选 id，不需要处理完整路径对象。
    """
    return [
        {
            "id": i,
            "path": [list(p) for p in path],
        }
        for i, path in enumerate(paths)
    ]
