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
| GET | `/api/game/{id}/legal-moves` | 合法路径 |
| POST | `/api/game/{id}/move` | 执行移动 |
| POST | `/api/game/{id}/ai-move` | AI 走一步（默认 graph_progress） |
| GET | `/api/game/{id}/history` | 棋谱/回放 |

`ai-move` 支持：

```text
ai_type=scoring_aware   # 默认，读取积分配置
ai_type=graph_progress  # 图距离贪心
ai_type=progress        # 连跳奖励贪心
ai_type=greedy          # 简单贪心
ai_type=random          # 随机
```

## 2. Python GameEnv

```python
from backend.game.env import GameEnv

env = GameEnv(config)
result = env.reset()

actions = env.action_space()
result = env.step(actions[0]["id"])
```

### 方法

```text
reset()
legal_moves()
action_space()
step(action)
observe()
state_dict()
```

### StepResult

```text
game_id
current_player
winner
last_move
legal_paths
legal_actions
done
scores
temp_scores
```

## 3. Headless

```powershell
python -m backend.game.headless --config configs\a_2p_6dir.json --moves 10
```

- 加载配置
- 自动创建 GameState
- 可选随机走 N 步
- 输出最终结果

## 4. 棋谱接口

历史接口返回：

```text
game_id
config
moves
initial_pieces
snapshots
scores
temp_scores
winner
```

每一步 move 包含：

```text
player
path
scoring
scores
temp_scores
```

## 5. 外部 AI 接入方式

```python
env = GameEnv(config)
result = env.reset()
while not result.done:
    action = my_agent.choose(result.legal_actions)
    result = env.step(action)
```
