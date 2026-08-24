"""可选小 AI：第一版仅实现 RandomAI。"""

from __future__ import annotations

import random
from typing import List, Optional, Sequence


class RandomAI:
    def select_move(self, legal_paths: List[Sequence[Sequence[int]]]) -> Optional[list]:
        if not legal_paths:
            return None
        return random.choice(list(legal_paths))
