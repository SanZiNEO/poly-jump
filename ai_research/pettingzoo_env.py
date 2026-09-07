"""PolyJump PettingZoo AEC 环境包装。

支持两种动作模式：

- full_action：一次环境 step = 一条完整路径 action
- primitive：一次环境 step = 一个最小移动 step（单步/单跳/两格跳）

底层复用 `backend.game.env.GameEnv`，不改游戏核心。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.game.config import PolyJumpConfig
from backend.game.env import GameEnv

try:
    import numpy as np
    from gymnasium import spaces
    from pettingzoo import AECEnv

    PETTINGZOO_AVAILABLE = True
except ImportError:  # pragma: no cover - 依赖可选
    PETTINGZOO_AVAILABLE = False
    AECEnv = object  # type: ignore
    np = None
    spaces = None


MAX_ACTIONS = 20000


if PETTINGZOO_AVAILABLE:

    class PolyJumpAECEnv(AECEnv):  # type: ignore
        """PolyJump 的 PettingZoo AEC 环境。"""

        metadata = {"name": "polyjump_v0", "render_modes": []}

        def __init__(
            self,
            config: PolyJumpConfig,
            action_mode: str = "full_action",
        ):
            if action_mode not in ("full_action", "primitive"):
                raise ValueError("action_mode 只支持 full_action / primitive")

            self.config = config
            self.action_mode = action_mode
            self.env = GameEnv(config)
            self.players = config.players
            self.possible_agents = [f"player_{i}" for i in range(1, self.players + 1)]
            self.agents = list(self.possible_agents)

            state = self.env.state_dict()
            self.num_points = len(state["points"])
            self._point_index = {tuple(p): i for i, p in enumerate(state["points"])}

            observation_space = spaces.Box(
                low=-1000.0,
                high=1000.0,
                shape=(self.num_points * 3 + self.num_points + self.players,),
                dtype=np.float32,
            )
            action_space = spaces.Discrete(MAX_ACTIONS)
            self.observation_spaces = {
                agent: observation_space for agent in self.possible_agents
            }
            self.action_spaces = {
                agent: action_space for agent in self.possible_agents
            }

            self.agent_selection = self.possible_agents[0]
            self.rewards: Dict[str, float] = {a: 0.0 for a in self.possible_agents}
            self._cumulative_rewards: Dict[str, float] = {
                a: 0.0 for a in self.possible_agents
            }
            self.terminations: Dict[str, bool] = {
                a: False for a in self.possible_agents
            }
            self.truncations: Dict[str, bool] = {
                a: False for a in self.possible_agents
            }
            self.infos: Dict[str, dict] = {a: {} for a in self.possible_agents}
            self._skip_agent_selection = None

        def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
            if seed is not None:
                import random
                random.seed(seed)
            self.env = GameEnv(self.config)
            self.agents = list(self.possible_agents)
            self.agent_selection = self.possible_agents[0]
            self.rewards = {a: 0.0 for a in self.possible_agents}
            self._cumulative_rewards = {a: 0.0 for a in self.possible_agents}
            self.terminations = {a: False for a in self.possible_agents}
            self.truncations = {a: False for a in self.possible_agents}
            self.infos = {a: {} for a in self.possible_agents}
            self._skip_agent_selection = None
            self._set_current_info(self.agent_selection)

        def observation_space(self, agent: str):
            return self.observation_spaces[agent]

        def action_space(self, agent: str):
            return self.action_spaces[agent]

        def observe(self, agent: str):
            state = self.env.state_dict()
            return self._flatten_observation(state)

        def _flatten_observation(self, state: dict) -> "np.ndarray":
            obs = []

            for p in state["points"]:
                obs.extend([float(c) for c in p])

            pieces = state.get("pieces", {})
            owner_by_index = [0] * self.num_points
            for pos_key, owner in pieces.items():
                pos = tuple(int(v) for v in pos_key.split(","))
                idx = self._point_index.get(pos)
                if idx is not None:
                    owner_by_index[idx] = int(owner)
            obs.extend([float(v) for v in owner_by_index])

            current = int(state.get("current_player", 1))
            for i in range(1, self.players + 1):
                obs.append(1.0 if i == current else 0.0)

            return np.asarray(obs, dtype=np.float32)

        def legal_actions(self, agent: str) -> List[list]:
            if agent != self.agent_selection:
                return []
            obs = self.env.observe()
            if self.action_mode == "primitive":
                return [
                    path
                    for path, action_meta in zip(obs.legal_paths, obs.legal_actions)
                    if action_meta.get("step_count", 0) <= 1
                ]
            return [list(p) for p in obs.legal_paths]

        def _action_mask(self, agent: str) -> List[int]:
            legal = self.legal_actions(agent)
            mask = [0] * MAX_ACTIONS
            for i in range(len(legal)):
                mask[i] = 1
            return mask

        def _set_current_info(self, agent: str, extra: Optional[dict] = None) -> None:
            self.infos = {a: {} for a in self.possible_agents}
            info = {
                "legal_actions": [list(p) for p in self.legal_actions(agent)],
                "action_mask": self._action_mask(agent),
            }
            if extra:
                info.update(extra)
            self.infos[agent] = info

        def step(self, action: int):
            agent = self.agent_selection

            if self.terminations[agent] or self.truncations[agent]:
                self._was_dead_step()
                if self.agents:
                    self._set_current_info(self.agent_selection)
                return

            legal = self.legal_actions(agent)
            if not legal:
                raise ValueError(f"agent {agent} 没有合法动作")
            if action < 0 or action >= len(legal):
                raise ValueError(f"非法 action index: {action}")

            path = legal[action]
            self.env.execute_action(path)

            state = self.env.state_dict()
            winner = state.get("winner")
            player_index = int(agent.split("_")[1])
            reward = 0.0
            if winner is not None:
                reward = 1.0 if winner == player_index else -1.0

            self.rewards = {a: 0.0 for a in self.possible_agents}
            self.rewards[agent] = reward

            done = winner is not None
            for a in self.possible_agents:
                self.terminations[a] = done
                self.truncations[a] = False

            last_action = state["actions"][-1] if state.get("actions") else {}
            self._set_current_info(
                agent,
                {
                    "path": [list(p) for p in path],
                    "step_count": last_action.get("step_count", 0),
                    "straight_distance": last_action.get("straight_distance", 0.0),
                    "path_distance": last_action.get("path_distance", 0.0),
                },
            )

            self._accumulate_rewards()

            if done:
                return

            idx = self.possible_agents.index(agent)
            for offset in range(1, len(self.possible_agents) + 1):
                next_agent = self.possible_agents[(idx + offset) % len(self.possible_agents)]
                if self.legal_actions(next_agent):
                    self.agent_selection = next_agent
                    self._set_current_info(next_agent)
                    return

            for a in self.possible_agents:
                self.terminations[a] = True

        def render(self, mode: str = "human"):
            raise NotImplementedError("PolyJumpAECEnv 暂不提供 render")

        def close(self):
            pass

else:  # pragma: no cover - 依赖可选

    class PolyJumpAECEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError("需要安装 pettingzoo 和 gymnasium 才能使用 PolyJumpAECEnv")
