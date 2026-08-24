# AI / 研究接口

PolyJump 本身是游戏，不包含 AI 训练逻辑。
但提供干净接口，方便外部程序接入自己的 AI。

## 当前 AI

- RandomAI
  - 随机选择一条合法路径

## 建议的外部 AI 接入

```python
from backend.game.config import PolyJumpConfig
from backend.game.env import GameEnv

config = PolyJumpConfig(...)
env = GameEnv(config)

result = env.reset()
while not result.done:
    action = my_agent.choose(result.legal_actions)
    result = env.step(action)
```

## 积分接口

`StepResult` 提供：

```text
scores
temp_scores
```

外部程序可以用积分作为 reward。

## 后续可扩展（不内置）

- GreedyAI
- MCTS
- 小神经网络
- RL / 自博弈

如果外部程序需要：

- 局面克隆
- compact observation
- reward shaping

可以后续在接口层添加，不改变游戏本体。

## 头less

```powershell
python -m backend.game.headless --config configs\a_2p_6dir.json --moves 10
```
