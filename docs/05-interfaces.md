# 接口

## 1. HTTP API

启动：

```powershell
python -m uvicorn backend.app:app --reload
```

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/config` | 默认配置 |
| GET | `/api/direction-sets` | 方向规则 |
| POST | `/api/game/new` | 创建对局 |
| GET | `/api/game/{id}` | 当前局面 |
| GET | `/api/game/{id}/legal-actions` | 合法 action 路径 |
| POST | `/api/game/{id}/action` | 执行 action |
| POST | `/api/game/{id}/ai-action` | AI 执行一次 action（默认 graph_bfs） |
| GET | `/api/game/{id}/history` | 棋谱/回放 |

`ai-action` 支持：

```text
ai_type=graph_bfs            # 图距离 BFS
ai_type=euclidean            # 欧氏距离
ai_type=chebyshev            # 切比雪夫距离
```

## 2. Python GameEnv

```python
from backend.game.env import GameEnv

env = GameEnv(config)
result = env.reset()

actions = env.action_space()
result = env.execute_action(actions[0]["id"])
```

### 方法

```text
reset()
legal_actions()
action_space()
execute_action(action)
observe()
state_dict()
```

### ActionResult

```text
game_id
current_player
winner
last_action
legal_paths
legal_actions
done
scores
temp_scores
round
action_count
total_steps
total_straight_distance
total_path_distance
```

路径度量的具体定义见 [09-path-metrics.md](./09-path-metrics.md)。

## 3. Headless

```powershell
python -m backend.game.headless --config configs\a_2p_6dir.json --actions 10
```

- 加载配置
- 自动创建 GameState
- 可选自动执行 N 个 action
- 输出最终结果

## 4. 棋谱接口

历史接口返回：

```text
game_id
config
actions
initial_pieces
snapshots
scores
temp_scores
winner
action_count
path_stats
```

每个 action 包含：

```text
player
path
scoring
scores
temp_scores
step_count
straight_distance
path_distance
step_distances
```

## 5. 外部 AI 接入方式

```python
env = GameEnv(config)
result = env.reset()
while not result.done:
    action = my_agent.choose(result.legal_actions)
    result = env.execute_action(action)
```
