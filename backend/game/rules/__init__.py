"""规则执行包：应用移动、吃子、胜负判定。"""

from __future__ import annotations

from .apply import MoveApplier
from .winner import check_winner

__all__ = ["MoveApplier", "check_winner"]
