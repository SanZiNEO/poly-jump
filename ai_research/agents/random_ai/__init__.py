"""随机 AI：从合法路径中随机选一条，作为最底线。"""

from __future__ import annotations

import random
from typing import Optional

from backend.game.env import GameEnv

from ..base import Agent


class RandomAgent(Agent):
    slug = "random"
    display_name = "随机"

    def choose(self, env: GameEnv) -> Optional[list]:
        legal = env.observe().legal_paths
        if not legal:
            return None
        return random.choice(legal)
