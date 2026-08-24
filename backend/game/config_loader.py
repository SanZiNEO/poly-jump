"""从配置文件加载 PolyJumpConfig。

支持 JSON 文件。文件内容可以直接是配置对象，
也可以包含顶层 "config" 字段。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import PolyJumpConfig


def load_config(path: str | Path) -> PolyJumpConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data: Any = json.load(f)

    if isinstance(data, dict) and "config" in data:
        data = data["config"]

    return PolyJumpConfig(**data)


def save_config(config: PolyJumpConfig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
