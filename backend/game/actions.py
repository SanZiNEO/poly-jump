"""合法动作的稳定索引表示。"""

from __future__ import annotations

from typing import List, Tuple

from .path_metrics import path_metrics

Path = Tuple[Tuple[int, int, int], ...]


def action_index(paths: List[list]) -> List[dict]:
    """把合法路径列表转成带稳定 id 的动作列表。

    每个动作附带完整路径度量：
    - step_count
    - straight_distance
    - path_distance
    - step_distances

    外部 AI / 训练代码可以按需使用，平台不替它们做取舍。
    """
    return [
        {
            "id": i,
            "path": [list(p) for p in path],
            **path_metrics(path),
        }
        for i, path in enumerate(paths)
    ]
